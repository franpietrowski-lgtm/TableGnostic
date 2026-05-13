import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import CypherReferencePanel from "./CypherReferencePanel";
import { BookOpen, Search, Sparkles } from "lucide-react";
import { InstructionsPanel } from "./ReferenceEditor";
// V6.25.51 — non-BESM reference view extracted into a sibling module
// to keep this file focused on the BESM 4E tab-group surface.
import { SystemReferenceView, CustomLibrarySection } from "./reference/SystemReferenceView";

const SYSTEM_TABS = [
  { id: "besm-4e",  label: "BESM 4E (Native)" },
  { id: "anime-5e", label: "Anime 5E" },
  { id: "dnd-5e",   label: "D&D 5E (CC-BY SRD)" },
  { id: "cypher",   label: "Cypher System" },
];

/**
 * Reference page — three tab groups:
 *   1. Core BESM 4E       → core-stats / attributes / defects / etc.
 *   2. Combat & Play      → actions / companions / race templates /
 *                           size modifiers / weapons / items / armour
 *   3. Custom (Aurea)     → custom attributes / power packs / skills
 *
 * Cost-engine note rendered prominently: BESM 4E rule is COST = base × Level
 * (fixed) and Enhancements/Limiters change EFFECTIVE LEVEL only.
 */
export default function Reference() {
  const [ref, setRef] = useState(null);
  const [q, setQ] = useState("");
  const [tab, setTab] = useState("attributes");
  const [systemId, setSystemId] = useState("besm-4e");
  const [systemRef, setSystemRef] = useState(null);
  const [besmCustomLib, setBesmCustomLib] = useState(null);

  useEffect(() => { api.get("/besm/reference").then((r) => setRef(r.data)); }, []);
  useEffect(() => {
    if (systemId !== "besm-4e") return;
    api.get(`/reference/library?system_id=besm-4e`)
      .then((r) => setBesmCustomLib(r.data))
      .catch(() => setBesmCustomLib({ rows: [], total: 0, campaign_count: 0 }));
  }, [systemId]);
  useEffect(() => {
    if (systemId === "besm-4e") { setSystemRef(null); return; }
    api.get(`/systems/${systemId}/reference`)
      .then((r) => setSystemRef(r.data))
      .catch(() => setSystemRef({ kind: "scaffold",
        rule_note: "Reference content for this system has not yet been extracted." }));
  }, [systemId]);
  const ql = q.toLowerCase();

  const lists = useMemo(() => {
    if (!ref) return {};
    const f = (arr) => (arr || []).filter((a) =>
      ((a.name || a.difficulty || a.size || a.group || "") + " " + (a.summary || "") + " " + (a.effect || "") + " " + ((a.tags || []).join(" "))).toLowerCase().includes(ql));
    return {
      // Core
      attributes: f(ref.attributes),
      defects: f(ref.defects),
      skill_groups: f(ref.skill_groups),
      enhancements: f(ref.enhancements),
      limiters: f(ref.limiters),
      power_levels: f(ref.power_levels),
      target_numbers: f(ref.target_numbers),
      derived_values: f(ref.derived_values),
      extras_rules: f(ref.extras_rules),
      // New combat/play
      actions: f(ref.actions),
      companions: f(ref.companions),
      race_templates: f(ref.race_templates),
      class_templates: f(ref.class_templates),
      size_modifiers: f(ref.size_modifiers),
      weapons: f(ref.weapons),
      items_gear: f(ref.items_gear),
      armour: f(ref.armour),
      // V6.25.49 — universal status conditions / ailments.
      conditions: f(ref.conditions),
      // V6.25.45 — weapon/item-specific enhancement & limiter pools.
      // Already shipped in besm_data + /api/besm/reference; surfacing
      // them as Reference tabs so players can browse the full pool
      // before choosing what to attach in the weapon/item builder.
      weapon_enhancements: f(ref.weapon_enhancements),
      weapon_limiters:     f(ref.weapon_limiters),
      item_enhancements:   f(ref.item_enhancements),
      item_limiters:       f(ref.item_limiters),
      // Custom (Aurea)
      custom_attributes: f(ref.custom?.attributes),
      custom_power_packs: f(ref.custom?.power_packs),
      custom_skills: f(ref.custom?.skills),
    };
  }, [ref, ql]);

  if (!ref) return <div className="p-10 text-mist">Opening the tome…</div>;

  // V6.25.25 — Custom (yours) library aggregator (only for BESM tab; the
  // SystemReferenceView mounts its own for non-BESM systems).

  const TAB_GROUPS = [
    {
      label: "Core BESM 4E",
      tabs: [
        ["attributes", "Attributes"],
        ["defects", "Defects"],
        ["skill_groups", "Skill Groups"],
        ["enhancements", "Enhancements"],
        ["limiters", "Limiters"],
        ["derived_values", "Derived Values"],
        ["power_levels", "Power Levels"],
        ["target_numbers", "Target Numbers"],
        ["extras_rules", "BESM Extras"],
      ],
    },
    {
      label: "Combat & Play",
      tabs: [
        ["actions", "Actions"],
        ["companions", "Companions"],
        ["race_templates", "Race Templates"],
        ["class_templates", "Class Templates"],
        ["size_modifiers", "Size Modifiers"],
        ["weapons", "Weapons"],
        ["items_gear", "Items"],
        ["armour", "Armour"],
        ["conditions", "Conditions"],
      ],
    },
    {
      label: "Equipment Mods",
      tabs: [
        ["weapon_enhancements", "Weapon Enhancements"],
        ["weapon_limiters",     "Weapon Limiters"],
        ["item_enhancements",   "Item Enhancements"],
        ["item_limiters",       "Item Limiters"],
      ],
    },
    {
      label: "Custom · Aurea",
      tabs: [
        ["custom_attributes", "Custom Attributes"],
        ["custom_power_packs", "Power Packs / Bundles"],
        ["custom_skills", "Custom Skills"],
      ],
    },
    {
      label: "Help",
      tabs: [
        ["instructions", "Instructions"],
      ],
    },
  ];

  // V6.25.45 — formatter for weapon/item enhancement & limiter rows.
  // Renders `±N pts/rank · ranks <r> · <scope> · <note>`.
  const _modLine = (item, sign, scopeLabel) => {
    const mag = Math.abs(Number(item.cost_modifier ?? 1));
    const rr = item.rank_range;
    let rankStr = "";
    if (Array.isArray(rr)) {
      const lo = rr[0] ?? 1;
      const hi = rr[1];
      rankStr = hi === null || hi === undefined ? `ranks ${lo}+` :
                lo === hi ? `rank ${lo}` : `ranks ${lo}–${hi}`;
    } else if (typeof rr === "string" && rr.trim()) {
      rankStr = `rank ${rr}`;
    }
    return `${sign}${mag} pts/rank${rankStr ? ` · ${rankStr}` : ""} · ${scopeLabel}${item.note ? ` · ${item.note}` : ""}`;
  };

  // Per-tab card renderer — one row of bottom-line stats + the blurb if any.
  const lineFor = (item) => {
    switch (tab) {
      case "attributes":      return `${item.cost_per_level} pts/level${item.human_ok ? " · human" : ""}${item.note ? ` · ${item.note}` : ""}`;
      case "defects":         return `${item.points_per_rank} pts/rank · ${item.category}${item.note ? ` · ${item.note}` : ""}`;
      case "skill_groups":    return `${item.cost_per_level} pts/level`;
      case "enhancements":    return `Lowers effective level by 1 · cost unchanged`;
      case "limiters":        return `Raises effective level by 1 · cost unchanged`;
      case "derived_values":  return item.formula;
      case "power_levels":    return `${item.points} Character Points`;
      case "target_numbers":  return `TN ${item.tn}`;
      case "extras_rules":    return `${item.category}${item.summary ? ` — ${item.summary}` : ""}`;
      case "actions":         return `${item.category} · AP ${item.ap_cost}${item.summary ? ` — ${item.summary}` : ""}`;
      case "companions":      return `${item.type}${item.summary ? ` — ${item.summary}` : ""}`;
      case "race_templates":  return `${item.cp_cost} CP${item.summary ? ` — ${item.summary}` : ""}`;
      case "class_templates": return `${item.cp_cost} CP${item.bundle ? ` · ${item.bundle.length} entr${item.bundle.length === 1 ? "y" : "ies"}` : ""}${item.summary ? ` — ${item.summary}` : ""}`;
      case "size_modifiers":  return `Scale ${item.scale_metres}m · ATK ${item.atk_mod >= 0 ? "+" : ""}${item.atk_mod} · DEF ${item.def_mod >= 0 ? "+" : ""}${item.def_mod} · HP×${item.hp_mult}`;
      case "weapons":         return `${item.class} · DMG ${item.damage_mod >= 0 ? "+" : ""}${item.damage_mod}${item.range_m ? ` · range ${item.range_m}m` : ""}${item.note ? ` · ${item.note}` : ""}`;
      case "items_gear":      return `${item.category}${item.note ? ` · ${item.note}` : ""}`;
      case "armour":          return `AR ${item.armour_rating} · ${item.weight_class}${item.note ? ` · ${item.note}` : ""}`;
      // V6.25.49 — Conditions list: severity chip · tags · effect.
      case "conditions": {
        const sev = item.severity ? item.severity.toUpperCase() : "";
        const tags = (item.tags || []).join(" · ");
        return `${sev ? `[${sev}]` : ""}${tags ? ` ${tags}` : ""}${item.effect ? ` — ${item.effect}` : ""}`;
      }
      // V6.25.45 — Weapon / item-specific enhancement & limiter pools.
      // cost_modifier = + (enh) / − (lim) Character Points per rank.
      // rank_range may be a tuple [min, max|null] or a free string like "2 or 4".
      case "weapon_enhancements": return _modLine(item, "+", "weapon-only");
      case "weapon_limiters":     return _modLine(item, "−", "weapon-only");
      case "item_enhancements":   return _modLine(item, "+", "item-only");
      case "item_limiters":       return _modLine(item, "−", "item-only");
      case "custom_attributes":  return `Based on ${item.based_on} · ${item.base_cost_per_level} pts/level · Discipline: ${item.discipline}`;
      case "custom_power_packs": return `${item.discipline} · ${(item.components || []).length} component${(item.components || []).length === 1 ? "" : "s"}`;
      case "custom_skills":      return `${item.tier} · ${item.cost_per_level} pts/level · Discipline: ${item.discipline}`;
      default: return "";
    }
  };

  const showBesm4eRuleNote = ["enhancements", "limiters", "attributes",
                              "custom_attributes", "custom_power_packs",
                              "custom_skills"].includes(tab);

  return (
    <div className="px-8 md:px-12 py-10 max-w-6xl" data-system={systemId}>
      <div className="label-ref mb-2">Sacred Tome</div>
      <h1 className="font-display text-4xl tracking-wide text-parchment">
        {systemId === "besm-4e" ? "BESM 4E Reference" :
         systemId === "anime-5e" ? "Anime 5E Reference" :
         systemId === "dnd-5e" ? "D&D 5E Reference (CC-BY SRD 5.1)" :
         systemId === "cypher" ? "Cypher System Reference" :
         "System Reference"}
      </h1>
      <p className="text-mist mt-2 font-body">
        Look up mechanic names, costs, and page references — consult the
        rulebook for full prose. Switch systems below to view a different
        ruleset's reference data.
      </p>
      {/* System tab strip */}
      <div className="mt-4 flex flex-wrap gap-1.5" data-testid="reference-system-tabs">
        {SYSTEM_TABS.map((s) => (
          <button key={s.id} onClick={() => setSystemId(s.id)}
                  className={`text-[10px] px-3 py-1.5 rounded-sm font-ui uppercase tracking-widest transition-colors ${systemId === s.id ? "bg-gold/15 text-gold-bright border border-gold/30" : "text-mist hover:bg-gold/5 border border-transparent"}`}
                  data-testid={`reference-system-${s.id}`}>
            {s.label}
          </button>
        ))}
      </div>

      {systemId !== "besm-4e" && (
        <SystemReferenceView ref_={systemRef} systemId={systemId} q={q}/>
      )}
      {systemId !== "besm-4e" && <div className="h-6"/>}
      {systemId === "besm-4e" && (
      <>
      <div className="mt-3 text-[11px] font-ui italic text-mist/70" data-testid="ref-system-note">
        BESM 4E is fully populated below. PF2e, CoC, Savage Worlds, FATE,
        Cyberpunk RED, V5, Blades, Mothership, and Shadowrun 6E are scaffolded
        for selection on campaign creation; their reference content is coming
        in subsequent phases.
      </div>

      {/* Search bar */}
      <div className="mt-6 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 border border-gold/20 rounded-sm px-3 bg-void/60 w-80">
          <Search className="w-4 h-4 text-gold/60"/>
          <input className="bg-transparent outline-none py-2 text-sm text-parchment flex-1"
                 placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} data-testid="reference-search"/>
        </div>
      </div>

      {/* Tab groups */}
      <div className="mt-4 space-y-2">
        {TAB_GROUPS.map((group) => (
          <div key={group.label} className="flex items-start gap-3 flex-wrap">
            <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60 pt-2 w-32 shrink-0">
              {group.label}
            </div>
            <div className="flex flex-wrap gap-1.5 flex-1">
              {group.tabs.map(([v, l]) => (
                <button key={v} onClick={() => setTab(v)}
                        className={`btn btn-ghost text-xs ${tab === v ? "border-gold/60 text-gold-bright" : ""}`}
                        data-testid={`ref-tab-${v}`}>
                  {l}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="divider-sigil my-5"/>

      {/* BESM 4E rule note pinned for cost-relevant tabs */}
      {showBesm4eRuleNote && (
        <div className="card-mystic p-4 mb-4 border-gold/30" data-testid="ref-cost-rule-note">
          <div className="label-ref text-gold-bright mb-1 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5"/> BESM 4E cost rule
          </div>
          <div className="text-sm text-parchment/95 font-body leading-relaxed">
            <strong>Cost = base × assigned Level</strong> (fixed). Enhancements
            and Limiters do <em>not</em> change point cost — they shift{" "}
            <strong>effective Level</strong> by their <em>rank</em>:{" "}
            <code className="text-gold">+rank per Limiter</code>,{" "}
            <code className="text-gold">−rank per Enhancement</code>, floored at 1.
            Most modifiers are rank&nbsp;1, but the BESM 4E core + Extras call
            out heavier applications (e.g. <em>Item Specialist</em> at rank 2,
            <em> Always On</em> at rank 2, <em>Restriction Severe</em> at rank 3).
            Enter the rank the rulebook prescribes when authoring a custom row;
            stacking compounds linearly.
            Stack Limiters for narrow but powerful Attributes; stack Enhancements
            for broad-but-cheap utility ones.
          </div>
        </div>
      )}

      {/* Custom rule-note (Aurea) */}
      {tab.startsWith("custom_") && ref.custom?.rule_note && (
        <div className="card-mystic p-4 mb-4 border-arcane/40" data-testid="ref-custom-rule-note">
          <div className="label-ref text-arcane-light mb-1">Aurea — design note</div>
          <div className="text-[12px] text-parchment/90 font-body leading-relaxed whitespace-pre-line">
            {ref.custom.rule_note}
          </div>
        </div>
      )}

      {/* Instructions tab — short how-to guide for players (and GMs see extra). */}
      {tab === "instructions" && (
        <InstructionsPanel isGm={false} systemId={systemId}/>
      )}

      {/* Card grid */}
      {tab !== "instructions" && (
      <div className="grid md:grid-cols-2 gap-3">
        {(lists[tab] || []).map((item, i) => (
          <div key={i} className="card-mystic p-4" data-testid={`ref-card-${tab}-${i}`}>
            <div className="flex items-center justify-between">
              <div className="text-sm text-parchment font-ui">
                {item.name || item.difficulty || item.size || item.group}
              </div>
              <div className="text-[10px] font-ui uppercase tracking-widest text-gold/70 flex items-center gap-1">
                <BookOpen className="w-3 h-3"/>
                {item.page ? `p.${item.page} ` : ""}
                {item.source?.book ||
                  (tab === "extras_rules" ? "BESM Extras"
                  : tab.startsWith("custom_") ? "Aurea (custom)"
                  : "BESM 4E")}
              </div>
            </div>
            <div className="text-[11px] text-mist mt-1 font-ui">{lineFor(item)}</div>

            {item.blurb && (
              <div className="text-[12px] text-parchment/85 font-body leading-snug mt-2 pt-2 border-t border-gold/10"
                   data-testid={`ref-blurb-${tab}-${i}`}>
                {item.blurb}
              </div>
            )}
            {item.summary && !item.blurb && (
              <div className="text-[12px] text-parchment/85 font-body leading-snug mt-2 pt-2 border-t border-gold/10">
                {item.summary}
              </div>
            )}

            {/* Custom-attribute extras: enhancement/limiter intent + based-on */}
            {tab === "custom_attributes" && (
              <div className="mt-2 pt-2 border-t border-gold/10 space-y-1.5">
                {(item.enhancements_intent || []).length > 0 && (
                  <div className="text-[11px] font-ui">
                    <span className="text-gold/60 uppercase tracking-widest">Enhancements (broaden) </span>
                    <span className="text-gold-bright">{item.enhancements_intent.join(" · ")}</span>
                  </div>
                )}
                {(item.limiters_intent || []).length > 0 && (
                  <div className="text-[11px] font-ui">
                    <span className="text-gold/60 uppercase tracking-widest">Limiters (focus) </span>
                    <span className="text-arcane-light">{item.limiters_intent.join(" · ")}</span>
                  </div>
                )}
              </div>
            )}

            {/* Custom-power-pack extras: components + barter */}
            {tab === "custom_power_packs" && (
              <div className="mt-2 pt-2 border-t border-gold/10 space-y-1">
                <div className="text-[11px] font-ui">
                  <span className="text-gold/60 uppercase tracking-widest">Components </span>
                  <span className="text-parchment/90">{(item.components || []).join(" · ")}</span>
                </div>
                {item.barter_value && (
                  <div className="text-[10px] font-ui italic text-mist">
                    Barter: {item.barter_value}
                  </div>
                )}
              </div>
            )}

            {/* Custom-skill extras: components */}
            {tab === "custom_skills" && (item.components || []).length > 0 && (
              <div className="mt-2 pt-2 border-t border-gold/10 text-[11px] font-ui">
                <span className="text-gold/60 uppercase tracking-widest">Components </span>
                <span className="text-parchment/90">{item.components.join(" · ")}</span>
              </div>
            )}

            {tab === "extras_rules" && (
              <div className="text-[10px] text-gold/60 mt-1 font-ui uppercase tracking-widest">BESM Extras</div>
            )}
          </div>
        ))}
        {(lists[tab] || []).length === 0 && (
          <div className="text-mist italic text-sm">No matches.</div>
        )}
      </div>
      )}

      {/* Generic mechanic primers — only on the Attributes tab as the most relevant home */}
      {tab === "attributes" && ref.generic_blurbs && ref.generic_blurbs.length > 0 && (
        <div className="mt-8" data-testid="ref-generic-blurbs">
          <div className="label-ref mb-3">How the costing equation works</div>
          <div className="grid md:grid-cols-3 gap-3">
            {ref.generic_blurbs.map((g, i) => (
              <div key={i} className="card-mystic p-4">
                <div className="text-sm text-parchment font-ui">{g.name}</div>
                <div className="text-[12px] text-mist font-body leading-snug mt-2">{g.blurb}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {besmCustomLib && (
        <div className="mt-6" data-testid="besm-custom-library-mount">
          <CustomLibrarySection lib={besmCustomLib} systemId="besm-4e"/>
        </div>
      )}
      </>
      )}
    </div>
  );
}
