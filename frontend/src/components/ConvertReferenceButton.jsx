import React, { useState } from "react";
import { Wand2, X, ChevronRight, Sparkles, Copy, Check } from "lucide-react";
import { api, formatApiErrorDetail } from "../lib/api";

/**
 * V6.16.4 — ConvertReferenceButton
 *
 * Lets ANY viewer (player or GM) translate a single reference-library
 * entry (Attribute / Defect / Spell / Focus / Feat / Skill / Item)
 * from its source system into a target system they're currently
 * playing. Fires `POST /api/convert/content` which is the single-
 * mechanic path of the cross-system converter.
 *
 *   <ConvertReferenceButton entry={ref} sourceSystem="besm-4e"/>
 *
 * On success, opens a modal showing the translated payload with a
 * Copy-to-clipboard shortcut so the player can paste it into their
 * sheet or share it in chat. No DB write — this is preview content;
 * the receiving system's GM retains final authority on whether to
 * publish it into the reference library.
 *
 * V6.16.4 — `/api/convert/content` is authenticated-but-role-open, so
 * players can pull cross-system references on-demand. GM approval is
 * still required to persist them as a published reference entry.
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
const ALL_SYSTEMS = ["besm-4e", "anime-5e", "dnd-5e", "cypher"];

export default function ConvertReferenceButton({ entry, sourceSystem }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);

  if (!entry) return null;
  const src = sourceSystem || "besm-4e";

  // Reference-editor "kind" values → the converter's source_kind hint.
  const KIND_ALIAS = {
    attribute: "attribute",
    skill: "skill",
    defect: "defect",
    enhancement: "attribute",   // enhancement is a sub-modifier of an attr
    limiter: "attribute",
    power_pack: "power_bundle",
    power_bundle: "power_bundle",
    item: "item",
    weapon: "weapon",
    spell: "spell",
    feature: "feature",
    feat: "feat",
    focus: "focus",
    descriptor: "descriptor",
    type: "type",
  };
  const source_kind = KIND_ALIAS[entry.kind] || entry.kind || "attribute";

  const eligible = ALL_SYSTEMS.filter((s) => s !== src);

  const fire = async (targetSystem) => {
    setBusy(targetSystem); setErr(""); setResult(null);
    try {
      const payload = {
        name: entry.name, cost: entry.cost, summary: entry.summary,
        book: entry.book, page: entry.page, fields: entry.fields || {},
      };
      const { data } = await api.post("/convert/content", {
        source_system: src,
        target_system: targetSystem,
        source_kind,
        payload,
      });
      setResult({ targetSystem, data });
    } catch (e) {
      const detail = formatApiErrorDetail(e.response?.data?.detail) || e.message;
      if (e.response?.status === 403) {
        setErr("Cross-system translations are GM/admin-only for now. Ask your GM to convert this reference and republish it for the table.");
      } else {
        setErr(detail || "Conversion failed");
      }
    } finally { setBusy(""); }
  };

  const copyPayload = () => {
    if (!result) return;
    try {
      navigator.clipboard.writeText(JSON.stringify(result.data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* noop */ }
  };

  return (
    <>
      <button onClick={(e) => { e.stopPropagation(); setOpen(true); }}
              className="text-gold/70 hover:text-gold p-1"
              data-testid={`reference-convert-btn-${entry.id || entry.name}`}
              title={`Translate "${entry.name}" into another system's canonical shape.`}>
        <Wand2 className="w-3 h-3"/>
      </button>

      {open && (
        <div className="fixed inset-0 z-[8800] bg-void/80 backdrop-blur-sm flex items-center justify-center p-4"
             data-testid="convert-reference-modal" onClick={() => setOpen(false)}>
          <div className="card-mystic w-full max-w-2xl p-6"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-baseline justify-between mb-2">
              <div>
                <div className="text-[10px] tracking-widest uppercase text-gold-bright flex items-center gap-1">
                  <Sparkles className="w-3 h-3"/> Reference Translator
                </div>
                <div className="font-display text-xl text-parchment mt-0.5">
                  Translate "{entry.name}"
                </div>
                <div className="text-[11px] text-mist italic">
                  Source: {SYSTEM_LABEL[src] || src} · kind: {source_kind}
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="text-mist hover:text-ember"
                      data-testid="convert-reference-modal-close">
                <X className="w-4 h-4"/>
              </button>
            </div>

            {result ? (
              <div className="card-mystic p-4 border-l-4 border-l-gold-bright mt-3"
                   data-testid="convert-reference-result">
                <div className="flex items-baseline justify-between gap-3">
                  <div>
                    <div className="font-display text-lg text-gold-bright">
                      {result.data.name || entry.name}
                    </div>
                    <div className="text-[11px] text-mist">
                      Target: {SYSTEM_LABEL[result.targetSystem]} · kind: {result.data.kind}
                    </div>
                  </div>
                  <button onClick={copyPayload} className="btn btn-ghost text-xs"
                          data-testid="convert-reference-copy-btn">
                    {copied ? <Check className="w-3 h-3"/> : <Copy className="w-3 h-3"/>}
                    {copied ? "Copied" : "Copy JSON"}
                  </button>
                </div>
                {result.data.summary && (
                  <div className="text-[12px] text-parchment/90 italic mt-2 leading-snug">
                    {result.data.summary}
                  </div>
                )}
                <pre className="mt-3 text-[11px] text-parchment/80 bg-void/40 border border-gold/15 p-2 rounded-sm overflow-x-auto max-h-80"
                     data-testid="convert-reference-payload">
{JSON.stringify(result.data.target_payload || {}, null, 2)}
                </pre>
                {result.data.caveats && result.data.caveats.length > 0 && (
                  <div className="mt-2">
                    <div className="text-[10px] tracking-widest uppercase text-mist">Caveats</div>
                    <ul className="text-[11px] text-mist italic list-disc list-inside mt-1 space-y-0.5">
                      {result.data.caveats.slice(0, 5).map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  </div>
                )}
                <div className="text-[10px] text-mist/70 italic mt-3">
                  Preview only — GM approval needed to publish this translation
                  into the target system's reference library.
                </div>
                <div className="mt-3 flex justify-end gap-2">
                  <button onClick={() => setResult(null)}
                          className="btn btn-ghost text-xs">Translate elsewhere</button>
                  <button onClick={() => setOpen(false)}
                          className="btn btn-primary text-xs">Done</button>
                </div>
              </div>
            ) : (
              <>
                <div className="text-[11px] text-mist italic mb-3">
                  Pick a target system. Claude produces the canonical shape for that
                  ruleset in ~15-25s. Preview only — no DB write.
                </div>
                <div className="space-y-2">
                  {eligible.map((sys) => {
                    const accent = SYSTEM_ACCENT[sys] || "#C8A34A";
                    return (
                      <button key={sys} onClick={() => fire(sys)}
                              disabled={!!busy}
                              className="w-full text-left p-3 rounded-sm border hover:border-gold/60 hover:bg-gold/5 transition flex items-center gap-3 disabled:opacity-40"
                              style={{ borderColor: `${accent}55` }}
                              data-testid={`convert-reference-target-${sys}`}>
                        <span className="px-2 py-0.5 text-[10px] font-ui uppercase tracking-widest rounded-sm shrink-0"
                              style={{ background: `${accent}20`, color: accent, border: `1px solid ${accent}66` }}>
                          {SYSTEM_LABEL[sys]}
                        </span>
                        <div className="min-w-0 flex-1 text-xs text-parchment">
                          Translate to {SYSTEM_LABEL[sys]}
                        </div>
                        {busy === sys ? (
                          <span className="text-[10px] text-gold-bright">Translating…</span>
                        ) : (
                          <ChevronRight className="w-4 h-4 text-mist"/>
                        )}
                      </button>
                    );
                  })}
                </div>
                {err && (
                  <div className="mt-3 text-[11px] text-ember"
                       data-testid="convert-reference-error">{err}</div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
