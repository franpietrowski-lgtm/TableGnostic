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
export default function EncounterDesigner({ partySize = 4, className = "",
                                              campaignId, systemId = "anime-5e" }) {
  const [level, setLevel] = useState(1);
  const [size, setSize] = useState(partySize || 4);
  const [difficulty, setDifficulty] = useState(systemId === "besm-4e" ? "equal" : "medium");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const isBesm = systemId === "besm-4e";

  const run = async () => {
    setBusy(true); setErr("");
    try {
      let endpoint, qs;
      if (isBesm) {
        if (!campaignId) { setBusy(false); return; }
        qs = new URLSearchParams({
          campaign_id: campaignId, party_size: String(size), difficulty,
        });
        endpoint = `/besm/encounter-budget?${qs.toString()}`;
      } else {
        qs = new URLSearchParams({
          party_level: String(level), party_size: String(size), difficulty,
        });
        endpoint = `/anime5e/encounter-budget?${qs.toString()}`;
      }
      const { data } = await api.get(endpoint);
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
        {!isBesm && (
          <label className="text-[10px]">
            <span className="label-ref text-[9px] block">Level</span>
            <input className="input input-sm text-xs w-full" type="number" min={1} max={20}
                   value={level}
                   onChange={(e) => setLevel(Math.max(1, Math.min(20, +e.target.value || 1)))}
                   data-testid="encounter-designer-level"/>
          </label>
        )}
        <label className="text-[10px]">
          <span className="label-ref text-[9px] block">Party {size > 6 ? "⚠" : ""}</span>
          <input className="input input-sm text-xs w-full" type="number" min={1} max={12}
                 value={size}
                 onChange={(e) => setSize(Math.max(1, Math.min(12, +e.target.value || 1)))}
                 title={size > 6 ? "Soft cap is 6 — larger parties are allowed but encounter math may need GM eyeballing." : ""}
                 data-testid="encounter-designer-size"/>
        </label>
        <label className="text-[10px]">
          <span className="label-ref text-[9px] block">Difficulty</span>
          <select className="select select-sm text-xs w-full" value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  data-testid="encounter-designer-difficulty">
            {isBesm ? (
              <>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="equal">Equal</option>
                <option value="hard">Hard</option>
                <option value="deadly">Deadly</option>
              </>
            ) : (
              <>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
                <option value="deadly">Deadly</option>
              </>
            )}
          </select>
        </label>
      </div>
      {err && <div className="text-ember text-[10px] mb-2">{err}</div>}
      {result && !isBesm && (
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
      {result && isBesm && (
        <>
          <div className="flex items-baseline justify-between text-[11px] font-ui mb-2">
            <span className="text-mist">CP budget</span>
            <span className="text-gold-bright font-display text-lg"
                  data-testid="encounter-designer-budget">
              {result.encounter_budget} CP
            </span>
            <span className="text-[10px] text-mist">
              ({result.pc_cp}/PC · {result.power_level})
            </span>
          </div>
          <div className="border-t border-gold/15 pt-2">
            <div className="label-ref text-[9px] mb-1">Threat-tier slots (BESM 4E p.119+)</div>
            <div className="space-y-1">
              {(result.threat_slots || []).map((s) => (
                <div key={s.tier}
                     className="text-[11px] border-l-2 border-gold/30 pl-2 py-0.5"
                     data-testid={`besm-threat-${s.tier}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-parchment font-ui capitalize">
                      {s.max_count}× {s.tier}
                    </span>
                    <span className="text-[10px] text-mist">
                      {s.foe_cp} CP/foe · {s.budget_fit_pct}% of budget
                    </span>
                  </div>
                  <div className="text-[10px] text-mist italic">{s.note}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
      {result?.warnings?.length > 0 && (
        <div className="text-[10px] text-ember mt-2 italic"
             data-testid="encounter-designer-warnings">
          {result.warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
        </div>
      )}

      {/* V6.25.53 — Cosmological Tension picker. Lets the GM compare
          an attacker's Face (Aurae or Mortiscura) against the
          defender's Face and read out a ready-to-apply edge / advantage
          / obstacle modifier for the next roll. Lazy-loaded so non-
          Evereantha campaigns don't pay the network cost. */}
      <CosmologicalTension/>
    </div>
  );
}

function CosmologicalTension() {
  const [data, setData] = useState(null);
  const [attackerId, setAttackerId] = useState("");
  const [defenderId, setDefenderId] = useState("");
  const [opp, setOpp] = useState(null);

  useEffect(() => {
    api.get("/cosmology/evereantha")
      .then((r) => setData(r.data))
      .catch(() => setData({ aurae: [], mortiscura: [] }));
  }, []);

  useEffect(() => {
    if (!attackerId || !defenderId) { setOpp(null); return; }
    api.get(`/cosmology/evereantha/opposition?attacker=${attackerId}&defender=${defenderId}`)
      .then((r) => setOpp(r.data))
      .catch(() => setOpp(null));
  }, [attackerId, defenderId]);

  if (!data) return null;
  const allFaces = [
    ...(data.aurae || []).map((f) => ({ ...f, side: "aurae" })),
    ...(data.mortiscura || []).map((f) => ({ ...f, side: "mortiscura" })),
  ];
  if (allFaces.length === 0) return null;

  const magClass = {
    advantage: "border-emerald-400/60 bg-emerald-900/20 text-emerald-200",
    edge:      "border-amber-400/60 bg-amber-900/20 text-amber-200",
    neutral:   "border-mist/30 bg-mist/5 text-mist",
    obstacle:  "border-rose-400/60 bg-rose-900/20 text-rose-200",
  }[opp?.magnitude || "neutral"];

  const FaceOption = ({ f }) => (
    <option value={f.id}>
      {f.side === "aurae" ? "☼ " : "☾ "}{f.name} · {f.axis}
    </option>
  );

  return (
    <div className="mt-3 border-t border-amber-700/30 pt-3"
         data-testid="cosmological-tension">
      <div className="label-ref text-amber-300 text-[10px] uppercase tracking-widest mb-2">
        Cosmological Tension · Evereantha
      </div>
      <div className="grid grid-cols-2 gap-2 mb-2">
        <div>
          <label className="text-[9px] uppercase tracking-widest text-mist/60 block mb-0.5">
            Attacker Face
          </label>
          <select value={attackerId}
                  onChange={(e) => setAttackerId(e.target.value)}
                  className="input text-xs w-full"
                  data-testid="cosmology-attacker">
            <option value="">— select —</option>
            <optgroup label="Aurae">
              {(data.aurae || []).map((f) => <FaceOption key={f.id} f={{ ...f, side: "aurae" }}/>)}
            </optgroup>
            <optgroup label="Mortiscura">
              {(data.mortiscura || []).map((f) => <FaceOption key={f.id} f={{ ...f, side: "mortiscura" }}/>)}
            </optgroup>
          </select>
        </div>
        <div>
          <label className="text-[9px] uppercase tracking-widest text-mist/60 block mb-0.5">
            Defender Face
          </label>
          <select value={defenderId}
                  onChange={(e) => setDefenderId(e.target.value)}
                  className="input text-xs w-full"
                  data-testid="cosmology-defender">
            <option value="">— select —</option>
            <optgroup label="Aurae">
              {(data.aurae || []).map((f) => <FaceOption key={f.id} f={{ ...f, side: "aurae" }}/>)}
            </optgroup>
            <optgroup label="Mortiscura">
              {(data.mortiscura || []).map((f) => <FaceOption key={f.id} f={{ ...f, side: "mortiscura" }}/>)}
            </optgroup>
          </select>
        </div>
      </div>

      {opp && (
        <div className={`border rounded-sm p-2 ${magClass}`}
             data-testid="cosmology-tension-result">
          <div className="flex items-center justify-between text-[10px] uppercase tracking-widest mb-1">
            <span>Magnitude</span>
            <span className="font-display text-sm tracking-normal" data-testid="cosmology-tension-magnitude">
              {opp.magnitude}
            </span>
          </div>
          <div className="text-[11px] italic leading-snug">{opp.note}</div>
          <div className="text-[9px] text-mist/60 mt-1">
            {data.magnitude_legend?.[opp.magnitude]}
          </div>
        </div>
      )}
    </div>
  );
}
