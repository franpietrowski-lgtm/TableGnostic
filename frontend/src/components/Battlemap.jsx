import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { api } from "../lib/api";
import { useMinDelay } from "../lib/useMinDelay";
import {
  Map as MapIcon, Image as ImageIcon, Eye, EyeOff, Plus, X,
  Hammer, Hand, MousePointer2, Trash2, Ruler, Sparkles, Maximize2, Minimize2,
} from "lucide-react";
import BattlemapSidebar, { MARKER_ICONS } from "./BattlemapSidebar";

/**
 * Battlemap — square-grid canvas inside a SessionView.
 *
 * Modes:
 *   select  — click/drag to move tokens (player can move own; GM moves any)
 *   fog     — GM only: paint cells to hide; shift-click to reveal
 *   wall    — GM only: click + drag to draw a wall segment
 *   measure — anyone: click + drag to draw a ruler; cells, metres, +Mod
 *
 * V2 additions (this round):
 *   * Line-of-sight raycast — for each token, we raycast from active-uid's
 *     token to it and hide the destination if any wall segment intersects
 *     the ray. Active-actor tokens stay visible to themselves; GM sees
 *     everything regardless.
 *   * Distance-measure tool — temporary ruler line (chebyshev cells +
 *     metric metres, derived from grid scale 2m/cell).
 *   * Status-effect binding — pulls live effects from /api/effects on
 *     mount + every WS effect/effect_remove event so token rings reflect
 *     current battle state without a manual refresh.
 *
 * Real-time: re-uses the SessionView WS bridge via subscribe() prop.
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
  const [effects, setEffects] = useState([]); // live /api/effects rows
  const [mode, setMode] = useState(isGm ? "select" : "select");
  const [draggingId, setDraggingId] = useState(null);
  const [dragPos, setDragPos] = useState(null); // {x, y} grid-cell coords, mid-drag
  const [wallStart, setWallStart] = useState(null);
  const [measureStart, setMeasureStart] = useState(null);
  const [measureEnd, setMeasureEnd] = useState(null);
  const [losEnabled, setLosEnabled] = useState(true);
  // V6.25.48 — sidebar overhaul.
  // `snapToGrid` controls whether token drops round to half-cell
  // increments (default on). `pendingPlacement` holds a `{kind,
  // marker_type|character, color, label, atlas_node_id?}` payload
  // selected from the sidebar — next canvas click spawns it.
  // `vitals` is a {character_id: {hp_pct, ep_pct, ...}} map polled
  // from /map/vitals every 6s to auto-fill PC token rings (P1).
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [pendingPlacement, setPendingPlacement] = useState(null);
  const [vitals, setVitals] = useState({});
  // Mobile detector — strictly viewport-based; mobile users get a
  // view-only experience (no GM tools, locked to select mode). Desktop
  // gets the full editing kit. Tracks resize so a tablet rotation flips
  // the gating immediately.
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth < 768 : false
  );
  useEffect(() => {
    const onR = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", onR);
    return () => window.removeEventListener("resize", onR);
  }, []);
  // Fullscreen edit mode — desktop GM only. When ON, the map takes
  // over the viewport with a black backdrop so the GM can place
  // walls / tokens / fog / notes without the rest of the app fighting
  // for attention. Auto-engages whenever the GM picks an editing tool.
  const [fullscreenEdit, setFullscreenEdit] = useState(false);
  const isEditingMode = mode === "fog" || mode === "wall";
  // Player & mobile clients must stay in select mode. If a tool gets
  // assigned that they aren't allowed (e.g. fog), force-revert to
  // select instead of leaving an unusable cursor.
  useEffect(() => {
    if (isMobile && mode !== "select") setMode("select");
    if (!isGm && (mode === "fog" || mode === "wall")) setMode("select");
  }, [isMobile, isGm, mode]);
  // GM editor tool → auto-fullscreen (desktop only).
  useEffect(() => {
    if (isMobile) return;
    if (isGm && isEditingMode) setFullscreenEdit(true);
  }, [isGm, isEditingMode, isMobile]);
  // ESC bails out of fullscreen.
  useEffect(() => {
    if (!fullscreenEdit) return;
    const onKey = (e) => { if (e.key === "Escape") setFullscreenEdit(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fullscreenEdit]);
  // Min-delay so the "Unrolling the map…" line gets a beat to read.
  const stillUnrolling = useMinDelay(!state, 5000);
  const canvasRef = useRef(null);

  // V6.25.6 mobile sweep — pinch-zoom + 2-finger pan state. `zoom` is
  // a uniform scale; `pan` is a translate in canvas-local pixels.
  // `pinching` is true mid-gesture so we can short-circuit transition.
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [pinching, setPinching] = useState(false);
  const gestureRef = useRef({ startDist: 0, startZoom: 1,
                                 startCenter: { x: 0, y: 0 },
                                 startPan: { x: 0, y: 0 },
                                 panStart: null });

  const clampZoom = (z) => Math.min(4, Math.max(0.4, z));

  const onMapWheel = (e) => {
    // Only ctrl-wheel zooms — preserves natural scroll otherwise.
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    const delta = -Math.sign(e.deltaY) * 0.12;
    setZoom((z) => clampZoom(z + delta));
  };

  const _touchDist = (a, b) => {
    const dx = a.clientX - b.clientX, dy = a.clientY - b.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };
  const _touchCenter = (a, b) => ({
    x: (a.clientX + b.clientX) / 2,
    y: (a.clientY + b.clientY) / 2,
  });

  const onMapTouchStart = (e) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      setPinching(true);
      const [a, b] = e.touches;
      gestureRef.current = {
        startDist: _touchDist(a, b),
        startZoom: zoom,
        startCenter: _touchCenter(a, b),
        startPan: { ...pan },
        panStart: null,
      };
    } else if (e.touches.length === 1) {
      gestureRef.current.panStart = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY,
        startPan: { ...pan },
      };
    }
  };

  const onMapTouchMove = (e) => {
    if (e.touches.length === 2 && pinching) {
      e.preventDefault();
      const [a, b] = e.touches;
      const dist = _touchDist(a, b);
      const center = _touchCenter(a, b);
      const g = gestureRef.current;
      if (g.startDist > 0) {
        const newZoom = clampZoom(g.startZoom * (dist / g.startDist));
        // Pan to follow the pinch midpoint so zoom feels anchored.
        setZoom(newZoom);
        setPan({
          x: g.startPan.x + (center.x - g.startCenter.x),
          y: g.startPan.y + (center.y - g.startCenter.y),
        });
      }
    }
    // Single-finger pan only when zoomed in (otherwise touches drive
    // the existing measure / move flow).
    else if (e.touches.length === 1 && zoom > 1.05 && gestureRef.current.panStart) {
      e.preventDefault();
      const ps = gestureRef.current.panStart;
      setPan({
        x: ps.startPan.x + (e.touches[0].clientX - ps.x),
        y: ps.startPan.y + (e.touches[0].clientY - ps.y),
      });
    }
  };

  const onMapTouchEnd = (e) => {
    if (e.touches.length < 2) setPinching(false);
    if (e.touches.length === 0) gestureRef.current.panStart = null;
  };

  // ─── load map + effects ───
  useEffect(() => {
    if (!sessionId) return;
    let mounted = true;
    Promise.all([
      api.get(`/sessions/${sessionId}/map`),
      api.get(`/sessions/${sessionId}/effects`).catch(() => ({ data: [] })),
    ]).then(([mapResp, effResp]) => {
      if (!mounted) return;
      setState(mapResp.data);
      setEffects(effResp.data || []);
    }).catch(() => {});
    return () => { mounted = false; };
  }, [sessionId]);

  // ─── P1 — vitals refresh ───
  // V6.25.48 added a 6s poll of GET /map/vitals.
  // V6.25.50 — backend now PUSHES `map:vitals` over the session WS
  // (channels.py BESM spend + advancement.py Anime 5E EP cast + undo
  // + rest restore). Polling becomes a 30s heartbeat so newly-joined
  // clients catch up without waiting on a mutation event, and so a
  // missed WS message can self-heal.
  useEffect(() => {
    if (!sessionId) return;
    let mounted = true;
    const tick = async () => {
      try {
        const { data } = await api.get(`/sessions/${sessionId}/map/vitals`);
        if (mounted) setVitals(data?.vitals || {});
      } catch { /* swallow — sidebar handles empty */ }
    };
    tick();
    const h = setInterval(tick, 30000);
    return () => { mounted = false; clearInterval(h); };
  }, [sessionId]);

  useEffect(() => {
    if (!subscribe) return;
    const off = subscribe((evt) => {
      if (!evt || !evt.type) return;
      const { type, data } = evt;
      if (type === "map:state") setState(data);
      else if (type === "map:token") {
        setState((s) => {
          if (!s) return s;
          const tokens = s.tokens.filter((t) => t.id !== data.id);
          return { ...s, tokens: [...tokens, data] };
        });
      }
      else if (type === "map:token-remove") {
        setState((s) => s ? { ...s, tokens: s.tokens.filter((t) => t.id !== data.id) } : s);
      }
      else if (type === "map:fog") {
        setState((s) => {
          if (!s) return s;
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
          if (!s) return s;
          let walls = s.walls;
          if (data.added) walls = [...walls, data.added];
          if (data.removed) walls = walls.filter((w) => w.id !== data.removed);
          return { ...s, walls };
        });
      }
      // Live effects → re-derive token status rings.
      else if (type === "effect") {
        setEffects((prev) => {
          const others = prev.filter((e) => e.id !== data.id);
          return [...others, data];
        });
      }
      else if (type === "effect_remove") {
        setEffects((prev) => prev.filter((e) => e.id !== data.id));
      }
      // V6.25.50 — push-based vitals update. Channel spend / damage
      // routes broadcast {[character_id]: {hp_pct, ep_pct, ...}} and
      // we merge into the local vitals map so token rings update
      // instantly without waiting for the next 30s poll.
      else if (type === "map:vitals") {
        setVitals((prev) => ({ ...(prev || {}), ...(data || {}) }));
      }
    });
    return () => { try { off && off(); } catch { /* */ } };
  }, [subscribe]);

  // Active uid (initiative top of order) → matching character → token highlight
  const activeUid = (initiative && initiative.length > 0)
    ? (initiative[0].character_id
        ? (characters.find((c) => c.id === initiative[0].character_id) || {}).owner_id
        : initiative[0].uid)
    : null;
  const activeCharIds = characters
    .filter((c) => c.owner_id === activeUid)
    .map((c) => c.id);

  // Map character_id → list of effect names so PeerTile rings reflect /effects.
  const effectsByCharacter = useMemo(() => {
    const map = {};
    for (const e of effects) {
      if (!e.active) continue;
      const cid = e.target_character_id;
      if (!cid) continue;
      (map[cid] = map[cid] || []).push(e.name || e.kind || "FX");
    }
    return map;
  }, [effects]);

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

  // ─── LINE-OF-SIGHT RAYCAST (V2) ───
  // Pure 2-segment intersection test — for each pair (origin, target) we
  // walk every wall and ask "does origin→target intersect this segment?"
  // If yes for any wall, the target is occluded. Origin = active actor's
  // token (initiative top of order); falls back to the player's own token.
  const segmentsIntersect = (p1, p2, p3, p4) => {
    const d = (p2.x - p1.x) * (p4.y - p3.y) - (p2.y - p1.y) * (p4.x - p3.x);
    if (Math.abs(d) < 1e-9) return false;
    const t = ((p3.x - p1.x) * (p4.y - p3.y) - (p3.y - p1.y) * (p4.x - p3.x)) / d;
    const u = ((p3.x - p1.x) * (p2.y - p1.y) - (p3.y - p1.y) * (p2.x - p1.x)) / d;
    return t > 0.001 && t < 0.999 && u > 0.001 && u < 0.999;
  };

  const losOriginToken = useMemo(() => {
    if (!state) return null;
    if (isGm) return null;  // GM sees everything; don't bother
    // Prefer the current active-actor token if it's mine; else my own
    // first owned token.
    const myCharIds = characters.filter((c) => c.owner_id === user?.id).map((c) => c.id);
    const own = state.tokens.find((t) => myCharIds.includes(t.character_id));
    return own || null;
  }, [state, characters, user?.id, isGm]);

  const isOccluded = useCallback((target) => {
    if (!losEnabled || isGm) return false;
    if (!losOriginToken || !state?.walls?.length) return false;
    if (target.id === losOriginToken.id) return false;
    const o = { x: losOriginToken.x, y: losOriginToken.y };
    const t = { x: target.x, y: target.y };
    for (const w of state.walls) {
      if (segmentsIntersect(o, t, { x: w.x1, y: w.y1 }, { x: w.x2, y: w.y2 })) {
        return true;
      }
    }
    return false;
  }, [losOriginToken, state, isGm, losEnabled]);

  // ─── canvas interaction ───
  const onMouseDown = (ev) => {
    if (!state) return;
    const cell = eventToCell(ev);
    // V6.25.48 — sidebar-driven placement takes precedence over other
    // modes. If the GM has armed a marker / PC spawn via the sidebar,
    // the next canvas click drops it and clears the pending intent.
    if (pendingPlacement && isGm) {
      const x = snapToGrid ? Math.round(cell.x * 2) / 2 : cell.x;
      const y = snapToGrid ? Math.round(cell.y * 2) / 2 : cell.y;
      const base = {
        x, y,
        size: 1,
        hp_pct: 100, ep_pct: 100,
        status: [],
        color: pendingPlacement.color || "#c8a34a",
        label: pendingPlacement.label || "",
        kind: pendingPlacement.kind,
        marker_type: pendingPlacement.marker_type || null,
        character_id: pendingPlacement.character_id || null,
        atlas_node_id: pendingPlacement.atlas_node_id || null,
        tooltip: pendingPlacement.tooltip || null,
      };
      sendToken(base);
      setPendingPlacement(null);
      return;
    }
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
    if (mode === "measure") {
      setMeasureStart(cell);
      setMeasureEnd(cell);
      return;
    }
    // select mode — find a token under the click
    const hit = [...state.tokens].reverse().find((t) => {
      const dx = cell.x - t.x, dy = cell.y - t.y;
      return Math.abs(dx) < t.size / 2 + 0.5 && Math.abs(dy) < t.size / 2 + 0.5;
    });
    if (hit && tokenIsMine(hit) && !hit.locked) {
      setDraggingId(hit.id);
      setDragPos({ x: hit.x, y: hit.y });
    }
  };
  const onMouseMove = (ev) => {
    if (!state) return;
    const cell = eventToCell(ev);
    if (measureStart) setMeasureEnd(cell);
    if (!draggingId) return;
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
    if (mode === "measure" && measureStart) {
      // Ruler is a transient overlay — releasing freezes the line for a
      // beat then clears on next mode change. Nothing networked.
      return;
    }
    if (draggingId && dragPos) {
      const t = state.tokens.find((x) => x.id === draggingId);
      if (t) {
        const nx = snapToGrid ? Math.round(dragPos.x * 2) / 2 : dragPos.x;
        const ny = snapToGrid ? Math.round(dragPos.y * 2) / 2 : dragPos.y;
        sendToken({ ...t, x: nx, y: ny });
      }
    }
    setDraggingId(null);
    setDragPos(null);
  };

  // Clear the ruler when leaving measure mode.
  useEffect(() => {
    if (mode !== "measure") { setMeasureStart(null); setMeasureEnd(null); }
  }, [mode]);

  // ─── GM controls ───
  // V4.4 — direct file upload (no more URL pasting). After a successful
  // upload we ALSO offer to auto-scale the grid to the image's pixel
  // dimensions assuming a target cell size in px (default 64) — that gets
  // most Inkarnate / DungeonCraft / Talespire / RPGEngine renders to a
  // playable grid in one click.
  const fileInputRef = useRef(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadErr, setUploadErr] = useState("");
  const setBgImageFromFile = async (file) => {
    setUploadErr("");
    if (!file) return;
    if (file.size > 12 * 1024 * 1024) {
      setUploadErr("Image exceeds 12 MB cap.");
      return;
    }
    const fd = new FormData();
    fd.append("file", file);
    setUploadBusy(true);
    try {
      const { data } = await api.post(`/uploads/map`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const apiBase = process.env.REACT_APP_BACKEND_URL || "";
      const fullUrl = data.url.startsWith("http") ? data.url : `${apiBase}${data.url}`;
      // Persist the URL on the map state.
      const next = {
        grid: state.grid,
        image: { ...state.image, url: fullUrl, fit: "contain" },
        tokens: state.tokens, walls: state.walls, fog: state.fog,
      };
      // If the upload reported pixel dimensions, offer auto-grid scaling so
      // GMs don't have to do the cell-size math themselves.
      if (data.width && data.height) {
        const cellPx = state.grid.size_px || 64;
        const cols = Math.max(4, Math.round(data.width / cellPx));
        const rows = Math.max(4, Math.round(data.height / cellPx));
        const fit = window.confirm(
          `Image is ${data.width}×${data.height}px.\n\n` +
          `Auto-scale grid to ${cols} × ${rows} cells at ${cellPx}px/cell?\n` +
          `(Cancel = keep current ${state.grid.cols}×${state.grid.rows} grid)`
        );
        if (fit) next.grid = { ...state.grid, cols, rows };
      }
      await api.put(`/sessions/${sessionId}/map`, next);
    } catch (e) {
      const detail = e?.response?.data?.detail || e.message;
      setUploadErr(typeof detail === "string" ? detail : "Upload failed.");
    } finally {
      setUploadBusy(false);
    }
  };
  const setBgImageUrl = async () => {
    // Legacy escape hatch — paste a public URL (Inkarnate share-link, etc.)
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
  // V4.4 — pixel size of each cell. Smaller cells = denser grid for the
  // same map image. Useful when scaling a high-DPI Inkarnate render down.
  const setCellSize = async () => {
    const px = parseInt(window.prompt(
      "Pixel size of each grid cell (12–256)?",
      state.grid.size_px || 48,
    ), 10);
    if (!px || px < 12 || px > 256) return;
    await api.put(`/sessions/${sessionId}/map`, {
      grid: { ...state.grid, size_px: px },
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
  // V6.9 — cycle a token's grid-size (1 → 2 → 3 → 4 → 1). Shift+right-click
  // on a token while in select mode. Token visuals are already cell-zoom
  // aware (size is a multiplier of grid_size_px), so this is the single
  // missing handle to grow/shrink a creature inline.
  const cycleTokenSize = async (t) => {
    const next = ((Math.round(t.size || 1) % 4) + 1);
    await sendToken({ ...t, size: next });
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

  // ─── V6.25.48 — sidebar callbacks ───
  // Arming a placement just sets state — the actual spawn happens on
  // the next canvas click in onMouseDown.
  const armPcSpawn = (character) => {
    if (!isGm) return;
    setMode("select");  // override any active fog/wall tool
    setPendingPlacement({
      kind: "pc",
      character_id: character.id,
      label: character.name,
      color: character.token_color || "#c8a34a",
      tooltip: null,
    });
  };
  const armAtlasSpawn = (pin) => {
    if (!isGm) return;
    setMode("select");
    const mt = pin?.fields?.location_type || "other";
    const palette = MARKER_ICONS[mt] ? mt : "note";
    setPendingPlacement({
      kind: "marker",
      marker_type: palette,
      atlas_node_id: pin.id,
      label: pin.title,
      color: MARKER_ICONS[palette]?.color || "#fbbf24",
      tooltip: pin.content || pin.fields?.description || null,
    });
  };
  const zoomIn = () => setZoom((z) => clampZoom(z + 0.25));
  const zoomOut = () => setZoom((z) => clampZoom(z - 0.25));
  const zoomReset = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  // ─── render ───
  if (stillUnrolling || !state) return (
    <div className="card-mystic p-10 text-mist text-sm flex flex-col items-center justify-center gap-3 min-h-[40vh]" data-testid="battlemap-loading">
      <div className="text-gold font-display tracking-[0.4em] text-sm animate-flicker">
        UNROLLING THE MAP
      </div>
      <div className="text-mist/60 text-[10px] font-ui uppercase tracking-[0.3em]">
        Pinning the corners · invoking the grid
      </div>
    </div>
  );

  const fogSet = new Set(state.fog.map((c) => `${c.x},${c.y}`));

  // Fullscreen-edit wrapper — desktop GM only when an editing tool is
  // selected. The wrapper takes over the viewport with a black backdrop
  // so the rest of the app fades out behind the map. ESC or the
  // Minimize button exits.
  const Wrap = ({ children }) => (
    fullscreenEdit && !isMobile ? (
      <div className="fixed inset-0 z-[60] bg-black flex flex-col p-3 md:p-5 overflow-auto"
           data-testid="battlemap-fullscreen">
        <div className="flex items-center justify-between mb-2 gap-2">
          <div className="text-[10px] font-ui uppercase tracking-[0.3em] text-gold/80">
            Fullscreen Editing · Mode: <span className="text-gold-bright">{mode}</span> · ESC to exit
          </div>
          <button onClick={() => setFullscreenEdit(false)}
                  className="btn btn-ghost text-xs"
                  data-testid="battlemap-fullscreen-exit"
                  title="Exit fullscreen edit (ESC)">
            <Minimize2 className="w-3.5 h-3.5"/> Exit
          </button>
        </div>
        <div className="flex-1 min-h-0">{children}</div>
      </div>
    ) : children
  );

  return (<Wrap>
    <div className="flex flex-col lg:flex-row gap-3 lg:items-stretch"
         data-testid="battlemap-shell">
    <div className="card-mystic p-3 md:p-4 flex flex-col flex-1 min-w-0" data-testid="battlemap" data-mode={mode} data-mobile={isMobile ? "1" : "0"} data-pending-placement={pendingPlacement ? pendingPlacement.kind : ""}>
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
          {isGm && !isMobile && (
            <button onClick={() => setMode("fog")}
                    className={`btn ${mode === "fog" ? "btn-primary" : "btn-ghost"} text-xs px-2`}
                    data-testid="map-mode-fog" title="Paint fog (shift-click to reveal)">
              <Eye className="w-3.5 h-3.5"/>
            </button>
          )}
          {isGm && !isMobile && (
            <button onClick={() => setMode("wall")}
                    className={`btn ${mode === "wall" ? "btn-primary" : "btn-ghost"} text-xs px-2`}
                    data-testid="map-mode-wall" title="Draw wall segment">
              <Hammer className="w-3.5 h-3.5"/>
            </button>
          )}
          <button onClick={() => setMode("measure")}
                  className={`btn ${mode === "measure" ? "btn-primary" : "btn-ghost"} text-xs px-2`}
                  data-testid="map-mode-measure" title="Measure distance">
            <Ruler className="w-3.5 h-3.5"/>
          </button>
          {!isGm && (
            <button onClick={() => setLosEnabled((v) => !v)}
                    className={`btn btn-ghost text-xs px-2 ${losEnabled ? "border-arcane/60 text-arcane-light" : ""}`}
                    data-testid="map-los-toggle"
                    title={losEnabled ? "Line-of-sight: ON (walls hide tokens)" : "Line-of-sight: OFF (see all)"}>
              <Sparkles className="w-3.5 h-3.5"/>
            </button>
          )}
          {/* Desktop GM only — manual fullscreen toggle for the map. */}
          {isGm && !isMobile && (
            <button onClick={() => setFullscreenEdit((v) => !v)}
                    className={`btn btn-ghost text-xs px-2 ${fullscreenEdit ? "border-gold text-gold-bright" : ""}`}
                    data-testid="map-fullscreen-toggle"
                    title={fullscreenEdit ? "Exit fullscreen (ESC)" : "Fullscreen edit"}>
              {fullscreenEdit ? <Minimize2 className="w-3.5 h-3.5"/> : <Maximize2 className="w-3.5 h-3.5"/>}
            </button>
          )}
          {onClose && (
            <button onClick={onClose} className="btn btn-ghost text-xs px-2" data-testid="map-close" title="Close map">
              <X className="w-3.5 h-3.5"/>
            </button>
          )}
        </div>
      </div>

      {isGm && !isMobile && (
        <div className="flex flex-wrap gap-1.5 mb-2 text-[10px]" data-testid="map-gm-tools">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            data-testid="map-bg-file-input"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) setBgImageFromFile(f);
              e.target.value = "";  // allow re-uploading same file
            }}
          />
          <button onClick={() => fileInputRef.current?.click()}
                  disabled={uploadBusy}
                  className="btn btn-ghost text-[10px]" data-testid="map-bg-upload-btn"
                  title="Upload a PNG/JPEG/WEBP map image (≤32 MB · 2K-quality friendly)">
            <ImageIcon className="w-3 h-3"/> {uploadBusy ? "Uploading…" : "Upload Map"}
          </button>
          <button onClick={setBgImageUrl} className="btn btn-ghost text-[10px]" data-testid="map-bg-url-btn"
                  title="Paste a public image URL (Inkarnate share-link, etc.)">
            URL
          </button>
          <button onClick={setGrid} className="btn btn-ghost text-[10px]" data-testid="map-grid-btn">
            <MapIcon className="w-3 h-3"/> Grid · {state.grid.cols}×{state.grid.rows}
          </button>
          <button onClick={setCellSize} className="btn btn-ghost text-[10px]" data-testid="map-cell-btn"
                  title="Pixel size of each grid cell (default 48)">
            ⊞ {state.grid.size_px}px
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
          {uploadErr && (
            <span className="text-ember text-[10px] font-ui ml-2" data-testid="map-upload-err">{uploadErr}</span>
          )}
        </div>
      )}

      {/* Mobile = view-only banner. GMs need to prep on desktop. */}
      {isMobile && (
        <div className="mb-2 px-3 py-2 rounded-sm border border-arcane/40 bg-arcane/10 text-[10px] font-ui uppercase tracking-widest text-arcane-light"
             data-testid="map-mobile-viewonly-banner">
          Map is view-only on mobile. GMs prep walls / fog / tokens on desktop.
        </div>
      )}

      {/* V6.25.48 — pending placement banner */}
      {pendingPlacement && isGm && (
        <div className="mb-2 px-3 py-1.5 rounded-sm border border-gold/60 bg-gold/10 text-[10px] font-ui uppercase tracking-widest text-gold-bright flex items-center justify-between gap-2"
             data-testid="battlemap-placement-banner">
          <span>Click canvas to drop · {pendingPlacement.label}</span>
          <button type="button" onClick={() => setPendingPlacement(null)}
                  className="btn btn-ghost text-[10px] px-2 py-0 ml-3"
                  data-testid="battlemap-placement-cancel">
            cancel
          </button>
        </div>
      )}

      {/* Canvas
          V6.25.6 mobile sweep — pinch-zoom + 2-finger pan support via
          a CSS transform on the inner content stack. Wheel zoom on
          desktop too (Ctrl+wheel) so the same gesture works for
          trackpad users. State stays local (no save) — the map's grid
          + walls / tokens are still authored at native scale; this
          transform is a player-side viewport pan/zoom only. */}
      <div
        ref={canvasRef}
        className="relative w-full overflow-hidden border border-gold/30 bg-black/80 select-none cursor-crosshair"
        style={{
          aspectRatio: `${W} / ${H}`,
          // Fullscreen-edit OR mobile (view-only) → cap height to viewport so
          // the map "fits to screen" on first paint without scrolling.
          maxHeight: fullscreenEdit ? "calc(100vh - 90px)"
                   : isMobile ? "calc(100vh - 220px)"
                   : "75vh",
          margin: "0 auto",
          // Disable browser-native pinch-zoom (we own the gesture) +
          // disallow text selection on touch.
          touchAction: "none",
        }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onMapWheel}
        onTouchStart={onMapTouchStart}
        onTouchMove={onMapTouchMove}
        onTouchEnd={onMapTouchEnd}
        data-testid="battlemap-canvas"
      >
        {/* Pan / zoom transform stack — only applies to children. */}
        <div
          className="absolute inset-0"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "0 0",
            transition: pinching ? "none" : "transform 60ms linear",
          }}
        >
        {/* Background image */}
        {state.image?.url && (
          <img
            src={state.image.url}
            alt=""
            draggable={false}
            className="absolute inset-0 w-full h-full pointer-events-none"
            // Default to 'contain' so the whole map fits-to-screen on
            // first paint instead of being cropped.
            style={{ objectFit: state.image.fit || "contain" }}
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
          {/* Wall preview while dragging */}
          {wallStart && measureEnd === null && (
            <line x1={wallStart.x * cellSize} y1={wallStart.y * cellSize}
                  x2={(dragPos?.x ?? wallStart.x) * cellSize}
                  y2={(dragPos?.y ?? wallStart.y) * cellSize}
                  stroke="#c8a34a" strokeWidth="2" strokeDasharray="6,3"
                  opacity="0.6"/>
          )}
          {/* Measure ruler */}
          {measureStart && measureEnd && (() => {
            const dx = measureEnd.x - measureStart.x;
            const dy = measureEnd.y - measureStart.y;
            // Chebyshev distance (D&D-style — diagonals count 1) plus metric
            const cells = Math.round(Math.max(Math.abs(dx), Math.abs(dy)) * 10) / 10;
            const metres = cells * 2;  // BESM-friendly default scale: 2m / cell
            const midX = (measureStart.x + measureEnd.x) / 2 * cellSize;
            const midY = (measureStart.y + measureEnd.y) / 2 * cellSize;
            return (
              <g data-testid="map-measure-ruler">
                <line x1={measureStart.x * cellSize} y1={measureStart.y * cellSize}
                      x2={measureEnd.x * cellSize} y2={measureEnd.y * cellSize}
                      stroke="#f1d775" strokeWidth="2" strokeDasharray="4,2"/>
                <circle cx={measureStart.x * cellSize} cy={measureStart.y * cellSize}
                        r="4" fill="#f1d775"/>
                <circle cx={measureEnd.x * cellSize} cy={measureEnd.y * cellSize}
                        r="4" fill="#f1d775"/>
                <rect x={midX - 38} y={midY - 14} width="76" height="22"
                      rx="2" fill="rgba(7,6,10,0.8)" stroke="#f1d775"/>
                <text x={midX} y={midY + 1} fontSize="11" textAnchor="middle"
                      fill="#f1d775" fontFamily="ui-monospace, Menlo, monospace">
                  {cells} cell{cells === 1 ? "" : "s"} · {metres}m
                </text>
              </g>
            );
          })()}
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
          // V2: live status rings driven by /api/effects (target_character_id)
          const liveStatus = (t.character_id && effectsByCharacter[t.character_id]) || [];
          const allStatus = [...(t.status || []), ...liveStatus].slice(0, 4);
          // V2: line-of-sight occlusion — players don't see tokens behind walls.
          // Markers are never LoS-occluded (treasure under a wall is still
          // a treasure; GMs use fog if they want it hidden).
          const occluded = t.kind === "marker" ? false : isOccluded(t);
          if (occluded) return null;
          // V6.25.48 — live HP/EP from /vitals overrides static token values.
          // Falls back to whatever's stored on the token (so unseated NPCs
          // still render at their last persisted hp_pct).
          const liveVitals = t.character_id ? (vitals[t.character_id] || null) : null;
          const hpPct = Math.max(0, Math.min(100, liveVitals?.hp_pct ?? t.hp_pct ?? 100));
          const epPct = Math.max(0, Math.min(100, liveVitals?.ep_pct ?? t.ep_pct ?? 100));
          const isMarker = t.kind === "marker";
          const Marker = isMarker ? MARKER_ICONS[t.marker_type]?.Icon : null;
          // Rich hover tooltip: name, system vitals, atlas link, status.
          const tip = isMarker
            ? `${MARKER_ICONS[t.marker_type]?.label || "Marker"}: ${t.label || ""}`
              + (t.tooltip ? ` — ${t.tooltip}` : "")
            : `${t.label || ch?.name || ""}`
              + (liveVitals ? ` · HP ${liveVitals.hp_current}/${liveVitals.hp_max} · EP ${liveVitals.ep_current}/${liveVitals.ep_max}` : "")
              + (isActive ? " · ACTIVE" : "")
              + (liveStatus.length ? " · " + liveStatus.join(", ") : "");
          return (
            <button
              key={t.id}
              type="button"
              onContextMenu={isGm ? (e) => {
                e.preventDefault();
                if (e.shiftKey) {
                  cycleTokenSize(t);
                } else {
                  removeToken(t.id);
                }
              } : undefined}
              className={`absolute rounded-full border-2 flex items-center justify-center font-display text-base shadow-[0_2px_8px_rgba(0,0,0,0.6)]
                ${isActive ? "ring-2 ring-gold ring-offset-1 ring-offset-black animate-pulse" : ""}
                ${tokenIsMine(t) && !t.locked ? "cursor-grab active:cursor-grabbing" : "cursor-not-allowed"}`}
              style={{
                left: `calc(${px}% - ${sizePct / 2}%)`,
                top: `calc(${py}% - ${sizePct / 2}%)`,
                width: `${sizePct}%`,
                aspectRatio: "1 / 1",
                background: isMarker ? `${t.color || "#fbbf24"}33` : `${t.color || "#c8a34a"}cc`,
                borderColor: t.color || (isMarker ? "#fbbf24" : "#c8a34a"),
                color: "#0a0810",
                zIndex: isDragging ? 30 : 10,
              }}
              data-testid={`map-token-${t.id}`}
              data-token-kind={t.kind || "pc"}
              data-active={isActive ? "true" : "false"}
              aria-label={tip}
              title={tip + (isGm ? "  ·  right-click: remove · shift+right-click: cycle size" : "")}
            >
              {/* Marker = lucide icon; PC = initial letter */}
              {isMarker && Marker
                ? <Marker className="w-3/5 h-3/5" style={{ color: t.color || "#fbbf24" }}/>
                : initials}

              {/* V6.25.48 — invisible-when-full HP / EP arcs.
                  Rendered only when there's something to show. The
                  arcs sit around the token border without crowding
                  the centre; subtle by default, vivid as they
                  deplete. PC tokens only — markers don't have vitals. */}
              {!isMarker && (hpPct < 100 || epPct < 100) && (
                <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible"
                     viewBox="0 0 100 100" aria-hidden="true">
                  {/* HP arc — red, top half, sweeps clockwise as HP drops */}
                  {hpPct < 100 && (
                    <circle cx="50" cy="50" r="48" fill="none"
                            stroke="#f87171"
                            strokeWidth="4"
                            strokeOpacity={hpPct < 33 ? 0.95 : hpPct < 66 ? 0.7 : 0.45}
                            strokeDasharray={`${(hpPct / 100) * 150.8} 301.6`}
                            strokeDashoffset="-75.4"
                            transform="rotate(-90 50 50)"
                            data-testid={`map-token-${t.id}-hp-arc`}/>
                  )}
                  {/* EP arc — cyan, bottom half */}
                  {epPct < 100 && (
                    <circle cx="50" cy="50" r="48" fill="none"
                            stroke="#67e8f9"
                            strokeWidth="4"
                            strokeOpacity={epPct < 33 ? 0.9 : 0.55}
                            strokeDasharray={`${(epPct / 100) * 150.8} 301.6`}
                            strokeDashoffset="75.4"
                            transform="rotate(90 50 50)"
                            data-testid={`map-token-${t.id}-ep-arc`}/>
                  )}
                </svg>
              )}

              {/* Initiative-order dot — tiny gold pip at top of token
                  when initiative_order is set. Active-actor pulse
                  (the ring above) already conveys whose turn it is;
                  this is a secondary always-visible badge for queue
                  awareness. */}
              {t.initiative_order != null && t.initiative_order >= 0 && (
                <span className="absolute -top-2 -left-2 px-1 text-[8px] rounded-full
                                bg-gold text-void font-display border border-gold-bright shadow"
                      data-testid={`map-token-${t.id}-init`}>
                  {t.initiative_order}
                </span>
              )}

              {/* Status rings — manual + live effects */}
              {allStatus.map((s, i) => (
                <span key={`${s}-${i}`}
                      className={`absolute -top-1 -right-1 px-1 py-[1px] text-[8px] uppercase
                                 tracking-widest rounded-sm border
                                 ${i < (t.status || []).length
                                   ? "bg-arcane text-parchment border-arcane"
                                   : "bg-ember/90 text-parchment border-ember"}`}
                      style={{ transform: `translateY(${i * 10}px)` }}
                      data-testid={`map-token-${t.id}-status-${i}`}>
                  {s}
                </span>
              ))}
            </button>
          );
        })}
        </div>
        {/* /transform stack */}
      </div>

      <div className="text-[10px] font-ui uppercase tracking-widest text-mist/60 mt-2">
        {isMobile
          ? `View-only on mobile. ${losEnabled ? "Walls block your line of sight." : ""}`
          : isGm
            ? "GM · select to move tokens · fog: click hide / shift-click reveal · wall: click+drag · ruler: click+drag · right-click token to remove · shift+right-click to cycle size"
            : `Drag tokens you own. Gold ring = active turn. ${losEnabled ? "Walls block your line of sight." : "Line-of-sight off — seeing all."}`}
      </div>
    </div>
      {!isMobile && (
        <BattlemapSidebar
          isGm={isGm}
          isMobile={isMobile}
          characters={characters}
          tokens={state.tokens}
          vitals={vitals}
          pendingPlacement={pendingPlacement}
          onSetPendingPlacement={setPendingPlacement}
          onSpawnPc={armPcSpawn}
          onSpawnMarker={(mt) => setPendingPlacement({
            kind: "marker", marker_type: mt,
            color: MARKER_ICONS[mt]?.color, label: MARKER_ICONS[mt]?.label,
          })}
          onSpawnAtlasPin={armAtlasSpawn}
          snapToGrid={snapToGrid}
          onToggleSnap={() => setSnapToGrid((v) => !v)}
          zoom={zoom}
          onZoomIn={zoomIn}
          onZoomOut={zoomOut}
          onZoomReset={zoomReset}
          campaignId={campaign?.id}
          systemId={campaign?.system_id}
          sessionId={sessionId}
        />
      )}
    </div>
  </Wrap>);
}
