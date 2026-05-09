import React from "react";
import { Quote, Mail } from "lucide-react";
import Sigil from "./Sigil";

export default function AboutCreator() {
  return (
    <section id="about" className="relative z-10 px-5 md:px-10 py-24 md:py-32" data-testid="about-section">
      <div className="max-w-5xl mx-auto">
        <div className="grid md:grid-cols-[260px_1fr] gap-10 md:gap-14 items-start">
          {/* Founder mark — sigil + initials block. No portrait shipped yet. */}
          <div className="flex flex-col items-center md:items-start" data-testid="about-mark">
            <div
              className="relative rounded-sm border border-gold/30 bg-void/60 p-8 sigil-ring"
              style={{ aspectRatio: "1/1.1" }}
            >
              <Sigil size={140} />
              <div className="mt-5 text-center font-display tracking-[0.3em] text-parchment text-sm">
                F.&nbsp;T.&nbsp;P.
              </div>
              <div className="mt-1 text-center text-[10px] uppercase tracking-[0.32em] text-gold/65 font-ui">
                Creator · Sole Owner
              </div>
            </div>
          </div>

          <div>
            <div className="label-ref mb-4">About the creator</div>
            <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
              Built by a <span className="text-gold italic font-body normal-case">table person,</span> not a content farm.
            </h2>
            <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
              TableGnostics was created by{" "}
              <span className="text-parchment">Francis T. Pietrowski</span> as a
              response to a familiar tabletop problem: the campaign lives in too
              many places.
            </p>
            <p className="mt-4 text-mist text-base font-body leading-relaxed">
              The goal is not to replace the imagination of the GM, the books on
              the shelf, or the identity of any ruleset. The goal is to give the
              table a shared brain — one place where worlds, characters,
              mechanics, sessions, and homebrew can actually stay connected.
            </p>

            <blockquote className="mt-9 border-l border-gold/40 pl-6 italic font-body text-base md:text-lg text-parchment/90 leading-relaxed relative">
              <Quote className="absolute -left-3 -top-2 w-5 h-5 text-gold/50" />
              &ldquo;I built TableGnostics because I was tired of running games out of
              Discord, PDFs, spreadsheets, note apps, random macros, and memory.
              The table deserved better.&rdquo;
              <div className="not-italic mt-3 text-[11px] font-ui tracking-[0.28em] uppercase text-gold/70">
                — Francis T. Pietrowski
              </div>
            </blockquote>

            <div className="mt-9">
              <a href="#contact" className="btn px-6 py-3 text-sm" data-testid="about-cta-feedback">
                <Mail className="w-4 h-4" /> Send Feedback
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
