// Extracted from CampaignDetail.jsx in V6.10 refactor sprint.
// Knowledge Web tab: list / graph / chart views over codex nodes plus
// the node detail / editor surface. ~440 lines.
import React, { useEffect, useState } from "react";
import { Plus, Eye, EyeOff, Trash2, Sparkles, Network, ListTree, Lightbulb, X, Save, Check, Link as LinkIcon } from "lucide-react";
import { api, formatApiErrorDetail } from "../../lib/api";
import KnowledgeGraph from "../KnowledgeGraph";
import CodexChartView from "../CodexChartView";
import { NODE_TYPES, NODE_TEMPLATES, colorForType, labelForType } from "../../lib/nodeTemplates";
function KnowledgeTab({ camp, nodes, edges, onRefresh }) {
  const [view, setView] = useState("list"); // list | graph | chart
  const [showNew, setShowNew] = useState(false);
  const [filterType, setFilterType] = useState("all");
  const [selectedNode, setSelectedNode] = useState(null);
  const detailRef = React.useRef(null);

  // When a node is selected (whether from card grid or graph) scroll the
  // full Codex entry into view so GMs/players never wonder where the
  // detail panel went on long boards.
  React.useEffect(() => {
    if (!selectedNode || !detailRef.current) return;
    detailRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [selectedNode?.id]);

  const filtered = filterType === "all" ? nodes : nodes.filter((n) => n.type === filterType);

  const setVisibility = async (n, visibility) => {
    // Bidirectional visibility flip — GM can move a node between gm_only /
    // shared / revealed without forgetting it. "shared" makes it visible
    // to every member of the campaign; "revealed" only to the listed uids
    // (legacy alias — defaults to all members like the existing reveal flow).
    if (visibility === "revealed") {
      await api.post(`/nodes/${n.id}/reveal`, { user_ids: camp.member_ids });
    } else {
      await api.put(`/nodes/${n.id}/visibility`, { visibility });
    }
    onRefresh();
  };
  const remove = async (n) => {
    if (!window.confirm(`Forget "${n.title}"?`)) return;
    await api.delete(`/nodes/${n.id}`);
    onRefresh();
  };
  const linkNodes = async () => {
    const a = window.prompt("From node title (substring):");
    const b = window.prompt("To node title (substring):");
    const label = window.prompt("Relation label?", "related");
    if (!a || !b) return;
    const fromN = nodes.find((n) => n.title.toLowerCase().includes(a.toLowerCase()));
    const toN = nodes.find((n) => n.title.toLowerCase().includes(b.toLowerCase()));
    if (!fromN || !toN) { alert("Node not found."); return; }
    await api.post("/edges", { campaign_id: camp.id, from_node: fromN.id, to_node: toN.id, label: label || "related" });
    onRefresh();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div>
          <h3 className="h-arcane text-sm">World Codex</h3>
          <div className="text-[11px] text-mist font-body italic mt-1">
            Article-driven worldbuilding · NPCs, places, factions, items, lore — all interlinked.
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={() => setView("list")}
                  className={`btn btn-ghost text-xs ${view === "list" ? "ring-1 ring-gold/40" : ""}`}
                  data-testid="codex-view-list-btn">
            <ListTree className="w-3 h-3"/> List
          </button>
          <button onClick={() => setView("graph")}
                  className={`btn btn-ghost text-xs ${view === "graph" ? "ring-1 ring-gold/40" : ""}`}
                  data-testid="codex-view-graph-btn">
            <Network className="w-3 h-3"/> Graph
          </button>
          <button onClick={() => setView("chart")}
                  className={`btn btn-ghost text-xs ${view === "chart" ? "ring-1 ring-gold/40" : ""}`}
                  data-testid="codex-view-chart-btn"
                  title="Worldbuilding chart — biomes flow chart + 5-pillar grid (population, geography, magic, technology, history).">
            <Network className="w-3 h-3"/> Chart
          </button>
          {camp.is_gm && (
            <>
              <button onClick={async () => {
                if (!window.confirm("Reveal EVERY codex entry to all players?")) return;
                await api.post(`/campaigns/${camp.id}/nodes/bulk-visibility`, { visibility: "shared" });
                onRefresh();
              }} className="btn btn-ghost text-xs" data-testid="bulk-reveal-btn"
                title="GM: make every codex entry visible to all players">
                <Eye className="w-3 h-3"/> Reveal all
              </button>
              <button onClick={async () => {
                if (!window.confirm("Hide EVERY codex entry from players (set GM-only)?")) return;
                await api.post(`/campaigns/${camp.id}/nodes/bulk-visibility`, { visibility: "gm_only" });
                onRefresh();
              }} className="btn btn-ghost text-xs" data-testid="bulk-hide-btn"
                title="GM: pull every codex entry back to GM-only">
                <EyeOff className="w-3 h-3"/> Hide all
              </button>
            </>
          )}
          <button onClick={linkNodes} className="btn btn-ghost text-xs" data-testid="link-nodes-btn">
            <LinkIcon className="w-3 h-3"/> Link
          </button>
          <button onClick={() => setShowNew(true)} className="btn btn-primary text-xs" data-testid="new-node-btn">
            <Plus className="w-3 h-3"/> Weave node
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mb-4">
        <button onClick={() => setFilterType("all")}
                className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded-sm border ${filterType === "all" ? "border-gold/60 text-gold-bright" : "border-gold/15 text-mist/70 hover:text-parchment"}`}>
          All ({nodes.length})
        </button>
        {NODE_TYPES.map((t) => {
          const c = nodes.filter((n) => n.type === t.key).length;
          return (
            <button key={t.key} onClick={() => setFilterType(t.key)}
                    className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded-sm border ${filterType === t.key ? "border-gold/60 text-gold-bright" : "border-gold/15 text-mist/70 hover:text-parchment"}`}
                    data-testid={`type-filter-${t.key}`}>
              {t.label} ({c})
            </button>
          );
        })}
      </div>

      {showNew && <NodeEditor camp={camp} onClose={() => setShowNew(false)} onSaved={() => { setShowNew(false); onRefresh(); }}/>}

      {view === "chart" ? (
        <CodexChartView campId={camp.id} isGm={camp.is_gm}/>
      ) : view === "graph" ? (
        <div>
          <KnowledgeGraph nodes={filtered} edges={edges}
                          selectedId={selectedNode?.id}
                          onSelect={(n) => setSelectedNode(n)}/>
          {selectedNode && (
            <div ref={detailRef}>
              <NodeDetail node={selectedNode} camp={camp}
                          onClose={() => setSelectedNode(null)}
                          onSetVisibility={(v) => setVisibility(selectedNode, v)}
                          onRemove={() => { remove(selectedNode); setSelectedNode(null); }}/>
            </div>
          )}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No nodes of this kind yet.</div>
      ) : (
        <div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((n) => <NodeCard key={n.id} n={n} camp={camp}
                                            isSelected={selectedNode?.id === n.id}
                                            onSetVisibility={(v) => setVisibility(n, v)}
                                            onRemove={() => remove(n)}
                                            onClick={() => setSelectedNode(n)}/>)}
          </div>
          {/* Detail panel ALWAYS appears in card-grid mode when a node is selected.
              Previously only rendered in graph mode — cards looked unresponsive. */}
          {selectedNode && (
            <div ref={detailRef}>
              <NodeDetail node={selectedNode} camp={camp}
                          onClose={() => setSelectedNode(null)}
                          onSetVisibility={(v) => setVisibility(selectedNode, v)}
                          onRemove={() => { remove(selectedNode); setSelectedNode(null); }}/>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function NodeCard({ n, camp, isSelected, onSetVisibility, onRemove, onClick }) {
  const visBadge = {
    "gm_only":  { label: "GM-only", cls: "border-ember/40 text-ember", Icon: EyeOff },
    "shared":   { label: "Shared",  cls: "border-arcane/50 text-arcane-light", Icon: Eye },
    "revealed": { label: "Revealed", cls: "border-gold/60 text-gold-bright", Icon: Eye },
  }[n.visibility] || { label: n.visibility, cls: "border-mist/30 text-mist", Icon: Eye };
  const VisIcon = visBadge.Icon;
  return (
    <div className={`card-mystic p-4 cursor-pointer transition-all ${
                     isSelected ? "border-gold ring-1 ring-gold/40" : "hover:border-gold/40"}`}
         onClick={onClick}
         role="button" tabIndex={0}
         onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick(); } }}
         data-testid={`node-${n.id}`}
         aria-label={`Open codex card: ${n.title}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="tag uppercase" style={{ borderColor: colorForType(n.type) + "55", color: colorForType(n.type) }}>
          {labelForType(n.type)}
        </span>
        <span className={`tag uppercase ${visBadge.cls} flex items-center gap-1`}>
          <VisIcon className="w-3 h-3"/>{visBadge.label}
        </span>
      </div>
      <div className="text-left w-full mt-2">
        <div className="font-display text-base text-parchment hover:text-gold-bright transition">
          {n.title}
        </div>
        {n.content && <div className="text-xs text-mist mt-1 line-clamp-2 whitespace-pre-wrap font-body">{n.content}</div>}
      </div>
      {Object.keys(n.fields || {}).length > 0 && (
        <div className="mt-2 text-[10px] text-mist/70 font-ui italic">
          {Object.keys(n.fields).length} structured field{Object.keys(n.fields).length === 1 ? "" : "s"}
        </div>
      )}
      <div className="flex flex-wrap gap-1 mt-2">
        {(n.tags || []).map((t, i) => <span key={i} className="tag">{t}</span>)}
      </div>
      <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60 mt-3 italic">
        Click for full entry
      </div>
      {camp.is_gm && (
        <div className="mt-3 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <select
            className="select text-[11px] w-auto py-1 px-2"
            value={n.visibility}
            onChange={(e) => onSetVisibility(e.target.value)}
            data-testid={`vis-select-${n.id}`}
            title="Change visibility (GM)">
            <option value="gm_only">GM-only</option>
            <option value="shared">Shared</option>
            <option value="revealed">Revealed</option>
          </select>
          <button onClick={onRemove} className="btn btn-danger text-[11px] ml-auto"
                  data-testid={`forget-${n.id}`}>
            <Trash2 className="w-3 h-3"/>
          </button>
        </div>
      )}
    </div>
  );
}

function NodeDetail({ node, camp, onClose, onSetVisibility, onRemove }) {
  const tmpl = NODE_TEMPLATES[node.type];
  const visBadge = {
    "gm_only":  { label: "GM-only", cls: "border-ember/50 text-ember" },
    "shared":   { label: "Shared with players", cls: "border-arcane/50 text-arcane-light" },
    "revealed": { label: "Revealed", cls: "border-gold/60 text-gold-bright" },
  }[node.visibility] || { label: "Unknown", cls: "border-mist/40 text-mist" };
  return (
    <div className="card-mystic p-6 mt-4" data-testid="node-detail">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="tag uppercase" style={{ borderColor: colorForType(node.type) + "55", color: colorForType(node.type) }}>
              {labelForType(node.type)}
            </span>
            <span className={`tag uppercase ${visBadge.cls}`}>{visBadge.label}</span>
            {(node.tags || []).slice(0, 4).map((t) => (
              <span key={t} className="tag border-mist/30 text-mist/70 text-[10px]">#{t}</span>
            ))}
          </div>
          <h3 className="font-display text-3xl text-parchment mt-3 leading-tight">{node.title}</h3>
          {node.author_name && (
            <div className="text-[10px] font-ui uppercase tracking-widest text-gold/50 mt-1">
              authored by {node.author_name}
            </div>
          )}
        </div>
        <button onClick={onClose} className="btn btn-ghost p-2 shrink-0"><X className="w-4 h-4"/></button>
      </div>

      {node.content && (
        <>
          <div className="divider-sigil my-4"/>
          <div className="text-base text-parchment/95 whitespace-pre-wrap font-body leading-relaxed"
               data-testid="node-detail-content">
            {node.content}
          </div>
        </>
      )}

      {tmpl && Object.keys(node.fields || {}).length > 0 && (
        <>
          <div className="divider-sigil my-4"/>
          <div className="grid md:grid-cols-2 gap-4">
            {tmpl.fields.filter((f) => node.fields[f.key]).map((f) => (
              <div key={f.key}>
                <div className="label-ref">{f.label}</div>
                <div className="text-sm text-parchment/90 font-body whitespace-pre-wrap mt-1.5 leading-relaxed">
                  {node.fields[f.key]}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
      {camp.is_gm && (
        <div className="mt-5 pt-4 border-t border-gold/10 flex flex-wrap items-center gap-2"
             data-testid="node-detail-gm-tools">
          <div className="label-ref text-[10px] mr-1">Visibility</div>
          <select
            className="select text-xs w-auto"
            value={node.visibility}
            onChange={(e) => onSetVisibility(e.target.value)}
            data-testid="node-detail-vis-select">
            <option value="gm_only">GM-only</option>
            <option value="shared">Shared with players</option>
            <option value="revealed">Revealed (legacy)</option>
          </select>
          <button onClick={onRemove} className="btn btn-danger text-xs ml-auto"
                  data-testid="node-detail-forget">
            <Trash2 className="w-3 h-3"/> Forget
          </button>
        </div>
      )}
    </div>
  );
}

function NodeEditor({ camp, onClose, onSaved }) {
  const [type, setType] = useState("npc");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [visibility, setVisibility] = useState("gm_only");
  const [revealedTo, setRevealedTo] = useState([]); // user_ids when visibility=='revealed'
  const [fields, setFields] = useState({});
  const tmpl = NODE_TEMPLATES[type];

  const toggleRevealed = (uid) => {
    setRevealedTo((prev) => prev.includes(uid) ? prev.filter((x) => x !== uid) : [...prev, uid]);
  };

  const save = async (e) => {
    e?.preventDefault();
    if (!title.trim()) return;
    await api.post("/nodes", {
      campaign_id: camp.id, type, title, content,
      tags: tags.split(",").map((s) => s.trim()).filter(Boolean),
      visibility,
      revealed_to: visibility === "revealed" ? revealedTo : [],
      fields,
    });
    onSaved();
  };

  return (
    <div className="fixed inset-0 z-50 bg-void/80 backdrop-blur-sm flex items-start justify-center p-6 overflow-auto" data-testid="node-editor">
      <div className="card-mystic sigil-ring w-full max-w-3xl p-7 my-10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="label-ref">Weave</div>
            <h2 className="font-display text-2xl text-parchment tracking-wide">A new article</h2>
          </div>
          <button onClick={onClose} className="btn btn-ghost p-2"><X className="w-4 h-4"/></button>
        </div>

        <div className="grid md:grid-cols-3 gap-2 mb-4">
          {NODE_TYPES.map((t) => (
            <button key={t.key} onClick={() => { setType(t.key); setFields({}); }}
                    className={`text-left p-3 rounded-sm border transition ${type === t.key ? "border-gold/70 bg-gold/5" : "border-gold/15 hover:border-gold/40"}`}
                    data-testid={`pick-type-${t.key}`}>
              <div className="font-ui text-sm text-parchment">{t.label}</div>
              <div className="text-[10px] uppercase tracking-widest text-gold/60 mt-0.5">{t.key}</div>
            </button>
          ))}
        </div>

        {tmpl && (
          <div className="border-l-2 border-gold/40 pl-3 mb-4 text-xs text-mist italic font-body flex items-start gap-2">
            <Lightbulb className="w-3 h-3 text-gold/60 mt-0.5 shrink-0"/>
            {tmpl.intro}
          </div>
        )}

        <form onSubmit={save} className="space-y-3">
          <div className="grid md:grid-cols-2 gap-3">
            <input className="input" placeholder="Title (the name your table will say)" value={title} required
                   onChange={(e) => setTitle(e.target.value)} data-testid="node-title-input"/>
            {camp.is_gm && (
              <select className="select" value={visibility}
                      onChange={(e) => setVisibility(e.target.value)}
                      data-testid="node-visibility">
                <option value="gm_only">GM only — secret</option>
                <option value="shared">All players — visible to the table</option>
                <option value="revealed">Specific players — pick below</option>
              </select>
            )}
          </div>
          {camp.is_gm && visibility === "revealed" && (
            <div className="border border-gold/15 rounded-sm p-3 bg-gold/5" data-testid="reveal-picker">
              <div className="label-ref mb-2">Visible to which players?</div>
              {(camp.members || []).length === 0 ? (
                <div className="text-[11px] text-mist italic">No players seated yet.</div>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {(camp.members || []).map((m) => {
                    const on = revealedTo.includes(m.id);
                    return (
                      <button type="button" key={m.id} onClick={() => toggleRevealed(m.id)}
                              data-testid={`reveal-pick-${m.id}`}
                              className={`text-[11px] px-2 py-1 rounded-sm border transition ${on ? "border-gold/70 bg-gold/10 text-gold-bright" : "border-gold/15 text-mist/80 hover:border-gold/40"}`}>
                        {on ? <Check className="w-3 h-3 inline mr-1"/> : null}
                        {m.name || m.email}
                      </button>
                    );
                  })}
                </div>
              )}
              {revealedTo.length === 0 && (
                <div className="text-[10px] text-ember/80 italic mt-2">
                  Select at least one player, or this node will be hidden from everyone.
                </div>
              )}
            </div>
          )}
          <textarea className="input" placeholder="Description / opening prose"
                    value={content} onChange={(e) => setContent(e.target.value)}/>
          <input className="input" placeholder="tags, comma-separated" value={tags}
                 onChange={(e) => setTags(e.target.value)}/>

          {tmpl && (
            <div className="border-t border-gold/10 pt-4">
              <div className="label-ref mb-3 flex items-center gap-2">Structured fields <Sparkles className="w-3 h-3"/></div>
              <div className="grid md:grid-cols-2 gap-3">
                {tmpl.fields.map((f) => (
                  <div key={f.key} className={f.textarea ? "md:col-span-2" : ""}>
                    <label className="label-ref block mb-1">{f.label}</label>
                    {f.textarea
                      ? <textarea className="input" placeholder={f.placeholder}
                                  value={fields[f.key] || ""}
                                  onChange={(e) => setFields({ ...fields, [f.key]: e.target.value })}
                                  data-testid={`field-${f.key}`}/>
                      : <input className="input" placeholder={f.placeholder}
                               value={fields[f.key] || ""}
                               onChange={(e) => setFields({ ...fields, [f.key]: e.target.value })}
                               data-testid={`field-${f.key}`}/>}
                    {f.prompt && <div className="text-[10px] text-mist/70 italic mt-1">{f.prompt}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button type="submit" className="btn btn-primary" data-testid="node-submit-btn">
              <Save className="w-4 h-4"/> Weave
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


export default KnowledgeTab;
