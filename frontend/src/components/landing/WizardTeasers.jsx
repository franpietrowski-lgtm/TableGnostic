import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Compass, Upload, Megaphone, Rocket, Lock, Star, ArrowRight } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
  // V6.25.40 — Featured showcase ribbon. Pulls from `/api/public/featured`
  // (admin-curated, falls back to most-recently-published showcase).
  const [featured, setFeatured] = useState(null);
  useEffect(() => {
    let cancel = false;
    axios.get(`${API}/public/featured`)
      .then((r) => !cancel && setFeatured(r.data.item))
      .catch(() => !cancel && setFeatured(null));
    return () => { cancel = true; };
  }, []);

  return (
    <section id="wizards" className="relative z-10 px-5 md:px-10 py-24 md:py-32" data-testid="wizards-section">
      <div className="max-w-6xl mx-auto">
        {featured && (
          <div className="card-mystic p-6 md:p-8 mb-14 grid md:grid-cols-[1fr_auto] items-center gap-6"
               data-testid="featured-showcase">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-3 h-3 text-gold-bright"/>
                <span className="text-[10px] tracking-widest uppercase text-gold-bright">
                  {featured.featured ? "Featured table" : "Most recent showcase"}
                </span>
              </div>
              <h3 className="font-display text-2xl md:text-3xl text-parchment uppercase tracking-tight leading-tight">
                {featured.name}
              </h3>
              <div className="text-[11px] uppercase tracking-widest text-mist mt-1">
                {featured.system_id} · GM {featured.gm_name}
              </div>
              {featured.blurb && (
                <p className="mt-3 text-sm text-mist font-body leading-relaxed max-w-2xl">{featured.blurb}</p>
              )}
            </div>
            <div className="flex flex-col gap-2 shrink-0">
              <Link to={`/discover/${featured.slug}`}
                    className="btn btn-primary text-xs"
                    data-testid="featured-cta-showcase">
                Visit the showcase <ArrowRight className="w-3 h-3"/>
              </Link>
              <Link to={`/discover/${featured.slug}/gazette`}
                    className="btn btn-ghost text-xs"
                    data-testid="featured-cta-gazette">
                Read the Gazette <ArrowRight className="w-3 h-3"/>
              </Link>
            </div>
          </div>
        )}

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
