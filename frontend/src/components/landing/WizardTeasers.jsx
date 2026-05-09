import React from "react";
import { Compass, Upload, Megaphone, Rocket, Lock } from "lucide-react";

/**
 * Wizards are V2 per blueprint scope. Render teaser cards so visitors
 * see the surface area without exposing half-functional flows.
 */
const TEASERS = [
  {
    icon: Compass,
    title: "What system fits my table?",
    blurb: "Five questions on tone, crunch, power scale, session style, and homebrew tolerance — answered with a recommended system profile.",
    cta: "Find my table style",
  },
  {
    icon: Upload,
    title: "From spreadsheet to TableGnostics",
    blurb: "Paste a CSV row or short character sketch and preview the starter sheet shape before you commit.",
    cta: "Convert a character row",
  },
  {
    icon: Megaphone,
    title: "Publish my homebrew",
    blurb: "Choose a content type, summarise, set visibility, attest to license. Walk away with a marketplace listing preview.",
    cta: "Prepare a marketplace entry",
  },
  {
    icon: Rocket,
    title: "Build my first campaign space",
    blurb: "Name, system, session style, worldbuilding depth, player count → a starting module set ready to open in the app.",
    cta: "Draft a campaign workspace",
  },
];

export default function WizardTeasers() {
  return (
    <section id="wizards" className="relative z-10 px-5 md:px-10 py-24 md:py-32" data-testid="wizards-section">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <div className="label-ref mb-4">Wizards &amp; helper flows</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            Start faster. <span className="text-gold italic font-body normal-case">Fix less.</span>
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            Four guided helpers ship in the V2 landing release, giving visitors a
            taste of TableGnostics before account creation. Below is what is on
            deck.
          </p>
        </div>

        <div className="mt-14 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {TEASERS.map((t, i) => {
            const Icon = t.icon;
            return (
              <div
                key={t.title}
                className="card-mystic p-5 md:p-6 relative overflow-hidden"
                data-testid={`wizard-teaser-${i}`}
              >
                <div className="absolute top-3 right-3 inline-flex items-center gap-1 text-[9px] font-ui tracking-[0.25em] uppercase text-arcane border border-arcane/30 rounded-sm px-1.5 py-0.5 bg-void/60">
                  <Lock className="w-2.5 h-2.5" /> V2
                </div>
                <div className="w-9 h-9 mb-4 rounded-sm border border-gold/30 text-gold flex items-center justify-center bg-void/50">
                  <Icon className="w-4 h-4" />
                </div>
                <h3 className="font-display text-base text-parchment uppercase tracking-wide leading-snug">
                  {t.title}
                </h3>
                <p className="mt-3 text-sm text-mist font-body leading-relaxed">
                  {t.blurb}
                </p>
                <div className="mt-5 text-[11px] font-ui uppercase tracking-[0.22em] text-mist/55">
                  Coming: {t.cta}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
