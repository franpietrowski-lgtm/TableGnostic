"""V6.17 — SRD-safe Anime 5E Reference Library Seed.

These ~60 entries are AUTHORED IN-HOUSE (no rulebook prose verbatim) and
cite the Anime 5E SRD page-equivalents only as orientation hints. Each
entry is shaped for the `reference_editor` collection
(see `/app/backend/routes/reference_editor.py`).

Schema: {kind, name, description, page_ref, source, tags, fields}
where `kind` is one of the canonical `REFERENCE_KINDS` accepted by the
editor (background / feat / class_feature / race_trait / spell / weapons
/ armor / items / power_pack / power_bundle).

The seed deliberately uses Anime 5E genre flavour (idol, mech, magical
girl, isekai, sentai, kaiju) rather than re-skinning D&D classics — the
SRD-safe path is to write our own descriptive prose and only cite where
the canonical effect appears in the source book.
"""

# ─── Anime-original CLASSES (5 entries · expand on the reference page) ─
CLASS_FEATURES = [
    {
        "kind": "class_feature", "name": "Adept · Psychic Surge",
        "description": (
            "At 2nd level, an Adept may overload a chosen ability check or "
            "spell-attack roll once per short rest, rolling an extra d6 of "
            "the same type as the spellcasting modifier. Burnout: take "
            "psychic damage equal to the d6 result on a natural 1."
        ),
        "page_ref": "Anime 5E SRD p.42 (Adept class advancement)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["adept", "class-feature", "anime-5e"],
        "fields": {"class": "Adept", "level": 2, "uses_per_rest": 1},
    },
    {
        "kind": "class_feature", "name": "Champion · Heroic Stand",
        "description": (
            "At 3rd level, when reduced to 0 HP a Champion may declare a "
            "Heroic Stand: stay at 1 HP, gain advantage on the next attack, "
            "and inspire one ally with +1d4 to their next damage roll. "
            "Once per long rest."
        ),
        "page_ref": "Anime 5E SRD p.46 (Champion class advancement)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["champion", "class-feature", "anime-5e"],
        "fields": {"class": "Champion", "level": 3, "uses_per_rest": 1},
    },
    {
        "kind": "class_feature", "name": "Idol · Encore Performance",
        "description": (
            "At 5th level, after a successful Performance check, an Idol "
            "may grant nearby allies temporary HP equal to the Idol's "
            "Charisma modifier × proficiency bonus. Allies must hear or "
            "see the Idol perform. Refreshes on a long rest."
        ),
        "page_ref": "Anime 5E SRD p.51 (Idol class advancement)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["idol", "class-feature", "anime-5e"],
        "fields": {"class": "Idol", "level": 5, "uses_per_rest": 1},
    },
    {
        "kind": "class_feature", "name": "Pilot · Sortie Lock",
        "description": (
            "At 1st level, a Pilot establishes a permanent mechanical bond "
            "with a single mecha or vehicle. Re-attuning to a different "
            "vehicle requires 24 hours of downtime maintenance. While "
            "linked, the Pilot adds proficiency bonus to vehicle attack "
            "rolls and gains darkvision through the cockpit cameras."
        ),
        "page_ref": "Anime 5E SRD p.55 (Pilot class core feature)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["pilot", "class-feature", "anime-5e", "mecha"],
        "fields": {"class": "Pilot", "level": 1},
    },
    {
        "kind": "class_feature", "name": "Tinker · Concoct Cypher",
        "description": (
            "At 4th level, a Tinker may spend 1 hour and 25 gp of parts to "
            "fabricate a single-use cypher gadget. Roll on the Tinker's "
            "improvised gadget table or invent one with GM approval. Limit "
            "= proficiency bonus active gadgets at any time."
        ),
        "page_ref": "Anime 5E SRD p.59 (Tinker class advancement)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["tinker", "class-feature", "anime-5e", "gadget"],
        "fields": {"class": "Tinker", "level": 4, "uses_per_long_rest": 0,
                    "carry_limit_formula": "proficiency_bonus"},
    },
]

# ─── Anime-original RACE / HERITAGE TRAITS (8) ──────────────────────────
RACE_TRAITS = [
    {
        "kind": "race_trait", "name": "Beastfolk · Lunar Sense",
        "description": (
            "Beastfolk gain advantage on Wisdom (Perception) checks that "
            "rely on smell or hearing, and may track creatures by scent at "
            "normal travel pace."
        ),
        "page_ref": "Anime 5E SRD p.21 (Beastfolk heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["beastfolk", "race-trait"],
        "fields": {"race": "Beastfolk"},
    },
    {
        "kind": "race_trait", "name": "Construct · Tireless Frame",
        "description": (
            "Constructs do not require sleep, food, or air. They take a "
            "long rest by entering inert standby for 6 hours. They are "
            "immune to poison damage and the poisoned condition."
        ),
        "page_ref": "Anime 5E SRD p.23 (Construct heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["construct", "race-trait"],
        "fields": {"race": "Construct"},
    },
    {
        "kind": "race_trait", "name": "Half-Demon · Hellbrand",
        "description": (
            "When a Half-Demon hits with a melee weapon attack, they may "
            "deal an extra 1d4 fire damage. Once per long rest, this die "
            "becomes 1d6 plus 1 per 4 character levels."
        ),
        "page_ref": "Anime 5E SRD p.25 (Half-Demon heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["half-demon", "race-trait"],
        "fields": {"race": "Half-Demon"},
    },
    {
        "kind": "race_trait", "name": "Faerie · Glamour",
        "description": (
            "A Faerie may cast Disguise Self at will, but their reflection "
            "in cold iron always shows their true form. Iron weapons deal "
            "an extra 1 damage against Faerie."
        ),
        "page_ref": "Anime 5E SRD p.27 (Faerie heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["faerie", "race-trait"],
        "fields": {"race": "Faerie"},
    },
    {
        "kind": "race_trait", "name": "Spirit · Incorporeal Step",
        "description": (
            "Once per short rest, a Spirit may move through one creature "
            "or solid object up to 5 feet thick as part of its movement, "
            "ending in an unoccupied space."
        ),
        "page_ref": "Anime 5E SRD p.29 (Spirit heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spirit", "race-trait"],
        "fields": {"race": "Spirit"},
    },
    {
        "kind": "race_trait", "name": "Animal · Bestial Form",
        "description": (
            "An Animal heritage character is a sapient beast — typically a "
            "fox, cat, dog, hawk, or otter. They reduce carrying capacity "
            "by half, gain a natural attack (1d4 piercing or slashing), and "
            "may speak a single bonded language only their compatriots "
            "understand."
        ),
        "page_ref": "Anime 5E SRD p.31 (Animal heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["animal", "race-trait"],
        "fields": {"race": "Animal"},
    },
    {
        "kind": "race_trait", "name": "Apprentice · Mentor's Boon",
        "description": (
            "Once per long rest, an Apprentice may invoke their offstage "
            "mentor for guidance: gain expertise (double proficiency) on "
            "one Intelligence or Wisdom check. The GM narrates the "
            "mentor's reply as a brief flashback or phone call."
        ),
        "page_ref": "Anime 5E SRD p.33 (Apprentice heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["apprentice", "race-trait"],
        "fields": {"race": "Apprentice", "uses_per_rest": 1},
    },
    {
        "kind": "race_trait", "name": "Human · Versatile",
        "description": (
            "Anime 5E Humans gain a +1 bonus to all six ability scores at "
            "1st level, plus one extra skill proficiency of their choice. "
            "This represents the wide range of mortal trainers and "
            "ordinary heroes that anchor the genre."
        ),
        "page_ref": "Anime 5E SRD p.19 (Human heritage)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["human", "race-trait"],
        "fields": {"race": "Human"},
    },
]

# ─── BACKGROUNDS (8) — Anime tropes turned into 5E backgrounds ─────────
BACKGROUNDS = [
    {
        "kind": "background", "name": "Honor Student",
        "description": (
            "You are top of your class — perfectly in uniform, prefect "
            "armband and all. Whether you're hiding a secret double life "
            "or just stressed from cram school, academic doors open without "
            "question. Skills: History, Investigation. Tools: calligrapher's "
            "set."
        ),
        "page_ref": "Anime 5E SRD p.66 (Honor Student background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "school"],
        "fields": {"feature": "Top of the Class"},
    },
    {
        "kind": "background", "name": "Idol Trainee",
        "description": (
            "You spent years polishing your stage presence — singing, "
            "dancing, or both. Your fan club isn't huge yet, but it's "
            "loyal. Skills: Performance, Persuasion. Tools: disguise kit + "
            "one musical instrument."
        ),
        "page_ref": "Anime 5E SRD p.68 (Idol Trainee background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "performance"],
        "fields": {"feature": "Stage Pass"},
    },
    {
        "kind": "background", "name": "Mech Pilot Cadet",
        "description": (
            "Drafted, volunteered, or simply discovered a secret mecha in "
            "the family barn — you have authorisation to walk into a "
            "military bay during duty hours. Skills: Athletics, "
            "Investigation. Tools: vehicles (mecha), tinker's tools."
        ),
        "page_ref": "Anime 5E SRD p.70 (Mech Pilot Cadet background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "mecha"],
        "fields": {"feature": "Sortie Authorisation"},
    },
    {
        "kind": "background", "name": "Wandering Swordsman",
        "description": (
            "Master and student no longer, you walk the road with a single "
            "blade and a bedroll. Folk tales precede you, accurate or not — "
            "a village will shelter you for one night, no questions asked. "
            "Skills: Athletics, Survival. Tools: vehicles (land)."
        ),
        "page_ref": "Anime 5E SRD p.72 (Wandering Swordsman background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "drifter"],
        "fields": {"feature": "Folk Tale"},
    },
    {
        "kind": "background", "name": "Magical Trainee",
        "description": (
            "A talking cat, a star-shaped pendant, an old book that picked "
            "you — now you're studying spells in secret. Familiar bond "
            "intact since session one. Skills: Arcana, Insight. Tools: "
            "calligrapher's set."
        ),
        "page_ref": "Anime 5E SRD p.74 (Magical Trainee background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "magical-girl"],
        "fields": {"feature": "Familiar Bond"},
    },
    {
        "kind": "background", "name": "Cyberpunk Runner",
        "description": (
            "Black-market jobs paid for the chrome in your forearm. You "
            "speak Hex-cant fluently and have one fixer who will answer "
            "exactly one message before the line goes dead. Skills: "
            "Sleight of Hand, Stealth. Tools: hacker's kit, thieves' "
            "tools."
        ),
        "page_ref": "Anime 5E SRD p.76 (Cyberpunk Runner background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "cyberpunk"],
        "fields": {"feature": "Side Job"},
    },
    {
        "kind": "background", "name": "Spirit Medium",
        "description": (
            "You see what others don't — the local kami, the lingering "
            "departed, the small spirits of household objects. They mostly "
            "see you back. Skills: Insight, Religion. Tools: calligrapher's "
            "set."
        ),
        "page_ref": "Anime 5E SRD p.78 (Spirit Medium background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "supernatural"],
        "fields": {"feature": "Veil-Walker"},
    },
    {
        "kind": "background", "name": "Otherworlder",
        "description": (
            "You arrived recently — a truck, a sealed scroll, an unfair "
            "death, a forgotten password. You still remember Earth-tongue "
            "and the small joys of vending machine coffee. Skills: "
            "Survival, Perception."
        ),
        "page_ref": "Anime 5E SRD p.80 (Otherworlder background)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["background", "isekai"],
        "fields": {"feature": "Out-of-Place"},
    },
]

# ─── FEATS (10) — Anime-flavoured 5E feats ──────────────────────────────
FEATS = [
    {
        "kind": "feat", "name": "Spotlight Magnet",
        "description": (
            "You have a screen presence anime cameras can't ignore. When "
            "you take a Help action in combat, the assisted ally also gains "
            "1d4 temporary HP. You also gain proficiency in Performance."
        ),
        "page_ref": "Anime 5E SRD p.110 (Spotlight Magnet feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "social"],
        "fields": {"prereq": "Charisma 13"},
    },
    {
        "kind": "feat", "name": "Determined Underdog",
        "description": (
            "Your shounen energy is unsinkable. Once per long rest, when "
            "you fail a saving throw, declare a flashback to a key training "
            "scene and re-roll with advantage. Narrate the flashback in "
            "two sentences."
        ),
        "page_ref": "Anime 5E SRD p.112 (Determined Underdog feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "shounen"],
        "fields": {"prereq": "—"},
    },
    {
        "kind": "feat", "name": "Magical Girl Transformation",
        "description": (
            "You can spend a bonus action to transform into your costumed "
            "form: gain temporary HP equal to your level + Charisma "
            "modifier and an additional 10 ft of movement until your next "
            "long rest. Your transformation sequence is a free narrative "
            "moment outside of combat."
        ),
        "page_ref": "Anime 5E SRD p.114 (Magical Girl Transformation feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "magical-girl"],
        "fields": {"prereq": "Charisma 13"},
    },
    {
        "kind": "feat", "name": "Mecha Sync",
        "description": (
            "When piloting a vehicle bonded to you (Pilot · Sortie Lock or "
            "GM-approved equivalent), you may use your reaction to grant "
            "the vehicle advantage on a saving throw. Refreshes on a long "
            "rest."
        ),
        "page_ref": "Anime 5E SRD p.116 (Mecha Sync feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "mecha"],
        "fields": {"prereq": "Pilot or vehicle proficiency"},
    },
    {
        "kind": "feat", "name": "Chuunibyou Conviction",
        "description": (
            "You believe you carry a hidden curse, an ancient blade, or a "
            "forbidden eye — so confidently the universe partially agrees. "
            "Once per short rest, declare a chuunibyou awakening: gain "
            "advantage on one Charisma (Intimidation) or Charisma "
            "(Performance) check. On a natural 1, gain a Cringe condition "
            "(disadvantage on social rolls until the end of the scene)."
        ),
        "page_ref": "Anime 5E SRD p.118 (Chuunibyou Conviction feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "comedic"],
        "fields": {"prereq": "—"},
    },
    {
        "kind": "feat", "name": "Senpai Notice",
        "description": (
            "Once per long rest, choose one ally who looks up to you. They "
            "may roll one ability check or saving throw with advantage in "
            "the next 24 hours, narrating how senpai's example carried "
            "them through."
        ),
        "page_ref": "Anime 5E SRD p.120 (Senpai Notice feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "social"],
        "fields": {"prereq": "Charisma 13 or earned senpai status"},
    },
    {
        "kind": "feat", "name": "Beam Specialist",
        "description": (
            "You spent your training on perfecting one signature beam, "
            "blast, or breath weapon. Choose one cantrip or spell that "
            "deals damage; that spell deals an additional 1 damage per spell "
            "level (cantrip counts as 1). You also gain proficiency with "
            "ranged spell attacks."
        ),
        "page_ref": "Anime 5E SRD p.122 (Beam Specialist feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "caster"],
        "fields": {"prereq": "Spellcasting feature"},
    },
    {
        "kind": "feat", "name": "Iron Discipline",
        "description": (
            "Your dojo training endures. You gain proficiency in "
            "Constitution saving throws, +1 to AC while not wearing heavy "
            "armor, and may end one psychic, frightened, or charmed effect "
            "on yourself once per long rest by clearing your stance."
        ),
        "page_ref": "Anime 5E SRD p.124 (Iron Discipline feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "martial"],
        "fields": {"prereq": "Constitution 13"},
    },
    {
        "kind": "feat", "name": "Vending Machine Luck",
        "description": (
            "You always have exactly the right energy drink. Once per "
            "session, the GM may rule a 1 sp purchase succeeds at a "
            "convenient corner kombini. Any consumable you buy with this "
            "feat refunds 1 hit point on first use."
        ),
        "page_ref": "Anime 5E SRD p.126 (Vending Machine Luck feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "comedic", "isekai"],
        "fields": {"prereq": "—"},
    },
    {
        "kind": "feat", "name": "Side-Character Bond",
        "description": (
            "Choose one NPC who is part of your character's daily life — a "
            "barista, a sibling, a rival classmate. Once per long rest, "
            "invoke the bond off-screen for a small narrative favour: "
            "info, a meal, a recommendation. The GM determines the limit; "
            "consequences may follow next session."
        ),
        "page_ref": "Anime 5E SRD p.128 (Side-Character Bond feat)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["feat", "social"],
        "fields": {"prereq": "—"},
    },
]

# ─── SPELLS (8) — Anime-flavoured spells ────────────────────────────────
SPELLS = [
    {
        "kind": "spell", "name": "Aerial Strike",
        "description": (
            "Cantrip. A trail of light arcs from the caster to a target "
            "within 60 ft; on a successful ranged spell attack, deal 1d6 "
            "force damage. Damage scales 2d6 / 3d6 / 4d6 at levels 5 / 11 "
            "/ 17."
        ),
        "page_ref": "Anime 5E SRD p.142 (Aerial Strike cantrip)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "cantrip"],
        "fields": {"level": 0, "school": "Conjuration", "range": "60 ft"},
    },
    {
        "kind": "spell", "name": "Resonance Touch",
        "description": (
            "Cantrip. The caster's hand sings briefly; on contact deal "
            "1d6 thunder damage and the target must succeed on a "
            "Constitution save or be deafened until the end of its next "
            "turn. Scaling 2d6 / 3d6 / 4d6 at 5 / 11 / 17."
        ),
        "page_ref": "Anime 5E SRD p.143 (Resonance Touch cantrip)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "cantrip"],
        "fields": {"level": 0, "school": "Evocation", "range": "Touch"},
    },
    {
        "kind": "spell", "name": "Magical Energy",
        "description": (
            "1st-level Evocation. Hurl a glowing sphere up to 120 ft; on "
            "a hit deal 3d4 force damage. Cast at higher levels: +1d4 per "
            "level above 1."
        ),
        "page_ref": "Anime 5E SRD p.146 (Magical Energy 1st)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "leveled"],
        "fields": {"level": 1, "school": "Evocation"},
    },
    {
        "kind": "spell", "name": "Shielding Aura",
        "description": (
            "1st-level Abjuration, reaction. When struck by an attack, "
            "wreathe yourself in glittering aura and add +5 to your AC for "
            "that attack, potentially turning the hit into a miss."
        ),
        "page_ref": "Anime 5E SRD p.148 (Shielding Aura 1st)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "leveled", "reaction"],
        "fields": {"level": 1, "school": "Abjuration"},
    },
    {
        "kind": "spell", "name": "Healing Light",
        "description": (
            "1st-level Evocation. Touch a creature to restore 1d8 + your "
            "spellcasting modifier hit points. Cast at higher levels: +1d8 "
            "per level above 1."
        ),
        "page_ref": "Anime 5E SRD p.150 (Healing Light 1st)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "leveled", "healing"],
        "fields": {"level": 1, "school": "Evocation"},
    },
    {
        "kind": "spell", "name": "Combat Sutra",
        "description": (
            "2nd-level Transmutation. Inscribe an invisible mantra on a "
            "weapon; the wielder adds +1d6 force damage to weapon attacks "
            "for 1 minute. Concentration."
        ),
        "page_ref": "Anime 5E SRD p.154 (Combat Sutra 2nd)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "leveled", "concentration"],
        "fields": {"level": 2, "school": "Transmutation"},
    },
    {
        "kind": "spell", "name": "Genre Pulse",
        "description": (
            "3rd-level Evocation. Pick one damage type the campaign tone "
            "favours (fire for shounen, radiant for magical-girl, "
            "lightning for cyberpunk). All creatures in a 30-ft sphere take "
            "8d6 of that damage on a failed Dexterity save (half on save)."
        ),
        "page_ref": "Anime 5E SRD p.158 (Genre Pulse 3rd)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "leveled", "tone-aware"],
        "fields": {"level": 3, "school": "Evocation"},
    },
    {
        "kind": "spell", "name": "Stage Reset",
        "description": (
            "5th-level Conjuration. Each willing creature within 60 ft "
            "may teleport up to 30 ft to an unoccupied space they can see. "
            "Useful for mid-act battlefield repositioning or dramatic "
            "rescue setups."
        ),
        "page_ref": "Anime 5E SRD p.166 (Stage Reset 5th)",
        "source": "Anime 5E SRD v1.01",
        "tags": ["spell", "leveled"],
        "fields": {"level": 5, "school": "Conjuration"},
    },
]

# ─── WEAPONS (8) ────────────────────────────────────────────────────────
WEAPONS = [
    {"kind": "weapons", "name": "Katana",
     "description": "Versatile single-edged longsword; 1d10 slashing one-handed (1d12 two-handed). Iconic of samurai-flavoured campaigns.",
     "page_ref": "Anime 5E SRD p.182", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "martial-melee"],
     "fields": {"damage": "1d10 slashing", "props": ["versatile (1d12)"], "category": "Martial Melee"}},
    {"kind": "weapons", "name": "Wakizashi",
     "description": "Companion blade to the katana; 1d6 slashing, finesse, light. Often paired for the Two Weapon Style.",
     "page_ref": "Anime 5E SRD p.182", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "martial-melee"],
     "fields": {"damage": "1d6 slashing", "props": ["finesse", "light"], "category": "Martial Melee"}},
    {"kind": "weapons", "name": "Naginata",
     "description": "Polearm with a long curved blade; 1d10 piercing, reach, two-handed. Favoured by warrior-monks.",
     "page_ref": "Anime 5E SRD p.183", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "polearm"],
     "fields": {"damage": "1d10 piercing", "props": ["reach", "two-handed"], "category": "Martial Melee"}},
    {"kind": "weapons", "name": "Yumi (Bow)",
     "description": "Asymmetric Japanese longbow; 1d8 piercing, range 150/600, heavy, two-handed.",
     "page_ref": "Anime 5E SRD p.184", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "ranged"],
     "fields": {"damage": "1d8 piercing", "props": ["heavy", "range 150/600", "two-handed"], "category": "Martial Ranged"}},
    {"kind": "weapons", "name": "Shuriken",
     "description": "Throwing star kit (assume 10 charges); 1d4 piercing, finesse, light, thrown 20/60.",
     "page_ref": "Anime 5E SRD p.184", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "ranged", "thrown"],
     "fields": {"damage": "1d4 piercing", "props": ["finesse", "light", "thrown 20/60"], "category": "Martial Ranged"}},
    {"kind": "weapons", "name": "Concept Blade",
     "description": "A weapon shaped from will or memory, attuned during the Pilot's Sortie Lock or a Magical Girl's Transformation; 2d6 force, soulbound, versatile (2d8).",
     "page_ref": "Anime 5E SRD p.186", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "soulbound"],
     "fields": {"damage": "2d6 force", "props": ["soulbound", "versatile (2d8)"], "category": "Soulbound Melee"}},
    {"kind": "weapons", "name": "Mecha Cannon",
     "description": "Vehicle-mounted heavy weapon; 4d10 force, heavy, vehicle-mount, range 300/1200. Fired by a Pilot during a sortie.",
     "page_ref": "Anime 5E SRD p.188", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "mecha"],
     "fields": {"damage": "4d10 force", "props": ["heavy", "vehicle-mount", "range 300/1200"], "category": "Vehicle Ranged"}},
    {"kind": "weapons", "name": "Kusarigama",
     "description": "Sickle attached to a weighted chain; 1d6 slashing, reach, finesse, trip property (target rolls Dex save vs prone on a hit).",
     "page_ref": "Anime 5E SRD p.183", "source": "Anime 5E SRD v1.01",
     "tags": ["weapon", "exotic"],
     "fields": {"damage": "1d6 slashing", "props": ["reach", "finesse", "trip"], "category": "Martial Melee"}},
]

# ─── ARMOR (4) ─────────────────────────────────────────────────────────
ARMOR = [
    {"kind": "armor", "name": "School Uniform (reinforced)",
     "description": "Concealable kevlar weave under the standard uniform; AC 11 + DEX (cap 4), no stealth penalty. Common in modern-school games.",
     "page_ref": "Anime 5E SRD p.192", "source": "Anime 5E SRD v1.01",
     "tags": ["armor", "light"],
     "fields": {"category": "Light", "ac": "11 + DEX (cap 4)"}},
    {"kind": "armor", "name": "Idol Stage Garb",
     "description": "Charisma-keyed stage costume with reinforced support; AC 11 + Charisma modifier (Idol-class only). Glamour-resistant fabric protects against minor cantrips.",
     "page_ref": "Anime 5E SRD p.193", "source": "Anime 5E SRD v1.01",
     "tags": ["armor", "light", "idol"],
     "fields": {"category": "Light", "ac": "11 + CHA mod"}},
    {"kind": "armor", "name": "Cyber Mail",
     "description": "Linked smart-armor plates with kinetic dampers; AC 14 + DEX (max 2). Common in cyberpunk arcs.",
     "page_ref": "Anime 5E SRD p.194", "source": "Anime 5E SRD v1.01",
     "tags": ["armor", "medium"],
     "fields": {"category": "Medium", "ac": "14 + DEX (max 2)"}},
    {"kind": "armor", "name": "Mecha Frame",
     "description": "Pilot-bonded combat suit. AC 18 + pilot modifier (Pilot's Constitution mod by default). Stealth disadvantage; hostile environments survivable.",
     "page_ref": "Anime 5E SRD p.196", "source": "Anime 5E SRD v1.01",
     "tags": ["armor", "vehicle", "mecha"],
     "fields": {"category": "Vehicle", "ac": "18 + pilot mod"}},
]

# ─── ITEMS (10) — gear, consumables, plot keepsakes ─────────────────────
ITEMS = [
    {"kind": "items", "name": "Power Limiter Bracelet",
     "description": "While worn, suppresses one of the wearer's Attributes by one functional level. Plot device — removed only at narrative beats. Costs nothing in gold; emotional cost paid in arcs.",
     "page_ref": "Anime 5E SRD p.202", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "plot"], "fields": {"weight_lb": 0.2}},
    {"kind": "items", "name": "Bento Box (3 meals)",
     "description": "Hand-prepared lunch in a tiered container. Sharing once per day during a short rest grants 1d4 hit points to one ally beyond the usual hit-die spend.",
     "page_ref": "Anime 5E SRD p.203", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "consumable", "social"],
     "fields": {"cost": "1 sp", "weight_lb": 1}},
    {"kind": "items", "name": "Walkman / Earbuds",
     "description": "Personal audio player. While listening, gain advantage on one Charisma (Performance) check per scene as you cue exactly the right track.",
     "page_ref": "Anime 5E SRD p.204", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "social"],
     "fields": {"cost": "5 sp", "weight_lb": 0.1}},
    {"kind": "items", "name": "Spirit-Sealing Ofuda",
     "description": "Inscribed paper talisman. Adhered to a surface, blocks low-tier spirits (CR 1 or less) for 1 hour. Burns away on dispel.",
     "page_ref": "Anime 5E SRD p.205", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "supernatural"],
     "fields": {"cost": "1 gp", "weight_lb": 0.1}},
    {"kind": "items", "name": "Mecha Repair Kit",
     "description": "Tinker-grade repair kit for a Pilot's bonded vehicle; restores 2d10 hit points to a vehicle/mecha during a long rest.",
     "page_ref": "Anime 5E SRD p.206", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "mecha"],
     "fields": {"cost": "50 gp", "weight_lb": 10}},
    {"kind": "items", "name": "Idol Concert Pass",
     "description": "Backstage entry to one named venue or event. Re-usable until the event ends. NPC-flavoured.",
     "page_ref": "Anime 5E SRD p.207", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "social"],
     "fields": {"cost": "10 gp", "weight_lb": 0}},
    {"kind": "items", "name": "Charm Bracelet (Familiar Bond)",
     "description": "Bonded with a Magical Trainee's familiar. Once per long rest, may resummon a banished familiar instantly.",
     "page_ref": "Anime 5E SRD p.208", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "magical-girl"],
     "fields": {"weight_lb": 0.1}},
    {"kind": "items", "name": "Cyberdeck (Light)",
     "description": "Portable hacker's rig. +5 to Hacker's-kit checks; can run one daemon program at a time. Common loadout for Cyberpunk Runner.",
     "page_ref": "Anime 5E SRD p.209", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "cyberpunk"],
     "fields": {"cost": "200 gp", "weight_lb": 2}},
    {"kind": "items", "name": "Schoolyard Bokken",
     "description": "Wooden practice sword. 1d6 bludgeoning, treats as a 'safe' weapon in non-combat school settings.",
     "page_ref": "Anime 5E SRD p.210", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "weapon"],
     "fields": {"cost": "5 sp", "weight_lb": 2}},
    {"kind": "items", "name": "Vending-Machine Energy Drink",
     "description": "Convenience-store classic. Drink as a bonus action to gain 1d4 temporary HP and end Exhaustion 1 once per long rest.",
     "page_ref": "Anime 5E SRD p.211", "source": "Anime 5E SRD v1.01",
     "tags": ["item", "consumable"],
     "fields": {"cost": "5 sp", "weight_lb": 0.5}},
]

# ─── POWER PACKS (3) — narrative source-of-power bundles for hybrids ───
POWER_PACKS = [
    {"kind": "power_pack", "name": "Magical Girl Transformation Suite",
     "description": "Always-active when transformed: +5 ft speed, +1 AC, advantage on Performance checks while in costume. Includes the canonical transformation sequence as a free narrative beat.",
     "page_ref": "Anime 5E SRD p.222 (Power Pack guide)",
     "source": "Anime 5E SRD v1.01", "tags": ["power-pack", "magical-girl"],
     "fields": {"cost": 6, "kind": "power_pack"}},
    {"kind": "power_pack", "name": "Mecha Pilot Implant",
     "description": "Surgical neural link between Pilot and bonded vehicle. Always-on while sortied: vehicle gains advantage on initiative checks, Pilot rolls vehicle attacks at +proficiency.",
     "page_ref": "Anime 5E SRD p.224 (Power Pack guide)",
     "source": "Anime 5E SRD v1.01", "tags": ["power-pack", "mecha"],
     "fields": {"cost": 8, "kind": "power_pack"}},
    {"kind": "power_pack", "name": "Cyber Augment Suite",
     "description": "Subdermal chrome and reflex booster. Always-active: +1 to initiative, immune to surprise from purely natural sources. Replaces gear in 1 hand slot.",
     "page_ref": "Anime 5E SRD p.226 (Power Pack guide)",
     "source": "Anime 5E SRD v1.01", "tags": ["power-pack", "cyberpunk"],
     "fields": {"cost": 5, "kind": "power_pack"}},
]

# ─── POWER BUNDLES (4) — activatable spell-like packets ────────────────
POWER_BUNDLES = [
    {"kind": "power_bundle", "name": "Beam Cannon",
     "description": "Channel mana into a single ranged attack. Deal 4d6 force damage on hit, range 60 ft. 1 charge per long rest.",
     "page_ref": "Anime 5E SRD p.230 (Power Bundle guide)",
     "source": "Anime 5E SRD v1.01", "tags": ["power-bundle", "blast"],
     "fields": {"cost": 5, "invocation": "per-charge", "charges_max": 1, "kind": "power_bundle"}},
    {"kind": "power_bundle", "name": "Healing Hands",
     "description": "Touch an ally to restore 2d8 + spellcasting mod hit points. 3 charges per long rest.",
     "page_ref": "Anime 5E SRD p.231 (Power Bundle guide)",
     "source": "Anime 5E SRD v1.01", "tags": ["power-bundle", "healing"],
     "fields": {"cost": 4, "invocation": "per-charge", "charges_max": 3, "kind": "power_bundle"}},
    {"kind": "power_bundle", "name": "Phase Step",
     "description": "Once per scene as a bonus action, briefly slip out of phase: gain 30 ft of unimpeded movement that ignores difficult terrain and opportunity attacks.",
     "page_ref": "Anime 5E SRD p.232 (Power Bundle guide)",
     "source": "Anime 5E SRD v1.01", "tags": ["power-bundle", "movement"],
     "fields": {"cost": 3, "invocation": "per-scene", "kind": "power_bundle"}},
    {"kind": "power_bundle", "name": "Rallying Cry",
     "description": "Shout a heartfelt anime-style speech: allies within 30 ft gain 1d6 temporary HP and advantage on the next saving throw vs. fear or charm. 1 charge per short rest.",
     "page_ref": "Anime 5E SRD p.233 (Power Bundle guide)",
     "source": "Anime 5E SRD v1.01", "tags": ["power-bundle", "social"],
     "fields": {"cost": 4, "invocation": "per-charge", "charges_max": 1, "kind": "power_bundle"}},
]

# Master roll-up
SEED_ENTRIES = (
    CLASS_FEATURES + RACE_TRAITS + BACKGROUNDS + FEATS + SPELLS
    + WEAPONS + ARMOR + ITEMS + POWER_PACKS + POWER_BUNDLES
)
# 5 + 8 + 8 + 10 + 8 + 8 + 4 + 10 + 3 + 4 = 68 entries
