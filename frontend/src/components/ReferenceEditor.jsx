import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, X, BookOpen, AlertCircle, Edit3, Save } from "lucide-react";
import PowerBundleTemplatePicker from "./referenceEditor/PowerBundleTemplatePicker";
import SpellConversionAtlas from "./referenceEditor/SpellConversionAtlas";
import PowerBundleEditor from "./referenceEditor/PowerBundleEditor";
import ConvertReferenceButton from "./ConvertReferenceButton";

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
  companion: "Companions",
  attribute: "Attributes", skill: "Skills", defect: "Defects",
  // V6.3 additions — expanded cross-system authorable kinds
  enhancement: "Enhancements",
  limiter: "Limiters",
  power_pack: "Power Packs",
  power_bundle: "Power Bundles",
  spell: "Spells",
  feat: "Feats",
  background: "Backgrounds",
  race_trait: "Race Traits",
  class_feature: "Class Features",
  cypher_ability: "Type/Focus Abilities",
  cypher_item: "Artifacts",
  artifact: "Artifacts",
  descriptor: "Descriptors",
  focus: "Foci",
  type: "Types",
};
// V6.25 — `custom` kind removed from the Atelier Reference Editor.
// Custom / House Rules now live exclusively in the Campaign page's
// Custom Rules tab (CampaignDetail.CustomTab) to avoid the surface
// redundancy and deepen its homebrew Race/Class/Size/Stat wiring.
// System-aware label & ordering overrides. The backend kind enum stays the
// same (8 universal kinds), but we re-label them per active system so the
// GM sees rule-set-native vocabulary instead of always-Tri-Stat headings.
//
// E.g. "Defects" → "Cyphers" for Cypher campaigns (cyphers ARE one-shot
// hindrances/boons in mechanic terms), "Attributes" → "Type Abilities",
// "Companions" → "Foci". For D&D the same reuse pattern: "Attributes" →
// "Class Features", "Defects" → "Drawbacks", "Companions" → "Followers".
//
// This is purely cosmetic — it doesn't fork the data shape, so a PC
// migrating between systems doesn't break.
const SYSTEM_KIND_LABELS = {
  "cypher": {
    weapon: "Weapons", armor: "Armor", item: "Items / Equipment",
    companion: "Foci",          // Cypher characters PICK a focus, not a companion
    attribute: "Types",          // The 6 Cypher Types (Warrior / Adept / …)
    skill: "Skills (Trained)",
    defect: "Cyphers",          // Single-use mechanic items
  },
  "dnd-5e": {
    weapon: "Weapons", armor: "Armor", item: "Adventuring Gear / Magic Items",
    companion: "Followers / Mounts",
    attribute: "Class Features", // Mechanical features players can select
    skill: "Skills", defect: "Drawbacks / Backgrounds",
  },
  "anime-5e": {
    weapon: "Weapons", armor: "Armor", item: "Items / Cards",
    companion: "Companions / Mounts",
    attribute: "Tri-Stat Attributes",
    skill: "Skills", defect: "Defects",
  },
  "besm-4e": {
    weapon: "Weapons", armor: "Armor", item: "Items",
    companion: "Companions",
    attribute: "Attributes", skill: "Skills", defect: "Defects",
  },
};
const KIND_KEYS = Object.keys(KIND_LABELS);
// V6.12 — visual grouping of the 22 kinds into 5 thematic categories so
// authors don't face a 22-button wall (per DESIGN_AUDIT P0 #5). Each
// group renders as its own strip with a category header.
const KIND_GROUPS = [
  { key: "mechanics",      label: "Mechanics",       color: "#C8A34A",
    kinds: ["attribute", "skill", "defect", "enhancement", "limiter"] },
  { key: "bundles",        label: "Bundles & Packs", color: "#7A4FBF",
    kinds: ["power_pack", "power_bundle"] },
  { key: "content",        label: "Content",         color: "#E03A8E",
    kinds: ["spell", "feat", "background", "class_feature", "race_trait"] },
  { key: "cypher",         label: "Cypher",          color: "#3FAA62",
    kinds: ["type", "descriptor", "focus", "cypher_ability", "cypher_item", "artifact"] },
  { key: "items_rules",    label: "Items & Rules",   color: "#3F8FAA",
    kinds: ["weapon", "armor", "item", "companion"] },
];
// Resolve a kind to its group (for category-header styling on the Row).
const GROUP_OF_KIND = {};
for (const g of KIND_GROUPS) for (const k of g.kinds) GROUP_OF_KIND[k] = g;
// V6.3 — system-aware tab ordering. Only expose kinds that make mechanical
// sense for the active system; avoids a BESM GM having to scroll past 15
// Cypher-only kinds to find Attributes.
const SYSTEM_KIND_ORDER = {
  "besm-4e": ["attribute", "skill", "defect", "enhancement", "limiter",
              "power_pack", "power_bundle", "weapon", "armor", "item",
              "companion"],
  "anime-5e": ["class_feature", "race_trait", "background", "spell", "feat",
               "skill", "attribute", "defect", "enhancement", "limiter",
               "power_pack", "power_bundle", "weapon", "armor", "item",
               "companion"],
  "dnd-5e": ["class_feature", "race_trait", "background", "spell", "feat",
             "skill", "weapon", "armor", "item", "companion"],
  "cypher": ["type", "descriptor", "focus", "cypher_ability", "cypher_item",
             "artifact", "skill", "weapon", "armor", "item"],
};
// Kinds that flow back into the Character Builder's pickers — they expose
// extra structured inputs (cost_per_level / points_per_rank / category) so
// players can select them when forging a sheet.
const PLAYABLE_KINDS = new Set(["attribute", "skill", "defect",
  "enhancement", "limiter", "power_pack", "power_bundle",
  "spell", "feat", "background", "class_feature",
  "cypher_ability", "descriptor", "focus", "type"]);

export default function ReferenceEditor({ campaignId, isGm, systemId }) {
  const [tab, setTab] = useState("weapon");
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState("");
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  // V6.4 — Power Bundle template picker.
  const [showTemplates, setShowTemplates] = useState(false);
  // V6.5 — Spell Conversion Atlas (read-only reference).
  const [showAtlas, setShowAtlas] = useState(false);

  const refresh = async () => {
    try {
      const { data } = await api.get(`/campaigns/${campaignId}/reference?kind=${tab}`);
      setRows(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };
  useEffect(() => { refresh(); }, [campaignId, tab]);

  // V6.13 — Alt+M / Alt+B / Alt+C / Alt+Y / Alt+I keyboard shortcuts jump
  // to the first visible kind of each group. Honours SYSTEM_KIND_ORDER so
  // besm-only authors never get trapped in the Content / Cypher groups.
  useEffect(() => {
    const groupKeyByHotkey = {
      m: "mechanics", b: "bundles", c: "content",
      y: "cypher", i: "items_rules",
    };
    const onKey = (ev) => {
      if (!ev.altKey || ev.metaKey || ev.ctrlKey) return;
      const target = ev.target;
      const isEditable = target && (target.tagName === "INPUT"
        || target.tagName === "TEXTAREA" || target.isContentEditable);
      if (isEditable) return;
      const gk = groupKeyByHotkey[ev.key?.toLowerCase()];
      if (!gk) return;
      const ordered = SYSTEM_KIND_ORDER[systemId] || KIND_KEYS;
      const group = KIND_GROUPS.find((g) => g.key === gk);
      if (!group) return;
      const firstVisible = group.kinds.find((k) => ordered.includes(k));
      if (firstVisible) {
        ev.preventDefault();
        setTab(firstVisible);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [systemId]);

  const blank = () => ({
    kind: tab, name: "", summary: "", page: "",
    book: systemId || "besm-4e", cost: "", fields: {},
    also_to_codex: false,
  });

  const save = async (row) => {
    setBusy(true); setErr("");
    try {
      const payload = { ...row, page: row.page === "" ? null : Number(row.page) };
      const alsoCodex = !!row.also_to_codex;
      delete payload.also_to_codex;  // server schema doesn't expect this
      let saved;
      if (row.id) {
        const r = await api.patch(`/campaigns/${campaignId}/reference/${row.id}`, payload);
        saved = r.data;
      } else {
        const r = await api.post(`/campaigns/${campaignId}/reference`, payload);
        saved = r.data;
      }
      // V6.25.26 — When the GM ticked "also submit to Codex", we mirror
      // the entry as a codex node. The classifier picks `node_kind` and
      // World-Tree section automatically from name + summary heuristics.
      if (alsoCodex && saved && !row.id) {
        try {
          await api.post(`/campaigns/${campaignId}/codex-nodes`, {
            title: saved.name,
            name: saved.name,
            summary: saved.summary || "",
            content: saved.summary || "",
            type: "concept",
            visibility: "gm",
            tags: ["from-reference", saved.kind],
            fields: { source_reference_id: saved.id, source_kind: saved.kind },
          });
        } catch (codexErr) {
          // Don't fail the whole save — surface it but the reference is saved.
          setErr("Reference saved, but Codex mirror failed: " +
                  (formatApiErrorDetail(codexErr.response?.data?.detail) || codexErr.message));
        }
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

  // Per-system label resolution — reuse the universal kinds but show
  // system-native vocabulary on the tabs and the "Add X" button.
  const labels = SYSTEM_KIND_LABELS[systemId] || SYSTEM_KIND_LABELS["besm-4e"];
  const labelOf = (k) => labels[k] || KIND_LABELS[k];

  return (
    <div className="card-mystic p-4" data-testid="reference-editor"
         data-system={systemId}>
      <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
        <div>
          <div className="label-ref flex items-center gap-2"><BookOpen className="w-3 h-3"/> Reference Tables</div>
          <div className="text-[10px] text-mist/70 italic">
            {systemId === "cypher"
              ? "Per-campaign Cyphers · Foci · Types · Skills · Items · House Rules. Mechanic-only, page-cited."
              : systemId === "dnd-5e"
              ? "Per-campaign Class Features · Backgrounds · Items · Followers · House Rules. Mechanic-only, page-cited."
              : "Per-campaign Tri-Stat references — Attributes / Defects / Items / Companions / House Rules."}
          </div>
        </div>
        {isGm && !draft && (
          <div className="flex items-center gap-2 flex-wrap">
            {(tab === "power_bundle" || tab === "power_pack") && (
              <button onClick={() => setShowTemplates(true)}
                      className="btn btn-ghost text-xs"
                      data-testid="reference-import-templates-btn"
                      title="Browse the seeded D&D-spell-mimic Power Bundle templates.">
                <BookOpen className="w-3 h-3"/> Import from templates
              </button>
            )}
            {systemId === "anime-5e" && (
              <button onClick={() => setShowAtlas(true)}
                      className="btn btn-ghost text-xs"
                      data-testid="reference-open-atlas-btn"
                      title="Anime 5E only: D&D spells & class abilities translated to BESM/Anime 5E Attributes with SRD citations.">
                <BookOpen className="w-3 h-3"/> Spell Conversion Atlas
              </button>
            )}
            <button onClick={() => setDraft(blank())} className="btn btn-primary text-xs"
                    data-testid="reference-add-btn">
              <Plus className="w-3 h-3"/> Add {String(labelOf(tab)).split(" ")[0]}
            </button>
          </div>
        )}
      </div>
      <div className="mb-3 border-b border-gold/10 pb-2 space-y-2"
           data-testid="reference-tabs">
        {KIND_GROUPS.map((g) => {
          const ordered = (SYSTEM_KIND_ORDER[systemId] || KIND_KEYS);
          const visible = g.kinds.filter((k) => ordered.includes(k));
          if (visible.length === 0) return null;
          const hotkey = { mechanics: "M", bundles: "B", content: "C",
                           cypher: "Y", items_rules: "I" }[g.key];
          return (
            <div key={g.key} className="flex items-center gap-2 flex-wrap"
                 data-testid={`reference-group-${g.key}`}>
              <div className="text-[9px] uppercase tracking-widest font-ui min-w-[84px]"
                   style={{ color: g.color }}
                   title={`${g.label} · ${visible.length} kind${visible.length === 1 ? "" : "s"} · shortcut Alt+${hotkey}`}>
                <span className="inline-block w-2 h-2 rounded-full mr-1.5 align-middle"
                      style={{ backgroundColor: g.color }}/>
                {g.label}
                <kbd className="ml-1.5 text-[8px] border border-gold/20 rounded-sm px-1 py-0 text-mist/60 normal-case tracking-normal"
                     title={`Jump to ${g.label} — Alt+${hotkey}`}>⌥{hotkey}</kbd>
              </div>
              <div className="flex flex-wrap gap-1 flex-1">
                {visible.map((k) => (
                  <button key={k} onClick={() => setTab(k)}
                          className={`text-[10px] px-2 py-1 rounded-sm font-ui uppercase tracking-widest transition-colors border ${tab === k ? "bg-gold/15 text-gold-bright border-gold/30" : "border-transparent text-mist hover:bg-gold/5 hover:border-gold/20"}`}
                          style={tab === k ? { borderColor: g.color + "80", boxShadow: `inset 0 -2px 0 0 ${g.color}` } : undefined}
                          data-testid={`reference-tab-${k}`}>
                    {labelOf(k)}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      {err && <div className="text-ember text-xs mb-2">{err}</div>}
      {draft && (
        <Row row={draft} onChange={setDraft} onSave={save} onCancel={() => setDraft(null)}
             busy={busy} systemId={systemId} editing/>
      )}
      {rows.length === 0 && !draft && <div className="text-mist italic text-xs">No {String(labelOf(tab)).toLowerCase()} yet.</div>}
      <div className="space-y-2">
        {rows.map((r) => (
          <Row key={r.id} row={r} onChange={() => {}}
               onEdit={isGm ? () => setDraft(r) : null}
               onRemove={isGm ? () => remove(r.id) : null}/>
        ))}
      </div>
      {showTemplates && (
        <PowerBundleTemplatePicker
          campaignId={campaignId}
          onPick={(t) => {
            // Drop the template as the new draft. Shape it to the
            // Reference Editor's row schema.
            setDraft({
              ...blank(),
              kind: "power_bundle",
              name: t.name,
              summary: t.description,
              book: "Anime 5E Spell Conversions",
              fields: {
                components: (t.components || []).map((c) => ({
                  kind: c.kind, name: c.name,
                  cost_per_level: c.cost_per_level || 0,
                  level: c.level || 1,
                  points_per_rank: c.points_per_rank || 0,
                  rank: c.rank || 0,
                  refund: 0,
                  note: c.note || "",
                })),
                description: t.description,
                invocation: t.invocation,
                charges_max: t.charges_max,
                energy_cost: t.energy_cost,
                cooldown: t.cooldown,
                source_spell_name: t.source_spell_name,
                source_spell_level: t.source_spell_level,
                cost: t.cost,
                tags: t.tags,
              },
            });
            setShowTemplates(false);
          }}
          onClose={() => setShowTemplates(false)}/>
      )}
      {showAtlas && (
        <SpellConversionAtlas
          onClose={() => setShowAtlas(false)}
          onConvert={isGm ? async (slug) => {
            try {
              const { data: t } = await api.get(`/reference/spell-conversions/${slug}/as-power-bundle`);
              setTab("power_bundle");
              setDraft({
                ...blank(),
                kind: "power_bundle",
                name: t.name,
                summary: t.description,
                book: (t.references && t.references[0]) || "Anime 5E Spell Conversions",
                fields: {
                  components: t.components || [],
                  description: t.description,
                  invocation: t.invocation,
                  charges_max: t.charges_max,
                  energy_cost: t.energy_cost,
                  cooldown: t.cooldown,
                  source_spell_name: t.source_spell_name,
                  source_spell_level: t.source_spell_level,
                  cost: t.cost,
                  tags: t.tags,
                },
              });
              setShowAtlas(false);
            } catch (e) {
              setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
            }
          } : null}/>
      )}
    </div>
  );
}

function Row({ row, onChange, onSave, onCancel, busy, systemId, editing, onEdit, onRemove }) {
  const valid = row.page_validation;
  // Only BESM 4E uses the structured cost-per-level / points-per-rank /
  // category mechanic; D&D / Cypher / Anime 5E entries should NOT surface
  // those fields. We instead offer a system-shaped tier / level requirement
  // input that matches the host system.
  const isBesm = !systemId || systemId === "besm-4e";
  if (editing) {
    return (
      <div className="border border-gold/30 rounded-sm p-3 space-y-2 bg-gold/5"
           data-testid="reference-row-edit">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <input className="input col-span-2" placeholder="Name" value={row.name}
                 onChange={(e) => onChange({ ...row, name: e.target.value })}
                 data-testid="reference-input-name"/>
          <input className="input"
                 placeholder={isBesm ? "Cost (e.g. 2 pts/level)"
                   : systemId === "cypher" ? "Tier requirement (e.g. 2)"
                   : systemId === "dnd-5e" ? "Level requirement (e.g. 5)"
                   : systemId === "anime-5e" ? "Level / point cost"
                   : "Requirement"}
                 value={row.cost}
                 onChange={(e) => onChange({ ...row, cost: e.target.value })}
                 data-testid="reference-input-cost"/>
        </div>
        <textarea className="input min-h-[60px]" placeholder="Summary (mechanic-only — no rulebook prose)"
                  value={row.summary}
                  onChange={(e) => onChange({ ...row, summary: e.target.value })}
                  data-testid="reference-input-summary"/>
        {isBesm && PLAYABLE_KINDS.has(row.kind) && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 border border-gold/15 rounded-sm p-2 bg-gold/5"
               data-testid="reference-playable-fields">
            {(row.kind === "attribute" || row.kind === "skill"
              || row.kind === "enhancement" || row.kind === "limiter") && (
              <input className="input" type="number" step="0.5" min={0}
                     placeholder={row.kind === "enhancement" || row.kind === "limiter"
                       ? "Eff-level modifier (typically 1)"
                       : "Cost / Level (e.g. 4)"}
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
        {/* V6.3 — Power Pack / Power Bundle composer with live CP estimate.
            V6.25 — Universal Power Bundle Architecture: Custom Attributes &
            Skills ALSO expose the composer so a GM can attach limiters /
            defects / enhancements / size modifications directly to the base
            mechanic. The same CP math feeds the character sheet. */}
        {(row.kind === "power_pack" || row.kind === "power_bundle"
          || row.kind === "attribute" || row.kind === "skill") && (
          <>
            {(row.kind === "attribute" || row.kind === "skill") && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 border border-gold/15 rounded-sm p-2 bg-void/40"
                   data-testid="reference-size-mod-row">
                <input className="input" type="number" step="1"
                       placeholder="Size modifier (ranks, optional)"
                       title="BESM Size rank modification (e.g. +2 Large, -1 Small). Character sheet displays this next to the attribute."
                       value={row.fields?.size_modifier ?? ""}
                       onChange={(e) => onChange({ ...row,
                         fields: { ...(row.fields || {}),
                                   size_modifier: e.target.value === "" ? null : Number(e.target.value) } })}
                       data-testid="reference-input-size-modifier"/>
                <input className="input sm:col-span-2"
                       placeholder="Size note (e.g. 'Large aura reaches 10 ft')"
                       value={row.fields?.size_note || ""}
                       onChange={(e) => onChange({ ...row,
                         fields: { ...(row.fields || {}), size_note: e.target.value } })}
                       data-testid="reference-input-size-note"/>
              </div>
            )}
            <PowerBundleEditor row={row} onChange={onChange}/>
          </>
        )}
        {/* V6.25.12 — BESM 4E Weapon / Item composer.
            When authoring a `weapon` or `item` reference entry on a BESM
            campaign, surface the canonical Weapon Enhancements (p.135) /
            Weapon Limiters (p.142) pools plus the Item flavour pool.
            User flagged: weapons can also be items (sword) or NOT items
            (conjured fireball) — so item kind ALWAYS sees item mods, and
            weapon kind sees weapon mods + an "also an Item?" toggle that
            additionally reveals item mods + the half-cost rule. */}
        {isBesm && (row.kind === "weapon" || row.kind === "item") && (
          <BesmWeaponItemComposer row={row} onChange={onChange}/>
        )}
        {!isBesm && PLAYABLE_KINDS.has(row.kind) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 border border-gold/15 rounded-sm p-2 bg-gold/5"
               data-testid="reference-playable-fields">
            <input className="input" placeholder="Description / GM note (optional)"
                   value={row.fields?.description || ""}
                   onChange={(e) => onChange({ ...row,
                     fields: { ...(row.fields || {}), description: e.target.value } })}
                   data-testid="reference-input-description"/>
            {systemId === "cypher" && (
              <input className="input" placeholder="Genre tag (e.g. fantasy, scifi, horror, any)"
                     value={row.fields?.genre || ""}
                     onChange={(e) => onChange({ ...row,
                       fields: { ...(row.fields || {}), genre: e.target.value } })}
                     data-testid="reference-input-genre"/>
            )}
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
            {(SYSTEM_KIND_ORDER[systemId] || KIND_KEYS).map((k) => {
              const sysLabels = SYSTEM_KIND_LABELS[systemId] || SYSTEM_KIND_LABELS["besm-4e"];
              return <option key={k} value={k}>{sysLabels[k] || KIND_LABELS[k]}</option>;
            })}
          </select>
        </div>
        <div className="flex items-center justify-between gap-3 border-t border-gold/10 pt-2 flex-wrap">
          <label className="flex items-center gap-2 text-[11px] text-parchment cursor-pointer">
            <input type="checkbox"
                    checked={!!row.also_to_codex}
                    onChange={(e) => onChange({ ...row, also_to_codex: e.target.checked })}
                    disabled={!!row.id}
                    data-testid="reference-also-to-codex"/>
            <span>
              <b>Also submit to Codex</b>
              <span className="text-mist italic ml-1">
                — mirrors this entry as a codex node (auto-classified onto the World Tree).
                Available on first save only.
              </span>
            </span>
          </label>
          <div className="flex justify-end gap-2">
            <button onClick={onCancel} className="btn btn-ghost text-xs">Cancel</button>
            <button onClick={() => onSave(row)} disabled={busy || !row.name}
                    className="btn btn-primary text-xs" data-testid="reference-save-btn">
              <Save className="w-3 h-3"/> Save
            </button>
          </div>
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
          <ConvertReferenceButton entry={row} sourceSystem={systemId}/>
          {onRemove && <button onClick={onRemove} className="text-ember/70 hover:text-ember p-1"><X className="w-3 h-3"/></button>}
        </div>
      </div>
    </div>
  );
}

/** Static instructions card. Players see all but GM-Materials.
 *  System-aware — branches the "How to make a character" + "How to make a
 *  weapon/item" + "How to spend XP" steps per active ruleset so the GM
 *  doesn't see Tri-Stat point-buy instructions on a D&D 5E table.        */
export function InstructionsPanel({ isGm, systemId }) {
  const system = systemId || "besm-4e";
  return (
    <div className="card-mystic p-4" data-testid="instructions-panel"
         data-system={system}>
      <div className="label-ref mb-3 flex items-center gap-2">
        <BookOpen className="w-3 h-3"/> Quickstart Instructions
        <span className="text-[10px] text-mist normal-case tracking-normal italic">
          {system === "dnd-5e" && "(D&D 5E · class + slot)"}
          {system === "cypher" && "(Cypher · type/focus/descriptor)"}
          {system === "anime-5e" && "(Anime 5E · hybrid d20 + Tri-Stat)"}
          {system === "besm-4e" && "(BESM 4E · Tri-Stat point-buy)"}
        </span>
      </div>

      {/* ── Character creation ─────────────────────────────────────── */}
      {system === "dnd-5e" && (
        <Section title="How to make a D&D 5E character">
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Open <b>Characters → Create</b>. Pick concept and name.</li>
            <li>Choose a <b>Class</b> (12 SRD classes — drives hit-die, primary ability, save proficiencies, casting type).</li>
            <li>Set <b>Level</b> (1-20). Most tables start at 1, 3, or 5. Proficiency bonus auto-computes.</li>
            <li>Choose a <b>Race</b> (9 SRD races — applies ASI / size / speed / racial traits).</li>
            <li>Roll or assign <b>Ability Scores</b> (STR/DEX/CON/INT/WIS/CHA). Modifier = ⌊(score − 10) / 2⌋.</li>
            <li>Pick <b>Saving-Throw</b> proficiencies (granted by class) and <b>Skill</b> proficiencies (class + background pool).</li>
            <li>Select your <b>Background</b>, fill <b>Inventory</b> + <b>Spells Known</b> as appropriate, then Save.</li>
          </ol>
          <div className="text-[11px] text-mist/80 italic mt-2">
            d20 + ability mod (+ proficiency if proficient) ≥ DC. Critical hit on natural 20.
            All mechanics are CC-BY SRD 5.1 — consult the SRD for full descriptions.
          </div>
        </Section>
      )}
      {system === "cypher" && (
        <Section title="How to make a Cypher character">
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Build the <b>character sentence</b>: "I am a [Descriptor] [Type] who [Focus]." (e.g. <i>"Mystical Adept who Bears a Halo of Fire"</i>)</li>
            <li>Pick your <b>Type</b> (Warrior / Adept / Explorer / Speaker / Wright / Paradox) — drives starting Pool sizes &amp; Edge.</li>
            <li>Pick your <b>Descriptor</b> (16 options: Brash, Mystical, Resilient, …) — flavour + 1 Edge or Skill bonus.</li>
            <li>Pick your <b>Focus</b> — your special move (Bears a Halo of Fire / Crafts Unique Objects / Murders / …).</li>
            <li>Allocate <b>Stat Pools</b> (Might / Speed / Intellect) and <b>Edge</b> per pool. Set your <b>Effort</b> cap.</li>
            <li>Train <b>Skills</b> (Train = -1 step, Specialise = -1 more), pick starting <b>Cyphers</b> (single-use items).</li>
            <li>Set your <b>Tier</b> (1-6). Save.</li>
          </ol>
          <div className="text-[11px] text-mist/80 italic mt-2">
            Roll 1d20 ≥ (3 × difficulty). Lower difficulty by 1 step per Skill / Edge / Asset / Effort.
            Effort costs Pool points (max = Edge + 1). Cypher System Creator licence — Requires the Cypher System Rulebook from Monte Cook Games.
          </div>
        </Section>
      )}
      {system === "anime-5e" && (
        <Section title="How to make an Anime 5E character (hybrid)">
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Anime 5E uses a <b>5E d20 sheet</b> (class / level / race / 6 ability scores / saves / skills) PLUS a <b>Tri-Stat point-buy supplement</b>.</li>
            <li>Pick a 5E-style <b>Class</b> (Adept / Champion / Idol / Pilot / Tinker), <b>Level</b>, <b>Heritage</b>, set ability scores, save profs, skill profs.</li>
            <li>In the <b>Tri-Stat Supplement</b> card, set your point budget (default 50) and add <b>Tri-Stat Attributes</b> (Combat Mastery, Heightened Sense, Tough, Personal Gear, …) for genre-flavoured powers.</li>
            <li>Each Attribute level costs its listed pts/lvl. Mix freely — your d20 attacks resolve normally, the Tri-Stat layer adds signature techniques.</li>
            <li>Defects (Anime 5E core p.132) reduce the budget when added — refund the points at the GM's discretion.</li>
            <li>Save when both layers feel cohesive.</li>
          </ol>
          <div className="text-[11px] text-mist/80 italic mt-2">
            Anime 5E Tri-Stat OGL release · published by Dyskami Publishing.
            Attributes: core book p.91. Defects: p.132. Items: p.190+. The GM determines whether
            point-buy is on top of the d20 chassis or used standalone.
          </div>
        </Section>
      )}
      {system === "besm-4e" && (
        <Section title="How to make a BESM 4E character">
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Open <b>Characters → Create</b>. Pick concept, name, Power Level (Adventurous = 90 pts).</li>
            <li>Set <b>Stats</b> (Body / Mind / Soul) — sum should reflect the concept's strengths.</li>
            <li>Add <b>Attributes</b> from the system selector. Each Enhancement = 1 application that lowers effective Level by 1; each Limiter = 1 application that raises it by 1 (cost stays at base × level).</li>
            <li>Add <b>Skills</b> with components, and balance with <b>Defects</b> (refunds points) for narrative weight.</li>
            <li>Save. The GM will publish the sheet once the table approves.</li>
          </ol>
        </Section>
      )}

      {/* ── Reference Tables / GM authoring ─────────────────────────── */}
      {system === "dnd-5e" && (
        <Section title="How to author a D&D class feature, race, or magic item">
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Atelier → <b>Reference Tables</b>. The tab strip uses D&D vocabulary: <b>Class Features</b>, <b>Drawbacks / Backgrounds</b>, <b>Followers / Mounts</b>, <b>Adventuring Gear / Magic Items</b>.</li>
            <li>For a custom class feature, pick the <b>Class Features</b> tab → mechanic-only description, page reference (cite SRD only — no Wizards-trademarked content).</li>
            <li>For a magic item, use <b>Adventuring Gear / Magic Items</b> → name + mechanic effect + rarity in the summary.</li>
            <li>Players see your authored entries in the Character Forge picker tagged <b>"Campaign Reference"</b>.</li>
          </ol>
        </Section>
      )}
      {system === "cypher" && (
        <Section title="How to author Cyphers, Foci, Types, Relics, Equipment">
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Atelier → <b>Reference Tables</b>. Cypher-native tabs: <b>Cyphers</b>, <b>Foci</b>, <b>Types</b>, <b>Items / Equipment</b>, <b>GM Intrusions / House Rules</b>.</li>
            <li>For a custom <b>Cypher</b>: name, level (e.g. <i>1d6+1</i>), form (Patch / Vial / Coil / …), mechanic effect (single-use). Cite Cypher SRD page if drawn from the rulebook.</li>
            <li>For a custom <b>Focus</b>: name + role keyword (e.g. <i>"Bears a Halo of Fire — burns nearby foes"</i>).</li>
            <li>For a custom <b>Type</b>: name + starting Pools + Edge entitlements.</li>
            <li>For <b>Relics / Artifacts</b> use Items / Equipment tab and note the depletion roll (e.g. <i>"1 in 1d6 daily"</i>).</li>
            <li>Players see your authored entries in the Cypher Character Forge picker tagged <b>"Campaign Reference"</b>.</li>
          </ol>
        </Section>
      )}
      {(system === "besm-4e" || system === "anime-5e") && (
        <Section title="How to make a weapon or item">
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Atelier → Reference Tables → choose Weapons / Items.</li>
            <li>Click <b>Add Weapon/Item</b>. Name, mechanic-only summary, cost, page reference.</li>
            <li>The page is validated against the system book range. Out-of-range citations save with a warning so you can fix later.</li>
          </ol>
        </Section>
      )}

      {/* ── XP / advancement ────────────────────────────────────────── */}
      <Section title="How advancement works">
        {system === "dnd-5e" && (
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>D&D 5E uses XP-by-level brackets. Earn XP from encounters; the GM levels up the table at session boundaries.</li>
            <li>On level-up: gain hit points (rolled or fixed), new class features, and possibly a new Ability Score Improvement / feat.</li>
            <li>Re-open your character in <b>Edit</b> mode to bump the level field; recompute proficiency + slot tables.</li>
          </ol>
        )}
        {system === "cypher" && (
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>Cypher characters earn <b>XP</b> primarily through <b>GM Intrusions</b> (+2 to the player, +2 to a chosen ally; refusing costs −1 XP).</li>
            <li>Spend 4 XP for a <b>short-term benefit</b> (training new skill / +4 Pool / etc.). Spend 4 XP for a <b>long-term benefit</b> (lasting skill / contact / piece of gear).</li>
            <li>Tier-up (4 milestones) grants Pool/Edge increases and a new Type/Focus ability.</li>
          </ol>
        )}
        {(system === "besm-4e" || system === "anime-5e") && (
          <ol className="list-decimal list-inside space-y-1 text-sm text-parchment/90">
            <li>From your <b>Character Sheet → Spend XP</b>, propose a stat or attribute level change with the XP cost.</li>
            <li>The GM sees the proposal in the Atelier queue and approves or rejects it.</li>
            <li>On approval, the change applies immediately and XP is deducted. Live rolls always read the GM-approved snapshot.</li>
          </ol>
        )}
      </Section>

      {/* ── GM Materials (universal) ────────────────────────────────── */}
      {isGm && (
        <Section title="GM Materials" testid="instructions-gm-materials">
          <ul className="list-disc list-inside space-y-1 text-sm text-parchment/90">
            <li><b>Atelier tab</b> contains Session 0 / Arcs / Master Plot tiers. Continuity check flags missing references.</li>
            <li><b>Knowledge Web → Mechanic Ingestion</b>: drop in a rulebook excerpt or world bible; Claude returns categorized suggestions (system-aware — D&D returns classes/spells, Cypher returns cyphers/foci, etc.).</li>
            <li><b>Decks tab</b>: spawn built-in decks (Deck of Many Things for D&D, Cypher Draw, Genre Shift for Anime 5E, TableGnostic Mood for any system) OR author your own custom decks per campaign.</li>
            {system === "cypher" && (
              <li><b>GM Intrusion ledger</b>: every intrusion you offer should be logged in the Session Journal — XP awards (+2 player, +2 ally) post directly to the player's pool.</li>
            )}
            {system === "dnd-5e" && (
              <li><b>Encounter / CR considerations</b>: balance encounters by total Challenge Rating ≈ party level × number of PCs. Track HP/conditions on each combatant.</li>
            )}
            <li><b>GM Session Journal</b> is a pinned, GM-only Codex node. Append after every session.</li>
            <li><b>Export PDF</b> produces a DriveThruRPG-ready chronicle. Cypher campaigns are licence-gated — campaigns tagged with Numenera / The Strange / No Thank You Evil! return 451 with the verbatim disclaimer.</li>
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


/**
 * BesmWeaponItemComposer — V6.25.12
 *
 * Authoring surface for `weapon` and `item` reference entries on BESM
 * 4E campaigns. Pulls the four canonical mod pools from
 * `/api/besm/reference` (cached client-side) and lets the GM:
 *
 *   • set base level + cost-per-level,
 *   • toggle Weapon Enhancements / Limiters (p.135 / p.142) with rank
 *     spinners (1-12) — rank-aware, never changes cost,
 *   • for `weapon` rows, optionally tick "also an Item" which reveals
 *     the Item flavour pool AND triggers the half-cost rule on the
 *     resulting cost preview (BESM 4E p.135 Item rule),
 *   • for `item` rows, the half-cost rule is always active.
 *
 * The composed entry's `fields.enhancements` / `fields.limiters` arrays
 * are stored in the same shape the character sheet's MacroBuilder /
 * Customise panels read — `[{name, rank, value}]` — so a published
 * reference entry round-trips into a character build with the same
 * mechanical effect.
 */
function BesmWeaponItemComposer({ row, onChange }) {
  const [pools, setPools] = useState(null);
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const { data } = await api.get(`/besm/reference`);
        if (live) setPools({
          weapon_enhancements: data.weapon_enhancements || [],
          weapon_limiters:     data.weapon_limiters || [],
          item_enhancements:   data.item_enhancements || [],
          item_limiters:       data.item_limiters || [],
        });
      } catch { if (live) setPools({ weapon_enhancements: [], weapon_limiters: [],
                                       item_enhancements: [], item_limiters: [] }); }
    })();
    return () => { live = false; };
  }, []);

  const f = row.fields || {};
  const lvl = Number(f.level || 1);
  const cpl = Number(f.cost_per_level || 1);
  const isItemKind = row.kind === "item";
  const alsoItem = isItemKind || !!f.also_an_item;
  const enhArr = f.enhancements || [];
  const limArr = f.limiters || [];
  const contents = Array.isArray(f.item_contents) ? f.item_contents : [];

  const setField = (k, v) => onChange({ ...row, fields: { ...f, [k]: v } });
  const findIdx = (arr, name) =>
    arr.findIndex((m) => (m?.name || "").toLowerCase() === name.toLowerCase());
  const toggle = (which, name) => {
    const arr = (which === "enhancements" ? enhArr : limArr).slice();
    const j = findIdx(arr, name);
    const sign = which === "enhancements" ? -1 : 1;
    if (j >= 0) arr.splice(j, 1);
    else arr.push({ name, rank: 1, value: sign });
    setField(which, arr);
  };
  const setRank = (which, name, rk) => {
    const r = Math.max(1, Math.min(12, +rk || 1));
    const sign = which === "enhancements" ? -1 : 1;
    const arr = (which === "enhancements" ? enhArr : limArr).map((m) =>
      (m?.name || "").toLowerCase() === name.toLowerCase()
        ? { ...m, name, rank: r, value: sign * r } : m);
    setField(which, arr);
  };
  // Nested item_contents helpers (BESM 4E Mecha pattern, p.219).
  const addContent = () => setField("item_contents", [
    ...contents, { name: "", level: 1, cost_per_level: 1, note: "" },
  ]);
  const updateContent = (idx, patch) => setField(
    "item_contents",
    contents.map((c, i) => (i === idx ? { ...c, ...patch } : c)),
  );
  const removeContent = (idx) =>
    setField("item_contents", contents.filter((_, i) => i !== idx));

  // Live cost preview: gross = lvl × cpl + Σ (child.level × child.cost_per_level).
  // Item half-cost rule (p.135 / p.219) applies to the COMBINED raw total.
  const selfGross = lvl * cpl;
  const childGross = contents.reduce(
    (s, c) => s + Math.max(1, Number(c.level || 1)) * Math.max(0, Number(c.cost_per_level || 0)),
    0,
  );
  const gross = selfGross + childGross;
  const finalCost = alsoItem ? Math.ceil(gross / 2) : gross;
  const sumRanks = (a) => a.reduce((s, m) => s + (m.rank || 1), 0);
  const enhRanks = sumRanks(enhArr);
  const limRanks = sumRanks(limArr);
  const effLvl = Math.max(1, lvl + limRanks - enhRanks);

  const Pool = ({ label, items, kind, color }) => (
    <div className="mb-2">
      <div className="label-ref mb-1">{label}</div>
      <div className="flex flex-wrap gap-1">
        {(items || []).map((e) => {
          const idx = findIdx(kind === "enhancements" ? enhArr : limArr, e.name);
          const selected = idx >= 0;
          const cur = selected ? (kind === "enhancements" ? enhArr : limArr)[idx] : null;
          return (
            <button key={e.name} type="button"
                    onClick={() => toggle(kind, e.name)}
                    title={`${e.note || e.name}\np.${e.page} ${e.source?.book || ""} · rank: ${Array.isArray(e.rank_range) ? e.rank_range.join("-") : e.rank_range || "1"}`}
                    className={`tag ${selected ? color : ""}`}
                    data-testid={`besm-composer-${kind}-${e.name.replace(/\s+/g,"-")}`}>
              {e.name}
              {selected && cur?.rank > 1 && (
                <span className="text-[10px] ml-1 opacity-80">×{cur.rank}</span>
              )}
            </button>
          );
        })}
      </div>
      {(kind === "enhancements" ? enhArr : limArr).length > 0 && (
        <div className="mt-2 space-y-1">
          {(kind === "enhancements" ? enhArr : limArr).map((m, i) => (
            <div key={`${m.name}-${i}`} className="flex items-center gap-2 text-xs flex-wrap">
              <span className={`tag ${color}`}>{m.name}</span>
              <label className="text-[10px] text-mist">×rank</label>
              <input type="number" min={1} max={12} value={m.rank || 1}
                      onChange={(e) => setRank(kind, m.name, +e.target.value)}
                      className="input w-16 text-center select-sm"
                      data-testid={`besm-composer-rank-${kind}-${m.name.replace(/\s+/g,"-")}`}/>
              <span className="text-[10px] text-mist/70">
                ({kind === "enhancements" ? "−" : "+"}{m.rank || 1} eff.lvl)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="border border-gold/20 rounded-sm p-3 bg-void/40 space-y-2"
         data-testid={`besm-composer-${row.kind}`}>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <input className="input" type="number" min={1} max={20} placeholder="Level"
               value={f.level || ""}
               onChange={(e) => setField("level", e.target.value === "" ? "" : Number(e.target.value))}
               data-testid="besm-composer-level"/>
        <input className="input" type="number" min={0} step="0.5" placeholder="Cost / Level"
               value={f.cost_per_level || ""}
               onChange={(e) => setField("cost_per_level", e.target.value === "" ? "" : Number(e.target.value))}
               data-testid="besm-composer-cpl"/>
        {row.kind === "weapon" && (
          <label className="flex items-center gap-2 text-xs text-parchment cursor-pointer
                              border border-gold/15 rounded-sm px-2 bg-void/60">
            <input type="checkbox" checked={!!f.also_an_item}
                    onChange={(e) => setField("also_an_item", e.target.checked)}
                    data-testid="besm-composer-also-item"/>
            <span>Also an Item?</span>
            <span className="text-[9px] text-mist/70 italic">(tick for swords, untick for conjured Fireballs)</span>
          </label>
        )}
      </div>

      {/* Cost preview row. */}
      <div className="text-[11px] text-mist border-t border-gold/10 pt-2"
           data-testid="besm-composer-cost-preview">
        Self: <span className="text-parchment font-display">{selfGross}</span> pts
        ({lvl} × {cpl})
        {childGross > 0 && (
          <>
            {" "}+ Contents: <span className="text-parchment font-display">{childGross}</span> pts
          </>
        )}
        {(childGross > 0 || alsoItem) && (
          <>
            {" "}= Gross: <span className="text-parchment font-display">{gross}</span> pts
          </>
        )}
        {alsoItem && (
          <>
            {" "}· <span className="text-arcane">Item half-cost (p.135):</span>{" "}
            <span className="text-gold-bright font-display">ceil({gross}/2) = {finalCost} pts</span>
          </>
        )}
        {(enhRanks > 0 || limRanks > 0) && (
          <>
            {" "}· effective Level: <span className="text-arcane">×{effLvl}</span>
            <span className="text-mist/70"> (base {lvl} + {limRanks} lim − {enhRanks} enh)</span>
          </>
        )}
      </div>

      {/* Nested Item Contents (Mecha pattern, BESM 4E p.219).
          Surfaces ONLY when the row is an item OR a weapon-also-item. */}
      {alsoItem && (
        <div className="border-t border-gold/10 pt-2"
             data-testid="besm-composer-item-contents">
          <div className="flex items-center justify-between mb-1">
            <div>
              <div className="label-ref">Item Contents · Mecha pattern (p.219)</div>
              <div className="text-[10px] text-mist/70 italic">
                Nested attributes carried INSIDE this item (e.g. a Mecha&apos;s
                weapon mounts, a bag&apos;s inner attribute pool). Their raw
                cost feeds the Item half-cost rule above.
              </div>
            </div>
            <button type="button" onClick={addContent}
                    className="btn btn-ghost text-[11px]"
                    data-testid="besm-composer-item-content-add">
              + Add nested attribute
            </button>
          </div>
          {contents.length === 0 && (
            <div className="text-mist italic text-[11px]">
              No nested contents. Most items don&apos;t need them — use this
              for the Mecha pattern (BESM 4E p.219) when the item itself
              carries other Attributes that pay the half-cost together.
            </div>
          )}
          <div className="space-y-2">
            {contents.map((c, i) => {
              const cl = Math.max(1, Number(c.level || 1));
              const cc = Math.max(0, Number(c.cost_per_level || 0));
              const cgross = cl * cc;
              return (
                <div key={i}
                     className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center
                                border border-gold/10 rounded-sm p-2 bg-void/30"
                     data-testid={`besm-composer-item-content-row-${i}`}>
                  <input className="input sm:col-span-5"
                         placeholder="Nested attribute name (e.g. Weapon, Armour, Sensors)"
                         value={c.name || ""}
                         onChange={(e) => updateContent(i, { name: e.target.value })}
                         data-testid={`besm-composer-item-content-name-${i}`}/>
                  <input className="input sm:col-span-2 text-center"
                         type="number" min={1} max={20}
                         placeholder="Lvl"
                         value={c.level ?? ""}
                         onChange={(e) => updateContent(i, {
                           level: e.target.value === "" ? "" : Number(e.target.value),
                         })}
                         data-testid={`besm-composer-item-content-level-${i}`}/>
                  <input className="input sm:col-span-2 text-center"
                         type="number" min={0} step="0.5"
                         placeholder="Cost/Lvl"
                         value={c.cost_per_level ?? ""}
                         onChange={(e) => updateContent(i, {
                           cost_per_level: e.target.value === "" ? "" : Number(e.target.value),
                         })}
                         data-testid={`besm-composer-item-content-cpl-${i}`}/>
                  <span className="sm:col-span-2 text-[11px] text-mist/80 text-center">
                    raw <span className="text-parchment font-display">{cgross}</span> pts
                  </span>
                  <button type="button"
                          onClick={() => removeContent(i)}
                          className="btn btn-ghost text-[11px] sm:col-span-1"
                          data-testid={`besm-composer-item-content-remove-${i}`}>
                    ×
                  </button>
                  {(c.note || c.note === "") && (
                    <input className="input sm:col-span-12"
                           placeholder="Optional note (e.g. mount slot, charges)"
                           value={c.note || ""}
                           onChange={(e) => updateContent(i, { note: e.target.value })}
                           data-testid={`besm-composer-item-content-note-${i}`}/>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {pools ? (
        <>
          <Pool label="Weapon Enhancements · BESM 4E p.135"
                 items={pools.weapon_enhancements} kind="enhancements"
                 color="border-gold text-gold-bright bg-gold/15"/>
          <Pool label="Weapon Limiters · BESM 4E p.142"
                 items={pools.weapon_limiters} kind="limiters"
                 color="border-ember text-ember bg-ember/15"/>
          {alsoItem && (
            <>
              <Pool label="Item Enhancements · TableGnostic flavour pool"
                     items={pools.item_enhancements} kind="enhancements"
                     color="border-gold text-gold-bright bg-gold/10"/>
              <Pool label="Item Limiters · TableGnostic flavour pool"
                     items={pools.item_limiters} kind="limiters"
                     color="border-ember text-ember bg-ember/10"/>
            </>
          )}
        </>
      ) : (
        <div className="text-mist text-[11px] italic">Loading mod pools…</div>
      )}

      <input className="input" placeholder="Description / GM note (optional)"
             value={f.description || ""}
             onChange={(e) => setField("description", e.target.value)}
             data-testid="besm-composer-description"/>
    </div>
  );
}


