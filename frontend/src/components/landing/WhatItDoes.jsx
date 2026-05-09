import React from "react";
import { Globe2, UserCog, MessagesSquare, ArrowRight } from "lucide-react";

const CARDS = [
  {
    id: "world-first",
    title: "Build the world before the session collapses into notes.",
    icon: Globe2,
    copy: "Use Genesis, Codex, and the World Creation Tree to turn factions, locations, NPCs, motives, histories, and mysteries into a browsable campaign graph.",
    bullets: [
      "Genesis 7-phase plot designer",
      "Codex Knowledge Graph",
      "World Creation Tree",
      "Linked NPC motives, resources, weaknesses",
      "Campaign reference editor",
      "Exportable lore",
    ],
    cta: "See worldbuilding tools",
    target: "#features",
    visual: "world",
    accent: "gold",
  },
  {
    id: "character-smart",
    title: "Your sheet knows what your character can actually do.",
    icon: UserCog,
    copy: "Character-aware macros pull from the live sheet, not a generic rules stub. Attributes, skills, defects, derived values, HP, EP, enhancements, limiters, and item ranks feed directly into rolls.",
    bullets: [
      "Quick-Roll Bar",
      "Click-to-insert Macro Builder",
      "Per-row macro sprinkles",
      "BESM enhancement / limiter ranks",
      "Item & weapon-specific modifiers",
      "Live preview before roll firing",
    ],
    cta: "See character automation",
    target: "#features",
    visual: "character",
    accent: "arcane",
  },
  {
    id: "table-aware",
    title: "The chat layer is the rules layer.",
    icon: MessagesSquare,
    copy: "Slash commands resolve server-side, so refreshes do not erase the table state. Players fire saved macros from chat or bound sheet slots; GMs audit what happened.",
    bullets: [
      "/roll · /cast · /use bundle · /spend xp",
      "/undo with audit trail",
      "User-defined macros",
      "XP marketplace proposals",
      "Auditable table actions",
      "Session state preservation",
    ],
    cta: "See session tools",
    target: "#features",
    visual: "table",
    accent: "ember",
  },
];

export default function WhatItDoes() {
  return (
    <section id="what" className="relative z-10 px-5 md:px-10 py-24 md:py-32" data-testid="what-section">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <div className="label-ref mb-4">What TableGnostics does</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            Everything your table keeps losing <span className="text-gold italic font-body normal-case">between tools.</span>
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            Worldbuilding, character math, play-by-post, live sessions, homebrew,
            exports, and campaign memory — built to work together instead of sitting
            in separate tabs.
          </p>
        </div>

        <div className="mt-16 grid lg:grid-cols-3 gap-6">
          {CARDS.map((c, i) => (
            <SceneCard key={c.id} card={c} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

function SceneCard({ card, index }) {
  const Icon = card.icon;
  const accentText = {
    gold: "text-gold-bright",
    arcane: "text-arcane",
    ember: "text-ember",
  }[card.accent];
  const accentBorder = {
    gold: "border-gold/40",
    arcane: "border-arcane/50",
    ember: "border-ember/50",
  }[card.accent];

  return (
    <div
      className="card-mystic p-6 md:p-7 flex flex-col group transition-all duration-500 hover:-translate-y-1"
      data-testid={`scene-card-${card.id}`}
    >
      <div className={`mb-5 w-11 h-11 rounded-sm border ${accentBorder} ${accentText} flex items-center justify-center bg-void/60`}>
        <Icon className="w-5 h-5" />
      </div>

      {/* visual mock */}
      <SceneVisual variant={card.visual} accent={card.accent} />

      <div className="mt-6 text-[10px] font-ui uppercase tracking-[0.3em] text-gold/55">
        Scene 0{index + 1}
      </div>
      <h3 className="mt-2 font-display text-lg md:text-xl text-parchment leading-snug">
        {card.title}
      </h3>
      <p className="mt-3 text-sm text-mist font-body leading-relaxed">
        {card.copy}
      </p>

      <ul className="mt-5 space-y-1.5">
        {card.bullets.map((b) => (
          <li key={b} className="text-xs text-mist/85 font-ui flex gap-2">
            <span className={`${accentText} mt-0.5`}>◆</span>
            <span>{b}</span>
          </li>
        ))}
      </ul>

      <a
        href={card.target}
        className={`mt-6 inline-flex items-center gap-1.5 text-[11px] font-ui uppercase tracking-[0.22em] ${accentText} hover:underline underline-offset-4`}
        data-testid={`scene-cta-${card.id}`}
      >
        {card.cta} <ArrowRight className="w-3 h-3" />
      </a>
    </div>
  );
}

/**
 * Stylized abstract "screenshot" device per scene — pure CSS/SVG so the
 * page stays under the perf budget.
 */
function SceneVisual({ variant, accent }) {
  const accentHex = { gold: "#c8a34a", arcane: "#a999d6", ember: "#c25646" }[accent];
  if (variant === "world") {
    return (
      <div className="relative h-40 rounded-sm border border-gold/15 bg-gradient-to-br from-ink to-void overflow-hidden">
        <svg viewBox="0 0 200 120" className="w-full h-full">
          <defs>
            <radialGradient id="wg" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stopColor={accentHex} stopOpacity="0.18" />
              <stop offset="100%" stopColor={accentHex} stopOpacity="0" />
            </radialGradient>
          </defs>
          <rect width="200" height="120" fill="url(#wg)" />
          {/* nodes */}
          {[
            [40, 30], [90, 22], [150, 38], [60, 70], [130, 85], [170, 70], [100, 95],
          ].map(([x, y], i) => (
            <g key={i}>
              <circle cx={x} cy={y} r="4" fill={accentHex} opacity="0.85" />
              <circle cx={x} cy={y} r="9" fill="none" stroke={accentHex} strokeWidth="0.5" opacity="0.4" />
            </g>
          ))}
          {/* edges */}
          <g stroke={accentHex} strokeWidth="0.6" opacity="0.55" fill="none">
            <line x1="40" y1="30" x2="90" y2="22" />
            <line x1="90" y1="22" x2="150" y2="38" />
            <line x1="150" y1="38" x2="170" y2="70" />
            <line x1="170" y1="70" x2="130" y2="85" />
            <line x1="130" y1="85" x2="100" y2="95" />
            <line x1="60" y1="70" x2="100" y2="95" />
            <line x1="60" y1="70" x2="40" y2="30" />
            <line x1="90" y1="22" x2="60" y2="70" />
          </g>
        </svg>
        <div className="absolute top-2 left-2 text-[9px] font-mono text-gold/70">CODEX_GRAPH</div>
        <div className="absolute bottom-2 right-2 text-[9px] font-mono text-mist/60">7 nodes · 8 edges</div>
      </div>
    );
  }
  if (variant === "character") {
    return (
      <div className="relative h-40 rounded-sm border border-arcane/25 bg-gradient-to-br from-ink to-void overflow-hidden p-3">
        <div className="text-[9px] font-mono text-arcane mb-2">CHARACTER · BESM 4E</div>
        {[
          { label: "BODY", val: "8", mod: "+3" },
          { label: "MIND", val: "9", mod: "+4" },
          { label: "SOUL", val: "7", mod: "+2" },
        ].map((s, i) => (
          <div key={i} className="flex items-center gap-2 mb-1.5">
            <span className="text-[10px] font-ui tracking-widest text-mist/75 w-12">{s.label}</span>
            <div className="flex-1 h-1.5 bg-void rounded-sm overflow-hidden">
              <div
                className="h-full"
                style={{ width: `${parseInt(s.val) * 10}%`, background: accentHex }}
              />
            </div>
            <span className="text-[10px] font-mono text-parchment w-6 text-right">{s.val}</span>
            <span className="text-[10px] font-mono text-arcane w-8 text-right">{s.mod}</span>
            <span className="text-[10px] text-arcane">✦</span>
          </div>
        ))}
        <div className="mt-3 px-2 py-1 border border-arcane/30 rounded-sm bg-void/50 font-mono text-[9px] text-arcane">
          /macro: 2d6 + MIND_mod + skill(Occult)
        </div>
      </div>
    );
  }
  // table-aware
  return (
    <div className="relative h-40 rounded-sm border border-ember/25 bg-gradient-to-br from-ink to-void overflow-hidden p-3">
      <div className="text-[9px] font-mono text-ember mb-2">SESSION · CHAT</div>
      <div className="space-y-1">
        <div className="text-[10px] font-mono">
          <span className="text-gold/80">GM</span>{" "}
          <span className="text-mist/85">The dragon stirs.</span>
        </div>
        <div className="text-[10px] font-mono">
          <span className="text-arcane">Kael</span>{" "}
          <span className="text-mist/85">/cast fireball</span>
        </div>
        <div className="text-[10px] font-mono pl-4 text-ember">
          → 8d6 fire = <span className="font-bold text-gold-bright">31</span>
        </div>
        <div className="text-[10px] font-mono">
          <span className="text-arcane">Mira</span>{" "}
          <span className="text-mist/85">/use bundle &quot;Sword Flourish&quot;</span>
        </div>
        <div className="text-[10px] font-mono pl-4 text-gold/85">
          → atk 17 hit · 2d8+4 = 13
        </div>
        <div className="text-[10px] font-mono text-mist/55">
          <span className="text-ember/85">/spend xp 5 → Bundle approved by GM ✓</span>
        </div>
      </div>
    </div>
  );
}
