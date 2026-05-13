/**
 * V6.25.48 — Battlemap right sidebar.
 *
 * Sections (top-down):
 *   1. View controls         — snap-to-grid toggle, zoom in/out/reset.
 *   2. PC roster             — click-to-spawn round tokens (once per
 *                              session, persistent). Each row shows
 *                              the live HP/EP percentage from /vitals.
 *   3. Marker palette        — 8 curated map icons: door, trap,
 *                              treasure, chest, stairs, portal,
 *                              ladder, note. Click one to enter
 *                              "place-marker" mode; next canvas click
 *                              drops the marker.
 *   4. Atlas-pin spawner     — list of pinned locations from the
 *                              campaign atlas (P2). Click to spawn a
 *                              marker linked back to the codex node.
 *   5. Legend                — colour swatches: PC / NPC / marker /
 *                              active actor / occluded. So new
 *                              players immediately read the canvas.
 *
 * Only the canvas + token interaction belong to <Battlemap />. The
 * sidebar is purely declarative — it just reports the user's intent
 * to spawn/place via callbacks; the parent owns the side-effects.
 */
import React, { useEffect, useState, useMemo } from "react";
import {
  Plus, ZoomIn, ZoomOut, Crosshair, Magnet, MapPin,
  DoorOpen, Skull, Gem, Box, ArrowUpDown, Sparkle, Footprints, StickyNote,
} from "lucide-react";
import { api } from "../lib/api";

export const MARKER_ICONS = {
  door:      { Icon: DoorOpen,    color: "#a3e635", label: "Door" },
  trap:      { Icon: Skull,       color: "#f87171", label: "Trap" },
  treasure:  { Icon: Gem,         color: "#fbbf24", label: "Treasure" },
  chest:     { Icon: Box,         color: "#d97706", label: "Chest" },
  stairs:    { Icon: ArrowUpDown, color: "#94a3b8", label: "Stairs" },
  portal:    { Icon: Sparkle,     color: "#c084fc", label: "Portal" },
  ladder:    { Icon: Footprints,  color: "#a8a29e", label: "Ladder" },
  note:      { Icon: StickyNote,  color: "#fde047", label: "Note" },
};

export default function BattlemapSidebar({
  isGm, isMobile, characters = [], tokens = [], vitals = {},
  pendingPlacement, onSetPendingPlacement,
  onSpawnPc, onSpawnMarker, onSpawnAtlasPin,
  snapToGrid, onToggleSnap,
  zoom, onZoomIn, onZoomOut, onZoomReset,
  campaignId,
}) {
  const [atlasPins, setAtlasPins] = useState([]);
  const [atlasLoaded, setAtlasLoaded] = useState(false);

  // Lazy-load atlas pins once. Keep silent on permission errors —
  // sidebar still works without atlas access.
  useEffect(() => {
    if (!campaignId || atlasLoaded) return;
    api.get(`/writer/atlas/${campaignId}`)
      .then((r) => {
        setAtlasPins(r.data?.pins || []);
        setAtlasLoaded(true);
      })
      .catch(() => { setAtlasLoaded(true); });
  }, [campaignId, atlasLoaded]);

  const spawnedCharIds = useMemo(
    () => new Set(tokens.filter((t) => t.kind !== "marker" && t.character_id)
                        .map((t) => t.character_id)),
    [tokens],
  );
  const spawnedAtlasIds = useMemo(
    () => new Set(tokens.filter((t) => t.atlas_node_id).map((t) => t.atlas_node_id)),
    [tokens],
  );

  // Roster: published PCs first, then NPCs. Hide unpublished from
  // players (they shouldn't see hidden NPCs they don't own).
  const roster = useMemo(() => {
    return (characters || [])
      .filter((c) => c.published || isGm)
      .slice()
      .sort((a, b) => (a.name || "").localeCompare(b.name || ""));
  }, [characters, isGm]);

  return (
    <aside className="card-mystic p-3 w-full lg:w-72 lg:max-w-72 lg:min-w-72 flex flex-col gap-3 text-xs"
           data-testid="battlemap-sidebar">
      {/* ── 1. View controls ── */}
      <section data-testid="battlemap-sidebar-view-controls">
        <div className="label-ref text-[10px] uppercase tracking-widest text-mist/70 mb-1">
          View
        </div>
        <div className="flex items-center gap-1.5">
          <button type="button" onClick={onToggleSnap}
                  className={`btn btn-ghost text-[10px] flex-1 ${snapToGrid ? "border-gold/60 text-gold-bright" : ""}`}
                  data-testid="battlemap-snap-toggle"
                  title={snapToGrid ? "Snap-to-grid ON (drag rounds to half-cell)"
                                    : "Snap-to-grid OFF (free placement)"}>
            <Magnet className="w-3 h-3"/> Snap
          </button>
          <button type="button" onClick={onZoomOut}
                  className="btn btn-ghost text-[10px] px-2"
                  data-testid="battlemap-zoom-out" title="Zoom out">
            <ZoomOut className="w-3 h-3"/>
          </button>
          <button type="button" onClick={onZoomReset}
                  className="btn btn-ghost text-[10px] px-2"
                  data-testid="battlemap-zoom-reset" title="Reset zoom"
                  aria-label={`Reset zoom (current ${(zoom * 100).toFixed(0)}%)`}>
            <Crosshair className="w-3 h-3"/>
          </button>
          <button type="button" onClick={onZoomIn}
                  className="btn btn-ghost text-[10px] px-2"
                  data-testid="battlemap-zoom-in" title="Zoom in">
            <ZoomIn className="w-3 h-3"/>
          </button>
        </div>
        <div className="text-[9px] text-mist/50 text-right mt-1 font-ui tracking-widest"
             data-testid="battlemap-zoom-readout">
          {(zoom * 100).toFixed(0)}%
        </div>
      </section>

      {/* ── 2. PC roster ── */}
      <section data-testid="battlemap-sidebar-pc-roster">
        <div className="label-ref text-[10px] uppercase tracking-widest text-mist/70 mb-1 flex justify-between">
          <span>Roster ({roster.length})</span>
          <span className="text-mist/40">click + to spawn</span>
        </div>
        <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
          {roster.length === 0 && (
            <div className="text-[10px] text-mist/40 italic"
                 data-testid="battlemap-roster-empty">
              No characters in this campaign yet.
            </div>
          )}
          {roster.map((c) => {
            const alreadyOnMap = spawnedCharIds.has(c.id);
            const v = vitals[c.id];
            const hp = v?.hp_pct ?? 100;
            const ep = v?.ep_pct ?? 100;
            return (
              <div key={c.id}
                   className={`flex items-center gap-2 px-2 py-1 rounded-sm border
                              ${alreadyOnMap ? "border-gold/20 bg-gold/5" : "border-mist/10 hover:border-gold/30"}`}
                   data-testid={`battlemap-roster-row-${c.id}`}>
                <span className="w-5 h-5 rounded-full flex items-center justify-center font-display text-[10px] shrink-0"
                      style={{ background: `${c.token_color || "#c8a34a"}cc`,
                               color: "#0a0810", border: `1px solid ${c.token_color || "#c8a34a"}` }}>
                  {(c.name || "?").charAt(0).toUpperCase()}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] text-parchment truncate"
                       title={c.name}>{c.name}</div>
                  {v ? (
                    <div className="flex gap-1 text-[8px] font-ui text-mist/60 tracking-wider"
                         data-testid={`battlemap-roster-vitals-${c.id}`}>
                      <span className="text-ember/90">HP {hp}%</span>
                      <span className="text-cyan-300/80">EP {ep}%</span>
                    </div>
                  ) : (
                    <div className="text-[8px] text-mist/30 italic">vitals…</div>
                  )}
                </div>
                {isGm && (
                  <button type="button"
                          onClick={() => onSpawnPc(c)}
                          disabled={alreadyOnMap}
                          className={`btn ${alreadyOnMap ? "btn-ghost opacity-40 cursor-not-allowed" : "btn-primary"} text-[10px] px-2 py-0.5`}
                          data-testid={`battlemap-spawn-pc-${c.id}`}
                          title={alreadyOnMap ? "Already on the map" : "Click then click on canvas to drop"}>
                    {alreadyOnMap ? "✓" : <Plus className="w-3 h-3"/>}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ── 3. Marker palette (GM only) ── */}
      {isGm && (
        <section data-testid="battlemap-sidebar-marker-palette">
          <div className="label-ref text-[10px] uppercase tracking-widest text-mist/70 mb-1 flex justify-between">
            <span>Markers</span>
            {pendingPlacement && (
              <span className="text-gold-bright animate-pulse"
                    data-testid="battlemap-pending-placement">
                Click canvas to drop {pendingPlacement.label}
              </span>
            )}
          </div>
          <div className="grid grid-cols-4 gap-1">
            {Object.entries(MARKER_ICONS).map(([key, { Icon, color, label }]) => {
              const active = pendingPlacement?.kind === "marker"
                          && pendingPlacement?.marker_type === key;
              return (
                <button type="button"
                        key={key}
                        onClick={() => onSetPendingPlacement(
                          active ? null : { kind: "marker", marker_type: key, color, label }
                        )}
                        className={`p-1.5 rounded-sm border flex flex-col items-center gap-0.5
                                   ${active ? "border-gold bg-gold/10"
                                            : "border-mist/15 hover:border-gold/40"}`}
                        title={label}
                        data-testid={`battlemap-marker-${key}`}>
                  <Icon className="w-4 h-4" style={{ color }}/>
                  <span className="text-[8px] text-mist/70">{label}</span>
                </button>
              );
            })}
          </div>
        </section>
      )}

      {/* ── 4. Atlas pins (P2) ── */}
      {isGm && atlasPins.length > 0 && (
        <section data-testid="battlemap-sidebar-atlas-pins">
          <div className="label-ref text-[10px] uppercase tracking-widest text-mist/70 mb-1">
            From Atlas ({atlasPins.length})
          </div>
          <div className="space-y-0.5 max-h-32 overflow-y-auto pr-1">
            {atlasPins.map((p) => {
              const linked = spawnedAtlasIds.has(p.id);
              const t = p.fields?.location_type || "other";
              return (
                <button key={p.id}
                        type="button"
                        onClick={() => onSpawnAtlasPin(p)}
                        disabled={linked}
                        className={`w-full text-left text-[10px] px-2 py-1 rounded-sm border flex items-center gap-2
                                   ${linked ? "border-gold/20 bg-gold/5 cursor-not-allowed opacity-60"
                                            : "border-mist/10 hover:border-gold/40"}`}
                        data-testid={`battlemap-atlas-spawn-${p.id}`}
                        title={linked ? "Already placed on this map"
                                      : "Click to drop a linked marker, then click on canvas"}>
                  <MapPin className="w-3 h-3 shrink-0" style={{ color: "#fbbf24" }}/>
                  <span className="flex-1 truncate text-gold-bright">{p.title}</span>
                  <span className="text-[8px] text-mist/40 capitalize">{t}</span>
                </button>
              );
            })}
          </div>
        </section>
      )}

      {/* ── 5. Legend ── */}
      <section data-testid="battlemap-sidebar-legend" className="mt-auto pt-2 border-t border-mist/10">
        <div className="label-ref text-[10px] uppercase tracking-widest text-mist/70 mb-1">
          Legend
        </div>
        <div className="grid grid-cols-1 gap-0.5 text-[10px] text-mist/80">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full border-2"
                  style={{ background: "#c8a34acc", borderColor: "#c8a34a" }}/>
            <span>Player token</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full border-2 ring-1 ring-gold animate-pulse"
                  style={{ background: "#c8a34acc", borderColor: "#c8a34a" }}/>
            <span>Active turn</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-1 rounded-full" style={{ background: "#f87171" }}/>
            <span>HP ring · low = red arc</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-1 rounded-full" style={{ background: "#67e8f9" }}/>
            <span>EP ring · cyan arc</span>
          </div>
          <div className="flex items-center gap-2">
            <Gem className="w-3 h-3 text-yellow-400"/>
            <span>Marker · GM-placed</span>
          </div>
        </div>
      </section>
    </aside>
  );
}
