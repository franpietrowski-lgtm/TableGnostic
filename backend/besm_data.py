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

# V6.25.11 — Canonical BESM 4E Weapon Enhancements (Core p.135).
# Each entry carries its rule-sanctioned rank range (some ranks are
# fixed, some are open-ended 1+, some are discrete pick-one like
# Incapacitating 2-or-4). Cost-per-rank defaults to +1 unless the
# core book specifies otherwise. The `note` is a TableGnostic
# descriptive pass — NOT rulebook prose.
WEAPON_ENHANCEMENTS = [
    {"name": "Accurate",        "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 2],
     "note": "Attacker gains a per-rank bonus to hit with this weapon."},
    {"name": "Aura",            "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Weapon glows, pulses, or chills the air — broadcasts its nature."},
    {"name": "Autofire",        "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [3, 3],
     "note": "Full-auto: trades ammo for a burst of attacks in a round."},
    {"name": "Blight",          "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank seeds one additional decay effect at the target site."},
    {"name": "Contact",         "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 2],
     "note": "Each rank lets the weapon function through skin / hide / hull contact."},
    {"name": "Contagious",      "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Afflicted targets transmit the effect onward each rank tier."},
    {"name": "Continuing",      "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Open-ended rank — effect persists for each rank purchased (rounds)."},
    {"name": "Drain",           "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank siphons one tier of a target's resource (EP / HP / trait)."},
    {"name": "Enervation",      "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Open-ended: each rank inflicts one further tier of fatigue penalty."},
    {"name": "Flare",           "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank widens the vision-blinding / sensor-flare zone."},
    {"name": "Flexible",        "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank extends the weapon's effective reach via whip / chain geometry."},
    {"name": "Helper",          "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Grants a combat-allied familiar or smart-assist tied to the weapon."},
    {"name": "Homing",          "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 2],
     "note": "Each rank bestows a tracking / guidance system (radar / IR / thermal)."},
    {"name": "Incapacitating",  "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": "2 or 4",
     "note": "Rank 2 stuns / knocks down on hit; rank 4 KOs outright (pick one)."},
    {"name": "Inconspicuous",   "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [3, 3],
     "note": "The weapon's function is not obviously offensive to observers."},
    {"name": "Incurable",       "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank resists magical / technological healing of the inflicted wound."},
    {"name": "Indirect",        "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Attack routes around cover / line-of-sight obstacles."},
    {"name": "Insidious",       "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [3, 3],
     "note": "Victim does not immediately realise they've been struck."},
    {"name": "Irritant",        "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank applies a discomfort / distraction tier on hit."},
    {"name": "Linked",          "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Weapon chains with another attack (combo / echo shot)."},
    {"name": "Multidimensional", "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Weapon crosses dimensional / planar barriers that would block mundane hits."},
    {"name": "Muscle",          "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Weapon's damage scales with the wielder's raw Body / Strength."},
    {"name": "Penetrating",     "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Each rank ignores one tier of armour / AR."},
    {"name": "Piercing",        "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Each rank drills the attack through additional layers of cover."},
    {"name": "Psychic",         "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [4, 4],
     "note": "Fixed rank 4 — weapon bypasses the body and targets the mind directly."},
    {"name": "Quake",           "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 4],
     "note": "Each rank expands the seismic / shockwave radius."},
    {"name": "Reach",           "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Extends melee reach by one zone (polearms, spears, staves)."},
    {"name": "Selective",       "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Wielder chooses who inside the attack zone is affected and who is spared."},
    {"name": "Spreading",       "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Each rank adds one more target the attack splits to."},
    {"name": "Stun",            "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Target must save or be stunned for one round on a solid hit."},
    {"name": "Tangle",          "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Each rank entangles / restrains the struck target one tier tighter."},
    {"name": "Targetted",       "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank lets the wielder target specific body parts / subsystems."},
    {"name": "Trap",            "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Weapon lies in wait — triggers on an event you define."},
    {"name": "Unique",          "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Each rank of Unique is a single-use custom enhancement ratified with the GM."},
    {"name": "Vampiric",        "cost_modifier": 1, "page": 135, "scope": "weapon",
     "rank_range": "2 or 4",
     "note": "Rank 2 = wielder heals HP on hit; rank 4 = wielder also drains EP."},
]

# V6.25.11 — Canonical BESM 4E Weapon Limiters (Core p.142).
WEAPON_LIMITERS = [
    {"name": "Alt-Munition",    "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": "special",
     "note": "Weapon requires a special, unusual, or custom-crafted ammo type."},
    {"name": "Ammo",            "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 4],
     "note": "Each rank tightens the magazine / shot budget one tier (rank 4 = very limited)."},
    {"name": "Backblast",       "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 2],
     "note": "Each rank widens the self-damaging blow-back zone behind the wielder."},
    {"name": "Exclusive",       "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank narrows who may effectively wield the weapon."},
    {"name": "Fieldless",       "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Weapon doesn't function in specific field / technology states."},
    {"name": "Hands",           "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Weapon demands both hands — no shield / off-hand actions."},
    {"name": "Inaccurate",      "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 2],
     "note": "Each rank imposes one tier of to-hit penalty."},
    {"name": "Ingest",          "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 1],
     "note": "Effect requires the target to swallow / inhale the payload."},
    {"name": "Non-Penetrating", "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Each rank adds a tier of armour the weapon CANNOT overcome."},
    {"name": "Stoppable",       "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 4],
     "note": "Each rank adds one common counter that defeats the weapon outright."},
    {"name": "Toxic",           "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 2],
     "note": "Payload also harms the wielder on botched handling / long exposure."},
    {"name": "Unique",          "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, None],
     "note": "Each rank is a custom weapon-specific limiter agreed with the GM."},
    {"name": "Unreliable",      "cost_modifier": -1, "page": 142, "scope": "weapon",
     "rank_range": [1, 3],
     "note": "Each rank raises the chance of jam / misfire / dud on activation."},
]

# V6.25.11 — Item-specific mods retained as a TableGnostic companion
# pool (not strictly BESM 4E core). Items' half-cost rule lives in the
# validator — these are FLAVOUR mods applied to the Item attribute on
# top of its internal build. Useful for signature magical / relic
# items that have narrative character beyond their mechanical contents.
ITEM_ENHANCEMENTS = [
    {"name": "Compact",            "cost_modifier": 1, "page": 42, "scope": "item",
     "note": "Each rank halves apparent volume — easier to conceal & carry."},
    {"name": "Multi-Form",         "cost_modifier": 2, "page": 42, "scope": "item",
     "note": "+2/rk — item shifts between forms (sword ⇄ bag ⇄ ring) on command."},
    {"name": "Nigh-Indestructible","cost_modifier": 1, "page": 43, "scope": "item",
     "note": "Each rank survives one tier of damage that would normally destroy it."},
    {"name": "Subtle",             "cost_modifier": 1, "page": 43, "scope": "item",
     "note": "Detection rolls suffer one rank of penalty per rank purchased."},
    {"name": "Self-Repair",        "cost_modifier": 1, "page": 44, "scope": "item",
     "note": "Item recovers one tier of damage per scene of inactivity."},
    {"name": "Living Item",        "cost_modifier": 2, "page": 44, "scope": "item",
     "note": "+2/rk — sentient gear with limited communication."},
    {"name": "Auto-Refining",      "cost_modifier": 1, "page": 44, "scope": "item",
     "note": "Item processes contained materials into useful substances on its own schedule."},
]

ITEM_LIMITERS = [
    {"name": "Easily Lost",   "cost_modifier": -1, "page": 46, "scope": "item",
     "note": "Item slips from grip / pack on a botched skill check or surprise."},
    {"name": "Fragile",       "cost_modifier": -1, "page": 46, "scope": "item",
     "note": "Each rank lowers durability one tier — breaks on minor mishap."},
    {"name": "Volatile",      "cost_modifier": -1, "page": 47, "scope": "item",
     "note": "Risks self-damage on critical failure — pairs with weapon Backlash."},
    {"name": "Static",        "cost_modifier": -1, "page": 47, "scope": "item",
     "note": "Item's level cannot be raised by XP later — the gear is what it is."},
    {"name": "Bulky",         "cost_modifier": -1, "page": 47, "scope": "item",
     "note": "Encumbers the wielder; impedes stealth + acrobatics."},
    {"name": "Tied to Owner", "cost_modifier": -1, "page": 48, "scope": "item",
     "note": "Only functions for one specific user — others see a mundane object."},
    {"name": "Unwarned Eject","cost_modifier": -1, "page": 48, "scope": "item",
     "note": "Auto-functioning items expel by-products without notifying the wielder."},
    {"name": "No Selection",  "cost_modifier": -1, "page": 49, "scope": "item",
     "note": "Auto-refining / multi-form items cannot be commanded — the item picks."},
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
NODE_TYPES = ["npc", "location", "item", "event", "quest", "lore", "faction", "creature",
               # V6.25.11 — Materials intake pipeline. GM-seeded + player-
               # journalled content for artisan classes, loot tables,
               # encounter / director-console material-based hooks.
               "material", "byproduct", "craft_output"]

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


def with_source(items, source_book=None):
    """Attach source metadata to each entry for API consumption."""
    book = source_book or BOOK
    enriched = []
    for it in items:
        enriched.append({**it, "source": {"book": book, "page": it.get("page")}})
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


# -------- Size templates --------
# Size in BESM 4E is a TEMPLATE applied to a character / creature / item /
# weapon (and occasionally a location's structural defence). It modifies
# damage output, defence, movement pace, weight, and storage capacity. It
# is NOT a campaign-wide world-scale enum.
# The ladder below combines BESM 4E's Diminutive ↔ Massive scale with the
# more familiar Tiny ↔ Colossal d20 vocabulary so GMs can apply whichever
# vocabulary their table prefers.
SIZE_TEMPLATES = [
    {"name": "Diminutive", "alias": "Tiny",      "rank": -3,
     "damage_mod": -10, "defence_mod": +6, "speed_mult": 0.50,
     "weight_mult": 0.10,
     "blurb": "Sprite / fairy / pixie scale. Low damage, hard to hit, slow afoot but small enough to pass through anything."},
    {"name": "Small",      "alias": "Small",     "rank": -2,
     "damage_mod": -5,  "defence_mod": +3, "speed_mult": 0.75,
     "weight_mult": 0.50,
     "blurb": "Halfling / goblin / housecat scale. Modest damage, harder to hit than Medium."},
    {"name": "Medium",     "alias": "Medium",    "rank":  0,
     "damage_mod":  0,  "defence_mod":  0, "speed_mult": 1.0,
     "weight_mult": 1.0,
     "blurb": "Standard humanoid scale (default for PCs)."},
    {"name": "Large",      "alias": "Large",     "rank": +1,
     "damage_mod": +5,  "defence_mod": -2, "speed_mult": 1.25,
     "weight_mult": 4.0,
     "blurb": "Ogre / horse / war-bear scale. Hits harder, easier to hit."},
    {"name": "Huge",       "alias": "Huge",      "rank": +2,
     "damage_mod": +10, "defence_mod": -4, "speed_mult": 1.5,
     "weight_mult": 12.0,
     "blurb": "Giant / wagon / small mecha scale."},
    {"name": "Gargantuan", "alias": "Gargantuan","rank": +3,
     "damage_mod": +20, "defence_mod": -6, "speed_mult": 2.0,
     "weight_mult": 40.0,
     "blurb": "Dragon / siege engine / mecha scale."},
    {"name": "Massive",    "alias": "Colossal",  "rank": +4,
     "damage_mod": +40, "defence_mod": -8, "speed_mult": 2.5,
     "weight_mult": 200.0,
     "blurb": "Kaiju / capital ship / fortress scale. Damage measured in structures."},
]

SIZE_BY_NAME = {s["name"]: s for s in SIZE_TEMPLATES}
DEFAULT_SIZE = "Medium"


# -------- Per-Attribute mod whitelists (BESM 4E) --------
# Most Attributes accept all 5 Enhancements + all 23 Limiters. A handful have
# rule-side restrictions or strong conventions. `None` = all mods allowed.
# A list = only the named mods make sense for that Attribute.
# These are advisory, surfaced as warnings in the Customise picker — not hard
# blocks (the GM Primer can override anything via custom rules).
ALL_ENHANCEMENTS = [e["name"] for e in ENHANCEMENTS]
ALL_LIMITERS = [lim["name"] for lim in LIMITERS]

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
        # Anime 5E is Dyskami's d20 / 5E-compatible system, distributed under
        # the OGL via the Tri-Stat Emporium community programme.
        "id": "anime-5e", "name": "Anime 5E", "publisher": "Dyskami Publishing",
        "edition": "v1.3.6", "year": 2024,
        "copyright": (
            "Anime 5E written by Mark MacKinnon. "
            "Anime 5E published by Dyskami Publishing Company with Japanime Games. "
            "Tri-Stat Emporium, Tri-Stat System, and Anime 5E are trademarks of "
            "Dyskami Publishing Company. Anime 5E text © {YEAR} Dyskami Publishing Company. "
            "All rights reserved under international law."
        ),
        "links": ["http://Anime5E.com"],
        # Anime 5E uses its own Tri-Stat Emporium logo (distinct from BESM 4E).
        # File served from /app/frontend/public/system-logos/.
        "logo_url": "/system-logos/anime5e-tristat-emporium.png",
        "supported": True,  # System is data-scaffolded V3.6; full Reference / Builder lands V3.7
        "blurb": "Open-licensed (OGL) d20 5E-compatible system tuned for anime / pulp action. Classes, races, and feats. Mechanics scaffolded — full reference & builder coming next batch.",
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
        "id": "cypher", "name": "Cypher System", "publisher": "Monte Cook Games",
        "edition": "Cypher System Rulebook", "year": 2015,
        # Required text per Monte Cook Games' Cypher System Creator programme.
        "copyright": (
            "This product was created under license. CYPHER SYSTEM and its logo, and "
            "CYPHER SYSTEM CREATOR and its logo, are trademarks of Monte Cook Games, LLC "
            "in the U.S.A. and other countries. All Monte Cook Games characters and "
            "character names, and the distinctive likenesses thereof, are trademarks of "
            "Monte Cook Games, LLC. www.montecookgames.com. "
            "This work contains material that is © Monte Cook Games, LLC and/or other "
            "authors, used with permission under the Community Content Agreement for "
            "Cypher System Creator. All other original material in this work is © {YEAR} "
            "by Table-Gnostic and published under the Community Content Agreement for "
            "Cypher System Creator."
        ),
        "links": ["https://www.montecookgames.com"],
        "supported": False,
        "blurb": "Player-tier d20 + modifier with effort/edge/intrusions; tier-based progression. The Cypher System Creator programme allows tool integrations like this one.",
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



# ──────────────────────────────────────────────────────────────────────────
# Expanded reference catalogues (BESM 4E core book)
# ──────────────────────────────────────────────────────────────────────────

# Combat / scene actions taxonomy (Chapter 8 — Combat)
ACTIONS = [
    {"name": "Standard Attack", "category": "Attack",
     "ap_cost": 1, "page": 178,
     "summary": "Roll 2d6+ATK vs target's DEF; on hit, deal Damage."},
    {"name": "Defend (Active)", "category": "Defence",
     "ap_cost": 0, "page": 180,
     "summary": "Use DEF + 2d6 to oppose an incoming attack."},
    {"name": "Block / Parry", "category": "Defence",
     "ap_cost": 1, "page": 180,
     "summary": "Spend an AP to gain +2 to next active defence."},
    {"name": "Move", "category": "Movement",
     "ap_cost": 1, "page": 178,
     "summary": "Cross your Movement value in metres on a single Move action."},
    {"name": "Sprint", "category": "Movement",
     "ap_cost": 2, "page": 178,
     "summary": "Cover up to 2× Movement; cannot make ranged attacks the same turn."},
    {"name": "Charge", "category": "Attack",
     "ap_cost": 2, "page": 179,
     "summary": "Move + melee attack at +1 ATK / -1 DEF until next turn."},
    {"name": "Aim", "category": "Modifier",
     "ap_cost": 1, "page": 179,
     "summary": "Stack +1 ATK on next ranged attack (max +3 over consecutive turns)."},
    {"name": "Dodge", "category": "Defence",
     "ap_cost": 1, "page": 180,
     "summary": "Move up to 1m and gain +2 DEF until your next turn."},
    {"name": "Grapple", "category": "Attack",
     "ap_cost": 1, "page": 181,
     "summary": "Body-vs-Body roll-under; success holds the target."},
    {"name": "Ranged Attack", "category": "Attack",
     "ap_cost": 1, "page": 182,
     "summary": "ATK + range modifier vs target DEF."},
    {"name": "Skill Check", "category": "Action",
     "ap_cost": 1, "page": 174,
     "summary": "2d6 + Stat + Skill vs Target Number."},
    {"name": "Recover", "category": "Action",
     "ap_cost": 2, "page": 183,
     "summary": "Regain (Mind+Soul) Energy Points; once per scene."},
    {"name": "Use Power Pack", "category": "Action",
     "ap_cost": "varies", "page": 73,  # BESM Extras
     "summary": "Activate a bundled Power Pack — see its trigger condition."},
]

# Companions / Henchmen / Servants (Chapter 5 — Attribute · Companion)
COMPANIONS = [
    {"name": "Henchman", "type": "Companion",
     "page": 88,
     "summary": "Single follower; allotted CP via Servant Attribute. "
                "Follows orders, may earn promotion."},
    {"name": "Servant", "type": "Companion",
     "page": 124,
     "summary": "Group / household / unit attached to the PC; CP per servant."},
    {"name": "Mecha / Vehicle", "type": "Companion",
     "page": 102,
     "summary": "Sentient or piloted construct treated as a Companion build."},
    {"name": "Mount / Animal", "type": "Companion",
     "page": 88,
     "summary": "Trained beast — bonded by Loyalty defect or Companion attribute."},
    {"name": "AI / Spirit", "type": "Companion",
     "page": 93,  # BESM Extras
     "summary": "Non-corporeal partner; Soul-only build, no Body."},
]

# Race templates — BESM 4E ships these as quick "kits"; users can extend.
# These cover only the *names + costs + page refs*, no rule prose.
RACE_TEMPLATES = [
    {"name": "Human (Standard)", "cp_cost": 0,  "page": 35,
     "summary": "Baseline 0-cost; no template attributes."},
    {"name": "Half-Demon",       "cp_cost": 8,  "page": 36,
     "summary": "+1 Body, Aura of Inhuman Beauty 1, Tough 1; Vow defect 1."},
    {"name": "Beastfolk",        "cp_cost": 6,  "page": 37,
     "summary": "Heightened Senses 2, Speed 1, Natural Weapons 1; Marked 1."},
    {"name": "Construct",        "cp_cost": 12, "page": 38,
     "summary": "Tough 2, Heavy Armour 1, Special Defence (Sleep, Poison) 2; Conditional Ownership 1."},
    {"name": "Faerie",           "cp_cost": 10, "page": 39,
     "summary": "Flight 1, Stealth 1, Resilience 1; Marked 1, Vulnerability (Iron) 1."},
    {"name": "Spirit (Bodiless)", "cp_cost": 14, "page": 40,
     "summary": "Insubstantial 1, Special Movement (Phasing), Heightened Awareness; Phys-Imp 1, Restricted Activities 1."},
    {"name": "Animal (Sentient)", "cp_cost": 4, "page": 41,
     "summary": "Heightened Senses 2, Speed 1; Awkward Size, Inept (Social) 1."},
    {"name": "Apprentice Artisan (Aurea)", "cp_cost": 4, "page": None,
     "summary": "Custom — Aurean apprentice race-template: Skill Group "
                "(Crafts) at Lvl 1, Wealth 1; Marked 1 (artisan brand). See Custom Catalogue."},
]

# Size modifiers — applied per-creature; SIZE_TEMPLATES already lists them
# above. This block is the consolidated Combat-effect table players reference
# during a fight (BESM 4E p.149 + Extras hp scaling p.32).
SIZE_MODIFIERS = [
    {"size": "Microscopic", "scale_metres": 0.0001, "atk_mod": -8,  "def_mod": +8,  "hp_mult": 0.05, "page": 149},
    {"size": "Tiny",        "scale_metres": 0.5,    "atk_mod": -4,  "def_mod": +4,  "hp_mult": 0.50, "page": 149},
    {"size": "Small",       "scale_metres": 1.5,    "atk_mod": -2,  "def_mod": +2,  "hp_mult": 0.75, "page": 149},
    {"size": "Medium",      "scale_metres": 2.0,    "atk_mod": 0,   "def_mod": 0,   "hp_mult": 1.00, "page": 149},
    {"size": "Large",       "scale_metres": 4.0,    "atk_mod": +2,  "def_mod": -2,  "hp_mult": 1.50, "page": 149},
    {"size": "Huge",        "scale_metres": 8.0,    "atk_mod": +4,  "def_mod": -4,  "hp_mult": 2.50, "page": 149},
    {"size": "Massive",     "scale_metres": 16.0,   "atk_mod": +6,  "def_mod": -6,  "hp_mult": 4.00, "page": 149},
    {"size": "Colossal",    "scale_metres": 32.0,   "atk_mod": +8,  "def_mod": -8,  "hp_mult": 6.00, "page": 149},
]

# Weapon table — names + class + damage; rules / page refs only.
WEAPONS = [
    {"name": "Dagger",          "class": "Light Melee",  "damage_mod": +5,  "concealable": True,  "page": 184},
    {"name": "Short Sword",     "class": "Melee",        "damage_mod": +10, "concealable": False, "page": 184},
    {"name": "Long Sword",      "class": "Melee",        "damage_mod": +15, "concealable": False, "page": 184},
    {"name": "Greatsword",      "class": "Heavy Melee",  "damage_mod": +20, "concealable": False, "page": 184},
    {"name": "Spear",           "class": "Melee/Reach",  "damage_mod": +12, "concealable": False, "page": 184},
    {"name": "Axe (One-handed)", "class": "Melee",       "damage_mod": +13, "concealable": False, "page": 184},
    {"name": "Hammer (Smith)",  "class": "Melee/Improv", "damage_mod": +12, "concealable": False, "page": 184},
    {"name": "Crossbow",        "class": "Ranged",       "damage_mod": +18, "range_m": 60, "page": 185},
    {"name": "Short Bow",       "class": "Ranged",       "damage_mod": +12, "range_m": 50, "page": 185},
    {"name": "Long Bow",        "class": "Ranged",       "damage_mod": +18, "range_m": 100, "page": 185},
    {"name": "Throwing Knife",  "class": "Thrown",       "damage_mod": +6,  "range_m": 10, "page": 185},
    {"name": "Pistol",          "class": "Firearm",      "damage_mod": +20, "range_m": 30, "page": 186},
    {"name": "Rifle",           "class": "Firearm",      "damage_mod": +30, "range_m": 200, "page": 186},
    {"name": "Pocket Lamp Burst (Custom)", "class": "Special / Item", "damage_mod": +0, "range_m": 5, "page": None,
     "note": "Aurea custom — Roney's pocket lamp; blinds Body-roll-under for 1d6 turns."},
]

# Items / common gear (non-weapon)
ITEMS_GEAR = [
    {"name": "Backpack",          "category": "Carry",      "page": 188},
    {"name": "Climbing Kit",      "category": "Tool",       "page": 188},
    {"name": "Lantern (Oil)",     "category": "Illumination", "page": 188},
    {"name": "Healer's Kit",      "category": "Medical",    "page": 188},
    {"name": "Smith's Toolset",   "category": "Crafting",   "page": 188},
    {"name": "Alchemy Bandolier", "category": "Crafting",   "page": None,
     "note": "Aurea custom — twelve-vial leather bandolier (Eli's signature kit)."},
    {"name": "Tinker Harness",    "category": "Crafting",   "page": None,
     "note": "Aurea custom — folding brass-frame harness (Roney's signature kit)."},
    {"name": "Forge Bellows (Folding)", "category": "Crafting", "page": None,
     "note": "Aurea custom — Laryk's travelling field-forge."},
    {"name": "Reagent Pouches",   "category": "Crafting",   "page": 188},
    {"name": "Spyglass",          "category": "Tool",       "page": 189},
    {"name": "Compass",           "category": "Tool",       "page": 189},
    {"name": "Iron Stakes (Bag)", "category": "Crafting",   "page": None,
     "note": "Aurea custom — set of forged stakes; barter currency among Ferrilith."},
]

# Armour table — names + AR + weight class; mechanics-only.
ARMOUR = [
    {"name": "Padded / Cloth",        "armour_rating": 4,  "weight_class": "Light",  "page": 190},
    {"name": "Leather Jerkin",        "armour_rating": 6,  "weight_class": "Light",  "page": 190},
    {"name": "Boiled Leather",        "armour_rating": 8,  "weight_class": "Medium", "page": 190},
    {"name": "Studded Leather",       "armour_rating": 9,  "weight_class": "Medium", "page": 190},
    {"name": "Chain Shirt",           "armour_rating": 12, "weight_class": "Medium", "page": 190},
    {"name": "Breastplate",           "armour_rating": 14, "weight_class": "Medium", "page": 190},
    {"name": "Banded Mail",           "armour_rating": 16, "weight_class": "Heavy",  "page": 190},
    {"name": "Plate Harness (Full)",  "armour_rating": 20, "weight_class": "Heavy",  "page": 190},
    {"name": "Smith's Apron (Aurea)", "armour_rating": 8,  "weight_class": "Light",  "page": None,
     "note": "Aurea custom — Laryk's hammered apron; Ferrilith-marked, not for sale outside the Order."},
    {"name": "Apothecary Coat",       "armour_rating": 4,  "weight_class": "Light",  "page": None,
     "note": "Aurea custom — vial-loops; +1 to Apocophae Discipline rolls when drawing in haste."},
]


# ──────────────────────────────────────────────────────────────────────────
# AUREA — Custom / Created BESM 4E content
#
# Magic system designed using BESM 4E core + BESM Extras as a worked example.
# All four Disciplines (Apocophae, Ferrilith, Techgnostic, Faunamimic) are
# expressed PURELY through BESM Attribute / Skill / Defect mechanics — no
# new sub-systems. This catalogue powers the Reference page's "Custom"
# subsection (toggle: Custom / Created → Attributes · Power Packs · Skills).
# ──────────────────────────────────────────────────────────────────────────

AUREA_CUSTOM_BOOK = "Aurea (Table-Gnostic original setting)"

# Custom-attribute subsection — adapted Attributes specific to Aurea's
# magic system. Each row maps onto an existing BESM attribute (so the
# cost engine doesn't change), with a setting-specific name and its
# enhancement / limiter intent recorded. These are TEACHING examples —
# GMs can copy the rows into their own custom_attributes for re-use.
AUREA_CUSTOM_ATTRIBUTES = [
    {"name": "Apothecary Tincture",
     "based_on": "Healing", "base_cost_per_level": 4,
     "enhancements_intent": ["Range (vial throw)", "Affects Incorporeal (purges curse)"],
     "limiters_intent":     ["Consumable (single dose)", "Restricted (prepared in advance)"],
     "discipline": "Apocophae",
     "summary": "Bottled tinctures — heal, purge, soothe. Cost is base × Level "
                "(BESM 4E rule); Limiters raise effective Level (more potent), "
                "Enhancements lower it (broader application)."},
    {"name": "Stone-Shape",
     "based_on": "Special Movement", "base_cost_per_level": 2,
     "enhancements_intent": ["Affects Others (carry party across raised stair)"],
     "limiters_intent":     ["Restricted (must touch worked stone)"],
     "discipline": "Ferrilith",
     "summary": "Coax slate / granite / basalt into stair, jack, or barrier — "
                "a movement / construction Attribute. Restricted to materials "
                "the Ferrilith has prayed over."},
    {"name": "Forge-Strike",
     "based_on": "Special Attack", "base_cost_per_level": 4,
     "enhancements_intent": ["Penetrating (Armour)", "Burning"],
     "limiters_intent":     ["Activation (must shout the Word)", "Limited Shots (3/scene)"],
     "discipline": "Ferrilith",
     "summary": "A struck blow that splits shield like kindling. Encodes the "
                "Ferrilith's vow of strength + a forge-fire effect."},
    {"name": "Cog-Insight",
     "based_on": "Cognition", "base_cost_per_level": 1,
     "enhancements_intent": ["Affects Others (read a partner's tool)"],
     "limiters_intent":     ["Restricted (mechanical objects only)"],
     "discipline": "Techgnostic",
     "summary": "Reads the linkages — gears, fluids, springs, hidden geometry."},
    {"name": "Pocket Detonation",
     "based_on": "Special Attack", "base_cost_per_level": 4,
     "enhancements_intent": ["Area Effect", "Stun (Mind)"],
     "limiters_intent":     ["Limited Shots (1/scene, must be rebuilt)"],
     "discipline": "Techgnostic",
     "summary": "Brass concussion horn — a one-shot, scene-changing detonation "
                "the Techgnostic builds during downtime."},
    {"name": "Wild Speech",
     "based_on": "Telepathy", "base_cost_per_level": 4,
     "enhancements_intent": ["Affects Others (entire pack/herd)"],
     "limiters_intent":     ["Restricted (animals only, not sapients)"],
     "discipline": "Faunamimic",
     "summary": "Wordless conversation with non-sapient animals; Faunamimic apologies "
                "and bargains are spoken in this register."},
    {"name": "Pelt-Shift",
     "based_on": "Alternate Form", "base_cost_per_level": 5,
     "enhancements_intent": ["Multiple Forms (elder + youth)"],
     "limiters_intent":     ["Activation (firelight required)", "Restricted (specific two forms only)"],
     "discipline": "Faunamimic",
     "summary": "The signature Faunamimic shift between an elder fur-clad form and "
                "a younger almost-human form. Always two forms, no more."},
    {"name": "Reagent-Sense",
     "based_on": "Heightened Senses", "base_cost_per_level": 1,
     "enhancements_intent": ["Range (50m)"],
     "limiters_intent":     ["Restricted (Apocophae herbs only)"],
     "discipline": "Apocophae",
     "summary": "Names a tincture by scent at five paces and a poison at three; "
                "Apocophae apprentices train this from year one."},
]

# Aurea-specific Power Packs (BESM Extras — Power Packs / Bundles, p.73-76).
# Each Pack is a narrative + mechanical bundle that tags an attribute
# combination by setting-source ("the Apocophae Field Kit"). These are the
# templates apprentice PCs roll with on day one.
AUREA_CUSTOM_POWER_PACKS = [
    {"name": "Apocophae's Field Kit",
     "discipline": "Apocophae",
     "components": ["Apothecary Tincture", "Reagent-Sense",
                    "Apocophae Discipline (Skill Group)"],
     "barter_value": "12 vials @ 1 prestige · 8-week tincture stock",
     "summary": "Glass-and-leather bandolier of tinctures, folding mortar-pestle, "
                "preserving wax tin, a folio of recipe cards in the master's hand."},
    {"name": "Ferrilith's Anvil",
     "discipline": "Ferrilith",
     "components": ["Forge-Strike", "Stone-Shape", "Heavy Armour",
                    "Ferrilith Discipline (Skill Group)"],
     "barter_value": "Iron stakes @ 1 prestige · Smith's apron @ 4 prestige",
     "summary": "Folding bellows, twin tongs, spike-hammer wrapped in oiled "
                "leather, and a pouch of iron stakes."},
    {"name": "Techgnost's Workbench",
     "discipline": "Techgnostic",
     "components": ["Item L8 (harness)", "Pocket Detonation", "Cog-Insight",
                    "Techgnostic Discipline (Skill Group)"],
     "barter_value": "Light burst @ 2 prestige · Springs @ 0.1 prestige each",
     "summary": "Canvas harness on a folding brass frame; pocket gadgets within "
                "easy reach: light burst, concussive instrument, half-finished prototypes."},
    {"name": "Faunamimic's Cloak",
     "discipline": "Faunamimic",
     "components": ["Pelt-Shift", "Wild Speech", "Heightened Senses",
                    "Skill Group (Wilderness)"],
     "barter_value": "Pelts barter only by direct apology — no prestige",
     "summary": "Patchwork pelts, traps, and a hand-bound book of animal-name "
                "syllables. Faunamimic packs are never sold — they are *given*."},
    {"name": "Apprentice's Carry-All (Generic)",
     "discipline": "All",
     "components": ["Item L4 (kit)", "Wealth 1", "Skill Group (Discipline) L1"],
     "barter_value": "Issue-standard 4-prestige kit",
     "summary": "The starter pack each apprentice walks out of the master's "
                "shop with on Maiden-Adventure dawn."},
]

# Aurea-specific Skills — extend SKILL_GROUPS with the four Disciplines
# as 2-pt/Lvl Lesser Groups (BESM 4E p.120 cost class).
AUREA_CUSTOM_SKILLS = [
    {"group": "Apocophae Discipline",  "tier": "Lesser Group", "cost_per_level": 2,
     "components": ["Foraging", "Brewing", "Diagnosis", "Reagent Lore"],
     "discipline": "Apocophae",
     "summary": "Gather, infuse, dose, dispense — every Apocophae apprentice's "
                "core kit. Each component starts at L1 when the Group is taken."},
    {"group": "Ferrilith Discipline",  "tier": "Lesser Group", "cost_per_level": 2,
     "components": ["Smithing", "Stone-Shaping", "Engineering", "Survivalist"],
     "discipline": "Ferrilith",
     "summary": "Shape stone, smith iron, raise wall and stair. The Ferrilith "
                "Lesser Group covers all four trades at L1."},
    {"group": "Techgnostic Discipline", "tier": "Lesser Group", "cost_per_level": 2,
     "components": ["Mechanics", "Tinkering", "Drafting", "Lockpicking"],
     "discipline": "Techgnostic",
     "summary": "Design, fabricate, repair, improvise. Drafting at L1 lets a "
                "Techgnostic write plans another artisan can build from."},
    {"group": "Faunamimic Discipline",  "tier": "Lesser Group", "cost_per_level": 2,
     "components": ["Tracking", "Trap-laying", "Animal Empathy", "Mimicry"],
     "discipline": "Faunamimic",
     "summary": "The wilderness craft of the Faunamimic. Animal Empathy is "
                "the bridge to Wild Speech; Mimicry is *not* for Sapients."},
    {"group": "Aurean Barter & Etiquette", "tier": "Lesser Group", "cost_per_level": 2,
     "components": ["Bartering", "Heraldry (Guild Sigils)", "Manners (Manor)",
                    "Reading Letters of Marque"],
     "discipline": "All",
     "summary": "The non-magical skill set every apprentice picks up on the road. "
                "Without it the Mayor will not even open the door."},
]

# Mechanics-only blurb explaining the rule we enforce in code.
AUREA_RULE_NOTE = (
    "BESM 4E rule (Mark MacKinnon, Dyskami primer): Enhancements and Limiters "
    "do NOT change point cost — they change EFFECTIVE LEVEL. "
    "Cost = assigned Level × Cost-per-Level. "
    "Effective Level = assigned Level + #Limiters − #Enhancements (≥ 1). "
    "All Aurea custom attributes obey this rule — the Apocophae's Apothecary "
    "Tincture with one Limiter (Consumable) functions one Level above its "
    "assigned cost, and one Enhancement (Range) drops it back. Stack "
    "Limiters for narrow but powerful tinctures."
)
