import React, { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Dice6, X, Heart, Zap, Sword, Shield, BookOpen, Sparkles, Crown } from "lucide-react";
import { api } from "../lib/api";

/**
 * ActorPopover — the active player's surface during their turn.
 *
 * One popover, two stacked panes:
 *   1. <RollOptionsList>  — system-aware roll suggestions built from
 *      the character's Stats + Attributes + Skills, filtered through
 *      the campaign's GM Primer prohibited list. Click to roll;
 *      the existing /api/dice endpoint broadcasts the result via WS.
 *   2. <JournalThisTurn>  — quick textarea to append a journal
 *      entry onto the active character's Folio AND the session log,
 *      so the recap pipeline picks it up.
 *
 * Rendered via createPortal so the popover never gets clipped by the
 * AV strip's overflow. Anchored to the active tile via getBoundingClientRect().
 */

export default function ActorPopover({ anchorEl, sessionId, character, campaign, onClose }) {
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const popRef = useRef(null);

  useEffect(() => {
    if (!anchorEl) return;
    const reflow = () => {
      const r = anchorEl.getBoundingClientRect();
      const W = 360;
      const margin = 12;
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      let left = r.left + r.width / 2 - W / 2;
      if (left < margin) left = margin;
      if (left + W > vw - margin) left = vw - W - margin;
      let top = r.bottom + 8;
      // If we'd run off the bottom, anchor above the tile.
      if (top + 360 > vh - margin) top = Math.max(margin, r.top - 360 - 8);
      setPos({ top, left });
    };
    reflow();
    window.addEventListener("resize", reflow);
    window.addEventListener("scroll", reflow, true);
    return () => {
      window.removeEventListener("resize", reflow);
      window.removeEventListener("scroll", reflow, true);
    };
  }, [anchorEl]);

  // Outside-click + Escape close
  useEffect(() => {
    const onDoc = (e) => {
      if (popRef.current && popRef.current.contains(e.target)) return;
      if (anchorEl && anchorEl.contains(e.target)) return;
      onClose();
    };
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [anchorEl, onClose]);

  if (!anchorEl || !character) return null;

  return createPortal(
    <div
      ref={popRef}
      role="dialog"
      data-testid="actor-popover"
      style={{ position: "fixed", top: pos.top, left: pos.left, zIndex: 1100, width: 360 }}
      className="card-mystic p-4 border border-gold/50 shadow-[0_24px_70px_-30px_rgba(212,175,55,0.7)] animate-fade-in"
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {character.token_color && (
              <span aria-hidden="true"
                    className="inline-block w-3 h-3 rounded-full border border-gold/40 shrink-0"
                    style={{ backgroundColor: character.token_color,
                             boxShadow: `0 0 8px ${character.token_color}99` }}/>
            )}
            <div className="font-display text-lg text-parchment tracking-wide truncate">
              {character.name}
            </div>
          </div>
          <div className="text-[10px] font-ui uppercase tracking-widest text-gold/70 truncate">
            Your turn · {character.power_level || "Heroic"}
          </div>
        </div>
        <button onClick={onClose} className="btn btn-ghost p-1.5"
                data-testid="actor-popover-close" aria-label="Close">
          <X className="w-3.5 h-3.5"/>
        </button>
      </div>

      {/* Quick derived stat row */}
      <DerivedRow ch={character}/>

      <div className="divider-sigil my-3"/>
      <RollOptionsList ch={character} campaign={campaign} sessionId={sessionId}/>
      <div className="divider-sigil my-3"/>
      <JournalThisTurn ch={character} sessionId={sessionId}/>
    </div>,
    document.body
  );
}

function DerivedRow({ ch }) {
  const d = ch.derived || {};
  const stat = (label, val, Icon) => (
    <div className="flex flex-col items-center" title={label}>
      <Icon className="w-3 h-3 text-gold/70"/>
      <div className="text-[10px] font-ui uppercase tracking-widest text-mist">{label}</div>
      <div className="text-sm font-display text-gold-bright">{val ?? "—"}</div>
    </div>
  );
  return (
    <div className="grid grid-cols-5 gap-2 text-center" data-testid="actor-popover-derived">
      {stat("ATK", d.attack_value, Sword)}
      {stat("DEF", d.defence_value, Shield)}
      {stat("HP",  d.health_points, Heart)}
      {stat("EP",  d.energy_points, Zap)}
      {stat("DM",  d.damage_multiplier, Sparkles)}
    </div>
  );
}

/* -------- Roll Options -------- */

function RollOptionsList({ ch, campaign, sessionId }) {
  const [rolling, setRolling] = useState(false);

  // Build the suggestion list. BESM 4E posture: 2d6 + Stat (+ Skill or
  // Attribute) vs target number. Filtered against the GM Primer's
  // prohibited lists so a banned Attribute can't be rolled directly.
  const options = useMemo(() => buildBesmRollOptions(ch, campaign), [ch, campaign]);

  const fire = async (opt) => {
    if (rolling) return;
    setRolling(true);
    try {
      await api.post("/dice", {
        session_id: sessionId,
        notation: opt.notation,
        label: opt.label,
        target: opt.target ?? null,
        character_id: ch.id || null,
        private: false,
      });
    } catch (e) {
      // Failure shows up server-side; popover stays open.
      console.warn("dice roll failed", e);
    } finally {
      setRolling(false);
    }
  };

  return (
    <div data-testid="roll-options">
      <div className="label-ref mb-2 flex items-center gap-2">
        <Dice6 className="w-3 h-3"/> Roll Options
      </div>
      {options.length === 0 ? (
        <div className="text-[11px] text-mist italic">
          This character has no statted Attributes or Skills yet — flesh out their
          Forge sheet to enable system-aware rolls.
        </div>
      ) : (
        <div className="max-h-44 overflow-y-auto pr-1 space-y-1.5 scroll-stylish">
          {options.map((opt, i) => (
            <button
              key={`${opt.kind}-${i}-${opt.label}`}
              type="button"
              onClick={() => fire(opt)}
              disabled={rolling}
              data-testid={`roll-opt-${opt.kind}-${i}`}
              className="w-full text-left p-2 rounded-sm border border-gold/15 hover:border-gold/50 transition flex items-baseline justify-between gap-2 group"
            >
              <span className="min-w-0 flex-1">
                <span className="text-[12px] text-parchment font-ui">{opt.label}</span>
                {opt.note && (
                  <span className="block text-[10px] text-mist italic mt-0.5">{opt.note}</span>
                )}
              </span>
              <span className="text-gold-bright font-display text-[12px] shrink-0">
                {opt.notation}
                {opt.target ? <span className="text-mist/70 ml-1">· TN {opt.target}</span> : null}
              </span>
            </button>
          ))}
        </div>
      )}
      <div className="text-[10px] text-mist/60 italic mt-1.5 font-ui">
        Suggestions filtered through GM Primer; click to roll & broadcast.
      </div>
    </div>
  );
}

// BESM 4E roll-options builder. System-specific; Anime 5E + Cypher land
// alongside their content batches. Posture: prefer the player's strongest
// Stat for the implied check, layer Attribute / Skill bonuses where they
// exist on the sheet, surface Defects only when they have a roll-active
// trigger ("Phobia", "Achilles Heel", etc.) — those are GM-fired anyway.
function buildBesmRollOptions(ch, campaign) {
  const out = [];
  const s = ch.stats || {};
  const prohibitedA = new Set((campaign?.prohibited_attributes) || []);
  const prohibitedS = new Set((campaign?.prohibited_skill_groups) || []);

  // Generic Stat checks (always available on BESM 4E).
  const statRow = (key, label) => {
    const v = s[key] || 0;
    out.push({
      kind: "stat",
      label: `${label} check`,
      note: `2d6 + ${label} (${v})`,
      notation: `2d6+${v}`,
      target: 7, // Average TN — GM may call higher.
    });
  };
  statRow("body", "Body");
  statRow("mind", "Mind");
  statRow("soul", "Soul");

  // Attribute rolls — most BESM Attributes resolve as 2d6 + dominant Stat
  // + Attribute Level. We pair common combat Attributes to Body, mental
  // ones to Mind, social ones to Soul, and anything else to the highest.
  const dominant = (a) => {
    if (/Attack|Defence|Tough|Massive|Weapon/i.test(a.name)) return ["Body", s.body || 0];
    if (/Cognition|Mind|Heightened Awareness|Sixth Sense|Telepathy|Mind Shield/i.test(a.name))
      return ["Mind", s.mind || 0];
    if (/Connected|Wealth|Inspire|Healing|Conversion/i.test(a.name)) return ["Soul", s.soul || 0];
    const top = Math.max(s.body || 0, s.mind || 0, s.soul || 0);
    const lbl = (s.body === top) ? "Body" : (s.mind === top) ? "Mind" : "Soul";
    return [lbl, top];
  };
  for (const a of ch.attributes || []) {
    if (prohibitedA.has(a.name)) continue;
    const [statLbl, statVal] = dominant(a);
    const lvl = a.level || 0;
    out.push({
      kind: "attr",
      label: `${a.name} ×${lvl}`,
      note: `2d6 + ${statLbl} (${statVal}) + ${a.name} (${lvl})${a.note ? " · " + a.note : ""}`,
      notation: `2d6+${statVal + lvl}`,
      target: tnForAttribute(a.name),
    });
  }

  // Skill Groups — 2d6 + Mind (default) + Group Level.
  for (const sk of ch.skills || []) {
    if (prohibitedS.has(sk.group)) continue;
    const lvl = sk.level || 0;
    out.push({
      kind: "skill",
      label: `${sk.group} ×${lvl}`,
      note: `2d6 + Mind (${s.mind || 0}) + ${sk.group} (${lvl})${sk.note ? " · " + sk.note : ""}`,
      notation: `2d6+${(s.mind || 0) + lvl}`,
      target: 9, // Skill Group default TN — average difficulty.
    });
  }

  // Plain unmodified d6 / 2d6 for ad-hoc situations
  out.push({ kind: "raw", label: "Plain 2d6", note: "Unmodified roll", notation: "2d6", target: null });
  out.push({ kind: "raw", label: "Plain d20", note: "Cross-system fallback", notation: "1d20", target: null });

  return out;
}

// Per-Attribute target-number heuristics. Combat Attributes lean on the
// table's standing TN; passive Attributes get easier TNs.
function tnForAttribute(name) {
  if (/Attack|Defence|Massive|Weapon|Combat/i.test(name)) return 7;  // standard combat
  if (/Heightened|Sixth Sense|Cognition/i.test(name)) return 9;       // perception
  if (/Healing|Inspire|Conversion|Mind/i.test(name)) return 11;       // hard
  return 9;
}

/* -------- Journal This Turn -------- */

function JournalThisTurn({ ch, sessionId }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const submit = async (e) => {
    e?.preventDefault();
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      await api.post(`/characters/${ch.id}/journal`, {
        text: text.trim(),
        session_id: sessionId || null,
      });
      setText("");
      setSavedAt(new Date());
      setTimeout(() => setSavedAt(null), 1800);
    } catch (e) {
      console.warn("journal submit failed", e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <form onSubmit={submit} data-testid="journal-this-turn">
      <div className="label-ref mb-1.5 flex items-center gap-2">
        <BookOpen className="w-3 h-3"/> Journal this turn
      </div>
      <textarea
        className="input min-h-[60px] text-[12px]"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="One line your character will remember…"
        data-testid="journal-input"
      />
      <div className="flex items-center justify-between mt-1.5 gap-2">
        <div className="text-[10px] text-mist/60 italic">
          Saves to your Folio + feeds the session recap.
        </div>
        <button type="submit" disabled={busy || !text.trim()}
                className="btn btn-primary text-[10px] py-1 px-2"
                data-testid="journal-submit">
          {busy ? "Saving…" : savedAt ? "Saved ✓" : "Save"}
        </button>
      </div>
    </form>
  );
}

export { Crown };  // re-export to avoid an import-warning when tree-shaking
