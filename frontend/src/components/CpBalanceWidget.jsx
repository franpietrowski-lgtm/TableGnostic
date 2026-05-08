/**
 * CpBalanceWidget — V6.25.22
 *
 * Floating CP / DP balance widget. Pinned to the top of the
 * Character Sheet on BESM 4E and Anime 5E systems ONLY (every
 * other system has its own currency model).
 *
 * Three live stats:
 *   • TOTAL — the assigned discretionary budget.
 *       BESM: `character.total_points` (set in builder).
 *       Anime 5E: 80 + (level − 1) per core p.20.
 *   • SPENT — sum of every Attribute / Defect / Race CP cost.
 *   • REMAINING — TOTAL − SPENT, doubles as the live CP/XP bank
 *       that the existing XP ledger spends from. The ledger and
 *       this widget agree because both pull from the same
 *       `/anime5e/budget-breakdown` (or `/besm/audit`) endpoint.
 *
 * The widget is sticky-positioned (top: 0 with backdrop blur) so
 * it stays visible as the user scrolls through Attributes / Skills
 * / Inventory. It collapses to a 36px pill on mobile.
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Coins, Loader2, RefreshCw, AlertTriangle } from "lucide-react";


export default function CpBalanceWidget({
  character, system, isOwnerOrGm, onRefresh,
}) {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const cid = character?.id;
  const isAnime = system === "anime-5e";
  const isBesm = system === "besm-4e";
  const enabled = !!cid && (isAnime || isBesm);

  const refresh = useCallback(async () => {
    if (!enabled) return;
    setBusy(true); setErr("");
    try {
      if (isAnime) {
        const { data } = await api.get(
          `/characters/${cid}/anime5e/budget-breakdown`);
        setData({
          total: data.canonical_raw_dp || 0,
          spent: data.total_spent || 0,
          remaining: (data.canonical_raw_dp || 0) - (data.total_spent || 0),
          tier: data.tier?.name,
          level: data.level,
          race_cost: data.race_cost,
          race_name: data.race?.name,
          unit: "DP",
          system: "anime-5e",
          formula: "80 + (level − 1)",
          stored: data.stored_point_budget,
          suspicious: data.suspicious_budget,
          breakdown: {
            abilities: data.ability_score_cost,
            race: data.race_cost,
            point_buys: data.point_buy_total,
          },
        });
      } else {
        // BESM 4E — use the character's own total_points + sum buys.
        const total = Number(character?.total_points || 0);
        const buys = (character?.point_buys || character?.folio?.point_buys || []);
        const spent = buys.reduce(
          (s, b) => s + (Number(b.cost_per_level || 0)
                          * Number(b.level || 1)), 0);
        setData({
          total,
          spent,
          remaining: total - spent,
          unit: "CP",
          system: "besm-4e",
          formula: character?.power_level || "—",
          breakdown: { point_buys: spent },
        });
      }
    } catch (e) {
      if (e.response?.status !== 404) {
        setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    } finally { setBusy(false); }
  }, [enabled, cid, isAnime, character]);

  useEffect(() => {
    refresh();
    // V6.25.22 — listen for ledger / builder events so the widget
    // updates the moment a buy is added or XP is spent.
    const refresher = () => refresh();
    window.addEventListener("tg:budget-recomputed", refresher);
    window.addEventListener("tg:character-mutated", refresher);
    return () => {
      window.removeEventListener("tg:budget-recomputed", refresher);
      window.removeEventListener("tg:character-mutated", refresher);
    };
  }, [refresh]);

  if (!enabled || !data) return null;

  const overspent = data.remaining < 0;
  const pct = Math.max(
    0, Math.min(100, Math.round((data.spent / Math.max(1, data.total)) * 100)),
  );

  return (
    <div className="sticky top-0 z-30 -mx-4 px-4 sm:mx-0 sm:px-0
                    backdrop-blur-md bg-void/85 border-b border-gold/15"
         data-testid="cp-balance-widget">
      <div className="flex flex-wrap items-center gap-3 py-2">
        <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-gold/80 font-ui">
          <Coins className="w-3 h-3"/>
          <span data-testid="cp-balance-unit">{data.unit} bank</span>
        </div>

        <div className="flex items-baseline gap-3">
          <div data-testid="cp-balance-total">
            <span className="text-[10px] uppercase tracking-widest text-mist/70">
              Total{" "}
            </span>
            <span className="font-display text-base text-parchment">
              {data.total}
            </span>
          </div>
          <div data-testid="cp-balance-spent">
            <span className="text-[10px] uppercase tracking-widest text-mist/70">
              Spent{" "}
            </span>
            <span className="font-display text-base text-arcane-light">
              {data.spent}
            </span>
          </div>
          <div data-testid="cp-balance-remaining">
            <span className="text-[10px] uppercase tracking-widest text-mist/70">
              Remaining{" "}
            </span>
            <span className={`font-display text-lg ${overspent
              ? "text-ember" : "text-gold-bright"}`}>
              {data.remaining}
            </span>
          </div>
        </div>

        {/* Spend progress bar (centre-flexed when room permits). */}
        <div className="flex-1 min-w-[120px] h-1.5 rounded-full overflow-hidden
                        bg-void/80 border border-gold/10"
             data-testid="cp-balance-progress">
          <div className={overspent ? "bg-ember" : "bg-gold-bright"}
               style={{ width: `${overspent ? 100 : pct}%`,
                         height: "100%", transition: "width 220ms ease-out" }}/>
        </div>

        {/* Right-aligned context + refresh. */}
        <div className="flex items-center gap-2 text-[10px] text-mist/80 font-ui">
          {data.tier && (
            <span data-testid="cp-balance-tier">
              Tier <span className="text-gold-bright">{data.tier}</span>
              {data.level && <> · L{data.level}</>}
            </span>
          )}
          {!data.tier && data.formula && (
            <span data-testid="cp-balance-formula">{data.formula}</span>
          )}
          {data.suspicious && (
            <span className="text-ember flex items-center gap-1"
                  title="Stored budget diverges from RAW formula"
                  data-testid="cp-balance-warning">
              <AlertTriangle className="w-3 h-3"/> drift
            </span>
          )}
          {overspent && (
            <span className="text-ember flex items-center gap-1"
                  data-testid="cp-balance-overspent">
              <AlertTriangle className="w-3 h-3"/> overspent
            </span>
          )}
          <button onClick={refresh} disabled={busy}
                  className="touch-target text-mist/70 hover:text-gold-bright"
                  data-testid="cp-balance-refresh"
                  title="Recompute from the ledger">
            {busy ? <Loader2 className="w-3 h-3 animate-spin"/>
                  : <RefreshCw className="w-3 h-3"/>}
          </button>
        </div>
      </div>

      {/* Breakdown row (subtle, mobile collapses below). */}
      <div className="text-[10px] text-mist/70 italic pb-1.5 flex flex-wrap gap-x-3 gap-y-0.5"
           data-testid="cp-balance-breakdown">
        {isAnime && (
          <>
            {data.breakdown.abilities > 0 && (
              <span>abilities {data.breakdown.abilities}</span>
            )}
            {data.breakdown.race > 0 && (
              <span>
                race {data.breakdown.race}
                {data.race_name && <> ({data.race_name})</>}
              </span>
            )}
            {data.breakdown.point_buys > 0 && (
              <span>attributes {data.breakdown.point_buys}</span>
            )}
          </>
        )}
        {isBesm && data.breakdown.point_buys > 0 && (
          <span>attributes {data.breakdown.point_buys}</span>
        )}
        {err && (
          <span className="text-ember"
                data-testid="cp-balance-error">{err}</span>
        )}
      </div>
    </div>
  );
}
