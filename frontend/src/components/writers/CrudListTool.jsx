/**
 * V6.25.47 — Shared CRUD-list scaffold for the four remaining writer
 * tools (Cultures, Cosmology, POV Bibles, Themes & Motifs).
 *
 * Each tool is a thin wrapper around <CrudListTool /> that supplies:
 *   • api path (e.g. `/writer/cultures`)
 *   • collection key on the GET response (e.g. `cultures`, `entries`)
 *   • per-record field schema (label + multiline + maxLength)
 *   • optional "kind" facet so multi-kind collections (cosmology,
 *     themes) can be grouped in the UI
 *
 * The pattern: GET list → if creating, show inline form → list cards
 * with edit/delete affordances. Same look across all four for cognitive
 * consistency; same idiom as Magic Architect (V6.25.46).
 */
import React, { useEffect, useState } from "react";
import { Plus, Save, X, Trash2 } from "lucide-react";
import { api } from "../../lib/api";

export function CrudListTool({
  campId, basePath, collectionKey, themeAccent, icon: Icon,
  pageTitle, pageBlurb, fields, kinds, kindLabel,
  testidPrefix,
}) {
  const [data, setData] = useState(null);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const refresh = async () => {
    try {
      const r = await api.get(`${basePath}/${campId}`);
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Load failed.");
    }
  };
  useEffect(() => { if (campId) refresh(); }, [campId]);  // eslint-disable-line

  const blankForm = () => {
    const out = {};
    fields.forEach((f) => { out[f.key] = ""; });
    if (kinds) out.kind = kinds[0][0];
    return out;
  };

  const startEdit = (row) => {
    setEditId(row?.id || "new");
    setForm(row ? { ...blankForm(), ...row } : blankForm());
    setErr("");
  };
  const cancel = () => { setEditId(null); setForm({}); setErr(""); };

  const save = async () => {
    // Build PATCH/POST payload — only the model-defined fields.
    const payload = {};
    fields.forEach((f) => { payload[f.key] = form[f.key] || ""; });
    if (kinds) payload.kind = form.kind;
    if (!payload.name?.trim()) { setErr("Name is required."); return; }
    setBusy(true); setErr("");
    try {
      if (editId === "new") {
        await api.post(`${basePath}/${campId}`, payload);
      } else {
        await api.patch(`${basePath}/${campId}/${editId}`, payload);
      }
      cancel();
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Save failed.");
    } finally { setBusy(false); }
  };

  const remove = async (rid) => {
    if (!confirm("Delete this entry?")) return;
    setBusy(true);
    try {
      await api.delete(`${basePath}/${campId}/${rid}`);
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Delete failed.");
    } finally { setBusy(false); }
  };

  if (!data) {
    return <div className="p-6 text-mist italic"
                data-testid={`${testidPrefix}-loading`}>Loading…</div>;
  }
  const rows = data[collectionKey] || [];

  // Group by kind when kinds-facet is enabled.
  const grouped = kinds
    ? kinds.map(([k, label]) => ({ k, label, items: rows.filter((r) => r.kind === k) }))
    : [{ k: null, label: null, items: rows }];

  return (
    <div className="p-4 space-y-3" data-testid={`${testidPrefix}-page`}>
      <div className={`card-mystic p-3 border-${themeAccent}-700/30 flex items-center gap-3`}>
        <Icon className={`w-5 h-5 text-${themeAccent}-300`}/>
        <div className="flex-1">
          <div className={`label-ref text-${themeAccent}-300`}>{pageTitle}</div>
          <div className="text-[11px] text-mist/70 italic">{pageBlurb}</div>
        </div>
        {data.writable && (
          <button type="button" onClick={() => startEdit(null)}
                  className="btn btn-primary text-xs"
                  data-testid={`${testidPrefix}-new`}>
            <Plus className="w-3 h-3"/> New
          </button>
        )}
      </div>

      {editId && (
        <div className={`card-mystic p-4 border-${themeAccent}-500/50 space-y-2`}
             data-testid={`${testidPrefix}-edit-form`}>
          <div className="flex items-center gap-2">
            <Icon className={`w-4 h-4 text-${themeAccent}-300`}/>
            <span className={`label-ref text-${themeAccent}-300 flex-1`}>
              {editId === "new" ? `New entry` : "Editing"}
            </span>
            <button type="button" onClick={cancel} className="btn btn-ghost text-xs p-1">
              <X className="w-3 h-3"/>
            </button>
          </div>
          {kinds && (
            <div>
              <label className="label-ref block mb-1 text-[10px]">{kindLabel || "Kind"}</label>
              <select value={form.kind}
                      onChange={(e) => setForm({ ...form, kind: e.target.value })}
                      className="input text-xs w-full"
                      data-testid={`${testidPrefix}-form-kind`}>
                {kinds.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
          )}
          {fields.map((f) => (
            <div key={f.key}>
              <label className="label-ref block mb-1 text-[10px]">{f.label}</label>
              {f.multiline ? (
                <textarea value={form[f.key] || ""}
                          onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                          placeholder={f.placeholder}
                          maxLength={f.maxLength || 4000}
                          className="input text-xs w-full min-h-[70px]"
                          data-testid={`${testidPrefix}-form-${f.key}`}/>
              ) : (
                <input type="text" value={form[f.key] || ""}
                       onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                       placeholder={f.placeholder}
                       maxLength={f.maxLength || 160}
                       className="input text-xs w-full"
                       data-testid={`${testidPrefix}-form-${f.key}`}/>
              )}
            </div>
          ))}
          {err && <div className="text-[11px] text-rose-300">{err}</div>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={cancel} className="btn btn-ghost text-xs">Cancel</button>
            <button type="button" onClick={save} disabled={busy}
                    className="btn btn-primary text-xs"
                    data-testid={`${testidPrefix}-form-save`}>
              <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      )}

      {grouped.map(({ k, label, items }) => (
        items.length > 0 && (
          <div key={k || "all"}>
            {label && (
              <div className={`label-ref text-${themeAccent}-300 text-[10px] uppercase tracking-widest mb-1 mt-2`}>
                {label} ({items.length})
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {items.map((r) => (
                <div key={r.id}
                     className={`card-mystic p-3 border-${themeAccent}-700/30 hover:border-${themeAccent}-500/60 transition`}
                     data-testid={`${testidPrefix}-row-${r.id}`}>
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex-1">
                      <div className={`label-ref text-${themeAccent}-300`}>{r.name}</div>
                      {r.kind && (
                        <div className="text-[10px] uppercase tracking-widest text-mist/60">{r.kind}</div>
                      )}
                    </div>
                    {data.writable && (
                      <div className="flex gap-1">
                        <button onClick={() => startEdit(r)}
                                className="btn btn-ghost text-[10px] px-1"
                                data-testid={`${testidPrefix}-edit-${r.id}`}>edit</button>
                        <button onClick={() => remove(r.id)}
                                className={`btn btn-ghost text-[10px] px-1 text-rose-300`}
                                data-testid={`${testidPrefix}-delete-${r.id}`}>
                          <Trash2 className="w-3 h-3"/>
                        </button>
                      </div>
                    )}
                  </div>
                  {fields.filter((f) => f.preview !== false).slice(0, 4).map((f) => (
                    r[f.key] ? (
                      <div key={f.key} className="text-[11px] text-mist/80 mb-1 leading-snug">
                        <b className="text-mist/60">{f.label}:</b> <span className="line-clamp-2">{r[f.key]}</span>
                      </div>
                    ) : null
                  ))}
                </div>
              ))}
            </div>
          </div>
        )
      ))}

      {rows.length === 0 && !editId && (
        <div className="text-[12px] text-mist/60 italic text-center py-6"
             data-testid={`${testidPrefix}-empty`}>
          No entries yet. {data.writable ? "Click 'New' to begin." : ""}
        </div>
      )}
    </div>
  );
}
