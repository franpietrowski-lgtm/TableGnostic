import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, X, BookOpen, AlertCircle, Edit3, Save } from "lucide-react";

/**
 * ReferenceEditor — V4.4 Phase I.
 *
 * Lets a GM curate a campaign-scoped Weapons / Armor / Items / Companions /
 * Custom-rules table. Every entry is page-validated against the known
 * book ranges (besm-4e: 1-320, anime-5e: 1-200, etc.) — out-of-range
 * pages still save but show a warning so the GM knows to fix the cite.
 *
 * Players see this read-only (with the gm_only fields hidden).
 */
const KIND_LABELS = {
  weapon: "Weapons", armor: "Armor", item: "Items",
  companion: "Companions", custom: "Custom Rules",
  attribute: "Attributes", skill: "Skills", defect: "Defects",
};
const KIND_KEYS = Object.keys(KIND_LABELS);
// Kinds that flow back into the Character Builder's pickers — they expose
// extra structured inputs (cost_per_level / points_per_rank / category) so
// players can select them when forging a sheet.
const PLAYABLE_KINDS = new Set(["attribute", "skill", "defect"]);

export default function ReferenceEditor({ campaignId, isGm, systemId }) {
  const [tab, setTab] = useState("weapon");
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState("");
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      const { data } = await api.get(`/campaigns/${campaignId}/reference?kind=${tab}`);
      setRows(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };
  useEffect(() => { refresh(); }, [campaignId, tab]);

  const blank = () => ({
    kind: tab, name: "", summary: "", page: "",
    book: systemId || "besm-4e", cost: "", fields: {},
  });

  const save = async (row) => {
    setBusy(true); setErr("");
    try {
      const payload = { ...row, page: row.page === "" ? null : Number(row.page) };
      if (row.id) {
        await api.patch(`/campaigns/${campaignId}/reference/${row.id}`, payload);
      } else {
        await api.post(`/campaigns/${campaignId}/reference`, payload);
      }
      setDraft(null);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const remove = async (rid) => {
    if (!window.confirm("Delete this entry?")) return;
    await api.delete(`/campaigns/${campaignId}/reference/${rid}`);
    await refresh();
  };

  return (
    <div className="card-mystic p-4" data-testid="reference-editor">
      <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
        <div>
          <div className="label-ref flex items-center gap-2"><BookOpen className="w-3 h-3"/> Reference Tables</div>
          <div className="text-[10px] text-mist/70 italic">
            Per-campaign Weapons / Armor / Items / Companions / Custom rules.
            Page citations are validated against the system book range.
          </div>
        </div>
        {isGm && !draft && (
          <button onClick={() => setDraft(blank())} className="btn btn-primary text-xs"
                  data-testid="reference-add-btn">
            <Plus className="w-3 h-3"/> Add {KIND_LABELS[tab].slice(0, -1)}
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-1 mb-3 border-b border-gold/10 pb-2"
           data-testid="reference-tabs">
        {KIND_KEYS.map((k) => (
          <button key={k} onClick={() => setTab(k)}
                  className={`text-[10px] px-2 py-1 rounded-sm font-ui uppercase tracking-widest transition-colors ${tab === k ? "bg-gold/15 text-gold-bright border border-gold/30" : "text-mist hover:bg-gold/5"}`}
                  data-testid={`reference-tab-${k}`}>
            {KIND_LABELS[k]}
          </button>
        ))}
      </div>
      {err && <div className="text-ember text-xs mb-2">{err}</div>}
      {draft && (
        <Row row={draft} onChange={setDraft} onSave={save} onCancel={() => setDraft(null)}
             busy={busy} systemId={systemId} editing/>
      )}
      {rows.length === 0 && !draft && <div className="text-mist italic text-xs">No {KIND_LABELS[tab].toLowerCase()} yet.</div>}
      <div className="space-y-2">
        {rows.map((r) => (
          <Row key={r.id} row={r} onChange={() => {}}
               onEdit={isGm ? () => setDraft(r) : null}
               onRemove={isGm ? () => remove(r.id) : null}/>
        ))}
      </div>
    </div>
  );
}

function Row({ row, onChange, onSave, onCancel, busy, systemId, editing, onEdit, onRemove }) {
  const valid = row.page_validation;
  if (editing) {
    return (
      <div className="border border-gold/30 rounded-sm p-3 space-y-2 bg-gold/5"
           data-testid="reference-row-edit">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <input className="input col-span-2" placeholder="Name" value={row.name}
                 onChange={(e) => onChange({ ...row, name: e.target.value })}
                 data-testid="reference-input-name"/>
          <input className="input" placeholder="Cost (e.g. 2 pts/level)" value={row.cost}
                 onChange={(e) => onChange({ ...row, cost: e.target.value })}
                 data-testid="reference-input-cost"/>
        </div>
        <textarea className="input min-h-[60px]" placeholder="Summary (mechanic-only — no rulebook prose)"
                  value={row.summary}
                  onChange={(e) => onChange({ ...row, summary: e.target.value })}
                  data-testid="reference-input-summary"/>
        {PLAYABLE_KINDS.has(row.kind) && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 border border-gold/15 rounded-sm p-2 bg-gold/5"
               data-testid="reference-playable-fields">
            {row.kind !== "defect" && (
              <input className="input" type="number" step="0.5" min={0}
                     placeholder="Cost / Level (e.g. 4)"
                     value={(row.fields?.cost_per_level ?? "")}
                     onChange={(e) => onChange({ ...row,
                       fields: { ...(row.fields || {}),
                                 cost_per_level: e.target.value === "" ? "" : Number(e.target.value) } })}
                     data-testid="reference-input-cost-per-level"/>
            )}
            {row.kind === "defect" && (
              <input className="input" type="number" min={1}
                     placeholder="Points / Rank (e.g. 1 or 2)"
                     value={(row.fields?.points_per_rank ?? "")}
                     onChange={(e) => onChange({ ...row,
                       fields: { ...(row.fields || {}),
                                 points_per_rank: e.target.value === "" ? "" : Number(e.target.value) } })}
                     data-testid="reference-input-points-per-rank"/>
            )}
            {row.kind === "defect" && (
              <select className="select" value={row.fields?.category || "Lesser"}
                      onChange={(e) => onChange({ ...row,
                        fields: { ...(row.fields || {}), category: e.target.value } })}
                      data-testid="reference-input-defect-category">
                <option value="Lesser">Lesser</option>
                <option value="Greater">Greater</option>
                <option value="Custom">Custom</option>
              </select>
            )}
            <input className="input" placeholder="Description / GM note (optional)"
                   value={row.fields?.description || ""}
                   onChange={(e) => onChange({ ...row,
                     fields: { ...(row.fields || {}), description: e.target.value } })}
                   data-testid="reference-input-description"/>
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <input className="input" placeholder="Page" type="number" min={1} max={999}
                 value={row.page} onChange={(e) => onChange({ ...row, page: e.target.value })}
                 data-testid="reference-input-page"/>
          <input className="input" placeholder="Book (besm-4e, anime-5e, …)"
                 value={row.book || systemId || "besm-4e"}
                 onChange={(e) => onChange({ ...row, book: e.target.value })}
                 data-testid="reference-input-book"/>
          <select className="select" value={row.kind}
                  onChange={(e) => onChange({ ...row, kind: e.target.value })}
                  data-testid="reference-input-kind">
            {KIND_KEYS.map((k) => <option key={k} value={k}>{KIND_LABELS[k]}</option>)}
          </select>
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="btn btn-ghost text-xs">Cancel</button>
          <button onClick={() => onSave(row)} disabled={busy || !row.name}
                  className="btn btn-primary text-xs" data-testid="reference-save-btn">
            <Save className="w-3 h-3"/> Save
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className={`border rounded-sm p-3 ${valid && !valid.valid ? "border-ember/40" : "border-gold/15"}`}
         data-testid={`reference-row-${row.id}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-sm text-parchment font-ui">
            <b>{row.name}</b>
            {row.cost && <span className="text-gold/60 text-[10px] ml-2">{row.cost}</span>}
            {row.page && <span className="text-mist/60 text-[10px] ml-2">p.{row.page} {row.book}</span>}
          </div>
          {row.summary && <div className="text-[12px] text-parchment/85 italic mt-1 leading-snug">{row.summary}</div>}
          {valid && !valid.valid && (
            <div className="text-[10px] text-ember mt-1 flex items-center gap-1" data-testid="reference-page-warn">
              <AlertCircle className="w-3 h-3"/> {valid.reason}
            </div>
          )}
        </div>
        <div className="flex gap-1.5 flex-shrink-0">
          {onEdit && <button onClick={onEdit} className="text-mist/70 hover:text-gold p-1"><Edit3 className="w-3 h-3"/></button>}
          {onRemove && <button onClick={onRemove} className="text-ember/70 hover:text-ember p-1"><X className="w-3 h-3"/></button>}
        </div>
      </div>
    </div>
  );
}

/** Static instructions card. Players see all but GM-Materials. */
export function InstructionsPanel({ isGm }) {
  return (
    <div className="card-mystic p-4" data-testid="instructions-panel">
      <div className="label-ref mb-3 flex items-center gap-2">
        <BookOpen className="w-3 h-3"/> Quickstart Instructions
      </div>
      <Section title="How to make a character">
        <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
          <li>Open <b>Characters → Create</b>. Pick concept, name, Power Level (Adventurous = 90 pts).</li>
          <li>Set <b>Stats</b> (Body / Mind / Soul) — sum should reflect the concept's strengths.</li>
          <li>Add <b>Attributes</b> from the system selector. Each Enhancement = 1 application that lowers effective Level by 1; each Limiter = 1 application that raises it by 1 (cost stays at base × level).</li>
          <li>Add <b>Skills</b> with components, and balance with <b>Defects</b> (refunds points) for narrative weight.</li>
          <li>Save. The GM will publish the sheet once the table approves.</li>
        </ol>
      </Section>
      <Section title="How to make a weapon or item">
        <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
          <li>Atelier → Reference Tables → choose Weapons / Items.</li>
          <li>Click <b>Add Weapon/Item</b>. Name, mechanic-only summary, cost, page reference.</li>
          <li>The page is validated against the system book range. Out-of-range citations save with a warning so you can fix later.</li>
        </ol>
      </Section>
      <Section title="How to spend XP">
        <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
          <li>From your <b>Character Sheet → Spend XP</b>, propose a stat or attribute level change with the XP cost.</li>
          <li>The GM sees the proposal in the Atelier queue and approves or rejects it.</li>
          <li>On approval, the change applies immediately and XP is deducted. Live rolls always read the GM-approved snapshot.</li>
        </ol>
      </Section>
      {isGm && (
        <Section title="GM Materials" testid="instructions-gm-materials">
          <ul className="list-disc list-inside space-y-1 text-sm text-parchment/90">
            <li><b>Atelier tab</b> contains Session 0 / Arcs / Master Plot tiers. Continuity check flags missing references.</li>
            <li><b>Knowledge Web → Mechanic Ingestion</b>: drop in a rulebook excerpt or world bible; Claude returns categorized suggestions.</li>
            <li><b>GM Session Journal</b> is a pinned, GM-only Codex node. Append after every session.</li>
            <li><b>Export PDF</b> produces a DriveThruRPG-ready chronicle including the World Codex appendix and per-PC sheets.</li>
            <li><b>XP Award scorecard</b> (Session view) tallies engagement and proposes per-PC awards. Suggest-only — never auto-commits.</li>
          </ul>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children, testid }) {
  return (
    <div className="mb-4" data-testid={testid}>
      <div className="text-[11px] font-ui uppercase tracking-widest text-gold-bright mb-1">{title}</div>
      {children}
    </div>
  );
}
