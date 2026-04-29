/**
 * Anime 5E — hybrid character builder.
 *
 * Anime 5E is a Tri-Stat OGL release that grafts the BESM point-buy
 * engine onto a 5E d20 chassis. Implementation here is a thin
 * adapter: reshape the Anime 5E reference into a 5E-shape ref and
 * delegate to Dnd5eBuilder, passing the original Anime 5E ref through
 * `hybridSupplement` so the Tri-Stat point-buy card renders below
 * the d20 sheet.
 *
 * The Tri-Stat card itself lives in `Anime5eHybridSupplement.jsx`
 * (separate file so Dnd5e.jsx and Anime5e.jsx can share it without
 * creating a circular ESM cycle).
 *
 * Persists into `folio.dnd_state` (5E half) AND `folio.anime5e_state`
 * (Tri-Stat half).
 */
import React from "react";
import { Dnd5eBuilder } from "./Dnd5e";

export function Anime5eBuilder({ campaign, ref_, charId }) {
  // Build a 5E-shape ref from the Anime 5E hybrid response. The Anime 5E
  // reference DOES expose `classes`, `heritages`/`races`, `skills`, etc.
  // but its abilities default to Body/Mind/Soul. For the D&D-shape sheet
  // we upgrade abilities to the D&D 6 + map back when point-buy is shown.
  const dndRef = {
    ...ref_,
    classes: ref_.classes || [],
    races: ref_.heritages || ref_.races || [],
    abilities: ref_.abilities || [
      { name: "Strength", abbr: "STR" }, { name: "Dexterity", abbr: "DEX" },
      { name: "Constitution", abbr: "CON" }, { name: "Intelligence", abbr: "INT" },
      { name: "Wisdom", abbr: "WIS" }, { name: "Charisma", abbr: "CHA" },
    ],
    skills: ref_.skills?.length ? ref_.skills : [],
  };
  return (
    <Dnd5eBuilder campaign={campaign} ref_={dndRef} charId={charId}
                  hybridSupplement={ref_}/>
  );
}

// Re-export so callers that previously did `import { Anime5eHybridSupplement }
// from './Anime5e'` keep working without churn.
export { Anime5eHybridSupplement } from "./Anime5eHybridSupplement";
