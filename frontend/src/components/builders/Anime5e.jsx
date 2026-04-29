/**
 * Anime 5E — hybrid character builder.
 *
 * Anime 5E is a Tri-Stat OGL release that grafts the BESM point-buy engine
 * onto a 5E d20 chassis. It uses 5E ability scores AND lets you buy
 * Tri-Stat attributes / skills / defects on top with a point budget.
 *
 * Implementation:
 *  - `Anime5eBuilder` reuses `Dnd5eBuilder` as the d20 chassis (mapping
 *    Anime 5E's `heritages`/`races` shape into the 5E expected fields)
 *    and passes the Anime 5E ref through `hybridSupplement` so the
 *    Tri-Stat point-buy card renders below the d20 sheet.
 *  - `Anime5eHybridSupplement` is the point-buy card itself; it lives
 *    here (not in Dnd5e.jsx) so the conceptual ownership stays clean —
 *    Dnd5e.jsx imports it for the optional render path.
 *
 * Persists into `folio.dnd_state` (5E half) AND `folio.anime5e_state`
 * (Tri-Stat half).
 */
import React from "react";
import { X } from "lucide-react";
import { Dnd5eBuilder } from "./Dnd5e";

export function Anime5eBuilder({ campaign, ref_, charId }) {
  // Build a 5E-shape ref from the Anime 5E hybrid response. The Anime 5E
  // reference DOES expose `classes`, `heritages`/`races`, `skills`, etc.
  // but its abilities default to Body/Mind/Soul. For the D&D-shape sheet we
  // upgrade abilities to the D&D 6 + map back when point-buy is shown.
  const dndRef = {
    ...ref_,
    classes: ref_.classes || [],
    races: ref_.heritages || ref_.races || [],
    abilities: ref_.abilities || [
      { name: "Strength", abbr: "STR" }, { name: "Dexterity", abbr: "DEX" },
      { name: "Constitution", abbr: "CON" }, { name: "Intelligence", abbr: "INT" },
      { name: "Wisdom", abbr: "WIS" }, { name: "Charisma", abbr: "CHA" },
    ],
    skills: ref_.skills?.length ? ref_.skills : [],
  };
  return (
    <Dnd5eBuilder campaign={campaign} ref_={dndRef} charId={charId}
                  hybridSupplement={ref_}/>
  );
}


/**
 * Anime5eHybridSupplement — Tri-Stat point-buy layer for Anime 5E.
 * The top sheet uses 5E mechanics (class/level/abilities/saves/skills),
 * and this card lets the player spend a separate Tri-Stat point budget
 * on Tri-Stat Attributes (e.g. Combat Mastery, Heightened Senses, Tough,
 * Personal Gear) for genre-flavoured powers that don't fit the 5E class.
 *
 * Persists into `folio.anime5e_state` alongside `folio.dnd_state`.
 */
export function Anime5eHybridSupplement({ ch, setCh, ref_ }) {
  const state = ch.folio?.anime5e_state || {
    point_budget: 50, point_buys: [],
  };
  const setState = (patch) => setCh({ ...ch,
    folio: { ...(ch.folio || {}),
              anime5e_state: { ...state, ...patch } } });
  const buys = state.point_buys || [];
  const totalSpent = buys.reduce(
    (sum, b) => sum + ((b.cost_per_level || 0) * (b.level || 1)), 0);
  const remaining = (state.point_budget || 0) - totalSpent;

  const addAttribute = (name) => {
    const opt = (ref_.point_buy_attributes || []).find((a) => a.name === name);
    if (!opt) return;
    setState({ point_buys: [...buys, {
      name: opt.name, cost_per_level: opt.cost_per_level,
      level: 1, blurb_role: opt.blurb_role,
    }] });
  };
  const setBuy = (i, patch) => {
    const next = buys.slice();
    next[i] = { ...next[i], ...patch };
    setState({ point_buys: next });
  };
  const removeBuy = (i) => setState({ point_buys: buys.filter((_, j) => j !== i) });

  return (
    <div className="card-mystic p-5 mt-4 border-pink-400/30"
         style={{ borderLeftWidth: 3, borderLeftColor: "#E03A8E" }}
         data-testid="anime5e-hybrid-supplement">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <h3 className="h-arcane text-sm">
            Tri-Stat Supplement
            <span className="text-[9px] text-mist ml-2 uppercase tracking-widest">Anime 5E hybrid</span>
          </h3>
          <div className="text-[11px] text-mist/80 italic">
            Point-buy attributes layered on top of your d20 sheet — for
            genre powers, custom gear, and signature techniques the 5E
            class doesn't cover.
          </div>
        </div>
        <div className="text-right">
          <div className="label-ref">Point Budget</div>
          <div className="font-display text-2xl text-gold-bright">
            <span className={remaining < 0 ? "text-ember" : ""}>{remaining}</span>
            <span className="text-mist text-sm"> / {state.point_budget}</span>
          </div>
          <div className="text-[10px] text-mist">spent {totalSpent}</div>
        </div>
      </div>

      <div className="mt-3 grid sm:grid-cols-2 gap-2">
        <input className="input" type="number" min={0}
               placeholder="Point budget (50)"
               value={state.point_budget}
               onChange={(e) => setState({ point_budget: Math.max(0, +e.target.value || 0) })}
               data-testid="anime5e-point-budget"/>
        <select className="select"
                onChange={(e) => { if (e.target.value) { addAttribute(e.target.value); e.target.value = ""; } }}
                data-testid="anime5e-add-attribute">
          <option value="">+ Add Tri-Stat Attribute…</option>
          {(ref_.point_buy_attributes || []).map((a) => (
            <option key={a.name} value={a.name}>
              {a.name} ({a.cost_per_level} pts/lvl) — {a.blurb_role}
            </option>
          ))}
        </select>
      </div>

      {buys.length === 0 ? (
        <div className="text-mist italic text-xs mt-3">
          Pick a Tri-Stat Attribute above to add a point-buy power.
        </div>
      ) : (
        <div className="mt-3 space-y-2">
          {buys.map((b, i) => (
            <div key={i}
                 className="border border-gold/15 rounded-sm p-2.5 flex items-center gap-2 flex-wrap"
                 data-testid={`anime5e-buy-${i}`}>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-parchment font-ui">
                  <b>{b.name}</b>
                  <span className="text-[10px] text-mist ml-2">{b.cost_per_level} pts/lvl</span>
                </div>
                <div className="text-[10px] text-mist/70 italic">{b.blurb_role}</div>
              </div>
              <label className="label-ref">LVL</label>
              <input type="number" min={1} max={6} className="input w-16 text-center"
                     value={b.level}
                     onChange={(e) => setBuy(i, { level: Math.max(1, +e.target.value || 1) })}
                     data-testid={`anime5e-buy-level-${i}`}/>
              <span className="font-display text-gold">
                {b.cost_per_level * b.level} pts
              </span>
              <button onClick={() => removeBuy(i)} className="text-ember/70 hover:text-ember"
                      data-testid={`anime5e-buy-remove-${i}`}>
                <X className="w-4 h-4"/>
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="text-[10px] text-mist/60 italic mt-3">
        Anime 5E hybrid mode — the 5E class/level/slot mechanics drive your
        d20 rolls; Tri-Stat point-buy adds genre-flavoured powers.
      </div>
    </div>
  );
}
