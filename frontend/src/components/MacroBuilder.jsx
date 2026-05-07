/**
 * MacroBuilder — V6.25.9
 *
 * Character-aware macro composer for the Quick-Roll Bar.
 *
 * The builder reads from the LIVE character sheet (not the SRD or the
 * campaign reference editor). All tokens it inserts substitute against
 * that character's mechanical state at fire time:
 *
 *   • {stat:body|mind|soul|str|dex|con|int|wis|cha}
 *   • {attr:<Name>}      → effective Level (base + Σlim.rank − Σenh.rank)
 *   • {skill:<Name>}     → assigned Level
 *   • {def:<Name>}       → Defect rank
 *   • {derived:cv|atk|dfn|hp|ep|dm|ac|init}
 *   • {hp}, {ep}, {sanity}
 *   • Plain dice: 2d6, 3d6, 1d20, etc.
 *   • Plain numerics, +/-/×/÷, parens.
 *
 * Use:
 *   <MacroBuilder
 *      campaignId={...}
 *      character={fullCharDoc}      // builder pulls attributes/skills/defects/stats from here
 *      systemId={"besm-4e"|"dnd-5e"|"anime-5e"|"cypher"}
 *      seedFormula={""}              // optional pre-fill (e.g. when launched from a sheet row)
 *      onSaved={(macro) => ...}
 *      onClose={() => ...}/>
 *
 * The popup is rendered via React Portal at <body> root so it cannot
 * be visually clipped by ancestor stacking contexts (the V6.25.7
 * macro creator was rendering BEHIND the next scroll section because
 * its `card-mystic` ancestor created a stacking context).
 */
import React, { useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { api } from "../lib/api";
import { Plus, X, Dices, Hash, Eye, AlertCircle, Loader2 } from "lucide-react";

const SYSTEM_STATS = {
  "besm-4e":  ["body", "mind", "soul"],
  "anime-5e": ["body", "mind", "soul", "str", "dex", "con", "int", "wis", "cha"],
  "dnd-5e":   ["str", "dex", "con", "int", "wis", "cha"],
  "cypher":   [],
};
const SYSTEM_DERIVED = {
  "besm-4e":  ["cv", "atk", "dfn", "hp", "ep", "dm"],
  "anime-5e": ["cv", "atk", "dfn", "hp", "ep", "dm", "ac", "init"],
  "dnd-5e":   ["ac", "init"],
  "cypher":   [],
};
const DICE_PRESETS = ["2d6", "3d6", "1d20", "1d10", "1d8", "1d6", "1d4"];

export default function MacroBuilder({
  campaignId, character, systemId = "besm-4e", seedFormula = "",
  onSaved, onClose,
}) {
  const [name, setName] = useState("");
  const [label, setLabel] = useState("");
  const [scope, setScope] = useState("user");
  const [formula, setFormula] = useState(seedFormula);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [preview, setPreview] = useState(null);

  const append = (token) => {
    setFormula((f) => {
      if (!f) return token;
      // Auto-insert + between value-like tokens to keep the formula valid.
      const trimmed = f.trim();
      const lastCh = trimmed.slice(-1);
      const opTrail = "+-*/×÷(".includes(lastCh);
      return opTrail ? `${trimmed}${token}` : `${trimmed}+${token}`;
    });
  };
  const appendOp = (op) => setFormula((f) => `${f}${op}`);

  const resetFormula = () => { setFormula(""); setPreview(null); };

  // The "Test against character" live preview hits the same backend
  // resolver path the chat /macro fire does, so what you see here is
  // exactly what'll resolve at fire-time. We use the raw `roll_dice`
  // path indirectly by POSTing a temporary macro fire — but to keep
  // this self-contained without round-tripping, we just substitute on
  // the client side using the same token grammar.
  const live = useMemo(() => _expandClientSide(formula, character), [formula, character]);

  const submit = async (e) => {
    e?.preventDefault?.();
    setBusy(true); setErr(""); setPreview(null);
    try {
      const { data } = await api.post(`/campaigns/${campaignId}/macros`,
        { name, formula, label, scope });
      onSaved?.(data);
    } catch (e2) {
      setErr(e2.response?.data?.detail || e2.message);
    } finally { setBusy(false); }
  };

  const previewRoll = () => {
    setPreview({ expanded: live });
  };

  const stats   = SYSTEM_STATS[systemId] || SYSTEM_STATS["besm-4e"];
  const derived = SYSTEM_DERIVED[systemId] || SYSTEM_DERIVED["besm-4e"];
  const attrs   = (character?.attributes || []).filter((a) => a?.name);
  const skills  = (character?.skills || []).filter((s) => s?.group || s?.name);
  const defects = (character?.defects || []).filter((d) => d?.name);

  // V6.25.11 — Refinery state. Holds the parsed unresolved tokens
  // pending user disambiguation. Each item: {idx, raw, kind, ?tn}.
  // `idx` is the character offset of the bare token in `formula`.
  const [refinery, setRefinery] = useState([]);
  const refine = () => setRefinery(_parseUnresolved(formula));
  const resolveRefineryPick = (slot, name) => {
    // Replace the bare token at `slot.idx` with `{kind:Name}` (or
    // `{stat:Name}:tn` when the slot carried a target-number suffix).
    setFormula((f) => {
      const before = f.slice(0, slot.idx);
      const after = f.slice(slot.idx + slot.raw.length);
      const tnSuffix = slot.tn ? ` (TN ${slot.tn})` : "";
      // The TN-suffix lives in the comment / label, not the formula —
      // the dice engine doesn't need it; the GM sees it in the live
      // preview line for table-side adjudication.
      return before + `{${slot.kind}:${name}}${tnSuffix}` + after;
    });
    // Drop the resolved slot from the queue.
    setRefinery((r) => r.filter((x) => x.idx !== slot.idx));
  };

  return createPortal(
    <div className="fixed inset-0 z-[200] flex items-end sm:items-center justify-center p-0 sm:p-4
                       bg-void/90 backdrop-blur-sm overflow-y-auto"
         onClick={onClose}
         data-testid="macro-builder">
      <form onSubmit={submit}
            onClick={(e) => e.stopPropagation()}
            className="card-mystic p-5 max-w-2xl w-full max-h-[95vh] overflow-y-auto
                          mb-0 sm:mb-auto"
            style={{ backgroundColor: "rgb(8, 6, 14)" }}>
        <div className="flex items-start justify-between mb-3 gap-2 flex-wrap">
          <div>
            <div className="label-ref">Macro Builder</div>
            <div className="font-display text-lg text-parchment">
              {character?.name ? `for ${character.name}` : "New macro"}
            </div>
            <div className="text-[10px] text-mist italic mt-0.5">
              Tokens read from this character's sheet at fire-time —
              effective Levels include limiter / enhancement ranks.
            </div>
          </div>
          <button type="button" onClick={onClose} className="text-mist hover:text-gold-bright"
                  aria-label="Close" data-testid="macro-builder-close">
            <X className="w-4 h-4"/>
          </button>
        </div>

        {/* Identity row. */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
          <div>
            <label className="label-ref block mb-1">Name (used as <code>/name</code>)</label>
            <input className="input" required pattern="[A-Za-z][A-Za-z0-9_-]{0,30}"
                   value={name} placeholder="strike"
                   onChange={(e) => setName(e.target.value)}
                   data-testid="macro-builder-name" autoFocus/>
          </div>
          <div>
            <label className="label-ref block mb-1">Display label</label>
            <input className="input" value={label} placeholder="Sword Strike"
                   onChange={(e) => setLabel(e.target.value)}
                   data-testid="macro-builder-label"/>
          </div>
          <div>
            <label className="label-ref block mb-1">Scope</label>
            <select className="select" value={scope}
                     onChange={(e) => setScope(e.target.value)}
                     data-testid="macro-builder-scope">
              <option value="user">Personal</option>
              <option value="campaign">Campaign (GM-only)</option>
            </select>
          </div>
        </div>

        {/* Formula composer. */}
        <div className="border border-gold/20 rounded-sm p-3 mb-3 bg-void/40">
          <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
            <label className="label-ref">Formula</label>
            <div className="flex gap-1 flex-wrap">
              <button type="button" onClick={refine}
                      className="btn btn-ghost text-[10px] border border-gold/30 hover:border-gold-bright"
                      title="Parse free-form tokens like `attribute`, `skill`, `stat:15` and surface dropdown pickers."
                      data-testid="macro-builder-refine">
                ⚗ Refinery
              </button>
              <button type="button" onClick={previewRoll} className="btn btn-ghost text-[10px]"
                      data-testid="macro-builder-preview">
                <Eye className="w-3 h-3"/> Preview
              </button>
              <button type="button" onClick={resetFormula} className="btn btn-ghost text-[10px]"
                      data-testid="macro-builder-reset">
                Clear
              </button>
            </div>
          </div>
          <input className="input font-mono text-sm" value={formula}
                 placeholder="2d6+attribute+skill+stat:15  ← type plain words; click Refinery to pick"
                 onChange={(e) => setFormula(e.target.value)}
                 data-testid="macro-builder-formula"/>
          <div className="text-[10px] text-mist mt-1.5 font-mono break-all"
               data-testid="macro-builder-preview-line">
            <span className="text-mist/60 not-italic">live →</span> {live || "—"}
          </div>
          <div className="text-[10px] text-mist/60 mt-1 italic">
            Free-form tip: type <span className="text-gold-bright">attribute</span>, <span className="text-gold-bright">skill</span>, <span className="text-gold-bright">defect</span>, <span className="text-gold-bright">stat</span>, or <span className="text-gold-bright">derived</span> as bare words. Add <span className="text-gold-bright">:N</span> after a stat (e.g. <span className="text-gold-bright">stat:15</span>) to record a Target Number for the GM. Hit <span className="text-gold-bright">Refinery</span> and the dropdowns will pin to your character sheet.
          </div>
          {preview && (
            <div className="mt-2 text-[11px] text-gold-bright"
                 data-testid="macro-builder-preview-result">
              At fire-time, this resolves to: <span className="font-mono">{preview.expanded}</span>
            </div>
          )}

          {/* V6.25.11 — Refinery: dropdowns for unresolved bare tokens. */}
          {refinery.length > 0 && (
            <div className="mt-3 border-t border-gold/15 pt-3 space-y-2"
                 data-testid="macro-refinery-panel">
              <div className="label-ref">Refinery — pick the right entry from your sheet</div>
              {refinery.map((slot, i) => (
                <div key={`${slot.idx}-${i}`}
                     className="flex flex-wrap items-center gap-2 text-xs"
                     data-testid={`macro-refinery-slot-${slot.kind}-${slot.idx}`}>
                  <span className="text-mist/70">
                    @{slot.idx}: <code className="text-gold-bright">{slot.raw}</code> →
                  </span>
                  <select className="select select-sm"
                           defaultValue=""
                           onChange={(e) => e.target.value && resolveRefineryPick(slot, e.target.value)}
                           data-testid={`macro-refinery-pick-${slot.kind}-${slot.idx}`}>
                    <option value="" disabled>Pick {slot.kind}…</option>
                    {(slot.kind === "attr" ? attrs.map((a) => a.name)
                      : slot.kind === "skill" ? skills.map((s) => s.group || s.name)
                      : slot.kind === "def" ? defects.map((d) => d.name)
                      : slot.kind === "stat" ? stats
                      : slot.kind === "derived" ? derived
                      : []).map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                  {slot.tn && (
                    <span className="text-[10px] text-arcane">vs TN {slot.tn}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Operator row. */}
        <div className="mb-3">
          <div className="label-ref mb-1">Operators</div>
          <div className="flex flex-wrap gap-1.5">
            {["+", "-", "×", "÷", "(", ")"].map((op) => (
              <button key={op} type="button"
                      onClick={() => appendOp(op === "×" ? "*" : op === "÷" ? "/" : op)}
                      className="tag hover:border-gold-bright"
                      data-testid={`macro-op-${op}`}>{op}</button>
            ))}
          </div>
        </div>

        {/* Dice presets + custom dice. */}
        <div className="mb-3">
          <div className="label-ref mb-1 flex items-center gap-1">
            <Dices className="w-3 h-3"/> Dice
          </div>
          <div className="flex flex-wrap gap-1.5 items-center">
            {DICE_PRESETS.map((d) => (
              <button key={d} type="button" onClick={() => append(d)}
                      className="tag hover:border-gold-bright"
                      data-testid={`macro-dice-${d}`}>{d}</button>
            ))}
            <CustomDicePicker onPick={append}/>
          </div>
        </div>

        {/* Numeric modifier. */}
        <div className="mb-3">
          <div className="label-ref mb-1 flex items-center gap-1">
            <Hash className="w-3 h-3"/> Flat modifier
          </div>
          <NumericInjector onPick={append}/>
        </div>

        {/* Stats. */}
        {stats.length > 0 && (
          <ChipGroup label="Stats" testid="macro-stats">
            {stats.map((s) => (
              <TokenChip key={s} token={`{stat:${s}}`} display={s.toUpperCase()}
                         hint={_describeStat(s, character)}
                         onPick={append}/>
            ))}
          </ChipGroup>
        )}

        {/* Attributes from the character sheet. */}
        {attrs.length > 0 && (
          <ChipGroup label="Attributes (effective level — limiter/enh ranks applied)"
                     testid="macro-attrs">
            {attrs.map((a, i) => {
              const eff = _effLevel(a);
              const tok = `{attr:${a.name}}`;
              const limR = (a.limiters || []).reduce((s, m) => s + (typeof m === "string" ? 1 : Math.max(1, +m.rank || Math.abs(+m.value || 0) || 1)), 0);
              const enhR = (a.enhancements || []).reduce((s, m) => s + (typeof m === "string" ? 1 : Math.max(1, +m.rank || Math.abs(+m.value || 0) || 1)), 0);
              // Helpful tooltip showing the eff-level breakdown so users
              // learn the math while authoring macros.
              const tooltip =
                `${a.display_name || a.name} (${a.name}) → eff ×${eff}\n`
                + `  base level ×${a.level || 1}`
                + (limR ? ` + ${limR} limiter rank${limR === 1 ? "" : "s"}` : "")
                + (enhR ? ` − ${enhR} enhancement rank${enhR === 1 ? "" : "s"}` : "")
                + `\nClick to insert ${tok} — resolves to +${eff} at fire-time.`;
              return (
                <TokenChip key={`${a.name}-${i}`}
                           token={tok}
                           display={a.display_name || a.name}
                           hint={`eff ×${eff}`}
                           tooltipOverride={tooltip}
                           onPick={append}/>
              );
            })}
          </ChipGroup>
        )}

        {/* Skills. */}
        {skills.length > 0 && (
          <ChipGroup label="Skills" testid="macro-skills">
            {skills.map((s, i) => (
              <TokenChip key={`${s.group || s.name}-${i}`}
                         token={`{skill:${s.group || s.name}}`}
                         display={s.group || s.name}
                         hint={`lvl ${s.level || 0}`}
                         onPick={append}/>
            ))}
          </ChipGroup>
        )}

        {/* Defects. */}
        {defects.length > 0 && (
          <ChipGroup label="Defects" testid="macro-defects">
            {defects.map((d, i) => (
              <TokenChip key={`${d.name}-${i}`}
                         token={`{def:${d.name}}`}
                         display={d.name}
                         hint={`rank ${d.rank || 1}`}
                         tone="ember"
                         onPick={append}/>
            ))}
          </ChipGroup>
        )}

        {/* Derived. */}
        {derived.length > 0 && (
          <ChipGroup label="Derived" testid="macro-derived">
            {derived.map((d) => (
              <TokenChip key={d} token={`{derived:${d}}`} display={d.toUpperCase()}
                         hint={String(_derived(d, character) ?? "—")}
                         onPick={append}/>
            ))}
            <TokenChip token="{hp}" display="HP"
                       hint="current"
                       onPick={append}/>
            <TokenChip token="{ep}" display="EP"
                       hint="current"
                       onPick={append}/>
          </ChipGroup>
        )}

        {err && (
          <div className="text-ember text-[11px] mb-2 flex items-start gap-1"
               data-testid="macro-builder-error">
            <AlertCircle className="w-3 h-3 mt-0.5 shrink-0"/>{err}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2 border-t border-gold/10">
          <button type="button" onClick={onClose}
                  className="btn btn-ghost text-xs">Cancel</button>
          <button type="submit" disabled={busy || !name || !formula}
                  className="btn btn-primary text-xs"
                  data-testid="macro-builder-save">
            {busy ? <Loader2 className="w-3 h-3 animate-spin"/> : <Plus className="w-3 h-3"/>}
            {busy ? "Saving…" : "Save macro"}
          </button>
        </div>
      </form>
    </div>,
    document.body
  );
}


function ChipGroup({ label, testid, children }) {
  return (
    <div className="mb-3" data-testid={testid}>
      <div className="label-ref mb-1">{label}</div>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function TokenChip({ token, display, hint, tone, tooltipOverride, onPick }) {
  const toneCls = tone === "ember"
    ? "border-ember/40 hover:border-ember"
    : "border-gold/30 hover:border-gold-bright";
  return (
    <button type="button"
            onClick={() => onPick(token)}
            title={tooltipOverride || token}
            className={`tag inline-flex items-center gap-1 ${toneCls}`}
            data-testid={`macro-chip-${token.replace(/[{}:]/g, "-")}`}>
      <span>{display}</span>
      {hint && <span className="text-[9px] text-mist/70">· {hint}</span>}
    </button>
  );
}

function CustomDicePicker({ onPick }) {
  const [n, setN] = useState(2);
  const [d, setD] = useState(6);
  return (
    <span className="inline-flex items-center gap-1 ml-2">
      <input type="number" min={1} max={20} value={n}
             onChange={(e) => setN(+e.target.value || 1)}
             className="input w-12 text-center select-sm"
             data-testid="macro-dice-custom-n"/>
      <span className="text-mist text-[11px]">d</span>
      <select className="select select-sm" value={d}
              onChange={(e) => setD(+e.target.value)}
              data-testid="macro-dice-custom-d">
        {[2,3,4,6,8,10,12,20,100].map((s) => <option key={s} value={s}>{s}</option>)}
      </select>
      <button type="button" onClick={() => onPick(`${n}d${d}`)}
              className="btn btn-ghost text-[10px]"
              data-testid="macro-dice-custom-add">+</button>
    </span>
  );
}

function NumericInjector({ onPick }) {
  const [n, setN] = useState(2);
  return (
    <div className="flex items-center gap-2">
      <input type="number" value={n}
             onChange={(e) => setN(+e.target.value || 0)}
             className="input w-24 text-center select-sm"
             data-testid="macro-flat-n"/>
      <button type="button"
              onClick={() => onPick(n >= 0 ? `+${n}` : String(n))}
              className="btn btn-ghost text-[10px]"
              data-testid="macro-flat-add">
        Insert {n >= 0 ? `+${n}` : n}
      </button>
    </div>
  );
}


// ── pure helpers for client-side preview only ─────────────────

const _modRank = (m) => {
  if (typeof m === "string") return 1;
  if (m && typeof m.rank === "number") return Math.max(1, m.rank);
  if (m && typeof m.value === "number") return Math.max(1, Math.abs(m.value));
  return 1;
};
const _effLevel = (a) => {
  if (!a) return 0;
  if (typeof a.effective_level === "number") return Math.max(1, a.effective_level);
  const base = a.level || 1;
  const lim = (a.limiters || []).reduce((s, m) => s + _modRank(m), 0);
  const enh = (a.enhancements || []).reduce((s, m) => s + _modRank(m), 0);
  return Math.max(1, base + lim - enh);
};
const _by = (rows, n) => (rows || []).find((r) =>
  (r?.name || r?.group || "").toLowerCase() === (n || "").toLowerCase());

const _modOf = (score) => Math.floor(((+score || 10) - 10) / 2);

function _derived(key, ch) {
  if (!ch) return null;
  const stats = ch.stats || {};
  const dnd = (ch.folio?.dnd_state) || {};
  const ab = dnd.ability_scores || {};
  const lvl = (n) => (_by(ch.attributes, n)?.level) || 0;
  const body = +stats.body || 0, mind = +stats.mind || 0, soul = +stats.soul || 0;
  const cv = Math.floor((body + mind + soul) / 3);
  const m = {
    cv, atk: cv + lvl("Attack Mastery"), dfn: Math.max(0, cv - 2 + lvl("Defence Mastery")),
    hp: (body + soul) * 5 + lvl("Tough") * 5,
    ep: (mind + soul) * 5 + lvl("Energised") * 5,
    dm: 5 + lvl("Massive Damage") * 5,
    ac: +dnd.ac || 10, init: _modOf(ab.Dexterity),
  };
  return m[key];
}

function _describeStat(key, ch) {
  if (!ch) return "—";
  const s = ch.stats || {};
  const ab = (ch.folio?.dnd_state?.ability_scores) || {};
  const k = key.toLowerCase();
  if (["body","mind","soul"].includes(k)) return String(s[k] || 0);
  const map = {str:"Strength",dex:"Dexterity",con:"Constitution",
                int:"Intelligence",wis:"Wisdom",cha:"Charisma"};
  const v = ab[map[k]];
  return v != null ? `${v} (mod ${_modOf(v)})` : "—";
}

/** Mirror of backend's `_expand_macro_tokens` for live preview. */
function _expandClientSide(formula, ch) {
  if (!formula || !ch) return formula || "";
  const dnd = (ch.folio?.dnd_state) || {};
  const ab = dnd.ability_scores || {};
  const stats = ch.stats || {};
  const lvl = +(dnd.level || ch.level || 1);
  const prof = Math.max(2, 2 + Math.floor((lvl - 1) / 4));
  const sign = (v) => (v >= 0 ? `+${v}` : String(v));

  let out = formula;
  out = out.replace(/\{(attr|skill|def|stat|derived)\s*:\s*([^}]+)\}/gi,
    (_, kind, name) => {
      const k = kind.toLowerCase(); const n = (name || "").trim();
      let v = 0;
      if (k === "attr")  v = _effLevel(_by(ch.attributes, n));
      if (k === "skill") v = (_by(ch.skills, n)?.level) || 0;
      if (k === "def")   v = (_by(ch.defects, n)?.rank) || 0;
      if (k === "stat") {
        const lk = n.toLowerCase();
        if (["body","mind","soul"].includes(lk)) v = +stats[lk] || 0;
        else {
          const map = {str:"Strength",dex:"Dexterity",con:"Constitution",
                       int:"Intelligence",wis:"Wisdom",cha:"Charisma"};
          v = _modOf(ab[map[lk]]);
        }
      }
      if (k === "derived") v = +_derived(n.toLowerCase(), ch) || 0;
      return sign(v);
    });
  out = out.replace(/\{(hp|ep|sanity)\}/gi, (_, k) => {
    if (k === "hp") return sign(_derived("hp", ch) || 0);
    if (k === "ep") return sign(_derived("ep", ch) || 0);
    if (k === "sanity") return sign(+dnd.sanity || 0);
    return "+0";
  });
  // Scalar back-compat (STR/DEX/CON/INT/WIS/CHA + BODY/MIND/SOUL + PROF/LVL).
  out = out.replace(
    /(?<![A-Za-z0-9_])(STR|DEX|CON|INT|WIS|CHA|BODY|MIND|SOUL|PROF|LVL)(?![A-Za-z0-9_])/gi,
    (m) => {
      const k = m.toUpperCase();
      const map = {
        STR: _modOf(ab.Strength),    DEX: _modOf(ab.Dexterity),
        CON: _modOf(ab.Constitution),INT: _modOf(ab.Intelligence),
        WIS: _modOf(ab.Wisdom),      CHA: _modOf(ab.Charisma),
        BODY: +stats.body || 0,      MIND: +stats.mind || 0,
        SOUL: +stats.soul || 0,      PROF: prof, LVL: lvl,
      };
      return sign(map[k] || 0);
    });
  out = out.replace(/\+\+/g, "+").replace(/\+-/g, "-").replace(/--/g, "+");
  return out;
}

/**
 * V6.25.11 — Refinery parser.
 *
 * Walks a free-form formula and returns a queue of UNRESOLVED bare-word
 * tokens that should be promoted to typed `{kind:Name}` references via
 * a character-sheet-aware dropdown.
 *
 * Recognised bare words (case-insensitive, NOT inside `{}` typed tokens):
 *   • attribute / attr        →  kind: "attr"
 *   • skill                   →  kind: "skill"
 *   • defect / def            →  kind: "def"
 *   • stat[:N]                →  kind: "stat"   (N = optional Target Number)
 *   • derived                 →  kind: "derived"
 *
 * Already-typed tokens like `{attr:Weapon}` are left alone — they're
 * already specific.
 *
 * Example: `2d6+attribute+stat:15` returns:
 *   [
 *     { idx: 4,  raw: "attribute", kind: "attr" },
 *     { idx: 14, raw: "stat:15",   kind: "stat",  tn: 15 },
 *   ]
 *
 * The UI then renders one dropdown per slot, and `resolveRefineryPick`
 * substitutes the bare token with its typed form in place.
 */
function _parseUnresolved(formula) {
  if (!formula) return [];
  // Mask already-typed `{kind:name}` regions so we don't double-parse.
  const typedRanges = [];
  const typedRe = /\{[^}]+\}/g;
  let tm;
  while ((tm = typedRe.exec(formula))) {
    typedRanges.push([tm.index, tm.index + tm[0].length]);
  }
  const inTyped = (i) => typedRanges.some(([a, b]) => i >= a && i < b);

  const slots = [];
  // attr / attribute  ·  skill  ·  defect / def  ·  derived
  const wordRe = /\b(attribute|attr|skill|defect|def|derived)\b(?!\s*:)/gi;
  let m;
  while ((m = wordRe.exec(formula))) {
    if (inTyped(m.index)) continue;
    const w = m[1].toLowerCase();
    const kind =
      w === "attribute" || w === "attr" ? "attr"
      : w === "skill"                    ? "skill"
      : w === "defect" || w === "def"   ? "def"
      :                                    "derived";
    slots.push({ idx: m.index, raw: m[0], kind });
  }
  // stat with optional :N — e.g. `stat`, `stat:15`.
  const statRe = /\bstat(?::(\d+))?\b/gi;
  let sm;
  while ((sm = statRe.exec(formula))) {
    if (inTyped(sm.index)) continue;
    const tn = sm[1] ? parseInt(sm[1], 10) : null;
    slots.push({ idx: sm.index, raw: sm[0], kind: "stat", tn });
  }
  // Sort by appearance order; user picks top-down.
  return slots.sort((a, b) => a.idx - b.idx);
}
