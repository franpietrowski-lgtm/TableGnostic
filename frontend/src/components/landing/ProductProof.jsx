import React, { useEffect, useState } from "react";
import axios from "axios";
import { CheckCircle2, GitBranch, Boxes, Activity, Users, Map, Scroll, Newspaper, Globe2, Store } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PROOF = [
  {
    title: "Latest Internal Milestone",
    big: "V6.25.10",
    icon: GitBranch,
    accent: "gold",
    bullets: [
      "Per-row macro sprinkles",
      "BESM Extras item / weapon modifiers",
      "Mobile Sweep V3",
      "Apocophea AutoMakers Bag demo",
      "Verified macro firing from chat or slot",
      "Live tooltip hints",
    ],
  },
  {
    title: "Cumulative Test Status",
    big: "26 / 26",
    icon: CheckCircle2,
    accent: "arcane",
    sub: "pytest checks passing",
    note: "Core mechanics, macro grammar, marketplace flows, mobile-facing features, and BESM modifier logic are covered by regression tests.",
  },
  {
    title: "Shipping Strip",
    icon: Activity,
    accent: "ember",
    timeline: [
      ["V6.25.5", "Marketplace V1"],
      ["V6.25.6", "Chat Hot-Keys"],
      ["V6.25.8", "Footer + Archive"],
      ["V6.25.9", "Character-Aware Macros"],
      ["V6.25.10", "Macro Sprinkles + Mobile V3"],
    ],
  },
  {
    title: "App Stack",
    icon: Boxes,
    accent: "gold",
    stack: [
      "React",
      "Tailwind",
      "FastAPI",
      "MongoDB",
      "WebSockets",
      "WebRTC signaling",
      "Resend",
    ],
  },
];

export default function ProductProof() {
  // V6.25.40 — Live "by the numbers" strip from `/api/public/stats`.
  // Surfaces actual app activity above the static milestone cards so
  // visitors see motion, not marketing.
  const [stats, setStats] = useState(null);
  useEffect(() => {
    let cancel = false;
    axios.get(`${API}/public/stats`)
      .then((r) => !cancel && setStats(r.data))
      .catch(() => !cancel && setStats({}));
    return () => { cancel = true; };
  }, []);

  const counterTiles = stats ? [
    { l: "Campaigns",          v: stats.campaigns ?? 0,            Icon: Map },
    { l: "Public showcases",   v: stats.public_campaigns ?? 0,     Icon: Globe2 },
    { l: "Heroes built",       v: stats.characters ?? 0,           Icon: Users },
    { l: "Codex nodes",        v: stats.codex_nodes ?? 0,          Icon: Scroll },
    { l: "Gazettes pressed",   v: stats.gazettes_pressed ?? 0,     Icon: Newspaper },
    { l: "Marketplace listings", v: stats.marketplace_listings ?? 0, Icon: Store },
  ] : [];

  return (
    <section
      id="proof"
      className="relative z-10 px-5 md:px-10 py-24 md:py-32 border-y border-gold/10 bg-void/30"
      data-testid="product-proof-section"
    >
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <div className="label-ref mb-4">Live product proof</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            Not a mockup. <span className="text-gold italic font-body normal-case">A working table tool.</span>
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            TableGnostics is actively built, tested, and shipping. Below is what
            the current internal milestone looks like.
          </p>
        </div>

        {/* V6.25.40 — Live counters strip */}
        {stats && (
          <div className="mt-10 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3"
               data-testid="proof-live-stats">
            {counterTiles.map(({ l, v, Icon }) => (
              <div key={l} className="card-mystic p-4 text-center"
                   data-testid={`proof-stat-${l.toLowerCase().replace(/[^a-z0-9]/g, "-")}`}>
                <Icon className="w-4 h-4 text-gold-bright mx-auto mb-1.5"/>
                <div className="text-2xl md:text-3xl font-display text-parchment tabular-nums leading-none">
                  {Number(v).toLocaleString()}
                </div>
                <div className="text-[9px] tracking-widest uppercase text-mist mt-1.5">{l}</div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-14 grid md:grid-cols-2 gap-5">
          {PROOF.map((p, i) => (
            <ProofCard key={i} card={p} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ProofCard({ card }) {
  const Icon = card.icon;
  const accent = {
    gold: { text: "text-gold-bright", border: "border-gold/40" },
    arcane: { text: "text-arcane", border: "border-arcane/45" },
    ember: { text: "text-ember", border: "border-ember/45" },
  }[card.accent];

  return (
    <div className="card-mystic p-6 md:p-7" data-testid={`proof-card-${card.title.toLowerCase().replace(/[^a-z0-9]/g, "-")}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-9 h-9 rounded-sm border ${accent.border} ${accent.text} flex items-center justify-center bg-void/60`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="label-ref">{card.title}</div>
      </div>

      {card.big && (
        <div className={`font-display text-4xl md:text-5xl tracking-tight ${accent.text}`}>
          {card.big}
        </div>
      )}
      {card.sub && (
        <div className="mt-1 text-xs font-ui uppercase tracking-[0.25em] text-mist/70">
          {card.sub}
        </div>
      )}
      {card.note && (
        <p className="mt-4 text-sm text-mist font-body leading-relaxed">
          {card.note}
        </p>
      )}

      {card.bullets && (
        <ul className="mt-5 space-y-1.5">
          {card.bullets.map((b) => (
            <li key={b} className="text-sm text-mist/85 font-ui flex gap-2">
              <span className={`${accent.text} mt-0.5`}>◆</span>
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}

      {card.timeline && (
        <ol className="mt-5 space-y-3 relative pl-5 border-l border-gold/20">
          {card.timeline.map(([v, label], i) => (
            <li key={v} className="relative">
              <span className={`absolute -left-[26px] top-1 w-2 h-2 rounded-full ${i === card.timeline.length - 1 ? "bg-gold-bright" : "bg-gold/50"}`} />
              <div className="font-mono text-xs text-gold-bright">{v}</div>
              <div className="text-sm text-mist font-ui">{label}</div>
            </li>
          ))}
        </ol>
      )}

      {card.stack && (
        <div className="mt-5 flex flex-wrap gap-2">
          {card.stack.map((s) => (
            <span
              key={s}
              className="text-[11px] font-mono text-gold-bright/85 border border-gold/25 rounded-sm px-2.5 py-1 bg-ink/40"
            >
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
