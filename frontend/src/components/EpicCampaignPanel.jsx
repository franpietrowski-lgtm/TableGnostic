import React, { useEffect, useState, useMemo } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Plus, X, Save, Sparkles, Skull, Target, Quote, ListTree,
  Wand2, Compass, Eye, Mountain, Crown, Library, Link as LinkIcon,
  ChevronDown, ChevronRight,
} from "lucide-react";

/**
 * EpicCampaignPanel — Sclanders' "Epic Campaigns" framework.
 *
 * Companion to the existing 7-phase Genesis Master-Plot. Designed to be used
 * INDEPENDENTLY, in tandem, or one-or-the-other — pure GM brainstorming kit.
 *
 * Sections (matching the book's chapter order):
 *   1. The Plan & Constraints                 (ch.1-2)
 *   2. Theme not Tone                          (ch.5)
 *   3. The Sentence                            (ch.7)
 *   4. Nemesis · OGAS framework                (ch.3-4, 8, 11)
 *   5. Villains & Henchmen                     (ch.3, 11)
 *   6. Expanding Goal Table                    (ch.8.3)
 *   7. Plan → Milestones (POE per milestone)   (ch.9)
 *   8. Adventures (mode + type tagging)        (ch.10)
 *   9. Seeding (names/places/objects/people)   (ch.12)
 *  10. Beginning Adventure (POE templates)     (ch.13)
 *  11. Climax & Ending                         (ch.14)
 *
 * "Sync to Codex" pushes the Nemesis + each Villain + each Seed into the
 * World Codex as gm_only nodes — idempotent (re-run is a no-op until the
 * GM edits the entity). Linked node ids are persisted on the entity so
 * the Codex copy stays in sync on subsequent edits.
 */
export default function EpicCampaignPanel({ campId, characters: charactersProp, nodes: nodesProp }) {
  const [state, setState] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [fetchedCharacters, setFetchedCharacters] = useState([]);
  const [fetchedNodes, setFetchedNodes] = useState([]);
  const characters = charactersProp ?? fetchedCharacters;
  const nodes = nodesProp ?? fetchedNodes;
  const [open, setOpen] = useState({
    fundamentals: true, theme: false, sentence: true,
    nemesis: true, villains: false, expanding: false,
    milestones: true, adventures: false, seeds: false,
    beginning: false, climax: false, links: false,
  });

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/epic/${campId}`);
        setState(data);
      } catch (e) {
        setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    })();
  }, [campId]);

  // If the parent didn't pre-fetch the linkable lists, fetch them ourselves so
  // the Tie-ins picker has options to select from.
  useEffect(() => {
    if (!campId) return;
    if (!charactersProp) {
      api.get(`/campaigns/${campId}/characters`)
        .then((r) => setFetchedCharacters(Array.isArray(r.data) ? r.data : []))
        .catch(() => {});
    }
    if (!nodesProp) {
      api.get(`/campaigns/${campId}/nodes`)
        .then((r) => setFetchedNodes(Array.isArray(r.data) ? r.data : []))
        .catch(() => {});
    }
  }, [campId, charactersProp, nodesProp]);

  const save = async () => {
    if (!state) return;
    setBusy(true); setErr("");
    try {
      const payload = { ...state };
      delete payload.campaign_id;
      delete payload.updated_at;
      const { data } = await api.put(`/epic/${campId}`, payload);
      setState(data);
      setSavedAt(Date.now());
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  const seedToCodex = async () => {
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/epic/${campId}/seed-codex`);
      setState(data.epic);
      window.alert(
        data.nodes_created > 0
          ? `Synced — ${data.nodes_created} new Codex node${data.nodes_created === 1 ? "" : "s"} created (gm-only).`
          : "Already in sync — no new nodes were needed."
      );
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  const setField = (k, v) => setState((s) => ({ ...s, [k]: v }));
  const setSentence = (patch) => setState((s) => ({ ...s, sentence: { ...s.sentence, ...patch } }));
  const setNemesis = (patch) => setState((s) => ({ ...s, nemesis: { ...s.nemesis, ...patch } }));
  const setBeginning = (patch) => setState((s) => ({ ...s, beginning: { ...s.beginning, ...patch } }));
  const setEndingCool = (patch) => setState((s) => ({ ...s, ending_coolness: { ...s.ending_coolness, ...patch } }));

  // List helpers
  const addToList = (k, blank) => setState((s) => ({ ...s, [k]: [...(s[k] || []), blank] }));
  const removeFromList = (k, i) => setState((s) => {
    const arr = [...(s[k] || [])]; arr.splice(i, 1); return { ...s, [k]: arr };
  });
  const updateInList = (k, i, patch) => setState((s) => {
    const arr = [...(s[k] || [])]; arr[i] = { ...arr[i], ...patch }; return { ...s, [k]: arr };
  });

  const characterOptions = useMemo(
    () => characters.map((c) => ({ id: c.id, name: c.name || "(unnamed)" })),
    [characters]
  );
  const nodeOptions = useMemo(
    () => (nodes || []).map((n) => ({ id: n.id, title: n.title })),
    [nodes]
  );

  if (err) return <div className="text-ember" data-testid="epic-error">{err}</div>;
  if (!state) return <div className="text-mist italic font-body text-xs">Summoning the Epic Campaign Plan…</div>;

  return (
    <div className="space-y-4" data-testid="epic-campaign-panel">
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div>
          <div className="label-ref">Epic Campaign · Sclanders Framework</div>
          <h3 className="font-display text-xl text-parchment mt-1">The Plan, the Nemesis, the Pay-off</h3>
          <div className="text-[11px] font-ui text-mist/70 italic mt-1 max-w-3xl">
            Independent of (or alongside) the 7-phase Master Plot above. Brainstorm the Nemesis and their Plan,
            seed the table, design Adventures by mode and type, then pay it all off at a Cool climax.
            Use whatever sections speak to you — every field is optional.
          </div>
        </div>
        <div className="flex items-center gap-2">
          {savedAt && (
            <span className="text-[10px] text-arcane-light italic" data-testid="epic-saved-tick">
              Saved · {new Date(savedAt).toLocaleTimeString()}
            </span>
          )}
          <button onClick={seedToCodex} disabled={busy}
                  className="btn btn-ghost text-xs" data-testid="epic-sync-codex-btn"
                  title="Push the Nemesis, Villains and Seeds into the World Codex as gm-only nodes.">
            <Library className="w-3 h-3"/> Sync to Codex
          </button>
          <button onClick={save} disabled={busy}
                  className="btn btn-primary text-xs" data-testid="epic-save-btn">
            <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {/* 1. Fundamentals */}
      <Section title="1 · The Plan & Constraints" icon={<Compass className="w-3.5 h-3.5"/>}
               testid="epic-section-fundamentals" open={open.fundamentals} onToggle={() => setOpen({ ...open, fundamentals: !open.fundamentals })}>
        <Field label="Plan summary"
               help="One paragraph: what the table is being asked to live through. The Plan is what the Nemesis intends — not what will happen."
               testid="epic-plan-summary">
          <textarea className="input min-h-[70px]" value={state.plan_summary}
                    onChange={(e) => setField("plan_summary", e.target.value)}
                    placeholder="The Order of the Darkening Star intends to shatter the Solar-Lunar Caldera and free the Eclipse Saint."
                    data-testid="epic-plan-summary-input"/>
        </Field>
        <div className="grid md:grid-cols-3 gap-3">
          <Field label="System constraint" help="Whatever the system rewards or punishes shapes the Plan." testid="epic-constraint-system">
            <input className="input" value={state.constraints_system}
                   onChange={(e) => setField("constraints_system", e.target.value)}
                   placeholder="BESM 4E · narrative-lethal at high tier"
                   data-testid="epic-constraint-system-input"/>
          </Field>
          <Field label="Longevity constraint" help="Sessions you've actually got. Be honest." testid="epic-constraint-longevity">
            <input className="input" value={state.constraints_longevity}
                   onChange={(e) => setField("constraints_longevity", e.target.value)}
                   placeholder="~24 sessions over 8 months"
                   data-testid="epic-constraint-longevity-input"/>
          </Field>
          <Field label="Table constraint" help="Players' tone, lethality, and content boundaries." testid="epic-constraint-table">
            <input className="input" value={state.constraints_table}
                   onChange={(e) => setField("constraints_table", e.target.value)}
                   placeholder="Heroic with consequences. No on-screen torture."
                   data-testid="epic-constraint-table-input"/>
          </Field>
        </div>
      </Section>

      {/* 2. Theme */}
      <Section title="2 · Theme (not Tone)" icon={<Sparkles className="w-3.5 h-3.5"/>}
               testid="epic-section-theme" open={open.theme} onToggle={() => setOpen({ ...open, theme: !open.theme })}>
        <div className="grid md:grid-cols-2 gap-3">
          <Field label="Theme" help="A single declarative claim the campaign will argue. e.g. 'Faith demands proof.'" testid="epic-theme">
            <input className="input" value={state.theme}
                   onChange={(e) => setField("theme", e.target.value)}
                   placeholder="Faith demands proof."
                   data-testid="epic-theme-input"/>
          </Field>
          <Field label="How might the theme evolve?" help="The theme can mutate as the table interrogates it. Note where you'd let it bend." testid="epic-theme-evol">
            <input className="input" value={state.theme_evolution}
                   onChange={(e) => setField("theme_evolution", e.target.value)}
                   placeholder="By Act III: 'Proof is a hollow thing without faith.'"
                   data-testid="epic-theme-evol-input"/>
          </Field>
        </div>
      </Section>

      {/* 3. The Sentence */}
      <Section title="3 · The Sentence" icon={<Quote className="w-3.5 h-3.5"/>}
               testid="epic-section-sentence" open={open.sentence} onToggle={() => setOpen({ ...open, sentence: !open.sentence })}>
        <div className="grid md:grid-cols-2 gap-3">
          <Field label="Someone…" help="Your Nemesis, by name." testid="epic-sentence-someone">
            <input className="input" value={state.sentence.someone}
                   onChange={(e) => setSentence({ someone: e.target.value })}
                   placeholder="Malshe Darkening" data-testid="epic-sentence-someone-input"/>
          </Field>
          <Field label="…wants something" help="The McGuffin. The thing." testid="epic-sentence-wants">
            <input className="input" value={state.sentence.wants}
                   onChange={(e) => setSentence({ wants: e.target.value })}
                   placeholder="The Forge-Glass Hammer" data-testid="epic-sentence-wants-input"/>
          </Field>
          <Field label="…in a timeframe" help="A clock. Everything is more interesting when there's a clock." testid="epic-sentence-when">
            <input className="input" value={state.sentence.timeframe}
                   onChange={(e) => setSentence({ timeframe: e.target.value })}
                   placeholder="Before the Solar Eclipse, in 8 sessions"
                   data-testid="epic-sentence-when-input"/>
          </Field>
          <Field label="…by a method" help="Manipulation, Minions, or Objects (or a mix)." testid="epic-sentence-method">
            <select className="select" value={state.sentence.method || ""}
                    onChange={(e) => setSentence({ method: e.target.value })}
                    data-testid="epic-sentence-method-input">
              <option value="">— pick one —</option>
              <option value="manipulation">Manipulation</option>
              <option value="minions">Minions</option>
              <option value="objects">Objects</option>
              <option value="mixed">Mixed</option>
            </select>
            <input className="input mt-1.5" value={state.sentence.method_detail}
                   onChange={(e) => setSentence({ method_detail: e.target.value })}
                   placeholder="e.g. through the Iron-Cantor's choir"
                   data-testid="epic-sentence-method-detail"/>
          </Field>
        </div>
        <Field label="Refined sentence" help="One line, said out loud. This is the campaign you're actually running." testid="epic-sentence-refined">
          <textarea className="input min-h-[55px] italic" value={state.sentence.refined}
                    onChange={(e) => setSentence({ refined: e.target.value })}
                    placeholder="Malshe Darkening wants the Forge-Glass Hammer before the Solar Eclipse, manipulating the Iron-Cantor's choir to do it."
                    data-testid="epic-sentence-refined-input"/>
        </Field>
      </Section>

      {/* 4. Nemesis */}
      <Section title="4 · Nemesis · OGAS" icon={<Skull className="w-3.5 h-3.5"/>}
               testid="epic-section-nemesis" open={open.nemesis} onToggle={() => setOpen({ ...open, nemesis: !open.nemesis })}>
        <NpcEditor entity={state.nemesis} onPatch={setNemesis} testidPrefix="epic-nemesis" lockedRole="nemesis"/>
      </Section>

      {/* 5. Villains & Henchmen */}
      <Section title="5 · Villains & Henchmen" icon={<Target className="w-3.5 h-3.5"/>}
               testid="epic-section-villains" open={open.villains} onToggle={() => setOpen({ ...open, villains: !open.villains })}
               action={
                 <button onClick={() => addToList("villains", { name: "", role: "villain", occupation: "", attitude: "", goal: "", stake: "", desire: "other", psychology: "other", weakness: "", weakness_kind: "none", notes: "" })}
                         className="btn btn-ghost text-xs" data-testid="epic-add-villain">
                   <Plus className="w-3 h-3"/> Villain
                 </button>
               }>
        {(state.villains || []).length === 0 && (
          <div className="text-mist italic font-body text-xs">No villains yet. The Nemesis is the puppeteer; villains are the hands.</div>
        )}
        <div className="space-y-3">
          {(state.villains || []).map((v, i) => (
            <div key={v.id || i} className="border border-gold/15 rounded-sm p-3" data-testid={`epic-villain-${i}`}>
              <div className="flex justify-end mb-1">
                <button onClick={() => removeFromList("villains", i)} className="text-ember/70 hover:text-ember"
                        data-testid={`epic-villain-${i}-remove`}><X className="w-4 h-4"/></button>
              </div>
              <NpcEditor entity={v} onPatch={(patch) => updateInList("villains", i, patch)}
                         testidPrefix={`epic-villain-${i}`}/>
            </div>
          ))}
        </div>
      </Section>

      {/* 6. Expanding Goal */}
      <Section title="6 · Expanding Goal Table" icon={<Mountain className="w-3.5 h-3.5"/>}
               testid="epic-section-expanding" open={open.expanding} onToggle={() => setOpen({ ...open, expanding: !open.expanding })}>
        <div className="text-[11px] text-mist/70 italic mb-2">
          Each entry: a side-effect of the Nemesis pursuing their Goal. NPCs displaced. Cities burned. Trade-routes diverted.
          When the PCs finally engage, these are the consequences they have to clean up — or fail to.
        </div>
        <ChipList items={state.expanding_goal} setItems={(v) => setField("expanding_goal", v)}
                  placeholder="A new consequence of the Plan unfolding"
                  testid="epic-expanding-goal"/>
      </Section>

      {/* 7. Plan → Milestones */}
      <Section title="7 · Milestones · the Plan" icon={<ListTree className="w-3.5 h-3.5"/>}
               testid="epic-section-milestones" open={open.milestones} onToggle={() => setOpen({ ...open, milestones: !open.milestones })}
               action={
                 <button onClick={() => addToList("milestones", { title: "", sequence: (state.milestones || []).length + 1, obstacles: [], resources_have: [], resources_needed: [], poe_problem: "", poe_obstacle: "", poe_event: "", completed: false })}
                         className="btn btn-ghost text-xs" data-testid="epic-add-milestone">
                   <Plus className="w-3 h-3"/> Milestone
                 </button>
               }>
        {(state.milestones || []).length === 0 && <div className="text-mist italic font-body text-xs">Nemesis Goal → milestones → obstacles → resources → tasks.</div>}
        <div className="space-y-3">
          {(state.milestones || []).map((m, i) => (
            <MilestoneEditor key={m.id || i} m={m} idx={i}
                             onPatch={(p) => updateInList("milestones", i, p)}
                             onRemove={() => removeFromList("milestones", i)}/>
          ))}
        </div>
      </Section>

      {/* 8. Adventures */}
      <Section title="8 · Adventures · mode + type" icon={<Wand2 className="w-3.5 h-3.5"/>}
               testid="epic-section-adventures" open={open.adventures} onToggle={() => setOpen({ ...open, adventures: !open.adventures })}
               action={
                 <button onClick={() => addToList("adventures", { title: "", mode: "advancing-campaign", type: "nemesis-on-track", summary: "", events: [], linked_milestone_id: null, linked_pc_ids: [] })}
                         className="btn btn-ghost text-xs" data-testid="epic-add-adventure">
                   <Plus className="w-3 h-3"/> Adventure
                 </button>
               }>
        {(state.adventures || []).length === 0 && (
          <div className="text-mist italic font-body text-xs">
            Three modes (Advancing-Campaign / Advancing-PCs / Enhancing-Game) and 8 types. Tag every adventure so the campaign breathes.
          </div>
        )}
        <div className="space-y-3">
          {(state.adventures || []).map((a, i) => (
            <AdventureEditor key={a.id || i} a={a} idx={i}
                             milestones={state.milestones || []}
                             characterOptions={characterOptions}
                             onPatch={(p) => updateInList("adventures", i, p)}
                             onRemove={() => removeFromList("adventures", i)}/>
          ))}
        </div>
      </Section>

      {/* 9. Seeds */}
      <Section title="9 · Seeds · make it seem planned" icon={<Eye className="w-3.5 h-3.5"/>}
               testid="epic-section-seeds" open={open.seeds} onToggle={() => setOpen({ ...open, seeds: !open.seeds })}
               action={
                 <button onClick={() => addToList("seeds", { kind: "name", label: "", payoff: "", seeded_in: "", paid_off: false })}
                         className="btn btn-ghost text-xs" data-testid="epic-add-seed">
                   <Plus className="w-3 h-3"/> Seed
                 </button>
               }>
        <div className="text-[11px] text-mist/70 italic mb-2">
          Names, places, objects, people, dreams, portents, omens. Drop them in early. Pay them off later.
          Mark them PAID OFF when the table notices.
        </div>
        {(state.seeds || []).length === 0 && <div className="text-mist italic font-body text-xs">No seeds drafted yet.</div>}
        <div className="space-y-2">
          {(state.seeds || []).map((s, i) => (
            <SeedRow key={s.id || i} s={s} idx={i}
                     onPatch={(p) => updateInList("seeds", i, p)}
                     onRemove={() => removeFromList("seeds", i)}/>
          ))}
        </div>
      </Section>

      {/* 10. Beginning */}
      <Section title="10 · Beginning Adventure" icon={<Compass className="w-3.5 h-3.5"/>}
               testid="epic-section-beginning" open={open.beginning} onToggle={() => setOpen({ ...open, beginning: !open.beginning })}>
        <div className="grid md:grid-cols-2 gap-3">
          <Field label="POE template" help="Sclanders ch.13 — pick the open that pulls your table in fastest." testid="epic-beginning-kind">
            <select className="select" value={state.beginning.kind || ""}
                    onChange={(e) => setBeginning({ kind: e.target.value })}
                    data-testid="epic-beginning-kind-input">
              <option value="">— pick one —</option>
              <option value="gigantic-battle">Gigantic battle sequence</option>
              <option value="common-backstory">Common backstory</option>
              <option value="awkward-inn">The awkward inn</option>
              <option value="common-problem">Common problem</option>
              <option value="pre-game-game">Pre-game game</option>
              <option value="prologue-cutaway">Prologue: cut-away sequence</option>
              <option value="flash-forward">Flash-forward</option>
              <option value="order-hire">Order / hire</option>
              <option value="personal-attack">Personal attack</option>
            </select>
          </Field>
          <Field label="Open notes" help="What's the very first scene? Who's there, what's at stake?" testid="epic-beginning-notes">
            <textarea className="input min-h-[55px]" value={state.beginning.notes}
                      onChange={(e) => setBeginning({ notes: e.target.value })}
                      placeholder="Open with the apprentices being assigned the Maiden Adventure by the Mayor."
                      data-testid="epic-beginning-notes-input"/>
          </Field>
        </div>
      </Section>

      {/* 11. Climax */}
      <Section title="11 · Climax & Ending" icon={<Crown className="w-3.5 h-3.5"/>}
               testid="epic-section-climax" open={open.climax} onToggle={() => setOpen({ ...open, climax: !open.climax })}>
        <div className="text-[11px] text-mist/70 italic mb-2">
          Coolness Factors — the five levers Sclanders pulls to make the climax memorable. Plus the four C's of Climax.
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          <Field label="Location" help="Where does the climax happen? It should mean something." testid="epic-cool-location">
            <input className="input" value={state.ending_coolness.location}
                   onChange={(e) => setEndingCool({ location: e.target.value })}
                   placeholder="Solar-Lunar Caldera, mid-eclipse"
                   data-testid="epic-cool-location-input"/>
          </Field>
          <Field label="Abilities" help="Which PC abilities should shine?" testid="epic-cool-abilities">
            <input className="input" value={state.ending_coolness.abilities}
                   onChange={(e) => setEndingCool({ abilities: e.target.value })}
                   placeholder="Eli's Healing-at-Range; Roney's Pocket Detonation"
                   data-testid="epic-cool-abilities-input"/>
          </Field>
          <Field label="NPCs" help="Who shows up that nobody expected?" testid="epic-cool-npcs">
            <input className="input" value={state.ending_coolness.npcs}
                   onChange={(e) => setEndingCool({ npcs: e.target.value })}
                   placeholder="Mishtee returns. Frock changes sides."
                   data-testid="epic-cool-npcs-input"/>
          </Field>
          <Field label="Situation" help="What's the situation that nobody can ignore?" testid="epic-cool-situation">
            <input className="input" value={state.ending_coolness.situation}
                   onChange={(e) => setEndingCool({ situation: e.target.value })}
                   placeholder="The Caldera cracks open as the eclipse begins."
                   data-testid="epic-cool-situation-input"/>
          </Field>
          <Field label="Pressure" help="What's the clock?" testid="epic-cool-pressure">
            <input className="input" value={state.ending_coolness.pressure}
                   onChange={(e) => setEndingCool({ pressure: e.target.value })}
                   placeholder="Eclipse totality lasts 4 minutes."
                   data-testid="epic-cool-pressure-input"/>
          </Field>
        </div>
        <div className="grid md:grid-cols-2 gap-3 mt-3">
          <Field label="Chaos & Calm" help="Where does the table catch its breath inside the climax?" testid="epic-end-chaos">
            <textarea className="input min-h-[55px]" value={state.ending_chaos_calm}
                      onChange={(e) => setField("ending_chaos_calm", e.target.value)}
                      data-testid="epic-end-chaos-input"/>
          </Field>
          <Field label="Contingency" help="What's your fallback if the table breaks the climax?" testid="epic-end-contingency">
            <textarea className="input min-h-[55px]" value={state.ending_contingency}
                      onChange={(e) => setField("ending_contingency", e.target.value)}
                      data-testid="epic-end-contingency-input"/>
          </Field>
          <Field label="Catastrophic consequences" help="What changes for the world if the PCs fail?" testid="epic-end-consequences">
            <textarea className="input min-h-[55px]" value={state.ending_consequences}
                      onChange={(e) => setField("ending_consequences", e.target.value)}
                      data-testid="epic-end-consequences-input"/>
          </Field>
          <Field label="Climax beats" help="Just the bullet-points of how it plays out at the table." testid="epic-end-climax">
            <textarea className="input min-h-[55px]" value={state.ending_climax}
                      onChange={(e) => setField("ending_climax", e.target.value)}
                      data-testid="epic-end-climax-input"/>
          </Field>
        </div>
      </Section>

      {/* Linked tie-ins */}
      <Section title="Tie-ins · Codex / Characters / References" icon={<LinkIcon className="w-3.5 h-3.5"/>}
               testid="epic-section-links" open={open.links} onToggle={() => setOpen({ ...open, links: !open.links })}>
        <div className="text-[11px] text-mist/70 italic mb-2">
          Optional cross-links — the Plan can pull Codex nodes, PCs, and the Atelier reference items into one mental model.
          These are pure pointers; nothing here is destructive.
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          <PickList label="Linked Codex nodes" items={state.linked_node_ids || []}
                    setItems={(v) => setField("linked_node_ids", v)}
                    options={nodeOptions.map((n) => ({ value: n.id, label: n.title }))}
                    testid="epic-link-nodes"/>
          <PickList label="Linked Characters" items={state.linked_character_ids || []}
                    setItems={(v) => setField("linked_character_ids", v)}
                    options={characterOptions.map((c) => ({ value: c.id, label: c.name }))}
                    testid="epic-link-pcs"/>
        </div>
      </Section>
    </div>
  );
}


// ─────────────────────────── Sub-components ───────────────────────────

function Section({ title, icon, testid, open, onToggle, action, children }) {
  return (
    <div className="card-mystic p-4" data-testid={testid}>
      <div className="flex items-baseline justify-between mb-2 gap-3 flex-wrap">
        <button onClick={onToggle} className="flex items-center gap-2 text-left flex-1 min-w-0"
                data-testid={`${testid}-toggle`}>
          {open ? <ChevronDown className="w-3.5 h-3.5 text-gold/70 shrink-0"/> : <ChevronRight className="w-3.5 h-3.5 text-gold/70 shrink-0"/>}
          <span className="text-gold/70 shrink-0">{icon}</span>
          <span className="label-ref">{title}</span>
        </button>
        {action}
      </div>
      {open && <div className="space-y-3 mt-3">{children}</div>}
    </div>
  );
}

function Field({ label, help, testid, children }) {
  return (
    <div data-testid={testid}>
      <label className="label-ref block mb-1">{label}</label>
      {children}
      {help && <div className="text-[10px] text-mist/60 italic mt-1">{help}</div>}
    </div>
  );
}

function NpcEditor({ entity, onPatch, testidPrefix, lockedRole }) {
  return (
    <div className="space-y-3">
      <div className="grid md:grid-cols-[1fr_140px_140px] gap-2">
        <input className="input" value={entity.name || ""}
               onChange={(e) => onPatch({ name: e.target.value })}
               placeholder="Name"
               data-testid={`${testidPrefix}-name`}/>
        <select className="select" value={entity.role || "villain"}
                onChange={(e) => onPatch({ role: e.target.value })}
                disabled={!!lockedRole}
                data-testid={`${testidPrefix}-role`}>
          <option value="nemesis">Nemesis</option>
          <option value="villain">Villain</option>
          <option value="henchman">Henchman</option>
          <option value="ally">Ally</option>
          <option value="neutral">Neutral</option>
        </select>
        <select className="select" value={entity.psychology || "other"}
                onChange={(e) => onPatch({ psychology: e.target.value })}
                title="Sclanders ch.8 — three nemesis psychologies"
                data-testid={`${testidPrefix}-psych`}>
          <option value="bft">Blunt-Force-Trauma</option>
          <option value="never-present">Never-Present</option>
          <option value="mentor">Mentor</option>
          <option value="other">Other / mixed</option>
        </select>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <Field label="Occupation · what they DO" testid={`${testidPrefix}-occupation`}>
          <input className="input" value={entity.occupation || ""}
                 onChange={(e) => onPatch({ occupation: e.target.value })}
                 placeholder="Star-Cult Hierophant"
                 data-testid={`${testidPrefix}-occupation-input`}/>
        </Field>
        <Field label="Attitude · how they BEHAVE" testid={`${testidPrefix}-attitude`}>
          <input className="input" value={entity.attitude || ""}
                 onChange={(e) => onPatch({ attitude: e.target.value })}
                 placeholder="Patient, reverent, never raises voice"
                 data-testid={`${testidPrefix}-attitude-input`}/>
        </Field>
        <Field label="Goal · what they WANT" testid={`${testidPrefix}-goal`}>
          <input className="input" value={entity.goal || ""}
                 onChange={(e) => onPatch({ goal: e.target.value })}
                 placeholder="Free the Eclipse Saint"
                 data-testid={`${testidPrefix}-goal-input`}/>
        </Field>
        <Field label="Stake · what they LOSE" testid={`${testidPrefix}-stake`}>
          <input className="input" value={entity.stake || ""}
                 onChange={(e) => onPatch({ stake: e.target.value })}
                 placeholder="His name struck from the cosmic record"
                 data-testid={`${testidPrefix}-stake-input`}/>
        </Field>
      </div>
      <div className="grid md:grid-cols-3 gap-2">
        <Field label="Driving desire" help="ch.4 — Power · Status · Wealth · Revenge · Justification · Love" testid={`${testidPrefix}-desire`}>
          <select className="select" value={entity.desire || "other"}
                  onChange={(e) => onPatch({ desire: e.target.value })}
                  data-testid={`${testidPrefix}-desire-input`}>
            <option value="power">Power</option>
            <option value="status">Status</option>
            <option value="wealth">Wealth</option>
            <option value="revenge">Revenge</option>
            <option value="justification">Justification</option>
            <option value="love">Love</option>
            <option value="other">Other</option>
          </select>
        </Field>
        <Field label="Weakness pattern" help="ch.11 — what kind of subservience does the weakness produce?" testid={`${testidPrefix}-wkind`}>
          <select className="select" value={entity.weakness_kind || "none"}
                  onChange={(e) => onPatch({ weakness_kind: e.target.value })}
                  data-testid={`${testidPrefix}-wkind-input`}>
            <option value="none">None</option>
            <option value="desired">Desired subservience</option>
            <option value="ignorant">Ignorant subservience</option>
            <option value="respected">Respected subservience</option>
            <option value="hated">Hated subservience</option>
          </select>
        </Field>
        <Field label="Weakness" testid={`${testidPrefix}-weakness`}>
          <input className="input" value={entity.weakness || ""}
                 onChange={(e) => onPatch({ weakness: e.target.value })}
                 placeholder="Cannot speak his daughter's name"
                 data-testid={`${testidPrefix}-weakness-input`}/>
        </Field>
      </div>
      <Field label="Notes" testid={`${testidPrefix}-notes`}>
        <textarea className="input min-h-[50px]" value={entity.notes || ""}
                  onChange={(e) => onPatch({ notes: e.target.value })}
                  data-testid={`${testidPrefix}-notes-input`}/>
      </Field>
      {entity.linked_node_id && (
        <div className="text-[10px] text-arcane-light italic" data-testid={`${testidPrefix}-codex-link`}>
          ✓ Synced to Codex (node id: {entity.linked_node_id.slice(0, 8)}…)
        </div>
      )}
    </div>
  );
}

function MilestoneEditor({ m, idx, onPatch, onRemove }) {
  return (
    <div className="border border-gold/15 rounded-sm p-3" data-testid={`epic-milestone-${idx}`}>
      <div className="grid md:grid-cols-[1fr_80px_auto] gap-2 items-center mb-2">
        <input className="input" value={m.title || ""}
               onChange={(e) => onPatch({ title: e.target.value })}
               placeholder={`Milestone ${idx + 1}`}
               data-testid={`epic-milestone-${idx}-title`}/>
        <input type="number" min={1} className="input text-center" value={m.sequence || idx + 1}
               onChange={(e) => onPatch({ sequence: +e.target.value })}
               title="Sequence"
               data-testid={`epic-milestone-${idx}-seq`}/>
        <button onClick={onRemove} className="text-ember/70 hover:text-ember"
                data-testid={`epic-milestone-${idx}-remove`}><X className="w-4 h-4"/></button>
      </div>
      <div className="grid md:grid-cols-3 gap-2">
        <ChipList label="Obstacles" items={m.obstacles || []} setItems={(v) => onPatch({ obstacles: v })}
                  placeholder="A thing in the way" testid={`epic-milestone-${idx}-obstacles`}/>
        <ChipList label="Resources we have" items={m.resources_have || []} setItems={(v) => onPatch({ resources_have: v })}
                  placeholder="Something already on hand" testid={`epic-milestone-${idx}-have`}/>
        <ChipList label="Resources we need" items={m.resources_needed || []} setItems={(v) => onPatch({ resources_needed: v })}
                  placeholder="Something to acquire" testid={`epic-milestone-${idx}-need`}/>
      </div>
      <div className="mt-2 grid md:grid-cols-3 gap-2">
        <Field label="POE · Problem" testid={`epic-milestone-${idx}-poe-prob`}>
          <input className="input" value={m.poe_problem || ""}
                 onChange={(e) => onPatch({ poe_problem: e.target.value })}
                 placeholder="What's actually wrong"
                 data-testid={`epic-milestone-${idx}-poe-prob-input`}/>
        </Field>
        <Field label="POE · Obstacle" testid={`epic-milestone-${idx}-poe-obs`}>
          <input className="input" value={m.poe_obstacle || ""}
                 onChange={(e) => onPatch({ poe_obstacle: e.target.value })}
                 placeholder="What stops it being trivial"
                 data-testid={`epic-milestone-${idx}-poe-obs-input`}/>
        </Field>
        <Field label="POE · Event" testid={`epic-milestone-${idx}-poe-evt`}>
          <input className="input" value={m.poe_event || ""}
                 onChange={(e) => onPatch({ poe_event: e.target.value })}
                 placeholder="What kicks it into motion"
                 data-testid={`epic-milestone-${idx}-poe-evt-input`}/>
        </Field>
      </div>
      <label className="flex items-center gap-2 mt-2 text-[11px] font-ui text-mist">
        <input type="checkbox" checked={!!m.completed}
               onChange={(e) => onPatch({ completed: e.target.checked })}
               data-testid={`epic-milestone-${idx}-completed`}/>
        Completed
      </label>
    </div>
  );
}

function AdventureEditor({ a, idx, milestones, characterOptions, onPatch, onRemove }) {
  return (
    <div className="border border-gold/15 rounded-sm p-3" data-testid={`epic-adv-${idx}`}>
      <div className="grid md:grid-cols-[1fr_180px_180px_auto] gap-2 items-center mb-2">
        <input className="input" value={a.title || ""}
               onChange={(e) => onPatch({ title: e.target.value })}
               placeholder="Adventure title"
               data-testid={`epic-adv-${idx}-title`}/>
        <select className="select" value={a.mode || "advancing-campaign"}
                onChange={(e) => onPatch({ mode: e.target.value })}
                data-testid={`epic-adv-${idx}-mode`}>
          <option value="advancing-campaign">Mode: Advance Campaign</option>
          <option value="advancing-pcs">Mode: Advance PCs</option>
          <option value="enhancing-game">Mode: Enhance Game</option>
        </select>
        <select className="select" value={a.type || "nemesis-on-track"}
                onChange={(e) => onPatch({ type: e.target.value })}
                data-testid={`epic-adv-${idx}-type`}>
          <option value="nemesis-on-track">Nemesis-On-Track</option>
          <option value="nemesis-revenge">Nemesis-Revenge</option>
          <option value="ah-ha">Ah-Ha!</option>
          <option value="backstory">Backstory</option>
          <option value="pc-goal">PC-Goal</option>
          <option value="emergent">Emergent</option>
          <option value="chaos">Chaos</option>
          <option value="pacing">Pacing</option>
        </select>
        <button onClick={onRemove} className="text-ember/70 hover:text-ember"
                data-testid={`epic-adv-${idx}-remove`}><X className="w-4 h-4"/></button>
      </div>
      <textarea className="input mb-2" value={a.summary || ""}
                onChange={(e) => onPatch({ summary: e.target.value })}
                placeholder="One paragraph: what this adventure puts the table through."
                data-testid={`epic-adv-${idx}-summary`}/>
      <div className="grid md:grid-cols-2 gap-3">
        <ChipList label="5-step events" items={a.events || []} setItems={(v) => onPatch({ events: v })}
                  placeholder="Event that drives the plot" testid={`epic-adv-${idx}-events`}/>
        <div className="space-y-2">
          <Field label="Linked milestone" testid={`epic-adv-${idx}-milestone`}>
            <select className="select" value={a.linked_milestone_id || ""}
                    onChange={(e) => onPatch({ linked_milestone_id: e.target.value || null })}
                    data-testid={`epic-adv-${idx}-milestone-input`}>
              <option value="">— none —</option>
              {milestones.map((m, i) => (
                <option key={m.id || i} value={m.id || ""}>{m.title || `Milestone ${i + 1}`}</option>
              ))}
            </select>
          </Field>
          {(a.mode === "advancing-pcs" || a.type === "backstory" || a.type === "pc-goal") && (
            <PickList label="Linked PCs"
                      items={a.linked_pc_ids || []}
                      setItems={(v) => onPatch({ linked_pc_ids: v })}
                      options={characterOptions.map((c) => ({ value: c.id, label: c.name }))}
                      testid={`epic-adv-${idx}-pcs`}/>
          )}
        </div>
      </div>
    </div>
  );
}

function SeedRow({ s, idx, onPatch, onRemove }) {
  return (
    <div className="grid md:grid-cols-[120px_1fr_1fr_120px_24px] gap-2 items-center" data-testid={`epic-seed-${idx}`}>
      <select className="select select-sm" value={s.kind || "name"}
              onChange={(e) => onPatch({ kind: e.target.value })}
              data-testid={`epic-seed-${idx}-kind`}>
        <option value="name">Name</option>
        <option value="place">Place</option>
        <option value="object">Object</option>
        <option value="person">Person</option>
        <option value="dream">Dream</option>
        <option value="portent">Portent</option>
        <option value="omen">Omen</option>
      </select>
      <input className="input" value={s.label || ""}
             onChange={(e) => onPatch({ label: e.target.value })}
             placeholder="The seed itself"
             data-testid={`epic-seed-${idx}-label`}/>
      <input className="input" value={s.payoff || ""}
             onChange={(e) => onPatch({ payoff: e.target.value })}
             placeholder="What it pays off"
             data-testid={`epic-seed-${idx}-payoff`}/>
      <input className="input" value={s.seeded_in || ""}
             onChange={(e) => onPatch({ seeded_in: e.target.value })}
             placeholder="Session 1"
             data-testid={`epic-seed-${idx}-when`}/>
      <button onClick={onRemove} className="text-ember/70 hover:text-ember"
              data-testid={`epic-seed-${idx}-remove`}><X className="w-3 h-3"/></button>
      <label className="md:col-span-5 flex items-center gap-2 text-[11px] font-ui text-mist">
        <input type="checkbox" checked={!!s.paid_off}
               onChange={(e) => onPatch({ paid_off: e.target.checked })}
               data-testid={`epic-seed-${idx}-paidoff`}/>
        Paid off at the table
      </label>
    </div>
  );
}

function ChipList({ label, items, setItems, placeholder, testid }) {
  const [v, setV] = useState("");
  const add = () => { const t = v.trim(); if (!t) return; setItems([...(items || []), t]); setV(""); };
  return (
    <div>
      {label && <div className="label-ref mb-1">{label}</div>}
      <div className="flex flex-wrap gap-1 mb-1.5">
        {(items || []).map((it, i) => (
          <span key={i} className="tag" data-testid={`${testid}-chip-${i}`}>
            {it}
            <button className="ml-1" onClick={() => setItems(items.filter((_, j) => j !== i))}>
              <X className="w-3 h-3 inline"/>
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="input" placeholder={placeholder} value={v}
               onChange={(e) => setV(e.target.value)}
               onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
               data-testid={`${testid}-input`}/>
        <button onClick={add} type="button" className="btn btn-ghost"
                data-testid={`${testid}-add`}><Plus className="w-3 h-3"/></button>
      </div>
    </div>
  );
}

function PickList({ label, items, setItems, options, testid }) {
  const [pick, setPick] = useState("");
  const add = () => {
    if (!pick) return;
    if ((items || []).includes(pick)) { setPick(""); return; }
    setItems([...(items || []), pick]);
    setPick("");
  };
  const labelFor = (id) => (options.find((o) => o.value === id)?.label) || id;
  return (
    <div>
      {label && <div className="label-ref mb-1">{label}</div>}
      <div className="flex flex-wrap gap-1 mb-1.5">
        {(items || []).map((id, i) => (
          <span key={id} className="tag" data-testid={`${testid}-chip-${i}`}>
            {labelFor(id)}
            <button className="ml-1" onClick={() => setItems(items.filter((x) => x !== id))}>
              <X className="w-3 h-3 inline"/>
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <select className="select" value={pick} onChange={(e) => setPick(e.target.value)}
                data-testid={`${testid}-select`}>
          <option value="">— pick to add —</option>
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button onClick={add} type="button" className="btn btn-ghost"
                data-testid={`${testid}-add`}><Plus className="w-3 h-3"/></button>
      </div>
    </div>
  );
}
