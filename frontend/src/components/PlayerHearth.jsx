import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  User, Swords, BookMarked, ArrowRight, Heart, Calendar, Pin,
} from "lucide-react";
import { api } from "../lib/api";

/**
 * PlayerHearth — V6.14 per-role player widget strip.
 *
 * Mounts above the Dashboard hero for users who have at least one seated
 * character. Three focused widgets answer "what am I doing next, with
 * which character, and where do I find my notes?":
 *   1. Your Sheet  — primary seated character with HP ring + level + campaign
 *   2. Next Session — next upcoming (or in-progress) session the PC belongs to
 *   3. Your Codex  — latest journal entries authored by the user
 *
 * GM-only users (zero seated characters) don't see this strip — their
 * existing Dashboard hearth already serves them well.
 */
export default function PlayerHearth({ myChars }) {
  const [upcoming, setUpcoming] = useState(null);
  const [journal, setJournal] = useState([]);

  // Pick the "primary" seated character — most recently-updated seat
  // (proxy for "the one the player actually plays").
  const primary = useMemo(() => {
    if (!myChars || myChars.length === 0) return null;
    return [...myChars].sort((a, b) =>
      (b.updated_at || "").localeCompare(a.updated_at || "")
    )[0];
  }, [myChars]);

  useEffect(() => {
    if (!primary) return;
    (async () => {
      // Upcoming session in the same campaign.
      try {
        const { data: sessions } = await api.get(
          `/campaigns/${primary.campaign_id}/sessions`);
        const now = Date.now();
        const upcoming = (sessions || [])
          .filter((s) => {
            const when = new Date(s.scheduled_at || 0).getTime();
            return s.status === "in-progress"
              || (when && when > now - 2 * 3600e3);   // 2h grace
          })
          .sort((a, b) =>
            new Date(a.scheduled_at || 0).getTime()
            - new Date(b.scheduled_at || 0).getTime());
        setUpcoming(upcoming[0] || null);
      } catch (_) {}
      // Pull journal entries from folio.
      const entries = (primary.folio?.journal || []).slice(-3).reverse();
      setJournal(entries);
    })();
  }, [primary]);

  if (!primary) return null;  // GM-only users opt out naturally.

  // HP stats (BESM/Anime5E chars carry stats on folio; D&D on folio.dnd_state).
  const hp = primary.folio?.dnd_state?.hp_current ?? primary.health ?? 0;
  const hpMax = primary.folio?.dnd_state?.hp_max ?? primary.health_max
    ?? primary.health ?? 0;
  const hpPct = hpMax > 0 ? Math.max(0, Math.min(100, (hp / hpMax) * 100)) : 0;
  const hpColor = hpPct > 66 ? "#3FAA62" : hpPct > 33 ? "#C8A34A" : "#7A1F2E";

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6"
         data-testid="player-hearth">
      {/* ─── Your Sheet ─── */}
      <Link to={`/app/characters/${primary.id}`}
            className="card-mystic p-4 flex flex-col hover:border-gold/40 transition-colors group"
            data-testid="hearth-your-sheet">
        <div className="flex items-center justify-between">
          <div className="label-ref flex items-center gap-2">
            <User className="w-3 h-3"/> Your sheet
          </div>
          <ArrowRight className="w-4 h-4 text-mist/60 group-hover:text-gold-bright transition-colors"/>
        </div>
        <div className="flex items-center gap-3 mt-3">
          {primary.portrait_url && (
            <img src={`${process.env.REACT_APP_BACKEND_URL || ""}${primary.portrait_url}`}
                 alt="" className="w-14 h-18 rounded-sm object-cover border border-gold/30 flex-shrink-0"
                 style={{ height: 72 }}/>
          )}
          <div className="min-w-0 flex-1">
            <div className="font-display text-lg text-parchment truncate">{primary.name}</div>
            <div className="text-[10px] text-gold/70 font-ui uppercase tracking-widest">
              {primary.system_id?.replace("-", " ") || "—"}
              {primary.folio?.dnd_state?.level && ` · Lv ${primary.folio.dnd_state.level}`}
              {primary.folio?.cypher_state?.tier && ` · Tier ${primary.folio.cypher_state.tier}`}
            </div>
            {hpMax > 0 && (
              <div className="mt-2" data-testid="hearth-hp-bar">
                <div className="flex justify-between text-[9px] font-ui uppercase tracking-widest">
                  <span className="text-mist">HP</span>
                  <span style={{ color: hpColor }}>{Math.round(hp)}/{Math.round(hpMax)}</span>
                </div>
                <div className="h-1.5 bg-void/60 rounded-full mt-0.5 overflow-hidden">
                  <div className="h-full transition-all"
                       style={{ width: `${hpPct}%`, backgroundColor: hpColor }}/>
                </div>
              </div>
            )}
          </div>
        </div>
        {myChars.length > 1 && (
          <div className="text-[10px] text-mist/70 italic mt-3">
            + {myChars.length - 1} other seat{myChars.length > 2 ? "s" : ""} across your tables
          </div>
        )}
      </Link>

      {/* ─── Next Session ─── */}
      <Link to={upcoming ? `/app/sessions/${upcoming.id}` : `/app/campaigns/${primary.campaign_id}`}
            className="card-mystic p-4 flex flex-col hover:border-gold/40 transition-colors group"
            data-testid="hearth-next-session">
        <div className="flex items-center justify-between">
          <div className="label-ref flex items-center gap-2">
            <Calendar className="w-3 h-3"/> Next session
          </div>
          <ArrowRight className="w-4 h-4 text-mist/60 group-hover:text-gold-bright transition-colors"/>
        </div>
        {upcoming ? (
          <div className="mt-3 flex-1">
            {upcoming.status === "in-progress" && (
              <span className="tag border-ember/50 text-ember mb-2 inline-flex items-center gap-1"
                    data-testid="hearth-session-live">
                <Heart className="w-3 h-3 fill-current animate-pulse"/> LIVE NOW
              </span>
            )}
            <div className="font-display text-lg text-parchment truncate">
              {upcoming.name || upcoming.title || "Untitled session"}
            </div>
            {upcoming.scheduled_at && (
              <div className="text-[11px] text-mist mt-1">
                {new Date(upcoming.scheduled_at).toLocaleString([], {
                  weekday: "short", month: "short", day: "numeric",
                  hour: "2-digit", minute: "2-digit",
                })}
              </div>
            )}
            {upcoming.plot_phase && (
              <span className="tag border-arcane/40 text-arcane-light mt-2 inline-flex text-[10px]">
                {upcoming.plot_phase}
              </span>
            )}
          </div>
        ) : (
          <div className="mt-3 flex-1 text-[12px] text-mist italic">
            No scheduled session. The table waits on the Loremaster.
          </div>
        )}
      </Link>

      {/* ─── Your Codex ─── */}
      <Link to={`/app/characters/${primary.id}#history`}
            className="card-mystic p-4 flex flex-col hover:border-gold/40 transition-colors group"
            data-testid="hearth-your-codex">
        <div className="flex items-center justify-between">
          <div className="label-ref flex items-center gap-2">
            <BookMarked className="w-3 h-3"/> Your codex
          </div>
          <ArrowRight className="w-4 h-4 text-mist/60 group-hover:text-gold-bright transition-colors"/>
        </div>
        {journal.length === 0 ? (
          <div className="mt-3 flex-1 text-[12px] text-mist italic">
            No journal entries yet. Drop a note from your character sheet —
            it feeds the Atelier + session recaps.
          </div>
        ) : (
          <div className="mt-3 space-y-2 flex-1">
            {journal.map((e, i) => (
              <div key={i} className="text-[11px] border-l-2 border-arcane/40 pl-2"
                   data-testid={`hearth-journal-${i}`}>
                <div className="text-[9px] text-mist uppercase tracking-widest">
                  {e.created_at ? new Date(e.created_at).toLocaleDateString() : ""}
                </div>
                <div className="text-parchment line-clamp-2 font-body">{e.text}</div>
              </div>
            ))}
          </div>
        )}
        <div className="text-[10px] text-mist/70 italic mt-3 flex items-center gap-1">
          <Pin className="w-2.5 h-2.5"/> From {primary.name}'s journal
        </div>
      </Link>
    </div>
  );
}
