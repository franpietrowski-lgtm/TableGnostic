/**
 * V6.25.46 — Storyteller Manuscript: real markdown editor (replaces scaffold).
 *
 * Three-pane layout:
 *   • Left: chapter / scene / beat tree (collapsible).
 *   • Center: distraction-free markdown editor for the selected section.
 *   • Right: live word-count + status panel.
 *
 * Auto-saves on a 1500ms debounce after typing stops. Manual save
 * button always available. Word-count is computed server-side on
 * every PATCH so the tree-level total stays authoritative.
 *
 * Markdown rendering is left to a future drop — for now the editor
 * is a plain <textarea> with markdown-preview toggle.
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { PenTool, Plus, Trash2, Eye, EyeOff, FileText, X } from "lucide-react";
import { api } from "../../lib/api";

const KIND_INDENT = { chapter: 0, scene: 1, beat: 2 };

export default function StManuscriptTool({ campId }) {
  const [data, setData] = useState(null);
  const [sel, setSel] = useState(null);     // section id or null
  const [body, setBody] = useState("");
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("planned");
  const [preview, setPreview] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const debounceRef = useRef(null);
  const dirtyRef = useRef(false);

  const refresh = async () => {
    try {
      const r = await api.get(`/writer/manuscript/${campId}`);
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load manuscript.");
    }
  };
  useEffect(() => { if (campId) refresh(); }, [campId]);

  // Build a parent→children index then sort by order.
  const tree = useMemo(() => {
    const rows = (data?.sections || []).slice().sort(
      (a, b) => (a.order || 0) - (b.order || 0),
    );
    const byParent = {};
    rows.forEach((r) => {
      const k = r.parent_id || "_root";
      (byParent[k] = byParent[k] || []).push(r);
    });
    const out = [];
    const walk = (parentKey, depth) => {
      (byParent[parentKey] || []).forEach((node) => {
        out.push({ ...node, _depth: depth });
        walk(node.id, depth + 1);
      });
    };
    walk("_root", 0);
    return out;
  }, [data]);

  const selected = useMemo(
    () => (data?.sections || []).find((r) => r.id === sel) || null,
    [data, sel],
  );

  useEffect(() => {
    if (!selected) { setBody(""); setTitle(""); setStatus("planned"); return; }
    setBody(selected.body_md || "");
    setTitle(selected.title || "");
    setStatus(selected.status || "planned");
    dirtyRef.current = false;
  }, [selected?.id]);   // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-save debounce.
  useEffect(() => {
    if (!selected || !data?.writable) return;
    if (!dirtyRef.current) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => save(), 1500);
    return () => debounceRef.current && clearTimeout(debounceRef.current);
  }, [body, title, status]);   // eslint-disable-line react-hooks/exhaustive-deps

  const save = async () => {
    if (!selected) return;
    setBusy(true); setErr("");
    try {
      // V6.25.47 — `kind` is immutable on PATCH; the backend rejects
      // any send that includes it (extra="forbid"). Only mutable
      // fields ride the wire here.
      await api.patch(`/writer/manuscript/${campId}/${selected.id}`, {
        title: title.trim() || "Untitled",
        body_md: body,
        status,
      });
      dirtyRef.current = false;
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Save failed.");
    } finally { setBusy(false); }
  };

  const createSection = async (kind, parent_id) => {
    setBusy(true); setErr("");
    try {
      const defaultTitle = kind === "chapter" ? "New Chapter"
        : kind === "scene" ? "New Scene" : "New Beat";
      const r = await api.post(`/writer/manuscript/${campId}`, {
        kind, parent_id, title: defaultTitle, status: "planned",
      });
      await refresh();
      setSel(r.data?.id || null);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Create failed.");
    } finally { setBusy(false); }
  };

  const deleteSection = async (sid) => {
    if (!confirm("Delete this section and all its children?")) return;
    setBusy(true); setErr("");
    try {
      await api.delete(`/writer/manuscript/${campId}/${sid}`);
      if (sel === sid) setSel(null);
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Delete failed.");
    } finally { setBusy(false); }
  };

  if (!data) {
    return <div className="p-6 text-mist italic" data-testid="st-manuscript-loading">Opening manuscript…</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr_220px] gap-3 p-4"
         data-testid="st-manuscript-page">
      {/* Tree */}
      <div className="card-mystic p-3 border-rose-700/30 max-h-[70vh] overflow-auto"
           data-testid="st-manuscript-tree">
        <div className="flex items-center justify-between mb-2">
          <div className="label-ref text-rose-300 flex items-center gap-1">
            <FileText className="w-3 h-3"/> Manuscript
          </div>
          {data.writable && (
            <button type="button" onClick={() => createSection("chapter", null)}
                    className="btn btn-ghost text-[10px] text-rose-300"
                    data-testid="st-manuscript-new-chapter">
              <Plus className="w-3 h-3"/> Chapter
            </button>
          )}
        </div>
        {tree.length === 0 ? (
          <div className="text-[11px] text-mist/60 italic">
            {data.writable ? "Start with a chapter." : "Empty manuscript."}
          </div>
        ) : tree.map((n) => (
          <div key={n.id} className="flex items-center group gap-1"
               style={{ paddingLeft: `${KIND_INDENT[n.kind] * 12}px` }}>
            <button onClick={() => setSel(n.id)}
                    className={`flex-1 text-left text-[12px] py-0.5 px-1 rounded-sm ${
                      sel === n.id ? "bg-rose-900/30 text-rose-200" : "text-mist hover:bg-rose-900/15"
                    }`}
                    data-testid={`st-manuscript-row-${n.id}`}>
              <span className="text-[9px] uppercase tracking-widest text-mist/50 mr-1">
                {n.kind[0]}
              </span>
              {n.title || "Untitled"}
              {(n.word_count || 0) > 0 && (
                <span className="text-[9px] text-mist/50 ml-1">· {n.word_count}w</span>
              )}
            </button>
            {data.writable && (
              <span className="opacity-0 group-hover:opacity-100 flex gap-0.5">
                {n.kind === "chapter" && (
                  <button onClick={() => createSection("scene", n.id)}
                          className="text-[9px] text-rose-300 px-1"
                          title="Add scene"
                          data-testid={`st-manuscript-new-scene-${n.id}`}>+s</button>
                )}
                {n.kind === "scene" && (
                  <button onClick={() => createSection("beat", n.id)}
                          className="text-[9px] text-rose-300 px-1"
                          title="Add beat"
                          data-testid={`st-manuscript-new-beat-${n.id}`}>+b</button>
                )}
                <button onClick={() => deleteSection(n.id)}
                        className="text-[9px] text-rose-400 px-1"
                        title="Delete"
                        data-testid={`st-manuscript-del-${n.id}`}>
                  <Trash2 className="w-2.5 h-2.5"/>
                </button>
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Editor */}
      <div className="card-mystic p-3 border-rose-700/30 min-h-[70vh] flex flex-col">
        {!selected ? (
          <div className="flex-1 flex items-center justify-center text-mist/60 italic text-sm">
            Select a section on the left to start writing.
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-2">
              <PenTool className="w-4 h-4 text-rose-300"/>
              <input type="text" value={title}
                     onChange={(e) => { setTitle(e.target.value); dirtyRef.current = true; }}
                     disabled={!data.writable}
                     className="bg-transparent text-lg font-display text-parchment flex-1 outline-none border-b border-rose-900/30 pb-1"
                     data-testid="st-manuscript-title-input"/>
              <span className="text-[9px] uppercase tracking-widest text-rose-300/70">{selected.kind}</span>
              <button type="button" onClick={() => setPreview((v) => !v)}
                      className="btn btn-ghost text-[11px]"
                      data-testid="st-manuscript-preview-toggle">
                {preview ? <EyeOff className="w-3 h-3"/> : <Eye className="w-3 h-3"/>}
              </button>
            </div>
            {preview ? (
              <pre className="flex-1 whitespace-pre-wrap text-mist font-body text-sm
                              overflow-auto leading-relaxed"
                   data-testid="st-manuscript-preview">{body || "—"}</pre>
            ) : (
              <textarea value={body}
                        onChange={(e) => { setBody(e.target.value); dirtyRef.current = true; }}
                        disabled={!data.writable}
                        placeholder="Write in markdown — # heading, **bold**, _italic_…"
                        className="flex-1 input font-mono text-sm resize-none min-h-[55vh]"
                        data-testid="st-manuscript-body-textarea"/>
            )}
          </>
        )}
      </div>

      {/* Stats */}
      <div className="card-mystic p-3 border-rose-700/30 space-y-3"
           data-testid="st-manuscript-stats">
        <div>
          <div className="label-ref text-rose-300">Manuscript</div>
          <div className="text-3xl font-display text-parchment mt-1">
            {(data.total_word_count || 0).toLocaleString()}
          </div>
          <div className="text-[10px] uppercase tracking-widest text-mist/60">
            total words
          </div>
        </div>
        {selected && (
          <>
            <div className="border-t border-rose-900/30 pt-2">
              <div className="text-[10px] uppercase tracking-widest text-mist/60">
                This section
              </div>
              <div className="text-xl font-display text-rose-200">
                {(selected.word_count || 0).toLocaleString()} <span className="text-[11px] text-mist/60">words</span>
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-widest text-mist/60 mb-1">
                Status
              </div>
              <select value={status}
                      onChange={(e) => { setStatus(e.target.value); dirtyRef.current = true; }}
                      disabled={!data.writable}
                      className="input text-xs w-full"
                      data-testid="st-manuscript-status-select">
                <option value="planned">Planned</option>
                <option value="drafted">Drafted</option>
                <option value="revised">Revised</option>
                <option value="cut">Cut</option>
              </select>
            </div>
            {data.writable && (
              <button type="button" onClick={save} disabled={busy}
                      className="btn btn-primary text-xs w-full"
                      data-testid="st-manuscript-save">
                {busy ? "Saving…" : (dirtyRef.current ? "Save now" : "Saved")}
              </button>
            )}
          </>
        )}
        {err && (
          <div className="text-[11px] text-rose-300 italic"
               data-testid="st-manuscript-error">{err}</div>
        )}
      </div>
    </div>
  );
}
