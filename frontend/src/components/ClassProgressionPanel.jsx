/**
 * ClassProgressionPanel — V6.19
 *
 * Inline character-sheet block on the Mechanics tab. Shows:
 *   - Class proficiencies (saves / armor / weapons / tools / skills)
 *   - Spell progression bracket (full / half / warlock / none)
 *   - Per-level granted-features timeline (level 1 → current)
 *
 * Read-only. If the class isn't in the canonical library, surfaces a
 * "homebrew custom class" callout with link to the Atelier · References
 * tab.
 */
import React, { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";

const SPELL_BLURB = {
  full_caster: "Full caster (CHA/INT/WIS-based, 1st-level slots from level 1).",
  half_caster: "Half caster (1st-level slots from level 2).",
  third_caster: "Third caster (Eldritch Knight / Arcane Trickster pattern).",
  warlock: "Pact magic (short-rest slot recovery).",
  none: "Non-caster.",
  unknown: "Spell progression unknown — homebrew class.",
};

export default function ClassProgressionPanel({ characterId }) {
  const [data, setData] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/characters/${characterId}/class-progression`);
      setData(data);
    } catch { /* ignore */ }
  }, [characterId]);
  useEffect(() => { refresh(); }, [refresh]);

  if (!data) return null;

  return (
    <div className="card-mystic p-4 mt-4" data-testid="class-progression-panel">
      <div className="flex items-baseline justify-between mb-2 flex-wrap gap-2">
        <div>
          <div className="label-ref">Class · {data.class || "?"} (Level {data.level})</div>
          <div className="text-[10px] text-mist italic">
            Cumulative proficiencies and per-level granted features.
          </div>
        </div>
      </div>

      {!data.known ? (
        <div className="border-l-2 border-arcane/40 bg-arcane/5 p-2 text-[11px] text-parchment"
             data-testid="class-progression-homebrew">
          <span className="text-arcane-light">✦</span> {data.advice}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 text-xs mb-3"
               data-testid="class-proficiencies">
            <PropList label="Hit Die" items={[data.hit_die]}/>
            <PropList label="Saves" items={data.save_profs}/>
            <PropList label="Armor"
                       items={data.armor_profs.length ? data.armor_profs : ["—"]}/>
            <PropList label="Weapons" items={data.weapon_profs}/>
            <PropList label="Tools"
                       items={data.tool_profs.length ? data.tool_profs : ["—"]}/>
            <PropList label="Skills (pick from)" items={[data.skill_choices]}/>
          </div>

          <div className="text-[11px] text-mist italic mb-2 border-l-2 border-arcane/30 pl-2"
               data-testid="class-spell-progression">
            ✦ {SPELL_BLURB[data.spell_progression] || SPELL_BLURB.unknown}
          </div>

          <div className="text-[10px] uppercase tracking-widest text-mist mb-1">
            Granted features by level
          </div>
          <div className="space-y-1.5" data-testid="class-timeline">
            {data.timeline.map((row) => (
              <div key={row.level}
                   className={`border rounded-sm p-2 ${row.level === data.level ? "border-gold-bright/60 bg-gold/10" : "border-gold/15"}`}
                   data-testid={`class-timeline-row-${row.level}`}>
                <div className="text-[10px] uppercase tracking-widest text-gold mb-0.5">
                  Level {row.level}
                  {row.level === data.level && (
                    <span className="ml-2 text-gold-bright text-[9px]">(current)</span>
                  )}
                </div>
                <ul className="text-[12px] text-parchment list-none space-y-0.5">
                  {row.features.map((f, i) => (
                    <li key={i} className="leading-snug">— {f}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function PropList({ label, items }) {
  return (
    <div className="border border-gold/15 rounded-sm p-2">
      <div className="text-[9px] uppercase tracking-widest text-mist mb-0.5">{label}</div>
      <div className="text-parchment">
        {(items || []).map((it, i) => (
          <span key={i} className="block leading-snug">{it}</span>
        ))}
      </div>
    </div>
  );
}
