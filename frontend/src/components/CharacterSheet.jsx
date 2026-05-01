import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";
import { Dice6, Edit3, BookOpen, Trash2, Printer } from "lucide-react";
import BesmTerm from "./ui/BesmTerm";
import XPApprovalQueue, { XPSpendForm } from "./XPApprovalQueue";
import CharacterApprovalPanel from "./CharacterApprovalPanel";
import CompanionAssignPanel from "./CompanionAssignPanel";
import CharacterStatusRings from "./CharacterStatusRings";
import CharacterPortrait from "./CharacterPortrait";
import DndSheetView from "./sheets/DndSheetView";
import CypherSheetView from "./sheets/CypherSheetView";
import { CharacterJournal } from "./sheets/sheetCommon";

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
  // V6.14 — active sub-tab. Valid: identity | mechanics | inventory | history.
  const [sheetTab, setSheetTab] = useState(() => {
    const h = ((typeof window !== "undefined" && window.location.hash) || "")
      .replace("#", "");
    return ["identity", "mechanics", "inventory", "history"].includes(h) ? h : "mechanics";
  });

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

  // V6.11 — owner / GM may patch a single attribute / skill / defect's
  // level inline on the sheet (no need to re-enter the builder for a quick
  // tweak). Recomputes total CP server-side.
  const canEditMech = !!user && (user.id === ch.owner_id || campaign?.is_gm);
  const patchListItem = async (listKey, idx, patch) => {
    const list = (ch[listKey] || []).map((row, i) => i === idx ? { ...row, ...patch } : row);
    try {
      const { data } = await api.put(`/characters/${ch.id}`, { ...ch, [listKey]: list });
      setCh(data);
    } catch (e) {
      alert(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

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

      {/* V6.14 — Character-sheet sub-tabs (DESIGN_AUDIT P1 #7).
          Identity stays visible at the top; Mechanics / Inventory / History
          switch out below. Default to Mechanics so the sheet still "opens"
          on its dice surface. Honours URL hash (#inventory, #history) so
          deep links work. */}
      <SheetTabBar value={sheetTab} onChange={setSheetTab}/>

      {/* ───────── Identity tab ───────── */}
      {sheetTab === "identity" && (
      <div className="mt-3 flex items-start justify-between flex-wrap gap-4"
           data-testid="sheet-identity-pane">
        <div className="flex items-start gap-5 flex-1 min-w-0">
          <CharacterPortrait character={ch} canEdit={canEditMech} onUploaded={load}/>
          <div className="min-w-0 flex-1">
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
          <CharacterStatusRings characterId={ch.id}/>
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
      )}

      {/* ───────── Mechanics tab ───────── */}
      {sheetTab === "mechanics" && (<>
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
                        ×{canEditMech ? (
                          <input type="number" min={1} max={20}
                                 value={a.level || 1}
                                 onChange={(e) => patchListItem("attributes", i, { level: Math.max(1, +e.target.value || 1) })}
                                 className="bg-transparent border-b border-gold/40 w-10 text-center font-display text-gold focus:outline-none focus:border-gold"
                                 data-testid={`attr-level-edit-${i}`}
                                 title="Click to set assigned Level — cost recomputes on save"/>
                        ) : a.level}
                        <span className="text-gold/60 text-[10px] font-ui">assigned</span>
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
                        ×{canEditMech ? (
                          <input type="number" min={1} max={6}
                                 value={d.rank || 1}
                                 onChange={(e) => patchListItem("defects", i, { rank: Math.max(1, +e.target.value || 1) })}
                                 className="bg-transparent border-b border-ember/40 w-10 text-center font-display text-ember focus:outline-none"
                                 data-testid={`defect-rank-edit-${i}`}
                                 title="Click to set Rank — refund recomputes on save"/>
                        ) : d.rank}
                        <span className="text-ember/60 text-[10px] font-ui">rank</span>
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
                      {s.group} <span className="text-gold" title="Group Level">×{canEditMech ? (
                        <input type="number" min={1} max={10}
                               value={s.level || 1}
                               onChange={(e) => patchListItem("skills", i, { level: Math.max(1, +e.target.value || 1) })}
                               className="bg-transparent border-b border-gold/40 w-10 text-center font-display text-gold focus:outline-none"
                               data-testid={`skill-level-edit-${i}`}
                               title="Click to set Level — cost recomputes on save"/>
                      ) : s.level}</span>
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
      </>)}

      {/* Journal — History tab content (universal across systems). */}
      {sheetTab === "history" && (
        <>
          <CharacterJournal character={ch} onUpdated={load}/>
          <SheetHistoryPanel character={ch}/>
        </>
      )}

      {/* Inventory tab content — lists items from every system's loadout
          source (BESM power packs / D&D magic items / Cypher cyphers). */}
      {sheetTab === "inventory" && (
        <SheetInventoryPanel character={ch} canEditMech={canEditMech}/>
      )}

    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// SheetTabBar — V6.14 sub-tab strip (Identity / Mechanics / Inventory / History)
// ────────────────────────────────────────────────────────────────────
function SheetTabBar({ value, onChange }) {
  const tabs = [
    { id: "identity",  label: "Identity",  hint: "Portrait, approvals, XP, companions" },
    { id: "mechanics", label: "Mechanics", hint: "Stats, attributes, skills, dice" },
    { id: "inventory", label: "Inventory", hint: "Gear, cyphers, power packs, magic items" },
    { id: "history",   label: "History",   hint: "Journal, XP log, character audit" },
  ];
  return (
    <div className="mt-4 flex gap-1 flex-wrap border-b border-gold/20 pb-1"
         data-testid="sheet-tabs">
      {tabs.map((t) => (
        <button key={t.id} onClick={() => { onChange(t.id); try { window.location.hash = t.id; } catch (_) {} }}
                className={`px-3 py-1.5 text-[11px] uppercase tracking-widest font-ui rounded-t-sm transition-colors ${value === t.id ? "bg-gold/15 text-gold-bright border-b-2 border-gold" : "text-mist hover:bg-gold/5"}`}
                title={t.hint}
                data-testid={`sheet-tab-${t.id}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// SheetInventoryPanel — gathers every inventory-adjacent bucket from the
// character's folio into a single tidy page. Read-only for now; GMs
// still edit via the builder. Designed to be tolerant of sparse data.
// ────────────────────────────────────────────────────────────────────
function SheetInventoryPanel({ character, canEditMech }) {
  const folio = character.folio || {};
  const dnd = folio.dnd_state || {};
  const cypher = folio.cypher_state || {};
  const magicItems = dnd.magic_items || [];
  const cyphers = cypher.cyphers || [];
  const dndInventory = dnd.inventory || [];
  const powerPacks = character.power_packs || [];
  const powerBundles = character.power_bundles || [];
  const empty = magicItems.length === 0 && cyphers.length === 0
    && dndInventory.length === 0 && powerPacks.length === 0 && powerBundles.length === 0;
  if (empty) {
    return (
      <div className="card-mystic p-8 mt-4 text-center" data-testid="sheet-inventory-empty">
        <div className="font-display text-lg text-parchment">The pack is empty.</div>
        <div className="text-mist italic text-sm mt-2">
          No magic items, cyphers, power packs, or loadout entries recorded yet.
          {canEditMech && " Open Edit to populate your character's kit."}
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-4 mt-4" data-testid="sheet-inventory">
      {magicItems.length > 0 && (
        <div className="card-mystic p-5" data-testid="sheet-inventory-magic-items">
          <div className="label-ref mb-2">Magic items &amp; boons</div>
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
              {magicItems.map((it, i) => (
                <tr key={i} className="border-b border-gold/5">
                  <td className="py-1.5 text-parchment">{it.name}</td>
                  <td className="py-1.5 text-mist text-xs font-ui uppercase tracking-widest">{it.slot || "—"}</td>
                  <td className="py-1.5">
                    {it.tag && <span className="tag border-gold/50 text-gold-bright text-[10px]">{it.tag}</span>}
                  </td>
                  <td className="py-1.5 pl-2 text-mist text-xs">{it.notes || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {cyphers.length > 0 && (
        <div className="card-mystic p-5" data-testid="sheet-inventory-cyphers">
          <div className="label-ref mb-2">Cyphers carried</div>
          <ul className="space-y-1">
            {cyphers.map((c, i) => (
              <li key={i} className="text-sm text-parchment font-body">· {typeof c === "string" ? c : c.name}</li>
            ))}
          </ul>
        </div>
      )}
      {dndInventory.length > 0 && (
        <div className="card-mystic p-5" data-testid="sheet-inventory-dnd">
          <div className="label-ref mb-2">Inventory</div>
          <ul className="space-y-1">
            {dndInventory.map((it, i) => (
              <li key={i} className="text-sm text-parchment font-body">· {it}</li>
            ))}
          </ul>
        </div>
      )}
      {(powerPacks.length > 0 || powerBundles.length > 0) && (
        <div className="card-mystic p-5" data-testid="sheet-inventory-packs">
          <div className="label-ref mb-2">Power packs &amp; bundles</div>
          <div className="grid sm:grid-cols-2 gap-2">
            {powerPacks.map((p, i) => (
              <div key={i} className="border border-gold/15 rounded-sm p-2">
                <div className="text-sm text-gold-bright font-ui">{p.name}</div>
                <div className="text-[10px] text-mist">Pack · {p.level ? `Lv ${p.level}` : "—"} · {p.cost_per_level ? `${p.cost_per_level} CP/lvl` : "—"}</div>
                {p.blurb && <div className="text-[11px] text-mist italic mt-1">{p.blurb}</div>}
              </div>
            ))}
            {powerBundles.map((b, i) => (
              <div key={`b${i}`} className="border border-arcane/30 rounded-sm p-2">
                <div className="text-sm text-arcane-light font-ui">{b.name}</div>
                <div className="text-[10px] text-mist">Bundle · {b.total_cost != null ? `${b.total_cost} CP` : "—"}</div>
                {b.blurb && <div className="text-[11px] text-mist italic mt-1">{b.blurb}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// SheetHistoryPanel — XP ledger from ch.xp_total / ch.xp_unspent +
// folio.xp_log if present. Read-only summary with timestamps.
// ────────────────────────────────────────────────────────────────────
function SheetHistoryPanel({ character }) {
  const folio = character.folio || {};
  const xpLog = folio.xp_log || [];
  return (
    <div className="space-y-4 mt-4" data-testid="sheet-history">
      <div className="card-mystic p-5 grid sm:grid-cols-3 gap-3" data-testid="sheet-history-xp">
        <div className="border border-gold/15 rounded-sm py-3 px-2 text-center">
          <div className="label-ref">XP earned</div>
          <div className="font-display text-2xl text-gold">{Number(character.xp_total || 0).toFixed(2)}</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-3 px-2 text-center">
          <div className="label-ref">XP unspent</div>
          <div className="font-display text-2xl text-gold-bright">{Number(character.xp_unspent || 0).toFixed(2)}</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-3 px-2 text-center">
          <div className="label-ref">Points spent</div>
          <div className="font-display text-2xl text-parchment">{character.spent?.total_spent ?? 0}<span className="text-mist text-sm"> / {character.total_points}</span></div>
        </div>
      </div>
      {xpLog.length > 0 && (
        <div className="card-mystic p-5" data-testid="sheet-history-xp-log">
          <div className="label-ref mb-2">XP log</div>
          <ul className="space-y-2">
            {[...xpLog].reverse().slice(0, 30).map((entry, i) => (
              <li key={i} className="text-sm border-l-2 border-gold/20 pl-3">
                <div className="text-[10px] text-mist uppercase tracking-widest">
                  {entry.created_at ? new Date(entry.created_at).toLocaleString() : ""}
                  {entry.amount != null && <span className="text-gold-bright ml-2">{entry.amount > 0 ? "+" : ""}{entry.amount} XP</span>}
                </div>
                <div className="text-parchment font-body">{entry.reason || entry.note || "(no reason given)"}</div>
                {entry.approved_by && <div className="text-[10px] text-mist italic">Approved by {entry.approved_by}</div>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
