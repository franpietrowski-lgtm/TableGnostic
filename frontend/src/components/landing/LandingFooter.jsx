import React from "react";
import Sigil from "./Sigil";

export default function LandingFooter() {
  const year = new Date().getFullYear();
  return (
    <footer
      className="relative z-10 border-t border-gold/15 bg-gradient-to-b from-void/60 to-void/95 px-5 md:px-12 py-14"
      data-testid="landing-footer"
    >
      <div className="max-w-5xl mx-auto flex flex-col items-center text-center gap-5">
        <a href="#hero" className="inline-flex flex-col items-center gap-3 group" data-testid="footer-brand">
          <Sigil size={84} />
          <div>
            <div className="font-display tracking-[0.3em] text-base text-parchment group-hover:text-gold-bright transition-colors">
              TABLEGNOSTICS
            </div>
            <div className="text-[10px] font-ui tracking-[0.28em] uppercase text-gold/65 mt-0.5">
              not the system. the table.
            </div>
          </div>
        </a>

        <div
          className="text-[11px] text-parchment/85 font-ui tracking-wide"
          data-testid="footer-creator"
        >
          Created &amp; solely owned by{" "}
          <span className="text-gold-bright font-display tracking-[0.22em]">
            FRANCIS&nbsp;T.&nbsp;PIETROWSKI
          </span>
        </div>

        <div
          className="text-[10px] md:text-[11px] text-mist/80 leading-relaxed font-ui max-w-3xl"
          data-testid="footer-legal"
        >
          <p>
            TableGnostics is an independent, system-aware tabletop platform.
            All <strong>original platform code, UI, branding, mark, and
            creator-authored content</strong> are © {year} Francis T.
            Pietrowski, all rights reserved. The TableGnostics mark and the
            &ldquo;Not the system. The table.&rdquo; tagline are proprietary.
          </p>
          <p className="mt-2">
            Game systems referenced inside campaigns &mdash; including BESM 4E,
            Anime 5E, the Cypher System, Numenera, Dungeons &amp; Dragons,
            Pathfinder, Fate, Mothership, Blades in the Dark, Call of Cthulhu,
            Savage Worlds, Cyberpunk RED, Vampire: the Masquerade, and
            Shadowrun &mdash; are the property of their respective rights-holders.
            The platform displays only mechanical names, page references, and
            numerics. <strong>No rulebook prose, lore, art, or proprietary
            setting material is reproduced</strong>; per-system attribution and
            required licence text appear on each campaign page and exported PDF.
          </p>
          <p className="mt-2">
            Use of TableGnostics is provided <strong>&ldquo;as-is&rdquo;</strong>{" "}
            without warranty of any kind. The creator and platform are not
            liable for any game-table outcomes, lost data, or damages arising
            from use. Users are solely responsible for the homebrew content
            they author and for ensuring they have the rights to share or sell
            any material published through the marketplace.
          </p>
        </div>

        <div className="text-[10px] text-mist/60 font-ui tracking-wide pt-4 border-t border-gold/10 w-full max-w-3xl">
          © {year} Francis T. Pietrowski · TableGnostics Platform · All rights
          reserved.
        </div>
      </div>
    </footer>
  );
}
