/**
 * EncountersLibrary — V6.25.26 (anti-railroad encounter flow)
 *
 * GM-only library where encounters live as first-class artifacts.
 * Authoring is decoupled from session binding — GMs bulk-create and
 * pick from inside a session.
 *
 * Statuses: draft → ready → running → completed | template
 *
 * Usable in two modes:
 *   1. Director's Console (campaign-wide) — full CRUD + clone + bulk auth.
 *   2. Session view (`session_id` prop set) — picker + Run / Complete affordances.
 */
import React, { useEffect, useMemo, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Swords, Plus, Trash2, Copy, Save, X, Play, CheckCircle2, FileEdit, Pencil,
  Bookmark, Filter,
} from "lucide-react";

const ENCOUNTER_TYPES = [
  { key: "combat",      label: "Combat" },
  { key: "social",      label: "Social" },
  { key: "exploration", label: "Exploration" },
  { key: "puzzle",      label: "Puzzle" },
  { key: "mixed",       label: "Mixed" },
];
const STATUS_LABELS = {
  draft: "Draft", ready: "Ready", running: "Running",
  completed: "Completed", template: "Template",
};


export default function EncountersLibrary({ campId, sessionId = null, isGm = false }) {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState({ status: "", type: "" });
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const refresh = async () => {
    try {
      const params = new URLSearchParams();
      if (filter.status) params.set("status", filter.status);
      if (filter.type)   params.set("encounter_type", filter.type);
      const r = await api.get(`/campaigns/${campId}/encounters-library?${params.toString()}`);
      setRows(r.data?.rows || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };
  useEffect(() => { if (campId) refresh(); /* eslint-disable-next-line */ }, [campId, filter.status, filter.type]);

  const save = async () => {
    setBusy(true); setErr("");
    try {
      const url = draft.id
        ? `/campaigns/${campId}/encounters-library/${draft.id}`
        : `/campaigns/${campId}/encounters-library`;
      await api[draft.id ? "patch" : "post"](url, draft);
      setDraft(null);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const remove = async (eid) => {
    if (!window.confirm("Delete this encounter?")) return;
    await api.delete(`/campaigns/${campId}/encounters-library/${eid}`);
    refresh();
  };
  const clone = async (eid) => {
    await api.post(`/campaigns/${campId}/encounters-library/${eid}/clone?as_template=true`);
    refresh();
  };
  const run = async (eid) => {
    if (!sessionId) {
      window.alert("Open a session view to run an encounter.");
      return;
    }
    await api.post(`/campaigns/${campId}/encounters-library/${eid}/run?session_id=${sessionId}`);
    refresh();
  };
  const complete = async (eid) => {
    const note = window.prompt("Completion notes? (optional)") || "";
    await api.post(`/campaigns/${campId}/encounters-library/${eid}/complete?completion_notes=${encodeURIComponent(note)}`);
    refresh();
  };

  return (
    <div className="card-mystic p-4 space-y-3" data-testid="encounters-library">
      <div className="flex items-baseline justify-between flex-wrap gap-2 border-b border-gold/10 pb-2">
        <div>
          <div className="h-arcane text-sm flex items-center gap-2">
            <Swords className="w-4 h-4"/> Encounters Library
          </div>
          <div className="text-[11px] text-mist italic">
            {sessionId
              ? "Pick an encounter to run in this session — anti-railroad: bulk-author then choose live."
              : "Bulk-authoring & template archive. Pick from inside a session at play time."}
          </div>
        </div>
        {isGm && (
          <button onClick={() => setDraft(blankDraft())}
                  className="btn btn-primary text-xs"
                  data-testid="encounter-new-btn">
            <Plus className="w-3 h-3"/> New encounter
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-1.5 items-center text-[10px]">
        <Filter className="w-3 h-3 text-mist"/>
        <select className="select text-[10px]" value={filter.status}
                 onChange={(e) => setFilter({ ...filter, status: e.target.value })}
                 data-testid="encounter-filter-status">
          <option value="">all status</option>
          {Object.keys(STATUS_LABELS).map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
        <select className="select text-[10px]" value={filter.type}
                 onChange={(e) => setFilter({ ...filter, type: e.target.value })}
                 data-testid="encounter-filter-type">
          <option value="">all types</option>
          {ENCOUNTER_TYPES.map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
        </select>
        <span className="ml-auto text-mist tabular-nums">{rows.length} entries</span>
      </div>

      {err && <div className="text-ember text-xs" data-testid="encounter-error">{err}</div>}

      {rows.length === 0 && !draft && (
        <div className="text-mist italic text-[11px]" data-testid="encounter-empty">
          No encounters in the library yet. Create one to seed the archive.
        </div>
      )}

      <div className="space-y-1.5">
        {rows.map((e) => (
          <EncounterRow key={e.id} e={e} sessionId={sessionId} isGm={isGm}
                          onEdit={() => setDraft({ ...e })}
                          onRemove={() => remove(e.id)}
                          onClone={() => clone(e.id)}
                          onRun={() => run(e.id)}
                          onComplete={() => complete(e.id)}/>
        ))}
      </div>

      {draft && (
        <EncounterEditorModal draft={draft} setDraft={setDraft}
                                busy={busy} onSave={save}
                                onCancel={() => setDraft(null)}/>
      )}
    </div>
  );
}


function blankDraft() {
  return {
    name: "", summary: "", encounter_type: "combat", cr_target: null,
    monsters: [], complications: [], terrain: "", rewards: [],
    tags: [], status: "draft", notes: "",
  };
}


function EncounterRow({ e, sessionId, isGm, onEdit, onRemove, onClone, onRun, onComplete }) {
  const statusColor = {
    draft:     "border-mist text-mist",
    ready:     "border-arcane-light text-arcane-light",
    running:   "border-gold text-gold-bright bg-gold/10",
    completed: "border-emerald-400 text-emerald-300",
    template:  "border-violet-400 text-violet-300",
  }[e.status] || "border-mist";

  return (
    <div className="border border-gold/10 rounded-sm p-2 bg-void/30 flex items-center gap-2 flex-wrap"
         data-testid={`encounter-row-${e.id}`}>
      <div className="flex-1 min-w-[220px]">
        <div className="flex items-baseline gap-2">
          <span className="text-sm text-parchment font-display">{e.name}</span>
          <span className={`tag text-[9px] ${statusColor}`}>{STATUS_LABELS[e.status]}</span>
          {e.encounter_type && (
            <span className="text-[9px] text-arcane-light uppercase tracking-widest">
              {e.encounter_type}
            </span>
          )}
        </div>
        {e.summary && <div className="text-[11px] text-mist italic">{e.summary}</div>}
        <div className="text-[9px] text-mist mt-0.5">
          {e.monsters?.length || 0} foes
          {e.cr_target ? ` · CR ${e.cr_target}` : ""}
          {e.linked_session_id && e.linked_session_id !== sessionId
            ? ` · linked ${e.linked_session_id.slice(0, 8)}…` : ""}
          {e.cloned_from_id ? " · cloned" : ""}
        </div>
      </div>
      {sessionId && isGm && e.status !== "running" && e.status !== "completed" && (
        <button onClick={onRun} className="btn btn-primary text-[10px]"
                title="Run this encounter in the current session."
                data-testid={`encounter-run-${e.id}`}>
          <Play className="w-3 h-3"/> Run
        </button>
      )}
      {sessionId && isGm && e.status === "running" && (
        <button onClick={onComplete} className="btn btn-ghost text-[10px]"
                title="Mark this encounter completed (with optional notes)."
                data-testid={`encounter-complete-${e.id}`}>
          <CheckCircle2 className="w-3 h-3"/> Complete
        </button>
      )}
      {isGm && (
        <>
          <button onClick={onEdit} className="btn btn-ghost text-[10px]"
                  data-testid={`encounter-edit-${e.id}`}>
            <Pencil className="w-3 h-3"/>
          </button>
          <button onClick={onClone} className="btn btn-ghost text-[10px]"
                  title="Clone as template for re-use."
                  data-testid={`encounter-clone-${e.id}`}>
            <Copy className="w-3 h-3"/>
          </button>
          <button onClick={onRemove} className="btn btn-ghost text-[10px]"
                  data-testid={`encounter-delete-${e.id}`}>
            <Trash2 className="w-3 h-3"/>
          </button>
        </>
      )}
    </div>
  );
}


function EncounterEditorModal({ draft, setDraft, busy, onSave, onCancel }) {
  const set = (k, v) => setDraft({ ...draft, [k]: v });
  return (
    <div className="fixed inset-0 z-[200] bg-void/80 flex items-center justify-center p-4"
         onClick={onCancel} data-testid="encounter-editor-modal">
      <div className="card-mystic p-5 max-w-2xl w-full max-h-[90vh] overflow-y-auto space-y-3 relative"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={onCancel}
                 className="absolute top-2 right-2 text-mist hover:text-parchment">
          <X className="w-4 h-4"/>
        </button>
        <div className="h-arcane text-sm flex items-center gap-2">
          <FileEdit className="w-4 h-4"/> {draft.id ? "Edit encounter" : "Author encounter"}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div>
            <div className="label-ref">Name</div>
            <input className="input text-sm w-full" value={draft.name}
                    onChange={(e) => set("name", e.target.value)}
                    data-testid="encounter-name"/>
          </div>
          <div>
            <div className="label-ref">Type</div>
            <select className="select" value={draft.encounter_type}
                     onChange={(e) => set("encounter_type", e.target.value)}
                     data-testid="encounter-type-pick">
              {ENCOUNTER_TYPES.map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
            </select>
          </div>
        </div>
        <div>
          <div className="label-ref">Summary</div>
          <textarea className="input text-sm w-full" rows={2}
                     value={draft.summary} onChange={(e) => set("summary", e.target.value)}
                     placeholder="One-line hook for the encounter."
                     data-testid="encounter-summary"/>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div>
            <div className="label-ref">CR target</div>
            <input type="number" step="0.25" min="0" max="30"
                    value={draft.cr_target ?? ""}
                    onChange={(e) => set("cr_target", e.target.value === "" ? null : +e.target.value)}
                    className="input"
                    data-testid="encounter-cr"/>
          </div>
          <div>
            <div className="label-ref">Status</div>
            <select className="select" value={draft.status}
                     onChange={(e) => set("status", e.target.value)}
                     data-testid="encounter-status-pick">
              {Object.keys(STATUS_LABELS).map((s) =>
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
            </select>
          </div>
        </div>
        <div>
          <div className="label-ref">Terrain / setting</div>
          <input className="input text-sm w-full" value={draft.terrain}
                  onChange={(e) => set("terrain", e.target.value)}
                  placeholder="Stone bridge over a chasm. Wind 30 mph from the east."
                  data-testid="encounter-terrain"/>
        </div>
        <div>
          <div className="label-ref">Complications (one per line)</div>
          <textarea className="input text-sm w-full" rows={2}
                     value={(draft.complications || []).join("\n")}
                     onChange={(e) => set("complications",
                       e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
                     placeholder={"Cracking ice underfoot\nReinforcements arrive on round 3"}
                     data-testid="encounter-complications"/>
        </div>
        <div>
          <div className="label-ref">Notes (running prep)</div>
          <textarea className="input text-sm w-full" rows={3}
                     value={draft.notes} onChange={(e) => set("notes", e.target.value)}
                     placeholder="Statblocks, intent, escape conditions, narrative outs."
                     data-testid="encounter-notes"/>
        </div>
        <div>
          <div className="label-ref">Tags (comma-separated)</div>
          <input className="input text-sm w-full"
                  value={(draft.tags || []).join(", ")}
                  onChange={(e) => set("tags", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
                  placeholder="ambush, urban, midboss"
                  data-testid="encounter-tags"/>
        </div>
        <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
          <button onClick={onCancel} className="btn btn-ghost text-xs">Cancel</button>
          <button onClick={onSave} disabled={busy || !draft.name?.trim()}
                   className="btn btn-primary text-xs"
                   data-testid="encounter-save">
            <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
