/**
 * V6.25.46 — Worldbuilder Atlas: real authoring tool (replaces scaffold).
 *
 * Workflow:
 *   1. GM provides a world-map image URL (PNG/JPG/SVG). Stored on
 *      `campaign.world_map_url`.
 *   2. Click anywhere on the map to drop a new pin → opens a quick
 *      sheet that creates a fresh `location` codex node anchored at
 *      that x/y (0..1 normalised).
 *   3. Drag an existing un-pinned location from the right panel onto
 *      the map to attach coords to it.
 *   4. Hover a pin → label + location_type chip. Click → opens the
 *      node card for editing.
 *
 * The atlas IS the codex location layer. Same data, two views.
 *
 * Backend: GET/PATCH /api/writer/atlas/{cid}, POST /pins, DELETE /pins/{id}.
 */
import React, { useEffect, useRef, useState } from "react";
import { MapPin, Trash2, Save, X, Image as ImageIcon, Pin } from "lucide-react";
import { api } from "../../lib/api";

const TYPE_PALETTE = {
  city:        "#fbbf24",  town:        "#f59e0b",  village:    "#d97706",
  tavern:      "#a3e635",  keep:        "#94a3b8",  ruin:       "#94a3b8",
  forest:      "#22c55e",  road:        "#a8a29e",  chamber:    "#c084fc",
  mountain:    "#78716c",  waterway:    "#06b6d4",  shrine:     "#fde047",
  battlefield: "#f87171",  other:       "#9ca3af",
};

export default function WbAtlasTool({ campId }) {
  const [data, setData] = useState(null);
  const [mapUrlDraft, setMapUrlDraft] = useState("");
  const [mapCaptionDraft, setMapCaptionDraft] = useState("");
  const [pinDraft, setPinDraft] = useState(null);    // {x, y} when creating
  const [hoverPin, setHoverPin] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const imgRef = useRef(null);

  const refresh = async () => {
    try {
      const r = await api.get(`/writer/atlas/${campId}`);
      setData(r.data);
      setMapUrlDraft(r.data?.world_map_url || "");
      setMapCaptionDraft(r.data?.world_map_caption || "");
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load atlas.");
    }
  };
  useEffect(() => { if (campId) refresh(); }, [campId]);

  const saveMap = async () => {
    setBusy(true); setErr("");
    try {
      await api.patch(`/writer/atlas/${campId}/map`, {
        world_map_url: mapUrlDraft.trim() || null,
        world_map_caption: mapCaptionDraft.trim() || null,
      });
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to save map.");
    } finally { setBusy(false); }
  };

  const onMapClick = (e) => {
    if (!data?.writable || !data?.world_map_url) return;
    const r = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width;
    const y = (e.clientY - r.top) / r.height;
    setPinDraft({ x, y, title: "", description: "", location_type: "other" });
  };

  const submitPin = async () => {
    if (!pinDraft) return;
    if (!pinDraft.title.trim()) { setErr("Pin needs a title."); return; }
    setBusy(true); setErr("");
    try {
      await api.post(`/writer/atlas/${campId}/pins`, {
        title: pinDraft.title.trim(),
        description: pinDraft.description.trim() || null,
        map_x: pinDraft.x, map_y: pinDraft.y,
        location_type: pinDraft.location_type,
      });
      setPinDraft(null);
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to drop pin.");
    } finally { setBusy(false); }
  };

  const attachExisting = async (node) => {
    if (!pinDraft) return;
    setBusy(true); setErr("");
    try {
      await api.post(`/writer/atlas/${campId}/pins`, {
        node_id: node.id,
        title: node.title,
        map_x: pinDraft.x, map_y: pinDraft.y,
      });
      setPinDraft(null);
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to attach.");
    } finally { setBusy(false); }
  };

  const unpin = async (nodeId) => {
    if (!confirm("Remove this pin from the map? The codex node stays.")) return;
    setBusy(true); setErr("");
    try {
      await api.delete(`/writer/atlas/${campId}/pins/${nodeId}`);
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to unpin.");
    } finally { setBusy(false); }
  };

  if (!data) return <div className="p-6 text-mist italic" data-testid="wb-atlas-loading">Summoning atlas…</div>;

  return (
    <div className="p-4 grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4"
         data-testid="wb-atlas-page">
      <div>
        {/* Map URL editor */}
        <div className="card-mystic p-3 mb-3 border-emerald-700/30">
          <div className="flex items-center gap-2 mb-2">
            <ImageIcon className="w-4 h-4 text-emerald-300"/>
            <span className="label-ref text-emerald-300">World map source</span>
          </div>
          {data.writable ? (
            <div className="space-y-2">
              <input type="url" value={mapUrlDraft}
                     onChange={(e) => setMapUrlDraft(e.target.value)}
                     placeholder="Paste a public image URL (PNG/JPG/SVG)…"
                     className="input text-xs w-full"
                     data-testid="wb-atlas-map-url"/>
              <input type="text" value={mapCaptionDraft}
                     onChange={(e) => setMapCaptionDraft(e.target.value)}
                     placeholder="Caption / scale note (optional)"
                     className="input text-xs w-full"
                     data-testid="wb-atlas-map-caption"
                     maxLength={400}/>
              <div className="flex justify-end">
                <button type="button" onClick={saveMap} disabled={busy}
                        className="btn btn-primary text-xs"
                        data-testid="wb-atlas-map-save">
                  <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save map"}
                </button>
              </div>
            </div>
          ) : (
            <div className="text-[11px] text-mist/70 italic">
              Read-only. Ask your GM/worldbuilder to set a map URL.
            </div>
          )}
        </div>

        {/* Map canvas with pins */}
        {data.world_map_url ? (
          <div className="relative card-mystic p-0 overflow-hidden border-emerald-700/30"
               data-testid="wb-atlas-canvas">
            <img ref={imgRef} src={data.world_map_url} alt="World map"
                 onClick={onMapClick}
                 className={`w-full h-auto block ${data.writable ? "cursor-crosshair" : ""}`}
                 onError={() => setErr("Map image failed to load — bad URL?")}
                 data-testid="wb-atlas-map-img"/>
            {/* Existing pins */}
            {(data.pins || []).map((p) => {
              const x = p.fields?.map_x;
              const y = p.fields?.map_y;
              const type = p.fields?.location_type || "other";
              const color = TYPE_PALETTE[type] || TYPE_PALETTE.other;
              if (x == null || y == null) return null;
              return (
                <div key={p.id}
                     className="absolute -translate-x-1/2 -translate-y-full group"
                     style={{ left: `${x * 100}%`, top: `${y * 100}%` }}
                     onMouseEnter={() => setHoverPin(p.id)}
                     onMouseLeave={() => setHoverPin(null)}
                     data-testid={`wb-atlas-pin-${p.id}`}>
                  <MapPin className="w-6 h-6 drop-shadow-md"
                          style={{ color }}/>
                  {hoverPin === p.id && (
                    <div className="absolute left-1/2 -translate-x-1/2 -top-2 -translate-y-full
                                    bg-void/95 border border-gold/30 rounded-sm px-2 py-1
                                    min-w-[180px] text-[11px] z-10 pointer-events-auto"
                         data-testid={`wb-atlas-pin-tooltip-${p.id}`}>
                      <div className="text-gold-bright font-ui">{p.title}</div>
                      <div className="text-mist/80 italic capitalize">{type}</div>
                      {p.fields?.description && (
                        <div className="text-mist mt-1 line-clamp-2">
                          {p.fields.description}
                        </div>
                      )}
                      {data.writable && (
                        <button type="button" onClick={() => unpin(p.id)}
                                className="text-[10px] text-rose-300 hover:underline mt-1"
                                data-testid={`wb-atlas-pin-unpin-${p.id}`}>
                          <Trash2 className="w-3 h-3 inline mr-0.5"/> Unpin (keep node)
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            {/* New-pin preview marker */}
            {pinDraft && (
              <div className="absolute -translate-x-1/2 -translate-y-full"
                   style={{ left: `${pinDraft.x * 100}%`, top: `${pinDraft.y * 100}%` }}
                   data-testid="wb-atlas-pin-draft-marker">
                <MapPin className="w-7 h-7 text-emerald-300 animate-pulse"/>
              </div>
            )}
            {data.world_map_caption && (
              <div className="absolute bottom-0 right-0 left-0 px-3 py-1
                              bg-void/70 text-[10px] text-mist italic">
                {data.world_map_caption}
              </div>
            )}
          </div>
        ) : (
          <div className="card-mystic p-12 text-center text-mist/70 italic border-dashed border-emerald-700/30"
               data-testid="wb-atlas-no-map">
            No world map URL set yet. Paste one above to start pinning.
          </div>
        )}
      </div>

      {/* Sidebar — pin draft form OR unpinned locations */}
      <div className="space-y-3">
        {pinDraft ? (
          <div className="card-mystic p-3 border-emerald-700/30"
               data-testid="wb-atlas-pin-draft">
            <div className="flex items-center justify-between mb-2">
              <div className="label-ref text-emerald-300 flex items-center gap-1">
                <Pin className="w-3 h-3"/> Drop pin
              </div>
              <button type="button" onClick={() => setPinDraft(null)}
                      className="btn btn-ghost text-[11px] p-1"
                      data-testid="wb-atlas-pin-draft-cancel">
                <X className="w-3 h-3"/>
              </button>
            </div>
            <div className="text-[11px] text-mist/70 italic mb-2">
              ({(pinDraft.x * 100).toFixed(1)}%, {(pinDraft.y * 100).toFixed(1)}%)
            </div>
            <input type="text" value={pinDraft.title}
                   onChange={(e) => setPinDraft({...pinDraft, title: e.target.value})}
                   placeholder="Place name…"
                   className="input text-xs w-full mb-2" autoFocus
                   data-testid="wb-atlas-pin-draft-title"/>
            <textarea value={pinDraft.description}
                      onChange={(e) => setPinDraft({...pinDraft, description: e.target.value})}
                      placeholder="Sensory description…"
                      className="input text-xs w-full mb-2 min-h-[60px]"
                      data-testid="wb-atlas-pin-draft-desc"/>
            <select value={pinDraft.location_type}
                    onChange={(e) => setPinDraft({...pinDraft, location_type: e.target.value})}
                    className="input text-xs w-full mb-2"
                    data-testid="wb-atlas-pin-draft-type">
              {Object.keys(TYPE_PALETTE).map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <button type="button" onClick={submitPin} disabled={busy}
                    className="btn btn-primary text-xs w-full mb-2"
                    data-testid="wb-atlas-pin-draft-submit">
              {busy ? "Dropping…" : "Drop pin (new node)"}
            </button>
            {(data.unpinned_locations || []).length > 0 && (
              <>
                <div className="label-ref text-[10px] text-mist/60 uppercase tracking-widest mt-2 mb-1">
                  Or attach an existing un-pinned location
                </div>
                <div className="max-h-40 overflow-auto space-y-1">
                  {(data.unpinned_locations || []).map((n) => (
                    <button key={n.id} onClick={() => attachExisting(n)}
                            className="w-full text-left text-[11px] px-2 py-1 rounded-sm hover:bg-emerald-900/20 border border-emerald-900/20"
                            data-testid={`wb-atlas-attach-${n.id}`}>
                      <div className="text-gold-bright">{n.title}</div>
                      <div className="text-mist/60 italic">
                        {n.fields?.location_type || "—"}
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="card-mystic p-3 border-emerald-700/30"
               data-testid="wb-atlas-pins-list">
            <div className="label-ref text-emerald-300 mb-2">Pinned ({(data.pins || []).length})</div>
            {(data.pins || []).length === 0 ? (
              <div className="text-[11px] text-mist/60 italic">
                {data.writable
                  ? "Click on the map to drop your first pin."
                  : "No pins yet."}
              </div>
            ) : (
              <div className="space-y-1 max-h-80 overflow-auto">
                {(data.pins || []).map((p) => {
                  const t = p.fields?.location_type || "other";
                  return (
                    <div key={p.id} className="text-[11px] flex items-center gap-2 py-0.5">
                      <MapPin className="w-3 h-3" style={{ color: TYPE_PALETTE[t] }}/>
                      <span className="text-gold-bright">{p.title}</span>
                      <span className="text-mist/50 capitalize text-[10px]">· {t}</span>
                    </div>
                  );
                })}
              </div>
            )}
            {(data.unpinned_locations || []).length > 0 && (
              <div className="mt-3 pt-2 border-t border-emerald-900/30">
                <div className="label-ref text-[10px] text-mist/60 uppercase tracking-widest mb-1">
                  Locations awaiting a pin ({data.unpinned_locations.length})
                </div>
                <div className="text-[10px] text-mist/60 italic">
                  Click anywhere on the map, then pick one from the draft sidebar.
                </div>
              </div>
            )}
          </div>
        )}

        {err && (
          <div className="card-mystic p-2 border-rose-700/40 text-[11px] text-rose-200"
               data-testid="wb-atlas-error">{err}</div>
        )}
      </div>
    </div>
  );
}
