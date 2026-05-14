/**
 * CraftingServicePanel — V6.25.26
 *
 * GM authoring surface for crafting materials. Three tiers:
 *   • Raw      — ore, hide, flowers, roots, bark, nectar, etc.
 *   • Refined  — raw → ingot, polished gem, dye, tanned hide.
 *   • Assembled— refined → hilt, ring, jewellery, ale, finished armor.
 *
 * Each tier has its own list with a + Add button. Refined/Assembled rows
 * can cite ingredient_ids — a recipe trace that the Director's Console
 * loot designer + character sheet inventory will consume downstream.
 */
import React, { useEffect, useState, useMemo } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Hammer, Plus, Trash2, X, Save, Pickaxe, Gem, Wrench } from "lucide-react";

const TIERS = [
  { key: "raw",       label: "Materials · Raw",
    Icon: Pickaxe, blurb: "Off-the-ground / out-of-the-ground / off-an-entity. Ore, hide, flowers, roots, bark, nectar, teeth, hair." },
  { key: "refined",   label: "Materials · Refined",
    Icon: Gem,     blurb: "Raw transformed: ore→ingot, gem→polished cut gem, flower→dye, hide→tanned leather." },
  { key: "assembled", label: "Materials · Assembled",
    Icon: Wrench,  blurb: "Refined transformed into a finished good: ingot→hilt/blade/ring, jewelry, nectar→ale, leather→armor." },
];


export default function CraftingServicePanel({ campId, isGm }) {
  const [rows, setRows] = useState([]);
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const refresh = async () => {
    try {
      const r = await api.get(`/campaigns/${campId}/materials`);
      setRows(r.data?.rows || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };
  useEffect(() => { if (campId) refresh(); /* eslint-disable-next-line */ }, [campId]);

  const beginNew = (tier) => setDraft({
    tier, name: "", summary: "", rarity: "common",
    ingredient_ids: [], yields: 1, fields: {}, also_to_codex: false,
  });
  const beginEdit = (m) => setDraft({ ...m });
  const cancel = () => setDraft(null);

  const save = async () => {
    setBusy(true); setErr("");
    try {
      const payload = { ...draft };
      const url = draft.id
        ? `/campaigns/${campId}/materials/${draft.id}`
        : `/campaigns/${campId}/materials`;
      const m = draft.id ? "patch" : "post";
      await api[m](url, payload);
      setDraft(null);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const remove = async (mid) => {
    if (!window.confirm("Delete this material?")) return;
    await api.delete(`/campaigns/${campId}/materials/${mid}`);
    refresh();
  };

  const grouped = useMemo(() => {
    const g = { raw: [], refined: [], assembled: [] };
    rows.forEach((r) => { (g[r.tier] = g[r.tier] || []).push(r); });
    return g;
  }, [rows]);

  return (
    <div className="card-mystic p-4 space-y-4" data-testid="crafting-service-panel">
      <div className="flex items-baseline justify-between flex-wrap gap-2 border-b border-gold/10 pb-2">
        <div>
          <div className="h-arcane text-sm flex items-center gap-2">
            <Hammer className="w-4 h-4"/> Crafting Service · ⌥C
          </div>
          <div className="text-[11px] text-mist italic">
            Three-tier materials catalogue · feeds Director's Console loot tables
            + character-sheet inventory + codex (when ticked).
          </div>
        </div>
      </div>

      {err && <div className="text-ember text-xs" data-testid="crafting-error">{err}</div>}

      {TIERS.map((tier) => {
        const T = tier.Icon;
        const list = grouped[tier.key] || [];
        return (
          <div key={tier.key} className="space-y-1.5"
               data-testid={`crafting-tier-${tier.key}`}>
            <div className="flex items-baseline justify-between flex-wrap gap-2">
              <div>
                <div className="label-ref flex items-center gap-2">
                  <T className="w-3 h-3"/> {tier.label}
                </div>
                <div className="text-[10px] text-mist italic">{tier.blurb}</div>
              </div>
              {isGm && (
                <button onClick={() => beginNew(tier.key)}
                        className="btn btn-ghost text-[10px]"
                        data-testid={`crafting-add-${tier.key}`}>
                  <Plus className="w-3 h-3"/> Add {tier.key}
                </button>
              )}
            </div>
            {list.length === 0 && (
              <div className="text-[10px] text-mist italic"
                   data-testid={`crafting-empty-${tier.key}`}>
                No {tier.key} materials yet.
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {list.map((m) => (
                <MaterialCard key={m.id} m={m} allRows={rows}
                                onEdit={() => beginEdit(m)}
                                onRemove={() => remove(m.id)}
                                isGm={isGm}/>
              ))}
            </div>
          </div>
        );
      })}

      {draft && (
        <MaterialEditor draft={draft} setDraft={setDraft}
                          allRows={rows}
                          busy={busy} onSave={save} onCancel={cancel}/>
      )}
    </div>
  );
}


function MaterialCard({ m, allRows, onEdit, onRemove, isGm }) {
  const ingredients = (m.ingredient_ids || [])
    .map((id) => allRows.find((r) => r.id === id))
    .filter(Boolean);
  return (
    <div className="border border-gold/10 rounded-sm p-2 bg-void/30 text-[11px]"
         data-testid={`material-row-${m.id}`}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-parchment font-display">{m.name}</span>
        <span className="text-[9px] text-arcane-light uppercase tracking-widest">{m.rarity}</span>
      </div>
      {m.summary && <div className="text-[10px] text-mist italic mt-0.5">{m.summary}</div>}
      {ingredients.length > 0 && (
        <div className="text-[9px] text-arcane-light mt-1">
          ← {ingredients.map((i) => i.name).join(" + ")}
        </div>
      )}
      {m.yields > 1 && (
        <div className="text-[9px] text-mist mt-0.5">yields ×{m.yields}</div>
      )}
      {isGm && (
        <div className="mt-1 flex gap-1.5 justify-end">
          <button onClick={onEdit} className="text-mist hover:text-parchment text-[10px]"
                  data-testid={`material-edit-${m.id}`}>edit</button>
          <button onClick={onRemove} className="text-mist hover:text-ember"
                  data-testid={`material-delete-${m.id}`}>
            <Trash2 className="w-3 h-3"/>
          </button>
        </div>
      )}
    </div>
  );
}


function MaterialEditor({ draft, setDraft, allRows, busy, onSave, onCancel }) {
  // Refined cites Raw; Assembled cites Refined + Raw.
  const eligibleIngredients = allRows.filter((r) => {
    if (draft.tier === "refined")  return r.tier === "raw";
    if (draft.tier === "assembled") return r.tier === "refined" || r.tier === "raw";
    return false;
  });
  const toggleIngredient = (id) => {
    const cur = new Set(draft.ingredient_ids || []);
    cur.has(id) ? cur.delete(id) : cur.add(id);
    setDraft({ ...draft, ingredient_ids: Array.from(cur) });
  };

  return (
    <div className="fixed inset-0 z-[8800] bg-void/80 backdrop-blur-sm flex items-center justify-center p-4"
         onClick={onCancel} data-testid="material-editor-modal">
      <div className="card-mystic p-5 max-w-md w-full max-h-[90vh] overflow-y-auto space-y-3 relative"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={onCancel}
                 className="absolute top-2 right-2 text-mist hover:text-parchment">
          <X className="w-4 h-4"/>
        </button>
        <div className="h-arcane text-sm">
          {draft.id ? "Edit" : "Author"} {draft.tier} material
        </div>
        <div>
          <div className="label-ref">Name</div>
          <input className="input text-sm w-full" value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  placeholder={draft.tier === "raw" ? "Iron Ore"
                    : draft.tier === "refined" ? "Iron Ingot" : "Iron Sword Hilt"}
                  data-testid="material-name"/>
        </div>
        <div>
          <div className="label-ref">Summary</div>
          <textarea className="input text-sm w-full" rows={2}
                     value={draft.summary}
                     onChange={(e) => setDraft({ ...draft, summary: e.target.value })}
                     placeholder="One-line description for the table."
                     data-testid="material-summary"/>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="label-ref">Rarity</div>
            <select className="select" value={draft.rarity}
                     onChange={(e) => setDraft({ ...draft, rarity: e.target.value })}
                     data-testid="material-rarity">
              {["common", "uncommon", "rare", "very_rare", "legendary"].map((r) =>
                <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <div className="label-ref">Yields per craft</div>
            <input type="number" min={1} max={20} value={draft.yields}
                    onChange={(e) => setDraft({ ...draft, yields: +e.target.value || 1 })}
                    className="input text-center"
                    data-testid="material-yields"/>
          </div>
        </div>
        {eligibleIngredients.length > 0 && (
          <div>
            <div className="label-ref">Ingredients (recipe)</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {eligibleIngredients.map((r) => {
                const on = (draft.ingredient_ids || []).includes(r.id);
                return (
                  <button key={r.id} type="button"
                           onClick={() => toggleIngredient(r.id)}
                           className={`tag text-[10px] ${on ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                           data-testid={`material-ingredient-${r.id}`}>
                    {r.name} <span className="text-[9px] text-arcane-light">· {r.tier}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
        {!draft.id && (
          <label className="flex items-center gap-2 text-[11px] text-parchment cursor-pointer">
            <input type="checkbox"
                    checked={!!draft.also_to_codex}
                    onChange={(e) => setDraft({ ...draft, also_to_codex: e.target.checked })}
                    data-testid="material-also-to-codex"/>
            <span>
              <b>Also submit to Codex</b>
              <span className="text-mist italic ml-1">— mirror as a codex node.</span>
            </span>
          </label>
        )}
        <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
          <button onClick={onCancel} className="btn btn-ghost text-xs">Cancel</button>
          <button onClick={onSave} disabled={busy || !draft.name?.trim()}
                   className="btn btn-primary text-xs"
                   data-testid="material-save">
            <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
