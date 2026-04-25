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


# -------- Mechanic-only explanatory blurbs --------
# These are GENERIC mechanic descriptions written in original wording.
# They describe HOW a thing works inside the cost equation
#   final_cost = base_cost × level × (1 + Σ enhancements − Σ limiters)
# without reproducing the rulebook's prose, lore, or examples.
ATTRIBUTE_BLURBS = {
    "Absorption": "Convert incoming damage of a chosen energy type into a personal resource (HP, EP, or a fuel pool).",
    "Alternate Form": "Switch to a secondary statblock at runtime; build the alternate form with a fraction of your points.",
    "Alternate Identity": "Maintain a parallel social/legal identity; mechanic governs how easily one identity reveals the other.",
    "Armour": "Each Level subtracts a fixed amount from incoming damage before HP loss is calculated.",
    "Attack Mastery": "Adds its Level to your Attack Combat Value, improving every attack roll by that amount.",
    "Augmented": "A trait raised beyond the human ceiling. Each Level lifts a Stat or derived value above its normal cap.",
    "Capacity": "Carry, store, or contain more than the baseline. Scales lift, hold, or stowage capacity per Level.",
    "Change State": "Shift physical form (gas, liquid, light, etc.) for movement / defence purposes.",
    "Cognition": "Bonus on knowledge / recall / mental analysis rolls. Each Level adds a flat bonus to deduction-style checks.",
    "Combat Technique": "Each Level grants one named combat manoeuvre (Lightning Reflexes, Two Weapons, etc.). Stacks with weapons.",
    "Companion": "A persistent allied character built with a fraction of your own points; acts on its own initiative.",
    "Connected": "A network of contacts / favours. Higher Levels = wider, deeper, or more important contacts.",
    "Control Environment": "Manipulate weather / terrain / ambient effects within a scene-scale area.",
    "Conversion": "Persuade or recruit foes mid-encounter; resolves as a contested mental action.",
    "Data Access": "Reach databases, archives, or networks beyond what mundane research can find.",
    "Defence Mastery": "Adds its Level to your Defence Combat Value, improving every defence roll by that amount.",
    "Dimension Walk": "Step between adjacent realities or planes. Range and frequency scale with Level.",
    "Dynamic Powers": "Open-ended effect-swap (10 pts/Level). Almost always restricted by GM Primer at lower power levels.",
    "Elasticity": "Stretch or extend body parts. Reach and contortion scale with Level.",
    "Enemy Attack": "A held-back attack that triggers on a foe's setup. Tactical reaction-style mechanic.",
    "Enemy Defence": "A reactive defence that turns or punishes an opponent's incoming attack.",
    "Energised": "Each Level adds +5 Energy Points — the resource pool for stamina powers, casting, etc.",
    "Exorcism": "Banish or weaken supernatural / extradimensional entities through a contested check.",
    "Extra Actions": "Each Level grants one additional action per round. Most expensive Level-1 Attribute (4 pts).",
    "Extra Arms": "Adds appendages. Each pair grants extra grip / hold / parallel manipulation actions.",
    "Features": "Each Level grants one minor narrative perk (sense, immunity-to-trivia, social grace, etc.).",
    "Flight": "Aerial movement Attribute. Speed and ceiling scale with Level.",
    "Force Field": "A second HP-like barrier sitting in front of your real HP. Each Level adds capacity.",
    "Gear": "A lump of mundane equipment your character carries. 1 pt/Level scales with quality and quantity.",
    "Ground Speed": "Each Level multiplies overland movement rate.",
    "Healing": "Restore HP to others or self. Each Level raises the rate or pool of healing per use.",
    "Heightened Awareness": "Each Level adds a generic perception bonus across the board, regardless of sense.",
    "Heightened Senses": "Each Level grants one keener sense or sense-class. Stacks with mundane perception checks.",
    "Illusion": "Project sensory deception. Complexity and persistence scale with Level.",
    "Immunity": "Each Level grants total immunity to a chosen damage type, condition, or hazard.",
    "Immutable": "Resists a chosen kind of forced change (transformation, mind control, dispel, etc.).",
    "Inspire": "Bonus to allies on a contested or social action. Buff-style effect.",
    "Item": "Half-price Attribute (0.5 pts/Level) representing an external object that can be lost, stolen, or broken.",
    "Jumping": "Vertical and horizontal leap distance. Each Level multiplies baseline jump.",
    "Massive Damage": "Each Level adds +5 damage to a chosen damage source — typically a Weapon or unarmed strike.",
    "Melee Attack": "Adds its Level to a chosen melee weapon class only. Cheaper than Attack Mastery, narrower scope.",
    "Melee Defence": "Adds its Level to defence against a chosen melee weapon class only.",
    "Merge": "Fuse with an object, host, or another character; combined statblock per merge rules.",
    "Metamorphosis": "Reshape your physical form within a defined library of options.",
    "Mimic": "Copy another's Attribute or Skill for a limited duration after observing it.",
    "Mind Control": "Mental compulsion Attribute. Highly restricted in most campaigns — confirm with the GM.",
    "Mind Shield": "Each Level grants resistance against mental Attributes (Mind Control, Telepathy, etc.).",
    "Minions": "A pool of low-level followers. Each Level grows the pool's size or competence.",
    "Mulligan": "Re-roll a failed check (or force an opponent's re-roll) a limited number of times per session.",
    "Nullify": "Suppress another's Attribute for a contested duration. Heavy GM-Primer territory.",
    "Plant Control": "Manipulate flora — entangle, grow, blight. Area and effect scale with Level.",
    "Pocket Dimension": "A private storage / sanctuary plane keyed to you. Capacity scales with Level.",
    "Portal": "Open a traversable doorway between two locations. Range and aperture scale with Level.",
    "Power Flux": "Reshape your own power loadout under defined constraints (10 pts/Level).",
    "Power Variation": "Swap one specific Attribute for another within a thematic set, scene by scene.",
    "Projection": "Cast a duplicate or astral form away from your body. Range and durability scale with Level.",
    "Ranged Attack": "Adds its Level to a chosen ranged weapon class only. Narrower scope than Attack Mastery.",
    "Ranged Defence": "Adds its Level to defence against a chosen ranged weapon class only.",
    "Regeneration": "Auto-heal HP each round. Each Level raises the per-round restoration.",
    "Reincarnation": "On death, return in a new form after a delay. Frequency and form scale with Level.",
    "Resilient": "Resistance against environmental hazards (heat, cold, vacuum, radiation, etc.).",
    "Sensory Block": "Project a barrier blocking a chosen sense or detection method within an area.",
    "Sixth Sense": "Detect a specific category of phenomena (magic, evil, lies, etc.) without normal senses.",
    "Size Change": "Grow or shrink dramatically (10 pts/Level). Affects reach, damage, defence, and stealth.",
    "Skill Group": "Buys a tier-priced bundle of related skills. Cost rises with the tier (Lesser/Greater/Major).",
    "Spaceflight": "Movement in vacuum / interplanetary scale. Each Level multiplies cosmic-scale speed.",
    "Special Movement": "One specialised mode (climbing, swinging, balancing, etc.) bought per Level.",
    "Summon Creatures": "Call temporary supernatural servants. Number and power scale with Level.",
    "Supersense": "An exotic sense beyond mortal range (radar, X-ray, life-detection, etc.).",
    "Superspeed": "Move and act at extreme tempo. Each Level multiplies movement and adds initiative.",
    "Superstrength": "Lift, throw, and crush at superhuman scale. Each Level multiplies carrying / damage.",
    "Swarm": "You are (or control) a body composed of many small parts; fragmented HP and immunity logic apply.",
    "Telekinesis": "Move objects at range without contact. Strength and precision scale with Level.",
    "Telepathy": "Two-way mental communication. Range and bandwidth scale with Level.",
    "Teleport": "Instantaneous self-relocation. Range and frequency scale with Level.",
    "Tough": "Each Level adds +5 Hit Points. Mechanically the cheapest way to soak more damage before falling.",
    "Transfer": "Move HP, EP, or Attribute Levels from one target to another (consensual or contested).",
    "Transmute": "Change matter from one state or substance to another. Mass and complexity scale with Level.",
    "Tunnelling": "Bore through earth / stone / wall material. Speed and material grade scale with Level.",
    "Unaffected": "Total immunity to a chosen ongoing condition or environmental class.",
    "Undetectable": "Resists a chosen detection method (visual, magical, electronic, etc.).",
    "Unique Attribute": "Custom GM-authored Attribute (1-10 pts/Level). Defined entirely by the table's primer.",
    "Unknown Power": "An undefined power-slot. Cost is set by the GM at reveal time.",
    "Water Speed": "Swimming / surface / underwater movement rate. Each Level multiplies aquatic speed.",
    "Wealth": "Mundane economic class. Higher Levels unlock larger purchases without spending Character Points.",
    "Weapon": "A persistent damage-dealing object. Reshape with Enhancements (Penetrating, Reach, etc.) and Limiters (Charges, Activation).",
}

# Defect families share the same mechanic shape, so we describe them by category…
DEFECT_CATEGORY_BLURBS = {
    "Lesser":  "Lesser Defect: returns +1 Character Point per Rank. Light narrative friction; little mechanical drag.",
    "Greater": "Greater Defect: returns +2 Character Points per Rank. Real mechanical or narrative cost in play.",
    "Serious": "Serious Defect: returns +3 Character Points per Rank. Defining flaw — expect frequent in-play impact.",
    "Special": "Special / Custom Defect: GM defines refund and trigger conditions case-by-case.",
}
# …plus per-name nuance for the most-used picks.
DEFECT_BLURBS = {
    "Achilles Heel": "A specific stimulus deals extra damage or bypasses your defences entirely.",
    "Awkward Size": "Item-only Defect: the object is too large/small for normal handling. Penalises stealth, fitting, or use.",
    "Bane": "A category of foe (creature type, faction, etc.) hits you harder or resists your attacks.",
    "Blind Fury": "Once triggered, you attack indiscriminately and lose target discrimination until calmed.",
    "Conditional Ownership": "An asset (Item, Companion, Wealth) can be revoked by an external authority on any session.",
    "Confined": "You are physically constrained to a defined space and lose access outside it.",
    "Cursed": "A persistent supernatural malus tied to a trigger; surfaces at narratively inconvenient moments.",
    "Easily Distracted": "Penalty on focus-dependent rolls when a competing stimulus is present.",
    "Fragile": "Reduced HP-pool or shorter wound-thresholds compared to baseline.",
    "Hounded": "An organised group continuously hunts you — recurring antagonist pressure.",
    "Impaired Manipulation": "Penalty or outright inability for fine-motor / object-manipulation actions.",
    "Impaired Speech": "Penalty or inability for verbal communication; reduces Social rolls and casting verbal components.",
    "Inept Attack": "A specific Attack Combat Value bucket suffers a penalty.",
    "Inept Defence": "A specific Defence Combat Value bucket suffers a penalty.",
    "Involuntary Change": "Triggers an Alternate Form / Metamorphosis swap outside your control.",
    "Ism": "Subject to social discrimination by a defined group — penalises Social rolls in their society.",
    "Magnet": "Attracts a specific category of unwanted attention (police, predators, opportunists, etc.).",
    "Marked": "An obvious distinguishing trait makes stealth and disguise harder.",
    "Nemesis": "A recurring antagonist whose appearances tilt the table against you.",
    "Nightmares": "Disrupted rest reduces full-recovery benefits between sessions.",
    "Obligated": "Bound by oath / debt / role to act for a specific cause; refusal carries narrative cost.",
    "Phobia": "Panic / freeze response when exposed to a specific trigger.",
    "Physical Impairment": "A persistent bodily limitation imposing standing penalties.",
    "Red Tape": "Bureaucratic friction — every official action takes longer or costs more.",
    "Reduced Damage": "Your damage output is permanently below baseline for your power tier.",
    "Sensory Impairment": "A blocked or dampened sense reduces Perception rolls in that channel.",
    "Shortcoming": "A chosen Stat or Skill is below baseline for your power tier.",
    "Significant Other": "A loved one creates leverage / kidnap-risk against you.",
    "Skeleton in the Closet": "A concealed past will surface if your enemies dig. Reputation and secrecy are at risk.",
    "Social Fault": "A faux-pas pattern that reliably degrades Social rolls in mixed company.",
    "Special Requirement": "A regular ritual / consumption / contact is required to keep your build functioning.",
    "Unappealing": "Reduced effectiveness on Social rolls that depend on personal appeal.",
    "Unique Defect": "Custom GM-authored Defect. Refund set per primer.",
    "Vulnerability": "Specific damage type bypasses Armour / Force Field or deals double.",
    "Wanted": "Active arrest warrant or bounty creates ongoing pursuit pressure.",
    "Weak Point": "A precise body part / interface, when struck, ignores defences or applies a status.",
}

# Per-name nuance for Enhancements (mechanic-only, not lore)
ENHANCEMENT_BLURB = (
    "An Enhancement raises an Attribute's effective Level for cost purposes. "
    "Stacking N enhancements multiplies the per-Level cost: cost × Level × (1 + N − Limiters)."
)
ENHANCEMENT_BLURBS = {
    "Area":     "Effect covers a wider area than baseline. Scale: from melee-radius up to scene-scale.",
    "Duration": "Effect persists longer than the default round-or-action window.",
    "Range":    "Effect projects further than its default contact / short-range default.",
    "Targets":  "Effect can hit / govern more targets per activation.",
    "Potent":   "Effect lands harder than baseline — overcomes one tier of resistance.",
}

LIMITER_BLURB = (
    "A Limiter lowers an Attribute's cost in exchange for narrative or situational restrictions. "
    "Stacking N limiters reduces the cost: cost × Level × (1 + Enhancements − N). Net cost cannot fall below 1 per Level."
)
LIMITER_BLURBS = {
    "Activation":      "Requires a specific trigger word, gesture, or condition before the Attribute fires.",
    "Assisted":        "Needs a partner / ally / tool to function. Lone use fails.",
    "Backlash":        "Misuse or failure damages or hinders the user.",
    "Charges":         "A finite number of uses per scene / session before a recharge phase.",
    "Concentration":   "Maintaining the effect occupies your action; breaks if you take damage or split focus.",
    "Consumable":      "Burns a physical component each use.",
    "Delay":           "Takes time to spool up between activation and effect.",
    "Dependent":       "Requires a specific external state (line-of-sight, ambient element, etc.).",
    "Deplete":         "Each use temporarily reduces the effective Level until rest.",
    "Detectable":      "Use is visible / audible / traceable by a defined detection method.",
    "Emotional":       "Only functions when in a specific emotional state (rage, calm, fear, etc.).",
    "Environmental":   "Only works in a specific terrain / element / atmosphere.",
    "Equipment":       "The Attribute lives in a piece of gear — the gear can be lost, stolen, or destroyed.",
    "Imbue":           "The Attribute must be loaded into an object that then carries it.",
    "Irreversible":    "Once activated on a target, the effect cannot be cancelled by you.",
    "Localised":       "Only one body part / facet can be affected at a time.",
    "Maximum":         "Caps the maximum effective Level this Attribute can reach in play.",
    "Object":          "Can only be used through a specific physical object.",
    "Permanent":       "Always-on; cannot be turned off voluntarily.",
    "Recovery":        "Long downtime required to recover after use.",
    "Semi-Permanent":  "Cannot be turned off freely — requires a specific action / condition to dismiss.",
    "Unique":          "Only one instance / target / occurrence can ever exist at a time.",
    "Unpredictable":   "Result varies per use — sometimes weaker, sometimes off-target.",
}

EXTRAS_BLURBS = {
    "Power Packs": "A themed bundle of Attributes priced as a unit (e.g. a Wizardry pack). Cheaper than buying parts separately, but the bundle moves as one Attribute.",
    "Power Bundles": "A custom mix-and-match Attribute package the GM authorises. Use to wrap a 'class' or 'kit' into one purchase.",
    "Shock Value": "Optional gritty damage track — minor wounds reduce performance before HP runs out. Toggle on for grim/horror.",
    "Sanity Points": "Optional mental HP track. Triggers on cosmic / horror exposure. Toggle on for Lovecraftian or psychological play.",
    "Mass Combat": "Abstract resolution for engagements involving many combatants. Replaces per-figure rounds with unit-scale rolls.",
    "Critical Hits": "Optional rule: matching dice or beating TN by ≥5 inflicts extra damage / a complication.",
    "Critical Failures": "Optional rule: rolling 2 on 2d6 (or matching low) triggers a fumble / mishap.",
    "Skill Specialisations": "Narrow-focus subskills that grant a bonus inside their niche.",
    "Skill Ranks": "Rank-based skill progression (Rank 1–5). Replaces flat Levels with tiered competency.",
    "Threat Scores": "GM-facing threat budget for sessions / encounters. Spend to escalate stakes.",
    "Genius Skills": "Optional rule that flags one or two Skills as 'prodigy-level', granting an oversize bonus.",
    "Individual Skills": "Replaces grouped Skill purchases with one-skill-at-a-time precision (more granular, slightly higher accounting cost).",
    "Templates and Skills": "Pre-built skill packages mapped to professions / archetypes — faster character creation.",
    "Morale for NPCs": "Optional rout / surrender check for NPC groups when losses pass a threshold.",
    "Grappling (Expanded)": "Fuller grapple resolution: position, escape, controlled movement, and damage from holds.",
    "Tactical Combat": "Hex / square grid combat layer with facing, cover, and exact movement.",
    "Combined Attacks": "Multiple attackers focus on one target, pooling rolls for greater effect.",
    "Poisons": "Toxin / venom track separate from HP. Save tier and onset time per dose.",
    "Disease": "Long-tail illness mechanic with stages, contagion, and recovery checks.",
    "Deprivation": "Hunger / thirst / cold / exhaustion as accumulating penalties.",
    "Artificial Intelligences": "Stat block style for non-biological NPCs — different vulnerabilities and recovery rules.",
}

POWER_LEVEL_BLURBS = {
    "Mundane":     "Real-world humans. No supernatural Attributes. Stat caps low, point pool small.",
    "Adventurous": "Pulp / action hero range. Capable specialists; very limited or no powers.",
    "Heroic":      "Standard fantasy/anime/superhero starting tier. Distinctive powers expected.",
    "Epic":        "World-shaping adventurers. Multiple high-Level Attributes; faction-tier influence.",
    "Mythic":      "Reality-altering tier. Avoid unless your campaign is built for it.",
}

GENERIC_BLURBS = {
    "How costing works": (
        "Every Attribute costs (base cost per Level) × (Level) × (1 + Enhancements − Limiters). "
        "Defects refund a flat amount per Rank. Total Spent = Stats + Attributes + Skills − Defect refunds, "
        "and must stay within the campaign's Character Point budget."
    ),
    "Items vs Mundane": (
        "An Item is an Attribute purchased at half price (0.5/Level) representing something external to your body. "
        "A 'mundane' object is anything in your inventory that isn't a purchased Attribute — narrative, not mechanical."
    ),
    "Weapon vs Gear vs Item": (
        "Weapon is a damage-dealing Attribute (2/Level) reshaped by Enhancements/Limiters. "
        "Gear is a lump of equipment quality (1/Level). Item is the half-price wrapper for ANY external Attribute (0.5×)."
    ),
}


# -------- Per-Attribute mod whitelists (BESM 4E) --------
# Most Attributes accept all 5 Enhancements + all 23 Limiters. A handful have
# rule-side restrictions or strong conventions. `None` = all mods allowed.
# A list = only the named mods make sense for that Attribute.
# These are advisory, surfaced as warnings in the Customise picker — not hard
# blocks (the GM Primer can override anything via custom rules).
ALL_ENHANCEMENTS = [e["name"] for e in ENHANCEMENTS]
ALL_LIMITERS = [l["name"] for l in LIMITERS]

ATTRIBUTE_MOD_WHITELIST = {
    # Wealth, Connected, Gear, Item, Companion, Minions are "narrative-shape"
    # Attributes — Range / Targets enhancements rarely apply.
    "Wealth":     {"enhancements": [], "limiters": ["Charges", "Activation", "Detectable", "Permanent", "Unique"]},
    "Connected":  {"enhancements": ["Range"], "limiters": ["Activation", "Detectable", "Localised", "Unique"]},
    "Gear":       {"enhancements": [], "limiters": ["Charges", "Consumable", "Equipment", "Object", "Unique"]},
    "Item":       {"enhancements": ALL_ENHANCEMENTS, "limiters": ALL_LIMITERS},  # half-price wrapper, anything goes
    "Companion":  {"enhancements": ["Range", "Duration"], "limiters": ["Activation", "Equipment", "Object", "Unique"]},
    "Minions":    {"enhancements": ["Range", "Duration", "Targets"], "limiters": ["Activation", "Equipment", "Unique"]},
    # Mastery / Combat-Technique are flat numerical bonuses; modifiers don't really apply.
    "Attack Mastery":   {"enhancements": [], "limiters": ["Object", "Activation", "Environmental"]},
    "Defence Mastery":  {"enhancements": [], "limiters": ["Object", "Activation", "Environmental"]},
    "Combat Technique": {"enhancements": [], "limiters": ["Object", "Activation", "Environmental"]},
    "Massive Damage":   {"enhancements": ["Potent"], "limiters": ["Object", "Activation", "Charges", "Environmental"]},
    "Tough":            {"enhancements": [], "limiters": ["Activation", "Environmental", "Detectable"]},
    "Energised":        {"enhancements": [], "limiters": ["Activation", "Environmental", "Detectable"]},
    # Heightened Awareness / Senses — narrow but accept several mods.
    "Heightened Awareness": {"enhancements": ["Range"], "limiters": ["Activation", "Detectable", "Environmental", "Concentration"]},
    "Heightened Senses":    {"enhancements": ["Range"], "limiters": ["Activation", "Detectable", "Environmental"]},
    # Movement modes — Range / Duration meaningful, Targets / Area not.
    "Flight":     {"enhancements": ["Range", "Duration"], "limiters": ALL_LIMITERS},
    "Teleport":   {"enhancements": ["Range", "Targets"],  "limiters": ALL_LIMITERS},
    "Tunnelling": {"enhancements": ["Range", "Duration"], "limiters": ALL_LIMITERS},
    "Ground Speed":     {"enhancements": ["Duration"], "limiters": ALL_LIMITERS},
    "Water Speed":      {"enhancements": ["Duration"], "limiters": ALL_LIMITERS},
    "Spaceflight":      {"enhancements": ["Duration"], "limiters": ALL_LIMITERS},
    "Special Movement": {"enhancements": ["Duration"], "limiters": ALL_LIMITERS},
    "Superspeed":       {"enhancements": ["Duration"], "limiters": ALL_LIMITERS},
    # Mind-affecting — restricted at most tables.
    "Mind Control":  {"enhancements": ALL_ENHANCEMENTS, "limiters": ALL_LIMITERS},
    "Telepathy":     {"enhancements": ["Range", "Targets", "Duration"], "limiters": ALL_LIMITERS},
    "Mind Shield":   {"enhancements": ["Targets", "Duration"], "limiters": ["Activation", "Environmental", "Charges"]},
    # Open-ended power slots — almost anything makes sense.
    "Dynamic Powers": {"enhancements": ALL_ENHANCEMENTS, "limiters": ALL_LIMITERS},
    "Power Flux":     {"enhancements": ALL_ENHANCEMENTS, "limiters": ALL_LIMITERS},
    "Power Variation":{"enhancements": ALL_ENHANCEMENTS, "limiters": ALL_LIMITERS},
}

def attribute_whitelist(name: str) -> dict:
    """Return {'enhancements': [...], 'limiters': [...]} for an Attribute name.
    Empty list = none allowed (rule advisory). Missing entry = all allowed.
    """
    rec = ATTRIBUTE_MOD_WHITELIST.get(name)
    if rec is None:
        return {"enhancements": ALL_ENHANCEMENTS, "limiters": ALL_LIMITERS, "open": True}
    return {"enhancements": rec.get("enhancements", []), "limiters": rec.get("limiters", []), "open": False}

def attribute_blurb(name: str) -> str:
    return ATTRIBUTE_BLURBS.get(name, "")

def defect_blurb(category: str, name: str = "") -> str:
    # Prefer the per-name blurb when available; fall back to category text.
    return DEFECT_BLURBS.get(name) or DEFECT_CATEGORY_BLURBS.get(category, "")

def enhancement_blurb(name: str) -> str:
    return ENHANCEMENT_BLURBS.get(name) or ENHANCEMENT_BLURB

def limiter_blurb(name: str) -> str:
    return LIMITER_BLURBS.get(name) or LIMITER_BLURB

def extras_blurb(name: str) -> str:
    return EXTRAS_BLURBS.get(name, "")

def power_level_blurb(name: str) -> str:
    return POWER_LEVEL_BLURBS.get(name, "")


# -------- Game-system registry --------
# Table-Gnostic is BESM-native today; the registry advertises which other
# systems we plan to support so GMs can already commit to one at campaign
# creation. Mechanics for non-BESM systems are SCAFFOLD ONLY — the Reference
# tab and Character Forge will surface a "system content coming soon" placeholder
# until that system's data is filled in. This keeps the legal posture clean
# (we never reproduce another publisher's text without licensing).
GAME_SYSTEMS = [
    {
        "id": "besm-4e", "name": "BESM 4E", "publisher": "Dyskami Publishing",
        "edition": "4th Edition", "year": 2020,
        # Dyskami's exact required notice for Tri-Stat Emporium / BESM 4E works.
        # The {YEAR} token is filled at render time.
        "copyright": (
            "BESM Fourth Edition created and written by Mark MacKinnon. "
            "BESM Fourth Edition published by Dyskami Publishing Company with Japanime Games. "
            "Tri-Stat Emporium, Tri-Stat System, and BESM are trademarks of "
            "White Wolf Entertainment AB. Tri-Stat System text © {YEAR} "
            "White Wolf Entertainment AB. All rights reserved under international law."
        ),
        "links": ["http://www.white-wolf.com", "http://BESM4.life"],
        "logo_url": "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/yhzl2ww7_Tri-Stat%20Emporium%20BESM%20Logo%20300dpi.png",
        "supported": True,
        "blurb": "Tri-Stat point-buy: Body / Mind / Soul plus Attributes, Defects, Skill Groups. Native to Table-Gnostic.",
    },
    {
        "id": "dnd-5e", "name": "Dungeons & Dragons 5E", "publisher": "Wizards of the Coast",
        "edition": "5th Edition", "year": 2014,
        "copyright": "Dungeons & Dragons and D&D 5E are © Wizards of the Coast. SRD content available under OGL/CC.",
        "supported": False,
        "blurb": "Class + Level + Race; d20 + modifier vs DC. SRD-licensed content can be loaded; full PHB/DMG cannot.",
    },
    {
        "id": "pf2e", "name": "Pathfinder 2E", "publisher": "Paizo",
        "edition": "2nd Edition", "year": 2019,
        "copyright": "Pathfinder 2E is © Paizo Inc. Most rules text is available under the ORC licence.",
        "supported": False,
        "blurb": "Three-action combat economy; d20 + modifier with critical success/failure on ±10.",
    },
    {
        "id": "coc-7e", "name": "Call of Cthulhu 7E", "publisher": "Chaosium",
        "edition": "7th Edition", "year": 2014,
        "copyright": "Call of Cthulhu is © Chaosium Inc.",
        "supported": False,
        "blurb": "Percentile (d100) skill rolls with hard / extreme thresholds; Sanity track central to play.",
    },
    {
        "id": "savage-worlds", "name": "Savage Worlds Adventure Edition", "publisher": "Pinnacle",
        "edition": "Adventure Edition", "year": 2020,
        "copyright": "Savage Worlds is © Pinnacle Entertainment Group.",
        "supported": False,
        "blurb": "Trait dice (d4–d12) with Wild Die for player characters; pulp tempo, Bennies for re-rolls.",
    },
    {
        "id": "fate-core", "name": "FATE Core", "publisher": "Evil Hat Productions",
        "edition": "Core", "year": 2013,
        "copyright": "FATE Core is © Evil Hat Productions, available under the OGL and CC-BY.",
        "supported": False,
        "blurb": "4dF (Fate dice) + skill ladder; Aspects & Compels drive narrative leverage.",
    },
    {
        "id": "cyberpunk-red", "name": "Cyberpunk RED", "publisher": "R. Talsorian Games",
        "edition": "RED", "year": 2020,
        "copyright": "Cyberpunk RED is © R. Talsorian Games.",
        "supported": False,
        "blurb": "Roles + Lifepath; d10 + skill + stat vs DV. Cyberware Humanity track central.",
    },
    {
        "id": "vampire-5e", "name": "Vampire: The Masquerade 5E", "publisher": "Renegade Game Studios",
        "edition": "5th Edition", "year": 2018,
        "copyright": "Vampire: The Masquerade is © Paradox Interactive / White Wolf.",
        "supported": False,
        "blurb": "d10 dice pool with Hunger dice; Disciplines, Predator Type, Humanity / Touchstones.",
    },
    {
        "id": "blades-in-the-dark", "name": "Blades in the Dark", "publisher": "Evil Hat Productions",
        "edition": "1st", "year": 2017,
        "copyright": "Blades in the Dark is © One Seven Design / John Harper.",
        "supported": False,
        "blurb": "Position / Effect rolls; Stress, Trauma, Devil's Bargains. Crew sheet shared by the table.",
    },
    {
        "id": "mothership", "name": "Mothership 1E", "publisher": "Tuesday Knight Games",
        "edition": "1st Edition", "year": 2023,
        "copyright": "Mothership is © Tuesday Knight Games.",
        "supported": False,
        "blurb": "Percentile skills with Stress / Panic; sci-fi horror lethality dialled high.",
    },
    {
        "id": "shadowrun-6e", "name": "Shadowrun 6E", "publisher": "Catalyst Game Labs",
        "edition": "6th Edition", "year": 2019,
        "copyright": "Shadowrun is © Topps / The Topps Company; published under licence by Catalyst Game Labs.",
        "supported": False,
        "blurb": "d6 dice pools, Edge as currency; Matrix / Magic / Mundane intertwined.",
    },
]

GAME_SYSTEM_IDS = {s["id"] for s in GAME_SYSTEMS}
GAME_SYSTEMS_BY_ID = {s["id"]: s for s in GAME_SYSTEMS}
DEFAULT_SYSTEM_ID = "besm-4e"
