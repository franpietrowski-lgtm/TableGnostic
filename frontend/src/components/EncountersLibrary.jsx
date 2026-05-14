/**
 * EncountersLibrary — V6.25.29 (anti-railroad encounter flow + entity-aware completion)
 *
 * GM-only library where encounters live as first-class artifacts.
 * Authoring is decoupled from session binding — GMs bulk-create and
 * pick from inside a session.
 *
 * Statuses: draft → ready → running → completed | template
 *
 * V6.25.29 additions:
 *   • Bestiary picker in the editor — pulls system-specific monsters
 *     from /systems/{systemId}/reference and adds them to encounter.monsters[].
 *   • Casualty + kill-tally modal at completion time — vigilizes NPC
 *     codex nodes and tallies monster kills per character/campaign.
 *
 * Usable in two modes:
 *   1. Director's Console (campaign-wide) — full CRUD + clone + bulk auth.
 *   2. Session view (`session_id` prop set) — picker + Run / Complete affordances.
 */
import React, { useEffect, useMemo, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Swords, Plus, Trash2, Copy, Save, X, Play, CheckCircle2, FileEdit, Pencil,
  Filter, Skull, BookOpen,
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


export default function EncountersLibrary({ campId, sessionId = null, isGm = false, systemId = null }) {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState({ status: "", type: "" });
  const [draft, setDraft] = useState(null);
  const [completing, setCompleting] = useState(null);  // V6.25.29 — encounter pending completion
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
    // V6.25.29 — session_id is optional now. In Director Console
    // (no session) the encounter still flips to "running" so the
    // GM can resolve + propagate to the codex out-of-band.
    setBusy(true); setErr("");
    try {
      const url = sessionId
        ? `/campaigns/${campId}/encounters-library/${eid}/run?session_id=${sessionId}`
        : `/campaigns/${campId}/encounters-library/${eid}/run`;
      await api.post(url);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };
  const complete = async (encounter) => {
    // V6.25.29 — open the completion modal instead of a prompt; the
    // GM can vigilize casualties and tally monster kills before
    // the codex propagation fires.
    setCompleting(encounter);
  };
  const submitCompletion = async (eid, payload) => {
    setBusy(true); setErr("");
    try {
      await api.post(
        `/campaigns/${campId}/encounters-library/${eid}/complete`,
        payload);
      setCompleting(null);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
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
                          onComplete={() => complete(e)}/>
        ))}
      </div>

      {draft && (
        <EncounterEditorModal draft={draft} setDraft={setDraft}
                                busy={busy} onSave={save}
                                systemId={systemId}
                                onCancel={() => setDraft(null)}/>
      )}
      {completing && (
        <EncounterCompleteModal encounter={completing}
                                  campId={campId}
                                  sessionId={sessionId}
                                  busy={busy}
                                  onCancel={() => setCompleting(null)}
                                  onSubmit={(payload) => submitCompletion(completing.id, payload)}/>
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
      {/* V6.25.29 — Run/Complete also exposed in Director Console
          (no sessionId), since GMs commonly resolve out-of-band
          encounters and the codex propagation must work everywhere. */}
      {isGm && e.status !== "running" && e.status !== "completed" && (
        <button onClick={onRun} className="btn btn-primary text-[10px]"
                title="Mark this encounter as running."
                data-testid={`encounter-run-${e.id}`}>
          <Play className="w-3 h-3"/> Run
        </button>
      )}
      {isGm && e.status === "running" && (
        <button onClick={onComplete} className="btn btn-ghost text-[10px]"
                title="Resolve & propagate to codex (vigilize NPCs, tally kills)."
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


function EncounterEditorModal({ draft, setDraft, busy, onSave, onCancel, systemId }) {
  const set = (k, v) => setDraft({ ...draft, [k]: v });
  const [bestiary, setBestiary] = useState(null);
  useEffect(() => {
    let cancelled = false;
    if (!systemId) return undefined;
    api.get(`/systems/${systemId}/reference`).then((r) => {
      if (cancelled) return;
      const ref = r.data || {};
      // Per system, monsters live under different keys.
      const list = ref.monsters || ref.bestiary || [];
      setBestiary(list);
    }).catch(() => setBestiary([]));
    return () => { cancelled = true; };
  }, [systemId]);

  const addMonster = (m) => {
    const row = {
      name: m.name,
      count: 1,
      cr: m.cr ?? null,
      level: m.level ?? null,
      ref_id: m.id || null,
      stats: { ac: m.ac, hp: m.hp, speed: m.speed, atks: m.atks },
      system: systemId,
    };
    set("monsters", [...(draft.monsters || []), row]);
  };
  const updateMonsterCount = (idx, count) => {
    const list = [...(draft.monsters || [])];
    list[idx] = { ...list[idx], count: Math.max(1, +count || 1) };
    set("monsters", list);
  };
  const removeMonster = (idx) => {
    const list = (draft.monsters || []).filter((_, i) => i !== idx);
    set("monsters", list);
  };
  return (
    <div className="fixed inset-0 z-[8800] bg-void/80 backdrop-blur-sm flex items-center justify-center p-4"
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

        {/* V6.25.29 — Per-system bestiary picker. */}
        <div className="border-t border-gold/10 pt-3">
          <div className="label-ref mb-1 flex items-center gap-1">
            <Skull className="w-3 h-3"/> Foes ({(draft.monsters || []).length})
          </div>
          <ul className="space-y-1 mb-2" data-testid="encounter-monster-list">
            {(draft.monsters || []).map((m, i) => (
              <li key={i}
                  className="flex items-center gap-2 text-xs border border-gold/10 rounded-sm p-1.5 bg-void/40"
                  data-testid={`encounter-monster-row-${i}`}>
                <span className="text-parchment font-body flex-1">{m.name}</span>
                {m.cr != null && <span className="text-gold/60">CR {m.cr}</span>}
                {m.stats?.hp && <span className="text-mist">HP {m.stats.hp}</span>}
                <input type="number" className="input w-16 text-xs"
                       value={m.count} min={1}
                       onChange={(e) => updateMonsterCount(i, e.target.value)}
                       data-testid={`encounter-monster-count-${i}`}/>
                <button onClick={() => removeMonster(i)}
                        className="touch-target text-mist hover:text-ember"
                        data-testid={`encounter-monster-del-${i}`}>
                  <X className="w-3 h-3"/>
                </button>
              </li>
            ))}
            {(draft.monsters || []).length === 0 && (
              <li className="text-mist italic text-[11px]">No foes attached. Browse the bestiary below or use the manual textbox.</li>
            )}
          </ul>
          <BestiaryPicker bestiary={bestiary} onPick={addMonster} systemId={systemId}/>
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



// ────────────────────────────────────────────────────────────────────
// BestiaryPicker — V6.25.29 — system-aware bestiary chooser.
// Displays the per-system monster catalogue (D&D 5E monsters,
// Cypher bestiary, etc.) so the GM can drop foes into an encounter
// with one click.
// ────────────────────────────────────────────────────────────────────
function BestiaryPicker({ bestiary, onPick, systemId }) {
  const [q, setQ] = useState("");
  const [crMin, setCrMin] = useState("");
  const [crMax, setCrMax] = useState("");
  if (!bestiary) {
    return <div className="text-mist italic text-[11px]" data-testid="bestiary-loading">
      Loading {systemId || "system"} bestiary…
    </div>;
  }
  if (bestiary.length === 0) {
    return <div className="text-mist italic text-[11px]" data-testid="bestiary-empty">
      No bestiary seeded for this system yet.
    </div>;
  }
  const ql = q.toLowerCase();
  const minN = crMin === "" ? -Infinity : +crMin;
  const maxN = crMax === "" ? Infinity : +crMax;
  const filtered = bestiary.filter((m) => {
    const cr = (m.cr ?? m.level ?? 0);
    if (cr < minN || cr > maxN) return false;
    if (!ql) return true;
    return JSON.stringify(m).toLowerCase().includes(ql);
  });
  return (
    <div className="border border-gold/15 rounded-sm p-2 bg-void/30"
         data-testid="bestiary-picker">
      <div className="flex items-center gap-1.5 mb-2 flex-wrap">
        <BookOpen className="w-3 h-3 text-gold/60"/>
        <span className="text-[10px] text-mist uppercase tracking-widest">Bestiary</span>
        <input className="input text-xs h-7 flex-1 min-w-[140px]"
               placeholder="Search by name / type"
               value={q} onChange={(e) => setQ(e.target.value)}
               data-testid="bestiary-search"/>
        <input type="number" className="input text-xs h-7 w-16"
               placeholder="CR min" value={crMin}
               onChange={(e) => setCrMin(e.target.value)}
               data-testid="bestiary-cr-min"/>
        <input type="number" className="input text-xs h-7 w-16"
               placeholder="CR max" value={crMax}
               onChange={(e) => setCrMax(e.target.value)}
               data-testid="bestiary-cr-max"/>
        <span className="text-[9px] text-mist tabular-nums">{filtered.length} / {bestiary.length}</span>
      </div>
      <ul className="max-h-44 overflow-y-auto space-y-0.5">
        {filtered.slice(0, 60).map((m, i) => (
          <li key={`${m.name}-${i}`}
              className="flex items-center gap-2 text-[11px] hover:bg-gold/5 rounded-sm px-1 py-0.5 cursor-pointer"
              onClick={() => onPick(m)}
              data-testid={`bestiary-pick-${m.name?.toLowerCase().replace(/\s+/g, "-")}`}>
            <span className="text-parchment font-body flex-1">{m.name}</span>
            {m.cr != null && <span className="text-gold/60">CR {m.cr}</span>}
            {m.level != null && m.cr == null && (
              <span className="text-gold/60">L{m.level}</span>
            )}
            {m.type && <span className="text-mist">{m.type}</span>}
            <Plus className="w-3 h-3 text-mist"/>
          </li>
        ))}
      </ul>
    </div>
  );
}


// ────────────────────────────────────────────────────────────────────
// EncounterCompleteModal — V6.25.29
// At completion time the GM:
//   • adds free-text resolution notes,
//   • toggles which referenced NPC entities died (with reason +
//     witness picker), so the codex can vigilize them,
//   • tallies kills per monster (count + which character scored
//     the killing blow), so kill_logs accumulate.
// ────────────────────────────────────────────────────────────────────
function EncounterCompleteModal({ encounter, campId, sessionId, busy, onCancel, onSubmit }) {
  const [notes, setNotes] = useState(encounter.completion_notes || "");
  const [entities, setEntities] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [casualties, setCasualties] = useState({});  // node_id -> {death_reason, witnesses[], killed_by}
  const [kills, setKills] = useState(() =>
    (encounter.monsters || []).map((m) => ({
      monster_name: m.name,
      monster_ref_id: m.ref_id || null,
      cr: m.cr ?? null,
      system: m.system || null,
      count_planned: m.count || 1,
      count: 0,
      killed_by_character_id: "",
    })));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [eRes, cRes] = await Promise.all([
          api.get(`/campaigns/${campId}/entities`),
          api.get(`/campaigns/${campId}/characters`),
        ]);
        if (cancelled) return;
        setEntities((eRes.data?.rows || []).filter((e) =>
          ["npc", "character", "person"].includes(e.node_kind || e.type)));
        setCharacters(cRes.data || []);
      } catch (_) { /* tolerate */ }
    })();
    return () => { cancelled = true; };
  }, [campId]);

  const toggleCasualty = (nodeId) => {
    setCasualties((c) => {
      const next = { ...c };
      if (next[nodeId]) delete next[nodeId];
      else next[nodeId] = { death_reason: "", witnesses: [], killed_by_character_id: "" };
      return next;
    });
  };
  const setCasField = (nodeId, k, v) => {
    setCasualties((c) => ({ ...c, [nodeId]: { ...(c[nodeId] || {}), [k]: v } }));
  };

  const submit = () => {
    const payload = {
      completion_notes: notes,
      session_id: sessionId,
      casualties: Object.entries(casualties).map(([nid, v]) => ({
        node_id: nid,
        death_reason: v.death_reason || "",
        witnesses: v.witnesses || [],
        killed_by_character_id: v.killed_by_character_id || null,
      })),
      kills: kills
        .filter((k) => (k.count || 0) > 0)
        .map((k) => ({
          monster_name: k.monster_name,
          monster_ref_id: k.monster_ref_id,
          count: +k.count,
          cr: k.cr,
          system: k.system,
          killed_by_character_id: k.killed_by_character_id || null,
        })),
    };
    onSubmit(payload);
  };

  return (
    <div className="fixed inset-0 z-[8800] bg-void/85 backdrop-blur-sm flex items-center justify-center p-4"
         onClick={onCancel} data-testid="encounter-complete-modal">
      <div className="card-mystic p-5 max-w-3xl w-full max-h-[90vh] overflow-y-auto space-y-4 relative"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={onCancel}
                className="absolute top-2 right-2 text-mist hover:text-parchment">
          <X className="w-4 h-4"/>
        </button>
        <div className="h-arcane text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4"/> Resolve · {encounter.name}
        </div>
        <div>
          <div className="label-ref">Completion notes</div>
          <textarea className="input text-sm w-full" rows={3}
                    value={notes} onChange={(e) => setNotes(e.target.value)}
                    placeholder="What happened? What changed in the world?"
                    data-testid="encounter-complete-notes"/>
        </div>

        {/* ── Casualties — NPC vigil ───────────────────────────── */}
        <div className="border-t border-gold/10 pt-3">
          <div className="label-ref mb-2 flex items-center gap-1">
            <Skull className="w-3 h-3"/> NPC casualties (vigilize on codex)
          </div>
          {entities.length === 0 && (
            <div className="text-mist italic text-[11px]" data-testid="complete-no-entities">
              No NPC codex entities in this campaign.
            </div>
          )}
          <ul className="space-y-1.5" data-testid="complete-casualties">
            {entities.map((e) => {
              const checked = !!casualties[e.id];
              return (
                <li key={e.id}
                    className="border border-gold/10 rounded-sm p-2 bg-void/40">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={checked}
                           onChange={() => toggleCasualty(e.id)}
                           data-testid={`complete-cas-toggle-${e.id}`}/>
                    <span className="text-parchment">{e.title}</span>
                    {e.fields?.deceased && (
                      <span className="text-ember text-[10px] uppercase tracking-widest">
                        already deceased
                      </span>
                    )}
                  </label>
                  {checked && (
                    <div className="mt-1.5 ml-6 space-y-1">
                      <input className="input text-xs w-full"
                             placeholder="Death reason (e.g. Slain by Azazel during the Bridge ambush)"
                             value={casualties[e.id]?.death_reason || ""}
                             onChange={(ev) => setCasField(e.id, "death_reason", ev.target.value)}
                             data-testid={`complete-cas-reason-${e.id}`}/>
                      <select className="select text-xs"
                              value={casualties[e.id]?.killed_by_character_id || ""}
                              onChange={(ev) => setCasField(e.id, "killed_by_character_id", ev.target.value)}
                              data-testid={`complete-cas-killer-${e.id}`}>
                        <option value="">— killed by (optional) —</option>
                        {characters.map((c) => (
                          <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                      </select>
                      <select multiple className="select text-xs h-20"
                              value={casualties[e.id]?.witnesses || []}
                              onChange={(ev) => setCasField(
                                e.id, "witnesses",
                                Array.from(ev.target.selectedOptions, (o) => o.value))}
                              data-testid={`complete-cas-witnesses-${e.id}`}>
                        {entities.filter((w) => w.id !== e.id).map((w) => (
                          <option key={w.id} value={w.id}>{w.title}</option>
                        ))}
                      </select>
                      <div className="text-[9px] text-mist italic">
                        Hold cmd/ctrl to multi-select witnesses.
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>

        {/* ── Kill tally — monster/creature ────────────────────── */}
        <div className="border-t border-gold/10 pt-3">
          <div className="label-ref mb-2 flex items-center gap-1">
            <Swords className="w-3 h-3"/> Kill tally (monsters / creatures)
          </div>
          {kills.length === 0 && (
            <div className="text-mist italic text-[11px]" data-testid="complete-no-kills">
              No foes attached to this encounter — nothing to tally.
            </div>
          )}
          <ul className="space-y-1.5" data-testid="complete-kills">
            {kills.map((k, i) => (
              <li key={`${k.monster_name}-${i}`}
                  className="border border-gold/10 rounded-sm p-2 bg-void/40 flex items-center gap-2 flex-wrap">
                <span className="text-sm text-parchment flex-1">
                  {k.monster_name}
                  {k.cr != null && <span className="text-gold/60 text-[10px] ml-1">CR {k.cr}</span>}
                  <span className="text-mist text-[10px] ml-1">/ {k.count_planned} planned</span>
                </span>
                <input type="number" className="input text-xs w-20"
                       min={0} max={999}
                       placeholder="killed"
                       value={k.count}
                       onChange={(ev) => {
                         const next = [...kills];
                         next[i] = { ...next[i], count: +ev.target.value };
                         setKills(next);
                       }}
                       data-testid={`complete-kill-count-${i}`}/>
                <select className="select text-xs"
                        value={k.killed_by_character_id || ""}
                        onChange={(ev) => {
                          const next = [...kills];
                          next[i] = { ...next[i], killed_by_character_id: ev.target.value };
                          setKills(next);
                        }}
                        data-testid={`complete-kill-killer-${i}`}>
                  <option value="">— killing blow —</option>
                  {characters.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
          <button onClick={onCancel} className="btn btn-ghost text-xs"
                  data-testid="complete-cancel">Cancel</button>
          <button onClick={submit} disabled={busy}
                  className="btn btn-primary text-xs"
                  data-testid="complete-submit">
            <CheckCircle2 className="w-3 h-3"/> {busy ? "Resolving…" : "Resolve & propagate"}
          </button>
        </div>
      </div>
    </div>
  );
}
