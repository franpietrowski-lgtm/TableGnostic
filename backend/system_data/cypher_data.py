"""Cypher System reference data — Cypher System Creator licence.

Mechanic names + page references only — no reproduced flavour prose, lore,
type/focus paragraph descriptions, or numbered cypher-effect prose.

Cypher System core dice mechanic: roll a single d20 ≥ (3 × difficulty).
Difficulty 1-10. Effort, Edge, and Skills lower difficulty by 1 step each.
"""

BOOK = {
    "title": "Cypher System Reference (Cypher System Creator programme)",
    "publisher": "Monte Cook Games, LLC",
    "license": "Cypher System Creator — community content licence",
    "page_range_max": 400,
    # Settings the Creator licence EXPLICITLY allows full content for.
    "creator_full_settings": [
        "Godforsaken", "Gods of the Fall", "Masters of the Night",
        "Predation", "The Heartwood", "The Revel", "Unmasked",
    ],
    # Settings that Creators may CITE for compatibility but NOT duplicate.
    "creator_compat_only": [
        "Claim the Sky", "First Responders", "Stay Alive!", "The Origin",
        "The Stars Are Fire", "We Are All Mad Here",
    ],
    # Settings explicitly FORBIDDEN under the Creator licence.
    "forbidden_settings": ["Numenera", "The Strange", "No Thank You, Evil!"],
    # Required cover text + product-description text per the licence.
    "required_cover_line": (
        "Requires the Cypher System Rulebook from Monte Cook Games. "
        "Distributed through the Cypher System Creator™ at DriveThruRPG."
    ),
    "required_product_desc_line": (
        "Requires the Cypher System Rulebook from Monte Cook Games."
    ),
}

# Three core stat pools — the Cypher engine.
STAT_POOLS = [
    {"name": "Might",        "blurb_role": "Physical force · vigor"},
    {"name": "Speed",        "blurb_role": "Quickness · reflexes"},
    {"name": "Intellect",    "blurb_role": "Mental acuity · learning"},
]

# Six SRD types — Cypher's "classes" — with structured starting pools so the
# builder can auto-fill on Type change. The three numbers are the SRD "extra"
# pool points the player ADDS to a baseline of 7 across all three pools (so
# Warrior 8/8/2 = 15/15/9 starting pools).
TYPES = [
    {"name": "Warrior",        "intrusion": "Combat",   "starting_pools": "Might+8 / Speed+8 / Intellect+2",
     "pool_offsets": {"Might": 8, "Speed": 8, "Intellect": 2}, "edge_at_1": ["Might 1"],
     "starting_edge": {"Might": 1, "Speed": 0, "Intellect": 0}, "starting_cypher_limit": 2},
    {"name": "Adept",          "intrusion": "Esoteric", "starting_pools": "Might+2 / Speed+8 / Intellect+8",
     "pool_offsets": {"Might": 2, "Speed": 8, "Intellect": 8}, "edge_at_1": ["Intellect 1"],
     "starting_edge": {"Might": 0, "Speed": 0, "Intellect": 1}, "starting_cypher_limit": 3},
    {"name": "Explorer",       "intrusion": "Recovery", "starting_pools": "Might+6 / Speed+6 / Intellect+6",
     "pool_offsets": {"Might": 6, "Speed": 6, "Intellect": 6}, "edge_at_1": ["Might 1 OR Speed 1"],
     "starting_edge": {"Might": 1, "Speed": 0, "Intellect": 0}, "starting_cypher_limit": 2},
    {"name": "Speaker",        "intrusion": "Social",   "starting_pools": "Might+4 / Speed+4 / Intellect+8",
     "pool_offsets": {"Might": 4, "Speed": 4, "Intellect": 8}, "edge_at_1": ["Intellect 1"],
     "starting_edge": {"Might": 0, "Speed": 0, "Intellect": 1}, "starting_cypher_limit": 2},
    {"name": "Wright",         "intrusion": "Crafting", "starting_pools": "Might+4 / Speed+8 / Intellect+8",
     "pool_offsets": {"Might": 4, "Speed": 8, "Intellect": 8}, "edge_at_1": ["Speed 1 OR Intellect 1"],
     "starting_edge": {"Might": 0, "Speed": 0, "Intellect": 1}, "starting_cypher_limit": 3},
    {"name": "Paradox",        "intrusion": "Reality",  "starting_pools": "Might+0 / Speed+8 / Intellect+12",
     "pool_offsets": {"Might": 0, "Speed": 8, "Intellect": 12}, "edge_at_1": ["Intellect 2"],
     "starting_edge": {"Might": 0, "Speed": 0, "Intellect": 2}, "starting_cypher_limit": 4},
]

# Pool baseline added to every Type — SRD "every PC starts with 7 in each pool".
POOL_BASELINE = 7

# Tier-based mechanics — recovery rolls per day and cypher carry limit.
# Recoveries: 1 action + 10 min + 1 hr + 10 hr per day at Tier 1; +1 step per
# tier when modifier added by some types/foci. (SRD recovery rolls.)
TIER_DERIVED = {
    "recoveries_per_day": {1: 4, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4},
    "recovery_die": {1: "1d6+1", 2: "1d6+2", 3: "1d6+3",
                      4: "1d6+4", 5: "1d6+5", 6: "1d6+6"},
}

# Genre / setting tags. Used by the front-end to filter Descriptors / Foci /
# Equipment lists when a campaign declares its `setting_genre`. Setting names
# follow the Cypher SRD's listed genres — the LIBRARY-LEGAL settings shipped
# in the core book. Forbidden settings (Numenera, Strange, NTYE, etc.) are
# blocked from BRANDED PDF export elsewhere, but the genre filter itself
# applies to whatever setting the GM selects.
SETTING_GENRES = [
    {"key": "fantasy",     "label": "Fantasy",      "blurb": "Sword & sorcery, swords and spells"},
    {"key": "modern",      "label": "Modern",       "blurb": "Contemporary thriller / horror / urban"},
    {"key": "post",        "label": "Post-Apocalypse", "blurb": "Aftermath / scavenger / weird-tech"},
    {"key": "scifi",       "label": "Science-Fiction", "blurb": "Space-opera, cyber, hard-SF"},
    {"key": "horror",      "label": "Horror",       "blurb": "Cosmic horror, occult investigation"},
    {"key": "superhero",   "label": "Superhero",    "blurb": "Capes / masks / city-scale"},
    {"key": "historical",  "label": "Historical",   "blurb": "Period game with one fantastical lever"},
    {"key": "any",         "label": "Genre-Agnostic", "blurb": "All Descriptors / Foci available"},
]


# 16 SRD descriptors — flavour-flag for backstory + 1 Edge or Skill bonus.
# The `genres` tag lists the genres the descriptor fits naturally; the front-
# end uses this to narrow the picker when a setting is declared. An empty /
# missing tag list means the descriptor is genre-agnostic.
DESCRIPTORS = [
    {"name": "Brash",       "genres": ["fantasy", "modern", "post", "scifi", "superhero"]},
    {"name": "Charming",    "genres": ["fantasy", "modern", "scifi", "superhero", "historical"]},
    {"name": "Clever",      "genres": ["any"]},
    {"name": "Doomed",      "genres": ["fantasy", "horror", "post"]},
    {"name": "Empathic",    "genres": ["modern", "scifi", "superhero", "historical"]},
    {"name": "Graceful",    "genres": ["fantasy", "modern", "scifi", "historical"]},
    {"name": "Hideous",     "genres": ["horror", "post"]},
    {"name": "Impulsive",   "genres": ["any"]},
    {"name": "Intelligent", "genres": ["any"]},
    {"name": "Mystical",    "genres": ["fantasy", "horror", "superhero"]},
    {"name": "Mysterious",  "genres": ["fantasy", "horror", "modern", "post", "superhero"]},
    {"name": "Resilient",   "genres": ["any"]},
    {"name": "Stealthy",    "genres": ["fantasy", "modern", "post", "scifi", "superhero", "historical"]},
    {"name": "Swift",       "genres": ["any"]},
    {"name": "Tough",       "genres": ["any"]},
    {"name": "Vicious",     "genres": ["fantasy", "post", "horror"]},
]

# 18 SRD foci — name + sentence-fragment role + genre tags.
FOCI = [
    {"name": "Bears a Halo of Fire",       "role": "Burns nearby foes · area zones",
     "genres": ["fantasy", "horror", "superhero"]},
    {"name": "Carries a Quiver",            "role": "Ranged archery specialist",
     "genres": ["fantasy", "post", "historical"]},
    {"name": "Commands Mental Might",       "role": "Telepathy · psionic blasts",
     "genres": ["scifi", "superhero", "horror"]},
    {"name": "Conducts Weird Science",      "role": "Improvised cyphers · gadgets",
     "genres": ["scifi", "post", "modern", "superhero"]},
    {"name": "Crafts Illusions",            "role": "Visual / auditory deceptions",
     "genres": ["fantasy", "horror", "modern", "superhero"]},
    {"name": "Crafts Unique Objects",       "role": "Item creation · workshop bonuses",
     "genres": ["any"]},
    {"name": "Defends the Weak",            "role": "Tank · ally protection",
     "genres": ["any"]},
    {"name": "Entertains",                  "role": "Charisma · audience-buff",
     "genres": ["fantasy", "modern", "scifi", "historical", "superhero"]},
    {"name": "Exists Partially Out of Phase","role": "Phase shift · selective intangibility",
     "genres": ["scifi", "horror", "superhero"]},
    {"name": "Explores Dark Places",        "role": "Stealth · subterranean expertise",
     "genres": ["fantasy", "post", "horror", "modern"]},
    {"name": "Fights with Panache",         "role": "Duellist · improvised reposte",
     "genres": ["fantasy", "modern", "historical", "superhero"]},
    {"name": "Howls at the Moon",           "role": "Shapeshift · primal form",
     "genres": ["fantasy", "horror", "superhero"]},
    {"name": "Leads",                       "role": "Allies act as if Trained",
     "genres": ["any"]},
    {"name": "Masters Defense",             "role": "Armor · Speed defense",
     "genres": ["any"]},
    {"name": "Masters Weaponry",            "role": "Weapon-mastery · combat finesse",
     "genres": ["any"]},
    {"name": "Murders",                     "role": "Stealth strikes · finishers",
     "genres": ["fantasy", "modern", "horror", "post"]},
    {"name": "Wields Two Weapons at Once",  "role": "Twin-blade · split-attack",
     "genres": ["fantasy", "post", "scifi", "modern"]},
    {"name": "Works Miracles",              "role": "Divine intervention · faith effects",
     "genres": ["fantasy", "horror", "historical"]},
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
    "pool_baseline": POOL_BASELINE,
    "tier_derived": TIER_DERIVED,
    "setting_genres": SETTING_GENRES,
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



# ─── V6.25.23 — Foundational Cypher data for Cycle B ──────────────────

COMPATIBILITY_NOTICE = (
    "Compatible with the Cypher System per the Cypher System Open "
    "License (CSOL 2022). Mechanics are referenced by name; full "
    "rules text is not reproduced — see your Cypher System Rulebook "
    "or the SRD for canonical wording."
)


GENRES = [
    {"key": "fantasy",         "name": "Fantasy",
     "blurb": "Magic, myth, and adventure in a world of swords and sorcery."},
    {"key": "modern",          "name": "Modern",
     "blurb": "Contemporary settings — espionage, urban thrillers, slice-of-life with a twist."},
    {"key": "science-fiction", "name": "Science Fiction",
     "blurb": "Spaceships, alien worlds, and far-future technology."},
    {"key": "superheroes",     "name": "Superheroes",
     "blurb": "Powers, capes, and four-colour heroics."},
    {"key": "horror",          "name": "Horror",
     "blurb": "Dread, the unknown, and what hunts at the edge of the lamplight."},
    {"key": "post-apocalyptic","name": "Post-Apocalyptic",
     "blurb": "Survival in a broken world — scrap, faith, and salvage."},
    {"key": "fairy-tale",      "name": "Fairy Tale",
     "blurb": "Story-logic worlds where wishes have weight and woods listen."},
    {"key": "historical",      "name": "Historical",
     "blurb": "Real-world periods played straight or with a Cypher tilt."},
]


TIER_PROGRESSION = [
    {"tier": 1, "max_effort": 1,
     "blurb": "First-tier characters: novice but capable, rough around the edges."},
    {"tier": 2, "max_effort": 2,
     "blurb": "Second-tier characters: seasoned, with one signature trick mastered."},
    {"tier": 3, "max_effort": 3,
     "blurb": "Third-tier characters: respected veterans with multiple specialities."},
    {"tier": 4, "max_effort": 4,
     "blurb": "Fourth-tier characters: regional luminaries — name dropped in tavern songs."},
    {"tier": 5, "max_effort": 5,
     "blurb": "Fifth-tier characters: world-class talents who reshape their corner of the setting."},
    {"tier": 6, "max_effort": 6,
     "blurb": "Sixth-tier characters: legends — campaign-defining figures, capable of mythic feats."},
]


ADVANCEMENT_STEPS_PER_TIER = [
    {"key": "increasing-capabilities", "name": "Increasing Capabilities", "xp_cost": 4,
     "effect": "Add 4 points distributed among your stat Pools (no more than 2 to any single Pool)."},
    {"key": "moving-toward-perfection", "name": "Moving Toward Perfection", "xp_cost": 4,
     "effect": "Add 1 point of Edge to any stat."},
    {"key": "extra-effort", "name": "Extra Effort", "xp_cost": 4,
     "effect": "Increase your maximum Effort by 1."},
    {"key": "skill-training", "name": "Skill Training", "xp_cost": 4,
     "effect": "Become trained in a skill, or upgrade a trained skill to specialised."},
]


CYPHER_TYPES_FULL = [
    {
        "key": "warrior", "name": "Warrior",
        "role_blurb": "Action-first front-liners who solve problems with steel, speed, and trained instinct.",
        "starting_stat_pools": {"Might": 11, "Speed": 10, "Intellect": 8},
        "starting_edge":       {"Might": 1, "Speed": 0, "Intellect": 0},
        "free_pool_points":    6, "starting_effort": 1, "starting_cypher_limit": 2,
        "abilities_by_tier": {
            "1": ["Bash","Combat Prowess","Control the Field","Improved Edge","No Need for Weapons","Overwatch","Physical Skills","Practiced in Armor","Quick Throw","Swipe","Trained Without Armor"],
            "2": ["Crushing Blow","Hemorrhage","Reload","Skill With Attacks","Skill With Defense","Successive Attack"],
            "3": ["Deadly Aim","Energy Resistance","Experienced in Armor","Expert Cypher Use","Fury","Lunge","Reaction","Seize the Moment","Slice","Spray","Trick Shot","Vigilance"],
            "4": ["Amazing Effort","Capable Warrior","Experienced Defender","Feint","Increased Effects","Momentum","Pry Open","Snipe","Tough As Nails"],
            "5": ["Adroit Cypher Use","Arc Spray","Improved Success","Jump Attack","Mastery in Armor","Mastery With Attacks","Mastery With Defense","Parry"],
            "6": ["Again and Again","Finishing Blow","Magnificent Moment","Murderer","Spin Attack","Weapon and Body"],
        },
    },
    {
        "key": "adept", "name": "Adept",
        "role_blurb": "Wielders of forces beyond the mundane — magic, psionics, or transcendent technology.",
        "starting_stat_pools": {"Might": 7, "Speed": 9, "Intellect": 12},
        "starting_edge":       {"Might": 0, "Speed": 0, "Intellect": 1},
        "free_pool_points":    6, "starting_effort": 1, "starting_cypher_limit": 3,
        "abilities_by_tier": {
            "1": ["Distortion","Erase Memories","Far Step","Hedge Magic","Magic Training","Onslaught","Push","Resonance Field","Scan","Shatter","Ward"],
            "2": ["Adaptation","Cutting Light","Hover","Mind Reading","Retrieve Memories","Reveal","Stasis"],
            "3": ["Adroit Cypher Use","Countermeasures","Energy Protection","Fire and Ice","Force Field Barrier","Sensor","Targeting Eye"],
            "4": ["Death Touch","Exile","Invisibility","Matter Cloud","Mind Control","Projection","Rapid Processing","Regeneration","Reshape","Wormhole"],
            "5": ["Absorb Energy","Concussion","Conjuration","Create","Dust to Dust","Knowing the Unknown","Master Cypher Use","Teleportation","True Senses"],
            "6": ["Control Weather","Earthquake","Move Mountains","Traverse the Worlds","Usurp Cypher"],
        },
    },
    {
        "key": "explorer", "name": "Explorer",
        "role_blurb": "Curious, fearless adventurers who chart the unknown — physical, mental, or geographic.",
        "starting_stat_pools": {"Might": 10, "Speed": 9, "Intellect": 9},
        "starting_edge":       {"Might": 1, "Speed": 0, "Intellect": 0},
        "free_pool_points":    6, "starting_effort": 1, "starting_cypher_limit": 2,
        "abilities_by_tier": {
            "1": ["Block","Danger Sense","Decipher","Endurance","Find the Way","Fleet of Foot","Improved Edge","Knowledge Skills","Muscles of Iron","No Need for Weapons","Physical Skills"],
            "2": ["Curious","Danger Instinct","Enable Others","Escape","Eye for Detail","Foil Danger","Hand to Eye","Investigative Skills","Quick Recovery","Range Increase","Skill With Defense","Stand Watch","Travel Skills","Wreck"],
            "3": ["Controlled Fall","Experienced in Armor","Expert Cypher Use","Ignore the Pain","Obstacle Running","Resilience","Run and Fight","Seize the Moment","Skill With Attacks","Stone Breaker","Think Your Way Out","Trapfinder","Wrest From Chance"],
            "4": ["Capable Warrior","Expert Skill","Increased Effects","Read the Signs","Runner","Subtle Steps","Tough As Nails"],
            "5": ["Adroit Cypher Use","Free to Move","Group Friendship","Hard to Kill","Jump Attack","Mastery With Defense","Parry","Physically Gifted","Take Command","Vigilant"],
            "6": ["Again and Again","Inspire Coordinated Actions","Mastery in Armor","Mastery With Attacks","Negate Danger","Share Defense","Spin Attack","Wild Vitality"],
        },
    },
    {
        "key": "speaker", "name": "Speaker",
        "role_blurb": "Charismatic talkers — leaders, manipulators, and bards who turn conversations into weapons.",
        "starting_stat_pools": {"Might": 8, "Speed": 9, "Intellect": 11},
        "starting_edge":       {"Might": 0, "Speed": 0, "Intellect": 1},
        "free_pool_points":    6, "starting_effort": 1, "starting_cypher_limit": 2,
        "abilities_by_tier": {
            "1": ["Anecdote","Babel","Demeanor of Command","Encouragement","Enthrall","Erase Memories","Fast Talk","Inspire Aggression","Interaction Skills","Practiced With Medium Weapons","Spin Identity","Terrifying Presence","Understanding"],
            "2": ["Basic Follower","Calm Stranger","Disincentivize","Gather Intelligence","Impart Ideal","Inspiring Ease","Practiced in Armor","Skill With Defense","Speedy Recovery","Unexpected Betrayal"],
            "3": ["Accelerate","Blend In","Discerning Mind","Expert Cypher Use","Expert Follower","Grand Deception","Lead by Inquiry","Mind Reading","Oratory","Perfect Stranger","Quick Wits","Telling"],
            "4": ["Anticipate Attack","Confounding Banter","Feint","Heightened Skills","Psychosis","Read the Signs","Spur Effort","Strategize","Suggestion"],
            "5": ["Adroit Cypher Use","Discipline of Watchfulness","Experienced in Armor","Flee","Foul Aura","Knowing the Unknown","Regeneration","Skill With Attacks","Stimulate"],
            "6": ["Assume Control","Battle Management","Crowd Control","Inspiring Success","Recruit Deputy","Shatter Mind","True Senses","Word of Command"],
        },
    },
]


XP_MECHANICS = {
    "awards": [
        {"key": "gm-intrusion", "name": "GM Intrusion",
         "blurb": "When the GM injects a complication, the player accepting it earns 2 XP and immediately hands 1 of those XP to another player at the table."},
        {"key": "discovery", "name": "Discovery",
         "blurb": "Significant discoveries — a hidden ruin, a lost truth, a narrative breakthrough — award 1-2 XP at the GM's discretion."},
        {"key": "character-arc", "name": "Character Arc Progression",
         "blurb": "Personal long-term arcs award milestone XP when key beats land in play."},
    ],
    "spends": [
        {"key": "reroll", "cost": 1, "name": "Re-roll",
         "blurb": "Spend 1 XP to re-roll any die you just rolled."},
        {"key": "refuse-intrusion", "cost": 1, "name": "Refuse a GM Intrusion",
         "blurb": "Spend 1 XP to decline an intrusion. With 0 XP, you cannot refuse."},
        {"key": "player-intrusion", "cost": 1, "name": "Player Intrusion",
         "blurb": "Spend 1 XP to introduce a beneficial twist on your turn (GM ratifies)."},
        {"key": "short-term-benefit", "cost": 2, "name": "Short-term Benefit",
         "blurb": "Recover from a minor setback or gain a one-scene minor advantage."},
        {"key": "medium-term-benefit", "cost": 3, "name": "Medium-term Benefit",
         "blurb": "Gain a session-long contact, asset, or minor narrative claim."},
        {"key": "long-term-benefit", "cost": 4, "name": "Long-term Benefit",
         "blurb": "Establish a permanent contact, home, or cement a narrative truth."},
        {"key": "advancement-step", "cost": 4, "name": "Character Advancement Step",
         "blurb": "Buy one of the four canonical advancement steps; complete all four to advance a tier."},
        {"key": "peer-transfer", "cost": 1, "name": "Peer XP Transfer",
         "blurb": "Hand 1 XP to another character with a brief narrative justification."},
        {"key": "narrative-pool", "cost": "variable", "name": "Narrative-Pool Spend",
         "blurb": "Several players pool XP to author a setting-shaping change (typically 4-12 XP, GM ratifies the scale)."},
    ],
    "advancement_steps": ADVANCEMENT_STEPS_PER_TIER,
    "peer_transfer_rule":
        "When a player accepts a GM intrusion, they receive 2 XP and must immediately give 1 of those XP to another player, with a brief narrative justification.",
    "intrusion_refusal_rule":
        "A player may refuse any GM intrusion by spending 1 XP. The intrusion is rescinded; the player gains nothing further. A player with 0 XP may not refuse.",
    "tier_advancement_rule":
        "Buying all four advancement steps (4 × 4 = 16 XP) advances the character to the next tier. Steps may be purchased in any order.",
}


SKILL_LEVELS = [
    {"level": "Inability",   "step_shift": 1,  "blurb": "Hindered by 1 step (task is one tougher than printed)."},
    {"level": "Untrained",   "step_shift": 0,  "blurb": "No bonus, no penalty."},
    {"level": "Trained",     "step_shift": -1, "blurb": "Eased by 1 step."},
    {"level": "Specialised", "step_shift": -2, "blurb": "Eased by 2 steps."},
]


RULES_NOTES = [
    "Difficulty scales 1-10 with a target number of 3 × difficulty (DC 9 = task 3).",
    "Effort spends Pool points 1:1 to ease a task by 1 step per level of Effort applied.",
    "Edge reduces the Pool cost of Effort and ability use by its rating, never below 1.",
    "Cypher limit caps how many cyphers a character may carry; exceeding it triggers GM intrusion.",
    "GM Intrusions inject complications; accepting one awards 2 XP (1 to you, 1 to a peer).",
    "Damage Track: Hale → Impaired → Debilitated → Dead. Dropping a Pool to 0 ticks the track.",
]


def list_genres():
    return GENRES


def get_type_full(key: str):
    if not key:
        return None
    k = key.strip().lower()
    return next((t for t in CYPHER_TYPES_FULL if t["key"] == k), None)


def tier_caps(tier: int):
    t = int(tier)
    if not 1 <= t <= 6:
        return None
    return next((row for row in TIER_PROGRESSION if row["tier"] == t), None)


def all_abilities_for(type_key: str, up_to_tier: int):
    """Flat list of every ability available at or below `up_to_tier`."""
    t = get_type_full(type_key)
    if not t:
        return []
    out = []
    for tier_str, names in t["abilities_by_tier"].items():
        if int(tier_str) <= int(up_to_tier):
            for n in names:
                out.append({"name": n, "tier": int(tier_str)})
    return out


# ─── V6.25.25 (Cypher Flavor) ─────────────────────────────────────────
# Flavors are genre-locked tweaks that re-skin Types, Descriptors, Foci,
# Cyphers, and Artifacts so the SAME core mechanics fit a different
# fictional setting. Per the canonical Cypher rules, Flavors do not
# add new abilities — they SUBSTITUTE flavour-tagged variants of the
# canonical roster (e.g. a Warrior in a Sci-Fi Combat flavor still
# uses Bash / Combat Prowess but with a re-skinned name + cosmetic
# blurb so the player can speak the table's vocabulary).
#
# Each flavor row carries:
#   key          — slug
#   name         — display label
#   genres       — which genres support this flavor (subset of GENRES)
#   role_blurb   — what kind of character it produces
#   substitutions — dict of canonical ability name → flavor-skinned name
#                   (NOT a new mechanic — just a re-label so the GM /
#                    player can speak the genre's vocabulary at the table)

FLAVORS = [
    {"key": "magic", "name": "Magic Flavor",
     "genres": ["fantasy", "horror", "fairy-tale", "superheroes"],
     "role_blurb": "Sword-and-sorcery, hedge wizardry, divine wonder. Re-skins combat tricks as cantrips and physical defenses as wards.",
     "substitutions": {
         "Onslaught":      "Eldritch Bolt",
         "Ward":           "Mystic Aegis",
         "Hedge Magic":    "Cantrip",
         "Far Step":       "Step Through Veils",
     }},
    {"key": "combat", "name": "Combat Flavor",
     "genres": ["fantasy", "modern", "post-apocalyptic", "science-fiction", "historical"],
     "role_blurb": "Hard-edged martial training. Adept abilities re-skin as battle techniques; Speakers gain commander vocabulary.",
     "substitutions": {
         "Onslaught":         "Power Strike",
         "Ward":              "Bracing Stance",
         "Skill With Attacks": "Trained Strike",
         "Demeanor of Command": "Battlefield Voice",
     }},
    {"key": "stealth", "name": "Stealth Flavor",
     "genres": ["modern", "fantasy", "horror", "post-apocalyptic", "historical", "science-fiction"],
     "role_blurb": "Shadows, knives, soft-soled boots. Onslaught becomes a silent strike; Ward becomes camouflage.",
     "substitutions": {
         "Onslaught":      "Silent Strike",
         "Ward":           "Camouflage",
         "Far Step":       "Slip Through",
         "Hedge Magic":    "Sleight of Hand",
     }},
    {"key": "technology", "name": "Technology Flavor",
     "genres": ["science-fiction", "modern", "post-apocalyptic", "superheroes"],
     "role_blurb": "Rebreathers, smart-guns, neural lace. Magic abilities re-skin as devices; foci hot-swap to gear.",
     "substitutions": {
         "Onslaught":         "Pulse Weapon",
         "Ward":              "Force Field",
         "Hedge Magic":       "Field Repair",
         "Far Step":          "Jump Drive",
         "Resonance Field":   "Shield Generator",
     }},
    {"key": "skills-knowledge", "name": "Skills & Knowledge Flavor",
     "genres": ["any"],
     "role_blurb": "Scholars, librarians, savants. Trades combat tricks for languages, lore, and investigation.",
     "substitutions": {
         "Onslaught":      "Devastating Question",
         "Skill Training": "Specialised Lore",
         "Hedge Magic":    "Footnote Knowledge",
     }},
    {"key": "horror-occult", "name": "Horror/Occult Flavor",
     "genres": ["horror", "fairy-tale", "fantasy"],
     "role_blurb": "Madness-tinged. Each spell costs a sliver of sanity narratively; cyphers manifest as cursed relics.",
     "substitutions": {
         "Onslaught":      "Mind-Touch Curse",
         "Ward":           "Sigil of Banishment",
         "Hedge Magic":    "Whispered Rite",
     }},
]


def flavors_for_genre(genre: str):
    if not genre:
        return list(FLAVORS)
    g = genre.strip().lower()
    return [f for f in FLAVORS
            if "any" in f["genres"] or g in f["genres"]]




# ─── V6.25.24 (Cycle B-6) — Bestiary seed ───────────────────────────
# Cypher creatures use a single LEVEL stat (1-10) which derives target
# numbers (TN = level × 3), health (level × 3 unless noted), and damage.
# This seed covers a starter spread across genres so the GM has a working
# bestiary on day one. Mechanics-only — full lore prose comes from the
# GM's setting work, not this file.

BESTIARY = [
    {"id": "fantasy-bandit",      "name": "Bandit",
     "level": 2, "health": 6, "damage": 3, "armor": 0,
     "genres": ["fantasy", "modern", "post-apocalyptic", "historical"],
     "role": "minion · pack-tactics",
     "blurb": "Common hold-up artist. Operates in groups of 2-6."},
    {"id": "fantasy-cult-leader", "name": "Cult Leader",
     "level": 5, "health": 22, "damage": 6, "armor": 1,
     "genres": ["fantasy", "horror", "modern"],
     "role": "social caster · debuff",
     "blurb": "Charismatic, knowledgeable, and terrifying when cornered."},
    {"id": "fantasy-dragon-juvenile", "name": "Juvenile Dragon",
     "level": 7, "health": 30, "damage": 9, "armor": 4,
     "genres": ["fantasy", "fairy-tale"],
     "role": "boss · breath weapon (level 6 cone, 30 ft)",
     "blurb": "Big enough to be terrifying, small enough to be killed."},
    {"id": "horror-shadowling",   "name": "Shadowling",
     "level": 3, "health": 9, "damage": 4, "armor": 0,
     "genres": ["horror", "fairy-tale", "fantasy"],
     "role": "ambusher · light-vulnerable",
     "blurb": "Half-real silhouette that drains warmth as it grasps."},
    {"id": "horror-eldritch-cultist", "name": "Eldritch Cultist",
     "level": 4, "health": 12, "damage": 4, "armor": 2,
     "genres": ["horror", "modern", "fantasy"],
     "role": "caster · reality-warp",
     "blurb": "Madness keeps them upright after wounds that should fell."},
    {"id": "scifi-warbot-mk1",    "name": "Warbot Mk-I",
     "level": 4, "health": 16, "damage": 5, "armor": 3,
     "genres": ["science-fiction", "post-apocalyptic", "superheroes"],
     "role": "elite · firearm + impact resistance",
     "blurb": "Mass-produced bipedal combat drone. Outdated, still lethal."},
    {"id": "scifi-rogue-ai",      "name": "Rogue AI Avatar",
     "level": 6, "health": 22, "damage": 6, "armor": 2,
     "genres": ["science-fiction", "modern", "superheroes"],
     "role": "boss · network-bound · projection",
     "blurb": "Strikes through any networked surface; pure intellect made manifest."},
    {"id": "post-mutant-hound",   "name": "Mutant Hound",
     "level": 3, "health": 9, "damage": 4, "armor": 1,
     "genres": ["post-apocalyptic", "horror", "science-fiction"],
     "role": "minion · pack",
     "blurb": "Twisted descendants of dogs left behind. Faster than the original."},
    {"id": "post-scrap-warlord", "name": "Scrap Warlord",
     "level": 5, "health": 16, "damage": 6, "armor": 2,
     "genres": ["post-apocalyptic", "modern"],
     "role": "elite · two-handed weapons + crew",
     "blurb": "Salvage-armoured, oil-stained, and certain you have something they want."},
    {"id": "fairy-river-spirit",  "name": "River Spirit",
     "level": 3, "health": 12, "damage": 4, "armor": 0,
     "genres": ["fairy-tale", "fantasy"],
     "role": "guardian · water-bound · barters",
     "blurb": "Polite if respected. Drowning if not."},
    {"id": "super-nameless-thug", "name": "Nameless Thug",
     "level": 1, "health": 3, "damage": 2, "armor": 0,
     "genres": ["superheroes", "modern", "post-apocalyptic", "historical"],
     "role": "trash mob · fights in groups",
     "blurb": "Lots of these. Defeat trivially in clusters of 3."},
    {"id": "super-supervillain-lieutenant", "name": "Supervillain Lieutenant",
     "level": 6, "health": 24, "damage": 7, "armor": 3,
     "genres": ["superheroes"],
     "role": "elite · powered · monologues",
     "blurb": "Has a code-name. Has a back-story. Will not last the climax."},
]


def list_bestiary(genre: str = ""):
    if not genre or genre == "any":
        return list(BESTIARY)
    return [b for b in BESTIARY if genre in b.get("genres", []) or "any" in b.get("genres", [])]


# ─── V6.25.23 — merge supplementary data into the canonical REFERENCE
# dict so /api/systems/cypher/reference exposes everything in one shot.
REFERENCE.update({
    "tier_progression": TIER_PROGRESSION,
    "advancement_steps": ADVANCEMENT_STEPS_PER_TIER,
    "types_full": CYPHER_TYPES_FULL,
    "genres": GENRES,
    "xp_mechanics": XP_MECHANICS,
    "skill_levels_v2": SKILL_LEVELS,
    "rules_notes": RULES_NOTES,
    "compatibility_notice": COMPATIBILITY_NOTICE,
    "bestiary": BESTIARY,
    "flavors": FLAVORS,
})
