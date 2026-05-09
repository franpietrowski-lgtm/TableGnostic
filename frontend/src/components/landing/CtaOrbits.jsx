import React from "react";

/**
 * CtaOrbits — small decorative orbital flourish that lives NEXT TO the
 * primary signup CTA in the hero left column.
 *
 * 3 concentric rune-rings with 3 orbiting glyph dots that gently emit a
 * gold pulse toward the button. Pure CSS / SVG — no JS, no canvas, no
 * heavy animation library. Honors prefers-reduced-motion.
 */
export default function CtaOrbits({ size = 96 }) {
  return (
    <div
      className="cta-orbits relative shrink-0 select-none pointer-events-none"
      style={{ width: size, height: size }}
      data-testid="cta-orbits"
      aria-hidden="true"
    >
      {/* glow halo */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background:
            "radial-gradient(circle at 50% 50%, rgba(212,175,55,0.28) 0%, rgba(109,74,158,0.12) 45%, transparent 72%)",
          filter: "blur(2px)",
          animation: "ctaOrbitsHalo 4.5s ease-in-out infinite",
        }}
      />

      <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full">
        <defs>
          <linearGradient id="ctaG" x1="0" x2="1">
            <stop offset="0" stopColor="#e5c370" />
            <stop offset="1" stopColor="#8a6b20" />
          </linearGradient>
          <radialGradient id="ctaDotG" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#f4dc92" />
            <stop offset="100%" stopColor="#8a6b20" stopOpacity="0.3" />
          </radialGradient>
        </defs>

        {/* outer rune ring — slow CCW spin */}
        <g style={{ transformOrigin: "50px 50px", animation: "ctaOrbitsCcw 22s linear infinite" }}>
          <circle cx="50" cy="50" r="44" fill="none" stroke="url(#ctaG)" strokeWidth="0.6" opacity="0.5" />
          {/* tick marks */}
          {Array.from({ length: 12 }).map((_, i) => {
            const a = (i / 12) * Math.PI * 2;
            const x1 = 50 + Math.cos(a) * 41.5;
            const y1 = 50 + Math.sin(a) * 41.5;
            const x2 = 50 + Math.cos(a) * 44.5;
            const y2 = 50 + Math.sin(a) * 44.5;
            return (
              <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="url(#ctaG)" strokeWidth="0.6" opacity={i % 3 === 0 ? 0.85 : 0.35} />
            );
          })}
        </g>

        {/* mid ring — CW */}
        <g style={{ transformOrigin: "50px 50px", animation: "ctaOrbitsCw 14s linear infinite" }}>
          <circle cx="50" cy="50" r="32" fill="none" stroke="url(#ctaG)" strokeWidth="0.5"
                  strokeDasharray="2 4" opacity="0.55" />
        </g>

        {/* inner heptagram — slow pulse only */}
        <g style={{ transformOrigin: "50px 50px", animation: "ctaOrbitsPulse 3.4s ease-in-out infinite" }}>
          <polygon
            points="50,28 60,40 78,42 64,55 68,72 50,63 32,72 36,55 22,42 40,40"
            fill="none" stroke="url(#ctaG)" strokeWidth="0.7" opacity="0.85"
          />
          <polygon
            points="50,40 56,49 50,58 44,49"
            fill="url(#ctaG)" opacity="0.18"
          />
        </g>

        {/* 3 orbiting glyph dots, each on its own rotation */}
        <g style={{ transformOrigin: "50px 50px", animation: "ctaOrbitsCw 9s linear infinite" }}>
          <circle cx="50" cy="6" r="2.2" fill="url(#ctaDotG)" />
        </g>
        <g style={{ transformOrigin: "50px 50px", animation: "ctaOrbitsCcw 13s linear infinite" }}>
          <circle cx="50" cy="18" r="1.6" fill="url(#ctaDotG)" opacity="0.85" />
        </g>
        <g style={{ transformOrigin: "50px 50px", animation: "ctaOrbitsCw 17s linear infinite" }}>
          <circle cx="94" cy="50" r="1.4" fill="#e5c370" opacity="0.7" />
        </g>
      </svg>

      <style>{`
        @keyframes ctaOrbitsCw {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes ctaOrbitsCcw {
          from { transform: rotate(0deg); }
          to   { transform: rotate(-360deg); }
        }
        @keyframes ctaOrbitsPulse {
          0%, 100% { opacity: 0.75; transform: scale(1); }
          50%      { opacity: 1;    transform: scale(1.03); }
        }
        @keyframes ctaOrbitsHalo {
          0%, 100% { opacity: 0.55; transform: scale(1); }
          50%      { opacity: 0.85; transform: scale(1.06); }
        }
        @media (prefers-reduced-motion: reduce) {
          .cta-orbits *,
          .cta-orbits {
            animation: none !important;
          }
        }
      `}</style>
    </div>
  );
}
