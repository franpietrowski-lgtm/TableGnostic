"""V6.21 — Anime 5E + PHB race DP cost table (RAW-correct).

Source: Anime 5E core p.28-30 Race list + Table 04 (p.31-32) for
PHB cross-cost breakdown. Each entry lists the canonical DP cost and a
short in-house summary of the race's thematic / mechanical identity.

Classes are FREE (no DP cost) — balancing happens through level
progression only. Race is the first big DP sink at creation.

Core references:
  - p.7  tier table (combat scaling, NOT the DP budget)
  - p.20 Discretionary Points: 80 base + 1/level above 1st
  - p.24 Ability Scores cost DP equal to the score value
  - p.28-45 Race profiles
"""
from __future__ import annotations
from typing import Any, Dict, List

# V6.21 — canonical race table. dp_cost = the Point total the Race's
# features add up to per the core rulebook. The UI shows this next to
# the race picker and auto-deducts from the DP pool on selection.

ANIME_5E_RACES: List[Dict[str, Any]] = [
    {"key": "archfiend",  "name": "Archfiend",  "dp_cost": 15,
     "size": "Huge",
     "blurb": "Towering demonic brawler — 15-ton bruiser with Conversion, Tunnelling, Mind Control (Lesser), Massive Damage, and fire/infernal heritage. Poor social / exploration, unmatched in melee."},
    {"key": "asrai",      "name": "Asrai",      "dp_cost": 11,
     "size": "Medium",
     "blurb": "Water-fey dancer with liquid-form evasion, aquatic grace, and aether-touched grace."},
    {"key": "blinkbeast", "name": "Blinkbeast", "dp_cost": 10,
     "size": "Medium",
     "blurb": "Short-hop teleporter with predatory instincts — blink, pounce, repeat."},
    {"key": "demonaga",   "name": "Demonaga",   "dp_cost": 14,
     "size": "Medium",
     "blurb": "Serpentine demon-kin — poison-touched, naga-tailed, infernal bloodline."},
    {"key": "fairy",      "name": "Fairy",      "dp_cost": 4,
     "size": "Tiny",
     "blurb": "Tiny winged fey — natural flight at a cost of hit points and carrying capacity."},
    {"key": "grey",       "name": "Grey",       "dp_cost": 12,
     "size": "Medium",
     "blurb": "Psionic grey-alien — telepathy, mind-shield, detached analytical stare."},
    {"key": "half-dragon","name": "Half-Dragon","dp_cost": 13,
     "size": "Medium",
     "blurb": "Scaled heritage — breath weapon, elemental resistance, dragon-blooded poise."},
    {"key": "half-troll", "name": "Half-Troll", "dp_cost": 9,
     "size": "Medium",
     "blurb": "Regenerating bruiser — heals wounds over rounds, vulnerability to fire/acid."},
    {"key": "haud",       "name": "Haud",       "dp_cost": 12,
     "size": "Medium",
     "blurb": "Four-armed martial adept — extra actions, ambidextrous mastery."},
    {"key": "kodama",     "name": "Kodama",     "dp_cost": 10,
     "size": "Small",
     "blurb": "Tree-spirit guardian — plant-kinship, forest-walk, woodland empath."},
    {"key": "nekojin",    "name": "Nekojin",    "dp_cost": 8,
     "size": "Medium",
     "blurb": "Catfolk — feline agility, landing grace, cultural curiosity."},
    {"key": "parasite",   "name": "Parasite",   "dp_cost": 16,
     "size": "Small",
     "blurb": "Host-riding symbiote — possesses vessels, transfers between hosts. Steep cost for dramatic flexibility."},
    {"key": "satyr",      "name": "Satyr",      "dp_cost": 7,
     "size": "Medium",
     "blurb": "Goat-legged reveller — charm magic, pipe-melodies, forest charm."},
    {"key": "slime",      "name": "Slime",      "dp_cost": 11,
     "size": "Medium",
     "blurb": "Gelatinous shapechanger — squeeze through cracks, absorb small items."},
    # ── PHB crossover races (per Table 04 costs, Anime 5E p.31-32) ──
    {"key": "dragonborn",        "name": "Dragonborn",        "dp_cost":  9, "size": "Medium",
     "blurb": "Draconic humanoid — breath weapon, elemental resistance, Common + Draconic."},
    {"key": "dwarf-hill",        "name": "Dwarf (Hill)",      "dp_cost": 12, "size": "Medium",
     "blurb": "Stonecunning hillfolk — +2 CON / +1 WIS, +1 HP/level, 25ft heavy-armor."},
    {"key": "dwarf-mountain",    "name": "Dwarf (Mountain)",  "dp_cost": 14, "size": "Medium",
     "blurb": "Armored peakfolk — +2 CON / +2 STR, light + medium armor proficient."},
    {"key": "elf-dark",          "name": "Elf (Dark / Drow)", "dp_cost": 13, "size": "Medium",
     "blurb": "Drow — 120' darkvision, Drow magic, sunlight disadvantage, +2 DEX / +1 CHA."},
    {"key": "elf-high",          "name": "Elf (High)",        "dp_cost": 12, "size": "Medium",
     "blurb": "High Elf — +2 DEX / +1 INT, one cantrip, extra martial weapon training."},
    {"key": "elf-wood",          "name": "Elf (Wood)",        "dp_cost": 11, "size": "Medium",
     "blurb": "Wood Elf — +2 DEX / +1 WIS, 35ft speed, Mask of the Wild."},
    {"key": "gnome-forest",      "name": "Gnome (Forest)",    "dp_cost":  4, "size": "Small",
     "blurb": "Forest gnome — +2 INT / +1 DEX, minor illusion, small-beast speech."},
    {"key": "gnome-rock",        "name": "Gnome (Rock)",      "dp_cost":  4, "size": "Small",
     "blurb": "Rock gnome — +2 INT / +1 CON, Artificer's Lore, tinker's tools."},
    {"key": "half-elf",          "name": "Half-Elf",          "dp_cost": 11, "size": "Medium",
     "blurb": "Half-Elf — +2 CHA, +1 to two other abilities, skill versatility, fey resilience."},
    {"key": "half-orc",          "name": "Half-Orc",          "dp_cost":  8, "size": "Medium",
     "blurb": "Half-Orc — +2 STR / +1 CON, Relentless Endurance, Savage Attacks, Intimidation."},
    {"key": "halfling-lightfoot","name": "Halfling (Lightfoot)","dp_cost": 3, "size": "Small",
     "blurb": "Lightfoot halfling — +2 DEX / +1 CHA, stealthy, Lucky, 25ft speed."},
    {"key": "halfling-stout",    "name": "Halfling (Stout)",  "dp_cost":  5, "size": "Small",
     "blurb": "Stout halfling — +2 DEX / +1 CON, poison resistance + save advantage, Lucky."},
    {"key": "human",             "name": "Human",             "dp_cost":  7, "size": "Medium",
     "blurb": "Standard human — +1 to every ability, one extra language, 30ft speed. The versatile baseline."},
    {"key": "tiefling",          "name": "Tiefling",          "dp_cost": 12, "size": "Medium",
     "blurb": "Tiefling — +2 CHA / +1 INT, Infernal Legacy (cantrip + spells), fire resistance."},
]

# Back-compat alias so existing callers (anime5e/races endpoint,
# budget-breakdown helper, tests) keep working.
RACE_DP_COSTS = ANIME_5E_RACES


# ─── Raceless option (user spec / core p.28 sidebar) ────────────────────
RACELESS = {
    "key": "raceless", "name": "Raceless", "dp_cost": 0, "size": "Medium",
    "blurb": "Skip the race template. Save the DP for Attributes, or craft a bespoke identity with your DM. Companions and monsters are Raceless by default.",
}


def get_race(key: str) -> Dict[str, Any] | None:
    """Lookup a race by canonical key or display name (case-insensitive)."""
    if not key:
        return None
    k = key.strip().lower()
    if k in ("raceless", "none", ""):
        return RACELESS
    for r in ANIME_5E_RACES:
        if r["key"].lower() == k or r["name"].lower() == k:
            return r
    return None


# ─── Anime 5E combat tier table (core p.7) — NOT the DP budget ─────────
# These tiers cap ability scores, proficiency bonus, AC, and damage by
# character level. The *DP budget* is a different mechanic — see below.
ANIME5E_TIER_TABLE = [
    (1,  "Novice",    {"max_ability_high": 18, "max_ability_mid": 17,
                       "max_attr_ranks": 4,  "max_prof": 3, "max_ac": 20, "max_normal_dmg": 25}),
    (4,  "Capable",   {"max_ability_high": 19, "max_ability_mid": 18,
                       "max_attr_ranks": 5,  "max_prof": 4, "max_ac": 22, "max_normal_dmg": 40}),
    (10, "Seasoned",  {"max_ability_high": 20, "max_ability_mid": 19,
                       "max_attr_ranks": 6,  "max_prof": 5, "max_ac": 24, "max_normal_dmg": 60}),
    (16, "Veteran",   {"max_ability_high": 22, "max_ability_mid": 20,
                       "max_attr_ranks": 8,  "max_prof": 7, "max_ac": 26, "max_normal_dmg": 100}),
    (20, "Mythical",  {"max_ability_high": 24, "max_ability_mid": 22,
                       "max_attr_ranks": 10, "max_prof": 10, "max_ac": 30, "max_normal_dmg": 200}),
    (99, "Epic",      {"max_ability_high": 99, "max_ability_mid": 99,
                       "max_attr_ranks": 99, "max_prof": 99, "max_ac": 99, "max_normal_dmg": 9999}),
]


def anime5e_tier_for_level(level: int) -> Dict[str, Any]:
    """Return the combat tier metadata for a given level (NOT budget)."""
    lvl = max(1, int(level or 1))
    for max_lvl, name, caps in ANIME5E_TIER_TABLE:
        if lvl <= max_lvl:
            return {"max_level": max_lvl, "name": name, "level": lvl,
                     "dp": dp_budget_for_level(lvl),  # back-compat: audit pulls `dp` for display
                     "blurb": f"Tier '{name}' caps: ability {caps['max_ability_high']}/{caps['max_ability_mid']}, prof +{caps['max_prof']}, AC {caps['max_ac']}.",
                     "caps": caps}
    last = ANIME5E_TIER_TABLE[-1]
    return {"max_level": last[0], "name": last[1], "level": lvl,
             "dp": dp_budget_for_level(lvl),
             "blurb": "Epic — no caps.", "caps": last[2]}


# ─── Discretionary Points budget (core p.20 — RAW-correct) ─────────────
def dp_budget_for_level(level: int) -> int:
    """RAW Anime 5E Discretionary Points budget.

    Core p.20: '80 Discretionary Points during character creation.
    If a character begins above 1st Level, the DM can also award an
    additional 1 Point for each Level above 1st as a bonus.'

    So: budget = 80 + (level - 1).
    """
    lvl = max(1, int(level or 1))
    return 80 + (lvl - 1)
