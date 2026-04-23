import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, useAuth, formatApiErrorDetail } from "../lib/api";
import { ArrowRight, UserPlus2, LogIn, Users, Clock3, Scroll, Sparkles } from "lucide-react";

export default function Invite() {
  const { token } = useParams();
  const nav = useNavigate();
  const { user, loading } = useAuth();
  const [info, setInfo] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    api.get(`/invites/${token}`).then((r) => setInfo(r.data))
       .catch((e) => setErr(formatApiErrorDetail(e.response?.data?.detail) || "Invite not found."));
  }, [token]);

  const accept = async () => {
    if (!user) { nav(`/auth?mode=register&redirect=${encodeURIComponent(`/invite/${token}`)}`); return; }
    setBusy(true);
    try {
      const { data } = await api.post(`/invites/${token}/accept`);
      setDone(true);
      setTimeout(() => nav(`/app/campaigns/${data.campaign_id}`), 1200);
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
    finally { setBusy(false); }
  };

  if (err) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="card-mystic p-8 max-w-md text-center relative z-10">
          <h1 className="font-display text-2xl text-parchment tracking-wide">Invite is closed</h1>
          <p className="text-mist mt-2 font-body">{err}</p>
          <Link to="/" className="btn mt-6 inline-flex">Return home</Link>
        </div>
      </div>
    );
  }
  if (!info || loading) {
    return <div className="min-h-screen flex items-center justify-center text-gold font-display tracking-[0.4em] animate-flicker">OPENING THE INVITE</div>;
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative">
      <div className="relative z-10 w-full max-w-xl page">
        <Link to="/" className="block text-center mb-8 font-display tracking-[0.35em] text-parchment">
          TABLE<span className="text-gold">·</span>GNOSTIC
        </Link>

        <div className="card-mystic sigil-ring p-8">
          <div className="label-ref flex items-center gap-2 mb-3"><Sparkles className="w-3 h-3"/> You've been invited</div>
          <h1 className="font-display text-3xl text-parchment tracking-wide">{info.name}</h1>
          <div className="mt-1 text-xs font-ui uppercase tracking-widest text-gold/70">
            {info.system} · {info.power_level} · GM {info.gm_name}
          </div>
          {info.description && <p className="text-mist mt-4 font-body leading-relaxed">{info.description}</p>}

          <div className="mt-5 flex flex-wrap gap-1">
            {info.genre && <span className="tag">{info.genre}</span>}
            {info.tone && <span className="tag">{info.tone}</span>}
            {(info.tags || []).map((t, i) => <span key={i} className="tag">{t}</span>)}
          </div>

          <div className="mt-5 flex flex-wrap gap-4 text-xs text-mist font-ui">
            <span className="flex items-center gap-1"><Users className="w-3 h-3 text-gold/70"/> {info.seated}/{info.max_players} seated</span>
            {info.schedule && <span className="flex items-center gap-1"><Clock3 className="w-3 h-3 text-gold/70"/> {info.schedule}</span>}
            {info.experience_level && <span className="flex items-center gap-1"><Scroll className="w-3 h-3 text-gold/70"/> {info.experience_level}</span>}
          </div>

          <div className="divider-sigil my-6"/>

          {done ? (
            <div className="text-center text-gold-bright font-display tracking-widest animate-flicker">
              SEAT CLAIMED — OPENING THE TABLE…
            </div>
          ) : info.full ? (
            <div className="text-center text-ember font-body italic">This table is full. Wait for a seat to open or ask the GM to expand the table.</div>
          ) : user ? (
            <button onClick={accept} disabled={busy} className="btn btn-primary w-full py-3" data-testid="invite-accept-btn">
              {busy ? "…" : <><UserPlus2 className="w-4 h-4"/> Take this seat</>}
              <ArrowRight className="w-4 h-4"/>
            </button>
          ) : (
            <div className="space-y-2">
              <button onClick={() => nav(`/auth?mode=register&redirect=${encodeURIComponent(`/invite/${token}`)}`)}
                      className="btn btn-primary w-full py-3" data-testid="invite-signup-btn">
                <UserPlus2 className="w-4 h-4"/> Create an account to accept
              </button>
              <button onClick={() => nav(`/auth?mode=login&redirect=${encodeURIComponent(`/invite/${token}`)}`)}
                      className="btn w-full py-3" data-testid="invite-signin-btn">
                <LogIn className="w-4 h-4"/> Already have one? Sign in
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
