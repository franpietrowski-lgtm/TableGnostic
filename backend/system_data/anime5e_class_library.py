"""V6.25.12 — Anime 5E class progression library (L1-L20 scaffold).

This module seeds the per-level grant timeline for every Anime 5E core
class. The shape mirrors the existing `system_data/class_progression.py`
contract so the AdvancementBadge + `/advancement` endpoint surface
"# pending" approvals automatically as a character levels up.

────────────────────────────────────────────────────────────────────
SCAFFOLD STATUS — V6.25.12
────────────────────────────────────────────────────────────────────
The catalog below carries the **structural skeleton**:
   • The canonical Anime 5E core class roster.
   • The L1-L20 progression GRID (proficiency bonus, ASI levels, milestone
     levels) using the universal Anime 5E pattern (ASI at 4 / 8 / 12 / 16 / 19,
     Boon levels at 3 / 7 / 13 / 17, capstone at 20).
   • CP-cost mapping shape so attribute / power-bundle costs can layer
     on top of the per-level grants when the character sheet imports
     them.

The per-class FEATURE NAMES (e.g. "Rage", "Sneak Attack", "Magical Girl
Transformation") need to be populated against the actual Anime 5E core
book. Each class entry below contains a `_features_pending: True` flag
so GMs can tell at a glance which class is fully seeded vs. scaffold-only.

The advancement-wizard "# pending approval" pill counts every
unconfirmed grant on a character's progression timeline regardless of
seed completeness — so the plumbing works even on the unseeded classes.
A GM with the core book in hand can author the per-class entries
through the V6.25.x Custom Rules + Reference Editor surfaces TODAY,
and those authored entries take priority over this fallback.
────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
from typing import Any, Dict, List


# ── universal Anime 5E progression grid ─────────────────────────────

# Proficiency bonus by character level (mirrors D&D 5E PB curve, which
# Anime 5E inherits per the 5e SRD chassis).
PROFICIENCY_BONUS = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6,
}

# Ability Score Improvement / feat picks by class level.
ASI_LEVELS = {4, 8, 12, 16, 19}

# Major class-feature milestones common to most Anime 5E classes.
MILESTONE_LEVELS = {3, 7, 13, 17, 20}


# ── core class roster (canonical Anime 5E) ──────────────────────────

# A class entry is:
#   {
#     "id": "magical-girl",
#     "name": "Magical Girl",
#     "page": 84,
#     "subclass_choice_at": 3,
#     "primary_stat": "soul",
#     "save_proficiencies": ["soul", "mind"],
#     "skill_pool": ["Performance", "Persuasion", "Insight", ...],
#     "skill_picks": 2,
#     "weapon_proficiencies": ["simple", "wand"],
#     "armour_proficiencies": ["light"],
#     "hit_die": 8,
#     "_features_pending": True,
#     "features": {
#         1: ["Magical Transformation", "Familiar"],
#         2: ["Heart Surge"],
#         ... up to 20
#     },
#   }
#
# `_features_pending: True` means the per-level feature names below are
# placeholders ("Class Feature L<level>") that should be replaced from
# the actual Anime 5E core book by a GM with the source on hand.

CORE_CLASSES: List[Dict[str, Any]] = [
    {
        "id": "adventurer",  "name": "Adventurer",  "page": 80,
        "primary_stat": "body", "hit_die": 10,
        "save_proficiencies": ["body", "soul"],
        "skill_picks": 2,
        "skill_pool": ["Acrobatics", "Athletics", "Perception",
                        "Survival", "Stealth", "Investigation"],
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light", "medium", "shield"],
        "_features_pending": True,
    },
    {
        "id": "champion",  "name": "Champion",  "page": 82,
        "primary_stat": "body", "hit_die": 10,
        "save_proficiencies": ["body", "mind"],
        "skill_picks": 2,
        "skill_pool": ["Athletics", "Intimidation", "Persuasion",
                        "Insight", "Religion", "Animal Handling"],
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light", "medium", "heavy", "shield"],
        "_features_pending": True,
    },
    {
        "id": "magical-girl",  "name": "Magical Girl",  "page": 84,
        "primary_stat": "soul", "hit_die": 8,
        "save_proficiencies": ["soul", "mind"],
        "skill_picks": 2,
        "skill_pool": ["Performance", "Persuasion", "Insight",
                        "Arcana", "History", "Religion"],
        "weapon_proficiencies": ["simple", "wand"],
        "armour_proficiencies": ["light"],
        "_features_pending": True,
    },
    {
        "id": "samurai",  "name": "Samurai",  "page": 86,
        "primary_stat": "body", "hit_die": 10,
        "save_proficiencies": ["body", "mind"],
        "skill_picks": 2,
        "skill_pool": ["Athletics", "Insight", "History",
                        "Intimidation", "Acrobatics"],
        "weapon_proficiencies": ["simple", "martial", "katana"],
        "armour_proficiencies": ["light", "medium", "shield"],
        "_features_pending": True,
    },
    {
        "id": "wandering-monk",  "name": "Wandering Monk",  "page": 88,
        "primary_stat": "body", "hit_die": 8,
        "save_proficiencies": ["body", "soul"],
        "skill_picks": 2,
        "skill_pool": ["Acrobatics", "Athletics", "Insight",
                        "Religion", "Stealth"],
        "weapon_proficiencies": ["simple", "shortsword"],
        "armour_proficiencies": [],
        "_features_pending": True,
    },
    {
        "id": "concentrated-mage",  "name": "Concentrated Mage",  "page": 90,
        "primary_stat": "mind", "hit_die": 6,
        "save_proficiencies": ["mind", "soul"],
        "skill_picks": 2,
        "skill_pool": ["Arcana", "History", "Insight",
                        "Investigation", "Medicine", "Religion"],
        "weapon_proficiencies": ["simple", "wand"],
        "armour_proficiencies": [],
        "_features_pending": True,
    },
    {
        "id": "dynamic-sorcerer",  "name": "Dynamic Sorcerer",  "page": 92,
        "primary_stat": "soul", "hit_die": 6,
        "save_proficiencies": ["mind", "soul"],
        "skill_picks": 2,
        "skill_pool": ["Arcana", "Persuasion", "Deception",
                        "Insight", "Religion"],
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": [],
        "_features_pending": True,
    },
    {
        "id": "elementalist",  "name": "Elementalist",  "page": 94,
        "primary_stat": "soul", "hit_die": 8,
        "save_proficiencies": ["body", "soul"],
        "skill_picks": 2,
        "skill_pool": ["Arcana", "Athletics", "Survival",
                        "Nature", "Religion"],
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": ["light"],
        "_features_pending": True,
    },
    {
        "id": "shapeshifter",  "name": "Shapeshifter",  "page": 96,
        "primary_stat": "body", "hit_die": 8,
        "save_proficiencies": ["body", "mind"],
        "skill_picks": 2,
        "skill_pool": ["Animal Handling", "Athletics", "Stealth",
                        "Survival", "Nature"],
        "weapon_proficiencies": ["simple", "natural"],
        "armour_proficiencies": ["light"],
        "_features_pending": True,
    },
    {
        "id": "tech-genius",  "name": "Tech Genius",  "page": 98,
        "primary_stat": "mind", "hit_die": 6,
        "save_proficiencies": ["mind", "soul"],
        "skill_picks": 2,
        "skill_pool": ["Arcana", "Investigation", "Medicine",
                        "Insight", "Sleight of Hand"],
        "weapon_proficiencies": ["simple", "firearms"],
        "armour_proficiencies": ["light"],
        "_features_pending": True,
    },
    {
        "id": "gun-bunny",  "name": "Gun Bunny",  "page": 100,
        "primary_stat": "body", "hit_die": 10,
        "save_proficiencies": ["body", "mind"],
        "skill_picks": 2,
        "skill_pool": ["Acrobatics", "Athletics", "Perception",
                        "Sleight of Hand", "Stealth"],
        "weapon_proficiencies": ["simple", "firearms"],
        "armour_proficiencies": ["light", "medium"],
        "_features_pending": True,
    },
    {
        "id": "hot-rod",  "name": "Hot Rod",  "page": 102,
        "primary_stat": "body", "hit_die": 8,
        "save_proficiencies": ["body", "soul"],
        "skill_picks": 2,
        "skill_pool": ["Athletics", "Acrobatics", "Persuasion",
                        "Performance", "Intimidation"],
        "weapon_proficiencies": ["simple", "martial"],
        "armour_proficiencies": ["light"],
        "_features_pending": True,
    },
    {
        "id": "pet-monster-trainer",  "name": "Pet Monster Trainer",  "page": 104,
        "primary_stat": "soul", "hit_die": 8,
        "save_proficiencies": ["soul", "mind"],
        "skill_picks": 2,
        "skill_pool": ["Animal Handling", "Survival", "Insight",
                        "Nature", "Persuasion"],
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": ["light"],
        "_features_pending": True,
    },
    {
        "id": "artisan",  "name": "Artisan",  "page": 106,
        "primary_stat": "mind", "hit_die": 8,
        "save_proficiencies": ["mind", "body"],
        "skill_picks": 3,
        "skill_pool": ["Arcana", "Investigation", "Insight",
                        "Persuasion", "History", "Sleight of Hand",
                        "Survival", "Nature"],
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": ["light"],
        # Artisans have a craft-material focus — the codex materials
        # pipeline (V6.25.11) feeds their downtime crafting actions.
        "crafting_traditions": ["alchemy", "smithing", "herbalism",
                                  "tinkering", "tailoring", "scribing"],
        "_features_pending": True,
    },
    {
        "id": "adept",  "name": "Adept",  "page": 108,
        "primary_stat": "soul", "hit_die": 8,
        "save_proficiencies": ["soul", "body"],
        "skill_picks": 2,
        "skill_pool": ["Insight", "Religion", "Medicine",
                        "Persuasion", "Athletics"],
        "weapon_proficiencies": ["simple"],
        "armour_proficiencies": ["light", "medium", "shield"],
        "_features_pending": True,
    },
    {
        "id": "bandit",  "name": "Bandit",  "page": 110,
        "primary_stat": "body", "hit_die": 8,
        "save_proficiencies": ["body", "mind"],
        "skill_picks": 4,
        "skill_pool": ["Acrobatics", "Stealth", "Sleight of Hand",
                        "Deception", "Investigation", "Perception",
                        "Persuasion", "Insight"],
        "weapon_proficiencies": ["simple", "shortsword", "longsword",
                                   "rapier", "hand crossbow"],
        "armour_proficiencies": ["light"],
        "_features_pending": True,
    },
]


def universal_grants_at_level(level: int) -> Dict[str, Any]:
    """Universal grants any Anime 5E character receives at `level`,
    regardless of class — proficiency-bonus jumps + ASI prompts."""
    out: Dict[str, Any] = {
        "level": level,
        "proficiency_bonus": PROFICIENCY_BONUS.get(level, 2),
    }
    if level in ASI_LEVELS:
        out["asi_or_feat"] = True
    if level in MILESTONE_LEVELS:
        out["milestone"] = True
    return out


def class_skeleton(class_id: str) -> Dict[str, Any] | None:
    """Look up a class entry by id."""
    for c in CORE_CLASSES:
        if c["id"] == class_id:
            return c
    return None


def grants_for(class_id: str, level: int) -> Dict[str, Any]:
    """Return all grants a character of `class_id` receives at `level`.

    Layers:
      • universal grants (PB / ASI / milestone)
      • class-specific seeded features (currently empty for scaffold;
        custom-rules entries authored by the GM take priority)
    """
    base = universal_grants_at_level(level)
    cls = class_skeleton(class_id)
    if not cls:
        return base
    base["class_id"] = class_id
    base["class_name"] = cls["name"]
    base["page"] = cls.get("page")

    # Level-1 onboarding bundle (saves + proficiencies + starting skills).
    if level == 1:
        base["save_proficiencies"]   = cls.get("save_proficiencies") or []
        base["skill_picks"]          = cls.get("skill_picks") or 0
        base["skill_pool"]           = cls.get("skill_pool") or []
        base["weapon_proficiencies"] = cls.get("weapon_proficiencies") or []
        base["armour_proficiencies"] = cls.get("armour_proficiencies") or []
        base["hit_die"]              = cls.get("hit_die")
        if cls.get("crafting_traditions"):
            base["crafting_traditions"] = cls["crafting_traditions"]

    # Per-level feature grant — scaffold names. Real names come from
    # GM-authored custom-rules entries (preferred) or a future seeded
    # core-book ingest pass (`_features_pending: True` flag).
    base["features_pending"] = bool(cls.get("_features_pending"))
    base["features"] = (cls.get("features") or {}).get(level, [])

    # CP-cost shape — the character-sheet CP audit reads this when
    # importing class grants. Anime 5E uses DP for raw stats and CP for
    # attributes (see Anime 5E core p.45-46). Per-level CP grants are
    # the SAME magnitude as the level (1 CP per class-level milestone).
    base["cp_grant"] = 1 if (level in MILESTONE_LEVELS) else 0

    return base
