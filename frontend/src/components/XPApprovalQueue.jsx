import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Sparkles, Check, X, Send, Inbox, RefreshCw } from "lucide-react";

/**
 * XPApprovalQueue — V4.4 Phase H.
 *
 * Two roles in one component:
 *   * Player view: list their own pending proposals on a character.
 *   * GM view (when isGm): list every pending proposal in the campaign,
 *     with Approve / Reject buttons.
 *
 * Until the GM approves, NOTHING on the character sheet changes — so
 * live roll-resolution logic continues to read the last-approved snapshot.
 */
export default function XPApprovalQueue({ campaignId, characterId, isGm, onUpdate }) {
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const refresh = async () => {
    setBusy(true);
    try {
      const url = isGm
        ? `/campaigns/${campaignId}/xp-pending`
        : `/characters/${characterId}/xp-pending`;
      const { data } = await api.get(url);
      setRows(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => { refresh(); }, [campaignId, characterId, isGm]);

  const decide = async (pid, action, reason = "") => {
    try {
      if (action === "approve") {
        await api.post(`/xp-pending/${pid}/approve`);
      } else {
        await api.post(`/xp-pending/${pid}/reject`, { reason });
      }
      await refresh();
      onUpdate && onUpdate();
    } catch (e) {
      window.alert("Decision failed: " + (e.response?.data?.detail || e.message));
    }
  };

  if (err) return <div className="text-ember text-xs">{err}</div>;
  if (rows.length === 0) return null;

  return (
    <div className="card-mystic p-4" data-testid="xp-approval-queue">
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Inbox className="w-3 h-3"/> XP Spend · {isGm ? "Pending Approval" : "Awaiting GM"}
          </div>
          <div className="text-[10px] text-mist/70 italic">
            {isGm ? "Approve applies the change + debits XP. Reject leaves XP intact."
                  : "Submit a change → GM reviews → applies on approve."}
          </div>
        </div>
        <button onClick={refresh} className="btn btn-ghost text-xs" data-testid="xp-approval-refresh">
          <RefreshCw className="w-3 h-3"/>
        </button>
      </div>
      <ul className="space-y-2">
        {rows.map((r) => (
          <li key={r.id}
              className="border border-gold/15 rounded-sm p-3 flex items-center justify-between gap-3"
              data-testid={`xp-pending-${r.id}`}>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-ui">
                <span className="text-gold">{r.character_name}</span>
                <span className="text-mist/70 ml-2 text-[10px]">— by {r.proposed_by_name}</span>
              </div>
              <div className="text-[12px] text-parchment/85 italic mt-1 leading-snug">{r.summary}</div>
              <div className="text-[10px] text-gold/60 font-ui mt-1">
                cost {r.cost} XP · change: <span className="text-mist/80">{JSON.stringify(r.change)}</span>
              </div>
            </div>
            {isGm && (
              <div className="flex gap-1.5 flex-shrink-0">
                <button onClick={() => decide(r.id, "approve")}
                        className="btn btn-primary text-[10px] py-1 px-2"
                        data-testid={`xp-pending-approve-${r.id}`}>
                  <Check className="w-3 h-3"/> Approve
                </button>
                <button onClick={() => {
                          const reason = window.prompt("Rejection reason?", "");
                          if (reason !== null) decide(r.id, "reject", reason);
                        }}
                        className="btn btn-ghost text-[10px] py-1 px-2 text-ember"
                        data-testid={`xp-pending-reject-${r.id}`}>
                  <X className="w-3 h-3"/> Reject
                </button>
              </div>
            )}
            {!isGm && (
              <span className={`tag text-[9px] ${r.status === "pending" ? "border-gold/50 text-gold-bright" : r.status === "approved" ? "border-arcane/50 text-arcane-light" : "border-ember/50 text-ember"}`}>
                {r.status}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** XPSpendForm — embedded on CharacterSheet for the owner to propose
 *  a stat boost or attribute level-up. */
export function XPSpendForm({ characterId, character, onProposed }) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState("stat");  // stat | attribute_level
  const [statKey, setStatKey] = useState("body");
  const [attrName, setAttrName] = useState("");
  const [delta, setDelta] = useState(1);
  const [cost, setCost] = useState(1);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    try {
      const change = kind === "stat"
        ? { [`stats.${statKey}`]: +delta }
        : { attribute_level: { name: attrName, delta: +delta } };
      const summary = kind === "stat"
        ? `${delta >= 0 ? "+" : ""}${delta} ${statKey}`
        : `${attrName}: ${delta >= 0 ? "+" : ""}${delta} level`;
      await api.post(`/characters/${characterId}/xp-spend`, {
        cost: +cost, reason: reason || summary, change, summary,
      });
      setOpen(false); setReason("");
      onProposed && onProposed();
    } catch (e) {
      window.alert("Could not submit: " + (e.response?.data?.detail || e.message));
    } finally { setBusy(false); }
  };

  if (!open) return (
    <button onClick={() => setOpen(true)} className="btn btn-ghost text-xs"
            data-testid="xp-spend-open"
            title="Propose to spend XP. GM approves before changes apply.">
      <Send className="w-3 h-3"/> Spend XP
    </button>
  );
  return (
    <div className="card-mystic p-3 mt-2" data-testid="xp-spend-form">
      <div className="label-ref mb-2 flex items-center gap-2"><Sparkles className="w-3 h-3"/> Propose XP Spend</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <select className="select" value={kind} onChange={(e) => setKind(e.target.value)}
                data-testid="xp-spend-kind">
          <option value="stat">Stat (Body/Mind/Soul)</option>
          <option value="attribute_level">Attribute level</option>
        </select>
        {kind === "stat" ? (
          <select className="select" value={statKey} onChange={(e) => setStatKey(e.target.value)}
                  data-testid="xp-spend-stat">
            <option value="body">Body</option>
            <option value="mind">Mind</option>
            <option value="soul">Soul</option>
          </select>
        ) : (
          <select className="select" value={attrName} onChange={(e) => setAttrName(e.target.value)}
                  data-testid="xp-spend-attr">
            <option value="">— choose attribute —</option>
            {(character.attributes || []).map((a, i) => (
              <option key={i} value={a.name}>{a.name} (×{a.level})</option>
            ))}
          </select>
        )}
        <label className="text-xs">
          Delta:
          <input type="number" className="input" min={-3} max={5}
                 value={delta} onChange={(e) => setDelta(+e.target.value)}
                 data-testid="xp-spend-delta"/>
        </label>
        <label className="text-xs">
          XP cost:
          <input type="number" className="input" min={0.5} max={20} step={0.5}
                 value={cost} onChange={(e) => setCost(+e.target.value)}
                 data-testid="xp-spend-cost"/>
        </label>
      </div>
      <input className="input mt-2" placeholder="Why? (optional, GM sees this)"
             value={reason} onChange={(e) => setReason(e.target.value)}
             data-testid="xp-spend-reason"/>
      <div className="flex gap-2 mt-2 justify-end">
        <button onClick={() => setOpen(false)} className="btn btn-ghost text-xs">Cancel</button>
        <button onClick={submit} disabled={busy || (kind === "attribute_level" && !attrName)}
                className="btn btn-primary text-xs" data-testid="xp-spend-submit">
          {busy ? "Submitting…" : "Submit for GM"}
        </button>
      </div>
    </div>
  );
}
