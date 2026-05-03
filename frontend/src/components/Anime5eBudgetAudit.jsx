/**
 * Anime5eBudgetAudit — V6.21
 *
 * Inline component on the character sheet's Mechanics tab. Renders the
 * RAW-correct Discretionary Points (DP) budget (Anime 5E core p.20:
 * 80 + level − 1), broken down into the three spend buckets:
 *
 *   1. Ability Score DP cost    — sum of all 6 ability score values
 *                                  (18 STR costs 18 DP; core p.24).
 *   2. Race DP cost             — per Table 04 (Anime 5E p.28-45).
 *   3. BESM-style point-buy     — Attributes / Enhancements / Defects
 *                                  on the `anime5e_state.point_buys[]`
 *                                  supplement layer.
 *
 * Classes cost 0 DP — features auto-grant per level.
 *
 * GMs / owners get a "Recompute budget" button that calls the existing
 * /api/characters/{cid}/anime5e-recompute-budget endpoint to align the
 * stored budget with the campaign's `anime5e_xp_formula` (raw / flat /
 * curve / tier).
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { AlertTriangle, RefreshCw, CheckCircle, Info } from "lucide-react";

export default function Anime5eBudgetAudit({ characterId, isOwnerOrGm }) {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [showBreakdown, setShowBreakdown] = useState(false);

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
      await refresh();
      window.dispatchEvent(new CustomEvent("tg:budget-recomputed", { detail: r }));
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (!data) return null;
  const sus = data.suspicious_budget;
  const overspent = (data.net_unspent ?? 0) < 0;

  return (
    <div className="card-mystic p-4 mt-4" data-testid="anime5e-budget-audit">
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-2">
        <div>
          <div className="label-ref">Anime 5E Discretionary Points (DP)</div>
          <div className="text-[10px] text-mist italic">
            RAW: 80 DP + 1/level above 1st (Anime 5E core p.20).
            Ability scores cost DP = value; classes 0 DP; races per Table 04.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowBreakdown((v) => !v)}
                  className="btn btn-ghost text-[10px] flex items-center gap-1"
                  data-testid="audit-toggle-breakdown">
            <Info className="w-3 h-3"/> {showBreakdown ? "Hide" : "Show"} detail
          </button>
          {isOwnerOrGm && (
            <button onClick={recompute} disabled={busy}
                    className="btn btn-ghost text-[10px] flex items-center gap-1"
                    data-testid="audit-recompute">
              <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`}/>
              Recompute
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <Stat label="Tier" value={data.tier?.name || "?"}
              hint={data.tier?.blurb} testid="audit-tier"/>
        <Stat label="RAW budget" value={data.canonical_raw_dp}
              hint={`Anime 5E core p.20 — 80 + (level − 1) at level ${data.level}`}
              testid="audit-canonical"/>
        <Stat label="Stored budget" value={data.stored_point_budget}
              flag={sus} testid="audit-stored"/>
        <Stat label="Total spent" value={data.total_spent}
              flag={overspent} testid="audit-total-spent"/>
        <Stat label="Ability scores"
              value={`${data.ability_score_cost} DP`}
              hint="Sum of all 6 ability score values (core p.24)."
              testid="audit-ability-cost"/>
        <Stat label="Race cost"
              value={data.race ? `${data.race.dp_cost} (${data.race.name})` : "0 (none)"}
              testid="audit-race-cost"/>
        <Stat label="Attributes / point-buy" value={`${data.point_buy_total} DP`}
              hint="BESM-style genre-flair Attributes & Enhancements."
              testid="audit-spent"/>
        <Stat label="Net unspent" value={data.net_unspent}
              flag={overspent} testid="audit-net-unspent"/>
      </div>

      {showBreakdown && (
        <div className="mt-3 border-t border-gold/15 pt-3 text-[11px]"
             data-testid="audit-ability-breakdown">
          <div className="label-ref mb-1">Ability Score DP breakdown</div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {Object.entries(data.ability_score_breakdown || {}).map(([k, v]) => (
              <div key={k} className="border border-gold/20 rounded-sm p-1.5">
                <div className="text-[9px] uppercase tracking-widest text-mist">
                  {k.slice(0, 3)}
                </div>
                <div className="font-display text-gold-bright">{v}</div>
                <div className="text-[9px] text-mist">{v} DP</div>
              </div>
            ))}
          </div>
          {data.point_buys?.length > 0 && (
            <div className="mt-3">
              <div className="label-ref mb-1">Point-buy breakdown</div>
              <div className="space-y-1">
                {data.point_buys.map((pb, i) => (
                  <div key={i} className="flex justify-between border-b border-gold/10 pb-1">
                    <span className="text-parchment">
                      {pb.name || "?"} ×{pb.level || 1}
                    </span>
                    <span className="text-gold-bright">
                      {(pb.cost_per_level || 0) * (pb.level || 1)} DP
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="mt-3 text-[10px] text-mist italic">
            {data.formula_note}
          </div>
        </div>
      )}

      {overspent ? (
        <div className="mt-2 border-l-2 border-ember bg-ember/10 p-2 text-[11px] text-ember"
             data-testid="audit-overspent">
          <AlertTriangle className="w-3 h-3 inline mr-1"/>
          Character is {Math.abs(data.net_unspent)} DP over budget. Lower an
          ability score, drop a point-buy rank, or have the GM raise the
          budget via the primer (RAW / curve / flat).
        </div>
      ) : sus ? (
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
