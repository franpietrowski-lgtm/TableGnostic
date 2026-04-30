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
    custom: "GM Intrusions / House Rules",
    attribute: "Types",          // The 6 Cypher Types (Warrior / Adept / …)
    skill: "Skills (Trained)",
    defect: "Cyphers",          // Single-use mechanic items
  },
  "dnd-5e": {
    weapon: "Weapons", armor: "Armor", item: "Adventuring Gear / Magic Items",
    companion: "Followers / Mounts",
    custom: "House Rules",
    attribute: "Class Features", // Mechanical features players can select
    skill: "Skills", defect: "Drawbacks / Backgrounds",
  },
  "anime-5e": {
    weapon: "Weapons", armor: "Armor", item: "Items / Cards",
    companion: "Companions / Mounts",
    custom: "House Rules",
    attribute: "Tri-Stat Attributes",
    skill: "Skills", defect: "Defects",
  },
  "besm-4e": {
    weapon: "Weapons", armor: "Armor", item: "Items",
    companion: "Companions", custom: "Custom Rules",
    attribute: "Attributes", skill: "Skills", defect: "Defects",
  },
};
const KIND_KEYS = Object.keys(KIND_LABELS);
// V6.3 — system-aware tab ordering. Only expose kinds that make mechanical
// sense for the active system; avoids a BESM GM having to scroll past 15
// Cypher-only kinds to find Attributes.
const SYSTEM_KIND_ORDER = {
  "besm-4e": ["attribute", "skill", "defect", "enhancement", "limiter",
              "power_pack", "power_bundle", "weapon", "armor", "item",
              "companion", "custom"],
  "anime-5e": ["class_feature", "race_trait", "background", "spell", "feat",
               "skill", "attribute", "defect", "enhancement", "limiter",
               "power_pack", "power_bundle", "weapon", "armor", "item",
               "companion", "custom"],
  "dnd-5e": ["class_feature", "race_trait", "background", "spell", "feat",
             "skill", "weapon", "armor", "item", "companion", "custom"],
  "cypher": ["type", "descriptor", "focus", "cypher_ability", "cypher_item",
             "artifact", "skill", "weapon", "armor", "item", "custom"],
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
            <button onClick={() => setShowAtlas(true)}
                    className="btn btn-ghost text-xs"
                    data-testid="reference-open-atlas-btn"
                    title="Read-only atlas: D&D spells & class abilities translated to BESM Attributes with SRD citations.">
              <BookOpen className="w-3 h-3"/> Spell Conversion Atlas
            </button>
            <button onClick={() => setDraft(blank())} className="btn btn-primary text-xs"
                    data-testid="reference-add-btn">
              <Plus className="w-3 h-3"/> Add {String(labelOf(tab)).split(" ")[0]}
            </button>
          </div>
        )}
      </div>
      <div className="flex flex-wrap gap-1 mb-3 border-b border-gold/10 pb-2"
           data-testid="reference-tabs">
        {(SYSTEM_KIND_ORDER[systemId] || KIND_KEYS).map((k) => (
          <button key={k} onClick={() => setTab(k)}
                  className={`text-[10px] px-2 py-1 rounded-sm font-ui uppercase tracking-widest transition-colors ${tab === k ? "bg-gold/15 text-gold-bright border border-gold/30" : "text-mist hover:bg-gold/5"}`}
                  data-testid={`reference-tab-${k}`}>
            {labelOf(k)}
          </button>
        ))}
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

/**
 * PowerBundleTemplatePicker — modal grid of seeded D&D-spell-mimic
 * Power Bundle templates. Click a card to drop it into the draft editor.
 */
function PowerBundleTemplatePicker({ onPick, onClose, campaignId }) {
  const [templates, setTemplates] = useState([]);
  const [err, setErr] = useState("");
  const [filter, setFilter] = useState("");
  // V6.5 — Live Spend Preview: pick a character; hover a template to
  // see fits/over math projected onto their current spend.
  const [chars, setChars] = useState([]);
  const [previewCharId, setPreviewCharId] = useState("");
  const [previewByCost, setPreviewByCost] = useState({});

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/reference/power-bundle-templates");
        setTemplates(data.templates || []);
        if (campaignId) {
          const cs = await api.get(`/campaigns/${campaignId}/characters`).then((r) => r.data);
          setChars(cs || []);
          if (cs?.length) setPreviewCharId(cs[0].id);
        }
      } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
    })();
  }, [campaignId]);

  const filtered = templates.filter((t) =>
    !filter || t.name.toLowerCase().includes(filter.toLowerCase())
    || (t.school || "").toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
         onClick={onClose} data-testid="bundle-template-picker">
      <div className="card-mystic p-6 max-w-4xl w-full max-h-[85vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref">Power Bundle Templates</div>
            <h3 className="font-display text-xl text-gold mt-1">D&D-spell-mimic starter library</h3>
            <div className="text-[11px] text-mist italic">
              Seeded from the <b>Anime 5E Spell Conversions</b> supplement. Click a card
              to drop it into the editor — tweak cost, invocation, and components before saving.
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost text-xs"
                  data-testid="bundle-template-picker-close">Close</button>
        </div>
        <input className="input text-sm mb-3" placeholder="Filter by name or school…"
               value={filter} onChange={(e) => setFilter(e.target.value)}
               data-testid="bundle-template-filter"/>
        {/* V6.5 — Live Spend Preview: pick a PC → cards show fits/over. */}
        {chars.length > 0 && (
          <div className="flex items-center gap-2 mb-3 text-xs" data-testid="bundle-preview-picker">
            <span className="label-ref text-[9px]">Spend Preview for</span>
            <select className="select select-sm" value={previewCharId}
                    onChange={(e) => setPreviewCharId(e.target.value)}
                    data-testid="bundle-preview-character-select">
              <option value="">— no preview —</option>
              {chars.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || "(unnamed)"} · {c.power_level} · {c.total_points} CP
                </option>
              ))}
            </select>
            <span className="text-[10px] text-mist italic">
              Hover a card → live projection of the PC's CP spend if imported.
            </span>
          </div>
        )}
        {err && <div className="text-ember text-xs mb-2">{err}</div>}
        <div className="grid gap-2 sm:grid-cols-2">
          {filtered.map((t) => {
            const preview = previewByCost[t.cost];
            const fits = preview?.fits;
            return (
              <button key={t.name} onClick={() => onPick(t)}
                      onMouseEnter={async () => {
                        if (!previewCharId || previewByCost[t.cost] !== undefined) return;
                        try {
                          const { data } = await api.post(
                            `/characters/${previewCharId}/simulate-import`,
                            { extra_cost: t.cost });
                          setPreviewByCost((prev) => ({ ...prev, [t.cost]: data }));
                        } catch (_) { /* silent */ }
                      }}
                      className="text-left card-mystic p-3 hover:-translate-y-0.5 transition"
                      data-testid={`bundle-template-${t.source_spell_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-ui text-parchment text-sm">{t.name}</span>
                  <span className="text-[10px] text-mist uppercase tracking-widest">
                    L{t.source_spell_level} · {t.school}
                  </span>
                </div>
                <div className="text-[11px] text-mist italic mt-1 line-clamp-2">{t.description}</div>
                <div className="flex items-center gap-2 mt-2 text-[10px] font-ui flex-wrap">
                  <span className="tag border-gold/40 text-gold-bright">{t.cost} CP</span>
                  <span className="tag border-arcane/30 text-arcane">{t.invocation}</span>
                  {t.charges_max > 0 && <span className="tag border-mist/40 text-mist">{t.charges_max} charges</span>}
                  {t.energy_cost > 0 && <span className="tag border-ember/30 text-ember">{t.energy_cost} EP</span>}
                  {preview && (
                    <span className={`tag ${fits ? "border-arcane/60 text-arcane" : "border-ember/60 text-ember"}`}
                          data-testid={`bundle-preview-result-${t.cost}`}
                          title={preview.summary}>
                      {fits ? `OK (${preview.headroom} spare)` : `OVER by ${-preview.headroom}`}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * SpellConversionAtlas — V6.5 read-only reference that renders the
 * D&D-to-BESM translation library (`/reference/spell-conversions`).
 * Filter by spell level, school, or free-text. Each row shows the
 * canonical D&D spell/ability, its BESM attribute conversion, every
 * enhancement/limiter with its numeric value, the net CP, and the
 * SRD citation — so players can see HOW rule X gets expressed on a
 * BESM sheet rather than just getting a fire-and-forget Power Bundle.
 */
function SpellConversionAtlas({ onClose, onConvert }) {
  const [rows, setRows] = useState([]);
  const [schools, setSchools] = useState([]);
  const [total, setTotal] = useState(0);
  const [err, setErr] = useState("");
  const [search, setSearch] = useState("");
  const [school, setSchool] = useState("");
  const [maxLvl, setMaxLvl] = useState(9);

  useEffect(() => {
    (async () => {
      try {
        const qs = new URLSearchParams();
        qs.set("max_level", String(maxLvl));
        if (school) qs.set("school", school);
        const { data } = await api.get(`/reference/spell-conversions?${qs.toString()}`);
        setRows(data.entries || []);
        setSchools(data.schools || []);
        setTotal(data.total || 0);
      } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
    })();
  }, [school, maxLvl]);

  const filtered = rows.filter((r) =>
    !search || r.source_name.toLowerCase().includes(search.toLowerCase())
    || (r.short_description || "").toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
         onClick={onClose} data-testid="spell-conversion-atlas">
      <div className="card-mystic p-6 max-w-5xl w-full max-h-[88vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref">Spell Conversion Atlas</div>
            <h3 className="font-display text-xl text-gold mt-1">
              D&D 5E → BESM / Anime 5E · {total} entries
            </h3>
            <div className="text-[11px] text-mist italic max-w-xl leading-snug">
              Read-only translation library. Each row shows how a D&D spell or class feature maps to a BESM Attribute bundle — cost, enhancement/limiter values, and SRD page citation. Copy any line into your campaign's Power Bundle reference if you want it purchasable.
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost text-xs"
                  data-testid="spell-conversion-atlas-close">Close</button>
        </div>
        <div className="grid gap-2 sm:grid-cols-3 mb-3">
          <input className="input text-sm" placeholder="Filter by name or text…"
                 value={search} onChange={(e) => setSearch(e.target.value)}
                 data-testid="spell-conversion-search"/>
          <select className="select text-sm" value={school}
                  onChange={(e) => setSchool(e.target.value)}
                  data-testid="spell-conversion-school">
            <option value="">All schools</option>
            {schools.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="select text-sm" value={maxLvl}
                  onChange={(e) => setMaxLvl(Number(e.target.value))}
                  data-testid="spell-conversion-max-level">
            {[0,1,2,3,4,5,6,7,8,9].map((l) => (
              <option key={l} value={l}>Up to level {l}</option>
            ))}
          </select>
        </div>
        {err && <div className="text-ember text-xs mb-2">{err}</div>}
        <div className="space-y-3">
          {filtered.map((r, i) => (
            <div key={`${r.source_name}-${i}`} className="border border-gold/15 rounded-sm p-3"
                 data-testid={`spell-conversion-${r.source_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}>
              <div className="flex items-baseline justify-between flex-wrap gap-2">
                <div>
                  <span className="font-ui text-parchment text-sm">{r.source_name}</span>
                  <span className="ml-2 tag border-gold/40 text-gold-bright">
                    L{r.source_level} · {r.school}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="tag border-arcane/40 text-arcane">{r.net_cp} CP net</span>
                  {onConvert && (
                    <button
                      onClick={() => onConvert(r.source_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase())}
                      className="btn btn-ghost text-[10px]"
                      title="Convert this read-only conversion into an editable Power Bundle draft (opens in the editor pre-filled)."
                      data-testid={`spell-convert-${r.source_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}>
                      → Power Bundle
                    </button>
                  )}
                </div>
              </div>
              <div className="text-[11px] text-mist italic mt-1">{r.short_description}</div>
              {(r.besm || []).map((b, j) => (
                <div key={j} className="mt-2 text-[12px] border-l-2 border-gold/30 pl-3">
                  <div className="font-ui text-gold-bright">
                    {b.attribute} <span className="text-mist text-[10px]">· {b.cost_per_level}/Lvl × {b.level}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(b.enhancements || []).map((e, k) => (
                      <span key={`e${k}`} className="tag border-arcane/30 text-arcane"
                            title={e.name}>
                        +{e.name}{e.value != null ? ` (${e.value > 0 ? "+" : ""}${e.value})` : ""}
                      </span>
                    ))}
                    {(b.limiters || []).map((l, k) => (
                      <span key={`l${k}`} className="tag border-ember/30 text-ember"
                            title={l.name}>
                        −{l.name}{l.value != null ? ` (${l.value > 0 ? "+" : ""}${l.value})` : ""}
                      </span>
                    ))}
                  </div>
                  {b.note && <div className="text-[10px] text-mist italic mt-1">{b.note}</div>}
                </div>
              ))}
              <div className="text-[10px] text-mist/70 italic mt-2">Source: {r.source_reference}</div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-[11px] text-mist italic" data-testid="spell-conversion-empty">
              No conversions match the current filters.
            </div>
          )}
        </div>
      </div>
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
        {/* V6.3 — Power Pack / Power Bundle composer with live CP estimate. */}
        {(row.kind === "power_pack" || row.kind === "power_bundle") && (
          <PowerBundleEditor row={row} onChange={onChange}/>
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
            {KIND_KEYS.map((k) => {
              const sysLabels = SYSTEM_KIND_LABELS[systemId] || SYSTEM_KIND_LABELS["besm-4e"];
              return <option key={k} value={k}>{sysLabels[k] || KIND_LABELS[k]}</option>;
            })}
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
 * PowerBundleEditor — composer for BESM Power Packs & Power Bundles.
 *
 * A Power Bundle is a named, reusable cluster of components (Attributes,
 * Skills, Defects, Enhancements, Limiters) that a GM authors in the
 * Atelier and a player can drop into a character sheet as a single
 * "spell-like" unit. The composer calls `/api/reference/estimate-bundle-cost`
 * on every edit so the GM sees the net CP cost the bundle imposes — plus
 * a hint at how many CP this slot would "cost" vs a D&D spell-level
 * equivalent (guidance only, not enforcement).
 */
function PowerBundleEditor({ row, onChange }) {
  const comps = row.fields?.components || [];
  const [estimate, setEstimate] = React.useState(null);
  const [err, setErr] = React.useState("");

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
        <div className="label-ref">Bundle Components</div>
        <div className="text-[10px] text-mist italic">
          Each component contributes to the bundle's net CP cost — use this to keep
          "Fireball-like" bundles balanced against equivalent D&D spell slots.
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
