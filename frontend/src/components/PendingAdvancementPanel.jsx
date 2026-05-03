/**
 * PendingAdvancementPanel — V6.18
 *
 * Lives on the character sheet's Identity tab below the Approval Panel.
 * Renders Level-Up Tickets the player has filed but the GM has not yet
 * approved or rejected. Visible to all table members:
 *   - Player sees their tickets + status, plus a "Withdraw" button on
 *     pending tickets they filed.
 *   - GM sees Approve / Reject buttons + per-ticket compliance preview.
 *
 * Persists nothing locally — every action round-trips to the backend.
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";
import { CheckCircle, XCircle, Clock, Inbox, Send } from "lucide-react";

export default function PendingAdvancementPanel({ characterId, isGm, ownerId, onChanged }) {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [decisionNote, setDecisionNote] = useState({});

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/characters/${characterId}/advancement/pending`);
      setTickets(data.tickets || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [characterId]);
  useEffect(() => { refresh(); }, [refresh]);

  // Listen for the wizard's filed-event so the panel pops up immediately.
  useEffect(() => {
    const onFiled = () => refresh();
    window.addEventListener("tg:advancement-applied", onFiled);
    window.addEventListener("tg:advancement-ticket-changed", onFiled);
    return () => {
      window.removeEventListener("tg:advancement-applied", onFiled);
      window.removeEventListener("tg:advancement-ticket-changed", onFiled);
    };
  }, [refresh]);

  const pending = tickets.filter((t) => t.status === "pending");
  const history = tickets.filter((t) => t.status !== "pending");
  if (!tickets.length) return null;

  const act = async (ticketId, action) => {
    setBusy(ticketId + ":" + action); setErr("");
    try {
      const note = decisionNote[ticketId] || "";
      let r;
      if (action === "approve") {
        r = await api.post(
          `/characters/${characterId}/advancement/approve/${ticketId}`,
          { note });
        if (r.data && r.data.blocked_by_compliance) {
          setErr(`Approval blocked by compliance: ${(r.data.compliance?.issues || []).join(" / ")}`);
        }
      } else if (action === "reject") {
        await api.post(
          `/characters/${characterId}/advancement/reject/${ticketId}`,
          { note });
      } else if (action === "withdraw") {
        await api.post(
          `/characters/${characterId}/advancement/withdraw/${ticketId}`);
      }
      window.dispatchEvent(new CustomEvent("tg:advancement-ticket-changed"));
      onChanged && onChanged();
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(""); }
  };

  return (
    <div className="card-mystic p-4 mt-4" data-testid="pending-advancement-panel">
      <div className="flex items-baseline justify-between mb-2 gap-2 flex-wrap">
        <div>
          <div className="label-ref">Pending Level-Up Tickets</div>
          <div className="text-[10px] text-mist italic">
            Player choices awaiting GM ratification. Compliance pre-flight runs at approval.
          </div>
        </div>
        <Inbox className="w-4 h-4 text-gold/50"/>
      </div>

      {pending.length === 0 ? (
        <div className="text-mist italic text-xs"
             data-testid="pending-tickets-empty">
          No tickets awaiting approval.
        </div>
      ) : pending.map((t) => {
        const filer = t.filed_by || "?";
        const canWithdraw = !isGm && t.filed_by_id === user?.id;
        return (
          <div key={t.id}
               className="border border-gold/20 rounded-sm p-3 mt-2"
               data-testid={`pending-ticket-${t.id}`}>
            <div className="flex items-baseline justify-between gap-2 flex-wrap">
              <div className="min-w-0 flex-1">
                <div className="font-ui text-sm text-parchment">
                  <Clock className="w-3 h-3 inline mr-1 text-gold-bright"/>
                  {t.advancement_id} · {t.choice_key || "—"}
                </div>
                <div className="text-[11px] text-mist mt-0.5">
                  Filed by <b>{filer}</b>
                  {t.cp_cost ? ` · ${t.cp_cost} CP` : ""}
                  {t.detail && Object.keys(t.detail).length > 0 ? (
                    <span className="ml-1 text-gold/70">
                      · {Object.entries(t.detail).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`).join(" · ")}
                    </span>
                  ) : null}
                </div>
                {t.note && (
                  <div className="text-[11px] text-parchment/85 italic mt-1">"{t.note}"</div>
                )}
              </div>
            </div>
            {isGm && (
              <div className="mt-2 flex items-center gap-2 flex-wrap">
                <input className="input flex-1 min-w-[160px] text-xs"
                       placeholder="Decision note (optional)"
                       value={decisionNote[t.id] || ""}
                       onChange={(e) => setDecisionNote({ ...decisionNote, [t.id]: e.target.value })}
                       data-testid={`ticket-note-${t.id}`}/>
                <button onClick={() => act(t.id, "approve")}
                        disabled={busy === t.id + ":approve"}
                        className="btn btn-primary text-[10px]"
                        data-testid={`ticket-approve-${t.id}`}>
                  <CheckCircle className="w-3 h-3"/> Approve &amp; commit
                </button>
                <button onClick={() => act(t.id, "reject")}
                        disabled={busy === t.id + ":reject"}
                        className="btn btn-danger text-[10px]"
                        data-testid={`ticket-reject-${t.id}`}>
                  <XCircle className="w-3 h-3"/> Reject
                </button>
              </div>
            )}
            {!isGm && canWithdraw && (
              <div className="mt-2">
                <button onClick={() => act(t.id, "withdraw")}
                        disabled={busy === t.id + ":withdraw"}
                        className="btn btn-ghost text-[10px]"
                        data-testid={`ticket-withdraw-${t.id}`}>
                  Withdraw
                </button>
              </div>
            )}
          </div>
        );
      })}

      {history.length > 0 && (
        <details className="mt-3" data-testid="pending-tickets-history">
          <summary className="text-[10px] uppercase tracking-widest text-mist cursor-pointer hover:text-gold">
            History · {history.length} resolved ticket{history.length === 1 ? "" : "s"}
          </summary>
          <div className="mt-2 space-y-1">
            {history.slice(-10).reverse().map((t) => (
              <div key={t.id} className="text-[11px] border-l-2 border-gold/15 pl-2 py-0.5"
                   data-testid={`history-ticket-${t.id}`}>
                <span className={`tag text-[9px] ${t.status === "approved" ? "border-gold-bright/40 text-gold-bright" : t.status === "rejected" ? "border-ember/40 text-ember" : "border-mist/40 text-mist"}`}>
                  {t.status}
                </span>
                <span className="ml-1 text-parchment">{t.advancement_id} · {t.choice_key || "—"}</span>
                {(t.approval_note || t.rejection_note) && (
                  <span className="text-mist italic ml-2">"{t.approval_note || t.rejection_note}"</span>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {err && <div className="text-ember text-xs mt-2" data-testid="pending-panel-error">{err}</div>}
    </div>
  );
}
