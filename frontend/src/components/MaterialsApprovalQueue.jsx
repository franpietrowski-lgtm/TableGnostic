/**
 * MaterialsApprovalQueue — V6.25.13
 *
 * GM-facing approval surface for the V6.25.12 player Materials Intake
 * pipeline. Mirrors the XPApprovalQueue pattern: one row per pending
 * ticket with name + kind + summary + tags + rarity + submitter, plus
 * Approve / Reject buttons. Approving seeds a codex node with the
 * matching `node_kind` (material / byproduct / craft_output) and
 * provenance back to the player; rejection preserves the player's
 * journal entry but flags the ticket 'rejected'.
 *
 * Permission model: this component renders nothing for non-GMs (they
 * already see their own tickets via MaterialsIntakePanel).
 *
 * Use:
 *   <MaterialsApprovalQueue campaignId={cid} isGm={camp?.is_gm}/>
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Inbox, Check, X, RefreshCw, FlaskConical, Recycle, Hammer, Loader2,
} from "lucide-react";

const KIND_META = {
  material:     { label: "Material",     Icon: FlaskConical, tone: "text-arcane" },
  byproduct:    { label: "Byproduct",    Icon: Recycle,      tone: "text-mist" },
  craft_output: { label: "Craft Output", Icon: Hammer,       tone: "text-gold-bright" },
};

export default function MaterialsApprovalQueue({ campaignId, isGm }) {
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [pendingId, setPendingId] = useState("");

  const refresh = useCallback(async () => {
    if (!campaignId) return;
    setBusy(true);
    setErr("");
    try {
      const { data } = await api.get(
        `/campaigns/${campaignId}/materials-queue?status=pending`,
      );
      setRows(data || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  }, [campaignId]);

  useEffect(() => { refresh(); }, [refresh]);

  if (!isGm) return null;

  const decide = async (tid, action) => {
    setPendingId(tid);
    try {
      await api.post(`/campaigns/${campaignId}/materials-queue/${tid}/${action}`);
      await refresh();
    } catch (e) {
      window.alert(
        "Decision failed: "
        + (formatApiErrorDetail(e.response?.data?.detail) || e.message),
      );
    } finally {
      setPendingId("");
    }
  };

  return (
    <div className="card-mystic p-4" data-testid="materials-approval-queue">
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Inbox className="w-3 h-3"/> Materials Queue · Pending Approval
          </div>
          <div className="text-[10px] text-mist/70 italic">
            Player-submitted material / byproduct / craft-output tickets.
            Approving seeds a codex node with the right kind &amp; provenance.
          </div>
        </div>
        <button onClick={refresh}
                disabled={busy}
                className="btn btn-ghost text-[11px]"
                data-testid="materials-queue-refresh">
          {busy
            ? <Loader2 className="w-3 h-3 animate-spin"/>
            : <RefreshCw className="w-3 h-3"/>}
          Refresh
        </button>
      </div>

      {err && (
        <div className="text-ember text-xs mb-2"
             data-testid="materials-queue-error">{err}</div>
      )}

      {rows.length === 0 && !busy && (
        <div className="text-mist italic text-xs"
             data-testid="materials-queue-empty">
          No pending tickets. When players submit materials from their
          character journals, they&apos;ll surface here for review.
        </div>
      )}

      <div className="space-y-2">
        {rows.map((t) => {
          const meta = KIND_META[t.node_kind] || {
            label: t.node_kind, Icon: FlaskConical, tone: "text-mist",
          };
          const I = meta.Icon;
          const busyRow = pendingId === t.id;
          return (
            <div key={t.id}
                 className="border border-gold/15 rounded-sm p-3 space-y-1.5"
                 data-testid={`materials-queue-row-${t.id}`}>
              <div className="flex items-start gap-2">
                <I className={`w-4 h-4 mt-0.5 ${meta.tone}`}/>
                <div className="flex-1 min-w-0">
                  <div className="text-parchment font-display truncate">
                    {t.name}
                    <span className="ml-2 text-[10px] text-mist/70 font-ui uppercase tracking-widest">
                      {meta.label}
                    </span>
                    {t.rarity && (
                      <span className="ml-2 text-[10px] text-arcane">
                        {t.rarity}
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-mist">
                    submitted by{" "}
                    <span className="text-parchment">
                      {t.submitter_name || t.submitter_id?.slice(0, 8)}
                    </span>
                    {" · "}
                    {new Date(t.submitted_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {t.summary && (
                <div className="text-xs text-parchment/90 italic pl-6">
                  {t.summary}
                </div>
              )}
              {(t.tags || []).length > 0 && (
                <div className="flex flex-wrap gap-1 pl-6">
                  {t.tags.map((tg) => (
                    <span key={tg}
                          className="tag text-[10px]"
                          data-testid={`materials-queue-tag-${t.id}-${tg}`}>
                      {tg}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-2 pl-6 pt-1">
                <button onClick={() => decide(t.id, "approve")}
                        disabled={busyRow}
                        className="btn btn-primary text-[11px]"
                        data-testid={`materials-approve-${t.id}`}>
                  {busyRow
                    ? <Loader2 className="w-3 h-3 animate-spin"/>
                    : <Check className="w-3 h-3"/>}
                  Approve &amp; seed codex
                </button>
                <button onClick={() => decide(t.id, "reject")}
                        disabled={busyRow}
                        className="btn btn-ghost text-[11px]"
                        data-testid={`materials-reject-${t.id}`}>
                  <X className="w-3 h-3"/> Reject
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
