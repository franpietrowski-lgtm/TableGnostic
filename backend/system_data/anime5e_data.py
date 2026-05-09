"""Anime 5E reference data — D&D 5E + BESM-style point-buy hybrid.

CORRECT FRAMING (per the official Anime 5E hybrid release):
  • Anime 5E is essentially D&D 5E with a BESM-style optional point-buy
    LAYER on top for genre-flavour customisation.
  • It DOES NOT use Tri-Stat ability scores. The d20 chassis runs
    Strength / Dexterity / Constitution / Intelligence / Wisdom /
    Charisma exactly as in 5E.
  • The port is one-way: D&D SRD races, classes, feats, and
    backgrounds import directly into Anime 5E. Anime 5E content
    (point-buy attributes / defects) does NOT port back to a
    strict-5E table.
  • The point-buy layer is OPTIONAL — a GM can run a campaign with
    pure 5E + Anime 5E races/classes and never touch the point engine.

We keep a `tri_stat_legacy_abilities` list internally for migration of
older characters that were built before this clarification, but new
characters should use the standard D&D 5E ability score block.
"""

BOOK = {
    "title": "Anime 5E SRD v1.01",
    "publisher": "Mark MacKinnon · Dyskami Publishing Company",
    "license": "OGL — D&D 5E + BESM-style point-buy hybrid",
    "page_range_max": 200,
}

# Cross-system tag so D&D-5E settings can opt in to Anime 5E supplement use.
CROSS_SYSTEMS = ["dnd-5e"]

# Anime 5E ability scores ARE the standard 5E six. Body/Mind/Soul are
# retained ONLY for migration of characters built under the previous
# (incorrect) Tri-Stat framing; new sheets use the d20 SRD set.
ABILITIES = [
    {"name": "Strength",      "abbr": "STR"},
    {"name": "Dexterity",     "abbr": "DEX"},
    {"name": "Constitution",  "abbr": "CON"},
    {"name": "Intelligence",  "abbr": "INT"},
    {"name": "Wisdom",        "abbr": "WIS"},
    {"name": "Charisma",      "abbr": "CHA"},
]
TRI_STAT_LEGACY_ABILITIES = [
    {"name": "Body",  "abbr": "BOD"},
    {"name": "Mind",  "abbr": "MND"},
    {"name": "Soul",  "abbr": "SOL"},
]

# Anime 5E original classes — these layer onto the d20 chassis with
# point-buy genre flavour. Saves use the standard 5E six abilities.
CLASSES = [
    {"name": "Adept",      "primary": "Wisdom", "hit_die": 8,  "blurb_role": "Caster · psychic",
     "origin": "anime-5e",
     "saves": ["Wisdom", "Charisma"]},
    {"name": "Champion",   "primary": "Strength", "hit_die": 12, "blurb_role": "Front-line warrior",
     "origin": "anime-5e",
     "saves": ["Strength", "Constitution"]},
    {"name": "Idol",       "primary": "Charisma", "hit_die": 6,  "blurb_role": "Face · charm caster",
     "origin": "anime-5e",
     "saves": ["Charisma", "Wisdom"]},
    {"name": "Pilot",      "primary": "Intelligence", "hit_die": 8,  "blurb_role": "Mecha / vehicle",
     "origin": "anime-5e",
     "saves": ["Intelligence", "Dexterity"]},
    {"name": "Tinker",     "primary": "Intelligence", "hit_die": 8,  "blurb_role": "Item-crafter · gadgeteer",
     "origin": "anime-5e",
     "saves": ["Intelligence", "Wisdom"]},

    # ─── D&D 5E SRD imports (CC-BY 4.0). The 5E ability score block
    # is the same one Anime 5E uses, so these import directly. The
    # `origin` tag lets the UI badge "5E-import · BESM-layerable" —
    # GMs may grant D&D-class PCs a BESM-style point-buy budget via
    # the optional supplement card on the sheet.
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

# V6.25.15 — Canonical Anime 5E Attributes table (core book p.91-130).
# Each entry is the official approved attribute name + Character-Point
# cost-per-level + a short non-rulebook descriptive blurb categorising
# the mechanic. Ranks are open-ended unless noted; Lesser variants pay
# fewer points but with stricter scope.
#
# Cost-per-level === total CP that one rank of the attribute consumes.
# Page references point at the Anime 5E core rulebook entry that
# defines the attribute's full mechanic.
POINT_BUY_ATTRIBUTES = [
    # ── Combat ────────────────────────────────────────────────────────
    {"name": "AC Bonus",            "cost_per_level": 1, "page": 92,  "category": "combat",
     "blurb_role": "Bonus to Armor Class (harder to hit)"},
    {"name": "Armour Proficiency",  "cost_per_level": 1, "page": 92,  "category": "combat",
     "blurb_role": "Proficiency with an armour category — drops the penalties"},
    {"name": "Combat Mastery",      "cost_per_level": 1, "page": 93,  "category": "combat",
     "blurb_role": "+1 attack-roll bonus per Rank"},
    {"name": "Combat Technique",    "cost_per_level": 1, "page": 94,  "category": "combat",
     "blurb_role": "One special combat manoeuvre per Rank"},
    {"name": "Edge",                "cost_per_level": 1, "page": 100, "category": "combat",
     "blurb_role": "Advantage on a narrow class of dice rolls"},
    {"name": "Extra Actions",       "cost_per_level": 4, "page": 101, "category": "combat",
     "blurb_role": "One additional un-restricted action per round"},
    {"name": "Extra Actions – Lesser", "cost_per_level": 2, "page": 101, "category": "combat",
     "blurb_role": "One extra non-attack / non-spell action per round"},
    {"name": "Forced Disadvantage", "cost_per_level": 1, "page": 102, "category": "combat",
     "blurb_role": "Imposes Disadvantage on enemies opposing you"},
    {"name": "Massive Damage",      "cost_per_level": 3, "page": 106, "category": "combat",
     "blurb_role": "Extra damage on attacks meeting a trigger condition"},
    {"name": "Massive Damage – Lesser", "cost_per_level": 1, "page": 106, "category": "combat",
     "blurb_role": "Extra damage on a narrow class of attacks"},

    # ── Defensive ─────────────────────────────────────────────────────
    {"name": "Immunity",            "cost_per_level": 3, "page": 103, "category": "defensive",
     "blurb_role": "Complete immunity to a chosen damage type or effect"},
    {"name": "Immunity – Lesser",   "cost_per_level": 1, "page": 103, "category": "defensive",
     "blurb_role": "Resistance (½ damage) to a chosen damage type"},
    {"name": "Immutable",           "cost_per_level": 1, "page": 104, "category": "defensive",
     "blurb_role": "Bonus to resist transform / displace / alter effects"},
    {"name": "Protected",           "cost_per_level": 1, "page": 111, "category": "defensive",
     "blurb_role": "Reduces damage from a specific attack type"},
    {"name": "Resilient",           "cost_per_level": 1, "page": 112, "category": "defensive",
     "blurb_role": "Adapts to survive a hostile environment"},

    # ── Mental ────────────────────────────────────────────────────────
    {"name": "Augmented",           "cost_per_level": 1, "page": 92,  "category": "mental",
     "blurb_role": "Boost one Ability Score above species cap"},
    {"name": "Cognition",           "cost_per_level": 2, "page": 93,  "category": "mental",
     "blurb_role": "Pre-cognition or post-cognition glimpses"},
    {"name": "Enhanced Proficiency", "cost_per_level": 2, "page": 101, "category": "mental",
     "blurb_role": "Bonus to your Proficiency Bonus in a focused area"},
    {"name": "Heightened Senses",   "cost_per_level": 1, "page": 102, "category": "mental",
     "blurb_role": "Sharpens one or more senses beyond mortal range"},
    {"name": "Language",            "cost_per_level": 1, "page": 105, "category": "mental",
     "blurb_role": "An additional spoken / signed language per Rank"},
    {"name": "Mind Shield",         "cost_per_level": 1, "page": 108, "category": "mental",
     "blurb_role": "Bonus to resist mental intrusion / domination"},
    {"name": "Saving Throw Proficiency", "cost_per_level": 2, "page": 112, "category": "mental",
     "blurb_role": "Adds Proficiency Bonus to one Ability's saves"},
    {"name": "Sixth Sense",         "cost_per_level": 1, "page": 112, "category": "mental",
     "blurb_role": "Detect a chosen hidden phenomenon (danger / magic / etc.)"},
    {"name": "Skill Proficiency",   "cost_per_level": 1, "page": 113, "category": "mental",
     "blurb_role": "Proficiency in one additional skill"},
    {"name": "Supersense",          "cost_per_level": 2, "page": 118, "category": "mental",
     "blurb_role": "One sense functions far beyond normal humanoid range"},

    # ── Physical ──────────────────────────────────────────────────────
    {"name": "Elasticity",          "cost_per_level": 2, "page": 100, "category": "physical",
     "blurb_role": "Stretch limbs / body to superhuman lengths"},
    {"name": "Fast",                "cost_per_level": 1, "page": 101, "category": "physical",
     "blurb_role": "Doubles base movement speed per Rank"},
    {"name": "Flight",              "cost_per_level": 3, "page": 102, "category": "physical",
     "blurb_role": "Aerial movement (winged / magic / tech)"},
    {"name": "Jumping",             "cost_per_level": 1, "page": 105, "category": "physical",
     "blurb_role": "Greatly increased jump distance and safe landings"},
    {"name": "Regeneration",        "cost_per_level": 1, "page": 112, "category": "physical",
     "blurb_role": "+1 HP recovered per Rank per round"},
    {"name": "Size Change",         "cost_per_level": 5, "page": 112, "category": "physical",
     "blurb_role": "Grow or shrink one Size Rank per Rank"},
    {"name": "Size Change – Lesser", "cost_per_level": 4, "page": 112, "category": "physical",
     "blurb_role": "Grow OR shrink (one direction only) per Rank"},
    {"name": "Special Movement",    "cost_per_level": 1, "page": 116, "category": "physical",
     "blurb_role": "One unconventional movement type per Rank"},
    {"name": "Speedburst",          "cost_per_level": 2, "page": 116, "category": "physical",
     "blurb_role": "Brief burst of vastly increased speed"},

    # ── Social ────────────────────────────────────────────────────────
    {"name": "Alternate Identity",  "cost_per_level": 1, "page": 92,  "category": "social",
     "blurb_role": "One distinct alternate persona per Rank"},
    {"name": "Companion",           "cost_per_level": 5, "page": 95,  "category": "social",
     "blurb_role": "Loyal NPC / pet sidekick with its own stat block"},
    {"name": "Connected",           "cost_per_level": 1, "page": 98,  "category": "social",
     "blurb_role": "Membership / favour with an organisation"},
    {"name": "Inspire",             "cost_per_level": 1, "page": 104, "category": "social",
     "blurb_role": "Buff allies' ability / skill checks via leadership"},
    {"name": "Inspire – Greater",   "cost_per_level": 3, "page": 104, "category": "social",
     "blurb_role": "Inspire bonus also covers attack rolls + saves"},
    {"name": "Minions",             "cost_per_level": 2, "page": 108, "category": "social",
     "blurb_role": "Loyal humanoid retinue eager for orders"},
    {"name": "Minions – Greater",   "cost_per_level": 4, "page": 108, "category": "social",
     "blurb_role": "More capable / more numerous Minions"},
    {"name": "Monster Training",    "cost_per_level": 1, "page": 108, "category": "social",
     "blurb_role": "Train and improve pet monsters"},

    # ── Supernatural ──────────────────────────────────────────────────
    {"name": "Change State",        "cost_per_level": 3, "page": 92,  "category": "supernatural",
     "blurb_role": "Briefly transform body to liquid / gas / incorporeal"},
    {"name": "Control Environment", "cost_per_level": 1, "page": 98,  "category": "supernatural",
     "blurb_role": "Subtle control over a small area's conditions"},
    {"name": "Conversion",          "cost_per_level": 3, "page": 98,  "category": "supernatural",
     "blurb_role": "Convert damage taken into temp boosts to other Attributes"},
    {"name": "Dynamic Powers",      "cost_per_level": 10, "page": 99, "category": "supernatural",
     "blurb_role": "Major bender-style elemental / ideological control"},
    {"name": "Dynamic Powers – Lesser", "cost_per_level": 5, "page": 99, "category": "supernatural",
     "blurb_role": "Narrow scoped Dynamic Powers (one minor category)"},
    {"name": "Energised",           "cost_per_level": 1, "page": 101, "category": "supernatural",
     "blurb_role": "Larger Energy pool for ability use"},
    {"name": "Mimic",               "cost_per_level": 4, "page": 106, "category": "supernatural",
     "blurb_role": "Briefly copy another character's Attribute or Ability Score"},
    {"name": "Mind Control",        "cost_per_level": 3, "page": 106, "category": "supernatural",
     "blurb_role": "Mentally dominate creatures by touch"},
    {"name": "Mind Control – Lesser", "cost_per_level": 1, "page": 107, "category": "supernatural",
     "blurb_role": "Suggest narrow actions to a narrow class of targets"},
    {"name": "Nullify",             "cost_per_level": 5, "page": 110, "category": "supernatural",
     "blurb_role": "Temporarily render another's Attribute unusable"},
    {"name": "Portal",              "cost_per_level": 5, "page": 111, "category": "supernatural",
     "blurb_role": "Open dimensional portals for travel"},
    {"name": "Spell Amplification", "cost_per_level": 1, "page": 116, "category": "supernatural",
     "blurb_role": "Modify a spell's area / range / duration / components"},
    {"name": "Spell-Like Ability",  "cost_per_level": 1, "page": 117, "category": "supernatural",
     "blurb_role": "Cast a chosen spell as if a class spellcaster"},
    {"name": "Telepathy",           "cost_per_level": 3, "page": 118, "category": "supernatural",
     "blurb_role": "Read / send thoughts and influence memories"},
    {"name": "Telepathy – Lesser",  "cost_per_level": 1, "page": 119, "category": "supernatural",
     "blurb_role": "Telepathy with a narrow target class (e.g. own pet)"},
    {"name": "Teleport",            "cost_per_level": 5, "page": 119, "category": "supernatural",
     "blurb_role": "Instantaneously move to a different location"},

    # ── Utility ───────────────────────────────────────────────────────
    {"name": "Features",            "cost_per_level": 1, "page": 101, "category": "utility",
     "blurb_role": "Minor situational advantages (one per Rank)"},
    {"name": "Healing",             "cost_per_level": 1, "page": 102, "category": "utility",
     "blurb_role": "Touch-restore Hit Points to a target"},
    {"name": "Item",                "cost_per_level": 4, "page": 105, "category": "utility",
     "blurb_role": "Signature item that contains its own Attributes (½ cost)"},
    {"name": "Mulligan",            "cost_per_level": 1, "page": 110, "category": "utility",
     "blurb_role": "Re-roll dice a limited number of times per session"},
    {"name": "Pocket Dimension",    "cost_per_level": 2, "page": 110, "category": "utility",
     "blurb_role": "Personal extra-planar storage / sanctum"},
    {"name": "Wealth",              "cost_per_level": 3, "page": 121, "category": "utility",
     "blurb_role": "Ladder of material affluence (Frugal → Filthy Rich)"},
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
    {"name": "Idol Stage Garb",             "category": "Light",  "ac": "11 + CHA mod",     "stealth": "ok"},
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

# Defects — a BESM-style point-buy concept. Each Defect gives BACK points.
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

# V6.25.32 — Anime 5E reference parity expansion. Pulls SUBCLASSES /
# FEATS / TOOLS / LANGUAGES / MAGIC_ITEMS / MONSTERS / DAMAGE_TYPES /
# SCHOOLS from the sibling `anime5e_extended` module so the Anime 5E
# Reference page reaches feature-parity with the D&D 5E one. Anime 5E
# re-uses the SRD pool (one-way port, CC-BY 4.0) and adds anime-flavoured
# originals (henshin pendants, kaiju, transformation feats, idol mics).
from .anime5e_extended import (  # noqa: E402
    SUBCLASSES, FEATS, TOOLS, LANGUAGES, MAGIC_ITEMS, MONSTERS,
    DAMAGE_TYPES, SCHOOLS, CLASS_FEATURES,
)
# V6.25.35 — Otherworldly Patrons + Pacts + Invocations + anime
# demon-folk heritages. Shared module so D&D 5E + Anime 5E don't
# duplicate canon.
from .patrons_pacts import (  # noqa: E402
    PATRONS as _PATRONS,
    PACTS as _PACTS,
    INVOCATIONS as _INVOCATIONS,
    DEMON_HERITAGES as _DEMON_HERITAGES,
)


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
    # V6.25.32 — extended reference parity with D&D 5E.
    "subclasses":     SUBCLASSES,
    "feats":          FEATS,
    "tools":          TOOLS,
    "languages":      LANGUAGES,
    "magic_items":    MAGIC_ITEMS,
    "monsters":       MONSTERS,
    "damage_types":   DAMAGE_TYPES,
    "schools":        SCHOOLS,
    "class_features": CLASS_FEATURES,
    # V6.25.35 — Patrons / Pacts / Invocations (Warlock canon shared
    # with D&D 5E) + anime-specific demon-folk heritages on top of the
    # SRD heritage roster so the Reference page exposes Tieflings /
    # Half-Demons / Cursed Bloodlines / Oni-blooded / Hellspawn /
    # Spirit-Touched without polluting the core HERITAGES list.
    "patrons":         _PATRONS,
    "pacts":           _PACTS,
    "invocations":     _INVOCATIONS,
    "demon_heritages": _DEMON_HERITAGES,
    "modifier_formula": "(score - 10) // 2",
    "rule_note": (
        "Anime 5E is D&D 5E + an OPTIONAL BESM-style point-buy LAYER. "
        "Roll d20 + ability mod + proficiency for everything — class, "
        "level, hit dice, AC, and saves are pure 5E. The point-buy "
        "layer is OPTIONAL flavour: spend a budget on signature genre "
        "powers (Combat Mastery, Heightened Senses, Personal Gear, "
        "Custom Technique). The port is one-way — D&D SRD races / "
        "classes / feats / backgrounds import directly into Anime 5E; "
        "Anime 5E content does NOT port back to a strict-5E table."
    ),
}
