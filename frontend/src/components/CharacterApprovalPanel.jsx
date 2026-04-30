import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { ShieldCheck, AlertTriangle, ScrollText, Gavel, RefreshCw } from "lucide-react";

/**
 * CharacterApprovalPanel — rules-compliance validator + dual approval gate.
 *
 * Two-stage approval:
 *   1. App-internal validation — mechanical compliance check (BESM CP math,
 *      Anime 5E BESM-style point-buy budget, D&D level bounds, Cypher tier).
 *   2. GM ratification — explicit sign-off from the campaign GM.
 *
 * A character is "Approved for Play" when:
 *   - GM has ratified AND
 *   - (app_validated passed) OR (campaign has house_rules declared)
 *
 * A character that isn't approved cannot be seated at a session
 * (session seat-take endpoint returns 409 — GM can force with ?force=true).
 */
export default function CharacterApprovalPanel({ characterId, isGm, campaignHouseRules, onChanged }) {
  const [state, setState] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const { data } = await api.get(`/characters/${characterId}/validate`);
      setState(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [characterId]);

  useEffect(() => { load(); }, [load]);

  const appValidate = async () => {
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/characters/${characterId}/app-validate`);
      setState((prev) => ({ ...(prev || {}), ...data }));
      onChanged && onChanged();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const gmApprove = async (approved) => {
    setBusy(true); setErr("");
    try {
      await api.post(`/characters/${characterId}/approve-for-play`, {
        approved, note,
      });
      setNote("");
      await load();
      onChanged && onChanged();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (!state) return (
    <div className="card-mystic p-4 mt-4" data-testid="character-approval-panel-loading">
      <div className="text-xs text-mist">Auditing sheet…</div>
    </div>
  );

  const approved = state.approved_for_play;
  const houseRules = state.house_rules_active;
  const passes = state.passes_rules;
  const issues = state.issues || [];
  const warnings = state.warnings || [];
  const bd = state.breakdown || {};

  return (
    <div className="card-mystic p-5 mt-4" data-testid="character-approval-panel"
         style={{ borderLeftWidth: 3,
                  borderLeftColor: approved ? "#3FAA62" : issues.length ? "#7A1F2E" : "#C8A34A" }}>
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <ShieldCheck className="w-4 h-4"/> Character Approval
          </div>
          <div className="text-[11px] text-mist/80 italic mt-1 leading-snug max-w-xl">
            Two-stage gate before this PC can be seated at a session:
            (1) app-internal rules-compliance check, (2) GM ratification.
            House rules on the campaign skip the app-internal gate.
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className={`tag ${approved
            ? "border-arcane/50 text-arcane"
            : "border-ember/40 text-ember"}`}
                data-testid="approval-status-badge">
            {approved ? "Approved for Play" : "Not approved"}
          </span>
          {houseRules && (
            <span className="tag border-gold/40 text-gold-bright" data-testid="approval-house-rules-badge"
                  title="Campaign has house-rules declared — rules-compliance gate is bypassed.">
              House Rules
            </span>
          )}
        </div>
      </div>

      {/* System-specific breakdown ─────────────────────────── */}
      <div className="mt-4 text-[12px] border border-gold/15 rounded-sm p-3"
           data-testid="approval-breakdown">
        <div className="label-ref flex items-center gap-2">
          <ScrollText className="w-3 h-3"/> Rules audit · {state.system_id}
          {state.total_points ? (
            <span className="text-[10px] text-mist ml-2">
              budget {state.total_points} CP
            </span>
          ) : null}
        </div>
        {state.system_id === "besm-4e" && (
          <BesmBreakdown bd={bd} cap={state.total_points}/>
        )}
        {state.system_id === "anime-5e" && (
          <Anime5eBreakdown bd={bd}/>
        )}
        {(state.system_id === "dnd-5e" || state.system_id === "cypher") && (
          <div className="mt-2 text-parchment font-ui">{bd.chassis_note}</div>
        )}

        {issues.length > 0 && (
          <div className="mt-3 p-2 border border-ember/30 rounded-sm bg-ember/5"
               data-testid="approval-issues">
            <div className="label-ref text-ember flex items-center gap-1">
              <AlertTriangle className="w-3 h-3"/> Rules violations
            </div>
            <ul className="mt-1 space-y-0.5 list-disc list-inside text-[11px] text-ember">
              {issues.map((i, k) => <li key={k}>{i}</li>)}
            </ul>
          </div>
        )}
        {warnings.length > 0 && (
          <div className="mt-2 p-2 border border-gold/30 rounded-sm bg-gold/5"
               data-testid="approval-warnings">
            <div className="label-ref text-gold flex items-center gap-1">
              <AlertTriangle className="w-3 h-3"/> Advisories
            </div>
            <ul className="mt-1 space-y-0.5 list-disc list-inside text-[11px] text-gold">
              {warnings.map((i, k) => <li key={k}>{i}</li>)}
            </ul>
          </div>
        )}
      </div>

      {/* Status row ─────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 mt-3 text-[11px]">
        <div className="border border-gold/15 rounded-sm p-2" data-testid="approval-app-status">
          <div className="label-ref text-[9px]">App-Internal</div>
          <div className={`font-ui ${state.app_validated ? "text-arcane" : "text-ember"}`}>
            {state.app_validated ? "PASSES rules check" :
             passes ? "Pending — run validator" : "FAILS rules check"}
          </div>
        </div>
        <div className="border border-gold/15 rounded-sm p-2" data-testid="approval-gm-status">
          <div className="label-ref text-[9px]">GM Ratification</div>
          <div className={`font-ui ${state.gm_approved ? "text-arcane" : "text-mist"}`}>
            {state.gm_approved
              ? `Approved by ${state.approval?.gm_approved_by_name || "GM"}`
              : "Pending GM sign-off"}
          </div>
          {state.approval?.gm_approval_stale_reason && (
            <div className="text-[10px] text-ember italic mt-0.5">
              {state.approval.gm_approval_stale_reason}
            </div>
          )}
        </div>
      </div>

      {/* Actions ───────────────────────────────────────── */}
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <button onClick={appValidate} disabled={busy}
                className="btn btn-ghost text-xs"
                data-testid="approval-run-validator-btn">
          <RefreshCw className="w-3 h-3"/> Re-run rules audit
        </button>
        {isGm && (
          <>
            <input className="input text-xs flex-1 min-w-[180px]"
                   placeholder="GM note (optional)"
                   value={note}
                   onChange={(e) => setNote(e.target.value)}
                   data-testid="approval-gm-note-input"/>
            <button onClick={() => gmApprove(true)}
                    disabled={busy}
                    className="btn btn-primary text-xs"
                    data-testid="approval-gm-approve-btn"
                    title="Ratify this sheet as approved for live-session play.">
              <Gavel className="w-3 h-3"/> Approve
            </button>
            {state.gm_approved && (
              <button onClick={() => gmApprove(false)}
                      disabled={busy}
                      className="btn btn-danger text-xs"
                      data-testid="approval-gm-revoke-btn">
                Revoke
              </button>
            )}
          </>
        )}
      </div>
      {err && <div className="text-ember text-xs mt-2" data-testid="approval-error">{err}</div>}

      {campaignHouseRules && houseRules && (
        <div className="mt-3 p-2 border border-gold/30 rounded-sm bg-gold/5 text-[11px] text-mist"
             data-testid="approval-house-rules-note">
          <div className="label-ref text-gold-bright text-[9px] mb-0.5">House rules in effect</div>
          <div className="italic whitespace-pre-wrap max-h-24 overflow-y-auto">{campaignHouseRules}</div>
        </div>
      )}
    </div>
  );
}

function BesmBreakdown({ bd, cap }) {
  if (!bd || !bd.lines) return null;
  const spent = bd.total_spent || 0;
  const pct = cap > 0 ? Math.min(100, (spent / cap) * 100) : 0;
  const over = spent > cap;
  return (
    <div className="mt-2">
      <div className="flex items-baseline gap-3 text-parchment font-ui">
        <span className="font-display text-lg" style={{ color: over ? "#7A1F2E" : "#C8A34A" }}>
          {spent}
        </span>
        <span className="text-mist">/ {cap} CP</span>
        {over && <span className="text-ember text-[10px] font-ui uppercase tracking-widest">OVER BUDGET</span>}
      </div>
      <div className="h-1.5 bg-void/60 rounded-full mt-1 overflow-hidden">
        <div className="h-full transition-all"
             style={{ width: `${Math.min(100, pct)}%`,
                      backgroundColor: over ? "#7A1F2E" : pct > 95 ? "#C8A34A" : "#3FAA62" }}/>
      </div>
      <details className="mt-2">
        <summary className="text-[10px] text-mist cursor-pointer uppercase tracking-widest font-ui">
          {bd.lines.length} line item{bd.lines.length === 1 ? "" : "s"} · stats {bd.stat_total} · attrs {bd.attribute_total} · skills {bd.skill_total} · defect refund −{bd.defect_refund}
        </summary>
        <table className="w-full text-[11px] mt-2" data-testid="approval-breakdown-lines">
          <thead className="text-[9px] font-ui uppercase tracking-widest text-gold/60">
            <tr className="border-b border-gold/15">
              <th className="text-left py-1">Kind</th>
              <th className="text-left py-1">Name</th>
              <th className="text-right py-1">Lvl</th>
              <th className="text-right py-1">Cost/Lvl</th>
              <th className="text-right py-1">Pts</th>
            </tr>
          </thead>
          <tbody>
            {bd.lines.map((l, i) => (
              <tr key={i} className="border-b border-gold/5">
                <td className="py-1 text-mist text-[10px] uppercase tracking-widest">{l.kind}</td>
                <td className="py-1 text-parchment">{l.name}</td>
                <td className="py-1 text-right">{l.level ?? "—"}</td>
                <td className="py-1 text-right text-mist">{l.cost_per_level ?? "—"}</td>
                <td className={`py-1 text-right font-display ${l.points < 0 ? "text-ember" : "text-gold"}`}>
                  {l.points}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}

function Anime5eBreakdown({ bd }) {
  const pb = bd?.point_buy || { total_spent: 0, budget: 0, lines: [] };
  const over = pb.budget > 0 && pb.total_spent > pb.budget;
  const pct = pb.budget > 0 ? Math.min(100, (pb.total_spent / pb.budget) * 100) : 0;
  return (
    <div className="mt-2">
      {bd.chassis_note && (
        <div className="text-[11px] text-parchment font-ui mb-2">{bd.chassis_note}</div>
      )}
      <div className="label-ref text-[9px] mb-1">BESM-style point-buy layer</div>
      <div className="flex items-baseline gap-3 text-parchment font-ui">
        <span className="font-display text-lg" style={{ color: over ? "#7A1F2E" : "#E03A8E" }}>
          {pb.total_spent}
        </span>
        <span className="text-mist">/ {pb.budget || "—"} pts</span>
        {over && <span className="text-ember text-[10px] font-ui uppercase tracking-widest">OVER BUDGET</span>}
      </div>
      {pb.budget > 0 && (
        <div className="h-1.5 bg-void/60 rounded-full mt-1 overflow-hidden">
          <div className="h-full transition-all"
               style={{ width: `${Math.min(100, pct)}%`,
                        backgroundColor: over ? "#7A1F2E" : "#E03A8E" }}/>
        </div>
      )}
      {pb.lines?.length > 0 && (
        <ul className="mt-2 text-[11px] space-y-0.5" data-testid="approval-pointbuy-lines">
          {pb.lines.map((l, i) => (
            <li key={i} className="flex justify-between border-b border-gold/10 py-0.5">
              <span className="text-parchment">{l.name} <span className="text-mist text-[10px]">×{l.level}</span></span>
              <span className="text-gold">{l.points} pts</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
