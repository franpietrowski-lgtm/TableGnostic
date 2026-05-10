/**
 * AppliedTemplatesPanel — V6.25.39
 *
 * Inline character-sheet block on the Mechanics tab. Shows which BESM
 * race / class templates the character has applied (read from
 * `folio.applied_templates`) plus a per-row breakdown of which
 * attributes / skills / defects were contributed by which template.
 *
 * V6.25.39 — Always renders for BESM/Anime-5E sheets even when no
 * templates are applied yet. Shows a "Pick a Race / Class →" deep link
 * so players can discover the feature instead of finding an empty card.
 */
import React from "react";
import { Link } from "react-router-dom";
import { Users, GraduationCap, ArrowRight } from "lucide-react";

export default function AppliedTemplatesPanel({ character }) {
  const folio = character?.folio || {};
  const applied = folio.applied_templates || [];

  const rowsFor = (tid) => {
    const a = (character.attributes || []).filter((x) => x.from_template_id === tid);
    const s = (character.skills || []).filter((x) => x.from_template_id === tid);
    const d = (character.defects || []).filter((x) => x.from_template_id === tid);
    return { attributes: a, skills: s, defects: d };
  };

  // Empty-state — render a discoverable placeholder so players can find
  // the race/class picker. Linked directly into the Character Builder's
  // Templates tab.
  if (applied.length === 0) {
    return (
      <div className="card-mystic p-4 mt-4" data-testid="applied-templates-panel-empty">
        <div className="flex items-baseline justify-between mb-2 flex-wrap gap-2">
          <div className="label-ref flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-gold/60"/>
            Race / Class Templates
          </div>
          <div className="text-[10px] text-mist italic">
            Optional — speeds Session 0.
          </div>
        </div>
        <div className="text-sm text-mist mb-3">
          No race or class template applied yet. Templates pre-build a
          mechanic bundle (stat adjustments, signature attributes, skills,
          and defects) so a player can spin up a recognisable archetype
          in one click — Apocophea, Lithomorph, Ferralith, Faunamimic, or
          a class chassis like Healer, Monk-Smith, Techgnostic-Wright.
        </div>
        {character?.campaign_id && (
          <Link to={`/app/campaigns/${character.campaign_id}/characters/${character.id}/edit?tab=templates`}
                className="btn btn-primary text-xs"
                data-testid="applied-templates-pick-cta">
            <GraduationCap className="w-3.5 h-3.5"/> Pick a Race / Class
            <ArrowRight className="w-3 h-3"/>
          </Link>
        )}
      </div>
    );
  }

  return (
    <div className="card-mystic p-4 mt-4" data-testid="applied-templates-panel">
      <div className="flex items-baseline justify-between mb-2 flex-wrap gap-2">
        <div className="label-ref flex items-center gap-2">
          <Users className="w-3.5 h-3.5 text-gold/60"/>
          Race / Class Templates
        </div>
        <div className="text-[10px] text-mist italic">
          Pre-built mechanic bundles applied at character creation. Optional —
          they only exist to speed Session 0.
        </div>
      </div>

      <div className="space-y-3">
        {applied.map((t) => {
          const rows = rowsFor(t.id);
          const sa = t.stat_adjustments || {};
          const statBits = ["body", "mind", "soul"]
            .filter((k) => (sa[k] ?? 0) !== 0)
            .map((k) => `${k[0].toUpperCase() + k.slice(1)} ${sa[k] > 0 ? "+" : ""}${sa[k]}`);
          return (
            <div key={t.id} className="border border-gold/15 rounded-sm p-3"
                 data-testid={`applied-template-${t.id}`}>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <span className="tag mr-2">{t.kind}</span>
                  <span className="font-display text-base text-parchment">{t.name}</span>
                </div>
                <span className={`text-[11px] font-ui ${(t.total_cp ?? 0) < 0 ? "text-arcane" : "text-gold-bright"}`}>
                  {t.total_cp ?? 0} CP
                </span>
              </div>

              {t.description && (
                <div className="text-[11px] text-mist mt-1 whitespace-pre-wrap font-body">
                  {t.description}
                </div>
              )}

              {statBits.length > 0 && (
                <div className="mt-2 text-[11px] text-parchment">
                  <span className="text-gold/60 uppercase tracking-widest text-[9px]">Stat adj.</span>
                  {" · "}{statBits.join(" / ")}
                </div>
              )}

              {(rows.attributes.length + rows.skills.length + rows.defects.length) > 0 && (
                <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-2 text-[11px]">
                  {rows.attributes.length > 0 && (
                    <div>
                      <div className="text-gold/60 uppercase tracking-widest text-[9px] mb-0.5">Attributes</div>
                      <ul className="space-y-0.5">
                        {rows.attributes.map((a, i) => (
                          <li key={i} className="text-parchment leading-snug">
                            — {a.name} <span className="text-mist/70">L{a.level}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {rows.skills.length > 0 && (
                    <div>
                      <div className="text-gold/60 uppercase tracking-widest text-[9px] mb-0.5">Skills</div>
                      <ul className="space-y-0.5">
                        {rows.skills.map((s, i) => (
                          <li key={i} className="text-parchment leading-snug">
                            — {s.group} <span className="text-mist/70">L{s.level}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {rows.defects.length > 0 && (
                    <div>
                      <div className="text-gold/60 uppercase tracking-widest text-[9px] mb-0.5">Defects</div>
                      <ul className="space-y-0.5">
                        {rows.defects.map((d, i) => (
                          <li key={i} className="text-parchment leading-snug">
                            — {d.name} <span className="text-mist/70">R{d.rank}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
