import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../lib/api";
import { ArrowRight, Sparkles, LogIn, UserPlus } from "lucide-react";

export default function Auth() {
  const { user, login, register } = useAuth();
  const nav = useNavigate();
  const [sp] = useSearchParams();
  const [mode, setMode] = useState(sp.get("mode") || "login");
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (user) nav(sp.get("redirect") || "/app"); }, [user, nav, sp]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form.email, form.password, form.name);
      nav(sp.get("redirect") || "/app");
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const fillDemo = (role) => {
    if (role === "gm") setForm({ ...form, email: "gm@tablegnostic.com", password: "gm123456" });
    if (role === "player") setForm({ ...form, email: "player@tablegnostic.com", password: "player12345" });
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative px-4">
      <div className="relative z-10 w-full max-w-md page">
        <Link to="/" className="block text-center mb-8 font-display tracking-[0.35em] text-parchment" data-testid="brand-link">
          TABLE<span className="text-gold">·</span>GNOSTIC
        </Link>

        <div className="card-mystic sigil-ring p-8">
          <div className="label-ref flex items-center gap-2 mb-3"><Sparkles className="w-3 h-3" /> The table awaits</div>
          <h1 className="font-display text-3xl tracking-wide mb-2 text-parchment">
            {mode === "login" ? "Return to the table" : "Take a seat"}
          </h1>
          <p className="text-sm text-mist mb-6 font-body">
            {mode === "login" ? "Speak the words that know you." : "Craft the name by which the table will know you."}
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="label-ref block mb-1">Name</label>
                <input className="input" value={form.name} required
                       onChange={(e) => setForm({ ...form, name: e.target.value })}
                       data-testid="auth-name-input" />
              </div>
            )}
            <div>
              <label className="label-ref block mb-1">Email</label>
              <input className="input" type="email" value={form.email} required
                     onChange={(e) => setForm({ ...form, email: e.target.value })}
                     data-testid="auth-email-input" autoComplete="email" />
            </div>
            <div>
              <label className="label-ref block mb-1">Password</label>
              <input className="input" type="password" value={form.password} required minLength={6}
                     onChange={(e) => setForm({ ...form, password: e.target.value })}
                     data-testid="auth-password-input"
                     autoComplete={mode === "login" ? "current-password" : "new-password"} />
            </div>

            {err && <div className="text-sm text-ember font-ui" data-testid="auth-error">{err}</div>}

            <button type="submit" disabled={busy}
                    className="btn btn-primary w-full py-3" data-testid="auth-submit-btn">
              {busy ? "…" : mode === "login" ? <><LogIn className="w-4 h-4" /> Sign In</> : <><UserPlus className="w-4 h-4" /> Create Account</>}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="divider-sigil my-6" />

          <div className="flex items-center justify-between text-xs">
            <button onClick={() => setMode(mode === "login" ? "register" : "login")}
                    className="text-gold/80 hover:text-gold-bright font-ui tracking-wider uppercase"
                    data-testid="auth-toggle-mode">
              {mode === "login" ? "New here? Take a seat" : "Already seated? Sign in"}
            </button>
          </div>

          <div className="mt-6">
            <div className="label-ref mb-2">Try a demo identity</div>
            <div className="flex gap-2">
              <button type="button" onClick={() => fillDemo("gm")} className="btn btn-ghost text-xs flex-1" data-testid="demo-gm-btn">Demo GM</button>
              <button type="button" onClick={() => fillDemo("player")} className="btn btn-ghost text-xs flex-1" data-testid="demo-player-btn">Demo Player</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
