"""V6.19 — Per-level class progression timeline + proficiency block.

Surfaces, for any class+level pair, the cumulative list of features /
proficiencies / spell-known counts unlocked from level 1 to current.
Used by:
  - Character sheet "Granted at this level" timeline component
  - Pending-ticket compliance pre-flight (sanity-check spell counts)
  - Reference page (left-rail Class section auto-populates by class)

In-house authored summaries — no rulebook prose verbatim. Values come
from the SRD 5.1 class tables and the Anime 5E core class chassis (p.42-60).
"""
from __future__ import annotations
from typing import Any, Dict, List


# Compact per-class progression. Each class lists per-level grants:
#   level 1 grants: hit dice, save proficiencies, weapon/armor profs,
#                   skill picks, starting features.
#   level N grants: incremental features only.
# This is summary text — for detail the reference page links out.
CLASS_PROGRESSION: Dict[str, Dict[str, Any]] = {
    "Artificer": {
        "hit_die": "1d8",
        "save_profs": ["Constitution", "Intelligence"],
        "armor_profs": ["Light armor", "Medium armor", "Shields"],
        "weapon_profs": ["Simple weapons", "Hand crossbows", "Heavy crossbows"],
        "tool_profs_default": ["Thieves' tools", "Tinker's tools",
                                "+1 artisan tool of your choice"],
        "skill_choices": "2 from Arcana, History, Investigation, Medicine, Nature, Perception, Sleight of Hand",
        "spell_progression": "half_caster",
        "levels": {
            1: ["Magical Tinkering — turn 1-lb objects into magic-light/sound novelties.",
                "Spellcasting — Intelligence-based, Artificer spell list."],
            2: ["Infuse Item — 2 infusions known, 2 active (e.g. +1 weapon, bag of holding-equiv)."],
            3: ["Subclass — choose Alchemist / Artillerist / Battle Smith.",
                "The Right Tool for the Job — fabricate any artisan tool in 1 hour."],
            4: ["Ability Score Improvement (or feat)."],
            5: ["Subclass feature (e.g. Alchemical Savant / Arcane Firearm / Extra Attack).",
                "Artificer cantrips: 2 known."],
            6: ["Tool Expertise — double proficiency on tool checks.",
                "Subclass feature."],
            7: ["Flash of Genius — reaction, +INT to ally save/check 1/long rest."],
            8: ["Ability Score Improvement (or feat)."],
            9: ["Subclass feature."],
            10: ["Magic Item Adept — attune to 4 items max, faster crafting."],
        },
    },
    "Wizard": {
        "hit_die": "1d6",
        "save_profs": ["Intelligence", "Wisdom"],
        "armor_profs": [],
        "weapon_profs": ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"],
        "tool_profs_default": [],
        "skill_choices": "2 from Arcana, History, Insight, Investigation, Medicine, Religion",
        "spell_progression": "full_caster",
        "levels": {
            1: ["Spellcasting — Intelligence-based, Wizard spell list.",
                "Arcane Recovery — once/day on short rest, recover slots equal to ½ wizard level."],
            2: ["Arcane Tradition (subclass) — pick School of Evocation / Abjuration / etc."],
            3: ["2nd-level slots."],
            4: ["Ability Score Improvement (or feat)."],
            5: ["3rd-level slots."],
            6: ["Subclass feature."],
            7: ["4th-level slots."],
            8: ["Ability Score Improvement (or feat)."],
            9: ["5th-level slots."],
            10: ["Subclass feature."],
        },
    },
    "Fighter": {
        "hit_die": "1d10",
        "save_profs": ["Strength", "Constitution"],
        "armor_profs": ["All armor", "Shields"],
        "weapon_profs": ["Simple weapons", "Martial weapons"],
        "tool_profs_default": [],
        "skill_choices": "2 from Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, Survival",
        "spell_progression": "none",
        "levels": {
            1: ["Fighting Style — pick 1 of 6 (Archery / Defense / Dueling / GWF / Protection / TWF).",
                "Second Wind — bonus action, 1d10+level HP, 1/short rest."],
            2: ["Action Surge — 1 extra action, 1/short rest."],
            3: ["Martial Archetype (subclass) — Champion / Battle Master / Eldritch Knight."],
            4: ["Ability Score Improvement (or feat)."],
            5: ["Extra Attack — 2 attacks per Attack action."],
            6: ["Ability Score Improvement (or feat) [Fighter bonus]."],
            7: ["Subclass feature."],
            8: ["Ability Score Improvement (or feat)."],
            9: ["Indomitable — re-roll 1 failed save 1/long rest."],
            10: ["Subclass feature."],
        },
    },
    # Anime 5E originals (chassis is D&D-5E-flavoured):
    "Adept": {
        "hit_die": "1d8",
        "save_profs": ["Wisdom", "Charisma"],
        "armor_profs": ["Light armor"],
        "weapon_profs": ["Simple weapons", "Martial finesse weapons"],
        "tool_profs_default": ["Calligrapher's set OR meditation kit"],
        "skill_choices": "2 from Arcana, Insight, Perception, Persuasion, Religion",
        "spell_progression": "full_caster",
        "levels": {
            1: ["Spellcasting — Wisdom-based, Adept spell list.",
                "Inner Focus — bonus action, +CHA mod to next save 1/short rest."],
            2: ["Psychic Surge — overload a check or spell-attack 1/short rest (1d6, burnout on nat-1)."],
            3: ["Subclass — Way of the Empath / Way of the Aether."],
            4: ["Ability Score Improvement (or feat)."],
            5: ["3rd-level slots."],
        },
    },
    "Idol": {
        "hit_die": "1d8",
        "save_profs": ["Charisma", "Constitution"],
        "armor_profs": ["Light armor"],
        "weapon_profs": ["Simple weapons", "Hand crossbows", "Whips", "Concert mics-as-improvised"],
        "tool_profs_default": ["Disguise kit", "Choose 1 musical instrument"],
        "skill_choices": "3 from Acrobatics, Athletics, Performance, Persuasion, Sleight of Hand",
        "spell_progression": "half_caster",
        "levels": {
            1: ["Spellcasting — Charisma-based, Idol spell list.",
                "Charm Anthem — bonus action, target one creature within 30 ft, advantage on next CHA roll."],
            2: ["Idol Reserve — gain temp HP equal to CHA + idol level on Performance success 1/short rest."],
            3: ["Subclass — Stage Maven / Idol of Hope."],
            4: ["Ability Score Improvement (or feat)."],
            5: ["Encore Performance — heal allies who hear you for CHA × prof bonus 1/long rest."],
        },
    },
    "Pilot": {
        "hit_die": "1d10",
        "save_profs": ["Dexterity", "Intelligence"],
        "armor_profs": ["Light armor", "Medium armor", "Mecha-frame armor"],
        "weapon_profs": ["Simple weapons", "Vehicle-mounted weapons"],
        "tool_profs_default": ["Vehicles (mecha)", "Tinker's tools"],
        "skill_choices": "2 from Athletics, Investigation, Perception, Piloting, Tech",
        "spell_progression": "none",
        "levels": {
            1: ["Sortie Lock — bond with 1 mecha/vehicle; +PB to vehicle attacks; cockpit darkvision.",
                "Manoeuvre die — d6, fuels Pilot tactics."],
            2: ["Vehicle Action Surge — extra action while bonded 1/short rest."],
            3: ["Subclass — Sortie Specialist / Mecha Knight."],
            4: ["Ability Score Improvement (or feat)."],
            5: ["Extra Attack — 2 vehicle attacks per Attack action."],
        },
    },
    "Tinker": {
        "hit_die": "1d8",
        "save_profs": ["Constitution", "Intelligence"],
        "armor_profs": ["Light armor", "Medium armor"],
        "weapon_profs": ["Simple weapons", "Hand crossbows"],
        "tool_profs_default": ["Tinker's tools", "+2 artisan tools of your choice"],
        "skill_choices": "2 from Arcana, History, Investigation, Medicine, Sleight of Hand",
        "spell_progression": "half_caster",
        "levels": {
            1: ["Spellcasting — Intelligence-based, Tinker spell list.",
                "Improvised Gadget — fabricate a 1-shot gadget once/short rest."],
            2: ["Infuse Item — 2 infusions known, 2 active."],
            3: ["Subclass — Alchemist / Artillerist / Battle Smith."],
            4: ["Concoct Cypher — fabricate a single-use cypher gadget (1 hour, 25gp parts)."],
            5: ["Subclass feature."],
        },
    },
    # Add Cypher Type / Focus progression separately (different paradigm).
}


def cumulative_features(class_name: str, level: int) -> Dict[str, Any]:
    """Return cumulative features unlocked from level 1 to `level`.

    Strips parenthetical (e.g. 'Artificer (Alchemist)' → 'Artificer').
    Returns `{class, level, hit_die, save_profs, armor_profs, weapon_profs,
              tool_profs, skill_choices, spell_progression, timeline}`
    where `timeline` is `[{level, features: [...]}]` from level 1 to `level`.
    """
    base = (class_name or "").split("(")[0].strip()
    prog = CLASS_PROGRESSION.get(base)
    if not prog:
        return {
            "class": base, "level": level, "known": False,
            "timeline": [],
            "hit_die": "?",
            "save_profs": [], "armor_profs": [], "weapon_profs": [],
            "tool_profs": [], "skill_choices": "",
            "spell_progression": "unknown",
            "advice": (
                f"Class '{base}' has no canonical progression in the V6.19 "
                f"library — add a homebrew custom class entry via the "
                f"Atelier · References tab (kind: 'custom_class')."
            ),
        }
    timeline: List[Dict[str, Any]] = []
    lvl = max(1, int(level or 1))
    for L in range(1, lvl + 1):
        if L in prog["levels"]:
            timeline.append({"level": L, "features": prog["levels"][L]})
    return {
        "class": base,
        "level": lvl,
        "known": True,
        "hit_die": prog["hit_die"],
        "save_profs": prog["save_profs"],
        "armor_profs": prog["armor_profs"],
        "weapon_profs": prog["weapon_profs"],
        "tool_profs": prog["tool_profs_default"],
        "skill_choices": prog["skill_choices"],
        "spell_progression": prog["spell_progression"],
        "timeline": timeline,
    }
