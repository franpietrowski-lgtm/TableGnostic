/**
 * V6.25.45 — Writer-role page scaffolds.
 *
 * MVP placeholders for the Worldbuilder + Storyteller account roles.
 * Each page renders a niche-styled hero card with a feature outline
 * and a "what's coming" note. The intent is to wire up the navigation
 * + role gating end-to-end so the experience swap is real; the
 * authoring tools themselves ship in follow-up drops.
 *
 * Why a single file? These are intentionally lightweight stubs and
 * keeping them grouped lets us iterate quickly without 8 separate
 * files cluttering the components dir. When a stub graduates to a
 * real tool, it can be promoted to its own module.
 */
import React from "react";
import {
  Map as MapIcon, Sparkles, Globe2, Library, Compass,
  PenTool, Feather, ListTree, Target,
} from "lucide-react";
// V6.25.46 — real authoring tools replacing the scaffold placeholders
// for Atlas, Magic Architect, Manuscript, and Outline. The remaining
// 4 (Cultures, Cosmology, POV Bibles, Themes) stay scaffolded with
// "coming next ship" honest labels until their backend lands.
import WbAtlasTool from "./WbAtlasTool";
import WbMagicArchitectTool from "./WbMagicArchitectTool";
import StManuscriptTool from "./StManuscriptTool";
import StOutlineTool from "./StOutlineTool";

const ROLE_THEME = {
  worldbuilder: {
    accent: "text-emerald-300",
    bg: "from-emerald-950/40 to-void/30",
    ring: "border-emerald-700/30",
  },
  storyteller: {
    accent: "text-rose-300",
    bg: "from-rose-950/40 to-void/30",
    ring: "border-rose-800/30",
  },
};

/**
 * V6.25.46 — Campaign-picker stub.
 *
 * The real-tool surfaces (Atlas, Magic Architect, Manuscript, Outline)
 * are campaign-scoped — they need to know WHICH campaign's data to
 * load. When mounted as a standalone `/app/wb/atlas` (no campaign
 * context), we route the user to pick a campaign first. When mounted
 * inside the Atelier (`campId` prop set), they render directly.
 */
function PickCampaignFirst({ label, testid }) {
  return (
    <div className="p-8 max-w-xl mx-auto card-mystic" data-testid={testid}>
      <div className="label-ref text-gold-bright mb-2">{label}</div>
      <div className="text-mist leading-relaxed">
        This authoring tool is campaign-scoped. Open one of your
        campaigns and switch to <b>Atelier ▸ Worldbuilder Studio</b> (or
        <b> Storyteller Workshop</b>) to use it. Standalone access from
        the writer-role nav is coming in a future drop.
      </div>
      <a href="/app/campaigns"
         className="btn btn-primary text-xs mt-4 inline-flex items-center gap-1"
         data-testid={`${testid}-pick-campaign`}>
        Open Campaigns →
      </a>
    </div>
  );
}

function ScaffoldPage({ role, title, icon: Icon, blurb, bullets, testid }) {
  const t = ROLE_THEME[role];
  return (
    <div className={`p-6 max-w-3xl mx-auto`} data-testid={testid}>
      <div className={`card-mystic ${t.ring} p-6 bg-gradient-to-br ${t.bg}`}>
        <div className="flex items-center gap-3 mb-4">
          <Icon className={`w-7 h-7 ${t.accent}`}/>
          <div>
            <div className="label-ref text-mist/70">{role === "worldbuilder" ? "Worldbuilder" : "Storyteller"}</div>
            <h1 className="text-2xl font-display tracking-wide text-parchment">{title}</h1>
          </div>
        </div>
        <p className="text-mist leading-relaxed mb-5">{blurb}</p>
        <div className="space-y-2">
          {bullets.map((b, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <span className={`mt-1 w-1.5 h-1.5 rounded-full ${t.accent.replace("text-", "bg-")}`}/>
              <span className="text-mist/90">{b}</span>
            </div>
          ))}
        </div>
        <div className={`mt-6 text-[11px] uppercase tracking-widest ${t.accent} italic`}>
          Coming in V6.25.47 — Atlas, Magic Architect, Manuscript, and Outline
          shipped real tools first. The role + nav swap is live now.
        </div>
      </div>
    </div>
  );
}

/* ---------- Worldbuilder pages ---------- */

export function WbAtlas({ campId }) {
  // V6.25.46 — campId may come from Atelier-embedded usage. For the
  // standalone /app/wb/atlas route, campId is undefined; the user
  // must pick which campaign's atlas they want to edit first.
  if (!campId) return <PickCampaignFirst label="Atlas" testid="wb-atlas-page"/>;
  return <WbAtlasTool campId={campId}/>;
}

export function WbMagicArchitect({ campId }) {
  if (!campId) return <PickCampaignFirst label="Magic Architect" testid="wb-magic-architect-page"/>;
  return <WbMagicArchitectTool campId={campId}/>;
}

export function WbCultures() {
  return <ScaffoldPage role="worldbuilder" title="Cultures & Languages" icon={Library}
    testid="wb-cultures-page"
    blurb="People-groups, their tongues, their rituals, their kitchen smells. Tag each culture with naming conventions, etiquette quirks, and conflict triggers."
    bullets={[
      "Culture sheets with naming generators (per culture & per role).",
      "Language seeds (phonology hints, common phrases, etiquette).",
      "Ritual & holiday calendar tied into the Cosmology page.",
      "Diaspora / migration history that powers PC backstory prompts.",
    ]}/>;
}

export function WbCosmology() {
  return <ScaffoldPage role="worldbuilder" title="Cosmology & Calendar" icon={Compass}
    testid="wb-cosmology-page"
    blurb="The shape of time and the layers of reality. Sun(s), moon(s), planes, prophesied dates. The skeleton that every culture's calendar pins itself to."
    bullets={[
      "Planar / dimensional model with bleed-through rules.",
      "Calendar editor: per-culture month/day naming + festival anchors.",
      "Eclipses, omens, prophesied dates auto-feed the timeline.",
      "Cosmic event ledger (great wars, sealings, etc.).",
    ]}/>;
}

/* ---------- Storyteller pages ---------- */

export function StManuscript({ campId }) {
  if (!campId) return <PickCampaignFirst label="Manuscript" testid="st-manuscript-page"/>;
  return <StManuscriptTool campId={campId}/>;
}

export function StOutline({ campId }) {
  if (!campId) return <PickCampaignFirst label="Outline & Beats" testid="st-outline-page"/>;
  return <StOutlineTool campId={campId}/>;
}

export function StPovBibles() {
  return <ScaffoldPage role="storyteller" title="POV Character Bibles" icon={Feather}
    testid="st-pov-bibles-page"
    blurb="Literary character sheets. Not statted — voiced. Goals, wounds, lies they believe, what they want vs. what they need, how they sound on the page."
    bullets={[
      "POV sheet per character: voice quirks, vocab fingerprints, gait.",
      "Want / Need / Wound triangle with progression tracking.",
      "Relationship web (read-only by default; opt-in to publish).",
      "Per-character revelation timeline — what does the reader know when?",
    ]}/>;
}

export function StThemes() {
  return <ScaffoldPage role="storyteller" title="Themes & Motifs" icon={Target}
    testid="st-themes-page"
    blurb="Themes are the spine; motifs are the recurring metaphors. Track which beats embody which themes and where each motif appears so revisions stay coherent."
    bullets={[
      "Theme ledger with intent + counter-statement.",
      "Motif tracker: term + first occurrence + cadence (linear, climactic, accelerating).",
      "Thematic heat-map across chapters.",
      "Revision-pass checklist: 'does this scene serve a tracked theme?'",
    ]}/>;
}

/* ---------- Default world-builder/storyteller dashboard tile ----------
   The user lands on /app first; we render a role-specific welcome card
   so they immediately know they're in the writer dashboard, not the
   standard player/gm dashboard. Surfaced as a small component the
   default Dashboard can mount when role is writer-typed.
*/

export function WriterRoleHeader({ role, userName }) {
  if (role !== "worldbuilder" && role !== "storyteller") return null;
  const t = ROLE_THEME[role];
  const sub = role === "worldbuilder"
    ? "Building worlds for novels, novellas, and the games other people will run inside them."
    : "Outlining, drafting, and revising tales — the campaign is the manuscript.";
  return (
    <div className={`card-mystic ${t.ring} p-4 bg-gradient-to-br ${t.bg} mb-4`}
         data-testid={`writer-role-header-${role}`}>
      <div className="label-ref text-mist/70">
        Welcome back, {userName || "writer"}
      </div>
      <div className={`text-lg font-display tracking-wide ${t.accent}`}>
        {role === "worldbuilder" ? "Worldbuilder Studio" : "Storyteller Workshop"}
      </div>
      <div className="text-[12px] text-mist/80 italic mt-1">{sub}</div>
    </div>
  );
}
