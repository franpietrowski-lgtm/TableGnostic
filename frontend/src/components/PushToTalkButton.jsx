/**
 * PushToTalkButton — V6.25.36
 *
 * Hold-to-record in-character speech. On release, the audio chunk is
 * uploaded to /api/sessions/{sid}/voice-lines along with character_id +
 * start/end timestamps. The server runs Whisper and persists the
 * transcript to the `voice_lines` collection — which the recap
 * generator weaves into the chronicle alongside chat / rolls / encounter
 * ticks. Voice lines are NEVER pushed to player journals (deliberate —
 * journals stay a player's own POV so the GM can spot lies / sub-plot
 * drift).
 *
 * UX:
 *   • Hold the button (mouse, touch, or Space-bar while focused).
 *   • While held: pulsing red "Recording…" indicator + a 60s soft cap.
 *   • On release: 'Transcribing…' → success toast or quiet error.
 *   • Author can quietly delete the last line within 60s (Undo button).
 *
 * Permission: requires browser microphone permission. We ask once,
 * cache the stream, and reuse it for subsequent pushes (avoids the
 * permission prompt on every push).
 */
import React, { useEffect, useRef, useState, useCallback } from "react";
import { Mic, MicOff, Loader2, Undo2, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";
import {
  acquireSharedMic, releaseSharedMic, lastSharedMicError,
} from "../lib/useSharedMicStream";

const MAX_PUSH_SECONDS = 60;          // soft cap — release auto-fires
const AUTHOR_UNDO_WINDOW_MS = 60_000; // matches backend grace window

export default function PushToTalkButton({ sessionId, characterId, characterName }) {
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [permission, setPermission] = useState("idle"); // idle | granted | denied
  const [lastLine, setLastLine] = useState(null);
  const [err, setErr] = useState("");
  // V6.25.56 Phase E — no per-PTT getUserMedia. We acquire/release the
  // SHARED microphone singleton (also used by AVSeats) so the OS sees
  // exactly one mic consumer at a time. heldRef tracks whether THIS
  // component currently holds a refcount on the shared stream.
  const heldRef = useRef(false);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const startedAtRef = useRef(null);
  const timeoutRef = useRef(null);

  // Acquire / cache the microphone stream. Called lazily on first press.
  // Only acquires once per component lifetime; subsequent calls are no-ops
  // that return the existing shared stream.
  const ensureStream = useCallback(async () => {
    const s = await acquireSharedMic();
    if (!s) {
      setPermission("denied");
      const e = lastSharedMicError();
      setErr(e?.name === "NotAllowedError"
        ? "Microphone permission denied."
        : "Microphone unavailable.");
      return null;
    }
    // First successful acquire becomes the persistent refcount this
    // component holds; later acquires must immediately release so the
    // shared refcount never drifts above 1 from PTT.
    if (heldRef.current) {
      releaseSharedMic();
    } else {
      heldRef.current = true;
    }
    setPermission("granted");
    return s;
  }, []);

  // Pick the best supported mime — webm/opus is ubiquitous in Chromium
  // and Firefox; Safari prefers mp4. We let MediaRecorder pick if our
  // preferred type isn't supported.
  const _pickMime = () => {
    const candidates = [
      "audio/webm;codecs=opus", "audio/webm",
      "audio/ogg;codecs=opus",  "audio/ogg",
      "audio/mp4", "audio/m4a",
    ];
    for (const c of candidates) {
      if (window.MediaRecorder?.isTypeSupported?.(c)) return c;
    }
    return undefined;
  };

  const start = useCallback(async () => {
    if (recording || busy) return;
    if (!characterId) {
      setErr("Pick a character to speak as first.");
      return;
    }
    setErr("");
    const stream = await ensureStream();
    if (!stream) return;
    const mime = _pickMime();
    let rec;
    try {
      rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    } catch (e) {
      setErr("Recorder init failed.");
      return;
    }
    chunksRef.current = [];
    rec.ondataavailable = (ev) => { if (ev.data?.size) chunksRef.current.push(ev.data); };
    recorderRef.current = rec;
    startedAtRef.current = new Date();
    rec.start();
    setRecording(true);
    timeoutRef.current = setTimeout(() => stop(), MAX_PUSH_SECONDS * 1000);
  }, [recording, busy, characterId, ensureStream]);

  const stop = useCallback(async () => {
    const rec = recorderRef.current;
    if (!rec || rec.state === "inactive") return;
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    setBusy(true);
    setRecording(false);
    const stoppedAt = new Date();

    await new Promise((res) => {
      rec.onstop = res;
      try { rec.stop(); } catch (_e) { res(); }
    });
    const blob = new Blob(chunksRef.current, { type: rec.mimeType || "audio/webm" });
    if (blob.size < 1500) {
      // Too short to transcribe usefully (< ~0.3s)
      setBusy(false);
      setErr("Push was too brief to transcribe.");
      return;
    }
    try {
      const fd = new FormData();
      const ext = (rec.mimeType || "").includes("ogg") ? "ogg"
                : (rec.mimeType || "").includes("mp4") ? "m4a"
                : "webm";
      fd.append("audio", blob, `voice.${ext}`);
      fd.append("character_id", characterId);
      fd.append("started_at", startedAtRef.current?.toISOString() || stoppedAt.toISOString());
      fd.append("ended_at",   stoppedAt.toISOString());
      const r = await api.post(`/sessions/${sessionId}/voice-lines`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const line = r.data?.voice_line;
      if (line) {
        setLastLine({ ...line, _fetched_at: Date.now() });
      }
    } catch (e) {
      setErr(e?.response?.data?.detail || "Voice upload failed.");
    } finally {
      setBusy(false);
    }
  }, [characterId, sessionId]);

  // Space-bar push-to-talk while button has focus.
  const onKeyDown = (e) => { if (e.code === "Space") { e.preventDefault(); start(); } };
  const onKeyUp   = (e) => { if (e.code === "Space") { e.preventDefault(); stop(); } };

  const undoLast = async () => {
    if (!lastLine?.id) return;
    try {
      await api.delete(`/sessions/${sessionId}/voice-lines/${lastLine.id}`);
      setLastLine(null);
    } catch (e) { /* swallow */ }
  };

  // Cleanup when leaving the session. Release our refcount on the
  // shared mic so the OS mic LED goes off the moment we unmount (and
  // AVSeats isn't also holding it).
  useEffect(() => () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (heldRef.current) {
      heldRef.current = false;
      releaseSharedMic();
    }
  }, []);

  // Hide the undo button after the grace window closes.
  const undoVisible = lastLine && (Date.now() - (lastLine._fetched_at || 0) < AUTHOR_UNDO_WINDOW_MS);

  return (
    <div className="flex items-center gap-2" data-testid="ptt-bar">
      <button
        type="button"
        disabled={busy || !characterId}
        onMouseDown={start} onMouseUp={stop} onMouseLeave={() => recording && stop()}
        onTouchStart={start} onTouchEnd={stop} onTouchCancel={() => recording && stop()}
        onKeyDown={onKeyDown} onKeyUp={onKeyUp}
        className={`btn flex items-center gap-1.5 ${recording
          ? "bg-rose-900/60 text-rose-100 border-rose-700/60 animate-pulse"
          : busy
            ? "bg-amber-900/40 text-amber-200 border-amber-700/40"
            : "bg-gold/15 text-gold-bright border-gold/30 hover:bg-gold/25"} border`}
        title={characterId
          ? `Hold to speak as ${characterName || "your character"} (Space-bar also works while focused)`
          : "Pick a character to speak as first."}
        data-testid="ptt-button">
        {busy
          ? <><Loader2 className="w-3 h-3 animate-spin"/> Transcribing…</>
          : recording
            ? <><Mic className="w-3 h-3"/> Recording…</>
            : permission === "denied"
              ? <><MicOff className="w-3 h-3"/> Mic blocked</>
              : <><Mic className="w-3 h-3"/> Push to speak</>}
      </button>
      {undoVisible && (
        <button type="button" onClick={undoLast}
                className="btn btn-ghost text-[10px]"
                data-testid="ptt-undo-btn"
                title="Misspoke? Undo within 60s.">
          <Undo2 className="w-3 h-3"/> Undo "{(lastLine.text || "").slice(0, 32)}{(lastLine.text || "").length > 32 ? "…" : ""}"
        </button>
      )}
      {err && (
        <span className="text-[10px] text-ember flex items-center gap-1" data-testid="ptt-error">
          <AlertTriangle className="w-3 h-3"/> {err}
        </span>
      )}
    </div>
  );
}
