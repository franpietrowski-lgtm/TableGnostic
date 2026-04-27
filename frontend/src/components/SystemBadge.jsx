import React from "react";
import { Shield } from "lucide-react";

/**
 * System-specific badge & legal overlay for the CampaignDetail header.
 *
 * Per-system attribution lives HERE — not on the platform-wide footer
 * (which carries TableGnostic's own disclaimer). This is where Tri-Stat
 * Emporium · Dyskami · CC-BY · Cypher System Creator marks appear.
 *
 * Logo files are resolved from /system-logos/{system_id}.png with a
 * graceful fallback to the platform sigil when the file is absent.
 */

// Per-system: visible name on the badge, minimal mechanic-rights notice,
// and the licence-required attribution (verbatim where the licence dictates).
const PROFILES = {
  "besm-4e": {
    label: "BESM Fourth Edition",
    licence: "Tri-Stat Emporium · Dyskami Publishing Company",
    notice: "Mechanic-only references displayed under the Tri-Stat Emporium licence. " +
            "All rulebook prose, lore, and art © Mark MacKinnon / Dyskami Publishing.",
    accent: "#3B1E63",
  },
  "anime-5e": {
    label: "Anime 5E (Tri-Stat OGL)",
    licence: "Tri-Stat Emporium · Mark MacKinnon · Dyskami Publishing",
    notice: "Anime 5E SRD content displayed under the Open Game Licence. " +
            "Game mechanics only — flavour text & art remain © their creators.",
    accent: "#E03A8E",
  },
  "dnd-5e": {
    label: "D&D 5E (CC-BY SRD 5.1)",
    licence: "Wizards of the Coast LLC · CC-BY-4.0",
    notice: "Mechanics drawn exclusively from the System Reference Document 5.1. " +
            "No trademark-protected content (Forgotten Realms, classic monsters) " +
            "is reproduced. © Wizards of the Coast.",
    accent: "#7A1F2E",
  },
  "cypher": {
    label: "Cypher System (Cypher System Creator)",
    licence: "Monte Cook Games, LLC · Cypher System Creator programme",
    notice: "Requires the Cypher System Rulebook from Monte Cook Games. " +
            "Cypher System Creator licensed settings: Godforsaken · Gods of the Fall · " +
            "Masters of the Night · Predation · The Heartwood · The Revel · Unmasked. " +
            "Compatibility-only citations: Claim the Sky · Stay Alive! · The Origin · " +
            "The Stars Are Fire · We Are All Mad Here. Numenera / The Strange / " +
            "No Thank You, Evil! are NOT permitted under the Creator licence. " +
            "© Monte Cook Games, LLC.",
    accent: "#0F2540",
  },
  "_default": {
    label: "TableGnostic Custom System",
    licence: "Original / Community content",
    notice: "Mechanic content shown is original or community-sourced. " +
            "GMs are responsible for ensuring per-source licensing compliance.",
    accent: "#C8A34A",
  },
};


export default function SystemBadge({ systemId, systemName }) {
  const p = PROFILES[systemId] || PROFILES["_default"];
  const logoUrl = `/system-logos/${systemId}.png`;
  return (
    <div className="card-mystic p-3 mt-3 border" data-testid="system-badge"
         style={{ borderColor: `${p.accent}66` }}>
      <div className="flex items-center gap-3">
        <img src={logoUrl} alt={p.label}
             className="h-10 w-10 object-contain shrink-0 rounded-sm bg-void/40"
             onError={(e) => { e.currentTarget.style.display = "none"; }}
             data-testid="system-badge-logo"/>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-0.5">
            <Shield className="w-3 h-3 shrink-0" style={{ color: p.accent }}/>
            <span className="text-xs font-ui uppercase tracking-widest text-parchment truncate">
              {systemName || p.label}
            </span>
          </div>
          <div className="text-[10px] text-mist/80 font-ui">{p.licence}</div>
          <div className="text-[10px] text-mist/60 italic mt-1 leading-snug"
               data-testid="system-badge-notice">{p.notice}</div>
        </div>
      </div>
    </div>
  );
}
