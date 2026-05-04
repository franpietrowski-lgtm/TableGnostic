// Extracted from ReferenceEditor.jsx in V6.10 refactor.
// Composer for a Power Bundle's components (Attribute/Skill/Defect/Enhancement/Limiter).
// Recomputes net CP cost via `/api/reference/estimate-bundle-cost` on every change.
import React from "react";
import { Plus, X } from "lucide-react";
import { api, formatApiErrorDetail } from "../../lib/api";

function PowerBundleEditor({ row, onChange }) {
  const comps = row.fields?.components || [];
  const [estimate, setEstimate] = React.useState(null);
  const [err, setErr] = React.useState("");

  // V6.25 — Universal Power Bundle Architecture: this editor also mounts
  // on Custom Attributes / Skills so modifiers can be attached. Re-label
  // the header in that context ("Attached Modifiers") since the list no
  // longer represents a multi-component bundle — it's ONE base mechanic
  // plus ranked enhancements / limiters / defects.
  const isAttached = (row.kind === "attribute" || row.kind === "skill");
  const headerLabel = isAttached ? "Attached Modifiers" : "Bundle Components";
  const helperText = isAttached
    ? "Attach limiters / defects / enhancements / size mods to this base "
      + "mechanic. The CP math flows straight to the character sheet."
    : "Each component contributes to the bundle's net CP cost — use this "
      + "to keep \"Fireball-like\" bundles balanced against equivalent "
      + "D&D spell slots.";

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.post("/reference/estimate-bundle-cost",
          { components: comps });
        if (!cancelled) setEstimate(data);
      } catch (e) {
        if (!cancelled) setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    })();
    return () => { cancelled = true; };
  }, [JSON.stringify(comps)]);

  const setComps = (next) => onChange({ ...row,
    fields: { ...(row.fields || {}), components: next } });
  const addComp = () => setComps([...comps,
    { kind: "attribute", name: "", cost_per_level: 0, level: 1,
      points_per_rank: 0, rank: 0, refund: 0, note: "" }]);
  const patch = (i, p) => setComps(comps.map((c, j) => j === i ? { ...c, ...p } : c));
  const drop = (i) => setComps(comps.filter((_, j) => j !== i));

  return (
    <div className="border border-gold/20 rounded-sm p-3 bg-gold/5 space-y-2"
         data-testid="reference-bundle-editor">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div className="label-ref">{headerLabel}</div>
        <div className="text-[10px] text-mist italic">
          {helperText}
        </div>
      </div>
      {comps.length === 0 && (
        <div className="text-[11px] text-mist italic">No components yet. Click + to add one.</div>
      )}
      <div className="space-y-2">
        {comps.map((c, i) => (
          <div key={i} className="grid grid-cols-1 sm:grid-cols-[120px_1fr_90px_90px_90px_24px] gap-2 items-center"
               data-testid={`reference-bundle-comp-${i}`}>
            <select className="select select-sm" value={c.kind}
                    onChange={(e) => patch(i, { kind: e.target.value })}>
              <option value="attribute">Attribute</option>
              <option value="skill">Skill Group</option>
              <option value="defect">Defect</option>
              <option value="enhancement">Enhancement</option>
              <option value="limiter">Limiter</option>
            </select>
            <input className="input" placeholder="Name (e.g. Weapon)"
                   value={c.name} onChange={(e) => patch(i, { name: e.target.value })}/>
            {c.kind !== "defect" ? (
              <input className="input" type="number" step="0.5" min={0}
                     placeholder="Cost/Lvl"
                     value={c.cost_per_level}
                     onChange={(e) => patch(i, { cost_per_level: Number(e.target.value) || 0 })}/>
            ) : (
              <input className="input" type="number" min={0}
                     placeholder="Pts/Rank"
                     value={c.points_per_rank}
                     onChange={(e) => patch(i, { points_per_rank: Number(e.target.value) || 0 })}/>
            )}
            <input className="input" type="number" min={0}
                   placeholder={c.kind === "defect" ? "Rank" : "Level"}
                   value={c.kind === "defect" ? c.rank : c.level}
                   onChange={(e) => patch(i, c.kind === "defect"
                     ? { rank: Number(e.target.value) || 0 }
                     : { level: Number(e.target.value) || 0 })}/>
            <input className="input" type="number" min={0}
                   placeholder="Refund"
                   title="Item-defect refund for this component (attribute-only)."
                   value={c.refund || 0}
                   disabled={c.kind !== "attribute"}
                   onChange={(e) => patch(i, { refund: Number(e.target.value) || 0 })}/>
            <button onClick={() => drop(i)} className="text-ember/70 hover:text-ember p-1"
                    aria-label="Remove component">
              <X className="w-3 h-3"/>
            </button>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between flex-wrap gap-2 pt-2 border-t border-gold/15">
        <button onClick={addComp} className="btn btn-ghost text-xs"
                data-testid="reference-bundle-add-comp">
          <Plus className="w-3 h-3"/> Add component
        </button>
        {estimate && (
          <div className="text-[11px] font-ui"
               data-testid="reference-bundle-estimate">
            <span className="text-mist">Net CP cost: </span>
            <span className={estimate.total_cost < 0 ? "text-arcane" : "text-gold-bright"}>
              {estimate.total_cost}
            </span>
            <span className="text-mist"> · {estimate.component_count} component{estimate.component_count === 1 ? "" : "s"}</span>
          </div>
        )}
      </div>
      {err && <div className="text-ember text-[11px]">{err}</div>}
    </div>
  );
}

export default PowerBundleEditor;
