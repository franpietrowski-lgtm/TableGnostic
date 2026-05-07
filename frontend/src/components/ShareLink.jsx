/**
 * ShareLink — V6.25.17
 *
 * Public landing page for a named campaign share link
 * (/share/:token). Mirrors the Invite component but reads the
 * `password_required`, `expired`, `capped`, and `valid` flags from
 * /api/share-links/{token} and posts the redemption to
 * /api/share-links/{token}/redeem.
 */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, useAuth, formatApiErrorDetail } from "../lib/api";
import {
  ArrowRight, UserPlus2, LogIn, Users, Sparkles, Lock, Tag,
} from "lucide-react";

export default function ShareLink() {
  const { token } = useParams();
  const nav = useNavigate();
  const { user, loading } = useAuth();
  const [info, setInfo] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [password, setPassword] = useState("");

  useEffect(() => {
    api.get(`/share-links/${token}`)
      .then((r) => setInfo(r.data))
      .catch((e) => setErr(
        formatApiErrorDetail(e.response?.data?.detail) || "Link not found."));
  }, [token]);

  const redeem = async () => {
    if (!user) {
      nav(`/auth?mode=register&redirect=${encodeURIComponent(`/share/${token}`)}`);
      return;
    }
    setBusy(true); setErr("");
    try {
      const body = info?.password_required ? { password } : {};
      const { data } = await api.post(`/share-links/${token}/redeem`, body);
      setDone(true);
      setTimeout(() => nav(`/app/campaigns/${data.campaign_id}`), 1200);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (err && !info) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="card-mystic p-8 max-w-md text-center relative z-10">
          <h1 className="font-display text-2xl text-parchment tracking-wide">
            Link is closed
          </h1>
          <p className="text-mist mt-2 font-body">{err}</p>
          <Link to="/" className="btn mt-6 inline-flex">Return home</Link>
        </div>
      </div>
    );
  }
  if (!info || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center
                      text-gold font-display tracking-[0.4em] animate-flicker">
        OPENING THE SHARE LINK
      </div>
    );
  }

  const blocked = info.expired || info.capped || !info.valid;

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative">
      <div className="relative z-10 w-full max-w-xl page">
        <Link to="/" className="block text-center mb-8 font-display tracking-[0.35em] text-parchment">
          TABLE<span className="text-gold">·</span>GNOSTIC
        </Link>

        <div className="card-mystic sigil-ring p-8" data-testid="share-link-landing">
          <div className="label-ref flex items-center gap-2 mb-3">
            <Sparkles className="w-3 h-3"/> Private share link
          </div>
          <h1 className="font-display text-3xl text-parchment tracking-wide">
            {info.name}
          </h1>
          <div className="mt-1 text-xs font-ui uppercase tracking-widest text-gold/70">
            {info.system} · GM {info.gm_name}
          </div>
          <div className="mt-3 flex items-center gap-2 text-[11px] text-arcane-light">
            <Tag className="w-3 h-3"/>
            <span data-testid="share-link-label">{info.label}</span>
          </div>

          <div className="mt-5 flex flex-wrap gap-4 text-xs text-mist font-ui">
            <span className="flex items-center gap-1">
              <Users className="w-3 h-3 text-gold/70"/>
              {info.seated}/{info.max_players} seated
            </span>
          </div>

          <div className="divider-sigil my-6"/>

          {done ? (
            <div className="text-center text-gold-bright font-display tracking-widest animate-flicker">
              SEAT CLAIMED — OPENING THE TABLE…
            </div>
          ) : info.expired ? (
            <div className="text-center text-ember font-body italic"
                 data-testid="share-link-expired">
              This share link has expired. Ask the GM for a fresh one.
            </div>
          ) : info.capped ? (
            <div className="text-center text-ember font-body italic"
                 data-testid="share-link-capped">
              This share link has been fully redeemed. Ask the GM for
              a new one.
            </div>
          ) : user ? (
            <div className="space-y-2">
              {info.password_required && (
                <div className="card-mystic p-3 border border-arcane/40"
                     data-testid="share-link-password-prompt">
                  <div className="text-[10px] uppercase tracking-widest text-arcane flex items-center gap-1">
                    <Lock className="w-3 h-3"/> Password required
                  </div>
                  <input type="password" autoFocus
                         className="input mt-2 w-full font-mono text-xs"
                         placeholder="Enter the share-link password"
                         value={password}
                         onChange={(e) => setPassword(e.target.value)}
                         onKeyDown={(e) => { if (e.key === "Enter") redeem(); }}
                         data-testid="share-link-password-input"/>
                </div>
              )}
              <button onClick={redeem}
                      disabled={blocked || busy
                                 || (info.password_required && !password)}
                      className="btn btn-primary w-full py-3"
                      data-testid="share-link-redeem">
                {busy ? "…" : <><UserPlus2 className="w-4 h-4"/> Redeem &amp; take a seat</>}
                <ArrowRight className="w-4 h-4"/>
              </button>
              {err && (
                <div className="text-ember text-xs text-center"
                     data-testid="share-link-error">{err}</div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <button onClick={() => nav(`/auth?mode=register&redirect=${encodeURIComponent(`/share/${token}`)}`)}
                      className="btn btn-primary w-full py-3"
                      data-testid="share-link-signup-btn">
                <UserPlus2 className="w-4 h-4"/> Create an account to redeem
              </button>
              <button onClick={() => nav(`/auth?mode=login&redirect=${encodeURIComponent(`/share/${token}`)}`)}
                      className="btn w-full py-3"
                      data-testid="share-link-signin-btn">
                <LogIn className="w-4 h-4"/> Already have one? Sign in
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
