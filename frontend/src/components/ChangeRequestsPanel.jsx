/**
 * ChangeRequestsPanel — V6.25.41
 *
 * GM ↔ player approval queue.
 *
 * • Players see *their own* pending submissions (cancel button).
 * • GM/admin see every pending request with Approve / Reject buttons +
 *   inline reason prompt on reject.
 *
 * The panel is hidden entirely on a campaign with
 * `gm_approval_required=false` to avoid noise. GM can flip the gate
 * via the `ApprovalSettingCard` below (lives next to the discover
 * publish card on the Invite & Share tab).
 *
 * Wires:
 *   GET    /api/campaigns/{cid}/change-requests
 *   POST   /api/campaigns/{cid}/change-requests/{rid}/approve
 *   POST   /api/campaigns/{cid}/change-requests/{rid}/reject
 *   POST   /api/campaigns/{cid}/change-requests/{rid}/cancel
 *   PATCH  /api/campaigns/{cid}/settings/approval
 */
import React, { useCallback, useEffect, useState } from "react";
import { Inbox, CheckCircle2, XCircle, RotateCcw, Shield, Settings2 } from "lucide-react";
import { api } from "../lib/api";


export function ApprovalSettingCard({ camp, onRefresh }) {
  const [busy, setBusy] = useState(false);
  const required = !!camp.gm_approval_required;
  const toggle = async () => {
    setBusy(true);
    try {
      await api.patch(`/campaigns/${camp.id}/settings/approval`,
                       { gm_approval_required: !required });
      onRefresh && onRefresh();
    } finally { setBusy(false); }
  };
  return (
    <div className="card-mystic p-5 mt-4" data-testid="approval-setting-card">
      <div className="label-ref mb-2 flex items-center gap-2">
        <Shield className="w-3 h-3 text-gold/60"/> Strict permission gating
        {required && <span className="tag bg-arcane/30 text-parchment text-[9px] uppercase tracking-widest">on</span>}
      </div>
      <div className="text-[11px] text-mist/80 italic mb-3">
        When on, player edits to <code className="text-gold-bright">character / inventory</code> route through your
        approval queue instead of writing directly. GM and admin always bypass.
      </div>
      <label className="flex items-center gap-2 text-sm text-parchment cursor-pointer">
        <input type="checkbox" checked={required} onChange={toggle}
               data-testid="approval-required-checkbox"/>
        <span>Require GM approval for player diffs</span>
      </label>
      <button onClick={toggle} disabled={busy}
              className="btn btn-primary text-xs mt-3"
              data-testid="approval-save-btn">
        {busy ? "Saving…" : required ? "Disable gating" : "Enable gating"}
      </button>
    </div>
  );
}


export default function ChangeRequestsPanel({ camp }) {
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    try {
      const r = await api.get(`/campaigns/${camp.id}/change-requests?status=pending`);
      setRows(r.data.items || []);
    } catch { /* ignore */ }
  }, [camp.id]);

  useEffect(() => { reload(); }, [reload]);

  if (!camp.gm_approval_required && rows.length === 0) return null;

  const isGm = !!camp.is_gm;

  const approve = async (rid) => {
    setBusy(true);
    try {
      await api.post(`/campaigns/${camp.id}/change-requests/${rid}/approve`);
      await reload();
    } finally { setBusy(false); }
  };
  const reject = async (rid) => {
    const reason = window.prompt("Reason for rejection (visible to filer):", "");
    if (reason === null) return;
    setBusy(true);
    try {
      await api.post(`/campaigns/${camp.id}/change-requests/${rid}/reject`, { reason });
      await reload();
    } finally { setBusy(false); }
  };
  const cancel = async (rid) => {
    if (!window.confirm("Cancel this request?")) return;
    setBusy(true);
    try {
      await api.post(`/campaigns/${camp.id}/change-requests/${rid}/cancel`);
      await reload();
    } finally { setBusy(false); }
  };

  return (
    <div className="card-mystic p-5 mt-4" data-testid="change-requests-panel">
      <div className="label-ref flex items-center gap-2 mb-3">
        <Inbox className="w-3 h-3 text-gold/60"/>
        {isGm ? "Approval queue" : "Your pending submissions"}
        <span className="tag bg-ember/30 text-parchment text-[9px] uppercase tracking-widest">
          {rows.length} pending
        </span>
      </div>
      {rows.length === 0 && (
        <div className="text-mist/70 text-xs italic">No pending change requests.</div>
      )}
      <ul className="space-y-2">
        {rows.map((r) => (
          <li key={r.id}
              className="border border-gold/15 rounded-sm p-3 bg-void/40"
              data-testid={`change-req-${r.id}`}>
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div className="min-w-0">
                <div className="text-[9px] uppercase tracking-widest text-gold/70">
                  {r.kind} · by {r.submitted_by_name} · {(r.submitted_at || "").slice(0, 16).replace("T", " ")}
                </div>
                <div className="text-parchment text-sm font-display tracking-wide leading-tight mt-0.5">
                  {r.summary}
                </div>
                {r.proposed_value && (
                  <pre className="text-[10px] text-mist/80 bg-ink/50 p-2 mt-2 overflow-x-auto rounded-sm border border-gold/10">
{JSON.stringify(r.proposed_value, null, 2).slice(0, 400)}
                  </pre>
                )}
              </div>
              <div className="flex gap-1 flex-wrap">
                {isGm && (
                  <>
                    <button onClick={() => approve(r.id)} disabled={busy}
                            className="btn btn-primary text-[10px]"
                            data-testid={`change-req-approve-${r.id}`}>
                      <CheckCircle2 className="w-3 h-3"/> Approve
                    </button>
                    <button onClick={() => reject(r.id)} disabled={busy}
                            className="btn btn-danger text-[10px]"
                            data-testid={`change-req-reject-${r.id}`}>
                      <XCircle className="w-3 h-3"/> Reject
                    </button>
                  </>
                )}
                {!isGm && (
                  <button onClick={() => cancel(r.id)} disabled={busy}
                          className="btn btn-ghost text-[10px]"
                          data-testid={`change-req-cancel-${r.id}`}>
                    <RotateCcw className="w-3 h-3"/> Cancel
                  </button>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
