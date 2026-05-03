// CharacterSheet shared bits — extracted in V6.10 refactor sprint.
// Stat / SimpleListCard / DiceCard / CharacterJournal / Anime5eSupplementView
// pulled out of the 1421-line CharacterSheet.jsx so that file can stay
// focused on the layout shell and routing.
import React, { useState } from "react";
import { Dice6 } from "lucide-react";
import { api, formatApiErrorDetail } from "../../lib/api";

export function Stat({ label, v }) {
  return (
    <div>
      <div className="label-ref">{label}</div>
      <div className="font-display text-xl text-gold-bright">{v}</div>
    </div>
  );
}

export function SimpleListCard({ title, items, testid, systemId, autoLinkKind }) {
  // V6.21 — each item is clickable to open its reference entry. Items
  // may be plain strings (legacy) or rich dicts from ReferencePicker.
  // Tolerant of strings OR objects ({name, tier, cost, description}).
  // Ability/cypher lists from cross-system conversions return rich
  // dicts; legacy seeds + manual entry use plain strings.
  const handleClick = (it) => {
    if (!systemId) return;
    const name = typeof it === "string" ? it : (it?.name || it?.title);
    if (!name) return;
    window.dispatchEvent(new CustomEvent("tg:open-reference", {
      detail: {
        system_id: systemId,
        kind: (typeof it === "object" && it?.__kind) || autoLinkKind || "items",
        name,
      },
    }));
  };
  const renderItem = (it, i) => {
    if (it == null) return null;
    const clickable = !!systemId;
    const cls = `text-sm text-parchment font-body${clickable ? " cursor-pointer hover:text-gold-bright" : ""}`;
    if (typeof it === "string" || typeof it === "number") {
      return (
        <li key={i} className={cls}
            onClick={() => handleClick(it)}
            data-testid={clickable ? `${testid}-item-${i}` : undefined}>
          · {it}
        </li>
      );
    }
    // Object with name + optional tier/cost/description/damage/school
    const head = [it.name || it.title,
                   it.tier ? `T${it.tier}` : null,
                   it.level != null ? `L${it.level}` : null,
                   it.school,
                   it.damage,
                   it.ac,
                   it.category,
                   it.cost ? `cost ${it.cost}` : null,
                  ].filter(Boolean).join(" · ");
    return (
      <li key={i}
          className={`text-sm text-parchment font-body${systemId ? " cursor-pointer hover:text-gold-bright" : ""}`}
          onClick={() => handleClick(it)}
          data-testid={systemId ? `${testid}-item-${i}` : undefined}>
        <div>· <b>{head || "—"}</b></div>
        {it.description && (
          <div className="text-mist text-[12px] italic ml-3 mt-0.5 leading-snug">
            {it.description}
          </div>
        )}
      </li>
    );
  };
  return (
    <div className="card-mystic p-6 mt-4" data-testid={testid}>
      <div className="label-ref">{title}</div>
      <ul className="mt-2 space-y-1.5">
        {(items || []).map(renderItem)}
      </ul>
    </div>
  );
}

export function DiceCard({ quickRolls, roll }) {
  // Lightweight wrapper so D&D / Cypher views get the same dice surface
  // without duplicating the markup.
  return (
    <div className="card-mystic p-6 mt-6" data-testid="system-dice-card">
      <div className="h-arcane text-sm">Dice Macros</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {quickRolls.map((q) => (
          <button key={q.label} onClick={() => roll(q.notation, q.label)}
                  className="btn btn-ghost text-xs"
                  title={q.hint || q.notation}
                  data-testid={`quick-${q.label.replace(/\s+/g, "-")}`}>
            <Dice6 className="w-3 h-3"/> {q.label}
          </button>
        ))}
      </div>
      <div className="text-[10px] text-mist/70 italic mt-2">
        Click a macro to post the roll into the campaign's first PBP channel.
        Open a session to also feed the live spotlight + dice altar.
      </div>
    </div>
  );
}

export function CharacterJournal({ character, onUpdated }) {
  const entries = character.folio?.journal || [];
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async () => {
    const t = text.trim();
    if (!t) return;
    setBusy(true); setErr("");
    try {
      await api.post(`/characters/${character.id}/journal`, { text: t });
      setText("");
      onUpdated && onUpdated();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };
  return (
    <div className="card-mystic p-6 mt-6" data-testid="character-journal">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="label-ref">Character Journal</div>
          <div className="text-[11px] text-mist/70 italic mt-1">
            Anything you write here is timestamped and pushed to the campaign's World Codex
            as a player journal node — feeds session recaps too.
          </div>
        </div>
        <span className="text-[10px] text-mist tracking-widest uppercase">
          {entries.length} entr{entries.length === 1 ? "y" : "ies"}
        </span>
      </div>
      <div className="mt-3 flex gap-2">
        <textarea className="input min-h-[60px] flex-1"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="What does your character note about today's session?"
                  data-testid="character-journal-input"/>
        <button onClick={submit} disabled={busy || !text.trim()}
                className="btn btn-primary text-xs self-stretch px-4"
                data-testid="character-journal-submit">
          {busy ? "Posting…" : "Add"}
        </button>
      </div>
      {err && <div className="text-ember text-xs mt-2" data-testid="character-journal-error">{err}</div>}
      {entries.length > 0 && (
        <div className="mt-4 space-y-2 max-h-[420px] overflow-y-auto pr-1">
          {[...entries].reverse().map((e, i) => (
            <div key={i} className="border border-gold/15 rounded-sm p-3"
                 data-testid={`character-journal-entry-${i}`}>
              <div className="text-[10px] text-mist tracking-widest uppercase mb-1">
                {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
                {e.session_id ? ` · session ${e.session_id.slice(0, 6)}…` : ""}
              </div>
              <div className="text-sm text-parchment whitespace-pre-wrap font-body">{e.text}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Anime 5E hybrid supplement — read-only echo on the character sheet.
// Displays the BESM-style point-buy attributes the player layered on top
// of their d20 chassis (`folio.anime5e_state.point_buys[]`).
export function Anime5eSupplementView({ folio }) {
  const state = folio?.anime5e_state;
  const buys = state?.point_buys || [];
  if (!state || buys.length === 0) return null;
  const totalSpent = buys.reduce(
    (sum, b) => sum + ((b.cost_per_level || 0) * (b.level || 1)), 0);
  return (
    <div className="card-mystic p-6 mt-4 border-l-4"
         style={{ borderLeftColor: "#E03A8E" }}
         data-testid="anime5e-sheet-supplement">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <div className="label-ref">BESM Point-Buy Layer · Anime 5E hybrid</div>
          <div className="text-[11px] text-mist/80 italic">
            Genre-power layer over the d20 chassis. BESM-style point-buy (one-way port from 5E).
          </div>
        </div>
        <div className="text-right">
          <div className="font-display text-xl text-gold">{totalSpent}<span className="text-mist text-sm"> / {state.point_budget || 50}</span></div>
          <div className="text-[10px] text-mist">pts spent</div>
        </div>
      </div>
      <div className="mt-3 space-y-2">
        {buys.map((b, i) => (
          <div key={i} className="border border-gold/15 rounded-sm p-2 flex items-center justify-between gap-3"
               data-testid={`anime5e-sheet-buy-${i}`}>
            <div className="min-w-0 flex-1">
              <div className="text-sm text-parchment font-ui"><b>{b.name}</b>
                <span className="text-[10px] text-mist ml-2">×{b.level}</span>
              </div>
              {b.blurb_role && <div className="text-[11px] text-mist/70 italic">{b.blurb_role}</div>}
            </div>
            <span className="font-display text-gold">{(b.cost_per_level || 0) * (b.level || 1)} pts</span>
          </div>
        ))}
      </div>
    </div>
  );
}
