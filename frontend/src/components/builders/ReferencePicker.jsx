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
  // V6.25 — Universal Power Bundle Architecture: when the picker is
  // surfacing spells, we ALSO include `power_bundle` and `power_pack`
  // custom entries from the Reference Editor (they ARE spell-mimic
  // mechanics with CP cost). Fixed URL `/references` → `/reference`
  // (the backend endpoint is singular) which was silently 404ing.
  // V6.25.3 — also pull `/campaigns/{cid}/custom` (Custom Rules tab
  // entries) so character-sheet pickers can offer the GM-authored
  // homebrew of every kind by system: feats, traits, features, foci,
  // descriptors, cyphers, artifacts, race / class templates, etc.
  useEffect(() => {
    if (!campaignId) { setCustom([]); return; }
    let cancelled = false;
    const wantsFeat   = kinds.some((k) => /feat/i.test(k));
    const wantsTrait  = kinds.some((k) => /trait/i.test(k));
    const wantsFeat2  = kinds.includes("feature") || kinds.includes("class_features");
    const wantsRace   = kinds.includes("race") || kinds.includes("races");
    const wantsClass  = kinds.includes("class") || kinds.includes("classes");
    const wantsFocus  = kinds.includes("focus") || kinds.includes("foci");
    const wantsDescr  = kinds.includes("descriptor") || kinds.includes("descriptors");
    const wantsType   = kinds.includes("type") || kinds.includes("types") || kinds.includes("ability");
    const wantsCypher = kinds.includes("cypher") || kinds.includes("cyphers");
    const wantsArti   = kinds.includes("artifact") || kinds.includes("artifacts");
    const wantsHouse  = kinds.includes("house") || kinds.includes("houseRules");
    const customKindNeeded = (k) => {
      switch (k) {
        case "feat":       return wantsFeat;
        case "trait":      return wantsTrait;
        case "feature":    return wantsFeat2;
        case "race":       return wantsRace;
        case "class":      return wantsClass;
        case "focus":      return wantsFocus;
        case "descriptor": return wantsDescr;
        case "ability":    return wantsType;
        case "cypher":     return wantsCypher;
        case "artifact":   return wantsArti;
        case "house":      return wantsHouse;
        default:           return false;
      }
    };
    (async () => {
      try {
        // 1) Reference Editor entries (weapons / armor / items / spells / power-bundles).
        const { data: refData } = await api.get(`/campaigns/${campaignId}/reference`);
        const refMatches = (refData?.entries || refData || []).filter((e) => {
          const k = (e.kind || "").toLowerCase();
          if (kinds.includes("weapons") && (k === "weapons" || k === "weapon")) return true;
          if (kinds.includes("armor") && k === "armor") return true;
          if (kinds.includes("items") && (k === "items" || k === "item")) return true;
          if (kinds.includes("spells") && (
            k === "spells" || k === "spell"
            || k === "power_bundle" || k === "power_pack")) return true;
          return false;
        });
        // 2) Custom Rules tab entries (per-system homebrew).
        let customRules = [];
        try {
          const { data: cust } = await api.get(`/campaigns/${campaignId}/custom`);
          customRules = (cust || []).filter((e) => customKindNeeded((e.kind || "").toLowerCase()));
        } catch { /* ignore — endpoint may 404 on legacy campaigns */ }

        const all = [...refMatches, ...customRules];
        // Normalise to the picker's shape.
        const normalised = all.map((e) => {
          const k = (e.kind || "").toLowerCase();
          if (k === "power_bundle" || k === "power_pack") {
            const f = e.fields || {};
            return {
              ...e,
              level: f.source_spell_level ?? e.level ?? null,
              school: f.school || e.school || "Power Bundle",
              cost: e.cost || (f.cost != null ? `${f.cost} CP` : ""),
              effect: f.description || e.summary || "",
              form: f.invocation || "",
              damage: f.energy_cost ? `EP ${f.energy_cost}` : "",
              range: f.charges_max ? `${f.charges_max}×` : "",
            };
          }
          // Custom Rules shape → picker shape.
          if (["feat","trait","feature","race","class","focus","descriptor",
                "ability","cypher","artifact","house"].includes(k)) {
            const eff = e.effects || {};
            return {
              ...e,
              __custom_rule: true,
              effect: e.description_note || "",
              cost: typeof eff.total_cp === "number" ? `${eff.total_cp} CP` : "",
              level: e.cost_per_level != null ? `${e.cost_per_level}/lvl` : "",
              color: e.color || "",  // V6.25.8 — surface GM-set color tag.
            };
          }
          return e;
        });
        if (!cancelled) setCustom(normalised);
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
          // V6.25.8 — GM-set color tag bleeds through onto the chip border.
          const tagColor = isObj ? (v.color || v.fields?.color || "") : "";
          const hint = isObj
            ? [v.damage, v.ac, v.level != null ? `L${v.level}` : null,
                v.school, v.cost, v.kind, v.category,
                v.effect, v.role, v.form]  // V6.23 cypher fields
              .filter(Boolean).join(" · ")
            : "";
          return (
            <span key={i} className="tag group inline-flex items-center gap-1"
                  style={tagColor ? { borderLeft: `3px solid ${tagColor}`, paddingLeft: "0.4rem" } : undefined}
                  data-testid={`${testidPrefix}-chip-${i}`}>
              {tagColor && (
                <span className="inline-block w-2 h-2 rounded-full"
                      style={{ background: tagColor }}
                      title="GM-set color tag"
                      data-testid={`${testidPrefix}-chip-color-${i}`}/>
              )}
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
            {suggestions.map((e, i) => {
              const tagColor = e.color || e.fields?.color || "";
              return (
              <button key={`${e.name}-${i}`}
                      onClick={() => addEntry(e)}
                      className={`w-full text-left px-3 py-2 border-b border-gold/10 hover:bg-gold/10
                                  ${activeIdx === i ? "bg-gold/15" : ""}`}
                      style={tagColor ? { borderLeft: `3px solid ${tagColor}` } : undefined}
                      data-testid={`${testidPrefix}-suggest-${i}`}>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-display text-parchment">
                    {tagColor && (
                      <span className="inline-block w-2 h-2 rounded-full mr-1.5 align-middle"
                            style={{ background: tagColor }}/>
                    )}
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
            );})}
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
