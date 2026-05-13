import React, { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
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
  Newspaper,
  ArrowRight,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
  // V6.25.40 — Live "Recently Pressed" gazette ribbon under the feature
  // grid. Driven by `/api/public/recent-gazettes` (only campaigns with
  // `discover_published=true` contribute issues). Hidden when zero
  // issues have ever been pressed publicly.
  const [gazettes, setGazettes] = useState([]);
  useEffect(() => {
    let cancel = false;
    axios.get(`${API}/public/recent-gazettes?limit=3`)
      .then((r) => !cancel && setGazettes(r.data.items || []))
      .catch(() => !cancel && setGazettes([]));
    return () => { cancel = true; };
  }, []);

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

        {gazettes.length > 0 && (
          <div className="mt-14" data-testid="recent-gazettes-ribbon">
            <div className="flex items-end justify-between flex-wrap mb-4 gap-3">
              <div>
                <div className="label-ref mb-1 flex items-center gap-2">
                  <Newspaper className="w-3 h-3 text-gold/60"/>
                  Recently pressed
                </div>
                <h3 className="font-display text-xl md:text-2xl text-parchment uppercase tracking-tight">
                  From the <span className="italic font-body normal-case text-gold">Gazette desk</span>
                </h3>
              </div>
              <Link to="/discover/browse" className="text-[11px] text-mist hover:text-gold-bright">
                Browse all showcases →
              </Link>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {gazettes.map((g, i) => (
                <Link key={i}
                      to={`/discover/${g.campaign_slug}/gazette`}
                      className="card-mystic p-4 hover:-translate-y-1 transition-all duration-500 group block"
                      data-testid={`gazette-tile-${i}`}>
                  <div className="text-[9px] uppercase tracking-widest text-gold/70 mb-1">
                    Issue #{g.issue_number} · {g.date_label}
                  </div>
                  <div className="font-display text-base text-parchment leading-tight group-hover:text-gold-bright transition-colors">
                    {g.masthead}
                  </div>
                  <div className="text-[11px] text-mist/80 italic mt-2 truncate">
                    {g.campaign_name}
                  </div>
                  <div className="mt-3 text-[10px] text-gold-bright flex items-center gap-1">
                    Read the issue <ArrowRight className="w-3 h-3"/>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
