// Extracted from ReferenceEditor.jsx in V6.10 refactor.
// Read-only modal that renders the D&D 5E → BESM/Anime 5E spell-conversion
// reference library (`/api/reference/spell-conversions`).
import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../../lib/api";

function SpellConversionAtlas({ onClose, onConvert }) {
  const [rows, setRows] = useState([]);
  const [schools, setSchools] = useState([]);
  const [total, setTotal] = useState(0);
  const [err, setErr] = useState("");
  const [search, setSearch] = useState("");
  const [school, setSchool] = useState("");
  const [maxLvl, setMaxLvl] = useState(9);

  useEffect(() => {
    (async () => {
      try {
        const qs = new URLSearchParams();
        qs.set("max_level", String(maxLvl));
        if (school) qs.set("school", school);
        const { data } = await api.get(`/reference/spell-conversions?${qs.toString()}`);
        setRows(data.entries || []);
        setSchools(data.schools || []);
        setTotal(data.total || 0);
      } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
    })();
  }, [school, maxLvl]);

  const filtered = rows.filter((r) =>
    !search || r.source_name.toLowerCase().includes(search.toLowerCase())
    || (r.short_description || "").toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
         onClick={onClose} data-testid="spell-conversion-atlas">
      <div className="card-mystic p-6 max-w-5xl w-full max-h-[88vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref">Spell Conversion Atlas</div>
            <h3 className="font-display text-xl text-gold mt-1">
              D&D 5E → BESM / Anime 5E · {total} entries
            </h3>
            <div className="text-[11px] text-mist italic max-w-xl leading-snug">
              Read-only translation library. Each row shows how a D&D spell or class feature maps to a BESM Attribute bundle — cost, enhancement/limiter values, and SRD page citation. Copy any line into your campaign's Power Bundle reference if you want it purchasable.
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost text-xs"
                  data-testid="spell-conversion-atlas-close">Close</button>
        </div>
        <div className="grid gap-2 sm:grid-cols-3 mb-3">
          <input className="input text-sm" placeholder="Filter by name or text…"
                 value={search} onChange={(e) => setSearch(e.target.value)}
                 data-testid="spell-conversion-search"/>
          <select className="select text-sm" value={school}
                  onChange={(e) => setSchool(e.target.value)}
                  data-testid="spell-conversion-school">
            <option value="">All schools</option>
            {schools.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="select text-sm" value={maxLvl}
                  onChange={(e) => setMaxLvl(Number(e.target.value))}
                  data-testid="spell-conversion-max-level">
            {[0,1,2,3,4,5,6,7,8,9].map((l) => (
              <option key={l} value={l}>Up to level {l}</option>
            ))}
          </select>
        </div>
        {err && <div className="text-ember text-xs mb-2">{err}</div>}
        <div className="space-y-3">
          {filtered.map((r, i) => (
            <div key={`${r.source_name}-${i}`} className="border border-gold/15 rounded-sm p-3"
                 data-testid={`spell-conversion-${r.source_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}>
              <div className="flex items-baseline justify-between flex-wrap gap-2">
                <div>
                  <span className="font-ui text-parchment text-sm">{r.source_name}</span>
                  <span className="ml-2 tag border-gold/40 text-gold-bright">
                    L{r.source_level} · {r.school}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="tag border-arcane/40 text-arcane">{r.net_cp} CP net</span>
                  {onConvert && (
                    <button
                      onClick={() => onConvert(r.source_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase())}
                      className="btn btn-ghost text-[10px]"
                      title="Convert this read-only conversion into an editable Power Bundle draft (opens in the editor pre-filled)."
                      data-testid={`spell-convert-${r.source_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}>
                      → Power Bundle
                    </button>
                  )}
                </div>
              </div>
              <div className="text-[11px] text-mist italic mt-1">{r.short_description}</div>
              {(r.besm || []).map((b, j) => (
                <div key={j} className="mt-2 text-[12px] border-l-2 border-gold/30 pl-3">
                  <div className="font-ui text-gold-bright">
                    {b.attribute} <span className="text-mist text-[10px]">· {b.cost_per_level}/Lvl × {b.level}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(b.enhancements || []).map((e, k) => (
                      <span key={`e${k}`} className="tag border-arcane/30 text-arcane"
                            title={e.name}>
                        +{e.name}{e.value != null ? ` (${e.value > 0 ? "+" : ""}${e.value})` : ""}
                      </span>
                    ))}
                    {(b.limiters || []).map((l, k) => (
                      <span key={`l${k}`} className="tag border-ember/30 text-ember"
                            title={l.name}>
                        −{l.name}{l.value != null ? ` (${l.value > 0 ? "+" : ""}${l.value})` : ""}
                      </span>
                    ))}
                  </div>
                  {b.note && <div className="text-[10px] text-mist italic mt-1">{b.note}</div>}
                </div>
              ))}
              <div className="text-[10px] text-mist/70 italic mt-2">Source: {r.source_reference}</div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-[11px] text-mist italic" data-testid="spell-conversion-empty">
              No conversions match the current filters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SpellConversionAtlas;
