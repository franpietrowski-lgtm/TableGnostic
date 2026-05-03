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
      // V6.24 — use the new PATCH /characters/{id}/folio endpoint so we
      // skip CharacterIn validation (which previously rejected the
      // partial body and silently reverted the toggle).
      await api.patch(`/characters/${characterId}/folio`, {
        bucket: "dnd_state",
        patch: { spells_prepared: next },
      });
    } catch (e) {
      // revert on failure
      setLocalPrep(localPrep);
    } finally { setBusy(false); }
  }, [characterId, localPrep, isOwnerOrGm]);

  // V6.24 — Equip controls. Tap an inventory item to set / clear the
  // appropriate slot (weapon_equipped / offhand_equipped / armor_equipped).
  // Maps the picker entry's __kind / category to the right slot.
  const equipItem = useCallback(async (item, slot) => {
    if (!isOwnerOrGm) return;
    const isObj = typeof item === "object" && item !== null;
    if (!isObj) return;  // legacy free-text strings can't auto-equip
    setBusy(true);
    try {
      const slotKey = slot === "weapon" ? "weapon_equipped"
                     : slot === "offhand" ? "offhand_equipped"
                     : "armor_equipped";
      // Normalize the entry to the slot's expected shape so the slot
      // card renders correctly. Defensive coercion: damage / props
      // must be string / array of strings.
      const norm = {
        name: typeof item.name === "string" ? item.name : "Item",
        damage: typeof item.damage === "string" ? item.damage : undefined,
        damage_type: undefined,  // SRD damage already includes the type token
        props: Array.isArray(item.props)
          ? item.props.filter((p) => typeof p === "string") : [],
        category: typeof item.category === "string" ? item.category : undefined,
        base_ac: +item.base_ac || (item.ac && parseInt(item.ac)) || undefined,
        dex_cap: typeof item.dex_cap === "number" ? item.dex_cap : undefined,
        bonus: +item.bonus || 0,
        bonus_ac: +item.bonus_ac || 0,
      };
      await api.patch(`/characters/${characterId}/folio`, {
        bucket: "dnd_state",
        patch: { [slotKey]: norm },
      });
      // Trigger a refresh so the slot card picks up the new value.
      window.dispatchEvent(new CustomEvent("tg:character-folio-changed",
                                             { detail: { characterId } }));
    } catch (_) { /* swallow */ } finally { setBusy(false); }
  }, [characterId, isOwnerOrGm]);

  const unequipSlot = useCallback(async (slot) => {
    if (!isOwnerOrGm) return;
    setBusy(true);
    try {
      const slotKey = slot === "weapon" ? "weapon_equipped"
                     : slot === "offhand" ? "offhand_equipped"
                     : "armor_equipped";
      await api.patch(`/characters/${characterId}/folio`, {
        bucket: "dnd_state",
        patch: { [slotKey]: null },
      });
      window.dispatchEvent(new CustomEvent("tg:character-folio-changed",
                                             { detail: { characterId } }));
    } catch (_) { /* swallow */ } finally { setBusy(false); }
  }, [characterId, isOwnerOrGm]);

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
              <div className="font-ui">{typeof equippedWeapon.name === "string" ? equippedWeapon.name : "—"}</div>
              <div className="text-[10px] text-mist mt-0.5">
                {typeof equippedWeapon.damage === "string" ? equippedWeapon.damage : ""}
                {typeof equippedWeapon.damage_type === "string" ? ` · ${equippedWeapon.damage_type}` : ""}
                {Array.isArray(equippedWeapon.props)
                  ? ` · ${equippedWeapon.props.filter((p) => typeof p === "string").join(", ")}`
                  : ""}
              </div>
              <div className="text-[10px] text-gold-bright mt-1">
                Atk: +{profBonus + Math.max(mod("Strength"), mod("Dexterity"))}
                {" "}· Dmg: {typeof equippedWeapon.damage === "string" ? equippedWeapon.damage : "—"}{Math.max(mod("Strength"), mod("Dexterity")) >= 0 ? `+${Math.max(mod("Strength"), mod("Dexterity"))}` : Math.max(mod("Strength"), mod("Dexterity"))}
              </div>
              {isOwnerOrGm && (
                <button onClick={() => unequipSlot("weapon")} disabled={busy}
                        className="btn btn-ghost text-[9px] mt-1"
                        data-testid="unequip-weapon">
                  Unequip
                </button>
              )}
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
              <div className="font-ui">{typeof equippedOffhand.name === "string" ? equippedOffhand.name : "—"}</div>
              <div className="text-[10px] text-mist mt-0.5">
                {equippedOffhand.bonus_ac ? `+${equippedOffhand.bonus_ac} AC` : ""}
                {typeof equippedOffhand.damage === "string" ? ` · ${equippedOffhand.damage}` : ""}
              </div>
              {isOwnerOrGm && (
                <button onClick={() => unequipSlot("offhand")} disabled={busy}
                        className="btn btn-ghost text-[9px] mt-1"
                        data-testid="unequip-offhand">
                  Unequip
                </button>
              )}
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
              <div className="font-ui">{typeof equippedArmor.name === "string" ? equippedArmor.name : "—"}</div>
              <div className="text-[10px] text-mist mt-0.5">
                {typeof equippedArmor.category === "string" ? equippedArmor.category : ""}
                {equippedArmor.base_ac ? ` · base AC ${equippedArmor.base_ac}` : ""}
                {equippedArmor.dex_cap != null ? ` (dex cap ${equippedArmor.dex_cap})` : ""}
              </div>
              {isOwnerOrGm && (
                <button onClick={() => unequipSlot("armor")} disabled={busy}
                        className="btn btn-ghost text-[9px] mt-1"
                        data-testid="unequip-armor">
                  Unequip
                </button>
              )}
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

      {/* ── V6.24 — Equippable inventory tray ────────────────────── */}
      <EquippableInventory inventory={state.inventory || []}
                            equipItem={equipItem}
                            isOwnerOrGm={isOwnerOrGm}
                            busy={busy}/>

      {/* ── V6.24 — Artificer Infusions panel ────────────────────── */}
      <ArtificerInfusionsPanel infusionsKnown={state.infusions_known || []}
                                 infusionsActive={state.infusions_active || []}
                                 characterId={characterId}
                                 classLevels={state.class_levels || {}}
                                 isOwnerOrGm={isOwnerOrGm}/>

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


/**
 * EquippableInventory — V6.24
 *
 * Lists every rich inventory entry (added via ReferencePicker) and
 * presents per-item Equip buttons routed to the right slot based on
 * the entry's `__kind` (or its category / props for legacy data).
 *
 * Legacy plain-string entries are not equippable here — they show as
 * a passive tally so the player still has visibility.
 */
function EquippableInventory({ inventory, equipItem, isOwnerOrGm, busy }) {
  if (!inventory || inventory.length === 0) return null;
  const richEntries = inventory.filter((it) => typeof it === "object" && it !== null);
  const stringEntries = inventory.filter((it) => typeof it === "string");
  if (richEntries.length === 0 && stringEntries.length === 0) return null;

  const slotsFor = (it) => {
    const k = (it.__kind || it.kind || "").toLowerCase();
    const cat = (it.category || "").toLowerCase();
    const out = [];
    // Weapon: __kind 'weapons', or kind contains 'melee' / 'ranged'
    if (k === "weapons" || k.includes("melee") || k.includes("ranged") || it.damage) {
      out.push("weapon");
      // Add off-hand if it has the light or thrown property.
      const props = Array.isArray(it.props)
        ? it.props.filter((p) => typeof p === "string").map((p) => p.toLowerCase())
        : [];
      if (props.some((p) => p.includes("light")) || k === "armor" /* shield-as-armor edge */) {
        out.push("offhand");
      }
    }
    if (k === "armor" || cat === "shield" || cat === "light" || cat === "medium" || cat === "heavy") {
      // shield → offhand, else regular armor slot.
      if (cat === "shield" || (it.name || "").toLowerCase().includes("shield")) {
        out.push("offhand");
      } else {
        out.push("armor");
      }
    }
    return [...new Set(out)];
  };

  return (
    <div className="card-mystic p-5 mt-4" data-testid="equippable-inventory">
      <div className="label-ref mb-2">Inventory · equip slots</div>
      <div className="text-[10px] text-mist/70 italic mb-2">
        Pick a slot to equip from your current inventory. Items added
        via the SRD picker (weapons / armor / shields) auto-detect
        eligible slots; legacy free-text items can't auto-equip.
      </div>
      {richEntries.length > 0 && (
        <div className="space-y-1.5">
          {richEntries.map((it, i) => {
            const slots = slotsFor(it);
            const name = typeof it.name === "string" ? it.name : "Item";
            const hint = [it.kind, it.damage, it.ac, it.category]
              .filter(Boolean).join(" · ");
            return (
              <div key={i}
                   className="flex items-center justify-between flex-wrap gap-2 border-l-2 border-gold/20 pl-2"
                   data-testid={`inv-equip-row-${i}`}>
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-parchment truncate">{name}</div>
                  {hint && <div className="text-[10px] text-mist truncate">{hint}</div>}
                </div>
                {isOwnerOrGm && (
                  <div className="flex flex-wrap gap-1">
                    {slots.length === 0 ? (
                      <span className="text-[10px] text-mist italic">no slot detected</span>
                    ) : (
                      slots.map((s) => (
                        <button key={s} onClick={() => equipItem(it, s)}
                                disabled={busy}
                                className="btn btn-ghost text-[10px]"
                                data-testid={`equip-${s}-${i}`}>
                          Equip → {s === "weapon" ? "Main" : s === "offhand" ? "Off-hand" : "Armor"}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      {stringEntries.length > 0 && (
        <div className="mt-3 text-[10px] text-mist italic">
          {stringEntries.length} legacy free-text {stringEntries.length === 1 ? "item" : "items"}{" "}
          (not auto-equippable): {stringEntries.slice(0, 5).join(", ")}
          {stringEntries.length > 5 && "…"}
        </div>
      )}
    </div>
  );
}

/**
 * ArtificerInfusionsPanel — V6.24
 *
 * Surfaces the character's known + active Artificer infusions on the
 * sheet. Active infusions are toggleable (via PATCH /folio); known
 * count is sourced from the level-up wizard (advancement tickets).
 *
 * Hidden for non-Artificers. The level → known/active table mirrors
 * the backend's `_artificer_infusion_slots()`.
 */
function ArtificerInfusionsPanel({ infusionsKnown, infusionsActive,
                                     characterId, classLevels, isOwnerOrGm }) {
  const [busy, setBusy] = useState(false);
  const artificerLevel = +(classLevels?.Artificer || 0);
  if (artificerLevel < 2) return null;

  // Mirror backend slot table.
  const SLOTS = {
    2: [4, 2], 3: [4, 2], 4: [4, 2], 5: [4, 2],
    6: [6, 3], 7: [6, 3], 8: [6, 3], 9: [6, 3],
    10: [8, 4], 11: [8, 4], 12: [8, 4], 13: [8, 4],
    14: [10, 5], 15: [10, 5], 16: [10, 5], 17: [10, 5],
    18: [12, 6], 19: [12, 6], 20: [12, 6],
  };
  const [knownCap, activeCap] = SLOTS[artificerLevel] || [4, 2];
  const owedKnown = Math.max(0, knownCap - infusionsKnown.length);
  const activeOver = infusionsActive.length > activeCap;

  const toggleActive = async (name) => {
    if (!isOwnerOrGm) return;
    const next = infusionsActive.includes(name)
      ? infusionsActive.filter((x) => x !== name)
      : [...infusionsActive, name];
    setBusy(true);
    try {
      await api.patch(`/characters/${characterId}/folio`, {
        bucket: "dnd_state",
        patch: { infusions_active: next },
      });
      window.dispatchEvent(new CustomEvent("tg:character-folio-changed",
                                             { detail: { characterId } }));
    } catch (_) { /* swallow */ } finally { setBusy(false); }
  };

  return (
    <div className="card-mystic p-4 mt-4" data-testid="artificer-infusions-panel">
      <div className="flex items-baseline justify-between flex-wrap gap-1">
        <div>
          <div className="label-ref">Artificer · Infuse Item</div>
          <div className="text-[10px] text-mist italic">
            Lv. {artificerLevel} — {knownCap} known · {activeCap} active simultaneously.
            Long rest replaces active picks; ticking a box flips it on.
          </div>
        </div>
        <div className="text-[11px]">
          <span className="text-mist">Known </span>
          <span className={infusionsKnown.length > knownCap ? "text-ember" : "text-gold-bright"}>
            {infusionsKnown.length}/{knownCap}
          </span>
          <span className="text-mist"> · Active </span>
          <span className={activeOver ? "text-ember" : "text-gold-bright"}>
            {infusionsActive.length}/{activeCap}
          </span>
        </div>
      </div>
      {owedKnown > 0 && (
        <div className="mt-2 text-[11px] text-ember"
             data-testid="infusions-owed">
          {owedKnown} infusion{owedKnown === 1 ? "" : "s"} unspent. File a
          level-up ticket from the Pending Approval panel above to pick.
        </div>
      )}
      {infusionsKnown.length === 0 ? (
        <div className="text-[11px] text-mist italic mt-2">
          No infusions yet — file a level-up ticket to learn your first.
        </div>
      ) : (
        <div className="mt-2 grid sm:grid-cols-2 gap-1.5">
          {infusionsKnown.map((name, i) => {
            const active = infusionsActive.includes(name);
            const wouldOverflow = !active && infusionsActive.length >= activeCap;
            return (
              <label key={i}
                     className={`flex items-center gap-2 cursor-pointer text-xs border rounded-sm px-2 py-1.5
                                  ${active ? "border-gold/50 bg-gold/5" : "border-gold/15"}
                                  ${wouldOverflow ? "opacity-60" : ""}`}
                     data-testid={`infusion-row-${i}`}>
                <input type="checkbox" checked={active}
                       disabled={busy || !isOwnerOrGm || wouldOverflow}
                       onChange={() => toggleActive(name)}
                       data-testid={`infusion-toggle-${i}`}/>
                <span className="text-parchment">{name}</span>
                {active && (
                  <span className="ml-auto text-[9px] text-gold-bright">
                    ACTIVE
                  </span>
                )}
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

