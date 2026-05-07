"""V6.25.16 — D&D 5E → Anime 5E legacy class conversion table.

Source: Anime 5E core rulebook pp.82-88 (D&D legacy class
deconstruction) cross-referenced with the canonical Anime 5E
attribute roster (system_data/anime5e_data.py POINT_BUY_ATTRIBUTES)
and the canonical core class library (anime5e_class_library.py).

Only Anime 5E attributes that ACTUALLY EXIST in the approved Anime 5E
attribute table are listed here — the deconstruction cherry-picks
canonical attributes that recreate each D&D class's flavour without
resorting to attribute names that don't exist in our seed.

The mapping is INTENTIONALLY suggestive, not prescriptive — the
build-wizard surfaces it as "Convert from D&D" recommendations the
player can accept or override.
"""
from __future__ import annotations
from typing import Any, Dict, List


DND_TO_ANIME5E_CLASS_MAP: Dict[str, Dict[str, Any]] = {
    "Barbarian": {
        "anime5e_class_id": "adventurer",
        "primary_ability": "Strength",
        "anime5e_attributes": [
            ("Massive Damage", 2),
            ("AC Bonus", 2),
            ("Combat Mastery", 2),
            ("Special Movement", 1),
            ("Resilient", 1),
        ],
        "defects_suggested": ["Berserk", "Easily Distracted", "Marked"],
        "notes":
            "Brute physical force — Massive Damage + AC Bonus + Resilient "
            "stand in for D&D's Rage / Unarmoured Defence. Berserk Defect "
            "captures the volatility of the rage state.",
    },
    "Bard": {
        "anime5e_class_id": "adventurer",
        "primary_ability": "Charisma",
        "anime5e_attributes": [
            ("Inspire", 2),
            ("Skill Proficiency", 4),
            ("Spell-Like Ability", 3),
            ("Edge", 1),
            ("Connected", 2),
        ],
        "defects_suggested": ["Easily Distracted", "Show-off", "Obligated"],
        "notes":
            "Performance-driven support — Inspire + Skill Proficiency + "
            "Spell-Like Ability rebuild the bard's buff/utility/spell "
            "triangle. Connected covers the patron / venue network.",
    },
    "Cleric": {
        "anime5e_class_id": "warder",
        "primary_ability": "Wisdom",
        "anime5e_attributes": [
            ("Spell-Like Ability", 4),
            ("Healing", 3),
            ("Saving Throw Proficiency", 1),
            ("Connected", 2),
            ("Inspire", 1),
        ],
        "defects_suggested": ["Devotion", "Obligated", "Secret"],
        "notes":
            "Healing + spell-list mix carries the Cleric's role; the "
            "Devotion defect makes the divine pact mechanically real.",
    },
    "Druid": {
        "anime5e_class_id": "warder",
        "primary_ability": "Wisdom",
        "anime5e_attributes": [
            ("Spell-Like Ability", 3),
            ("Change State", 2),
            ("Healing", 2),
            ("Companion", 1),
            ("Special Movement", 1),
        ],
        "defects_suggested": ["Devotion", "Marked", "Vulnerability"],
        "notes":
            "Change State substitutes for Wild Shape; Companion captures "
            "the animal-bond. Devotion = the Druidic Oath.",
    },
    "Fighter": {
        "anime5e_class_id": "samurai",
        "primary_ability": "Strength",
        "anime5e_attributes": [
            ("Combat Mastery", 4),
            ("Combat Technique", 3),
            ("Extra Actions", 1),
            ("AC Bonus", 2),
            ("Armour Proficiency", 2),
        ],
        "defects_suggested": ["Honour", "Wanted", "Marked"],
        "notes":
            "The pure martial chassis — Extra Actions absorbs Action Surge, "
            "Combat Technique covers the Manoeuvre / Champion paths.",
    },
    "Monk": {
        "anime5e_class_id": "ninja",
        "primary_ability": "Dexterity",
        "anime5e_attributes": [
            ("AC Bonus", 3),
            ("Combat Mastery", 2),
            ("Special Movement", 2),
            ("Energised", 2),
            ("Combat Technique", 2),
        ],
        "defects_suggested": ["Vow", "Pacifism", "Significant Other"],
        "notes":
            "Energised + Combat Technique recreate the Ki / discipline "
            "loop; AC Bonus + Special Movement absorb Unarmoured Defence "
            "and the supernatural-speed milestones.",
    },
    "Paladin": {
        "anime5e_class_id": "warder",
        "primary_ability": "Strength",
        "anime5e_attributes": [
            ("Healing", 2),
            ("Combat Mastery", 2),
            ("Saving Throw Proficiency", 2),
            ("Spell-Like Ability", 2),
            ("Connected", 1),
            ("Armour Proficiency", 2),
        ],
        "defects_suggested": ["Devotion", "Honour", "Obligated"],
        "notes":
            "Heal + Smite + Aura — Healing + Combat Mastery + Spell-Like "
            "give you the trio. Devotion is the Oath; pick Honour for "
            "Conquest / Vengeance flavours.",
    },
    "Ranger": {
        "anime5e_class_id": "hunter",
        "primary_ability": "Dexterity",
        "anime5e_attributes": [
            ("Combat Mastery", 2),
            ("Heightened Senses", 2),
            ("Special Movement", 1),
            ("Companion", 1),
            ("Spell-Like Ability", 1),
            ("Skill Proficiency", 2),
        ],
        "defects_suggested": ["Easily Distracted", "Marked", "Vow"],
        "notes":
            "Heightened Senses + Skill Proficiency rebuild Favoured "
            "Enemy / Natural Explorer; Companion handles the beast bond.",
    },
    "Rogue": {
        "anime5e_class_id": "shadow-warrior",
        "primary_ability": "Dexterity",
        "anime5e_attributes": [
            ("Massive Damage – Lesser", 2),
            ("Combat Technique", 2),
            ("Skill Proficiency", 4),
            ("Special Movement", 1),
            ("Edge", 1),
        ],
        "defects_suggested": ["Wanted", "Skeleton in the Closet", "Greed"],
        "notes":
            "Massive Damage – Lesser + Combat Technique are Sneak Attack "
            "+ Cunning Action; Skill Proficiency floods Expertise.",
    },
    "Sorcerer": {
        "anime5e_class_id": "dynamic-spellbinder",
        "primary_ability": "Charisma",
        "anime5e_attributes": [
            ("Dynamic Powers – Lesser", 2),
            ("Spell-Like Ability", 4),
            ("Spell Amplification", 2),
            ("Energised", 2),
        ],
        "defects_suggested": ["Marked", "Unpredictable", "Significant Other"],
        "notes":
            "Innate magic — Dynamic Powers – Lesser is the Sorcerous "
            "Origin; Spell Amplification is Metamagic.",
    },
    "Warlock": {
        "anime5e_class_id": "dynamic-spellbinder",
        "primary_ability": "Charisma",
        "anime5e_attributes": [
            ("Spell-Like Ability", 3),
            ("Dynamic Powers – Lesser", 1),
            ("Energised", 2),
            ("Connected", 2),
        ],
        "defects_suggested": ["Obligated", "Secret", "Marked"],
        "notes":
            "Pact-driven caster — Connected (the patron) + Obligated "
            "make the bargain mechanical. Dynamic Powers – Lesser is "
            "the Pact's narrow but potent gift.",
    },
    "Wizard": {
        "anime5e_class_id": "dynamic-spellbinder",
        "primary_ability": "Intelligence",
        "anime5e_attributes": [
            ("Spell-Like Ability", 5),
            ("Spell Amplification", 2),
            ("Energised", 2),
            ("Skill Proficiency", 1),
        ],
        "defects_suggested": ["Skeleton in the Closet", "Easily Distracted",
                              "Significant Other"],
        "notes":
            "Studied caster — Spell-Like Ability dominates; Spell "
            "Amplification is the metamagic bench. Companion (familiar) "
            "is optional.",
    },
}


def list_dnd_classes() -> List[str]:
    return sorted(DND_TO_ANIME5E_CLASS_MAP.keys())


def convert(dnd_class_name: str) -> Dict[str, Any] | None:
    """Return the V6.25.16 conversion record for a D&D class name.

    Lookup is case-insensitive."""
    if not dnd_class_name:
        return None
    key = dnd_class_name.strip().title()
    rec = DND_TO_ANIME5E_CLASS_MAP.get(key)
    if not rec:
        return None
    return {"dnd_class": key, **rec}
