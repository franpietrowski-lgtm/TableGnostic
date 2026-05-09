import React from "react";
import { Scroll, Dice6, Users, Network } from "lucide-react";

/**
 * Four glance-pillars matching the language used on rules-forge.emergent.host:
 * Guided Worlds · Live Sessions · Character Forge · Knowledge Web.
 *
 * Sits between the Hero and the System Trust Strip as a quick-read
 * "what does this thing do" badge row before the deeper scene cards.
 */
const PILLARS = [
  {
    id: "worlds",
    icon: Scroll,
    title: "Guided Worlds",
    copy: "Structured worldbuilding workflows that shape tone, factions, and threads into publishable campaigns.",
  },
  {
    id: "sessions",
    icon: Dice6,
    title: "Live Sessions",
    copy: "Initiative, dice, chat, effects, and round-ticks running at the table in real time.",
  },
  {
    id: "forge",
    icon: Users,
    title: "Character Forge",
    copy: "Tri-Stat point-buy, D&D class+slot, and Cypher type/focus/descriptor in one builder — every choice cites its source.",
  },
  {
    id: "web",
    icon: Network,
    title: "Knowledge Web",
    copy: "Role-gated nodes that reveal themselves only when the tale permits it.",
  },
];

export default function Pillars() {
  return (
    <section
      className="relative z-10 px-5 md:px-10 pb-16 md:pb-24"
      data-testid="pillars-section"
    >
      <div className="max-w-6xl mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {PILLARS.map((p) => {
          const Icon = p.icon;
          return (
            <div
              key={p.id}
              className="card-mystic p-5 transition-all duration-500 hover:-translate-y-1 group"
              data-testid={`pillar-${p.id}`}
            >
              <div className="w-9 h-9 mb-4 rounded-sm border border-gold/30 text-gold flex items-center justify-center bg-void/50 group-hover:border-gold-bright group-hover:text-gold-bright transition-colors">
                <Icon className="w-4 h-4" />
              </div>
              <div className="font-display tracking-[0.2em] text-sm text-parchment uppercase">
                {p.title}
              </div>
              <p className="mt-3 text-sm text-mist font-body leading-relaxed">
                {p.copy}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
