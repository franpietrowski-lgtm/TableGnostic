import React from "react";
import { CheckCircle2 as CircleCheckBig, Hammer, Telescope } from "lucide-react";

const NOW = [
  "Genesis",
  "Codex Knowledge Graph",
  "World Creation Tree",
  "Character Builder",
  "Quick-Roll Bar",
  "Character-aware macros",
  "Per-row macro sprinkles",
  "Play-by-post commands",
  "Marketplace V1",
  "Marketplace watch list / digest",
  "Genesis Archive",
  "BESM modifier ranks",
  "BESM item / weapon mods",
  "PDF export",
  "Mobile navigation & sheet improvements",
];

const NEXT_90 = [
  {
    title: "Strict Permission Gating",
    body: "Players submit Codex / Genesis edits into GM approval flows.",
  },
  {
    title: "Anime 5E + D&D Level-20 Class Library",
    body: "Expanded class data and deeper progression support.",
  },
  {
    title: "Reference Editor Item / Weapon Composer",
    body: "Compose items and weapons first, then apply filtered modifier pools.",
  },
  {
    title: "Landing Page Buildout",
    body: "Public marketing page, waitlist, screenshots, contact, and launch analytics.",
  },
];

const HORIZON = [
  "Marketplace V2 with Stripe Connect payouts",
  "Public canon registry",
  "LLM-assisted session recap with GM safety pass",
  "Companion mobile app",
  "Private campaign share links",
  "Public world pages",
  "More system-specific builder depth",
];

export default function Roadmap() {
  return (
    <section id="roadmap" className="relative z-10 px-5 md:px-10 py-24 md:py-32" data-testid="roadmap-section">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <div className="label-ref mb-4">Roadmap</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            What is shipping <span className="text-gold italic font-body normal-case">next.</span>
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            The roadmap is honest, visible, and separated from what is already
            working.
          </p>
        </div>

        <div className="mt-14 grid lg:grid-cols-3 gap-5">
          {/* CURRENT */}
          <div className="card-mystic p-6 md:p-7" data-testid="roadmap-now">
            <div className="flex items-center gap-2 mb-4">
              <CircleCheckBig className="w-4 h-4 text-gold-bright" />
              <div className="label-ref">Current · demoable</div>
            </div>
            <ul className="space-y-1.5">
              {NOW.map((t) => (
                <li key={t} className="text-sm text-mist/90 font-ui flex gap-2">
                  <span className="text-gold-bright mt-0.5">✓</span> {t}
                </li>
              ))}
            </ul>
          </div>

          {/* NEXT 90 */}
          <div className="card-mystic p-6 md:p-7 border-arcane/30" data-testid="roadmap-next-90">
            <div className="flex items-center gap-2 mb-4">
              <Hammer className="w-4 h-4 text-arcane" />
              <div className="label-ref" style={{ color: "#a999d6" }}>Next 90 days</div>
            </div>
            <ul className="space-y-4">
              {NEXT_90.map((n) => (
                <li key={n.title}>
                  <div className="font-display text-sm text-parchment uppercase tracking-wide">
                    {n.title}
                  </div>
                  <div className="mt-1 text-xs text-mist/85 font-body leading-relaxed">
                    {n.body}
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* HORIZON */}
          <div className="card-mystic p-6 md:p-7" data-testid="roadmap-horizon">
            <div className="flex items-center gap-2 mb-4">
              <Telescope className="w-4 h-4 text-ember" />
              <div className="label-ref" style={{ color: "#c25646" }}>12 — 24 month horizon</div>
            </div>
            <ul className="space-y-1.5">
              {HORIZON.map((h) => (
                <li key={h} className="text-sm text-mist/90 font-ui flex gap-2">
                  <span className="text-ember mt-0.5">→</span> {h}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
