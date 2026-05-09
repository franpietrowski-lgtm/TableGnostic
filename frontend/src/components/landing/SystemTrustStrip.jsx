import React from "react";

const FIRST_CLASS = [
  { id: "besm-4e", label: "BESM 4E", img: "/system-logos/besm-4e.png" },
  { id: "anime-5e", label: "Anime 5E", img: "/system-logos/anime5e-tristat-emporium.png" },
  { id: "cypher", label: "Cypher", img: "/system-logos/cypher.png" },
  { id: "dnd-5e", label: "D&D 5E", img: null },
];

const SCAFFOLDED = [
  "Pathfinder",
  "Fate",
  "Mothership",
  "Blades in the Dark",
  "Call of Cthulhu",
  "Savage Worlds",
  "Cyberpunk RED",
  "Vampire: the Masquerade",
  "Shadowrun",
  "Numenera",
];

export default function SystemTrustStrip() {
  return (
    <section
      className="relative z-10 border-y border-gold/10 bg-void/40 backdrop-blur-sm py-12 md:py-16"
      data-testid="system-trust-strip"
    >
      <div className="max-w-6xl mx-auto px-5 md:px-10">
        <div className="text-center">
          <div className="label-ref mb-3">System-aware. Not system-locked.</div>
          <div className="font-display text-xl md:text-2xl tracking-[0.18em] text-parchment uppercase">
            Four flagship systems. <span className="text-gold">Ten more scaffolded.</span>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-6 items-center justify-items-center">
          {FIRST_CLASS.map((s) => (
            <div
              key={s.id}
              className="flex flex-col items-center gap-3 opacity-90 hover:opacity-100 transition-opacity"
              data-testid={`trust-system-${s.id}`}
            >
              {s.img ? (
                <img
                  src={s.img}
                  alt={s.label}
                  className="h-14 w-auto max-w-[140px] object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              ) : (
                <div className="h-14 w-[140px] flex items-center justify-center border border-gold/30 rounded-sm bg-void/40">
                  <span className="font-display text-2xl text-gold tracking-widest">
                    D&amp;D
                  </span>
                </div>
              )}
              <div className="text-[10px] font-ui uppercase tracking-[0.22em] text-mist/80 text-center">
                {s.label}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-center gap-2">
          <span className="text-[10px] font-ui uppercase tracking-[0.3em] text-mist/60 mr-2">
            Scaffolded:
          </span>
          {SCAFFOLDED.map((name) => (
            <span
              key={name}
              className="text-[10px] font-ui tracking-[0.18em] uppercase text-mist/70 border border-gold/15 rounded-sm px-2.5 py-1 bg-ink/40"
              data-testid={`scaffold-${name.toLowerCase().replace(/[^a-z0-9]/g, "-")}`}
            >
              {name}
            </span>
          ))}
        </div>

        <p className="mt-10 max-w-3xl mx-auto text-center text-xs md:text-sm font-body italic text-mist/70 leading-relaxed">
          TableGnostics helps automate your table&rsquo;s own campaign data. It does
          not replace the books you already own. Mechanic names and page references
          only — never reproduced rulebook prose, art, or setting text.
        </p>
      </div>
    </section>
  );
}
