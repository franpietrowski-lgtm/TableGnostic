import React, { useEffect, useRef, useState, useCallback } from "react";
import { api, API } from "../lib/api";
import {
  Hash, Send, Plus, Pin, PinOff, MessageSquare, Smile,
  Trash2, X, Dice6, ChevronRight, AtSign, Image as ImageIcon, Paperclip,
} from "lucide-react";

/**
 * Discord-style PBP channels for a campaign.
 *
 * V2 additions:
 *   * Real-time over /api/ws/campaign/{cid} — falls back to 4 s polling.
 *   * @mention autocomplete picker — typing "@" opens a member list driven
 *     by GET /api/campaigns/{cid}/members; arrow keys + Tab/Enter to insert.
 *   * URL-based image attachments — the Image button accepts a public URL
 *     (avoids needing an upload pipeline; the user can paste any CDN link).
 */

const QUICK_REACTIONS = ["👍", "🎲", "✨", "🔥", "⚔️", "❤️"];
const POLL_MS = 8000;  // slow fallback poll; the WS handles real-time

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
  // V2 — @mention autocomplete + WS state
  const [members, setMembers] = useState([]);
  const [mention, setMention] = useState(null); // { matches, index } when @ active
  const wsRef = useRef(null);
  const wsConnectedRef = useRef(false);
  const inputRef = useRef(null);
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

  // ─── V2: members for @mention autocomplete ───
  useEffect(() => {
    if (!campaign?.id) return;
    api.get(`/campaigns/${campaign.id}/members`)
      .then((r) => setMembers(r.data))
      .catch(() => setMembers([]));
  }, [campaign?.id]);

  // ─── V2: campaign WebSocket for real-time channel updates ───
  useEffect(() => {
    if (!campaign?.id) return;
    const token = (document.cookie.match(/access=([^;]+)/) || [])[1]
                  || localStorage.getItem("access_token");
    if (!token) return;  // still falls back to polling
    const wsUrl = `${API.replace(/^http/, "ws")}/ws/campaign/${campaign.id}?token=${encodeURIComponent(token)}`;
    let ws;
    try { ws = new WebSocket(wsUrl); } catch { return; }
    wsRef.current = ws;
    ws.onopen = () => { wsConnectedRef.current = true; };
    ws.onclose = () => { wsConnectedRef.current = false; };
    ws.onerror = () => { wsConnectedRef.current = false; };
    ws.onmessage = (ev) => {
      let evt; try { evt = JSON.parse(ev.data); } catch { return; }
      const { type, data } = evt || {};
      if (type === "channel:msg") {
        // Insert or replace (covers edits)
        setMessages((prev) => {
          if (data.channel_id !== activeId) return prev;
          if (data.thread_id) return prev;  // root only; thread shown in drawer
          const others = prev.filter((m) => m.id !== data.id);
          return [...others, data].sort((a, b) => a.created_at.localeCompare(b.created_at));
        });
        // Thread updates
        setThreadMsgs((prev) => {
          if (!openThreadFor || data.thread_id !== openThreadFor._thread_id) return prev;
          const others = prev.filter((m) => m.id !== data.id);
          return [...others, data].sort((a, b) => a.created_at.localeCompare(b.created_at));
        });
      }
      else if (type === "channel:msg-delete") {
        setMessages((prev) => prev.filter((m) => m.id !== data.id));
        setThreadMsgs((prev) => prev.filter((m) => m.id !== data.id));
      }
      else if (type === "channel:reaction") {
        setMessages((prev) => prev.map((m) => m.id === data.msg_id ? { ...m, reactions: data.reactions } : m));
        setThreadMsgs((prev) => prev.map((m) => m.id === data.msg_id ? { ...m, reactions: data.reactions } : m));
      }
      else if (type === "channel:pin") {
        setMessages((prev) => prev.map((m) => m.id === data.msg_id ? { ...m, pinned: data.pinned } : m));
      }
    };
    return () => { try { ws.close(); } catch {} };
  }, [campaign?.id, activeId, openThreadFor]);

  useEffect(() => {
    if (!activeId) return;
    // Slow polling as a WS fallback / catch-up. WS handles realtime; this
    // only matters when the WS dropped or was never opened.
    const t = setInterval(() => { if (!wsConnectedRef.current) loadMessages(); }, POLL_MS);
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
      // The WS will deliver this to all subscribers (including us) — but to
      // make composing feel snappy on flaky networks, we still optimistically
      // append. A duplicate would be dedup'd by the WS handler (replaces by id).
      setMessages((prev) => {
        if (prev.find((m) => m.id === data.id)) return prev;
        return [...prev, data];
      });
      setDraft("");
      setMention(null);
    } finally { setBusy(false); }
  };

  // ─── V2: @mention autocomplete ───
  // Detect a "@partial" right before the cursor; render a picker; arrow keys
  // navigate it; Tab/Enter inserts the matched handle.
  const updateMentionState = (value, caret) => {
    const sub = value.slice(0, caret);
    const m = sub.match(/(?:^|\s)@([A-Za-z0-9_-]*)$/);
    if (!m) { setMention(null); return; }
    const partial = m[1].toLowerCase();
    const matches = members.filter((mb) =>
      mb.handle.startsWith(partial) || mb.name.toLowerCase().includes(partial),
    ).slice(0, 6);
    if (!matches.length) { setMention(null); return; }
    setMention({ matches, index: 0, partial, caret });
  };
  const insertMention = (m) => {
    const ta = inputRef.current;
    if (!ta) return;
    const caret = ta.selectionStart || draft.length;
    const sub = draft.slice(0, caret);
    const replaced = sub.replace(/@[A-Za-z0-9_-]*$/, `@${m.handle} `);
    const next = replaced + draft.slice(caret);
    setDraft(next);
    setMention(null);
    setTimeout(() => {
      ta.focus();
      const pos = replaced.length;
      ta.setSelectionRange(pos, pos);
    }, 0);
  };

  const onKey = (e) => {
    // Mention picker steers Up/Down/Enter/Tab/Esc when active.
    if (mention) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setMention((m) => ({ ...m, index: (m.index + 1) % m.matches.length }));
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setMention((m) => ({ ...m, index: (m.index - 1 + m.matches.length) % m.matches.length }));
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        insertMention(mention.matches[mention.index]);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setMention(null);
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const onComposerChange = (e) => {
    const v = e.target.value;
    setDraft(v);
    updateMentionState(v, e.target.selectionStart);
  };

  // Image attachment — paste a public URL. Skips a full upload pipeline so
  // it works today; user can use any CDN link (Imgur, Discord cdn, etc.).
  const attachImage = async () => {
    const url = window.prompt("Paste a public image URL (or any file URL):");
    if (!url) return;
    const name = window.prompt("Display name?", url.split("/").pop()) || "attachment";
    const isImg = /\.(png|jpe?g|webp|gif|avif)(\?|$)/i.test(url);
    const body = isImg ? `![${name}](${url})` : `[${name}](${url})`;
    setDraft((d) => d + (d ? " " : "") + body);
    setTimeout(() => inputRef.current?.focus(), 0);
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
  // Light markdown — renders ![name](url) as <img> and [name](url) as a link.
  // Plain text otherwise; preserves newlines.
  const renderText = (text) => {
    if (!text) return null;
    const parts = [];
    const re = /(!?\[([^\]]+)\]\(([^)\s]+)\))/g;
    let lastIdx = 0, m, key = 0;
    while ((m = re.exec(text)) !== null) {
      if (m.index > lastIdx) parts.push(text.slice(lastIdx, m.index));
      const isImg = m[0].startsWith("!");
      const name = m[2];
      const url = m[3];
      if (isImg) {
        parts.push(
          <img key={`a${key++}`} src={url} alt={name}
               className="my-2 max-h-64 rounded border border-gold/30"
               loading="lazy"/>,
        );
      } else {
        parts.push(
          <a key={`a${key++}`} href={url} target="_blank" rel="noopener noreferrer"
             className="text-arcane-light underline">{name}</a>,
        );
      }
      lastIdx = m.index + m[0].length;
    }
    if (lastIdx < text.length) parts.push(text.slice(lastIdx));
    return <span className="whitespace-pre-wrap">{parts}</span>;
  };

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
    // V6.25.6 — Cut B chat hot-keys.
    if (m.kind === "cast" || m.slash_meta?.kind === "cast") {
      const r = m.slash_meta?.resolved || {};
      return (
        <div className="border-l-2 border-arcane/50 pl-2" data-testid={`channel-cast-${m.id}`}>
          <div className="text-arcane-light font-display text-sm">
            ✦ {m.author_name} casts <span className="text-gold-bright">{m.slash_meta?.name || r.name}</span>
          </div>
          {r.hit ? (
            <div className="text-[11px] text-mist mt-0.5">
              {r.level != null && `Lvl ${r.level}`}
              {r.school && ` · ${r.school}`}
              {r.cost && ` · ${r.cost}`}
              {r.effect && <div className="text-parchment/85 mt-1 italic">{r.effect.slice(0, 200)}</div>}
            </div>
          ) : (
            <div className="text-[11px] text-ember/70 italic mt-0.5">
              ✗ Not in this campaign's spell pool. Cast as flavour only.
            </div>
          )}
        </div>
      );
    }
    if (m.kind === "use_bundle" || m.slash_meta?.kind === "use_bundle") {
      const r = m.slash_meta?.resolved || {};
      return (
        <div className="border-l-2 border-gold/50 pl-2" data-testid={`channel-bundle-${m.id}`}>
          <div className="text-gold-bright font-display text-sm">
            ⚡ {m.author_name} invokes <span className="text-parchment">{m.slash_meta?.name || r.name}</span>
          </div>
          {r.hit ? (
            <div className="text-[11px] text-mist mt-0.5">
              {r.invocation && `${r.invocation}`}
              {r.charges_max != null && ` · ${r.charges_max}× / scene`}
              {r.energy_cost ? ` · EP ${r.energy_cost}` : ""}
              {r.cooldown && ` · cooldown ${r.cooldown}`}
              {r.description && <div className="text-parchment/85 mt-1 italic">{r.description.slice(0, 200)}</div>}
            </div>
          ) : (
            <div className="text-[11px] text-ember/70 italic mt-0.5">
              ✗ No bundle by that name. Invoked as flavour only.
            </div>
          )}
        </div>
      );
    }
    if (m.kind === "spend_xp" || m.slash_meta?.kind === "spend_xp") {
      const p = m.slash_meta?.proposal || {};
      return (
        <div className="border-l-2 border-gold-bright/60 pl-2" data-testid={`channel-spend-${m.id}`}>
          <div className="text-gold-bright font-display text-sm">
            ↟ {m.author_name} proposes a {m.slash_meta?.amount} XP spend
            {p.character_name && <span className="text-mist text-[11px] ml-1">on {p.character_name}</span>}
          </div>
          <div className="text-[11px] text-mist italic mt-0.5">"{m.slash_meta?.reason}"</div>
          {p.error ? (
            <div className="text-[11px] text-ember/70 mt-0.5">✗ {p.error}</div>
          ) : (
            <div className="text-[11px] text-arcane-light mt-0.5">
              ✓ Queued — GM review pending in the XP Approval Queue.
            </div>
          )}
        </div>
      );
    }
    return renderText(m.body);
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

        <div className="border-t border-gold/10 pt-2 mt-2 relative">
          {/* @mention autocomplete picker */}
          {mention && (
            <div className="absolute left-0 right-0 -top-1 -translate-y-full bg-void border border-gold/40 rounded-sm shadow-lg z-30"
                 data-testid="channel-mention-picker">
              {mention.matches.map((m, i) => (
                <button key={m.id}
                        type="button"
                        onMouseDown={(e) => { e.preventDefault(); insertMention(m); }}
                        className={`w-full text-left px-3 py-1.5 text-sm font-ui flex items-center gap-2
                          ${i === mention.index ? "bg-gold/20 text-gold-bright" : "text-parchment hover:bg-gold/10"}`}
                        data-testid={`channel-mention-${m.handle}`}>
                  <AtSign className="w-3 h-3 text-gold/70"/>
                  <span>{m.handle}</span>
                  <span className="text-mist/60 text-[11px] ml-1">{m.name}</span>
                  {m.is_gm && <span className="ml-auto text-[10px] text-gold/60 uppercase tracking-widest">GM</span>}
                </button>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <button onClick={attachImage} className="btn btn-ghost px-2"
                    title="Attach an image or file by URL"
                    data-testid="channel-attach-btn">
              <ImageIcon className="w-4 h-4"/>
            </button>
            <input
              ref={inputRef}
              className="input flex-1"
              placeholder='Speak. Try /roll 2d6+Body or @handle to mention'
              value={draft}
              onChange={onComposerChange}
              onKeyDown={onKey}
              data-testid="channel-composer-input"
            />
            <button onClick={send} disabled={busy} className="btn btn-primary"
                    data-testid="channel-composer-send">
              <Send className="w-4 h-4"/>
            </button>
          </div>
          <div className="text-[10px] font-ui text-mist/50 uppercase tracking-widest mt-1 flex items-center gap-2 flex-wrap">
            <span>/roll <span className="text-gold/60">notation</span></span>
            <span>/me <span className="text-gold/60">action</span></span>
            <span>/w @<span className="text-gold/60">handle</span> message</span>
            <span title="Cast a spell from the campaign reference / homebrew pool.">/cast <span className="text-gold/60">name</span></span>
            <span title="Invoke a Power Bundle from the campaign pool.">/use bundle <span className="text-gold/60">name</span></span>
            <span title="Propose an XP spend on your character — GM approves.">/spend xp <span className="text-gold/60">N for reason</span></span>
            <span className="ml-auto">{wsConnectedRef.current ? "● live" : "○ polling"}</span>
          </div>
        </div>
      </section>

      {/* Thread drawer */}
      {openThreadFor && (
        <div className="fixed inset-0 z-50 bg-void/90 backdrop-blur-md flex justify-end" data-testid="thread-drawer">
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
