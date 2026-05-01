import React, { useEffect, useMemo, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Map, Network, RefreshCw, Pin, Check, X as XIcon, ChevronLeft, ChevronRight } from "lucide-react";

/**
 * CodexChartView V2 — V6.11 worldbuilding chart redesigned per user spec.
 *
 *   1. World Creation Tree (top) — organisational chart rooted on the
 *      Creation / Beginning node, branching into 3 primary pillars:
 *        Population · Geography · History
 *      Each pillar fans out into its declared sub-branches (read from
 *      `node.fields.pillar_branch` if set, else inferred from `type`).
 *
 *   2. Biome Pyramid (bottom) — 4-quadrant chart positioning location
 *      nodes by their declared `temperature` (Hot↔Cold) and `humidity`
 *      (Wet↔Dry) fields. Self-fills sample biomes (rainforest, tundra,
 *      desert, etc.) when the GM hasn't yet detailed location climate
 *      data, so the chart never feels empty.
 *
 *   GMs can click any node to drop a Timeline marker at the active
 *   session (preserved from V6.9).
 */

const PILLAR_BRANCHES = {
  population: [
    "races", "nations", "languages", "factions", "prominent_people",
    "technology", "religions", "beliefs", "laws", "wars", "conflicts",
  ],
  geography: [
    "biomes", "locations", "natural_divides", "natural_laws", "magic",
    "gods", "dimensions", "connected_worlds", "uniqueness",
    "countries", "continents",
  ],
  history: [
    "natural_history", "of_the_people", "written", "oral", "truth", "lies",
  ],
};

// Auto-infer which pillar a node belongs to based on its type when the GM
// hasn't explicitly stamped fields.pillar.
const TYPE_TO_PILLAR = {
  npc: "population", faction: "population", culture: "population",
  race: "population", religion: "population", language: "population",
  location: "geography", region: "geography", place: "geography",
  biome: "geography", dimension: "geography", country: "geography",
  spell: "geography", artifact: "geography", deity: "geography",
  historical: "history", event: "history", myth: "history", lore: "history",
  tech: "population", weapon: "population", item: "population",
  creature: "geography",
};

// Sample biomes that auto-populate the pyramid when no real location data
// supplies climate/temperature, so the chart always renders meaningfully.
const SAMPLE_BIOMES = [
  { title: "Rainforest",  temperature: "hot",     humidity: "wet" },
  { title: "Tropical Coast", temperature: "hot",  humidity: "wet" },
  { title: "Savanna",     temperature: "hot",     humidity: "neutral" },
  { title: "Desert",      temperature: "hot",     humidity: "dry" },
  { title: "Mediterranean", temperature: "warm",  humidity: "neutral" },
  { title: "Temperate Forest", temperature: "warm", humidity: "wet" },
  { title: "Steppe",      temperature: "warm",    humidity: "dry" },
  { title: "Marsh / Bog", temperature: "cool",    humidity: "wet" },
  { title: "Boreal / Taiga", temperature: "cold", humidity: "wet" },
  { title: "Tundra",      temperature: "cold",    humidity: "dry" },
  { title: "Glacial",     temperature: "cold",    humidity: "neutral" },
];

// Map fuzzy text values to coarse buckets.
const tempBucket = (raw) => {
  const s = (raw || "").toLowerCase();
  if (/(arctic|polar|frozen|glacial|tundra|cold)/.test(s)) return "cold";
  if (/(cool|chilly|boreal|taiga|alpine)/.test(s)) return "cool";
  if (/(temperate|mild|mediterranean|warm)/.test(s)) return "warm";
  if (/(tropical|jungle|equator|hot|desert|savanna|sahara)/.test(s)) return "hot";
  return "warm";
};
const humBucket = (raw) => {
  const s = (raw || "").toLowerCase();
  if (/(rain|swamp|marsh|bog|wet|tropical|jungle|coast|aquatic|humid)/.test(s)) return "wet";
  if (/(arid|desert|dry|tundra|steppe|savanna)/.test(s)) return "dry";
  return "neutral";
};

export default function CodexChartView({ campId, isGm }) {
  const [nodes, setNodes] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState("");
  const [pinningId, setPinningId] = useState("");
  const [pinFeedback, setPinFeedback] = useState("");
  const [draftPin, setDraftPin] = useState(null);  // V6.16 — preview before commit
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true); setErr("");
    try {
      const [n, s] = await Promise.all([
        api.get(`/campaigns/${campId}/nodes`).then((r) => r.data || []),
        api.get(`/campaigns/${campId}/sessions`).then((r) => r.data || []),
      ]);
      setNodes(n);
      const ordered = s.slice().sort((a, b) => {
        const ta = new Date(a.scheduled_at || a.played_at || a.created_at || 0).getTime();
        const tb = new Date(b.scheduled_at || b.played_at || b.created_at || 0).getTime();
        return ta - tb;
      });
      setSessions(ordered);
      if (!activeSessionId && ordered.length) {
        const inProgress = ordered.find((x) => x.status === "in-progress");
        const upcoming = ordered.find((x) => !x.played_at);
        setActiveSessionId((inProgress || upcoming || ordered[ordered.length - 1]).id);
      }
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [campId]);

  // V6.16 — clicking a node now opens a confirm preview rather than
  // committing immediately. Lets the GM see WHICH session it lands on
  // (visible mini-timeline strip) and shuffle it before persisting.
  const openDraftPin = (node) => {
    if (!isGm) return;
    if (sessions.length === 0) {
      setPinFeedback("This campaign has no sessions yet — schedule one first.");
      setTimeout(() => setPinFeedback(""), 4000);
      return;
    }
    // Default to the picker's active session (or the first one).
    const targetSid = activeSessionId || sessions[0].id;
    setDraftPin({ node, sessionId: targetSid });
  };

  const commitDraftPin = async () => {
    if (!draftPin) return;
    const { node, sessionId } = draftPin;
    setPinningId(node.id); setPinFeedback("");
    try {
      await api.post(`/campaigns/${campId}/timeline-markers`, {
        session_id: sessionId,
        codex_node_id: node.id,
        label: node.title,
        kind: "node",
        color: node.fields?.color || "#C8A34A",
      });
      const sess = sessions.find((s) => s.id === sessionId);
      setPinFeedback(`Pinned "${node.title}" → ${sess?.name || "session"}.`);
      try { window.dispatchEvent(new CustomEvent("tg:timeline-marker-added", { detail: { campId } })); } catch (_) {}
      setTimeout(() => setPinFeedback(""), 4000);
      setDraftPin(null);
    } catch (e) {
      setPinFeedback(formatApiErrorDetail(e.response?.data?.detail) || "Pin failed.");
    } finally { setPinningId(""); }
  };

  // Legacy entry point kept for callers that still pass directly.
  const dropMarkerOnTimeline = openDraftPin;

  // ── World Creation Tree buckets ────────────────────────────────────────
  const treeBuckets = useMemo(() => {
    const out = { population: {}, geography: {}, history: {} };
    for (const n of nodes) {
      const fpillar = (n.fields?.pillar || "").toLowerCase();
      const pillar = ["population", "geography", "history"].includes(fpillar)
        ? fpillar
        : (TYPE_TO_PILLAR[(n.type || "").toLowerCase()] || "population");
      const branch = (n.fields?.pillar_branch || n.fields?.branch || n.type || "other").toLowerCase().replace(/\s+/g, "_");
      out[pillar][branch] = out[pillar][branch] || [];
      out[pillar][branch].push(n);
    }
    return out;
  }, [nodes]);

  // ── Biome Pyramid placements ──────────────────────────────────────────
  const pyramidNodes = useMemo(() => {
    // 1) Pull every location-ish node that has temperature OR humidity OR
    //    biome metadata declared. Place it in the appropriate quadrant.
    const placed = [];
    for (const n of nodes) {
      const t = (n.type || "").toLowerCase();
      if (!["location", "region", "place", "biome", "country", "continent"].includes(t)) continue;
      const f = n.fields || {};
      const temp = f.temperature || f.climate || f.biome || "";
      const hum = f.humidity || f.moisture || f.biome || "";
      if (!temp && !hum) continue;  // skip nodes with no climate metadata
      placed.push({
        id: n.id,
        title: n.title,
        temp: tempBucket(temp),
        hum: humBucket(hum),
        real: true,
      });
    }
    // 2) If GM hasn't seeded any biome metadata yet, fall back to sample
    //    biomes so the chart still renders.
    if (placed.length === 0) {
      return SAMPLE_BIOMES.map((s, i) => ({
        id: `sample-${i}`,
        title: s.title,
        temp: s.temperature, hum: s.humidity,
        real: false,
      }));
    }
    return placed;
  }, [nodes]);

  if (loading) return <div className="text-mist text-xs italic">Drawing the chart…</div>;
  if (err) return <div className="text-ember text-xs">{err}</div>;

  // Reusable clickable tag for tree leaves
  const NodeChip = ({ n, color }) => {
    const clickable = isGm && sessions.length > 0;
    return (
      <button
        onClick={() => clickable && openDraftPin(n)}
        className={`text-[10px] font-ui px-1.5 py-0.5 rounded-sm border truncate max-w-full ${clickable ? "cursor-pointer hover:bg-gold/10 transition-colors" : "cursor-default"}`}
        style={{ borderColor: (color || "#C8A34A") + "55",
                 color: color || "#C8A34A",
                 background: (color || "#C8A34A") + "0c" }}
        title={clickable ? `Click to pin "${n.title}" on Timeline` : (sessions.length === 0 ? "Schedule a session first to enable pinning." : n.title)}
        data-testid={`codex-tree-node-${n.id}`}
      >
        {pinningId === n.id ? "…" : n.title}
      </button>
    );
  };

  // Pyramid quadrant cell layout
  const QUADRANTS = [
    { temp: "hot",  hum: "wet",     label: "Rainforest tier · hot/wet",   color: "#3FAA62", row: 0, col: 0 },
    { temp: "hot",  hum: "neutral", label: "Savanna tier · hot/balanced", color: "#7AAA3F", row: 0, col: 1 },
    { temp: "hot",  hum: "dry",     label: "Desert tier · hot/dry",       color: "#C8A34A", row: 0, col: 2 },
    { temp: "warm", hum: "wet",     label: "Temperate Forest · warm/wet", color: "#3F8FAA", row: 1, col: 0 },
    { temp: "warm", hum: "neutral", label: "Mediterranean · warm/balanced", color: "#5F7AAA", row: 1, col: 1 },
    { temp: "warm", hum: "dry",     label: "Steppe · warm/dry",           color: "#AA7A3F", row: 1, col: 2 },
    { temp: "cool", hum: "wet",     label: "Marshlands · cool/wet",       color: "#3FAA9A", row: 2, col: 0 },
    { temp: "cool", hum: "neutral", label: "Highlands · cool/balanced",   color: "#7A8FAA", row: 2, col: 1 },
    { temp: "cool", hum: "dry",     label: "Highlands Steppe · cool/dry", color: "#8F7A6F", row: 2, col: 2 },
    { temp: "cold", hum: "wet",     label: "Taiga · cold/wet",            color: "#5F7A8F", row: 3, col: 0 },
    { temp: "cold", hum: "neutral", label: "Glacial Coast · cold/balanced", color: "#AABFCE", row: 3, col: 1 },
    { temp: "cold", hum: "dry",     label: "Tundra · cold/dry",           color: "#CFD7DC", row: 3, col: 2 },
  ];

  return (
    <div className="space-y-4" data-testid="codex-chart-view">
      {/* ─── Pin-to-Timeline session picker (default target) ─── */}
      {isGm && (
        <div className="card-mystic p-3 flex items-center justify-between flex-wrap gap-3"
             data-testid="codex-chart-pin-bar">
          <div className="flex items-center gap-2 text-[11px]">
            <Pin className="w-3.5 h-3.5 text-gold"/>
            <span className="text-mist">Default session for new pins:</span>
            <select
              value={activeSessionId}
              onChange={(e) => setActiveSessionId(e.target.value)}
              className="input-mystic text-[11px] py-1"
              data-testid="codex-chart-active-session"
            >
              {sessions.length === 0 && <option value="">— no sessions —</option>}
              {sessions.map((s, i) => (
                <option key={s.id} value={s.id}>
                  Session {i + 1} · {s.name || "untitled"}
                  {s.scheduled_at && ` · ${new Date(s.scheduled_at).toLocaleDateString()}`}
                </option>
              ))}
            </select>
            <span className="text-[10px] text-mist/60 italic">
              Click any node — a confirm panel lets you reposition before saving.
            </span>
          </div>
          {pinFeedback && (
            <div className="text-[11px] text-gold-bright italic"
                 data-testid="codex-chart-pin-feedback">
              {pinFeedback}
            </div>
          )}
        </div>
      )}

      {/* ─── World Creation Tree — org chart ─── */}
      <div className="card-mystic p-5" data-testid="codex-creation-tree">
        <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref flex items-center gap-2">
              <Network className="w-4 h-4"/> World Creation Tree
            </div>
            <div className="text-[11px] text-mist italic max-w-2xl">
              Creation root → Population · Geography · History pillars → declared sub-branches.
              Branches read from <code>fields.pillar</code> &amp; <code>fields.pillar_branch</code>.
            </div>
          </div>
          <button onClick={load} className="btn btn-ghost text-xs"
                  data-testid="codex-chart-refresh">
            <RefreshCw className="w-3 h-3"/> Refresh
          </button>
        </div>

        <div className="flex flex-col items-center gap-3">
          {/* Root */}
          <div className="px-5 py-2 rounded-sm border-2 border-gold/60 bg-gold/10 text-gold-bright font-display text-base"
               data-testid="codex-tree-root">
            Creation · Beginning
          </div>
          {/* Connector */}
          <div className="h-4 w-px bg-gold/40"/>
          {/* 3 pillars */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 w-full">
            {[
              ["population", "Population", "#C8A34A"],
              ["geography",  "Geography",  "#3FAA62"],
              ["history",    "History",    "#E03A8E"],
            ].map(([key, label, color]) => {
              const branches = Object.entries(treeBuckets[key] || {}).sort();
              const knownOrder = PILLAR_BRANCHES[key] || [];
              const sorted = branches.sort((a, b) => {
                const ai = knownOrder.indexOf(a[0]);
                const bi = knownOrder.indexOf(b[0]);
                if (ai !== -1 && bi !== -1) return ai - bi;
                if (ai !== -1) return -1;
                if (bi !== -1) return 1;
                return a[0].localeCompare(b[0]);
              });
              return (
                <div key={key}
                     className="border-t-2 rounded-sm p-3"
                     style={{ borderTopColor: color, background: color + "0a" }}
                     data-testid={`codex-tree-pillar-${key}`}>
                  <div className="font-display text-base mb-2" style={{ color }}>{label}</div>
                  {sorted.length === 0 ? (
                    <div className="text-[11px] text-mist italic">No entries on this pillar yet.</div>
                  ) : (
                    <div className="space-y-2">
                      {sorted.slice(0, 12).map(([branch, items]) => (
                        <div key={branch} data-testid={`codex-tree-branch-${key}-${branch}`}>
                          <div className="text-[9px] uppercase tracking-widest text-mist/70">
                            {branch.replace(/_/g, " ")} · {items.length}
                          </div>
                          <div className="flex flex-wrap gap-1 mt-0.5">
                            {items.slice(0, 8).map((n) => (
                              <NodeChip key={n.id} n={n} color={color}/>
                            ))}
                            {items.length > 8 && (
                              <span className="text-[9px] text-mist italic self-center">+{items.length - 8}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ─── Biome Pyramid ─── */}
      <div className="card-mystic p-5" data-testid="codex-biome-pyramid">
        <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref flex items-center gap-2">
              <Map className="w-4 h-4"/> Biome Pyramid
            </div>
            <div className="text-[11px] text-mist italic max-w-2xl">
              Locations placed by their <code>fields.temperature</code> (Hot↔Cold) and
              <code> fields.humidity</code> (Wet↔Dry). Falls back to sample biomes
              if no climate metadata is set so you can see the spread.
              {pyramidNodes.some((p) => !p.real) && (
                <span className="ml-1 text-arcane-light">[showing sample biomes — fill in location climate to populate]</span>
              )}
            </div>
          </div>
        </div>

        {/* Axis labels + 4-row × 3-col grid */}
        <div className="grid grid-cols-[auto_1fr] gap-3">
          <div className="flex flex-col justify-around text-[9px] uppercase tracking-widest text-mist text-right pr-1 min-w-[34px]">
            <div>Hot</div>
            <div>Warm</div>
            <div>Cool</div>
            <div>Cold</div>
          </div>
          <div className="grid grid-cols-3 gap-2" data-testid="biome-pyramid-grid">
            {QUADRANTS.map((q) => {
              const ns = pyramidNodes.filter((p) => p.temp === q.temp && p.hum === q.hum);
              return (
                <div key={`${q.temp}-${q.hum}`}
                     className="border rounded-sm p-2 min-h-[64px]"
                     style={{ borderColor: q.color + "55", background: q.color + "08" }}
                     data-testid={`biome-quad-${q.temp}-${q.hum}`}
                     title={q.label}>
                  <div className="text-[9px] uppercase tracking-widest mb-1" style={{ color: q.color }}>
                    {q.label}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {ns.length === 0 ? (
                      <span className="text-[9px] text-mist/40 italic">—</span>
                    ) : (
                      ns.map((p) => (
                        <span key={p.id}
                              className={`text-[10px] px-1.5 py-0.5 rounded-sm border truncate ${p.real ? "" : "italic opacity-60"}`}
                              style={{ borderColor: q.color + "66", color: q.color }}
                              data-testid={`biome-node-${p.id}`}>
                          {p.title}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        {/* Bottom humidity axis */}
        <div className="grid grid-cols-[auto_1fr] gap-3 mt-1">
          <div className="min-w-[34px]"/>
          <div className="grid grid-cols-3 text-[9px] uppercase tracking-widest text-mist text-center">
            <div>Wet</div>
            <div>Balanced</div>
            <div>Dry</div>
          </div>
        </div>
      </div>

      {/* V6.16 — Pin confirm panel with visible mini-timeline strip */}
      {draftPin && (
        <PinConfirmPanel
          draft={draftPin}
          sessions={sessions}
          busy={pinningId === draftPin.node.id}
          onPickSession={(sid) => setDraftPin((d) => d && { ...d, sessionId: sid })}
          onConfirm={commitDraftPin}
          onCancel={() => setDraftPin(null)}
        />
      )}
    </div>
  );
}

/**
 * V6.16 — PinConfirmPanel
 *
 * Floating modal that appears after a GM clicks any codex node to drop a
 * Timeline marker. Renders a horizontal mini-timeline strip showing every
 * session in the campaign as a pill (the visible "timeline graphic" the
 * GM pins onto), with the candidate session highlighted. The GM can:
 *   • Click any session pill (or use the ◀ ▶ chevrons) to retarget
 *   • Confirm to commit the pin
 *   • Cancel to discard the draft
 *
 * The strip auto-scrolls the picked session into view on retarget.
 */
function PinConfirmPanel({ draft, sessions, busy, onPickSession, onConfirm, onCancel }) {
  const { node, sessionId } = draft;
  const idx = Math.max(0, sessions.findIndex((s) => s.id === sessionId));
  const targetSess = sessions[idx];
  const stripRef = React.useRef(null);

  React.useEffect(() => {
    const el = stripRef.current?.querySelector(`[data-pin-strip-idx="${idx}"]`);
    try { el?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" }); } catch (_) {}
  }, [idx]);

  React.useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onCancel();
      if (e.key === "Enter") onConfirm();
      if (e.key === "ArrowLeft" && idx > 0) onPickSession(sessions[idx - 1].id);
      if (e.key === "ArrowRight" && idx < sessions.length - 1) onPickSession(sessions[idx + 1].id);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [idx, sessions, onPickSession, onConfirm, onCancel]);

  const dotColor = node.fields?.color || "#C8A34A";

  return (
    <div className="fixed inset-0 z-[8800] bg-void/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-3 sm:p-6"
         data-testid="pin-confirm-overlay" onClick={onCancel}>
      <div className="card-mystic w-full max-w-3xl p-5 sm:p-6"
           onClick={(e) => e.stopPropagation()}
           data-testid="pin-confirm-panel">
        <div className="flex items-baseline justify-between gap-3 mb-3">
          <div className="min-w-0 flex-1">
            <div className="text-[10px] tracking-widest uppercase text-gold-bright flex items-center gap-1.5">
              <Pin className="w-3 h-3" /> Pin to Timeline
            </div>
            <div className="font-display text-xl text-parchment mt-0.5 truncate">
              {node.title}
            </div>
            <div className="text-[11px] text-mist italic">
              Drops a marker on the campaign Timeline at the picked session.
              Pin a place, NPC, faction, or moment so future you knows when it entered the story.
            </div>
          </div>
          <button onClick={onCancel} className="text-mist hover:text-ember shrink-0"
                  data-testid="pin-confirm-cancel" title="Cancel (ESC)">
            <XIcon className="w-4 h-4" />
          </button>
        </div>

        {/* Visible mini-timeline strip — every session as a tappable pill. */}
        <div className="mt-2">
          <div className="flex items-center justify-between mb-1.5">
            <div className="label-ref text-[10px]">Timeline</div>
            <div className="text-[10px] text-mist tracking-widest uppercase">
              Session {idx + 1} of {sessions.length}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => idx > 0 && onPickSession(sessions[idx - 1].id)}
              disabled={idx === 0}
              className="btn btn-ghost p-1 disabled:opacity-30"
              data-testid="pin-confirm-prev"
              title="Previous session">
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div ref={stripRef}
                 className="flex-1 flex items-center gap-2 overflow-x-auto py-2 px-1 border-y border-gold/15 bg-void/40 rounded-sm"
                 data-testid="pin-confirm-strip">
              {sessions.map((s, i) => {
                const picked = i === idx;
                return (
                  <button key={s.id}
                          data-pin-strip-idx={i}
                          data-testid={`pin-confirm-strip-${i}`}
                          onClick={() => onPickSession(s.id)}
                          title={s.name || `Session ${i + 1}`}
                          className={`group relative flex flex-col items-center min-w-[120px] px-3 py-2 rounded-sm border transition-all ${
                            picked
                              ? "bg-gold/15 text-gold-bright border-gold"
                              : "bg-void/40 text-mist border-gold/20 hover:border-gold/50 hover:bg-gold/5"
                          }`}>
                    {/* The candidate marker drop — only on picked. */}
                    {picked && (
                      <span className="absolute -top-2 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full border-2 border-void"
                            style={{ background: dotColor }}
                            data-testid={`pin-confirm-marker-${i}`}/>
                    )}
                    <span className="text-[10px] tracking-widest uppercase text-mist">#{i + 1}</span>
                    <span className="text-xs font-ui truncate max-w-[110px]">
                      {s.name || "untitled"}
                    </span>
                    {s.scheduled_at && (
                      <span className="text-[9px] text-mist/70 mt-0.5">
                        {new Date(s.scheduled_at).toLocaleDateString()}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => idx < sessions.length - 1 && onPickSession(sessions[idx + 1].id)}
              disabled={idx >= sessions.length - 1}
              className="btn btn-ghost p-1 disabled:opacity-30"
              data-testid="pin-confirm-next"
              title="Next session">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="text-[10px] text-mist/70 italic mt-1.5">
            ◀ ▶ to walk · Enter to confirm · ESC to cancel
          </div>
        </div>

        {/* Summary line */}
        <div className="mt-4 p-3 rounded-sm border border-gold/20 bg-void/30 flex items-center gap-2.5"
             data-testid="pin-confirm-summary">
          <span className="inline-block w-3 h-3 rounded-full shrink-0" style={{ background: dotColor }} />
          <div className="text-[12px] text-parchment leading-snug flex-1 min-w-0">
            <b className="text-gold-bright">{node.title}</b>
            <span className="text-mist"> will be pinned to </span>
            <b>{targetSess?.name || "this session"}</b>
            {targetSess?.scheduled_at && (
              <span className="text-mist/80"> · {new Date(targetSess.scheduled_at).toLocaleDateString()}</span>
            )}
            .
          </div>
        </div>

        <div className="mt-4 flex items-center justify-end gap-2">
          <button onClick={onCancel} className="btn btn-ghost text-xs" data-testid="pin-confirm-cancel-btn">
            Cancel
          </button>
          <button onClick={onConfirm} disabled={busy} className="btn btn-primary text-xs"
                  data-testid="pin-confirm-confirm-btn">
            <Check className="w-3 h-3" /> {busy ? "Pinning…" : "Confirm pin"}
          </button>
        </div>
      </div>
    </div>
  );
}
