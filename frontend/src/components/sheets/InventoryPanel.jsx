/**
 * InventoryPanel — V6.25.27
 *
 * Inventory rework per the user's spec:
 *   • Tabbed sections: All / Mundane / Material / Item / Weapon / Shield /
 *     Armor / Consumable / Magic.
 *   • Edit-mode adds rows; each row toggles Equipped / Attuned / Readied.
 *   • Equipment slots — L-Hand · R-Hand · Head · Torso · Legs · Feet.
 *     Two-handed weapons claim both hands. Slotless attuned items
 *     (e.g. Eli's Apothecary Bandolier) ride alongside without
 *     occupying a slot. Readied items (potions, scrolls, traps) get
 *     a charges counter and live outside the slot grid.
 *   • Auto-derives rows from BESM Attributes named Item / Weapon /
 *     Shield / Armor (plus Healing-style consumables) and from Power
 *     Packs / Power Bundles, so the existing character data shows
 *     up immediately. The user-added manual rows live in
 *     `folio.inventory_state.items` (PATCH /folio bucket=inventory_state).
 *
 * The inventory state contract:
 *   folio.inventory_state = {
 *     items: [InventoryItem],
 *     equipped: { "L-Hand": id|null, "R-Hand": id|null,
 *                 "Head": id|null, "Torso": id|null,
 *                 "Legs": id|null, "Feet": id|null },
 *     attuned_ids: [id],   // attuned-but-not-slotted (e.g. bandoliers)
 *     readied_ids: [id],
 *   }
 *   InventoryItem = {
 *     id, name, category ("mundane"|"material"|"item"|"weapon"|"shield"
 *                           |"armor"|"accessory"|"consumable"|"magic"),
 *     qty, max_qty, handed (0|1|2), slot_hint,
 *     attune_required, ready_required, attuned, readied,
 *     equipped_to, charges_current, charges_max,
 *     effect, notes, source_kind ("derived"|"manual"|"pack"|"bundle"),
 *     source_id, source_label, macro_token,
 *   }
 */
import React, { useEffect, useMemo, useState } from "react";
import { api, formatApiErrorDetail } from "../../lib/api";
import { Plus, Trash2, Sparkles, Hand, Shield, Sword, Pill, Scroll, Coins, Edit3, X, Save } from "lucide-react";

const SLOTS = ["L-Hand", "R-Hand", "Head", "Torso", "Legs", "Feet"];

const CATEGORY_TABS = [
  { id: "all",        label: "All" },
  { id: "weapon",     label: "Weapons", icon: Sword },
  { id: "shield",     label: "Shields", icon: Shield },
  { id: "armor",      label: "Armor" },
  { id: "item",       label: "Items" },
  { id: "consumable", label: "Readied", icon: Pill },
  { id: "material",   label: "Materials" },
  { id: "mundane",    label: "Mundane", icon: Coins },
  { id: "magic",      label: "Magic", icon: Sparkles },
  { id: "accessory",  label: "Accessory" },
];

// ── helpers ────────────────────────────────────────────────────────
const newId = () =>
  (crypto?.randomUUID && crypto.randomUUID())
  || `inv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

function categoryFor(attr) {
  const n = (attr.name || "").toLowerCase();
  if (n === "weapon") return "weapon";
  if (n === "shield") return "shield";
  if (n === "armor" || n === "armour") return "armor";
  if (n === "item") return "item";
  if (n === "wealth") return "mundane";
  if (n === "healing") return "consumable";
  return null;
}

/** Auto-derive read-only inventory rows from BESM Attributes,
 * Power Packs, and Power Bundles. These rows mirror what the
 * builder owns; their qty / equip toggles still live in
 * folio.inventory_state.equipped / attuned_ids / readied_ids. */
function deriveRows(character) {
  const out = [];
  for (const attr of character.attributes || []) {
    const cat = categoryFor(attr);
    if (!cat) continue;
    out.push({
      id: `derived:attr:${attr.name}:${attr.custom_attribute_id || attr.name}`,
      name: attr.name === "Item"
        ? (attr.note ? attr.note.split("—")[0].trim() || attr.note.slice(0, 40) : "Item")
        : attr.name,
      category: cat,
      qty: cat === "consumable" ? attr.level : 1,
      max_qty: cat === "consumable" ? attr.level : 1,
      handed: attr.name === "Weapon" ? 1 : 0,
      slot_hint: attr.name === "Weapon"
        ? "R-Hand" : attr.name === "Shield"
        ? "L-Hand" : attr.name === "Armor"
        ? "Torso" : null,
      attune_required: cat === "item" || cat === "magic",
      ready_required: cat === "consumable",
      effect: attr.note || "",
      source_kind: "derived",
      source_label: `Attribute · ${attr.name} ×${attr.level}`,
      _readonly: true,
    });
  }
  for (const p of character.power_packs || []) {
    out.push({
      id: `derived:pack:${p.id || p.name}`,
      name: p.name,
      category: "magic",
      qty: 1, max_qty: 1, handed: 0,
      attune_required: true, ready_required: false,
      effect: p.blurb || "",
      source_kind: "pack",
      source_label: `Power Pack · ${p.cost_per_level || "?"} CP/lvl`,
      _readonly: true,
    });
  }
  for (const b of character.power_bundles || []) {
    out.push({
      id: `derived:bundle:${b.id || b.name}`,
      name: b.name,
      category: "magic",
      qty: 1, max_qty: 1, handed: 0,
      attune_required: true, ready_required: false,
      effect: b.blurb || "",
      source_kind: "bundle",
      source_label: `Bundle · ${b.total_cost ?? "?"} CP`,
      _readonly: true,
    });
  }
  return out;
}

/** Merge derived (read-only) rows with manual user rows, then overlay
 * equipped / attuned / readied state from inventory_state. */
function buildRows(character, invState) {
  const manual = (invState?.items || []).map((i) => ({ ...i, _readonly: false }));
  const derived = deriveRows(character);
  const all = [...derived, ...manual];
  const equipped = invState?.equipped || {};
  const attunedIds = new Set(invState?.attuned_ids || []);
  const readiedIds = new Set(invState?.readied_ids || []);
  // V6.25.39 — Per-item `handed` overrides for derived rows so the user
  // can mark a phoenix-staff "Weapon ×3" attribute as two-handed even
  // though the auto-deriver defaults to one-handed. Stored on
  // `inventory_state.handed_overrides = { [itemId]: 0|1|2 }`.
  const handedOverrides = invState?.handed_overrides || {};
  return all.map((it) => {
    const slotEntry = Object.entries(equipped).find(([, id]) => id === it.id);
    // Apply handed override if present (allows GM/player to flip a
    // derived 1-H weapon → 2-H for things like longbows, staves,
    // greatswords baked from a single BESM `Weapon ×N` attribute).
    const effectiveHanded = handedOverrides[it.id] !== undefined
      ? Number(handedOverrides[it.id])
      : it.handed;
    return {
      ...it,
      handed: effectiveHanded,
      equipped_to: slotEntry ? slotEntry[0] : null,
      attuned: attunedIds.has(it.id),
      readied: readiedIds.has(it.id),
    };
  });
}

// ── component ──────────────────────────────────────────────────────
export default function InventoryPanel({ character, canEdit, onChanged }) {
  const initial = character?.folio?.inventory_state || {
    items: [], equipped: {}, attuned_ids: [], readied_ids: [],
  };
  const [invState, setInvState] = useState(initial);
  const [tab, setTab] = useState("all");
  const [editingId, setEditingId] = useState(null);
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    setInvState(character?.folio?.inventory_state
                || { items: [], equipped: {}, attuned_ids: [], readied_ids: [] });
  }, [character?.id, character?.folio?.inventory_state]);

  const rows = useMemo(() => buildRows(character, invState),
                          [character, invState]);
  const filtered = tab === "all" ? rows : rows.filter((r) => r.category === tab);

  const persist = async (next) => {
    if (!character?.id) return;
    setBusy(true); setErr("");
    try {
      await api.patch(`/characters/${character.id}/folio`, {
        bucket: "inventory_state",
        patch: next,
      });
      setInvState((s) => ({ ...s, ...next }));
      onChanged && onChanged();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const upsertItem = async (item) => {
    const items = [...(invState.items || [])];
    const i = items.findIndex((x) => x.id === item.id);
    if (i >= 0) items[i] = item; else items.push({ ...item, id: item.id || newId() });
    await persist({ ...invState, items });
    setEditingId(null);
    setAdding(false);
  };

  const removeItem = async (id) => {
    const items = (invState.items || []).filter((x) => x.id !== id);
    const equipped = { ...(invState.equipped || {}) };
    Object.keys(equipped).forEach((s) => { if (equipped[s] === id) equipped[s] = null; });
    const attuned_ids = (invState.attuned_ids || []).filter((x) => x !== id);
    const readied_ids = (invState.readied_ids || []).filter((x) => x !== id);
    await persist({ ...invState, items, equipped, attuned_ids, readied_ids });
  };

  const toggleEquip = async (item) => {
    if (!item.slot_hint) return;
    const equipped = { ...(invState.equipped || {}) };
    const wantSlot = item.slot_hint;
    const handsNeeded = item.handed === 2 ? ["L-Hand", "R-Hand"] : [wantSlot];
    // un-equip toggle
    if (item.equipped_to) {
      handsNeeded.forEach((s) => { equipped[s] = null; });
      if (item.handed === 2) { equipped["L-Hand"] = null; equipped["R-Hand"] = null; }
      Object.keys(equipped).forEach((s) => { if (equipped[s] === item.id) equipped[s] = null; });
      return persist({ ...invState, equipped });
    }
    // Block if any required slot occupied.
    const blocked = handsNeeded.find((s) => equipped[s] && equipped[s] !== item.id);
    if (blocked) {
      setErr(`Slot ${blocked} is already occupied. Unequip first.`);
      setTimeout(() => setErr(""), 2400);
      return;
    }
    handsNeeded.forEach((s) => { equipped[s] = item.id; });
    return persist({ ...invState, equipped });
  };

  const toggleAttune = async (item) => {
    const set = new Set(invState.attuned_ids || []);
    if (set.has(item.id)) set.delete(item.id); else set.add(item.id);
    return persist({ ...invState, attuned_ids: [...set] });
  };

  const toggleReadied = async (item) => {
    const set = new Set(invState.readied_ids || []);
    if (set.has(item.id)) set.delete(item.id); else set.add(item.id);
    return persist({ ...invState, readied_ids: [...set] });
  };

  // V6.25.39 — Toggle one-handed ↔ two-handed for the current weapon.
  // For derived rows (auto-built from BESM Weapon attributes), persists
  // to `handed_overrides` so the player can mark "Eli's phoenix staff"
  // two-handed without touching the underlying attribute. For manual
  // rows, mutates the item's `handed` directly. When flipping a
  // currently-equipped weapon, also un-equips it so the player must
  // re-equip and see the new slot-claim block.
  const toggleHanded = async (item) => {
    const nextH = item.handed === 2 ? 1 : 2;
    let newState = { ...invState };
    if (item._readonly) {
      const overrides = { ...(invState.handed_overrides || {}) };
      overrides[item.id] = nextH;
      newState.handed_overrides = overrides;
    } else {
      newState.items = (invState.items || []).map((x) =>
        x.id === item.id ? { ...x, handed: nextH } : x);
    }
    // If currently equipped, un-equip so the slot claim re-evaluates.
    if (item.equipped_to) {
      const eq = { ...(invState.equipped || {}) };
      Object.keys(eq).forEach((s) => { if (eq[s] === item.id) eq[s] = null; });
      newState.equipped = eq;
    }
    return persist(newState);
  };

  const adjustCharges = async (item, delta) => {
    if (item._readonly) return;
    const items = (invState.items || []).map((x) => {
      if (x.id !== item.id) return x;
      const cur = Number(x.charges_current ?? x.charges_max ?? 0);
      const max = Number(x.charges_max ?? 0);
      const next = Math.max(0, Math.min(max || cur + delta, cur + delta));
      return { ...x, charges_current: next };
    });
    return persist({ ...invState, items });
  };

  return (
    <div className="space-y-4 mt-4" data-testid="inventory-panel">
      {/* Equipped summary — also rendered on Mechanics; this duplicate
          gives players a quick at-a-glance while inside Inventory. */}
      <EquippedStrip rows={rows} />

      <div className="card-mystic p-4 sm:p-5" data-testid="inventory-board">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
          <div className="flex flex-wrap gap-1" data-testid="inventory-tabs">
            {CATEGORY_TABS.map((t) => (
              <button key={t.id}
                      onClick={() => setTab(t.id)}
                      className={`px-2.5 py-1.5 text-[10px] uppercase tracking-widest font-ui rounded-sm border ${
                        tab === t.id
                          ? "bg-gold/15 text-gold-bright border-gold"
                          : "border-gold/15 text-mist hover:bg-gold/5"
                      }`}
                      data-testid={`inventory-tab-${t.id}`}>
                {t.label}
              </button>
            ))}
          </div>
          {canEdit && (
            <button onClick={() => setAdding(true)}
                    className="btn-ghost text-xs flex items-center gap-1"
                    data-testid="inventory-add-btn">
              <Plus className="w-3 h-3"/> Add item
            </button>
          )}
        </div>

        {err && <div className="text-ember text-xs mb-2"
                     data-testid="inventory-error">{err}</div>}

        {(adding || editingId) && (
          <ItemEditor
            initial={editingId
              ? rows.find((r) => r.id === editingId)
              : null}
            onSave={upsertItem}
            onCancel={() => { setAdding(false); setEditingId(null); }} />
        )}

        {filtered.length === 0 && !adding && (
          <div className="text-mist italic text-sm py-6 text-center"
               data-testid="inventory-empty">
            Nothing in this bucket yet.
            {canEdit && tab !== "all" && (
              <> Click <b>Add item</b> to drop one in.</>
            )}
          </div>
        )}

        <ul className="divide-y divide-gold/10" data-testid="inventory-rows">
          {filtered.map((r) => (
            <InventoryRow key={r.id}
                          item={r}
                          canEdit={canEdit}
                          busy={busy}
                          onEquip={() => toggleEquip(r)}
                          onAttune={() => toggleAttune(r)}
                          onReady={() => toggleReadied(r)}
                          onCharges={(d) => adjustCharges(r, d)}
                          onHanded={() => toggleHanded(r)}
                          onEdit={() => !r._readonly && setEditingId(r.id)}
                          onDelete={() => !r._readonly && removeItem(r.id)} />
          ))}
        </ul>
      </div>
    </div>
  );
}


// ── EquippedStrip ──────────────────────────────────────────────────
export function EquippedStrip({ rows }) {
  const byId = Object.fromEntries(rows.map((r) => [r.id, r]));
  const slotItems = SLOTS.map((s) => {
    const item = rows.find((r) => r.equipped_to === s);
    return { slot: s, item };
  });
  const attuned = rows.filter((r) => r.attuned && !r.equipped_to);
  const readied = rows.filter((r) => r.readied);
  return (
    <div className="card-mystic p-4 sm:p-5" data-testid="equipped-strip">
      <div className="flex items-center justify-between mb-2">
        <div className="label-ref flex items-center gap-2">
          <Hand className="w-3 h-3"/> Equipped
        </div>
        <div className="text-[10px] text-mist/60 italic">
          L · R · Head · Torso · Legs · Feet
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {slotItems.map(({ slot, item }) => (
          <div key={slot}
               className={`rounded-sm border p-2 text-xs ${
                 item ? "border-gold/40 bg-gold/5" : "border-gold/10"
               }`}
               data-testid={`equip-slot-${slot.toLowerCase()}`}>
            <div className="text-[10px] uppercase tracking-widest text-mist/70">{slot}</div>
            <div className={`mt-1 font-body ${item ? "text-parchment" : "text-mist/40 italic"}`}>
              {item ? item.name : "—"}
            </div>
            {item?.handed === 2 && (
              <div className="text-[10px] text-arcane-light italic">two-handed</div>
            )}
          </div>
        ))}
      </div>
      {(attuned.length > 0 || readied.length > 0) && (
        <div className="mt-3 grid sm:grid-cols-2 gap-3 text-xs">
          <div data-testid="equip-attuned-list">
            <div className="label-ref mb-1">Attuned (slotless)</div>
            {attuned.length === 0 && <div className="text-mist/40 italic">—</div>}
            {attuned.map((it) => (
              <div key={it.id} className="text-parchment">· {it.name}</div>
            ))}
          </div>
          <div data-testid="equip-readied-list">
            <div className="label-ref mb-1">Readied</div>
            {readied.length === 0 && <div className="text-mist/40 italic">—</div>}
            {readied.map((it) => (
              <div key={it.id} className="text-parchment">
                · {it.name}
                {it.charges_max != null && (
                  <span className="text-mist text-[10px] ml-1">
                    ({it.charges_current ?? it.charges_max}/{it.charges_max})
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


// ── InventoryRow ───────────────────────────────────────────────────
function InventoryRow({ item, canEdit, onEquip, onAttune, onReady,
                         onCharges, onEdit, onDelete, onHanded, busy }) {
  const i = item;
  const equippable = !!i.slot_hint;
  return (
    <li className="py-2 grid sm:grid-cols-[1fr_auto] gap-2 items-start"
        data-testid={`inventory-row-${i.id}`}>
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-body text-parchment text-sm">{i.name}</span>
          <span className="text-[10px] uppercase tracking-widest text-gold/70 font-ui">
            {i.category}
          </span>
          {i.qty > 1 && (
            <span className="text-[10px] text-mist">×{i.qty}</span>
          )}
          {i.handed > 0 && (
            <span className="text-[10px] text-arcane-light/80"
                  data-testid={`inv-handed-${i.id}`}>
              {i.handed === 2 ? "two-handed" : "one-handed"}
            </span>
          )}
          {i.source_label && (
            <span className="text-[10px] italic text-mist/60">{i.source_label}</span>
          )}
        </div>
        {i.effect && (
          <div className="text-[11px] text-mist mt-0.5 line-clamp-2">{i.effect}</div>
        )}
        {i.notes && (
          <div className="text-[11px] text-mist/70 italic mt-0.5">{i.notes}</div>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {i.charges_max != null && (
          <div className="flex items-center gap-1 mr-2"
               data-testid={`inv-charges-${i.id}`}>
            {canEdit && !i._readonly && (
              <button className="touch-target text-mist hover:text-ember"
                      onClick={() => onCharges(-1)}
                      disabled={busy}
                      title="Use a charge">−</button>
            )}
            <span className="font-display text-gold-bright">
              {i.charges_current ?? i.charges_max}
              <span className="text-mist text-[10px]">/{i.charges_max}</span>
            </span>
            {canEdit && !i._readonly && (
              <button className="touch-target text-mist hover:text-gold-bright"
                      onClick={() => onCharges(+1)}
                      disabled={busy}
                      title="Replenish">+</button>
            )}
          </div>
        )}
        {equippable && canEdit && (
          <Toggle on={!!i.equipped_to}
                  label={i.equipped_to ? `Eq · ${i.equipped_to}` : "Equip"}
                  onClick={onEquip}
                  testid={`inv-equip-${i.id}`} />
        )}
        {equippable && canEdit && i.slot_hint && ["L-Hand", "R-Hand"].includes(i.slot_hint) && (
          <Toggle on={i.handed === 2}
                  label={i.handed === 2 ? "2-H" : "1-H"}
                  onClick={onHanded}
                  testid={`inv-toggle-handed-${i.id}`}/>
        )}
        {i.attune_required && canEdit && (
          <Toggle on={i.attuned}
                  label={i.attuned ? "Attuned" : "Attune"}
                  onClick={onAttune}
                  testid={`inv-attune-${i.id}`} />
        )}
        {i.ready_required && canEdit && (
          <Toggle on={i.readied}
                  label={i.readied ? "Readied" : "Ready"}
                  onClick={onReady}
                  testid={`inv-ready-${i.id}`} />
        )}
        {!i._readonly && canEdit && (
          <>
            <button className="touch-target text-mist/60 hover:text-gold-bright"
                    title="Edit"
                    onClick={onEdit}
                    data-testid={`inv-edit-${i.id}`}>
              <Edit3 className="w-3.5 h-3.5"/>
            </button>
            <button className="touch-target text-mist/60 hover:text-ember"
                    title="Delete"
                    onClick={onDelete}
                    data-testid={`inv-delete-${i.id}`}>
              <Trash2 className="w-3.5 h-3.5"/>
            </button>
          </>
        )}
      </div>
    </li>
  );
}

function Toggle({ on, label, onClick, testid }) {
  return (
    <button onClick={onClick}
            className={`px-2 py-0.5 text-[10px] uppercase tracking-widest rounded-sm border font-ui ${
              on
                ? "bg-gold/15 text-gold-bright border-gold"
                : "border-gold/20 text-mist hover:bg-gold/5"
            }`}
            data-testid={testid}>
      {label}
    </button>
  );
}


// ── ItemEditor ─────────────────────────────────────────────────────
function ItemEditor({ initial, onSave, onCancel }) {
  const [it, setIt] = useState(() => initial || {
    id: "", name: "", category: "item", qty: 1, max_qty: 1, handed: 0,
    slot_hint: null, attune_required: false, ready_required: false,
    effect: "", notes: "",
    charges_current: null, charges_max: null, source_kind: "manual",
  });
  const set = (k, v) => setIt({ ...it, [k]: v });
  return (
    <div className="bg-void/60 border border-gold/20 rounded-sm p-3 mb-3 space-y-2"
         data-testid="inventory-editor">
      <div className="flex items-center justify-between">
        <div className="label-ref">{initial ? "Edit item" : "New item"}</div>
        <button onClick={onCancel}
                className="touch-target text-mist hover:text-ember"
                data-testid="inventory-editor-cancel">
          <X className="w-4 h-4"/>
        </button>
      </div>
      <div className="grid sm:grid-cols-2 gap-2">
        <input className="input" placeholder="Name"
               value={it.name} onChange={(e) => set("name", e.target.value)}
               data-testid="inventory-editor-name"/>
        <select className="select" value={it.category}
                onChange={(e) => set("category", e.target.value)}
                data-testid="inventory-editor-category">
          {CATEGORY_TABS.filter((c) => c.id !== "all").map((c) => (
            <option key={c.id} value={c.id}>{c.label}</option>
          ))}
        </select>
        <div className="flex items-center gap-2">
          <label className="text-[10px] uppercase tracking-widest text-mist">qty</label>
          <input type="number" className="input w-20" value={it.qty}
                 onChange={(e) => set("qty", +e.target.value)}/>
          <label className="text-[10px] uppercase tracking-widest text-mist">max</label>
          <input type="number" className="input w-20" value={it.max_qty || ""}
                 onChange={(e) => set("max_qty", +e.target.value)}/>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[10px] uppercase tracking-widest text-mist">handed</label>
          <select className="select" value={it.handed}
                  onChange={(e) => set("handed", +e.target.value)}>
            <option value={0}>—</option>
            <option value={1}>one-handed</option>
            <option value={2}>two-handed</option>
          </select>
          <label className="text-[10px] uppercase tracking-widest text-mist">slot</label>
          <select className="select" value={it.slot_hint || ""}
                  onChange={(e) => set("slot_hint", e.target.value || null)}>
            <option value="">—</option>
            {SLOTS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[10px] uppercase tracking-widest text-mist">charges</label>
          <input type="number" className="input w-20"
                 value={it.charges_current ?? ""}
                 placeholder="cur"
                 onChange={(e) => set("charges_current",
                                       e.target.value === "" ? null : +e.target.value)}/>
          <span className="text-mist">/</span>
          <input type="number" className="input w-20"
                 value={it.charges_max ?? ""}
                 placeholder="max"
                 onChange={(e) => set("charges_max",
                                       e.target.value === "" ? null : +e.target.value)}/>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-xs flex items-center gap-1">
            <input type="checkbox" checked={!!it.attune_required}
                   onChange={(e) => set("attune_required", e.target.checked)}/>
            Requires attunement
          </label>
          <label className="text-xs flex items-center gap-1">
            <input type="checkbox" checked={!!it.ready_required}
                   onChange={(e) => set("ready_required", e.target.checked)}/>
            Readied (consumable)
          </label>
        </div>
      </div>
      <textarea className="input" placeholder="Effect / mechanics"
                value={it.effect} onChange={(e) => set("effect", e.target.value)}/>
      <textarea className="input" placeholder="Notes (origin, lore, etc.)"
                value={it.notes} onChange={(e) => set("notes", e.target.value)}/>
      <div className="flex justify-end gap-2">
        <button className="btn-ghost text-xs" onClick={onCancel}
                data-testid="inventory-editor-cancel-btn">Cancel</button>
        <button className="btn text-xs flex items-center gap-1"
                onClick={() => onSave(it)}
                disabled={!it.name?.trim()}
                data-testid="inventory-editor-save">
          <Save className="w-3 h-3"/> Save
        </button>
      </div>
    </div>
  );
}
