import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { Dice6, Edit3, BookOpen, Trash2 } from "lucide-react";
import BesmTerm from "./ui/BesmTerm";

export default function CharacterSheet() {
  const { id } = useParams();
  const nav = useNavigate();
  const [ch, setCh] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [err, setErr] = useState("");
  const [rollLabel, setRollLabel] = useState("");
  const [rollNotation, setRollNotation] = useState("2d6");
  const [rollTarget, setRollTarget] = useState("");
  const [lastRoll, setLastRoll] = useState(null);
  const [selectedSession, setSelectedSession] = useState("");
  const [pbpChannelId, setPbpChannelId] = useState(null);

  const load = async () => {
    try {
      const data = await api.get(`/characters/${id}`).then((r) => r.data);
      setCh(data);
      const [s, channels] = await Promise.all([
        api.get(`/campaigns/${data.campaign_id}/sessions`).then((r) => r.data),
        api.get(`/campaigns/${data.campaign_id}/channels`).then((r) => r.data).catch(() => []),
      ]);
      setSessions(s);
      if (s.length) setSelectedSession(s[0].id);
      if (channels.length) setPbpChannelId(channels[0].id);
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };
  useEffect(() => { load(); }, [id]);

  if (err) return <div className="p-10 text-ember">{err}</div>;
  if (!ch) return <div className="p-10 text-mist">Summoning…</div>;

  // Sheet roll = always posts a /roll line into the campaign's first PBP
  // channel (the "macro chat") so the table sees it immediately. If a live
  // session is selected, ALSO posts to the live /api/dice altar so the
  // session log + spotlight still light up.
  const roll = async (notation = rollNotation, label = rollLabel) => {
    let posted = false;
    if (pbpChannelId) {
      const body = label
        ? `/roll ${notation}     # ${ch.name} · ${label}`
        : `/roll ${notation}     # ${ch.name}`;
      try {
        await api.post(`/channels/${pbpChannelId}/messages`, { body });
        posted = true;
      } catch {}
    }
    if (selectedSession) {
      try {
        const { data } = await api.post("/dice", {
          session_id: selectedSession, notation, label,
          target: rollTarget ? +rollTarget : null, character_id: ch.id,
        });
        setLastRoll(data);
        posted = true;
      } catch (e) { setLastRoll({ error: formatApiErrorDetail(e.response?.data?.detail) || e.message }); }
    } else if (posted) {
      setLastRoll({ pbp_only: true, label: label || notation });
    } else {
      setLastRoll({ error: "Start a session or open a channel first to roll dice." });
    }
  };

  // Macro: post a narrative emote into the PBP channel (no dice).
  const emote = async (text) => {
    if (!pbpChannelId) return;
    try { await api.post(`/channels/${pbpChannelId}/messages`, { body: `/me ${text}` }); } catch {}
  };

  // BESM 4E (Tri-Stat): Stat checks are 2d6 + Stat ≥ Target Number.
  // Combat rolls (ATK/DEF) similarly add the derived value.
  // Initiative is 1d6 + Mind (BESM 4E p.171).
  const quickRolls = [
    { label: "Body Roll", notation: "2d6+body", hint: "Roll 2d6, add Body, meet/beat the GM's Target Number." },
    { label: "Mind Roll", notation: "2d6+mind" },
    { label: "Soul Roll", notation: "2d6+soul" },
    { label: "Attack", notation: "2d6+atk" },
    { label: "Defence", notation: "2d6+def" },
    { label: "Initiative", notation: "1d6+mind" },
  ];

  const delChar = async () => {
    if (!window.confirm("Forget this character?")) return;
    await api.delete(`/characters/${id}`);
    nav(`/app/campaigns/${ch.campaign_id}`);
  };

  return (
    <div className="px-8 md:px-12 py-10 max-w-6xl">
      <Link to={`/app/campaigns/${ch.campaign_id}`} className="text-xs font-ui uppercase tracking-widest text-gold/70">
        ← Campaign
      </Link>
      <div className="mt-3 flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="label-ref mb-1">BESM 4E · {ch.power_level} · {ch.total_points} pts</div>
          <h1 className="font-display text-4xl tracking-wide text-parchment flex items-center gap-3">
            {ch.token_color && (
              <span aria-label="Token colour"
                    data-testid="sheet-token-color"
                    className="inline-block w-5 h-5 rounded-full border border-gold/40"
                    style={{ backgroundColor: ch.token_color,
                             boxShadow: `0 0 10px ${ch.token_color}99` }}/>
            )}
            {ch.name}
          </h1>
          <div className="text-mist font-body italic mt-1">{ch.concept}</div>
          <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60 mt-2">
            by {ch.owner_name} · spent {ch.spent?.total_spent ?? 0} / {ch.total_points} pts
            {ch.size && ch.size !== "Medium" ? ` · ${ch.size}` : ""}
          </div>
        </div>
        <div className="flex gap-2">
          <Link to={`/app/characters/${ch.id}/edit`} className="btn" data-testid="edit-character-btn">
            <Edit3 className="w-4 h-4"/> Edit
          </Link>
          <button onClick={delChar} className="btn btn-danger"><Trash2 className="w-4 h-4"/></button>
        </div>
      </div>

      <div className="mt-8 grid lg:grid-cols-3 gap-6">
        {/* Left: Core */}
        <div className="card-mystic p-6">
          <div className="label-ref">Core Stats</div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            {["body", "mind", "soul"].map((s) => (
              <button key={s} type="button"
                      onClick={() => roll(`2d6+${s}`, `${ch.name} · ${s} check`)}
                      className="border border-gold/15 rounded-sm py-3 hover:border-gold/40 hover:bg-gold/5 transition-colors group"
                      data-testid={`sheet-stat-${s}`}
                      title={`Roll 2d6+${s} (BESM 4E: meet/beat the Target Number)`}>
                <div className="label-ref">{s}</div>
                <div className="font-display text-3xl text-gold">{ch.stats[s]}</div>
                <div className="text-[9px] font-ui uppercase tracking-widest text-mist/50 group-hover:text-gold-bright">2d6+{s}</div>
              </button>
            ))}
          </div>
          <div className="divider-sigil my-4"/>
          <div className="label-ref">Derived · p.168 BESM 4E</div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            {[
              ["CV", ch.derived?.combat_value],
              ["ATK", ch.derived?.attack_value],
              ["DEF", ch.derived?.defence_value],
              ["HP", ch.derived?.health_points],
              ["EP", ch.derived?.energy_points],
              ["DM", ch.derived?.damage_multiplier],
            ].map(([l, v]) => (
              <div key={l} className="border border-gold/15 rounded-sm py-2">
                <div className="label-ref">{l}</div>
                <div className="font-display text-xl text-gold-bright">{v}</div>
              </div>
            ))}
          </div>
          <div className="divider-sigil my-4"/>
          <div className="label-ref">Notes</div>
          <div className="text-sm text-mist mt-2 whitespace-pre-wrap font-body">{ch.notes || "—"}</div>
        </div>

        {/* Middle: Attributes / Defects / Skills */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card-mystic p-6">
            <div className="h-arcane text-sm mb-3">Attributes</div>
            {ch.attributes.length === 0 && <div className="text-mist italic text-xs">—</div>}
            <div className="space-y-2">
              {ch.attributes.map((a, i) => (
                <div key={i} className="border border-gold/10 rounded-sm p-3 flex items-start justify-between flex-wrap gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-ui">
                      <BesmTerm name={a.name} cost={`${a.cost_per_level} pts/level`}
                                page={a.page} note={a.note}
                                book={a.page ? "BESM 4E" : "Custom"}/>
                      <span className="text-gold ml-2">×{a.level}</span>
                      {typeof a.effective_level === "number" && a.effective_level !== a.level && (
                        <span className="ml-2 text-arcane-light text-[11px] font-ui uppercase tracking-widest"
                              title={`BESM 4E: cost stays at ${a.cost_per_level}×${a.level}; +1 effective Level per Limiter, −1 per Enhancement.`}
                              data-testid={`attr-eff-level-${i}`}>
                          (eff. ×{a.effective_level})
                        </span>
                      )}
                    </div>
                    {a.note && (
                      <div className="text-[12px] text-parchment/85 italic mt-1 font-body leading-snug"
                           data-testid={`attr-note-${i}`}>
                        {a.note}
                      </div>
                    )}
                    <div className="text-[10px] text-mist font-ui uppercase tracking-widest flex items-center gap-1 mt-1">
                      <BookOpen className="w-3 h-3"/> {a.page ? `p.${a.page} BESM 4E` : "Custom"}
                    </div>
                    {(a.enhancements.length > 0 || a.limiters.length > 0) && (
                      <div className="mt-1.5 flex flex-wrap gap-1">
                        {a.enhancements.map((e, j) => <span key={j} className="tag border-gold/40 text-gold-bright">+{e}</span>)}
                        {a.limiters.map((l, j) => <span key={j} className="tag border-ember/40 text-ember">-{l}</span>)}
                      </div>
                    )}
                  </div>
                  <button onClick={() => roll("2d6", `${a.name} roll`)}
                          className="btn btn-ghost text-xs" data-testid={`attr-roll-${i}`}>
                    <Dice6 className="w-3 h-3"/> 2d6
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="card-mystic p-6">
            <div className="h-arcane text-sm mb-3">Defects</div>
            {ch.defects.length === 0 && <div className="text-mist italic text-xs">—</div>}
            <div className="space-y-2">
              {ch.defects.map((d, i) => (
                <div key={i} className="border border-gold/10 rounded-sm p-3 flex items-start justify-between flex-wrap gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-ui">
                      <BesmTerm name={d.name} cost={`${d.points_per_rank} pts/rank`}
                                page={d.page} note={d.note} category={d.category}
                                book={d.page ? "BESM 4E" : "Custom"}/>
                      <span className="text-ember ml-2">×{d.rank}</span>
                    </div>
                    {d.note && (
                      <div className="text-[12px] text-parchment/85 italic mt-1 font-body leading-snug"
                           data-testid={`defect-note-${i}`}>
                        {d.note}
                      </div>
                    )}
                    <div className="text-[10px] text-mist font-ui uppercase tracking-widest flex items-center gap-1 mt-1">
                      <BookOpen className="w-3 h-3"/> {d.page ? `p.${d.page} BESM 4E` : "Custom"} · {d.category}
                    </div>
                  </div>
                  <span className="text-ember font-display">{d.points_per_rank * d.rank} pts</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card-mystic p-6">
            <div className="h-arcane text-sm mb-3">Skill Groups</div>
            {ch.skills.length === 0 && <div className="text-mist italic text-xs">—</div>}
            <div className="space-y-2">
              {ch.skills.map((s, i) => (
                <div key={i} className="border border-gold/10 rounded-sm p-3 flex items-start justify-between flex-wrap gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-parchment font-ui">
                      {s.group} <span className="text-gold">×{s.level}</span>
                      {s.cost_per_level ? <span className="text-gold/60 text-[10px] ml-2 font-ui uppercase tracking-widest">{s.cost_per_level} pt/lvl</span> : null}
                    </div>
                    {s.note && (
                      <div className="text-[12px] text-parchment/85 italic mt-1 font-body leading-snug"
                           data-testid={`skill-note-${i}`}>
                        {s.note}
                      </div>
                    )}
                    {Array.isArray(s.components) && s.components.length > 0 && (
                      <ul className="mt-1.5 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-0.5 text-[11px] font-body text-mist"
                          data-testid={`skill-components-${i}`}>
                        {s.components.map((c, j) => (
                          <li key={j} className="flex items-baseline gap-1.5">
                            <span className="text-gold/60 font-ui">·</span>
                            <span className="text-parchment/90">{c.name}</span>
                            {c.level ? <span className="text-gold">×{c.level}</span> : null}
                            {c.note && <span className="italic text-mist/70">— {c.note}</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                    <div className="text-[10px] text-mist font-ui uppercase tracking-widest flex items-center gap-1 mt-1.5">
                      <BookOpen className="w-3 h-3"/> {s.page ? `p.${s.page} BESM 4E` : "Custom"}
                    </div>
                  </div>
                  <button onClick={() => roll("2d6", `${s.group} skill roll`)}
                          className="btn btn-ghost text-xs"><Dice6 className="w-3 h-3"/> Roll</button>
                </div>
              ))}
            </div>
          </div>

          {/* Power Packs / Source-of-Power groupings — narrative bundles that
              tie a character's powers, materials, or training back to a
              single in-setting source (BESM Extras p.42 — Power Packs/Bundles). */}
          {Array.isArray(ch.power_packs) && ch.power_packs.length > 0 && (
            <div className="card-mystic p-6" data-testid="power-packs">
              <div className="h-arcane text-sm mb-3">Power Pack · Source of Power</div>
              <div className="space-y-3">
                {ch.power_packs.map((pp, i) => (
                  <div key={i} className="border border-gold/15 rounded-sm p-3" data-testid={`power-pack-${i}`}>
                    <div className="flex items-baseline justify-between flex-wrap gap-2">
                      <div className="text-sm font-ui text-parchment">{pp.name}</div>
                      <div className="text-[10px] font-ui uppercase tracking-widest text-gold/70">
                        {pp.cost ? `${pp.cost} pts` : "Narrative · no cost"}
                      </div>
                    </div>
                    {pp.description && (
                      <div className="text-[12px] text-parchment/85 italic mt-1 font-body leading-snug">
                        {pp.description}
                      </div>
                    )}
                    {Array.isArray(pp.references) && pp.references.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {pp.references.map((r, j) => (
                          <span key={j} className="tag border-arcane/40 text-arcane">{r}</span>
                        ))}
                      </div>
                    )}
                    <div className="text-[10px] text-mist font-ui uppercase tracking-widest flex items-center gap-1 mt-1.5">
                      <BookOpen className="w-3 h-3"/> BESM Extras · Power Packs
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card-mystic p-6">
            <div className="flex items-center justify-between">
              <div className="h-arcane text-sm">Dice</div>
              <select className="select w-auto" value={selectedSession}
                      onChange={(e) => setSelectedSession(e.target.value)} data-testid="dice-session-select">
                <option value="">— no session —</option>
                {sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
              </select>
            </div>
            <div className="grid md:grid-cols-3 gap-3 mt-4">
              <input className="input" placeholder="Notation (e.g. 2d6+body)" value={rollNotation}
                     onChange={(e) => setRollNotation(e.target.value)} data-testid="dice-notation"/>
              <input className="input" placeholder="Label" value={rollLabel}
                     onChange={(e) => setRollLabel(e.target.value)} data-testid="dice-label"/>
              <input className="input" type="number" placeholder="Target (optional)" value={rollTarget}
                     onChange={(e) => setRollTarget(e.target.value)} data-testid="dice-target"/>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {quickRolls.map((q) => (
                <button key={q.label} onClick={() => roll(q.notation, q.label)} className="btn btn-ghost text-xs"
                        data-testid={`quick-${q.label.replace(/\s+/g, '-')}`}>
                  <Dice6 className="w-3 h-3"/> {q.label}
                </button>
              ))}
              <button onClick={() => roll()} className="btn btn-primary text-xs" data-testid="roll-btn">
                <Dice6 className="w-3 h-3"/> Roll
              </button>
            </div>
            {lastRoll && (
              <div className="mt-4 border border-gold/20 rounded-sm p-3 bg-void/40" data-testid="last-roll">
                {lastRoll.error ? (
                  <div className="text-ember text-sm">{lastRoll.error}</div>
                ) : (
                  <div>
                    <div className="text-xs text-mist font-ui uppercase tracking-widest">
                      {lastRoll.label || "Roll"} · {lastRoll.notation}
                    </div>
                    <div className="font-display text-3xl text-gold mt-1">{lastRoll.result?.total}</div>
                    <div className="text-[10px] text-mist font-ui mt-1">
                      {lastRoll.result?.rolls?.map((r, i) => (
                        <span key={i} className="mr-2">
                          {r.results ? `[${r.results.join(",")}]` : r.ref ? `${r.ref}:${r.value}` : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
