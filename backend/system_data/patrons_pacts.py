"""Patrons & Pacts — Warlock-flavoured reference data shared by D&D 5E
and Anime 5E (the SRD chassis). V6.25.35.

This module is the canon source for:
  • Otherworldly Patrons     — the entity a Warlock has bargained with
  • Pact Boons                — Tome / Blade / Chain / Talisman
  • Pact Magic Invocations    — a curated set of common Eldritch Invocations
  • Demon-/cursed-folk heritages for Anime 5E (extends the SRD races
    with anime-specific demon/oni/cursed bloodline options)

Everything is mechanics-only. The numbers are SRD-safe (CC-BY 4.0
where the SRD covers them; original anime-flavoured originals where
the source canon is closed). Pages refer to the SRD 5.1 layout where
the entry is canon, or to Anime 5E supplement section §A for our
originals.
"""

# ── Otherworldly Patrons ─────────────────────────────────────────
# Each patron has a thematic flavour, a recommended pact, expanded
# spell list (just titles — the spell rows live in dnd5e_extended),
# and 1-2 hallmark feature names for player-facing reference.
PATRONS = [
    {"name": "Archfey",
     "summary": "Bargained with a fey lord — illusion, fae mischief, summer/winter court politics.",
     "expanded_spells": ["Faerie Fire", "Sleep", "Calm Emotions", "Phantasmal Force",
                          "Blink", "Plant Growth", "Dominate Beast", "Greater Invisibility",
                          "Dominate Person", "Seeming"],
     "feature_levels": [
         {"level": 1,  "feature": "Fey Presence — frighten/charm 10ft cube"},
         {"level": 6,  "feature": "Misty Escape — bonus-action invisibility teleport"},
         {"level": 10, "feature": "Beguiling Defenses — immunity to charm + reflect"},
         {"level": 14, "feature": "Dark Delirium — long charm/frighten illusion"},
     ],
     "page": 110},
    {"name": "Fiend",
     "summary": "Pacted with a devil/demon — temporary HP on kill, fire/dark damage, hellish boons.",
     "expanded_spells": ["Burning Hands", "Command", "Blindness/Deafness", "Scorching Ray",
                          "Fireball", "Stinking Cloud", "Fire Shield", "Wall of Fire",
                          "Flame Strike", "Hallow"],
     "feature_levels": [
         {"level": 1,  "feature": "Dark One's Blessing — temp HP on reducing creature to 0"},
         {"level": 6,  "feature": "Dark One's Own Luck — d10 to ability check/save"},
         {"level": 10, "feature": "Fiendish Resilience — pick a damage resistance/long rest"},
         {"level": 14, "feature": "Hurl Through Hell — banish 1 round / 10d10 psychic on return"},
     ],
     "page": 111},
    {"name": "Great Old One",
     "summary": "Channelled an alien horror — telepathy, psychic damage, and creeping dread.",
     "expanded_spells": ["Dissonant Whispers", "Tasha's Hideous Laughter", "Detect Thoughts",
                          "Phantasmal Force", "Clairvoyance", "Sending", "Dominate Beast",
                          "Evard's Black Tentacles", "Dominate Person", "Telekinesis"],
     "feature_levels": [
         {"level": 1,  "feature": "Awakened Mind — 30ft telepathy"},
         {"level": 6,  "feature": "Entropic Ward — disadvantage on attack 1/short rest"},
         {"level": 10, "feature": "Thought Shield — psychic resistance + reflect on telepathic probes"},
         {"level": 14, "feature": "Create Thrall — charm via incapacitated humanoid"},
     ],
     "page": 112},
    {"name": "Celestial",
     "summary": "Pact with a celestial being — radiant damage, healing, and beacons of light.",
     "expanded_spells": ["Cure Wounds", "Guiding Bolt", "Flaming Sphere", "Lesser Restoration",
                          "Daylight", "Revivify", "Guardian of Faith", "Wall of Fire",
                          "Flame Strike", "Greater Restoration"],
     "feature_levels": [
         {"level": 1,  "feature": "Healing Light — 1d6 healing pool / long rest"},
         {"level": 6,  "feature": "Radiant Soul — bonus radiant damage on a roll"},
         {"level": 10, "feature": "Celestial Resilience — temp HP on rest"},
         {"level": 14, "feature": "Searing Vengeance — radiant burst on ally KO"},
     ],
     "page": 113},
    {"name": "Hexblade",
     "summary": "Bargained with a sentient weapon — accurate strikes, hex curses, dark cavalry.",
     "expanded_spells": ["Shield", "Wrathful Smite", "Blur", "Branding Smite", "Blink",
                          "Elemental Weapon", "Phantasmal Killer", "Staggering Smite",
                          "Banishing Smite", "Cone of Cold"],
     "feature_levels": [
         {"level": 1,  "feature": "Hexblade's Curse + Hex Warrior (CHA-to-weapon)"},
         {"level": 6,  "feature": "Accursed Specter — kill humanoid → spectral ally"},
         {"level": 10, "feature": "Armor of Hexes — disadvantage on hex's hits 1d6"},
         {"level": 14, "feature": "Master of Hexes — re-curse on kill"},
     ],
     "page": 114},
    {"name": "Genie",
     "summary": "Bound to a noble genie — elemental damage of chosen kind, vessel sanctuary, wishes.",
     "expanded_spells": ["Detect Evil and Good", "Sleep", "Phantasmal Force", "See Invisibility",
                          "Create Food and Water", "Tongues", "Phantasmal Killer", "Stoneskin",
                          "Creation", "Wall of Stone"],
     "feature_levels": [
         {"level": 1,  "feature": "Genie's Vessel — bonus action elemental dmg + sanctuary"},
         {"level": 6,  "feature": "Elemental Gift — resist genie's element + flight 10 min"},
         {"level": 10, "feature": "Sanctuary Vessel — long rest + heal allies inside"},
         {"level": 14, "feature": "Limited Wish — cast 6th-level-or-lower spell"},
     ],
     "page": 115},
    {"name": "Fathomless",
     "summary": "Pact with the deep — tentacles, abyssal cold, and pressure of the leagues below.",
     "expanded_spells": ["Create or Destroy Water", "Thunderwave", "Gust of Wind", "Silence",
                          "Lightning Bolt", "Sleet Storm", "Control Water", "Summon Elemental",
                          "Bigby's Hand", "Cone of Cold"],
     "feature_levels": [
         {"level": 1,  "feature": "Tentacle of the Deeps — 30ft reach 1d8 cold + slow"},
         {"level": 6,  "feature": "Oceanic Soul — cold resist + speak underwater"},
         {"level": 10, "feature": "Guardian Coil — react redirect 2d8 to tentacle"},
         {"level": 14, "feature": "Grasping Tentacles — Evard's Black Tentacles 1/long rest"},
     ],
     "page": 116},
    {"name": "Undead",
     "summary": "Pacted with an undying tyrant — necrotic damage, fear, and a brush with death.",
     "expanded_spells": ["Bane", "False Life", "Blindness/Deafness", "Phantasmal Force",
                          "Phantom Steed", "Speak with Dead", "Death Ward", "Greater Invisibility",
                          "Antilife Shell", "Cloudkill"],
     "feature_levels": [
         {"level": 1,  "feature": "Form of Dread — frighten on hit + necrotic resistance"},
         {"level": 6,  "feature": "Grave Touched — necrotic crit threshold expanded"},
         {"level": 10, "feature": "Necrotic Husk — 10d10 necrotic burst when reduced to 0 HP"},
         {"level": 14, "feature": "Spirit Projection — astral form 1/long rest"},
     ],
     "page": 117},
]


# ── Pact Boons (Pact Magic 3rd-level feature) ─────────────────────
PACTS = [
    {"name": "Pact of the Tome",     "page": 107,
     "summary": "A Book of Shadows — gain 3 cantrips from any class list. Replaceable on long rest."},
    {"name": "Pact of the Blade",    "page": 108,
     "summary": "Conjure a melee weapon as bonus action; CHA-to-attack via Hex Warrior; magical."},
    {"name": "Pact of the Chain",    "page": 108,
     "summary": "Find Familiar with expanded forms (imp/pseudodragon/quasit/sprite); attack as your action."},
    {"name": "Pact of the Talisman", "page": 109,
     "summary": "Wearer of the talisman adds 1d4 to a failed ability check (Tasha's). Heroic safety net."},
]


# ── Eldritch Invocations (curated subset for player-facing UI) ────
INVOCATIONS = [
    {"name": "Agonizing Blast",       "prereq": "Eldritch Blast cantrip",
     "summary": "Add CHA modifier to Eldritch Blast damage.",            "page": 110},
    {"name": "Armor of Shadows",      "prereq": "—",
     "summary": "Cast Mage Armor on yourself at-will.",                  "page": 110},
    {"name": "Beast Speech",          "prereq": "—",
     "summary": "Speak with beasts at will.",                            "page": 110},
    {"name": "Devil's Sight",         "prereq": "—",
     "summary": "See in normal & magical darkness 120 ft.",              "page": 110},
    {"name": "Eldritch Mind",         "prereq": "—",
     "summary": "Advantage on Constitution saves to maintain concentration.", "page": 110},
    {"name": "Eldritch Spear",        "prereq": "Eldritch Blast cantrip",
     "summary": "Eldritch Blast range = 300 ft.",                        "page": 110},
    {"name": "Mask of Many Faces",    "prereq": "—",
     "summary": "Cast Disguise Self at-will.",                            "page": 110},
    {"name": "Mire the Mind",         "prereq": "Warlock 5",
     "summary": "Cast Slow once per long rest using a warlock slot.",     "page": 110},
    {"name": "Misty Visions",         "prereq": "—",
     "summary": "Cast Silent Image at-will.",                              "page": 110},
    {"name": "Pact of the Blade Strike", "prereq": "Pact of the Blade",
     "summary": "When you hit with your pact weapon, force a CHA save or be frightened until end of next turn.", "page": 110},
    {"name": "Repelling Blast",       "prereq": "Eldritch Blast cantrip",
     "summary": "Push target 10 ft on a hit.",                            "page": 111},
    {"name": "Thirsting Blade",       "prereq": "Pact of the Blade · 5th lv",
     "summary": "Make 2 attacks with your pact weapon when you take the Attack action.", "page": 111},
    {"name": "Voice of the Chain Master", "prereq": "Pact of the Chain",
     "summary": "Telepathic communication and senses share with familiar.","page": 111},
    {"name": "Whispers of the Grave", "prereq": "Warlock 9",
     "summary": "Cast Speak with Dead at-will.",                          "page": 111},
]


# ── Anime 5E demon-folk heritages ─────────────────────────────────
# These extend the SRD chassis with anime-flavoured cursed/demonic
# bloodlines. Each entry follows the same shape as anime5e_data
# `heritages` rows so they can be cross-listed in the picker.
DEMON_HERITAGES = [
    {"name": "Tiefling (Standard)",          "origin": "infernal",
     "ability_bonuses": {"CHA": 2, "INT": 1},
     "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60 ft", "Hellish Resistance (fire)",
                "Infernal Legacy: Thaumaturgy cantrip; Hellish Rebuke 1/day at L3; Darkness 1/day at L5"],
     "page": 200},
    {"name": "Half-Demon (Anime)",           "origin": "demonic-hybrid",
     "ability_bonuses": {"STR": 1, "CON": 2},
     "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60 ft",
                "Demonic Aura — radiate fear 5 ft once/short rest",
                "Resist Necrotic + Fire",
                "Cursed Bloodline — disadvantage on saves vs. Holy when below ½ HP"],
     "page": 201},
    {"name": "Cursed Bloodline (Anime)",     "origin": "ancestral-curse",
     "ability_bonuses": {"WIS": 1, "CHA": 2},
     "size": "Medium", "speed": 30,
     "traits": ["Darkvision 30 ft",
                "Sigil Awakening — at L3 unlock a permanent +1d6 necrotic on melee attacks during full moon / night",
                "Mark of the Pact — visible cursed mark; -2 social with clergy",
                "Resist Psychic"],
     "page": 202},
    {"name": "Oni-blooded (Anime)",          "origin": "yokai",
     "ability_bonuses": {"STR": 2, "CON": 1},
     "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60 ft",
                "Horns — natural 1d6 piercing unarmed",
                "Heritage Rage — once/long rest enter rage-like state (advantage STR checks/saves, +2 melee dmg, 1 min)",
                "Resist Cold"],
     "page": 203},
    {"name": "Hellspawn",                    "origin": "abyssal",
     "ability_bonuses": {"DEX": 1, "CHA": 2},
     "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60 ft",
                "Resist Fire",
                "Chain-Bound — at L3 manifest spectral chains (Reach 5ft, 1d6 force, restrains DC 13)",
                "Whisper of the Pact — Inquisitive Insight bonus on Patron-related lore"],
     "page": 204},
    {"name": "Aasimar (Standard)",           "origin": "celestial",
     "ability_bonuses": {"CHA": 2},
     "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60 ft", "Celestial Resistance (necrotic + radiant)",
                "Healing Hands 1/long rest",
                "Light cantrip"],
     "page": 205},
    {"name": "Fallen-Aasimar",               "origin": "celestial-fallen",
     "ability_bonuses": {"CHA": 2, "STR": 1},
     "size": "Medium", "speed": 30,
     "traits": ["Darkvision 60 ft", "Celestial Resistance (necrotic + radiant)",
                "Healing Hands 1/long rest",
                "Necrotic Shroud — at L3 grow shadowy wings 1 min, fear 10ft, +d10 necrotic on a hit, 1/long rest"],
     "page": 206},
    {"name": "Spirit-Touched",               "origin": "shinto-spirit",
     "ability_bonuses": {"WIS": 2, "DEX": 1},
     "size": "Medium", "speed": 30,
     "traits": ["See Invisibility (Spirits only) 60 ft",
                "Spirit Channel — once/short rest cast Augury",
                "Resist Radiant + Necrotic"],
     "page": 207},
]


__all__ = ["PATRONS", "PACTS", "INVOCATIONS", "DEMON_HERITAGES"]
