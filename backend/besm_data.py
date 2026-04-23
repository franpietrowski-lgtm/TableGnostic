"""
BESM 4E reference data.

LEGAL COMPLIANCE: This module contains ONLY mechanical reference data:
names, numeric costs, page references to the official BESM 4E rulebook.
It does NOT contain rulebook text, descriptions, or explanatory content.
All rule text must be consulted in the official BESM 4E rulebook from
Dyskami Publishing Company. Source references follow the format
"BESM 4E p.<page>" so players can look up the official rules.

Data extracted from:
  BESM Fourth Edition (Dyskami Publishing, 2020)
  Table-07: Character Attributes (p.77)
  Table-11: Allowable Enhancements (p.146)
  Table-12: Limiters (p.148)
  Table-14: Defects (p.155)
"""

BOOK = "BESM 4E"

# Core Stats (Chapter 4, p.70-73)
CORE_STATS = [
    {"key": "body", "name": "Body", "page": 71},
    {"key": "mind", "name": "Mind", "page": 71},
    {"key": "soul", "name": "Soul", "page": 71},
]

# Derived Values (Chapter 8, p.168-171)
DERIVED_VALUES = [
    {"key": "combat_value", "name": "Combat Value",
     "formula": "floor((Body + Mind + Soul) / 3)", "page": 169},
    {"key": "attack_value", "name": "Attack Value",
     "formula": "Combat Value + Attack Mastery + Combat Technique(Attack)",
     "page": 169},
    {"key": "defence_value", "name": "Defence Value",
     "formula": "Combat Value - 2 + Defence Mastery + Combat Technique(Defence)",
     "page": 169},
    {"key": "health_points", "name": "Health Points",
     "formula": "(Body + Soul) * 5 + Tough*5 + Massive Damage modifiers",
     "page": 170},
    {"key": "energy_points", "name": "Energy Points",
     "formula": "(Mind + Soul) * 5 + Energised*5",
     "page": 170},
    {"key": "damage_multiplier", "name": "Damage Multiplier",
     "formula": "5 (baseline, modified by Massive Damage / Weapon)",
     "page": 171},
    {"key": "initiative", "name": "Initiative",
     "formula": "Body + Mind + 1d6", "page": 182},
]

# Table-07: Character Attributes (p.77). cost = Character Points per Level.
# Asterisk (*) = human-appropriate Attribute per the book.
# "variable" means cost depends on chosen configuration.
ATTRIBUTES = [
    {"name": "Absorption", "cost_per_level": 5, "page": 78, "human_ok": False},
    {"name": "Alternate Form", "cost_per_level": 4, "page": 78, "human_ok": False},
    {"name": "Alternate Identity", "cost_per_level": 1, "page": 80, "human_ok": False},
    {"name": "Armour", "cost_per_level": 2, "page": 80, "human_ok": False},
    {"name": "Attack Mastery", "cost_per_level": 1, "page": 80, "human_ok": True},
    {"name": "Augmented", "cost_per_level": 2, "page": 80, "human_ok": False},
    {"name": "Capacity", "cost_per_level": 1, "page": 81, "human_ok": False},
    {"name": "Change State", "cost_per_level": 3, "page": 82, "human_ok": False},
    {"name": "Cognition", "cost_per_level": 2, "page": 82, "human_ok": False},
    {"name": "Combat Technique", "cost_per_level": 1, "page": 83, "human_ok": True},
    {"name": "Companion", "cost_per_level": 4, "page": 84, "human_ok": True},
    {"name": "Connected", "cost_per_level": 1, "page": 84, "human_ok": True},
    {"name": "Control Environment", "cost_per_level": 1, "page": 86, "human_ok": False},
    {"name": "Conversion", "cost_per_level": 3, "page": 86, "human_ok": False},
    {"name": "Data Access", "cost_per_level": 2, "page": 88, "human_ok": False},
    {"name": "Defence Mastery", "cost_per_level": 1, "page": 88, "human_ok": True},
    {"name": "Dimension Walk", "cost_per_level": 5, "page": 89, "human_ok": False},
    {"name": "Dynamic Powers", "cost_per_level": 10, "page": 89, "human_ok": False},
    {"name": "Elasticity", "cost_per_level": 1, "page": 90, "human_ok": False},
    {"name": "Enemy Attack", "cost_per_level": 1, "page": 90, "human_ok": True},
    {"name": "Enemy Defence", "cost_per_level": 1, "page": 90, "human_ok": True},
    {"name": "Energised", "cost_per_level": 1, "page": 91, "human_ok": True},
    {"name": "Exorcism", "cost_per_level": 1, "page": 91, "human_ok": False},
    {"name": "Extra Actions", "cost_per_level": 4, "page": 92, "human_ok": True},
    {"name": "Extra Arms", "cost_per_level": 1, "page": 92, "human_ok": False},
    {"name": "Features", "cost_per_level": 1, "page": 92, "human_ok": True},
    {"name": "Flight", "cost_per_level": 3, "page": 94, "human_ok": False},
    {"name": "Force Field", "cost_per_level": 4, "page": 94, "human_ok": False},
    {"name": "Gear", "cost_per_level": 1, "page": 95, "human_ok": True},
    {"name": "Ground Speed", "cost_per_level": 1, "page": 96, "human_ok": False},
    {"name": "Healing", "cost_per_level": 1, "page": 96, "human_ok": False},
    {"name": "Heightened Awareness", "cost_per_level": 1, "page": 97, "human_ok": True},
    {"name": "Heightened Senses", "cost_per_level": 1, "page": 97, "human_ok": False},
    {"name": "Illusion", "cost_per_level": 1, "page": 97, "human_ok": False},
    {"name": "Immunity", "cost_per_level": 3, "page": 98, "human_ok": False},
    {"name": "Immutable", "cost_per_level": 1, "page": 99, "human_ok": False},
    {"name": "Inspire", "cost_per_level": 1, "page": 99, "human_ok": True},
    {"name": "Item", "cost_per_level": 0.5, "page": 101, "human_ok": True, "note": "Half Points"},
    {"name": "Jumping", "cost_per_level": 1, "page": 101, "human_ok": False},
    {"name": "Massive Damage", "cost_per_level": 3, "page": 102, "human_ok": True},
    {"name": "Melee Attack", "cost_per_level": 1, "page": 102, "human_ok": True},
    {"name": "Melee Defence", "cost_per_level": 1, "page": 103, "human_ok": True},
    {"name": "Merge", "cost_per_level": 4, "page": 103, "human_ok": False},
    {"name": "Metamorphosis", "cost_per_level": 2, "page": 106, "human_ok": False},
    {"name": "Mimic", "cost_per_level": 2, "page": 107, "human_ok": False},
    {"name": "Mind Control", "cost_per_level": 5, "page": 108, "human_ok": False},
    {"name": "Mind Shield", "cost_per_level": 1, "page": 109, "human_ok": True},
    {"name": "Minions", "cost_per_level": 2, "page": 109, "human_ok": True},
    {"name": "Mulligan", "cost_per_level": 1, "page": 109, "human_ok": True},
    {"name": "Nullify", "cost_per_level": 5, "page": 110, "human_ok": False},
    {"name": "Plant Control", "cost_per_level": 1, "page": 110, "human_ok": False},
    {"name": "Pocket Dimension", "cost_per_level": 1, "page": 112, "human_ok": False},
    {"name": "Portal", "cost_per_level": 2, "page": 112, "human_ok": False},
    {"name": "Power Flux", "cost_per_level": 10, "page": 113, "human_ok": False},
    {"name": "Power Variation", "cost_per_level": 4, "page": 114, "human_ok": False},
    {"name": "Projection", "cost_per_level": 3, "page": 114, "human_ok": False},
    {"name": "Ranged Attack", "cost_per_level": 1, "page": 116, "human_ok": True},
    {"name": "Ranged Defence", "cost_per_level": 1, "page": 116, "human_ok": True},
    {"name": "Regeneration", "cost_per_level": 5, "page": 117, "human_ok": False},
    {"name": "Reincarnation", "cost_per_level": 2, "page": 117, "human_ok": False},
    {"name": "Resilient", "cost_per_level": 2, "page": 118, "human_ok": False},
    {"name": "Sensory Block", "cost_per_level": 1, "page": 119, "human_ok": False},
    {"name": "Sixth Sense", "cost_per_level": 1, "page": 119, "human_ok": False},
    {"name": "Size Change", "cost_per_level": 10, "page": 120, "human_ok": False},
    {"name": "Skill Group", "cost_per_level": 2, "page": 120, "human_ok": True, "note": "1/2/3 per Group tier"},
    {"name": "Spaceflight", "cost_per_level": 1, "page": 121, "human_ok": False},
    {"name": "Special Movement", "cost_per_level": 1, "page": 122, "human_ok": False},
    {"name": "Summon Creatures", "cost_per_level": 2, "page": 122, "human_ok": False},
    {"name": "Supersense", "cost_per_level": 1, "page": 123, "human_ok": False},
    {"name": "Superspeed", "cost_per_level": 3, "page": 123, "human_ok": False},
    {"name": "Superstrength", "cost_per_level": 4, "page": 124, "human_ok": False},
    {"name": "Swarm", "cost_per_level": 2, "page": 124, "human_ok": False},
    {"name": "Telekinesis", "cost_per_level": 4, "page": 125, "human_ok": False},
    {"name": "Telepathy", "cost_per_level": 3, "page": 126, "human_ok": False},
    {"name": "Teleport", "cost_per_level": 3, "page": 127, "human_ok": False},
    {"name": "Tough", "cost_per_level": 1, "page": 128, "human_ok": True},
    {"name": "Transfer", "cost_per_level": 3, "page": 128, "human_ok": False},
    {"name": "Transmute", "cost_per_level": 3, "page": 128, "human_ok": False},
    {"name": "Tunnelling", "cost_per_level": 1, "page": 129, "human_ok": False},
    {"name": "Unaffected", "cost_per_level": 2, "page": 129, "human_ok": False},
    {"name": "Undetectable", "cost_per_level": 2, "page": 131, "human_ok": False},
    {"name": "Unique Attribute", "cost_per_level": 1, "page": 131, "human_ok": True, "note": "1-10 variable"},
    {"name": "Unknown Power", "cost_per_level": 0, "page": 132, "human_ok": True, "note": "Variable (GM set)"},
    {"name": "Water Speed", "cost_per_level": 1, "page": 132, "human_ok": False},
    {"name": "Wealth", "cost_per_level": 3, "page": 132, "human_ok": True},
    {"name": "Weapon", "cost_per_level": 2, "page": 132, "human_ok": True},
]

# Table-14: Defects (p.155). Lesser=-1/rank, Greater=-2/rank, Serious=-3/rank.
DEFECTS = [
    {"name": "Achilles Heel", "category": "Greater", "points_per_rank": -2, "page": 156},
    {"name": "Awkward Size", "category": "Greater", "points_per_rank": -2, "page": 156, "note": "Special (Items only)"},
    {"name": "Bane", "category": "Greater", "points_per_rank": -2, "page": 156},
    {"name": "Blind Fury", "category": "Greater", "points_per_rank": -2, "page": 157},
    {"name": "Conditional Ownership", "category": "Lesser", "points_per_rank": -1, "page": 157},
    {"name": "Confined", "category": "Serious", "points_per_rank": -3, "page": 158},
    {"name": "Cursed", "category": "Greater", "points_per_rank": -2, "page": 158},
    {"name": "Easily Distracted", "category": "Lesser", "points_per_rank": -1, "page": 158},
    {"name": "Fragile", "category": "Lesser", "points_per_rank": -1, "page": 158},
    {"name": "Hounded", "category": "Greater", "points_per_rank": -2, "page": 158},
    {"name": "Impaired Manipulation", "category": "Serious", "points_per_rank": -3, "page": 158},
    {"name": "Impaired Speech", "category": "Serious", "points_per_rank": -3, "page": 160},
    {"name": "Inept Attack", "category": "Lesser", "points_per_rank": -1, "page": 160},
    {"name": "Inept Defence", "category": "Lesser", "points_per_rank": -1, "page": 160},
    {"name": "Involuntary Change", "category": "Lesser", "points_per_rank": -1, "page": 160},
    {"name": "Ism", "category": "Greater", "points_per_rank": -2, "page": 160},
    {"name": "Magnet", "category": "Lesser", "points_per_rank": -1, "page": 161},
    {"name": "Marked", "category": "Lesser", "points_per_rank": -1, "page": 161},
    {"name": "Nemesis", "category": "Lesser", "points_per_rank": -1, "page": 161},
    {"name": "Nightmares", "category": "Lesser", "points_per_rank": -1, "page": 161},
    {"name": "Obligated", "category": "Greater", "points_per_rank": -2, "page": 163},
    {"name": "Phobia", "category": "Lesser", "points_per_rank": -1, "page": 163},
    {"name": "Physical Impairment", "category": "Serious", "points_per_rank": -3, "page": 163},
    {"name": "Red Tape", "category": "Lesser", "points_per_rank": -1, "page": 163},
    {"name": "Reduced Damage", "category": "Serious", "points_per_rank": -3, "page": 163},
    {"name": "Sensory Impairment", "category": "Serious", "points_per_rank": -3, "page": 164},
    {"name": "Shortcoming", "category": "Lesser", "points_per_rank": -1, "page": 164},
    {"name": "Significant Other", "category": "Lesser", "points_per_rank": -1, "page": 165},
    {"name": "Skeleton in the Closet", "category": "Greater", "points_per_rank": -2, "page": 165},
    {"name": "Social Fault", "category": "Lesser", "points_per_rank": -1, "page": 166},
    {"name": "Special Requirement", "category": "Serious", "points_per_rank": -3, "page": 166},
    {"name": "Unappealing", "category": "Lesser", "points_per_rank": -1, "page": 166},
    {"name": "Unique Defect", "category": "Special", "points_per_rank": 0, "page": 167, "note": "Variable"},
    {"name": "Vulnerability", "category": "Greater", "points_per_rank": -2, "page": 167},
    {"name": "Wanted", "category": "Greater", "points_per_rank": -2, "page": 167},
    {"name": "Weak Point", "category": "Greater", "points_per_rank": -2, "page": 167},
]

# Table-11: Standard Enhancements (p.146)
ENHANCEMENTS = [
    {"name": "Area", "cost_modifier": 1, "page": 145},
    {"name": "Duration", "cost_modifier": 1, "page": 146},
    {"name": "Range", "cost_modifier": 1, "page": 147},
    {"name": "Targets", "cost_modifier": 1, "page": 147},
    {"name": "Potent", "cost_modifier": 1, "page": 147},
]

# Table-12: Limiters (p.148)
LIMITERS = [
    {"name": "Activation", "cost_modifier": -1, "page": 148},
    {"name": "Assisted", "cost_modifier": -1, "page": 148},
    {"name": "Backlash", "cost_modifier": -1, "page": 148},
    {"name": "Charges", "cost_modifier": -1, "page": 148},
    {"name": "Concentration", "cost_modifier": -1, "page": 149},
    {"name": "Consumable", "cost_modifier": -1, "page": 149},
    {"name": "Delay", "cost_modifier": -1, "page": 149},
    {"name": "Dependent", "cost_modifier": -1, "page": 149},
    {"name": "Deplete", "cost_modifier": -1, "page": 149},
    {"name": "Detectable", "cost_modifier": -1, "page": 150},
    {"name": "Emotional", "cost_modifier": -1, "page": 150},
    {"name": "Environmental", "cost_modifier": -1, "page": 150},
    {"name": "Equipment", "cost_modifier": -1, "page": 150},
    {"name": "Imbue", "cost_modifier": -1, "page": 150},
    {"name": "Irreversible", "cost_modifier": -1, "page": 151},
    {"name": "Localised", "cost_modifier": -1, "page": 151},
    {"name": "Maximum", "cost_modifier": -1, "page": 151},
    {"name": "Object", "cost_modifier": -1, "page": 151},
    {"name": "Permanent", "cost_modifier": -1, "page": 152},
    {"name": "Recovery", "cost_modifier": -1, "page": 152},
    {"name": "Semi-Permanent", "cost_modifier": -1, "page": 152},
    {"name": "Unique", "cost_modifier": -1, "page": 153},
    {"name": "Unpredictable", "cost_modifier": -1, "page": 153},
]

# Skill Groups (p.120, Table-07). Cost varies by group tier (1/2/3 per level).
# The book groups Skills into Group categories. Listed here with page refs only.
SKILL_GROUPS = [
    {"name": "Adventuring", "cost_per_level": 2, "page": 120},
    {"name": "Artisan", "cost_per_level": 1, "page": 120},
    {"name": "Everyman", "cost_per_level": 1, "page": 120},
    {"name": "Scholar", "cost_per_level": 2, "page": 120},
    {"name": "Scientist", "cost_per_level": 3, "page": 120},
    {"name": "Technician", "cost_per_level": 2, "page": 120},
    {"name": "Warrior", "cost_per_level": 3, "page": 120},
]

# Power Levels (Table-01, p.22)
POWER_LEVELS = [
    {"name": "Mundane", "points": 40, "page": 22},
    {"name": "Adventurous", "points": 80, "page": 22},
    {"name": "Heroic", "points": 120, "page": 22},
    {"name": "Epic", "points": 200, "page": 22},
    {"name": "Mythic", "points": 300, "page": 22},
]

# Knowledge node types (app-level, not BESM-specific)
NODE_TYPES = ["npc", "location", "item", "event", "quest", "lore", "faction", "creature"]

# BESM Extras — Rule Expansions & Character Options (Dyskami, v1.1.2)
# This is a separate book; source references use the "BESM Extras" label.
BOOK_EXTRAS = "BESM Extras"

EXTRAS_RULES = [
    # Chapter 1 — Stats & Values
    {"name": "Shock Value", "category": "Stat Extension", "page": 14, "summary": "gritty injury tracking"},
    {"name": "Sanity Points", "category": "Stat Extension", "page": 15, "summary": "horror / mental strain track"},
    # Chapter 2 — Skills
    {"name": "Skill Ranks", "category": "Skill Expansion", "page": 19, "summary": "rank-based skill progression (Rank 1–5)"},
    {"name": "Genius Skills", "category": "Skill Expansion", "page": 23, "summary": "prodigy-level bonus rules"},
    {"name": "Skill Specialisations", "category": "Skill Expansion", "page": 24, "summary": "narrow-focus bonuses"},
    {"name": "Individual Skills", "category": "Skill Expansion", "page": 26, "summary": "replace Skill Groups with single skills"},
    {"name": "Templates and Skills", "category": "Skill Expansion", "page": 26, "summary": "pre-built skill template kits"},
    # Chapter 3 — Expanded Attributes / Enh / Lim (page refs vary)
    # Chapter 4 — Combat
    {"name": "Morale for NPCs", "category": "Combat Option", "page": 51, "summary": "rout / surrender mechanics"},
    {"name": "Mass Combat", "category": "Combat Option", "page": 52, "summary": "large-scale engagements"},
    {"name": "Critical Hits", "category": "Combat Option", "page": 56},
    {"name": "Critical Failures", "category": "Combat Option", "page": 57},
    {"name": "Grappling (Expanded)", "category": "Combat Option", "page": 58},
    {"name": "Tactical Combat", "category": "Combat Option", "page": 60},
    {"name": "Combined Attacks", "category": "Combat Option", "page": 62},
    # Chapter 6 — Power Packs & Bundles
    {"name": "Power Packs", "category": "Character Option", "page": 73, "summary": "themed attribute bundles (e.g. Wizardry)"},
    {"name": "Power Bundles", "category": "Character Option", "page": 76, "summary": "mix-and-match attribute packages"},
    # Chapter 7 — Hazards
    {"name": "Poisons", "category": "Hazard", "page": 80},
    {"name": "Disease", "category": "Hazard", "page": 82},
    {"name": "Deprivation", "category": "Hazard", "page": 84},
    {"name": "Threat Scores", "category": "Hazard", "page": 86},
    {"name": "Artificial Intelligences", "category": "NPC Type", "page": 93},
]
TARGET_NUMBERS = [
    {"difficulty": "Easy", "tn": 6, "page": 177},
    {"difficulty": "Average", "tn": 8, "page": 177},
    {"difficulty": "Challenging", "tn": 10, "page": 177},
    {"difficulty": "Hard", "tn": 12, "page": 177},
    {"difficulty": "Very Hard", "tn": 14, "page": 177},
    {"difficulty": "Extreme", "tn": 16, "page": 177},
    {"difficulty": "Nearly Impossible", "tn": 18, "page": 177},
]


def with_source(items):
    """Attach source metadata to each entry for API consumption."""
    enriched = []
    for it in items:
        enriched.append({**it, "source": {"book": BOOK, "page": it.get("page")}})
    return enriched
