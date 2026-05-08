/**
 * CypherReferencePanel — V6.25.24 (Cycle B-2)
 *
 * Reads `/api/systems/cypher/reference` and surfaces the entire Cypher
 * SRD content grouped by GENRE, with five sub-section tabs:
 *   • Types        (the 4 core types + per-tier ability roster)
 *   • Descriptors  (filtered to the selected genre)
 *   • Foci         (filtered to the selected genre)
 *   • Cyphers      (the seeded short-list — random tables come in B-5)
 *   • Artifacts    (the seeded short-list — random tables come in B-5)
 *
 * Plus three rule strips:
 *   • Tier progression (T1-T6 effort caps + 4 advancement steps)
 *   • XP mechanics (awards / spends / peer transfer / narrative pool)
 *   • Skill levels + paraphrased rules notes + compatibility notice
 *
 * GM affordances: a "Make custom Type / Descriptor / Foci / Cypher /
 * Artifact" button per sub-section opens a draft form with field
 * names mirroring the printed-book layout. Submission posts to the
 * existing `/campaigns/{cid}/reference` endpoint with the right
 * `kind` so the entry shows up in the Atelier reference editor.
 */
import React, { useEffect, useState, useMemo } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Library, Sparkles, ChevronRight, Plus, X, Loader2, Tag, Globe2,
} from "lucide-react";

const GENRE_KEY_FALLBACK = [
  "fantasy", "modern", "science-fiction", "superheroes", "horror",
  "post-apocalyptic", "fairy-tale", "historical",
];
// The reference data uses two genre-key vocabularies — the V6.25.23
// `genres` list uses 'science-fiction' / 'post-apocalyptic', while
// the older descriptor / foci tags use 'scifi' / 'post' / 'superhero'.
// Map the new keys back to the old tags so genre filtering JUST WORKS.
const GENRE_KEY_ALIAS = {
  "science-fiction": "scifi",
  "post-apocalyptic": "post",
  "superheroes":     "superhero",
};

const SUB_TABS = [
  { key: "types",       label: "Types",       Icon: Library },
  { key: "descriptors", label: "Descriptors", Icon: Tag },
  { key: "foci",        label: "Foci",        Icon: Sparkles },
  { key: "cyphers",     label: "Cyphers",     Icon: ChevronRight },
  { key: "artifacts",   label: "Artifacts",   Icon: ChevronRight },
];

const matchesGenre = (entry, genreKey) => {
  if (!genreKey) return true;
  const tags = entry.genres || entry.genre_tags || [];
  if (tags.includes("any") || tags.length === 0) return true;
  const alias = GENRE_KEY_ALIAS[genreKey] || genreKey;
  return tags.includes(genreKey) || tags.includes(alias);
};


export default function CypherReferencePanel({ campId, isGm }) {
  const [ref, setRef] = useState(null);
  const [err, setErr] = useState("");
  const [genre, setGenre] = useState("fantasy");
  const [tab, setTab] = useState("types");
  const [draft, setDraft] = useState(null);

  useEffect(() => {
    api.get("/systems/cypher/reference")
      .then((r) => setRef(r.data))
      .catch((e) => setErr(
        formatApiErrorDetail(e.response?.data?.detail) || e.message));
  }, []);

  const filteredDescriptors = useMemo(
    () => (ref?.descriptors || []).filter((d) => matchesGenre(d, genre)),
    [ref, genre],
  );
  const filteredFoci = useMemo(
    () => (ref?.foci || []).filter((f) => matchesGenre(f, genre)),
    [ref, genre],
  );

  if (err) {
    return (
      <div className="card-mystic p-4 text-ember"
           data-testid="cypher-ref-error">{err}</div>
    );
  }
  if (!ref) {
    return (
      <div className="card-mystic p-4 text-mist italic"
           data-testid="cypher-ref-loading">Loading Cypher reference…</div>
    );
  }

  return (
    <div className="space-y-3" data-testid="cypher-reference-panel">
      <div className="card-mystic p-3">
        <div className="flex items-baseline justify-between flex-wrap gap-2">
          <div>
            <div className="label-ref flex items-center gap-2">
              <Library className="w-3 h-3"/> Cypher System Reference
            </div>
            <div className="text-[10px] text-mist/70 italic">
              {ref.compatibility_notice}
            </div>
          </div>
        </div>

        {/* Genre tabs. */}
        <div className="flex flex-wrap gap-1 mt-3"
             data-testid="cypher-ref-genres">
          {(ref.genres || []).map((g) => (
            <button key={g.key}
                    onClick={() => setGenre(g.key)}
                    className={`tag text-[10px] ${genre === g.key
                      ? "border-gold text-gold-bright bg-gold/10"
                      : "text-mist hover:text-parchment"}`}
                    data-testid={`cypher-ref-genre-${g.key}`}
                    title={g.blurb}>
              <Globe2 className="w-3 h-3 inline mr-1"/> {g.name}
            </button>
          ))}
        </div>

        {/* Sub-section tabs. */}
        <div className="flex flex-wrap gap-1 mt-3 border-t border-gold/10 pt-3"
             data-testid="cypher-ref-tabs">
          {SUB_TABS.map((s) => {
            const I = s.Icon;
            return (
              <button key={s.key}
                      onClick={() => setTab(s.key)}
                      className={`btn text-xs ${tab === s.key ? "btn-primary" : "btn-ghost"}`}
                      data-testid={`cypher-ref-tab-${s.key}`}>
                <I className="w-3 h-3"/> {s.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Active sub-section content. */}
      {tab === "types" && (
        <TypesSection
          types={ref.types_full || []}
          tierProgression={ref.tier_progression || []}
          advancementSteps={ref.advancement_steps || []}/>
      )}
      {tab === "descriptors" && (
        <ListSection
          rows={filteredDescriptors}
          emptyHint={`No descriptors tagged for ${genre} — every descriptor in the SRD has at least an "any" tag.`}
          campId={campId}
          isGm={isGm}
          kind="descriptor"
          genre={genre}
          onMakeCustom={() => setDraft({ kind: "descriptor" })}/>
      )}
      {tab === "foci" && (
        <ListSection
          rows={filteredFoci}
          emptyHint={`No foci tagged for ${genre}.`}
          campId={campId}
          isGm={isGm}
          kind="foci"
          genre={genre}
          onMakeCustom={() => setDraft({ kind: "foci" })}/>
      )}
      {tab === "cyphers" && (
        <ListSection
          rows={(ref.cyphers || []).map((c) => ({
            ...c,
            secondary_label: c.level_die || c.depletion,
          }))}
          campId={campId}
          isGm={isGm}
          kind="cypher"
          genre={genre}
          onMakeCustom={() => setDraft({ kind: "cypher" })}/>
      )}
      {tab === "artifacts" && (
        <ListSection
          rows={(ref.artifacts || []).map((a) => ({
            ...a,
            secondary_label: a.depletion,
          }))}
          campId={campId}
          isGm={isGm}
          kind="artifact"
          genre={genre}
          onMakeCustom={() => setDraft({ kind: "artifact" })}/>
      )}

      {/* Universal rule strips — always visible, regardless of tab. */}
      <RuleStrip ref={ref}/>

      {draft && (
        <CustomDraftModal
          campId={campId}
          kind={draft.kind}
          genre={genre}
          onClose={() => setDraft(null)}/>
      )}
    </div>
  );
}


function TypesSection({ types, tierProgression, advancementSteps }) {
  const [openType, setOpenType] = useState(null);
  return (
    <div className="space-y-2" data-testid="cypher-ref-types-section">
      {types.map((t) => {
        const expanded = openType === t.key;
        return (
          <div key={t.key} className="card-mystic p-3"
               data-testid={`cypher-ref-type-${t.key}`}>
            <button onClick={() => setOpenType(expanded ? null : t.key)}
                    className="w-full flex items-center justify-between text-left">
              <div>
                <div className="font-display text-base text-parchment">
                  {t.name}
                </div>
                <div className="text-[11px] text-mist italic">
                  {t.role_blurb}
                </div>
              </div>
              <div className="text-[10px] text-mist tabular-nums whitespace-nowrap ml-3">
                Pool {t.starting_stat_pools.Might}/{t.starting_stat_pools.Speed}/{t.starting_stat_pools.Intellect}
                {" · "}cypher limit {t.starting_cypher_limit}
              </div>
            </button>
            {expanded && (
              <div className="mt-3 border-t border-gold/10 pt-3 space-y-3">
                {[1, 2, 3, 4, 5, 6].map((tier) => {
                  const list = t.abilities_by_tier[String(tier)] || [];
                  const cap = tierProgression.find((p) => p.tier === tier);
                  return (
                    <div key={tier}
                         data-testid={`cypher-ref-${t.key}-tier-${tier}`}>
                      <div className="flex items-baseline justify-between">
                        <div className="text-[11px] text-arcane-light font-display">
                          Tier {tier}
                        </div>
                        <div className="text-[10px] text-mist">
                          max effort {cap?.max_effort} · {list.length} abilities
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {list.map((name) => (
                          <span key={name}
                                className="tag text-[10px] text-parchment">
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
                <div className="border-t border-gold/10 pt-3">
                  <div className="text-[11px] text-arcane-light font-display">
                    Advancement (4 steps × 4 XP = 16 XP per tier)
                  </div>
                  <ul className="text-[10px] text-mist space-y-0.5 mt-1">
                    {advancementSteps.map((s) => (
                      <li key={s.key}>
                        <span className="text-parchment">{s.name}</span>
                        {" — "}{s.effect}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}


function ListSection({ rows, emptyHint, campId, isGm, kind, genre, onMakeCustom }) {
  return (
    <div className="card-mystic p-3 space-y-2"
         data-testid={`cypher-ref-list-${kind}`}>
      <div className="flex justify-between items-baseline">
        <div className="text-[10px] text-mist">
          {rows.length} {kind}{rows.length === 1 ? "" : "s"} for {genre}
        </div>
        {isGm && campId && (
          <button onClick={onMakeCustom}
                  className="btn btn-ghost text-[10px]"
                  data-testid={`cypher-ref-make-custom-${kind}`}>
            <Plus className="w-3 h-3"/> Make custom {kind}
          </button>
        )}
      </div>
      {rows.length === 0 && (
        <div className="text-mist italic text-[11px]">{emptyHint}</div>
      )}
      {rows.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
          {rows.map((r, i) => (
            <div key={r.id || r.name || i}
                 className="border border-gold/10 rounded-sm p-2 bg-void/30
                            text-[11px] text-parchment"
                 data-testid={`cypher-ref-${kind}-row-${i}`}>
              <div className="flex justify-between gap-2">
                <span className="font-display">{r.name}</span>
                {r.secondary_label && (
                  <span className="text-[10px] text-arcane-light">{r.secondary_label}</span>
                )}
              </div>
              {r.blurb && (
                <div className="text-[10px] text-mist mt-0.5 italic">{r.blurb}</div>
              )}
              {(r.genres || []).length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {r.genres.map((g) => (
                    <span key={g} className="tag text-[9px]">{g}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


function RuleStrip({ ref }) {
  return (
    <div className="card-mystic p-3 space-y-2"
         data-testid="cypher-ref-rules-strip">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <div className="label-ref">Tier progression</div>
          <ul className="text-[11px] text-mist space-y-0.5">
            {(ref.tier_progression || []).map((t) => (
              <li key={t.tier} data-testid={`cypher-ref-tier-${t.tier}`}>
                <span className="text-parchment">Tier {t.tier}</span>
                {" — "}max effort <span className="text-arcane-light">{t.max_effort}</span>
                {" · "}<span className="italic">{t.blurb}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="label-ref">XP mechanics</div>
          <div className="text-[10px] text-mist/80 italic mb-1">
            Awards: {(ref.xp_mechanics?.awards || []).map((a) => a.name).join(" · ")}
          </div>
          <ul className="text-[11px] text-mist space-y-0.5">
            {(ref.xp_mechanics?.spends || []).map((s) => (
              <li key={s.key}>
                <span className="text-parchment">{s.name}</span>
                {" "}<span className="text-arcane-light">({s.cost} XP)</span>
                {" — "}<span className="italic">{s.blurb}</span>
              </li>
            ))}
          </ul>
          <div className="text-[10px] text-arcane-light mt-2">
            Tier advancement: {ref.xp_mechanics?.tier_advancement_rule}
          </div>
        </div>
      </div>

      <div>
        <div className="label-ref">Skill levels</div>
        <div className="flex flex-wrap gap-2 text-[11px]">
          {(ref.skill_levels_v2 || []).map((s) => (
            <span key={s.level} className="tag text-[10px]">
              {s.level} <span className="text-mist">({s.step_shift > 0 ? "+" : ""}{s.step_shift} step)</span>
            </span>
          ))}
        </div>
      </div>

      <div>
        <div className="label-ref">Rules notes</div>
        <ul className="text-[10px] text-mist italic list-disc pl-5">
          {(ref.rules_notes || []).map((n, i) => <li key={i}>{n}</li>)}
        </ul>
      </div>
    </div>
  );
}


/**
 * CustomDraftModal — surfaces the printed-book field layout for a
 * Type / Descriptor / Foci / Cypher / Artifact, then POSTs the
 * result to /campaigns/{cid}/reference so the entry shows up in
 * the Atelier reference editor as a campaign-local override.
 */
function CustomDraftModal({ campId, kind, genre, onClose }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [doc, setDoc] = useState({ name: "", blurb: "", genres: [genre] });

  const fields = FIELDS_BY_KIND[kind] || FIELDS_BY_KIND.descriptor;

  const submit = async () => {
    if (!doc.name.trim()) { setErr("Name required."); return; }
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${campId}/reference`, {
        kind: kind === "foci" ? "focus" : kind,
        name: doc.name.trim(),
        summary: doc.blurb.trim(),
        fields: { ...doc, genre, system_id: "cypher" },
      });
      onClose && onClose();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-void/80 z-[200] flex items-center justify-center p-4"
         onClick={onClose}
         data-testid={`cypher-custom-modal-${kind}`}>
      <div className="card-mystic p-5 max-w-2xl w-full max-h-[90vh] overflow-y-auto
                      relative space-y-3"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose}
                className="absolute top-2 right-2 text-mist hover:text-parchment"
                data-testid="cypher-custom-close">
          <X className="w-4 h-4"/>
        </button>
        <div>
          <div className="label-ref">Make custom {kind}</div>
          <div className="text-[10px] text-mist/70 italic">
            Fields mirror the printed-book layout. Saves to your
            campaign as a local Reference entry.
          </div>
        </div>

        <div className="space-y-2">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-mist">Name</div>
            <input className="input text-sm w-full"
                   value={doc.name}
                   onChange={(e) => setDoc({ ...doc, name: e.target.value })}
                   data-testid={`cypher-custom-name-${kind}`}/>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-mist">Blurb / one-liner</div>
            <textarea className="input text-xs w-full" rows={2}
                      value={doc.blurb}
                      onChange={(e) => setDoc({ ...doc, blurb: e.target.value })}
                      data-testid={`cypher-custom-blurb-${kind}`}/>
          </div>
          {fields.map((f) => (
            <div key={f.key}>
              <div className="text-[10px] uppercase tracking-widest text-mist">
                {f.label}
              </div>
              <input className="input text-xs w-full"
                     placeholder={f.placeholder || ""}
                     value={doc[f.key] || ""}
                     onChange={(e) => setDoc({ ...doc, [f.key]: e.target.value })}
                     data-testid={`cypher-custom-${f.key}-${kind}`}/>
            </div>
          ))}
        </div>

        {err && <div className="text-ember text-xs"
                     data-testid="cypher-custom-error">{err}</div>}

        <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
          <button onClick={onClose} className="btn btn-ghost text-xs"
                  data-testid="cypher-custom-cancel">Cancel</button>
          <button onClick={submit}
                  disabled={busy || !doc.name.trim()}
                  className="btn btn-primary text-xs"
                  data-testid="cypher-custom-submit">
            {busy ? <Loader2 className="w-3 h-3 animate-spin"/>
                  : <Plus className="w-3 h-3"/>}
            Save to Reference
          </button>
        </div>
      </div>
    </div>
  );
}

const FIELDS_BY_KIND = {
  descriptor: [
    { key: "edge_or_skill", label: "Edge / Skill bonus", placeholder: "+1 Might Edge or trained in Speed defence…" },
    { key: "inability",     label: "Inability (one)",     placeholder: "Hindered by 1 step in stealth tasks…" },
    { key: "starter_kit",   label: "Starter kit / equipment", placeholder: "An iron horse-shoe, a dog-eared journal…" },
    { key: "ties_to_party", label: "Ties to the party (4 picks)" },
  ],
  foci: [
    { key: "tier1_ability",  label: "Tier 1 ability NAME",  placeholder: "Skill With Attacks (Light Weapons)" },
    { key: "tier2_ability",  label: "Tier 2 ability NAME" },
    { key: "tier3_ability",  label: "Tier 3 ability NAME" },
    { key: "tier4_ability",  label: "Tier 4 ability NAME" },
    { key: "tier5_ability",  label: "Tier 5 ability NAME" },
    { key: "tier6_ability",  label: "Tier 6 ability NAME" },
    { key: "minor_effect",   label: "Minor effect" },
    { key: "major_effect",   label: "Major effect" },
  ],
  cypher: [
    { key: "level_die",      label: "Level die",      placeholder: "1d6+2" },
    { key: "internal_external", label: "Internal / External" },
    { key: "form",           label: "Form",           placeholder: "Vial of glittering liquid" },
    { key: "effect",         label: "Effect (paraphrased)" },
  ],
  artifact: [
    { key: "level_die",   label: "Level die",     placeholder: "1d6+3" },
    { key: "form",        label: "Form" },
    { key: "effect",      label: "Effect" },
    { key: "depletion",   label: "Depletion roll", placeholder: "1 in 1d20" },
  ],
  type: [
    { key: "starting_pools", label: "Starting pools (M/S/I)", placeholder: "11 / 10 / 8" },
    { key: "starting_edge",  label: "Starting edge (M/S/I)",  placeholder: "1 / 0 / 0" },
    { key: "free_pool_pts",  label: "Free pool points",       placeholder: "6" },
    { key: "starting_effort", label: "Starting effort",       placeholder: "1" },
    { key: "starting_cypher_limit", label: "Starting cypher limit", placeholder: "2" },
  ],
};
