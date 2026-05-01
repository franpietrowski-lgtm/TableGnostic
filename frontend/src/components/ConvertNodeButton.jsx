import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Wand2, X, ChevronRight, Sparkles } from "lucide-react";
import { api, formatApiErrorDetail } from "../lib/api";

/**
 * V6.16.4 — ConvertNodeButton
 *
 * Header-toolbar action that lets a GM port a Codex creature node into
 * another of their campaigns (any system). Calls
 * `POST /api/convert/creature` which uses Claude to translate the
 * source stat block into the target system's canonical shape (D&D 5E
 * monster block, Cypher antagonist, BESM creature, Anime 5E monster +
 * anime_traits).
 *
 *   <ConvertNodeButton node={codexNode} />
 *
 * Mirrors `ConvertCharacterButton` but targets the `nodes` collection
 * instead of `characters`. Visible only on creature-kind nodes (the
 * caller is responsible for gating, but a defensive check is here too).
 * Server-side enforces GM/admin permission on both source and target
 * campaigns.
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

export default function ConvertNodeButton({ node }) {
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

  if (!node) return null;
  const isCreature = (
    node.type === "creature"
    || node.motive === "creature"
    || (node.fields && node.fields.kind === "creature")
  );
  if (!isCreature) return null;

  const eligible = campaigns.filter(
    (c) => c.is_gm && c.id !== node.campaign_id
  );

  const fire = async (target) => {
    setBusy(target.id); setErr(""); setResult(null);
    try {
      const { data } = await api.post("/convert/creature", {
        source_node_id: node.id,
        target_campaign_id: target.id,
        name_override: `${node.title} (${SYSTEM_LABEL[target.system_id] || target.system_id})`,
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
              data-testid="convert-node-btn"
              title="Port this creature into another of your campaigns (any system) using the Claude-assisted converter.">
        <Wand2 className="w-4 h-4"/> Port to…
      </button>

      {open && (
        <div className="fixed inset-0 z-[8800] bg-void/80 backdrop-blur-sm flex items-center justify-center p-4"
             data-testid="convert-node-modal" onClick={() => setOpen(false)}>
          <div className="card-mystic w-full max-w-lg p-6"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-baseline justify-between mb-2">
              <div>
                <div className="text-[10px] tracking-widest uppercase text-gold-bright flex items-center gap-1">
                  <Sparkles className="w-3 h-3"/> Cross-system Creature Port
                </div>
                <div className="font-display text-xl text-parchment mt-0.5">
                  Port "{node.title}" to…
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="text-mist hover:text-ember"
                      data-testid="convert-node-modal-close">
                <X className="w-4 h-4"/>
              </button>
            </div>
            <div className="text-[11px] text-mist italic mb-4">
              Pick another of your campaigns. Claude will translate the stat block into
              the target system (CR/HP/AC for D&D, level/difficulty/health for Cypher,
              CP for BESM, 5E+anime_traits for Anime 5E). Lands as a new codex node in
              the Entities pool. Takes ~20-40s.
            </div>

            {result ? (
              <div className="card-mystic p-4 border-l-4 border-l-gold-bright"
                   data-testid="convert-node-result">
                <div className="font-display text-lg text-gold-bright">
                  Port complete.
                </div>
                <div className="text-[12px] text-parchment mt-1">
                  Created <b>{result.data.node.title}</b> in <b>{result.target.name}</b>.
                  It will appear in the Director's Console Entities pool under
                  "Codex · Creatures & Beasts".
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
                  <button onClick={() => nav(`/app/campaigns/${result.target.id}`)}
                          className="btn btn-primary text-xs"
                          data-testid="convert-node-result-open-btn">
                    Open target campaign <ChevronRight className="w-3 h-3"/>
                  </button>
                </div>
              </div>
            ) : (
              <>
                {eligible.length === 0 && (
                  <div className="text-[12px] text-mist italic"
                       data-testid="convert-node-no-targets">
                    You don't GM any other campaigns yet — create one in another system,
                    then come back to port this creature.
                  </div>
                )}
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {eligible.map((c) => {
                    const accent = SYSTEM_ACCENT[c.system_id] || "#C8A34A";
                    const same = c.system_id === (node.fields?.system_id || "besm-4e");
                    return (
                      <button key={c.id} onClick={() => fire(c)}
                              disabled={!!busy}
                              className="w-full text-left p-3 rounded-sm border hover:border-gold/60 hover:bg-gold/5 transition flex items-center gap-3 disabled:opacity-40"
                              style={{ borderColor: `${accent}55` }}
                              data-testid={`convert-node-target-${c.id}`}>
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
                          <span className="text-[10px] text-gold-bright">Porting…</span>
                        ) : (
                          <ChevronRight className="w-4 h-4 text-mist"/>
                        )}
                      </button>
                    );
                  })}
                </div>
                {err && (
                  <div className="mt-3 text-[11px] text-ember"
                       data-testid="convert-node-error">{err}</div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
