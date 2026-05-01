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
// `logo` is the absolute path under /app/frontend/public/system-logos/ —
// each publisher's logo file has a different stem, so the mapping is
// explicit (don't try to derive from system_id).
const PROFILES = {
  "besm-4e": {
    label: "BESM Fourth Edition",
    licence: "Tri-Stat Emporium · Dyskami Publishing Company",
    notice: "Mechanic-only references displayed under the Tri-Stat Emporium licence. " +
            "All rulebook prose, lore, and art © Mark MacKinnon / Dyskami Publishing.",
    accent: "#3B1E63",
    logo: "/system-logos/besm-4e.png",
  },
  "anime-5e": {
    label: "Anime 5E (Tri-Stat OGL)",
    licence: "Tri-Stat Emporium · Mark MacKinnon · Dyskami Publishing",
    notice: "Anime 5E SRD content displayed under the Open Game Licence. " +
            "Game mechanics only — flavour text & art remain © their creators.",
    accent: "#E03A8E",
    logo: "/system-logos/anime5e-tristat-emporium.png",
  },
  "dnd-5e": {
    label: "D&D 5E (CC-BY SRD 5.1)",
    licence: "Wizards of the Coast LLC · CC-BY-4.0",
    notice: "Mechanics drawn exclusively from the System Reference Document 5.1. " +
            "No trademark-protected content (Forgotten Realms, classic monsters) " +
            "is reproduced. © Wizards of the Coast.",
    accent: "#7A1F2E",
    logo: null,  // No bundled SRD-safe logo — fallback to platform sigil + text.
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
    logo: "/system-logos/cypher.png",
  },
  "_default": {
    label: "TableGnostic Custom System",
    licence: "Original / Community content",
    notice: "Mechanic content shown is original or community-sourced. " +
            "GMs are responsible for ensuring per-source licensing compliance.",
    accent: "#C8A34A",
    logo: null,
  },
};


export default function SystemBadge({ systemId, systemName, compact = false }) {
  const p = PROFILES[systemId] || PROFILES["_default"];
  const logoUrl = p.logo;
  if (compact) {
    // Card-corner colored pill — used on the Campaigns + Discover lists where
    // the full notice would crowd the tile. The accent colour matches the
    // publisher's brand so a glance distinguishes systems visually.
    return (
      <div
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm border text-[10px] font-ui uppercase tracking-widest"
        style={{ borderColor: `${p.accent}77`, color: p.accent, background: `${p.accent}14` }}
        data-testid="system-badge-compact"
        title={`${p.label} · ${p.licence}`}>
        <Shield className="w-3 h-3 shrink-0" style={{ color: p.accent }} />
        <span className="truncate">{systemName || p.label}</span>
      </div>
    );
  }
  return (
    <div className="card-mystic p-3 mt-3 border" data-testid="system-badge"
         style={{ borderColor: `${p.accent}66` }}>
      <div className="flex items-center gap-3">
        {logoUrl ? (
          <img src={logoUrl} alt={p.label}
               className="h-10 w-10 object-contain shrink-0 rounded-sm bg-void/40"
               onError={(e) => { e.currentTarget.style.display = "none"; }}
               data-testid="system-badge-logo"/>
        ) : (
          <div
            className="h-10 w-10 shrink-0 rounded-sm flex items-center justify-center font-display text-[10px] tracking-widest"
            style={{ background: `${p.accent}22`, color: p.accent, border: `1px solid ${p.accent}66` }}
            data-testid="system-badge-logo-fallback"
            aria-label={p.label}>
            {(systemId || "").slice(0, 4).toUpperCase()}
          </div>
        )}
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
