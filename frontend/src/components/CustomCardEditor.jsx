/**
 * CustomCardEditor — V5.0 GM-side authoring surface for campaign-scoped
 * card decks. Lives next to the system catalogue inside CardDeckPanel.
 *
 * Each campaign can host any number of custom decks (character / npc /
 * cypher / weapon / item / generic). Cards are { name, suit, rank, effect }.
 * Saved decks appear in the spawn catalogue alongside system built-ins
 * with deck_id = "custom:{uuid}".
 */
import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, Save, Trash2, X, Edit3 } from "lucide-react";

const KIND_OPTIONS = [
  { v: "character", l: "Character / NPC cards" },
  { v: "npc",       l: "NPC roster" },
  { v: "cypher",    l: "Cyphers (Cypher System)" },
  { v: "weapon",    l: "Weapon cards" },
  { v: "item",      l: "Item / Loot cards" },
  { v: "generic",   l: "Generic / Mood / Plot" },
];

// Per-system kind suggestion — reorders the dropdown so the most likely
// option for that ruleset is first. Doesn't restrict; just sorts.
const KIND_HINT_BY_SYSTEM = {
  "cypher": ["cypher", "npc", "character", "item", "weapon", "generic"],
  "dnd-5e": ["item", "npc", "character", "weapon", "cypher", "generic"],
  "anime-5e": ["character", "npc", "item", "weapon", "cypher", "generic"],
  "besm-4e": ["generic", "npc", "character", "item", "weapon", "cypher"],
};

export default function CustomCardEditor({ campaignId, systemId, onChange }) {
  const [decks, setDecks] = useState([]);
  const [draft, setDraft] = useState(null);  // null = list view, {…} = editing
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      const { data } = await api.get(`/cards/custom-decks?campaign_id=${campaignId}`);
      setDecks(data || []);
      onChange?.();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, [campaignId]);

  const sortedKinds = (() => {
    const order = KIND_HINT_BY_SYSTEM[systemId] || KIND_HINT_BY_SYSTEM["besm-4e"];
    const map = Object.fromEntries(KIND_OPTIONS.map((k) => [k.v, k]));
    return order.map((v) => map[v]).filter(Boolean);
  })();

  const startNew = () => setDraft({
    id: null, name: "", kind: sortedKinds[0]?.v || "generic", cards: [],
  });
  const startEdit = (d) => setDraft({ ...d, cards: [...(d.cards || [])] });

  const save = async () => {
    if (!draft.name.trim()) { setErr("Deck needs a name."); return; }
    setBusy(true); setErr("");
    try {
      const cards = draft.cards.map((c) => ({
        name: c.name, suit: c.suit || "", rank: c.rank || "",
        effect: c.effect || "",
      })).filter((c) => c.name.trim());
      if (draft.id) {
        await api.patch(`/cards/custom-decks/${draft.id}`,
                         { name: draft.name, kind: draft.kind, cards });
      } else {
        await api.post(`/cards/custom-decks`,
                        { campaign_id: campaignId, name: draft.name,
                          kind: draft.kind, cards });
      }
      setDraft(null);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this deck and any active draws from it?")) return;
    try {
      await api.delete(`/cards/custom-decks/${id}`);
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  const addCard = () => setDraft({ ...draft,
    cards: [...draft.cards, { name: "", suit: "", rank: "", effect: "" }] });
  const setCard = (i, patch) => {
    const cards = draft.cards.slice();
    cards[i] = { ...cards[i], ...patch };
    setDraft({ ...draft, cards });
  };
  const removeCard = (i) => setDraft({ ...draft,
    cards: draft.cards.filter((_, j) => j !== i) });

  return (
    <div className="card-mystic p-4 mt-4" data-testid="custom-card-editor"
         data-system={systemId}>
      <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Edit3 className="w-3 h-3"/> Custom Decks
          </div>
          <div className="text-[10px] text-mist/70 italic">
            GM-authored decks for this campaign.
            {systemId === "cypher" && " (Custom cyphers, types, foci, intrusions, NPC cards.)"}
            {systemId === "dnd-5e" && " (Magic items, NPC cards, encounter prompts, loot tables.)"}
            {systemId === "anime-5e" && " (Genre cards, character beats, mecha gear, loot.)"}
            {systemId === "besm-4e" && " (Mood, NPC, item, or any narrative ceremony deck.)"}
          </div>
        </div>
        {!draft && (
          <button onClick={startNew} className="btn btn-primary text-xs"
                  data-testid="custom-deck-new-btn">
            <Plus className="w-3 h-3"/> New deck
          </button>
        )}
      </div>
      {err && <div className="text-ember text-xs mb-2" data-testid="custom-deck-err">{err}</div>}

      {!draft ? (
        decks.length === 0 ? (
          <div className="text-mist italic text-xs">No custom decks yet.</div>
        ) : (
          <div className="space-y-2">
            {decks.map((d) => (
              <div key={d.id}
                   className="border border-gold/15 rounded-sm p-3 flex items-center justify-between gap-2 flex-wrap"
                   data-testid={`custom-deck-${d.id}`}>
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-parchment font-ui truncate">
                    <b>{d.name}</b>
                    <span className="text-[10px] text-mist ml-2 uppercase tracking-widest">{d.kind}</span>
                  </div>
                  <div className="text-[10px] text-mist/70">
                    {(d.cards || []).length} cards · authored by {d.created_by}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => startEdit(d)} className="btn btn-ghost text-xs"
                          data-testid={`custom-deck-edit-${d.id}`}>
                    <Edit3 className="w-3 h-3"/>
                  </button>
                  <button onClick={() => remove(d.id)} className="btn btn-ghost text-xs text-ember/70"
                          data-testid={`custom-deck-delete-${d.id}`}>
                    <Trash2 className="w-3 h-3"/>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        // Editor
        <div className="border border-gold/30 rounded-sm p-3 bg-gold/5 space-y-3"
             data-testid="custom-deck-editor">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input className="input col-span-2" placeholder="Deck name (e.g. 'Aurean Reagent Cyphers')"
                   value={draft.name}
                   onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                   data-testid="custom-deck-name"/>
            <select className="select" value={draft.kind}
                    onChange={(e) => setDraft({ ...draft, kind: e.target.value })}
                    data-testid="custom-deck-kind">
              {sortedKinds.map((k) => (
                <option key={k.v} value={k.v}>{k.l}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2 max-h-96 overflow-auto">
            {draft.cards.map((c, i) => (
              <div key={i} className="border border-gold/15 rounded-sm p-2 space-y-1.5"
                   data-testid={`custom-card-${i}`}>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-1.5">
                  <input className="input col-span-2" placeholder="Card name"
                         value={c.name}
                         onChange={(e) => setCard(i, { name: e.target.value })}
                         data-testid={`custom-card-name-${i}`}/>
                  <input className="input" placeholder={draft.kind === "cypher" ? "Form (Patch / Vial …)" : "Suit / Group"}
                         value={c.suit || ""}
                         onChange={(e) => setCard(i, { suit: e.target.value })}
                         data-testid={`custom-card-suit-${i}`}/>
                  <div className="flex gap-1">
                    <input className="input flex-1" placeholder={draft.kind === "cypher" ? "Level (e.g. 1d6+1)" : "Rank"}
                           value={c.rank || ""}
                           onChange={(e) => setCard(i, { rank: e.target.value })}
                           data-testid={`custom-card-rank-${i}`}/>
                    <button onClick={() => removeCard(i)} className="btn btn-ghost text-xs text-ember/70"
                            data-testid={`custom-card-remove-${i}`}>
                      <X className="w-3 h-3"/>
                    </button>
                  </div>
                </div>
                <textarea className="input min-h-[44px] text-sm"
                          placeholder={
                            draft.kind === "cypher"
                              ? "Mechanic effect (no rulebook prose) — e.g. '+5 Armor for 1 hour'"
                              : draft.kind === "character" || draft.kind === "npc"
                              ? "Stat block / role description"
                              : "Effect / description"
                          }
                          value={c.effect || ""}
                          onChange={(e) => setCard(i, { effect: e.target.value })}
                          data-testid={`custom-card-effect-${i}`}/>
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center gap-2 flex-wrap">
            <button onClick={addCard} type="button" className="btn btn-ghost text-xs"
                    data-testid="custom-card-add">
              <Plus className="w-3 h-3"/> Add card ({draft.cards.length})
            </button>
            <div className="flex gap-2">
              <button onClick={() => setDraft(null)} className="btn btn-ghost text-xs"
                      data-testid="custom-deck-cancel">Cancel</button>
              <button onClick={save} disabled={busy} className="btn btn-primary text-xs"
                      data-testid="custom-deck-save">
                <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save deck"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
