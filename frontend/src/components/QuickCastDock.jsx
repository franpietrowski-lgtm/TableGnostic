/**
 * QuickCastDock — V6.17
 *
 * Floating bottom-right dock that follows the player across the Session
 * View. Detects the active player's character (via /api/sessions/{id}/seat
 * or sessions.character_id) and surfaces:
 *   - Compact spell-slot row (one chip per slot level)
 *   - Power-bundle invoke buttons
 *   - Long / short rest controls
 *   - "Open full sheet" link
 *
 * Collapsible. Hidden when no character is bound to the session.
 */
import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";
import { ChevronDown, ChevronUp, Zap, RotateCcw, Sparkles, ExternalLink } from "lucide-react";

export default function QuickCastDock({ sessionId, campaignId }) {
  const { user } = useAuth();
  const [characterId, setCharacterId] = useState(null);
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Resolve which character to show: prefer the character the user owns
  // in this campaign with a seat in this session.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data: chars } = await api.get(`/campaigns/${campaignId}/characters`);
        if (cancelled) return;
        // Heuristic: the first PC the current user owns in this campaign.
        const own = (chars || []).find((c) => c.owner_id === user?.id);
        if (own) setCharacterId(own.id);
      } catch { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [campaignId, user?.id]);

  const refresh = useCallback(async () => {
    if (!characterId) return;
    try {
      const { data } = await api.get(`/characters/${characterId}/spell-tracker`);
      setData(data);
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [characterId]);
  useEffect(() => { refresh(); }, [refresh]);

  // Sync with the inline tracker on the sheet.
  useEffect(() => {
    const onChanged = () => refresh();
    window.addEventListener("tg:spell-tracker-changed", onChanged);
    return () => window.removeEventListener("tg:spell-tracker-changed", onChanged);
  }, [refresh]);

  if (!characterId || !data) return null;
  const hasSlots = (data.spell_slots || []).length > 0;
  const hasBundles = (data.power_bundles || []).length > 0;
  if (!hasSlots && !hasBundles && !data.ep_max) return null;

  const cast = async (payload) => {
    setBusy(true); setError("");
    try {
      const { data } = await api.post(
        `/characters/${characterId}/spell-tracker/cast`, payload);
      setData(data);
      window.dispatchEvent(new CustomEvent("tg:spell-tracker-changed"));
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };
  const restore = async (rest_type) => {
    setBusy(true); setError("");
    try {
      const { data } = await api.post(
        `/characters/${characterId}/spell-tracker/restore`, { rest_type });
      setData(data);
      window.dispatchEvent(new CustomEvent("tg:spell-tracker-changed"));
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed bottom-3 right-3 z-40 max-w-[280px] sm:max-w-[320px]"
         data-testid="quick-cast-dock">
      <div className="card-mystic p-2.5 shadow-xl border-gold/40 bg-void/95 backdrop-blur-md">
        <button onClick={() => setOpen(!open)}
                className="w-full flex items-center justify-between gap-2 text-[10px] uppercase tracking-widest text-gold-bright"
                data-testid="quick-cast-toggle">
          <span className="flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5"/> Quick cast
          </span>
          {open ? <ChevronDown className="w-3.5 h-3.5"/> : <ChevronUp className="w-3.5 h-3.5"/>}
        </button>

        {open && (
          <div className="mt-2 space-y-2" data-testid="quick-cast-body">
            {hasSlots && (
              <div>
                <div className="text-[9px] text-mist uppercase tracking-widest mb-1">Slots</div>
                <div className="flex flex-wrap gap-1">
                  {data.spell_slots.map((s) => (
                    <button key={s.slot_level}
                            onClick={() => cast({ kind: "slot", slot_level: s.slot_level })}
                            disabled={busy || s.remaining <= 0}
                            className="border border-gold/30 px-1.5 py-0.5 rounded-sm hover:bg-gold/10 disabled:opacity-30 transition-colors text-[10px]"
                            data-testid={`qc-slot-${s.slot_level}`}
                            title={`Cast a level-${s.slot_level} spell`}>
                      <span className="text-mist">L{s.slot_level}</span>{" "}
                      <span className="font-display text-gold-bright">{s.remaining}</span>
                      <span className="text-mist">/{s.max}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {hasBundles && (
              <div>
                <div className="text-[9px] text-mist uppercase tracking-widest mb-1">Bundles</div>
                <div className="space-y-1">
                  {data.power_bundles.map((b) => (
                    <button key={b.name}
                            onClick={() => cast({ kind: "bundle", bundle_name: b.name })}
                            disabled={busy || b.charges_current <= 0}
                            className="w-full text-left border border-arcane/30 px-2 py-1 rounded-sm hover:bg-arcane/10 disabled:opacity-30 transition-colors flex items-center justify-between gap-2"
                            data-testid={`qc-bundle-${b.name}`}>
                      <span className="text-[11px] text-parchment truncate">{b.name}</span>
                      <span className="text-[10px] text-arcane-light">
                        {b.charges_current}/{b.charges_max}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {data.ep_max > 0 && (
              <div>
                <div className="text-[9px] text-mist uppercase tracking-widest mb-1">EP</div>
                <div className="border border-pink-400/30 rounded-sm px-2 py-1 flex items-center justify-between">
                  <span className="font-display text-sm" style={{ color: "#E03A8E" }}>
                    {data.ep_current}/{data.ep_max}
                  </span>
                  <div className="flex items-center gap-1">
                    {[1, 2].map((amt) => (
                      <button key={amt}
                              onClick={() => cast({ kind: "ep", amount: amt })}
                              disabled={busy || data.ep_current < amt}
                              className="text-[10px] text-pink-400 hover:text-pink-300 disabled:opacity-30"
                              data-testid={`qc-ep-${amt}`}>
                        −{amt}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between gap-1 pt-1 border-t border-gold/15">
              <button onClick={() => restore("short")} disabled={busy}
                      className="text-[10px] text-mist hover:text-gold flex items-center gap-1"
                      data-testid="qc-short-rest">
                <RotateCcw className="w-3 h-3"/> Short
              </button>
              <button onClick={() => restore("long")} disabled={busy}
                      className="text-[10px] text-gold-bright hover:text-gold flex items-center gap-1"
                      data-testid="qc-long-rest">
                <RotateCcw className="w-3 h-3"/> Long
              </button>
              <Link to={`/app/characters/${characterId}`}
                    className="text-[10px] text-mist hover:text-gold flex items-center gap-1"
                    data-testid="qc-open-sheet">
                <ExternalLink className="w-3 h-3"/> Sheet
              </Link>
            </div>

            {error && <div className="text-ember text-[10px]" data-testid="qc-error">{error}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
