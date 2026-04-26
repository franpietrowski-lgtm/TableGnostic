import React, { useEffect, useRef, useState, useCallback } from "react";
import { api } from "../lib/api";
import {
  Hash, Send, Plus, Pin, PinOff, MessageSquare, Smile,
  Trash2, X, Dice6, ChevronRight, AtSign,
} from "lucide-react";

/**
 * Discord-style PBP channels for a campaign.
 *
 * Layout:
 *   ┌──────────────┬─────────────────────────────────┐
 *   │ #channels    │   message stream                 │
 *   │ list         │   composer (markdown + slash)    │
 *   │              │   thread drawer (right slide-in) │
 *   └──────────────┴─────────────────────────────────┘
 *
 * Slash commands (parsed server-side):
 *   /roll 2d6+Body                 → dice message with computed total
 *   /me steps into the firelight    → emote
 *   /w @handle private aside        → whisper (still posted; rendered private)
 *
 * Real-time: V1 uses 4-second polling on the active channel; the backend
 * already broadcasts on a campaign room, ready for a WS upgrade in V1.5.
 */

const QUICK_REACTIONS = ["👍", "🎲", "✨", "🔥", "⚔️", "❤️"];
const POLL_MS = 4000;

export default function ChannelsPanel({ campaign, user }) {
  const isGm = !!campaign && (campaign.gm_id === user?.id || user?.role === "admin");
  const [channels, setChannels] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [openThreadFor, setOpenThreadFor] = useState(null); // message id
  const [threadDraft, setThreadDraft] = useState("");
  const [threadMsgs, setThreadMsgs] = useState([]);
  const [emojiFor, setEmojiFor] = useState(null); // msg id under the picker
  const endRef = useRef(null);

  // ─── load + poll ───
  const loadChannels = useCallback(async () => {
    if (!campaign?.id) return;
    const { data } = await api.get(`/campaigns/${campaign.id}/channels`);
    setChannels(data);
    if (!activeId && data[0]) setActiveId(data[0].id);
  }, [campaign?.id, activeId]);

  const loadMessages = useCallback(async () => {
    if (!activeId) return;
    const { data } = await api.get(`/channels/${activeId}/messages`);
    setMessages(data);
  }, [activeId]);

  useEffect(() => { loadChannels(); }, [loadChannels]);
  useEffect(() => { loadMessages(); }, [loadMessages]);

  useEffect(() => {
    if (!activeId) return;
    const t = setInterval(loadMessages, POLL_MS);
    return () => clearInterval(t);
  }, [activeId, loadMessages]);

  useEffect(() => {
    if (endRef.current) endRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, activeId]);

  // ─── actions ───
  const send = async () => {
    if (!draft.trim() || !activeId || busy) return;
    setBusy(true);
    try {
      const { data } = await api.post(`/channels/${activeId}/messages`, { body: draft });
      setMessages((prev) => [...prev, data]);
      setDraft("");
    } finally { setBusy(false); }
  };
  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const newChannel = async () => {
    if (!isGm) return;
    const name = window.prompt("New channel name (kebab-case, no #)?", "council");
    if (!name) return;
    const topic = window.prompt("Channel topic?", "");
    const { data } = await api.post(`/campaigns/${campaign.id}/channels`,
      { name: name.replace(/[^a-z0-9-]/gi, "-").toLowerCase(), topic, kind: "text", position: channels.length });
    setChannels((c) => [...c, data]);
    setActiveId(data.id);
  };

  const togglePin = async (m) => {
    if (!isGm) return;
    const { data } = await api.post(`/messages/${m.id}/pin`);
    setMessages((prev) => prev.map((x) => x.id === m.id ? { ...x, pinned: data.pinned } : x));
  };
  const deleteMsg = async (m) => {
    if (!window.confirm("Delete this message?")) return;
    await api.delete(`/messages/${m.id}`);
    setMessages((prev) => prev.filter((x) => x.id !== m.id));
  };
  const react = async (m, emoji) => {
    setEmojiFor(null);
    const { data } = await api.post(`/messages/${m.id}/reactions`, { emoji });
    setMessages((prev) => prev.map((x) => x.id === m.id ? { ...x, reactions: data.reactions } : x));
  };

  // ─── threads ───
  const openThread = async (m) => {
    setOpenThreadFor(m);
    setThreadMsgs([]);
    // First, find or create a thread anchored to this message
    const tList = await api.get(`/channels/${activeId}/threads`).then(r => r.data);
    let th = tList.find((t) => t.parent_msg_id === m.id);
    if (!th) {
      const { data } = await api.post(`/channels/${activeId}/threads`, {
        name: m.body.slice(0, 60), parent_msg_id: m.id,
      });
      th = data;
    }
    setOpenThreadFor({ ...m, _thread_id: th.id, _thread_name: th.name });
    const { data: tmsgs } = await api.get(`/channels/${activeId}/messages?thread_id=${th.id}`);
    setThreadMsgs(tmsgs);
  };
  const sendThread = async () => {
    if (!threadDraft.trim() || !openThreadFor?._thread_id) return;
    const { data } = await api.post(`/channels/${activeId}/messages`, {
      body: threadDraft, thread_id: openThreadFor._thread_id,
    });
    setThreadMsgs((p) => [...p, data]);
    setThreadDraft("");
  };

  // ─── render helpers ───
  const renderBody = (m) => {
    if (m.kind === "roll" && m.slash_meta?.result) {
      const r = m.slash_meta.result;
      const dice = r.rolls?.filter((x) => x.results) || [];
      return (
        <div className="space-y-1" data-testid={`channel-roll-${m.id}`}>
          <div className="font-display text-2xl text-gold-bright">{r.total}</div>
          <div className="text-[10px] font-ui text-mist uppercase tracking-widest">
            {m.slash_meta.notation} ·
            {dice.map((d, i) => (
              <span key={i} className="ml-1">[{d.results.join(",")}]</span>
            ))}
            {r.flat ? <span className="ml-1">{r.flat >= 0 ? "+" : ""}{r.flat}</span> : null}
          </div>
        </div>
      );
    }
    if (m.slash_meta?.kind === "emote") {
      return <em className="text-arcane-light">* {m.author_name} {m.slash_meta.text}</em>;
    }
    if (m.slash_meta?.kind === "whisper") {
      return (
        <div className="text-arcane-light italic">
          <AtSign className="w-3 h-3 inline mr-1"/>
          whispered to @{m.slash_meta.to_handle}: {m.slash_meta.text}
        </div>
      );
    }
    return <span className="whitespace-pre-wrap">{m.body}</span>;
  };

  const isMine = (m) => m.author_id === user?.id;
  const canDelete = (m) => isMine(m) || isGm;

  // Active channel reference
  const active = channels.find((c) => c.id === activeId);
  const pinned = messages.filter((m) => m.pinned);

  if (!campaign) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-3 md:gap-4 h-[70vh] md:h-[75vh]"
         data-testid="channels-panel">
      {/* Channel list */}
      <aside className="card-mystic p-3 overflow-y-auto scroll-stylish" data-testid="channels-list">
        <div className="flex items-center justify-between mb-2">
          <div className="label-ref">Channels</div>
          {isGm && (
            <button onClick={newChannel} className="btn btn-ghost text-[10px] px-2"
                    data-testid="channel-new-btn"><Plus className="w-3 h-3"/></button>
          )}
        </div>
        <div className="space-y-1">
          {channels.map((ch) => (
            <button key={ch.id}
                    onClick={() => setActiveId(ch.id)}
                    className={`w-full text-left px-2 py-1.5 rounded-sm text-sm font-ui flex items-center gap-1.5
                      ${ch.id === activeId ? "bg-gold/20 text-gold-bright" : "text-mist hover:bg-gold/5"}`}
                    data-testid={`channel-${ch.name}`}>
              <Hash className="w-3.5 h-3.5"/>
              <span className="truncate">{ch.name}</span>
            </button>
          ))}
        </div>
      </aside>

      {/* Stream + composer */}
      <section className="card-mystic p-4 flex flex-col min-h-0" data-testid="channel-stream">
        {active && (
          <div className="flex items-center gap-2 mb-2">
            <Hash className="w-5 h-5 text-gold"/>
            <h2 className="font-display text-xl text-parchment">{active.name}</h2>
            {active.topic && (
              <span className="text-[11px] font-ui text-mist/70 truncate">· {active.topic}</span>
            )}
          </div>
        )}
        <div className="divider-sigil"/>

        {pinned.length > 0 && (
          <div className="px-3 py-2 mb-2 border-2 border-gold/40 bg-gold/5 rounded-sm"
               data-testid="channel-pinned">
            <div className="text-[10px] font-ui uppercase tracking-widest text-gold-bright mb-1">
              <Pin className="w-3 h-3 inline mr-1"/> Pinned
            </div>
            {pinned.map((m) => (
              <div key={m.id} className="text-xs text-parchment">{m.author_name}: {m.body.slice(0, 100)}</div>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-y-auto scroll-stylish space-y-2 pr-1" data-testid="channel-messages">
          {messages.length === 0 && (
            <div className="text-mist italic text-[12px]">No messages yet. Speak first.</div>
          )}
          {messages.map((m) => (
            <div key={m.id}
                 className="group px-2.5 py-2 rounded-sm border border-gold/5 hover:border-gold/20 hover:bg-gold/5 relative"
                 data-testid={`channel-msg-${m.id}`}>
              <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60 flex items-center gap-2">
                <span>{m.author_name}</span>
                <span className="text-mist/40">·</span>
                <span className="text-mist/40">{new Date(m.created_at).toLocaleTimeString()}</span>
                {m.pinned && <Pin className="w-3 h-3 text-gold"/>}
                {m.edited_at && <span className="text-mist/40">(edited)</span>}
              </div>
              <div className="text-sm text-parchment font-body">{renderBody(m)}</div>

              {/* reactions */}
              {(m.reactions || []).length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {m.reactions.map((r) => (
                    <button key={r.emoji} onClick={() => react(m, r.emoji)}
                            className={`text-[11px] px-1.5 py-0.5 rounded border
                              ${r.uids.includes(user?.id) ? "border-gold/60 bg-gold/10" : "border-gold/15 bg-black/30"}`}
                            data-testid={`channel-msg-${m.id}-reaction-${r.emoji}`}>
                      {r.emoji} {r.uids.length}
                    </button>
                  ))}
                </div>
              )}

              {/* hover toolbar */}
              <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                <button onClick={() => setEmojiFor(emojiFor === m.id ? null : m.id)}
                        className="p-1 hover:text-gold-bright" title="React"
                        data-testid={`channel-msg-${m.id}-react-btn`}>
                  <Smile className="w-3.5 h-3.5"/>
                </button>
                <button onClick={() => openThread(m)} className="p-1 hover:text-gold-bright"
                        title="Open thread"
                        data-testid={`channel-msg-${m.id}-thread-btn`}>
                  <MessageSquare className="w-3.5 h-3.5"/>
                </button>
                {isGm && (
                  <button onClick={() => togglePin(m)} className="p-1 hover:text-gold-bright"
                          title={m.pinned ? "Unpin" : "Pin"}
                          data-testid={`channel-msg-${m.id}-pin-btn`}>
                    {m.pinned ? <PinOff className="w-3.5 h-3.5"/> : <Pin className="w-3.5 h-3.5"/>}
                  </button>
                )}
                {canDelete(m) && (
                  <button onClick={() => deleteMsg(m)} className="p-1 hover:text-ember"
                          title="Delete"
                          data-testid={`channel-msg-${m.id}-delete-btn`}>
                    <Trash2 className="w-3.5 h-3.5"/>
                  </button>
                )}
              </div>

              {emojiFor === m.id && (
                <div className="absolute top-7 right-1 z-30 bg-void border border-gold/40 rounded-sm p-1 flex gap-1 shadow-lg"
                     data-testid={`channel-msg-${m.id}-emoji-picker`}>
                  {QUICK_REACTIONS.map((e) => (
                    <button key={e} onClick={() => react(m, e)}
                            className="text-base hover:scale-125 transition-transform">
                      {e}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div ref={endRef}/>
        </div>

        <div className="border-t border-gold/10 pt-2 mt-2">
          <div className="flex gap-2">
            <input
              className="input flex-1"
              placeholder='Speak. Try /roll 2d6+Body or /me steps forward'
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKey}
              data-testid="channel-composer-input"
            />
            <button onClick={send} disabled={busy} className="btn btn-primary"
                    data-testid="channel-composer-send">
              <Send className="w-4 h-4"/>
            </button>
          </div>
          <div className="text-[10px] font-ui text-mist/50 uppercase tracking-widest mt-1">
            /roll <span className="text-gold/60">notation</span> ·
            /me <span className="text-gold/60">action</span> ·
            /w @<span className="text-gold/60">handle</span> message
          </div>
        </div>
      </section>

      {/* Thread drawer */}
      {openThreadFor && (
        <div className="fixed inset-0 z-50 bg-void/80 flex justify-end" data-testid="thread-drawer">
          <div className="w-full md:w-[420px] h-full bg-void/95 border-l border-gold/30 flex flex-col">
            <div className="flex items-center justify-between p-3 border-b border-gold/10">
              <div className="min-w-0">
                <div className="label-ref">Thread</div>
                <div className="text-sm text-parchment truncate">{openThreadFor._thread_name}</div>
              </div>
              <button onClick={() => setOpenThreadFor(null)} className="btn btn-ghost"
                      data-testid="thread-close-btn">
                <X className="w-4 h-4"/>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto scroll-stylish p-3 space-y-2">
              <div className="px-2.5 py-2 rounded-sm border border-gold/15 bg-gold/5">
                <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
                  {openThreadFor.author_name}
                </div>
                <div className="text-sm text-parchment">{openThreadFor.body}</div>
              </div>
              {threadMsgs.map((tm) => (
                <div key={tm.id} className="px-2.5 py-2 rounded-sm border border-gold/5"
                     data-testid={`thread-msg-${tm.id}`}>
                  <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
                    {tm.author_name}
                  </div>
                  <div className="text-sm text-parchment">{renderBody(tm)}</div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-gold/10 flex gap-2">
              <input className="input flex-1" placeholder="Reply in thread…"
                     value={threadDraft}
                     onChange={(e) => setThreadDraft(e.target.value)}
                     onKeyDown={(e) => e.key === "Enter" && sendThread()}
                     data-testid="thread-input"/>
              <button onClick={sendThread} className="btn btn-primary" data-testid="thread-send">
                <Send className="w-4 h-4"/>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
