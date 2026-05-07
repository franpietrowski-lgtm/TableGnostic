import React from "react";
import { Store, ArrowRight, Copy, Eye, Bell, BadgeDollarSign, ShieldCheck } from "lucide-react";

const BULLETS = [
  { icon: Copy, text: "Publish custom rules and clone marketplace entries with one click." },
  { icon: Eye, text: "Watch list and weekly digest so creators see real interest." },
  { icon: ShieldCheck, text: "Snapshot listings so future edits don't break cloned copies." },
  { icon: Bell, text: "License attestation for public and paywalled listings." },
  { icon: BadgeDollarSign, text: "Future Stripe Connect author payouts (10% platform-cut concept)." },
];

export default function MarketplaceSection() {
  return (
    <section
      id="marketplace"
      className="relative z-10 px-5 md:px-10 py-24 md:py-32 border-y border-gold/10 bg-void/30"
      data-testid="marketplace-section"
    >
      <div className="max-w-6xl mx-auto grid lg:grid-cols-[1.05fr_0.95fr] gap-10 lg:gap-16 items-start">
        <div>
          <div className="label-ref mb-4">Marketplace + Homebrew</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            Homebrew is not a <span className="text-ember italic font-body normal-case">side door.</span>
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            TableGnostics treats custom content as a first-class part of the
            campaign. Create a race, class, feat, trait, power bundle, item,
            weapon, spell, house rule, artifact, focus, descriptor, or custom
            mechanic. Keep it private, share it with your campaign, publish it
            to the marketplace, or clone it into another table.
          </p>

          <ul className="mt-8 space-y-3.5">
            {BULLETS.map((b, i) => {
              const Icon = b.icon;
              return (
                <li key={i} className="flex gap-3 items-start" data-testid={`market-bullet-${i}`}>
                  <span className="w-7 h-7 rounded-sm border border-gold/30 text-gold flex items-center justify-center bg-void/40 shrink-0">
                    <Icon className="w-3.5 h-3.5" />
                  </span>
                  <span className="text-sm text-mist font-body leading-relaxed pt-1">{b.text}</span>
                </li>
              );
            })}
          </ul>

          <div className="mt-10 flex flex-wrap gap-3">
            <a
              href="/auth?mode=register"
              className="btn btn-primary px-6 py-3 text-sm"
              data-testid="market-cta-explore"
            >
              <Store className="w-4 h-4" /> Explore the marketplace <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          <p className="mt-7 text-xs italic font-body text-mist/60 max-w-lg leading-relaxed">
            Marketplace entries are for original, user-authored content or
            content the publisher has rights to share.
          </p>
        </div>

        {/* Marketplace mock card */}
        <div className="card-mystic p-5 md:p-6 relative">
          <div className="flex items-center justify-between">
            <div className="label-ref">Marketplace · public</div>
            <span className="text-[10px] font-mono text-gold/70">v6.25.10</span>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {[
              { name: "Pact of the Lantern", type: "Power Bundle", system: "BESM 4E", price: "Free" },
              { name: "Apocophea AutoMakers Bag", type: "Item", system: "BESM 4E", price: "Free" },
              { name: "Quick-Cast Glaive", type: "Class Tweak", system: "Cypher", price: "Free" },
              { name: "Eldritch Bargain", type: "House Rule", system: "D&D 5E", price: "Free" },
            ].map((m, i) => (
              <div
                key={i}
                className="rounded-sm border border-gold/20 bg-ink/60 p-3"
                data-testid={`market-mock-card-${i}`}
              >
                <div className="text-[10px] font-ui tracking-widest uppercase text-arcane">
                  {m.type}
                </div>
                <div className="mt-1 font-display text-sm text-parchment leading-tight">
                  {m.name}
                </div>
                <div className="mt-3 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-gold-bright">{m.system}</span>
                  <span className="text-mist/70">{m.price}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 px-3 py-2 rounded-sm bg-gold/10 border border-gold/30 text-[11px] font-ui tracking-wide text-gold-bright flex items-center gap-2">
            <Copy className="w-3 h-3" /> Cloned 23 times this week
          </div>
        </div>
      </div>
    </section>
  );
}
