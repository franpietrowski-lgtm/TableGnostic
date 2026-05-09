/**
 * RollTableDesigner — V6.25.25 (Cycle D)
 *
 * GM-only roll-table designer for the Director's Console. Each table is
 * a weighted list whose entries MUST point at a seeded reference, codex
 * node, or carry a deliberate literal body. Tables declare a rarity tier
 * (common → legendary) which auto-sets the minimum party tier to roll —
 * preventing accidental "level-1 party finds a legendary artifact" rolls.
 */
import React, { useEffect, useState, useMemo } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Dices, Plus, X, Trash2, Save, BookOpen, Network, Pencil, RotateCcw,
} from "lucide-react";

const RARITY_TIERS = [
  { key: "common",    label: "Common",     die: "1d6",   gate: 1 },
  { key: "uncommon",  label: "Uncommon",   die: "1d10",  gate: 2 },
  { key: "rare",      label: "Rare",       die: "1d20",  gate: 4 },
  { key: "very_rare", label: "Very Rare",  die: "1d50",  gate: 6 },
  { key: "legendary", label: "Legendary",  die: "1d100", gate: 9 },
];


export default function RollTableDesigner({ campId, partyTier = 1 }) {
  const [tables, setTables] = useState([]);
  const [selected, setSelected] = useState(null);
  const [draft, setDraft] = useState(null);
  const [refLib, setRefLib] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [rollResult, setRollResult] = useState(null);

  const refresh = async () => {
    try {
      const r = await api.get(`/campaigns/${campId}/roll-tables`);
      setTables(r.data?.rows || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  useEffect(() => {
    if (!campId) return;
    refresh();
    api.get(`/campaigns/${campId}/reference?limit=500`)
      .then((r) => setRefLib(r.data?.rows || r.data || []))
      .catch(() => setRefLib([]));
    api.get(`/campaigns/${campId}/codex-nodes`)
      .then((r) => setNodes(r.data?.rows || r.data || []))
      .catch(() => setNodes([]));
    api.get(`/campaigns/${campId}/materials`)
      .then((r) => setMaterials(r.data?.rows || []))
      .catch(() => setMaterials([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campId]);

  const beginNew = () => {
    setDraft({
      name: "",
      description: "",
      rarity_tier: "common",
      min_party_tier: 1,
      entries: [{ weight: 1, label: "", reference_id: null, node_id: null, material_id: null, body: "" }],
    });
    setSelected(null);
    setRollResult(null);
  };

  const beginEdit = (t) => {
    setDraft({
      ...t,
      entries: (t.entries || []).map((e) => ({
        weight: e.weight || 1,
        label: e.label || "",
        reference_id: e.reference_id || null,
        node_id: e.node_id || null,
        material_id: e.material_id || null,
        body: e.body || "",
      })),
    });
    setSelected(t);
    setRollResult(null);
  };

  const saveDraft = async () => {
    setBusy(true); setErr("");
    try {
      // Strip empty fields per the "exactly one source" rule.
      const cleanEntries = draft.entries.map((e) => {
        if (e.reference_id) return { weight: e.weight, label: e.label, reference_id: e.reference_id };
        if (e.node_id)      return { weight: e.weight, label: e.label, node_id: e.node_id };
        if (e.material_id)  return { weight: e.weight, label: e.label, material_id: e.material_id };
        return { weight: e.weight, label: e.label, body: e.body };
      });
      const payload = { ...draft, entries: cleanEntries };
      const url = selected
        ? `/campaigns/${campId}/roll-tables/${selected.id}`
        : `/campaigns/${campId}/roll-tables`;
      const m = selected ? "patch" : "post";
      const r = await api[m](url, payload);
      await refresh();
      setSelected(r.data);
      setDraft(null);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const remove = async (tid) => {
    if (!window.confirm("Delete this roll table?")) return;
    await api.delete(`/campaigns/${campId}/roll-tables/${tid}`);
    if (selected?.id === tid) setSelected(null);
    refresh();
  };

  const roll = async (t) => {
    setBusy(true); setErr(""); setRollResult(null);
    try {
      const r = await api.post(
        `/campaigns/${campId}/roll-tables/${t.id}/roll?party_tier=${partyTier || 1}`);
      setRollResult(r.data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="card-mystic p-4 space-y-3" data-testid="roll-table-designer">
      <div className="flex items-baseline justify-between flex-wrap gap-2 border-b border-gold/10 pb-2">
        <div>
          <div className="h-arcane text-sm flex items-center gap-2">
            <Dices className="w-4 h-4"/> Roll-Table Designer
          </div>
          <div className="text-[10px] text-mist italic">
            Gated to seeded materials · party tier {partyTier} · entries
            must point at a Reference Editor row, a Codex node, or carry
            a deliberate literal body.
          </div>
        </div>
        <button onClick={beginNew} className="btn btn-primary text-xs"
                 data-testid="roll-table-new-btn">
          <Plus className="w-3 h-3"/> New table
        </button>
      </div>

      {err && <div className="text-ember text-xs"
                    data-testid="roll-table-error">{err}</div>}

      {/* List of tables */}
      <div className="space-y-1.5">
        {tables.length === 0 && !draft && (
          <div className="text-mist italic text-[11px]"
               data-testid="roll-table-empty">
            No roll tables yet. Click "New table" to author one — start
            with a Common loot/encounter table to seed everyday rolls.
          </div>
        )}
        {tables.map((t) => {
          const tier = RARITY_TIERS.find((r) => r.key === t.rarity_tier) || RARITY_TIERS[0];
          const gated = (partyTier || 1) < t.min_party_tier;
          return (
            <div key={t.id}
                 className="border border-gold/10 rounded-sm p-2 bg-void/30 flex items-center gap-2 flex-wrap"
                 data-testid={`roll-table-row-${t.id}`}>
              <div className="flex-1 min-w-[200px]">
                <div className="text-sm text-parchment font-display">{t.name}</div>
                <div className="text-[10px] text-mist italic">
                  {tier.label} · {tier.die} · gate ≥ tier {t.min_party_tier} · {t.entries?.length || 0} entries
                </div>
              </div>
              <button onClick={() => roll(t)} disabled={busy || gated}
                      className="btn btn-ghost text-[10px]"
                      title={gated ? `Party tier ${partyTier} is below this table's gate (≥${t.min_party_tier}).` : "Roll the table"}
                      data-testid={`roll-table-roll-${t.id}`}>
                <Dices className="w-3 h-3"/> Roll
              </button>
              <button onClick={() => beginEdit(t)}
                      className="btn btn-ghost text-[10px]"
                      data-testid={`roll-table-edit-${t.id}`}>
                <Pencil className="w-3 h-3"/> Edit
              </button>
              <button onClick={() => remove(t.id)}
                      className="btn btn-ghost text-[10px]"
                      data-testid={`roll-table-delete-${t.id}`}>
                <Trash2 className="w-3 h-3"/>
              </button>
            </div>
          );
        })}
      </div>

      {/* Roll result */}
      {rollResult && (
        <div className="border border-gold/30 rounded-sm p-3 bg-gold/5"
             data-testid="roll-table-result">
          <div className="flex items-center justify-between gap-2">
            <div className="text-[11px] text-mist italic">
              {rollResult.table_name} · {rollResult.die} · {rollResult.rarity_tier}
            </div>
            <button onClick={() => setRollResult(null)}
                     className="text-mist hover:text-parchment"
                     data-testid="roll-result-dismiss">
              <X className="w-3 h-3"/>
            </button>
          </div>
          <div className="mt-1.5 text-base font-display text-gold-bright">
            {rollResult.result?.label || rollResult.result?.source?.name || "(unnamed)"}
          </div>
          {rollResult.result?.source?.summary && (
            <div className="text-[11px] text-parchment/85 italic mt-0.5">
              {rollResult.result.source.summary}
            </div>
          )}
          {rollResult.result?.body && (
            <div className="text-[11px] text-parchment mt-1">{rollResult.result.body}</div>
          )}
          <div className="text-[10px] text-arcane-light mt-1">
            source: {rollResult.result?.source?.kind}
            {rollResult.result?.source?.ref_kind ? ` · ${rollResult.result.source.ref_kind}` : ""}
            {rollResult.result?.source?.node_kind ? ` · ${rollResult.result.source.node_kind}` : ""}
          </div>
        </div>
      )}

      {/* Editor */}
      {draft && (
        <RollTableEditor draft={draft} setDraft={setDraft}
                          refLib={refLib} nodes={nodes} materials={materials}
                          onCancel={() => { setDraft(null); setSelected(null); }}
                          onSave={saveDraft} busy={busy}/>
      )}
    </div>
  );
}


function RollTableEditor({ draft, setDraft, refLib, nodes, materials, onCancel, onSave, busy }) {
  const totalWeight = useMemo(() =>
    (draft.entries || []).reduce((s, e) => s + (Number(e.weight) || 0), 0),
    [draft.entries]);

  const setField = (k, v) => setDraft({ ...draft, [k]: v });
  const setEntry = (i, patch) => setDraft({
    ...draft,
    entries: draft.entries.map((e, j) => j === i ? { ...e, ...patch } : e),
  });
  const addEntry = () => setDraft({
    ...draft,
    entries: [...draft.entries, { weight: 1, label: "", reference_id: null, node_id: null, material_id: null, body: "" }],
  });
  const removeEntry = (i) => setDraft({
    ...draft,
    entries: draft.entries.filter((_, j) => j !== i),
  });

  const tier = RARITY_TIERS.find((r) => r.key === draft.rarity_tier) || RARITY_TIERS[0];

  return (
    <div className="border-t border-gold/10 pt-3 space-y-2"
         data-testid="roll-table-editor">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div>
          <div className="label-ref">Name</div>
          <input className="input text-sm w-full" value={draft.name}
                  onChange={(e) => setField("name", e.target.value)}
                  placeholder="Tavern omens · loot · NPC entrances"
                  data-testid="roll-table-name"/>
        </div>
        <div>
          <div className="label-ref">Rarity tier</div>
          <select className="select" value={draft.rarity_tier}
                   onChange={(e) => {
                     const t = RARITY_TIERS.find((x) => x.key === e.target.value);
                     setDraft({ ...draft, rarity_tier: e.target.value,
                                  min_party_tier: Math.max(draft.min_party_tier || 1, t.gate) });
                   }}
                   data-testid="roll-table-rarity">
            {RARITY_TIERS.map((t) =>
              <option key={t.key} value={t.key}>{t.label} · {t.die} · gate ≥ tier {t.gate}</option>)}
          </select>
        </div>
      </div>
      <div>
        <div className="label-ref">Description</div>
        <textarea className="input text-sm w-full" rows={2}
                   value={draft.description}
                   onChange={(e) => setField("description", e.target.value)}
                   placeholder="What does the GM look at this for?"
                   data-testid="roll-table-description"/>
      </div>

      <div className="border-t border-gold/10 pt-2">
        <div className="flex items-baseline justify-between mb-1">
          <div className="label-ref">Entries — total weight {totalWeight}</div>
          <button onClick={addEntry} className="btn btn-ghost text-[10px]"
                   data-testid="roll-table-add-entry">
            <Plus className="w-3 h-3"/> Add entry
          </button>
        </div>
        <div className="space-y-2">
          {draft.entries.map((e, i) => (
            <RollEntryRow key={i} idx={i} entry={e}
                            refLib={refLib} nodes={nodes} materials={materials}
                            onChange={(patch) => setEntry(i, patch)}
                            onRemove={() => removeEntry(i)}/>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
        <button onClick={onCancel} className="btn btn-ghost text-xs">
          <RotateCcw className="w-3 h-3"/> Cancel
        </button>
        <button onClick={onSave} disabled={busy || !draft.name?.trim() || draft.entries.length === 0}
                 className="btn btn-primary text-xs"
                 data-testid="roll-table-save">
          <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save table"}
        </button>
      </div>
      <div className="text-[10px] text-mist italic">
        Gate auto-snaps to the rarity's canonical floor ({tier.gate}) so
        a Common-rarity table can't accidentally drop legendary loot
        on a tier-1 party.
      </div>
    </div>
  );
}


function RollEntryRow({ idx, entry, refLib, nodes, materials, onChange, onRemove }) {
  const sourceKind = entry.reference_id ? "reference"
                        : entry.node_id ? "node"
                        : entry.material_id ? "material"
                        : entry.body ? "body" : "";

  const setSource = (kind) => {
    const cleared = { reference_id: null, node_id: null, material_id: null, body: "" };
    if (kind === "reference") cleared.reference_id = refLib[0]?.id || null;
    if (kind === "node")      cleared.node_id      = nodes[0]?.id  || null;
    if (kind === "material")  cleared.material_id  = materials[0]?.id || null;
    if (kind === "body")      cleared.body         = "";
    onChange(cleared);
  };

  return (
    <div className="border border-gold/10 rounded-sm p-2 bg-void/40 space-y-1.5"
         data-testid={`roll-entry-${idx}`}>
      <div className="flex items-center gap-2">
        <input type="number" min={1} max={100} value={entry.weight}
                onChange={(e) => onChange({ weight: +e.target.value || 1 })}
                className="input w-16 text-center text-xs"
                data-testid={`roll-entry-weight-${idx}`}/>
        <span className="text-[10px] text-mist">×</span>
        <input type="text" value={entry.label}
                onChange={(e) => onChange({ label: e.target.value })}
                className="input text-xs flex-1"
                placeholder="Label (auto-fills from source if blank)"
                data-testid={`roll-entry-label-${idx}`}/>
        <button onClick={onRemove} className="text-mist hover:text-ember"
                 data-testid={`roll-entry-remove-${idx}`}>
          <X className="w-3 h-3"/>
        </button>
      </div>

      <div className="flex flex-wrap gap-1 text-[10px]">
        <button type="button" onClick={() => setSource("reference")}
                 className={`tag ${sourceKind === "reference" ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                 data-testid={`roll-entry-src-ref-${idx}`}>
          <BookOpen className="w-3 h-3"/> Reference
        </button>
        <button type="button" onClick={() => setSource("node")}
                 className={`tag ${sourceKind === "node" ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                 data-testid={`roll-entry-src-node-${idx}`}>
          <Network className="w-3 h-3"/> Codex node
        </button>
        <button type="button" onClick={() => setSource("material")}
                 className={`tag ${sourceKind === "material" ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                 data-testid={`roll-entry-src-material-${idx}`}>
          <Dices className="w-3 h-3"/> Material
        </button>
        <button type="button" onClick={() => setSource("body")}
                 className={`tag ${sourceKind === "body" ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                 data-testid={`roll-entry-src-body-${idx}`}>
          <Pencil className="w-3 h-3"/> Literal text
        </button>
      </div>

      {sourceKind === "reference" && (
        <select className="select" value={entry.reference_id || ""}
                 onChange={(e) => onChange({ reference_id: e.target.value })}
                 data-testid={`roll-entry-ref-pick-${idx}`}>
          <option value="">— pick a seeded reference —</option>
          {refLib.map((r) => (
            <option key={r.id} value={r.id}>{r.kind} · {r.name}</option>
          ))}
        </select>
      )}
      {sourceKind === "node" && (
        <select className="select" value={entry.node_id || ""}
                 onChange={(e) => onChange({ node_id: e.target.value })}
                 data-testid={`roll-entry-node-pick-${idx}`}>
          <option value="">— pick a codex node —</option>
          {nodes.map((n) => (
            <option key={n.id} value={n.id}>{n.node_kind || n.type} · {n.title || n.name}</option>
          ))}
        </select>
      )}
      {sourceKind === "material" && (
        <select className="select" value={entry.material_id || ""}
                 onChange={(e) => onChange({ material_id: e.target.value })}
                 data-testid={`roll-entry-material-pick-${idx}`}>
          <option value="">— pick a material —</option>
          {materials.map((m) => (
            <option key={m.id} value={m.id}>{m.tier} · {m.rarity} · {m.name}</option>
          ))}
        </select>
      )}
      {sourceKind === "body" && (
        <textarea className="input text-xs w-full" rows={2}
                   value={entry.body}
                   onChange={(e) => onChange({ body: e.target.value })}
                   placeholder="Deliberate literal body — authored, not silently drifting."
                   data-testid={`roll-entry-body-${idx}`}/>
      )}
    </div>
  );
}
