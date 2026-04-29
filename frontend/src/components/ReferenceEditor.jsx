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
          <button onClick={() => setDraft(blank())} className="btn btn-primary text-xs"
                  data-testid="reference-add-btn">
            <Plus className="w-3 h-3"/> Add {String(labelOf(tab)).split(" ")[0]}
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-1 mb-3 border-b border-gold/10 pb-2"
           data-testid="reference-tabs">
        {KIND_KEYS.map((k) => (
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
