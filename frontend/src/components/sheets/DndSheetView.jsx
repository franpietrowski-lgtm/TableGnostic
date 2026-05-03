// DndSheetView — extracted in V6.10 refactor.
// Renders the D&D 5E (and Anime 5E hybrid d20-chassis) read-only character
// sheet. Spell slots + chassis + abilities + class features. ~390 lines.
import React from "react";
import { Stat, SimpleListCard, DiceCard, Anime5eSupplementView } from "./sheetCommon";
import DndDerivedAndEquipment from "./DndDerivedAndEquipment";

export default function DndSheetView({ state, folio, roll, characterId, isOwnerOrGm }) {
  const sc = state.ability_scores || {};
  const lvl = Math.max(1, +(state.level || 1));
  const profBonus = Math.max(2, 2 + Math.floor((lvl - 1) / 4));
  // V6.20 — default ability scores to 10 (not 0) when unset, so the
  // sheet shows the canonical baseline instead of -5 modifiers across
  // the board for converter-imported characters that omitted scores.
  const mod = (s) => Math.floor((((sc[s] != null && sc[s] > 0) ? sc[s] : 10) - 10) / 2);
  const fmt = (n) => (n >= 0 ? `+${n}` : `${n}`);
  const six = ["Strength", "Dexterity", "Constitution",
                "Intelligence", "Wisdom", "Charisma"];
  const abbr = { Strength: "STR", Dexterity: "DEX", Constitution: "CON",
                  Intelligence: "INT", Wisdom: "WIS", Charisma: "CHA" };
  const quickRolls = six.map((s) => ({
    label: `${abbr[s]} check`, notation: `1d20${fmt(mod(s))}`,
    hint: `d20 ${fmt(mod(s))} (SRD 5.1)`,
  })).concat([
    { label: "Initiative",
      notation: `1d20${fmt(mod("Dexterity"))}`, hint: "d20 + DEX mod" },
    { label: `Atk (PROF+STR)`,
      notation: `1d20${fmt(mod("Strength") + profBonus)}`,
      hint: "d20 + STR mod + proficiency" },
    { label: `Atk (PROF+DEX)`,
      notation: `1d20${fmt(mod("Dexterity") + profBonus)}`,
      hint: "d20 + DEX mod + proficiency" },
  ]);
  return (
    <div data-system="dnd-5e" data-testid="dnd-sheet-view">
      <div className="card-mystic p-6 mt-8">
        <div className="label-ref">Class · Race · Background</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
          <Stat label="Class" v={state.class || "—"}/>
          <Stat label="Level" v={lvl}/>
          <Stat label="Race" v={state.race || "—"}/>
          <Stat label="Proficiency" v={`+${profBonus}`}/>
        </div>

        {(() => {
          const defaultHd = { Barbarian: 12, Fighter: 10, Paladin: 10, Ranger: 10,
                              Bard: 8, Cleric: 8, Druid: 8, Monk: 8, Rogue: 8, Warlock: 8,
                              Sorcerer: 6, Wizard: 6, Adept: 8, Champion: 12, Idol: 6,
                              Pilot: 8, Tinker: 8 }[state.class] || 8;
          const defaultCasting = { Barbarian: "none", Fighter: "none", Monk: "none", Rogue: "none",
                                    Bard: "full", Cleric: "full", Druid: "full", Sorcerer: "full",
                                    Wizard: "full", Paladin: "half", Ranger: "half",
                                    Warlock: "pact",
                                    Adept: "full", Champion: "none", Idol: "none",
                                    Pilot: "half", Tinker: "half" }[state.class] || "—";
          const defaultSpeed = { Dwarf: 25, Halfling: 25, Gnome: 25,
                                  Elf: 30, Human: 30, Dragonborn: 30, "Half-Elf": 30,
                                  "Half-Orc": 30, Tiefling: 30, Faerie: 25, Apprentice: 30,
                                  Beastfolk: 30, Construct: 30, "Half-Demon": 30, Spirit: 30,
                                  Animal: 40 }[state.race] || 30;
          const hd = state.hit_die || defaultHd;
          return (
            <div className="mt-4 grid sm:grid-cols-3 gap-3 text-[12px] text-parchment/85 leading-snug"
                 data-testid="dnd-chassis-summary">
              <div className="border border-gold/10 rounded-sm p-3">
                <div className="label-ref mb-1">Class · {state.class || "—"}</div>
                d{hd} hit die · casting: <span className="text-gold">{defaultCasting}</span>
                {state.saving_throw_profs?.length > 0 && (
                  <div className="mt-1 text-mist">
                    Saves: {state.saving_throw_profs.map((s) => s.slice(0, 3).toUpperCase()).join(" · ")}
                  </div>
                )}
              </div>
              <div className="border border-gold/10 rounded-sm p-3">
                <div className="label-ref mb-1">Race · {state.race || "—"}</div>
                speed {defaultSpeed} ft
                {state.racial_traits?.length ? (
                  <div className="mt-1 text-mist truncate" title={state.racial_traits.join(" · ")}>
                    {state.racial_traits.join(" · ")}
                  </div>
                ) : null}
              </div>
              <div className="border border-gold/10 rounded-sm p-3">
                <div className="label-ref mb-1">Background · {state.background || "—"}</div>
                {state.skill_profs?.length > 0 ? (
                  <div className="text-mist">
                    <span className="text-parchment/80">Skills:</span> {state.skill_profs.join(", ")}
                  </div>
                ) : <div className="text-mist italic">no skill profs recorded</div>}
                {state.tools?.length > 0 && (
                  <div className="mt-1 text-mist">
                    <span className="text-parchment/80">Tools:</span> {state.tools.join(", ")}
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {state.background && (
          <div className="mt-3 text-[12px] text-parchment/80 font-ui">
            <span className="text-mist">Background feature:</span> {state.background_feature || state.background}
          </div>
        )}
      </div>

      {(() => {
        const conMod = mod("Constitution");
        const hitDie = state.class && state.hit_die ? state.hit_die : null;
        const defaultHd = { Barbarian: 12, Fighter: 10, Paladin: 10, Ranger: 10,
                            Bard: 8, Cleric: 8, Druid: 8, Monk: 8, Rogue: 8, Warlock: 8,
                            Sorcerer: 6, Wizard: 6 }[state.class] || 8;
        const hd = hitDie || defaultHd;
        const hpMax = state.hp_max ?? Math.max(1, hd + conMod + ((hd / 2 + 1) + conMod) * (lvl - 1));
        const hpCur = state.hp_current ?? hpMax;
        const pct = hpMax > 0 ? Math.max(0, Math.min(100, (hpCur / hpMax) * 100)) : 0;
        const colour = pct > 66 ? "#3FAA62" : pct > 33 ? "#C8A34A" : "#7A1F2E";
        return (
          <div className="card-mystic p-5 mt-4 grid sm:grid-cols-2 gap-3 items-center"
               data-testid="dnd-hp-ring">
            <div>
              <div className="label-ref">Hit Points</div>
              <div className="font-display text-3xl text-gold">
                <span style={{ color: colour }}>{Math.round(hpCur)}</span>
                <span className="text-mist text-xl"> / {Math.round(hpMax)}</span>
              </div>
              <div className="h-2 bg-void/60 rounded-full mt-2 overflow-hidden">
                <div className="h-full transition-all"
                     style={{ width: `${pct}%`, backgroundColor: colour }}/>
              </div>
            </div>
            <div className="text-[11px] text-mist/80 leading-snug font-ui">
              Auto-computed from class hit-die ({hd}) + CON mod{conMod >= 0 ? " +" : " "}{conMod} per level.
              GM: override with <code>state.hp_max</code> / <code>state.hp_current</code> in the editor.
              Death saves and exhaustion ranks are tracked in chat.
            </div>
          </div>
        );
      })()}

      <div className="card-mystic p-6 mt-4">
        <div className="label-ref">Ability Scores</div>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-3 text-center">
          {six.map((s) => {
            const m = mod(s);
            // V6.20 — show 10 baseline when score is unset (matches the
            // mod() default), so converter sheets read as canonical.
            const display = (sc[s] != null && sc[s] > 0) ? sc[s] : 10;
            return (
              <button key={s}
                      onClick={() => roll(`1d20${fmt(m)}`, `${state.class || ""} · ${abbr[s]} check`)}
                      className="border border-gold/15 rounded-sm py-2 hover:border-gold/40 hover:bg-gold/5 transition-colors group"
                      data-testid={`dnd-sheet-roll-${abbr[s]}`}
                      title={`Roll d20 ${fmt(m)}`}>
                <div className="label-ref">{abbr[s]}</div>
                <div className="font-display text-2xl text-gold">{display}</div>
                <div className="text-[10px] font-ui text-gold-bright group-hover:text-gold">{fmt(m)}</div>
              </button>
            );
          })}
        </div>
      </div>

      {(state.saving_throw_profs?.length || state.skill_profs?.length) > 0 && (
        <div className="card-mystic p-6 mt-4 grid sm:grid-cols-2 gap-4">
          <div>
            <div className="label-ref">Saving Throw Profs</div>
            <div className="flex flex-wrap gap-1 mt-2">
              {(state.saving_throw_profs || []).map((s) => (
                <span key={s} className="tag border-gold/40 text-gold-bright">{abbr[s] || s} +{profBonus}</span>
              ))}
            </div>
          </div>
          <div>
            <div className="label-ref">Skill Profs</div>
            <div className="flex flex-wrap gap-1 mt-2">
              {(state.skill_profs || []).map((s) => (
                <span key={s} className="tag">{s}</span>
              ))}
              {!state.skill_profs?.length && <span className="text-mist italic text-xs">—</span>}
            </div>
          </div>
        </div>
      )}

      {(() => {
        const cls = state.class;
        const FULL = ["Bard","Cleric","Druid","Sorcerer","Wizard"];
        const HALF = ["Paladin","Ranger"];
        const isFull = FULL.includes(cls);
        const isHalf = HALF.includes(cls);
        const isWarlock = cls === "Warlock";
        if (!isFull && !isHalf && !isWarlock) return null;
        const FULL_TBL = [[2,0,0,0,0,0,0,0,0],[3,0,0,0,0,0,0,0,0],[4,2,0,0,0,0,0,0,0],
          [4,3,0,0,0,0,0,0,0],[4,3,2,0,0,0,0,0,0],[4,3,3,0,0,0,0,0,0],
          [4,3,3,1,0,0,0,0,0],[4,3,3,2,0,0,0,0,0],[4,3,3,3,1,0,0,0,0],
          [4,3,3,3,2,0,0,0,0],[4,3,3,3,2,1,0,0,0],[4,3,3,3,2,1,0,0,0],
          [4,3,3,3,2,1,1,0,0],[4,3,3,3,2,1,1,0,0],[4,3,3,3,2,1,1,1,0],
          [4,3,3,3,2,1,1,1,0],[4,3,3,3,2,1,1,1,1],[4,3,3,3,3,1,1,1,1],
          [4,3,3,3,3,2,1,1,1],[4,3,3,3,3,2,2,1,1]];
        const HALF_TBL = [[0,0,0,0,0,0,0,0,0],[2,0,0,0,0,0,0,0,0],[3,0,0,0,0,0,0,0,0],
          [3,0,0,0,0,0,0,0,0],[4,2,0,0,0,0,0,0,0],[4,2,0,0,0,0,0,0,0],
          [4,3,0,0,0,0,0,0,0],[4,3,0,0,0,0,0,0,0],[4,3,2,0,0,0,0,0,0],
          [4,3,2,0,0,0,0,0,0],[4,3,3,0,0,0,0,0,0],[4,3,3,0,0,0,0,0,0],
          [4,3,3,1,0,0,0,0,0],[4,3,3,1,0,0,0,0,0],[4,3,3,2,0,0,0,0,0],
          [4,3,3,2,0,0,0,0,0],[4,3,3,3,1,0,0,0,0],[4,3,3,3,1,0,0,0,0],
          [4,3,3,3,2,0,0,0,0],[4,3,3,3,2,0,0,0,0]];
        const WARLOCK_TBL = [[1,1],[2,1],[2,2],[2,2],[2,3],[2,3],[2,4],[2,4],[2,5],
          [2,5],[3,5],[3,5],[3,5],[3,5],[3,5],[3,5],[4,5],[4,5],[4,5],[4,5]];
        const CANTRIPS = {
          Bard: [2,2,2,2,3,3,3,3,3,4,4,4,4,4,4,4,4,4,4,4],
          Cleric: [3,3,3,4,4,4,4,4,4,5,5,5,5,5,5,5,5,5,5,5],
          Druid: [2,2,2,3,3,3,3,3,3,4,4,4,4,4,4,4,4,4,4,4],
          Sorcerer: [4,4,4,5,5,5,5,5,5,6,6,6,6,6,6,6,6,6,6,6],
          Warlock: [2,2,2,3,3,3,3,3,3,4,4,4,4,4,4,4,4,4,4,4],
          Wizard: [3,3,3,4,4,4,4,4,4,5,5,5,5,5,5,5,5,5,5,5],
        };
        const cantripsKnown = (CANTRIPS[cls] || [])[lvl - 1] || 0;
        const used = state.slot_usage || {};
        if (isWarlock) {
          const [slots, slotLevel] = WARLOCK_TBL[lvl - 1];
          return (
            <div className="card-mystic p-5 mt-4" data-testid="dnd-spell-slots">
              <div className="label-ref mb-2">Pact Magic · Warlock</div>
              <div className="text-xs text-mist mb-2">
                {slots} slot{slots === 1 ? "" : "s"} · all at slot level {slotLevel} · short-rest recovers
              </div>
              <div className="text-[11px] text-mist">Cantrips known: <b className="text-gold">{cantripsKnown}</b></div>
            </div>
          );
        }
        const tbl = (isFull ? FULL_TBL : HALF_TBL)[lvl - 1] || [];
        return (
          <div className="card-mystic p-5 mt-4" data-testid="dnd-spell-slots">
            <div className="label-ref mb-2">Spell Slots</div>
            <div className="grid grid-cols-3 sm:grid-cols-9 gap-1">
              {tbl.map((max, i) => max > 0 ? (
                <div key={i} className="text-center border border-gold/15 rounded-sm py-1.5">
                  <div className="text-[9px] text-mist tracking-widest uppercase">{i + 1}{["st","nd","rd","th","th","th","th","th","th"][i]}</div>
                  <div className="font-display text-base text-gold-bright">{Math.max(0, max - (used[i + 1] || 0))}<span className="text-mist text-xs">/{max}</span></div>
                </div>
              ) : null)}
            </div>
            <div className="text-[11px] text-mist mt-2">Cantrips known: <b className="text-gold">{cantripsKnown}</b></div>
          </div>
        );
      })()}

      {folio?.anime5e_state && (() => {
        const an = folio.anime5e_state;
        // V6.20 — clamp EP at 0 minimum so a freshly-converted character
        // with default ability scores doesn't display a nonsensical -15.
        const computed = 10 + (mod("Charisma") * lvl);
        const epMax = Math.max(0, an.ep_max ?? computed);
        const epCur = Math.max(0, an.ep_current ?? epMax);
        const pct = epMax > 0 ? Math.max(0, Math.min(100, (epCur / epMax) * 100)) : 0;
        return (
          <div className="card-mystic p-5 mt-4" data-testid="anime5e-ep-pool"
               style={{ borderLeftWidth: 3, borderLeftColor: "#E03A8E" }}>
            <div className="label-ref">Energy Points (Anime 5E)</div>
            <div className="flex items-center gap-3 mt-1">
              <div className="font-display text-2xl" style={{ color: "#E03A8E" }}>
                {Math.round(epCur)}<span className="text-mist text-sm"> / {Math.round(epMax)}</span>
              </div>
              <div className="flex-1 h-2 bg-void/60 rounded-full overflow-hidden">
                <div className="h-full transition-all" style={{ width: `${pct}%`, backgroundColor: "#E03A8E" }}/>
              </div>
            </div>
            <div className="text-[10px] text-mist/70 italic mt-1">
              Spent on signature techniques. Default max = 10 + CHA mod × level.
              GM override via state.anime5e_state.ep_max.
            </div>
          </div>
        );
      })()}

      {/* V6.20 — Derived values + equipment slots + subclass + feats + spell prep */}
      {characterId && (
        <DndDerivedAndEquipment characterId={characterId} state={state}
                                  folio={folio} isOwnerOrGm={!!isOwnerOrGm}/>
      )}

      {((state.magic_items?.length || 0) > 0) && (
        <div className="card-mystic p-5 mt-4" data-testid="dnd-magic-items">
          <div className="label-ref mb-2">Combat Gear &amp; Boons</div>
          <table className="w-full text-sm">
            <thead className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
              <tr className="border-b border-gold/15">
                <th className="text-left py-1.5">Item</th>
                <th className="text-left py-1.5">Slot</th>
                <th className="text-left py-1.5">Tag</th>
                <th className="text-left py-1.5 pl-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {(state.magic_items || []).map((it, i) => (
                <tr key={i} className="border-b border-gold/5">
                  <td className="py-1.5 text-parchment">{it.name}</td>
                  <td className="py-1.5 text-mist text-xs font-ui uppercase tracking-widest">{it.slot || "—"}</td>
                  <td className="py-1.5">
                    {it.tag && (
                      <span className="tag border-gold/50 text-gold-bright text-[10px]">
                        {it.tag}
                      </span>
                    )}
                  </td>
                  <td className="py-1.5 pl-2 text-mist text-xs">{it.notes || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="text-[10px] text-mist/60 italic mt-2">
            GM: populate via state.magic_items = [{`{`}name,slot,tag,notes{`}`}]. Tags: +1 / +2 / +3 / Attuned / Boon / Cursed.
          </div>
        </div>
      )}

      <div className="card-mystic p-5 mt-4" data-testid="dnd-class-features">
        <div className="label-ref mb-2">Class Features · Unlocked at Level {lvl}</div>
        {(state.class_features?.length || 0) === 0 ? (
          <div className="text-[11px] text-mist italic">
            No class features recorded yet. Populate via
            state.class_features = [&#123;level, name, blurb&#125;] from the SRD class
            table. The sheet will list everything your current level has
            unlocked.
          </div>
        ) : (
          <div className="space-y-1.5">
            {(state.class_features || [])
              .filter((f) => (f.level || 1) <= lvl)
              .sort((a, b) => (a.level || 1) - (b.level || 1))
              .map((f, i) => (
                <div key={i} className="text-[12px] leading-snug">
                  <span className="text-gold font-ui text-[10px] uppercase tracking-widest mr-2">
                    Lv {f.level || 1}
                  </span>
                  <span className="text-parchment font-ui">{f.name}</span>
                  {f.blurb && <span className="text-mist ml-2 italic">· {f.blurb}</span>}
                </div>
              ))}
          </div>
        )}
      </div>

      {(state.racial_traits?.length || 0) > 0 && (
        <div className="card-mystic p-5 mt-4" data-testid="dnd-racial-traits">
          <div className="label-ref mb-2">Racial / Heritage Traits</div>
          <div className="flex flex-wrap gap-1.5">
            {(state.racial_traits || []).map((t, i) => (
              <span key={i} className="tag">{t}</span>
            ))}
          </div>
        </div>
      )}

      {(state.inventory?.length || 0) > 0 && (
        <SimpleListCard title="Inventory" items={state.inventory} testid="dnd-sheet-inv"/>
      )}
      {(state.spells_known?.length || 0) > 0 && (
        <SimpleListCard title="Spells Known / Prepared" items={state.spells_known}
                         testid="dnd-sheet-spells"/>
      )}
      {state.notes && (
        <div className="card-mystic p-6 mt-4">
          <div className="label-ref">Notes</div>
          <div className="text-sm text-mist mt-2 whitespace-pre-wrap font-body">{state.notes}</div>
        </div>
      )}

      <Anime5eSupplementView folio={folio}/>

      <DiceCard quickRolls={quickRolls} roll={roll}/>
    </div>
  );
}
