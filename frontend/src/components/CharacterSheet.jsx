import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";
import { Dice6, Edit3, BookOpen, Trash2, Printer } from "lucide-react";
import BesmTerm from "./ui/BesmTerm";
import XPApprovalQueue, { XPSpendForm } from "./XPApprovalQueue";
import CharacterApprovalPanel from "./CharacterApprovalPanel";
import CompanionAssignPanel from "./CompanionAssignPanel";

export default function CharacterSheet() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const [ch, setCh] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [err, setErr] = useState("");
  const [rollLabel, setRollLabel] = useState("");
  const [rollNotation, setRollNotation] = useState("2d6");
  const [rollTarget, setRollTarget] = useState("");
  const [lastRoll, setLastRoll] = useState(null);
  const [selectedSession, setSelectedSession] = useState("");
  const [pbpChannelId, setPbpChannelId] = useState(null);
  const [campaign, setCampaign] = useState(null);

  const load = async () => {
    try {
      const data = await api.get(`/characters/${id}`).then((r) => r.data);
      setCh(data);
      const [s, channels, camp] = await Promise.all([
        api.get(`/campaigns/${data.campaign_id}/sessions`).then((r) => r.data),
        api.get(`/campaigns/${data.campaign_id}/channels`).then((r) => r.data).catch(() => []),
        api.get(`/campaigns/${data.campaign_id}`).then((r) => r.data).catch(() => null),
      ]);
      setSessions(s);
      setCampaign(camp);
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
            {(() => {
              // V6.3 — system label is driven by the CAMPAIGN's system_id,
              // not by which folio state-bag happens to be populated. An
              // Anime 5E campaign is Anime 5E regardless of whether the
              // player only filled in the d20 chassis; the Anime 5E rules
              // still govern encounter design, CR, and the optional
              // BESM-style point-buy layer.
              const sysId = campaign?.system_id;
              if (sysId === "anime-5e") {
                const d = dndState || {};
                return `Anime 5E · ${d.class || "Class"} ${d.level || 1} · ${d.race || "Race"}`;
              }
              if (sysId === "dnd-5e" || (!sysId && dndState && !ch.folio?.anime5e_state)) {
                const d = dndState || {};
                return `D&D 5E · ${d.class || "Class"} ${d.level || 1} · ${d.race || "Race"}`;
              }
              if (sysId === "cypher" || (!sysId && cypherState)) {
                const c = cypherState || {};
                return `Cypher · Tier ${c.tier || 1} · ${c.descriptor || "?"} ${c.type || "?"}`;
              }
              return `BESM 4E · ${ch.power_level} · ${ch.total_points} pts`;
            })()}
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
          <CharacterApprovalPanel
            characterId={ch.id}
            isGm={!!(campaign?.is_gm)}
            campaignHouseRules={campaign?.house_rules || ""}
            onChanged={load}/>
          {campaign?.is_gm && (
            <CompanionAssignPanel
              characterId={ch.id}
              campaignId={ch.campaign_id}
              ownerId={ch.owner_id}
              companions={ch.companion_owners || []}
              onChanged={load}/>
          )}
        </div>
        <div className="flex gap-2">
          <button onClick={async () => {
                    try {
                      const token = localStorage.getItem("tg_token");
                      const r = await fetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/characters/${ch.id}/export.pdf?mode=mobile`,
                        { headers: { Authorization: `Bearer ${token}` } });
                      if (!r.ok) throw new Error(`HTTP ${r.status}`);
                      const blob = await r.blob();
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `${(ch.name || "character").replace(/\s+/g, "_")}-sheet.pdf`;
                      document.body.appendChild(a); a.click(); a.remove();
                      URL.revokeObjectURL(url);
                    } catch (e) { window.alert("PDF download failed: " + e.message); }
                  }}
                  className="btn btn-ghost text-xs"
                  data-testid="export-mobile-sheet-btn"
                  title="Download a phone-portrait PDF character sheet (A6) — easy to hand to a player mid-session.">
            <Printer className="w-4 h-4"/> Mobile PDF
          </button>
          <Link to={`/app/characters/${ch.id}/edit`} className="btn" data-testid="edit-character-btn">
            <Edit3 className="w-4 h-4"/> Edit
          </Link>
          <button onClick={delChar} className="btn btn-danger"><Trash2 className="w-4 h-4"/></button>
        </div>
      </div>

      {/* System-shaped read view — D&D 5E / Cypher get their own block;
          BESM 4E (and Anime 5E by default) keep the original tri-stat layout. */}
      {dndState && <DndSheetView state={dndState} folio={ch.folio} roll={roll}/>}
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
                          {a.enhancements.map((e, j) => <span key={`e${j}`}
                            className="tag border-gold/40 text-gold-bright cursor-help"
                            title={`Enhancement: ${e}. Lowers the Attribute's effective Level by 1 — the power is more potent per CP paid. Stacks if listed multiple times.`}>+{e}</span>)}
                          {a.limiters.map((l, j) => <span key={`l${j}`}
                            className="tag border-ember/40 text-ember cursor-help"
                            title={`Limiter: ${l}. Raises the Attribute's effective Level by 1 — the power is narrower, so each CP buys more functional range. Stacks if listed multiple times.`}>−{l}</span>)}
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

          {/* V6.7 — Power Bundles (activatable spell-like packets). Distinct
              from Power Packs (always-on source-of-power). Only renders on
              BESM 4E + Anime 5E hybrid sheets. */}
          {(campaign?.system_id === "besm-4e" || campaign?.system_id === "anime-5e")
            && Array.isArray(ch.power_bundles) && ch.power_bundles.length > 0 && (
            <div className="card-mystic p-6 mt-4" data-testid="character-power-bundles">
              <div className="h-arcane text-sm mb-3">Power Bundle · Activatable Effects</div>
              <div className="space-y-3">
                {ch.power_bundles.map((pb, i) => (
                  <div key={i} className="border-l-2 border-arcane/40 pl-3 py-1">
                    <div className="flex items-baseline justify-between flex-wrap gap-1">
                      <span className="font-ui text-parchment">{pb.name}</span>
                      <div className="flex items-center gap-1 text-[10px] font-ui">
                        <span className="tag border-gold/40 text-gold-bright">{pb.cost} CP</span>
                        <span className="tag border-arcane/30 text-arcane">{pb.invocation || "per-scene"}</span>
                        {pb.charges_max > 0 && <span className="tag border-mist/40 text-mist">{pb.charges_current || 0}/{pb.charges_max}</span>}
                        {pb.energy_cost > 0 && <span className="tag border-ember/30 text-ember">{pb.energy_cost} EP</span>}
                      </div>
                    </div>
                    {pb.description && <div className="text-[11px] text-parchment/85 italic mt-1">{pb.description}</div>}
                    {pb.cooldown && <div className="text-[10px] text-mist mt-1">Cooldown: {pb.cooldown}</div>}
                    {pb.source_spell_name && (
                      <div className="text-[10px] text-mist font-ui uppercase tracking-widest mt-1.5">
                        ↪ Mimics D&D: {pb.source_spell_name} (L{pb.source_spell_level || 0})
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-3 text-[10px] text-mist italic flex items-center gap-1">
                <BookOpen className="w-3 h-3"/> BESM Extras p.42 · Power Bundles
              </div>
            </div>
          )}

          {/* V6.7 — Forge buttons for Power Pack / Bundle. Visible to
              the owner so they can author new ones via the Atelier. */}
          {(campaign?.system_id === "besm-4e" || campaign?.system_id === "anime-5e")
            && user?.id === ch.owner_id && (
            <div className="card-mystic p-4 mt-4 flex items-center justify-between flex-wrap gap-2"
                 data-testid="character-forge-power-bundles">
              <div>
                <div className="label-ref">Power forge</div>
                <div className="text-[11px] text-mist italic">
                  Author new packs (always-on sources of power) or bundles (activatable effects) in the Atelier — they show up here once saved on the sheet.
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Link to={`/app/campaigns/${ch.campaign_id}?tab=atelier&kind=power_pack`}
                      className="btn btn-ghost text-xs"
                      data-testid="forge-power-pack-link">
                  + Power Pack
                </Link>
                <Link to={`/app/campaigns/${ch.campaign_id}?tab=atelier&kind=power_bundle`}
                      className="btn btn-ghost text-xs"
                      data-testid="forge-power-bundle-link">
                  + Power Bundle
                </Link>
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

      {/* Journal — universal across all systems. Fed by /characters/{id}/journal,
          which timestamps each entry and (optionally) auto-pins it to the
          campaign's World Codex as a `player_journal` node. The textbox stays
          editable inline; rendered entries are read-only with a delete affordance
          handled by the GM/owner. */}
      <CharacterJournal character={ch} onUpdated={load}/>

    </div>
  );
}

function CharacterJournal({ character, onUpdated }) {
  const entries = character.folio?.journal || [];
  const [text, setText] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState("");
  const submit = async () => {
    const t = text.trim();
    if (!t) return;
    setBusy(true); setErr("");
    try {
      await api.post(`/characters/${character.id}/journal`, { text: t });
      setText("");
      onUpdated && onUpdated();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };
  return (
    <div className="card-mystic p-6 mt-6" data-testid="character-journal">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="label-ref">Character Journal</div>
          <div className="text-[11px] text-mist/70 italic mt-1">
            Anything you write here is timestamped and pushed to the campaign's World Codex
            as a player journal node — feeds session recaps too.
          </div>
        </div>
        <span className="text-[10px] text-mist tracking-widest uppercase">
          {entries.length} entr{entries.length === 1 ? "y" : "ies"}
        </span>
      </div>
      <div className="mt-3 flex gap-2">
        <textarea className="input min-h-[60px] flex-1"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="What does your character note about today's session?"
                  data-testid="character-journal-input"/>
        <button onClick={submit} disabled={busy || !text.trim()}
                className="btn btn-primary text-xs self-stretch px-4"
                data-testid="character-journal-submit">
          {busy ? "Posting…" : "Add"}
        </button>
      </div>
      {err && <div className="text-ember text-xs mt-2" data-testid="character-journal-error">{err}</div>}
      {entries.length > 0 && (
        <div className="mt-4 space-y-2 max-h-[420px] overflow-y-auto pr-1">
          {[...entries].reverse().map((e, i) => (
            <div key={i} className="border border-gold/15 rounded-sm p-3"
                 data-testid={`character-journal-entry-${i}`}>
              <div className="text-[10px] text-mist tracking-widest uppercase mb-1">
                {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
                {e.session_id ? ` · session ${e.session_id.slice(0, 6)}…` : ""}
              </div>
              <div className="text-sm text-parchment whitespace-pre-wrap font-body">{e.text}</div>
            </div>
          ))}
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
function DndSheetView({ state, folio, roll }) {
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
        <div className="label-ref">Class · Race · Background</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
          <Stat label="Class" v={state.class || "—"}/>
          <Stat label="Level" v={lvl}/>
          <Stat label="Race" v={state.race || "—"}/>
          <Stat label="Proficiency" v={`+${profBonus}`}/>
        </div>

        {/* Detailed chassis summary — hit-die · saves · casting (class);
            ASI · size · speed · traits (race); skills · tools · feature
            (background). Same layout the D&D builder surfaces near the
            top, mirrored onto the sheet view so Anime 5E hybrid sheets
            (which share the dnd_state folio) read consistently. */}
        {(() => {
          // Best-effort defaults for classes not in the campaign ref.
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

      {/* Spell slots — derived from class + level using the SRD tables.
          Adept/Cleric/Druid/Sorcerer/Wizard/Bard = full caster.
          Paladin/Ranger = half caster (slots start at level 2).
          Warlock = pact-magic. Non-casters get nothing rendered. */}
      {(() => {
        const cls = state.class;
        const FULL = ["Bard","Cleric","Druid","Sorcerer","Wizard"];
        const HALF = ["Paladin","Ranger"];
        const isFull = FULL.includes(cls);
        const isHalf = HALF.includes(cls);
        const isWarlock = cls === "Warlock";
        if (!isFull && !isHalf && !isWarlock) return null;
        // Hard-coded SRD 5.1 spell-slot tables — matches the dnd5e_data.py
        // tables shipped backend-side. Keeping them here too so the sheet
        // renders without an extra round-trip.
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

      {/* Anime 5E — Energy Points pool. Only renders if this is an
          Anime 5E hybrid sheet (folio has anime5e_state). EP is the
          anime-flavoured resource pool for signature techniques per the
          Anime 5E v1.02 sheet. `folio.anime5e_state.ep_max` / `ep_current`
          let the player & GM track it without an extra sheet pass. */}
      {folio?.anime5e_state && (() => {
        const an = folio.anime5e_state;
        const epMax = an.ep_max ?? 10 + (mod("Charisma") * lvl);
        const epCur = an.ep_current ?? epMax;
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

      {/* Combat Gear & Boons — magical items, +1 weapons/armor, class
          attunements. Free-form but with a TAG column so the table can
          see instantly what's enchanted. Stored at
          state.magic_items[] = [{name, slot, tag, notes}]. */}
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

      {/* Class features unlocked by level — the "what did I get at level
          up" reference the table always asks for. Data-driven from
          state.class_features[] = [{level, name, blurb}]. If empty, we
          render a gentle prompt so the player knows to populate it. */}
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

      {/* Racial/heritage traits — explicit card so these don't get lost
          in the chassis summary. If state.racial_traits is empty we
          hide (chassis card already showed the shorthand list). */}
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

      {/* Anime 5E hybrid — render the Tri-Stat point-buy supplement read-only
          if the character carries one. The supplement lives at
          folio.anime5e_state.point_buys[]. We surface it so the GM and table
          can see the genre-power layer alongside the d20 sheet. */}
      <Anime5eSupplementView folio={folio}/>

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
  const tier = Math.max(1, +(state.tier || 1));
  const cypherLimit = state.cypher_limit ?? (state.starting_cypher_limit || 2);
  const armor = state.armor || 0;
  const recoveriesMax = state.recoveries_max || 4;
  const recoveriesUsed = state.recoveries_used || 0;
  const recoveryDie = state.recovery_die
    || `1d6+${Math.min(6, Math.max(1, tier))}`;
  const rollAtDifficulty = () => {
    const label = `Cypher roll · diff ${diff}${extraSteps ? ` (−${extraSteps} steps)` : ""} · TN ${target}`;
    roll("1d20", label);
  };
  const quickRolls = [
    { label: "Cypher Roll (d20)", notation: "1d20",
      hint: "1d20 ≥ 3 × difficulty. Train/Specialise/Effort/Asset each lower difficulty 1 step." },
    { label: `Recovery (${recoveryDie})`, notation: recoveryDie, hint: "Cypher pool recovery roll." },
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

      {/* Cypher derived block — Armor (damage soak), Recovery rolls remaining,
          Cypher carry limit (Tier-based), Effort cap. These are the canonical
          Cypher derived values the table needs to see at a glance. */}
      <div className="card-mystic p-5 mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center"
           data-testid="cypher-derived-block">
        <div className="border border-gold/15 rounded-sm py-2">
          <div className="label-ref">Armor</div>
          <div className="font-display text-2xl text-gold-bright"
               data-testid="cypher-armor-value">{armor}</div>
          <div className="text-[9px] text-mist">soak / hit</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-2">
          <div className="label-ref">Cypher Limit</div>
          <div className="font-display text-2xl text-gold-bright"
               data-testid="cypher-limit-value">{cypherLimit}</div>
          <div className="text-[9px] text-mist">max carried</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-2"
             data-testid="cypher-recoveries-block">
          <div className="label-ref">Recoveries</div>
          <div className="font-display text-2xl text-gold-bright">
            {Math.max(0, recoveriesMax - recoveriesUsed)}
            <span className="text-mist text-xs"> / {recoveriesMax}</span>
          </div>
          <div className="text-[9px] text-mist">{recoveryDie}/day</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-2">
          <div className="label-ref">Effort</div>
          <div className="font-display text-2xl text-gold-bright">{state.effort || 1}</div>
          <div className="text-[9px] text-mist">max steps</div>
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
          <div className="label-ref flex items-center gap-2">
            Skills Trained
            <span className="text-[10px] text-mist/70 italic normal-case tracking-normal"
                  title="Trained skills: difficulty of tasks using this skill is lowered by 1 step (Specialised lowers by 2). Inability: raised by 1 step.">
              (hover any tag)
            </span>
          </div>
          <div className="flex flex-wrap gap-1 mt-2">
            {state.skill_trains.map((s) => {
              const [skill, kind] = (typeof s === "string")
                ? [s, /^specialised?:/i.test(s) ? "specialised"
                     : /^inability:/i.test(s) ? "inability" : "trained"]
                : [s.name, s.kind || "trained"];
              const tooltip = kind === "specialised"
                ? `Specialised in ${skill}: difficulty lowered by 2 steps — normally requires two training slots.`
                : kind === "inability"
                ? `Inability with ${skill}: difficulty raised by 1 step. Often taken for roleplay or to free a training slot.`
                : `Trained in ${skill}: difficulty lowered by 1 step on applicable tasks.`;
              const cls = kind === "specialised" ? "border-arcane/50 text-arcane"
                        : kind === "inability" ? "border-ember/40 text-ember"
                        : "border-gold/40 text-gold-bright";
              return <span key={typeof s === "string" ? s : s.name}
                           className={`tag cursor-help ${cls}`}
                           title={tooltip}>{skill}</span>;
            })}
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

// Anime 5E hybrid supplement — read-only echo on the character sheet.
// Displays the BESM-style point-buy attributes the player layered on top
// of their d20 chassis (`folio.anime5e_state.point_buys[]`). Pure
// presentation. Anime 5E is a D&D 5E chassis with an OPTIONAL BESM-style
// point-buy layer — it is NOT Tri-Stat. Body / Mind / Soul scores are
// absent here.
function Anime5eSupplementView({ folio }) {
  const state = folio?.anime5e_state;
  const buys = state?.point_buys || [];
  if (!state || buys.length === 0) return null;
  const totalSpent = buys.reduce(
    (sum, b) => sum + ((b.cost_per_level || 0) * (b.level || 1)), 0);
  return (
    <div className="card-mystic p-6 mt-4 border-l-4"
         style={{ borderLeftColor: "#E03A8E" }}
         data-testid="anime5e-sheet-supplement">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <div className="label-ref">BESM Point-Buy Layer · Anime 5E hybrid</div>
          <div className="text-[11px] text-mist/80 italic">
            Genre-power layer over the d20 chassis. BESM-style point-buy (one-way port from 5E).
          </div>
        </div>
        <div className="text-right">
          <div className="font-display text-xl text-gold">{totalSpent}<span className="text-mist text-sm"> / {state.point_budget || 50}</span></div>
          <div className="text-[10px] text-mist">pts spent</div>
        </div>
      </div>
      <div className="mt-3 space-y-2">
        {buys.map((b, i) => (
          <div key={i} className="border border-gold/15 rounded-sm p-2 flex items-center justify-between gap-3"
               data-testid={`anime5e-sheet-buy-${i}`}>
            <div className="min-w-0 flex-1">
              <div className="text-sm text-parchment font-ui"><b>{b.name}</b>
                <span className="text-[10px] text-mist ml-2">×{b.level}</span>
              </div>
              {b.blurb_role && <div className="text-[11px] text-mist/70 italic">{b.blurb_role}</div>}
            </div>
            <span className="font-display text-gold">{(b.cost_per_level || 0) * (b.level || 1)} pts</span>
          </div>
        ))}
      </div>
    </div>
  );
}
