import React, { useState } from "react";
import { Crown, Swords, Globe, Hammer } from "lucide-react";

const ROLES = [
  {
    id: "gm",
    label: "GM",
    icon: Crown,
    title: "For GMs who prep like architects.",
    copy: "Build campaigns, approve player contributions, manage reference material, structure encounters, publish homebrew, and export polished table documents.",
    features: [
      "Atelier",
      "Genesis",
      "Director's Console",
      "Approval Queue",
      "Campaign Reference Editor",
      "Genesis Archive",
      "Marketplace Publish",
      "PDF campaign export",
      "Live session tools",
    ],
    quote:
      "My session prep used to live in five tabs. Now it lives in one Codex graph.",
    quoteWho: "— Kept by a GM running a 4-system rotation table",
  },
  {
    id: "player",
    label: "Player",
    icon: Swords,
    title: "For players who want the sheet to keep up.",
    copy: "Build characters, bind macros, track notes, use inventory, manage spells, roll from live stats, and keep play moving.",
    features: [
      "Character Builder",
      "Quick-Roll Bar",
      "Character-aware macros",
      "Spell Tracker",
      "Folio",
      "Journal",
      "Inventory",
      "Consent Checkbox",
      "Live session access",
    ],
    quote:
      "I built the character, bound the moves, and knew exactly why the roll was what it was.",
    quoteWho: "— Player, BESM 4E ongoing campaign",
  },
  {
    id: "worldbuilder",
    label: "Worldbuilder",
    icon: Globe,
    title: "For worldbuilders who need more than folders.",
    copy: "Turn lore into linked, searchable, exportable structure. Factions, places, histories, characters, relics, mysteries, and plot threads can all connect.",
    features: [
      "Codex Knowledge Graph",
      "World Creation Tree",
      "Reference Editor",
      "Canon Registry",
      "Linked lore nodes",
      "Public world publishing path",
      "Markdown / PDF exports",
    ],
    quote:
      "My worldbook became something my players could actually navigate.",
    quoteWho: "— Worldbuilder, multi-campaign setting",
  },
  {
    id: "homebrew",
    label: "Homebrew Creator",
    icon: Hammer,
    title: "For creators who want their mechanics to travel.",
    copy: "Author feats, classes, powers, bundles, races, traits, items, weapons, and house rules once — then clone, publish, revise, and share them across tables.",
    features: [
      "Custom Rules",
      "Power Bundles",
      "BESM Templates",
      "Item / Weapon Mod Pools",
      "Marketplace V1",
      "Watch List + Digest",
      "License Attestation",
      "Future Paywall Support",
    ],
    quote: "Author it once. Share it everywhere.",
    quoteWho: "— Homebrew creator, Marketplace V1 early author",
  },
];

export default function RoleTour() {
  const [active, setActive] = useState("gm");
  const role = ROLES.find((r) => r.id === active);

  return (
    <section id="roles" className="relative z-10 px-5 md:px-10 py-24 md:py-32" data-testid="role-tour-section">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <div className="label-ref mb-4">Role-based tour</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            Built for the <span className="text-gold italic font-body normal-case">whole table</span> — not just the GM.
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            TableGnostics changes shape based on who is using it: GM, player,
            worldbuilder, or homebrew creator.
          </p>
        </div>

        <div className="mt-12 grid lg:grid-cols-[280px_1fr] gap-6 lg:gap-10">
          {/* Tab rail */}
          <div className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible scroll-stylish pb-2 lg:pb-0">
            {ROLES.map((r) => {
              const Icon = r.icon;
              const isActive = r.id === active;
              return (
                <button
                  key={r.id}
                  onClick={() => setActive(r.id)}
                  className={`text-left whitespace-nowrap px-5 py-4 rounded-sm border-l-2 transition-all flex items-center gap-3 ${
                    isActive
                      ? "bg-gold/10 border-gold text-gold-bright"
                      : "bg-ink/40 border-transparent text-mist hover:bg-gold/5 hover:text-parchment border-l-2"
                  }`}
                  data-testid={`role-tab-${r.id}`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <div>
                    <div className="font-display tracking-[0.22em] text-sm uppercase">
                      {r.label}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Active panel */}
          <div className="card-mystic p-6 md:p-9" data-testid={`role-panel-${role.id}`}>
            <div className="label-ref mb-3">{role.label} workflow</div>
            <h3 className="font-display text-2xl md:text-3xl text-parchment leading-tight">
              {role.title}
            </h3>
            <p className="mt-4 text-mist font-body text-base leading-relaxed">
              {role.copy}
            </p>

            <div className="mt-7 grid sm:grid-cols-2 gap-x-6 gap-y-1.5">
              {role.features.map((f) => (
                <div key={f} className="text-sm text-mist/90 font-ui flex gap-2">
                  <span className="text-gold mt-0.5">◆</span> {f}
                </div>
              ))}
            </div>

            <blockquote className="mt-8 border-l border-gold/40 pl-5 italic font-body text-base md:text-lg text-parchment/90 leading-relaxed">
              &ldquo;{role.quote}&rdquo;
              <div className="not-italic mt-2 text-[11px] font-ui tracking-widest uppercase text-gold/60">
                {role.quoteWho}
              </div>
            </blockquote>
          </div>
        </div>
      </div>
    </section>
  );
}
