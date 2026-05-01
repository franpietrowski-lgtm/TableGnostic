// Extracted from ReferenceEditor.jsx in V6.10 refactor.
// Modal that lists D&D-mimic Power Bundle templates and (optionally)
// previews how importing one would impact a chosen PC's CP spend.
import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../../lib/api";

function PowerBundleTemplatePicker({ onPick, onClose, campaignId }) {
  const [templates, setTemplates] = useState([]);
  const [err, setErr] = useState("");
  const [filter, setFilter] = useState("");
  // V6.5 — Live Spend Preview: pick a character; hover a template to
  // see fits/over math projected onto their current spend.
  const [chars, setChars] = useState([]);
  const [previewCharId, setPreviewCharId] = useState("");
  const [previewByCost, setPreviewByCost] = useState({});

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/reference/power-bundle-templates");
        setTemplates(data.templates || []);
        if (campaignId) {
          const cs = await api.get(`/campaigns/${campaignId}/characters`).then((r) => r.data);
          setChars(cs || []);
          if (cs?.length) setPreviewCharId(cs[0].id);
        }
      } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
    })();
  }, [campaignId]);

  const filtered = templates.filter((t) =>
    !filter || t.name.toLowerCase().includes(filter.toLowerCase())
    || (t.school || "").toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className="fixed inset-0 bg-void/90 backdrop-blur-md z-50 flex items-center justify-center p-4"
         onClick={onClose} data-testid="bundle-template-picker">
      <div className="card-mystic p-6 max-w-4xl w-full max-h-[85vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between flex-wrap gap-2 mb-3">
          <div>
            <div className="label-ref">Power Bundle Templates</div>
            <h3 className="font-display text-xl text-gold mt-1">D&D-spell-mimic starter library</h3>
            <div className="text-[11px] text-mist italic">
              Seeded from the <b>Anime 5E Spell Conversions</b> supplement. Click a card
              to drop it into the editor — tweak cost, invocation, and components before saving.
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost text-xs"
                  data-testid="bundle-template-picker-close">Close</button>
        </div>
        <input className="input text-sm mb-3" placeholder="Filter by name or school…"
               value={filter} onChange={(e) => setFilter(e.target.value)}
               data-testid="bundle-template-filter"/>
        {/* V6.5 — Live Spend Preview: pick a PC → cards show fits/over. */}
        {chars.length > 0 && (
          <div className="flex items-center gap-2 mb-3 text-xs" data-testid="bundle-preview-picker">
            <span className="label-ref text-[9px]">Spend Preview for</span>
            <select className="select select-sm" value={previewCharId}
                    onChange={(e) => setPreviewCharId(e.target.value)}
                    data-testid="bundle-preview-character-select">
              <option value="">— no preview —</option>
              {chars.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || "(unnamed)"} · {c.power_level} · {c.total_points} CP
                </option>
              ))}
            </select>
            <span className="text-[10px] text-mist italic">
              Hover a card → live projection of the PC's CP spend if imported.
            </span>
          </div>
        )}
        {err && <div className="text-ember text-xs mb-2">{err}</div>}
        <div className="grid gap-2 sm:grid-cols-2">
          {filtered.map((t) => {
            const preview = previewByCost[t.cost];
            const fits = preview?.fits;
            return (
              <button key={t.name} onClick={() => onPick(t)}
                      onMouseEnter={async () => {
                        if (!previewCharId || previewByCost[t.cost] !== undefined) return;
                        try {
                          const { data } = await api.post(
                            `/characters/${previewCharId}/simulate-import`,
                            { extra_cost: t.cost });
                          setPreviewByCost((prev) => ({ ...prev, [t.cost]: data }));
                        } catch (_) { /* silent */ }
                      }}
                      className="text-left card-mystic p-3 hover:-translate-y-0.5 transition"
                      data-testid={`bundle-template-${t.source_spell_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-ui text-parchment text-sm">{t.name}</span>
                  <span className="text-[10px] text-mist uppercase tracking-widest">
                    L{t.source_spell_level} · {t.school}
                  </span>
                </div>
                <div className="text-[11px] text-mist italic mt-1 line-clamp-2">{t.description}</div>
                <div className="flex items-center gap-2 mt-2 text-[10px] font-ui flex-wrap">
                  <span className="tag border-gold/40 text-gold-bright">{t.cost} CP</span>
                  <span className="tag border-arcane/30 text-arcane">{t.invocation}</span>
                  {t.charges_max > 0 && <span className="tag border-mist/40 text-mist">{t.charges_max} charges</span>}
                  {t.energy_cost > 0 && <span className="tag border-ember/30 text-ember">{t.energy_cost} EP</span>}
                  {preview && (
                    <span className={`tag ${fits ? "border-arcane/60 text-arcane" : "border-ember/60 text-ember"}`}
                          data-testid={`bundle-preview-result-${t.cost}`}
                          title={preview.summary}>
                      {fits ? `OK (${preview.headroom} spare)` : `OVER by ${-preview.headroom}`}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default PowerBundleTemplatePicker;
