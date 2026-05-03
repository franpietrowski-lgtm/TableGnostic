/**
 * DndDerivedAndEquipment — V6.20
 *
 * Surfaces the at-a-glance values players actually reach for during
 * play that the older sheet was hiding:
 *   - AC / Initiative / Passive Perception / Spell Save DC / Spell Atk
 *   - Equipped weapon slot (main + offhand) with attack & damage line
 *   - Equipped armor slot with don/doff state and AC contribution
 *   - Subclass picker (if not yet chosen)
 *   - Feats granted via advancement_log with description fetched from the
 *     campaign reference library
 *   - Spell list with toggleable "Prepared today" checkboxes that persist
 *     to `folio.dnd_state.spells_prepared`
 *
 * Lives under DndSheetView's main render between the spell-slot block and
 * the magic-items table.
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { Sparkles, Shield, Sword, Plus, BookOpen, Check } from "lucide-react";

const ABILITIES = ["Strength", "Dexterity", "Constitution",
                   "Intelligence", "Wisdom", "Charisma"];
const ABBR = { Strength: "STR", Dexterity: "DEX", Constitution: "CON",
                Intelligence: "INT", Wisdom: "WIS", Charisma: "CHA" };

const SPELLCASTING_ABILITY = {
  Bard: "Charisma", Cleric: "Wisdom", Druid: "Wisdom",
  Sorcerer: "Charisma", Warlock: "Charisma", Wizard: "Intelligence",
  Paladin: "Charisma", Ranger: "Wisdom",
  // Anime 5E originals
  Adept: "Wisdom", Idol: "Charisma", Tinker: "Intelligence",
  // D&D 5E SRD Artificer
  Artificer: "Intelligence",
};

export default function DndDerivedAndEquipment({
  characterId, state, folio, isOwnerOrGm,
}) {
  const sc = state.ability_scores || {};
  const lvl = Math.max(1, +(state.level || 1));
  const profBonus = Math.max(2, 2 + Math.floor((lvl - 1) / 4));
  const mod = (a) => Math.floor((((sc[a] != null && sc[a] > 0) ? sc[a] : 10) - 10) / 2);
  const cls = (state.class || "").split("(")[0].trim();
  const castAb = SPELLCASTING_ABILITY[cls];
  const castMod = castAb ? mod(castAb) : 0;
  const spellSaveDc = castAb ? 8 + profBonus + castMod : null;
  const spellAttack = castAb ? profBonus + castMod : null;

  // AC: if state.ac is overridden, honor it; otherwise compute from
  // equipped armor (state.armor_equipped) or default unarmored.
  const equippedArmor = state.armor_equipped || null;
  const acFromArmor = useMemo(() => {
    if (state.ac != null) return state.ac;
    if (!equippedArmor) return 10 + mod("Dexterity");
    const base = +equippedArmor.base_ac || 10;
    const cap = equippedArmor.dex_cap;
    const dex = cap === 0 ? 0 : Math.min(mod("Dexterity"), cap == null ? 99 : +cap);
    return base + dex + (+equippedArmor.bonus || 0);
  }, [state.ac, equippedArmor, sc]); // eslint-disable-line react-hooks/exhaustive-deps

  const init = mod("Dexterity");
  const passivePerception = 10 + mod("Wisdom")
    + ((state.skill_profs || []).includes("Perception") ? profBonus : 0);

  const equippedWeapon = state.weapon_equipped || null;
  const equippedOffhand = state.offhand_equipped || null;

  // Feats granted via advancement_log.
  const featTickets = (state.advancement_log || [])
    .filter((a) => a.key === "feat" || (a.detail && a.detail.feat));

  // Spell prep state.
  const spellsKnown = state.spells_known || [];
  const spellsPrepared = state.spells_prepared || [];
  const [busy, setBusy] = useState(false);
  const [localPrep, setLocalPrep] = useState(spellsPrepared);
  useEffect(() => { setLocalPrep(spellsPrepared); }, [JSON.stringify(spellsPrepared)]);

  const togglePrep = useCallback(async (spellName) => {
    if (!isOwnerOrGm) return;
    const next = localPrep.includes(spellName)
      ? localPrep.filter((x) => x !== spellName)
      : [...localPrep, spellName];
    setLocalPrep(next);
    setBusy(true);
    try {
      // Persist via PATCH on character; back-end already accepts arbitrary
      // folio.dnd_state field updates.
      await api.put(`/characters/${characterId}`, {
        folio: { ...folio, dnd_state: { ...state, spells_prepared: next } },
      });
    } catch (e) {
      // revert on failure
      setLocalPrep(localPrep);
    } finally { setBusy(false); }
  }, [characterId, folio, state, localPrep, isOwnerOrGm]);

  return (
    <>
      {/* ── Derived Values strip ── */}
      <div className="card-mystic p-5 mt-4" data-testid="dnd-derived-values">
        <div className="label-ref mb-2">Derived Values · at a glance</div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          <Derived label="AC" value={acFromArmor} testid="derived-ac"/>
          <Derived label="Initiative" value={init >= 0 ? `+${init}` : `${init}`} testid="derived-init"/>
          <Derived label="Passive Per." value={passivePerception} testid="derived-passive"/>
          <Derived label={spellSaveDc != null ? "Spell Save DC" : "—"}
                    value={spellSaveDc ?? "—"} testid="derived-spell-dc"/>
          <Derived label={spellAttack != null ? "Spell Attack" : "—"}
                    value={spellAttack != null ? (spellAttack >= 0 ? `+${spellAttack}` : `${spellAttack}`) : "—"}
                    testid="derived-spell-atk"/>
        </div>
        <div className="text-[10px] text-mist italic mt-2">
          Auto-computed from class + level + ability scores. Override AC by
          setting <code>state.ac</code>; equip armor below to recompute.
        </div>
      </div>

      {/* ── Equipment slots ── */}
      <div className="card-mystic p-5 mt-4 grid sm:grid-cols-3 gap-3"
           data-testid="dnd-equipment-slots">
        {/* Weapon */}
        <SlotCard label="Weapon (main)" icon={<Sword className="w-3.5 h-3.5"/>}
                   testid="slot-weapon-main">
          {equippedWeapon ? (
            <div className="text-sm text-parchment">
              <div className="font-ui">{equippedWeapon.name}</div>
              <div className="text-[10px] text-mist mt-0.5">
                {equippedWeapon.damage} {equippedWeapon.damage_type ? `· ${equippedWeapon.damage_type}` : ""}
                {equippedWeapon.props ? ` · ${equippedWeapon.props.join(", ")}` : ""}
              </div>
              <div className="text-[10px] text-gold-bright mt-1">
                Atk: +{profBonus + Math.max(mod("Strength"), mod("Dexterity"))}
                {" "}· Dmg: {equippedWeapon.damage}{Math.max(mod("Strength"), mod("Dexterity")) >= 0 ? `+${Math.max(mod("Strength"), mod("Dexterity"))}` : Math.max(mod("Strength"), mod("Dexterity"))}
              </div>
            </div>
          ) : (
            <EmptySlotHint testid="empty-weapon-main"/>
          )}
        </SlotCard>

        {/* Offhand */}
        <SlotCard label="Off-hand / Shield" icon={<Shield className="w-3.5 h-3.5"/>}
                   testid="slot-offhand">
          {equippedOffhand ? (
            <div className="text-sm text-parchment">
              <div className="font-ui">{equippedOffhand.name}</div>
              <div className="text-[10px] text-mist mt-0.5">
                {equippedOffhand.bonus_ac ? `+${equippedOffhand.bonus_ac} AC` : ""}
                {equippedOffhand.damage ? ` · ${equippedOffhand.damage}` : ""}
              </div>
            </div>
          ) : (
            <EmptySlotHint testid="empty-offhand"/>
          )}
        </SlotCard>

        {/* Armor */}
        <SlotCard label="Armor" icon={<Shield className="w-3.5 h-3.5"/>}
                   testid="slot-armor">
          {equippedArmor ? (
            <div className="text-sm text-parchment">
              <div className="font-ui">{equippedArmor.name}</div>
              <div className="text-[10px] text-mist mt-0.5">
                {equippedArmor.category} · base AC {equippedArmor.base_ac}
                {equippedArmor.dex_cap != null ? ` (dex cap ${equippedArmor.dex_cap})` : ""}
              </div>
              <div className="text-[10px] text-gold-bright mt-1">
                Don / doff via the Inventory tab — currently equipped.
              </div>
            </div>
          ) : (
            <EmptySlotHint testid="empty-armor" extra="Unarmored: AC = 10 + DEX mod"/>
          )}
        </SlotCard>
      </div>

      {/* ── Subclass picker (only when subclass is empty) ── */}
      {!state.subclass && cls && (
        <div className="card-mystic p-5 mt-4" data-testid="dnd-subclass-pending">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="label-ref">Subclass — pending choice</div>
              <div className="text-[11px] text-mist italic mt-1">
                {cls}s pick a subclass. File a Level-Up Ticket via the
                <Sparkles className="w-3 h-3 inline mx-1 text-gold"/>
                <b>pending choice</b> badge above.
              </div>
            </div>
          </div>
        </div>
      )}
      {state.subclass && (
        <div className="card-mystic p-5 mt-4" data-testid="dnd-subclass-chosen">
          <div className="label-ref">Subclass</div>
          <div className="font-display text-xl text-gold-bright mt-1">{state.subclass}</div>
        </div>
      )}

      {/* ── Feats granted ── */}
      {featTickets.length > 0 && (
        <div className="card-mystic p-5 mt-4" data-testid="dnd-feats-granted">
          <div className="label-ref mb-2">Feats &amp; advancement log</div>
          <div className="space-y-1">
            {(state.advancement_log || []).map((entry, i) => (
              <div key={i} className="border-l-2 border-gold/30 pl-2 py-0.5 text-[12px]"
                   data-testid={`feat-entry-${i}`}>
                <span className="text-gold-bright font-ui">
                  Lv {entry.level || "?"}
                </span>
                <span className="text-parchment ml-2">
                  {entry.key === "feat" ? "Feat: " : entry.key.startsWith("asi") ? "ASI: " : ""}
                  {entry.detail?.feat
                    || entry.detail?.ability
                    || (entry.detail?.abilities || []).join(", ")
                    || entry.choice_key
                    || entry.key}
                </span>
                {entry.note && <span className="text-mist italic ml-2">"{entry.note}"</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Spell preparation (if class casts spells) ── */}
      {spellsKnown.length > 0 && (
        <div className="card-mystic p-5 mt-4" data-testid="dnd-spell-prep">
          <div className="flex items-baseline justify-between flex-wrap gap-2 mb-2">
            <div>
              <div className="label-ref">Spell List · prepared today</div>
              <div className="text-[10px] text-mist italic">
                Tick the spells you want available this session.
                Prepared count: {localPrep.length}/{spellsKnown.length}.
              </div>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-1">
            {spellsKnown.map((spell) => {
              const name = typeof spell === "string" ? spell : (spell.name || "Unknown");
              const lvl = typeof spell === "object" ? spell.level : null;
              const prepped = localPrep.includes(name);
              return (
                <label key={name}
                       className={`border ${prepped ? "border-gold-bright/60 bg-gold/10" : "border-gold/15"} rounded-sm px-2 py-1.5 flex items-center gap-2 ${isOwnerOrGm ? "cursor-pointer hover:border-gold/40" : "cursor-not-allowed opacity-80"}`}
                       data-testid={`spell-prep-row-${name.replace(/\s+/g, "-")}`}>
                  <input type="checkbox" checked={prepped}
                         disabled={busy || !isOwnerOrGm}
                         onChange={() => togglePrep(name)}
                         className="accent-gold"
                         data-testid={`spell-prep-toggle-${name.replace(/\s+/g, "-")}`}/>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-parchment truncate">{name}</div>
                    {lvl != null && (
                      <div className="text-[10px] text-mist">
                        {lvl === 0 ? "Cantrip" : `Lv ${lvl}`}
                      </div>
                    )}
                  </div>
                  {prepped && <Check className="w-3 h-3 text-gold-bright"/>}
                </label>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}

function Derived({ label, value, testid }) {
  return (
    <div className="border border-gold/15 rounded-sm p-2 text-center"
         data-testid={testid}>
      <div className="text-[9px] uppercase tracking-widest text-mist">{label}</div>
      <div className="font-display text-xl text-gold-bright mt-0.5">{value}</div>
    </div>
  );
}

function SlotCard({ label, icon, children, testid }) {
  return (
    <div className="border border-gold/20 rounded-sm p-3" data-testid={testid}>
      <div className="text-[10px] uppercase tracking-widest text-mist mb-1 flex items-center gap-1">
        {icon} {label}
      </div>
      {children}
    </div>
  );
}

function EmptySlotHint({ testid, extra }) {
  return (
    <div className="text-[11px] text-mist italic" data-testid={testid}>
      <Plus className="w-3 h-3 inline mr-1 text-gold/40"/>
      Empty slot. Equip via the Inventory tab.
      {extra && <div className="text-[10px] text-mist/70 mt-1">{extra}</div>}
    </div>
  );
}
