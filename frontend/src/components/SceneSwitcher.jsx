/**
 * SceneSwitcher — V6.25.43
 *
 * GM-only Sessions affordance to segment a live session into discrete
 * scenes. The recap engine groups chat / PTT / dice by scene.
 *
 * Design rules (locked by the product owner):
 *   • No pre-defined scene catalogue. Each scene is created on the fly.
 *   • No scene editing UI. Once a scene is created and the close click
 *     is confirmed, its metadata is frozen for the rest of the session.
 *   • Click-to-confirm guard on both START (premature slicing) and END
 *     (retcon prevention).
 *   • Players see a passive readout of the active scene + their PTT /
 *     chat is auto-attributed to it server-side.
 *
 * Network surface:
 *   GET    /api/sessions/{sid}/scenes/active
 *   GET    /api/sessions/{sid}/scenes
 *   POST   /api/sessions/{sid}/scenes
 *   POST   /api/sessions/{sid}/scenes/{scene_id}/close?confirmed=true
 *   PATCH  /api/sessions/{sid}/scenes/{scene_id}/setup
 *   PATCH  /api/sessions/{sid}/default-thread
 *
 * The component subscribes to the session WebSocket for the
 * scene:start / scene:end / scene:update events so every connected
 * player re-renders instantly when the GM switches scenes.
 */
import React, { useEffect, useRef, useState } from "react";
import { Clapperboard, Scissors, MapPin, Tags, Check, X, ChevronRight } from "lucide-react";
import { api } from "../lib/api";

export default function SceneSwitcher({ sessionId, campaignId, isGm, subscribe }) {
  const [active, setActive] = useState(null);
  const [scenes, setScenes] = useState([]);
  const [locations, setLocations] = useState([]);
  const [channels, setChannels] = useState([]);   // for inline channel options
  const [threads, setThreads] = useState([]);
  const [showStart, setShowStart] = useState(false);
  const [showEnd, setShowEnd] = useState(false);
  const [name, setName] = useState("");
  const [locationId, setLocationId] = useState("");
  const [adhocLocation, setAdhocLocation] = useState(""); // on-the-fly text
  const [targetThreadId, setTargetThreadId] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const mounted = useRef(true);

  useEffect(() => () => { mounted.current = false; }, []);

  // ---------- initial load + WS subscription ----------
  const refresh = async () => {
    try {
      const a = await api.get(`/sessions/${sessionId}/scenes/active`);
      if (mounted.current) setActive(a.data?.scene || null);
      const l = await api.get(`/sessions/${sessionId}/scenes`);
      if (mounted.current) setScenes(l.data?.scenes || []);
    } catch (_e) { /* swallow */ }
  };
  useEffect(() => { if (sessionId) refresh(); }, [sessionId]);

  useEffect(() => {
    if (!subscribe) return;
    return subscribe((evt) => {
      if (!evt || !evt.type) return;
      if (evt.type === "scene:start" || evt.type === "scene:end" ||
          evt.type === "scene:update") {
        refresh();
      }
    });
  }, [subscribe]);

  // ---------- lookups for GM (locations + channels + threads) ----------
  useEffect(() => {
    if (!isGm || !campaignId) return;
    (async () => {
      try {
        // Pull only `location` nodes for the location picker.
        const { data } = await api.get(`/campaigns/${campaignId}/nodes`);
        const all = Array.isArray(data) ? data : (data?.nodes || []);
        setLocations(all.filter((n) => n.type === "location").slice(0, 400));
      } catch (_e) { /* swallow */ }
      try {
        // V6.25.44 — channels endpoint returns ARRAY directly (not
        // {channels: [...]}). Same for threads. Previous shape-guess
        // returned [] every time, leaving the dropdown empty.
        const { data: chRaw } = await api.get(`/campaigns/${campaignId}/channels`);
        const chans = Array.isArray(chRaw) ? chRaw : (chRaw?.channels || []);
        setChannels(chans);
        const tlist = [];
        for (const ch of chans) {
          try {
            const tr = await api.get(`/channels/${ch.id}/threads`);
            const trArr = Array.isArray(tr.data) ? tr.data : (tr.data?.threads || []);
            trArr.forEach((t) => tlist.push({ ...t, channel_name: ch.name }));
          } catch { /* ignore single-channel failure */ }
        }
        setThreads(tlist);
      } catch (_e) { /* swallow */ }
    })();
  }, [isGm, campaignId]);

  // ---------- actions ----------
  const startScene = async () => {
    setBusy(true); setErr("");
    try {
      await api.post(`/sessions/${sessionId}/scenes`, {
        name: name.trim() || undefined,
        location_id: locationId || undefined,
        adhoc_location_label: adhocLocation.trim() || undefined,
        target_thread_id: targetThreadId || undefined,
      });
      setShowStart(false);
      setName(""); setLocationId(""); setAdhocLocation(""); setTargetThreadId("");
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to start scene.");
    } finally { setBusy(false); }
  };

  const endScene = async () => {
    if (!active) return;
    setBusy(true); setErr("");
    try {
      await api.post(
        `/sessions/${sessionId}/scenes/${active.id}/close?confirmed=true`,
      );
      setShowEnd(false);
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to close scene.");
    } finally { setBusy(false); }
  };

  // ---------- render ----------
  // Players see a passive readout. GMs see controls.
  return (
    <div className="card-mystic p-3 flex flex-col gap-2"
         data-testid="scene-switcher">
      <div className="flex items-center gap-2">
        <Clapperboard className="w-4 h-4 text-gold-bright"/>
        <div className="label-ref text-gold-bright">Scene</div>
        {active ? (
          <span className="text-[11px] text-mist truncate"
                data-testid="scene-active-label">
            {active.name} <span className="text-gold/70">· {active.slug}</span>
          </span>
        ) : (
          <span className="text-[11px] text-mist/60 italic"
                data-testid="scene-active-empty">no active scene</span>
        )}
        <div className="flex-1"/>
        {isGm && !active && (
          <button type="button" onClick={() => setShowStart(true)}
                  className="btn btn-primary text-[11px] flex items-center gap-1"
                  data-testid="scene-start-btn">
            <ChevronRight className="w-3 h-3"/> Start scene
          </button>
        )}
        {isGm && active && (
          <>
            <button type="button" onClick={() => setShowStart(true)}
                    className="btn btn-ghost text-[11px] flex items-center gap-1"
                    data-testid="scene-next-btn"
                    title="Switching scenes auto-closes the current one.">
              Switch
            </button>
            <button type="button" onClick={() => setShowEnd(true)}
                    className="btn text-[11px] flex items-center gap-1 bg-rose-950/40 text-rose-200 border-rose-900/40"
                    data-testid="scene-end-btn">
              <Scissors className="w-3 h-3"/> End
            </button>
          </>
        )}
      </div>

      {active?.location_label && (
        <div className="flex items-start gap-1 text-[11px] text-mist/80"
             data-testid="scene-location-line">
          <MapPin className="w-3 h-3 mt-0.5 text-gold/70"/>
          <div>
            <span className="text-gold-bright">{active.location_label}</span>
            {active.location_description && (
              <span className="text-mist/60 italic"> — {active.location_description}</span>
            )}
          </div>
        </div>
      )}

      {scenes.length > 0 && (
        <div className="text-[10px] text-mist/50 uppercase tracking-widest"
             data-testid="scene-history-count">
          {scenes.length} scene{scenes.length === 1 ? "" : "s"} in this session
        </div>
      )}

      {/* -------- Start scene confirm modal -------- */}
      {showStart && (
        <ConfirmModal title={active ? "Switch to a new scene" : "Start a new scene"}
                      body={
          <div className="space-y-2">
            <div className="text-[11px] text-mist/80">
              {active ? (
                <>This closes <b>{active.name}</b> and starts a new scene.
                Click-to-confirm prevents premature slicing.</>
              ) : (
                <>Create the first scene of this session. Pick a label,
                anchor location, and (optionally) a thread to mirror
                PTT lines into for play-by-post viewability.</>
              )}
            </div>
            <input
              type="text" maxLength={120} value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Scene label (optional — defaults to Scene N)"
              className="input text-xs w-full"
              data-testid="scene-start-name"/>
            <select value={locationId}
                    onChange={(e) => { setLocationId(e.target.value);
                                       if (e.target.value) setAdhocLocation(""); }}
                    className="input text-xs w-full"
                    data-testid="scene-start-location">
              <option value="">— Codex location (optional) —</option>
              {locations.length === 0 && (
                <option value="" disabled>No location nodes in this campaign yet</option>
              )}
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.title}{l.fields?.location_type ? ` · ${l.fields.location_type}` : ""}
                </option>
              ))}
            </select>
            {/* V6.25.44 — on-the-fly custom location text input. Players
                often need "in the dripping cellar" without authoring a
                full codex node first. The text label persists on the
                scene and the recap engine includes it as the location. */}
            <input
              type="text" maxLength={200} value={adhocLocation}
              onChange={(e) => { setAdhocLocation(e.target.value);
                                  if (e.target.value) setLocationId(""); }}
              placeholder='Or describe an on-the-fly location ("the dripping cellar at dusk")'
              className="input text-xs w-full"
              data-testid="scene-start-adhoc-location"/>
            <select value={targetThreadId}
                    onChange={(e) => setTargetThreadId(e.target.value)}
                    className="input text-xs w-full"
                    data-testid="scene-start-thread">
              <option value="">— Target for PTT mirror (optional) —</option>
              {channels.length > 0 && (
                <optgroup label="Channels (root)">
                  {channels.map((c) => (
                    <option key={`ch-${c.id}`} value={c.id}>
                      #{c.name}
                    </option>
                  ))}
                </optgroup>
              )}
              {threads.length > 0 && (
                <optgroup label="Threads">
                  {threads.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.channel_name ? `#${t.channel_name} · ` : ""}{t.name}
                    </option>
                  ))}
                </optgroup>
              )}
              {channels.length === 0 && threads.length === 0 && (
                <option value="" disabled>No channels or threads yet — create one in Channels first</option>
              )}
            </select>
          </div>
        } confirmLabel={active ? "Switch scene" : "Start scene"}
        onCancel={() => { setShowStart(false); setErr(""); }}
        onConfirm={startScene} busy={busy} err={err}
        testId="scene-start-modal"/>
      )}

      {/* -------- End scene confirm modal -------- */}
      {showEnd && active && (
        <ConfirmModal title={`End scene "${active.name}"`}
                      body={
          <div className="text-[11px] text-mist/80 space-y-1">
            <div>This closes the scene and freezes its content. There is no edit-after, no retcon.</div>
            <div className="text-mist/60 italic">Slug: <code>{active.slug}</code></div>
          </div>
        } confirmLabel="End scene" destructive
        onCancel={() => { setShowEnd(false); setErr(""); }}
        onConfirm={endScene} busy={busy} err={err}
        testId="scene-end-modal"/>
      )}
    </div>
  );
}

// ---------- shared modal ----------
function ConfirmModal({ title, body, confirmLabel, destructive, onCancel,
                       onConfirm, busy, err, testId }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
         data-testid={testId}>
      <div className="card-mystic max-w-md w-full p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Tags className="w-4 h-4 text-gold-bright"/>
          <div className="label-ref text-gold-bright flex-1">{title}</div>
          <button type="button" onClick={onCancel}
                  className="btn btn-ghost text-[11px] p-1"
                  data-testid={`${testId}-cancel`}>
            <X className="w-3 h-3"/>
          </button>
        </div>
        {body}
        {err && <div className="text-[11px] text-ember"
                     data-testid={`${testId}-err`}>{err}</div>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onCancel}
                  className="btn btn-ghost text-[11px]"
                  data-testid={`${testId}-cancel2`}>
            Cancel
          </button>
          <button type="button" onClick={onConfirm} disabled={busy}
                  className={`btn text-[11px] flex items-center gap-1 ${destructive
                    ? "bg-rose-900/50 text-rose-100 border-rose-700/50 hover:bg-rose-900/70"
                    : "btn-primary"}`}
                  data-testid={`${testId}-confirm`}>
            <Check className="w-3 h-3"/>
            {busy ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
