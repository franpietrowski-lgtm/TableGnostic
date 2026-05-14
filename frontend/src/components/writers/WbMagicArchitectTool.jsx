/**
 * V6.25.46 — Worldbuilder Magic Architect.
 *
 * A simple CRUD interface for magic sources: define your Primary
 * Sources (e.g. Faces of Aurae / Faces of Mortiscure), their
 * invocation cost, and their side-effects. Each entry can be tagged
 * with an alignment so the character builder + atlas can route
 * effects appropriately.
 *
 * Backend: GET/POST/PATCH/DELETE /api/writer/magic/{cid}
 */
import React, { useEffect, useState } from "react";
import { Sparkles, Plus, Trash2, Save, X, Eye } from "lucide-react";
import { api } from "../../lib/api";

const KIND_OPTIONS = [
  ["primary", "Primary Source"],
  ["channel", "Channel"],
  ["effect",  "Effect"],
];
const ALIGN_OPTIONS = [
  ["aurae",      "Aurae"],
  ["mortiscure", "Mortiscure"],
  ["both",       "Both"],
  ["none",       "Unaligned"],
];

const blankForm = () => ({
  name: "", kind: "primary", alignment: "none",
  summary: "", invocation_cost: "", side_effects: "",
});

export default function WbMagicArchitectTool({ campId }) {
  const [data, setData] = useState(null);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState(blankForm());
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const refresh = async () => {
    try {
      const r = await api.get(`/writer/magic/${campId}`);
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Load failed.");
    }
  };
  useEffect(() => { if (campId) refresh(); }, [campId]);

  const startEdit = (s) => {
    setEditId(s?.id || "new");
    setForm(s ? { ...blankForm(), ...s } : blankForm());
  };
  const cancel = () => { setEditId(null); setForm(blankForm()); setErr(""); };

  const save = async () => {
    if (!form.name.trim()) { setErr("Name is required."); return; }
    setBusy(true); setErr("");
    try {
      if (editId === "new") {
        await api.post(`/writer/magic/${campId}`, form);
      } else {
        await api.patch(`/writer/magic/${campId}/${editId}`, form);
      }
      cancel();
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Save failed.");
    } finally { setBusy(false); }
  };

  const remove = async (sid) => {
    if (!window.confirm("Delete this magic source?")) return;
    setBusy(true);
    try {
      await api.delete(`/writer/magic/${campId}/${sid}`);
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Delete failed.");
    } finally { setBusy(false); }
  };

  if (!data) {
    return <div className="p-6 text-mist italic" data-testid="wb-magic-loading">Channelling…</div>;
  }

  return (
    <div className="p-4 space-y-3" data-testid="wb-magic-architect-page">
      <div className="card-mystic p-3 border-emerald-700/30 flex items-center gap-3">
        <Sparkles className="w-5 h-5 text-emerald-300"/>
        <div className="flex-1">
          <div className="label-ref text-emerald-300">Magic Architect</div>
          <div className="text-[11px] text-mist/70 italic">
            Define Primary Sources, channels, and effects. Source → channel → cost → consequence.
            Aurae & Mortiscure are weighted Primary Sources here, not a pantheon.
          </div>
        </div>
        {data.writable && (
          <button type="button" onClick={() => startEdit(null)}
                  className="btn btn-primary text-xs"
                  data-testid="wb-magic-new">
            <Plus className="w-3 h-3"/> New source
          </button>
        )}
      </div>

      {/* Edit form */}
      {editId && (
        <div className="card-mystic p-4 border-emerald-500/50 space-y-2"
             data-testid="wb-magic-edit-form">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-300"/>
            <span className="label-ref text-emerald-300 flex-1">
              {editId === "new" ? "New magic source" : "Editing"}
            </span>
            <button type="button" onClick={cancel} className="btn btn-ghost text-xs p-1">
              <X className="w-3 h-3"/>
            </button>
          </div>
          <input type="text" value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })}
                 placeholder="Name (e.g. Face of Aurae · Dawnbearer)"
                 className="input text-xs w-full"
                 data-testid="wb-magic-form-name"/>
          <div className="grid grid-cols-2 gap-2">
            <select value={form.kind}
                    onChange={(e) => setForm({ ...form, kind: e.target.value })}
                    className="input text-xs w-full"
                    data-testid="wb-magic-form-kind">
              {KIND_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
            <select value={form.alignment}
                    onChange={(e) => setForm({ ...form, alignment: e.target.value })}
                    className="input text-xs w-full"
                    data-testid="wb-magic-form-alignment">
              {ALIGN_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <textarea value={form.summary || ""}
                    onChange={(e) => setForm({ ...form, summary: e.target.value })}
                    placeholder="Summary — what is this source, who reveres it, what does it tilt?"
                    className="input text-xs w-full min-h-[80px]"
                    data-testid="wb-magic-form-summary"/>
          <textarea value={form.invocation_cost || ""}
                    onChange={(e) => setForm({ ...form, invocation_cost: e.target.value })}
                    placeholder="Invocation cost — per use, per day, per soul?"
                    className="input text-xs w-full min-h-[50px]"
                    data-testid="wb-magic-form-cost"/>
          <textarea value={form.side_effects || ""}
                    onChange={(e) => setForm({ ...form, side_effects: e.target.value })}
                    placeholder="Side effects — what changes in the world after each invocation?"
                    className="input text-xs w-full min-h-[50px]"
                    data-testid="wb-magic-form-side-effects"/>
          {err && <div className="text-[11px] text-rose-300">{err}</div>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={cancel}
                    className="btn btn-ghost text-xs"
                    data-testid="wb-magic-form-cancel">Cancel</button>
            <button type="button" onClick={save} disabled={busy}
                    className="btn btn-primary text-xs"
                    data-testid="wb-magic-form-save">
              <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      )}

      {/* List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {(data.sources || []).map((s) => (
          <div key={s.id}
               className="card-mystic p-3 border-emerald-700/30 hover:border-emerald-500/60 transition"
               data-testid={`wb-magic-row-${s.id}`}>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1">
                <div className="label-ref text-emerald-300">{s.name}</div>
                <div className="text-[10px] uppercase tracking-widest text-mist/60">
                  {s.kind || "primary"} · {s.alignment || "none"}
                </div>
              </div>
              {data.writable && (
                <div className="flex gap-1">
                  <button type="button" onClick={() => startEdit(s)}
                          className="btn btn-ghost text-[10px] px-1"
                          data-testid={`wb-magic-edit-${s.id}`}>edit</button>
                  <button type="button" onClick={() => remove(s.id)}
                          className="btn btn-ghost text-[10px] px-1 text-rose-300"
                          data-testid={`wb-magic-delete-${s.id}`}>
                    <Trash2 className="w-3 h-3"/>
                  </button>
                </div>
              )}
            </div>
            {s.summary && (
              <div className="text-[11px] text-mist mb-2 line-clamp-3 leading-relaxed">{s.summary}</div>
            )}
            {s.invocation_cost && (
              <div className="text-[10px] text-emerald-200/80 italic">
                <b>Cost:</b> {s.invocation_cost}
              </div>
            )}
            {s.side_effects && (
              <div className="text-[10px] text-rose-200/80 italic">
                <b>Side effects:</b> {s.side_effects}
              </div>
            )}
          </div>
        ))}
      </div>
      {(data.sources || []).length === 0 && !editId && (
        <div className="text-[12px] text-mist/60 italic text-center py-6">
          No magic sources defined yet. {data.writable ? "Click 'New source' to begin." : ""}
        </div>
      )}

      {/* V6.25.53 — Evereantha cosmology quick-ref. Hard-seeded
          Faces of Aurae × Mortiscura + opposition matrix. Lazy-load
          so non-Evereantha campaigns don't pay the network cost,
          but always available as a writer aid. */}
      <CosmologyQuickRef/>
    </div>
  );
}

// ─────────────── V6.25.53 — Evereantha cosmology quick-ref ───────────────

function CosmologyQuickRef() {
  const [open, setOpen] = React.useState(false);
  const [data, setData] = React.useState(null);
  const [selectedFace, setSelectedFace] = React.useState(null);

  React.useEffect(() => {
    if (!open || data) return;
    api.get("/cosmology/evereantha")
      .then((r) => setData(r.data))
      .catch(() => setData({ aurae: [], mortiscura: [] }));
  }, [open, data]);

  return (
    <div className="card-mystic p-3 mt-4 border-amber-700/30"
         data-testid="cosmology-quickref">
      <button type="button"
              onClick={() => setOpen((v) => !v)}
              className="w-full flex items-center justify-between gap-3 text-left"
              data-testid="cosmology-quickref-toggle">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-amber-300"/>
          <div>
            <div className="label-ref text-amber-300">Evereantha Cosmology · Quick-Ref</div>
            <div className="text-[10px] text-mist/60 italic">
              Faces of Aurae × Mortiscura — canon for every Evereantha campaign
            </div>
          </div>
        </div>
        <span className="text-[10px] text-mist/70">{open ? "Hide" : "Show"}</span>
      </button>

      {open && data && (
        <div className="mt-3 space-y-3" data-testid="cosmology-quickref-body">
          {/* Selected face detail */}
          {selectedFace && (
            <div className="border border-amber-500/40 bg-amber-900/10 rounded-sm p-3"
                 data-testid="cosmology-face-detail">
              <div className="flex items-center justify-between mb-1">
                <div className="font-display text-amber-200 text-lg">
                  {selectedFace.name} <span className="text-[10px] text-mist/60 uppercase tracking-widest">· {selectedFace.axis}</span>
                </div>
                <button type="button" onClick={() => setSelectedFace(null)}
                        className="text-[10px] text-mist/60 hover:text-parchment"
                        data-testid="cosmology-face-detail-close">close</button>
              </div>
              <div className="text-[11px] text-mist mb-2">{selectedFace.summary}</div>
              <div className="text-[10px] text-amber-200/80 uppercase tracking-widest mb-1">Core: {selectedFace.core_uses}</div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2">
                {(selectedFace.nodes || []).map((n) => (
                  <div key={n.name} className="border border-mist/15 rounded-sm p-2 bg-ink/40 text-[10px]"
                       data-testid={`cosmology-node-${n.name.toLowerCase()}`}>
                    <div className="text-amber-300 font-display">{n.name}</div>
                    <div className="mb-1"><span className="text-[9px] tracking-widest uppercase text-mist/45 mr-1">Domain</span><span className="text-mist/80 italic">{n.domain}</span></div>
                    <div className="mb-0.5"><span className="text-[9px] tracking-widest uppercase text-mist/45 mr-1">Rank 1</span>{n.rank_1}</div>
                    <div className="mb-0.5"><span className="text-[9px] tracking-widest uppercase text-mist/45 mr-1">Rank 3</span>{n.rank_3}</div>
                    <div className="text-rose-300/80"><span className="text-[9px] tracking-widest uppercase text-rose-300/55 mr-1">Failure</span>{n.failure}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Aurae faces grid */}
          <div data-testid="cosmology-aurae-grid">
            <div className="label-ref text-emerald-300 text-[10px] uppercase tracking-widest mb-1">
              Faces of Aurae · creation, expansion, life
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {(data.aurae || []).map((f) => (
                <button type="button"
                        key={f.id}
                        onClick={() => setSelectedFace(f)}
                        className={`text-left p-2 rounded-sm border transition-colors
                                   ${selectedFace?.id === f.id
                                     ? "border-emerald-400 bg-emerald-900/30"
                                     : "border-emerald-700/30 bg-emerald-950/20 hover:border-emerald-500/60"}`}
                        data-testid={`cosmology-aurae-${f.id}`}>
                  <div className="text-emerald-200 font-display text-sm">{f.name}</div>
                  <div className="text-[9px] uppercase tracking-widest text-mist/60">{f.axis}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Mortiscura faces grid */}
          <div data-testid="cosmology-mortiscura-grid">
            <div className="label-ref text-rose-300 text-[10px] uppercase tracking-widest mb-1">
              Faces of Mortiscura · concealment, distortion, negation
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {(data.mortiscura || []).map((f) => (
                <button type="button"
                        key={f.id}
                        onClick={() => setSelectedFace(f)}
                        className={`text-left p-2 rounded-sm border transition-colors
                                   ${selectedFace?.id === f.id
                                     ? "border-rose-400 bg-rose-900/30"
                                     : "border-rose-800/30 bg-rose-950/20 hover:border-rose-500/60"}`}
                        data-testid={`cosmology-mortiscura-${f.id}`}>
                  <div className="text-rose-200 font-display text-sm">{f.name}</div>
                  <div className="text-[9px] uppercase tracking-widest text-mist/60">{f.axis}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Opposition legend */}
          <div className="border-t border-mist/10 pt-2 text-[9px] text-mist/60 uppercase tracking-widest"
               data-testid="cosmology-legend">
            <b className="text-mist/80">Cosmological tension:</b>{" "}
            ADVANTAGE = +1 step / 2d20 take-higher ·{" "}
            EDGE = +d4 ·{" "}
            NEUTRAL = fiction-led ·{" "}
            OBSTACLE = +1 difficulty
          </div>
        </div>
      )}
    </div>
  );
}
