import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Users, Map, ScrollText, Swords, X, CornerDownLeft } from "lucide-react";
import { api } from "../lib/api";

/**
 * CmdKPalette — V6.13 global search overlay, cross-platform Cmd+K / Ctrl+K.
 *
 * Searches across every campaign the user can see + its codex nodes,
 * characters, and sessions via `GET /api/search`. Result list is
 * keyboard-navigable (↑/↓ + Enter) and escape-closes. Shown as a modal
 * centred near the top of the viewport so it behaves like a command
 * bar across the whole authenticated shell.
 */
const ICONS = {
  campaign: ScrollText,
  node: Map,
  character: Users,
  session: Swords,
};

const TYPE_ACCENT = {
  campaign: "#C8A34A",
  node: "#3FAA62",
  character: "#E03A8E",
  session: "#3F8FAA",
};

export default function CmdKPalette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [rows, setRows] = useState([]);
  const [cursor, setCursor] = useState(0);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);
  const nav = useNavigate();

  // Global hotkey toggle.
  useEffect(() => {
    const onKey = (ev) => {
      const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
      const mod = isMac ? ev.metaKey : ev.ctrlKey;
      if (mod && (ev.key === "k" || ev.key === "K")) {
        ev.preventDefault();
        setOpen((prev) => !prev);
      }
      if (open && ev.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  // Focus on open.
  useEffect(() => {
    if (open) {
      setQ(""); setRows([]); setCursor(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Debounced fetch.
  useEffect(() => {
    if (!open) return;
    if (q.trim().length < 2) { setRows([]); return; }
    const t = setTimeout(async () => {
      setBusy(true);
      try {
        const { data } = await api.get(`/search?q=${encodeURIComponent(q)}`);
        setRows(data || []);
        setCursor(0);
      } catch (_) { setRows([]); }
      finally { setBusy(false); }
    }, 180);
    return () => clearTimeout(t);
  }, [q, open]);

  // Arrow / enter.
  const onKeyDown = (ev) => {
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      setCursor((c) => Math.min(rows.length - 1, c + 1));
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      setCursor((c) => Math.max(0, c - 1));
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      const row = rows[cursor];
      if (row) { pick(row); }
    }
  };

  const pick = (row) => {
    setOpen(false);
    if (row?.url) nav(row.url);
  };

  // Group by type for readability.
  const grouped = useMemo(() => {
    const out = {};
    for (const r of rows) { (out[r.type] = out[r.type] || []).push(r); }
    return out;
  }, [rows]);

  if (!open) {
    // Render a tiny help hint (Cmd+K) pinned nowhere — the global
    // listener handles everything; we just need the DOM node for the
    // listener to live on. Empty fragment keeps the shell layout sane.
    return null;
  }

  let runningIdx = 0;

  return (
    <div className="fixed inset-0 z-[60] bg-void/90 backdrop-blur-md flex items-start justify-center pt-[8vh] p-4"
         onClick={() => setOpen(false)}
         data-testid="cmdk-overlay">
      <div className="w-full max-w-xl card-mystic p-0 overflow-hidden sigil-ring"
           onClick={(e) => e.stopPropagation()}
           data-testid="cmdk-palette">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-gold/20">
          <Search className="w-4 h-4 text-gold/70 flex-shrink-0"/>
          <input ref={inputRef}
                 className="flex-1 bg-transparent outline-none text-parchment placeholder:text-mist/50 text-sm font-ui"
                 placeholder="Search campaigns, codex, characters, sessions…"
                 value={q}
                 onChange={(e) => setQ(e.target.value)}
                 onKeyDown={onKeyDown}
                 data-testid="cmdk-input"/>
          <div className="text-[9px] text-mist/60 font-ui uppercase tracking-widest">
            {busy ? "…" : rows.length ? `${rows.length} hits` : ""}
          </div>
          <button onClick={() => setOpen(false)} className="text-mist/60 hover:text-parchment"
                  data-testid="cmdk-close">
            <X className="w-4 h-4"/>
          </button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto scroll-stylish">
          {q.trim().length < 2 && (
            <div className="px-4 py-6 text-[11px] text-mist/60 italic text-center"
                 data-testid="cmdk-empty">
              Type at least 2 characters. Open from anywhere with <kbd className="border border-gold/20 rounded-sm px-1.5 py-0.5 text-mist mx-0.5">⌘K</kbd> / <kbd className="border border-gold/20 rounded-sm px-1.5 py-0.5 text-mist mx-0.5">Ctrl+K</kbd>.
            </div>
          )}
          {q.trim().length >= 2 && rows.length === 0 && !busy && (
            <div className="px-4 py-6 text-[11px] text-mist/60 italic text-center"
                 data-testid="cmdk-no-results">
              No matches across your tables.
            </div>
          )}
          {Object.entries(grouped).map(([type, items]) => {
            const Icon = ICONS[type] || Search;
            const accent = TYPE_ACCENT[type] || "#C8A34A";
            return (
              <div key={type} data-testid={`cmdk-group-${type}`}>
                <div className="px-4 py-1 text-[9px] uppercase tracking-widest font-ui sticky top-0 bg-void/90 backdrop-blur-sm"
                     style={{ color: accent }}>
                  {type === "node" ? "Codex nodes" : `${type}s`}
                </div>
                {items.map((r) => {
                  const idx = runningIdx++;
                  const isActive = cursor === idx;
                  return (
                    <button key={`${r.type}-${r.id}`}
                            onClick={() => pick(r)}
                            onMouseEnter={() => setCursor(idx)}
                            className={`w-full text-left px-4 py-2 flex items-start gap-3 transition-colors ${isActive ? "bg-gold/10" : "hover:bg-gold/5"}`}
                            data-testid={`cmdk-result-${r.type}-${r.id}`}>
                      <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: accent }}/>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-parchment font-ui truncate">{r.title}</div>
                        <div className="text-[11px] text-mist truncate">
                          {r.subtitle || r.campaign_name}
                        </div>
                      </div>
                      {isActive && (
                        <CornerDownLeft className="w-3 h-3 text-gold-bright flex-shrink-0 mt-1"/>
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
        <div className="px-4 py-2 border-t border-gold/10 text-[9px] text-mist/60 font-ui uppercase tracking-widest flex justify-between items-center">
          <span>↑ ↓ navigate · ↵ open · Esc close</span>
          <span>TableGnostic Cmd-K</span>
        </div>
      </div>
    </div>
  );
}
