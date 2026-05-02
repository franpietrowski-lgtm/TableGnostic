/**
 * SpellTracker — V6.17
 *
 * Inline character-sheet widget showing live spell-slot / power-bundle /
 * EP usage with cast/restore controls. Owner & GM may interact; players
 * watching another sheet see read-only.
 *
 * Lives at the top of the spell list section on D&D / Anime 5E sheets.
 * Pulses gold when a slot/charge is consumed (descriptive feedback).
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Sparkles, RotateCcw, Zap } from "lucide-react";

export default function SpellTracker({ characterId, isOwnerOrGm }) {
  const [data, setData] = useState(null);
  const [pulse, setPulse] = useState(""); // testid hint of the last item pulsed
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/characters/${characterId}/spell-tracker`);
      setData(data);
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [characterId]);
  useEffect(() => { refresh(); }, [refresh]);

  // Listen for cross-component cast events from the QuickCastDock so we
  // refresh in lockstep.
  useEffect(() => {
    const onCast = () => refresh();
    window.addEventListener("tg:spell-tracker-changed", onCast);
    return () => window.removeEventListener("tg:spell-tracker-changed", onCast);
  }, [refresh]);

  if (!data) return null;
  const hasSlots = (data.spell_slots || []).length > 0;
  const hasBundles = (data.power_bundles || []).length > 0;
  const hasEp = data.ep_max > 0;
  if (!hasSlots && !hasBundles && !hasEp) return null;

  const cast = async (payload, label) => {
    if (!isOwnerOrGm) {
      setError("Only the owner / GM may cast.");
      return;
    }
    setBusy(true); setError("");
    try {
      const { data } = await api.post(
        `/characters/${characterId}/spell-tracker/cast`, payload);
      setData(data);
      setPulse(label);
      setTimeout(() => setPulse(""), 700);
      window.dispatchEvent(new CustomEvent("tg:spell-tracker-changed"));
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const restore = async (rest_type) => {
    if (!isOwnerOrGm) return;
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
    <div className="card-mystic p-4 mt-4" data-testid="spell-tracker">
      <div className="flex items-baseline justify-between mb-2 flex-wrap gap-2">
        <div>
          <div className="label-ref">Spell &amp; Cooldown Tracker</div>
          <div className="text-[10px] text-mist italic">
            Tap a slot or charge to spend it. Long Rest restores all; Short Rest restores Warlock + per-scene bundles.
          </div>
        </div>
        {isOwnerOrGm && (
          <div className="flex items-center gap-1">
            <button onClick={() => restore("short")}
                    disabled={busy}
                    className="btn btn-ghost text-[10px]"
                    data-testid="spell-tracker-short-rest">
              <RotateCcw className="w-3 h-3"/> Short rest
            </button>
            <button onClick={() => restore("long")}
                    disabled={busy}
                    className="btn btn-primary text-[10px]"
                    data-testid="spell-tracker-long-rest">
              <RotateCcw className="w-3 h-3"/> Long rest
            </button>
          </div>
        )}
      </div>

      {hasSlots && (
        <div className="mt-2" data-testid="tracker-slots">
          <div className="text-[10px] uppercase tracking-widest text-mist mb-1">
            Spell slots {data.warlock_short_rest ? "· Pact (short rest)" : ""}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {data.spell_slots.map((s) => {
              const remaining = s.remaining;
              const id = `slot-${s.slot_level}`;
              const pulsing = pulse === id;
              return (
                <div key={s.slot_level}
                     className={`border rounded-sm px-2 py-1 ${pulsing ? "border-gold bg-gold/30 animate-pulse" : "border-gold/30"}`}
                     data-testid={`tracker-slot-${s.slot_level}`}>
                  <div className="text-[9px] text-mist tracking-widest uppercase">
                    Lv {s.slot_level}
                  </div>
                  <div className="font-display text-base text-gold-bright text-center">
                    {remaining}
                    <span className="text-mist text-[10px]">/{s.max}</span>
                  </div>
                  {isOwnerOrGm && (
                    <button
                      onClick={() => cast({ kind: "slot", slot_level: s.slot_level }, id)}
                      disabled={busy || remaining <= 0}
                      className="text-[9px] uppercase tracking-widest text-gold hover:text-gold-bright disabled:opacity-30 disabled:cursor-not-allowed mt-0.5 block"
                      data-testid={`tracker-cast-slot-${s.slot_level}`}>
                      <Zap className="w-2.5 h-2.5 inline"/> Cast
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {hasBundles && (
        <div className="mt-3" data-testid="tracker-bundles">
          <div className="text-[10px] uppercase tracking-widest text-mist mb-1">
            Power bundles
          </div>
          <div className="space-y-1">
            {data.power_bundles.map((b) => {
              const id = `bundle-${b.name}`;
              const pulsing = pulse === id;
              return (
                <div key={b.name}
                     className={`border ${pulsing ? "border-arcane bg-arcane/20 animate-pulse" : "border-arcane/30"} rounded-sm p-2 flex items-center justify-between gap-2 flex-wrap`}
                     data-testid={`tracker-bundle-${b.name}`}>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-parchment font-ui truncate">{b.name}</div>
                    <div className="text-[10px] text-mist">
                      {b.invocation}
                      {b.cooldown ? ` · ${b.cooldown}` : ""}
                      {b.energy_cost > 0 ? ` · ${b.energy_cost} EP` : ""}
                    </div>
                  </div>
                  <span className="font-display text-arcane-light">
                    {b.charges_current}<span className="text-mist text-xs">/{b.charges_max}</span>
                  </span>
                  {isOwnerOrGm && (
                    <button
                      onClick={() => cast({ kind: "bundle", bundle_name: b.name }, id)}
                      disabled={busy || b.charges_current <= 0}
                      className="btn btn-ghost text-[10px] disabled:opacity-30"
                      data-testid={`tracker-cast-bundle-${b.name}`}>
                      <Sparkles className="w-3 h-3"/> Invoke
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {hasEp && (
        <div className="mt-3" data-testid="tracker-ep">
          <div className="text-[10px] uppercase tracking-widest text-mist mb-1">
            Energy points (Anime 5E)
          </div>
          <div className="border border-pink-400/30 rounded-sm p-2 flex items-center gap-2">
            <span className="font-display text-lg" style={{ color: "#E03A8E" }}>
              {data.ep_current}<span className="text-mist text-xs">/{data.ep_max}</span>
            </span>
            {isOwnerOrGm && (
              <div className="flex items-center gap-1 ml-auto">
                {[1, 2, 5].map((amt) => (
                  <button key={amt}
                          onClick={() => cast({ kind: "ep", amount: amt }, `ep-${amt}`)}
                          disabled={busy || data.ep_current < amt}
                          className="btn btn-ghost text-[10px] disabled:opacity-30"
                          data-testid={`tracker-spend-ep-${amt}`}>
                    −{amt} EP
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {error && <div className="text-ember text-xs mt-2" data-testid="tracker-error">{error}</div>}
    </div>
  );
}
