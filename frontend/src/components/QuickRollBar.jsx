/**
 * QuickRollBar — V6.25.7
 *
 * Six clickable slots on the character sheet's Mechanics tab. Each slot
 * is either:
 *   • A user macro (click to roll into the most-recent channel as
 *     `/<macroname>` with an optional `+N` modifier injection field).
 *   • An empty slot — click to OPEN the macro creator inline. Per the
 *     user's V6.25.7 ask, slots are click-to-select OR click-to-create.
 *
 * State lives in the macros collection per campaign. The "select" mode
 * lets the player switch a slot to point at a different existing macro
 * without leaving the character sheet.
 */
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Plus, Dices, Trash2, Pencil, X } from "lucide-react";

const SLOT_COUNT = 6;
const SLOT_KEY = (charId) => `tg_qrb_slots_${charId}`;

export default function QuickRollBar({ character, campaignId, channelId, onRolled }) {
  const [macros, setMacros] = useState([]);
  const [slots, setSlots] = useState(() => {
    try { return JSON.parse(localStorage.getItem(SLOT_KEY(character?.id)) || "[]"); }
    catch { return []; }
  });
  const [picking, setPicking] = useState(null);          // index | null
  const [creating, setCreating] = useState(null);        // index | null
  const [modifierFor, setModifierFor] = useState(null);  // index | null
  const [modifier, setModifier] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!campaignId) return;
    api.get(`/campaigns/${campaignId}/macros`)
      .then((r) => setMacros(r.data || []))
      .catch(() => setMacros([]));
  }, [campaignId]);

  // Auto-fill from "most used" if the player has no manual selections yet.
  useEffect(() => {
    if (slots.length > 0 || macros.length === 0) return;
    const sorted = [...macros].sort((a, b) => (b.use_count || 0) - (a.use_count || 0));
    setSlots(sorted.slice(0, SLOT_COUNT).map((m) => m.id));
  }, [macros, slots.length]);

  // Persist slot picks per character.
  useEffect(() => {
    if (!character?.id) return;
    localStorage.setItem(SLOT_KEY(character.id), JSON.stringify(slots));
  }, [slots, character?.id]);

  const setSlot = (i, macroId) => {
    const next = [...slots]; next[i] = macroId; setSlots(next);
  };

  const fireMacro = async (macro, mod = "") => {
    if (!channelId) {
      setErr("No active channel — open the campaign chat first.");
      return;
    }
    setBusy(true); setErr("");
    try {
      const body = `/${macro.name}${mod ? ` ${mod.startsWith("+") || mod.startsWith("-") ? mod : "+" + mod}` : ""}`;
      const { data } = await api.post(`/channels/${channelId}/messages`,
        { body, attachments: [] });
      if (onRolled) onRolled(data);
      // Refresh use_count locally so sort-by-most-used responds.
      setMacros((prev) => prev.map((m) =>
        m.id === macro.id ? { ...m, use_count: (m.use_count || 0) + 1 } : m));
      setModifierFor(null); setModifier("");
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  };

  const onSlotClick = (i) => {
    const macroId = slots[i];
    if (!macroId) {
      // Empty slot — show picker (existing) or creator (new).
      setPicking(i);
      return;
    }
    const m = macros.find((x) => x.id === macroId);
    if (!m) { setSlot(i, null); return; }
    // Click on bound slot → open modifier injection mini-panel
    // before firing. Quick-fire (no modifier) is the second-tap.
    if (modifierFor === i) { fireMacro(m, modifier); return; }
    setModifierFor(i); setModifier("");
  };

  return (
    <div className="card-mystic p-4 mt-4" data-testid="quick-roll-bar">
      <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
        <div className="label-ref">Quick-Roll Bar</div>
        <div className="text-[10px] text-mist italic">
          Tap a slot to set a macro. Tap a bound slot to inject a modifier
          (advantage / edges / Effort) and fire.
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {Array.from({ length: SLOT_COUNT }).map((_, i) => {
          const macroId = slots[i];
          const m = macros.find((x) => x.id === macroId);
          if (!m) {
            return (
              <button key={i} onClick={() => onSlotClick(i)}
                      className="border border-dashed border-gold/30 rounded-sm p-3 min-h-[60px]
                                 hover:border-gold-bright hover:bg-gold/5 transition-colors text-mist/60"
                      data-testid={`qrb-slot-empty-${i}`}>
                <Plus className="w-4 h-4 mx-auto"/>
                <div className="text-[10px] uppercase tracking-widest mt-1">Slot {i+1}</div>
              </button>
            );
          }
          const isModifying = modifierFor === i;
          return (
            <div key={i} className={`border rounded-sm p-2 min-h-[60px] flex flex-col gap-1
                                        ${isModifying ? "border-gold-bright bg-gold/10" : "border-gold/30"}`}
                 data-testid={`qrb-slot-${i}`}>
              <div className="flex items-start justify-between gap-1">
                <button onClick={() => onSlotClick(i)}
                        className="flex-1 text-left text-parchment text-sm font-display leading-tight hover:text-gold-bright"
                        data-testid={`qrb-fire-${i}`}>
                  {m.label}
                </button>
                <button onClick={() => setPicking(i)}
                        className="text-mist/50 hover:text-gold-bright p-0.5"
                        title="Change macro on this slot"
                        data-testid={`qrb-change-${i}`}>
                  <Pencil className="w-3 h-3"/>
                </button>
              </div>
              <div className="text-[10px] text-mist/70 font-ui">{m.formula}</div>
              {isModifying && (
                <div className="flex gap-1 mt-1">
                  <input className="input select-sm flex-1 min-w-0" placeholder="+2"
                         value={modifier} autoFocus
                         onChange={(e) => setModifier(e.target.value)}
                         onKeyDown={(e) => { if (e.key === "Enter") fireMacro(m, modifier); }}
                         data-testid={`qrb-mod-input-${i}`}/>
                  <button onClick={() => fireMacro(m, modifier)} disabled={busy}
                          className="btn btn-primary text-xs"
                          data-testid={`qrb-fire-go-${i}`}>
                    <Dices className="w-3 h-3"/>
                  </button>
                  <button onClick={() => { setModifierFor(null); setModifier(""); }}
                          className="btn btn-ghost text-xs" data-testid={`qrb-cancel-${i}`}>
                    <X className="w-3 h-3"/>
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
      {err && <div className="text-ember text-[11px] mt-2" data-testid="qrb-error">{err}</div>}

      {picking !== null && (
        <SlotPicker
          slot={picking}
          macros={macros}
          onPick={(macroId) => { setSlot(picking, macroId); setPicking(null); }}
          onCreate={() => { setCreating(picking); setPicking(null); }}
          onUnbind={() => { setSlot(picking, null); setPicking(null); }}
          onClose={() => setPicking(null)}/>
      )}

      {creating !== null && (
        <MacroCreator
          campaignId={campaignId}
          onSaved={(m) => { setMacros([...macros, m]); setSlot(creating, m.id); setCreating(null); }}
          onClose={() => setCreating(null)}/>
      )}
    </div>
  );
}


function SlotPicker({ slot, macros, onPick, onCreate, onUnbind, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-void/80 flex items-center justify-center p-4"
         onClick={onClose}
         data-testid={`qrb-picker-${slot}`}>
      <div className="card-mystic p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="label-ref">Slot {slot + 1}</div>
            <div className="font-display text-lg text-parchment">Pick a macro</div>
          </div>
          <button onClick={onClose} className="text-mist hover:text-gold-bright" aria-label="Close">
            <X className="w-4 h-4"/>
          </button>
        </div>
        <div className="space-y-1 max-h-[50vh] overflow-y-auto">
          {macros.length === 0 && (
            <div className="text-mist italic text-[11px] text-center py-3">
              No macros yet — create your first below.
            </div>
          )}
          {macros.map((m) => (
            <button key={m.id} onClick={() => onPick(m.id)}
                    className="w-full text-left border border-gold/15 rounded-sm p-2 hover:border-gold/40 hover:bg-gold/5"
                    data-testid={`qrb-pick-${m.id}`}>
              <div className="text-parchment text-sm font-display">{m.label}</div>
              <div className="text-[10px] text-mist/70 font-ui">/{m.name} · {m.formula}</div>
            </button>
          ))}
        </div>
        <div className="flex justify-end gap-2 mt-4 flex-wrap">
          <button onClick={onUnbind} className="btn btn-ghost text-xs"
                  data-testid="qrb-picker-unbind">Unbind</button>
          <button onClick={onCreate} className="btn btn-primary text-xs"
                  data-testid="qrb-picker-create">
            <Plus className="w-3 h-3"/> New macro
          </button>
        </div>
      </div>
    </div>
  );
}


function MacroCreator({ campaignId, onSaved, onClose }) {
  const [name, setName] = useState("");
  const [formula, setFormula] = useState("");
  const [label, setLabel] = useState("");
  const [scope, setScope] = useState("user");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/campaigns/${campaignId}/macros`,
        { name, formula, label, scope });
      onSaved(data);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-void/80 flex items-center justify-center p-4"
         onClick={onClose}
         data-testid="qrb-creator">
      <form onSubmit={submit} className="card-mystic p-5 max-w-md w-full"
            onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="label-ref">New macro</div>
            <div className="text-[10px] text-mist italic mt-0.5">
              Tokens: STR / DEX / CON / INT / WIS / CHA · BODY / MIND / SOUL · PROF · LVL.
              They expand from your character's stats at fire time.
            </div>
          </div>
          <button type="button" onClick={onClose} className="text-mist hover:text-gold-bright"
                  aria-label="Close">
            <X className="w-4 h-4"/>
          </button>
        </div>
        <label className="label-ref block mb-1">Name (used as /name)</label>
        <input className="input mb-2" value={name} required pattern="[A-Za-z][A-Za-z0-9_-]{0,30}"
               placeholder="e.g. strike" autoFocus
               onChange={(e) => setName(e.target.value)}
               data-testid="qrb-creator-name"/>
        <label className="label-ref block mb-1">Label (display)</label>
        <input className="input mb-2" value={label}
               placeholder="e.g. Sword Strike"
               onChange={(e) => setLabel(e.target.value)}
               data-testid="qrb-creator-label"/>
        <label className="label-ref block mb-1">Formula</label>
        <input className="input mb-2" value={formula} required
               placeholder="1d20+STR+PROF"
               onChange={(e) => setFormula(e.target.value)}
               data-testid="qrb-creator-formula"/>
        <label className="label-ref block mb-1">Scope</label>
        <select className="select mb-2" value={scope}
                onChange={(e) => setScope(e.target.value)}
                data-testid="qrb-creator-scope">
          <option value="user">Personal (only me)</option>
          <option value="campaign">Campaign (everyone — GM-only)</option>
        </select>
        {err && <div className="text-ember text-[11px] mt-2"
                       data-testid="qrb-creator-error">{err}</div>}
        <div className="flex justify-end gap-2 mt-3">
          <button type="button" onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
          <button type="submit" disabled={busy} className="btn btn-primary text-xs"
                  data-testid="qrb-creator-save">
            {busy ? "Saving…" : "Save macro"}
          </button>
        </div>
      </form>
    </div>
  );
}
