import React, { useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { ArrowRight, KeyRound, CheckCircle2 } from "lucide-react";

export default function Reset() {
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const token = sp.get("token") || "";
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="card-mystic p-8 max-w-md text-center relative z-10">
          <h1 className="font-display text-2xl text-parchment">No reset token</h1>
          <p className="text-mist mt-2">This link is incomplete. Request a fresh one.</p>
          <Link to="/auth?mode=login" className="btn mt-5 inline-flex">Back to sign in</Link>
        </div>
      </div>
    );
  }

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    if (pw !== pw2) { setErr("Passwords don't match."); return; }
    if (pw.length < 6) { setErr("Password must be at least 6 characters."); return; }
    setBusy(true);
    try {
      await api.post("/auth/reset-password", { token, password: pw });
      setDone(true);
      setTimeout(() => nav("/auth?mode=login"), 1800);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative">
      <div className="relative z-10 w-full max-w-md page">
        <Link to="/" className="block text-center mb-8 font-display tracking-[0.35em] text-parchment">
          TABLE<span className="text-gold">·</span>GNOSTIC
        </Link>
        <div className="card-mystic sigil-ring p-8">
          <div className="label-ref flex items-center gap-2 mb-3"><KeyRound className="w-3 h-3"/> Set a new password</div>
          {done ? (
            <div className="text-center py-4">
              <CheckCircle2 className="w-8 h-8 text-gold-bright mx-auto mb-3"/>
              <h1 className="font-display text-2xl text-parchment">Password rewoven</h1>
              <p className="text-mist mt-2 font-body">Returning you to the threshold…</p>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              <div>
                <label className="label-ref block mb-1">New password</label>
                <input type="password" className="input" value={pw} required minLength={6}
                       onChange={(e) => setPw(e.target.value)} data-testid="reset-pw"/>
              </div>
              <div>
                <label className="label-ref block mb-1">Confirm password</label>
                <input type="password" className="input" value={pw2} required minLength={6}
                       onChange={(e) => setPw2(e.target.value)} data-testid="reset-pw2"/>
              </div>
              {err && <div className="text-ember text-sm">{err}</div>}
              <button type="submit" disabled={busy} className="btn btn-primary w-full py-3" data-testid="reset-submit">
                {busy ? "…" : "Reset password"} <ArrowRight className="w-4 h-4"/>
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
