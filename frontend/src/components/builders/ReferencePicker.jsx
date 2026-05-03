/**
 * ReferencePicker — V6.21 dropdown selector backed by the SRD catalog.
 *
 * Replaces the old free-text `FreeList` for inventory, spells, armor,
 * and magic-item entries across the character sheet and builder flows.
 *
 * Props:
 *   - title        : Card header ("Inventory", "Spells Known", etc.)
 *   - placeholder  : Input placeholder text.
 *   - values       : Array of existing entries (strings OR dict entries
 *                    shaped {name, damage, ac, level, school, ...}).
 *   - onChange     : (next[]) => void
 *   - testidPrefix : data-testid prefix for every interactive element.
 *   - systemId     : "dnd-5e" / "anime-5e" / "cypher" — selects the
 *                    canonical SRD catalog to search.
 *   - kinds        : Array of catalog keys to include, e.g.
 *                    ["weapons","armor","items"] for inventory, or
 *                    ["spells"] for spells.
 *   - campaignId   : (optional) — if set, also fetches the campaign's
 *                    custom references (ReferenceEditor entries).
 *   - maxSpellLevel: (optional) — filter spell list by level ≤ N.
 *
 * UX:
 *   - Existing entries render as rich chips (damage / AC / level badge).
 *   - Click a chip to open its full reference entry inline (V6.21 auto-
 *     link — dispatches `tg:open-reference` event on click).
 *   - Type → autocomplete dropdown shows matching catalog entries with
 *     their mechanical tags (damage / AC / spell level).
 *   - Pick → adds as a rich object entry.
 *   - ↵ on an unknown string → adds as free-text (fallback for homebrew).
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../lib/api";
import { Plus, X, Search, Sparkles, ExternalLink } from "lucide-react";

export default function ReferencePicker({
  title, placeholder, values, onChange, testidPrefix,
  systemId = "dnd-5e", kinds = ["weapons", "armor", "items"],
  campaignId = null, maxSpellLevel = null,
}) {
  const [draft, setDraft] = useState("");
  const [open, setOpen] = useState(false);
  const [catalog, setCatalog] = useState([]);
  const [custom, setCustom] = useState([]);
  const [activeIdx, setActiveIdx] = useState(-1);
  const boxRef = useRef(null);

  // Load SRD catalog for the picked kinds.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get(`/systems/${systemId}/reference`);
        const merged = [];
        kinds.forEach((k) => {
          const bucket = data?.[k] || [];
          bucket.forEach((e) => merged.push({ ...e, __kind: k }));
        });
        if (!cancelled) setCatalog(merged);
      } catch { /* silent */ }
    })();
    return () => { cancelled = true; };
  }, [systemId, kinds.join(",")]);

  // Load campaign-scoped custom reference entries (homebrew / GM additions).
  useEffect(() => {
    if (!campaignId) { setCustom([]); return; }
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get(`/campaigns/${campaignId}/references`);
        const all = (data?.entries || data || []).filter((e) => {
          const k = (e.kind || "").toLowerCase();
          if (kinds.includes("weapons") && (k === "weapons" || k === "weapon")) return true;
          if (kinds.includes("armor") && k === "armor") return true;
          if (kinds.includes("items") && (k === "items" || k === "item")) return true;
          if (kinds.includes("spells") && (k === "spells" || k === "spell")) return true;
          return false;
        });
        if (!cancelled) setCustom(all);
      } catch { /* optional */ }
    })();
    return () => { cancelled = true; };
  }, [campaignId, kinds.join(",")]);

  // Filtered autocomplete list.
  const suggestions = useMemo(() => {
    const q = (draft || "").trim().toLowerCase();
    const pool = [...catalog, ...custom.map((c) => ({ ...c, __kind: c.kind, __custom: true }))];
    let out = pool;
    if (maxSpellLevel != null) {
      out = out.filter((e) => (e.level ?? 0) <= maxSpellLevel);
    }
    if (q) {
      out = out.filter((e) =>
        (e.name || "").toLowerCase().includes(q) ||
        (e.damage || "").toLowerCase().includes(q) ||
        (e.school || "").toLowerCase().includes(q) ||
        (e.kind || "").toLowerCase().includes(q) ||
        (e.effect || "").toLowerCase().includes(q) ||  // V6.23 — cypher
        (e.role || "").toLowerCase().includes(q)       // V6.23 — cypher focus
      );
    }
    return out.slice(0, 12);
  }, [catalog, custom, draft, maxSpellLevel]);

  // Close dropdown on outside click.
  useEffect(() => {
    const h = (e) => {
      if (!boxRef.current?.contains(e.target)) { setOpen(false); setActiveIdx(-1); }
    };
    window.addEventListener("mousedown", h);
    return () => window.removeEventListener("mousedown", h);
  }, []);

  const addEntry = (entry) => {
    // `entry` may be a plain string (fallback free-text) or a catalog dict.
    const next = [...(values || []), entry];
    onChange(next);
    setDraft(""); setOpen(false); setActiveIdx(-1);
  };

  const commitDraft = () => {
    if (!draft.trim()) return;
    const match = suggestions[activeIdx] || suggestions[0];
    if (match && match.name.toLowerCase() === draft.trim().toLowerCase()) {
      addEntry(match);
    } else if (activeIdx >= 0 && suggestions[activeIdx]) {
      addEntry(suggestions[activeIdx]);
    } else {
      // Fallback: free-text homebrew.
      addEntry(draft.trim());
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(suggestions.length - 1, i + 1));
      setOpen(true);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      commitDraft();
    } else if (e.key === "Escape") {
      setOpen(false); setActiveIdx(-1);
    }
  };

  const openReference = (entry) => {
    // V6.21 — Reference auto-link. Dispatches an event the parent
    // CharacterSheet listens for to open the ReferenceBrowser modal
    // focused on the picked entry.
    const name = typeof entry === "string" ? entry : entry.name;
    window.dispatchEvent(new CustomEvent("tg:open-reference", {
      detail: { system_id: systemId, kind: entry.__kind || entry.kind || "items", name },
    }));
  };

  return (
    <div className={`card-mystic p-4 mt-4 ${open ? "relative z-50" : ""}`}
         data-testid={`${testidPrefix}-picker`}
         style={open ? { isolation: "isolate" } : undefined}>
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="h-arcane text-sm">{title}</h3>
        <span className="text-[10px] text-mist italic">
          {catalog.length + custom.length} entries in catalog
          {custom.length > 0 && ` (${custom.length} homebrew)`}
        </span>
      </div>

      {/* Existing entries as rich chips. */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {(values || []).length === 0 && (
          <span className="text-[11px] text-mist italic">Empty — add entries below.</span>
        )}
        {(values || []).map((v, i) => {
          const isObj = typeof v === "object" && v !== null;
          const name = isObj ? (v.name || "—") : String(v);
          const hint = isObj
            ? [v.damage, v.ac, v.level != null ? `L${v.level}` : null,
                v.school, v.cost, v.kind, v.category,
                v.effect, v.role, v.form]  // V6.23 cypher fields
              .filter(Boolean).join(" · ")
            : "";
          return (
            <span key={i} className="tag group inline-flex items-center gap-1"
                  data-testid={`${testidPrefix}-chip-${i}`}>
              <button onClick={() => openReference(v)}
                      className="hover:text-gold-bright cursor-pointer"
                      title={`Open reference for ${name}`}
                      data-testid={`${testidPrefix}-chip-open-${i}`}>
                <ExternalLink className="w-2.5 h-2.5 inline mr-1 opacity-60"/>
                {name}
              </button>
              {hint && <span className="text-[10px] text-mist">· {hint}</span>}
              <button onClick={() => onChange(values.filter((_, j) => j !== i))}
                      className="ml-0.5 hover:text-ember"
                      data-testid={`${testidPrefix}-chip-remove-${i}`}>
                <X className="w-3 h-3 inline"/>
              </button>
            </span>
          );
        })}
      </div>

      {/* Dropdown autocomplete. */}
      <div className="relative" ref={boxRef}>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-mist"/>
            <input className="input pl-7" placeholder={placeholder}
                   value={draft}
                   onChange={(e) => { setDraft(e.target.value); setOpen(true); setActiveIdx(0); }}
                   onFocus={() => setOpen(true)}
                   onKeyDown={onKeyDown}
                   data-testid={`${testidPrefix}-input`}/>
          </div>
          <button onClick={commitDraft} type="button" className="btn btn-ghost"
                  data-testid={`${testidPrefix}-add`}>
            <Plus className="w-3 h-3"/>
          </button>
        </div>

        {open && suggestions.length > 0 && (
          <div className="absolute z-[100] left-0 right-12 mt-1 max-h-72 overflow-y-auto
                          border border-gold/40 rounded-sm shadow-2xl"
               style={{
                 // Solid (fully opaque) obsidian background — earlier
                 // `bg-void/95 backdrop-blur-md` let downstream cards
                 // bleed through when a stacking context wrapped the
                 // parent. Inline styles ensure consistent contrast.
                 backgroundColor: "rgb(8, 6, 14)",
                 backgroundImage: "linear-gradient(180deg, rgba(60,45,20,0.12), rgba(0,0,0,0.9))",
               }}
               data-testid={`${testidPrefix}-dropdown`}>
            {suggestions.map((e, i) => (
              <button key={`${e.name}-${i}`}
                      onClick={() => addEntry(e)}
                      className={`w-full text-left px-3 py-2 border-b border-gold/10 hover:bg-gold/10
                                  ${activeIdx === i ? "bg-gold/15" : ""}`}
                      data-testid={`${testidPrefix}-suggest-${i}`}>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-display text-parchment">
                    {e.__custom && <Sparkles className="w-3 h-3 inline mr-1 text-gold-bright"/>}
                    {e.name}
                  </span>
                  <span className="text-[10px] text-mist">
                    {e.__kind || e.kind}
                    {e.level != null && ` · L${e.level}`}
                  </span>
                </div>
                <div className="text-[11px] text-mist mt-0.5">
                  {[e.damage, e.ac, e.school, e.range, e.cost, e.weight, e.category,
                    e.effect, e.role, e.form, e.intrusion]  // V6.23 cypher fields
                    .filter(Boolean).join(" · ")}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="text-[10px] text-mist/70 italic mt-2">
        Type to filter the SRD catalog. Click a chip's icon to open its
        reference. Unknown names add as homebrew free-text (the reference
        editor can codify them later).
      </div>
    </div>
  );
}
