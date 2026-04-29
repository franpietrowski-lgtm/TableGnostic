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
    {"name": "Adept",      "primary": "Mind", "hit_die": 8,  "blurb_role": "Caster · psychic",
     "origin": "anime-5e",
     "saves": ["Mind", "Soul"]},
    {"name": "Champion",   "primary": "Body", "hit_die": 12, "blurb_role": "Front-line warrior",
     "origin": "anime-5e",
     "saves": ["Body", "Mind"]},
    {"name": "Idol",       "primary": "Soul", "hit_die": 6,  "blurb_role": "Face · charm caster",
     "origin": "anime-5e",
     "saves": ["Soul", "Mind"]},
    {"name": "Pilot",      "primary": "Mind", "hit_die": 8,  "blurb_role": "Mecha / vehicle",
     "origin": "anime-5e",
     "saves": ["Mind", "Body"]},
    {"name": "Tinker",     "primary": "Mind", "hit_die": 8,  "blurb_role": "Item-crafter · gadgeteer",
     "origin": "anime-5e",
     "saves": ["Mind", "Soul"]},

    # ─── D&D 5E SRD imports (CC-BY 4.0). Reshape: 5E ability names
    # remain (so the dnd_state folio is compatible), and we tag origin
    # so the UI can badge "5E-import · Tri-Stat layerable" — GMs may
    # grant D&D-class PCs a Tri-Stat point budget via the hybrid
    # supplement card on the sheet.
    {"name": "Barbarian", "hit_die": 12, "primary": "Strength",
     "saves": ["Strength", "Constitution"], "casting": "none", "origin": "dnd-5e-srd",
     "blurb_role": "Rage-fuelled frontline berserker (SRD 5.1)"},
    {"name": "Bard", "hit_die": 8, "primary": "Charisma",
     "saves": ["Dexterity", "Charisma"], "casting": "full", "origin": "dnd-5e-srd",
     "blurb_role": "Charisma full-caster · inspirer · jack-of-skills (SRD 5.1)"},
    {"name": "Cleric", "hit_die": 8, "primary": "Wisdom",
     "saves": ["Wisdom", "Charisma"], "casting": "full", "origin": "dnd-5e-srd",
     "blurb_role": "Divine full-caster · healer · buffer (SRD 5.1)"},
    {"name": "Druid", "hit_die": 8, "primary": "Wisdom",
     "saves": ["Intelligence", "Wisdom"], "casting": "full", "origin": "dnd-5e-srd",
     "blurb_role": "Nature full-caster · wild-shaper (SRD 5.1)"},
    {"name": "Fighter", "hit_die": 10, "primary": "Strength or Dexterity",
     "saves": ["Strength", "Constitution"], "casting": "none", "origin": "dnd-5e-srd",
     "blurb_role": "Weapon specialist · Second Wind / Action Surge (SRD 5.1)"},
    {"name": "Monk", "hit_die": 8, "primary": "Dexterity & Wisdom",
     "saves": ["Strength", "Dexterity"], "casting": "none", "origin": "dnd-5e-srd",
     "blurb_role": "Ki-fuelled martial artist · mobile striker (SRD 5.1)"},
    {"name": "Paladin", "hit_die": 10, "primary": "Strength & Charisma",
     "saves": ["Wisdom", "Charisma"], "casting": "half", "origin": "dnd-5e-srd",
     "blurb_role": "Half-caster · smite · aura support (SRD 5.1)"},
    {"name": "Ranger", "hit_die": 10, "primary": "Dexterity & Wisdom",
     "saves": ["Strength", "Dexterity"], "casting": "half", "origin": "dnd-5e-srd",
     "blurb_role": "Half-caster · skirmisher · favored enemy (SRD 5.1)"},
    {"name": "Rogue", "hit_die": 8, "primary": "Dexterity",
     "saves": ["Dexterity", "Intelligence"], "casting": "none", "origin": "dnd-5e-srd",
     "blurb_role": "Sneak Attack · expertise · evasion (SRD 5.1)"},
    {"name": "Sorcerer", "hit_die": 6, "primary": "Charisma",
     "saves": ["Constitution", "Charisma"], "casting": "full", "origin": "dnd-5e-srd",
     "blurb_role": "Innate caster · metamagic · sorcery points (SRD 5.1)"},
    {"name": "Warlock", "hit_die": 8, "primary": "Charisma",
     "saves": ["Wisdom", "Charisma"], "casting": "pact", "origin": "dnd-5e-srd",
     "blurb_role": "Pact-caster · invocations · short-rest slots (SRD 5.1)"},
    {"name": "Wizard", "hit_die": 6, "primary": "Intelligence",
     "saves": ["Intelligence", "Wisdom"], "casting": "full", "origin": "dnd-5e-srd",
     "blurb_role": "Prepared full-caster · spellbook · Arcane Recovery (SRD 5.1)"},
]

# Eight genre-anchored race / heritage templates available without 5E setting baggage.
HERITAGES = [
    {"name": "Human",       "asi": "+1 to all", "size": "Medium", "speed": 30, "origin": "anime-5e"},
    {"name": "Beastfolk",   "asi": "+2 Body / +1 Soul", "size": "Medium", "speed": 30, "origin": "anime-5e",
     "traits": ["Animal Sense", "Natural Weapon"]},
    {"name": "Construct",   "asi": "+2 Body / +1 Mind", "size": "Medium", "speed": 30, "origin": "anime-5e",
     "traits": ["Tireless", "Resilient", "Repair (vs. Heal)"]},
    {"name": "Half-Demon",  "asi": "+2 Soul / +1 Body", "size": "Medium", "speed": 30, "origin": "anime-5e",
     "traits": ["Darkvision", "Hellbrand"]},
    {"name": "Faerie",      "asi": "+2 Soul / +1 Mind", "size": "Small", "speed": 25, "origin": "anime-5e",
     "traits": ["Glamour", "Iron-bane"]},
    {"name": "Spirit",      "asi": "+2 Mind / +1 Soul", "size": "Medium", "speed": 30, "origin": "anime-5e",
     "traits": ["Incorporeal Step", "Ethereal Sight"]},
    {"name": "Animal",      "asi": "+2 Body",            "size": "Small/Medium", "speed": 40, "origin": "anime-5e",
     "traits": ["Bestial Form", "Limited Speech"]},
    {"name": "Apprentice",  "asi": "+1 / +1 / +1",       "size": "Medium", "speed": 30, "origin": "anime-5e",
     "traits": ["Versatile", "Mentor's Boon"]},

    # ─── D&D 5E SRD races (CC-BY 4.0). Names / ASI / speed retained
    # so existing D&D-shape folios import cleanly. Anime 5E GMs may
    # retexture flavour (e.g. "Dwarf" becomes "Mountain Clan Osmite")
    # without changing mechanics.
    {"name": "Dwarf",       "asi": "+2 Con",            "size": "Medium", "speed": 25, "origin": "dnd-5e-srd",
     "traits": ["Darkvision 60 ft", "Dwarven Resilience", "Stonecunning"]},
    {"name": "Elf",         "asi": "+2 Dex",            "size": "Medium", "speed": 30, "origin": "dnd-5e-srd",
     "traits": ["Darkvision 60 ft", "Keen Senses", "Fey Ancestry", "Trance"]},
    {"name": "Halfling",    "asi": "+2 Dex",            "size": "Small",  "speed": 25, "origin": "dnd-5e-srd",
     "traits": ["Lucky", "Brave", "Halfling Nimbleness"]},
    {"name": "Dragonborn",  "asi": "+2 Str / +1 Cha",   "size": "Medium", "speed": 30, "origin": "dnd-5e-srd",
     "traits": ["Breath Weapon", "Draconic Ancestry", "Damage Resistance"]},
    {"name": "Gnome",       "asi": "+2 Int",            "size": "Small",  "speed": 25, "origin": "dnd-5e-srd",
     "traits": ["Darkvision 60 ft", "Gnome Cunning"]},
    {"name": "Half-Elf",    "asi": "+2 Cha / +1+1",     "size": "Medium", "speed": 30, "origin": "dnd-5e-srd",
     "traits": ["Darkvision 60 ft", "Fey Ancestry", "Skill Versatility"]},
    {"name": "Half-Orc",    "asi": "+2 Str / +1 Con",   "size": "Medium", "speed": 30, "origin": "dnd-5e-srd",
     "traits": ["Darkvision 60 ft", "Relentless Endurance", "Savage Attacks"]},
    {"name": "Tiefling",    "asi": "+2 Cha / +1 Int",   "size": "Medium", "speed": 30, "origin": "dnd-5e-srd",
     "traits": ["Darkvision 60 ft", "Hellish Resistance", "Infernal Legacy"]},
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

# Genre backgrounds — 8 anime tropes turned into 5E-shape backgrounds.
BACKGROUNDS = [
    {"name": "Honor Student",  "skills": ["History", "Investigation"],
     "tools": ["Calligrapher's set"], "languages": "one of choice",
     "feature": "Top of the Class — academic doors open without question",
     "page_role": "Slice-of-life / school"},
    {"name": "Idol Trainee",   "skills": ["Performance", "Persuasion"],
     "tools": ["Disguise kit", "Musical instrument (one)"], "languages": "—",
     "feature": "Stage Pass — fans recognise & assist when role is on-mode",
     "page_role": "Pop-star arc"},
    {"name": "Mech Pilot Cadet", "skills": ["Athletics", "Investigation"],
     "tools": ["Vehicles (mecha)", "Tinker's tools"], "languages": "—",
     "feature": "Sortie Authorisation — military bay access on duty",
     "page_role": "Mecha"},
    {"name": "Wandering Swordsman", "skills": ["Athletics", "Survival"],
     "tools": ["Vehicles (land)"], "languages": "—",
     "feature": "Folk Tale — a village will shelter you for one night",
     "page_role": "Shōnen action"},
    {"name": "Magical Trainee", "skills": ["Arcana", "Insight"],
     "tools": ["Calligrapher's set"], "languages": "one of choice",
     "feature": "Familiar Bond — you began with a low-power familiar",
     "page_role": "Magical girl"},
    {"name": "Cyberpunk Runner", "skills": ["Sleight of Hand", "Stealth"],
     "tools": ["Hacker's kit", "Thieves' tools"], "languages": "Hex-cant",
     "feature": "Side Job — black-market liaison who answers a single message",
     "page_role": "Cyberpunk"},
    {"name": "Spirit Medium",   "skills": ["Insight", "Religion"],
     "tools": ["Calligrapher's set"], "languages": "Spirit-tongue",
     "feature": "Veil-Walker — sense the local spirit population",
     "page_role": "Supernatural"},
    {"name": "Otherworlder",    "skills": ["Survival", "Perception"],
     "tools": ["Vehicles (land or air)"], "languages": "you remember Earth-tongue",
     "feature": "Out-of-Place — common knowledge often surprises you, occasionally to your benefit",
     "page_role": "Isekai"},
]

# Defects — a Tri-Stat point-buy concept. Each Defect gives BACK points.
DEFECTS = [
    {"name": "Awkward",        "rebate_per_level": 1, "blurb_role": "−1 to social rolls per level"},
    {"name": "Bane",           "rebate_per_level": 1, "blurb_role": "Susceptibility to a substance / phenomenon"},
    {"name": "Conditional Power", "rebate_per_level": 1, "blurb_role": "Powers only function when X"},
    {"name": "Easily Distracted", "rebate_per_level": 1, "blurb_role": "Specific stimulus pulls focus"},
    {"name": "Marked",         "rebate_per_level": 1, "blurb_role": "Conspicuous tattoo / aura / mark"},
    {"name": "Owned by Another", "rebate_per_level": 2, "blurb_role": "Bound to a NPC's bidding"},
    {"name": "Phobia",         "rebate_per_level": 1, "blurb_role": "Specific terror provokes flight"},
    {"name": "Skeleton in Closet", "rebate_per_level": 2, "blurb_role": "Hidden secret weaponizable by GM"},
]

# Equipment items — anime gadget kit.
ITEMS = [
    {"name": "Power Limiter Bracelet",  "cost": "—",       "weight": "0.2 lb",
     "uses": "Suppresses an Attribute by one level until removed. Plot-keyed."},
    {"name": "Bento Box (3 meals)",      "cost": "1 sp",    "weight": "1 lb",
     "uses": "Restore 1d4 hp on a short rest, once per day, when shared."},
    {"name": "Walkman / Earbuds",        "cost": "5 sp",    "weight": "0.1 lb",
     "uses": "Cue music for a Spotlit moment (DM Intrusion candy)."},
    {"name": "Spirit-Sealing Ofuda",     "cost": "1 gp",    "weight": "0.1 lb",
     "uses": "Adhered to a surface, blocks low-tier spirit passage 1 hour."},
    {"name": "Mecha Repair Kit",         "cost": "50 gp",   "weight": "10 lb",
     "uses": "Restore 2d10 hp to a vehicle/mecha during a long rest."},
    {"name": "Idol Concert Pass",        "cost": "10 gp",   "weight": "—",
     "uses": "Grants social entry to one venue/event."},
    {"name": "Charm Bracelet (Familiar Bond)", "cost": "—", "weight": "0.1 lb",
     "uses": "Resummon a banished familiar (1/long rest)."},
    {"name": "Cyberdeck (Light)",         "cost": "200 gp", "weight": "2 lb",
     "uses": "+5 to Hacker checks; can run one daemon at a time."},
    {"name": "Schoolyard Bokken",         "cost": "5 sp",   "weight": "2 lb",
     "uses": "1d6 bludgeoning · counts as a 'safe' weapon for school settings."},
    {"name": "Ration Box (1 week)",       "cost": "5 gp",   "weight": "8 lb",
     "uses": "Travel sustenance · fan-service convention warm-up rolls."},
]

# Anime 5E uses the SRD spell-slot table (full for Adept, half for Pilot/Tinker,
# none for Champion/Idol — Idol uses Soul-driven Performance abilities instead).
# We re-export an alias here so the front-end can pick the right table by class.
CLASS_CASTING = {
    "Adept":    "full",
    "Champion": "none",
    "Idol":     "none",      # Idol uses Soul-stunts, not slots
    "Pilot":    "half",
    "Tinker":   "half",
}

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
    "backgrounds": BACKGROUNDS,
    "skills": SKILLS,
    "spells": SPELLS,
    "weapons": WEAPONS,
    "armor": ARMOR,
    "items": ITEMS,
    "conditions": CONDITIONS,
    "power_levels": POWER_LEVELS,
    "point_buy_attributes": POINT_BUY_ATTRIBUTES,
    "defects": DEFECTS,
    "class_casting": CLASS_CASTING,
    "modifier_formula": "(score - 10) // 2",
    "rule_note": (
        "Anime 5E supports BOTH 5E class+slot play AND Tri-Stat point-buy. "
        "Roll d20 + ability mod + proficiency for class-mode, OR 2d6 + Stat "
        "+ Attribute Level for point-buy mode. GM picks the engine in the "
        "campaign Primer. Mechanic-only content per the OGL/Tri-Stat Emporium release."
    ),
}
