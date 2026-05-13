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
import { Sparkles, Plus, Trash2, Save, X } from "lucide-react";
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
    if (!confirm("Delete this magic source?")) return;
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
    </div>
  );
}
