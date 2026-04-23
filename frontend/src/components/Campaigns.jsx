import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, Scroll, X, Users, Lock, Globe2 } from "lucide-react";

export default function Campaigns() {
  const [rows, setRows] = useState([]);
  const [sp] = useSearchParams();
  const [showCreate, setShowCreate] = useState(sp.get("create") === "1");
  const [filter, setFilter] = useState("all");

  const load = async () => {
    const { data } = await api.get("/campaigns");
    setRows(data);
  };
  useEffect(() => { load(); }, []);

  const filtered = rows.filter((c) => filter === "all" || c.visibility === filter);

  return (
    <div className="px-8 md:px-12 py-10">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="label-ref mb-2">Hall of Tables</div>
          <h1 className="font-display text-4xl tracking-wide text-parchment">Campaigns</h1>
          <p className="text-mist mt-2 font-body">Browse public tables or host your own.</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary" data-testid="new-campaign-btn">
          <Plus className="w-4 h-4" /> Forge a campaign
        </button>
      </div>

      <div className="mt-6 flex gap-2">
        {["all", "public", "private"].map((k) => (
          <button key={k} onClick={() => setFilter(k)}
                  className={`btn btn-ghost text-xs ${filter === k ? "border-gold/60 text-gold-bright" : ""}`}
                  data-testid={`filter-${k}`}>
            {k.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="divider-sigil my-6" />

      {filtered.length === 0 ? (
        <div className="text-mist italic font-body">No campaigns yet. Be the first to light the hearth.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((c) => (
            <Link key={c.id} to={`/app/campaigns/${c.id}`}
                  className="card-mystic p-5 transition hover:-translate-y-0.5"
                  data-testid={`campaign-${c.id}`}>
              <div className="flex items-center justify-between">
                <span className="label-ref">{c.system}</span>
                <span className="tag">{c.visibility === "public" ? <><Globe2 className="w-3 h-3"/> Public</> : <><Lock className="w-3 h-3"/> Private</>}</span>
              </div>
              <div className="font-display text-xl text-parchment mt-2">{c.name}</div>
              <div className="text-sm text-mist mt-1 line-clamp-2 font-body">{c.description || "—"}</div>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-gold/70 font-ui">{c.power_level}</span>
                <span className="text-xs text-mist font-ui flex items-center gap-1">
                  <Users className="w-3 h-3"/> {c.member_ids?.length || 0}/{c.max_players}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {(c.tags || []).slice(0, 4).map((t, i) => <span key={i} className="tag">{t}</span>)}
              </div>
            </Link>
          ))}
        </div>
      )}

      {showCreate && <CreateModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); load(); }} />}
    </div>
  );
}

function CreateModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    name: "", description: "", system: "BESM 4E",
    tone: "", genre: "", tags: "", experience_level: "Any",
    schedule: "", max_players: 6, visibility: "public", power_level: "Heroic",
  });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const payload = { ...form, tags: form.tags.split(",").map((s) => s.trim()).filter(Boolean), max_players: +form.max_players };
      const { data } = await api.post("/campaigns", payload);
      onCreated();
      nav(`/app/campaigns/${data.id}`);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-void/80 backdrop-blur-sm flex items-start justify-center p-6 overflow-auto" data-testid="create-campaign-modal">
      <div className="card-mystic sigil-ring w-full max-w-2xl p-8 my-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="label-ref">Forge</div>
            <h2 className="font-display text-2xl text-parchment tracking-wide">A new rite</h2>
          </div>
          <button onClick={onClose} className="btn btn-ghost p-2" data-testid="close-create-modal"><X className="w-4 h-4"/></button>
        </div>
        <form onSubmit={submit} className="grid md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="label-ref block mb-1">Campaign name</label>
            <input className="input" value={form.name} required
                   onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="create-name"/>
          </div>
          <div className="md:col-span-2">
            <label className="label-ref block mb-1">Description</label>
            <textarea className="input" value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="create-description"/>
          </div>
          <div>
            <label className="label-ref block mb-1">Tone</label>
            <input className="input" value={form.tone} placeholder="dark, whimsical…"
                   onChange={(e) => setForm({ ...form, tone: e.target.value })} data-testid="create-tone"/>
          </div>
          <div>
            <label className="label-ref block mb-1">Genre</label>
            <input className="input" value={form.genre} placeholder="cyberpunk, shojo…"
                   onChange={(e) => setForm({ ...form, genre: e.target.value })} data-testid="create-genre"/>
          </div>
          <div>
            <label className="label-ref block mb-1">Tags (comma-sep.)</label>
            <input className="input" value={form.tags}
                   onChange={(e) => setForm({ ...form, tags: e.target.value })} data-testid="create-tags"/>
          </div>
          <div>
            <label className="label-ref block mb-1">Experience level</label>
            <select className="select" value={form.experience_level}
                    onChange={(e) => setForm({ ...form, experience_level: e.target.value })} data-testid="create-experience">
              <option>Any</option><option>Newcomer</option><option>Intermediate</option><option>Veteran</option>
            </select>
          </div>
          <div>
            <label className="label-ref block mb-1">Schedule</label>
            <input className="input" value={form.schedule} placeholder="Fri 7pm EST, biweekly"
                   onChange={(e) => setForm({ ...form, schedule: e.target.value })} data-testid="create-schedule"/>
          </div>
          <div>
            <label className="label-ref block mb-1">Power level</label>
            <select className="select" value={form.power_level}
                    onChange={(e) => setForm({ ...form, power_level: e.target.value })} data-testid="create-power">
              <option>Mundane</option><option>Adventurous</option><option>Heroic</option>
              <option>Epic</option><option>Mythic</option>
            </select>
          </div>
          <div>
            <label className="label-ref block mb-1">Max players</label>
            <input className="input" type="number" min={1} max={12} value={form.max_players}
                   onChange={(e) => setForm({ ...form, max_players: e.target.value })} data-testid="create-max"/>
          </div>
          <div>
            <label className="label-ref block mb-1">Visibility</label>
            <select className="select" value={form.visibility}
                    onChange={(e) => setForm({ ...form, visibility: e.target.value })} data-testid="create-visibility">
              <option value="public">Public</option><option value="private">Private</option>
            </select>
          </div>

          {err && <div className="md:col-span-2 text-sm text-ember">{err}</div>}
          <div className="md:col-span-2 flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button disabled={busy} type="submit" className="btn btn-primary" data-testid="create-submit">
              {busy ? "…" : "Forge"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
