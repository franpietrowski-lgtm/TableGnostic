import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import * as Tabs from "@radix-ui/react-tabs";
import { Users, Plus, UserPlus2, ArrowRight, Trash2, Sparkles, Eye, EyeOff, Link as LinkIcon } from "lucide-react";

export default function CampaignDetail() {
  const { id } = useParams();
  const [camp, setCamp] = useState(null);
  const [characters, setCharacters] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [customs, setCustoms] = useState([]);
  const [err, setErr] = useState("");
  const nav = useNavigate();

  const load = async () => {
    try {
      const c = await api.get(`/campaigns/${id}`).then((r) => r.data);
      setCamp(c);
      const [ch, nd, se, cu] = await Promise.all([
        api.get(`/campaigns/${id}/characters`).then(r => r.data),
        api.get(`/campaigns/${id}/nodes`).then(r => r.data),
        api.get(`/campaigns/${id}/sessions`).then(r => r.data),
        c.is_gm ? api.get(`/campaigns/${id}/custom`).then(r => r.data) : [],
      ]);
      setCharacters(ch); setNodes(nd); setSessions(se); setCustoms(cu);
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
  const startSession = async () => {
    const title = prompt("Session title?", `Session ${sessions.length + 1}`);
    if (!title) return;
    const { data } = await api.post("/sessions", { campaign_id: id, title });
    nav(`/app/sessions/${data.id}`);
  };

  return (
    <div className="px-8 md:px-12 py-10">
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
          {camp.is_gm && <button onClick={startSession} className="btn btn-primary" data-testid="start-session-btn">
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
        <Tabs.List className="flex gap-2 border-b border-gold/10 pb-3">
          {[
            ["characters", "Characters"],
            ["knowledge", "Knowledge Web"],
            ["sessions", "Sessions"],
            ...(camp.is_gm ? [["custom", "Custom Rules"]] : []),
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
        <Tabs.Content value="knowledge" className="pt-6">
          <KnowledgeTab camp={camp} nodes={nodes} onRefresh={load} />
        </Tabs.Content>
        <Tabs.Content value="sessions" className="pt-6">
          <SessionsTab camp={camp} sessions={sessions} onStart={startSession} />
        </Tabs.Content>
        {camp.is_gm && (
          <Tabs.Content value="custom" className="pt-6">
            <CustomTab campId={id} customs={customs} onRefresh={load} />
          </Tabs.Content>
        )}
      </Tabs.Root>
    </div>
  );
}

function CharactersTab({ camp, characters, onRefresh }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="h-arcane text-sm">Player Characters</h3>
        <Link to={`/app/campaigns/${camp.id}/characters/new`} className="btn btn-primary text-xs"
              data-testid="new-character-btn">
          <Plus className="w-3 h-3"/> Forge character
        </Link>
      </div>
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

function KnowledgeTab({ camp, nodes, onRefresh }) {
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({ type: "npc", title: "", content: "", tags: "", visibility: "gm_only" });
  const create = async (e) => {
    e.preventDefault();
    await api.post("/nodes", {
      campaign_id: camp.id, type: form.type, title: form.title, content: form.content,
      tags: form.tags.split(",").map(s => s.trim()).filter(Boolean),
      visibility: form.visibility,
    });
    setShowNew(false);
    setForm({ type: "npc", title: "", content: "", tags: "", visibility: "gm_only" });
    onRefresh();
  };
  const reveal = async (n) => {
    if (!window.confirm(`Reveal "${n.title}" to all seated players?`)) return;
    await api.post(`/nodes/${n.id}/reveal`, { user_ids: camp.member_ids });
    onRefresh();
  };
  const remove = async (n) => {
    if (!window.confirm(`Forget "${n.title}"?`)) return;
    await api.delete(`/nodes/${n.id}`);
    onRefresh();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="h-arcane text-sm">Knowledge Web</h3>
        <button onClick={() => setShowNew(true)} className="btn btn-primary text-xs" data-testid="new-node-btn">
          <Plus className="w-3 h-3"/> Weave a node
        </button>
      </div>
      {showNew && (
        <form onSubmit={create} className="card-mystic p-5 mb-4 grid md:grid-cols-2 gap-3" data-testid="new-node-form">
          <select className="select" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
            {["npc","location","item","event","quest","lore","faction","creature"].map((t) => <option key={t}>{t}</option>)}
          </select>
          <input className="input" placeholder="Title" value={form.title} required
                 onChange={(e) => setForm({ ...form, title: e.target.value })}/>
          <textarea className="input md:col-span-2" placeholder="Content (your own prose, lore, secrets…)" value={form.content}
                    onChange={(e) => setForm({ ...form, content: e.target.value })}/>
          <input className="input" placeholder="tags, comma-separated" value={form.tags}
                 onChange={(e) => setForm({ ...form, tags: e.target.value })}/>
          {camp.is_gm && (
            <select className="select" value={form.visibility}
                    onChange={(e) => setForm({ ...form, visibility: e.target.value })}>
              <option value="gm_only">GM only</option>
              <option value="shared">Shared with table</option>
            </select>
          )}
          <div className="md:col-span-2 flex justify-end gap-2">
            <button type="button" onClick={() => setShowNew(false)} className="btn btn-ghost">Cancel</button>
            <button type="submit" className="btn btn-primary">Weave</button>
          </div>
        </form>
      )}
      {nodes.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No threads woven yet.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {nodes.map((n) => (
            <div key={n.id} className="card-mystic p-4" data-testid={`node-${n.id}`}>
              <div className="flex items-center justify-between">
                <span className="tag uppercase">{n.type}</span>
                <span className="text-[10px] text-gold/60 font-ui uppercase tracking-widest flex items-center gap-1">
                  {n.visibility === "gm_only" ? <EyeOff className="w-3 h-3"/> : <Eye className="w-3 h-3"/>}
                  {n.visibility}
                </span>
              </div>
              <div className="font-display text-base text-parchment mt-2">{n.title}</div>
              <div className="text-xs text-mist mt-1 line-clamp-3 whitespace-pre-wrap font-body">{n.content || "—"}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {(n.tags || []).map((t, i) => <span key={i} className="tag">{t}</span>)}
              </div>
              {camp.is_gm && (
                <div className="mt-3 flex gap-2">
                  {n.visibility !== "revealed" && (
                    <button onClick={() => reveal(n)} className="btn btn-ghost text-[11px]" data-testid={`reveal-${n.id}`}>
                      <Eye className="w-3 h-3"/> Reveal
                    </button>
                  )}
                  <button onClick={() => remove(n)} className="btn btn-danger text-[11px]">
                    <Trash2 className="w-3 h-3"/>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SessionsTab({ camp, sessions, onStart }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="h-arcane text-sm">Sessions</h3>
        {camp.is_gm && <button onClick={onStart} className="btn btn-primary text-xs" data-testid="new-session-btn">
          <Plus className="w-3 h-3"/> Start session
        </button>}
      </div>
      {sessions.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No sessions have been run.</div>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => (
            <Link key={s.id} to={`/app/sessions/${s.id}`} className="card-mystic p-4 flex items-center justify-between"
                  data-testid={`session-${s.id}`}>
              <div>
                <div className="font-display text-base text-parchment">{s.title}</div>
                <div className="text-xs text-mist font-ui uppercase tracking-widest">
                  Round {s.round || 0} · {s.status}
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-gold/70"/>
            </Link>
          ))}
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
        <select className="select" value={form.kind}
                onChange={(e) => setForm({ ...form, kind: e.target.value })}>
          <option value="attribute">Attribute</option>
          <option value="defect">Defect</option>
          <option value="skill">Skill</option>
        </select>
        <input className="input" placeholder="Name" value={form.name} required
               onChange={(e) => setForm({ ...form, name: e.target.value })}/>
        <input className="input" type="number" step="0.5" placeholder="Cost per level"
               value={form.cost_per_level} onChange={(e) => setForm({ ...form, cost_per_level: e.target.value })}/>
        <input className="input" placeholder="Category (Greater/Lesser/Serious, or Group tier)" value={form.category}
               onChange={(e) => setForm({ ...form, category: e.target.value })}/>
        <input className="input md:col-span-2" placeholder="Page reference (e.g. Custom · Homebrew 1.2)" value={form.page_ref}
               onChange={(e) => setForm({ ...form, page_ref: e.target.value })}/>
        <textarea className="input md:col-span-2" placeholder="Your description / mechanics notes"
                  value={form.description_note}
                  onChange={(e) => setForm({ ...form, description_note: e.target.value })}/>
        <div className="md:col-span-2 flex justify-end">
          <button className="btn btn-primary" type="submit">Save</button>
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
