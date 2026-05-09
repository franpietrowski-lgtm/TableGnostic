import React from "react";
import {
  Sparkles,
  Network,
  TreePine,
  Wand2,
  MousePointerClick,
  Sliders,
  Sword,
  Terminal,
  Store,
  Archive,
  Download,
  Smartphone,
} from "lucide-react";

const FEATURES = [
  {
    title: "Genesis Plot Designer",
    icon: Sparkles,
    copy: "A seven-phase structure for turning campaign ideas into playable foundations.",
  },
  {
    title: "Codex Knowledge Graph",
    icon: Network,
    copy: "Characters, factions, locations, lore, histories, motives, and mysteries become connected nodes instead of buried notes.",
  },
  {
    title: "World Creation Tree",
    icon: TreePine,
    copy: "Organize worldbuilding across population, geography, history, culture, conflict, and campaign-facing play material.",
  },
  {
    title: "Character-Aware Macros",
    icon: Wand2,
    copy: "Build rolls from actual sheet values: stats, attributes, skills, defects, derived values, HP, EP, sanity, and custom formulas.",
  },
  {
    title: "Add Rolls From the Sheet",
    icon: MousePointerClick,
    copy: "Click a wand beside a stat, derived value, attribute, skill, or defect to seed a macro from that exact row.",
  },
  {
    title: "BESM Modifier Ranks",
    icon: Sliders,
    copy: "Range ×4 is not the same thing as Range ×1. TableGnostics tracks rank-weighted enhancements and limiters.",
  },
  {
    title: "Item and Weapon Mods",
    icon: Sword,
    copy: "Weapons and item-like attributes can surface their own enhancement and limiter pools, with source notes and rank costs.",
  },
  {
    title: "Play-by-Post That Resolves",
    icon: Terminal,
    copy: "Use slash commands like /cast, /use bundle, and /spend xp to keep table actions readable and auditable.",
  },
  {
    title: "Homebrew Marketplace",
    icon: Store,
    copy: "Publish custom content, browse table-ready homebrew, clone entries into campaigns, and track marketplace interest.",
  },
  {
    title: "Genesis Archive",
    icon: Archive,
    copy: "Snapshot, inspect, restore, or delete Genesis versions without losing the campaign's development history.",
  },
  {
    title: "Take the Campaign With You",
    icon: Download,
    copy: "Export campaign and character material as Markdown, JSON, or PDF so your table is never trapped.",
  },
  {
    title: "Built for the Table, Not Just the Desk",
    icon: Smartphone,
    copy: "Mobile navigation, touch targets, sticky sheet tabs, stacked cards, and gesture-aware views keep play usable on smaller screens.",
  },
];

export default function FeatureHighlights() {
  return (
    <section id="features" className="relative z-10 px-5 md:px-10 py-24 md:py-32" data-testid="features-section">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <div className="label-ref mb-4">Feature highlights</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            The pieces that make the table <span className="text-gold italic font-body normal-case">feel whole.</span>
          </h2>
        </div>

        <div className="mt-14 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className="card-mystic p-5 md:p-6 transition-all duration-500 hover:-translate-y-1 group"
                data-testid={`feature-card-${i}`}
              >
                <div className="w-9 h-9 mb-4 rounded-sm border border-gold/30 text-gold flex items-center justify-center bg-void/50 group-hover:border-gold-bright group-hover:text-gold-bright transition-colors">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="font-display text-base text-parchment leading-snug uppercase tracking-wide">
                  {f.title}
                </div>
                <p className="mt-3 text-sm text-mist font-body leading-relaxed">
                  {f.copy}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
