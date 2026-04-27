"""D&D 5E reference data — CC-BY SRD 5.1 / 5.2 mechanics only.

Every entry cites only mechanic names + page references. Flavour prose,
lore paragraphs, and class/race feature descriptions are deliberately
absent — GMs and players reference the SRD directly for those.
"""

BOOK = {
    "title": "D&D 5th Edition System Reference Document",
    "edition": "5.1 (CC-BY 4.0)",
    "publisher": "Wizards of the Coast LLC",
    "license": "CC-BY-4.0 — see LEGAL_COMPLIANCE.md",
}

# 12 SRD classes — name, hit die, primary ability, saving throw proficiencies,
# spellcasting type, and SRD page where the class is detailed.
CLASSES = [
    {"name": "Barbarian", "hit_die": 12, "primary": "Strength",
     "saves": ["Strength", "Constitution"], "casting": "none", "page": 4},
    {"name": "Bard", "hit_die": 8, "primary": "Charisma",
     "saves": ["Dexterity", "Charisma"], "casting": "full", "page": 8},
    {"name": "Cleric", "hit_die": 8, "primary": "Wisdom",
     "saves": ["Wisdom", "Charisma"], "casting": "full", "page": 14},
    {"name": "Druid", "hit_die": 8, "primary": "Wisdom",
     "saves": ["Intelligence", "Wisdom"], "casting": "full", "page": 22},
    {"name": "Fighter", "hit_die": 10, "primary": "Strength or Dexterity",
     "saves": ["Strength", "Constitution"], "casting": "none", "page": 28},
    {"name": "Monk", "hit_die": 8, "primary": "Dexterity & Wisdom",
     "saves": ["Strength", "Dexterity"], "casting": "none", "page": 32},
    {"name": "Paladin", "hit_die": 10, "primary": "Strength & Charisma",
     "saves": ["Wisdom", "Charisma"], "casting": "half", "page": 36},
    {"name": "Ranger", "hit_die": 10, "primary": "Dexterity & Wisdom",
     "saves": ["Strength", "Dexterity"], "casting": "half", "page": 40},
    {"name": "Rogue", "hit_die": 8, "primary": "Dexterity",
     "saves": ["Dexterity", "Intelligence"], "casting": "none", "page": 44},
    {"name": "Sorcerer", "hit_die": 6, "primary": "Charisma",
     "saves": ["Constitution", "Charisma"], "casting": "full", "page": 49},
    {"name": "Warlock", "hit_die": 8, "primary": "Charisma",
     "saves": ["Wisdom", "Charisma"], "casting": "pact", "page": 53},
    {"name": "Wizard", "hit_die": 6, "primary": "Intelligence",
     "saves": ["Intelligence", "Wisdom"], "casting": "full", "page": 58},
]

# 9 SRD races — name, ASI, size, speed, key traits, page.
RACES = [
    {"name": "Dwarf",       "asi": "+2 Con",            "size": "Medium", "speed": 25,
     "traits": ["Darkvision 60ft", "Dwarven Resilience", "Stonecunning"], "page": 64},
    {"name": "Elf",         "asi": "+2 Dex",            "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60ft", "Keen Senses", "Fey Ancestry", "Trance"], "page": 65},
    {"name": "Halfling",    "asi": "+2 Dex",            "size": "Small",  "speed": 25,
     "traits": ["Lucky", "Brave", "Halfling Nimbleness"], "page": 66},
    {"name": "Human",       "asi": "+1 to all",         "size": "Medium", "speed": 30,
     "traits": ["Versatile"], "page": 67},
    {"name": "Dragonborn",  "asi": "+2 Str / +1 Cha",   "size": "Medium", "speed": 30,
     "traits": ["Draconic Ancestry", "Breath Weapon", "Damage Resistance"], "page": 68},
    {"name": "Gnome",       "asi": "+2 Int",            "size": "Small",  "speed": 25,
     "traits": ["Darkvision 60ft", "Gnome Cunning"], "page": 69},
    {"name": "Half-Elf",    "asi": "+2 Cha / +1 +1",    "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60ft", "Fey Ancestry", "Skill Versatility"], "page": 70},
    {"name": "Half-Orc",    "asi": "+2 Str / +1 Con",   "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60ft", "Menacing", "Relentless Endurance", "Savage Attacks"], "page": 71},
    {"name": "Tiefling",    "asi": "+2 Cha / +1 Int",   "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60ft", "Hellish Resistance", "Infernal Legacy"], "page": 71},
]

# Six core abilities. Modifier formula: (score - 10) // 2.
ABILITIES = [
    {"name": "Strength",     "abbr": "STR"},
    {"name": "Dexterity",    "abbr": "DEX"},
    {"name": "Constitution", "abbr": "CON"},
    {"name": "Intelligence", "abbr": "INT"},
    {"name": "Wisdom",       "abbr": "WIS"},
    {"name": "Charisma",     "abbr": "CHA"},
]

# 18 SRD skills mapped to their associated ability.
SKILLS = [
    {"name": "Acrobatics",      "ability": "Dexterity"},
    {"name": "Animal Handling", "ability": "Wisdom"},
    {"name": "Arcana",          "ability": "Intelligence"},
    {"name": "Athletics",       "ability": "Strength"},
    {"name": "Deception",       "ability": "Charisma"},
    {"name": "History",         "ability": "Intelligence"},
    {"name": "Insight",         "ability": "Wisdom"},
    {"name": "Intimidation",    "ability": "Charisma"},
    {"name": "Investigation",   "ability": "Intelligence"},
    {"name": "Medicine",        "ability": "Wisdom"},
    {"name": "Nature",          "ability": "Intelligence"},
    {"name": "Perception",      "ability": "Wisdom"},
    {"name": "Performance",     "ability": "Charisma"},
    {"name": "Persuasion",      "ability": "Charisma"},
    {"name": "Religion",        "ability": "Intelligence"},
    {"name": "Sleight of Hand", "ability": "Dexterity"},
    {"name": "Stealth",         "ability": "Dexterity"},
    {"name": "Survival",        "ability": "Wisdom"},
]

# A representative SRD spell sample at every level 0-5. Each has its dice formula
# pre-stamped so the frontend can offer a one-click roll macro.
SPELLS = [
    # Cantrips
    {"name": "Fire Bolt",        "level": 0, "school": "Evocation",  "dice": "1d10 fire (+1d10/5lv)",   "range": "120 ft", "page": 242},
    {"name": "Sacred Flame",     "level": 0, "school": "Evocation",  "dice": "1d8 radiant (DEX save)",  "range": "60 ft",  "page": 273},
    {"name": "Eldritch Blast",   "level": 0, "school": "Evocation",  "dice": "1d10 force (+1 ray/5lv)", "range": "120 ft", "page": 237},
    {"name": "Mage Hand",        "level": 0, "school": "Conjuration", "dice": "—",                       "range": "30 ft",  "page": 256},
    # 1st level
    {"name": "Magic Missile",    "level": 1, "school": "Evocation",  "dice": "3 × (1d4+1) force",        "range": "120 ft", "page": 257},
    {"name": "Cure Wounds",      "level": 1, "school": "Evocation",  "dice": "1d8 + casting mod heal",   "range": "Touch",  "page": 230},
    {"name": "Burning Hands",    "level": 1, "school": "Evocation",  "dice": "3d6 fire (DEX save half)", "range": "15 ft cone", "page": 220},
    {"name": "Shield",           "level": 1, "school": "Abjuration", "dice": "+5 AC reaction",           "range": "Self",   "page": 275},
    {"name": "Healing Word",     "level": 1, "school": "Evocation",  "dice": "1d4 + casting mod heal",   "range": "60 ft",  "page": 250},
    # 2nd
    {"name": "Misty Step",       "level": 2, "school": "Conjuration", "dice": "Teleport 30 ft (BA)",     "range": "Self",   "page": 261},
    {"name": "Scorching Ray",    "level": 2, "school": "Evocation",  "dice": "3 × 2d6 fire (atk)",       "range": "120 ft", "page": 273},
    # 3rd
    {"name": "Fireball",         "level": 3, "school": "Evocation",  "dice": "8d6 fire (DEX save half)", "range": "150 ft", "page": 241},
    {"name": "Lightning Bolt",   "level": 3, "school": "Evocation",  "dice": "8d6 lightning (DEX save half)", "range": "100 ft line", "page": 255},
    {"name": "Counterspell",     "level": 3, "school": "Abjuration", "dice": "Auto if ≤3rd; else DC 10+slv", "range": "60 ft", "page": 228},
    # 4th
    {"name": "Polymorph",        "level": 4, "school": "Transmutation", "dice": "WIS save · CR ≤ target", "range": "60 ft", "page": 266},
    # 5th
    {"name": "Cone of Cold",     "level": 5, "school": "Evocation",  "dice": "8d8 cold (CON save half)", "range": "60 ft cone", "page": 224},
    {"name": "Hold Monster",     "level": 5, "school": "Enchantment", "dice": "WIS save · paralyzed",    "range": "90 ft", "page": 251},
]

# A representative SRD weapon sample with damage dice — drives the dice macros.
WEAPONS = [
    {"name": "Dagger",       "kind": "Simple Melee",   "damage": "1d4 piercing", "props": ["finesse", "light", "thrown 20/60"], "page": 149},
    {"name": "Shortsword",   "kind": "Martial Melee",  "damage": "1d6 piercing", "props": ["finesse", "light"], "page": 149},
    {"name": "Longsword",    "kind": "Martial Melee",  "damage": "1d8 slashing", "props": ["versatile (1d10)"], "page": 149},
    {"name": "Greatsword",   "kind": "Martial Melee",  "damage": "2d6 slashing", "props": ["heavy", "two-handed"], "page": 149},
    {"name": "Greataxe",     "kind": "Martial Melee",  "damage": "1d12 slashing", "props": ["heavy", "two-handed"], "page": 149},
    {"name": "Rapier",       "kind": "Martial Melee",  "damage": "1d8 piercing", "props": ["finesse"], "page": 149},
    {"name": "Quarterstaff", "kind": "Simple Melee",   "damage": "1d6 bludgeoning", "props": ["versatile (1d8)"], "page": 149},
    {"name": "Shortbow",     "kind": "Simple Ranged",  "damage": "1d6 piercing", "props": ["range 80/320", "two-handed"], "page": 149},
    {"name": "Longbow",      "kind": "Martial Ranged", "damage": "1d8 piercing", "props": ["heavy", "range 150/600", "two-handed"], "page": 149},
    {"name": "Light Crossbow", "kind": "Simple Ranged", "damage": "1d8 piercing", "props": ["loading", "range 80/320", "two-handed"], "page": 149},
    {"name": "Heavy Crossbow", "kind": "Martial Ranged", "damage": "1d10 piercing", "props": ["heavy", "loading", "range 100/400", "two-handed"], "page": 149},
    {"name": "Warhammer",    "kind": "Martial Melee",  "damage": "1d8 bludgeoning", "props": ["versatile (1d10)"], "page": 149},
    {"name": "Maul",         "kind": "Martial Melee",  "damage": "2d6 bludgeoning", "props": ["heavy", "two-handed"], "page": 149},
]

# Armor SRD sample.
ARMOR = [
    {"name": "Leather",       "category": "Light",  "ac": "11 + DEX", "stealth": "ok",         "page": 145},
    {"name": "Studded Leather", "category": "Light", "ac": "12 + DEX", "stealth": "ok",        "page": 145},
    {"name": "Chain Shirt",   "category": "Medium", "ac": "13 + DEX (max 2)", "stealth": "ok", "page": 145},
    {"name": "Half Plate",    "category": "Medium", "ac": "15 + DEX (max 2)", "stealth": "disadvantage", "page": 145},
    {"name": "Chain Mail",    "category": "Heavy",  "ac": "16",            "stealth": "disadvantage", "page": 145},
    {"name": "Plate",         "category": "Heavy",  "ac": "18",            "stealth": "disadvantage", "page": 145},
    {"name": "Shield",        "category": "Shield", "ac": "+2",            "stealth": "ok",   "page": 145},
]

# Adventuring gear sample.
ITEMS = [
    {"name": "Adventuring Pack", "cost": "—",   "weight": "varies", "page": 152},
    {"name": "Healer's Kit",      "cost": "5gp", "weight": "3 lb",   "page": 152, "uses": "10 charges · stabilise"},
    {"name": "Rope, Hempen 50ft", "cost": "1gp", "weight": "10 lb",  "page": 153},
    {"name": "Rations (1 day)",   "cost": "5sp", "weight": "2 lb",   "page": 153},
    {"name": "Spellbook",         "cost": "50gp","weight": "3 lb",   "page": 153},
    {"name": "Holy Symbol",       "cost": "5gp", "weight": "1 lb",   "page": 152},
    {"name": "Component Pouch",   "cost": "25gp","weight": "2 lb",   "page": 152},
]

# Conditions reference.
CONDITIONS = [
    {"name": "Blinded",     "effect": "Auto-fail sight checks · attacks vs. you adv · your atks dis"},
    {"name": "Charmed",     "effect": "Cannot attack charmer · charmer adv on social checks"},
    {"name": "Deafened",    "effect": "Cannot hear · auto-fail hearing checks"},
    {"name": "Frightened",  "effect": "Disadv on checks/atks while source in sight · cannot move closer"},
    {"name": "Grappled",    "effect": "Speed 0 · ends if grappler incap or moves out of reach"},
    {"name": "Incapacitated","effect": "No actions or reactions"},
    {"name": "Invisible",   "effect": "Heavily obscured · attacks vs. you dis · your atks adv"},
    {"name": "Paralyzed",   "effect": "Incapacitated · auto-fail STR/DEX saves · atks vs. you adv · melee crit"},
    {"name": "Petrified",   "effect": "Incapacitated · weight x10 · auto-fail STR/DEX · adv saves vs poison/disease"},
    {"name": "Poisoned",    "effect": "Disadv on attacks and ability checks"},
    {"name": "Prone",       "effect": "Crawl only · disadv on attacks · melee atks vs. you adv · ranged dis"},
    {"name": "Restrained",  "effect": "Speed 0 · disadv on atks/saves · atks vs. you adv"},
    {"name": "Stunned",     "effect": "Incapacitated · auto-fail STR/DEX saves · atks vs. you adv"},
    {"name": "Unconscious", "effect": "Incapacitated · prone · auto-fail STR/DEX · melee crit"},
]

# Action economy summary.
ACTIONS = [
    {"name": "Attack",       "kind": "Action",       "summary": "Make one weapon or unarmed attack."},
    {"name": "Cast a Spell", "kind": "varies",       "summary": "1 action / 1 bonus / 1 reaction / minutes per spell."},
    {"name": "Dash",         "kind": "Action",       "summary": "Gain extra movement = your speed."},
    {"name": "Disengage",    "kind": "Action",       "summary": "Movement does not provoke OAs this turn."},
    {"name": "Dodge",        "kind": "Action",       "summary": "Atks vs. you have disadv · DEX saves with adv."},
    {"name": "Help",         "kind": "Action",       "summary": "Ally has adv on next ability check or first atk."},
    {"name": "Hide",         "kind": "Action",       "summary": "Make a Stealth check vs. passive Perception."},
    {"name": "Ready",        "kind": "Action",       "summary": "Trigger a held action with reaction when condition met."},
    {"name": "Search",       "kind": "Action",       "summary": "Wisdom (Perception) or Intelligence (Investigation)."},
    {"name": "Use an Object","kind": "Action",       "summary": "Interact with an item beyond a free interaction."},
    {"name": "Opportunity Attack", "kind": "Reaction", "summary": "Foe leaves your reach without disengaging."},
]

# Power-level analogue: starting level brackets that map into BESM-shaped tiers
# so the campaign-create modal can offer Heroic / Adventurous / Cosmic equivalents.
POWER_LEVELS = [
    {"name": "Apprentice", "level_range": "1-2",   "blurb": "Local stakes, single town"},
    {"name": "Heroic",     "level_range": "3-5",   "blurb": "Regional stakes, named villains"},
    {"name": "Champion",   "level_range": "6-10",  "blurb": "Kingdom-scale, magical artefacts"},
    {"name": "Master",     "level_range": "11-16", "blurb": "Continental, planar excursions"},
    {"name": "Mythic",     "level_range": "17-20", "blurb": "World/cosmic stakes, godlike foes"},
]

REFERENCE = {
    "system_id": "dnd-5e",
    "kind": "class-and-slot",  # selector-driven, not point-buy
    "book": BOOK,
    "abilities": ABILITIES,
    "classes": CLASSES,
    "races": RACES,
    "skills": SKILLS,
    "spells": SPELLS,
    "weapons": WEAPONS,
    "armor": ARMOR,
    "items": ITEMS,
    "conditions": CONDITIONS,
    "actions": ACTIONS,
    "power_levels": POWER_LEVELS,
    "modifier_formula": "(score - 10) // 2",
    "proficiency_by_level": [2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6],
    "rule_note": (
        "D&D 5E uses class + level + slot mechanics. Roll d20 + ability mod + "
        "proficiency (if proficient) vs. DC. Critical hit on natural 20 doubles "
        "weapon damage dice. Content here is mechanic-only per CC-BY SRD 5.1."
    ),
}
