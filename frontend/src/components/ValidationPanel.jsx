/**
 * ValidationPanel — V6.25.34
 *
 * Live warnings panel embedded on the Character Sheet (and surfaceable
 * from the GM Director Console). Polls `/api/characters/{cid}/validations`
 * and shows duplicate-attribute, over-benchmark stat / attr / defect
 * issues with one-click "Dismiss" — dismissals persist and only re-fire
 * if a new warning of a different signature arises.
 *
 * Weapons / weapon-items are exempt from benchmark caps (Anime 5E rule).
 */
import React, { useEffect, useState, useCallback } from "react";
import { AlertTriangle, X, ShieldOff } from "lucide-react";
import { api } from "../lib/api";

export default function ValidationPanel({ characterId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const reload = useCallback(async () => {
    if (!characterId) return;
    setLoading(true);
    try {
      const r = await api.get(`/characters/${characterId}/validations`);
      setData(r.data);
    } catch (_e) { setData(null); }
    finally { setLoading(false); }
  }, [characterId]);

  useEffect(() => { reload(); }, [reload]);

  const dismiss = async (sig) => {
    try {
      await api.post(`/characters/${characterId}/validations/dismiss`,
                       { signature: sig });
      await reload();
    } catch (_e) { /* swallow */ }
  };

  if (loading && !data) return null;
  if (!data || data.warnings.length === 0) return null;

  return (
    <div className="card-mystic p-4 mt-4 border-l-2 border-arcane/60"
         data-testid="character-validation-panel">
      <div className="flex items-baseline justify-between gap-2 mb-2 flex-wrap">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-arcane"/>
          <span className="label-ref text-arcane">
            Sheet Validation · {data.warnings.length} warning{data.warnings.length === 1 ? "" : "s"}
          </span>
        </div>
        <div className="text-[10px] text-mist/70">
          benchmarks: stat ≤ {data.benchmarks.stat_cap} · attr ≤ {data.benchmarks.attr_cap} · defect rank ≤ {data.benchmarks.defect_rank_cap}
        </div>
      </div>
      <ul className="space-y-1.5">
        {data.warnings.map((w) => (
          <li key={w.signature}
              className="text-[12px] flex items-start gap-2 border border-arcane/15 rounded-sm p-2"
              data-testid={`validation-warning-${w.kind}-${w.target_name}`}>
            <ShieldOff className="w-3 h-3 mt-0.5 text-arcane shrink-0"/>
            <div className="flex-1 min-w-0">
              <div className="text-parchment">{w.message}</div>
              <div className="text-[10px] text-mist/60 mt-0.5">
                kind: {w.kind} · target: {w.target_name}
                {typeof w.level === "number" && ` · L/R ${w.level}/${w.cap}`}
              </div>
            </div>
            <button type="button" onClick={() => dismiss(w.signature)}
                    className="btn btn-ghost text-[10px] shrink-0"
                    data-testid={`validation-dismiss-${w.kind}-${w.target_name}`}
                    title="Dismiss this warning. It returns only if state changes (new duplicate, different over-benchmark level, etc.).">
              <X className="w-3 h-3"/> Dismiss
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
