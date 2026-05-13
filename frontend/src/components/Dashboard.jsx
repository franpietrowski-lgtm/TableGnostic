/**
 * Dashboard — the player / GM hearth.
 *
 * One-page design. Everything a returning user asks in 5 seconds lives
 * above the fold:
 *   1. Hero strip — welcome + quick actions (Forge campaign · Deploy
 *      demo · Discover · How-to landing CTA when we ship it).
 *   2. Continue strip — last three sessions the user was active in,
 *      one-click resume links that land back inside the Session Altar.
 *   3. Your campaigns — rich system-badged cards with seated-count,
 *      current plot phase, owner-or-player indicator.
 *   4. Recent character activity — journal entries + XP events across
 *      the user's seated characters (honest "what happened since I
 *      was here last" strip).
 *   5. Discover strip — public tables seeking players, tightened to 6.
 *
 * Everything is responsive: the hero strip stacks on narrow, the
 * campaign grid collapses 3 → 2 → 1 at md / sm / base.
 */
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, useAuth } from "../lib/api";
import {
  Scroll, Plus, ArrowRight, Flame, PlayCircle, Users, Sparkles,
  BookOpen, Compass, Dices, BookMarked,
} from "lucide-react";
import PlayerHearth from "./PlayerHearth";
import { WriterRoleHeader } from "./writers/WriterPages";

const SYSTEM_TINT = {
  "besm-4e":  "#C8A34A",
  "dnd-5e":   "#B22222",
  "cypher":   "#7A88C7",
  "anime-5e": "#E03A8E",
};

const SYSTEM_LABEL = {
  "besm-4e":  "BESM 4E",
  "dnd-5e":   "D&D 5E",
  "cypher":   "Cypher",
  "anime-5e": "Anime 5E",
};

export default function Dashboard() {
  const { user } = useAuth();
  const [mine, setMine] = useState([]);
  const [all, setAll] = useState([]);
  const [myChars, setMyChars] = useState([]);
  const [recentSessions, setRecentSessions] = useState([]);

  useEffect(() => {
    (async () => {
      const [m, a, chs] = await Promise.all([
        api.get("/campaigns", { params: { mine: true } })
          .then((r) => r.data).catch(() => []),
        api.get("/campaigns").then((r) => r.data).catch(() => []),
        api.get("/characters", { params: { mine: true } })
          .then((r) => r.data).catch(() => []),
      ]);
      setMine(m); setAll(a); setMyChars(chs);

      // Pull the three most-recent sessions across the user's owned
      // campaigns — one parallel fetch per campaign is fine at this
      // cardinality (dashboards won't scale to 50 campaigns before
      // we'd need a dedicated /api/dashboard aggregator).
      const per = await Promise.all(
        m.slice(0, 8).map((c) =>
          api.get(`/campaigns/${c.id}/sessions`)
            .then((r) => (r.data || []).map((s) => ({ ...s, campaign: c })))
            .catch(() => [])
        )
      );
      const flat = [].concat(...per);
      flat.sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));
      setRecentSessions(flat.slice(0, 3));
    })();
  }, []);

  const publicCount = useMemo(
    () => all.filter((c) => c.visibility === "public").length, [all]);
  const gmCount = useMemo(() => mine.filter((c) => c.is_gm).length, [mine]);
  const seatCount = myChars.length;

  return (
    <div className="px-5 md:px-12 py-8 md:py-10 max-w-6xl" data-testid="dashboard">
      {/* ── Player Hearth widget strip (shows when user has ≥1 seated PC) ── */}
      <PlayerHearth myChars={myChars}/>

      {/* V6.25.45 — Writer-role welcome banner (Worldbuilder / Storyteller).
          Self-renders null for player/gm/admin so the regular hero strip
          still leads for them. */}
      <WriterRoleHeader role={user?.role} userName={user?.name}/>

      {/* ── Hero strip ── */}
      <div className="flex items-end justify-between flex-wrap gap-4 mb-2">
        <div>
          <div className="label-ref mb-2">Hearth</div>
          <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl tracking-wide text-parchment">
            Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}.
          </h1>
          <p className="text-mist font-body text-sm md:text-base mt-1 max-w-xl">
            Three live ways to take a seat: resume a session, forge a
            fresh campaign, or walk into a public table.
          </p>
        </div>
        {/* Quick stats — tight, honest, tabular-nums so the eye grabs
            them in one glance. */}
        <div className="flex gap-2 sm:gap-3 flex-wrap">
          <StatChip label="Campaigns" v={mine.length} testid="dash-stat-campaigns"/>
          <StatChip label="GM of" v={gmCount} testid="dash-stat-gm"/>
          <StatChip label="Seats" v={seatCount} testid="dash-stat-seats"/>
          <StatChip label="Public" v={publicCount} testid="dash-stat-public"/>
        </div>
      </div>

      {/* ── Quick action rail ── */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        <ActionCard to="/app/campaigns?create=1"
                    icon={<Plus className="w-4 h-4"/>}
                    title="Forge a campaign"
                    blurb="Start a new table — pick a system, seed the Atelier."
                    testid="dash-action-create"/>
        <ActionCard to="/app/campaigns"
                    icon={<Scroll className="w-4 h-4"/>}
                    title="My campaigns"
                    blurb={`${mine.length} open thread${mine.length === 1 ? "" : "s"}`}
                    testid="dash-action-mine"/>
        <ActionCard to="/app/discover"
                    icon={<Compass className="w-4 h-4"/>}
                    title="Discover tables"
                    blurb={`${publicCount} public table${publicCount === 1 ? "" : "s"} seeking players`}
                    testid="dash-action-discover"/>
        <ActionCard to="/app/reference"
                    icon={<BookOpen className="w-4 h-4"/>}
                    title="Reference Gate"
                    blurb="System SRDs · Atelier primers · custom entries."
                    testid="dash-action-reference"/>
      </div>

      {/* ── Continue at the table ── */}
      {recentSessions.length > 0 && (
        <div className="mt-10" data-testid="dash-continue">
          <div className="flex items-center justify-between mb-2">
            <h2 className="h-arcane text-lg flex items-center gap-2">
              <PlayCircle className="w-4 h-4 text-arcane-light"/> Continue at the table
            </h2>
            <Link to="/app/campaigns" className="text-[10px] text-gold/80 hover:text-gold-bright uppercase tracking-widest font-ui">
              All campaigns <ArrowRight className="inline w-3 h-3"/>
            </Link>
          </div>
          <div className="divider-sigil mb-3"/>
          <div className="grid md:grid-cols-3 gap-3">
            {recentSessions.map((s) => (
              <Link key={s.id} to={`/app/sessions/${s.id}`}
                    data-testid={`dash-session-${s.id}`}
                    className="card-mystic p-4 transition hover:-translate-y-0.5 hover:border-gold/60">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="label-ref">Session</span>
                  <SystemBadge systemId={s.campaign?.system_id}/>
                </div>
                <div className="mt-1 font-display text-lg text-parchment truncate">{s.title || "Untitled session"}</div>
                <div className="text-[11px] text-mist truncate">{s.campaign?.name}</div>
                <div className="mt-2 flex items-center gap-2 text-[10px] text-mist/70 font-ui">
                  <Users className="w-3 h-3"/>
                  {Object.keys(s.character_assignments || {}).length} seated
                  {s.round ? <span className="ml-1">· round {s.round}</span> : null}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── Your campaigns ── */}
      <div className="mt-10" data-testid="dash-campaigns">
        <div className="flex items-center justify-between">
          <h2 className="h-arcane text-lg flex items-center gap-2">
            <Scroll className="w-4 h-4 text-gold"/> Your campaigns
          </h2>
          <Link to="/app/campaigns"
                className="text-[10px] text-gold/80 hover:text-gold-bright uppercase tracking-widest font-ui">
            Browse all <ArrowRight className="inline w-3 h-3"/>
          </Link>
        </div>
        <div className="divider-sigil my-3"/>
        {mine.length === 0 ? (
          <div className="card-mystic p-6 text-center">
            <div className="text-mist text-sm font-body italic mb-3">
              No threads held yet. Start your first campaign, or sit in
              on a public table.
            </div>
            <div className="flex justify-center gap-2">
              <Link to="/app/campaigns?create=1" className="btn btn-primary text-xs"
                    data-testid="dash-empty-create">
                <Plus className="w-3 h-3"/> Forge a campaign
              </Link>
              <Link to="/app/discover" className="btn btn-ghost text-xs"
                    data-testid="dash-empty-discover">
                <Compass className="w-3 h-3"/> Discover public tables
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {mine.map((c) => (
              <Link key={c.id} to={`/app/campaigns/${c.id}`}
                    className="card-mystic p-4 transition hover:-translate-y-0.5 hover:border-gold/60"
                    data-testid={`campaign-card-${c.id}`}>
                <div className="flex items-center justify-between gap-2">
                  <SystemBadge systemId={c.system_id} compact />
                  <span className="text-[9px] font-ui uppercase tracking-widest text-mist">
                    {c.is_gm ? "GM" : "Player"}
                  </span>
                </div>
                <div className="font-display text-lg text-parchment mt-2 truncate">{c.name}</div>
                <div className="text-xs text-mist mt-1 line-clamp-2 h-8">
                  {c.description || <span className="italic">No description yet.</span>}
                </div>
                <SystemBadge systemId={c.system_id} />
                <div className="flex items-center justify-between mt-3">
                  <span className="tag text-[9px]">{c.visibility}</span>
                  <span className="text-[10px] text-gold/70 font-ui flex items-center gap-1">
                    <Users className="w-3 h-3"/>
                    {c.member_ids?.length || 0}{c.max_players ? `/${c.max_players}` : ""}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* ── Your characters ── */}
      {myChars.length > 0 && (
        <div className="mt-10" data-testid="dash-characters">
          <div className="flex items-center justify-between">
            <h2 className="h-arcane text-lg flex items-center gap-2">
              <Dices className="w-4 h-4 text-gold"/> Your characters
            </h2>
          </div>
          <div className="divider-sigil my-3"/>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {myChars.slice(0, 6).map((ch) => (
              <Link key={ch.id} to={`/app/characters/${ch.id}`}
                    className="card-mystic p-4 transition hover:-translate-y-0.5 hover:border-gold/60"
                    data-testid={`dash-character-${ch.id}`}>
                <div className="flex items-center gap-2">
                  {ch.token_color && (
                    <span className="inline-block w-3 h-3 rounded-full border border-gold/40"
                          style={{ backgroundColor: ch.token_color }}/>
                  )}
                  <div className="font-display text-base text-parchment truncate flex-1">
                    {ch.name || "Untitled"}
                  </div>
                </div>
                <div className="text-[11px] text-mist italic mt-1 line-clamp-2 h-8">
                  {ch.concept || "No concept yet."}
                </div>
                <div className="text-[10px] text-mist/70 mt-2 font-ui uppercase tracking-widest">
                  {ch.spent?.total_spent ?? 0} / {ch.total_points} pts
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── Discover strip ── */}
      {publicCount > 0 && (
        <div className="mt-10 mb-4" data-testid="dash-discover-strip">
          <div className="flex items-center justify-between">
            <h2 className="h-arcane text-lg flex items-center gap-2">
              <Flame className="w-4 h-4 text-ember"/> Tables seeking players
            </h2>
            <Link to="/app/discover"
                  className="text-[10px] text-gold/80 hover:text-gold-bright uppercase tracking-widest font-ui">
              Seekers' Hall <ArrowRight className="inline w-3 h-3"/>
            </Link>
          </div>
          <div className="divider-sigil my-3"/>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {all.filter((c) => c.visibility === "public" && !c.is_gm && !c.is_member).slice(0, 6).map((c) => (
              <Link key={c.id} to={`/app/campaigns/${c.id}`}
                    className="card-mystic p-4 transition hover:-translate-y-0.5 hover:border-gold/60"
                    data-testid={`dash-public-${c.id}`}>
                <div className="flex items-baseline justify-between gap-2">
                  <SystemBadge systemId={c.system_id}/>
                  <span className="text-[9px] font-ui uppercase tracking-widest text-mist">
                    {c.member_ids?.length || 0}/{c.max_players || "—"}
                  </span>
                </div>
                <div className="font-display text-base text-parchment mt-2 truncate">{c.name}</div>
                <div className="text-[11px] text-mist italic mt-1 line-clamp-2 h-8">
                  {c.description || "No description yet."}
                </div>
                <div className="mt-3 flex items-center gap-1 text-[10px] text-gold/80 font-ui uppercase tracking-widest">
                  <Sparkles className="w-3 h-3"/> by {c.gm_name || "a loremaster"}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatChip({ label, v, testid }) {
  return (
    <div className="border border-gold/15 rounded-sm px-3 py-1.5 bg-void/40" data-testid={testid}>
      <div className="text-[9px] font-ui uppercase tracking-widest text-mist">{label}</div>
      <div className="font-display text-xl text-gold-bright tabular-nums">{v}</div>
    </div>
  );
}

function ActionCard({ to, icon, title, blurb, testid }) {
  return (
    <Link to={to}
          className="card-mystic p-4 transition hover:-translate-y-0.5 hover:border-gold/60 flex flex-col h-full"
          data-testid={testid}>
      <div className="flex items-center gap-2 text-gold-bright">
        {icon}
        <span className="label-ref">{title}</span>
      </div>
      <div className="text-xs text-mist mt-2 flex-1">{blurb}</div>
      <div className="mt-2 text-[10px] text-gold/70 font-ui uppercase tracking-widest">
        Enter <ArrowRight className="inline w-3 h-3"/>
      </div>
    </Link>
  );
}

function SystemBadge({ systemId }) {
  const tint = SYSTEM_TINT[systemId] || "#C8A34A";
  const label = SYSTEM_LABEL[systemId] || (systemId || "system").toUpperCase();
  return (
    <span className="inline-flex items-center gap-1 text-[9px] font-ui uppercase tracking-widest px-1.5 py-0.5 rounded-sm"
          style={{
            backgroundColor: `${tint}20`,
            borderColor: `${tint}55`, borderWidth: 1, color: tint,
          }}>
      <BookMarked className="w-2.5 h-2.5"/> {label}
    </span>
  );
}
