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
// V6.25.47 — all 8 writer tools are real now. Lucide imports trimmed
// down to those still used (role-header + PickCampaignFirst surface).
// V6.25.46 — real authoring tools replacing the scaffold placeholders
// for Atlas, Magic Architect, Manuscript, and Outline.
// V6.25.47 — promoted the remaining 4 scaffolds to real tools:
// Cultures, Cosmology, POV Bibles, Themes & Motifs.
import WbAtlasTool from "./WbAtlasTool";
import WbMagicArchitectTool from "./WbMagicArchitectTool";
import WbCulturesTool from "./WbCulturesTool";
import WbCosmologyTool from "./WbCosmologyTool";
import StManuscriptTool from "./StManuscriptTool";
import StOutlineTool from "./StOutlineTool";
import StPovBiblesTool from "./StPovBiblesTool";
import StThemesTool from "./StThemesTool";

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
 * The real-tool surfaces are campaign-scoped — they need to know
 * WHICH campaign's data to load. When mounted as a standalone
 * `/app/wb/atlas` (no campaign context), we route the user to pick
 * a campaign first. When mounted inside the Atelier (`campId` prop
 * set), they render directly.
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

/* ---------- Worldbuilder pages ---------- */

export function WbAtlas({ campId }) {
  if (!campId) return <PickCampaignFirst label="Atlas" testid="wb-atlas-page"/>;
  return <WbAtlasTool campId={campId}/>;
}

export function WbMagicArchitect({ campId }) {
  if (!campId) return <PickCampaignFirst label="Magic Architect" testid="wb-magic-architect-page"/>;
  return <WbMagicArchitectTool campId={campId}/>;
}

export function WbCultures({ campId }) {
  if (!campId) return <PickCampaignFirst label="Cultures & Languages" testid="wb-cultures-page"/>;
  return <WbCulturesTool campId={campId}/>;
}

export function WbCosmology({ campId }) {
  if (!campId) return <PickCampaignFirst label="Cosmology & Calendar" testid="wb-cosmology-page"/>;
  return <WbCosmologyTool campId={campId}/>;
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

export function StPovBibles({ campId }) {
  if (!campId) return <PickCampaignFirst label="POV Character Bibles" testid="st-pov-bibles-page"/>;
  return <StPovBiblesTool campId={campId}/>;
}

export function StThemes({ campId }) {
  if (!campId) return <PickCampaignFirst label="Themes & Motifs" testid="st-themes-page"/>;
  return <StThemesTool campId={campId}/>;
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
