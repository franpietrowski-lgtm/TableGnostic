import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Activity, RefreshCw } from "lucide-react";

/**
 * CharacterStatusRings — V6.10 sheet-side mirror of the live battlemap
 * status effects. Reads /api/characters/{cid}/effects and renders any
 * currently-active conditions targeting this character as coloured rings.
 *
 * Updates: refresh button + 30s polling so off-session viewing reflects
 * recent GM-applied conditions (no WebSocket needed at the sheet level).
 */
export default function CharacterStatusRings({ characterId }) {
  const [effects, setEffects] = useState([]);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setBusy(true);
    try {
      const { data } = await api.get(`/characters/${characterId}/effects`);
      setEffects(data || []);
    } catch (_) { /* silent — sheet still renders */ }
    finally { setBusy(false); }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [characterId]);

  if (effects.length === 0) return null;

  return (
    <div className="card-mystic p-4 mt-3 border-l-4"
         style={{ borderLeftColor: "#E03A8E" }}
         data-testid="character-status-rings">
      <div className="flex items-baseline justify-between mb-2 gap-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Activity className="w-4 h-4"/> Live status conditions
          </div>
          <div className="text-[10px] text-mist italic">
            Mirrored from the active battlemap. {effects.length} active effect{effects.length === 1 ? "" : "s"}.
          </div>
        </div>
        <button onClick={load} className="btn btn-ghost text-[10px]"
                disabled={busy}
                data-testid="character-status-refresh">
          <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`}/> Refresh
        </button>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {effects.map((ef) => (
          <span key={ef.id}
                className="tag border-ember/50 text-ember inline-flex items-center gap-1 text-[10px]"
                title={`${ef.note || ef.name} · ${ef.duration_rounds} round${ef.duration_rounds === 1 ? "" : "s"} · applied by ${ef.applied_by || "GM"}`}
                data-testid={`character-status-effect-${ef.id}`}>
            {ef.name}
            {ef.duration_rounds > 1 && (
              <span className="text-[9px] opacity-70">· {ef.duration_rounds}r</span>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
