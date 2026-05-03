/**
 * Anime5eBudgetAudit — V6.19
 *
 * Inline component on the character sheet's Mechanics tab. Renders the
 * canonical Tier DP, race cost, point-buy spend, and net unspent. Flags
 * stored budgets that exceed 150% of canonical (the V6.4→V6.19 budget
 * formula rebalance).
 *
 * GMs / owners get a "Recompute budget" button that calls the existing
 * /api/characters/{cid}/anime5e-recompute-budget endpoint to align the
 * stored budget with the campaign's `anime5e_xp_formula`.
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { AlertTriangle, RefreshCw, CheckCircle } from "lucide-react";

export default function Anime5eBudgetAudit({ characterId, isOwnerOrGm }) {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/characters/${characterId}/anime5e/budget-breakdown`);
      setData(data);
    } catch (e) {
      // 404 is expected for non-Anime characters; silently ignore.
      if (e.response?.status !== 404) {
        setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    }
  }, [characterId]);
  useEffect(() => { refresh(); }, [refresh]);

  const recompute = async () => {
    setBusy(true); setErr("");
    try {
      const { data: r } = await api.post(`/characters/${characterId}/anime5e-recompute-budget`);
      // Show transient note then refresh.
      await refresh();
      window.dispatchEvent(new CustomEvent("tg:budget-recomputed", { detail: r }));
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (!data) return null;
  const sus = data.suspicious_budget;
  return (
    <div className="card-mystic p-4 mt-4" data-testid="anime5e-budget-audit">
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-2">
        <div>
          <div className="label-ref">Anime 5E DP / CP Audit</div>
          <div className="text-[10px] text-mist italic">
            Tier-canonical budget vs stored budget (Anime 5E core p.7-8).
          </div>
        </div>
        {isOwnerOrGm && (
          <button onClick={recompute} disabled={busy}
                  className="btn btn-ghost text-[10px] flex items-center gap-1"
                  data-testid="audit-recompute">
            <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`}/>
            Recompute
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <Stat label="Tier" value={data.tier?.name?.split("·")[0]?.trim() || "?"}
              hint={data.tier?.blurb} testid="audit-tier"/>
        <Stat label="Canonical DP" value={data.canonical_tier_dp}
              hint={`Anime 5E core ${data.tier?.name} → ${data.canonical_tier_dp} DP at level ${data.level}`}
              testid="audit-canonical"/>
        <Stat label="Stored budget" value={data.stored_point_budget}
              flag={sus} testid="audit-stored"/>
        <Stat label="Race cost"
              value={data.race ? `${data.race.dp_cost} (${data.race.name})` : "0 (none)"}
              testid="audit-race-cost"/>
        <Stat label="Point-buy spent" value={data.point_buy_total}
              testid="audit-spent"/>
        <Stat label="Net unspent" value={data.net_unspent}
              flag={data.net_unspent < 0} testid="audit-net-unspent"/>
        <Stat label="RAW unspent" value={data.raw_unspent}
              testid="audit-raw-unspent"/>
      </div>

      {sus ? (
        <div className="mt-2 border-l-2 border-ember/60 bg-ember/5 p-2 text-[11px] text-parchment"
             data-testid="audit-warning">
          <AlertTriangle className="w-3 h-3 inline mr-1 text-ember"/>
          {data.advice}
        </div>
      ) : (
        <div className="mt-2 text-[11px] text-mist flex items-center gap-1"
             data-testid="audit-clean">
          <CheckCircle className="w-3 h-3 text-gold-bright"/> {data.advice}
        </div>
      )}
      {err && <div className="text-ember text-xs mt-2" data-testid="audit-error">{err}</div>}
    </div>
  );
}

function Stat({ label, value, hint, flag, testid }) {
  return (
    <div className={`border rounded-sm p-2 ${flag ? "border-ember/40 bg-ember/5" : "border-gold/20"}`}
         title={hint || ""} data-testid={testid}>
      <div className="text-[9px] uppercase tracking-widest text-mist">{label}</div>
      <div className={`font-display ${flag ? "text-ember" : "text-gold-bright"} text-base`}>
        {value}
      </div>
    </div>
  );
}
