import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/api";
import { Dice6, Scroll, Network, Users, ArrowRight, Sparkles } from "lucide-react";

const Sigil = ({ className = "" }) => (
  <svg viewBox="0 0 120 120" className={className} xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="g1" x1="0" x2="1">
        <stop offset="0" stopColor="#e5c370" />
        <stop offset="1" stopColor="#8a6b20" />
      </linearGradient>
    </defs>
    <circle cx="60" cy="60" r="52" fill="none" stroke="url(#g1)" strokeWidth="1" opacity="0.8" />
    <circle cx="60" cy="60" r="44" fill="none" stroke="url(#g1)" strokeWidth="0.5" opacity="0.5" />
    <polygon points="60,18 72,38 96,40 78,56 82,80 60,68 38,80 42,56 24,40 48,38"
             fill="none" stroke="url(#g1)" strokeWidth="1.1" opacity="0.9" />
    <polygon points="60,40 70,56 60,72 50,56" fill="url(#g1)" opacity="0.25" />
    <text x="60" y="64" textAnchor="middle" fill="#e5c370" fontFamily="Cinzel, serif"
          fontSize="10" letterSpacing="3">TG</text>
  </svg>
);

export default function Landing() {
  const { user } = useAuth();
  const nav = useNavigate();

  return (
    <div className="page min-h-screen relative">
      <nav className="relative z-20 flex items-center justify-between px-6 md:px-10 py-6">
        <div className="flex items-center gap-3" data-testid="brand">
          <Sigil className="w-9 h-9 logo-mark" />
          <span className="font-display tracking-[0.35em] text-lg text-parchment">TABLE<span className="text-gold">·</span>GNOSTIC</span>
        </div>
        <div className="flex items-center gap-2">
          {user && user !== false ? (
            <button onClick={() => nav("/app")} className="btn" data-testid="enter-app-btn">
              Enter the Table <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <>
              <Link to="/auth?mode=login" className="btn btn-ghost" data-testid="nav-login">Sign In</Link>
              <Link to="/auth?mode=register" className="btn btn-primary" data-testid="nav-register">
                Take a Seat <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* HERO */}
      <section className="relative z-10 px-6 md:px-10 pt-10 md:pt-20 pb-28 max-w-6xl mx-auto">
        <div className="label-ref mb-6 flex items-center gap-2"><Sparkles className="w-3 h-3" /> An all-system-aware tabletop platform</div>
        <h1 className="font-display text-5xl md:text-7xl leading-[1.02] text-parchment">
          Not the system.
          <br />
          <span className="text-gold italic font-body">The table.</span>
        </h1>
        <p className="mt-8 text-mist max-w-2xl font-body text-lg md:text-xl leading-relaxed">
          A system-aware tabletop engine where rules execute, worlds organise, and revelation
          unfolds at the pace of the table. Build characters, run sessions, weave knowledge,
          discover new games — all citing sources, never reproducing them.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <button onClick={() => nav(user ? "/app" : "/auth?mode=register")}
                  className="btn btn-primary px-6 py-3" data-testid="cta-primary">
            Begin the Rite <ArrowRight className="w-4 h-4" />
          </button>
          <Link to="/auth?mode=login" className="btn px-6 py-3" data-testid="cta-secondary">
            I already have a seat
          </Link>
        </div>
        <div className="mt-14 divider-sigil max-w-sm" />
        <p className="mt-6 text-xs font-ui tracking-widest uppercase text-gold/60">
          Connection · Imagination · Revelation
        </p>
      </section>

      {/* PILLARS */}
      <section className="relative z-10 px-6 md:px-10 pb-24 max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            { icon: <Scroll className="w-5 h-5" />, t: "Guided Worlds", d: "Structured worldbuilding workflows that shape tone, factions, and threads into publishable campaigns." },
            { icon: <Dice6 className="w-5 h-5" />, t: "Live Sessions", d: "Initiative, dice, chat, effects, and round-ticks running at the table in real time." },
            { icon: <Users className="w-5 h-5" />, t: "Character Forge", d: "Tri-Stat point-buy, D&D class+slot, and Cypher type/focus/descriptor all in one builder — every choice cites its source." },
            { icon: <Network className="w-5 h-5" />, t: "Knowledge Web", d: "Role-gated nodes that reveal themselves only when the tale permits it." },
          ].map((p, i) => (
            <div key={i} className="card-mystic p-5 transition-transform duration-500 hover:-translate-y-1" data-testid={`pillar-${i}`}>
              <div className="w-9 h-9 flex items-center justify-center rounded-sm border border-gold/30 text-gold mb-4">
                {p.icon}
              </div>
              <div className="font-display tracking-[0.2em] text-sm text-parchment uppercase">{p.t}</div>
              <p className="mt-3 text-sm text-mist font-body leading-relaxed">{p.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* MANIFESTO */}
      <section className="relative z-10 px-6 md:px-10 pb-36 max-w-4xl mx-auto">
        <div className="label-ref mb-4">The table-gnostic creed</div>
        <blockquote className="font-body italic text-xl md:text-2xl text-parchment/90 leading-relaxed border-l border-gold/40 pl-6">
          "A table-gnostic is a tabletop player or creator who prioritises connection,
          experience, and shared imagination over any specific game system—treating the table
          itself as the primary engine of play."
        </blockquote>
        <div className="mt-10 text-xs font-ui uppercase tracking-[0.3em] text-gold/60">
          BESM 4E · Anime 5E · D&amp;D 5E · Cypher System · source-referenced · never reproduced
        </div>
      </section>

      {/* SYSTEM SHOWCASE */}
      <section className="relative z-10 px-6 md:px-10 pb-24 max-w-5xl mx-auto" data-testid="landing-systems">
        <div className="label-ref mb-3 text-center">Systems Currently Supported</div>
        <div className="text-mist text-sm font-body italic text-center mb-8">
          Mechanic-aware integration for these rule-sets — full reference, character forging, dice macros, and PDF chronicle exports for each.
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 items-center justify-items-center">
          {[
            { id: "besm-4e",  label: "BESM Fourth Edition",       img: "/system-logos/besm-4e.png" },
            { id: "anime-5e", label: "Anime 5E (Tri-Stat OGL)",   img: "/system-logos/anime5e-tristat-emporium.png" },
            { id: "dnd-5e",   label: "D&D 5E (CC-BY SRD 5.1)",    img: null },
            { id: "cypher",   label: "Cypher System Creator",     img: "/system-logos/cypher.png" },
          ].map((s) => (
            <div key={s.id} className="flex flex-col items-center gap-2 opacity-90 hover:opacity-100 transition-opacity"
                 data-testid={`landing-system-${s.id}`}>
              {s.img ? (
                <img src={s.img} alt={s.label}
                     className="h-14 w-auto max-w-[140px] object-contain"
                     onError={(e) => { e.currentTarget.style.display = "none"; }}/>
              ) : (
                <div className="h-14 w-[140px] flex items-center justify-center border border-gold/30 rounded-sm bg-void/40">
                  <span className="font-display text-2xl text-gold tracking-widest">D&amp;D</span>
                </div>
              )}
              <div className="text-[10px] font-ui uppercase tracking-widest text-mist/80 text-center leading-snug">
                {s.label}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-8 text-[10px] text-mist/60 italic text-center font-body max-w-3xl mx-auto leading-snug">
          Trademarks belong to their respective rights-holders. Tri-Stat Emporium · Dyskami Publishing · Wizards of the Coast · Monte Cook Games. TableGnostic displays only mechanic names and page references — never reproduced rulebook prose, lore, or art.
        </div>
      </section>

      <footer className="relative z-10 border-t border-gold/10 py-6 px-6 text-center text-xs font-ui tracking-widest uppercase text-mist/60">
        Table-Gnostic · A scrying glass for tabletops
      </footer>
    </div>
  );
}
