import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import * as Tabs from "@radix-ui/react-tabs";
import { Users, Plus, UserPlus2, ArrowRight, Trash2, Sparkles, Eye, EyeOff, Link as LinkIcon, Wand2, Shield, Copy, RefreshCw, Check, Save, Network, ListTree, Lightbulb, X, BookOpen, ChevronDown, ChevronRight, ScrollText, Upload, Globe, Lock, DollarSign } from "lucide-react";
import KnowledgeGraph from "./KnowledgeGraph";
import CodexChartView from "./CodexChartView";
import KnowledgeTab from "./campaignDetail/KnowledgeTab";
import PrimerTab from "./campaignDetail/PrimerTab";
import ChannelsPanel from "./ChannelsPanel";
import AtelierTab from "./AtelierTab";
import SystemBadge from "./SystemBadge";
import CardDeckPanel from "./CardDeckPanel";
import XPLedgerPanel from "./XPLedgerPanel";
import DeltaDropPanel from "./DeltaDropPanel";
import { SeatApplicationsPanel, ConsentRollPanel } from "./ConsentPanel";
import { useAuth } from "../lib/api";
import { NODE_TYPES, NODE_TEMPLATES, colorForType, labelForType } from "../lib/nodeTemplates";

export default function CampaignDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [camp, setCamp] = useState(null);
  const [characters, setCharacters] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [customs, setCustoms] = useState([]);
  const [edges, setEdges] = useState([]);
  const [err, setErr] = useState("");
  const [showStart, setShowStart] = useState(false);
  const [showLedger, setShowLedger] = useState(false);
  const nav = useNavigate();

  const load = async () => {
    try {
      const c = await api.get(`/campaigns/${id}`).then((r) => r.data);
      setCamp(c);
      const [ch, nd, se, cu, ed] = await Promise.all([
        api.get(`/campaigns/${id}/characters`).then(r => r.data),
        api.get(`/campaigns/${id}/nodes`).then(r => r.data),
        api.get(`/campaigns/${id}/sessions`).then(r => r.data),
        c.is_gm ? api.get(`/campaigns/${id}/custom`).then(r => r.data) : [],
        api.get(`/campaigns/${id}/edges`).then(r => r.data).catch(() => []),
      ]);
      setCharacters(ch); setNodes(nd); setSessions(se); setCustoms(cu); setEdges(ed);
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };
  useEffect(() => { load(); }, [id]);

  if (err) return <div className="p-10 text-ember">{err}</div>;
  if (!camp) return <div className="p-10 text-mist">Summoning…</div>;

  const join = async () => { await api.post(`/campaigns/${id}/join`, { message: "" }); load(); };
  const leave = async () => { await api.post(`/campaigns/${id}/leave`); load(); };
  const delCamp = async () => {
    if (!window.confirm("Dissolve this campaign? All threads will be lost.")) return;
    await api.delete(`/campaigns/${id}`); nav("/app/campaigns");
  };
  const startSession = async (title) => {
    if (!title || !title.trim()) return;
    const { data } = await api.post("/sessions", { campaign_id: id, title: title.trim() });
    setShowStart(false);
    nav(`/app/sessions/${data.id}`);
  };

  return (
    <div className="px-8 md:px-12 py-10" data-system={camp.system_id || "besm-4e"}
         data-testid="campaign-root">
      <Link to="/app/campaigns" className="text-xs font-ui uppercase tracking-widest text-gold/70 hover:text-gold-bright"
            data-testid="back-to-campaigns">← Campaigns</Link>
      <div className="mt-4 flex items-start justify-between flex-wrap gap-4">
        <div className="max-w-2xl">
          <div className="label-ref">{camp.system} · {camp.power_level}</div>
          {/* V6.25.6 mobile sweep — title scales down + truncates on
              mobile so the header doesn't dominate a phone screen. */}
          <h1 className="font-display text-2xl sm:text-4xl tracking-wide text-parchment mt-1 leading-tight">{camp.name}</h1>
          <CampaignDescription camp={camp} isGm={!!camp.is_gm} onSaved={load}/>
          <div className="flex flex-wrap gap-1 mt-3">
            {(camp.tags || []).map((t, i) => <span key={i} className="tag">{t}</span>)}
          </div>
          <div className="mt-4 text-[11px] sm:text-xs font-ui uppercase tracking-widest text-gold/60">
            GM: {camp.gm_name} · {(camp.member_ids || []).length}/{camp.max_players} seated · {camp.schedule || "no schedule"}
          </div>
          <SystemBadge systemId={camp.system_id} systemName={camp.system}/>
        </div>
        <div className="flex gap-2">
          {(user?.role === "gm" || user?.role === "admin") && (
            <button onClick={async () => {
              if (!window.confirm(`Clone "${camp.name}" into a new campaign you GM?`)) return;
              try {
                const { data } = await api.post(`/campaigns/${id}/clone`);
                window.location.href = `/app/campaigns/${data.campaign.id}`;
              } catch (e) { alert(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
            }} className="btn btn-ghost" data-testid="clone-campaign-btn"
                title="Fork this campaign into a copy you GM (carries World Codex, Genesis, edges, custom rules, and published characters).">
              <Copy className="w-4 h-4"/> Clone
            </button>
          )}
          {camp.is_gm && <Link to={`/app/campaigns/${id}/director`} className="btn" data-testid="director-btn"
                              title="GM Director's Console — pull NPCs from your Atelier into encounters, judge Challenge Rating, get tactical suggestions.">
            <Wand2 className="w-4 h-4"/> Director
          </Link>}
          {camp.is_gm && <button onClick={() => setShowLedger(true)} className="btn" data-testid="xp-ledger-btn"
                                 title="Campaign-level XP ledger — every award + conversion across all characters.">
            <ScrollText className="w-4 h-4"/> XP Ledger
          </button>}
          {camp.is_gm && <button onClick={() => setShowStart(true)} className="btn btn-primary" data-testid="start-session-btn">
            <Sparkles className="w-4 h-4"/> Start session
          </button>}
          {!camp.is_gm && !(camp.member_ids || []).includes(camp.current_user_id) && (
            <button onClick={join} className="btn btn-primary" data-testid="join-btn"><UserPlus2 className="w-4 h-4"/> Take a seat</button>
          )}
          {!camp.is_gm && <button onClick={leave} className="btn btn-ghost" data-testid="leave-btn">Leave</button>}
          {camp.is_gm && <button onClick={delCamp} className="btn btn-danger" data-testid="delete-campaign-btn"><Trash2 className="w-4 h-4"/></button>}
        </div>
      </div>

      <div className="divider-sigil my-8" />

      <Tabs.Root defaultValue="characters">
        {/* V6.25.6 mobile sweep — Tabs row scrolls horizontally on
            mobile (no wrap) and sticks to the top under 480px so the
            user can switch tabs without scrolling back up. */}
        <Tabs.List className="flex gap-2 border-b border-gold/10 pb-3 flex-nowrap overflow-x-auto sm:flex-wrap
                              sticky top-0 z-30 bg-void/95 backdrop-blur-sm
                              -mx-3 px-3 sm:static sm:mx-0 sm:px-0 sm:bg-transparent sm:backdrop-blur-none"
                    style={{ scrollbarWidth: "thin" }}>
          {[
            ["characters", "Characters"],
            ["channels", "Channels"],
            ["knowledge", "Knowledge Web"],
            ["sessions", "Sessions"],
            ["decks", "Decks"],
            ["primer", "Player Primer"],
            ...(camp.is_gm ? [["atelier", "Atelier"], ["delta", "Delta Drop"], ["custom", "Custom Rules"], ["invite", "Invite & Share"]] : []),
          ].map(([v, l]) => (
            <Tabs.Trigger key={v} value={v}
              className="px-3 sm:px-4 py-2 text-xs font-ui tracking-widest uppercase text-mist hover:text-parchment
                         flex-shrink-0 whitespace-nowrap
                         data-[state=active]:text-gold-bright data-[state=active]:border-b data-[state=active]:border-gold"
              data-testid={`tab-${v}`}>
              {l}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <Tabs.Content value="characters" className="pt-6">
          <CharactersTab camp={camp} characters={characters} onRefresh={load} />
        </Tabs.Content>
        <Tabs.Content value="channels" className="pt-6">
          <ChannelsPanel campaign={camp} user={user}/>
        </Tabs.Content>
        <Tabs.Content value="knowledge" className="pt-6">
          <KnowledgeTab camp={camp} nodes={nodes} edges={edges} onRefresh={load} />
        </Tabs.Content>
        <Tabs.Content value="sessions" className="pt-6">
          <SessionsTab camp={camp} sessions={sessions} nodes={nodes}
                       onStart={() => setShowStart(true)} onRefresh={load}/>
        </Tabs.Content>
        <Tabs.Content value="decks" className="pt-6">
          <CardDeckPanel campaignId={id} systemId={camp.system_id}
                         sessionId={null} isGm={!!camp.is_gm}/>
        </Tabs.Content>
        <Tabs.Content value="primer" className="pt-6">
          <PrimerTab camp={camp} onRefresh={load} />
        </Tabs.Content>
        {camp.is_gm && (
          <Tabs.Content value="atelier" className="pt-6">
            <AtelierTab campId={id} camp={camp} />
          </Tabs.Content>
        )}
        {camp.is_gm && (
          <Tabs.Content value="delta" className="pt-6">
            <DeltaDropPanel campaign={camp} onApplied={load}/>
          </Tabs.Content>
        )}
        {camp.is_gm && (
          <Tabs.Content value="custom" className="pt-6">
            <CustomTab campId={id} customs={customs} onRefresh={load} systemId={camp.system_id}/>
          </Tabs.Content>
        )}
        {camp.is_gm && (
          <Tabs.Content value="invite" className="pt-6">
            <InviteTab camp={camp} onRefresh={load} />
          </Tabs.Content>
        )}
      </Tabs.Root>

      {/* System credit footer — reflects whatever publisher matches camp.system_id.
          Tri-Stat Emporium voice on BESM, generic publisher © on others. */}
      <SystemCredit camp={camp}/>

      {/* Start Session modal */}
      {showStart && camp.is_gm && (
        <StartSessionModal
          defaultTitle={`Session ${sessions.length + 1}`}
          campName={camp.name}
          onClose={() => setShowStart(false)}
          onStart={startSession}
        />
      )}

      {/* Campaign-level XP ledger */}
      {showLedger && camp.is_gm && (
        <XPLedgerPanel campaignId={id} onClose={() => setShowLedger(false)}/>
      )}
    </div>
  );
}

function SystemCredit({ camp }) {
  const [sys, setSys] = useState(null);
  useEffect(() => {
    api.get("/systems").then((r) => {
      const all = r.data.systems || [];
      setSys(all.find((s) => s.id === (camp.system_id || "besm-4e")) || all[0]);
    }).catch(() => {});
  }, [camp.system_id]);
  if (!sys) return null;
  const isBesm = sys.id === "besm-4e";
  const year = new Date().getFullYear();
  const copyright = (sys.copyright || "").replaceAll("{YEAR}", year);
  const headline = isBesm ? "Tri-Stat Emporium" : sys.publisher;
  return (
    <div className="mt-10 pt-6 border-t border-gold/10" data-testid="tri-stat-credit">
      <div className="flex flex-col items-center gap-3">
        {sys.logo_url && (
          <img src={sys.logo_url} alt={`${sys.name} logo`}
               data-testid="system-logo"
               className="h-20 md:h-24 w-auto object-contain opacity-95 drop-shadow-lg"
               // The Emporium guidelines REQUIRE that the logo's aspect ratio is
               // preserved and the logo is not otherwise altered.
               style={{ imageRendering: "auto" }} />
        )}
        <div className="font-display tracking-[0.3em] text-gold/70 text-xs uppercase">
          {headline}
        </div>
        <div className="text-[10.5px] text-mist/80 font-ui max-w-2xl text-center leading-relaxed">
          {copyright}
        </div>
        {sys.links && sys.links.length > 0 && (
          <div className="flex gap-3 text-[10px] font-ui uppercase tracking-widest text-gold/60">
            {sys.links.map((href) => (
              <a key={href} href={href} target="_blank" rel="noreferrer" className="hover:text-gold-bright">
                {href.replace(/^https?:\/\//, "")}
              </a>
            ))}
          </div>
        )}
        {!sys.supported && (
          <div className="text-[10px] text-gold/60 italic">
            Mechanics for {sys.name} are scaffolded — reference content coming soon.
          </div>
        )}
        <div className="text-[10px] text-mist/60 italic mt-1">
          Table-Gnostic references rules and page numbers — it does not reproduce
          rulebook prose, lore, or examples. Bring your physical book to the table.
        </div>
      </div>
    </div>
  );
}

function StartSessionModal({ defaultTitle, campName, onClose, onStart }) {
  const [title, setTitle] = useState(defaultTitle);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const submit = async (e) => {
    e.preventDefault();
    if (!title.trim() || busy) return;
    setBusy(true);
    try { await onStart(title); } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-50 bg-void/80 backdrop-blur-sm flex items-start justify-center p-6 overflow-auto"
         data-testid="start-session-modal" role="dialog" aria-modal="true">
      <div className="card-mystic sigil-ring w-full max-w-md p-7 my-20">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="label-ref flex items-center gap-2"><Sparkles className="w-3 h-3"/> Light the hearth</div>
            <h2 className="font-display text-2xl text-parchment tracking-wide mt-1">Start a session</h2>
            <div className="text-[11px] font-ui uppercase tracking-widest text-mist/70 mt-1">{campName}</div>
          </div>
          <button onClick={onClose} className="btn btn-ghost p-2"><X className="w-4 h-4"/></button>
        </div>
        <div className="divider-sigil mb-4"/>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label-ref block mb-1">Session title</label>
            <input className="input" value={title} required autoFocus
                   onChange={(e) => setTitle(e.target.value)}
                   data-testid="start-session-title" placeholder="The Spire's First Bell" />
            <div className="text-[10px] text-mist italic mt-1">
              Players who have taken a seat will be able to join when you open the room.
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button type="submit" disabled={busy} className="btn btn-primary" data-testid="start-session-confirm">
              <Sparkles className="w-4 h-4"/> {busy ? "Lighting…" : "Begin"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CharactersTab({ camp, characters, onRefresh }) {
  const [seeding, setSeeding] = useState(false);
  const [seedErr, setSeedErr] = useState("");
  const isBesm = (camp.system_id || "besm-4e") === "besm-4e";
  const seed = async () => {
    if (!window.confirm("Seed three Adventurous-tier sample PCs from the Evereantha setting?\n\n• Cyma Glasswort — Apocophea (Herbalist)\n• Tarsis Hammergrip — Ferralith (Monk-Smith)\n• Vela Stoneglyph — Lithomorph (Geomantic Sculptor)\n\nThey'll be added as published characters in this campaign.")) return;
    setSeedErr(""); setSeeding(true);
    try {
      await api.post(`/campaigns/${camp.id}/seed/evereantha`);
      onRefresh();
    } catch (e) {
      setSeedErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setSeeding(false); }
  };
  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 className="h-arcane text-sm">Player Characters</h3>
        <div className="flex items-center gap-2">
          {camp.is_gm && isBesm && (
            <button onClick={seed} disabled={seeding} className="btn btn-ghost text-xs"
                    data-testid="seed-evereantha-btn"
                    title="Seed three Adventurous-tier sample PCs from the public Evereantha setting (BESM 4E mechanics).">
              <Sparkles className="w-3 h-3"/> {seeding ? "Seeding…" : "Seed Evereantha samples"}
            </button>
          )}
          <Link to={`/app/campaigns/${camp.id}/characters/new`} className="btn btn-primary text-xs"
                data-testid="new-character-btn">
            <Plus className="w-3 h-3"/> Forge character
          </Link>
        </div>
      </div>
      {seedErr && <div className="text-ember text-[11px] mb-2 font-ui">{seedErr}</div>}
      {characters.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No souls at this table yet.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {characters.map((c) => (
            <Link key={c.id} to={`/app/characters/${c.id}`} className="card-mystic p-5" data-testid={`character-${c.id}`}>
              <CharacterCardPreview c={c} systemId={camp.system_id || "besm-4e"}/>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

/** System-aware character card preview — replaces the BESM-shape Body/Mind/Soul
 *  strip with the right vital block for each system: D&D shows class+level,
 *  AC, HP. Cypher shows tier, type, pools. Anime 5E hybrid shows class +
 *  Tri-Stat point spend. BESM 4E unchanged. */
function CharacterCardPreview({ c, systemId }) {
  const dnd = c.folio?.dnd_state;
  const cyph = c.folio?.cypher_state;
  const anime = c.folio?.anime5e_state;
  // D&D 5E (or Anime-5E hybrid which also stores dnd_state)
  if (dnd) {
    const isAnime = systemId === "anime-5e" || !!anime;
    const sc = dnd.ability_scores || {};
    const mod = (s) => Math.floor(((sc[s] | 0) - 10) / 2);
    const lvl = Math.max(1, +(dnd.level || 1));
    const pb = Math.max(2, 2 + Math.floor((lvl - 1) / 4));
    const conMod = mod("Constitution");
    const dexMod = mod("Dexterity");
    const hd = ({ Barbarian: 12, Fighter: 10, Paladin: 10, Ranger: 10,
                  Bard: 8, Cleric: 8, Druid: 8, Monk: 8, Rogue: 8, Warlock: 8,
                  Sorcerer: 6, Wizard: 6 })[dnd.class] || 8;
    const hpMax = dnd.hp_max ?? Math.max(1, hd + conMod + ((hd / 2 + 1) + conMod) * (lvl - 1));
    const ac = 10 + dexMod;
    return (
      <>
        <div className="label-ref" data-testid={`card-system-${c.id}`}>
          {isAnime ? "Anime 5E" : "D&D 5E"} · {dnd.class || "Class"} {lvl} · {dnd.race || "Race"}
        </div>
        <div className="font-display text-lg text-parchment mt-1">{c.name}</div>
        <div className="text-xs text-mist mt-1 italic line-clamp-2">{c.concept || dnd.background || "—"}</div>
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <CardVital label="AC" v={ac}/>
          <CardVital label="HP" v={hpMax}/>
          <CardVital label="Prof" v={`+${pb}`}/>
        </div>
        <div className="mt-3 text-[10px] font-ui tracking-widest uppercase text-mist">
          by {c.owner_name}
          {isAnime && anime?.point_buys?.length ? (
            <span className="ml-1 text-pink-300">· tri-stat ×{anime.point_buys.length}</span>
          ) : null}
        </div>
      </>
    );
  }
  // Cypher
  if (cyph) {
    return (
      <>
        <div className="label-ref" data-testid={`card-system-${c.id}`}>
          Cypher · Tier {cyph.tier || 1} · {cyph.descriptor || "?"} {cyph.type || "?"}
        </div>
        <div className="font-display text-lg text-parchment mt-1">{c.name}</div>
        <div className="text-xs text-mist mt-1 italic line-clamp-2">{cyph.focus ? `who ${(cyph.focus || "").toLowerCase()}` : (c.concept || "—")}</div>
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <CardVital label="Might"     v={cyph.pools?.Might ?? 0}/>
          <CardVital label="Speed"     v={cyph.pools?.Speed ?? 0}/>
          <CardVital label="Intellect" v={cyph.pools?.Intellect ?? 0}/>
        </div>
        <div className="mt-3 text-[10px] font-ui tracking-widest uppercase text-mist">
          by {c.owner_name} · Armor {cyph.armor || 0} · Cypher×{cyph.cypher_limit || cyph.starting_cypher_limit || 2}
        </div>
      </>
    );
  }
  // Default — BESM 4E (Tri-Stat).
  return (
    <>
      <div className="label-ref">{c.power_level} · {c.total_points} pts</div>
      <div className="font-display text-lg text-parchment mt-1">{c.name}</div>
      <div className="text-xs text-mist mt-1 italic line-clamp-2">{c.concept || "—"}</div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        {["body", "mind", "soul"].map((s) => (
          <CardVital key={s} label={s} v={c.stats?.[s]}/>
        ))}
      </div>
      <div className="mt-3 text-[10px] font-ui tracking-widest uppercase text-mist">
        by {c.owner_name} · HP {c.derived?.health_points ?? "?"} · EP {c.derived?.energy_points ?? "?"}
      </div>
    </>
  );
}

function CardVital({ label, v }) {
  return (
    <div className="border border-gold/15 rounded-sm py-1">
      <div className="label-ref">{label}</div>
      <div className="font-display text-lg text-gold">{v}</div>
    </div>
  );
}

function labelForSystemShort(sysId) {
  return ({
    "dnd-5e":   "D&D 5E",
    "cypher":   "Cypher",
    "besm-4e":  "BESM 4E",
    "anime-5e": "Anime 5E",
  })[sysId] || sysId || "BESM 4E";
}

function SessionsTab({ camp, sessions, nodes, onStart, onRefresh }) {
  const journalNodes = nodes.filter((n) => n.type === "player_journal");
  const recordNodes = nodes.filter((n) => n.type === "session_record");
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="min-w-0">
          <h3 className="h-arcane text-sm">Sessions</h3>
          <div className="text-[11px] text-mist font-body italic mt-1">
            Live tables · player journals · GM recaps · finalize the chronicle when the dust settles.
          </div>
        </div>
        {camp.is_gm && <button onClick={onStart} className="btn btn-primary text-xs" data-testid="new-session-btn">
          <Plus className="w-3 h-3"/> Start session
        </button>}
      </div>
      <div className="divider-sigil my-3"/>

      {sessions.length === 0 && journalNodes.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No sessions have been run.</div>
      ) : (
        <div className="space-y-4">
          {sessions.map((s) => (
            <SessionRow key={s.id} session={s} camp={camp}
                        recordNodes={recordNodes.filter((r) => r.fields?.session_id === s.id)}
                        journalNodes={journalNodes.filter((j) => j.fields?.session_id === s.id)}
                        onRefresh={onRefresh}/>
          ))}
          {/* Orphan player journals — entered without an active session id. */}
          {(() => {
            const orphans = journalNodes.filter((j) => !sessions.find((s) => s.id === j.fields?.session_id));
            if (!orphans.length || !camp.is_gm) return null;
            return (
              <div className="card-mystic p-4 border-arcane/30" data-testid="session-orphan-journals">
                <div className="label-ref">Orphaned player journals</div>
                <div className="text-[11px] text-mist mt-1 font-body italic">
                  Entries written without an open session. The GM can review and re-link them.
                </div>
                <div className="mt-3 space-y-2">
                  {orphans.map((j) => (
                    <JournalRow key={j.id} j={j} onRefresh={onRefresh}/>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}


function SessionRow({ session, camp, recordNodes, journalNodes, onRefresh }) {
  const [open, setOpen] = useState(false);
  const [tone, setTone] = useState("lyrical");
  const [busy, setBusy] = useState(false);
  // The newest recap node for the session; finalisation rewrites it in place.
  const recap = (recordNodes || []).slice().sort((a, b) =>
    (b.created_at || "").localeCompare(a.created_at || ""))[0];
  const finalized = !!(recap?.fields?.is_finalized);

  const finalize = async () => {
    if (!recap) {
      alert("Generate a recap inside the live SessionView first — that's the spine the chronicle is woven onto.");
      return;
    }
    if (!journalNodes.length) {
      if (!window.confirm("No player journals are linked to this session. Weave the chronicle from the recap alone?")) return;
    }
    setBusy(true);
    try {
      await api.post(`/sessions/${session.id}/finalize`, {
        recap_node_id: recap.id,
        journal_node_ids: journalNodes.map((j) => j.id),
        tone,
      });
      onRefresh();
    } catch (e) {
      alert(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="card-mystic p-4" data-testid={`sessionrow-${session.id}`}>
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <Link to={`/app/sessions/${session.id}`} className="min-w-0">
          <div className="font-display text-lg text-parchment hover:text-gold-bright transition">
            {session.title}
          </div>
          <div className="text-[10px] text-mist font-ui uppercase tracking-widest mt-1">
            Round {session.round || 0} · {session.status}
            {finalized && <span className="ml-2 text-gold-bright">· chronicle finalised</span>}
          </div>
        </Link>
        <div className="flex items-center gap-2">
          <span className="tag uppercase border-arcane/40 text-arcane-light">
            {journalNodes.length} journal{journalNodes.length === 1 ? "" : "s"}
          </span>
          <span className={`tag uppercase ${recap ? "border-gold/60 text-gold-bright" : "border-mist/30 text-mist/60"}`}>
            {recap ? "recap ready" : "no recap"}
          </span>
          <button onClick={() => setOpen(!open)} className="btn btn-ghost text-xs"
                  data-testid={`sessionrow-toggle-${session.id}`}>
            {open ? <ChevronDown className="w-3 h-3"/> : <ChevronRight className="w-3 h-3"/>}
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-3 pt-3 border-t border-gold/10 space-y-3">
          {recap ? (
            <div data-testid={`sessionrow-recap-${session.id}`}>
              <div className="label-ref text-[10px] mb-1">
                {finalized ? "Finalised chronicle" : "GM recap (the spine)"}
              </div>
              <div className="text-sm text-parchment/95 whitespace-pre-wrap font-body leading-relaxed">
                {recap.content}
              </div>
            </div>
          ) : (
            <div className="text-[12px] text-mist italic font-body">
              No recap node yet — open the live SessionView and click "Generate Recap" to add one.
            </div>
          )}

          {journalNodes.length > 0 && (
            <div data-testid={`sessionrow-journals-${session.id}`}>
              <div className="label-ref text-[10px] mb-1">Player journals (colour + voice)</div>
              <div className="space-y-2">
                {journalNodes.map((j) => <JournalRow key={j.id} j={j} onRefresh={onRefresh}/>)}
              </div>
            </div>
          )}

          {camp.is_gm && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gold/10"
                 data-testid={`sessionrow-finalize-${session.id}`}>
              <div className="label-ref text-[10px]">Tone</div>
              <select className="select w-auto text-xs" value={tone}
                      onChange={(e) => setTone(e.target.value)}>
                <option value="lyrical">Lyrical (default)</option>
                <option value="terse">Terse / journal style</option>
                <option value="in-character">In-character campfire</option>
              </select>
              <button onClick={finalize} disabled={busy || !recap}
                      className="btn btn-primary text-xs"
                      data-testid={`sessionrow-finalize-btn-${session.id}`}
                      title="Weave recap + linked journals into the definitive chronicle.">
                <ScrollText className="w-3 h-3"/>
                {busy ? "Weaving…" : finalized ? "Re-weave chronicle" : "Finalize chronicle"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function JournalRow({ j, onRefresh }) {
  const [open, setOpen] = useState(false);
  const cname = j.fields?.character_name || "?";
  const when = (j.created_at || "").replace("T", " ").slice(0, 16);
  return (
    <div className="border border-arcane/25 bg-arcane/5 rounded-sm p-2"
         data-testid={`journal-${j.id}`}>
      <button type="button" onClick={() => setOpen(!open)}
              className="w-full text-left flex items-center justify-between gap-2">
        <div className="min-w-0 truncate">
          <span className="text-arcane-light font-ui text-[11px] uppercase tracking-widest mr-2">
            {cname}
          </span>
          <span className="text-mist/70 text-xs">{when}</span>
        </div>
        {open ? <ChevronDown className="w-3 h-3 text-arcane-light"/> : <ChevronRight className="w-3 h-3 text-arcane-light"/>}
      </button>
      {open && (
        <div className="mt-2 pt-2 border-t border-arcane/15 text-sm text-parchment/95 whitespace-pre-wrap font-body leading-relaxed">
          {j.content}
        </div>
      )}
    </div>
  );
}

function CustomTab({ campId, customs, onRefresh, systemId }) {
  // System-aware kind options + cost label.
  // BESM 4E uses Attribute/Defect/Skill.
  // D&D 5E surfaces Class Feature / Race Trait / Background Feat / House Rule.
  // Cypher uses Descriptor / Focus / Ability / Cypher / Artifact / House Rule.
  // Anime 5E hybrid offers both Tri-Stat and 5E shapes.
  const KIND_OPTIONS = (() => {
    // V6.25 — Universal homebrew baseline: Race / Class / Size / Stat
    // are structural kinds every system can extend (BESM Extras style).
    const HOMEBREW_BASE = [
      { value: "race",  label: "Homebrew Race" },
      { value: "class", label: "Homebrew Class" },
      { value: "size",  label: "Homebrew Size" },
      { value: "stat",  label: "Homebrew Stat" },
    ];
    if (systemId === "dnd-5e") {
      return [
        { value: "feature",   label: "Class feature" },
        { value: "trait",     label: "Race trait" },
        { value: "feat",      label: "Feat" },
        { value: "house",     label: "House rule" },
        ...HOMEBREW_BASE,
      ];
    }
    if (systemId === "cypher") {
      return [
        { value: "descriptor", label: "Descriptor" },
        { value: "focus",      label: "Focus" },
        { value: "ability",    label: "Type/Ability" },
        { value: "cypher",     label: "Cypher (one-shot)" },
        { value: "artifact",   label: "Artifact" },
        { value: "house",      label: "House rule" },
        ...HOMEBREW_BASE,
      ];
    }
    if (systemId === "anime-5e") {
      return [
        { value: "attribute", label: "Tri-Stat Attribute" },
        { value: "defect",    label: "Tri-Stat Defect" },
        { value: "skill",     label: "Skill" },
        { value: "feature",   label: "Class feature" },
        { value: "feat",      label: "Feat" },
        { value: "house",     label: "House rule" },
        ...HOMEBREW_BASE,
      ];
    }
    // BESM 4E default
    return [
      { value: "attribute", label: "Attribute" },
      { value: "defect",    label: "Defect" },
      { value: "skill",     label: "Skill" },
      ...HOMEBREW_BASE,
    ];
  })();
  const isBesmShape = !systemId || systemId === "besm-4e";
  const costLabel = isBesmShape ? "Cost per level" : (
    systemId === "cypher" ? "Tier requirement" :
    systemId === "dnd-5e" ? "Level requirement" : "Cost / Level"
  );
  const categoryHint = isBesmShape
    ? "Greater / Lesser / Serious"
    : (systemId === "cypher" ? "Genre tag (fantasy / scifi / horror / any)"
       : systemId === "dnd-5e" ? "Class tier (mundane / martial / casted)"
       : "Power band");

  const [form, setForm] = useState({
    kind: KIND_OPTIONS[0].value, name: "", cost_per_level: 1, category: "",
    page_ref: "Custom", description_note: "", effects: {}, color: "",
  });
  // V6.25.2 — when authoring BESM Race/Class templates, expand a
  // dedicated composer (stat adjustments + attributes + defects +
  // skills + enhancements/limiters) that mirrors the BESM Extras
  // template shape in the book. Non-BESM systems get the simpler flat
  // form; their `effects` stays empty and narrative-only.
  const isBesmSystem = !systemId || systemId === "besm-4e" || systemId === "anime-5e";
  const isBesmTemplate = isBesmSystem && (form.kind === "race" || form.kind === "class");
  const save = async (e) => {
    e.preventDefault();
    await api.post(`/campaigns/${campId}/custom`, {
      ...form,
      campaign_id: campId,
      cost_per_level: +form.cost_per_level,
      effects: form.effects || {},
      color: form.color || "",
    });
    setForm({ kind: KIND_OPTIONS[0].value, name: "", cost_per_level: 1,
              category: "", page_ref: "Custom", description_note: "",
              effects: {}, color: "" });
    onRefresh();
  };
  const del = async (cid) => { await api.delete(`/campaigns/${campId}/custom/${cid}`); onRefresh(); };

  return (
    <div>
      <div className="label-ref mb-3">Custom rules (GM-authored)</div>
      <p className="text-xs text-mist mb-4 font-body">
        Create your own homebrew entries for this campaign. Field shapes adapt to your campaign's system —
        currently <b>{labelForSystemShort(systemId)}</b>. Players can select them in the character forge.
        Your prose stays in your campaign — it is never reproduced elsewhere.
      </p>

      <form onSubmit={save} className="card-mystic p-5 mb-6 grid md:grid-cols-2 gap-3" data-testid="custom-form">
        <select className="select" value={form.kind} data-testid="rule-kind"
                onChange={(e) => setForm({ ...form, kind: e.target.value })}>
          {KIND_OPTIONS.map((k) => <option key={k.value} value={k.value}>{k.label}</option>)}
        </select>
        <input className="input" placeholder="Name" value={form.name} required data-testid="rule-name"
               onChange={(e) => setForm({ ...form, name: e.target.value })}/>
        <input className="input" type={isBesmShape ? "number" : "text"} step="0.5"
               placeholder={costLabel} data-testid="rule-cost"
               value={form.cost_per_level}
               onChange={(e) => setForm({ ...form, cost_per_level: e.target.value })}/>
        <input className="input" placeholder={categoryHint} data-testid="rule-category"
               value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}/>
        <input className="input md:col-span-2" placeholder="Page reference (e.g. Custom · Homebrew 1.2)"
               value={form.page_ref} data-testid="rule-pageref"
               onChange={(e) => setForm({ ...form, page_ref: e.target.value })}/>
        {/* V6.25.7 — Color tag. Surfaces in the picker dropdowns so
            homebrew vs canonical is glanceable. */}
        <div className="md:col-span-2 flex items-center gap-2 flex-wrap">
          <label className="label-ref">Color tag</label>
          <input type="color" className="w-8 h-8 rounded-sm border border-gold/20 bg-transparent cursor-pointer"
                 value={form.color || "#c8a34a"}
                 onChange={(e) => setForm({ ...form, color: e.target.value })}
                 data-testid="rule-color"
                 title="Color shown next to this entry in player pickers"/>
          {form.color && (
            <button type="button" onClick={() => setForm({ ...form, color: "" })}
                    className="btn btn-ghost text-xs"
                    data-testid="rule-color-clear"
                    title="Use the default color">
              Clear
            </button>
          )}
          <span className="text-[10px] text-mist italic">
            Tip: pick a hue your table uses for this campaign's homebrew
            so players spot it in dropdowns at a glance.
          </span>
        </div>
        <textarea className="input md:col-span-2" placeholder="Your description / mechanics notes"
                  value={form.description_note} data-testid="rule-description"
                  onChange={(e) => setForm({ ...form, description_note: e.target.value })}/>
        {isBesmTemplate && (
          <div className="md:col-span-2">
            <BesmTemplateComposer effects={form.effects || {}}
                                    onChange={(eff) => setForm({ ...form, effects: eff })}/>
          </div>
        )}
        <div className="md:col-span-2 flex justify-end">
          <button className="btn btn-primary" type="submit" data-testid="rule-submit">Save</button>
        </div>
      </form>

      {customs.length === 0 ? (
        <div className="text-mist italic font-body text-sm">No custom rules yet.</div>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {customs.map((c) => (
            <div key={c.id} className="card-mystic p-4" data-testid={`custom-${c.id}`}
                 style={c.color ? { borderLeft: `3px solid ${c.color}` } : undefined}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  {c.color && (
                    <span className="w-2.5 h-2.5 rounded-full inline-block"
                          style={{ background: c.color }}
                          data-testid={`custom-color-${c.id}`}
                          title="GM-set color tag"/>
                  )}
                  <span className="tag">{c.kind}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <PublishToMarketplace custom={c} campaignId={campId}/>
                  <button onClick={() => del(c.id)} className="text-ember/70 hover:text-ember p-1"
                          aria-label="Delete custom rule"
                          data-testid={`custom-delete-${c.id}`}>
                    <Trash2 className="w-3 h-3"/>
                  </button>
                </div>
              </div>
              <div className="font-display text-base text-parchment mt-2">{c.name}</div>
              <div className="text-xs text-gold/70 font-ui mt-1">{c.cost_per_level} pts/level · {c.category || "—"}</div>
              <div className="text-[10px] text-mist uppercase tracking-widest mt-1">{c.page_ref}</div>
              {c.description_note && <div className="text-xs text-mist mt-2 whitespace-pre-wrap font-body">{c.description_note}</div>}
              <BesmTemplateSummary effects={c.effects || {}} kind={c.kind}/>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InviteTab({ camp, onRefresh }) {
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const inviteUrl = `${window.location.origin}/invite/${camp.invite_token}`;
  const copy = async () => {
    try { await navigator.clipboard.writeText(inviteUrl); setCopied(true); setTimeout(() => setCopied(false), 1500); }
    catch { alert("Copy failed. Long-press the link to copy manually."); }
  };
  const regen = async () => {
    if (!window.confirm("Revoke the old link and issue a new one?")) return;
    setBusy(true);
    try { await api.post(`/campaigns/${camp.id}/regenerate-invite`); onRefresh(); }
    finally { setBusy(false); }
  };

  return (
    <div className="max-w-2xl">
      <div className="label-ref">Invite & Share</div>
      <h3 className="h-arcane text-sm mt-1">A direct path to the table</h3>
      <p className="text-xs text-mist font-body mt-2 italic">
        Share this link by DM, Discord, or email. Anyone who opens it will see a summary of the campaign
        and — if signed in — can claim a seat instantly.
      </p>

      <div className="card-mystic p-5 mt-6" data-testid="invite-card">
        <div className="label-ref mb-2">Invite link</div>
        <div className="flex items-center gap-2">
          <input className="input font-mono text-[11px]" readOnly value={inviteUrl} data-testid="invite-url"/>
          <button onClick={copy} className="btn" data-testid="invite-copy-btn">
            {copied ? <Check className="w-4 h-4 text-gold-bright"/> : <Copy className="w-4 h-4"/>}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
        <div className="mt-4 flex gap-2">
          <button onClick={regen} disabled={busy} className="btn btn-danger text-xs" data-testid="invite-regen-btn">
            <RefreshCw className="w-3 h-3"/> Revoke & regenerate
          </button>
        </div>
        <div className="mt-4 text-[10px] font-ui uppercase tracking-widest text-mist/70">
          {camp.visibility === "public"
            ? "Public campaign — also discoverable in the Seekers' Hall."
            : "Private campaign — only this link grants a seat."}
        </div>
      </div>
      <CanonPublishCard camp={camp} onRefresh={onRefresh}/>
      {/* V6.21 — GM/Player consent flow: seat applications queue +
          consent-required toggle + consent roll summary. */}
      <ConsentRequiredToggle camp={camp} onRefresh={onRefresh}/>
      <SeatApplicationsPanel campaignId={camp.id} onChanged={onRefresh}/>
      <ConsentRollPanel campaignId={camp.id}/>
    </div>
  );
}

function ConsentRequiredToggle({ camp, onRefresh }) {
  const [req, setReq] = useState(!!camp.consent_required);
  const [busy, setBusy] = useState(false);
  const save = async (next) => {
    setBusy(true);
    try {
      await api.put(`/campaigns/${camp.id}`, { ...camp, consent_required: next });
      setReq(next);
      onRefresh?.();
    } finally { setBusy(false); }
  };
  return (
    <div className="card-mystic p-4 mt-4" data-testid="consent-required-toggle">
      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" checked={req} disabled={busy}
               onChange={(e) => save(e.target.checked)}
               data-testid="consent-required-checkbox"/>
        <span className="text-xs">
          <b>Require player consent</b> before character sheets become
          editable.
        </span>
      </label>
      <div className="text-[10px] text-mist/70 italic mt-1">
        When on, seated players must tick the primer / house-rules /
        safety-tags acknowledgement from their character sheet before
        they can make changes. Re-consent is required whenever the
        primer or house-rules text changes.
      </div>
    </div>
  );
}

function CanonPublishCard({ camp, onRefresh }) {
  const [pub, setPub] = useState(!!camp.canon_published);
  const [blurb, setBlurb] = useState(camp.canon_blurb || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const save = async () => {
    setBusy(true); setErr("");
    try {
      if (pub) {
        await api.post(`/campaigns/${camp.id}/canon-publish`, { blurb });
      } else {
        await api.delete(`/campaigns/${camp.id}/canon-publish`);
      }
      onRefresh && onRefresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };
  return (
    <div className="card-mystic p-5 mt-4" data-testid="canon-publish-card">
      <div className="label-ref mb-2">Publish to Canon Registry</div>
      <div className="text-[11px] text-mist/80 italic mb-3">
        Lets fellow GMs discover this campaign's Delta Drops from
        <code> /app/canon</code>. Players + seat data stay private; only the
        campaign name, system, blurb, and delta-drop count are exposed.
      </div>
      <label className="flex items-center gap-2 text-sm text-parchment cursor-pointer">
        <input type="checkbox" checked={pub}
               onChange={(e) => setPub(e.target.checked)}
               data-testid="canon-publish-checkbox"/>
        <span>Publish this campaign to the Canon Registry</span>
      </label>
      {pub && (
        <textarea
          className="input mt-3 min-h-[70px] text-sm"
          placeholder="One-sentence pitch for the registry card (max 500 chars)"
          maxLength={500}
          value={blurb}
          onChange={(e) => setBlurb(e.target.value)}
          data-testid="canon-publish-blurb"/>
      )}
      <div className="flex items-center gap-3 mt-3">
        <button onClick={save} disabled={busy} className="btn btn-primary text-xs"
                data-testid="canon-publish-save">
          {busy ? "Saving…" : pub ? "Publish" : "Unpublish"}
        </button>
        {err && <span className="text-ember text-[11px]" data-testid="canon-publish-error">{err}</span>}
      </div>
    </div>
  );
}


/** V6.25 — Campaign description card with markdown-lite rendering
 *  (paragraphs, **bold**, *italic*), a collapse toggle, and GM inline
 *  edit (works even on closed / archived campaigns — the edit surface
 *  stays live as long as the viewer is the GM). */
function renderMarkdownLite(text) {
  if (!text) return null;
  const lines = String(text).split(/\r?\n/);
  const renderInline = (s) => {
    const parts = [];
    let rest = s;
    let key = 0;
    const pat = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/;
    while (rest) {
      const m = rest.match(pat);
      if (!m) { parts.push(<span key={key++}>{rest}</span>); break; }
      const idx = m.index;
      if (idx > 0) parts.push(<span key={key++}>{rest.slice(0, idx)}</span>);
      const tok = m[0];
      if (tok.startsWith("**")) parts.push(<strong key={key++} className="text-parchment">{tok.slice(2, -2)}</strong>);
      else if (tok.startsWith("*")) parts.push(<em key={key++}>{tok.slice(1, -1)}</em>);
      else parts.push(<code key={key++} className="text-gold-bright bg-void/60 px-1 rounded-sm">{tok.slice(1, -1)}</code>);
      rest = rest.slice(idx + tok.length);
    }
    return parts;
  };
  return lines.map((ln, i) => (
    ln.trim() === ""
      ? <div key={i} className="h-2"/>
      : <p key={i} className="text-mist font-body leading-relaxed">{renderInline(ln)}</p>
  ));
}

function CampaignDescription({ camp, isGm, onSaved }) {
  const [collapsed, setCollapsed] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(camp.description || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const hasContent = !!(camp.description && camp.description.trim());

  const save = async () => {
    setBusy(true); setErr("");
    try {
      await api.put(`/campaigns/${camp.id}`, { ...camp, description: draft });
      setEditing(false);
      if (onSaved) await onSaved();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (editing) {
    return (
      <div className="mt-3 card-mystic p-3" data-testid="campaign-description-edit">
        <textarea className="input min-h-[140px] font-body leading-relaxed"
                   value={draft}
                   onChange={(e) => setDraft(e.target.value)}
                   placeholder="Campaign description. Supports **bold**, *italic*, `code`, and paragraph breaks."
                   data-testid="campaign-description-textarea"/>
        <div className="flex items-center gap-2 justify-end mt-2 flex-wrap">
          {err && <span className="text-ember text-[11px]">{err}</span>}
          <button onClick={() => { setEditing(false); setDraft(camp.description || ""); }}
                  className="btn btn-ghost text-xs" data-testid="campaign-description-cancel">
            Cancel
          </button>
          <button onClick={save} disabled={busy}
                  className="btn btn-primary text-xs" data-testid="campaign-description-save">
            <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3" data-testid="campaign-description">
      <div className="flex items-center gap-2 mb-1">
        <button onClick={() => setCollapsed((c) => !c)}
                className="text-mist/70 hover:text-gold-bright flex items-center gap-1 text-[10px] font-ui uppercase tracking-widest"
                data-testid="campaign-description-toggle"
                title={collapsed ? "Show description" : "Hide description"}>
          {collapsed
            ? <ChevronRight className="w-3 h-3"/>
            : <ChevronDown className="w-3 h-3"/>}
          {collapsed ? "Show description" : "Description"}
        </button>
        {isGm && (
          <button onClick={() => { setDraft(camp.description || ""); setEditing(true); }}
                  className="text-mist/50 hover:text-gold-bright text-[10px] font-ui uppercase tracking-widest"
                  data-testid="campaign-description-edit-btn"
                  title="Edit description (GMs can edit anytime, even after the campaign is closed)">
            ✎ Edit
          </button>
        )}
      </div>
      {!collapsed && (
        <div data-testid="campaign-description-body">
          {hasContent
            ? renderMarkdownLite(camp.description)
            : <p className="text-mist/60 font-body italic">No description yet.</p>}
        </div>
      )}
    </div>
  );
}

/* V6.25.2 — BESM Race/Class template composer.
 *
 * BESM race/class templates (per the BESM Extras pattern — see
 * Half-Dragon, Werewolf Base Form, Artificer, Martial Artist samples)
 * combine stat adjustments + attributes + skills + defects with their
 * limiters/enhancements. Total CP is computed live and deducted from
 * the player's CP budget when the template is applied to a character.
 */
function _besmCompCost(c) {
  if (c.kind === "defect") {
    const r = Math.abs(+c.rank || 0);
    const p = Math.abs(+c.points_per_rank || 1);
    return -(r * p);
  }
  if (c.kind === "attribute" || c.kind === "skill") {
    const lvl = +c.level || 0;
    const per = +c.cost_per_level || 0;
    return Math.max(0, lvl * per - (+c.refund || 0));
  }
  return 0; // enhancement/limiter are effective-level modifiers, no direct CP
}

function BesmTemplateComposer({ effects, onChange }) {
  const stats = effects.stat_adjustments || { body: 0, mind: 0, soul: 0 };
  const comps = effects.components || [];
  const setStats = (patch) => onChange({
    ...effects, stat_adjustments: { ...stats, ...patch },
  });
  const setComps = (next) => {
    const total_cp = Object.values({ body: stats.body || 0, mind: stats.mind || 0, soul: stats.soul || 0 })
      .reduce((a, b) => a + (+b || 0), 0)
      + next.reduce((sum, c) => sum + _besmCompCost(c), 0);
    onChange({ ...effects, components: next, total_cp });
  };
  const addComp = () => setComps([...comps, { kind: "attribute", name: "",
    cost_per_level: 0, level: 1, points_per_rank: 0, rank: 0, refund: 0, note: "" }]);
  const patchComp = (i, p) => setComps(comps.map((c, j) => j === i ? { ...c, ...p } : c));
  const dropComp = (i) => setComps(comps.filter((_, j) => j !== i));

  // Live total_cp recompute whenever stats change.
  React.useEffect(() => {
    const total_cp = (+stats.body || 0) + (+stats.mind || 0) + (+stats.soul || 0)
      + comps.reduce((sum, c) => sum + _besmCompCost(c), 0);
    if (total_cp !== effects.total_cp) onChange({ ...effects, total_cp });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stats.body, stats.mind, stats.soul]);

  return (
    <div className="border border-gold/20 rounded-sm p-3 bg-gold/5 space-y-3"
         data-testid="besm-template-composer">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div className="label-ref">BESM Race / Class Template</div>
        <div className="text-[10px] text-mist italic">
          Stat adjustments + attributes + skills + defects (with limiters /
          enhancements). Total CP is deducted from the player's budget on Apply.
        </div>
      </div>

      {/* Stat adjustments — Body / Mind / Soul per BESM Extras cards. */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2"
           data-testid="besm-template-stats">
        {["body", "mind", "soul"].map((s) => (
          <div key={s}>
            <label className="label-ref">{s[0].toUpperCase() + s.slice(1)} adj.</label>
            <input className="input" type="number" step="1"
                   placeholder="0"
                   value={stats[s] ?? 0}
                   onChange={(e) => setStats({ [s]: Number(e.target.value) || 0 })}
                   data-testid={`besm-template-stat-${s}`}/>
          </div>
        ))}
      </div>

      {/* Component rows — reuses the PowerBundle composer shape. */}
      <div className="space-y-2">
        {comps.length === 0 && (
          <div className="text-[11px] text-mist italic">No components yet. Click + to add an attribute / skill / defect.</div>
        )}
        {comps.map((c, i) => (
          <div key={i} className="grid grid-cols-1 sm:grid-cols-[110px_1fr_80px_80px_80px_24px] gap-2 items-center"
               data-testid={`besm-template-comp-${i}`}>
            <select className="select select-sm" value={c.kind}
                    onChange={(e) => patchComp(i, { kind: e.target.value })}>
              <option value="attribute">Attribute</option>
              <option value="skill">Skill Group</option>
              <option value="defect">Defect</option>
              <option value="enhancement">Enhancement</option>
              <option value="limiter">Limiter</option>
            </select>
            <input className="input" placeholder="Name (e.g. Weapon: Fire Breath)"
                   value={c.name}
                   onChange={(e) => patchComp(i, { name: e.target.value })}/>
            {c.kind !== "defect" ? (
              <input className="input" type="number" step="0.5" min={0}
                     placeholder="Cost/Lvl"
                     value={c.cost_per_level}
                     onChange={(e) => patchComp(i, { cost_per_level: Number(e.target.value) || 0 })}/>
            ) : (
              <input className="input" type="number" min={0}
                     placeholder="Pts/Rank"
                     value={c.points_per_rank}
                     onChange={(e) => patchComp(i, { points_per_rank: Number(e.target.value) || 0 })}/>
            )}
            <input className="input" type="number" min={0}
                   placeholder={c.kind === "defect" ? "Rank" : "Level"}
                   value={c.kind === "defect" ? c.rank : c.level}
                   onChange={(e) => patchComp(i, c.kind === "defect"
                     ? { rank: Number(e.target.value) || 0 }
                     : { level: Number(e.target.value) || 0 })}/>
            <input className="input" placeholder="Note"
                   value={c.note || ""}
                   onChange={(e) => patchComp(i, { note: e.target.value })}/>
            <button type="button" onClick={() => dropComp(i)}
                    className="text-ember/70 hover:text-ember p-1"
                    aria-label="Remove component">
              <X className="w-3 h-3"/>
            </button>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-gold/15">
        <button type="button" onClick={addComp} className="btn btn-ghost text-xs"
                data-testid="besm-template-add-comp">
          <Plus className="w-3 h-3"/> Add component
        </button>
        <div className="text-[11px] font-ui" data-testid="besm-template-total-cp">
          <span className="text-mist">Template total: </span>
          <span className={((effects.total_cp || 0) < 0) ? "text-arcane" : "text-gold-bright"}>
            {effects.total_cp || 0} CP
          </span>
        </div>
      </div>
    </div>
  );
}

function BesmTemplateSummary({ effects, kind }) {
  if (!effects || Object.keys(effects).length === 0) return null;
  if (kind !== "race" && kind !== "class") return null;
  const stats = effects.stat_adjustments || {};
  const comps = effects.components || [];
  const total = effects.total_cp;
  const statBits = ["body", "mind", "soul"]
    .filter((s) => (stats[s] ?? 0) !== 0)
    .map((s) => `${s[0].toUpperCase() + s.slice(1)} ${stats[s] > 0 ? "+" : ""}${stats[s]}`);
  return (
    <div className="mt-2 text-[11px] text-mist border-t border-gold/10 pt-2" data-testid="besm-template-summary">
      {statBits.length > 0 && (
        <div><span className="text-gold/60 uppercase tracking-widest text-[9px]">Stats</span> · {statBits.join(" / ")}</div>
      )}
      {comps.length > 0 && (
        <div className="mt-1"><span className="text-gold/60 uppercase tracking-widest text-[9px]">Components</span> · {comps.length} entr{comps.length === 1 ? "y" : "ies"}</div>
      )}
      {typeof total === "number" && (
        <div className="mt-1"><span className="text-gold/60 uppercase tracking-widest text-[9px]">Template CP</span> <span className={total < 0 ? "text-arcane" : "text-gold-bright"}>{total}</span></div>
      )}
    </div>
  );
}


/* V6.25.5 — Publish a Custom Rules entry into the cross-table
 * Marketplace. GM-only (the parent CustomTab already gates rendering
 * to GM). Three access tiers: private / public / paywall (V2). Public
 * + paywall require a one-line license attestation per the marketplace
 * v1 spec.
 */
function PublishToMarketplace({ custom, campaignId }) {
  const [open, setOpen] = useState(false);
  const [access, setAccess] = useState("public");
  const [summary, setSummary] = useState("");
  const [licenseText, setLicenseText] = useState("");
  const [attest, setAttest] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  const submit = async () => {
    setBusy(true); setErr("");
    try {
      await api.post("/marketplace/publish", {
        source_campaign_id: campaignId,
        source_kind: "custom",
        source_id: custom.id,
        access,
        price_cents: 0,
        license_text: licenseText,
        summary,
        license_attestation: attest,
      });
      setDone(true);
      setTimeout(() => { setOpen(false); setDone(false); }, 1500);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (!open) {
    return (
      <button onClick={() => { setOpen(true); setSummary(custom.description_note?.slice(0, 240) || ""); }}
              className="text-mist/60 hover:text-arcane-light p-1"
              title="Publish to the cross-table Marketplace so other GMs can clone this entry."
              data-testid={`custom-publish-${custom.id}`}
              aria-label="Publish to Marketplace">
        <Upload className="w-3 h-3"/>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-void/80 flex items-center justify-center p-4"
         onClick={() => setOpen(false)}
         data-testid="publish-modal">
      <div className="card-mystic p-5 max-w-lg w-full" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="label-ref">Publish to Marketplace</div>
            <h3 className="font-display text-xl text-parchment mt-1">{custom.name}</h3>
            <div className="text-[11px] text-mist/70 uppercase tracking-widest font-ui mt-0.5">
              {custom.kind}
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="text-mist hover:text-gold-bright p-1"
                  aria-label="Close" data-testid="publish-close">
            <X className="w-4 h-4"/>
          </button>
        </div>
        {done ? (
          <div className="text-arcane-light text-center py-6 font-display"
               data-testid="publish-success">
            ✓ Published to Marketplace
          </div>
        ) : (
          <>
            <label className="label-ref block mt-2 mb-1">Access tier</label>
            <div className="grid grid-cols-3 gap-2 mb-3" role="radiogroup">
              {[
                ["public", Globe, "Public", "Any GM can clone."],
                ["paywall", DollarSign, "Paywall (V2)", "Pricing lands with Stripe in V2."],
                ["private", Lock, "Private", "Only you can see this listing."],
              ].map(([k, Icon, label, hint]) => (
                <button key={k} type="button" role="radio" aria-checked={access === k}
                        onClick={() => setAccess(k)}
                        className={`border rounded-sm p-2 text-left ${access === k ? "border-gold-bright bg-gold/10" : "border-gold/15 hover:border-gold/40"}`}
                        data-testid={`publish-access-${k}`}>
                  <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest font-ui">
                    <Icon className="w-3 h-3"/> {label}
                  </div>
                  <div className="text-[10px] text-mist mt-0.5">{hint}</div>
                </button>
              ))}
            </div>

            <label className="label-ref block mb-1">Summary (≤240 chars)</label>
            <textarea className="input min-h-[60px]" value={summary}
                      onChange={(e) => setSummary(e.target.value.slice(0, 240))}
                      placeholder="One-paragraph hook. Markdown-lite supported on the listing card."
                      data-testid="publish-summary"/>

            <label className="label-ref block mt-3 mb-1">License (optional)</label>
            <input className="input" value={licenseText}
                   onChange={(e) => setLicenseText(e.target.value)}
                   placeholder="e.g. CC-BY-SA 4.0 — credit Foo as original author"
                   data-testid="publish-license"/>

            {(access === "public" || access === "paywall") && (
              <label className="flex items-start gap-2 mt-3 text-[12px] text-parchment/85 cursor-pointer"
                     data-testid="publish-attest-row">
                <input type="checkbox" className="mt-0.5" checked={attest}
                       onChange={(e) => setAttest(e.target.checked)}
                       data-testid="publish-attest-checkbox"/>
                <span>
                  I authored this content or have rights to redistribute it
                  under the chosen license. <span className="text-mist/60 italic">
                  Required for public / paywall listings.</span>
                </span>
              </label>
            )}

            {err && <div className="text-ember text-[11px] mt-3" data-testid="publish-error">{err}</div>}

            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setOpen(false)} className="btn btn-ghost text-xs"
                      data-testid="publish-cancel">Cancel</button>
              <button onClick={submit} disabled={busy
                       || ((access === "public" || access === "paywall") && !attest)}
                      className="btn btn-primary text-xs"
                      data-testid="publish-submit">
                {busy ? "Publishing…" : "Publish"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

