import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { Dice6, Edit3, BookOpen, Trash2 } from "lucide-react";
import BesmTerm from "./ui/BesmTerm";
import XPApprovalQueue, { XPSpendForm } from "./XPApprovalQueue";

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
  // System-aware quick-rolls: D&D 5E uses d20 + ability mod, Cypher uses
  // 1d20 vs (3 × difficulty). Detected via `folio.dnd_state` /
  // `folio.cypher_state` populated by the system-shaped builders.
  const dndState = ch.folio?.dnd_state;
  const cypherState = ch.folio?.cypher_state;
  const _systemKind = dndState ? "dnd-5e" : cypherState ? "cypher" : "besm-4e";

  const quickRolls = dndState
    ? (() => {
        const lvl = Math.max(1, +(dndState.level || 1));
        const profBonus = Math.max(2, 2 + Math.floor((lvl - 1) / 4));
        const sc = dndState.ability_scores || {};
        const mod = (s) => Math.floor(((sc[s] | 0) - 10) / 2);
        const fmt = (n) => (n >= 0 ? `+${n}` : `${n}`);
        const six = ["Strength", "Dexterity", "Constitution",
                      "Intelligence", "Wisdom", "Charisma"];
        return six.map((s) => ({
          label: `${s.slice(0, 3).toUpperCase()} check`,
          notation: `1d20${fmt(mod(s))}`,
          hint: `d20 + ${s} mod (SRD 5.1)`,
        })).concat([
          { label: "Initiative", notation: `1d20${fmt(mod("Dexterity"))}`,
            hint: "d20 + DEX mod" },
          { label: "Attack (PROF + STR)",
            notation: `1d20${fmt(mod("Strength") + profBonus)}`,
            hint: "d20 + STR mod + proficiency" },
          { label: "Attack (PROF + DEX)",
            notation: `1d20${fmt(mod("Dexterity") + profBonus)}`,
            hint: "d20 + DEX mod + proficiency" },
        ]);
      })()
    : cypherState
    ? [
        { label: "Cypher Roll (d20)", notation: "1d20",
          hint: "Roll 1d20 ≥ (3 × difficulty). Effort/Edge lower difficulty 1 step each." },
        { label: "Recovery (1d6)",   notation: "1d6+1",
          hint: "Cypher recovery roll — pool restoration." },
        { label: "Cypher Damage",    notation: "1d6",
          hint: "Light cypher damage die." },
      ]
    : [
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
          <div className="label-ref mb-1" data-testid="sheet-system-label">
            {dndState
              ? `D&D 5E · ${dndState.class || "Class"} ${dndState.level || 1} · ${dndState.race || "Race"}`
              : cypherState
              ? `Cypher · Tier ${cypherState.tier || 1} · ${cypherState.descriptor || "?"} ${cypherState.type || "?"}`
              : `BESM 4E · ${ch.power_level} · ${ch.total_points} pts`}
          </div>
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
            {(ch.xp_total || ch.xp_unspent) ? (
              <span className="ml-2 text-arcane-light"
                    title="BESM 4E p.232 — Advancement. 1 XP ≈ 1 Character Point at GM discretion."
                    data-testid="sheet-xp-badge">
                · XP {Number(ch.xp_total || 0).toFixed(2)} earned · {Number(ch.xp_unspent || 0).toFixed(2)} unspent
              </span>
            ) : null}
          </div>
          <div className="mt-3">
            <XPSpendForm characterId={ch.id} character={ch} onProposed={load}/>
          </div>
          <XPApprovalQueue campaignId={ch.campaign_id} characterId={ch.id} isGm={false} onUpdate={load}/>
        </div>
        <div className="flex gap-2">
          <Link to={`/app/characters/${ch.id}/edit`} className="btn" data-testid="edit-character-btn">
            <Edit3 className="w-4 h-4"/> Edit
          </Link>
          <button onClick={delChar} className="btn btn-danger"><Trash2 className="w-4 h-4"/></button>
        </div>
      </div>

      {/* System-shaped read view — D&D 5E / Cypher get their own block;
          BESM 4E (and Anime 5E by default) keep the original tri-stat layout. */}
      {dndState && <DndSheetView state={dndState} roll={roll}/>}
      {cypherState && <CypherSheetView state={cypherState} roll={roll}/>}
      {!dndState && !cypherState && (
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
            <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
              <div className="h-arcane text-sm">Attributes</div>
              <div className="text-[9px] font-ui uppercase tracking-widest text-mist/60"
                   title="BESM 4E V4.1 — each Enhancement / Limiter row equals exactly one application. To apply the same modifier twice, list it twice.">
                <span className="text-gold-bright">×n assigned</span> · paid points · {" "}
                <span className="text-arcane-light">eff. ×n</span> = function lvl {" "}
                (+1 per Limiter, −1 per Enhancement, floored 1)
              </div>
            </div>
            {ch.attributes.length === 0 && <div className="text-mist italic text-xs">—</div>}
            <div className="space-y-2">
              {ch.attributes.map((a, i) => {
                // BESM 4E V4.1: each toggled Enhancement / Limiter row is exactly
                // ONE application. Multiple applications of the same name require
                // re-listing it (the array preserves duplicates). Effective Level
                // = assigned Level + #Limiters − #Enhancements (floored at 1).
                const enhCount = (a.enhancements || []).length;
                const limCount = (a.limiters || []).length;
                const itemDefRefund = (a.defects || []).reduce(
                  (s, d) => s + (d.points_per_rank || 0) * (d.rank || 0), 0);
                const effLvl = typeof a.effective_level === "number"
                  ? a.effective_level
                  : Math.max(1, (a.level || 1) + limCount - enhCount);
                const effDelta = effLvl - (a.level || 1);
                return (
                <div key={i} className="border border-gold/10 rounded-sm p-3 flex items-start justify-between flex-wrap gap-2">
                  <div className="min-w-0 flex-1">
                    {a.display_name && (
                      <div className="text-sm text-parchment font-ui font-semibold mb-0.5"
                           data-testid={`attr-display-${i}`}>{a.display_name}</div>
                    )}
                    <div className="text-sm font-ui">
                      <BesmTerm name={a.name} cost={`${a.cost_per_level} pts/level`}
                                page={a.page} note={a.note}
                                book={a.page ? "BESM 4E" : "Custom"}/>
                      <span className="text-gold ml-2" title="Assigned Level — what the player paid points for">
                        ×{a.level} <span className="text-gold/60 text-[10px] font-ui">assigned</span>
                      </span>
                      {effDelta !== 0 && (
                        <span className="ml-2 text-arcane-light text-[11px] font-ui uppercase tracking-widest"
                              title={`BESM 4E: cost stays at ${a.cost_per_level}×${a.level}. Each Enhancement lowers effective Level by 1 (more potent per assigned point). Each Limiter raises it by 1 (narrower scope = more functional power). Floored at 1.`}
                              data-testid={`attr-eff-level-${i}`}>
                          eff. ×{effLvl}
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
                      <span className="ml-2 text-gold/70">
                        cost {a.cost_per_level}×{a.level} = {Math.max(0, a.cost_per_level * a.level - itemDefRefund)} pts
                        {itemDefRefund > 0 ? ` (${a.cost_per_level * a.level} − ${itemDefRefund} item-defect refund)` : ""}
                      </span>
                    </div>
                    {(enhCount > 0 || limCount > 0) && (
                      <div className="mt-1.5">
                        <div className="text-[9px] font-ui uppercase tracking-widest text-mist/60 mb-1"
                             data-testid={`attr-applications-${i}`}>
                          {enhCount + limCount} application{enhCount + limCount === 1 ? "" : "s"} ·
                          {" "}{enhCount} enhancement{enhCount === 1 ? "" : "s"} ↓eff
                          {" "}· {limCount} limiter{limCount === 1 ? "" : "s"} ↑eff
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {a.enhancements.map((e, j) => <span key={`e${j}`} className="tag border-gold/40 text-gold-bright" title="Enhancement — lowers effective Level by 1">+{e}</span>)}
                          {a.limiters.map((l, j) => <span key={`l${j}`} className="tag border-ember/40 text-ember" title="Limiter — raises effective Level by 1">−{l}</span>)}
                        </div>
                      </div>
                    )}
                  </div>
                  <button onClick={() => roll("2d6", `${a.name} roll`)}
                          className="btn btn-ghost text-xs" data-testid={`attr-roll-${i}`}>
                    <Dice6 className="w-3 h-3"/> 2d6
                  </button>
                </div>
                );
              })}
            </div>
          </div>

          <div className="card-mystic p-6">
            <div className="h-arcane text-sm mb-3">Defects</div>
            {ch.defects.length === 0 && <div className="text-mist italic text-xs">—</div>}
            <div className="space-y-2">
              {ch.defects.map((d, i) => (
                <div key={i} className="border border-gold/10 rounded-sm p-3 flex items-start justify-between flex-wrap gap-2">
                  <div className="min-w-0 flex-1">
                    {d.display_name && (
                      <div className="text-sm text-parchment font-ui font-semibold mb-0.5"
                           data-testid={`defect-display-${i}`}>{d.display_name}</div>
                    )}
                    <div className="text-sm font-ui">
                      <BesmTerm name={d.name} cost={`${d.points_per_rank} pts/rank`}
                                page={d.page} note={d.note} category={d.category}
                                book={d.page ? "BESM 4E" : "Custom"}/>
                      <span className="text-ember ml-2" title="Rank — narrative severity">
                        ×{d.rank} <span className="text-ember/60 text-[10px] font-ui">rank</span>
                      </span>
                    </div>
                    {d.note && (
                      <div className="text-[12px] text-parchment/85 italic mt-1 font-body leading-snug"
                           data-testid={`defect-note-${i}`}>
                        {d.note}
                      </div>
                    )}
                    <div className="text-[10px] text-mist font-ui uppercase tracking-widest flex items-center gap-1 mt-1">
                      <BookOpen className="w-3 h-3"/> {d.page ? `p.${d.page} BESM 4E` : "Custom"} · {d.category}
                      <span className="ml-2 text-ember/70">refunds {d.points_per_rank}×{d.rank} = {d.points_per_rank * d.rank} pts</span>
                    </div>
                  </div>
                  <span className="text-ember font-display">+{d.points_per_rank * d.rank}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card-mystic p-6">
            <div className="h-arcane text-sm mb-3">Skill Groups</div>
            {ch.skills.length === 0 && <div className="text-mist italic text-xs">—</div>}
            <div className="space-y-2">
              {ch.skills.map((s, i) => {
                const totalCost = (s.cost_per_level || 0) * (s.level || 0);
                const compCount = Array.isArray(s.components) ? s.components.length : 0;
                return (
                <div key={i} className="border border-gold/10 rounded-sm p-3 flex items-start justify-between flex-wrap gap-2">
                  <div className="min-w-0 flex-1">
                    {s.display_name && (
                      <div className="text-sm text-parchment font-ui font-semibold mb-0.5"
                           data-testid={`skill-display-${i}`}>{s.display_name}</div>
                    )}
                    <div className="text-sm text-parchment font-ui">
                      {s.group} <span className="text-gold" title="Group Level">×{s.level}</span>
                      <span className="text-gold/50 text-[10px] ml-1 font-ui">assigned</span>
                      {s.cost_per_level ? (
                        <span className="text-gold/60 text-[10px] ml-2 font-ui uppercase tracking-widest">
                          {s.cost_per_level} pt/lvl · {totalCost} pts total
                        </span>
                      ) : null}
                      {compCount > 0 && (
                        <span className="text-mist/60 text-[10px] ml-2 font-ui">
                          · {compCount} component{compCount === 1 ? "" : "s"}
                        </span>
                      )}
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
                );
              })}
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
      )}
    </div>
  );
}

// ─── Reusable DiceCard ────────────────────────────────────────────────
function DiceCard({ quickRolls, roll }) {
  // Lightweight wrapper so D&D / Cypher views get the same dice surface
  // without duplicating the markup. Reads quickRolls from the parent so
  // the macros stay system-shaped (1d20+mod for D&D, 1d20 for Cypher).
  return (
    <div className="card-mystic p-6 mt-6" data-testid="system-dice-card">
      <div className="h-arcane text-sm">Dice Macros</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {quickRolls.map((q) => (
          <button key={q.label} onClick={() => roll(q.notation, q.label)}
                  className="btn btn-ghost text-xs"
                  title={q.hint || q.notation}
                  data-testid={`quick-${q.label.replace(/\s+/g, "-")}`}>
            <Dice6 className="w-3 h-3"/> {q.label}
          </button>
        ))}
      </div>
      <div className="text-[10px] text-mist/70 italic mt-2">
        Click a macro to post the roll into the campaign's first PBP channel.
        Open a session to also feed the live spotlight + dice altar.
      </div>
    </div>
  );
}

// ─── D&D 5E read view ─────────────────────────────────────────────────
function DndSheetView({ state, roll }) {
  const sc = state.ability_scores || {};
  const lvl = Math.max(1, +(state.level || 1));
  const profBonus = Math.max(2, 2 + Math.floor((lvl - 1) / 4));
  const mod = (s) => Math.floor(((sc[s] | 0) - 10) / 2);
  const fmt = (n) => (n >= 0 ? `+${n}` : `${n}`);
  const six = ["Strength", "Dexterity", "Constitution",
                "Intelligence", "Wisdom", "Charisma"];
  const abbr = { Strength: "STR", Dexterity: "DEX", Constitution: "CON",
                  Intelligence: "INT", Wisdom: "WIS", Charisma: "CHA" };
  // Quick rolls reused inside DiceCard for D&D
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
        <div className="label-ref">Class · Race</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
          <Stat label="Class" v={state.class || "—"}/>
          <Stat label="Level" v={lvl}/>
          <Stat label="Race" v={state.race || "—"}/>
          <Stat label="Proficiency" v={`+${profBonus}`}/>
        </div>
        {state.background && (
          <div className="mt-3 text-[12px] text-parchment/80 font-ui">
            <span className="text-mist">Background:</span> {state.background}
          </div>
        )}
      </div>

      {/* HP / Status ring — auto-computed max HP at level (class hit-die avg
          + CON mod per level), current HP from `state.hp_current` if set.
          Lets the GM track per-PC damage between sessions. */}
      {(() => {
        const conMod = mod("Constitution");
        const hitDie = state.class && state.hit_die ? state.hit_die : null;
        // Best-effort default hit die (can be edited via state.hit_die)
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
            return (
              <button key={s}
                      onClick={() => roll(`1d20${fmt(m)}`, `${state.class || ""} · ${abbr[s]} check`)}
                      className="border border-gold/15 rounded-sm py-2 hover:border-gold/40 hover:bg-gold/5 transition-colors group"
                      data-testid={`dnd-sheet-roll-${abbr[s]}`}
                      title={`Roll d20 ${fmt(m)}`}>
                <div className="label-ref">{abbr[s]}</div>
                <div className="font-display text-2xl text-gold">{sc[s] | 0}</div>
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

      <DiceCard quickRolls={quickRolls} roll={roll}/>
    </div>
  );
}

// ─── Cypher read view ─────────────────────────────────────────────────
function CypherSheetView({ state, roll }) {
  const [diff, setDiff] = useState(3);
  const [extraSteps, setExtraSteps] = useState(0);
  const sentence = state.sentence || (() => {
    const article = /^[aeiouAEIOU]/.test(state.descriptor || "") ? "an" : "a";
    return `I am ${article} ${state.descriptor || "?"} ${state.type || "?"} who ${(state.focus || "").toLowerCase() || "?"}.`;
  })();
  // Cypher target = (difficulty - steps_lowered) × 3, floor 0.
  const effectiveDiff = Math.max(0, diff - Math.max(0, extraSteps));
  const target = effectiveDiff * 3;
  const rollAtDifficulty = () => {
    const label = `Cypher roll · diff ${diff}${extraSteps ? ` (−${extraSteps} steps)` : ""} · TN ${target}`;
    roll("1d20", label);
  };
  const quickRolls = [
    { label: "Cypher Roll (d20)", notation: "1d20",
      hint: "1d20 ≥ 3 × difficulty. Train/Specialise/Effort/Asset each lower difficulty 1 step." },
    { label: "Recovery (1d6+1)", notation: "1d6+1", hint: "Cypher pool recovery roll." },
    { label: "Light Cypher Damage", notation: "1d6", hint: "Single-target light damage die." },
  ];
  return (
    <div data-system="cypher" data-testid="cypher-sheet-view">
      {/* Sentence */}
      <div className="card-mystic p-6 mt-8">
        <div className="label-ref">Character Sentence</div>
        <div className="text-base text-gold-bright italic mt-2"
             data-testid="cypher-sheet-sentence">"{sentence}"</div>
        <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] text-mist">
          <div><span className="label-ref">Descriptor</span> {state.descriptor || "—"}</div>
          <div><span className="label-ref">Type</span> {state.type || "—"}</div>
          <div><span className="label-ref">Focus</span> {state.focus || "—"}</div>
        </div>
      </div>

      {/* Pools + Edge — visual rings to show damage taken at-a-glance.
          The Pool max is the value entered when the PC was built; the
          *current* pool tracks damage taken. Players (and the GM) can
          adjust the current value with the small +/− buttons; the visual
          ring fills proportionally. */}
      <div className="card-mystic p-6 mt-4" data-testid="cypher-pool-rings">
        <div className="label-ref">Stat Pools (current / max) — damage tracker</div>
        <div className="grid grid-cols-3 gap-3 mt-3">
          {["Might", "Speed", "Intellect"].map((k) => {
            const max = state.pools?.[k] ?? 0;
            const cur = state.current_pools?.[k] ?? max;
            const pct = max > 0 ? Math.max(0, Math.min(100, (cur / max) * 100)) : 0;
            const colour = pct > 66 ? "#3FAA62" : pct > 33 ? "#C8A34A" : "#7A1F2E";
            return (
              <div key={k} className="border border-gold/15 rounded-sm p-3 text-center"
                   data-testid={`cypher-pool-ring-${k.toLowerCase()}`}>
                <div className="label-ref text-[9px]">{k}</div>
                <div className="font-display text-2xl text-gold">
                  <span style={{ color: colour }}>{cur}</span>
                  <span className="text-mist text-xs"> / {max}</span>
                </div>
                <div className="h-1.5 bg-void/60 rounded-full mt-1 overflow-hidden">
                  <div className="h-full transition-all"
                       style={{ width: `${pct}%`, backgroundColor: colour }}/>
                </div>
                <div className="text-[10px] font-ui text-mist mt-1">
                  Edge <span className="text-gold-bright">{state.edge?.[k] ?? 0}</span>
                </div>
              </div>
            );
          })}
        </div>
        <div className="text-[10px] text-mist/70 italic mt-2">
          Players: spend Pool with the Effort lever above. GMs: edit `current_pools` on the character sheet to mark damage between sessions.
        </div>
      </div>

      {/* Difficulty tracker — the canonical Cypher dice surface */}
      <div className="card-mystic p-6 mt-4" data-testid="cypher-difficulty-tracker">
        <div className="label-ref">Difficulty Tracker</div>
        <div className="grid sm:grid-cols-3 gap-3 mt-3 items-end">
          <div>
            <label className="label-ref">Task Difficulty (0-10)</label>
            <input className="input" type="number" min={0} max={10} value={diff}
                   onChange={(e) => setDiff(Math.max(0, Math.min(10, +e.target.value || 0)))}
                   data-testid="cypher-diff-input"/>
          </div>
          <div>
            <label className="label-ref">Steps Lowered (Train/Effort/Asset)</label>
            <input className="input" type="number" min={0} max={10} value={extraSteps}
                   onChange={(e) => setExtraSteps(Math.max(0, Math.min(10, +e.target.value || 0)))}
                   data-testid="cypher-steps-input"/>
          </div>
          <div className="text-center border border-gold/30 rounded-sm py-3 bg-gold/5">
            <div className="label-ref">Target Number</div>
            <div className="font-display text-3xl text-gold-bright" data-testid="cypher-tn">
              {target}
            </div>
            <div className="text-[10px] text-mist">eff. diff {effectiveDiff}</div>
          </div>
        </div>
        <button onClick={rollAtDifficulty} className="btn btn-primary mt-3"
                data-testid="cypher-roll-against-tn">
          <Dice6 className="w-4 h-4"/> Roll 1d20 vs TN {target}
        </button>

        {/* Effort and Edge usage hints — sit beneath the tracker because
            they're the levers a player pulls to lower the TN before the roll. */}
        <div className="grid sm:grid-cols-3 gap-2 mt-3 text-[11px] text-mist">
          <div className="border border-gold/15 rounded-sm p-2">
            <div className="label-ref text-[9px]">Effort</div>
            <div className="text-parchment font-ui">Spend (3 + 2× extra) Pool to lower difficulty 1 step / level. Max = Edge + 1.</div>
          </div>
          <div className="border border-gold/15 rounded-sm p-2">
            <div className="label-ref text-[9px]">Edge ({(state.edge?.Might||0)+(state.edge?.Speed||0)+(state.edge?.Intellect||0)} total)</div>
            <div className="text-parchment font-ui">Reduces Pool cost of Effort &amp; abilities by Edge for that pool.</div>
          </div>
          <div className="border border-gold/15 rounded-sm p-2">
            <div className="label-ref text-[9px]">Skill / Asset</div>
            <div className="text-parchment font-ui">Trained −1 step · Specialised −2 · Asset −1 (max 2 assets).</div>
          </div>
        </div>
      </div>

      {/* Intrusion ledger — Cypher's signature narrative tax. The GM offers
          an unfortunate complication; the player accepts (+2 XP self, +2 XP
          ally) or refuses (−1 XP). Buttons post a chat-side ledger entry. */}
      <div className="card-mystic p-6 mt-4" data-testid="cypher-intrusion-ledger">
        <div className="label-ref flex items-center gap-2">
          GM Intrusion Ledger
          <span className="text-[9px] text-mist normal-case tracking-normal italic">accept = +2 XP self · +2 XP ally · refuse = −1 XP</span>
        </div>
        <div className="flex gap-2 mt-3 flex-wrap">
          <button onClick={() => roll("0+2", "Intrusion accepted · +2 XP")}
                  className="btn btn-ghost text-xs"
                  title="Log accepting a GM intrusion (+2 XP self, +2 XP ally)"
                  data-testid="cypher-intrusion-accept">
            ✓ Accept (+2/+2)
          </button>
          <button onClick={() => roll("0-1", "Intrusion refused · −1 XP")}
                  className="btn btn-ghost text-xs"
                  title="Log refusing a GM intrusion (−1 XP)"
                  data-testid="cypher-intrusion-refuse">
            ✗ Refuse (−1)
          </button>
          <span className="text-[10px] text-mist italic ml-2 self-center">
            Logged as a chat ledger entry — GM can convert to formal XP via the XP Approval Queue.
          </span>
        </div>
      </div>

      {(state.skill_trains?.length || 0) > 0 && (
        <div className="card-mystic p-6 mt-4">
          <div className="label-ref">Skills Trained</div>
          <div className="flex flex-wrap gap-1 mt-2">
            {state.skill_trains.map((s) => <span key={s} className="tag border-gold/40 text-gold-bright">{s}</span>)}
          </div>
        </div>
      )}
      {(state.abilities?.length || 0) > 0 && (
        <SimpleListCard title="Type / Focus Abilities" items={state.abilities}
                         testid="cypher-sheet-abilities"/>
      )}
      {(state.cyphers?.length || 0) > 0 && (
        <SimpleListCard title="Cyphers Carried" items={state.cyphers}
                         testid="cypher-sheet-cyphers"/>
      )}
      {state.notes && (
        <div className="card-mystic p-6 mt-4">
          <div className="label-ref">Notes / GM Intrusion ledger</div>
          <div className="text-sm text-mist mt-2 whitespace-pre-wrap font-body">{state.notes}</div>
        </div>
      )}

      <DiceCard quickRolls={quickRolls} roll={roll}/>

      <div className="text-[10px] text-mist/60 italic mt-3 text-center">
        Cypher System Creator · Requires the Cypher System Rulebook from Monte Cook Games.
      </div>
    </div>
  );
}

function Stat({ label, v }) {
  return (
    <div>
      <div className="label-ref">{label}</div>
      <div className="font-display text-xl text-gold-bright">{v}</div>
    </div>
  );
}

function SimpleListCard({ title, items, testid }) {
  return (
    <div className="card-mystic p-6 mt-4" data-testid={testid}>
      <div className="label-ref">{title}</div>
      <ul className="mt-2 space-y-1">
        {items.map((it, i) => (
          <li key={i} className="text-sm text-parchment font-body">· {it}</li>
        ))}
      </ul>
    </div>
  );
}
