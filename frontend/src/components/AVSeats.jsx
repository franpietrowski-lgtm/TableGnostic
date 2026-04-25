import React, { useEffect, useRef, useState, useCallback } from "react";
import { Mic, MicOff, Video, VideoOff, PhoneOff, Phone, Crown } from "lucide-react";

/**
 * AVSeats — mesh WebRTC voice/video, mobile-first.
 * Reuses the parent SessionView's WebSocket as a signaling channel via
 * the (subscribe, send) bridge passed in props.
 *
 * Props:
 *   subscribe(handler) -> unsubscribe()  // receive { type, data } from server
 *   send({type, to?, data})              // send to server
 *   sessionTitle: string
 */

const ICE_SERVERS = [
  { urls: "stun:stun.l.google.com:19302" },
  { urls: "stun:stun1.l.google.com:19302" },
];

// Deterministic offerer: peer with the lexicographically smaller conn_id
// is the offerer for that pair. Avoids glare without negotiationneeded races.
function shouldOffer(myConnId, theirConnId) {
  return String(myConnId) < String(theirConnId);
}

export default function AVSeats({ subscribe, send, sessionTitle }) {
  const [me, setMe] = useState(null);            // {conn_id, uid, name, is_gm}
  const [peers, setPeers] = useState({});        // conn_id -> {conn_id, uid, name, is_gm, micOn, camOn, stream}
  const [joined, setJoined] = useState(false);
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [error, setError] = useState("");
  const [enlarged, setEnlarged] = useState(null); // conn_id of expanded tile

  const localStreamRef = useRef(null);
  const localVideoRef = useRef(null);
  const pcsRef = useRef({});         // conn_id -> RTCPeerConnection
  const pendingIceRef = useRef({});  // conn_id -> queued ICE candidates before remoteDescription is set
  const meRef = useRef(null);        // mirror of `me` for use in async callbacks

  // ------------ helpers ------------
  const upsertPeer = (conn_id, patch) => {
    setPeers((prev) => ({
      ...prev,
      [conn_id]: { ...(prev[conn_id] || { conn_id }), ...patch },
    }));
  };
  const removePeer = (conn_id) => {
    setPeers((prev) => {
      const next = { ...prev };
      delete next[conn_id];
      return next;
    });
    const pc = pcsRef.current[conn_id];
    if (pc) {
      try { pc.close(); } catch {}
      delete pcsRef.current[conn_id];
    }
    delete pendingIceRef.current[conn_id];
  };

  const broadcastAvState = useCallback((next) => {
    send({
      type: "presence:av-state",
      data: { mic: next.mic, cam: next.cam, in_call: next.in_call },
    });
  }, [send]);

  // ------------ peer connection factory ------------
  const createPC = useCallback((peerConnId, peerName) => {
    if (pcsRef.current[peerConnId]) return pcsRef.current[peerConnId];
    const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
    pcsRef.current[peerConnId] = pc;

    // local tracks
    const ls = localStreamRef.current;
    if (ls) {
      ls.getTracks().forEach((t) => pc.addTrack(t, ls));
    }

    pc.onicecandidate = (ev) => {
      if (ev.candidate) {
        send({
          type: "webrtc:ice",
          to: peerConnId,
          data: { candidate: ev.candidate },
        });
      }
    };
    pc.ontrack = (ev) => {
      const stream = ev.streams[0];
      upsertPeer(peerConnId, { stream, name: peerName });
    };
    pc.onconnectionstatechange = () => {
      if (["failed", "disconnected", "closed"].includes(pc.connectionState)) {
        // Don't yank tile — backend presence:leave is the source of truth
      }
    };
    return pc;
  }, [send]);

  // Initiate offer to a peer (used when WE are the deterministic offerer)
  const dialPeer = useCallback(async (peerConnId, peerName) => {
    const pc = createPC(peerConnId, peerName);
    try {
      const offer = await pc.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: true,
      });
      await pc.setLocalDescription(offer);
      send({ type: "webrtc:offer", to: peerConnId, data: { sdp: offer } });
    } catch (e) {
      console.warn("dialPeer failed", e);
    }
  }, [createPC, send]);

  // ------------ WS subscription (signaling + presence) ------------
  useEffect(() => {
    if (!subscribe) return;
    const off = subscribe(async (evt) => {
      if (!evt || !evt.type) return;
      const { type, data } = evt;

      if (type === "presence:room") {
        setMe(data.you);
        meRef.current = data.you;
        // Seed existing peer tiles
        const seeded = {};
        (data.peers || []).forEach((p) => {
          seeded[p.conn_id] = { ...p, micOn: false, camOn: false, stream: null };
        });
        setPeers(seeded);
      } else if (type === "presence:join") {
        upsertPeer(data.conn_id, { ...data, micOn: false, camOn: false, stream: null });
        // If we're already in the call and we're the deterministic offerer, dial them
        if (localStreamRef.current && meRef.current &&
            shouldOffer(meRef.current.conn_id, data.conn_id)) {
          dialPeer(data.conn_id, data.name);
        }
      } else if (type === "presence:leave") {
        removePeer(data.conn_id);
      } else if (type === "presence:av-state") {
        upsertPeer(data.conn_id, {
          micOn: !!data.mic,
          camOn: !!data.cam,
          inCall: !!data.in_call,
        });
      } else if (type === "webrtc:offer") {
        const peerConnId = data.from;
        const peerName = data.from_name;
        if (!localStreamRef.current) {
          // We received an offer but haven't joined the call yet — ignore.
          return;
        }
        const pc = createPC(peerConnId, peerName);
        try {
          await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          // flush any queued ICE
          const queued = pendingIceRef.current[peerConnId] || [];
          for (const c of queued) {
            try { await pc.addIceCandidate(c); } catch {}
          }
          delete pendingIceRef.current[peerConnId];
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          send({ type: "webrtc:answer", to: peerConnId, data: { sdp: answer } });
        } catch (e) { console.warn("offer handling failed", e); }
      } else if (type === "webrtc:answer") {
        const pc = pcsRef.current[data.from];
        if (!pc) return;
        try {
          await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          const queued = pendingIceRef.current[data.from] || [];
          for (const c of queued) {
            try { await pc.addIceCandidate(c); } catch {}
          }
          delete pendingIceRef.current[data.from];
        } catch (e) { console.warn("answer handling failed", e); }
      } else if (type === "webrtc:ice") {
        const pc = pcsRef.current[data.from];
        const cand = new RTCIceCandidate(data.candidate);
        if (pc && pc.remoteDescription && pc.remoteDescription.type) {
          try { await pc.addIceCandidate(cand); } catch {}
        } else {
          pendingIceRef.current[data.from] = pendingIceRef.current[data.from] || [];
          pendingIceRef.current[data.from].push(cand);
        }
      }
    });
    return () => { try { off && off(); } catch {} };
  }, [subscribe, send, createPC, dialPeer]);

  // ------------ join / leave call ------------
  const joinCall = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
        video: { width: { ideal: 480 }, height: { ideal: 360 }, facingMode: "user" },
      });
      localStreamRef.current = stream;
      if (localVideoRef.current) localVideoRef.current.srcObject = stream;
      setJoined(true);
      // dial existing peers we're the offerer for
      const myId = meRef.current?.conn_id;
      Object.values(peers).forEach((p) => {
        if (myId && shouldOffer(myId, p.conn_id)) {
          dialPeer(p.conn_id, p.name);
        }
      });
      broadcastAvState({ mic: true, cam: true, in_call: true });
      setMicOn(true);
      setCamOn(true);
    } catch (e) {
      console.warn("getUserMedia failed", e);
      setError(
        e?.name === "NotAllowedError"
          ? "Microphone/camera permission denied."
          : "Could not start your camera or microphone."
      );
    }
  };

  const leaveCall = () => {
    Object.keys(pcsRef.current).forEach((cid) => {
      try { pcsRef.current[cid].close(); } catch {}
    });
    pcsRef.current = {};
    pendingIceRef.current = {};
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => t.stop());
      localStreamRef.current = null;
    }
    if (localVideoRef.current) localVideoRef.current.srcObject = null;
    // wipe remote streams from local state (peers stay listed as seats with no media)
    setPeers((prev) => {
      const next = {};
      Object.entries(prev).forEach(([k, v]) => {
        next[k] = { ...v, stream: null, micOn: false, camOn: false, inCall: false };
      });
      return next;
    });
    setJoined(false);
    broadcastAvState({ mic: false, cam: false, in_call: false });
  };

  const toggleMic = () => {
    const s = localStreamRef.current;
    if (!s) return;
    const next = !micOn;
    s.getAudioTracks().forEach((t) => (t.enabled = next));
    setMicOn(next);
    broadcastAvState({ mic: next, cam: camOn, in_call: true });
  };
  const toggleCam = () => {
    const s = localStreamRef.current;
    if (!s) return;
    const next = !camOn;
    s.getVideoTracks().forEach((t) => (t.enabled = next));
    setCamOn(next);
    broadcastAvState({ mic: micOn, cam: next, in_call: true });
  };

  // cleanup on unmount
  useEffect(() => {
    return () => {
      Object.values(pcsRef.current).forEach((pc) => { try { pc.close(); } catch {} });
      pcsRef.current = {};
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  // ------------ render ------------
  const peerList = Object.values(peers);
  const tilesCount = peerList.length + (joined ? 1 : 0);

  return (
    <div
      className="card-mystic p-3 md:p-4"
      data-testid="av-seats"
      aria-label="Voice and video seats"
    >
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="min-w-0">
          <div className="label-ref">Voice / Cam Seats</div>
          <div className="text-[10px] font-ui uppercase tracking-widest text-mist/60 truncate">
            {tilesCount} at the table · {sessionTitle}
          </div>
        </div>
        {!joined ? (
          <button
            onClick={joinCall}
            className="btn btn-primary text-xs"
            data-testid="av-join-btn"
          >
            <Phone className="w-3 h-3" /> Join voice
          </button>
        ) : (
          <div className="flex items-center gap-1.5">
            <button
              onClick={toggleMic}
              className={`btn ${micOn ? "btn-ghost" : "btn-ghost text-ember"} text-xs px-2`}
              data-testid="av-mic-btn"
              aria-pressed={micOn}
              title={micOn ? "Mute mic" : "Unmute mic"}
            >
              {micOn ? <Mic className="w-3.5 h-3.5" /> : <MicOff className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={toggleCam}
              className={`btn ${camOn ? "btn-ghost" : "btn-ghost text-ember"} text-xs px-2`}
              data-testid="av-cam-btn"
              aria-pressed={camOn}
              title={camOn ? "Stop camera" : "Start camera"}
            >
              {camOn ? <Video className="w-3.5 h-3.5" /> : <VideoOff className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={leaveCall}
              className="btn btn-ghost text-xs px-2 text-ember hover:text-ember"
              data-testid="av-leave-btn"
              title="Leave call"
            >
              <PhoneOff className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="text-[11px] font-ui text-ember mb-2" data-testid="av-error">
          {error}
        </div>
      )}

      {/* Tile strip — horizontal scroll on mobile, wrap-grid on desktop */}
      <div
        className="flex gap-2 overflow-x-auto scroll-stylish md:flex-wrap md:overflow-visible -mx-1 px-1 pb-1"
        data-testid="av-tiles"
      >
        {joined && (
          <Tile
            key="self"
            name={(me?.name || "You") + " (you)"}
            isGm={!!me?.is_gm}
            isSelf
            videoRef={localVideoRef}
            micOn={micOn}
            camOn={camOn}
            inCall
            enlarged={enlarged === "self"}
            onToggleEnlarge={() => setEnlarged(enlarged === "self" ? null : "self")}
          />
        )}
        {peerList.map((p) => (
          <PeerTile
            key={p.conn_id}
            peer={p}
            enlarged={enlarged === p.conn_id}
            onToggleEnlarge={() =>
              setEnlarged(enlarged === p.conn_id ? null : p.conn_id)
            }
          />
        ))}
        {tilesCount === 0 && (
          <div className="text-[11px] font-ui text-mist/60 italic px-2 py-3" data-testid="av-empty">
            No one's around the table yet — invite players, then tap Join voice.
          </div>
        )}
      </div>
    </div>
  );
}

// ------------ Tile components ------------
function PeerTile({ peer, enlarged, onToggleEnlarge }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.srcObject = peer.stream || null;
  }, [peer.stream]);
  return (
    <Tile
      name={peer.name}
      isGm={!!peer.is_gm}
      videoRef={ref}
      micOn={peer.micOn}
      camOn={peer.camOn}
      hasStream={!!peer.stream}
      inCall={!!peer.inCall || !!peer.stream}
      enlarged={enlarged}
      onToggleEnlarge={onToggleEnlarge}
      testId={`av-tile-${peer.conn_id}`}
    />
  );
}

function Tile({
  name, isGm, isSelf, videoRef, micOn, camOn, hasStream, inCall,
  enlarged, onToggleEnlarge, testId,
}) {
  const showVideo = isSelf ? camOn : (hasStream && camOn);
  const dim = enlarged ? "w-[260px] h-[180px]" : "w-[120px] h-[90px] md:w-[140px] md:h-[100px]";
  return (
    <button
      type="button"
      onClick={onToggleEnlarge}
      className={`relative shrink-0 ${dim} rounded-sm overflow-hidden border ${
        inCall ? "border-gold/40" : "border-gold/10"
      } bg-black/60 group focus:outline-none focus:ring-1 focus:ring-gold/60`}
      data-testid={testId || "av-tile-self"}
      aria-label={`${name} ${inCall ? "in call" : "not in call"}`}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={!!isSelf}
        className={`w-full h-full object-cover ${showVideo ? "" : "hidden"}`}
      />
      {!showVideo && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-gold/15 border border-gold/30 flex items-center justify-center">
            <span className="font-display text-base md:text-lg text-gold-bright">
              {(name || "?").trim().charAt(0).toUpperCase()}
            </span>
          </div>
        </div>
      )}
      {/* footer chip */}
      <div className="absolute left-0 right-0 bottom-0 px-1.5 py-1 bg-gradient-to-t from-black/80 to-transparent flex items-center gap-1">
        {isGm && <Crown className="w-3 h-3 text-gold-bright shrink-0" aria-label="GM" />}
        <span className="text-[10px] text-parchment font-ui truncate flex-1 text-left">{name}</span>
        {inCall ? (
          micOn
            ? <Mic className="w-3 h-3 text-gold-bright shrink-0" />
            : <MicOff className="w-3 h-3 text-ember shrink-0" />
        ) : (
          <span className="text-[8px] uppercase tracking-widest text-mist/60">idle</span>
        )}
      </div>
    </button>
  );
}
