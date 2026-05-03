"""V6.19 — Anime 5E race / heritage Discretionary Point cost table.

Anime 5E core p.28-30 race table (in-house authored summaries — no
verbatim copy of rulebook prose). Each entry is a "race template" with
its base DP cost, the traits it grants for that cost, and a short
narrative blurb.

Used by:
  - Character creation flow (auto-deduct race cost from `point_budget`)
  - Pending compliance checks (validate races match permitted list)
  - Reference page (left-rail Race quick_ref section)
"""
from __future__ import annotations
from typing import Any, Dict, List

# Each race carries: dp_cost, traits (list of human-readable feature
# strings), page_ref (orientation citation only).
RACE_DP_COSTS: List[Dict[str, Any]] = [
    {
        "key": "human", "name": "Human", "dp_cost": 1,
        "page_ref": "Anime 5E SRD p.19",
        "traits": [
            "+1 to all six ability scores",
            "1 extra skill proficiency of your choice",
            "Versatile feat option at character creation",
        ],
        "blurb": "The genre's everyman — the trainer, the ordinary teen, the salaryman thrown into the unknown.",
    },
    {
        "key": "beastfolk", "name": "Beastfolk", "dp_cost": 3,
        "page_ref": "Anime 5E SRD p.21",
        "traits": [
            "+2 to one ability of choice (Str/Dex/Wis)",
            "Lunar Sense — advantage on scent/hearing Perception",
            "Track creatures by scent at travel pace",
            "Natural weapon (claw 1d4 slashing) at level 1",
        ],
        "blurb": "Sapient cat-people, fox-folk, wolf-kin and others walking the line between bestial and civilised.",
    },
    {
        "key": "construct", "name": "Construct", "dp_cost": 4,
        "page_ref": "Anime 5E SRD p.23",
        "traits": [
            "+2 Constitution, +1 Intelligence",
            "Tireless Frame — no need to sleep / breathe / eat",
            "Long rest = 6 hours of standby (immune to sleep)",
            "Immune to poison damage and the poisoned condition",
            "Vulnerable to lightning damage",
        ],
        "blurb": "Mechanical or magitechnical autonomous beings — soulbound automata, doll-cores, genuine androids.",
    },
    {
        "key": "half-demon", "name": "Half-Demon", "dp_cost": 4,
        "page_ref": "Anime 5E SRD p.25",
        "traits": [
            "+2 Charisma, +1 Strength",
            "Hellbrand — +1d4 fire damage on melee weapon hits",
            "Once/long rest — Hellbrand becomes 1d6 + 1/4 levels",
            "Resistance to fire damage",
            "Disadvantage on social rolls vs religious authorities",
        ],
        "blurb": "Born of mortal and infernal lineage — the 'cursed bloodline' trope made playable.",
    },
    {
        "key": "faerie", "name": "Faerie", "dp_cost": 4,
        "page_ref": "Anime 5E SRD p.27",
        "traits": [
            "+2 Dexterity, +1 Charisma",
            "Disguise Self at-will (cosmetic only)",
            "Reflection in cold iron always shows true form",
            "Iron weapons deal +1 damage against you",
            "Misty Step 1/short rest at level 5+",
        ],
        "blurb": "The fey-touched — kitsune, goblins, sprites, half-elves with otherworldly poise.",
    },
    {
        "key": "spirit", "name": "Spirit", "dp_cost": 5,
        "page_ref": "Anime 5E SRD p.29",
        "traits": [
            "+2 Wisdom, +1 Dexterity",
            "Incorporeal Step — pass through 5ft of solid matter 1/short rest",
            "Resistance to necrotic damage",
            "Detect Spirits at 30 ft (cantrip equivalent)",
            "Vulnerable to radiant damage",
        ],
        "blurb": "Yokai, ghost-touched, the not-quite-departed — semi-corporeal shrine guardians and household spirits.",
    },
    {
        "key": "animal", "name": "Animal", "dp_cost": 2,
        "page_ref": "Anime 5E SRD p.31",
        "traits": [
            "+2 Dexterity (or +1 to two stats)",
            "Bestial Form — sapient beast (fox/cat/dog/hawk/otter)",
            "Carrying capacity halved",
            "Natural attack (bite 1d4 piercing OR claw 1d4 slashing)",
            "Speak one bonded language only your compatriots understand",
        ],
        "blurb": "The sapient beast companion turned PC — talking foxes, scholar-cats, wandering wolves.",
    },
    {
        "key": "apprentice", "name": "Apprentice", "dp_cost": 1,
        "page_ref": "Anime 5E SRD p.33",
        "traits": [
            "+1 Intelligence or Wisdom",
            "Mentor's Boon — once/long rest, expertise on one INT or WIS check",
            "Begin play with 1 free downtime contact (mentor NPC)",
        ],
        "blurb": "Still in training — the disciple, the hopeful magic-girl trainee, the salt-rookie of the squad.",
    },
]


def get_race(key: str) -> Dict[str, Any] | None:
    """Lookup a race by canonical key (case-insensitive)."""
    if not key:
        return None
    k = key.strip().lower()
    for r in RACE_DP_COSTS:
        if r["key"] == k or r["name"].lower() == k:
            return r
    return None


# ─── Anime 5E Tier table (core p.7-8) — RAW-correct DP budget ───────────
# These are the canonical Discretionary Point budgets per Tier. The
# `tier` formula honours this strictly; "flat" / "curve" are tunable
# house-rule variants for GMs who want different scaling.

ANIME5E_TIER_TABLE = [
    # (max_level_inclusive, tier_name, dp_budget, tier_blurb)
    (2,  "Tier 1 · Beginner",  10,
     "Slice-of-life campaigns, school arcs, day-job adventures."),
    (5,  "Tier 2 · Adventurer", 20,
     "First-arc heroes, fledgling magical girls, rookie pilots."),
    (10, "Tier 3 · Hero",       40,
     "Established protagonists, recurring villains' equals."),
    (15, "Tier 4 · Champion",   60,
     "Saviour-level — the final arc of a 26-episode anime."),
    (20, "Tier 5 · Legend",     80,
     "Cosmic stakes — the multi-season finale, the demigod-tier."),
]


def anime5e_tier_for_level(level: int) -> Dict[str, Any]:
    """Return the canonical Tier metadata for a given level."""
    lvl = max(1, int(level or 1))
    for max_lvl, name, dp, blurb in ANIME5E_TIER_TABLE:
        if lvl <= max_lvl:
            return {"max_level": max_lvl, "name": name,
                     "dp": dp, "blurb": blurb, "level": lvl}
    final = ANIME5E_TIER_TABLE[-1]
    return {"max_level": final[0], "name": final[1],
             "dp": final[2], "blurb": final[3], "level": lvl}
