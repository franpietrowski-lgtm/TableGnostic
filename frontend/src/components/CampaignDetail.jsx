import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import * as Tabs from "@radix-ui/react-tabs";
import { Users, Plus, UserPlus2, ArrowRight, Trash2, Sparkles, Eye, EyeOff, Link as LinkIcon, Wand2, Shield, Copy, RefreshCw, Check, Save, Network, ListTree, Lightbulb, X, BookOpen, ChevronDown, ChevronRight, ScrollText } from "lucide-react";
import KnowledgeGraph from "./KnowledgeGraph";
import ChannelsPanel from "./ChannelsPanel";
import { useAuth } from "../lib/api";
import { NODE_TYPES, NODE_TEMPLATES, colorForType, labelForType } from "../lib/nodeTemplates";

export default function CampaignDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [camp, setCamp] = useState(null);
  const [characters, setCharacters] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [customs, setCustoms] = useState([]);
  const [edges, setEdges] = useState([]);
  const [err, setErr] = useState("");
  const [showStart, setShowStart] = useState(false);
  const nav = useNavigate();

  const load = async () => {
    try {
      const c = await api.get(`/campaigns/${id}`).then((r) => r.data);
      setCamp(c);
      const [ch, nd, se, cu, ed] = await Promise.all([
        api.get(`/campaigns/${id}/characters`).then(r => r.data),
        api.get(`/campaigns/${id}/nodes`).then(r => r.data),
        api.get(`/campaigns/${id}/sessions`).then(r => r.data),
        c.is_gm ? api.get(`/campaigns/${id}/custom`).then(r => r.data) : [],
        api.get(`/campaigns/${id}/edges`).then(r => r.data).catch(() => []),
      ]);
      setCharacters(ch); setNodes(nd); setSessions(se); setCustoms(cu); setEdges(ed);
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };
  useEffect(() => { load(); }, [id]);

  if (err) return <div className="p-10 text-ember">{err}</div>;
  if (!camp) return <div className="p-10 text-mist">Summoning…</div>;

  const join = async () => { await api.post(`/campaigns/${id}/join`, { message: "" }); load(); };
  const leave = async () => { await api.post(`/campaigns/${id}/leave`); load(); };
  const delCamp = async () => {
    if (!window.confirm("Dissolve this campaign? All threads will be lost.")) return;
    await api.delete(`/campaigns/${id}`); nav("/app/campaigns");
  };
  const startSession = async (title) => {
    if (!title || !title.trim()) return;
    const { data } = await api.post("/sessions", { campaign_id: id, title: title.trim() });
    setShowStart(false);
    nav(`/app/sessions/${data.id}`);
  };

  return (
    <div className="px-8 md:px-12 py-10" data-system={camp.system_id || "besm-4e"}
         data-testid="campaign-root">
      <Link to="/app/campaigns" className="text-xs font-ui uppercase tracking-widest text-gold/70 hover:text-gold-bright"
            data-testid="back-to-campaigns">← Campaigns</Link>
      <div className="mt-4 flex items-start justify-between flex-wrap gap-4">
        <div className="max-w-2xl">
          <div className="label-ref">{camp.system} · {camp.power_level}</div>
          <h1 className="font-display text-4xl tracking-wide text-parchment mt-1">{camp.name}</h1>
          <p className="text-mist mt-3 font-body leading-relaxed">{camp.description || "No description yet."}</p>
          <div className="flex flex-wrap gap-1 mt-3">
            {(camp.tags || []).map((t, i) => <span key={i} className="tag">{t}</span>)}
          </div>
          <div className="mt-4 text-xs font-ui uppercase tracking-widest text-gold/60">
            GM: {camp.gm_name} · {(camp.member_ids || []).length}/{camp.max_players} seated · {camp.schedule || "no schedule"}
          </div>
        </div>
        <div className="flex gap-2">
          {(user?.role === "gm" || user?.role === "admin") && (
            <button onClick={async () => {
              if (!window.confirm(`Clone "${camp.name}" into a new campaign you GM?`)) return;
              try {
                const { data } = await api.post(`/campaigns/${id}/clone`);
                window.location.href = `/app/campaigns/${data.campaign.id}`;
              } catch (e) { alert(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
            }} className="btn btn-ghost" data-testid="clone-campaign-btn"
                title="Fork this campaign into a copy you GM (carries World Codex, Genesis, edges, custom rules, and published characters).">
              <Copy className="w-4 h-4"/> Clone
            </button>
          )}
          {camp.is_gm && <Link to={`/app/campaigns/${id}/genesis`} className="btn" data-testid="genesis-btn">
            <Wand2 className="w-4 h-4"/> Atelier
          </Link>}
          {camp.is_gm && <button onClick={() => setShowStart(true)} className="btn btn-primary" data-testid="start-session-btn">
            <Sparkles className="w-4 h-4"/> Start session
          </button>}
          {!camp.is_gm && !(camp.member_ids || []).includes(camp.current_user_id) && (
            <button onClick={join} className="btn btn-primary" data-testid="join-btn"><UserPlus2 className="w-4 h-4"/> Take a seat</button>
          )}
          {!camp.is_gm && <button onClick={leave} className="btn btn-ghost" data-testid="leave-btn">Leave</button>}
          {camp.is_gm && <button onClick={delCamp} className="btn btn-danger" data-testid="delete-campaign-btn"><Trash2 className="w-4 h-4"/></button>}
        </div>
      </div>

      <div className="divider-sigil my-8" />

      <Tabs.Root defaultValue="characters">
        <Tabs.List className="flex gap-2 border-b border-gold/10 pb-3 flex-wrap">
          {[
            ["characters", "Characters"],
            ["channels", "Channels"],
            ["knowledge", "Knowledge Web"],
            ["sessions", "Sessions"],
            ["primer", "Player Primer"],
            ...(camp.is_gm ? [["custom", "Custom Rules"], ["invite", "Invite & Share"]] : []),
          ].map(([v, l]) => (
            <Tabs.Trigger key={v} value={v}
              className="px-4 py-2 text-xs font-ui tracking-widest uppercase text-mist hover:text-parchment
                         data-[state=active]:text-gold-bright data-[state=active]:border-b data-[state=active]:border-gold"
              data-testid={`tab-${v}`}>
              {l}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <Tabs.Content value="characters" className="pt-6">
          <CharactersTab camp={camp} characters={characters} onRefresh={load} />
        </Tabs.Content>
        <Tabs.Content value="channels" className="pt-6">
          <ChannelsPanel campaign={camp} user={user}/>
        </Tabs.Content>
        <Tabs.Content value="knowledge" className="pt-6">
          <KnowledgeTab camp={camp} nodes={nodes} edges={edges} onRefresh={load} />
        </Tabs.Content>
        <Tabs.Content value="sessions" className="pt-6">
          <SessionsTab camp={camp} sessions={sessions} nodes={nodes}
                       onStart={() => setShowStart(true)} onRefresh={load}/>
        </Tabs.Content>
        <Tabs.Content value="primer" className="pt-6">
          <PrimerTab camp={camp} onRefresh={load} />
        </Tabs.Content>
        {camp.is_gm && (
          <Tabs.Content value="custom" className="pt-6">
            <CustomTab campId={id} customs={customs} onRefresh={load} />
          </Tabs.Content>
        )}
        {camp.is_gm && (
          <Tabs.Content value="invite" className="pt-6">
            <InviteTab camp={camp} onRefresh={load} />
          </Tabs.Content>
        )}
      </Tabs.Root>

      {/* System credit footer — reflects whatever publisher matches camp.system_id.
          Tri-Stat Emporium voice on BESM, generic publisher © on others. */}
      <SystemCredit camp={camp}/>

      {/* Start Session modal */}
      {showStart && camp.is_gm && (
        <StartSessionModal
          defaultTitle={`Session ${sessions.length + 1}`}
          campName={camp.name}
          onClose={() => setShowStart(false)}
          onStart={startSession}
        />
      )}
    </div>
  );
}

function SystemCredit({ camp }) {
  const [sys, setSys] = useState(null);
  useEffect(() => {
    api.get("/systems").then((r) => {
      const all = r.data.systems || [];
      setSys(all.find((s) => s.id === (camp.system_id || "besm-4e")) || all[0]);
    }).catch(() => {});
  }, [camp.system_id]);
  if (!sys) return null;
  const isBesm = sys.id === "besm-4e";
  const year = new Date().getFullYear();
  const copyright = (sys.copyright || "").replaceAll("{YEAR}", year);
  const headline = isBesm ? "Tri-Stat Emporium" : sys.publisher;
  return (
    <div className="mt-10 pt-6 border-t border-gold/10" data-testid="tri-stat-credit">
      <div className="flex flex-col items-center gap-3">
        {sys.logo_url && (
          <img src={sys.logo_url} alt={`${sys.name} logo`}
               data-testid="system-logo"
               className="h-20 md:h-24 w-auto object-contain opacity-95 drop-shadow-lg"
               // The Emporium guidelines REQUIRE that the logo's aspect ratio is
               // preserved and the logo is not otherwise altered.
               style={{ imageRendering: "auto" }} />
        )}
        <div className="font-display tracking-[0.3em] text-gold/70 text-xs uppercase">
          {headline}
        </div>
        <div className="text-[10.5px] text-mist/80 font-ui max-w-2xl text-center leading-relaxed">
          {copyright}
        </div>
        {sys.links && sys.links.length > 0 && (
          <div className="flex gap-3 text-[10px] font-ui uppercase tracking-widest text-gold/60">
            {sys.links.map((href) => (
              <a key={href} href={href} target="_blank" rel="noreferrer" className="hover:text-gold-bright">
                {href.replace(/^https?:\/\//, "")}
              </a>
            ))}
          </div>
        )}
        {!sys.supported && (
          <div className="text-[10px] text-gold/60 italic">
            Mechanics for {sys.name} are scaffolded — reference content coming soon.
          </div>
        )}
        <div className="text-[10px] text-mist/60 italic mt-1">
          Table-Gnostic references rules and page numbers — it does not reproduce
          rulebook prose, lore, or examples. Bring your physical book to the table.
        </div>
      </div>
    </div>
  );
}

function StartSessionModal({ defaultTitle, campName, onClose, onStart }) {
  const [title, setTitle] = useState(defaultTitle);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const submit = async (e) => {
    e.preventDefault();
    if (!title.trim() || busy) return;
    setBusy(true);
    try { await onStart(title); } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-50 bg-void/80 backdrop-blur-sm flex items-start justify-center p-6 overflow-auto"
         data-testid="start-session-modal" role="dialog" aria-modal="true">
      <div className="card-mystic sigil-ring w-full max-w-md p-7 my-20">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="label-ref flex items-center gap-2"><Sparkles className="w-3 h-3"/> Light the hearth</div>
            <h2 className="font-display text-2xl text-parchment tracking-wide mt-1">Start a session</h2>
            <div className="text-[11px] font-ui uppercase tracking-widest text-mist/70 mt-1">{campName}</div>
          </div>
          <button onClick={onClose} className="btn btn-ghost p-2"><X className="w-4 h-4"/></button>
        </div>
        <div className="divider-sigil mb-4"/>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label-ref block mb-1">Session title</label>
            <input className="input" value={title} required autoFocus
                   onChange={(e) => setTitle(e.target.value)}
                   data-testid="start-session-title" placeholder="The Spire's First Bell" />
            <div className="text-[10px] text-mist italic mt-1">
              Players who have taken a seat will be able to join when you open the room.
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button type="submit" disabled={busy} className="btn btn-primary" data-testid="start-session-confirm">
              <Sparkles className="w-4 h-4"/> {busy ? "Lighting…" : "Begin"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CharactersTab({ camp, characters, onRefresh }) {
  const [seeding, setSeeding] = useState(false);
  const [seedErr, setSeedErr] = useState("");
  const isBesm = (camp.system_id || "besm-4e") === "besm-4e";
  const seed = async () => {
    if (!window.confirm("Seed three Adventurous-tier sample PCs from the Evereantha setting?\n\n• Cyma Glasswort — Apocophea (Herbalist)\n• Tarsis Hammergrip — Ferralith (Monk-Smith)\n• Vela Stoneglyph — Lithomorph (Geomantic Sculptor)\n\nThey'll be added as published characters in this campaign.")) return;
    setSeedErr(""); setSeeding(true);
    try {
      await api.post(`/campaigns/${camp.id}/seed/evereantha`);
      onRefresh();
    } catch (e) {
      setSeedErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setSeeding(false); }
  };
  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 className="h-arcane text-sm">Player Characters</h3>
        <div className="flex items-center gap-2">
          {camp.is_gm && isBesm && (
            <button onClick={seed} disabled={seeding} className="btn btn-ghost text-xs"
                    data-testid="seed-evereantha-btn"
                    title="Seed three Adventurous-tier sample PCs from the public Evereantha setting (BESM 4E mechanics).">
              <Sparkles className="w-3 h-3"/> {seeding ? "Seeding…" : "Seed Evereantha samples"}
            </button>
          )}
          <Link to={`/app/campaigns/${camp.id}/characters/new`} className="btn btn-primary text-xs"
                data-testid="new-character-btn">
            <Plus className="w-3 h-3"/> Forge character
          </Link>
        </div>
      </div>
      {seedErr && <div className="text-ember text-[11px] mb-2 font-ui">{seedErr}</div>}
      {characters.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No souls at this table yet.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {characters.map((c) => (
            <Link key={c.id} to={`/app/characters/${c.id}`} className="card-mystic p-5" data-testid={`character-${c.id}`}>
              <div className="label-ref">{c.power_level} · {c.total_points} pts</div>
              <div className="font-display text-lg text-parchment mt-1">{c.name}</div>
              <div className="text-xs text-mist mt-1 italic line-clamp-2">{c.concept || "—"}</div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                {["body", "mind", "soul"].map((s) => (
                  <div key={s} className="border border-gold/15 rounded-sm py-1">
                    <div className="label-ref">{s}</div>
                    <div className="font-display text-lg text-gold">{c.stats[s]}</div>
                  </div>
                ))}
              </div>
              <div className="mt-3 text-[10px] font-ui tracking-widest uppercase text-mist">
                by {c.owner_name} · HP {c.derived?.health_points ?? "?"} · EP {c.derived?.energy_points ?? "?"}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function KnowledgeTab({ camp, nodes, edges, onRefresh }) {
  const [view, setView] = useState("list"); // list | graph
  const [showNew, setShowNew] = useState(false);
  const [filterType, setFilterType] = useState("all");
  const [selectedNode, setSelectedNode] = useState(null);

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
          <button onClick={() => setView(view === "list" ? "graph" : "list")}
                  className="btn btn-ghost text-xs" data-testid="toggle-view-btn">
            {view === "list" ? <><Network className="w-3 h-3"/> Graph view</> : <><ListTree className="w-3 h-3"/> List view</>}
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

      {view === "graph" ? (
        <div>
          <KnowledgeGraph nodes={filtered} edges={edges}
                          selectedId={selectedNode?.id}
                          onSelect={(n) => setSelectedNode(n)}/>
          {selectedNode && (
            <NodeDetail node={selectedNode} camp={camp}
                        onClose={() => setSelectedNode(null)}
                        onSetVisibility={(v) => setVisibility(selectedNode, v)}
                        onRemove={() => { remove(selectedNode); setSelectedNode(null); }}/>
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
            <NodeDetail node={selectedNode} camp={camp}
                        onClose={() => setSelectedNode(null)}
                        onSetVisibility={(v) => setVisibility(selectedNode, v)}
                        onRemove={() => { remove(selectedNode); setSelectedNode(null); }}/>
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

function SessionsTab({ camp, sessions, nodes, onStart, onRefresh }) {
  const journalNodes = nodes.filter((n) => n.type === "player_journal");
  const recordNodes = nodes.filter((n) => n.type === "session_record");
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="min-w-0">
          <h3 className="h-arcane text-sm">Sessions</h3>
          <div className="text-[11px] text-mist font-body italic mt-1">
            Live tables · player journals · GM recaps · finalize the chronicle when the dust settles.
          </div>
        </div>
        {camp.is_gm && <button onClick={onStart} className="btn btn-primary text-xs" data-testid="new-session-btn">
          <Plus className="w-3 h-3"/> Start session
        </button>}
      </div>
      <div className="divider-sigil my-3"/>

      {sessions.length === 0 && journalNodes.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No sessions have been run.</div>
      ) : (
        <div className="space-y-4">
          {sessions.map((s) => (
            <SessionRow key={s.id} session={s} camp={camp}
                        recordNodes={recordNodes.filter((r) => r.fields?.session_id === s.id)}
                        journalNodes={journalNodes.filter((j) => j.fields?.session_id === s.id)}
                        onRefresh={onRefresh}/>
          ))}
          {/* Orphan player journals — entered without an active session id. */}
          {(() => {
            const orphans = journalNodes.filter((j) => !sessions.find((s) => s.id === j.fields?.session_id));
            if (!orphans.length || !camp.is_gm) return null;
            return (
              <div className="card-mystic p-4 border-arcane/30" data-testid="session-orphan-journals">
                <div className="label-ref">Orphaned player journals</div>
                <div className="text-[11px] text-mist mt-1 font-body italic">
                  Entries written without an open session. The GM can review and re-link them.
                </div>
                <div className="mt-3 space-y-2">
                  {orphans.map((j) => (
                    <JournalRow key={j.id} j={j} onRefresh={onRefresh}/>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}


function SessionRow({ session, camp, recordNodes, journalNodes, onRefresh }) {
  const [open, setOpen] = useState(false);
  const [tone, setTone] = useState("lyrical");
  const [busy, setBusy] = useState(false);
  // The newest recap node for the session; finalisation rewrites it in place.
  const recap = (recordNodes || []).slice().sort((a, b) =>
    (b.created_at || "").localeCompare(a.created_at || ""))[0];
  const finalized = !!(recap?.fields?.is_finalized);

  const finalize = async () => {
    if (!recap) {
      alert("Generate a recap inside the live SessionView first — that's the spine the chronicle is woven onto.");
      return;
    }
    if (!journalNodes.length) {
      if (!window.confirm("No player journals are linked to this session. Weave the chronicle from the recap alone?")) return;
    }
    setBusy(true);
    try {
      await api.post(`/sessions/${session.id}/finalize`, {
        recap_node_id: recap.id,
        journal_node_ids: journalNodes.map((j) => j.id),
        tone,
      });
      onRefresh();
    } catch (e) {
      alert(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="card-mystic p-4" data-testid={`sessionrow-${session.id}`}>
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <Link to={`/app/sessions/${session.id}`} className="min-w-0">
          <div className="font-display text-lg text-parchment hover:text-gold-bright transition">
            {session.title}
          </div>
          <div className="text-[10px] text-mist font-ui uppercase tracking-widest mt-1">
            Round {session.round || 0} · {session.status}
            {finalized && <span className="ml-2 text-gold-bright">· chronicle finalised</span>}
          </div>
        </Link>
        <div className="flex items-center gap-2">
          <span className="tag uppercase border-arcane/40 text-arcane-light">
            {journalNodes.length} journal{journalNodes.length === 1 ? "" : "s"}
          </span>
          <span className={`tag uppercase ${recap ? "border-gold/60 text-gold-bright" : "border-mist/30 text-mist/60"}`}>
            {recap ? "recap ready" : "no recap"}
          </span>
          <button onClick={() => setOpen(!open)} className="btn btn-ghost text-xs"
                  data-testid={`sessionrow-toggle-${session.id}`}>
            {open ? <ChevronDown className="w-3 h-3"/> : <ChevronRight className="w-3 h-3"/>}
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-3 pt-3 border-t border-gold/10 space-y-3">
          {recap ? (
            <div data-testid={`sessionrow-recap-${session.id}`}>
              <div className="label-ref text-[10px] mb-1">
                {finalized ? "Finalised chronicle" : "GM recap (the spine)"}
              </div>
              <div className="text-sm text-parchment/95 whitespace-pre-wrap font-body leading-relaxed">
                {recap.content}
              </div>
            </div>
          ) : (
            <div className="text-[12px] text-mist italic font-body">
              No recap node yet — open the live SessionView and click "Generate Recap" to add one.
            </div>
          )}

          {journalNodes.length > 0 && (
            <div data-testid={`sessionrow-journals-${session.id}`}>
              <div className="label-ref text-[10px] mb-1">Player journals (colour + voice)</div>
              <div className="space-y-2">
                {journalNodes.map((j) => <JournalRow key={j.id} j={j} onRefresh={onRefresh}/>)}
              </div>
            </div>
          )}

          {camp.is_gm && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gold/10"
                 data-testid={`sessionrow-finalize-${session.id}`}>
              <div className="label-ref text-[10px]">Tone</div>
              <select className="select w-auto text-xs" value={tone}
                      onChange={(e) => setTone(e.target.value)}>
                <option value="lyrical">Lyrical (default)</option>
                <option value="terse">Terse / journal style</option>
                <option value="in-character">In-character campfire</option>
              </select>
              <button onClick={finalize} disabled={busy || !recap}
                      className="btn btn-primary text-xs"
                      data-testid={`sessionrow-finalize-btn-${session.id}`}
                      title="Weave recap + linked journals into the definitive chronicle.">
                <ScrollText className="w-3 h-3"/>
                {busy ? "Weaving…" : finalized ? "Re-weave chronicle" : "Finalize chronicle"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function JournalRow({ j, onRefresh }) {
  const [open, setOpen] = useState(false);
  const cname = j.fields?.character_name || "?";
  const when = (j.created_at || "").replace("T", " ").slice(0, 16);
  return (
    <div className="border border-arcane/25 bg-arcane/5 rounded-sm p-2"
         data-testid={`journal-${j.id}`}>
      <button type="button" onClick={() => setOpen(!open)}
              className="w-full text-left flex items-center justify-between gap-2">
        <div className="min-w-0 truncate">
          <span className="text-arcane-light font-ui text-[11px] uppercase tracking-widest mr-2">
            {cname}
          </span>
          <span className="text-mist/70 text-xs">{when}</span>
        </div>
        {open ? <ChevronDown className="w-3 h-3 text-arcane-light"/> : <ChevronRight className="w-3 h-3 text-arcane-light"/>}
      </button>
      {open && (
        <div className="mt-2 pt-2 border-t border-arcane/15 text-sm text-parchment/95 whitespace-pre-wrap font-body leading-relaxed">
          {j.content}
        </div>
      )}
    </div>
  );
}

function CustomTab({ campId, customs, onRefresh }) {
  const [form, setForm] = useState({
    kind: "attribute", name: "", cost_per_level: 1, category: "", page_ref: "Custom", description_note: "",
  });
  const save = async (e) => {
    e.preventDefault();
    await api.post(`/campaigns/${campId}/custom`, { ...form, campaign_id: campId, cost_per_level: +form.cost_per_level });
    setForm({ kind: "attribute", name: "", cost_per_level: 1, category: "", page_ref: "Custom", description_note: "" });
    onRefresh();
  };
  const del = async (cid) => { await api.delete(`/campaigns/${campId}/custom/${cid}`); onRefresh(); };

  return (
    <div>
      <div className="label-ref mb-3">Custom rules (GM-authored)</div>
      <p className="text-xs text-mist mb-4 font-body">
        Create your own Attributes, Defects, or Skills for this campaign. Players can select them in the character forge.
        Your prose stays in your campaign — it is never reproduced elsewhere.
      </p>

      <form onSubmit={save} className="card-mystic p-5 mb-6 grid md:grid-cols-2 gap-3" data-testid="custom-form">
        <select className="select" value={form.kind} data-testid="rule-kind"
                onChange={(e) => setForm({ ...form, kind: e.target.value })}>
          <option value="attribute">Attribute</option>
          <option value="defect">Defect</option>
          <option value="skill">Skill</option>
        </select>
        <input className="input" placeholder="Name" value={form.name} required data-testid="rule-name"
               onChange={(e) => setForm({ ...form, name: e.target.value })}/>
        <input className="input" type="number" step="0.5" placeholder="Cost per level" data-testid="rule-cost"
               value={form.cost_per_level} onChange={(e) => setForm({ ...form, cost_per_level: e.target.value })}/>
        <input className="input" placeholder="Category (Greater/Lesser/Serious, or Group tier)" data-testid="rule-category"
               value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/>
        <input className="input md:col-span-2" placeholder="Page reference (e.g. Custom · Homebrew 1.2)"
               value={form.page_ref} data-testid="rule-pageref"
               onChange={(e) => setForm({ ...form, page_ref: e.target.value })}/>
        <textarea className="input md:col-span-2" placeholder="Your description / mechanics notes"
                  value={form.description_note} data-testid="rule-description"
                  onChange={(e) => setForm({ ...form, description_note: e.target.value })}/>
        <div className="md:col-span-2 flex justify-end">
          <button className="btn btn-primary" type="submit" data-testid="rule-submit">Save</button>
        </div>
      </form>

      {customs.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No custom rules yet.</div>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {customs.map((c) => (
            <div key={c.id} className="card-mystic p-4" data-testid={`custom-${c.id}`}>
              <div className="flex items-center justify-between">
                <span className="tag">{c.kind}</span>
                <button onClick={() => del(c.id)} className="text-ember/70 hover:text-ember"><Trash2 className="w-3 h-3"/></button>
              </div>
              <div className="font-display text-base text-parchment mt-2">{c.name}</div>
              <div className="text-xs text-gold/70 font-ui mt-1">{c.cost_per_level} pts/level · {c.category || "—"}</div>
              <div className="text-[10px] text-mist uppercase tracking-widest mt-1">{c.page_ref}</div>
              {c.description_note && <div className="text-xs text-mist mt-2 whitespace-pre-wrap font-body">{c.description_note}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PrimerTab({ camp, onRefresh }) {
  const [primer, setPrimer] = useState(camp.player_primer || "");
  const [allowedA, setAllowedA] = useState((camp.allowed_attributes || []).join(", "));
  const [prohibA, setProhibA] = useState((camp.prohibited_attributes || []).join(", "));
  const [allowedD, setAllowedD] = useState((camp.allowed_defects || []).join(", "));
  const [prohibD, setProhibD] = useState((camp.prohibited_defects || []).join(", "));
  const [allowedS, setAllowedS] = useState((camp.allowed_skill_groups || []).join(", "));
  const [prohibS, setProhibS] = useState((camp.prohibited_skill_groups || []).join(", "));
  const [pointMin, setPointMin] = useState(camp.character_point_min || 0);
  const [pointMax, setPointMax] = useState(camp.character_point_max || 0);
  const [maxAttrRank, setMaxAttrRank] = useState(camp.max_per_attribute_rank || 0);
  // V3.5/V3.6 — Campaign Benchmarks
  const [genre, setGenre] = useState(camp.genre || "");
  const [timePeriod, setTimePeriod] = useState(camp.time_period || "");
  const [defaultSize, setDefaultSize] = useState(camp.default_character_size || "Medium");
  const [damageRating, setDamageRating] = useState(camp.damage_rating_baseline || 5);
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState("");
  const parse = (s) => s.split(",").map((x) => x.trim()).filter(Boolean);

  const save = async () => {
    setErr(""); setSaved(false);
    try {
      const payload = { ...camp,
        player_primer: primer,
        allowed_attributes: parse(allowedA),
        prohibited_attributes: parse(prohibA),
        allowed_defects: parse(allowedD),
        prohibited_defects: parse(prohibD),
        allowed_skill_groups: parse(allowedS),
        prohibited_skill_groups: parse(prohibS),
        character_point_min: parseInt(pointMin) || 0,
        character_point_max: parseInt(pointMax) || 0,
        max_per_attribute_rank: parseInt(maxAttrRank) || 0,
        genre, time_period: timePeriod,
        default_character_size: defaultSize,
        damage_rating_baseline: parseInt(damageRating) || 5,
      };
      delete payload.is_gm; delete payload.members; delete payload.id;
      delete payload.gm_id; delete payload.gm_name; delete payload.member_ids;
      delete payload.invite_token; delete payload.created_at;
      await api.put(`/campaigns/${camp.id}`, payload);
      setSaved(true); setTimeout(() => setSaved(false), 1800);
      onRefresh();
    } catch (e) { setErr(e.response?.data?.detail || e.message); }
  };

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <div className="label-ref">Player Primer</div>
          <h3 className="h-arcane text-sm mt-1">What players need to know before they forge a character</h3>
        </div>
        {camp.is_gm && (
          <button onClick={save} className="btn btn-primary" data-testid="primer-save-btn">
            <Save className="w-4 h-4"/> {saved ? "Saved" : "Save"}
          </button>
        )}
      </div>
      <p className="text-xs text-mist font-body mt-2 italic">
        Visible to all seated players. Use it to establish the setting, the tone, what's allowed,
        what's off the table, and what the table expects from each character's arc.
      </p>
      <div className="divider-sigil my-4"/>

      {camp.is_gm ? (
        <textarea className="input min-h-[220px] font-body" placeholder="Welcome to the campaign. In this world…"
                  value={primer} onChange={(e) => setPrimer(e.target.value)} data-testid="primer-input"/>
      ) : (
        <div className="card-mystic p-5 whitespace-pre-wrap text-parchment/90 font-body leading-relaxed" data-testid="primer-readonly">
          {camp.player_primer || <span className="text-mist italic">The Game Master hasn't written a primer yet.</span>}
        </div>
      )}

      {camp.is_gm && (
        <>
          <div className="divider-sigil my-6"/>
          <div className="label-ref mb-2 flex items-center gap-2">Campaign Benchmarks <Shield className="w-3 h-3"/></div>
          <p className="text-xs text-mist font-body mb-4 italic">
            Set the table's tone, era, and scale. These flow into the Character Builder
            (display badges + later: filtering), the Live Session (token sizing),
            and the Damage Rating engine (Damage Multiplier baseline).
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3" data-testid="primer-benchmarks">
            <div>
              <label className="label-ref block mb-1">Genre</label>
              <input className="input" list="dl-genres" value={genre}
                     onChange={(e) => setGenre(e.target.value)}
                     placeholder="High Fantasy"
                     data-testid="primer-genre"/>
              <datalist id="dl-genres">
                {["High Fantasy","Low Fantasy","Sword & Sorcery","Cosmic Horror","Modern Horror","Cyberpunk","Steampunk","Space Opera","Hard Sci-Fi","Post-Apocalyptic","Mecha","Mythic Fantasy","Pulp Adventure","Noir","Anime","Slice of Life"].map((g) => <option key={g} value={g}/>)}
              </datalist>
            </div>
            <div>
              <label className="label-ref block mb-1">Time Period</label>
              <select className="select" value={timePeriod}
                      onChange={(e) => setTimePeriod(e.target.value)}
                      data-testid="primer-period">
                <option value="">— unset —</option>
                {["Stone Age","Bronze Age","Iron Age","Classical","Medieval","Renaissance","Industrial","Victorian","Modern","Near Future","Far Future","Post-Apocalyptic","Mixed / Anachronistic"].map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="label-ref block mb-1">Default Character Size</label>
              <select className="select" value={defaultSize}
                      onChange={(e) => setDefaultSize(e.target.value)}
                      data-testid="primer-size">
                {[["Diminutive","Diminutive — sprite / fairy / pixie"],
                  ["Small","Small — halfling / goblin / housecat"],
                  ["Medium","Medium — standard humanoid (default)"],
                  ["Large","Large — ogre / horse / war-bear"],
                  ["Huge","Huge — giant / wagon / small mecha"],
                  ["Gargantuan","Gargantuan — dragon / mecha / siege engine"],
                  ["Massive","Massive — kaiju / capital ship / fortress"]].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
              </select>
              <div className="text-[10px] text-mist/70 italic mt-1">
                Per-entity template; players can override on their sheet.
              </div>
            </div>
            <div>
              <label className="label-ref block mb-1">Damage Rating</label>
              <input className="input" type="number" min={1} max={20}
                     value={damageRating}
                     onChange={(e) => setDamageRating(e.target.value)}
                     data-testid="primer-dr"/>
              <div className="text-[10px] text-mist/70 italic mt-1">
                Baseline 5 (BESM default) · grittier = lower · cinematic = higher
              </div>
            </div>
          </div>

          <div className="divider-sigil my-6"/>
          <div className="label-ref mb-2 flex items-center gap-2">Character-Point Caps <Shield className="w-3 h-3"/></div>
          <p className="text-xs text-mist font-body mb-4 italic">
            Override the Power Level's default budget for this table. Useful for session-0 starts
            ("Heroic, but begin at 90") or floor enforcement ("nobody under 70"). Set to <b>0</b> to
            inherit the Power Level's default.
          </p>
          <div className="grid md:grid-cols-3 gap-3" data-testid="primer-caps">
            <div>
              <label className="label-ref block mb-1">Min Character Points</label>
              <input className="input" type="number" min={0} value={pointMin}
                     onChange={(e) => setPointMin(e.target.value)}
                     data-testid="primer-cap-min"/>
              <div className="text-[10px] text-mist/70 italic mt-1">0 = no floor</div>
            </div>
            <div>
              <label className="label-ref block mb-1">Max Character Points</label>
              <input className="input" type="number" min={0} value={pointMax}
                     onChange={(e) => setPointMax(e.target.value)}
                     data-testid="primer-cap-max"/>
              <div className="text-[10px] text-mist/70 italic mt-1">0 = use Power Level default</div>
            </div>
            <div>
              <label className="label-ref block mb-1">Max Level per Attribute</label>
              <input className="input" type="number" min={0} value={maxAttrRank}
                     onChange={(e) => setMaxAttrRank(e.target.value)}
                     data-testid="primer-cap-attr-rank"/>
              <div className="text-[10px] text-mist/70 italic mt-1">0 = no per-Attribute cap</div>
            </div>
          </div>

          <div className="divider-sigil my-6"/>
          <div className="label-ref mb-2 flex items-center gap-2">Allow / Prohibit Lists <Shield className="w-3 h-3"/></div>
          <p className="text-xs text-mist font-body mb-4 italic">
            Leave <b>Allowed</b> empty to permit everything, or list names to restrict the character forge
            to only those entries. <b>Prohibited</b> items are always hidden from the player picker.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <ListField label="Allowed Attributes" value={allowedA} setValue={setAllowedA} testid="allowed-attrs"
                       hint="e.g. Attack Mastery, Combat Technique, Flight, Heightened Senses"/>
            <ListField label="Prohibited Attributes" value={prohibA} setValue={setProhibA} testid="prohibited-attrs"
                       hint="e.g. Mind Control, Dynamic Powers"/>
            <ListField label="Allowed Defects" value={allowedD} setValue={setAllowedD} testid="allowed-defects"
                       hint="Narrow to flaws that fit the setting"/>
            <ListField label="Prohibited Defects" value={prohibD} setValue={setProhibD} testid="prohibited-defects"
                       hint="e.g. Awkward Size, Vulnerability"/>
            <ListField label="Allowed Skill Groups" value={allowedS} setValue={setAllowedS} testid="allowed-skills"/>
            <ListField label="Prohibited Skill Groups" value={prohibS} setValue={setProhibS} testid="prohibited-skills"/>
          </div>
          {err && <div className="mt-3 text-ember text-sm">{err}</div>}
        </>
      )}
    </div>
  );
}

function ListField({ label, value, setValue, testid, hint }) {
  return (
    <div>
      <label className="label-ref block mb-1">{label}</label>
      <input className="input" placeholder="comma-separated names"
             value={value} onChange={(e) => setValue(e.target.value)} data-testid={testid}/>
      {hint && <div className="text-[10px] text-mist/70 italic mt-1">{hint}</div>}
    </div>
  );
}

function InviteTab({ camp, onRefresh }) {
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const inviteUrl = `${window.location.origin}/invite/${camp.invite_token}`;
  const copy = async () => {
    try { await navigator.clipboard.writeText(inviteUrl); setCopied(true); setTimeout(() => setCopied(false), 1500); }
    catch { alert("Copy failed. Long-press the link to copy manually."); }
  };
  const regen = async () => {
    if (!window.confirm("Revoke the old link and issue a new one?")) return;
    setBusy(true);
    try { await api.post(`/campaigns/${camp.id}/regenerate-invite`); onRefresh(); }
    finally { setBusy(false); }
  };

  return (
    <div className="max-w-2xl">
      <div className="label-ref">Invite & Share</div>
      <h3 className="h-arcane text-sm mt-1">A direct path to the table</h3>
      <p className="text-xs text-mist font-body mt-2 italic">
        Share this link by DM, Discord, or email. Anyone who opens it will see a summary of the campaign
        and — if signed in — can claim a seat instantly.
      </p>

      <div className="card-mystic p-5 mt-6" data-testid="invite-card">
        <div className="label-ref mb-2">Invite link</div>
        <div className="flex items-center gap-2">
          <input className="input font-mono text-[11px]" readOnly value={inviteUrl} data-testid="invite-url"/>
          <button onClick={copy} className="btn" data-testid="invite-copy-btn">
            {copied ? <Check className="w-4 h-4 text-gold-bright"/> : <Copy className="w-4 h-4"/>}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
        <div className="mt-4 flex gap-2">
          <button onClick={regen} disabled={busy} className="btn btn-danger text-xs" data-testid="invite-regen-btn">
            <RefreshCw className="w-3 h-3"/> Revoke & regenerate
          </button>
        </div>
        <div className="mt-4 text-[10px] font-ui uppercase tracking-widest text-mist/70">
          {camp.visibility === "public"
            ? "Public campaign — also discoverable in the Seekers' Hall."
            : "Private campaign — only this link grants a seat."}
        </div>
      </div>
    </div>
  );
}

