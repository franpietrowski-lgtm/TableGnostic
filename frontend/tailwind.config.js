/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    container: { center: true, padding: "2rem", screens: { "2xl": "1400px" } },
    extend: {
      colors: {
        void: "#07060a",
        ink: "#0d0c12",
        parchment: "#f4ecd8",
        gold: {
          DEFAULT: "#c8a34a",
          bright: "#e5c370",
          deep: "#8a6b20",
          muted: "#7a6532",
        },
        sigil: "#d4af37",
        ember: "#b5542b",
        arcane: "#6d4a9e",
        mist: "#a9a3b8",
      },
      fontFamily: {
        display: ["Cinzel", "serif"],
        body: ["Fraunces", "serif"],
        ui: ["Manrope", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        sigil: "0 0 24px 0 rgba(212,175,55,0.15), inset 0 0 0 1px rgba(212,175,55,0.25)",
        "sigil-hover": "0 0 48px 0 rgba(212,175,55,0.35), inset 0 0 0 1px rgba(212,175,55,0.55)",
      },
      backgroundImage: {
        "star-noise":
          "radial-gradient(ellipse at top, rgba(109,74,158,0.08), transparent 55%), radial-gradient(ellipse at bottom, rgba(200,163,74,0.06), transparent 50%)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "drift": "drift 24s ease-in-out infinite",
        "flicker": "flicker 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        drift: { "0%,100%": { transform: "translate(0,0)" }, "50%": { transform: "translate(12px,-8px)" } },
        flicker: { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.82 } },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
