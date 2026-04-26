import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../lib/api";
import { ArrowRight, Sparkles, LogIn, UserPlus } from "lucide-react";

export default function Auth() {
  const { user, login, register } = useAuth();
  const nav = useNavigate();
  const [sp] = useSearchParams();
  const [mode, setMode] = useState(sp.get("mode") || "login");
  const [form, setForm] = useState({ email: "", password: "", name: "", role: "player" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (user) nav(sp.get("redirect") || "/app"); }, [user, nav, sp]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form.email, form.password, form.name, form.role);
      nav(sp.get("redirect") || "/app");
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
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
              <>
                <div>
                  <label className="label-ref block mb-1">Name</label>
                  <input className="input" value={form.name} required
                         onChange={(e) => setForm({ ...form, name: e.target.value })}
                         data-testid="auth-name-input" />
                </div>
                <div>
                  <label className="label-ref block mb-2">I'm here to…</label>
                  <div className="grid grid-cols-2 gap-2" data-testid="auth-role-picker">
                    {[
                      ["player", "Take a seat", "Play in campaigns hosted by GMs."],
                      ["gm", "Run the table", "Host campaigns; build worlds; run sessions."],
                    ].map(([v, t, sub]) => (
                      <button key={v} type="button" onClick={() => setForm({ ...form, role: v })}
                              data-testid={`auth-role-${v}`}
                              className={`p-3 text-left rounded-sm border transition ${form.role === v ? "border-gold/70 bg-gold/5" : "border-gold/15 hover:border-gold/40"}`}>
                        <div className="font-ui text-xs uppercase tracking-widest text-gold-bright">{t}</div>
                        <div className="text-[11px] text-mist mt-1 font-body leading-snug">{sub}</div>
                      </button>
                    ))}
                  </div>
                  <div className="text-[10px] text-mist/70 italic mt-1.5">
                    Players can switch to GM later from their profile.
                  </div>
                </div>
              </>
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
            {mode === "login" && (
              <button type="button" onClick={async () => {
                const email = window.prompt("Email for the reset link?", form.email);
                if (!email) return;
                try {
                  await (await import("../lib/api")).api.post("/auth/forgot-password", { email });
                  alert("If that email is on file, a reset link has been sent.");
                } catch { alert("Could not send reset email."); }
              }} className="text-mist/70 hover:text-gold-bright font-ui tracking-wider uppercase" data-testid="forgot-pw-btn">
                Forgot?
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
