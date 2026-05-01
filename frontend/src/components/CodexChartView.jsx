import React, { useEffect, useMemo, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Map, Network, RefreshCw } from "lucide-react";

/**
 * CodexChartView — V6.8 chart visualisation of the campaign codex.
 *
 * Per user reference image, two stacked surfaces:
 *   1. Geography / Biome flow chart   (top — region → biome → settlements)
 *   2. Worldbuilding pillar chart     (bottom — population × culture × magic × technology grid)
 *
 * Reads codex nodes' `fields.biome`, `fields.climate`, `fields.region`,
 * `fields.pillar`, `fields.depends_on[]` to bucket entries. Nodes that
 * don't carry these keys are still rendered, just without spatial
 * placement on the bottom grid. We never mutate.
 */
const PILLARS = [
  { key: "population", label: "Population & Culture", color: "#C8A34A" },
  { key: "geography",  label: "Geography & Biome",    color: "#3FAA62" },
  { key: "magic",      label: "Magic & Mystery",      color: "#7A4FBF" },
  { key: "technology", label: "Technology & Crafts",  color: "#3F8FAA" },
  { key: "history",    label: "History & Mythology",  color: "#E03A8E" },
];

export default function CodexChartView({ campId }) {
  const [nodes, setNodes] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true); setErr("");
    try {
      const { data } = await api.get(`/campaigns/${campId}/nodes`);
      setNodes(data || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [campId]);

  // Top half — Geography flow chart. Group nodes whose `type` is
  // location/region/place by their `fields.biome` (or 'Uncategorised').
  const geoBuckets = useMemo(() => {
    const buckets = {};
    for (const n of nodes) {
      if (!["location", "region", "place", "biome"].includes(n.type)) continue;
      const bk = (n.fields?.biome || n.fields?.climate || "Uncategorised").toString();
      buckets[bk] = buckets[bk] || [];
      buckets[bk].push(n);
    }
    return buckets;
  }, [nodes]);

  // Bottom half — pillar chart. Bucket every node by its declared pillar
  // (or auto-infer from type).
  const pillarBuckets = useMemo(() => {
    const out = Object.fromEntries(PILLARS.map((p) => [p.key, []]));
    for (const n of nodes) {
      const declared = (n.fields?.pillar || "").toLowerCase();
      let key = declared;
      if (!key) {
        // Heuristic by node type → pillar.
        const t = (n.type || "").toLowerCase();
        if (["faction", "culture", "race", "people", "npc"].includes(t)) key = "population";
        else if (["location", "region", "place", "biome"].includes(t)) key = "geography";
        else if (["spell", "artifact", "mystery", "deity"].includes(t)) key = "magic";
        else if (["tech", "weapon", "item"].includes(t)) key = "technology";
        else if (["historical", "event", "myth", "lore"].includes(t)) key = "history";
        else key = "history";
      }
      if (out[key]) out[key].push(n);
    }
    return out;
  }, [nodes]);

  if (loading) return <div className="text-mist text-xs italic">Drawing the chart…</div>;
  if (err) return <div className="text-ember text-xs">{err}</div>;

  return (
    <div className="space-y-4" data-testid="codex-chart-view">
      {/* ─── Top: Biome / Geography flow chart ─── */}
      <div className="card-mystic p-5">
        <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref flex items-center gap-2">
              <Map className="w-4 h-4"/> Geography &amp; Biome Flow
            </div>
            <div className="text-[11px] text-mist italic">
              Locations grouped by biome / climate (read from `fields.biome` or `fields.climate`).
            </div>
          </div>
          <button onClick={load} className="btn btn-ghost text-xs"
                  data-testid="codex-chart-refresh">
            <RefreshCw className="w-3 h-3"/> Refresh
          </button>
        </div>
        {Object.keys(geoBuckets).length === 0 ? (
          <div className="text-[12px] text-mist italic" data-testid="codex-chart-geo-empty">
            No location nodes carry biome / climate metadata yet. Add a `biome` or `climate` field on a location codex entry to populate this view.
          </div>
        ) : (
          <div className="flex flex-wrap gap-3" data-testid="codex-chart-geo">
            {Object.entries(geoBuckets).map(([biome, ns]) => (
              <div key={biome}
                   className="border-l-2 border-arcane/30 pl-3 min-w-[180px]"
                   data-testid={`codex-biome-${biome.replace(/\s+/g, '-').toLowerCase()}`}>
                <div className="font-display text-gold text-sm">{biome}</div>
                <div className="text-[9px] text-mist uppercase tracking-widest">{ns.length} locations</div>
                <ul className="mt-2 space-y-1">
                  {ns.slice(0, 6).map((n) => (
                    <li key={n.id} className="text-[11px] text-parchment border-l border-gold/15 pl-2">
                      {n.title}
                      {n.fields?.population && (
                        <span className="text-[9px] text-mist ml-1">· pop {n.fields.population}</span>
                      )}
                    </li>
                  ))}
                  {ns.length > 6 && (
                    <li className="text-[10px] text-mist italic">+{ns.length - 6} more</li>
                  )}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── Bottom: 5-pillar worldbuilding chart ─── */}
      <div className="card-mystic p-5">
        <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref flex items-center gap-2">
              <Network className="w-4 h-4"/> Worldbuilding Pillars
            </div>
            <div className="text-[11px] text-mist italic">
              Every node bucketed by its `fields.pillar` (override) or its `type` (auto-inferred).
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3"
             data-testid="codex-chart-pillars">
          {PILLARS.map((p) => {
            const ns = pillarBuckets[p.key] || [];
            return (
              <div key={p.key}
                   className="border-t-2 rounded-sm p-3 bg-void/30"
                   style={{ borderTopColor: p.color }}
                   data-testid={`codex-pillar-${p.key}`}>
                <div className="font-display text-sm" style={{ color: p.color }}>
                  {p.label}
                </div>
                <div className="text-[9px] text-mist uppercase tracking-widest">
                  {ns.length} entries
                </div>
                <ul className="mt-2 space-y-0.5 max-h-[200px] overflow-y-auto">
                  {ns.slice(0, 12).map((n) => (
                    <li key={n.id}
                        className="text-[10px] text-parchment truncate"
                        title={n.summary || n.content}>
                      · {n.title}
                    </li>
                  ))}
                  {ns.length > 12 && (
                    <li className="text-[9px] text-mist italic">
                      +{ns.length - 12} more
                    </li>
                  )}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
