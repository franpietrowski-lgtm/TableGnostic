/**
 * WorldCreationTree — V6.20
 *
 * Atelier sub-pane (mounted under Atelier · Genesis or Atelier · Worldbuild).
 * Renders the canonical 3-pillar Creation Tree (Population / Geography /
 * History) with the cross-pillar links the user spec'd. Each branch shows
 * the codex nodes already tagged into it, and exposes a "Seed prompt"
 * input for the GM to dump narrative cues against the branch.
 *
 * Plus a Creation Myth panel (root campaign-level lore) and the Codex
 * Link Widget modal (editable relationship type / color / weight 1-10).
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, Trash2, X, Sparkles, GitBranch, Link2, List, Network, Layers } from "lucide-react";
import WorldTreeGraph from "./WorldTreeGraph";
import WorldTreeLattice from "./WorldTreeLattice";

const PILLAR_COLORS = {
  Population: "#9CC4FF",
  Geography:  "#A8E6A1",
  History:    "#E0B0E5",
};

export default function WorldCreationTree({ campId, isGm }) {
  const [data, setData] = useState(null);
  const [myths, setMyths] = useState([]);
  const [codexLinks, setCodexLinks] = useState([]);
  const [viewMode, setViewMode] = useState("lattice"); // "lattice" | "pillars" | "graph"
  const [err, setErr] = useState("");
  const [linkModal, setLinkModal] = useState(null); // { source, target } or full edge

  const refresh = useCallback(async () => {
    try {
      const [{ data: tree }, { data: m }, linksRes] = await Promise.all([
        api.get(`/campaigns/${campId}/creation-tree`),
        api.get(`/campaigns/${campId}/creation-myths`),
        api.get(`/campaigns/${campId}/codex-links`).catch(() => ({ data: { edges: [] } })),
      ]);
      setData(tree);
      setMyths(m.myths || []);
      setCodexLinks(linksRes.data?.edges || linksRes.data?.codex_links || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [campId]);
  useEffect(() => { refresh(); }, [refresh]);

  // Flatten populated nodes across all pillars/branches for the graph.
  // NOTE: must be declared before any early return to satisfy the
  // react-hooks/rules-of-hooks lint rule.
  // V6.22 — backend returns populated as a flat map keyed by
  // "Pillar.Branch" (e.g., "Population.Factions"). Split the key so
  // each node carries its pillar + branch in `fields` for the graph
  // clusterer to pick up.
  const allNodes = useMemo(() => {
    const out = [];
    Object.entries(data?.populated || {}).forEach(([section, items]) => {
      const [pillar, branch] = section.split(".");
      (items || []).forEach((n) => {
        out.push({
          ...n,
          fields: { ...(n.fields || {}),
                     pillar: n.fields?.pillar || pillar,
                     pillar_branch: n.fields?.pillar_branch || branch },
        });
      });
    });
    // Also include unplaced nodes so the GM can see everything.
    (data?.unplaced || []).forEach((n) => {
      out.push({ ...n, fields: { ...(n.fields || {}), pillar: "Unclassified" } });
    });
    return out;
  }, [data]);

  if (!data) return null;
  const rootMyth = myths.find((m) => !m.parent_node_id);

  return (
    <div data-testid="world-creation-tree" className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="label-ref">Atelier · World Creation Tree</div>
          <h2 className="font-display text-2xl text-parchment mt-1">
            Roots, pillars, and cross-currents
          </h2>
          <p className="text-mist text-sm mt-1 italic max-w-2xl">
            {data.schema.root.blurb} {data.schema.logic_notes.join(" ")}
          </p>
        </div>
        {/* V6.21 Cut D V2 + V6.25.14 — view-mode toggle (lattice default). */}
        <div className="flex gap-1 flex-wrap" data-testid="wct-view-mode">
          <button onClick={() => setViewMode("lattice")}
                  className={`btn text-xs ${viewMode === "lattice" ? "btn-primary" : "btn-ghost"}`}
                  data-testid="wct-view-lattice">
            <Layers className="w-3 h-3"/> Lattice
          </button>
          <button onClick={() => setViewMode("pillars")}
                  className={`btn text-xs ${viewMode === "pillars" ? "btn-primary" : "btn-ghost"}`}
                  data-testid="wct-view-pillars">
            <List className="w-3 h-3"/> Pillars
          </button>
          <button onClick={() => setViewMode("graph")}
                  className={`btn text-xs ${viewMode === "graph" ? "btn-primary" : "btn-ghost"}`}
                  data-testid="wct-view-graph">
            <Network className="w-3 h-3"/> Graph
          </button>
        </div>
      </div>

      {err && <div className="text-ember text-xs" data-testid="wct-error">{err}</div>}

      {/* Creation Myth root */}
      <CreationMythRootCard
        campId={campId}
        myth={rootMyth}
        isGm={isGm}
        onChanged={refresh}/>

      {viewMode === "graph" ? (
        /* V6.21 Cut D V2 — Graph view clustering. */
        <WorldTreeGraph nodes={allNodes} edges={codexLinks}
                         onNodeClick={(n) => {
                           // Dispatch codex-detail open request the parent
                           // Atelier tab can listen for.
                           window.dispatchEvent(new CustomEvent("tg:open-codex-node", {
                             detail: { node_id: n.id, campaign_id: campId },
                           }));
                         }}/>
      ) : viewMode === "lattice" ? (
        /* V6.25.14 — staggered lattice with clickable cross-pillar bridges. */
        <>
          {(data.unplaced?.length || 0) > 0 && (
            <UnplacedTray campId={campId} unplaced={data.unplaced}
                           schema={data.schema}
                           isGm={isGm} onChanged={refresh}/>
          )}
          <WorldTreeLattice
            campId={campId}
            schema={data.schema}
            populated={data.populated || {}}
            bridgePrompts={data.bridge_prompts || {}}
            isGm={isGm}
            onChanged={refresh}/>
        </>
      ) : (
        <>
        {/* V6.22 — Unplaced codex tray. Shows auto-classified legacy
            codex entries above the pillar panels; GM can manually
            re-dock a node by clicking the 'pin' button. */}
        {(data.unplaced?.length || 0) > 0 && (
          <UnplacedTray campId={campId} unplaced={data.unplaced}
                         schema={data.schema}
                         isGm={isGm} onChanged={refresh}/>
        )}
        {/* Three pillars */}
        <div className="grid md:grid-cols-3 gap-3" data-testid="wct-pillars">
          {Object.entries(data.schema.pillars).map(([pillar, meta]) => (
            <PillarPanel key={pillar}
                          campId={campId}
                          pillar={pillar}
                          meta={meta}
                          populated={data.populated}
                          color={PILLAR_COLORS[pillar]}
                          isGm={isGm}
                          onChanged={refresh}/>
          ))}
        </div>

        {/* Cross-pillar arrow registry */}
        <CrossPillarLinks links={data.schema.cross_pillar_links}/>
        </>
      )}

      {/* Codex Link Widget launcher */}
      <button onClick={() => setLinkModal({ source_id: "", target_id: "" })}
              disabled={!isGm}
              className="btn btn-ghost text-xs"
              data-testid="open-codex-link-widget">
        <Link2 className="w-3 h-3"/> Add Codex Link
      </button>

      {linkModal && (
        <CodexLinkWidget campId={campId} edge={linkModal}
                          onClose={() => setLinkModal(null)}
                          onSaved={() => { setLinkModal(null); refresh(); }}/>
      )}

      {/* Per-node creation myths */}
      <div data-testid="wct-child-myths">
        <div className="label-ref">Per-node creation myths</div>
        {myths.filter((m) => m.parent_node_id).length === 0 ? (
          <div className="text-mist italic text-sm mt-1">
            No node-level myths yet. Open any codex entry, tick "Has own
            creation myth", and a child myth panel will save here.
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-2 mt-2">
            {myths.filter((m) => m.parent_node_id).map((m) => (
              <div key={m.id} className="card-mystic p-3"
                   data-testid={`wct-child-myth-${m.id}`}>
                <div className="text-sm text-parchment font-ui">{m.title}</div>
                <div className="text-[10px] text-mist mt-0.5">
                  Parent node: {m.parent_node_id}
                  {m.contradicts_root && (
                    <span className="ml-2 tag border-ember/40 text-ember text-[9px]">
                      contradicts root
                    </span>
                  )}
                </div>
                {m.body && (
                  <div className="text-[11px] text-parchment/85 italic mt-1 line-clamp-3">
                    {m.body}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * UnplacedTray — V6.22. Shows codex nodes that were auto-classified
 * (carry `auto_placed: true` from the backend) so the GM can confirm
 * the placement or re-dock to a different pillar/branch. Also shows
 * anything the classifier couldn't figure out under "Unknown type".
 *
 * V6.23 — Pin-to-pillar UI. Each row gets a pillar.branch select + Pin
 * button calling PATCH /campaigns/{cid}/codex-nodes/{nid}/place. GMs
 * can also bulk-pin everything via the "Auto-classify all" button (a
 * no-op for already-tagged entries; keeps RAW classifier mapping).
 */
function UnplacedTray({ campId, unplaced, schema, isGm, onChanged }) {
  const [pinning, setPinning] = useState({});  // { nodeId: section }
  const [busy, setBusy] = useState({});
  const [err, setErr] = useState("");

  // Build the pillar.branch option list from the schema so GMs can
  // dock into ANY canonical section (not just the classifier guesses).
  const allSections = useMemo(() => {
    const out = [];
    Object.entries(schema?.pillars || {}).forEach(([pillar, meta]) => {
      (meta.branches || []).forEach((branch) => {
        out.push(`${pillar}.${branch}`);
      });
    });
    return out;
  }, [schema]);

  const pin = async (nodeId) => {
    const section = pinning[nodeId];
    if (!section) { setErr("Pick a pillar.branch first."); return; }
    setBusy({ ...busy, [nodeId]: true }); setErr("");
    try {
      await api.patch(
        `/campaigns/${campId}/codex-nodes/${nodeId}/place`,
        { section },
      );
      onChanged && onChanged();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy({ ...busy, [nodeId]: false });
    }
  };

  if (unplaced.length === 0) return null;

  return (
    <div className="card-mystic p-3" data-testid="wct-unplaced-tray">
      <div className="flex items-baseline justify-between">
        <div className="label-ref">Unclassified codex entries</div>
        <span className="text-[10px] text-mist italic">
          {unplaced.length} unplaced — type didn't match a pillar.
        </span>
      </div>
      <div className="text-[10px] text-mist/80 italic mt-0.5 mb-2">
        Pick a pillar.branch and pin so the World Tree reflects your
        canon. Already-classified entries appear with a subtle "auto"
        badge inside the pillar panels below.
      </div>
      {!isGm ? (
        <div className="flex flex-wrap gap-1">
          {unplaced.slice(0, 30).map((n) => (
            <span key={n.id} className="tag text-[10px]"
                  data-testid={`wct-unplaced-${n.id}`}>
              {n.name} <span className="text-mist ml-1">({n.type || "?"})</span>
            </span>
          ))}
        </div>
      ) : (
        <div className="space-y-1.5 max-h-72 overflow-y-auto">
          {unplaced.slice(0, 60).map((n) => (
            <div key={n.id} className="border border-gold/15 rounded-sm px-2 py-1.5
                                         flex items-center gap-2 flex-wrap"
                 data-testid={`wct-unplaced-${n.id}`}>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-parchment truncate">
                  {n.name}
                </div>
                <div className="text-[10px] text-mist">
                  {n.type || "no type"}
                  {n.summary && <span className="italic"> — {n.summary.slice(0, 90)}</span>}
                </div>
              </div>
              <select className="select text-[10px] py-1 max-w-[180px]"
                      value={pinning[n.id] || ""}
                      onChange={(e) => setPinning({ ...pinning, [n.id]: e.target.value })}
                      data-testid={`wct-pin-select-${n.id}`}>
                <option value="">— pick pillar.branch —</option>
                {allSections.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <button onClick={() => pin(n.id)}
                      disabled={busy[n.id] || !pinning[n.id]}
                      className="btn btn-ghost text-[10px]"
                      data-testid={`wct-pin-btn-${n.id}`}>
                <Link2 className="w-3 h-3"/> Pin
              </button>
            </div>
          ))}
        </div>
      )}
      {err && <div className="text-ember text-[11px] mt-2">{err}</div>}
    </div>
  );
}

// ─── Pillar panel ───────────────────────────────────────────────────────

function PillarPanel({ pillar, meta, populated, color, campId, isGm, onChanged }) {
  return (
    <div className="card-mystic p-3 border-l-2"
         style={{ borderLeftColor: color }}
         data-testid={`wct-pillar-${pillar.toLowerCase()}`}>
      <div className="font-display text-lg" style={{ color }}>{pillar}</div>
      <div className="text-[11px] text-mist italic mt-1">{meta.blurb}</div>
      <div className="mt-3 space-y-1">
        {meta.branches.map((branch) => {
          const sec = `${pillar}.${branch}`;
          const items = populated[sec] || [];
          return (
            <BranchRow key={sec}
                        section={sec}
                        branch={branch}
                        items={items}
                        campId={campId}
                        color={color}
                        isGm={isGm}
                        onChanged={onChanged}/>
          );
        })}
      </div>
    </div>
  );
}

function BranchRow({ section, branch, items, campId, color, isGm, onChanged }) {
  const [open, setOpen] = useState(false);
  const [seed, setSeed] = useState("");
  const [busy, setBusy] = useState(false);

  const sow = async () => {
    if (!seed.trim()) return;
    setBusy(true);
    try {
      // Create a codex node tagged with creation_tree.section
      await api.post(`/campaigns/${campId}/codex-nodes`, {
        name: seed.split("\n")[0].slice(0, 80),
        node_kind: "concept",
        summary: seed,
        creation_tree: { section, color, weight: 5 },
      });
      setSeed("");
      setOpen(false);
      onChanged && onChanged();
    } catch (e) {
      // Silent fail — surface in console.
      console.warn("Sow failed:", e);
    } finally { setBusy(false); }
  };

  return (
    <div className="border border-gold/10 rounded-sm" data-testid={`wct-branch-${section.replace(/\W+/g, "-")}`}>
      <button onClick={() => setOpen(!open)}
              className="w-full flex items-center justify-between px-2 py-1 text-[12px] text-parchment hover:bg-gold/5 transition-colors">
        <span className="flex items-center gap-1.5">
          <GitBranch className="w-3 h-3" style={{ color }}/>
          {branch}
        </span>
        <span className="text-[10px] text-mist">
          {items.length}{items.length > 0 ? " seeded" : ""}
        </span>
      </button>
      {open && (
        <div className="px-2 py-2 border-t border-gold/10">
          {items.length > 0 && (
            <div className="space-y-0.5 mb-2">
              {items.map((it) => (
                <div key={it.id} className="text-[11px] text-mist border-l-2 pl-2 cursor-pointer hover:bg-gold/5 rounded-sm"
                     style={{ borderColor: it.color || color }}
                     onClick={() => window.dispatchEvent(new CustomEvent("tg:open-codex-node", { detail: { node_id: it.id, campaign_id: campId } }))}
                     data-testid={`wct-entry-${it.id}`}>
                  <span className="text-parchment">{it.name || it.title}</span>
                  {it.auto_placed && (
                    <span className="ml-1 text-[9px] text-gold-bright/70 italic"
                          title="Auto-classified by node type — confirm or re-dock to a different branch.">
                      · auto
                    </span>
                  )}
                  {it.summary && <span className="text-mist/80 italic ml-1">— {it.summary.slice(0, 80)}</span>}
                </div>
              ))}
            </div>
          )}
          {isGm && (
            <div>
              <textarea className="input w-full text-xs" rows={2}
                        value={seed}
                        onChange={(e) => setSeed(e.target.value)}
                        placeholder={`Seed an idea for ${branch}…`}
                        data-testid={`wct-seed-${section.replace(/\W+/g, "-")}`}/>
              <button onClick={sow} disabled={busy || !seed.trim()}
                      className="btn btn-ghost text-[10px] mt-1"
                      data-testid={`wct-sow-${section.replace(/\W+/g, "-")}`}>
                <Plus className="w-3 h-3"/> Sow as codex node
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CrossPillarLinks({ links }) {
  return (
    <details className="card-mystic p-3" data-testid="wct-cross-pillar">
      <summary className="text-[11px] uppercase tracking-widest text-mist cursor-pointer hover:text-gold">
        Cross-pillar arrows · {links.length} connectors
      </summary>
      <div className="mt-2 grid sm:grid-cols-2 gap-1">
        {links.map(([src, tgt, rel], i) => (
          <div key={i} className="text-[11px] text-parchment border-l-2 border-arcane/30 pl-2 py-0.5">
            <span className="text-mist">{src}</span>
            <span className="text-arcane-light mx-1">— {rel} →</span>
            <span className="text-gold-bright">{tgt}</span>
          </div>
        ))}
      </div>
    </details>
  );
}

// ─── Creation Myth root card ───────────────────────────────────────────

function CreationMythRootCard({ campId, myth, isGm, onChanged }) {
  const [edit, setEdit] = useState(false);
  const [data, setData] = useState({
    title: myth?.title || "",
    body: myth?.body || "",
    pillar_seeds: myth?.pillar_seeds || {},
  });
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setData({ title: myth?.title || "",
               body: myth?.body || "",
               pillar_seeds: myth?.pillar_seeds || {} });
  }, [myth?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = async () => {
    setBusy(true);
    try {
      if (myth) {
        await api.patch(`/campaigns/${campId}/creation-myths/${myth.id}`, data);
      } else {
        await api.post(`/campaigns/${campId}/creation-myths`, data);
      }
      setEdit(false);
      onChanged && onChanged();
    } catch (e) {
      console.warn("Save myth failed:", e);
    } finally { setBusy(false); }
  };

  return (
    <div className="card-mystic p-4 border-l-2 border-gold-bright/40"
         data-testid="wct-myth-root">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <div className="label-ref flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-gold-bright"/> Creation Myth · root
          </div>
          {!edit && (
            <h3 className="font-display text-xl text-parchment mt-0.5">
              {myth?.title || "Unwritten — every world begins somewhere."}
            </h3>
          )}
        </div>
        {isGm && !edit && (
          <button onClick={() => setEdit(true)}
                  className="btn btn-ghost text-xs"
                  data-testid="wct-myth-edit">
            {myth ? "Edit" : "Write the origin"}
          </button>
        )}
      </div>

      {!edit && myth?.body && (
        <p className="text-sm text-parchment/85 italic mt-2 leading-relaxed"
           data-testid="wct-myth-body">
          {myth.body}
        </p>
      )}

      {edit && (
        <div className="mt-2 space-y-2">
          <input className="input w-full" placeholder="Title (e.g. The Sundering)"
                 value={data.title}
                 onChange={(e) => setData({ ...data, title: e.target.value })}
                 data-testid="wct-myth-input-title"/>
          <textarea className="input w-full" rows={5}
                    placeholder="Origin lore — read aloud at session 0."
                    value={data.body}
                    onChange={(e) => setData({ ...data, body: e.target.value })}
                    data-testid="wct-myth-input-body"/>
          <div className="grid sm:grid-cols-3 gap-2">
            {["Population", "Geography", "History"].map((p) => (
              <input key={p} className="input"
                     placeholder={`${p} seed phrase…`}
                     value={data.pillar_seeds[p] || ""}
                     onChange={(e) => setData({
                       ...data,
                       pillar_seeds: { ...data.pillar_seeds, [p]: e.target.value }
                     })}
                     data-testid={`wct-myth-seed-${p.toLowerCase()}`}/>
            ))}
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => setEdit(false)} className="btn btn-ghost text-xs">Cancel</button>
            <button onClick={save} disabled={busy} className="btn btn-primary text-xs"
                    data-testid="wct-myth-save">
              {busy ? "Saving…" : "Save myth"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Codex Link Widget ──────────────────────────────────────────────────

const RELATIONSHIP_PRESETS = [
  "ally", "rival", "enemy", "mentor", "student", "family",
  "lover", "ex", "owns", "owned by", "born at", "rules over",
  "worships", "worshipped by", "based at", "claims",
  "shares with", "leads to", "predates", "documented in",
  "tensions", "remembered as", "occurs at", "native to",
  "contradicts", "shapes", "related",
];

const COLOR_PRESETS = [
  "#C9A876", "#9CC4FF", "#A8E6A1", "#E0B0E5", "#FFB39C",
  "#FFD66B", "#FF7373", "#73D3FF",
];

function CodexLinkWidget({ campId, edge, onClose, onSaved }) {
  const [data, setData] = useState({
    source_id: edge.source_id || "",
    target_id: edge.target_id || "",
    relationship_type: edge.relationship_type || "related",
    color: edge.color || "#C9A876",
    weight: edge.weight || 5,
    bidirectional: !!edge.bidirectional,
    notes: edge.notes || "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    api.get(`/campaigns/${campId}/codex-nodes`)
      .then((r) => setNodes(Array.isArray(r.data) ? r.data : (r.data?.nodes || [])))
      .catch(() => {});
  }, [campId]);

  const save = async () => {
    if (!data.source_id || !data.target_id) {
      setErr("Pick both source and target nodes."); return;
    }
    setBusy(true); setErr("");
    try {
      if (edge.id) {
        await api.patch(`/campaigns/${campId}/codex-links/${edge.id}`, data);
      } else {
        await api.post(`/campaigns/${campId}/codex-links`, data);
      }
      onSaved && onSaved();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-void/90 backdrop-blur-md z-50 flex items-start justify-center pt-20 p-4"
         onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
         data-testid="codex-link-widget">
      <div className="card-mystic max-w-md w-full p-5 shadow-2xl">
        <div className="flex items-baseline justify-between mb-3">
          <div>
            <div className="label-ref">Codex Link Widget</div>
            <h3 className="font-display text-xl text-parchment mt-0.5">
              {edge.id ? "Edit relationship" : "New relationship"}
            </h3>
          </div>
          <button onClick={onClose} className="text-mist hover:text-gold"
                  data-testid="codex-link-close">
            <X className="w-5 h-5"/>
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="label-ref">Source node</label>
            <select className="select mt-1 w-full" value={data.source_id}
                    onChange={(e) => setData({ ...data, source_id: e.target.value })}
                    data-testid="codex-link-source">
              <option value="">— pick source —</option>
              {nodes.map((n) => <option key={n.id} value={n.id}>{n.name || n.title || "(unnamed)"}</option>)}
            </select>
          </div>
          <div>
            <label className="label-ref">Target node</label>
            <select className="select mt-1 w-full" value={data.target_id}
                    onChange={(e) => setData({ ...data, target_id: e.target.value })}
                    data-testid="codex-link-target">
              <option value="">— pick target —</option>
              {nodes.map((n) => <option key={n.id} value={n.id}>{n.name || n.title || "(unnamed)"}</option>)}
            </select>
          </div>

          <div>
            <label className="label-ref">Relationship type</label>
            <input className="input mt-1 w-full"
                   list="rel-presets"
                   value={data.relationship_type}
                   onChange={(e) => setData({ ...data, relationship_type: e.target.value })}
                   data-testid="codex-link-rel"/>
            <datalist id="rel-presets">
              {RELATIONSHIP_PRESETS.map((p) => <option key={p} value={p}/>)}
            </datalist>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label-ref">Color</label>
              <div className="flex gap-1 mt-1 flex-wrap">
                {COLOR_PRESETS.map((c) => (
                  <button key={c} onClick={() => setData({ ...data, color: c })}
                          className={`w-6 h-6 rounded-full border-2 ${data.color === c ? "border-gold-bright" : "border-gold/20"}`}
                          style={{ backgroundColor: c }}
                          data-testid={`codex-link-color-${c.replace("#", "")}`}/>
                ))}
                <input type="color" value={data.color}
                       onChange={(e) => setData({ ...data, color: e.target.value })}
                       className="w-6 h-6 cursor-pointer"
                       data-testid="codex-link-color-custom"/>
              </div>
            </div>
            <div>
              <label className="label-ref">
                Weight · {data.weight}/10 ({data.weight <= 3 ? "loose" : data.weight <= 7 ? "tied" : "core"})
              </label>
              <input type="range" min={1} max={10} value={data.weight}
                     onChange={(e) => setData({ ...data, weight: Number(e.target.value) })}
                     className="w-full mt-1"
                     data-testid="codex-link-weight"/>
            </div>
          </div>

          <label className="flex items-center gap-2 text-xs text-parchment cursor-pointer">
            <input type="checkbox" checked={data.bidirectional}
                   onChange={(e) => setData({ ...data, bidirectional: e.target.checked })}
                   data-testid="codex-link-bidirectional"/>
            Bidirectional (same relationship both directions)
          </label>

          <div>
            <label className="label-ref">Notes (optional)</label>
            <textarea className="input mt-1 w-full" rows={2} value={data.notes}
                      onChange={(e) => setData({ ...data, notes: e.target.value })}
                      data-testid="codex-link-notes"/>
          </div>
        </div>

        {err && <div className="text-ember text-xs mt-2" data-testid="codex-link-error">{err}</div>}

        <div className="flex justify-end gap-2 mt-4">
          <button onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
          <button onClick={save} disabled={busy} className="btn btn-primary text-xs"
                  data-testid="codex-link-save">
            {busy ? "Saving…" : "Save link"}
          </button>
        </div>
      </div>
    </div>
  );
}
