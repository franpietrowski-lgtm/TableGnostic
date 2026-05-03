/**
 * WorldTreeGraph — V6.21 (Cut D V2)
 *
 * SVG force-directed graph view of the World Creation Tree. Renders
 * nodes clustered by creation-tree pillar (Population / Geography /
 * History) and connected by codex-link edges with weight-driven stroke
 * thickness + relationship-type colour.
 *
 * Physics is a lightweight spring simulation (no d3 dependency). Runs
 * ~200 ticks on mount, then freezes. Each pillar acts as an anchor
 * centre pulling its members; codex links pull linked nodes together.
 *
 * Props:
 *   - nodes: [{id, title, kind, fields:{pillar, pillar_branch}}, ...]
 *     (populated entries from /campaigns/{cid}/creation-tree)
 *   - edges: [{source_id, target_id, weight, color, relationship_type}, ...]
 *     (from /campaigns/{cid}/codex-links)
 *   - onNodeClick: (node) => void (opens codex node detail in parent)
 *   - width / height: SVG canvas (defaults: 800 × 520)
 *
 * Interactive:
 *   - Hover a node: highlights its direct-link neighbours.
 *   - Click a node: fires onNodeClick(node).
 *   - Legend top-right: pillar colour swatches + weight scale.
 */
import React, { useEffect, useMemo, useRef, useState } from "react";

const PILLAR_COLORS = {
  Population: "#E8B0D0",
  Geography:  "#A8E6A1",
  History:    "#B8A0E8",
  Unclassified: "#888888",
};

// Anchor centres per pillar (relative to the canvas).
const PILLAR_ANCHORS = {
  Population: { xr: 0.22, yr: 0.30 },
  Geography:  { xr: 0.78, yr: 0.30 },
  History:    { xr: 0.50, yr: 0.80 },
  Unclassified: { xr: 0.50, yr: 0.50 },
};

function inferPillar(node) {
  const p = node.fields?.pillar;
  if (p && PILLAR_COLORS[p]) return p;
  // Fall back on node kind:
  const k = (node.kind || "").toLowerCase();
  if (["person", "npc", "faction", "creature", "character"].includes(k)) return "Population";
  if (["location", "place", "biome", "region"].includes(k)) return "Geography";
  if (["lore", "event", "chronicle", "quest"].includes(k)) return "History";
  return "Unclassified";
}

export default function WorldTreeGraph({ nodes = [], edges = [],
                                          onNodeClick,
                                          width = 800, height = 520 }) {
  const [positions, setPositions] = useState({});
  const [hover, setHover] = useState(null);
  const svgRef = useRef(null);

  // Build node records with pillar assignment.
  const graphNodes = useMemo(() => {
    return nodes.map((n) => ({
      ...n,
      pillar: inferPillar(n),
    }));
  }, [nodes]);

  // Index edges by node for highlight lookup.
  const edgesByNode = useMemo(() => {
    const m = {};
    edges.forEach((e) => {
      (m[e.source_id] = m[e.source_id] || []).push(e.target_id);
      if (e.bidirectional) {
        (m[e.target_id] = m[e.target_id] || []).push(e.source_id);
      }
    });
    return m;
  }, [edges]);

  // Run a lightweight spring simulation on mount / nodes change.
  useEffect(() => {
    if (graphNodes.length === 0) return;
    const pos = {};
    graphNodes.forEach((n, i) => {
      const anchor = PILLAR_ANCHORS[n.pillar] || PILLAR_ANCHORS.Unclassified;
      // Jitter around the pillar anchor.
      pos[n.id] = {
        x: anchor.xr * width + (Math.random() - 0.5) * 80,
        y: anchor.yr * height + (Math.random() - 0.5) * 60,
        vx: 0, vy: 0,
      };
    });

    const PILLAR_PULL = 0.05;
    const REPULSION = 900;
    const DAMPING = 0.82;
    const EDGE_PULL_BASE = 0.015;

    for (let tick = 0; tick < 260; tick++) {
      // Pillar anchor spring.
      graphNodes.forEach((n) => {
        const p = pos[n.id]; if (!p) return;
        const a = PILLAR_ANCHORS[n.pillar] || PILLAR_ANCHORS.Unclassified;
        const ax = a.xr * width, ay = a.yr * height;
        p.vx += (ax - p.x) * PILLAR_PULL;
        p.vy += (ay - p.y) * PILLAR_PULL;
      });
      // Node-node repulsion.
      for (let i = 0; i < graphNodes.length; i++) {
        for (let j = i + 1; j < graphNodes.length; j++) {
          const a = pos[graphNodes[i].id]; const b = pos[graphNodes[j].id];
          if (!a || !b) continue;
          const dx = b.x - a.x; const dy = b.y - a.y;
          const d2 = dx * dx + dy * dy + 0.01;
          const f = REPULSION / d2;
          const d = Math.sqrt(d2);
          a.vx -= (dx / d) * f; a.vy -= (dy / d) * f;
          b.vx += (dx / d) * f; b.vy += (dy / d) * f;
        }
      }
      // Edge spring (weight-driven pull).
      edges.forEach((e) => {
        const a = pos[e.source_id]; const b = pos[e.target_id];
        if (!a || !b) return;
        const dx = b.x - a.x; const dy = b.y - a.y;
        const w = Math.max(1, Math.min(10, e.weight || 1));
        const pull = EDGE_PULL_BASE * (w / 5);
        a.vx += dx * pull; a.vy += dy * pull;
        b.vx -= dx * pull; b.vy -= dy * pull;
      });
      // Integrate + damping + clamp to canvas.
      graphNodes.forEach((n) => {
        const p = pos[n.id]; if (!p) return;
        p.vx *= DAMPING; p.vy *= DAMPING;
        p.x += p.vx;     p.y += p.vy;
        p.x = Math.max(30, Math.min(width - 30, p.x));
        p.y = Math.max(30, Math.min(height - 30, p.y));
      });
    }
    setPositions(pos);
  }, [graphNodes, edges, width, height]);

  if (graphNodes.length === 0) {
    return (
      <div className="card-mystic p-6 text-center text-mist italic"
           data-testid="world-tree-graph-empty">
        No codex nodes yet — seed from the Atelier · Genesis tab, or drop
        your first "Root event" here and the graph will populate.
      </div>
    );
  }

  const neighbours = hover ? new Set(edgesByNode[hover] || []) : new Set();

  return (
    <div className="card-mystic p-3" data-testid="world-tree-graph">
      <div className="flex items-center justify-between mb-2">
        <div className="label-ref">Graph view · clustered by pillar</div>
        <div className="flex items-center gap-3 text-[10px]">
          {Object.entries(PILLAR_COLORS).filter(([k]) => k !== "Unclassified").map(
            ([k, c]) => (
              <span key={k} className="inline-flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: c }}/>
                <span className="text-mist">{k}</span>
              </span>
            )
          )}
          <span className="text-mist">
            — stroke = link weight (1-10)
          </span>
        </div>
      </div>

      <svg ref={svgRef} width={width} height={height}
           viewBox={`0 0 ${width} ${height}`}
           className="w-full h-auto border border-gold/20 rounded-sm"
           style={{ background: "rgba(10, 8, 18, 0.3)" }}>
        {/* Pillar anchor labels (subtle). */}
        {Object.entries(PILLAR_ANCHORS).filter(([p]) => p !== "Unclassified").map(
          ([p, a]) => (
            <g key={p}>
              <circle cx={a.xr * width} cy={a.yr * height} r="40"
                      fill={PILLAR_COLORS[p]} fillOpacity="0.04"
                      stroke={PILLAR_COLORS[p]} strokeOpacity="0.2"
                      strokeDasharray="4 4"/>
              <text x={a.xr * width} y={a.yr * height - 48}
                    fill={PILLAR_COLORS[p]} fillOpacity="0.6"
                    fontSize="11" textAnchor="middle"
                    fontFamily="ui-serif, Georgia"
                    style={{ letterSpacing: "0.15em", textTransform: "uppercase" }}>
                {p}
              </text>
            </g>
          )
        )}

        {/* Edges — stroke width scales with weight. */}
        {edges.map((e, i) => {
          const a = positions[e.source_id]; const b = positions[e.target_id];
          if (!a || !b) return null;
          const active = hover && (e.source_id === hover || e.target_id === hover);
          const w = Math.max(1, Math.min(10, e.weight || 1));
          return (
            <g key={`e-${i}`}>
              <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                    stroke={e.color || "#C8A34A"}
                    strokeWidth={0.5 + w * 0.4}
                    strokeOpacity={active ? 0.95 : 0.35}
                    strokeLinecap="round"/>
              {active && e.relationship_type && (
                <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 4}
                      fill="#C8A34A" fontSize="9" textAnchor="middle"
                      style={{ pointerEvents: "none" }}>
                  {e.relationship_type}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes. */}
        {graphNodes.map((n) => {
          const p = positions[n.id]; if (!p) return null;
          const isHover = hover === n.id;
          const isNeighbour = neighbours.has(n.id);
          const col = PILLAR_COLORS[n.pillar] || PILLAR_COLORS.Unclassified;
          const r = isHover ? 10 : (isNeighbour ? 8 : 6);
          const opacity = (!hover || isHover || isNeighbour) ? 1 : 0.35;
          return (
            <g key={n.id} transform={`translate(${p.x}, ${p.y})`}
               style={{ cursor: "pointer" }}
               onMouseEnter={() => setHover(n.id)}
               onMouseLeave={() => setHover(null)}
               onClick={() => onNodeClick?.(n)}
               data-testid={`graph-node-${n.id}`}
               opacity={opacity}>
              <circle r={r}
                      fill={col} fillOpacity={isHover ? 0.9 : 0.7}
                      stroke={col} strokeWidth="1.5"/>
              <text x="0" y={-r - 4}
                    fill="#E4D4A8" fontSize={isHover ? 11 : 10}
                    textAnchor="middle"
                    style={{ pointerEvents: "none", fontFamily: "ui-serif, Georgia",
                             letterSpacing: "0.02em" }}>
                {n.title?.length > 24 ? n.title.slice(0, 22) + "…" : (n.title || "—")}
              </text>
              {isHover && n.kind && (
                <text x="0" y={r + 12}
                      fill="#9A9186" fontSize="9" textAnchor="middle"
                      style={{ pointerEvents: "none" }}>
                  {n.kind}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className="text-[10px] text-mist italic mt-2">
        Drag not supported (force-layout freezes on mount). Hover a node
        to highlight its codex-links. Click to open the codex entry.
        Heavy edges (weight 8-10) pull linked nodes into a tight core;
        weak edges (1-3) sit loose on the perimeter.
      </div>
    </div>
  );
}
