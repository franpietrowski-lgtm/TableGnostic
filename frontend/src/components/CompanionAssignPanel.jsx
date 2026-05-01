import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Users, Plus, X } from "lucide-react";

/**
 * CompanionAssignPanel — V6.9 GM-only widget on the character sheet.
 *
 * GMs assign extra players as "companion owners" of a character. Those
 * players gain move-token rights on the battlemap (same flow as actual
 * owners) and can view the sheet read-only. Useful for pets/sidekicks,
 * shared NPCs, or guest seats.
 *
 * Props:
 *   - characterId
 *   - campaignId
 *   - companions: List[user_id] currently assigned
 *   - ownerId: actual owner (excluded from the picker)
 *   - onChanged()
 */
export default function CompanionAssignPanel({ characterId, campaignId, companions = [], ownerId, onChanged }) {
  const [members, setMembers] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const { data } = await api.get(`/campaigns/${campaignId}/members`);
        if (!dead) setMembers(data || []);
      } catch (e) {
        if (!dead) setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    })();
    return () => { dead = true; };
  }, [campaignId]);

  const assign = async (playerId) => {
    setBusy(true); setErr("");
    try {
      await api.post(`/characters/${characterId}/companions?player_id=${playerId}`);
      onChanged && onChanged();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || "Assign failed.");
    } finally { setBusy(false); }
  };

  const revoke = async (playerId) => {
    setBusy(true); setErr("");
    try {
      await api.delete(`/characters/${characterId}/companions/${playerId}`);
      onChanged && onChanged();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || "Revoke failed.");
    } finally { setBusy(false); }
  };

  // Filter out the actual owner + already-assigned companions.
  const candidates = members.filter(
    (m) => m.id !== ownerId && !companions.includes(m.id),
  );
  const assigned = members.filter((m) => companions.includes(m.id));

  return (
    <div className="card-mystic p-3 mt-3" data-testid="companion-assign-panel">
      <div className="flex items-baseline justify-between mb-2 gap-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Users className="w-4 h-4"/> Companion seats
          </div>
          <div className="text-[10px] text-mist italic">
            GM-only · assigned players can move this character's token on the battlemap.
          </div>
        </div>
      </div>
      {err && <div className="text-ember text-[11px] mb-2">{err}</div>}
      {assigned.length === 0 && (
        <div className="text-[11px] text-mist italic" data-testid="companion-list-empty">
          No companion seats assigned yet.
        </div>
      )}
      {assigned.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2" data-testid="companion-list">
          {assigned.map((p) => (
            <span key={p.id}
                  className="tag border-arcane/40 text-arcane-light text-[10px] inline-flex items-center gap-1 group"
                  data-testid={`companion-row-${p.id}`}>
              {p.name || p.email}
              <button onClick={() => revoke(p.id)}
                      disabled={busy}
                      className="opacity-60 group-hover:opacity-100 transition"
                      title="Revoke companion seat"
                      data-testid={`companion-revoke-${p.id}`}>
                <X className="w-3 h-3"/>
              </button>
            </span>
          ))}
        </div>
      )}
      {candidates.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] text-mist uppercase tracking-widest">+ assign:</span>
          {candidates.map((p) => (
            <button key={p.id}
                    onClick={() => assign(p.id)}
                    disabled={busy}
                    className="btn btn-ghost text-[10px]"
                    data-testid={`companion-assign-${p.id}`}>
              <Plus className="w-3 h-3"/> {p.name || p.email}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
