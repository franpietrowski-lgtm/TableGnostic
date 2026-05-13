import React, { useEffect, useState } from "react";
import axios from "axios";
import { CheckCircle2, GitBranch, Boxes, Activity, Users, Map, Scroll, Newspaper, Globe2, Store, Dice5, Flame, UserCheck } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SYSTEM_LABEL = {
  "besm-4e":  "BESM 4E",
  "anime-5e": "Anime 5E",
  "dnd-5e":   "D&D 5E",
  "cypher":   "Cypher",
};

// Static fallback for the App Stack tile — every other tile is now
// live data (see useEffect below).
const STACK = ["React", "Tailwind", "FastAPI", "MongoDB", "WebSockets", "WebRTC signaling", "Resend"];

export default function ProductProof() {
  // V6.25.40 — Live "by the numbers" strip from `/api/public/stats`.
  // V6.25.49 — also fetch the 7-day activity-pulse for the sparkline
  // and surface the latest milestone + per-system breakdown from the
  // server (was previously hard-coded in this file).
  const [stats, setStats] = useState(null);
  const [pulse, setPulse] = useState(null);
  useEffect(() => {
    let cancel = false;
    Promise.all([
      axios.get(`${API}/public/stats`).catch(() => ({ data: {} })),
      axios.get(`${API}/public/activity-pulse`).catch(() => ({ data: { days: [] } })),
    ]).then(([s, p]) => {
      if (cancel) return;
      setStats(s.data);
      setPulse(p.data);
    });
    return () => { cancel = true; };
  }, []);

  const counterTiles = stats ? [
    { l: "Campaigns",          v: stats.campaigns ?? 0,            Icon: Map },
    { l: "Public showcases",   v: stats.public_campaigns ?? 0,     Icon: Globe2 },
    { l: "Heroes built",       v: stats.characters ?? 0,           Icon: Users },
    { l: "Sessions played",    v: stats.sessions_played ?? 0,      Icon: Dice5 },
    { l: "Codex nodes",        v: stats.codex_nodes ?? 0,          Icon: Scroll },
    { l: "Gazettes pressed",   v: stats.gazettes_pressed ?? 0,     Icon: Newspaper },
    { l: "Active in 24h",      v: stats.active_24h ?? 0,           Icon: Flame },
    { l: "GMs running tables", v: stats.gms_active ?? 0,           Icon: UserCheck },
    { l: "Marketplace listings", v: stats.marketplace_listings ?? 0, Icon: Store },
  ] : [];

  // V6.25.49 — server-derived cards replace the hard-coded PROOF array.
  // Falls back gracefully if PRD.md / test reports can't be parsed.
  const proof = stats ? [
    {
      title: "Latest Internal Milestone",
      big: stats.latest_version || "V6.25.x",
      icon: GitBranch,
      accent: "gold",
      sub: "live from changelog",
      note: "Auto-pulled from PRD.md so this number is always the actual milestone shipping, not whatever the marketing copy last remembered.",
    },
    {
      title: "Cumulative Test Status",
      big: stats.pytest_passing || "—",
      icon: CheckCircle2,
      accent: "arcane",
      sub: "pytest checks passing",
      note: "Core mechanics, macro grammar, marketplace flows, mobile features, BESM modifier logic, and battlemap surfaces are covered by regression tests.",
    },
    {
      title: "By System",
      icon: Boxes,
      accent: "ember",
      systems: Object.entries(stats.by_system || {})
        .map(([sid, n]) => [SYSTEM_LABEL[sid] || sid, n])
        .sort((a, b) => b[1] - a[1]),
    },
    {
      title: "App Stack",
      icon: Boxes,
      accent: "gold",
      stack: STACK,
    },
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
          <div className="mt-10 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-3 gap-3"
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

        {/* V6.25.49 — 7-day activity sparkline. Three bars per day:
            campaigns / sessions / characters created. Skips render if
            the entire week is zero so empty/fresh instances don't
            look like a flatline. */}
        {pulse && pulse.days && pulse.days.some(
            (d) => d.campaigns_created + d.sessions_opened + d.characters_made > 0) && (
          <ActivitySparkline days={pulse.days}/>
        )}

        <div className="mt-14 grid md:grid-cols-2 gap-5">
          {proof.map((p, i) => (
            <ProofCard key={i} card={p} />
          ))}
        </div>
      </div>
    </section>
  );
}

/**
 * V6.25.49 — 7-day activity bar chart.
 * Pure-SVG sparkline-ish micro-chart: 3 stacked bars per day, sized
 * proportionally to the busiest day's total. Renders gracefully on
 * mobile (compact) and desktop (wider).
 */
function ActivitySparkline({ days }) {
  const max = Math.max(1, ...days.map((d) =>
    d.campaigns_created + d.sessions_opened + d.characters_made));
  return (
    <div className="mt-6 card-mystic p-5" data-testid="proof-activity-pulse">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-ember"/>
          <span className="label-ref text-ember">7-day activity pulse</span>
        </div>
        <div className="flex gap-3 text-[10px] uppercase tracking-widest text-mist/70 font-ui">
          <span><i className="inline-block w-2 h-2 bg-gold-bright rounded-sm mr-1"/>Campaigns</span>
          <span><i className="inline-block w-2 h-2 bg-arcane rounded-sm mr-1"/>Sessions</span>
          <span><i className="inline-block w-2 h-2 bg-ember rounded-sm mr-1"/>Heroes</span>
        </div>
      </div>
      <div className="flex items-end gap-1.5 h-24" role="img"
           aria-label="Daily activity over the last seven days">
        {days.map((d) => {
          const c = d.campaigns_created, s = d.sessions_opened, h = d.characters_made;
          const total = c + s + h;
          const hPct = (total / max) * 100;
          const label = d.date.slice(5);
          return (
            <div key={d.date} className="flex-1 flex flex-col items-center gap-1"
                 data-testid={`proof-pulse-${d.date}`}
                 title={`${d.date} — ${c} campaigns · ${s} sessions · ${h} heroes`}>
              <div className="w-full flex flex-col-reverse justify-start"
                   style={{ height: `${Math.max(2, hPct)}%` }}>
                {c > 0 && <div className="bg-gold-bright"
                                style={{ flex: c, minHeight: "2px" }}/>}
                {s > 0 && <div className="bg-arcane"
                                style={{ flex: s, minHeight: "2px" }}/>}
                {h > 0 && <div className="bg-ember"
                                style={{ flex: h, minHeight: "2px" }}/>}
              </div>
              <span className="text-[8px] text-mist/60 font-ui tracking-widest">{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ProofCard({ card }) {
  const Icon = card.icon;
  const accent = {
    gold: { text: "text-gold-bright", border: "border-gold/40" },
    arcane: { text: "text-arcane", border: "border-arcane/45" },
    ember: { text: "text-ember", border: "border-ember/45" },
  }[card.accent];

  // V6.25.49 — stable, kebab-case testid per card so the test agent
  // can target individual milestone tiles (e.g. proof-card-latest-
  // internal-milestone) without scraping the DOM.
  const cardTid = `proof-card-${card.title.toLowerCase().replace(/[^a-z0-9]/g, "-")}`;
  const valueTid = `${cardTid}-value`;

  return (
    <div className="card-mystic p-6 md:p-7" data-testid={cardTid}>
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-9 h-9 rounded-sm border ${accent.border} ${accent.text} flex items-center justify-center bg-void/60`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="label-ref">{card.title}</div>
      </div>

      {card.big && (
        <div className={`font-display text-4xl md:text-5xl tracking-tight ${accent.text}`}
             data-testid={valueTid}>
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

      {/* V6.25.49 — per-system breakdown card (replaces hard-coded
          'shipping strip'). Bars are scaled to the busiest system. */}
      {card.systems && (
        <div className="mt-5 space-y-2" data-testid="proof-by-system">
          {card.systems.length === 0 && (
            <div className="text-[11px] text-mist/60 italic">No campaigns logged yet.</div>
          )}
          {card.systems.map(([name, n]) => {
            const max = Math.max(1, ...card.systems.map((r) => r[1]));
            const pct = (n / max) * 100;
            return (
              <div key={name} className="flex items-center gap-3"
                   data-testid={`proof-system-${name.toLowerCase().replace(/[^a-z0-9]/g, "-")}`}>
                <span className="text-xs font-ui text-mist/85 w-24 truncate">{name}</span>
                <div className="flex-1 h-2 bg-ink/60 rounded-sm overflow-hidden">
                  <div className="h-full bg-ember/80" style={{ width: `${pct}%` }}/>
                </div>
                <span className="text-xs font-display text-parchment tabular-nums w-10 text-right">{n}</span>
              </div>
            );
          })}
        </div>
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
