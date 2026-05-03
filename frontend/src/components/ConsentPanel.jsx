/**
 * ConsentPanel — V6.21 P2 GM/Player Consent Flow
 *
 * Two surfaces in one file:
 *   - <ConsentCheckbox/> — player-facing. Shows when the campaign has
 *     `consent_required=true` and the caller's consent is missing or
 *     stale (primer was edited since they agreed). A checkbox-driven
 *     acknowledgement with an optional free-text note.
 *   - <SeatApplicationsPanel/> — GM-facing. Lists pending seat
 *     applications with approve / reject buttons + GM note.
 *   - <ConsentRollPanel/> — GM-facing. Summary table of every member's
 *     consent status for the current primer snapshot.
 */
import React, { useCallback, useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { CheckCircle, XCircle, Clock, Shield, UserPlus, LogOut } from "lucide-react";

export function ConsentCheckbox({ campaignId, onChanged }) {
  const [state, setState] = useState(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [primer, setPrimer] = useState(true);
  const [house, setHouse] = useState(true);
  const [safety, setSafety] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/campaigns/${campaignId}/consent`);
      setState(data);
    } catch (e) {
      // 403 → not a member yet; silently hide.
      if (e.response?.status !== 403) {
        setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    }
  }, [campaignId]);
  useEffect(() => { refresh(); }, [refresh]);

  const submit = async () => {
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${campaignId}/consent`, {
        primer_acknowledged: primer,
        house_rules_acknowledged: house,
        safety_tags_acknowledged: safety,
        note,
      });
      await refresh();
      onChanged?.();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const withdraw = async () => {
    if (!window.confirm("Withdraw consent? Your sheet becomes read-only until you re-consent.")) return;
    setBusy(true);
    try {
      await api.delete(`/campaigns/${campaignId}/consent`);
      await refresh();
      onChanged?.();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const leave = async () => {
    if (!window.confirm("Leave this campaign? Your character stays with you; the seat frees up for the GM.")) return;
    setBusy(true);
    try {
      await api.post(`/campaigns/${campaignId}/leave`);
      window.location.assign("/app/campaigns");
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (!state) return null;
  const required = state.consent_required;
  const ok = state.up_to_date;
  const stale = state.consent && !state.up_to_date;

  return (
    <div className="card-mystic p-4 mt-4" data-testid="consent-panel">
      <div className="flex items-center gap-2 mb-2">
        <Shield className="w-4 h-4 text-gold-bright"/>
        <div className="label-ref">Table consent</div>
        {required && (
          <span className="tag text-[9px]">Required by GM</span>
        )}
      </div>

      {ok ? (
        <div className="flex items-center justify-between text-xs"
             data-testid="consent-current">
          <div className="text-gold-bright flex items-center gap-1">
            <CheckCircle className="w-3 h-3"/>
            Consent current · Agreed {state.consent.agreed_at?.slice(0, 10)}
          </div>
          <div className="flex gap-1">
            <button onClick={withdraw} disabled={busy}
                    className="btn btn-ghost text-[10px]"
                    data-testid="consent-withdraw">
              <XCircle className="w-3 h-3"/> Withdraw
            </button>
            <button onClick={leave} disabled={busy}
                    className="btn btn-ghost text-[10px]"
                    data-testid="consent-leave">
              <LogOut className="w-3 h-3"/> Leave seat
            </button>
          </div>
        </div>
      ) : (
        <div data-testid="consent-pending">
          {stale && (
            <div className="border-l-2 border-ember/60 bg-ember/5 p-2 mb-3 text-[11px]">
              <Clock className="w-3 h-3 inline mr-1 text-ember"/>
              The GM updated the primer since you last agreed — please
              re-consent.
            </div>
          )}
          <p className="text-[11px] text-mist mb-2">
            Before the GM can validate your character, tick the boxes
            below to acknowledge the table's primer, house rules, and
            safety tags.
          </p>
          <div className="space-y-1 text-xs">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={primer}
                     onChange={(e) => setPrimer(e.target.checked)}
                     data-testid="consent-chk-primer"/>
              <span>I've read the <b>Player Primer</b>.</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={house}
                     onChange={(e) => setHouse(e.target.checked)}
                     data-testid="consent-chk-house"/>
              <span>I accept the <b>House Rules</b>.</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={safety}
                     onChange={(e) => setSafety(e.target.checked)}
                     data-testid="consent-chk-safety"/>
              <span>I acknowledge the <b>safety & content tags</b>.</span>
            </label>
          </div>
          <textarea className="input min-h-[60px] mt-2 text-xs"
                    placeholder="Optional note to the GM (lines, veils, access needs…)"
                    value={note} onChange={(e) => setNote(e.target.value)}
                    data-testid="consent-note"/>
          <button onClick={submit} disabled={busy || !(primer && house && safety)}
                  className="btn btn-primary text-xs mt-2"
                  data-testid="consent-submit">
            {busy ? "Saving…" : "Agree and continue"}
          </button>
        </div>
      )}
      {err && <div className="text-ember text-xs mt-2">{err}</div>}
    </div>
  );
}


// ─── GM-facing seat applications panel ────────────────────────────────

export function SeatApplicationsPanel({ campaignId, onChanged }) {
  const [apps, setApps] = useState([]);
  const [err, setErr] = useState("");

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/campaigns/${campaignId}/seat-applications`);
      setApps(data?.applications || []);
    } catch (e) {
      if (e.response?.status !== 403) {
        setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    }
  }, [campaignId]);
  useEffect(() => { refresh(); }, [refresh]);

  const decide = async (aid, verb, gm_note) => {
    try {
      await api.post(`/campaigns/${campaignId}/seat-applications/${aid}/${verb}`,
                      { gm_note: gm_note || "" });
      await refresh();
      onChanged?.();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  const pending = apps.filter((a) => a.status === "pending");
  const resolved = apps.filter((a) => a.status !== "pending").slice(-5);

  return (
    <div className="card-mystic p-4 mt-4" data-testid="seat-applications-panel">
      <div className="flex items-center gap-2 mb-2">
        <UserPlus className="w-4 h-4 text-gold-bright"/>
        <div className="label-ref">Seat applications · GM queue</div>
        <span className="tag text-[9px]">{pending.length} pending</span>
      </div>
      {pending.length === 0 && (
        <div className="text-[11px] text-mist italic">No pending applications.</div>
      )}
      <div className="space-y-2">
        {pending.map((a) => (
          <SeatApplicationRow key={a.id} app={a} onDecide={decide}/>
        ))}
      </div>
      {resolved.length > 0 && (
        <details className="mt-3">
          <summary className="text-[11px] text-mist cursor-pointer">
            Recent history ({resolved.length})
          </summary>
          <div className="space-y-1 mt-1">
            {resolved.map((a) => (
              <div key={a.id} className="text-[11px] text-mist flex items-center gap-2"
                   data-testid={`seat-app-history-${a.id}`}>
                <span className={a.status === "approved" ? "text-gold-bright" : "text-ember"}>
                  {a.status === "approved" ? "✓" : "✗"} {a.status}
                </span>
                · {a.user_name} · {a.resolved_at?.slice(0, 10)}
                {a.gm_note && <span className="italic">· "{a.gm_note}"</span>}
              </div>
            ))}
          </div>
        </details>
      )}
      {err && <div className="text-ember text-xs mt-2">{err}</div>}
    </div>
  );
}

function SeatApplicationRow({ app, onDecide }) {
  const [note, setNote] = useState("");
  return (
    <div className="border border-gold/20 rounded-sm p-2"
         data-testid={`seat-app-${app.id}`}>
      <div className="flex items-baseline justify-between mb-1">
        <div className="font-display text-parchment text-sm">{app.user_name}</div>
        <div className="text-[10px] text-mist">
          {app.preferred_system_familiarity || "unknown"} · applied {app.applied_at?.slice(0, 10)}
        </div>
      </div>
      {app.character_pitch && (
        <div className="text-[11px] text-mist italic mb-1">
          Pitch: "{app.character_pitch}"
        </div>
      )}
      {app.note && (
        <div className="text-[11px] text-mist mb-1">Note: {app.note}</div>
      )}
      <div className="flex gap-2 mt-2">
        <input className="input flex-1 text-xs" placeholder="Optional GM note…"
               value={note} onChange={(e) => setNote(e.target.value)}
               data-testid={`seat-app-${app.id}-note`}/>
        <button onClick={() => onDecide(app.id, "approve", note)}
                className="btn btn-primary text-xs"
                data-testid={`seat-app-${app.id}-approve`}>
          Seat
        </button>
        <button onClick={() => onDecide(app.id, "reject", note)}
                className="btn btn-ghost text-xs"
                data-testid={`seat-app-${app.id}-reject`}>
          Reject
        </button>
      </div>
    </div>
  );
}


// ─── GM-facing consent roll (summary of every member's status) ───────

export function ConsentRollPanel({ campaignId }) {
  const [rows, setRows] = useState([]);
  const [required, setRequired] = useState(false);
  const [err, setErr] = useState("");

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/campaigns/${campaignId}/consent-roll`);
      setRows(data?.rows || []);
      setRequired(!!data?.consent_required);
    } catch (e) {
      if (e.response?.status !== 403) {
        setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    }
  }, [campaignId]);
  useEffect(() => { refresh(); }, [refresh]);

  return (
    <div className="card-mystic p-4 mt-4" data-testid="consent-roll-panel">
      <div className="flex items-center gap-2 mb-2">
        <Shield className="w-4 h-4 text-gold-bright"/>
        <div className="label-ref">Consent roll · table status</div>
        <span className={`tag text-[9px] ${required ? "" : "border-mist/30 text-mist"}`}>
          {required ? "Required" : "Optional"}
        </span>
      </div>
      {rows.length === 0 && (
        <div className="text-[11px] text-mist italic">No members seated yet.</div>
      )}
      <table className="w-full text-xs">
        <tbody>
          {rows.map((r) => (
            <tr key={r.user_id} className="border-b border-gold/10"
                data-testid={`consent-row-${r.user_id}`}>
              <td className="py-1 text-parchment">{r.user_name}</td>
              <td className="py-1 text-right">
                {r.up_to_date ? (
                  <span className="text-gold-bright">
                    <CheckCircle className="w-3 h-3 inline"/> Current
                  </span>
                ) : r.has_consent ? (
                  <span className="text-ember">
                    <Clock className="w-3 h-3 inline"/> Stale
                  </span>
                ) : (
                  <span className="text-mist">
                    <XCircle className="w-3 h-3 inline"/> Not yet
                  </span>
                )}
              </td>
              <td className="py-1 text-right text-mist text-[10px]">
                {r.agreed_at?.slice(0, 10) || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {err && <div className="text-ember text-xs mt-2">{err}</div>}
    </div>
  );
}


// ─── Player-facing seat application form ─────────────────────────────

export function SeatApplicationForm({ campaignId, onSubmitted }) {
  const [pitch, setPitch] = useState("");
  const [fam, setFam] = useState("some");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [applied, setApplied] = useState(false);

  const submit = async () => {
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${campaignId}/seat-applications`, {
        character_pitch: pitch,
        preferred_system_familiarity: fam,
        note,
      });
      setApplied(true);
      onSubmitted?.();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (applied) {
    return (
      <div className="card-mystic p-3 text-xs text-gold-bright"
           data-testid="seat-app-submitted">
        <CheckCircle className="w-3 h-3 inline mr-1"/>
        Application filed. The GM will review your pitch.
      </div>
    );
  }

  return (
    <div className="card-mystic p-4" data-testid="seat-app-form">
      <div className="label-ref mb-2">Apply for a seat</div>
      <textarea className="input min-h-[60px] text-xs mb-2"
                placeholder="Character pitch — a sentence or two on who you'd play…"
                value={pitch} onChange={(e) => setPitch(e.target.value)}
                data-testid="seat-app-pitch"/>
      <div className="flex items-center gap-2 text-xs mb-2">
        <label className="label-ref">System familiarity:</label>
        <select className="input text-xs" value={fam}
                onChange={(e) => setFam(e.target.value)}
                data-testid="seat-app-familiarity">
          <option value="new">New to the system</option>
          <option value="some">Some experience</option>
          <option value="expert">Expert</option>
        </select>
      </div>
      <textarea className="input min-h-[40px] text-xs mb-2"
                placeholder="Optional note (availability, lines/veils, accessibility…)"
                value={note} onChange={(e) => setNote(e.target.value)}
                data-testid="seat-app-note"/>
      <button onClick={submit} disabled={busy}
              className="btn btn-primary text-xs"
              data-testid="seat-app-submit">
        {busy ? "Filing…" : "Submit application"}
      </button>
      {err && <div className="text-ember text-xs mt-2">{err}</div>}
    </div>
  );
}
