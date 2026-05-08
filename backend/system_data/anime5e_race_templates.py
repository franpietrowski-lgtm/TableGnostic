"""V6.25.22 — Anime 5E race templates (bundled attributes / defects /
ability-score increases / languages, source: dys_anime5e_rpg p.28-45).

Each entry in `ANIME_5E_RACE_TEMPLATES` is keyed by the same `key`
used in `ANIME_5E_RACES`. The `dp_cost` already in `ANIME_5E_RACES`
is the published total — it is NOT recomputed from the bundle.
"""
from __future__ import annotations
from typing import Any, Dict, List


ANIME_5E_RACE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "archfiend": {
        "speed": 120,
        "ability_score_increase": {"Charisma": -1},
        "bundled_attributes": [
            {"name": "Augmented (Strength)", "ranks": 4},
            {"name": "Conversion", "ranks": 1},
            {"name": "Edge (Strength dice rolls)", "ranks": 4},
            {"name": "Fast (×4 speed; 120 feet/round)", "ranks": 2},
            {"name": "Features (Darkvision 120’ ×2)", "ranks": 2},
            {"name": "Language (Common, Infernal)", "ranks": 1},
            {"name": "Massive Damage – Lesser", "ranks": 4},
            {"name": "Mind Control – Lesser (Demons)", "ranks": 1},
            {"name": "Protected (-4 Standard damage)", "ranks": 4},
            {"name": "Tunnelling (1 foot/round)", "ranks": 1},
            {"name": "Unique Attribute (×4 Thrown Weapon Distance)", "ranks": 2},
        ],
        "bundled_defects": [
            {"name": "AC Penalty (-4 AC)", "severity": "minor"},
            {"name": "Inept Attack (-4 attack rolls)", "severity": "minor"},
            {"name": "Unique Defect (Big, Heavy, and Obvious)", "severity": "minor"},
            {"name": "Vulnerability (Lightning)", "severity": "minor"},
        ],
        "languages": ["Common", "Infernal"],
    },
    "asrai": {
        "speed": 30,
        "ability_score_increase": {"Dexterity": 1, "Intelligence": 1, "Charisma": 2},
        "bundled_attributes": [
            {"name": "Flight (30 feet/round)", "ranks": 1},
            {"name": "Sixth Sense (Danger)", "ranks": 1},
            {"name": "Special Movement (Zen Direction)", "ranks": 1},
        ],
        "bundled_defects": [],
        "languages": ["Common", "Elvish", "Sylvan"],
    },
    "blinkbeast": {
        "speed": 30,
        "ability_score_increase": {"Dexterity": 2},
        "bundled_attributes": [
            {"name": "Alternate Identity (Human Form)", "ranks": 1},
            {"name": "Dynamic Powers – Lesser (Vegetation; Area: 30’ -2; Concentration +1; Unpredictable +1)", "ranks": 1},
            {"name": "Teleport (100’)", "ranks": 2},
        ],
        "bundled_defects": [
            {"name": "Defective Ability (Charisma)", "severity": "minor"},
            {"name": "Defective Ability (Dexterity)", "severity": "minor"},
        ],
        "languages": ["Common", "Sylvan"],
    },
    "demonaga": {
        "speed": 60,
        "ability_score_increase": {},
        "bundled_attributes": [
            {"name": "Edge (Saving Throws vs. magic)", "ranks": 2},
            {"name": "Edge (Strength dice rolls)", "ranks": 4},
            {"name": "Fast (×2 speed; 60 feet/round)", "ranks": 1},
            {"name": "Immunity (Fire)", "ranks": 3},
            {"name": "Massive Damage – Lesser (+2 Strength Impacts)", "ranks": 2},
            {"name": "Protected (-2 Standard damage)", "ranks": 2},
            {"name": "Unique Attribute (×2 Thrown Weapon Distance)", "ranks": 1},
        ],
        "bundled_defects": [
            {"name": "AC Penalty (-2 AC)", "severity": "minor"},
            {"name": "Defective Ability (Charisma)", "severity": "minor"},
            {"name": "Inept Attack (-2 attack rolls)", "severity": "minor"},
            {"name": "Unique Defect (Big, Heavy, and Obvious)", "severity": "minor"},
            {"name": "Defective Ability (Wisdom)", "severity": "minor"},
        ],
        "languages": ["Common", "Draconic", "Primordial"],
    },
    "fairy": {
        "speed": 4,
        "ability_score_increase": {"Wisdom": 1, "Charisma": 2},
        "bundled_attributes": [
            {"name": "AC Bonus (+6 AC)", "ranks": 6},
            {"name": "Combat Mastery (+6 attack rolls)", "ranks": 6},
            {"name": "Control Environment (Lights)", "ranks": 1},
            {"name": "Features (Direction Sense, Scentless)", "ranks": 2},
            {"name": "Flight (90 feet/round)", "ranks": 2},
            {"name": "Heightened Senses (Smell)", "ranks": 1},
            {"name": "Spell-Like Ability (Major Image)", "ranks": 4},
            {"name": "Unique Attribute (Small, Light, and Unobtrusive)", "ranks": 3},
        ],
        "bundled_defects": [
            {"name": "Degraded (-8 Strength)", "severity": "extreme"},
            {"name": "Limited Damage (-6 Strength Impacts)", "severity": "major"},
            {"name": "Obstacle (Strength dice rolls)", "severity": "major"},
            {"name": "Slow (÷8 speed; 4 feet/round)", "severity": "major"},
            {"name": "Susceptible (+6 Standard damage)", "severity": "major"},
            {"name": "Unique Defect (Thrown Weapon Distance ÷8)", "severity": "major"},
        ],
        "languages": ["Common", "Elvish", "Sylvan"],
    },
    "grey": {
        "speed": 30,
        "ability_score_increase": {"Intelligence": 2},
        "bundled_attributes": [
            {"name": "Features (Ambidexterity, Darkvision 60’, Ultrasonic Communication)", "ranks": 3},
            {"name": "Heightened Senses (Hearing, Taste)", "ranks": 2},
            {"name": "Mind Control (Basic, non-aggressive)", "ranks": 1},
            {"name": "Spell-Like Ability (Cure Wounds)", "ranks": 2},
        ],
        "bundled_defects": [],
        "languages": ["Common"],
    },
    "half-dragon": {
        "speed": 30,
        "ability_score_increase": {"Strength": 1, "Constitution": 1},
        "bundled_attributes": [
            {"name": "Flight (30 feet/round)", "ranks": 1},
            {"name": "Immunity – Lesser (Fire)", "ranks": 3},
            {"name": "Weapon: Fire Breath (2d6 damage; Continuing -1; Range: 30’ -2; Spreading: 3 targets -2; Save +4)", "ranks": 4},
        ],
        "bundled_defects": [],
        "languages": ["Common", "Draconic"],
    },
    "half-troll": {
        "speed": 30,
        "ability_score_increase": {"Wisdom": 1},
        "bundled_attributes": [
            {"name": "Features (Darkvision 60’)", "ranks": 1},
            {"name": "Heightened Senses (Smell)", "ranks": 1},
            {"name": "Regeneration (4 HP/round)", "ranks": 4},
        ],
        "bundled_defects": [
            {"name": "Defective Ability (Constitution)", "severity": "minor"},
        ],
        "languages": ["Common", "Draconic", "Goblin", "Orc"],
    },
    "haud": {
        "speed": 30,
        "ability_score_increase": {"Intelligence": 1},
        "bundled_attributes": [
            {"name": "Extra Actions (1 Extra Action/round)", "ranks": 1},
            {"name": "Features (Darkvision 60’)", "ranks": 1},
            {"name": "Heightened Senses (Taste, Vision)", "ranks": 2},
            {"name": "Immunity – Lesser (Poison)", "ranks": 2},
            {"name": "Special Movement (Wall-Crawling 2)", "ranks": 2},
        ],
        "bundled_defects": [
            {"name": "Bane (Cold)", "severity": "minor"},
            {"name": "Defective Ability (Charisma)", "severity": "minor"},
            {"name": "Obstacle (Saving Throws vs cold)", "severity": "minor"},
        ],
        "languages": ["Common", "Draconic", "Goblin"],
    },
    "kodama": {
        "speed": 8,
        "ability_score_increase": {"Wisdom": 1},
        "bundled_attributes": [
            {"name": "AC Bonus (+4 AC)", "ranks": 4},
            {"name": "Change State (Liquid, gaseous, and incorporeal)", "ranks": 3},
            {"name": "Cognition (Postcognition)", "ranks": 1},
            {"name": "Combat Mastery (+4 attack rolls)", "ranks": 4},
            {"name": "Spell-Like Ability (Banishment)", "ranks": 5},
            {"name": "Spell-Like Ability (Cure Wounds)", "ranks": 2},
            {"name": "Unique Attribute (Small, Light, and Unobtrusive)", "ranks": 2},
        ],
        "bundled_defects": [
            {"name": "Degraded (-4 Strength)", "severity": "major"},
            {"name": "Limited Damage (-4 Strength Impacts)", "severity": "major"},
            {"name": "Obstacle (Strength dice rolls)", "severity": "major"},
            {"name": "Slow (÷4 speed; 8 feet/round)", "severity": "major"},
            {"name": "Susceptible (+4 Standard damage)", "severity": "major"},
            {"name": "Unique Defect (Thrown Weapon Distance ÷4)", "severity": "major"},
        ],
        "languages": ["Common", "Sylvan"],
    },
    "nekojin": {
        "speed": 30,
        "ability_score_increase": {"Dexterity": 2},
        "bundled_attributes": [
            {"name": "Edge (Initiative)", "ranks": 2},
            {"name": "Features (Darkvision 60’)", "ranks": 1},
            {"name": "Heightened Senses (Hearing)", "ranks": 1},
            {"name": "Mulligan (4 re-rolls/session)", "ranks": 2},
            {"name": "Special Movement (Cat-Like)", "ranks": 1},
        ],
        "bundled_defects": [
            {"name": "Easily Distracted (Things that distract cats)", "severity": "minor"},
        ],
        "languages": ["Common"],
    },
    "parasite": {
        "speed": 30,
        "ability_score_increase": {},
        "bundled_attributes": [
            {"name": "Elasticity (Two limbs stretch ×5; +4 grappling checks)", "ranks": 2},
            {"name": "Extra Actions – Lesser (1 Extra Action/round; not attacks)", "ranks": 1},
            {"name": "Immunity (Lightning)", "ranks": 2},
            {"name": "Massive Damage – Lesser (+1d8 unarmed attacks)", "ranks": 4},
            {"name": "Weapon: Extending Blades (1d8 slashing damage)", "ranks": 2},
        ],
        "bundled_defects": [
            {"name": "Bane (Loud Sounds)", "severity": "minor"},
        ],
        "languages": ["Common"],
    },
    "satyr": {
        "speed": 60,
        "ability_score_increase": {"Constitution": 1, "Charisma": 1},
        "bundled_attributes": [
            {"name": "Extra Actions – Lesser (1 Extra Action/round; not attacks)", "ranks": 1},
            {"name": "Fast (×2 speed; 60 feet/round)", "ranks": 1},
            {"name": "Jumping (3× normal distance)", "ranks": 1},
        ],
        "bundled_defects": [
            {"name": "Easily Distracted (Things that distract children)", "severity": "minor"},
        ],
        "languages": ["Common", "Elvish", "Sylvan"],
    },
    "slime": {
        "speed": 15,
        "ability_score_increase": {"Constitution": 1, "Charisma": 2},
        "bundled_attributes": [
            {"name": "AC Bonus (+2 AC)", "ranks": 2},
            {"name": "Elasticity (Entire body stretches ×5; +10 grappling checks)", "ranks": 5},
            {"name": "Combat Mastery (+2 attack rolls)", "ranks": 2},
            {"name": "Regeneration (2 HP/round)", "ranks": 2},
            {"name": "Special Movement (Slithering)", "ranks": 1},
            {"name": "Unique Attribute (Small, Light, and Unobtrusive)", "ranks": 1},
        ],
        "bundled_defects": [
            {"name": "Limited Damage (-2 Strength Impacts)", "severity": "minor"},
            {"name": "Obstacle (Strength dice rolls)", "severity": "major"},
            {"name": "Slow (÷2 speed; 15 feet/round)", "severity": "minor"},
            {"name": "Susceptible (+2 Standard damage)", "severity": "minor"},
            {"name": "Unique Defect (Thrown Weapon Distance ÷2)", "severity": "minor"},
        ],
        "languages": ["Common", "Undercommon"],
    },
}


def race_template(key: str) -> Dict[str, Any]:
    """Return the bundled attribute / defect / language template for a
    race key, or an empty stub when unknown.
    """
    if not key:
        return {"speed": 30, "ability_score_increase": {},
                "bundled_attributes": [], "bundled_defects": [],
                "languages": []}
    return ANIME_5E_RACE_TEMPLATES.get(key.strip().lower(), {
        "speed": 30, "ability_score_increase": {},
        "bundled_attributes": [], "bundled_defects": [],
        "languages": [],
    })


def merged_race_entry(race: Dict[str, Any]) -> Dict[str, Any]:
    """Return a race entry merged with its template (for the
    /anime5e/races endpoint)."""
    if not race:
        return race
    out: Dict[str, Any] = dict(race)
    tmpl = race_template(race.get("key") or "")
    for k, v in tmpl.items():
        out.setdefault(k, v)
    return out


def all_races_with_templates(base: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [merged_race_entry(r) for r in base]
