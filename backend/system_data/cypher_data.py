"""Cypher System reference data — Cypher System Creator licence.

Mechanic names + page references only — no reproduced flavour prose, lore,
type/focus paragraph descriptions, or numbered cypher-effect prose.

Cypher System core dice mechanic: roll a single d20 ≥ (3 × difficulty).
Difficulty 1-10. Effort, Edge, and Skills lower difficulty by 1 step each.
"""

BOOK = {
    "title": "Cypher System Reference Document (Cypher System Creator)",
    "publisher": "Monte Cook Games, LLC",
    "license": "Cypher System Creator — community content licence",
    "page_range_max": 400,
    "compatible_settings": ["Numenera", "The Strange", "Predation",
                             "Godforsaken", "Stay Alive!", "Claim the Sky",
                             "Old Gods of Appalachia", "Rust & Redemption"],
}

# Three core stat pools — the Cypher engine.
STAT_POOLS = [
    {"name": "Might",        "blurb_role": "Physical force · vigor"},
    {"name": "Speed",        "blurb_role": "Quickness · reflexes"},
    {"name": "Intellect",    "blurb_role": "Mental acuity · learning"},
]

# Six SRD types — Cypher's "classes" — kept to mechanic-only descriptors.
TYPES = [
    {"name": "Warrior",        "intrusion": "Combat",   "starting_pools": "Might+8 / Speed+8 / Intellect+2",
     "edge_at_1": ["Might 1"]},
    {"name": "Adept",          "intrusion": "Esoteric", "starting_pools": "Might+2 / Speed+8 / Intellect+8",
     "edge_at_1": ["Intellect 1"]},
    {"name": "Explorer",       "intrusion": "Recovery", "starting_pools": "Might+6 / Speed+6 / Intellect+6",
     "edge_at_1": ["Might 1 OR Speed 1"]},
    {"name": "Speaker",        "intrusion": "Social",   "starting_pools": "Might+4 / Speed+4 / Intellect+8",
     "edge_at_1": ["Intellect 1"]},
    {"name": "Wright",         "intrusion": "Crafting", "starting_pools": "Might+4 / Speed+8 / Intellect+8",
     "edge_at_1": ["Speed 1 OR Intellect 1"]},
    {"name": "Paradox",        "intrusion": "Reality",  "starting_pools": "Might+0 / Speed+8 / Intellect+12",
     "edge_at_1": ["Intellect 2"]},
]

# 16 SRD descriptors — flavour-flag for backstory + 1 Edge or Skill bonus.
DESCRIPTORS = [
    "Brash", "Charming", "Clever", "Doomed", "Empathic", "Graceful",
    "Hideous", "Impulsive", "Intelligent", "Mystical", "Mysterious",
    "Resilient", "Stealthy", "Swift", "Tough", "Vicious",
]

# 18 SRD foci — name + sentence-fragment role only.
FOCI = [
    {"name": "Bears a Halo of Fire",       "role": "Burns nearby foes · area zones"},
    {"name": "Carries a Quiver",            "role": "Ranged archery specialist"},
    {"name": "Commands Mental Might",       "role": "Telepathy · psionic blasts"},
    {"name": "Conducts Weird Science",      "role": "Improvised cyphers · gadgets"},
    {"name": "Crafts Illusions",            "role": "Visual / auditory deceptions"},
    {"name": "Crafts Unique Objects",       "role": "Item creation · workshop bonuses"},
    {"name": "Defends the Weak",            "role": "Tank · ally protection"},
    {"name": "Entertains",                  "role": "Charisma · audience-buff"},
    {"name": "Exists Partially Out of Phase","role": "Phase shift · selective intangibility"},
    {"name": "Explores Dark Places",        "role": "Stealth · subterranean expertise"},
    {"name": "Fights with Panache",         "role": "Duellist · improvised reposte"},
    {"name": "Howls at the Moon",           "role": "Shapeshift · primal form"},
    {"name": "Leads",                       "role": "Allies act as if Trained"},
    {"name": "Masters Defense",             "role": "Armor · Speed defense"},
    {"name": "Masters Weaponry",            "role": "Weapon-mastery · combat finesse"},
    {"name": "Murders",                     "role": "Stealth strikes · finishers"},
    {"name": "Wields Two Weapons at Once",  "role": "Twin-blade · split-attack"},
    {"name": "Works Miracles",              "role": "Divine intervention · faith effects"},
]

# Skills — task-shaped. Train / Specialise lowers difficulty by 1 each step.
SKILLS = [
    "Climbing", "Crafting", "Deception", "Endurance", "Healing",
    "Initiative", "Interaction", "Intimidation", "Jumping", "Knowledge",
    "Lore", "Negotiation", "Perception", "Persuasion", "Pickpocketing",
    "Repairing", "Riding", "Running", "Searching", "Stealth",
    "Survival", "Swimming", "Tracking",
]

# Cyphers — single-use mystery items. SRD core sample, mechanic-only.
CYPHERS = [
    {"name": "Adhesion Patch",    "level": "1d6+1",  "form": "Patch",   "effect": "Glues two objects · breaks at level+5 Might"},
    {"name": "Analeptic",          "level": "1d6+2",  "form": "Tablet",  "effect": "Restore (level) Pool points"},
    {"name": "Anti-venom",         "level": "1d6+1",  "form": "Vial",    "effect": "Auto-recover from venom up to level"},
    {"name": "Banishment Field",   "level": "1d6+3",  "form": "Sphere",  "effect": "Force one entity into another dimension for 1 round/lvl"},
    {"name": "Detonation",         "level": "1d6+2",  "form": "Pellet",  "effect": "level d6 damage to immediate radius"},
    {"name": "Force Shield",       "level": "1d6+1",  "form": "Bracer",  "effect": "+ (level) Armor for 1 hour"},
    {"name": "Gravity Negator",    "level": "1d6+2",  "form": "Disc",    "effect": "Float at will for 1 hour"},
    {"name": "Knowledge Enhancer", "level": "1d6+1",  "form": "Helmet",  "effect": "Specialise in 1 skill for 1 hour"},
    {"name": "Mind Probe",         "level": "1d6+3",  "form": "Wire",    "effect": "Read surface thoughts level rounds"},
    {"name": "Phase Disruptor",    "level": "1d6+3",  "form": "Crystal", "effect": "Hinder out-of-phase / spirit foes by 2"},
    {"name": "Spatial Warp",       "level": "1d6+2",  "form": "Coil",    "effect": "Teleport (level × 100) ft"},
    {"name": "Vital Sense",        "level": "1d6+1",  "form": "Patch",   "effect": "See life signs / count + intent at 50 ft"},
]

# Artifacts — persistent items with depletion roll.
ARTIFACTS = [
    {"name": "Crystallized Memory",       "level": "1d6+2", "form": "Cube",     "effect": "Replay any moment witnessed",       "depletion": "1 in 1d20"},
    {"name": "Far-Step Boots",             "level": "1d6+3", "form": "Boots",    "effect": "Telejump 100 ft as action",         "depletion": "1 in 1d10"},
    {"name": "Healing Vest",               "level": "1d6+2", "form": "Vest",     "effect": "Recover 1 Pool / hr while worn",    "depletion": "1 in 1d6 daily"},
    {"name": "Living Blade",               "level": "1d6+3", "form": "Sword",    "effect": "+(level/2) damage · regrows lost edge", "depletion": "—"},
    {"name": "Pocket Reality",             "level": "1d6+4", "form": "Sphere",   "effect": "Stable 30-ft cube extradimensional space", "depletion": "1 in 1d100"},
    {"name": "Ward Stone",                 "level": "1d6+2", "form": "Stone",    "effect": "Force shield level Armor on holder","depletion": "1 in 1d20"},
]

# GM Intrusion — the Cypher narrative tax.
GM_INTRUSION = {
    "summary": "GM offers an unfortunate complication; player accepts (+2 XP, +2 XP for chosen ally) or refuses (−1 XP). Driven by the GM, never the dice.",
    "page": 152,
}

# Six tiers — level brackets in Cypher.
POWER_LEVELS = [
    {"name": "Tier 1", "level_range": "1",   "blurb": "Apprentice · 6 starting pool, 0 Edge"},
    {"name": "Tier 2", "level_range": "2",   "blurb": "Established adventurer"},
    {"name": "Tier 3", "level_range": "3",   "blurb": "Veteran · regional renown"},
    {"name": "Tier 4", "level_range": "4",   "blurb": "Master · multi-Edge"},
    {"name": "Tier 5", "level_range": "5",   "blurb": "Legend · world-shaper"},
    {"name": "Tier 6", "level_range": "6",   "blurb": "Mythic · capstone abilities"},
]

REFERENCE = {
    "system_id": "cypher",
    "kind": "type-focus-descriptor",
    "book": BOOK,
    "stat_pools": STAT_POOLS,
    "types": TYPES,
    "descriptors": DESCRIPTORS,
    "foci": FOCI,
    "skills": SKILLS,
    "cyphers": CYPHERS,
    "artifacts": ARTIFACTS,
    "gm_intrusion": GM_INTRUSION,
    "power_levels": POWER_LEVELS,
    "modifier_formula": "Difficulty × 3 = TN; lower difficulty by 1 step per Skill / Edge / Asset / Effort",
    "rule_note": (
        "Cypher: roll 1d20 ≥ (3 × difficulty). Train (-1 step), Specialise (-1 step), "
        "Effort (-1 step per Pool point, max equal to Edge+1). Sentence: "
        "'I am a [adjective] [noun] who [verbs].' = Descriptor-Type-Focus."
    ),
}
