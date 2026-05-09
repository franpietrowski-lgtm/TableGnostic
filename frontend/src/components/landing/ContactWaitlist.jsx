import React, { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { Mail, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ROLE_OPTS = [
  { value: "gm", label: "Game Master" },
  { value: "player", label: "Player" },
  { value: "worldbuilder", label: "Worldbuilder" },
  { value: "homebrew_creator", label: "Homebrew Creator" },
  { value: "publisher", label: "Publisher / Partner" },
];

const SYSTEM_OPTS = [
  "BESM 4E",
  "Anime 5E",
  "Cypher",
  "D&D 5E",
  "Pathfinder",
  "Fate",
  "Mothership",
  "Blades in the Dark",
  "Call of Cthulhu",
  "Savage Worlds",
  "Cyberpunk RED",
  "Vampire: the Masquerade",
  "Shadowrun",
  "Numenera",
  "Other / Mixed",
];

export default function ContactWaitlist() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    location: "",
    role: "gm",
    primary_system: "BESM 4E",
    message: "",
    consent: false,
  });
  const [status, setStatus] = useState({ state: "idle", error: "" });

  const onChange = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.consent) {
      setStatus({ state: "error", error: "Please consent to be contacted." });
      return;
    }
    setStatus({ state: "loading", error: "" });
    try {
      await axios.post(`${API}/leads`, form);
      setStatus({ state: "ok", error: "" });
      setForm({
        name: "", email: "", phone: "", location: "",
        role: "gm", primary_system: "BESM 4E", message: "", consent: false,
      });
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        "Something went sideways. Try again in a moment.";
      setStatus({ state: "error", error: typeof msg === "string" ? msg : "Submission failed." });
    }
  };

  return (
    <section
      id="contact"
      className="relative z-10 px-5 md:px-10 py-24 md:py-32 border-t border-gold/10 bg-void/40"
      data-testid="contact-section"
    >
      <div className="max-w-6xl mx-auto grid lg:grid-cols-[0.95fr_1.05fr] gap-10 lg:gap-16">
        {/* Left — sales copy + alt paths */}
        <div>
          <div className="label-ref mb-4">Contact · waitlist · community</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            Take a seat at the <span className="text-gold italic font-body normal-case">next table.</span>
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            Drop your details and we&rsquo;ll keep you posted on releases,
            marketplace launches, and early-table invitations. Or skip the form
            entirely — make a free GM or Player profile and start your first
            campaign space right now.
          </p>

          <div className="mt-8 grid sm:grid-cols-2 gap-3">
            <Link
              to="/auth?mode=register"
              className="btn btn-primary px-5 py-3 text-sm justify-start"
              data-testid="contact-cta-start-table"
            >
              Begin the Rite — free profile <ArrowRight className="w-4 h-4 ml-auto" />
            </Link>
            <Link
              to="/auth?mode=login"
              className="btn px-5 py-3 text-sm justify-start"
              data-testid="contact-cta-already-have"
            >
              Resume the Rite <ArrowRight className="w-4 h-4 ml-auto" />
            </Link>
          </div>

          <ul className="mt-10 space-y-3 text-sm text-mist/85 font-ui">
            {[
              ["Join the waitlist", "Early access notices for new launches."],
              ["Send feedback", "GM, player, and creator notes go straight to the founder."],
              ["Marketplace inquiry", "If you publish homebrew or partner with creators."],
              ["Bug report", "Reproducible? Even better."],
            ].map(([t, d]) => (
              <li key={t} className="flex gap-3">
                <Mail className="w-3.5 h-3.5 text-gold-bright shrink-0 mt-1" />
                <span>
                  <span className="text-parchment">{t}</span>
                  <span className="text-mist/65"> — {d}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Right — form */}
        <form
          onSubmit={submit}
          className="card-mystic p-6 md:p-8 grid gap-4"
          data-testid="contact-form"
          noValidate
        >
          {status.state === "ok" ? (
            <div
              className="flex flex-col items-center text-center py-12 px-2"
              data-testid="contact-success"
            >
              <CheckCircle2 className="w-12 h-12 text-gold-bright" />
              <div className="mt-5 font-display text-xl text-parchment tracking-widest uppercase">
                Seat reserved.
              </div>
              <p className="mt-3 text-sm text-mist max-w-sm font-body leading-relaxed">
                The Loremaster has your message. You&rsquo;ll hear from
                TableGnostics soon — meanwhile, you can spin up a free profile
                and start a campaign space right away.
              </p>
              <Link
                to="/auth?mode=register"
                className="mt-7 btn btn-primary px-5 py-3 text-sm"
                data-testid="contact-success-cta"
              >
                Begin the Rite <ArrowRight className="w-4 h-4" />
              </Link>
              <button
                type="button"
                onClick={() => setStatus({ state: "idle", error: "" })}
                className="mt-3 text-[11px] text-mist/55 hover:text-mist underline-offset-4 hover:underline"
                data-testid="contact-success-reset"
              >
                Send another message
              </button>
            </div>
          ) : (
            <>
              <div className="grid sm:grid-cols-2 gap-4">
                <Field label="Name" required>
                  <input
                    className="input"
                    value={form.name}
                    onChange={(e) => onChange("name", e.target.value)}
                    placeholder="Your name"
                    required
                    data-testid="contact-input-name"
                  />
                </Field>
                <Field label="Email" required>
                  <input
                    type="email"
                    className="input"
                    value={form.email}
                    onChange={(e) => onChange("email", e.target.value)}
                    placeholder="you@table.com"
                    required
                    data-testid="contact-input-email"
                  />
                </Field>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <Field label="Phone (optional)">
                  <input
                    className="input"
                    value={form.phone}
                    onChange={(e) => onChange("phone", e.target.value)}
                    placeholder="+1 …"
                    data-testid="contact-input-phone"
                  />
                </Field>
                <Field label="Location (city / region, optional)">
                  <input
                    className="input"
                    value={form.location}
                    onChange={(e) => onChange("location", e.target.value)}
                    placeholder="Brooklyn, NY"
                    data-testid="contact-input-location"
                  />
                </Field>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <Field label="Role" required>
                  <select
                    className="select"
                    value={form.role}
                    onChange={(e) => onChange("role", e.target.value)}
                    data-testid="contact-input-role"
                  >
                    {ROLE_OPTS.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Primary system">
                  <select
                    className="select"
                    value={form.primary_system}
                    onChange={(e) => onChange("primary_system", e.target.value)}
                    data-testid="contact-input-system"
                  >
                    {SYSTEM_OPTS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <Field label="Message">
                <textarea
                  className="input"
                  rows={4}
                  value={form.message}
                  onChange={(e) => onChange("message", e.target.value)}
                  placeholder="What kind of table are you running, or what would you like to see?"
                  data-testid="contact-input-message"
                />
              </Field>

              <label className="flex items-start gap-3 mt-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.consent}
                  onChange={(e) => onChange("consent", e.target.checked)}
                  className="mt-1 w-4 h-4 accent-[#c8a34a]"
                  required
                  data-testid="contact-input-consent"
                />
                <span className="text-xs font-ui text-mist/85 leading-relaxed">
                  I&rsquo;m okay with TableGnostics contacting me about
                  releases, demos, marketplace updates, and table invitations.
                  We&rsquo;ll never sell your info.
                </span>
              </label>

              {status.state === "error" && (
                <div
                  className="flex items-center gap-2 text-xs text-ember bg-ember/10 border border-ember/30 rounded-sm px-3 py-2"
                  data-testid="contact-error"
                >
                  <AlertCircle className="w-3.5 h-3.5" />
                  {status.error}
                </div>
              )}

              <button
                type="submit"
                disabled={status.state === "loading"}
                className="btn btn-primary px-6 py-3 text-sm mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
                data-testid="contact-submit"
              >
                {status.state === "loading" ? "Sending…" : "Reserve my seat"}{" "}
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          )}
        </form>
      </div>
    </section>
  );
}

function Field({ label, required, children }) {
  return (
    <label className="block">
      <div className="text-[10px] font-ui uppercase tracking-[0.22em] text-gold/70 mb-1.5">
        {label}
        {required && <span className="text-ember ml-1">*</span>}
      </div>
      {children}
    </label>
  );
}
