/**
 * AtelierWorkshop — V6.19
 *
 * Atelier sub-page where the GM curates two table-delight tools:
 *   - GM Surprise Bag: weighted-random draws (complication / boon / twist
 *     / mood), tagged with system + use-count limits.
 *   - Scene-Break Cards: ritual cards the GM reads aloud at scene
 *     transitions (transition / cliffhanger / cooldown / arrival).
 *
 * Both have:
 *   - List view with edit/delete
 *   - "Add custom entry" form (the user-requested workshop seed section)
 *   - "Seed defaults" one-shot button (idempotent)
 *   - "Draw" button — random pull surfaces in a card-flip modal
 *
 * GM only. Mounted via the Atelier router as `/app/atelier/workshop`.
 */
import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, Trash2, Shuffle, X, Sparkles, BookOpen } from "lucide-react";

const SYSTEM_OPTIONS = ["", "besm-4e", "anime-5e", "dnd-5e", "cypher"];
const SURPRISE_CATEGORIES = ["complication", "boon", "twist", "mood"];
const SCENE_MOODS = ["transition", "cliffhanger", "cooldown", "arrival"];

export default function AtelierWorkshop({ campId: campIdProp }) {
  const params = useParams();
  const cid = campIdProp || params.id;
  const [tab, setTab] = useState("surprise-bag");
  return (
    <div className="px-2 py-2"
         data-testid="atelier-workshop">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <div className="label-ref">Atelier · Table Tools</div>
          <h1 className="font-display text-3xl tracking-wide text-parchment mt-1">
            Workshop
          </h1>
        </div>
      </div>
      <p className="text-mist mt-2 font-body text-sm">
        Stage tools for the table — a Surprise Bag of complications &amp; boons,
        plus a deck of Scene-Break Cards. Both are GM-curated, table-tagged,
        and randomisable for in-session draws.
      </p>
      <div className="mt-4 flex gap-1.5">
        <button onClick={() => setTab("surprise-bag")}
                className={`btn ${tab === "surprise-bag" ? "btn-primary" : "btn-ghost"} text-xs`}
                data-testid="tab-surprise-bag">
          🎲 Surprise Bag
        </button>
        <button onClick={() => setTab("scene-breaks")}
                className={`btn ${tab === "scene-breaks" ? "btn-primary" : "btn-ghost"} text-xs`}
                data-testid="tab-scene-breaks">
          🎴 Scene-Break Cards
        </button>
      </div>
      <div className="divider-sigil my-5"/>
      {tab === "surprise-bag" && <SurpriseBagPanel cid={cid}/>}
      {tab === "scene-breaks" && <SceneBreakPanel cid={cid}/>}
    </div>
  );
}

// ─── Surprise Bag panel ─────────────────────────────────────────────────

function SurpriseBagPanel({ cid }) {
  const [entries, setEntries] = useState([]);
  const [filter, setFilter] = useState({ category: "", system_id: "" });
  const [drawn, setDrawn] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/campaigns/${cid}/surprise-bag`);
      setEntries(data.entries || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [cid]);
  useEffect(() => { refresh(); }, [refresh]);

  const seed = async () => {
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${cid}/surprise-bag/seed`);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const draw = async () => {
    setBusy(true); setErr(""); setDrawn(null);
    try {
      const body = {};
      if (filter.category) body.category = filter.category;
      if (filter.system_id) body.system_id = filter.system_id;
      const { data } = await api.post(`/campaigns/${cid}/surprise-bag/draw`, body);
      setDrawn(data.drawn);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const del = async (id) => {
    if (!window.confirm("Remove this entry from the bag?")) return;
    try {
      await api.delete(`/campaigns/${cid}/surprise-bag/${id}`);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  return (
    <div data-testid="surprise-bag-panel">
      <div className="flex flex-wrap gap-2 items-end justify-between">
        <div className="flex gap-2 flex-wrap items-end">
          <div>
            <label className="label-ref">Filter category</label>
            <select className="select mt-1"
                    value={filter.category}
                    onChange={(e) => setFilter({ ...filter, category: e.target.value })}
                    data-testid="surprise-filter-category">
              <option value="">Any</option>
              {SURPRISE_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="label-ref">Filter system</label>
            <select className="select mt-1"
                    value={filter.system_id}
                    onChange={(e) => setFilter({ ...filter, system_id: e.target.value })}
                    data-testid="surprise-filter-system">
              {SYSTEM_OPTIONS.map((s) => <option key={s} value={s}>{s || "Any"}</option>)}
            </select>
          </div>
          <button onClick={draw} disabled={busy || entries.length === 0}
                  className="btn btn-primary text-xs"
                  data-testid="surprise-draw">
            <Shuffle className="w-3 h-3"/> Draw
          </button>
        </div>
        <div className="flex gap-2">
          {entries.length === 0 && (
            <button onClick={seed} disabled={busy}
                    className="btn btn-ghost text-xs"
                    data-testid="surprise-seed">
              <Sparkles className="w-3 h-3"/> Seed defaults (6 entries)
            </button>
          )}
        </div>
      </div>

      {err && <div className="text-ember text-xs mt-2" data-testid="surprise-error">{err}</div>}

      {drawn && (
        <DrawnCard onClose={() => setDrawn(null)} entry={drawn} testid="surprise-drawn"/>
      )}

      <SurpriseEntryForm cid={cid} onCreated={refresh}/>

      <div className="mt-6">
        <div className="label-ref mb-2">Bag contents · {entries.length} entr{entries.length === 1 ? "y" : "ies"}</div>
        {entries.length === 0 ? (
          <div className="text-mist italic text-sm" data-testid="surprise-empty">
            The bag is empty. Add a custom entry above, or seed the defaults.
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-2">
            {entries.map((e) => (
              <div key={e.id} className="card-mystic p-3 flex items-start gap-2"
                   data-testid={`surprise-entry-${e.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2 flex-wrap">
                    <div className="text-sm text-parchment font-ui">{e.title}</div>
                    <div className="flex items-center gap-1 flex-wrap">
                      <span className="tag border-gold/40 text-gold text-[9px]">{e.category}</span>
                      <span className="tag border-mist/40 text-mist text-[9px]">w{e.weight}</span>
                      {e.system_id && <span className="tag border-arcane/40 text-arcane-light text-[9px]">{e.system_id}</span>}
                    </div>
                  </div>
                  {e.blurb && <div className="text-[11px] text-parchment/80 italic mt-1">{e.blurb}</div>}
                  {(e.tags && e.tags.length > 0) && (
                    <div className="text-[10px] text-mist mt-1">
                      {e.tags.map((t) => `#${t}`).join(" ")}
                    </div>
                  )}
                  {e.use_count > 0 && (
                    <div className="text-[10px] text-mist/70 mt-0.5">
                      Drawn {e.use_count}{e.use_count_max ? `/${e.use_count_max}` : ""} times
                      {e.last_drawn_by ? ` · last by ${e.last_drawn_by}` : ""}
                    </div>
                  )}
                </div>
                <button onClick={() => del(e.id)}
                        className="text-mist hover:text-ember"
                        data-testid={`surprise-delete-${e.id}`}>
                  <Trash2 className="w-3.5 h-3.5"/>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SurpriseEntryForm({ cid, onCreated }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({
    title: "", blurb: "", category: "complication", weight: 3,
    tags: "", system_id: "", use_count_max: 0,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const create = async () => {
    if (!data.title.trim()) { setErr("Title required."); return; }
    setBusy(true); setErr("");
    try {
      const body = { ...data,
        tags: data.tags.split(",").map((s) => s.trim()).filter(Boolean) };
      if (!body.system_id) delete body.system_id;
      await api.post(`/campaigns/${cid}/surprise-bag`, body);
      setData({ title: "", blurb: "", category: "complication", weight: 3,
                 tags: "", system_id: "", use_count_max: 0 });
      setOpen(false);
      onCreated && onCreated();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (!open) {
    return (
      <button onClick={() => setOpen(true)}
              className="btn btn-ghost text-xs mt-4"
              data-testid="surprise-add-toggle">
        <Plus className="w-3 h-3"/> Add custom entry
      </button>
    );
  }
  return (
    <div className="card-mystic p-4 mt-4" data-testid="surprise-add-form">
      <div className="flex items-baseline justify-between mb-2">
        <div className="label-ref">Custom surprise · workshop seed</div>
        <button onClick={() => setOpen(false)} className="text-mist hover:text-gold"
                data-testid="surprise-add-close">
          <X className="w-4 h-4"/>
        </button>
      </div>
      <div className="grid sm:grid-cols-2 gap-2">
        <div>
          <label className="label-ref">Title</label>
          <input className="input mt-1 w-full" value={data.title}
                 onChange={(e) => setData({ ...data, title: e.target.value })}
                 placeholder="e.g. Friend's debt collector arrives"
                 data-testid="surprise-input-title"/>
        </div>
        <div>
          <label className="label-ref">Category</label>
          <select className="select mt-1 w-full" value={data.category}
                  onChange={(e) => setData({ ...data, category: e.target.value })}
                  data-testid="surprise-input-category">
            {SURPRISE_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="label-ref">Blurb (read-aloud or GM cue)</label>
          <textarea className="input mt-1 w-full" rows={2}
                    value={data.blurb}
                    onChange={(e) => setData({ ...data, blurb: e.target.value })}
                    placeholder="Short flavour text or GM action."
                    data-testid="surprise-input-blurb"/>
        </div>
        <div>
          <label className="label-ref">Weight (1-10)</label>
          <input type="number" min={1} max={10} className="input mt-1 w-full"
                 value={data.weight}
                 onChange={(e) => setData({ ...data, weight: Number(e.target.value) })}
                 data-testid="surprise-input-weight"/>
        </div>
        <div>
          <label className="label-ref">System tag</label>
          <select className="select mt-1 w-full" value={data.system_id}
                  onChange={(e) => setData({ ...data, system_id: e.target.value })}
                  data-testid="surprise-input-system">
            {SYSTEM_OPTIONS.map((s) => <option key={s} value={s}>{s || "Any system"}</option>)}
          </select>
        </div>
        <div>
          <label className="label-ref">Tags (comma-separated)</label>
          <input className="input mt-1 w-full" value={data.tags}
                 onChange={(e) => setData({ ...data, tags: e.target.value })}
                 placeholder="weather, social, mechanical"
                 data-testid="surprise-input-tags"/>
        </div>
        <div>
          <label className="label-ref">Max draws (0 = unlimited)</label>
          <input type="number" min={0} className="input mt-1 w-full"
                 value={data.use_count_max}
                 onChange={(e) => setData({ ...data, use_count_max: Number(e.target.value) })}
                 data-testid="surprise-input-uses"/>
        </div>
      </div>
      {err && <div className="text-ember text-xs mt-2" data-testid="surprise-form-error">{err}</div>}
      <div className="mt-3 flex justify-end gap-2">
        <button onClick={() => setOpen(false)} className="btn btn-ghost text-xs"
                data-testid="surprise-form-cancel">Cancel</button>
        <button onClick={create} disabled={busy}
                className="btn btn-primary text-xs"
                data-testid="surprise-form-submit">
          {busy ? "Saving…" : "Add to bag"}
        </button>
      </div>
    </div>
  );
}

// ─── Scene-Break Card panel ────────────────────────────────────────────

function SceneBreakPanel({ cid }) {
  const [cards, setCards] = useState([]);
  const [filter, setFilter] = useState("");
  const [drawn, setDrawn] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/campaigns/${cid}/scene-break-cards`);
      setCards(data.cards || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [cid]);
  useEffect(() => { refresh(); }, [refresh]);

  const seed = async () => {
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${cid}/scene-break-cards/seed`);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const draw = async () => {
    setBusy(true); setErr(""); setDrawn(null);
    try {
      const body = filter ? { mood: filter } : {};
      const { data } = await api.post(`/campaigns/${cid}/scene-break-cards/draw`, body);
      setDrawn(data.drawn);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const del = async (id) => {
    if (!window.confirm("Remove this card?")) return;
    try {
      await api.delete(`/campaigns/${cid}/scene-break-cards/${id}`);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  return (
    <div data-testid="scene-break-panel">
      <div className="flex flex-wrap gap-2 items-end justify-between">
        <div className="flex gap-2 flex-wrap items-end">
          <div>
            <label className="label-ref">Filter mood</label>
            <select className="select mt-1" value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    data-testid="scene-filter-mood">
              <option value="">Any mood</option>
              {SCENE_MOODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <button onClick={draw} disabled={busy || cards.length === 0}
                  className="btn btn-primary text-xs"
                  data-testid="scene-draw">
            <Shuffle className="w-3 h-3"/> Draw card
          </button>
        </div>
        {cards.length === 0 && (
          <button onClick={seed} disabled={busy}
                  className="btn btn-ghost text-xs"
                  data-testid="scene-seed">
            <Sparkles className="w-3 h-3"/> Seed defaults (4 cards)
          </button>
        )}
      </div>

      {err && <div className="text-ember text-xs mt-2" data-testid="scene-error">{err}</div>}

      {drawn && (
        <DrawnCard onClose={() => setDrawn(null)} entry={drawn} testid="scene-drawn" mood/>
      )}

      <SceneBreakForm cid={cid} onCreated={refresh}/>

      <div className="mt-6">
        <div className="label-ref mb-2">Deck contents · {cards.length} card{cards.length === 1 ? "" : "s"}</div>
        {cards.length === 0 ? (
          <div className="text-mist italic text-sm" data-testid="scene-empty">
            The deck is empty. Add a custom card above, or seed the defaults.
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-2">
            {cards.map((c) => (
              <div key={c.id} className="card-mystic p-3 flex items-start gap-2"
                   data-testid={`scene-card-${c.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2 flex-wrap">
                    <div className="text-sm text-parchment font-ui">{c.title}</div>
                    <span className="tag border-gold/40 text-gold text-[9px]">{c.mood}</span>
                  </div>
                  {c.body && <div className="text-[11px] text-parchment/80 mt-1">{c.body}</div>}
                  {c.music_cue && (
                    <div className="text-[10px] text-arcane-light mt-1">♪ {c.music_cue}</div>
                  )}
                </div>
                <button onClick={() => del(c.id)}
                        className="text-mist hover:text-ember"
                        data-testid={`scene-delete-${c.id}`}>
                  <Trash2 className="w-3.5 h-3.5"/>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SceneBreakForm({ cid, onCreated }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ title: "", body: "", mood: "transition", music_cue: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const create = async () => {
    if (!data.title.trim()) { setErr("Title required."); return; }
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${cid}/scene-break-cards`, data);
      setData({ title: "", body: "", mood: "transition", music_cue: "" });
      setOpen(false);
      onCreated && onCreated();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };
  if (!open) {
    return (
      <button onClick={() => setOpen(true)}
              className="btn btn-ghost text-xs mt-4"
              data-testid="scene-add-toggle">
        <Plus className="w-3 h-3"/> Add custom card
      </button>
    );
  }
  return (
    <div className="card-mystic p-4 mt-4" data-testid="scene-add-form">
      <div className="flex items-baseline justify-between mb-2">
        <div className="label-ref">Custom scene-break card</div>
        <button onClick={() => setOpen(false)} className="text-mist hover:text-gold">
          <X className="w-4 h-4"/>
        </button>
      </div>
      <div className="grid sm:grid-cols-2 gap-2">
        <div>
          <label className="label-ref">Title</label>
          <input className="input mt-1 w-full" value={data.title}
                 onChange={(e) => setData({ ...data, title: e.target.value })}
                 data-testid="scene-input-title"/>
        </div>
        <div>
          <label className="label-ref">Mood</label>
          <select className="select mt-1 w-full" value={data.mood}
                  onChange={(e) => setData({ ...data, mood: e.target.value })}
                  data-testid="scene-input-mood">
            {SCENE_MOODS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="label-ref">Read-aloud body</label>
          <textarea className="input mt-1 w-full" rows={3}
                    value={data.body}
                    onChange={(e) => setData({ ...data, body: e.target.value })}
                    placeholder="What the GM says aloud or describes."
                    data-testid="scene-input-body"/>
        </div>
        <div className="sm:col-span-2">
          <label className="label-ref">Music cue (optional)</label>
          <input className="input mt-1 w-full" value={data.music_cue}
                 onChange={(e) => setData({ ...data, music_cue: e.target.value })}
                 placeholder="Spotify URI / YouTube link / track name"
                 data-testid="scene-input-music"/>
        </div>
      </div>
      {err && <div className="text-ember text-xs mt-2" data-testid="scene-form-error">{err}</div>}
      <div className="mt-3 flex justify-end gap-2">
        <button onClick={() => setOpen(false)} className="btn btn-ghost text-xs">Cancel</button>
        <button onClick={create} disabled={busy} className="btn btn-primary text-xs"
                data-testid="scene-form-submit">
          {busy ? "Saving…" : "Add to deck"}
        </button>
      </div>
    </div>
  );
}

function DrawnCard({ entry, onClose, testid, mood }) {
  return (
    <div className="fixed inset-0 bg-void/90 backdrop-blur-md z-50 flex items-center justify-center p-4"
         data-testid={testid}
         onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="card-mystic max-w-md w-full p-6 shadow-2xl border-gold/40">
        <div className="flex items-baseline justify-between mb-2 gap-2">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-gold-bright">
              {mood ? `Scene-Break · ${entry.mood}` : `Surprise · ${entry.category}`}
            </div>
            <h2 className="font-display text-2xl text-parchment mt-1">{entry.title}</h2>
          </div>
          <button onClick={onClose} className="text-mist hover:text-gold"
                  data-testid={`${testid}-close`}>
            <X className="w-5 h-5"/>
          </button>
        </div>
        {(entry.blurb || entry.body) && (
          <div className="text-sm text-parchment/90 italic leading-relaxed mt-3"
               data-testid={`${testid}-body`}>
            {entry.blurb || entry.body}
          </div>
        )}
        {entry.music_cue && (
          <div className="text-xs text-arcane-light mt-3 flex items-center gap-1">
            <BookOpen className="w-3 h-3"/> Music cue: {entry.music_cue}
          </div>
        )}
        {(entry.tags && entry.tags.length > 0) && (
          <div className="text-[10px] text-mist mt-3">
            {entry.tags.map((t) => `#${t}`).join(" ")}
          </div>
        )}
      </div>
    </div>
  );
}
