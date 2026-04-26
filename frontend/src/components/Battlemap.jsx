import React, { useEffect, useRef, useState, useCallback } from "react";
import { api } from "../lib/api";
import {
  Map as MapIcon, Image as ImageIcon, Eye, EyeOff, Plus, X,
  Hammer, Hand, MousePointer2, Trash2,
} from "lucide-react";

/**
 * Battlemap — square-grid canvas inside a SessionView.
 *
 * Modes:
 *   select  — click/drag to move tokens (player can move own; GM moves any)
 *   fog     — GM only: paint cells to hide; shift-click to reveal
 *   wall    — GM only: click + drag to draw a wall segment
 *
 * Real-time:
 *   Re-uses the SessionView WS bridge via subscribe()/send() props
 *   (same surface AVSeats uses). Listens for map:* events and updates
 *   local state without a refetch.
 *
 * Token drag protocol:
 *   onMouseDown over a token enters a drag; onMouseUp commits the new
 *   (x, y) cell coordinate via POST /api/sessions/{sid}/map/tokens.
 *   Every mid-drag cell change is local-only — the network sees the
 *   final position only.
 *
 * Initiative spotlight:
 *   When `activeUid` is set (from initiative top-of-order), the matching
 *   character's token gets a gold ring + slow pulse.
 */
export default function Battlemap({
  sessionId,
  campaign,
  characters = [],
  initiative = [],
  user,
  subscribe,
  onClose,
}) {
  const isGm = !!campaign && (campaign.gm_id === user?.id || user?.role === "admin");

  const [state, setState] = useState(null);   // { grid, image, tokens, walls, fog, ... }
  const [mode, setMode] = useState(isGm ? "select" : "select");
  const [draggingId, setDraggingId] = useState(null);
  const [dragPos, setDragPos] = useState(null); // {x, y} grid-cell coords, mid-drag
  const [wallStart, setWallStart] = useState(null);
  const canvasRef = useRef(null);

  // ─── load + WS subscribe ───
  useEffect(() => {
    if (!sessionId) return;
    let mounted = true;
    api.get(`/sessions/${sessionId}/map`).then((r) => {
      if (mounted) setState(r.data);
    }).catch(() => {});
    return () => { mounted = false; };
  }, [sessionId]);

  useEffect(() => {
    if (!subscribe) return;
    const off = subscribe((evt) => {
      if (!evt || !evt.type || !state) return;
      const { type, data } = evt;
      if (type === "map:state") setState(data);
      else if (type === "map:token") {
        setState((s) => {
          const tokens = s.tokens.filter((t) => t.id !== data.id);
          return { ...s, tokens: [...tokens, data] };
        });
      }
      else if (type === "map:token-remove") {
        setState((s) => ({ ...s, tokens: s.tokens.filter((t) => t.id !== data.id) }));
      }
      else if (type === "map:fog") {
        setState((s) => {
          const cur = new Set(s.fog.map((c) => `${c.x},${c.y}`));
          (data.hide || []).forEach((c) => cur.add(`${c.x},${c.y}`));
          (data.reveal || []).forEach((c) => cur.delete(`${c.x},${c.y}`));
          return { ...s, fog: Array.from(cur).map((k) => {
            const [x, y] = k.split(",").map(Number);
            return { x, y };
          }) };
        });
      }
      else if (type === "map:wall") {
        setState((s) => {
          let walls = s.walls;
          if (data.added) walls = [...walls, data.added];
          if (data.removed) walls = walls.filter((w) => w.id !== data.removed);
          return { ...s, walls };
        });
      }
    });
    return () => { try { off && off(); } catch {} };
  }, [subscribe, state]);

  // Active uid (initiative top of order) → matching character → token highlight
  const activeUid = (initiative && initiative.length > 0)
    ? (initiative[0].character_id
        ? (characters.find((c) => c.id === initiative[0].character_id) || {}).owner_id
        : initiative[0].uid)
    : null;
  const activeCharIds = characters
    .filter((c) => c.owner_id === activeUid)
    .map((c) => c.id);

  // ─── helpers ───
  const cellSize = state?.grid?.size_px || 48;
  const cols = state?.grid?.cols || 24;
  const rows = state?.grid?.rows || 16;
  const W = cellSize * cols;
  const H = cellSize * rows;

  const eventToCell = (ev) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (ev.clientX - rect.left) * (W / rect.width);
    const y = (ev.clientY - rect.top) * (H / rect.height);
    return { x: x / cellSize, y: y / cellSize };
  };

  const sendToken = useCallback(async (token) => {
    try { await api.post(`/sessions/${sessionId}/map/tokens`, token); } catch {}
  }, [sessionId]);

  const tokenIsMine = (t) => {
    if (isGm) return true;
    if (!t.character_id) return false;
    const ch = characters.find((c) => c.id === t.character_id);
    return ch && ch.owner_id === user?.id;
  };

  // ─── canvas interaction ───
  const onMouseDown = (ev) => {
    if (!state) return;
    const cell = eventToCell(ev);
    if (mode === "fog" && isGm) {
      const x = Math.floor(cell.x), y = Math.floor(cell.y);
      const isShift = ev.shiftKey;
      api.post(`/sessions/${sessionId}/map/fog`,
        isShift ? { reveal: [{ x, y }] } : { hide: [{ x, y }] }).catch(() => {});
      return;
    }
    if (mode === "wall" && isGm) {
      setWallStart(cell);
      return;
    }
    // select mode — find a token under the click
    const hit = [...state.tokens].reverse().find((t) => {
      const dx = cell.x - t.x, dy = cell.y - t.y;
      return Math.abs(dx) < t.size / 2 + 0.5 && Math.abs(dy) < t.size / 2 + 0.5;
    });
    if (hit && tokenIsMine(hit)) {
      setDraggingId(hit.id);
      setDragPos({ x: hit.x, y: hit.y });
    }
  };
  const onMouseMove = (ev) => {
    if (!draggingId || !state) return;
    const cell = eventToCell(ev);
    setDragPos({ x: cell.x, y: cell.y });
  };
  const onMouseUp = (ev) => {
    if (!state) return;
    if (mode === "wall" && isGm && wallStart) {
      const cell = eventToCell(ev);
      api.post(`/sessions/${sessionId}/map/walls`, {
        x1: wallStart.x, y1: wallStart.y, x2: cell.x, y2: cell.y,
      }).catch(() => {});
      setWallStart(null);
      return;
    }
    if (draggingId && dragPos) {
      const t = state.tokens.find((x) => x.id === draggingId);
      if (t) {
        sendToken({ ...t, x: Math.round(dragPos.x * 2) / 2, y: Math.round(dragPos.y * 2) / 2 });
      }
    }
    setDraggingId(null);
    setDragPos(null);
  };

  // ─── GM controls ───
  const setBgImage = async () => {
    const url = window.prompt("Background image URL?", state?.image?.url || "");
    if (url == null) return;
    await api.put(`/sessions/${sessionId}/map`, {
      grid: state.grid,
      image: { ...state.image, url },
      tokens: state.tokens, walls: state.walls, fog: state.fog,
    });
  };
  const setGrid = async () => {
    const cols = parseInt(window.prompt("Cols?", state.grid.cols), 10);
    const rows = parseInt(window.prompt("Rows?", state.grid.rows), 10);
    if (!cols || !rows) return;
    await api.put(`/sessions/${sessionId}/map`, {
      grid: { ...state.grid, cols, rows },
      image: state.image,
      tokens: state.tokens, walls: state.walls, fog: state.fog,
    });
  };
  const seedTokensFromCharacters = async () => {
    if (!isGm) return;
    let i = 0;
    for (const c of characters) {
      if (!c.published) continue;
      const exists = (state.tokens || []).find((t) => t.character_id === c.id);
      if (exists) continue;
      await sendToken({
        character_id: c.id,
        label: c.name,
        color: c.token_color || "#c8a34a",
        x: 2 + (i * 2), y: 2,
        size: 1, hp_pct: 100, status: [],
      });
      i++;
    }
  };
  const removeToken = async (id) => {
    if (!isGm) return;
    if (!window.confirm("Remove this token?")) return;
    await api.delete(`/sessions/${sessionId}/map/tokens/${id}`).catch(() => {});
  };
  const removeWall = async (id) => {
    if (!isGm) return;
    await api.delete(`/sessions/${sessionId}/map/walls/${id}`).catch(() => {});
  };
  const clearAllFog = async () => {
    if (!isGm || !state) return;
    if (!window.confirm("Reveal the whole map to all players?")) return;
    await api.post(`/sessions/${sessionId}/map/fog`, { reveal: state.fog });
  };
  const fillAllFog = async () => {
    if (!isGm || !state) return;
    if (!window.confirm("Hide the entire map under fog?")) return;
    const cells = [];
    for (let x = 0; x < cols; x++) for (let y = 0; y < rows; y++) cells.push({ x, y });
    await api.post(`/sessions/${sessionId}/map/fog`, { hide: cells });
  };

  // ─── render ───
  if (!state) return (
    <div className="card-mystic p-6 text-mist text-sm" data-testid="battlemap-loading">
      Unrolling the map…
    </div>
  );

  const fogSet = new Set(state.fog.map((c) => `${c.x},${c.y}`));

  return (
    <div className="card-mystic p-3 md:p-4 flex flex-col" data-testid="battlemap" data-mode={mode}>
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="min-w-0">
          <div className="label-ref">Battlemap</div>
          <div className="text-[10px] font-ui uppercase tracking-widest text-mist/60 truncate">
            {cols}×{rows} · {state.tokens.length} token{state.tokens.length !== 1 && "s"} ·{" "}
            {fogSet.size} hidden cell{fogSet.size !== 1 && "s"}
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {/* mode toggles */}
          <button onClick={() => setMode("select")}
                  className={`btn ${mode === "select" ? "btn-primary" : "btn-ghost"} text-xs px-2`}
                  data-testid="map-mode-select" title="Select / move">
            <MousePointer2 className="w-3.5 h-3.5"/>
          </button>
          {isGm && (
            <button onClick={() => setMode("fog")}
                    className={`btn ${mode === "fog" ? "btn-primary" : "btn-ghost"} text-xs px-2`}
                    data-testid="map-mode-fog" title="Paint fog (shift-click to reveal)">
              <Eye className="w-3.5 h-3.5"/>
            </button>
          )}
          {isGm && (
            <button onClick={() => setMode("wall")}
                    className={`btn ${mode === "wall" ? "btn-primary" : "btn-ghost"} text-xs px-2`}
                    data-testid="map-mode-wall" title="Draw wall segment">
              <Hammer className="w-3.5 h-3.5"/>
            </button>
          )}
          {onClose && (
            <button onClick={onClose} className="btn btn-ghost text-xs px-2" data-testid="map-close" title="Close map">
              <X className="w-3.5 h-3.5"/>
            </button>
          )}
        </div>
      </div>

      {isGm && (
        <div className="flex flex-wrap gap-1.5 mb-2 text-[10px]" data-testid="map-gm-tools">
          <button onClick={setBgImage} className="btn btn-ghost text-[10px]" data-testid="map-bg-btn">
            <ImageIcon className="w-3 h-3"/> Image
          </button>
          <button onClick={setGrid} className="btn btn-ghost text-[10px]" data-testid="map-grid-btn">
            <MapIcon className="w-3 h-3"/> Grid
          </button>
          <button onClick={seedTokensFromCharacters} className="btn btn-ghost text-[10px]" data-testid="map-seed-tokens">
            <Plus className="w-3 h-3"/> Seed PCs
          </button>
          <button onClick={fillAllFog} className="btn btn-ghost text-[10px]" data-testid="map-fog-fill">
            <EyeOff className="w-3 h-3"/> Hide all
          </button>
          <button onClick={clearAllFog} className="btn btn-ghost text-[10px]" data-testid="map-fog-clear">
            <Eye className="w-3 h-3"/> Reveal all
          </button>
        </div>
      )}

      {/* Canvas */}
      <div
        ref={canvasRef}
        className="relative w-full overflow-hidden border border-gold/30 bg-black/80 select-none cursor-crosshair"
        style={{ aspectRatio: `${W} / ${H}` }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        data-testid="battlemap-canvas"
      >
        {/* Background image */}
        {state.image?.url && (
          <img
            src={state.image.url}
            alt=""
            draggable={false}
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ objectFit: state.image.fit || "cover" }}
          />
        )}
        {/* Grid overlay */}
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          <g opacity={state.grid.opacity}>
            {[...Array(cols + 1)].map((_, i) => (
              <line key={`v${i}`} x1={i * cellSize} y1={0} x2={i * cellSize} y2={H}
                    stroke={state.grid.color} strokeWidth="1"/>
            ))}
            {[...Array(rows + 1)].map((_, i) => (
              <line key={`h${i}`} x1={0} y1={i * cellSize} x2={W} y2={i * cellSize}
                    stroke={state.grid.color} strokeWidth="1"/>
            ))}
          </g>
          {/* Walls */}
          {state.walls.map((w) => (
            <line key={w.id}
                  x1={w.x1 * cellSize} y1={w.y1 * cellSize}
                  x2={w.x2 * cellSize} y2={w.y2 * cellSize}
                  stroke="#c8a34a" strokeWidth="3" strokeLinecap="round"
                  className={isGm ? "cursor-pointer pointer-events-auto" : ""}
                  onClick={isGm ? (e) => { e.stopPropagation(); removeWall(w.id); } : undefined}
                  data-testid={`map-wall-${w.id}`}/>
          ))}
        </svg>

        {/* Fog */}
        {Array.from(fogSet).map((k) => {
          const [x, y] = k.split(",").map(Number);
          return (
            <div key={k}
                 className="absolute pointer-events-none"
                 style={{
                   left: `${(x / cols) * 100}%`,
                   top: `${(y / rows) * 100}%`,
                   width: `${100 / cols}%`,
                   height: `${100 / rows}%`,
                   background: isGm ? "rgba(0,0,0,0.55)" : "rgba(0,0,0,1)",
                   backdropFilter: isGm ? "blur(2px)" : undefined,
                 }}
                 data-testid={`map-fog-cell-${x}-${y}`}/>
          );
        })}

        {/* Tokens */}
        {state.tokens.map((t) => {
          const isDragging = draggingId === t.id;
          const px = (isDragging && dragPos ? dragPos.x : t.x) / cols * 100;
          const py = (isDragging && dragPos ? dragPos.y : t.y) / rows * 100;
          const sizePct = (t.size || 1) / cols * 100;
          const isActive = t.character_id && activeCharIds.includes(t.character_id);
          const ch = characters.find((c) => c.id === t.character_id);
          const initials = (t.label || ch?.name || "?").trim().charAt(0).toUpperCase();
          return (
            <button
              key={t.id}
              type="button"
              onContextMenu={isGm ? (e) => { e.preventDefault(); removeToken(t.id); } : undefined}
              className={`absolute rounded-full border-2 flex items-center justify-center font-display text-base shadow-[0_2px_8px_rgba(0,0,0,0.6)]
                ${isActive ? "ring-2 ring-gold ring-offset-1 ring-offset-black animate-pulse" : ""}
                ${tokenIsMine(t) ? "cursor-grab active:cursor-grabbing" : "cursor-not-allowed"}`}
              style={{
                left: `calc(${px}% - ${sizePct / 2}%)`,
                top: `calc(${py}% - ${sizePct / 2}%)`,
                width: `${sizePct}%`,
                aspectRatio: "1 / 1",
                background: `${t.color || "#c8a34a"}cc`,
                borderColor: t.color || "#c8a34a",
                color: "#0a0810",
                zIndex: isDragging ? 30 : 10,
              }}
              data-testid={`map-token-${t.id}`}
              data-active={isActive ? "true" : "false"}
              aria-label={t.label || ch?.name || "token"}
              title={`${t.label || ch?.name || ""}${isActive ? " · ACTIVE" : ""} ${isGm ? "· right-click to remove" : ""}`}
            >
              {initials}
              {/* HP bar */}
              {t.hp_pct < 100 && (
                <div className="absolute -bottom-1 left-0 right-0 h-1 bg-black/80 rounded">
                  <div className="h-full bg-ember rounded"
                       style={{ width: `${Math.max(0, Math.min(100, t.hp_pct))}%` }}/>
                </div>
              )}
              {/* Status rings */}
              {(t.status || []).slice(0, 3).map((s, i) => (
                <span key={i}
                      className="absolute -top-1 -right-1 px-1 py-[1px] text-[8px] uppercase
                                 tracking-widest bg-arcane text-parchment rounded-sm border border-arcane"
                      style={{ transform: `translateY(${i * 10}px)` }}
                      data-testid={`map-token-${t.id}-status-${i}`}>
                  {s}
                </span>
              ))}
            </button>
          );
        })}
      </div>

      <div className="text-[10px] font-ui uppercase tracking-widest text-mist/60 mt-2">
        {isGm
          ? "GM · select to move tokens · fog: click hide / shift-click reveal · wall: click+drag · right-click token to remove"
          : "Drag tokens you own. Tokens with the gold ring are on the active turn."}
      </div>
    </div>
  );
}
