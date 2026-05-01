import React, { useEffect, useState, useRef, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Calendar, Swords, Star, RefreshCw, Pin, X } from "lucide-react";

/**
 * TimelinePanel — V6.8 graphical session/encounter tracker.
 *
 * Sessions form a horizontal spine. Encounters cluster above the parent
 * session. Codex-driven Timeline markers (V6.9) hang BELOW the spine —
 * GMs spawn them by clicking a node in `CodexChartView` while a session
 * is selected as the "active" anchor.
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
  const [markers, setMarkers] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [hovered, setHovered] = useState(null);
  const containerRef = useRef(null);
  const vibe = SYSTEM_VIBES[systemId] || SYSTEM_VIBES["besm-4e"];

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const [s, ns, m] = await Promise.all([
        api.get(`/campaigns/${campId}/sessions`).then((r) => r.data),
        api.get(`/campaigns/${campId}/nodes`).then((r) => r.data),
        api.get(`/campaigns/${campId}/timeline-markers`).then((r) => r.data).catch(() => []),
      ]);
      const ordered = (s || []).slice().sort((a, b) => {
        const ta = new Date(a.scheduled_at || a.played_at || a.created_at || 0).getTime();
        const tb = new Date(b.scheduled_at || b.played_at || b.created_at || 0).getTime();
        return ta - tb;
      });
      setSessions(ordered);
      setNodes((ns || []).filter((n) => ["encounter", "set-piece"].includes(n.type)));
      setMarkers(m || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setLoading(false); }
  }, [campId]);

  useEffect(() => { load(); }, [load]);

  // Listen for marker-added events from CodexChartView elsewhere on the page.
  useEffect(() => {
    const onAdded = (ev) => {
      if (ev?.detail?.campId === campId) load();
    };
    window.addEventListener("tg:timeline-marker-added", onAdded);
    return () => window.removeEventListener("tg:timeline-marker-added", onAdded);
  }, [campId, load]);

  const removeMarker = async (mid) => {
    if (!isGm) return;
    if (!window.confirm("Remove this timeline marker?")) return;
    try {
      await api.delete(`/campaigns/${campId}/timeline-markers/${mid}`);
      setMarkers((prev) => prev.filter((x) => x.id !== mid));
    } catch (e) {
      alert(formatApiErrorDetail(e.response?.data?.detail) || "Delete failed.");
    }
  };

  if (loading) return <div className="text-mist text-xs italic">Drawing the timeline…</div>;
  if (err) return <div className="text-ember text-xs">{err}</div>;

  const totalCount = sessions.length;
  const encountersBySession = (sid) => nodes.filter((n) => (n.session_id || n.linked_session_id) === sid);
  const markersBySession = (sid) => markers.filter((m) => m.session_id === sid);

  return (
    <div className="card-mystic p-5" data-testid="timeline-panel">
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Calendar className="w-4 h-4"/> Campaign Timeline
          </div>
          <div className="text-[11px] text-mist italic">
            Sessions on the spine; encounters cluster above, codex pins below. Hover any node to inspect.
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
          {/* Session columns */}
          <div className="relative flex items-start justify-between gap-2 mt-[-30px] min-w-[600px]">
            {sessions.map((s, idx) => {
              const enc = encountersBySession(s.id);
              const mks = markersBySession(s.id);
              const isHovered = hovered === s.id;
              return (
                <div key={s.id}
                     className="relative flex flex-col items-center"
                     style={{ minWidth: 120 }}
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
                  {/* Codex markers below the session */}
                  {mks.length > 0 && (
                    <div className="mt-2 flex flex-col items-center gap-1 max-w-[140px]"
                         data-testid={`timeline-markers-${s.id}`}>
                      {mks.map((m) => (
                        <span key={m.id}
                              className="tag text-[9px] inline-flex items-center gap-1
                                         px-1.5 py-0.5 rounded-sm border group"
                              style={{ borderColor: (m.color || "#C8A34A") + "66",
                                       color: m.color || "#C8A34A",
                                       background: (m.color || "#C8A34A") + "14" }}
                              title={m.label}
                              data-testid={`timeline-marker-${m.id}`}>
                          <Pin className="w-2.5 h-2.5"/>
                          <span className="truncate max-w-[80px]">{m.label}</span>
                          {isGm && (
                            <button
                              onClick={() => removeMarker(m.id)}
                              className="opacity-0 group-hover:opacity-100 ml-0.5 transition"
                              title="Remove marker"
                              data-testid={`timeline-marker-remove-${m.id}`}>
                              <X className="w-2.5 h-2.5"/>
                            </button>
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-4 text-[11px] text-mist italic">
        <Star className="w-3 h-3 inline -mt-0.5 mr-1 text-gold-bright"/>
        Sessions are the spine; encounters bloom from each. Click codex chart nodes (with a session selected) to drop pins below.
      </div>
    </div>
  );
}
