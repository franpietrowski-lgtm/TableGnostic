import React, { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, API } from "../lib/api";
import { Dice6, Send, Plus, X, Swords, Heart, Zap, Skull, Shield, ChevronRight } from "lucide-react";

export default function SessionView() {
  const { id } = useParams();
  const [session, setSession] = useState(null);
  const [chat, setChat] = useState([]);
  const [dice, setDice] = useState([]);
  const [init, setInit] = useState([]);
  const [effects, setEffects] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [msg, setMsg] = useState("");
  const [roll, setRoll] = useState("2d6");
  const [label, setLabel] = useState("");
  const [target, setTarget] = useState("");
  const [characterId, setCharacterId] = useState("");
  const chatEnd = useRef(null);

  const loadAll = async () => {
    const s = await api.get(`/sessions/${id}`).then((r) => r.data);
    setSession(s);
    const [c, d, i, e, chs] = await Promise.all([
      api.get(`/sessions/${id}/chat`).then(r => r.data),
      api.get(`/sessions/${id}/dice`).then(r => r.data),
      api.get(`/sessions/${id}/initiative`).then(r => r.data),
      api.get(`/sessions/${id}/effects`).then(r => r.data),
      api.get(`/campaigns/${s.campaign_id}/characters`).then(r => r.data),
    ]);
    setChat(c); setDice(d); setInit(i); setEffects(e); setCharacters(chs);
  };

  useEffect(() => { loadAll(); }, [id]);
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [chat]);

  // WebSocket live updates
  useEffect(() => {
    const wsUrl = API.replace(/^http/, "ws") + `/ws/session/${id}`;
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (e) => {
        try {
          const { type, data } = JSON.parse(e.data);
          if (type === "chat") setChat((p) => [...p, data]);
          if (type === "dice") setDice((p) => [data, ...p]);
          if (type === "initiative") setInit((p) => [...p, data].sort((a,b)=>b.roll-a.roll));
          if (type === "initiative_remove") setInit((p) => p.filter(x => x.id !== data.id));
          if (type === "effect") setEffects((p) => [...p, data]);
          if (type === "effect_remove") setEffects((p) => p.filter(x => x.id !== data.id));
          if (type === "round") setSession((s) => ({ ...s, round: data.round }));
        } catch {}
      };
      ws.onerror = () => {};
    } catch {}
    return () => { try { ws && ws.close(); } catch {} };
  }, [id]);

  if (!session) return <div className="p-10 text-mist">Opening the table…</div>;

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

  return (
    <div className="px-6 md:px-10 py-6 h-screen overflow-hidden grid grid-cols-[280px_1fr_320px] gap-6">
      {/* LEFT: Initiative + Effects */}
      <div className="card-mystic p-4 overflow-y-auto scroll-stylish">
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
        <div className="label-ref mb-2">Seat Characters</div>
        <div className="space-y-1.5">
          {characters.map((c) => (
            <button key={c.id} onClick={() => addInitFromChar(c)}
                    className="w-full text-left p-2 border border-gold/10 rounded-sm hover:border-gold/40 hover:bg-gold/5"
                    data-testid={`seat-char-${c.id}`}>
              <div className="text-xs text-parchment font-ui">{c.name}</div>
              <div className="text-[9px] text-mist uppercase tracking-widest">Body {c.stats.body} · Mind {c.stats.mind}</div>
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
      <div className="card-mystic p-5 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="label-ref">Live Session</div>
            <h1 className="font-display text-2xl tracking-wide text-parchment">{session.title}</h1>
          </div>
          <span className="tag">{session.status}</span>
        </div>
        <div className="divider-sigil"/>
        <div className="flex-1 overflow-y-auto scroll-stylish py-3 space-y-2">
          {chat.map((m) => (
            <div key={m.id} className={`px-3 py-2 rounded-sm border ${m.kind === "system" ? "border-arcane/40 bg-arcane/5" : "border-gold/5"}`}
                 data-testid={`chat-${m.id}`}>
              <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
                {m.user_name} · {m.kind}
              </div>
              <div className="text-sm text-parchment font-body whitespace-pre-wrap">{m.message}</div>
            </div>
          ))}
          <div ref={chatEnd}/>
        </div>
        <form onSubmit={sendChat} className="flex gap-2 pt-2 border-t border-gold/10">
          <input className="input flex-1" placeholder="Speak to the table…" value={msg}
                 onChange={(e) => setMsg(e.target.value)} data-testid="chat-input"/>
          <button type="submit" className="btn btn-primary" data-testid="chat-send-btn"><Send className="w-4 h-4"/></button>
        </form>
      </div>

      {/* RIGHT: Dice log + roller */}
      <div className="card-mystic p-4 flex flex-col min-h-0">
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
        </div>
        <div className="divider-sigil my-3"/>
        <div className="label-ref mb-2">Log</div>
        <div className="flex-1 overflow-y-auto scroll-stylish space-y-2">
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
  );
}
