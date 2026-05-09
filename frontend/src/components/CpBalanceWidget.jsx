/**
 * CpBalanceWidget — V6.25.27
 *
 * BESM 4E + Anime 5E CP/DP bank.
 *
 * Single source of truth, finally aligned with the Rules Audit:
 *   • BESM 4E  → `GET /api/characters/{cid}/validate` returns
 *                `breakdown.total_spent` (the same number the GM
 *                approval audit shows). Total = `total_points` from
 *                the player primer; once the character is GM-approved,
 *                every subsequently-earned XP rolls into Total via
 *                `character.xp_total`. Remaining doubles as the live
 *                XP-bank the player submits spends from.
 *   • Anime 5E → `GET /api/characters/{cid}/anime5e/budget-breakdown`.
 *
 * V6.25.27 — moved out of the read-only CharacterSheet into the
 * CharacterBuilder edit surface (per spec). The sheet's History tab
 * now reads the same `/validate` endpoint, so CP Bank, Rules Audit
 * and History all show identical numbers.
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
        const [bRes, vRes] = await Promise.all([
          api.get(`/characters/${cid}/anime5e/budget-breakdown`),
          api.get(`/characters/${cid}/validate`).catch(() => ({ data: {} })),
        ]);
        const data = bRes.data;
        const xpEarned = Number(character?.xp_total || 0);
        const primer = data.canonical_raw_dp || 0;
        const approved = !!vRes.data?.approved_for_play;
        const total = approved ? primer + xpEarned : primer;
        setData({
          total,
          primer,
          xp_earned: xpEarned,
          approved,
          spent: data.total_spent || 0,
          remaining: total - (data.total_spent || 0),
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
        // BESM 4E — Rules Audit endpoint is the canonical spend.
        // p.135 Item half-cost is already applied here.
        const { data: audit } = await api.get(`/characters/${cid}/validate`);
        const xpEarned = Number(character?.xp_total || 0);
        const primer = Number(audit.total_points || character?.total_points || 0);
        // `approved_for_play` is a derived flag on the validate response —
        // canonical for "the GM has signed off, XP now flows into Total".
        const approved = !!audit.approved_for_play;
        // Per spec: pre-approval Total = primer; post-approval Total =
        // primer + xp_total (the XP ledger feeds the bank).
        const total = approved ? primer + xpEarned : primer;
        const spent = Number(audit.breakdown?.total_spent ?? 0);
        setData({
          total,
          primer,
          xp_earned: xpEarned,
          approved,
          spent,
          remaining: total - spent,
          unit: "CP",
          system: "besm-4e",
          formula: character?.power_level || "—",
          breakdown: {
            stats: audit.breakdown?.stat_total,
            attrs: audit.breakdown?.attribute_total,
            skills: audit.breakdown?.skill_total,
            defects: -Math.abs(audit.breakdown?.defect_refund || 0),
            packs: (audit.breakdown?.power_pack_total || 0)
                    + (audit.breakdown?.power_bundle_total || 0),
          },
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
          {data.approved && data.xp_earned > 0 && (
            <span className="text-arcane-light/80 normal-case tracking-normal text-[10px] ml-1"
                  data-testid="cp-balance-xp-bonus"
                  title="XP earned post-approval rolls into Total via the XP ledger.">
              · primer {data.primer} + ledger {data.xp_earned}
            </span>
          )}
          {!data.approved && (
            <span className="text-mist/60 normal-case tracking-normal text-[10px] ml-1"
                  data-testid="cp-balance-pre-approval"
                  title="XP ledger feeds Total once the GM approves this character.">
              · pre-approval (primer)
            </span>
          )}
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
        {isBesm && (
          <>
            {data.breakdown.stats > 0 && <span>stats {data.breakdown.stats}</span>}
            {data.breakdown.attrs > 0 && <span>attrs {data.breakdown.attrs}</span>}
            {data.breakdown.skills > 0 && <span>skills {data.breakdown.skills}</span>}
            {data.breakdown.defects < 0 && (
              <span className="text-arcane-light/80">defects {data.breakdown.defects}</span>
            )}
            {data.breakdown.packs > 0 && <span>packs {data.breakdown.packs}</span>}
          </>
        )}
        {err && (
          <span className="text-ember"
                data-testid="cp-balance-error">{err}</span>
        )}
      </div>
    </div>
  );
}
