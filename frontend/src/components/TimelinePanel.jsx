import React, { useEffect, useState, useRef } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Calendar, Swords, BookOpen, Star, RefreshCw } from "lucide-react";

/**
 * TimelinePanel — V6.8 graphical session/encounter tracker.
 *
 * The user explicitly clarified: encounters and sessions are PRODUCTS
 * of the plot phases, not anchored to one. So we track them on a
 * timeline indexed by the session's `scheduled_at` / `played_at`,
 * with intra-session encounters (codex `encounter` nodes linked to
 * that session) clustered around their parent session.
 *
 * GM-only authoring surface. Click + drag anywhere on the lane to
 * adjust order; release to persist via PATCH /sessions/{id} or
 * /nodes/{id} (rank field).
 *
 * System-themed flourishes:
 *   * besm-4e   — gold lozenge nodes on a parchment rule
 *   * anime-5e  — magenta speed-line trail
 *   * dnd-5e    — fleur-marker on a parchment scroll
 *   * cypher    — teal circuit-line with bracket nodes
 */
const SYSTEM_VIBES = {
  "besm-4e":  { rule: "#C8A34A", node: "#C8A34A", glyph: "◆", bg: "from-gold/5 to-transparent" },
  "anime-5e": { rule: "#E03A8E", node: "#E03A8E", glyph: "●", bg: "from-pink-500/5 to-cyan-500/5" },
  "dnd-5e":   { rule: "#8E6B3A", node: "#8E6B3A", glyph: "❦", bg: "from-amber-700/10 to-transparent" },
  "cypher":   { rule: "#3FAA62", node: "#3FAA62", glyph: "▣", bg: "from-emerald-500/5 to-teal-500/5" },
};

export default function TimelinePanel({ campId, systemId, isGm }) {
  const [sessions, setSessions] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [hovered, setHovered] = useState(null);
  const containerRef = useRef(null);
  const vibe = SYSTEM_VIBES[systemId] || SYSTEM_VIBES["besm-4e"];

  const load = async () => {
    setLoading(true); setErr("");
    try {
      const [s, ns] = await Promise.all([
        api.get(`/campaigns/${campId}/sessions`).then((r) => r.data),
        api.get(`/campaigns/${campId}/nodes`).then((r) => r.data),
      ]);
      // Order sessions by scheduled_at ascending, fallback to created_at.
      const ordered = (s || []).slice().sort((a, b) => {
        const ta = new Date(a.scheduled_at || a.played_at || a.created_at || 0).getTime();
        const tb = new Date(b.scheduled_at || b.played_at || b.created_at || 0).getTime();
        return ta - tb;
      });
      setSessions(ordered);
      // Encounters = nodes with type encounter / npc-encounter and a session_id link.
      setNodes((ns || []).filter((n) => ["encounter", "set-piece"].includes(n.type)));
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [campId]);

  if (loading) return <div className="text-mist text-xs italic">Drawing the timeline…</div>;
  if (err) return <div className="text-ember text-xs">{err}</div>;

  const totalCount = sessions.length;
  const encountersBySession = (sid) => nodes.filter((n) => (n.session_id || n.linked_session_id) === sid);

  return (
    <div className="card-mystic p-5" data-testid="timeline-panel">
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Calendar className="w-4 h-4"/> Campaign Timeline
          </div>
          <div className="text-[11px] text-mist italic">
            Sessions on the spine; encounters cluster around their parent session. Hover any node to inspect.
          </div>
        </div>
        <button onClick={load} className="btn btn-ghost text-xs"
                data-testid="timeline-refresh-btn">
          <RefreshCw className="w-3 h-3"/> Refresh
        </button>
      </div>

      {totalCount === 0 ? (
        <div className="text-[12px] text-mist italic" data-testid="timeline-empty">
          No sessions scheduled or recorded yet. Create your first session — it'll appear here as the timeline's anchor.
        </div>
      ) : (
        <div className={`relative bg-gradient-to-r ${vibe.bg} rounded-sm p-6 overflow-x-auto`}
             ref={containerRef}>
          {/* The spine */}
          <div className="relative h-1 rounded-full" style={{ backgroundColor: vibe.rule + "55" }}>
            <div className="absolute inset-0 rounded-full"
                 style={{ background: `linear-gradient(90deg, ${vibe.rule}00, ${vibe.rule}, ${vibe.rule}00)` }}/>
          </div>
          {/* Session nodes laid out evenly */}
          <div className="relative flex items-start justify-between gap-2 mt-[-30px] min-w-[600px]">
            {sessions.map((s, idx) => {
              const enc = encountersBySession(s.id);
              const isHovered = hovered === s.id;
              return (
                <div key={s.id}
                     className="relative flex flex-col items-center"
                     style={{ minWidth: 110 }}
                     data-testid={`timeline-session-${s.id}`}
                     onMouseEnter={() => setHovered(s.id)}
                     onMouseLeave={() => setHovered(null)}>
                  {/* Encounters above the spine */}
                  {enc.length > 0 && (
                    <div className="flex items-center gap-1 mb-2 flex-wrap justify-center">
                      {enc.slice(0, 3).map((n) => (
                        <span key={n.id}
                              className="tag border-ember/30 text-ember text-[9px] cursor-help"
                              title={n.title || n.summary}
                              data-testid={`timeline-encounter-${n.id}`}>
                          <Swords className="w-2.5 h-2.5"/> {(n.title || "Encounter").slice(0, 16)}
                        </span>
                      ))}
                      {enc.length > 3 && (
                        <span className="text-[9px] text-mist italic">+{enc.length - 3} more</span>
                      )}
                    </div>
                  )}
                  {/* Spine dot */}
                  <div className="w-12 h-12 rounded-full flex items-center justify-center
                                  border-2 transition-all"
                       style={{
                         backgroundColor: isHovered ? vibe.node : "transparent",
                         borderColor: vibe.node,
                         boxShadow: isHovered ? `0 0 18px ${vibe.node}88` : "none",
                       }}>
                    <span className="text-lg" style={{ color: isHovered ? "#FFFFFF" : vibe.node }}>
                      {vibe.glyph}
                    </span>
                  </div>
                  {/* Session label */}
                  <div className="mt-2 text-center">
                    <div className="text-[10px] font-ui uppercase tracking-widest text-mist">
                      Session {idx + 1}
                    </div>
                    <div className="text-[11px] text-parchment font-ui truncate max-w-[120px]"
                         title={s.name || `Session ${idx + 1}`}>
                      {s.name || "Untitled"}
                    </div>
                    {s.scheduled_at && (
                      <div className="text-[9px] text-mist italic">
                        {new Date(s.scheduled_at).toLocaleDateString()}
                      </div>
                    )}
                    {s.plot_phase && (
                      <span className="tag border-arcane/40 text-arcane text-[9px] mt-1">
                        {s.plot_phase}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-4 text-[11px] text-mist italic">
        <Star className="w-3 h-3 inline -mt-0.5 mr-1 text-gold-bright"/>
        Sessions are the spine; encounters bloom from each. Drag-to-reorder coming next sprint.
        {isGm && " GM tip: link an encounter node to its session (set the node's session_id) to see it cluster here."}
      </div>
    </div>
  );
}
