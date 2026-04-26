import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { BookOpen, Search, Sparkles } from "lucide-react";

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

  useEffect(() => { api.get("/besm/reference").then((r) => setRef(r.data)); }, []);
  const ql = q.toLowerCase();

  const lists = useMemo(() => {
    if (!ref) return {};
    const f = (arr) => (arr || []).filter((a) =>
      ((a.name || a.difficulty || a.size || a.group || "") + " " + (a.summary || "")).toLowerCase().includes(ql));
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
      size_modifiers: f(ref.size_modifiers),
      weapons: f(ref.weapons),
      items_gear: f(ref.items_gear),
      armour: f(ref.armour),
      // Custom (Aurea)
      custom_attributes: f(ref.custom?.attributes),
      custom_power_packs: f(ref.custom?.power_packs),
      custom_skills: f(ref.custom?.skills),
    };
  }, [ref, ql]);

  if (!ref) return <div className="p-10 text-mist">Opening the tome…</div>;

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
        ["size_modifiers", "Size Modifiers"],
        ["weapons", "Weapons"],
        ["items_gear", "Items"],
        ["armour", "Armour"],
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
  ];

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
      case "size_modifiers":  return `Scale ${item.scale_metres}m · ATK ${item.atk_mod >= 0 ? "+" : ""}${item.atk_mod} · DEF ${item.def_mod >= 0 ? "+" : ""}${item.def_mod} · HP×${item.hp_mult}`;
      case "weapons":         return `${item.class} · DMG ${item.damage_mod >= 0 ? "+" : ""}${item.damage_mod}${item.range_m ? ` · range ${item.range_m}m` : ""}${item.note ? ` · ${item.note}` : ""}`;
      case "items_gear":      return `${item.category}${item.note ? ` · ${item.note}` : ""}`;
      case "armour":          return `AR ${item.armour_rating} · ${item.weight_class}${item.note ? ` · ${item.note}` : ""}`;
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
    <div className="px-8 md:px-12 py-10 max-w-6xl">
      <div className="label-ref mb-2">Sacred Tome</div>
      <h1 className="font-display text-4xl tracking-wide text-parchment">BESM 4E Reference</h1>
      <p className="text-mist mt-2 font-body">
        This application references the BESM 4E rulebook. Look up names, costs, and page numbers here
        — consult the official rulebook for the full text and rules.
      </p>
      <div className="mt-3 text-[11px] font-ui italic text-mist/70" data-testid="ref-system-note">
        Reference cards reflect the campaign's selected game system. Today,
        BESM 4E is fully populated — D&amp;D 5E, PF2e, CoC, Savage Worlds, FATE,
        Cyberpunk RED, V5, Blades, Mothership, and Shadowrun 6E are scaffolded
        for selection on campaign creation; their reference content is coming soon.
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
            <strong>effective Level</strong>: <code className="text-gold">+1 per Limiter</code>,{" "}
            <code className="text-gold">−1 per Enhancement</code>, floored at 1.
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

      {/* Card grid */}
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
    </div>
  );
}
