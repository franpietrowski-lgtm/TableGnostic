/**
 * CostOverridesPanel — V6.25.33
 *
 * GM-only campaign panel. Lets the GM enter an override CP cost for any
 * canonical reference-mechanic entry: BESM attribute / defect / skill_group
 * / race_template / class_template, or Anime 5E point-buy attribute /
 * heritage. The level + effective level + mechanics stay intact; only
 * the price the player pays from the CP bank changes. Single number
 * replaces the canon cost outright.
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Plus, Trash2, Save, Edit3 } from "lucide-react";
import { api, formatApiErrorDetail } from "../lib/api";

const KIND_OPTIONS_BESM = [
  { v: "attribute",      l: "Attribute (per level)" },
  { v: "defect",         l: "Defect (per rank)" },
  { v: "skill_group",    l: "Skill Group (per level)" },
  { v: "race_template",  l: "Race Template (total)" },
  { v: "class_template", l: "Class Template (total)" },
];
const KIND_OPTIONS_ANIME = [
  { v: "point_buy_attribute", l: "Point-Buy Attribute (per level)" },
  { v: "defect",              l: "Defect (per rank)" },
  { v: "heritage",            l: "Heritage (total)" },
  { v: "race_template",       l: "Race Template (total)" },
  { v: "class_template",      l: "Class Template (total)" },
];


export default function CostOverridesPanel({ campId, systemId }) {
  const [overrides, setOverrides] = useState([]);
  const [refData, setRefData] = useState(null);
  const [adding, setAdding] = useState(false);
  const [err, setErr] = useState("");

  const reload = useCallback(async () => {
    if (!campId) return;
    const r = await api.get(`/campaigns/${campId}/cost-overrides`).then((x) => x.data).catch(() => null);
    setOverrides(r?.overrides || []);
  }, [campId]);

  useEffect(() => { reload(); }, [reload]);

  // Pull the reference catalogue so we can offer a name auto-complete
  // based on what the campaign's system actually exposes.
  useEffect(() => {
    const url = (systemId && systemId !== "besm-4e")
      ? `/systems/${systemId}/reference`
      : "/besm/reference";
    api.get(url).then((r) => setRefData(r.data)).catch(() => {});
  }, [systemId]);

  const kindOptions = (systemId === "anime-5e") ? KIND_OPTIONS_ANIME : KIND_OPTIONS_BESM;

  const namesByKind = useMemo(() => {
    const r = refData || {};
    const get = (rows, key = "name") =>
      (rows || []).map((x) => (typeof x === "string" ? x : x[key])).filter(Boolean).sort();
    return {
      attribute:           get(r.attributes),
      defect:              get(r.defects),
      skill_group:         get(r.skill_groups),
      race_template:       get(r.race_templates),
      class_template:      get(r.class_templates),
      point_buy_attribute: get(r.point_buy_attributes),
      heritage:            get(r.heritages || r.races),
    };
  }, [refData]);

  return (
    <div className="card-mystic p-4" data-testid="cost-overrides-panel">
      <div className="flex items-baseline justify-between gap-3 mb-3 flex-wrap">
        <div>
          <div className="font-display text-parchment text-base">Cost Overrides</div>
          <div className="text-[11px] text-mist mt-0.5 max-w-xl">
            Replace the canon CP cost of any reference-mechanic entry for
            <strong className="text-parchment"> this campaign only</strong>.
            Level &amp; mechanics stay intact — only the price changes.
            Set the cost to <strong className="text-parchment">0</strong> to
            grant an entry as a starting perk and let the player keep their
            full CP budget for further customisation.
          </div>
        </div>
        <button type="button" onClick={() => setAdding(true)}
                className="btn btn-primary text-xs"
                data-testid="cost-override-add-btn">
          <Plus className="w-3 h-3"/> Add Override
        </button>
      </div>

      {err && <div className="text-ember text-sm mb-2" data-testid="cost-override-error">{err}</div>}

      {adding && (
        <OverrideEditor campId={campId} kindOptions={kindOptions}
                        namesByKind={namesByKind}
                        onCancel={() => { setAdding(false); setErr(""); }}
                        onSaved={async () => { setAdding(false); setErr(""); await reload(); }}
                        onError={setErr}/>
      )}

      {overrides.length === 0 && !adding && (
        <div className="text-mist text-sm italic">
          No overrides yet. The campaign uses canon costs from the rulebook.
        </div>
      )}

      {overrides.length > 0 && (
        <ul className="space-y-2 mt-2">
          {overrides.map((o) => (
            <OverrideRow key={o.id} ov={o} campId={campId}
                         kindOptions={kindOptions}
                         namesByKind={namesByKind}
                         onChanged={reload}
                         onError={setErr}/>
          ))}
        </ul>
      )}
    </div>
  );
}


function OverrideEditor({ campId, kindOptions, namesByKind,
                          existing, onCancel, onSaved, onError }) {
  const [kind, setKind] = useState(existing?.kind || kindOptions[0].v);
  const [name, setName] = useState(existing?.name || "");
  const [cost, setCost] = useState(existing?.override_cost ?? 0);
  const [note, setNote] = useState(existing?.note || "");
  const [saving, setSaving] = useState(false);

  const namePool = namesByKind[kind] || [];

  const save = async () => {
    onError("");
    if (!name.trim()) { onError("Name is required."); return; }
    setSaving(true);
    try {
      await api.put(`/campaigns/${campId}/cost-overrides`, {
        kind, name: name.trim(), override_cost: Number(cost), note,
      });
      await onSaved();
    } catch (e) {
      onError(formatApiErrorDetail(e?.response?.data?.detail, e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border border-gold/20 rounded-sm p-3 mb-2 bg-void/40"
         data-testid="cost-override-editor">
      <div className="grid grid-cols-1 md:grid-cols-[180px_1fr_120px] gap-2">
        <div>
          <label className="label-ref block mb-1">Kind</label>
          <select className="select" value={kind} onChange={(e) => setKind(e.target.value)}
                  disabled={!!existing}
                  data-testid="cost-override-kind">
            {kindOptions.map((o) => (
              <option key={o.v} value={o.v}>{o.l}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label-ref block mb-1">Name</label>
          <input list="cost-override-name-pool" type="text"
                 className="input"
                 value={name} onChange={(e) => setName(e.target.value)}
                 disabled={!!existing}
                 placeholder="Type or pick from list…"
                 data-testid="cost-override-name"/>
          <datalist id="cost-override-name-pool">
            {namePool.map((n) => <option key={n} value={n}/>)}
          </datalist>
        </div>
        <div>
          <label className="label-ref block mb-1">CP Cost</label>
          <input type="number" step="0.5" className="input text-center"
                 value={cost} onChange={(e) => setCost(e.target.value)}
                 data-testid="cost-override-cost"/>
        </div>
      </div>
      <div className="mt-2">
        <label className="label-ref block mb-1">House-rule note (optional)</label>
        <input type="text" className="input" value={note} onChange={(e) => setNote(e.target.value)}
               placeholder="Why this campaign deviates from canon…"
               data-testid="cost-override-note"/>
      </div>
      <div className="mt-3 flex gap-2">
        <button type="button" onClick={save} disabled={saving}
                className="btn btn-primary text-xs"
                data-testid="cost-override-save-btn">
          <Save className="w-3 h-3"/> {saving ? "Saving…" : "Save Override"}
        </button>
        <button type="button" onClick={onCancel}
                className="btn btn-ghost text-xs"
                data-testid="cost-override-cancel-btn">
          Cancel
        </button>
      </div>
    </div>
  );
}


function OverrideRow({ ov, campId, kindOptions, namesByKind, onChanged, onError }) {
  const [editing, setEditing] = useState(false);
  const [cost, setCost] = useState(ov.override_cost);
  const [note, setNote] = useState(ov.note || "");
  const [saving, setSaving] = useState(false);

  if (editing) {
    return (
      <li className="border border-gold/20 rounded-sm p-2 bg-void/40"
          data-testid={`cost-override-${ov.id}-edit`}>
        <div className="text-[11px] text-mist mb-1">
          {ov.kind} · <span className="text-parchment">{ov.name}</span>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="label-ref block mb-1 text-[9px]">CP cost</label>
            <input type="number" step="0.5" className="input w-24 text-center"
                   value={cost} onChange={(e) => setCost(e.target.value)}/>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="label-ref block mb-1 text-[9px]">Note</label>
            <input type="text" className="input" value={note}
                   onChange={(e) => setNote(e.target.value)}/>
          </div>
          <button type="button" disabled={saving} className="btn btn-primary text-xs"
                  onClick={async () => {
                    setSaving(true);
                    try {
                      await api.patch(`/campaigns/${campId}/cost-overrides/${ov.id}`,
                                       { override_cost: Number(cost), note });
                      setEditing(false);
                      await onChanged();
                    } catch (e) {
                      onError(formatApiErrorDetail(e?.response?.data?.detail, e));
                    } finally {
                      setSaving(false);
                    }
                  }}>
            <Save className="w-3 h-3"/> Save
          </button>
          <button type="button" className="btn btn-ghost text-xs"
                  onClick={() => { setEditing(false); setCost(ov.override_cost); setNote(ov.note || ""); }}>
            Cancel
          </button>
        </div>
      </li>
    );
  }

  return (
    <li className="border border-gold/15 rounded-sm p-2 flex items-center justify-between gap-3 flex-wrap"
        data-testid={`cost-override-${ov.id}`}>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] uppercase tracking-widest text-gold/60">{ov.kind}</div>
        <div className="font-display text-parchment text-base truncate">{ov.name}</div>
        {ov.note && <div className="text-[11px] text-mist italic mt-0.5">{ov.note}</div>}
      </div>
      <div className="text-right">
        <div className="text-[10px] uppercase tracking-widest text-gold/60">Cost</div>
        <div className={`font-display text-base ${Number(ov.override_cost) === 0 ? "text-gold-bright" : "text-parchment"}`}>
          {ov.override_cost} CP
        </div>
      </div>
      <div className="flex gap-1">
        <button type="button" onClick={() => setEditing(true)} className="btn btn-ghost text-xs"
                data-testid={`cost-override-${ov.id}-edit-btn`}>
          <Edit3 className="w-3 h-3"/>
        </button>
        <button type="button" className="btn btn-ghost text-xs text-ember"
                data-testid={`cost-override-${ov.id}-delete-btn`}
                onClick={async () => {
                  if (!window.confirm(`Delete override for "${ov.name}"?`)) return;
                  try {
                    await api.delete(`/campaigns/${campId}/cost-overrides/${ov.id}`);
                    await onChanged();
                  } catch (e) {
                    onError(formatApiErrorDetail(e?.response?.data?.detail, e));
                  }
                }}>
          <Trash2 className="w-3 h-3"/>
        </button>
      </div>
    </li>
  );
}
