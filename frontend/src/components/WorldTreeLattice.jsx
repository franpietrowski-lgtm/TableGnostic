/**
 * WorldTreeLattice — V6.25.14
 *
 * The canonical Worldbuilding "Charts" infographic (Shieldice Studio)
 * rendered as an interactive lattice. Three staggered pillars
 * (Population · Geography · History) sit side-by-side; SVG dotted
 * bridges interconnect sibling rows so the GM sees — at a glance —
 * which Population entries are gravitationally pulled toward which
 * Geography or History entries.
 *
 * Each bridge is clickable. Clicking opens a `BridgePromptModal`
 * pre-seeded with a contextual narrative prompt (e.g. "What law of
 * Population.Laws shapes the moral fibre of Geography.Countries?").
 * Submitting the modal calls `POST /world-tree/bridge-sow` which
 * creates one codex node on each side of the bridge plus a
 * relationship-tagged codex edge between them — the GM's narrative
 * seed becomes a permanent two-node sub-graph.
 *
 * Layout strategy:
 *   • 3 columns of branch cards, vertically staggered to mimic the
 *     printed chart's flow.
 *   • Each branch card lists the codex nodes already docked into
 *     that section, with a small "Sow" affordance for direct
 *     same-pillar seeding.
 *   • Bridges are rendered into a single absolute-positioned SVG
 *     overlay that spans the lattice bounding box; we measure each
 *     branch card's centre via refs and draw straight dotted
 *     polylines between paired cards.
 *   • A "History lenses" strip (Political / Cultural / Social /
 *     Economic / Diplomatic) anchors the bottom — clicking a lens
 *     filters the History column to only entries tagged that way.
 *
 * Mobile:  the lattice collapses to a single-column accordion at
 * `<sm` (`md:grid-cols-3 grid-cols-1`); SVG bridges hide; bridge
 * prompts surface inside an "All Bridges" foldout the user can
 * walk through one at a time.
 */
import React, {
  useEffect, useMemo, useRef, useState, useLayoutEffect, useCallback,
} from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  GitBranch, Plus, Sparkles, Send, Loader2, X, ArrowRight,
  ChevronDown, ChevronRight,
} from "lucide-react";

const PILLAR_COLOR = {
  Population: "#9CC4FF",
  Geography:  "#A8E6A1",
  History:    "#E0B0E5",
};

// Hue used for the SVG bridge stroke — modulated by the source pillar
// so Population→Geography reads visually distinct from History bridges.
const BRIDGE_COLOR = {
  Population: "#9CC4FF",
  Geography:  "#A8E6A1",
  History:    "#E0B0E5",
};

const PILLAR_ORDER = ["Population", "Geography", "History"];

export default function WorldTreeLattice({
  campId, schema, populated, bridgePrompts, isGm, onChanged,
}) {
  // Refs — one per "Pillar.Branch" so the SVG overlay can measure each
  // card's centre point and draw a polyline to its bridge partner.
  const cardRefs = useRef({});
  const containerRef = useRef(null);
  const [bounds, setBounds] = useState({ width: 0, height: 0 });
  const [bridgePositions, setBridgePositions] = useState([]);
  const [bridgeModal, setBridgeModal] = useState(null);
  const [hoverBridge, setHoverBridge] = useState(null);
  const [historyLens, setHistoryLens] = useState(null);

  const measure = useCallback(() => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setBounds({ width: rect.width, height: rect.height });
    const next = (schema.cross_pillar_links || []).map(([src, tgt, rel], i) => {
      const a = cardRefs.current[src];
      const b = cardRefs.current[tgt];
      if (!a || !b) return null;
      const ar = a.getBoundingClientRect();
      const br = b.getBoundingClientRect();
      const ax = ar.left + ar.width / 2 - rect.left;
      const ay = ar.top + ar.height / 2 - rect.top;
      const bx = br.left + br.width / 2 - rect.left;
      const by = br.top + br.height / 2 - rect.top;
      // Pull endpoints to the card edge (not centre) so the line
      // doesn't dive through the card body.
      const dx = bx - ax; const dy = by - ay;
      const dist = Math.max(1, Math.hypot(dx, dy));
      const ux = dx / dist; const uy = dy / dist;
      const aOffsetX = ux * (ar.width / 2 - 8);
      const aOffsetY = uy * (ar.height / 2 - 8);
      const bOffsetX = -ux * (br.width / 2 - 8);
      const bOffsetY = -uy * (br.height / 2 - 8);
      return {
        i, src, tgt, rel,
        x1: ax + aOffsetX, y1: ay + aOffsetY,
        x2: bx + bOffsetX, y2: by + bOffsetY,
        srcPillar: src.split(".")[0],
      };
    }).filter(Boolean);
    setBridgePositions(next);
  }, [schema.cross_pillar_links]);

  useLayoutEffect(() => { measure(); }, [measure, populated]);
  useEffect(() => {
    const ro = new ResizeObserver(() => measure());
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", measure);
    return () => { ro.disconnect(); window.removeEventListener("resize", measure); };
  }, [measure]);

  const setCardRef = (sec) => (el) => { cardRefs.current[sec] = el; };

  const openBridge = (b) => {
    if (!isGm) return;
    setBridgeModal({
      src: b.src, tgt: b.tgt, relationship: b.rel,
      promptText: (bridgePrompts || {})[`${b.src}|${b.tgt}`]
        || `How does ${b.src} affect ${b.tgt}?`,
    });
  };

  return (
    <div className="space-y-4" data-testid="world-tree-lattice">
      <div className="text-[11px] text-mist italic" data-testid="lattice-legend">
        <span className="text-arcane-light">Dotted bridges are clickable.</span>
        {" "}Each one is a narrative seed — author the two sides of a
        cross-pillar idea and it becomes a permanent two-node sub-graph
        in your codex.
      </div>

      <div ref={containerRef} className="relative">
        {/* SVG overlay (desktop only) — rendered behind the cards. */}
        <svg
          className="absolute inset-0 pointer-events-none hidden md:block"
          width={bounds.width} height={bounds.height}
          style={{ overflow: "visible", zIndex: 1 }}
          data-testid="lattice-bridges-svg">
          {bridgePositions.map((b) => {
            const stroke = BRIDGE_COLOR[b.srcPillar] || "#9CC4FF";
            const isHover = hoverBridge === b.i;
            return (
              <g key={b.i}
                 className="pointer-events-auto cursor-pointer"
                 onClick={() => openBridge(b)}
                 onMouseEnter={() => setHoverBridge(b.i)}
                 onMouseLeave={() => setHoverBridge(null)}
                 data-testid={`lattice-bridge-${b.src}-${b.tgt}`.replace(/[\s.]+/g, "-")}>
                <line x1={b.x1} y1={b.y1} x2={b.x2} y2={b.y2}
                      stroke={stroke}
                      strokeWidth={isHover ? 2.4 : 1.4}
                      strokeDasharray="5 4"
                      opacity={isHover ? 0.95 : 0.55}/>
                {/* Mid-line label — only rendered on hover so it
                    doesn't crowd the lattice at rest. */}
                {isHover && (
                  <g>
                    <rect
                      x={(b.x1 + b.x2) / 2 - 56}
                      y={(b.y1 + b.y2) / 2 - 10}
                      width={112} height={20}
                      rx={4} fill="#0c0a14" stroke={stroke} strokeOpacity={0.6}/>
                    <text x={(b.x1 + b.x2) / 2}
                          y={(b.y1 + b.y2) / 2 + 4}
                          textAnchor="middle"
                          fontSize="10" fill={stroke}
                          style={{ fontFamily: "ui-sans-serif" }}>
                      {b.rel}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>

        {/* Lattice — 3 columns, vertically staggered offsets. */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 relative"
             style={{ zIndex: 2 }}
             data-testid="lattice-columns">
          {PILLAR_ORDER.map((pillar, colIdx) => {
            const meta = schema.pillars[pillar];
            // Stagger: middle col pushed down a hair on desktop to
            // better mirror the printed chart's dance.
            const stagger = colIdx === 1 ? "md:mt-6" : colIdx === 2 ? "md:mt-3" : "";
            const lenses = pillar === "History" ? schema.history_lenses : null;
            return (
              <div key={pillar}
                   className={`space-y-2 ${stagger}`}
                   data-testid={`lattice-col-${pillar}`}>
                <div className="card-mystic p-2 text-center"
                     style={{ borderColor: `${PILLAR_COLOR[pillar]}55` }}>
                  <div className="font-display text-base"
                       style={{ color: PILLAR_COLOR[pillar] }}>
                    {pillar}
                  </div>
                  <div className="text-[10px] text-mist italic">{meta.blurb}</div>
                </div>

                {pillar === "History" && lenses && (
                  <div className="flex flex-wrap gap-1 justify-center"
                       data-testid="lattice-history-lenses">
                    {lenses.map((l) => (
                      <button key={l}
                              onClick={() => setHistoryLens(historyLens === l ? null : l)}
                              className={`tag text-[10px] ${historyLens === l ? "border-gold text-gold-bright bg-gold/10" : ""}`}
                              data-testid={`lattice-lens-${l}`}>
                        {l}
                      </button>
                    ))}
                  </div>
                )}

                {(meta.branches || []).map((branch) => {
                  const sec = `${pillar}.${branch}`;
                  const items = (populated[sec] || []).filter((n) => {
                    if (pillar !== "History" || !historyLens) return true;
                    const tags = (n.tags || []).map((t) => (t || "").toLowerCase());
                    return tags.includes(historyLens.toLowerCase());
                  });
                  return (
                    <BranchCard
                      key={sec}
                      ref={setCardRef(sec)}
                      pillar={pillar}
                      branch={branch}
                      section={sec}
                      items={items}
                      campId={campId}
                      isGm={isGm}
                      onChanged={onChanged}/>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile: bridges-as-list fallback (the SVG hides at <md). */}
      <BridgesAccordion
        bridges={schema.cross_pillar_links || []}
        prompts={bridgePrompts || {}}
        onPick={(b) => openBridge({ src: b[0], tgt: b[1], rel: b[2] })}
        isGm={isGm}/>

      {bridgeModal && (
        <BridgePromptModal
          campId={campId}
          src={bridgeModal.src}
          tgt={bridgeModal.tgt}
          relationship={bridgeModal.relationship}
          promptText={bridgeModal.promptText}
          onClose={() => setBridgeModal(null)}
          onSeeded={() => {
            setBridgeModal(null);
            onChanged && onChanged();
          }}/>
      )}
    </div>
  );
}


// ───────────────────────────────────────────────────────────────────────
// Branch card — one box per Pillar.Branch slot, lists docked nodes,
// exposes a Sow input (same-pillar seeding) for the GM.
// ───────────────────────────────────────────────────────────────────────

const BranchCard = React.forwardRef(function BranchCard({
  pillar, branch, section, items, campId, isGm, onChanged,
}, ref) {
  const [seed, setSeed] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);

  const sow = async () => {
    if (!seed.trim()) return;
    setBusy(true);
    try {
      await api.post(`/campaigns/${campId}/codex-nodes`, {
        name: seed.trim(),
        node_kind: "concept",
        summary: "",
        creation_tree: { section, color: PILLAR_COLOR[pillar] },
      });
      setSeed("");
      onChanged && onChanged();
    } catch (e) {
      window.alert("Sow failed: "
        + (formatApiErrorDetail(e.response?.data?.detail) || e.message));
    } finally { setBusy(false); }
  };

  const hasItems = items.length > 0;

  return (
    <div ref={ref}
         className="card-mystic p-2 relative"
         style={{ borderColor: `${PILLAR_COLOR[pillar]}33` }}
         data-testid={`lattice-card-${section.replace(/[\s.]+/g, "-")}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-left">
        <div className="flex items-center gap-1">
          {open ? <ChevronDown className="w-3 h-3 text-mist"/>
                : <ChevronRight className="w-3 h-3 text-mist"/>}
          <span className="text-parchment font-display text-sm">{branch}</span>
        </div>
        {hasItems && (
          <span className="text-[10px] text-mist/70 tabular-nums">
            {items.length}
          </span>
        )}
      </button>

      {open && (
        <div className="mt-1.5 space-y-1">
          {items.map((it) => (
            <div key={it.id}
                 className="text-[11px] text-parchment/90 border-l-2 pl-2 py-0.5
                            hover:bg-void/40 cursor-pointer"
                 style={{ borderColor: PILLAR_COLOR[pillar] + "88" }}
                 onClick={() => window.dispatchEvent(new CustomEvent(
                   "tg:open-codex-node",
                   { detail: { node_id: it.id, campaign_id: campId } }))}
                 data-testid={`lattice-item-${it.id}`}>
              {it.name}
              {(it.tags || []).includes("bridge-sown") && (
                <span className="ml-1 text-[9px] text-arcane">⟿ bridge</span>
              )}
            </div>
          ))}
          {!hasItems && (
            <div className="text-[10px] text-mist italic">No entries yet.</div>
          )}

          {isGm && (
            <div className="pt-1 border-t border-gold/10">
              <input className="input text-[11px] w-full"
                     placeholder={`Seed a ${branch}…`}
                     value={seed}
                     onChange={(e) => setSeed(e.target.value)}
                     onKeyDown={(e) => { if (e.key === "Enter") sow(); }}
                     data-testid={`lattice-seed-${section.replace(/[\s.]+/g, "-")}`}/>
              <button onClick={sow} disabled={busy || !seed.trim()}
                      className="btn btn-ghost text-[10px] mt-1"
                      data-testid={`lattice-sow-${section.replace(/[\s.]+/g, "-")}`}>
                {busy ? <Loader2 className="w-3 h-3 animate-spin"/>
                      : <Plus className="w-3 h-3"/>}
                Sow
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
});


// ───────────────────────────────────────────────────────────────────────
// Mobile bridges accordion (replaces the SVG overlay on narrow screens).
// ───────────────────────────────────────────────────────────────────────

function BridgesAccordion({ bridges, prompts, onPick, isGm }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="md:hidden card-mystic p-2"
         data-testid="lattice-mobile-bridges">
      <button onClick={() => setOpen(!open)}
              className="w-full flex items-center justify-between">
        <div className="flex items-center gap-1">
          <GitBranch className="w-3 h-3 text-arcane"/>
          <span className="text-parchment font-display text-sm">
            Cross-pillar bridges · {bridges.length}
          </span>
        </div>
        {open ? <ChevronDown className="w-3 h-3"/>
              : <ChevronRight className="w-3 h-3"/>}
      </button>
      {open && (
        <div className="mt-2 space-y-1 max-h-72 overflow-y-auto">
          {bridges.map((b, i) => (
            <button key={i}
                    onClick={() => isGm && onPick(b)}
                    disabled={!isGm}
                    className="w-full text-left text-[11px] border-l-2 border-arcane/30 pl-2 py-1
                               hover:bg-void/40 disabled:opacity-50">
              <span className="text-mist">{b[0]}</span>
              <ArrowRight className="inline w-3 h-3 mx-1 text-arcane-light"/>
              <span className="text-gold-bright">{b[1]}</span>
              <span className="text-arcane-light italic ml-1">— {b[2]}</span>
              {prompts[`${b[0]}|${b[1]}`] && (
                <div className="text-[10px] text-mist/70 mt-0.5">
                  {prompts[`${b[0]}|${b[1]}`]}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}


// ───────────────────────────────────────────────────────────────────────
// Bridge prompt modal — author both sides of a cross-pillar bridge,
// then POST /world-tree/bridge-sow seeds twin codex nodes + edge.
// ───────────────────────────────────────────────────────────────────────

function BridgePromptModal({
  campId, src, tgt, relationship, promptText, onClose, onSeeded,
}) {
  const [srcName, setSrcName] = useState("");
  const [srcSummary, setSrcSummary] = useState("");
  const [tgtName, setTgtName] = useState("");
  const [tgtSummary, setTgtSummary] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async () => {
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${campId}/world-tree/bridge-sow`, {
        src_section: src, tgt_section: tgt,
        relationship,
        src_name: srcName.trim(),
        src_summary: srcSummary.trim(),
        tgt_name: tgtName.trim(),
        tgt_summary: tgtSummary.trim(),
      });
      onSeeded && onSeeded();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-void/80 z-[200] flex items-center justify-center p-4"
         onClick={onClose}
         data-testid="bridge-prompt-modal">
      <div className="card-mystic p-5 max-w-2xl w-full max-h-[90vh] overflow-y-auto
                      relative space-y-3"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose}
                className="absolute top-2 right-2 text-mist hover:text-parchment"
                data-testid="bridge-prompt-close">
          <X className="w-4 h-4"/>
        </button>
        <div>
          <div className="label-ref flex items-center gap-2">
            <Sparkles className="w-3 h-3 text-arcane"/>
            Bridge Prompt
          </div>
          <div className="text-[12px] mt-1 text-parchment">
            <span className="text-mist">{src}</span>
            <span className="text-arcane-light italic mx-2">— {relationship} →</span>
            <span className="text-gold-bright">{tgt}</span>
          </div>
          <div className="text-[12px] text-arcane-light italic mt-2 border-l-2
                          border-arcane/40 pl-3 py-1 bg-void/40">
            {promptText}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-widest text-mist">
              Source: {src}
            </div>
            <input className="input text-sm w-full"
                   placeholder="Name of the source node"
                   value={srcName}
                   onChange={(e) => setSrcName(e.target.value)}
                   data-testid="bridge-src-name"/>
            <textarea className="input text-xs w-full" rows={3}
                      placeholder="Optional summary"
                      value={srcSummary}
                      onChange={(e) => setSrcSummary(e.target.value)}
                      data-testid="bridge-src-summary"/>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-widest text-mist">
              Target: {tgt}
            </div>
            <input className="input text-sm w-full"
                   placeholder="Name of the target node"
                   value={tgtName}
                   onChange={(e) => setTgtName(e.target.value)}
                   data-testid="bridge-tgt-name"/>
            <textarea className="input text-xs w-full" rows={3}
                      placeholder="Optional summary"
                      value={tgtSummary}
                      onChange={(e) => setTgtSummary(e.target.value)}
                      data-testid="bridge-tgt-summary"/>
          </div>
        </div>

        {err && <div className="text-ember text-xs"
                     data-testid="bridge-error">{err}</div>}

        <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
          <button onClick={onClose}
                  className="btn btn-ghost text-xs"
                  data-testid="bridge-cancel">Cancel</button>
          <button onClick={submit}
                  disabled={busy || !srcName.trim() || !tgtName.trim()}
                  className="btn btn-primary text-xs"
                  data-testid="bridge-submit">
            {busy ? <Loader2 className="w-3 h-3 animate-spin"/>
                  : <Send className="w-3 h-3"/>}
            Sow twin nodes &amp; bridge
          </button>
        </div>
      </div>
    </div>
  );
}
