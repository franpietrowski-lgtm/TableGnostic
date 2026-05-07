import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Play, Sparkles } from "lucide-react";
import Sigil from "./Sigil";

/**
 * Hero — left copy column, right animated sigil device. Mobile stacks.
 * Microcopy line names the four flagship systems for instant trust.
 */
export default function Hero({ user }) {
  const nav = useNavigate();

  return (
    <section
      id="hero"
      className="relative z-10 pt-32 md:pt-40 pb-24 md:pb-36 px-5 md:px-10"
      data-testid="hero-section"
    >
      <div className="max-w-7xl mx-auto grid lg:grid-cols-[1.1fr_0.9fr] gap-12 lg:gap-16 items-center">
        {/* LEFT — copy column */}
        <div>
          <div className="label-ref mb-7 flex items-center gap-2" data-testid="hero-eyebrow">
            <Sparkles className="w-3 h-3" />
            <span>A worldbuilding-first tabletop platform</span>
          </div>

          <h1 className="font-display text-[clamp(2.6rem,7vw,5.6rem)] leading-[0.98] text-parchment uppercase tracking-tight">
            <span className="block">Not the</span>
            <span className="block text-gold/90">system.</span>
            <span className="block italic font-body normal-case text-gold tracking-tight">
              The table.
            </span>
          </h1>

          <p className="mt-9 max-w-xl font-body text-lg md:text-xl leading-relaxed text-mist">
            For GMs, players, and homebrew creators tired of duct-taping Discord,
            sheets, docs, VTT notes, and worldbuilding wikis together to run one
            great campaign.
          </p>

          <p className="mt-5 max-w-xl font-body text-base leading-relaxed text-mist/80">
            Build worlds. Seat players. Automate character math. Run play-by-post.
            Support live sessions. Publish homebrew. Keep your lore, rules,
            characters, notes, and table history in one living campaign space.
          </p>

          <div className="mt-10 flex flex-wrap gap-3">
            <button
              onClick={() => nav(user ? "/app" : "/auth?mode=register")}
              className="btn btn-primary px-7 py-3.5 text-sm"
              data-testid="hero-cta-take-a-seat"
            >
              Take a Seat <ArrowRight className="w-4 h-4" />
            </button>
            <a
              href="#what"
              className="btn px-6 py-3.5 text-sm"
              data-testid="hero-cta-watch-tour"
            >
              <Play className="w-4 h-4" /> Watch the Table Tour
            </a>
          </div>

          {!user && (
            <div className="mt-6 text-xs font-ui text-mist/60">
              Already have a table?{" "}
              <Link
                to="/auth?mode=login"
                className="text-gold hover:text-gold-bright underline-offset-4 hover:underline"
                data-testid="hero-tertiary-login"
              >
                Open the app →
              </Link>
            </div>
          )}

          <div className="mt-12 divider-sigil max-w-md" />
          <p
            className="mt-5 text-[11px] font-ui tracking-[0.32em] uppercase text-gold/65"
            data-testid="hero-systems-microcopy"
          >
            BESM 4E · Anime 5E · Cypher · D&amp;D 5E · 9 more scaffolded
          </p>
        </div>

        {/* RIGHT — animated sigil device */}
        <div className="relative hidden lg:flex items-center justify-center">
          <HeroDevice />
        </div>
      </div>
    </section>
  );
}

function HeroDevice() {
  return (
    <div className="relative w-full aspect-square max-w-[520px]" data-testid="hero-device">
      {/* outer rotating ring */}
      <div className="absolute inset-0 rounded-full border border-gold/20 animate-[heroSpin_60s_linear_infinite]" />
      <div className="absolute inset-6 rounded-full border border-gold/10 animate-[heroSpin_90s_linear_reverse_infinite]" />
      <div className="absolute inset-12 rounded-full border border-arcane/20" />

      {/* radial glow */}
      <div
        className="absolute inset-0 rounded-full opacity-60"
        style={{
          background:
            "radial-gradient(circle at 50% 50%, rgba(212,175,55,0.18) 0%, rgba(109,74,158,0.10) 45%, transparent 70%)",
        }}
      />

      {/* central sigil */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="animate-flicker">
          <Sigil size={220} />
        </div>
      </div>

      {/* orbiting interface flashes */}
      <OrbitChip
        label="/cast fireball"
        cls="top-2 left-1/2 -translate-x-1/2"
        accent="gold"
        delay="0s"
      />
      <OrbitChip
        label="Codex node · faction"
        cls="right-0 top-1/3"
        accent="arcane"
        delay="0.6s"
      />
      <OrbitChip
        label="Macro · 2d6+STR"
        cls="bottom-2 left-1/2 -translate-x-1/2"
        accent="gold"
        delay="1.2s"
      />
      <OrbitChip
        label="Marketplace · clone"
        cls="left-0 top-1/2"
        accent="ember"
        delay="1.8s"
      />
      <OrbitChip
        label="PDF export"
        cls="right-4 bottom-8"
        accent="arcane"
        delay="2.4s"
      />

      {/* system glyphs */}
      <SystemGlyph cls="top-12 right-12" label="BESM 4E" />
      <SystemGlyph cls="bottom-12 right-12" label="A5E" />
      <SystemGlyph cls="bottom-12 left-12" label="CYPHER" />
      <SystemGlyph cls="top-12 left-12" label="D&D 5E" />

      <style>{`
        @keyframes heroSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes heroFloat {
          0%, 100% { transform: translateY(0); opacity: 0.85; }
          50%      { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

function OrbitChip({ label, cls, accent = "gold", delay = "0s" }) {
  const colors = {
    gold: "border-gold/45 text-gold-bright",
    arcane: "border-arcane/50 text-arcane",
    ember: "border-ember/50 text-ember",
  };
  return (
    <div
      className={`absolute ${cls} bg-void/85 backdrop-blur px-3 py-1.5 rounded-sm border ${colors[accent]} font-mono text-[10px] tracking-wider shadow-sigil`}
      style={{ animation: `heroFloat 4s ease-in-out infinite`, animationDelay: delay }}
    >
      {label}
    </div>
  );
}

function SystemGlyph({ cls, label }) {
  return (
    <div
      className={`absolute ${cls} w-12 h-12 rounded-full border border-gold/30 bg-ink/80 backdrop-blur flex items-center justify-center font-display text-[10px] tracking-widest text-gold`}
    >
      {label}
    </div>
  );
}
