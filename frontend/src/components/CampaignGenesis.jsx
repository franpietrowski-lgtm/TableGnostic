import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { ArrowRight, ArrowLeft, Save, Wand2, Plus, X, Sparkles, BookMarked, CheckCircle2, ExternalLink, Lightbulb } from "lucide-react";
import { TipDot, Tip } from "./ui/Tip";

const PROMPTS = {
  sentence_who: ["What single act defines them?", "What have they lost that they cannot replace?", "What do others whisper about them?"],
  sentence_wants: ["What do they want that only you can take away?", "Is this desire public or private?", "What won't they admit wanting?"],
  sentence_badly_when: ["What happens if they miss the deadline?", "Is the clock visible to the players, or only to the GM?", "What ritual, deadline, or body count triggers the reckoning?"],
  sentence_using: ["Is the tool dangerous to wield? Who else can wield it?", "Does the method demand a cost — body, name, truth?", "Could the method become a trap?"],
  sentence_reasons: ["Whose opposition matters most, and why?", "Is the real obstacle external, internal, or systemic?", "What personal wound makes this difficulty sharper?"],
  theme: ["What feeling should linger after the final session?", "What question is this campaign actually asking?", "What lie will the players learn to stop believing?"],
  nemesis_motive: ["What does the nemesis believe is just?", "What do they think the heroes don't understand?", "What traumatic moment set them on this path?"],
  nemesis_resources: ["Wealth, reputation, networks, soldiers, knowledge, or position?", "What do they have that the heroes don't?", "Which resource can the heroes chip away at?"],
  nemesis_weakness: ["The keyhole the heroes might reach through — a vow, a love, a wound, a hubris.", "Does the weakness require risk or sacrifice to exploit?", "Who else knows about it?"],
  beginning: ["Who is already bound to whom when play opens?", "What single image opens the first session?", "What question should hang in the air before a die is rolled?"],
  ending: ["Not the plot's ending — the emotional one. What should the table feel on the last night?", "What will the players remember in a year?", "What unresolved thread keeps the story alive after 'the end'?"],
};

const PHASES = [
  { key: "sentence",   title: "The Sentence",      blurb: "One line that holds the entire campaign. Who wants what, badly, by when, using what, against what odds." },
  { key: "theme",      title: "Theme & Tone",      blurb: "The emotional core your players should feel beneath every scene." },
  { key: "nemesis",    title: "Nemesis Design",    blurb: "The force in opposition. Their motive is the plot's engine." },
  { key: "plot",       title: "The Master Plot",   blurb: "Act structure that arcs from ordinary world to climax." },
  { key: "adventures", title: "Adventure Outlines",blurb: "Follow Plotters (story-advancing), Make Plotters (player-driven), and Adventures on the Fly." },
  { key: "npcs",       title: "Supporting Cast",   blurb: "Fodder and Plotter NPCs — the humans your table will remember." },
  { key: "bookends",   title: "Beginning & Ending",blurb: "Open with relationship, close with resonance." },
];

const BLANK = {
  campaign_id: "", sentence_who: "", sentence_wants: "", sentence_badly_when: "",
  sentence_using: "", sentence_reasons: "", theme: "", tone_words: [],
  nemesis_name: "", nemesis_type: "villain", nemesis_motive: "", nemesis_resources: "",
  nemesis_weakness: "", master_acts: [], adventures: [], seed_npcs: [],
  beginning: "", ending: "", phase_completed: 0,
};

export default function CampaignGenesis() {
  const { id } = useParams();
  const nav = useNavigate();
  const [g, setG] = useState(null);
  const [phase, setPhase] = useState(0);
  const [err, setErr] = useState("");
  const [saved, setSaved] = useState(false);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/campaigns/${id}/genesis`);
        setG({ ...BLANK, ...data, campaign_id: id });
        setPhase(Math.min(data.phase_completed || 0, PHASES.length - 1));
      } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
    })();
  }, [id]);

  const save = async (phaseIdx) => {
    setErr(""); setSaved(false);
    try {
      const body = { ...g, campaign_id: id, phase_completed: Math.max(g.phase_completed || 0, phaseIdx + 1) };
      const { data } = await api.put(`/campaigns/${id}/genesis`, body);
      setG((prev) => ({ ...prev, ...data }));
      setSaved(true);
      setTimeout(() => setSaved(false), 1800);
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };
  const next = async () => {
    await save(phase);
    if (phase < PHASES.length - 1) setPhase(phase + 1);
  };
  const prev = () => { if (phase > 0) setPhase(phase - 1); };
  const seedNodes = async () => {
    setSeeding(true);
    try {
      await save(PHASES.length - 1);
      const { data } = await api.post(`/campaigns/${id}/genesis/seed-nodes`);
      alert(`${data.nodes_created} knowledge nodes seeded (GM-only).`);
      nav(`/app/campaigns/${id}`);
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
    finally { setSeeding(false); }
  };

  if (!g) return <div className="p-10 text-mist">Opening the atelier…</div>;

  const Panel = ({ children }) => (
    <div className="card-mystic sigil-ring p-7 space-y-5" data-testid="genesis-panel">{children}</div>
  );
  const update = (patch) => setG({ ...g, ...patch });
  const updateArray = (key, idx, patch) => {
    const arr = [...(g[key] || [])]; arr[idx] = { ...arr[idx], ...patch };
    update({ [key]: arr });
  };
  const addRow = (key, row) => update({ [key]: [...(g[key] || []), row] });
  const removeRow = (key, idx) => {
    const arr = [...(g[key] || [])]; arr.splice(idx, 1);
    update({ [key]: arr });
  };

  const cur = PHASES[phase];
  const progressPct = Math.round((g.phase_completed / PHASES.length) * 100);

  return (
    <div className="px-8 md:px-12 py-10 max-w-4xl">
      <Link to={`/app/campaigns/${id}`} className="text-xs font-ui uppercase tracking-widest text-gold/70">
        ← Campaign
      </Link>
      <div className="mt-3">
        <div className="label-ref flex items-center gap-2"><Wand2 className="w-3 h-3"/> Campaign Atelier</div>
        <h1 className="font-display text-4xl tracking-wide text-parchment mt-1">Forge the Master Plot</h1>
        <p className="text-mist font-body mt-2 max-w-2xl">
          Seven phases, one arc. Complete them in order — or circle back at any time. Each save persists
          to your campaign.
        </p>
        <div className="mt-5 flex items-center gap-3">
          <div className="flex-1 h-[2px] bg-gold/10">
            <div className="h-full bg-gold transition-all duration-500" style={{ width: `${progressPct}%` }}/>
          </div>
          <div className="text-xs font-ui uppercase tracking-widest text-gold/70">
            {g.phase_completed}/{PHASES.length} phases
          </div>
        </div>
      </div>

      <div className="mt-8 flex flex-wrap gap-1.5">
        {PHASES.map((p, i) => (
          <button key={p.key} onClick={() => setPhase(i)}
                  className={`text-[10px] font-ui uppercase tracking-widest px-3 py-1.5 rounded-sm border transition
                    ${i === phase ? "border-gold text-gold-bright bg-gold/10" :
                       i < g.phase_completed ? "border-gold/30 text-gold/80" : "border-gold/10 text-mist/60"}`}
                  data-testid={`genesis-phase-${i}`}>
            {i < g.phase_completed && <CheckCircle2 className="w-3 h-3 inline mr-1"/>}
            {p.title}
          </button>
        ))}
      </div>

      <div className="divider-sigil my-6" />
      <div className="label-ref mb-2">Phase {phase + 1} of {PHASES.length}</div>
      <h2 className="font-display text-2xl text-parchment tracking-wide mb-1">{cur.title}</h2>
      <p className="text-sm text-mist font-body mb-5 italic">{cur.blurb}</p>

      {phase === 0 && (
        <Panel>
          <div className="text-xs text-mist font-body leading-relaxed">
            Complete one sentence. It is the keystone of everything that follows.
            <span className="block mt-2 text-gold/70 font-ui tracking-widest uppercase text-[10px]">
              "<span className="text-parchment">Someone</span> wants <span className="text-parchment">something</span> badly
              by <span className="text-parchment">when</span>, and is having difficulty getting it
              using <span className="text-parchment">something</span> because of <span className="text-parchment">reasons</span>."
            </span>
          </div>
          <Field label="WHO" placeholder="the protagonist(s) or antagonist(s)"
                 tip="The person, group, or force at the centre of the arc. A vampire noble, the rebellion, the city itself — as long as the table can care about them."
                 prompts={PROMPTS.sentence_who}
                 value={g.sentence_who} onChange={(v) => update({ sentence_who: v })} testid="sentence-who"/>
          <Field label="WANTS WHAT" placeholder="the core desire" value={g.sentence_wants}
                 tip="A concrete, imaginable goal — not an abstract virtue. 'To sit the ivory throne' beats 'power'."
                 prompts={PROMPTS.sentence_wants}
                 onChange={(v) => update({ sentence_wants: v })} testid="sentence-wants"/>
          <Field label="BADLY BY WHEN" placeholder="the ticking clock" value={g.sentence_badly_when}
                 tip="Urgency creates drama. Name the deadline: an eclipse, a wedding, three sessions, the next winter."
                 prompts={PROMPTS.sentence_badly_when}
                 onChange={(v) => update({ sentence_badly_when: v })} testid="sentence-when"/>
          <Field label="USING WHAT" placeholder="the method / tool / path" value={g.sentence_using}
                 tip="The road they take toward the goal. The relic, the ritual, the army, the forbidden knowledge."
                 prompts={PROMPTS.sentence_using}
                 onChange={(v) => update({ sentence_using: v })} testid="sentence-using"/>
          <Field label="BECAUSE OF" placeholder="the opposition / complication" value={g.sentence_reasons}
                 tip="Why it's hard. This is where your plot lives — whoever or whatever stands in their way is where the sessions happen."
                 prompts={PROMPTS.sentence_reasons}
                 onChange={(v) => update({ sentence_reasons: v })} testid="sentence-reasons"/>
          {g.sentence_who && (
            <div className="mt-3 p-4 border border-gold/30 rounded-sm bg-gold/5">
              <div className="label-ref mb-1">Your Sentence</div>
              <div className="font-body italic text-parchment/90 leading-relaxed">
                <span className="text-gold-bright">{g.sentence_who || "___"}</span> wants{" "}
                <span className="text-gold-bright">{g.sentence_wants || "___"}</span> badly by{" "}
                <span className="text-gold-bright">{g.sentence_badly_when || "___"}</span>, and is having difficulty
                getting it using <span className="text-gold-bright">{g.sentence_using || "___"}</span>{" "}
                because of <span className="text-gold-bright">{g.sentence_reasons || "___"}</span>.
              </div>
            </div>
          )}
        </Panel>
      )}

      {phase === 1 && (
        <Panel>
          <Field label="Theme" placeholder="e.g. the cost of devotion; rebirth through loss"
                 tip="The deeper idea underneath the plot. Themes aren't stated aloud — they rise out of repeated choices, images, and stakes."
                 prompts={PROMPTS.theme}
                 value={g.theme} onChange={(v) => update({ theme: v })} testid="theme-input" textarea/>
          <div>
            <label className="label-ref mb-1 flex items-center gap-2">
              Tone words
              <TipDot text="Three-to-five adjectives that describe the emotional colour of the campaign. They guide your descriptions, your NPC voices, and the music you play at the table."/>
            </label>
            <input className="input" placeholder="brooding, baroque, tragic (comma-separated)"
                   value={(g.tone_words || []).join(", ")}
                   onChange={(e) => update({ tone_words: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
                   data-testid="tone-words"/>
            <div className="mt-2 flex flex-wrap gap-1">
              {(g.tone_words || []).map((t, i) => <span key={i} className="tag">{t}</span>)}
            </div>
          </div>
        </Panel>
      )}

      {phase === 2 && (
        <Panel>
          <div className="grid md:grid-cols-2 gap-4">
            <Field label="Nemesis Name" value={g.nemesis_name}
                   tip="Name them before you describe them — a name locks the imagination. 'Archon Velvyn' is easier to play with than 'the evil priest'."
                   onChange={(v) => update({ nemesis_name: v })} testid="nemesis-name"/>
            <div>
              <label className="label-ref mb-1 flex items-center gap-2">
                Nemesis Type
                <TipDot text="Different types of nemesis create different stories. A Villain is personal; a Force of Nature is relentless; a System cannot be killed, only dismantled; an Inner nemesis cannot be outrun."/>
              </label>
              <select className="select" value={g.nemesis_type}
                      onChange={(e) => update({ nemesis_type: e.target.value })} data-testid="nemesis-type">
                <option value="villain">Villain (personal, intelligent)</option>
                <option value="henchman">Henchman (recurring foil)</option>
                <option value="rival">Rival (moral equal)</option>
                <option value="force">Force of Nature (impersonal, relentless)</option>
                <option value="system">System (institution, law, ideology)</option>
                <option value="inner">Inner (trauma, doubt, addiction)</option>
              </select>
            </div>
          </div>
          <Field label="Motive" placeholder="what do they want, and why do they want it now"
                 tip="The best villains think they are the hero. Give them a reason a reasonable person could almost agree with, then let the heroes discover the hidden cost."
                 prompts={PROMPTS.nemesis_motive}
                 value={g.nemesis_motive} onChange={(v) => update({ nemesis_motive: v })} testid="nemesis-motive" textarea/>
          <Field label="Resources" placeholder="power, networks, knowledge, tools"
                 tip="What makes them dangerous beyond the name? Concrete resources mean the heroes can spend sessions dismantling them."
                 prompts={PROMPTS.nemesis_resources}
                 value={g.nemesis_resources} onChange={(v) => update({ nemesis_resources: v })} testid="nemesis-resources" textarea/>
          <Field label="Weakness" placeholder="the keyhole through which the heroes may reach them"
                 tip="Not just an exploitable flaw — a narrative keyhole. Something the heroes can discover, earn, or sacrifice to reach."
                 prompts={PROMPTS.nemesis_weakness}
                 value={g.nemesis_weakness} onChange={(v) => update({ nemesis_weakness: v })} testid="nemesis-weakness" textarea/>
        </Panel>
      )}

      {phase === 3 && (
        <Panel>
          <div className="text-xs text-mist font-body">
            Break your Sentence into acts. Most campaigns sit comfortably in 3–5.
            <div className="mt-2 text-gold/60 italic">
              Tip: name each act like a chapter title. "The Lantern-Lit Road" beats "Act 1".
            </div>
          </div>
          {(g.master_acts || []).map((a, i) => (
            <div key={i} className="border border-gold/15 p-3 rounded-sm" data-testid={`act-${i}`}>
              <div className="flex items-center gap-2">
                <span className="label-ref">Act {i + 1}</span>
                <input className="input flex-1" placeholder="Act title" value={a.title || ""}
                       onChange={(e) => updateArray("master_acts", i, { title: e.target.value })}/>
                <button onClick={() => removeRow("master_acts", i)} className="text-ember/70"><X className="w-4 h-4"/></button>
              </div>
              <textarea className="input mt-2" placeholder="Core beat — what changes in the world by the end of this act"
                        value={a.beat || ""}
                        onChange={(e) => updateArray("master_acts", i, { beat: e.target.value })}/>
            </div>
          ))}
          <button className="btn btn-ghost text-xs" data-testid="add-act-btn"
                  onClick={() => addRow("master_acts", { title: "", beat: "" })}>
            <Plus className="w-3 h-3"/> Add Act
          </button>
        </Panel>
      )}

      {phase === 4 && (
        <Panel>
          <div className="text-xs text-mist font-body">
            Outline the sessions. Mark each as <b>Follow</b> (advances the master plot),
            <b className="ml-1">Make</b> (player-driven), or <b className="ml-1">Fly</b> (improvised).
            <div className="mt-2 text-gold/60 italic">
              Hook = the first 5 minutes · Stakes = what shifts if they fail · Outcome = what you expect, written loose enough to be wrong.
            </div>
          </div>
          {(g.adventures || []).map((a, i) => (
            <div key={i} className="border border-gold/15 p-3 rounded-sm space-y-2" data-testid={`adventure-${i}`}>
              <div className="flex items-center gap-2">
                <input className="input flex-1" placeholder="Adventure title" value={a.title || ""}
                       onChange={(e) => updateArray("adventures", i, { title: e.target.value })}/>
                <select className="select w-36" value={a.kind || "follow"}
                        onChange={(e) => updateArray("adventures", i, { kind: e.target.value })}>
                  <option value="follow">Follow Plotter</option>
                  <option value="make">Make Plotter</option>
                  <option value="fly">On the Fly</option>
                </select>
                <button onClick={() => removeRow("adventures", i)} className="text-ember/70"><X className="w-4 h-4"/></button>
              </div>
              <div className="grid md:grid-cols-3 gap-2">
                <input className="input" placeholder="Hook" value={a.hook || ""}
                       onChange={(e) => updateArray("adventures", i, { hook: e.target.value })}/>
                <input className="input" placeholder="Stakes" value={a.stakes || ""}
                       onChange={(e) => updateArray("adventures", i, { stakes: e.target.value })}/>
                <input className="input" placeholder="Expected Outcome" value={a.outcome || ""}
                       onChange={(e) => updateArray("adventures", i, { outcome: e.target.value })}/>
              </div>
            </div>
          ))}
          <button className="btn btn-ghost text-xs" data-testid="add-adventure-btn"
                  onClick={() => addRow("adventures", { title: "", kind: "follow", hook: "", stakes: "", outcome: "" })}>
            <Plus className="w-3 h-3"/> Add Adventure
          </button>
        </Panel>
      )}

      {phase === 5 && (
        <Panel>
          <div className="text-xs text-mist font-body">
            Seed at least three NPCs — the table will find their own favourites.
            <div className="mt-2 text-gold/60 italic">
              Plotters have names, wants, and voices. Fodder have one memorable trait and show up once.
            </div>
          </div>
          {(g.seed_npcs || []).map((n, i) => (
            <div key={i} className="border border-gold/15 p-3 rounded-sm space-y-2" data-testid={`npc-${i}`}>
              <div className="flex items-center gap-2">
                <input className="input flex-1" placeholder="NPC name" value={n.name || ""}
                       onChange={(e) => updateArray("seed_npcs", i, { name: e.target.value })}/>
                <select className="select w-40" value={n.role || "plotter"}
                        onChange={(e) => updateArray("seed_npcs", i, { role: e.target.value })}>
                  <option value="plotter">Plotter (named, recurring)</option>
                  <option value="fodder">Fodder (colour, brief)</option>
                  <option value="ally">Ally</option>
                  <option value="rival">Rival</option>
                  <option value="patron">Patron</option>
                </select>
                <button onClick={() => removeRow("seed_npcs", i)} className="text-ember/70"><X className="w-4 h-4"/></button>
              </div>
              <textarea className="input" placeholder="A memorable trait, voice, or want"
                        value={n.note || ""}
                        onChange={(e) => updateArray("seed_npcs", i, { note: e.target.value })}/>
            </div>
          ))}
          <button className="btn btn-ghost text-xs" data-testid="add-npc-btn"
                  onClick={() => addRow("seed_npcs", { name: "", role: "plotter", note: "" })}>
            <Plus className="w-3 h-3"/> Add NPC
          </button>
        </Panel>
      )}

      {phase === 6 && (
        <Panel>
          <Field label="Beginning" placeholder="how does the first session open? Who is already bound to whom?"
                 tip="Open with relationship, not with a quest-giver. A first scene where two PCs already share history gives you a campaign instead of a video game."
                 prompts={PROMPTS.beginning}
                 value={g.beginning} onChange={(v) => update({ beginning: v })} testid="beginning" textarea/>
          <Field label="Ending (aimed at)" placeholder="the emotional closing image you hope the table reaches"
                 tip="Not what the plot resolves, but what the players feel. Close on image, not exposition — a silence, a gesture, a promise."
                 prompts={PROMPTS.ending}
                 value={g.ending} onChange={(v) => update({ ending: v })} testid="ending" textarea/>
          <div className="border-t border-gold/10 pt-4">
            <div className="label-ref mb-2">Materialise</div>
            <p className="text-xs text-mist font-body mb-3">
              Turn this plan into <b>knowledge nodes</b> (Nemesis, NPCs, and Adventure hooks)
              in your campaign — all GM-only until you reveal them.
            </p>
            <button onClick={seedNodes} disabled={seeding} className="btn btn-primary" data-testid="seed-nodes-btn">
              <Sparkles className="w-4 h-4"/> {seeding ? "Summoning…" : "Seed Knowledge Web"}
            </button>
          </div>
        </Panel>
      )}

      {err && <div className="mt-4 text-ember text-sm" data-testid="genesis-error">{err}</div>}

      <div className="mt-6 flex items-center justify-between">
        <button onClick={prev} disabled={phase === 0} className="btn btn-ghost" data-testid="genesis-prev">
          <ArrowLeft className="w-4 h-4"/> Back
        </button>
        <div className="flex items-center gap-3">
          {saved && <span className="text-[11px] text-gold font-ui uppercase tracking-widest flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3"/> saved
          </span>}
          <button onClick={() => save(phase)} className="btn" data-testid="genesis-save">
            <Save className="w-4 h-4"/> Save
          </button>
          <button onClick={next} className="btn btn-primary" data-testid="genesis-next">
            {phase === PHASES.length - 1 ? "Complete" : "Next"} <ArrowRight className="w-4 h-4"/>
          </button>
        </div>
      </div>

      <div className="mt-14 border-t border-gold/10 pt-4 text-[10px] font-ui uppercase tracking-[0.22em] text-mist/70 leading-relaxed">
        <BookMarked className="w-3 h-3 inline mr-1"/>
        Framework inspired by <span className="text-gold/90">Guy Sclanders</span> — "The Complete Guide to Creating
        Epic Campaigns" (<em>How to be a Great GM</em>, 2018). Phase names and prompts reference the structure
        of the guide; all content you author here is your own.
        <a href="https://www.greatgamemaster.com" target="_blank" rel="noreferrer"
           className="ml-2 text-gold hover:text-gold-bright normal-case inline-flex items-center gap-1">
          greatgamemaster.com <ExternalLink className="w-3 h-3"/>
        </a>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, placeholder, textarea, testid, tip, prompts }) {
  return (
    <div>
      <label className="label-ref mb-1 flex items-center gap-2">
        {label}
        {tip && <TipDot text={tip}/>}
      </label>
      {textarea
        ? <textarea className="input" placeholder={placeholder} value={value || ""}
                    onChange={(e) => onChange(e.target.value)} data-testid={testid}/>
        : <input className="input" placeholder={placeholder} value={value || ""}
                 onChange={(e) => onChange(e.target.value)} data-testid={testid}/>}
      {prompts && prompts.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5 items-center">
          <Lightbulb className="w-3 h-3 text-gold/50"/>
          {prompts.map((p, i) => (
            <span key={i} className="text-[10px] text-mist/70 italic font-body border border-gold/10 px-2 py-0.5 rounded-sm">
              {p}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
