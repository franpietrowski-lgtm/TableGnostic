"""V6.25.13 — Anime 5E core class library (CANONICAL).

Source: dys_anime5e_rpg_v1.3.6.pdf (Anime 5E core rulebook).
Replaces V6.25.12 scaffold. Per-level features extracted verbatim
from the core book's class progression tables.

Mechanics (per Anime 5E core):
  • 14 canonical core classes.
  • Total 200 character Points over Levels 1-20.
  • Proficiency Bonus: +2 at L1, +1 every 4 levels (cap +6 at L17).
  • Ability Score Improvement: +2 to one OR +1 to two (max 20 unless GM allows higher).
  • Class selection does NOT require Discretionary Points.
  • Effects-based system: Anime 5E grants are listed as
    `{name, points}` pairs where `points` = the Point cost taken
    from the class's running Point budget (the [N] tokens in the
    feature column).
  • Multi-classing allowed; duplicate proficiencies from multiclass
    grant Bonus Points.

Legal: only mechanic NAMES, page-quotient grants, and Point costs
are reproduced — no rulebook prose. Per-system attribution + the
Anime 5E rights-holder credit appear on the campaign hub + PDF
exports.
"""
from __future__ import annotations
from typing import Any, Dict, List

PROFICIENCY_BONUS = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6,
}

# ASI prompts surface on the AdvancementBadge whenever a class's
# per-level entry includes "Ability Score Improvement [2]". The
# advancement engine reads the per-class table directly — this set is
# kept for legacy/fallback only.
ASI_LEVELS_FALLBACK = {4, 8, 12, 16, 19}


# ── canonical 14-class roster ───────────────────────────────────────
# Each `features` dict maps level (1-20) to a list of grant strings
# verbatim from the Anime 5E core class table. The advancement engine
# parses each grant for ASI prompts, point grants, and skill choices.

CORE_CLASSES: List[Dict[str, Any]] = [
    {
        "id": "adventurer", "name": "Adventurer", "page": 22,
        "primary_ability": "Dexterity", "hit_die": 6,
        "save_proficiencies": ["Dexterity", "Constitution", "Wisdom"],
        "skill_picks": 5,
        "weapon_proficiencies": ["simple", "select-2-martial"],
        "armour_proficiencies": ["light", "medium"],
        "tool_proficiencies": ["any-2"],
        "features": {
            1:  ["+2 Points [2]", "+2 Proficiency Bonus [2]"],
            2:  ["+2 Points [2]"],
            3:  ["+3 Points [3]"],
            4:  ["+3 Points [3]"],
            5:  ["+4 Points [4]"],
            6:  ["+4 Points [4]"],
            7:  ["+5 Points [5]"],
            8:  ["+5 Points [5]"],
            9:  ["+6 Points [6]"],
            10: ["+6 Points [6]"],
            11: ["+6 Points [6]"],
            12: ["+6 Points [6]"],
            13: ["+6 Points [6]"],
            14: ["+6 Points [6]"],
            15: ["+6 Points [6]"],
            16: ["+6 Points [6]"],
            17: ["+6 Points [6]"],
            18: ["+6 Points [6]"],
            19: ["+7 Points [7]"],
            20: ["+7 Points [7]"],
        },
    },
    {
        "id": "bender", "name": "Bender", "page": 28,
        "primary_ability": "Constitution", "hit_die": 8,
        "save_proficiencies": ["Constitution", "Wisdom"],
        "skill_picks": 2,
        "weapon_proficiencies": ["simple", "select-4-martial"],
        "armour_proficiencies": ["light", "shield"],
        "features": {
            1:  ["+1 Dynamic Powers – Lesser [5]"],
            2:  ["+2 Points [2]", "+1 Immutable [1]"],
            3:  ["+1 Dynamic Powers – Lesser [5]"],
            4:  ["+2 Points [2]", "+1 Energised [1]", "Ability Score Improvement [2]"],
            5:  ["+1 Dynamic Powers – Lesser [5]", "+1 Skill Proficiency [1]"],
            6:  ["+2 Points [2]", "+2 Edge (Attacks with Dynamic Powers) [2]"],
            7:  ["+1 Dynamic Powers – Lesser [5]"],
            8:  ["+2 Points [2]", "+1 Energised [1]", "Ability Score Improvement [2]"],
            9:  ["+1 Dynamic Powers – Lesser [5]"],
            10: ["+2 Points [2]", "+1 Immutable [1]", "+1 Skill Proficiency [1]"],
            11: ["+1 Dynamic Powers – Lesser [5]"],
            12: ["+2 Points [2]", "+1 Energised [1]", "Ability Score Improvement [2]"],
            13: ["+1 Dynamic Powers – Lesser [5]"],
            14: ["+2 Points [2]", "+4 Forced Disadvantage (All Attacks Against Character) [4]"],
            15: ["+1 Dynamic Powers – Lesser [5]", "+1 Skill Proficiency [1]"],
            16: ["+2 Points [2]", "Ability Score Improvement [2]"],
            17: ["+1 Dynamic Powers – Lesser [5]"],
            18: ["+3 Points [3]", "+1 Immutable [1]"],
            19: ["+1 Dynamic Powers – Lesser [5]", "Ability Score Improvement [2]"],
            20: ["+4 Points [4]"],
        },
    },
    {
        "id": "broker", "name": "Broker", "page": 34,
        "primary_ability": "Wisdom", "hit_die": 6,
        "save_proficiencies": ["Wisdom"],
        "skill_picks": 4,
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": [],
        "tool_proficiencies": ["any-4"],
        "features": {
            1:  ["+2 Points [2]", "+1 Connected [1]"],
            2:  ["+2 Points [2]", "+1 Sixth Sense [1]", "Ability Score Improvement [2]"],
            3:  ["+2 Points [2]", "+1 Features [1]", "+1 Skill Proficiency [1]"],
            4:  ["+2 Points [2]", "+1 Pocket Dimension [2]", "Ability Score Improvement [2]"],
            5:  ["+2 Points [2]", "+1 Item [4]"],
            6:  ["+2 Points [2]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            7:  ["+2 Points [2]", "+1 Connected [1]", "+1 Features [1]", "+1 Wealth [3]"],
            8:  ["+2 Points [2]", "+1 Saving Throw Proficiency [2]", "Ability Score Improvement [2]"],
            9:  ["+2 Points [2]", "+1 Sixth Sense [1]", "+1 Pocket Dimension [2]", "+1 Skill Proficiency [1]"],
            10: ["+2 Points [2]", "+1 Item [4]", "Ability Score Improvement [2]"],
            11: ["+2 Points [2]", "+1 Connected [1]", "+1 Features [1]"],
            12: ["+2 Points [2]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            13: ["+2 Points [2]", "+1 Sixth Sense [1]", "+1 Wealth [3]"],
            14: ["+2 Points [2]", "+1 Connected [1]", "+1 Pocket Dimension [2]", "Ability Score Improvement [2]"],
            15: ["+2 Points [2]", "+1 Item [4]", "+1 Skill Proficiency [1]"],
            16: ["+2 Points [2]", "+1 Saving Throw Proficiency [2]", "Ability Score Improvement [2]"],
            17: ["+2 Points [2]", "+1 Connected [1]", "+1 Features [1]", "+1 Sixth Sense [1]"],
            18: ["+2 Points [2]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            19: ["+2 Points [2]", "+1 Pocket Dimension [2]", "+1 Wealth [3]"],
            20: ["+2 Item [8]", "Ability Score Improvement [2]"],
        },
    },
    {
        "id": "dynamic-spellbinder", "name": "Dynamic Spellbinder", "page": 40,
        "primary_ability": "Intelligence", "hit_die": 6,
        "save_proficiencies": ["Intelligence"],
        "skill_picks": 2,
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": [],
        "features": {
            **{lvl: ["+1 Dynamic Powers [10]"] for lvl in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]},
            **{lvl: ["+2 Points [2]"] for lvl in [4, 8, 10, 14, 18, 20]},
            2:  ["+2 Points [2]", "+1 Energised [1]"],
            6:  ["+2 Points [2]", "+1 Energised [1]"],
            12: ["+2 Points [2]", "+1 Energised [1]"],
            16: ["+2 Points [2]", "+1 Energised [1]"],
        },
    },
    {
        "id": "hunter", "name": "Hunter", "page": 46,
        "primary_ability": "Strength", "hit_die": 10,
        "save_proficiencies": ["Constitution", "Intelligence"],
        "skill_picks": 3,
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light", "medium"],
        "tool_proficiencies": ["any-1"],
        "features": {
            1:  ["+1 Connected [1]"],
            2:  ["+1 Combat Technique [1]", "+1 Skill Proficiency [1]"],
            3:  ["+2 Points [2]", "+1 Special Movement [1]"],
            4:  ["+1 Wealth [3]", "Ability Score Improvement [2]"],
            5:  ["+1 Extra Actions [4]"],
            6:  ["+1 Connected [1]", "+3 Massive Damage – Lesser (+1d6 One Type) [3]"],
            7:  ["+1 Item [4]"],
            8:  ["+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            9:  ["+1 Heightened Senses [1]", "+2 Weapon [2]"],
            10: ["+1 Connected [1]", "+1 Extra Actions [4]"],
            11: ["+1 Skill Proficiency [1]", "+1 Wealth [3]"],
            12: ["+3 Massive Damage – Lesser (+1d6 One Type) [3]"],
            13: ["+1 Combat Technique [1]", "Ability Score Improvement [2]"],
            14: ["+1 Heightened Senses [1]", "+1 Item [4]"],
            15: ["+1 Extra Actions [4]"],
            16: ["+1 Wealth [3]", "Ability Score Improvement [2]"],
            17: ["+1 Connected [1]", "+2 Weapon [2]", "+1 Skill Proficiency [1]"],
            18: ["+1 Combat Technique [1]", "+3 Massive Damage – Lesser (+1d6 One Type) [3]"],
            19: ["+1 Special Movement [1]", "Ability Score Improvement [2]"],
            20: ["+4 Weapon [4]"],
        },
    },
    {
        "id": "isekai-student", "name": "Isekai Student", "page": 52,
        "primary_ability": "Charisma", "hit_die": 4,
        "save_proficiencies": ["Charisma"],
        "skill_picks": 2,
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": [],
        "features": {
            1:  ["+2 Points [2]", "+1 Mulligan [1]", "+1 Sixth Sense [1]"],
            2:  ["+2 Points [2]", "+1 Item [4]", "+1 Saving Throw Proficiency [2]", "Ability Score Improvement [2]"],
            3:  ["+4 Points [4]", "+1 Minions [2]", "+1 Skill Proficiency [1]"],
            4:  ["+2 Points [2]", "+1 Mulligan [1]", "Ability Score Improvement [2]"],
            5:  ["+4 Points [4]", "+1 Connected [1]", "+1 Inspire [1]"],
            6:  ["+2 Points [2]", "+1 Item [4]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            7:  ["+4 Points [4]", "+1 Mulligan [1]", "+1 Sixth Sense [1]"],
            8:  ["+2 Points [2]", "+1 Connected [1]", "+1 Minions [2]", "Ability Score Improvement [2]"],
            9:  ["+4 Points [4]", "+1 Skill Proficiency [1]", "+1 Saving Throw Proficiency [2]"],
            10: ["+2 Points [2]", "+1 Inspire [1]", "+1 Item [4]", "+1 Mulligan [1]", "Ability Score Improvement [2]"],
            11: ["+4 Points [4]", "+1 Connected [1]", "+1 Special Movement [1]"],
            12: ["+2 Points [2]", "+1 Immutable [1]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            13: ["+4 Points [4]", "+1 Minions [2]", "+1 Mulligan [1]", "+1 Sixth Sense [1]"],
            14: ["+2 Points [2]", "+1 Connected [1]", "+1 Item [4]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            15: ["+4 Points [4]", "+1 Inspire [1]", "+1 Saving Throw Proficiency [2]"],
            16: ["+2 Points [2]", "+1 Mulligan [1]", "Ability Score Improvement [2]"],
            17: ["+4 Points [4]", "+1 Connected [1]", "+1 Special Movement [1]"],
            18: ["+2 Points [2]", "+1 Minions [2]", "+1 Sixth Sense [1]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            19: ["+4 Points [4]", "+1 Item [4]"],
            20: ["+6 Points [6]", "+1 Connected [1]", "Ability Score Improvement [2]"],
        },
    },
    {
        "id": "magical-girl-guy", "name": "Magical Girl/Guy", "page": 58,
        "primary_ability": "Wisdom", "hit_die": 8,
        "save_proficiencies": ["Wisdom", "Charisma"],
        "skill_picks": 3,
        "weapon_proficiencies": ["simple", "select-2-martial"],
        "armour_proficiencies": ["light", "shield"],
        "tool_proficiencies": ["any-1"],
        "features": {
            1:  ["+1 Alternate Identity [1]", "+1 Companion [5]", "+1 Weapon [1]"],
            2:  ["+1 Point [1]", "+1 Companion [5]"],
            3:  ["+1 Item [4]", "Ability Score Improvement [2]"],
            4:  ["+1 Jumping [1]", "+2 Regeneration [2]"],
            5:  ["+1 Flight [3]", "+1 Skill Proficiency [1]"],
            6:  ["+2 Points [2]", "+1 Item [4]"],
            7:  ["+2 Points [2]", "+1 Regeneration [1]", "+1 Weapon [1]"],
            8:  ["+1 Extra Action [4]"],
            9:  ["+1 Item [4]", "Ability Score Improvement [2]"],
            10: ["+1 Saving Throw Proficiency [2]"],
            11: ["+1 Flight [3]", "+1 Skill Proficiency [1]"],
            12: ["+3 Points [3]", "+1 Weapon [1]"],
            13: ["+1 Item [4]", "+1 Regeneration [1]"],
            14: ["+1 Dynamic Powers [10]"],
            15: ["+1 Item [4]", "Ability Score Improvement [2]"],
            16: ["+1 Flight [3]"],
            17: ["+1 Skill Proficiency [1]", "+1 Weapon [1]"],
            18: ["+1 Item [4]"],
            19: ["+1 Weapon [1]"],
            20: ["+1 Dynamic Powers [10]"],
        },
    },
    {
        "id": "ninja", "name": "Ninja", "page": 64,
        "primary_ability": "Dexterity", "hit_die": 8,
        "save_proficiencies": ["Dexterity"],
        "skill_picks": 4,
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light", "shield"],
        "tool_proficiencies": ["any-2"],
        "features": {
            1:  ["+1 Point [1]", "+1 Jumping [1]"],
            2:  ["+1 Point [1]", "+2 Edge (Initiative Rolls) [2]"],
            3:  ["+1 Point [1]", "+1 Heightened Senses [1]", "+2 Massive Damage – Lesser (+1d4 Sneak Attacks) [2]"],
            4:  ["+1 Point [1]", "+1 Special Movement [1]", "Ability Score Improvement [2]"],
            5:  ["+1 Point [1]", "+1 Extra Actions [4]", "+1 Special Movement [1]"],
            6:  ["+1 Point [1]", "+1 Jumping [1]", "Ability Score Improvement [2]"],
            7:  ["+1 Point [1]", "+1 Sixth Sense [1]", "+1 Teleport [3]"],
            8:  ["+1 Point [1]", "+1 Control Environment (Darkness) [1]", "+2 Massive Damage – Lesser (+1d4 Sneak Attacks) [2]", "Ability Score Improvement [2]"],
            9:  ["+1 Point [1]", "+1 Fast [1]", "+1 Heightened Senses [1]"],
            10: ["+1 Point [1]", "+1 Combat Technique [1]", "Ability Score Improvement [2]"],
            11: ["+1 Point [1]", "+1 Combat Technique [1]", "+1 Jumping [1]"],
            12: ["+1 Point [1]", "+4 Forced Disadvantage (All Attacks Against Character) [4]", "Ability Score Improvement [2]"],
            13: ["+1 Point [1]", "+2 Massive Damage – Lesser (+1d4 Sneak Attacks) [2]", "+1 Special Movement [1]"],
            14: ["+1 Point [1]", "+1 Teleport [3]", "Ability Score Improvement [2]"],
            15: ["+1 Point [1]", "+1 Control Environment (Silence) [1]", "+1 Sixth Sense [1]"],
            16: ["+1 Point [1]", "+1 Jumping [1]", "Ability Score Improvement [2]"],
            17: ["+1 Point [1]", "+1 Extra Actions [4]", "+2 Undetectable (Sight 2) [4]"],
            18: ["+1 Point [1]", "+4 Edge (Attack Rolls) [4]", "Ability Score Improvement [2]"],
            19: ["+1 Point [1]", "+1 Heightened Senses [1]", "+2 Massive Damage – Lesser (+1d4 Sneak Attacks) [2]"],
            20: ["+2 Points [2]", "+2 Special Movement [2]", "Ability Score Improvement [2]"],
        },
    },
    {
        "id": "pet-monster-trainer", "name": "Pet Monster Trainer", "page": 70,
        "primary_ability": "Charisma", "hit_die": 4,
        "save_proficiencies": ["Dexterity", "Charisma"],
        "skill_picks": 2,
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": [],
        "features": {
            1:  ["+1 Companion [5]"],
            2:  ["+2 Points [2]", "+1 Monster Training [1]", "+1 Skill Proficiency [1]"],
            3:  ["+2 Points [2]", "+1 Companion [5]"],
            4:  ["+2 Points [2]", "+1 Monster Training [1]", "+1 Telepathy – Lesser (Pet Monster) [1]", "Ability Score Improvement [2]"],
            5:  ["+3 Points [3]", "+1 Companion [5]", "+1 Skill Proficiency [1]"],
            6:  ["+4 Points [4]", "+1 Saving Throw Proficiency [2]"],
            7:  ["+2 Points [2]", "+1 Companion [5]", "+1 Monster Training [1]"],
            8:  ["+1 Skill Proficiency [1]", "+1 Wealth [3]", "Ability Score Improvement [2]"],
            9:  ["+2 Points [2]", "+1 Companion [5]"],
            10: ["+4 Point [4]", "+1 Monster Training [1]", "+1 Extra Actions – Lesser [2]"],
            11: ["+2 Points [2]", "+1 Companion [5]", "+1 Skill Proficiency [1]"],
            12: ["+2 Points [2]", "+1 Saving Throw Proficiency [2]", "+1 Telepathy – Lesser (Pet Monster) [1]", "Ability Score Improvement [2]"],
            13: ["+3 Points [3]", "+1 Companion [5]", "+1 Monster Training [1]"],
            14: ["+4 Points [4]", "+1 Skill Proficiency [1]", "+1 Wealth [3]"],
            15: ["+2 Points [2]", "+1 Companion [5]"],
            16: ["+2 Points [2]", "+1 Monster Training [1]", "+1 Telepathy – Lesser (Pet Monster) [1]", "Ability Score Improvement [2]"],
            17: ["+3 Points [3]", "+1 Companion [5]", "+1 Skill Proficiency [1]"],
            18: ["+3 Point [3]", "+1 Telepathy [3]", "+1 Wealth [3]"],
            19: ["+1 Companion [5]", "+1 Monster Training [1]", "Ability Score Improvement [2]"],
            20: ["+3 Points [3]", "+1 Wealth [3]"],
        },
    },
    {
        "id": "psionicist", "name": "Psionicist", "page": 76,
        "primary_ability": "Intelligence", "hit_die": 4,
        "save_proficiencies": ["Intelligence", "Charisma"],
        "skill_picks": 2,
        "weapon_proficiencies": ["simple", "select-2-martial"],
        "armour_proficiencies": ["light", "shield"],
        "features": {
            1:  ["+1 Point [1]", "Spellcasting [2]"],
            2:  ["+1 Point [1]", "Spellcasting [4]"],
            3:  ["+1 Point [1]", "Spellcasting [6]"],
            4:  ["+1 Point [1]", "Spellcasting [5]"],
            5:  ["+1 Point [1]", "Spellcasting [9]"],
            6:  ["+1 Point [1]", "Spellcasting [5]"],
            7:  ["+1 Point [1]", "Spellcasting [11]"],
            8:  ["+1 Point [1]", "Spellcasting [6]"],
            9:  ["+1 Point [1]", "Spellcasting [8]"],
            10: ["+1 Point [1]", "Spellcasting [6]"],
            11: ["+1 Point [1]"],
            12: ["+1 Point [1]", "Spellcasting [9]"],
            13: ["+1 Point [1]", "Spellcasting [8]"],
            14: ["+1 Point [1]"],
            15: ["+1 Point [1]", "Spellcasting [10]"],
            16: ["+1 Point [1]", "Spellcasting [9]"],
            17: ["+1 Point [1]"],
            18: ["+1 Point [1]", "Spellcasting [11]"],
            19: ["+1 Point [1]", "Spellcasting [10]"],
            20: ["+1 Point [1]"],
        },
    },
    {
        "id": "samurai", "name": "Samurai", "page": 82,
        "primary_ability": "Strength", "hit_die": 10,
        "save_proficiencies": ["Strength", "Wisdom"],
        "skill_picks": 3,
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light", "medium", "heavy", "shield"],
        "tool_proficiencies": ["any-1"],
        "features": {
            1:  ["+2 Edge (Initiative Rolls) [2]"],
            2:  ["+1 Point [1]", "+1 Fast [1]"],
            3:  ["+1 Point [1]", "Ability Score Improvement [2]"],
            4:  ["+1 Point [1]", "+1 Combat Technique (Judge Opponent) [1]"],
            5:  ["+2 Combat Technique (Two Weapons) [2]", "+1 Inspire [1]", "+1 Skill Proficiency [1]"],
            6:  ["+3 Massive Damage – Lesser (+1d6 Melee Weapons) [3]", "Ability Score Improvement [2]"],
            7:  ["+1 Combat Technique (Critical Strike) [1]", "+1 Jumping [1]"],
            8:  ["+1 Skill Proficiency [1]", "+1 Extra Actions [4]"],
            9:  ["+1 Point [1]", "+1 Special Movement [1]", "Ability Score Improvement [2]"],
            10: ["+1 Combat Technique (Blind Fighting) [1]", "+1 Inspire [1]", "+1 Skill Proficiency [1]"],
            11: ["+2 Points [2]", "+2 Weapon [2]"],
            12: ["+3 Massive Damage – Lesser (+1d6 Melee Weapons) [3]", "Ability Score Improvement [2]"],
            13: ["+2 Points [2]", "+1 Combat Technique (Extended Range) [1]"],
            14: ["+1 Jumping [1]", "+1 Mulligan [1]", "+2 Weapon [2]"],
            15: ["+1 Inspire [1]", "+1 Skill Proficiency [1]", "Ability Score Improvement [2]"],
            16: ["+1 Extra Actions [4]"],
            17: ["+1 Skill Proficiency [1]", "+2 Weapon [2]"],
            18: ["+3 Massive Damage – Lesser (+1d6 Melee Weapons) [3]", "Ability Score Improvement [2]"],
            19: ["+2 Points [2]", "+1 Inspire [1]"],
            20: ["+1 Wealth [3]", "+2 Weapon [2]"],
        },
    },
    {
        "id": "shadow-warrior", "name": "Shadow Warrior", "page": 88,
        "primary_ability": "Strength", "hit_die": 12,
        "save_proficiencies": ["Strength"],
        "skill_picks": 1,
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light", "medium", "heavy", "shield"],
        "features": {
            1:  ["+1 Regeneration [1]"],
            2:  ["+2 Change State [6]"],
            3:  ["+1 Size Change – Lesser (Grow) [4]"],
            4:  ["+1 Extra Actions [4]"],
            5:  ["+1 Skill Proficiency [1]"],
            6:  ["+4 Massive Damage – Lesser (+1d8 Melee Attacks) [4]"],
            7:  ["+1 Regeneration [1]"],
            8:  ["Ability Score Improvement [2]"],
            9:  ["+1 Size Change – Lesser (Grow) [4]"],
            10: ["+1 Extra Actions [4]"],
            11: ["+1 Skill Proficiency [1]"],
            12: ["+1 Regeneration [1]"],
            13: ["+4 Massive Damage – Lesser (+1d8 Melee Attacks) [4]"],
            14: ["Ability Score Improvement [2]"],
            15: ["+1 Size Change – Lesser (Grow) [4]"],
            16: ["+1 Extra Actions [4]"],
            17: ["Ability Score Improvement [2]"],
            18: ["+1 Regeneration [1]"],
            19: ["+1 Skill Proficiency [1]"],
            20: ["+2 Change State [6]"],
        },
    },
    {
        "id": "techknight", "name": "Techknight", "page": 94,
        "primary_ability": "Dexterity", "hit_die": 10,
        "save_proficiencies": ["Dexterity", "Constitution"],
        "skill_picks": 3,
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light", "medium", "heavy", "shield"],
        "tool_proficiencies": ["any-1"],
        "features": {
            1:  ["+2 Combat Technique [2]", "+1 Connected (Techknight Order) [1]", "Techknight Armour [0]"],
            2:  ["+1 Item [4]"],
            3:  ["+1 Extra Actions [4]", "+1 Protected (-1 Melee damage) [1]"],
            4:  ["Ability Score Improvement [2]"],
            5:  ["+1 Combat Technique [1]", "+1 Protected (-1 Ranged damage) [1]"],
            6:  ["+1 Item [4]", "+1 Skill Proficiency [1]"],
            7:  ["+2 Edge (Saving Throws for 1 Ability) [2]", "+1 Protected (-1 Melee damage) [1]"],
            8:  ["+1 Combat Technique [1]", "Ability Score Improvement [2]"],
            9:  ["+1 Extra Actions [4]", "+1 Protected (-1 Ranged damage) [1]"],
            10: ["+1 Item [4]", "+1 Skill Proficiency [1]"],
            11: ["+1 Point [1]", "+1 Protected (-1 Melee damage) [1]"],
            12: ["+1 Point [1]", "Ability Score Improvement [2]"],
            13: ["+1 Extra Actions [4]", "+1 Protected (-1 Ranged damage) [1]"],
            14: ["+1 Item [4]", "+1 Skill Proficiency [1]"],
            15: ["+1 Point [1]", "+1 Sixth Sense [1]", "+1 Control Environment (Silence) [1]"],
            16: ["+1 Combat Technique [1]", "Ability Score Improvement [2]"],
            17: ["+1 Item [4]", "+1 Protected (-1 Melee damage) [1]"],
            18: ["+1 Extra Actions [4]"],
            19: ["Ability Score Improvement [2]"],
            20: ["+2 Points [2]", "+1 Protected (-1 Ranged damage) [1]"],
        },
    },
    {
        "id": "warder", "name": "Warder", "page": 100,
        "primary_ability": "Constitution", "hit_die": 6,
        "save_proficiencies": ["Constitution"],
        "skill_picks": 4,
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": ["shield"],
        "tool_proficiencies": ["any-1"],
        "features": {
            1:  ["+1 Massive Damage (+1) [3]", "+1 Special Movement [1]"],
            2:  ["+2 Points [2]", "+1 AC Bonus [1]", "+1 Skill Proficiency [1]", "+1 Special Movement [1]"],
            3:  ["+2 Points [2]", "+1 Transfer [3]", "Ability Score Improvement [2]"],
            4:  ["+1 Massive Damage (+1) [3]", "+1 Special Movement [1]"],
            5:  ["+2 Points [2]", "+1 AC Bonus [1]", "+1 Extra Actions [4]"],
            6:  ["+2 Points [2]", "+1 Transfer [3]", "Ability Score Improvement [2]"],
            7:  ["+1 Massive Damage (+1) [3]", "+1 Special Movement [1]"],
            8:  ["+3 Points [3]", "+1 AC Bonus [1]", "+1 Skill Proficiency [1]", "+1 Tool Proficiency [1]"],
            9:  ["+1 Point [1]", "+1 Extra Actions [4]", "Ability Score Improvement [2]"],
            10: ["+1 Massive Damage (+1) [3]", "+1 Special Movement [1]", "+1 Transfer [3]"],
            11: ["+4 Points [4]", "+2 AC Bonus [2]"],
            12: ["+4 Point [4]", "Ability Score Improvement [2]"],
            13: ["+3 Points [3]", "+1 Massive Damage (+1) [3]", "+1 Special Movement [1]"],
            14: ["+1 Point [1]", "+1 AC Bonus [1]", "+1 Extra Actions [4]"],
            15: ["+1 Point [1]", "+1 Transfer [3]", "Ability Score Improvement [2]"],
            16: ["+2 Points [2]", "+1 Massive Damage (+1) [3]", "+1 Special Movement [1]"],
            17: ["+4 Points [4]", "+1 AC Bonus [1]", "+1 Skill Proficiency [1]"],
            18: ["+4 Point [4]", "Ability Score Improvement [2]"],
            19: ["+1 Extra Actions [4]", "+1 Massive Damage (+1) [3]"],
            20: ["+2 AC Bonus [2]", "+1 Tool Proficiency [1]", "+1 Transfer [3]"],
        },
    },
]


# ── core rules notes (effect-based system) ──────────────────────────

CORE_RULES_NOTES: List[str] = [
    "Anime 5E is an effects-based system: rules describe an Attribute's"
    " EFFECT; player + GM define the in-fiction application.",
    "Total of 200 character Points distributed over Levels 1-20.",
    "Class selection does not require Discretionary Points.",
    "Proficiency Bonus: +2 at L1, +1 every 4 levels (cap +6 at L17).",
    "Ability Score Improvement: +2 to one Ability OR +1 to two; max 20"
    " unless GM permits higher.",
    "Multi-classing allowed; duplicate proficiencies grant Bonus Points.",
    "Effects-based casting replaces traditional spell-slot mechanics —"
    " spells cost fewer points but with stricter selection limits.",
]


# ── helper API ──────────────────────────────────────────────────────

def class_skeleton(class_id: str) -> Dict[str, Any] | None:
    for c in CORE_CLASSES:
        if c["id"] == class_id:
            return c
    return None


def grants_for(class_id: str, level: int) -> Dict[str, Any]:
    """Return ALL grants a character of `class_id` receives at `level`.

    Layers:
      • universal grants (PB jumps, ASI prompt detection)
      • class-specific features verbatim from Anime 5E core
      • L1 onboarding bundle (saves + profs + starting skills)
    """
    cls = class_skeleton(class_id)
    out: Dict[str, Any] = {
        "level": level,
        "proficiency_bonus": PROFICIENCY_BONUS.get(level, 2),
    }
    if not cls:
        return out
    out["class_id"] = class_id
    out["class_name"] = cls["name"]
    out["page"] = cls.get("page")
    feats = (cls.get("features") or {}).get(level, [])
    out["features"] = feats
    # ASI prompt: any feature mentioning 'Ability Score Improvement'.
    out["asi_or_feat"] = any("Ability Score Improvement" in f for f in feats)
    # CP / Point grant total parsed from `[N]` brackets.
    import re
    pts = 0
    for f in feats:
        for m in re.findall(r"\[(\d+)\]", f):
            pts += int(m)
    out["points_granted"] = pts

    if level == 1:
        out["save_proficiencies"]   = cls.get("save_proficiencies") or []
        out["skill_picks"]          = cls.get("skill_picks") or 0
        out["weapon_proficiencies"] = cls.get("weapon_proficiencies") or []
        out["armour_proficiencies"] = cls.get("armour_proficiencies") or []
        out["tool_proficiencies"]   = cls.get("tool_proficiencies") or []
        out["hit_die"]              = cls.get("hit_die")
        out["primary_ability"]      = cls.get("primary_ability")
    return out
