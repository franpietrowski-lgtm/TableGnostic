/**
 * MacroBar — system-aware quick-roll buttons for the Session Dice Altar.
 *
 * Given a character (optional) and the campaign's system_id, render a
 * tight grid of one-click dice macros that set the notation + label
 * fields on the parent dice roller. A follow-up click on "Roll" fires.
 *
 * Systems supported today:
 *   - BESM 4E: 2d6+stat checks (Body/Mind/Soul), ACV/DCV, initiative.
 *   - D&D 5E: d20+ability checks (six), advantage, disadvantage.
 *   - Cypher: 1d20 vs difficulty, +edge, -impaired.
 *   - Anime 5E: both 2d6 (Tri-Stat) AND d20 (D&D chassis) sets.
 *
 * The macro labels use the character's current shaped stats when we
 * have them; otherwise fall back to raw notation so the GM can still
 * roll flat dice.
 */
import React from "react";
import { Zap } from "lucide-react";

function Macros({ systemId, character, onPick }) {
  const f = character?.folio || {};
  const dnd = f.dnd_state;
  const cyph = f.cypher_state;
  const stats = character?.stats || { body: 0, mind: 0, soul: 0 };

  // D&D score → modifier
  const mod = (s) => Math.floor(((s | 0) - 10) / 2);
  const modStr = (v) => (v >= 0 ? `+${v}` : `${v}`);

  const out = [];

  const push = (label, notation, titleOverride) => {
    out.push({ label, notation, title: titleOverride || `${label} → ${notation}` });
  };

  if (systemId === "besm-4e" || (systemId === "anime-5e" && !dnd)) {
    push("Body",  `2d6+${stats.body|0}`);
    push("Mind",  `2d6+${stats.mind|0}`);
    push("Soul",  `2d6+${stats.soul|0}`);
    push("ACV",   `2d6+${(stats.body|0)+(stats.mind|0)}`, "ACV = Body+Mind");
    push("DCV",   `2d6+${(stats.body|0)+(stats.mind|0)}`, "DCV = Body+Mind");
    push("Init",  `1d6+${(stats.body|0)+(stats.mind|0)}`, "Initiative (1d6 + Body + Mind)");
  }

  if (dnd) {
    const a = dnd.ability_scores || {};
    push("STR", `d20${modStr(mod(a.Strength))}`);
    push("DEX", `d20${modStr(mod(a.Dexterity))}`);
    push("CON", `d20${modStr(mod(a.Constitution))}`);
    push("INT", `d20${modStr(mod(a.Intelligence))}`);
    push("WIS", `d20${modStr(mod(a.Wisdom))}`);
    push("CHA", `d20${modStr(mod(a.Charisma))}`);
    // Advantage / disadvantage — use 2d20-keep-highest/lowest notation if
    // your dice engine supports it; otherwise fall back to raw 2d20.
    push("Adv",  "2d20kh1", "Advantage (keep highest of 2d20)");
    push("Dis",  "2d20kl1", "Disadvantage (keep lowest of 2d20)");
  }

  if (cyph) {
    push("d20",     "1d20", "Flat difficulty check");
    push("d20+1",   "1d20+1", "Asset applied (+1 step)");
    push("d20-3",   "1d20-3", "Impaired (-3)");
    push("GM Intr", "1d6", "GM Intrusion reroll (1d6 narrative)");
  }

  // Anime 5E hybrid — if we have both a dnd_state AND anime5e_state,
  // append the Tri-Stat set.
  if (systemId === "anime-5e" && dnd && f.anime5e_state) {
    push("2d6+B", `2d6+${stats.body|0}`, "Tri-Stat Body");
    push("2d6+M", `2d6+${stats.mind|0}`, "Tri-Stat Mind");
    push("2d6+S", `2d6+${stats.soul|0}`, "Tri-Stat Soul");
  }

  return out;
}

export default function MacroBar({ systemId, character, onPick }) {
  const macros = Macros({ systemId, character, onPick });
  if (!macros.length) return null;
  return (
    <div className="border-t border-gold/10 pt-2 mt-2" data-testid="macro-bar">
      <div className="label-ref mb-1 flex items-center gap-1">
        <Zap className="w-3 h-3"/>
        Macros{character?.name ? ` · ${character.name}` : ""}
      </div>
      <div className="flex flex-wrap gap-1">
        {macros.map((m, i) => (
          <button key={i} type="button"
                  onClick={() => onPick(m.notation, m.label)}
                  className="px-2 py-1 text-[10px] font-ui border border-gold/20 rounded-sm
                             hover:border-gold/60 hover:bg-gold/10 text-parchment/90
                             tracking-widest uppercase"
                  title={m.title}
                  data-testid={`macro-${m.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}>
            {m.label}
          </button>
        ))}
      </div>
    </div>
  );
}
