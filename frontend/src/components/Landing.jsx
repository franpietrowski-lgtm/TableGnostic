import React, { useEffect } from "react";
import { useAuth } from "../lib/api";
import LandingNav from "./landing/LandingNav";
import Hero from "./landing/Hero";
import Pillars from "./landing/Pillars";
import SystemTrustStrip from "./landing/SystemTrustStrip";
import WhatItDoes from "./landing/WhatItDoes";
import RoleTour from "./landing/RoleTour";
import ProductProof from "./landing/ProductProof";
import FeatureHighlights from "./landing/FeatureHighlights";
import WizardTeasers from "./landing/WizardTeasers";
import MarketplaceSection from "./landing/MarketplaceSection";
import Roadmap from "./landing/Roadmap";
import AboutCreator from "./landing/AboutCreator";
import ContactWaitlist from "./landing/ContactWaitlist";
import LandingFooter from "./landing/LandingFooter";

/**
 * TableGnostics public landing page — single-page scrolling experience.
 * Sections (in order):
 *   1. Hero
 *   2. System trust strip
 *   3. What TableGnostics does
 *   4. Role-based tour
 *   5. Live product proof
 *   6. Feature highlights
 *   7. Wizards / helper flows (V2 teasers)
 *   8. Marketplace + homebrew
 *   9. Roadmap
 *  10. About the creator
 *  11. Contact / waitlist / community
 *  12. Footer
 */
export default function Landing() {
  const { user } = useAuth();

  // Smooth-scroll for in-page hash links (nav, hero anchors).
  useEffect(() => {
    const onClick = (e) => {
      const a = e.target.closest('a[href^="#"]');
      if (!a) return;
      const id = a.getAttribute("href").slice(1);
      if (!id) return;
      const el = document.getElementById(id);
      if (!el) return;
      e.preventDefault();
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  // Document title + description for SEO (no react-helmet dep).
  useEffect(() => {
    const prevTitle = document.title;
    document.title =
      "TableGnostics — Worldbuilding, Character Automation & Tabletop Campaign Tools";
    const setMeta = (name, content) => {
      let el = document.querySelector(`meta[name="${name}"]`);
      if (!el) {
        el = document.createElement("meta");
        el.setAttribute("name", name);
        document.head.appendChild(el);
      }
      el.setAttribute("content", content);
    };
    setMeta(
      "description",
      "TableGnostics is a multi-system tabletop platform for GMs, players, worldbuilders, and homebrew creators. Build worlds, automate character math, run play-by-post, manage sessions, publish homebrew, and export your campaign."
    );
    setMeta(
      "keywords",
      "tabletop campaign platform, worldbuilding software, GM tools, BESM 4E, Anime 5E, Cypher system, D&D campaign manager, play by post, homebrew marketplace, codex graph"
    );
    return () => {
      document.title = prevTitle;
    };
  }, []);

  const userResolved = user || null;

  return (
    <div className="page min-h-screen relative" data-testid="landing-root">
      <LandingNav user={userResolved} />
      <main>
        <Hero user={userResolved} />
        <Pillars />
        <SystemTrustStrip />
        <WhatItDoes />
        <RoleTour />
        <ProductProof />
        <FeatureHighlights />
        <WizardTeasers />
        <MarketplaceSection />
        <Roadmap />
        <AboutCreator />
        <ContactWaitlist />
      </main>
      <LandingFooter />
    </div>
  );
}
