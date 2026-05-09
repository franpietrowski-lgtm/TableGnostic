"""Anime 5E reference — extended catalogue (V6.25.32).

Mechanics-only. Where Anime 5E is a one-way port of the D&D 5E SRD, we
re-export the SRD-licensed catalogues from `dnd5e_extended` so an Anime 5E
table that imports an SRD class also gets the SRD subclass / feat / tool /
language pool. On top of that we add **anime-flavoured originals** — five
anime-class subclasses (one per Adept / Champion / Idol / Pilot / Tinker),
genre-flavoured tools, anime-trope feats, signature relics, and a kaiju
roster so the Anime 5E Reference page reaches parity with the D&D 5E one.

This module is consumed by `anime5e_data.py::REFERENCE`.
"""

from .dnd5e_extended import (  # noqa: E402
    LANGUAGES as _SRD_LANGUAGES,
    TOOLS as _SRD_TOOLS,
    FEATS as _SRD_FEATS,
    MAGIC_ITEMS as _SRD_MAGIC_ITEMS,
    MONSTERS as _SRD_MONSTERS,
    SUBCLASSES as _SRD_SUBCLASSES,
    DAMAGE_TYPES,
    SCHOOLS,
    CLASS_FEATURES as _SRD_CLASS_FEATURES,
)

BOOK_PAGE_BASE = 80  # Anime 5E SRD v1.01 supplement section start

# ── Anime 5E original subclasses (one canonical per anime class) ───
# These are mechanic-flavoured anime tropes; they sit alongside the
# SRD subclasses (re-exported below) so any class an Anime 5E player
# picks has at least one canonical subclass to choose from.
_ANIME_SUBCLASSES = [
    {"class": "Adept",    "name": "Way of the Mind's Eye",
     "key": ["Telepathic Whisper 3", "Probe 6 (1/day Detect Thoughts)",
             "Mind Spike 11 (3d6 psychic on hit, 1/short rest)",
             "Lucid Dominion 17 (cast Dominate Person 1/long rest)"],
     "page": BOOK_PAGE_BASE + 0},
    {"class": "Adept",    "name": "Way of the Burning Spirit",
     "key": ["Pyre Hand 3 (cantrip-tier 1d8 fire)",
             "Inner Fire 6 (resistance fire while focused)",
             "Phoenix Pulse 11 (3d10 fire AoE, 1/short rest)",
             "Ascendant Form 17 (1 min flight + fire aura, 1/long rest)"],
     "page": BOOK_PAGE_BASE + 1},
    {"class": "Champion", "name": "Crimson Edge Style",
     "key": ["Blooded Stance 3 (+2 dmg below ½ HP)",
             "Riposte 7 (reaction strike on miss)",
             "Cleaving Will 11 (extra atk on kill)",
             "Crimson Roar 18 (frighten 30ft cone, 1/long rest)"],
     "page": BOOK_PAGE_BASE + 2},
    {"class": "Champion", "name": "Iron-Will Bulwark",
     "key": ["Guardian's Stand 3 (impose disadv on adj. ally hits)",
             "Unyielding 7 (drop to 1 HP instead of 0, 1/long rest)",
             "Bulwark Shout 11 (rally allies +CHA temp HP)",
             "Last Bastion 18 (immune crit while above ½ HP)"],
     "page": BOOK_PAGE_BASE + 3},
    {"class": "Idol",     "name": "Stage of the Rising Sun",
     "key": ["Anthem 3 (allies +1 atk while you sing)",
             "Crowd Spark 6 (Bardic-Inspiration analogue)",
             "Stadium Roar 11 (3d8 thunder cone, 1/short rest)",
             "Encore of Triumph 18 (revive ally @ ½ HP, 1/long rest)"],
     "page": BOOK_PAGE_BASE + 4},
    {"class": "Idol",     "name": "Lyric of the Hidden Heart",
     "key": ["Confidant 3 (charm one humanoid 1 hr / long rest)",
             "Ballad of Sorrow 6 (-2 atk vs. allies in 30ft)",
             "Whispered Promise 11 (Suggestion at-will, save DC=Spell)",
             "Soul Aria 18 (1 min Dominate Monster, 1/long rest)"],
     "page": BOOK_PAGE_BASE + 5},
    {"class": "Pilot",    "name": "Frame of the Lance Knight",
     "key": ["Spear-Frame Mode 3 (+2 reach, dmg = d10)",
             "Boost Dash 7 (50ft straight-line charge, 1/short rest)",
             "Anti-Beam Shield 11 (resist radiant/lightning while piloting)",
             "Solar Lance 18 (10d6 radiant line 60ft, 1/long rest)"],
     "page": BOOK_PAGE_BASE + 6},
    {"class": "Pilot",    "name": "Frame of the Sky Hunter",
     "key": ["Aerial Frame 3 (fly 40ft while piloting)",
             "Vector Lock 7 (re-roll one missed ranged atk)",
             "Hover Volley 11 (3 ranged atks as action while flying)",
             "Halo Strike 18 (15d6 single-target dive, 1/long rest)"],
     "page": BOOK_PAGE_BASE + 7},
    {"class": "Tinker",   "name": "Workshop of the Brass Heart",
     "key": ["Brass Companion 3 (CR ¼ construct ally)",
             "Tinker's Toolbox 6 (cast Mending at-will)",
             "Forge Pulse 11 (3d8 fire/lightning AoE 30ft, 1/short rest)",
             "Animated Citadel 18 (CR 4 construct, 1 hr/long rest)"],
     "page": BOOK_PAGE_BASE + 8},
    {"class": "Tinker",   "name": "Workshop of the Phantom Lens",
     "key": ["Optical Veil 3 (invis 1 round, 1/short rest)",
             "Shrike Drone 6 (CR ⅛ flying scout)",
             "Hard-Light Wall 11 (15ft wall, 10 HP, 1 min)",
             "Photon Cascade 18 (10d8 radiant line 90ft, 1/long rest)"],
     "page": BOOK_PAGE_BASE + 9},
]

# Combine SRD canon (one per imported D&D class) + anime originals.
SUBCLASSES = _ANIME_SUBCLASSES + _SRD_SUBCLASSES

# ── Anime-genre tools (additive to SRD set) ────────────────────────
# These are all mechanic-only; tool descriptions stay short.
_ANIME_TOOLS = [
    {"name": "Hacker's Kit",          "category": "Anime/Tech", "ability": "Intelligence", "page": BOOK_PAGE_BASE + 20},
    {"name": "Mecha Diagnostic Rig",  "category": "Anime/Tech", "ability": "Intelligence", "page": BOOK_PAGE_BASE + 20},
    {"name": "Idol's Concert Kit",    "category": "Anime/Idol", "ability": "Charisma",     "page": BOOK_PAGE_BASE + 20},
    {"name": "Spirit-Charm Brush",    "category": "Anime/Occult","ability": "Wisdom",      "page": BOOK_PAGE_BASE + 20},
    {"name": "Otaku Lore Library",    "category": "Anime/Lore", "ability": "Intelligence", "page": BOOK_PAGE_BASE + 20},
    {"name": "Bento Cooking Kit",     "category": "Anime/Daily","ability": "Wisdom",       "page": BOOK_PAGE_BASE + 20},
    {"name": "Power-Limiter Tuner",   "category": "Anime/Tech", "ability": "Intelligence", "page": BOOK_PAGE_BASE + 20},
    {"name": "Familiar Charm Bracelet","category": "Anime/Occult","ability": "Charisma",   "page": BOOK_PAGE_BASE + 20},
]
TOOLS = _SRD_TOOLS + _ANIME_TOOLS

# ── Languages — anime-flavour additions to the SRD pool ────────────
_ANIME_LANGUAGES = [
    {"name": "Spirit-Tongue",  "script": "Sigil-glyph", "speakers": "Yokai · Spirits",        "category": "anime",  "page": BOOK_PAGE_BASE + 30},
    {"name": "Mech-Cant",      "script": "Glyph",        "speakers": "Engineers · Pilots",     "category": "anime", "page": BOOK_PAGE_BASE + 30},
    {"name": "Hex-cant",       "script": "Cypher",       "speakers": "Hackers · Underworld",   "category": "anime", "page": BOOK_PAGE_BASE + 30},
    {"name": "Earth-tongue",   "script": "Roman",        "speakers": "Isekai protagonists",    "category": "anime", "page": BOOK_PAGE_BASE + 30},
    {"name": "Lyrical Bardic", "script": "Common",       "speakers": "Idols · Bards",          "category": "anime", "page": BOOK_PAGE_BASE + 30},
]
LANGUAGES = _SRD_LANGUAGES + _ANIME_LANGUAGES

# ── Anime-trope feats (additive to SRD set) ────────────────────────
_ANIME_FEATS = [
    {"name": "Power Limiter",     "prereq": "—",
     "summary": "Spend an action to remove your bracelet — gain 1d4+CHA temp HP and advantage on next attack roll, 1/long rest", "page": BOOK_PAGE_BASE + 40},
    {"name": "Transformation Sequence", "prereq": "Idol or Adept",
     "summary": "Bonus action: enter a magical-girl form for 1 min — +2 AC, fly 30 ft, 1/long rest", "page": BOOK_PAGE_BASE + 41},
    {"name": "Mecha-Bond",        "prereq": "Pilot 3rd-lv",
     "summary": "Your bonded mecha shares a Frame Trait with you and grants +1 to a chosen save", "page": BOOK_PAGE_BASE + 42},
    {"name": "Tsundere Reflex",   "prereq": "—",
     "summary": "When an ally drops to 0 HP within 30ft, reaction: deal +1d10 damage on your next hit this round", "page": BOOK_PAGE_BASE + 43},
    {"name": "Senpai's Approval", "prereq": "CHA 13",
     "summary": "1/short rest: grant a chosen ally advantage on their next save / atk / check", "page": BOOK_PAGE_BASE + 44},
    {"name": "Friendship Power",  "prereq": "—",
     "summary": "When at least 2 allies are conscious within 30ft, +1 atk and saves; -1 if alone", "page": BOOK_PAGE_BASE + 45},
    {"name": "Anime Logic",       "prereq": "INT 13",
     "summary": "1/long rest: declare narrative fact (DM may veto) — gain advantage on the related check", "page": BOOK_PAGE_BASE + 46},
    {"name": "Hot-Blooded",       "prereq": "STR or CON 13",
     "summary": "Below ½ HP: +2 atk, +2 dmg, but -2 AC", "page": BOOK_PAGE_BASE + 47},
    {"name": "Plot Armor",        "prereq": "—",
     "summary": "1/long rest: turn a melee crit into a normal hit", "page": BOOK_PAGE_BASE + 48},
    {"name": "Side-Character Backstory", "prereq": "—",
     "summary": "+1 to one ability · gain proficiency in 2 skills + 1 tool + 1 language", "page": BOOK_PAGE_BASE + 49},
    {"name": "Eyecatch Recovery", "prereq": "—",
     "summary": "End of any turn: spend HD to heal as a free action, 1/short rest", "page": BOOK_PAGE_BASE + 50},
    {"name": "Catchphrase Casting", "prereq": "Spellcasting",
     "summary": "1/day: cast a known spell without verbal/somatic if you declare a catchphrase", "page": BOOK_PAGE_BASE + 51},
    {"name": "School Uniform Discipline", "prereq": "—",
     "summary": "While in uniform: +1 to all saves vs. charm/frighten · advantage on Insight", "page": BOOK_PAGE_BASE + 52},
    {"name": "Reincarnated Knowledge", "prereq": "Isekai background",
     "summary": "+1 INT · gain proficiency in 1 tool + 1 vehicle of your choice", "page": BOOK_PAGE_BASE + 53},
    {"name": "Swimsuit Episode Endurance", "prereq": "CON 13",
     "summary": "Resistance to exhaustion from heat / cold; +1 CON", "page": BOOK_PAGE_BASE + 54},
]
FEATS = _SRD_FEATS + _ANIME_FEATS

# ── Anime relics (additive to SRD magic items) ─────────────────────
_ANIME_RELICS = [
    {"name": "Henshin Pendant",      "rarity": "rare",      "type": "Wondrous", "attune": True,
     "summary": "Bonus action: transform — +2 AC and fly 30 ft for 10 min, 1/long rest", "page": BOOK_PAGE_BASE + 60},
    {"name": "Rune-bound Greatsword","rarity": "rare",      "type": "Weapon",   "attune": True,
     "summary": "+1 atk/dmg · 1/day cast Searing Smite as bonus action", "page": BOOK_PAGE_BASE + 61},
    {"name": "Pilot's Visor",        "rarity": "uncommon",  "type": "Eyewear",  "attune": True,
     "summary": "Adv on Pilot checks · ignore vision penalties when piloting", "page": BOOK_PAGE_BASE + 62},
    {"name": "Familiar Whistle",     "rarity": "uncommon",  "type": "Wondrous", "attune": True,
     "summary": "Summon a CR ⅛ familiar (Beast / Spirit) for 1 hour, 1/long rest", "page": BOOK_PAGE_BASE + 63},
    {"name": "Idol's Microphone",    "rarity": "rare",      "type": "Wondrous", "attune": True,
     "summary": "+CHA dmg on song-based abilities · cast Charm Person 1/short rest", "page": BOOK_PAGE_BASE + 64},
    {"name": "Hot-Spring Towel",     "rarity": "common",    "type": "Wondrous", "attune": False,
     "summary": "Short rest with this towel: regain 1 extra HD", "page": BOOK_PAGE_BASE + 65},
    {"name": "Senpai's Letter",      "rarity": "common",    "type": "Wondrous", "attune": False,
     "summary": "1/long rest: read aloud to grant an ally advantage on next save", "page": BOOK_PAGE_BASE + 66},
    {"name": "Mecha Repair Drone",   "rarity": "rare",      "type": "Wondrous", "attune": True,
     "summary": "Bonus action: repair vehicle/construct 2d8+CL HP, 3 charges/long rest", "page": BOOK_PAGE_BASE + 67},
    {"name": "Spirit-Bound Talisman","rarity": "uncommon",  "type": "Wondrous", "attune": True,
     "summary": "Adv on saves vs. possession · sense undead/spirits within 60 ft", "page": BOOK_PAGE_BASE + 68},
    {"name": "Catgirl Ear Ribbon",   "rarity": "uncommon",  "type": "Wondrous", "attune": True,
     "summary": "+1 DEX · darkvision 60 ft · adv on Stealth in dim light", "page": BOOK_PAGE_BASE + 69},
    {"name": "Power Suit Gauntlet",  "rarity": "rare",      "type": "Gauntlet", "attune": True,
     "summary": "+1 atk · unarmed dmg = 1d10 force · 1/day cast Shocking Grasp at 3rd lv", "page": BOOK_PAGE_BASE + 70},
    {"name": "Otaku's Encyclopaedia","rarity": "uncommon",  "type": "Tome",     "attune": False,
     "summary": "Pick a creature type each long rest — adv on Knowledge checks vs. that type", "page": BOOK_PAGE_BASE + 71},
    {"name": "Reincarnator's Diary", "rarity": "rare",      "type": "Tome",     "attune": True,
     "summary": "Once per session: ask the GM one yes/no metaphysical question (truthful)", "page": BOOK_PAGE_BASE + 72},
    {"name": "Magical Girl Wand",    "rarity": "rare",      "type": "Wand",     "attune": True,
     "summary": "+1 spell atk · 7 charges · cast Sacred Flame / Healing Word / Magic Missile", "page": BOOK_PAGE_BASE + 73},
    {"name": "Yokai-Ward Charm",     "rarity": "uncommon",  "type": "Wondrous", "attune": False,
     "summary": "Adv on saves vs. fey/spirit fear effects · resist necrotic 10 min, 1/long rest", "page": BOOK_PAGE_BASE + 74},
]
MAGIC_ITEMS = _SRD_MAGIC_ITEMS + _ANIME_RELICS

# ── Anime-flavour monsters (kaiju / yokai / mecha) ─────────────────
_ANIME_MONSTERS = [
    {"name": "Kaiju (Lesser)",     "cr": 9,  "type": "Monstrosity", "size": "Huge",     "ac": 17, "hp": 200, "speed": "40 ft, swim 40 ft", "atks": "Slam 3d10+6 · Stomp 4d6 (DEX save)",       "page": BOOK_PAGE_BASE + 80},
    {"name": "Kaiju (Great)",      "cr": 16, "type": "Monstrosity", "size": "Gargantuan","ac": 19, "hp": 400, "speed": "40 ft, swim 40 ft", "atks": "Bite 5d10 · Tail Sweep 6d6 cone · Atomic Beam 12d6 line", "page": BOOK_PAGE_BASE + 81},
    {"name": "Yokai (Tengu)",      "cr": 4,  "type": "Fey",         "size": "Medium",   "ac": 14, "hp": 65,  "speed": "30 ft, fly 60 ft", "atks": "Talons 2× 1d8+3 · Wind Slash 3d6 (30ft cone)", "page": BOOK_PAGE_BASE + 82},
    {"name": "Yokai (Kitsune-9)",  "cr": 8,  "type": "Fey",         "size": "Medium",   "ac": 16, "hp": 110, "speed": "40 ft", "atks": "Foxfire 4d6 fire · Charm 30ft cone (WIS DC 16)", "page": BOOK_PAGE_BASE + 83},
    {"name": "Yokai (Oni)",        "cr": 7,  "type": "Giant",       "size": "Large",    "ac": 16, "hp": 110, "speed": "30 ft", "atks": "Glaive 2× 2d12+5 · Change Shape (humanoid)", "page": BOOK_PAGE_BASE + 84},
    {"name": "Cyberdemon",         "cr": 11, "type": "Fiend",       "size": "Large",    "ac": 18, "hp": 175, "speed": "30 ft, fly 60 ft", "atks": "Plasma Cannon 5d6 · Rocket Salvo 8d6 (15ft sphere)", "page": BOOK_PAGE_BASE + 85},
    {"name": "Mecha Drone (Light)","cr": 1,  "type": "Construct",   "size": "Small",    "ac": 15, "hp": 22,  "speed": "30 ft, fly 30 ft", "atks": "Laser 1d6+2 · Self-Detonate 2d6", "page": BOOK_PAGE_BASE + 86},
    {"name": "Mecha Trooper",      "cr": 3,  "type": "Construct",   "size": "Medium",   "ac": 17, "hp": 65,  "speed": "30 ft", "atks": "Pulse Rifle 2d8+2 · Stomp 1d10+2", "page": BOOK_PAGE_BASE + 87},
    {"name": "Mecha Frame (Heavy)","cr": 9,  "type": "Construct",   "size": "Huge",     "ac": 19, "hp": 230, "speed": "40 ft", "atks": "Beam Cannon 6d6 line · Smash 4d10+6 · Anti-Air Missile 4d8 (DEX 16)", "page": BOOK_PAGE_BASE + 88},
    {"name": "Spirit (Lesser)",    "cr": 1,  "type": "Undead",      "size": "Medium",   "ac": 12, "hp": 22,  "speed": "fly 40 ft hover", "atks": "Chill Touch 2d6 necrotic", "page": BOOK_PAGE_BASE + 89},
    {"name": "Spirit (Vengeful)",  "cr": 5,  "type": "Undead",      "size": "Medium",   "ac": 13, "hp": 75,  "speed": "fly 40 ft hover", "atks": "Vengeance Wail 4d6 psychic (cone) · Possess (CHA save)", "page": BOOK_PAGE_BASE + 90},
    {"name": "Familiar (Adept)",   "cr": 0.25,"type": "Beast",      "size": "Tiny",     "ac": 13, "hp": 9,   "speed": "30 ft, fly 30 ft", "atks": "Bite/Peck 1d4 · Telepathic Link 30 ft", "page": BOOK_PAGE_BASE + 91},
    {"name": "Idol Fan Swarm",     "cr": 2,  "type": "Humanoid",    "size": "Large (swarm)","ac": 12, "hp": 45,  "speed": "30 ft", "atks": "Crowd Press 3d6 · Cheer (allies +1 atk)", "page": BOOK_PAGE_BASE + 92},
    {"name": "Hacker (NPC)",       "cr": 1,  "type": "Humanoid",    "size": "Medium",   "ac": 12, "hp": 22,  "speed": "30 ft", "atks": "Stun Baton 1d6+2 · Override Drone (CR ≤ 1)", "page": BOOK_PAGE_BASE + 93},
    {"name": "Magical Girl Trainee","cr": 2, "type": "Humanoid",    "size": "Medium",   "ac": 14, "hp": 40,  "speed": "30 ft", "atks": "Wand Bolt 2d8 force · Healing Light 2d6", "page": BOOK_PAGE_BASE + 94},
]
MONSTERS = _SRD_MONSTERS + _ANIME_MONSTERS

# Class-feature timeline — re-export SRD subset for the imported D&D classes;
# anime-original classes already carry their own progression in
# `anime5e_class_library.py` and are surfaced separately by the Atelier.
CLASS_FEATURES = _SRD_CLASS_FEATURES

__all__ = [
    "LANGUAGES", "TOOLS", "FEATS", "MAGIC_ITEMS", "MONSTERS",
    "SUBCLASSES", "DAMAGE_TYPES", "SCHOOLS", "CLASS_FEATURES",
]
