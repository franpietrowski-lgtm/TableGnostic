/**
 * PrivateAccessPanel — V6.25.17
 *
 * GM-facing surface for campaign-level access control:
 *   • Set / clear a join-password that gates the canonical invite link.
 *   • Author named "share links" (e.g. "patreon-gold", "core-friends"),
 *     each with optional password / expiry / max-use cap. Each link
 *     resolves to a public token the GM can hand out separately.
 *   • Audit trail per share-link (use_count, last_used_at).
 *
 * Mounts inside the "Invite & Share" tab on Campaign Detail. Renders
 * nothing for non-GM viewers.
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Lock, Unlock, Plus, Trash2, Copy, Check, Loader2, RefreshCw,
} from "lucide-react";

export default function PrivateAccessPanel({ camp, onRefresh }) {
  const [pwdInput, setPwdInput] = useState("");
  const [pwdSet, setPwdSet] = useState(!!camp?.access_password_set);
  const [pwdBusy, setPwdBusy] = useState(false);
  const [err, setErr] = useState("");

  const [links, setLinks] = useState([]);
  const [linksBusy, setLinksBusy] = useState(false);

  const [draft, setDraft] = useState({
    label: "", password: "", max_uses: "", expires_at: "",
  });
  const [draftBusy, setDraftBusy] = useState(false);
  const [copiedToken, setCopiedToken] = useState("");

  const refreshLinks = useCallback(async () => {
    if (!camp?.id) return;
    setLinksBusy(true);
    try {
      const { data } = await api.get(`/campaigns/${camp.id}/share-links`);
      setLinks(data || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setLinksBusy(false); }
  }, [camp?.id]);

  useEffect(() => {
    setPwdSet(!!camp?.access_password_set);
    refreshLinks();
  }, [camp?.id, camp?.access_password_set, refreshLinks]);

  if (!camp?.is_gm) return null;

  // ─── Campaign-level password ─────────────────────────────────────
  const setPwd = async (clear) => {
    setPwdBusy(true); setErr("");
    try {
      const body = clear ? { password: "" } : { password: pwdInput };
      const { data } = await api.post(
        `/campaigns/${camp.id}/access-password`, body);
      setPwdSet(!!data.password_set);
      setPwdInput("");
      onRefresh && onRefresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setPwdBusy(false); }
  };

  // ─── Share-link CRUD ─────────────────────────────────────────────
  const createLink = async () => {
    if (!draft.label.trim()) return;
    setDraftBusy(true); setErr("");
    try {
      const body = {
        label: draft.label.trim(),
        password: draft.password,
        max_uses: draft.max_uses === "" ? null : Number(draft.max_uses),
        expires_at: draft.expires_at || null,
      };
      await api.post(`/campaigns/${camp.id}/share-links`, body);
      setDraft({ label: "", password: "", max_uses: "", expires_at: "" });
      refreshLinks();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setDraftBusy(false); }
  };

  const removeLink = async (lid) => {
    if (!window.confirm("Revoke this share link?")) return;
    try {
      await api.delete(`/campaigns/${camp.id}/share-links/${lid}`);
      refreshLinks();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  const copyLink = async (token) => {
    const url = `${window.location.origin}/share/${token}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopiedToken(token);
      setTimeout(() => setCopiedToken(""), 1500);
    } catch {
      window.alert("Copy failed. Long-press the link to copy manually.");
    }
  };

  return (
    <div className="card-mystic p-4 mt-4 space-y-4"
         data-testid="private-access-panel">
      <div>
        <div className="label-ref flex items-center gap-2">
          {pwdSet ? <Lock className="w-3 h-3 text-arcane"/>
                  : <Unlock className="w-3 h-3 text-mist"/>}
          Private Access
        </div>
        <div className="text-[10px] text-mist/80 italic">
          Optional gates that sit on top of the public invite link. Set
          a campaign-wide password, or hand out named share links with
          their own password / expiry / use-cap.
        </div>
      </div>

      {/* Campaign-wide password */}
      <div className="border border-gold/15 rounded-sm p-3 space-y-2"
           data-testid="campaign-password-block">
        <div className="text-[11px] text-parchment font-display flex items-center gap-2">
          Campaign password
          <span className={`text-[10px] ${pwdSet ? "text-gold-bright" : "text-mist/70"}`}>
            {pwdSet ? "ACTIVE" : "OFF"}
          </span>
        </div>
        <div className="flex gap-2 items-center flex-wrap">
          <input className="input text-xs flex-1 min-w-[160px]"
                 type="password"
                 placeholder={pwdSet ? "Set a NEW password to replace the active one"
                                     : "Set a password to gate the invite link"}
                 value={pwdInput}
                 onChange={(e) => setPwdInput(e.target.value)}
                 data-testid="campaign-password-input"/>
          <button onClick={() => setPwd(false)}
                  disabled={pwdBusy || !pwdInput}
                  className="btn btn-primary text-xs"
                  data-testid="campaign-password-save">
            {pwdBusy ? <Loader2 className="w-3 h-3 animate-spin"/>
                     : <Lock className="w-3 h-3"/>}
            {pwdSet ? "Replace" : "Lock"}
          </button>
          {pwdSet && (
            <button onClick={() => setPwd(true)}
                    disabled={pwdBusy}
                    className="btn btn-ghost text-xs"
                    data-testid="campaign-password-clear">
              <Unlock className="w-3 h-3"/> Clear
            </button>
          )}
        </div>
        {pwdSet && (
          <div className="text-[10px] text-mist/70 italic">
            Players need this password the first time they redeem the
            invite link. Re-setting it does NOT eject anyone already seated.
          </div>
        )}
      </div>

      {/* Share-link CRUD */}
      <div className="border border-gold/15 rounded-sm p-3 space-y-2"
           data-testid="share-links-block">
        <div className="text-[11px] text-parchment font-display flex items-center justify-between">
          <span>Named share links</span>
          <button onClick={refreshLinks}
                  disabled={linksBusy}
                  className="btn btn-ghost text-[10px]"
                  data-testid="share-links-refresh">
            {linksBusy ? <Loader2 className="w-3 h-3 animate-spin"/>
                       : <RefreshCw className="w-3 h-3"/>}
            Refresh
          </button>
        </div>
        <div className="text-[10px] text-mist/70 italic">
          Each link is a separate token with its own password / expiry
          / max-use cap. Useful for "core friends" vs "patreon"
          cohorts. Deleting a link revokes it instantly.
        </div>

        {/* Existing links */}
        {links.map((l) => (
          <div key={l.id}
               className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center
                          border border-gold/10 rounded-sm p-2 bg-void/30"
               data-testid={`share-link-row-${l.id}`}>
            <div className="sm:col-span-3">
              <div className="text-parchment font-display text-xs">
                {l.label}
                {l.password_set && <Lock className="w-3 h-3 inline ml-1 text-arcane"/>}
              </div>
              <div className="text-[10px] text-mist/70">
                used {l.use_count}{l.max_uses != null ? `/${l.max_uses}` : ""}
                {l.expires_at && (
                  <> · expires {new Date(l.expires_at).toLocaleDateString()}</>
                )}
              </div>
            </div>
            <input className="input font-mono text-[10px] sm:col-span-7"
                   readOnly
                   value={`${window.location.origin}/share/${l.token}`}
                   data-testid={`share-link-url-${l.id}`}/>
            <button onClick={() => copyLink(l.token)}
                    className="btn btn-ghost text-[10px] sm:col-span-1"
                    data-testid={`share-link-copy-${l.id}`}>
              {copiedToken === l.token
                ? <Check className="w-3 h-3 text-gold-bright"/>
                : <Copy className="w-3 h-3"/>}
            </button>
            <button onClick={() => removeLink(l.id)}
                    className="btn btn-danger text-[10px] sm:col-span-1"
                    data-testid={`share-link-delete-${l.id}`}>
              <Trash2 className="w-3 h-3"/>
            </button>
          </div>
        ))}
        {links.length === 0 && !linksBusy && (
          <div className="text-mist italic text-[11px]">
            No share links yet. Create one below for your patrons or
            inner circle.
          </div>
        )}

        {/* Draft new link */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center pt-2
                        border-t border-gold/10"
             data-testid="share-link-draft">
          <input className="input text-xs sm:col-span-3"
                 placeholder="Label (e.g. patreon-gold)"
                 value={draft.label}
                 onChange={(e) => setDraft({ ...draft, label: e.target.value })}
                 data-testid="share-link-draft-label"/>
          <input className="input text-xs sm:col-span-3"
                 type="password"
                 placeholder="Password (optional)"
                 value={draft.password}
                 onChange={(e) => setDraft({ ...draft, password: e.target.value })}
                 data-testid="share-link-draft-password"/>
          <input className="input text-xs sm:col-span-2 text-center"
                 type="number" min={1}
                 placeholder="Max uses"
                 value={draft.max_uses}
                 onChange={(e) => setDraft({ ...draft, max_uses: e.target.value })}
                 data-testid="share-link-draft-maxuses"/>
          <input className="input text-xs sm:col-span-3"
                 type="datetime-local"
                 value={draft.expires_at}
                 onChange={(e) => setDraft({ ...draft, expires_at: e.target.value })}
                 data-testid="share-link-draft-expires"/>
          <button onClick={createLink}
                  disabled={draftBusy || !draft.label.trim()}
                  className="btn btn-primary text-xs sm:col-span-1"
                  data-testid="share-link-create">
            {draftBusy ? <Loader2 className="w-3 h-3 animate-spin"/>
                       : <Plus className="w-3 h-3"/>}
          </button>
        </div>
      </div>

      {err && <div className="text-ember text-xs"
                   data-testid="private-access-error">{err}</div>}
    </div>
  );
}
