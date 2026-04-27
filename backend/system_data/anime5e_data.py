"""Anime 5E reference data — Tri-Stat Emporium OGL release.

Anime 5E is published under both the Cypher CC-BY-style OGL and stands as
its own point-buy d20 hybrid (the Tri-Stat point engine grafted onto a 5E
chassis). The Reference page exposes BOTH shapes so a GM can run it as
either a stand-alone or a 5E supplement.

Mechanic names + page references only. No reproduced flavour prose.
"""

BOOK = {
    "title": "Anime 5E SRD v1.01",
    "publisher": "Mark MacKinnon · Dyskami Publishing Company",
    "license": "OGL — A Tri-Stat Emporium System",
    "page_range_max": 200,
}

# Cross-system tag so D&D-5E settings can opt in to Anime 5E supplement use.
CROSS_SYSTEMS = ["dnd-5e"]

# Anime 5E uses the BESM 4E Body / Mind / Soul tri-stat grafted onto a d20 chassis.
ABILITIES = [
    {"name": "Body",  "abbr": "BOD"},
    {"name": "Mind",  "abbr": "MND"},
    {"name": "Soul",  "abbr": "SOL"},
]

# Five archetypal classes — the Anime 5E shapes its classes around genre roles.
CLASSES = [
    {"name": "Adept",      "primary": "Mind", "hit_die": 8,  "blurb_role": "Caster · psychic"},
    {"name": "Champion",   "primary": "Body", "hit_die": 12, "blurb_role": "Front-line warrior"},
    {"name": "Idol",       "primary": "Soul", "hit_die": 6,  "blurb_role": "Face · charm caster"},
    {"name": "Pilot",      "primary": "Mind", "hit_die": 8,  "blurb_role": "Mecha / vehicle"},
    {"name": "Tinker",     "primary": "Mind", "hit_die": 8,  "blurb_role": "Item-crafter · gadgeteer"},
]

# Eight genre-anchored race / heritage templates available without 5E setting baggage.
HERITAGES = [
    {"name": "Human",       "asi": "+1 to all", "size": "Medium"},
    {"name": "Beastfolk",   "asi": "+2 Body / +1 Soul", "size": "Medium",
     "traits": ["Animal Sense", "Natural Weapon"]},
    {"name": "Construct",   "asi": "+2 Body / +1 Mind", "size": "Medium",
     "traits": ["Tireless", "Resilient", "Repair (vs. Heal)"]},
    {"name": "Half-Demon",  "asi": "+2 Soul / +1 Body", "size": "Medium",
     "traits": ["Darkvision", "Hellbrand"]},
    {"name": "Faerie",      "asi": "+2 Soul / +1 Mind", "size": "Small",
     "traits": ["Glamour", "Iron-bane"]},
    {"name": "Spirit",      "asi": "+2 Mind / +1 Soul", "size": "Medium",
     "traits": ["Incorporeal Step", "Ethereal Sight"]},
    {"name": "Animal",      "asi": "+2 Body",            "size": "Small/Medium",
     "traits": ["Bestial Form", "Limited Speech"]},
    {"name": "Apprentice",  "asi": "+1 / +1 / +1",       "size": "Medium",
     "traits": ["Versatile", "Mentor's Boon"]},
]

# A point-buy attribute engine layered on top so a GM can run Anime 5E in
# its native Tri-Stat mode — same shape as BESM 4E.
POINT_BUY_ATTRIBUTES = [
    {"name": "Combat Mastery",  "cost_per_level": 2, "blurb_role": "+1 to-hit per level"},
    {"name": "Heightened Sense","cost_per_level": 1, "blurb_role": "Sharpened sight/hearing/scent"},
    {"name": "Massive Damage",  "cost_per_level": 4, "blurb_role": "+5 damage per level"},
    {"name": "Mind Control",    "cost_per_level": 6, "blurb_role": "Compel target action"},
    {"name": "Personal Gear",   "cost_per_level": 1, "blurb_role": "Curated equipment"},
    {"name": "Ranged Attack",   "cost_per_level": 4, "blurb_role": "Custom ranged weapon"},
    {"name": "Special Movement","cost_per_level": 1, "blurb_role": "Wall-climb · water-walk · gliding"},
    {"name": "Tough",           "cost_per_level": 2, "blurb_role": "+5 HP per level"},
    {"name": "Wealth",          "cost_per_level": 1, "blurb_role": "Material affluence"},
]

# 18 5E-aligned skill names re-mapped to Body / Mind / Soul.
SKILLS = [
    {"name": "Acrobatics",      "ability": "Body"},
    {"name": "Athletics",       "ability": "Body"},
    {"name": "Stealth",         "ability": "Body"},
    {"name": "Sleight of Hand", "ability": "Body"},
    {"name": "Arcana",          "ability": "Mind"},
    {"name": "History",         "ability": "Mind"},
    {"name": "Investigation",   "ability": "Mind"},
    {"name": "Medicine",        "ability": "Mind"},
    {"name": "Nature",          "ability": "Mind"},
    {"name": "Religion",        "ability": "Mind"},
    {"name": "Animal Handling", "ability": "Soul"},
    {"name": "Insight",         "ability": "Soul"},
    {"name": "Perception",      "ability": "Soul"},
    {"name": "Survival",        "ability": "Soul"},
    {"name": "Deception",       "ability": "Soul"},
    {"name": "Intimidation",    "ability": "Soul"},
    {"name": "Performance",     "ability": "Soul"},
    {"name": "Persuasion",      "ability": "Soul"},
]

# Genre-flavoured spell sample — keeps to mechanic-only.
SPELLS = [
    {"name": "Aerial Strike",   "level": 0, "school": "Conjuration", "dice": "1d6 force",        "range": "60 ft"},
    {"name": "Resonance Touch", "level": 0, "school": "Evocation",   "dice": "1d6 sonic",        "range": "Touch"},
    {"name": "Magical Energy",  "level": 1, "school": "Evocation",   "dice": "3d4 force",        "range": "120 ft"},
    {"name": "Shielding Aura",  "level": 1, "school": "Abjuration",  "dice": "+5 AC reaction",   "range": "Self"},
    {"name": "Healing Light",   "level": 1, "school": "Evocation",   "dice": "1d8 + lvl heal",   "range": "Touch"},
    {"name": "Combat Sutra",    "level": 2, "school": "Transmutation","dice": "+1d6 weapon dmg", "range": "Self"},
    {"name": "Genre Pulse",     "level": 3, "school": "Evocation",   "dice": "8d6 chosen-type",  "range": "150 ft"},
    {"name": "Stage Reset",     "level": 5, "school": "Conjuration", "dice": "Battlefield reposition", "range": "60 ft"},
]

# Weapons — anime-flavoured. Damage is 5E-shaped.
WEAPONS = [
    {"name": "Katana",          "kind": "Martial Melee",  "damage": "1d10 slashing", "props": ["versatile (1d12)"]},
    {"name": "Wakizashi",       "kind": "Martial Melee",  "damage": "1d6 slashing",  "props": ["finesse", "light"]},
    {"name": "Naginata",        "kind": "Martial Melee",  "damage": "1d10 piercing", "props": ["reach", "two-handed"]},
    {"name": "Kusarigama",      "kind": "Martial Melee",  "damage": "1d6 slashing",  "props": ["reach", "finesse", "trip"]},
    {"name": "Bow, Yumi",       "kind": "Martial Ranged", "damage": "1d8 piercing",  "props": ["heavy", "range 150/600", "two-handed"]},
    {"name": "Shuriken",        "kind": "Martial Ranged", "damage": "1d4 piercing",  "props": ["finesse", "light", "thrown 20/60"]},
    {"name": "Concept Blade",   "kind": "Soulbound Melee","damage": "2d6 force",     "props": ["soulbound", "versatile (2d8)"]},
    {"name": "Mecha Cannon",    "kind": "Vehicle Ranged", "damage": "4d10 force",    "props": ["heavy", "vehicle-mount", "range 300/1200"]},
]

# Armour
ARMOR = [
    {"name": "School Uniform (reinforced)", "category": "Light",  "ac": "11 + DEX (cap 4)", "stealth": "ok"},
    {"name": "Idol Stage Garb",             "category": "Light",  "ac": "11 + SOL mod",     "stealth": "ok"},
    {"name": "Pilot Suit",                  "category": "Medium", "ac": "13 + DEX (max 2)", "stealth": "ok"},
    {"name": "Cyber Mail",                  "category": "Medium", "ac": "14 + DEX (max 2)", "stealth": "ok"},
    {"name": "Spirit Plate",                "category": "Heavy",  "ac": "17",               "stealth": "ok"},
    {"name": "Mecha Frame",                 "category": "Vehicle","ac": "18 + pilot mod",   "stealth": "disadvantage"},
]

# Conditions — same as 5E but the genre adds three.
CONDITIONS = [
    {"name": "Genre-Locked", "effect": "Cannot break the campaign tone — invokes GM Intrusion."},
    {"name": "Spotlit",      "effect": "+1 to one roll · ends after a turn unused."},
    {"name": "Eclipsed",     "effect": "Lose Reaction · ends at start of your next turn."},
]

# Power-level brackets aligned to 5E levels but flagged as Tri-Stat tiers too.
POWER_LEVELS = [
    {"name": "Slice-of-Life",  "level_range": "1-2",   "blurb": "Personal stakes, school setting"},
    {"name": "Adventurous",    "level_range": "3-5",   "blurb": "Town · regional stakes"},
    {"name": "Heroic",         "level_range": "6-10",  "blurb": "Nationwide · named villains"},
    {"name": "Mythic",         "level_range": "11-16", "blurb": "Continental · cosmic"},
    {"name": "Cosmic",         "level_range": "17-20", "blurb": "Multiverse · godlike opposition"},
]

REFERENCE = {
    "system_id": "anime-5e",
    "kind": "hybrid",  # both class+slot AND point-buy
    "book": BOOK,
    "cross_systems": CROSS_SYSTEMS,
    "abilities": ABILITIES,
    "classes": CLASSES,
    "heritages": HERITAGES,
    "skills": SKILLS,
    "spells": SPELLS,
    "weapons": WEAPONS,
    "armor": ARMOR,
    "conditions": CONDITIONS,
    "power_levels": POWER_LEVELS,
    "point_buy_attributes": POINT_BUY_ATTRIBUTES,
    "modifier_formula": "(score - 10) // 2",
    "rule_note": (
        "Anime 5E supports BOTH 5E class+slot play AND Tri-Stat point-buy. "
        "Roll d20 + ability mod + proficiency for class-mode, OR 2d6 + Stat "
        "+ Attribute Level for point-buy mode. GM picks the engine in the "
        "campaign Primer. Mechanic-only content per the OGL/Tri-Stat Emporium release."
    ),
}
