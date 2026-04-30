import React, { useState, useEffect } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Swords, Skull, RefreshCw } from "lucide-react";

/**
 * EncounterDesigner — V6.6 panel surfaced in Session View for
 * Anime 5E / D&D 5E campaigns. GMs enter party level + size + target
 * difficulty; we hit /api/anime5e/encounter-budget and render XP budget
 * + monster-slot suggestions + environmental-hazard budget.
 *
 * Pure math read; no writes. GM uses this as a stat-block-picker nudge,
 * not a hard constraint.
 */
export default function EncounterDesigner({ partySize = 4, className = "" }) {
  const [level, setLevel] = useState(1);
  const [size, setSize] = useState(partySize || 4);
  const [difficulty, setDifficulty] = useState("medium");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true); setErr("");
    try {
      const qs = new URLSearchParams({
        party_level: String(level),
        party_size: String(size),
        difficulty,
      });
      const { data } = await api.get(`/anime5e/encounter-budget?${qs.toString()}`);
      setResult(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  useEffect(() => { run(); /* auto-compute on mount */ }, []); // eslint-disable-line

  return (
    <div className={`card-mystic p-4 ${className}`} data-testid="encounter-designer">
      <div className="flex items-baseline justify-between gap-2 mb-2 flex-wrap">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Swords className="w-3 h-3"/> Encounter Designer
          </div>
          <div className="text-[10px] text-mist italic">
            Anime 5E / D&D 5E XP budgets · DMG p.82 conversion.
          </div>
        </div>
        <button onClick={run} disabled={busy} className="btn btn-ghost text-xs"
                data-testid="encounter-designer-run">
          <RefreshCw className="w-3 h-3"/> Recompute
        </button>
      </div>
      <div className="grid grid-cols-3 gap-2 mb-2">
        <label className="text-[10px]">
          <span className="label-ref text-[9px] block">Level</span>
          <input className="input input-sm text-xs w-full" type="number" min={1} max={20}
                 value={level}
                 onChange={(e) => setLevel(Math.max(1, Math.min(20, +e.target.value || 1)))}
                 data-testid="encounter-designer-level"/>
        </label>
        <label className="text-[10px]">
          <span className="label-ref text-[9px] block">Party</span>
          <input className="input input-sm text-xs w-full" type="number" min={1} max={12}
                 value={size}
                 onChange={(e) => setSize(Math.max(1, Math.min(12, +e.target.value || 1)))}
                 data-testid="encounter-designer-size"/>
        </label>
        <label className="text-[10px]">
          <span className="label-ref text-[9px] block">Difficulty</span>
          <select className="select select-sm text-xs w-full" value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  data-testid="encounter-designer-difficulty">
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
            <option value="deadly">Deadly</option>
          </select>
        </label>
      </div>
      {err && <div className="text-ember text-[10px] mb-2">{err}</div>}
      {result && (
        <>
          <div className="flex items-baseline justify-between text-[11px] font-ui mb-2">
            <span className="text-mist">XP budget</span>
            <span className="text-gold-bright font-display text-lg"
                  data-testid="encounter-designer-budget">
              {result.total_xp_budget} XP
            </span>
            <span className="text-[10px] text-mist">({result.xp_per_pc}/PC)</span>
          </div>
          <div className="border-t border-gold/15 pt-2">
            <div className="label-ref text-[9px] mb-1">Suggested monster slots</div>
            <div className="space-y-1">
              {(result.slot_suggestions || []).map((s) => (
                <div key={s.n_monsters}
                     className="flex items-center justify-between text-[11px] border-l-2 border-gold/30 pl-2"
                     data-testid={`encounter-slot-${s.n_monsters}`}>
                  <span className="text-parchment font-ui">
                    {s.n_monsters}× CR {s.cr}
                  </span>
                  <span className="text-[10px] text-mist">
                    {s.effective_xp} eff XP · {s.budget_fit_pct}% of budget
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-2 text-[11px] flex items-center gap-2 border-t border-gold/15 pt-2"
               data-testid="encounter-hazard-budget">
            <Skull className="w-3 h-3 text-ember"/>
            <span className="text-mist">Hazard budget:</span>
            <span className="text-ember font-ui">{result.environmental_hazard_budget} XP</span>
          </div>
        </>
      )}
    </div>
  );
}
