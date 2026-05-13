import React, { useEffect, useRef, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { api, API, useAuth } from "../lib/api";
import { useMinDelay } from "../lib/useMinDelay";
import { Dice6, Send, Plus, X, Swords, Heart, Zap, Skull, Shield, ChevronRight, Sparkles, ScrollText, Users, MessageSquare, Map as MapIcon } from "lucide-react";
import AVSeats from "./AVSeats";
import Battlemap from "./Battlemap";
import XPAwardPanel from "./XPAwardPanel";
import MacroBar from "./MacroBar";
import PushToTalkButton from "./PushToTalkButton";
import SceneSwitcher from "./SceneSwitcher";
import EncounterDesigner from "./EncounterDesigner";
import QuickCastDock from "./QuickCastDock";
import EncountersLibrary from "./EncountersLibrary";

export default function SessionView() {
  const { id } = useParams();
  const { user } = useAuth();
  const [session, setSession] = useState(null);
  const [chat, setChat] = useState([]);
  const [dice, setDice] = useState([]);
  const [init, setInit] = useState([]);
  const [effects, setEffects] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [campaign, setCampaign] = useState(null);
  const [msg, setMsg] = useState("");
  const [roll, setRoll] = useState("2d6");
  const [label, setLabel] = useState("");
  const [target, setTarget] = useState("");
  const [characterId, setCharacterId] = useState("");
  const [recap, setRecap] = useState(null);
  const [recapBusy, setRecapBusy] = useState(false);
  const [recapStyle, setRecapStyle] = useState("narrative");
  const [mobilePane, setMobilePane] = useState("chat"); // chat | init | dice (mobile only)
  const [mapOpen, setMapOpen] = useState(false);
  const [xpOpen, setXpOpen] = useState(false);
  const [loadErr, setLoadErr] = useState("");
  const chatEnd = useRef(null);
  const wsRef = useRef(null);
  const subsRef = useRef([]); // AVSeats subscribers

  const wsSubscribe = useCallback((handler) => {
    subsRef.current.push(handler);
    return () => {
      subsRef.current = subsRef.current.filter((h) => h !== handler);
    };
  }, []);
  const wsSend = useCallback((obj) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(obj));
    }
  }, []);

  const takeSeat = useCallback(async (charId) => {
    try {
      const { data } = await api.post(
        `/sessions/${id}/seat-character?character_id=${encodeURIComponent(charId || "")}`
      );
      // Optimistic local update — WS will arrive next anyway.
      setSession((s) => s ? ({ ...s, character_assignments: data.character_assignments }) : s);
    } catch (e) {
      // surface but don't crash
      console.warn("seat-character failed:", e?.response?.data?.detail || e.message);
    }
  }, [id]);

  // Compact one-liner for a character card — system-aware so non-BESM
  // sheets don't leak Body/Mind/Soul into the seat picker.
  const systemBlurb = useCallback((c, systemId) => {
    const dnd = c.folio?.dnd_state;
    const cyph = c.folio?.cypher_state;
    if (cyph) return `Cypher · T${cyph.tier || 1} · ${cyph.descriptor || "?"} ${cyph.type || "?"}`;
    if (dnd) {
      const isAnime = systemId === "anime-5e" || c.folio?.anime5e_state;
      return `${isAnime ? "Anime 5E" : "D&D 5E"} · ${dnd.class || "?"} ${dnd.level || 1} · ${dnd.race || "?"}`;
    }
    return `Body ${c.stats?.body ?? "?"} · Mind ${c.stats?.mind ?? "?"} · Soul ${c.stats?.soul ?? "?"}`;
  }, []);

  const loadAll = async () => {
    try {
      setLoadErr("");
      const s = await api.get(`/sessions/${id}`).then((r) => r.data);
      setSession(s);
      const [c, d, i, e, chs, camp] = await Promise.all([
        api.get(`/sessions/${id}/chat`).then(r => r.data).catch(() => []),
        api.get(`/sessions/${id}/dice`).then(r => r.data).catch(() => []),
        api.get(`/sessions/${id}/initiative`).then(r => r.data).catch(() => []),
        api.get(`/sessions/${id}/effects`).then(r => r.data).catch(() => []),
        api.get(`/campaigns/${s.campaign_id}/characters`).then(r => r.data).catch(() => []),
        api.get(`/campaigns/${s.campaign_id}`).then(r => r.data).catch(() => null),
      ]);
      setChat(c); setDice(d); setInit(i); setEffects(e); setCharacters(chs);
      setCampaign(camp);
    } catch (err) {
      // Session fetch failed — surface real message instead of hanging
      // on the OPENING THE TABLE min-delay forever.
      const detail = err?.response?.data?.detail || err?.message || "Session not found.";
      setLoadErr(typeof detail === "string" ? detail : "Session not found.");
    }
  };

  useEffect(() => { loadAll(); }, [id]);
  // Auto-select the first character the player actually owns (or the
  // single character if only one exists). Keeps the MacroBar and dice
  // character context sane without forcing the user to click the
  // dropdown every time they open a session.
  useEffect(() => {
    if (characterId) return;
    if (!characters.length) return;
    const mine = characters.find((c) => c.user_id === user?.id);
    setCharacterId((mine || characters[0]).id);
    // eslint-disable-next-line
  }, [characters]);
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [chat]);

  // WebSocket live updates (token-authenticated)
  useEffect(() => {
    const token = localStorage.getItem("tg_token");
    if (!token) return;
    const wsUrl = API.replace(/^http/, "ws") + `/ws/session/${id}?token=${encodeURIComponent(token)}`;
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onmessage = (e) => {
        let evt;
        try { evt = JSON.parse(e.data); } catch { return; }
        const { type, data } = evt;
        if (type === "chat") setChat((p) => [...p, data]);
        if (type === "dice") setDice((p) => [data, ...p]);
        if (type === "initiative") setInit((p) => [...p, data].sort((a,b)=>b.roll-a.roll));
        if (type === "initiative_remove") setInit((p) => p.filter(x => x.id !== data.id));
        if (type === "effect") setEffects((p) => [...p, data]);
        if (type === "effect_remove") setEffects((p) => p.filter(x => x.id !== data.id));
        if (type === "round") setSession((s) => ({ ...s, round: data.round }));
        if (type === "seating:update") {
          // Patch our local session.character_assignments map.
          setSession((s) => {
            if (!s) return s;
            const next = { ...(s.character_assignments || {}) };
            if (evt.character_id) next[evt.user_id] = evt.character_id;
            else delete next[evt.user_id];
            return { ...s, character_assignments: next };
          });
        }
        // Fan out to AVSeats subscribers (presence + WebRTC signaling)
        subsRef.current.forEach((h) => { try { h(evt); } catch {} });
      };
      ws.onerror = () => {};
    } catch {}
    return () => {
      try { ws && ws.close(); } catch {}
      wsRef.current = null;
    };
  }, [id]);

  // Min-display delay so the "Opening the table…" beat reads as ritual,
  // not a flash. Held ~5 s even after data resolves. When loadErr fires
  // we bypass the ritual and show the error so testing / real users
  // don't wait forever on a 404 session.
  const stillOpening = useMinDelay(!session && !loadErr, 5000);
  if (loadErr) {
    return (
      <div className="p-10 flex items-center justify-center min-h-[60vh]" data-testid="session-load-error">
        <div className="card-mystic p-6 max-w-md text-center">
          <div className="label-ref text-ember mb-2">The script slipped the Loremaster's hand</div>
          <div className="text-mist text-sm">{loadErr}</div>
          <Link to="/app/campaigns" className="btn btn-ghost mt-4 inline-flex">← Back to campaigns</Link>
        </div>
      </div>
    );
  }
  if (stillOpening) {
    return (
      <div className="p-10 flex items-center justify-center min-h-[60vh]" data-testid="session-loading">
        <div className="flex flex-col items-center gap-3">
          <div className="text-gold font-display tracking-[0.4em] text-sm animate-flicker">
            OPENING THE TABLE
          </div>
          <div className="text-mist/60 text-[10px] font-ui uppercase tracking-[0.3em]">
            Tuning the candles · {session ? "almost ready" : "fetching the script"}
          </div>
        </div>
      </div>
    );
  }
  if (!session) return null;

  const sendChat = async (e) => {
    e?.preventDefault();
    if (!msg.trim()) return;
    await api.post("/chat", { session_id: id, message: msg, kind: "chat" });
    setMsg("");
  };
  const rollDice = async () => {
    if (!roll.trim()) return;
    await api.post("/dice", {
      session_id: id, notation: roll, label, target: target ? +target : null,
      character_id: characterId || null, private: false,
    });
    setLabel("");
  };
  const addInit = async () => {
    const name = prompt("Name on initiative?");
    if (!name) return;
    const r = prompt("Roll / value? (e.g., Body+Mind+d6 result)", "10");
    await api.post("/initiative", {
      session_id: id, name, roll: parseInt(r) || 0, side: "npc",
    });
  };
  const addInitFromChar = async (c) => {
    const r = Math.floor(Math.random() * 6) + 1 + (c.stats.body || 0) + (c.stats.mind || 0);
    await api.post("/initiative", {
      session_id: id, name: c.name, character_id: c.id, roll: r, side: "pc",
    });
  };
  const addEffect = async () => {
    const target_name = prompt("Apply effect to whom?");
    if (!target_name) return;
    const name = prompt("Effect name?");
    if (!name) return;
    const duration = parseInt(prompt("Duration (rounds)?", "3")) || 1;
    await api.post("/effects", { session_id: id, target_name, name, duration_rounds: duration, note: "" });
  };
  const applyDamage = async (kind) => {
    const target_name = prompt(`Who takes ${kind.toUpperCase()} damage?`);
    if (!target_name) return;
    const amount = parseInt(prompt("Amount?")) || 0;
    if (!amount) return;
    await api.post("/damage", { session_id: id, target_name, amount, kind });
  };
  const advance = async () => {
    const { data } = await api.post(`/sessions/${id}/round/advance`);
    setSession((s) => ({ ...s, round: data.round }));
    await loadAll();
  };
  const generateRecap = async () => {
    setRecapBusy(true); setRecap(null);
    try {
      const { data } = await api.post(`/sessions/${id}/recap`, { style: recapStyle });
      setRecap(data);
    } catch (e) {
      setRecap({ error: e.response?.data?.detail || e.message });
    } finally { setRecapBusy(false); }
  };

  return (
    <div className="px-4 md:px-10 py-4 md:py-6 md:h-screen md:flex md:flex-col md:overflow-hidden"
         data-system={campaign?.system_id || "besm-4e"} data-testid="session-root">
      {/* AV Seats — voice/video strip above session panes */}
      <div className="mb-3 md:mb-4">
        <AVSeats
          subscribe={wsSubscribe}
          send={wsSend}
          sessionTitle={session.title}
          sessionId={id}
          campaign={campaign}
          characters={characters}
          initiative={init}
        />
      </div>

      <div className="md:flex-1 md:min-h-0 md:grid md:grid-cols-[280px_1fr_320px] gap-4 md:gap-6">
      {/* Mobile pane switcher */}
      <div className="md:hidden flex border-b border-gold/10 mb-3 sticky top-[52px] bg-void/90 backdrop-blur z-20" data-testid="session-mobile-tabs">
        {[
          ["chat", "Chat", MessageSquare],
          ["init", "Init", Users],
          ["dice", "Dice", Dice6],
        ].map(([k, l, I]) => (
          <button key={k} onClick={() => setMobilePane(k)}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-ui tracking-widest uppercase
                    ${mobilePane === k ? "text-gold-bright border-b-2 border-gold" : "text-mist/70"}`}
                  data-testid={`mobile-pane-${k}`}>
            <I className="w-4 h-4"/> {l}
          </button>
        ))}
      </div>

      {/* LEFT: Initiative + Effects */}
      <div className={`card-mystic p-4 md:overflow-y-auto md:scroll-stylish ${mobilePane === "init" ? "block" : "hidden md:block"}`}
           data-testid="initiative-panel">
        <Link to={`/app/campaigns/${session.campaign_id}`}
              className="text-[10px] font-ui uppercase tracking-widest text-gold/70">← Campaign</Link>
        <div className="label-ref mt-2">Round</div>
        <div className="flex items-center justify-between">
          <div className="font-display text-3xl text-gold-bright">{session.round || 0}</div>
          <button onClick={advance} className="btn btn-primary text-xs" data-testid="advance-round-btn">
            <ChevronRight className="w-3 h-3"/> Advance
          </button>
        </div>

        <div className="divider-sigil my-3"/>
        <div className="flex items-center justify-between mb-2">
          <div className="label-ref">Initiative</div>
          <button onClick={addInit} className="btn btn-ghost text-[10px]" data-testid="add-init-btn"><Plus className="w-3 h-3"/></button>
        </div>
        {init.length === 0 && <div className="text-mist italic text-[11px]">None.</div>}
        <div className="space-y-1.5">
          {init.map((i) => (
            <div key={i.id} className="flex items-center justify-between border border-gold/10 rounded-sm p-2"
                 data-testid={`init-${i.id}`}>
              <div className="min-w-0 flex-1">
                <div className="text-xs text-parchment font-ui truncate">{i.name}</div>
                <div className="text-[9px] text-mist uppercase tracking-widest">{i.side}</div>
              </div>
              <div className="font-display text-sm text-gold-bright mr-2">{i.roll}</div>
              <button onClick={async () => { await api.delete(`/initiative/${i.id}`); }}
                      className="text-ember/60 hover:text-ember"><X className="w-3 h-3"/></button>
            </div>
          ))}
        </div>

        <div className="divider-sigil my-3"/>
        <div className="label-ref mb-2">Take Seat · play this character</div>
        <div className="space-y-1.5" data-testid="take-seat-section">
          {(() => {
            const mine = characters.filter((c) => c.owner_id === user?.id);
            const seated = (session?.character_assignments || {})[user?.id];
            if (mine.length === 0) {
              return <div className="text-[10px] text-mist italic">No characters of yours in this campaign yet.</div>;
            }
            return (
              <>
                {mine.map((c) => {
                  const isSeated = seated === c.id;
                  return (
                    <button key={c.id} onClick={() => takeSeat(isSeated ? "" : c.id)}
                            className={`w-full text-left p-2 rounded-sm border ${
                              isSeated ? "border-gold bg-gold/10" : "border-gold/10 hover:border-gold/40 hover:bg-gold/5"
                            }`}
                            data-testid={`take-seat-${c.id}`}>
                      <div className="text-xs text-parchment font-ui flex items-center justify-between">
                        <span className="truncate">{c.name}</span>
                        {isSeated && <span className="text-[9px] text-gold-bright tracking-widest">SEATED</span>}
                      </div>
                      <div className="text-[9px] text-mist uppercase tracking-widest truncate">
                        {systemBlurb(c, campaign?.system_id)}
                      </div>
                    </button>
                  );
                })}
                {seated && (
                  <button onClick={() => takeSeat("")}
                          className="text-[10px] text-mist hover:text-ember w-full text-center mt-1"
                          data-testid="release-seat-btn">
                    Release seat
                  </button>
                )}
              </>
            );
          })()}
        </div>
        {/* Who else is seated (read-only summary) */}
        {Object.keys(session?.character_assignments || {}).length > 0 && (
          <div className="text-[10px] text-mist mt-2" data-testid="seating-summary">
            {Object.entries(session.character_assignments).map(([uid, cid]) => {
              if (uid === user?.id) return null;
              const ch = characters.find((x) => x.id === cid);
              if (!ch) return null;
              return (
                <div key={uid} className="truncate">
                  <span className="text-arcane-light">●</span> {ch.owner_name} → <span className="text-parchment">{ch.name}</span>
                </div>
              );
            })}
          </div>
        )}

        <div className="divider-sigil my-3"/>
        <div className="label-ref mb-2">Add to Initiative</div>
        <div className="space-y-1.5">
          {characters.map((c) => (
            <button key={c.id} onClick={() => addInitFromChar(c)}
                    className="w-full text-left p-2 border border-gold/10 rounded-sm hover:border-gold/40 hover:bg-gold/5"
                    data-testid={`seat-char-${c.id}`}>
              <div className="text-xs text-parchment font-ui">{c.name}</div>
              <div className="text-[9px] text-mist uppercase tracking-widest truncate">{systemBlurb(c, campaign?.system_id)}</div>
            </button>
          ))}
        </div>

        <div className="divider-sigil my-3"/>
        <div className="flex items-center justify-between mb-2">
          <div className="label-ref">Effects</div>
          <button onClick={addEffect} className="btn btn-ghost text-[10px]" data-testid="add-effect-btn"><Plus className="w-3 h-3"/></button>
        </div>
        {effects.length === 0 && <div className="text-mist italic text-[11px]">None active.</div>}
        <div className="space-y-1.5">
          {effects.map((e) => (
            <div key={e.id} className="border border-arcane/40 rounded-sm p-2 bg-arcane/10" data-testid={`effect-${e.id}`}>
              <div className="flex items-center justify-between">
                <div className="text-xs text-parchment font-ui">{e.name}</div>
                <button onClick={async () => { await api.delete(`/effects/${e.id}`); }}
                        className="text-ember/60 hover:text-ember"><X className="w-3 h-3"/></button>
              </div>
              <div className="text-[10px] text-mist font-ui">on {e.target_name} · {e.duration_rounds}r</div>
            </div>
          ))}
        </div>

        <div className="divider-sigil my-3"/>
        <div className="label-ref mb-2">Damage</div>
        <div className="flex gap-2">
          <button onClick={() => applyDamage("hp")} className="btn btn-ghost text-[10px] flex-1" data-testid="apply-hp-btn">
            <Heart className="w-3 h-3"/> HP
          </button>
          <button onClick={() => applyDamage("ep")} className="btn btn-ghost text-[10px] flex-1" data-testid="apply-ep-btn">
            <Zap className="w-3 h-3"/> EP
          </button>
        </div>
      </div>

      {/* CENTER: Chat */}
      <div className={`card-mystic p-4 md:p-5 flex flex-col min-h-[60vh] md:min-h-0 ${mobilePane === "chat" ? "flex" : "hidden md:flex"}`}
           data-testid="chat-panel">
        <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
          <div className="min-w-0 flex-1">
            <div className="label-ref">Live Session</div>
            <h1 className="font-display text-lg sm:text-xl md:text-2xl tracking-wide text-parchment truncate">{session.title}</h1>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap justify-end">
            <button onClick={() => setMapOpen(true)} className="btn btn-ghost text-[11px] sm:text-xs"
                    data-testid="open-battlemap-btn" title="Open the battlemap">
              <MapIcon className="w-3 h-3"/> <span className="hidden sm:inline">Map</span>
            </button>
            {campaign && (campaign.gm_id === user?.id || user?.role === "admin") && (
              <button onClick={() => setXpOpen(true)} className="btn btn-ghost text-[11px] sm:text-xs"
                      data-testid="open-xp-btn" title="Award session XP (BESM 4E p.232)">
                <Sparkles className="w-3 h-3"/> <span className="hidden sm:inline">XP</span>
              </button>
            )}
            <select className="select w-auto text-[11px] sm:text-xs" value={recapStyle}
                    onChange={(e) => setRecapStyle(e.target.value)} data-testid="recap-style"
                    title="Recap style">
              <option value="narrative">Narrative</option>
              <option value="bullet">Bulleted</option>
              <option value="in-character">In-character</option>
            </select>
            <button onClick={generateRecap} disabled={recapBusy} className="btn btn-ghost text-[11px] sm:text-xs"
                    data-testid="recap-btn" title="Generate Loremaster recap">
              <ScrollText className="w-3 h-3"/> <span className="hidden sm:inline">{recapBusy ? "Inscribing…" : "Recap"}</span>
            </button>
            <span className="tag hidden sm:inline-flex">{session.status}</span>
          </div>
        </div>
        <div className="divider-sigil"/>
        <div className="flex-1 overflow-y-auto scroll-stylish py-3 space-y-2">
          {chat.map((m) => (
            m.pinned ? (
              <div key={m.id} className="px-4 py-3 rounded-sm border-2 border-gold/40 bg-gold/5 sticky top-0 z-10"
                   data-testid={`pinned-recap-${m.id}`}>
                <div className="flex items-center gap-2 mb-2">
                  <ScrollText className="w-3 h-3 text-gold"/>
                  <span className="text-[10px] font-ui uppercase tracking-[0.25em] text-gold-bright">
                    Pinned · Last time at the table
                  </span>
                </div>
                <div className="text-sm text-parchment/95 font-body whitespace-pre-wrap leading-relaxed">{m.message}</div>
              </div>
            ) : (
              <div key={m.id} className={`px-3 py-2 rounded-sm border ${m.kind === "system" ? "border-arcane/40 bg-arcane/5" : "border-gold/5"}`}
                   data-testid={`chat-${m.id}`}>
                <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
                  {m.user_name} · {m.kind}
                </div>
                <div className="text-sm text-parchment font-body whitespace-pre-wrap">{m.message}</div>
              </div>
            )
          ))}
          <div ref={chatEnd}/>
        </div>
        <form onSubmit={sendChat} className="flex gap-2 pt-2 border-t border-gold/10">
          <input className="input flex-1" placeholder="Speak to the table…" value={msg}
                 onChange={(e) => setMsg(e.target.value)} data-testid="chat-input"/>
          <button type="submit" className="btn btn-primary" data-testid="chat-send-btn"><Send className="w-4 h-4"/></button>
        </form>
        {/* V6.25.36 — Push-to-talk for in-character speech. Audio is
            transcribed by Whisper and folded into the recap chronicle
            (NOT into player journals — those stay a player's own POV).
            V6.25.43 — wrapped above with the Scene Switcher so the GM
            can segment a session into named beats and PTT auto-mirrors
            into the active scene's target thread. */}
        <SceneSwitcher sessionId={id}
                       campaignId={campaign?.id || session?.campaign_id}
                       isGm={!!campaign?.is_gm || campaign?.gm_id === user?.id}
                       subscribe={wsSubscribe}/>
        <div className="flex items-center justify-between gap-2 mt-2">
          <PushToTalkButton sessionId={id}
                            characterId={characterId}
                            characterName={(characters.find((c) => c.id === characterId) || {}).name}/>
          <span className="text-[10px] text-mist/70 italic">
            Voice lines feed the recap, not journals — speak as your character.
          </span>
        </div>
      </div>

      {recap && (
        <div className="fixed inset-0 z-50 bg-void/90 backdrop-blur-md flex items-start justify-center p-2 sm:p-6 overflow-auto" data-testid="recap-modal">
          <div className="card-mystic sigil-ring w-full max-w-2xl p-4 sm:p-7 my-3 sm:my-10">
            <div className="flex items-center justify-between mb-3 gap-2">
              <div className="min-w-0">
                <div className="label-ref flex items-center gap-2"><Sparkles className="w-3 h-3"/> Loremaster's recap</div>
                <h2 className="font-display text-lg sm:text-2xl text-parchment tracking-wide mt-1 truncate">{session.title}</h2>
              </div>
              <button onClick={() => setRecap(null)} className="btn btn-ghost p-2 flex-shrink-0"><X className="w-4 h-4"/></button>
            </div>
            <div className="divider-sigil mb-4"/>
            {recap.error ? (
              <div className="text-ember text-sm">{recap.error}</div>
            ) : (
              <div className="text-parchment/95 font-body whitespace-pre-wrap leading-relaxed text-[15px]" data-testid="recap-text">
                {recap.text}
              </div>
            )}
            <div className="mt-4 text-[10px] font-ui uppercase tracking-widest text-mist/60">
              Generated by Claude Sonnet 4.5 · {recap.style || "narrative"}
            </div>
          </div>
        </div>
      )}

      {/* RIGHT: Dice log + roller */}
      <div className={`card-mystic p-4 flex-col min-h-[60vh] md:min-h-0 ${mobilePane === "dice" ? "flex" : "hidden md:flex"}`}
           data-testid="dice-panel">
        <div className="label-ref mb-2 flex items-center justify-between">
          <span>Dice Altar</span>
          <Dice6 className="w-4 h-4 text-gold"/>
        </div>
        <div className="space-y-2">
          <select className="select" value={characterId}
                  onChange={(e) => setCharacterId(e.target.value)} data-testid="dice-char-select">
            <option value="">— no character (flat) —</option>
            {characters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <input className="input" placeholder="e.g. 2d6-body" value={roll}
                 onChange={(e) => setRoll(e.target.value)} data-testid="session-roll-notation"/>
          <input className="input" placeholder="Label" value={label}
                 onChange={(e) => setLabel(e.target.value)}/>
          <input className="input" placeholder="Target (optional)" type="number" value={target}
                 onChange={(e) => setTarget(e.target.value)}/>
          <button onClick={rollDice} className="btn btn-primary w-full" data-testid="session-roll-btn">
            <Dice6 className="w-4 h-4"/> Roll
          </button>
          {/* System-native macros — populate notation+label from a
              character-aware button. Falls back to flat dice if no
              character is selected (dice-char-select == ""). */}
          <MacroBar
            systemId={campaign?.system_id || "besm-4e"}
            character={characters.find((c) => c.id === characterId) || null}
            onPick={(notation, lbl) => { setRoll(notation); setLabel(lbl); }}
          />
        </div>
        {/* V6.6/V6.7 — Encounter Designer (Anime 5E / D&D 5E XP-based, BESM 4E CP-based). */}
        {campaign?.is_gm
          && (campaign?.system_id === "anime-5e" || campaign?.system_id === "dnd-5e"
              || campaign?.system_id === "besm-4e") && (
          <EncounterDesigner className="mt-3"
                              partySize={(characters || []).length || 4}
                              campaignId={campaign?.id}
                              systemId={campaign?.system_id}/>
        )}
        <div className="divider-sigil my-3"/>
        <div className="label-ref mb-2">Log</div>
        <div className="flex-1 overflow-y-auto scroll-stylish space-y-2" data-testid="session-roll-log">
          {dice.map((d) => (
            <div key={d.id} className="border border-gold/10 rounded-sm p-2" data-testid={`dice-log-${d.id}`}>
              <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
                {d.user_name} · {d.notation}{d.label ? ` · ${d.label}` : ""}
              </div>
              <div className="font-display text-xl text-gold">{d.result?.total}</div>
              <div className="text-[10px] text-mist font-ui">
                {d.result?.rolls?.map((r, i) => (
                  <span key={i} className="mr-2">
                    {r.results ? `[${r.results.join(",")}]` : r.ref ? `${r.ref}:${r.value}` : ""}
                  </span>
                ))}
                {d.target != null && <span className={d.success ? "text-gold" : "text-ember"}> · TN {d.target}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
      </div>

      {/* Battlemap overlay — full-screen when toggled by the map button */}
      {mapOpen && (
        <div className="fixed inset-0 z-40 bg-void/90 backdrop-blur-md flex items-stretch justify-center p-1 sm:p-3 md:p-6 overflow-auto"
             data-testid="battlemap-overlay">
          <div className="w-full max-w-6xl">
            <Battlemap
              sessionId={id}
              campaign={campaign}
              characters={characters}
              initiative={init}
              user={user}
              subscribe={wsSubscribe}
              onClose={() => setMapOpen(false)}
            />
          </div>
        </div>
      )}

      {/* XP Award scorecard — GM-only, suggest-then-commit */}
      {xpOpen && campaign && (
        <XPAwardPanel
          sessionId={id}
          campaign={campaign}
          onClose={() => setXpOpen(false)}
          onCommitted={() => loadAll()}
        />
      )}

      {/* V6.25.26 — Anti-railroad encounters library: GM picks live during a session. */}
      {campaign?.is_gm && session && (
        <div className="mt-6 px-4">
          <EncountersLibrary campId={campaign.id || campaign._id || session.campaign_id}
                                sessionId={id} isGm={true}
                                systemId={campaign?.system_id}/>
        </div>
      )}

      {/* V6.17 — Floating Quick-Cast dock for the active player. */}
      {campaign && session && (
        <QuickCastDock sessionId={id} campaignId={campaign.id || campaign._id || session.campaign_id}/>
      )}
    </div>
  );
}
