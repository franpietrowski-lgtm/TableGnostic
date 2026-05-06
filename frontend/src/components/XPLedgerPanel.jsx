/**
 * XPLedgerPanel — campaign-level XP audit feed.
 *
 * GM-only modal that pulls `/api/campaigns/{cid}/xp/ledger` and shows:
 *   - per-character totals (awarded / unspent / converted)
 *   - reverse-chrono audit feed of every xp_log entry across the campaign
 *
 * Opens from the Atelier header button (data-testid='xp-ledger-btn').
 * Read-only; no edits from this surface.
 */
import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { X, ScrollText, Check } from "lucide-react";

const SOURCE_LABEL = {
  gm_award: "GM award",
  session_baseline: "Session",
  engagement_bonus: "Bonus",
  milestone: "Milestone",
  correction: "Correction",
  convert: "→ CP",
};

export default function XPLedgerPanel({ campaignId, onClose }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [filter, setFilter] = useState("");  // character_id filter

  useEffect(() => {
    if (!campaignId) return;
    api.get(`/campaigns/${campaignId}/xp/ledger`)
      .then((r) => setData(r.data))
      .catch((e) => setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message));
  }, [campaignId]);

  const entries = data ? (filter
    ? data.entries.filter((e) => e.character_id === filter)
    : data.entries) : [];

  return (
    <div className="fixed inset-0 z-40 bg-void/90 backdrop-blur-sm flex items-start justify-center p-3 md:p-6 overflow-auto"
         data-testid="xp-ledger-overlay"
         onClick={(e) => { if (e.target === e.currentTarget) onClose && onClose(); }}>
      <div className="w-full max-w-5xl card-mystic p-5 mt-10">
        <div className="flex items-baseline justify-between mb-3">
          <div>
            <div className="label-ref flex items-center gap-2">
              <ScrollText className="w-3 h-3"/> Campaign XP · Ledger
            </div>
            <div className="text-[11px] text-mist/70 italic mt-1">
              {data?.campaign_name || ""} — every xp_log entry across all characters, reverse-chrono.
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost p-2" data-testid="xp-ledger-close">
            <X className="w-4 h-4"/>
          </button>
        </div>

        {err && <div className="text-ember text-sm mb-3">{err}</div>}
        {!data && !err && <div className="text-mist italic">Tallying the ledger…</div>}

        {data && (
          <>
            {/* Campaign totals */}
            <div className="grid grid-cols-3 gap-3 mb-4" data-testid="xp-ledger-totals">
              <Tot label="Awarded" v={data.totals.awarded.toFixed(2)}/>
              <Tot label="Unspent" v={data.totals.unspent.toFixed(2)}/>
              <Tot label="Converted → CP" v={data.totals.converted.toFixed(2)}/>
            </div>

            {/* Per-character summary strip */}
            <div className="flex flex-wrap gap-2 mb-4" data-testid="xp-ledger-characters">
              <button onClick={() => setFilter("")}
                      className={`tag ${filter === "" ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                      data-testid="xp-ledger-filter-all">
                All · {data.characters.length}
              </button>
              {data.characters.map((c) => (
                <button key={c.id} onClick={() => setFilter(filter === c.id ? "" : c.id)}
                        className={`tag flex items-center gap-1.5 ${filter === c.id ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                        data-testid={`xp-ledger-filter-${c.id}`}
                        title={`Awarded ${c.xp_total} · Unspent ${c.xp_unspent} · Converted ${c.xp_converted}`}>
                  {c.token_color && (
                    <span className="inline-block w-2 h-2 rounded-full"
                          style={{ backgroundColor: c.token_color }}/>
                  )}
                  <span>{c.name}</span>
                  <span className="text-mist/70 text-[9px] tabular-nums">
                    {c.xp_unspent.toFixed(1)} / {c.xp_total.toFixed(1)}
                  </span>
                </button>
              ))}
            </div>

            {/* Audit feed
                V6.25.6 mobile sweep — full table at sm+ widths;
                stacked-card mode below 640px so the 8-col layout
                doesn't horizontal-scroll on phones. */}
            {entries.length === 0 ? (
              <div className="text-mist italic text-xs">
                No XP has been awarded in this campaign yet.
              </div>
            ) : (
              <>
                {/* Stacked-card mode (mobile only) */}
                <div className="sm:hidden space-y-2" data-testid="xp-ledger-cards">
                  {entries.map((e) => {
                    const delta = e.amount || 0;
                    return (
                      <div key={e.id}
                           className="border border-gold/15 rounded-sm p-3 bg-void/30"
                           data-testid={`xp-ledger-card-${e.id}`}>
                        <div className="flex items-baseline justify-between gap-2 mb-1">
                          <div className="font-display text-parchment leading-tight">
                            {e.character_name}
                            {e.owner_name && (
                              <span className="text-mist/60 text-[10px] ml-1 font-body">({e.owner_name})</span>
                            )}
                          </div>
                          <div className={`text-right font-display tabular-nums text-lg ${delta < 0 ? "text-ember" : "text-gold"}`}>
                            {delta >= 0 ? "+" : ""}{delta.toFixed(2)}
                          </div>
                        </div>
                        <div className="text-[11px] text-parchment/85 leading-snug">{e.reason}</div>
                        <div className="text-[10px] text-mist mt-1 flex justify-between">
                          <span>Base {e.base != null ? e.base.toFixed(2) : "—"} · Bonus {e.bonus != null ? e.bonus.toFixed(2) : "—"}</span>
                          <span>{(e.awarded_at || "").replace("T", " ").slice(0, 16)}</span>
                        </div>
                        <div className="text-[9px] text-mist/60 uppercase tracking-widest mt-0.5 font-ui">
                          {SOURCE_LABEL[e.source] || e.source}{e.by_gm_name ? ` · by ${e.by_gm_name}` : ""}
                          {e.converted_to_points != null && <span className="text-arcane-light ml-1">→{e.converted_to_points} CP</span>}
                        </div>
                      </div>
                    );
                  })}
                </div>
                {/* Full table (sm and up) */}
                <table className="w-full text-sm hidden sm:table" data-testid="xp-ledger-table">
                <thead className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
                  <tr className="border-b border-gold/15">
                    <th className="text-left py-2">When</th>
                    <th className="text-left py-2">Character</th>
                    <th className="text-right py-2">Base</th>
                    <th className="text-right py-2">Bonus</th>
                    <th className="text-right py-2">Δ</th>
                    <th className="text-left py-2 pl-2">Reason</th>
                    <th className="text-left py-2">Source</th>
                    <th className="text-left py-2">By</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((e) => {
                    const delta = e.amount || 0;
                    return (
                      <tr key={e.id}
                          className="border-b border-gold/5"
                          data-testid={`xp-ledger-entry-${e.id}`}>
                        <td className="py-1.5 text-mist text-[10px] font-ui">
                          {(e.awarded_at || "").replace("T", " ").slice(0, 19)}
                        </td>
                        <td className="py-1.5">
                          <span className="text-parchment">{e.character_name}</span>
                          {e.owner_name && (
                            <span className="text-mist/60 text-[10px] ml-1">({e.owner_name})</span>
                          )}
                        </td>
                        <td className="text-right tabular-nums text-mist">
                          {e.base != null ? e.base.toFixed(2) : "—"}
                        </td>
                        <td className="text-right tabular-nums text-mist">
                          {e.bonus != null ? e.bonus.toFixed(2) : "—"}
                        </td>
                        <td className={`text-right font-display tabular-nums ${delta < 0 ? "text-ember" : "text-gold"}`}>
                          {delta >= 0 ? "+" : ""}{delta.toFixed(2)}
                          {e.converted_to_points != null && (
                            <span className="text-[9px] text-arcane-light ml-1" title="Converted to Character Points">
                              (→{e.converted_to_points} CP)
                            </span>
                          )}
                        </td>
                        <td className="pl-2 text-parchment/90 max-w-xs truncate" title={e.reason}>
                          {e.reason}
                        </td>
                        <td className="text-[10px] text-mist font-ui uppercase tracking-widest">
                          {SOURCE_LABEL[e.source] || e.source}
                        </td>
                        <td className="text-[10px] text-mist">{e.by_gm_name}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              </>
            )}

            <div className="mt-3 text-[10px] text-mist/60 italic flex items-center gap-1">
              <Check className="w-3 h-3"/> Weights: IC {data.weights.chat_ic} · OOC {data.weights.chat_ooc} ·
              dice {data.weights.dice_macro} · journal {data.weights.journal} · spotlight {data.weights.spotlight}.
              Per-session bonus cap +{data.bonus_cap}. Baseline {data.default_baseline} XP / session.
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Tot({ label, v }) {
  return (
    <div className="border border-gold/15 rounded-sm p-3">
      <div className="text-[10px] font-ui uppercase tracking-widest text-mist">{label}</div>
      <div className="font-display text-2xl text-gold-bright tabular-nums">{v}</div>
    </div>
  );
}
