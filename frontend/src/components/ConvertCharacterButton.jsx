import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Wand2, X, ChevronRight, Sparkles } from "lucide-react";
import { api, formatApiErrorDetail } from "../lib/api";

/**
 * V6.16 — ConvertCharacterButton
 *
 * Header-toolbar action that lets a GM port the active character into
 * another of THEIR campaigns (any system). Calls
 * `POST /api/convert/character` which uses Claude to translate
 * mechanics into the target system's canonical shape.
 *
 *   <ConvertCharacterButton character={ch} isGm={true}/>
 *
 * Visible only when the viewer has GM rights on the source campaign.
 * The target list is filtered to campaigns where the viewer is also GM
 * (server enforces this — UI just hides ineligible options).
 */
const SYSTEM_LABEL = {
  "besm-4e": "BESM 4E",
  "anime-5e": "Anime 5E",
  "dnd-5e": "D&D 5E",
  "cypher": "Cypher",
};
const SYSTEM_ACCENT = {
  "besm-4e": "#3B1E63",
  "anime-5e": "#E03A8E",
  "dnd-5e": "#7A1F2E",
  "cypher": "#0F2540",
};

export default function ConvertCharacterButton({ character, isGm }) {
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [campaigns, setCampaigns] = useState([]);
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!open || campaigns.length > 0) return;
    api.get("/campaigns").then((r) => setCampaigns(r.data || []))
      .catch(() => setCampaigns([]));
  }, [open, campaigns.length]);

  if (!isGm || !character) return null;

  const eligible = campaigns.filter(
    (c) => c.is_gm && c.id !== character.campaign_id
  );

  const fire = async (target) => {
    setBusy(target.id); setErr(""); setResult(null);
    try {
      const { data } = await api.post("/convert/character", {
        source_character_id: character.id,
        target_campaign_id: target.id,
        keep_folio: true,
        name_override: `${character.name} (${SYSTEM_LABEL[target.system_id] || target.system_id})`,
      });
      setResult({ target, data });
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message || "Conversion failed");
    } finally { setBusy(""); }
  };

  return (
    <>
      <button onClick={() => setOpen(true)}
              className="btn btn-ghost text-xs"
              data-testid="convert-character-btn"
              title="Port this character into another of your campaigns (any system) using the Claude-assisted converter.">
        <Wand2 className="w-4 h-4"/> Convert →
      </button>

      {open && (
        <div className="fixed inset-0 z-[8800] bg-void/80 backdrop-blur-sm flex items-center justify-center p-4"
             data-testid="convert-modal" onClick={() => setOpen(false)}>
          <div className="card-mystic w-full max-w-lg p-6"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-baseline justify-between mb-2">
              <div>
                <div className="text-[10px] tracking-widest uppercase text-gold-bright flex items-center gap-1">
                  <Sparkles className="w-3 h-3"/> Cross-system Converter
                </div>
                <div className="font-display text-xl text-parchment mt-0.5">
                  Port "{character.name}" to…
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="text-mist hover:text-ember"
                      data-testid="convert-modal-close">
                <X className="w-4 h-4"/>
              </button>
            </div>
            <div className="text-[11px] text-mist italic mb-4">
              Pick another of your campaigns. Claude will translate mechanics into
              the target system's native shape (CP for BESM/Anime, class+level for D&D,
              tier+sentence for Cypher). Bio + journal carry over verbatim. Takes ~30-60s.
            </div>

            {result ? (
              <div className="card-mystic p-4 border-l-4 border-l-gold-bright"
                   data-testid="convert-result">
                <div className="font-display text-lg text-gold-bright">
                  Conversion complete.
                </div>
                <div className="text-[12px] text-parchment mt-1">
                  Created <b>{result.data.character.name}</b> in <b>{result.target.name}</b>.
                </div>
                {result.data.caveats && result.data.caveats.length > 0 && (
                  <div className="mt-2">
                    <div className="text-[10px] tracking-widest uppercase text-mist">Conversion caveats</div>
                    <ul className="text-[11px] text-mist italic list-disc list-inside mt-1 space-y-0.5">
                      {result.data.caveats.slice(0, 6).map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  </div>
                )}
                <div className="mt-3 flex justify-end gap-2">
                  <button onClick={() => { setOpen(false); setResult(null); }}
                          className="btn btn-ghost text-xs">Stay here</button>
                  <button onClick={() => nav(`/app/characters/${result.data.character.id}#mechanics`)}
                          className="btn btn-primary text-xs"
                          data-testid="convert-result-open-btn">
                    Open new sheet <ChevronRight className="w-3 h-3"/>
                  </button>
                </div>
              </div>
            ) : (
              <>
                {eligible.length === 0 && (
                  <div className="text-[12px] text-mist italic"
                       data-testid="convert-no-targets">
                    You don't GM any other campaigns yet — create one in another system,
                    then come back to port this character.
                  </div>
                )}
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {eligible.map((c) => {
                    const accent = SYSTEM_ACCENT[c.system_id] || "#C8A34A";
                    const same = c.system_id === character.system_id;
                    return (
                      <button key={c.id} onClick={() => fire(c)}
                              disabled={!!busy}
                              className="w-full text-left p-3 rounded-sm border hover:border-gold/60 hover:bg-gold/5 transition flex items-center gap-3 disabled:opacity-40"
                              style={{ borderColor: `${accent}55` }}
                              data-testid={`convert-target-${c.id}`}>
                        <span className="px-2 py-0.5 text-[10px] font-ui uppercase tracking-widest rounded-sm shrink-0"
                              style={{ background: `${accent}20`, color: accent, border: `1px solid ${accent}66` }}>
                          {SYSTEM_LABEL[c.system_id] || c.system_id}
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="text-sm text-parchment truncate">{c.name}</div>
                          <div className="text-[10px] text-mist truncate">
                            {same ? "(same system — direct copy)" : "(translation required)"}
                          </div>
                        </div>
                        {busy === c.id ? (
                          <span className="text-[10px] text-gold-bright">Converting…</span>
                        ) : (
                          <ChevronRight className="w-4 h-4 text-mist"/>
                        )}
                      </button>
                    );
                  })}
                </div>
                {err && (
                  <div className="mt-3 text-[11px] text-ember"
                       data-testid="convert-error">{err}</div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
