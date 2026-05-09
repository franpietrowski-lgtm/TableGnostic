import React from "react";

/**
 * Brand sigil — uppercase TG emblem inside a sevenfold star within a ringed
 * circle. Matches the in-app footer mark; safe to scale 24px → 200px.
 */
export default function Sigil({ size = 56, className = "", animate = false }) {
  return (
    <svg
      viewBox="0 0 120 120"
      style={{ width: size, height: size }}
      className={`logo-mark shrink-0 ${animate ? "sigil-animate" : ""} ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      data-testid="landing-sigil"
      aria-label="TableGnostic Sigil"
    >
      <defs>
        <linearGradient id="lsh" x1="0" x2="1">
          <stop offset="0" stopColor="#e5c370" />
          <stop offset="1" stopColor="#8a6b20" />
        </linearGradient>
        <radialGradient id="lshGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#e5c370" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#8a6b20" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="60" cy="60" r="56" fill="url(#lshGlow)" />
      <circle cx="60" cy="60" r="52" fill="none" stroke="url(#lsh)" strokeWidth="1" opacity="0.85" />
      <circle cx="60" cy="60" r="44" fill="none" stroke="url(#lsh)" strokeWidth="0.6" opacity="0.55" />
      <polygon
        points="60,18 72,38 96,40 78,56 82,80 60,68 38,80 42,56 24,40 48,38"
        fill="none"
        stroke="url(#lsh)"
        strokeWidth="1.2"
      />
      <polygon points="60,40 70,56 60,72 50,56" fill="url(#lsh)" opacity="0.30" />
      <text
        x="60" y="64" textAnchor="middle"
        fill="#e5c370" fontFamily="Cinzel, serif"
        fontSize="11" letterSpacing="3"
      >TG</text>
    </svg>
  );
}
