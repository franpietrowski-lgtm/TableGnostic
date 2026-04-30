/**
 * Anime5eHybridSupplement — BESM-style point-buy layer for Anime 5E.
 *
 * Lives in its own file so both Dnd5e.jsx (which embeds it as the
 * optional hybrid card) and Anime5e.jsx (which composes the full
 * builder) can import it without creating a circular ESM cycle.
 *
 * IMPORTANT — Anime 5E rules clarification (from the official
 * Anime 5E hybrid release):
 *   • Anime 5E is D&D 5E with a BESM-style point-buy LAYER on top.
 *   • It is NOT Tri-Stat. Body / Mind / Soul ability scores are
 *     absent. The d20 chassis runs class, level, hit dice, AC, and
 *     saves exactly as in 5E.
 *   • The point-buy layer is OPTIONAL flavour — it lets a player
 *     spend a separate budget on signature genre powers (Combat
 *     Mastery, Heightened Senses, Personal Gear, Custom Technique)
 *     for shōnen colour the 5E class doesn't quite cover.
 *   • The port is one-way: D&D SRD races, classes, feats, and
 *     backgrounds import directly into Anime 5E. Anime 5E content
 *     does NOT port back to a strict-5E table.
 *
 * Persists into `folio.anime5e_state` alongside `folio.dnd_state`.
 */
import React from "react";
import { X } from "lucide-react";

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
            BESM Point-Buy Layer
            <span className="text-[9px] text-mist ml-2 uppercase tracking-widest">Anime 5E hybrid</span>
          </h3>
          <div className="text-[11px] text-mist/80 italic">
            Optional BESM-flavoured point-buy on top of the standard
            5E sheet. Spend a budget on signature genre powers (Combat
            Mastery, Heightened Senses, Personal Gear, Custom
            Technique). The d20 class / level / saves / skills above
            run normally — this layer is pure flavour customisation.
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
          <option value="">+ Add BESM-style Attribute…</option>
          {(ref_.point_buy_attributes || []).map((a) => (
            <option key={a.name} value={a.name}>
              {a.name} ({a.cost_per_level} pts/lvl) — {a.blurb_role}
            </option>
          ))}
        </select>
      </div>

      {buys.length === 0 ? (
        <div className="text-mist italic text-xs mt-3">
          Pick a BESM-style attribute above to add a point-buy power.
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
        Anime 5E hybrid mode — the standard 5E class, level, hit dice,
        AC, saves, and skills above drive your d20 rolls. This BESM
        point-buy layer adds genre-flavoured powers and is one-way
        compatible (5E content imports here; Anime 5E content does NOT
        port back to a strict-5E table).
      </div>
    </div>
  );
}
