import React, { useEffect, useRef, useState } from "react";
import { colorForType } from "../lib/nodeTemplates";
import { Network, Maximize2, X } from "lucide-react";

/**
 * Lightweight force-directed graph in pure SVG.
 * Runs a small physics simulation (Verlet-style) for a few hundred ticks.
 * No external dependencies — keeps bundle tiny.
 */
export default function KnowledgeGraph({ nodes = [], edges = [], onSelect, selectedId, height = 520 }) {
  const svgRef = useRef(null);
  const [pos, setPos] = useState({});
  const [hovered, setHovered] = useState(null);
  const [drag, setDrag] = useState(null);
  const W = 1000, H = height;

  // Initialise positions in a circle
  useEffect(() => {
    const n = nodes.length || 1;
    const cx = W / 2, cy = H / 2;
    const r = Math.min(W, H) * 0.35;
    const next = {};
    nodes.forEach((nd, i) => {
      const a = (i / n) * Math.PI * 2;
      next[nd.id] = pos[nd.id] || {
        x: cx + Math.cos(a) * r * (0.6 + Math.random() * 0.4),
        y: cy + Math.sin(a) * r * (0.6 + Math.random() * 0.4),
        vx: 0, vy: 0,
      };
    });
    setPos(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length]);

  // Run physics simulation
  useEffect(() => {
    if (nodes.length === 0) return;
    let frame = 0;
    let raf = null;
    const k = 0.002, springLen = 160, repulsion = 9000, damping = 0.82, centerPull = 0.0008;
    const tick = () => {
      setPos((prev) => {
        const next = { ...prev };
        // initialize forces
        const f = {};
        nodes.forEach((n) => { f[n.id] = { x: 0, y: 0 }; });
        // Repulsion between nodes
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i].id, b = nodes[j].id;
            if (!next[a] || !next[b]) continue;
            const dx = next[a].x - next[b].x, dy = next[a].y - next[b].y;
            const d2 = dx*dx + dy*dy + 0.01;
            const d = Math.sqrt(d2);
            const force = repulsion / d2;
            f[a].x += (dx / d) * force; f[a].y += (dy / d) * force;
            f[b].x -= (dx / d) * force; f[b].y -= (dy / d) * force;
          }
        }
        // Spring along edges
        edges.forEach((e) => {
          const a = e.from_node, b = e.to_node;
          if (!next[a] || !next[b]) return;
          const dx = next[b].x - next[a].x, dy = next[b].y - next[a].y;
          const d = Math.sqrt(dx*dx + dy*dy) + 0.01;
          const diff = (d - springLen) * k;
          f[a].x += (dx / d) * diff * 80; f[a].y += (dy / d) * diff * 80;
          f[b].x -= (dx / d) * diff * 80; f[b].y -= (dy / d) * diff * 80;
        });
        // Centering force
        nodes.forEach((n) => {
          if (!next[n.id]) return;
          f[n.id].x += (W/2 - next[n.id].x) * centerPull;
          f[n.id].y += (H/2 - next[n.id].y) * centerPull;
        });
        // Integrate
        nodes.forEach((n) => {
          const p = next[n.id]; if (!p) return;
          if (drag && drag.id === n.id) return;
          p.vx = (p.vx + f[n.id].x) * damping;
          p.vy = (p.vy + f[n.id].y) * damping;
          p.x += p.vx; p.y += p.vy;
          // bounds
          p.x = Math.max(40, Math.min(W - 40, p.x));
          p.y = Math.max(40, Math.min(H - 40, p.y));
        });
        return next;
      });
      frame++;
      if (frame < 240) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => raf && cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

  // Drag interaction
  const onPointerDown = (e, id) => {
    const svg = svgRef.current; if (!svg) return;
    const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    const ctm = svg.getScreenCTM().inverse();
    const sp = pt.matrixTransform(ctm);
    setDrag({ id, dx: sp.x - pos[id].x, dy: sp.y - pos[id].y });
  };
  const onPointerMove = (e) => {
    if (!drag) return;
    const svg = svgRef.current; if (!svg) return;
    const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    const ctm = svg.getScreenCTM().inverse();
    const sp = pt.matrixTransform(ctm);
    setPos((p) => ({ ...p, [drag.id]: { ...p[drag.id], x: sp.x - drag.dx, y: sp.y - drag.dy, vx: 0, vy: 0 } }));
  };
  const onPointerUp = () => setDrag(null);

  return (
    <div className="card-mystic p-3 relative grain" style={{ height }} data-testid="graph-canvas">
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="w-full h-full select-none"
           onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerLeave={onPointerUp}>
        <defs>
          <radialGradient id="bgglow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#6d4a9e" stopOpacity="0.07"/>
            <stop offset="100%" stopColor="transparent"/>
          </radialGradient>
          <filter id="nodeshadow"><feGaussianBlur stdDeviation="2"/></filter>
        </defs>
        <rect width={W} height={H} fill="url(#bgglow)"/>

        {/* Edges */}
        {edges.map((e, i) => {
          const a = pos[e.from_node], b = pos[e.to_node];
          if (!a || !b) return null;
          return (
            <g key={i}>
              <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                    stroke="rgba(212,175,55,0.25)" strokeWidth="1"/>
              {e.label && (
                <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 4} fill="#c8a34a"
                      fontSize="9" textAnchor="middle" className="font-mono"
                      style={{ pointerEvents: "none" }}>
                  {e.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((n) => {
          const p = pos[n.id]; if (!p) return null;
          const c = colorForType(n.type);
          const isSel = selectedId === n.id;
          const isHov = hovered === n.id;
          const r = isSel ? 18 : isHov ? 15 : 12;
          return (
            <g key={n.id} transform={`translate(${p.x}, ${p.y})`}
               onPointerDown={(e) => onPointerDown(e, n.id)}
               onClick={() => onSelect && onSelect(n)}
               onPointerEnter={() => setHovered(n.id)}
               onPointerLeave={() => setHovered(null)}
               style={{ cursor: "pointer" }}>
              <circle r={r + 6} fill={c} opacity={0.15}/>
              <circle r={r} fill={c} opacity={0.85} stroke={isSel ? "#e5c370" : "rgba(0,0,0,0.4)"}
                      strokeWidth={isSel ? 2.5 : 1}/>
              <text y={r + 14} fill="#e9e3d2" fontSize="10" textAnchor="middle"
                    className="font-display tracking-wider" style={{ pointerEvents: "none" }}>
                {n.title.length > 20 ? n.title.slice(0, 20) + "…" : n.title}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="absolute top-3 left-3 text-[10px] font-ui uppercase tracking-widest text-mist/60 flex items-center gap-2">
        <Network className="w-3 h-3"/> {nodes.length} nodes · {edges.length} edges
      </div>
      <div className="absolute bottom-3 right-3 text-[10px] font-ui italic text-mist/50">
        drag to reposition · click to inspect
      </div>
    </div>
  );
}
