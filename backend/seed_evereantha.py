"""Evereantha — canonical seed data for Table-Gnostic.

Sourced from the user-supplied "Artisan's Tale" manuscript (public artifact).
ALL prose / lore / characters / places below are user-provided original setting
material — no third-party copyright applies. BESM 4E mechanic references
(attribute/defect/skill names + page numbers) are mechanic-only per the
Tri-Stat Emporium Community Content licence.

Three apprentice artisans on their Maiden Adventure across Aurea:

    Eli     · Apocophae (alchemist)        — token green
    Laryk   · Ferrilith (earth-smith monk)  — token bronze
    Roney   · Techgnostic (tinker)          — token copper

Plus a full World Codex (places, factions, NPCs, bestiary, the Order of the
Darkening Star nemesis) and an Atelier/Genesis pre-fill following the Sclanders
"Great GM" framework.
"""

# ───────────────────────────── PLAYER CHARACTERS ─────────────────────────────

EVEREANTHA_PCS = [
    # ---------- 1. Eli — Apocophae (alchemist apprentice) ----------
    {
        "name": "Eli",
        "concept": "Apocophae apprentice — alchemist of Eagles Nest, haunted by the Stranger",
        "power_level": "Adventurous",
        "total_points": 80,
        "token_color": "#5fa37a",  # apothecary green
        "size": "Medium",
        "stats": {"body": 4, "mind": 7, "soul": 6},  # 17
        "attributes": [
            {"name": "Healing", "level": 3, "cost_per_level": 4,
             "enhancements": ["Range"], "limiters": ["Consumable"], "page": 96,
             "note": "Tinctures bottled in cut glass — purple for sleep, green for clotting, orange for stamina."},
            {"name": "Item", "level": 6, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 100,
             "note": "Apothecary bandolier — twelve vials slotted into oiled leather, each labelled in her own hand."},
            {"name": "Heightened Senses", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 96,
             "note": "Trained nose: names a tincture by scent at five paces and a poison at three."},
            {"name": "Cognition", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 84,
             "note": "Apocophean composition tables, dosage by body-mass, antidote chains."},
            {"name": "Sixth Sense", "level": 1, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 124,
             "note": "Senses the absence of sound before predators strike — the silence before the Andrewsarchus."},
            {"name": "Wealth", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 132,
             "note": "Tinctures barter briskly across Aurea — never coin, but credit at every guildhouse."},
        ],
        "skills": [
            {"group": "Apocophae Discipline", "level": 3, "cost_per_level": 2, "page": 120,
             "note": "Lesser Group — gather, infuse, dose, dispense.",
             "components": [
                 {"name": "Foraging", "level": 1, "note": "Identify and harvest reagents from forest, mountain, cave."},
                 {"name": "Brewing", "level": 1, "note": "Compose and stabilise a tincture under field conditions."},
                 {"name": "Diagnosis", "level": 1, "note": "Read symptoms, dose by mass, choose the right vial."},
                 {"name": "Reagent Lore", "level": 1, "note": "Know which flora yields what — by scent, by region, by season."},
             ]},
        ],
        "defects": [
            {"name": "Phobia", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 156,
             "note": "Tall hooded strangers — a memory of childhood, the Stranger Artisan who saw her."},
            {"name": "Recurring Nightmares", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 158,
             "note": "The Stranger's silhouette returns on the third night of every journey."},
            {"name": "Marked", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 154,
             "note": "Herb-pigment stains permanent on her fingertips and forearms — every Apocophae can be read by them."},
        ],
        "power_packs": [
            {"name": "Apocophae's Field Kit",
             "description": "The barter-certified working kit of an Apocophae apprentice — a glass-and-leather "
                            "bandolier of tinctures, a folding mortar-pestle, a tin of preserving wax, and a "
                            "small folio of recipe cards in her master's hand.",
             "references": ["Healing", "Item", "Heightened Senses", "Apocophae Discipline"],
             "cost": 0},
        ],
        "folio": {
            "aliases": ["Eli of Eagles Nest", "Glasshands"],
            "gender_species_age": "Human · 19 · woman",
            "occupation": "Apocophae apprentice, on Maiden Adventure",
            "physical_description": "Compact and wiry, hands stained green-purple to the wrists, "
                                    "auburn hair tied back with a strip of waxed leather. A staff "
                                    "of polished rowan, head capped in dull copper.",
            "personality_traits": "Watchful, measured, generous with elixirs. Smiles slowly and rarely.",
            "motivations": "Earn the barter certificate. Prove the Stranger does not own her.",
            "fears_weaknesses": "The Stranger Artisan. Running out of glass.",
            "edges": ["Reads bodies before they speak", "Knows when a forest goes silent"],
            "obstacles": ["Cannot mix in motion", "Trauma response on sight of hooded travellers"],
            "goals": [
                {"title": "Return to Eagles Nest with a barter certificate", "kind": "long",
                 "note": "The whole reason for the journey."},
                {"title": "Brew the cataclysm-soil reagent at the Solar/Lunar site", "kind": "short",
                 "note": "Master Caryana's last assignment before departure."},
            ],
            "family": [
                {"name": "Master Caryana", "relation": "alchemy master", "note": "Eagles Nest's senior Apocophae, gave Eli her first vial."},
            ],
            "history_events": [
                {"date": "age 7", "title": "The Stranger Artisan",
                 "note": "A hooded artisan saw her in the dyer's stall. Said nothing. Left a green coin. The coin vanished by morning."},
                {"date": "age 14", "title": "First successful tincture",
                 "note": "Stabilised a Serenitas calmative without scorching the glass."},
            ],
            "journal": [],
        },
        "published": True,
    },

    # ---------- 2. Laryk — Ferrilith (earth-smith / monk apprentice) ----------
    {
        "name": "Laryk",
        "concept": "Ferrilith apprentice — eastern monk-smith of Eagles Nest, shaper of stone and iron",
        "power_level": "Adventurous",
        "total_points": 80,
        "token_color": "#a26a3c",  # forge bronze
        "size": "Medium",
        "stats": {"body": 6, "mind": 4, "soul": 5},  # 15
        "attributes": [
            {"name": "Massive Damage", "level": 1, "cost_per_level": 3,
             "enhancements": [], "limiters": [], "page": 102,
             "note": "Hammer-strikes that crater stone. Damage Multiplier +5 per Level."},
            {"name": "Tough", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 132,
             "note": "Lifelong forge work — soot-black palms, iron-thick wrists."},
            {"name": "Heavy Armour", "level": 2, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Restricted (worn smith's leathers)"], "page": 96,
             "note": "Boiled-leather and steel-plated apron, hammered by his own hand."},
            {"name": "Special Movement", "level": 1, "cost_per_level": 2,
             "enhancements": [], "limiters": [], "page": 124,
             "note": "Earth-Stride — sets foot on stone and the stone steadies him; never slips on slate or shale."},
            {"name": "Item", "level": 4, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 100,
             "note": "Smithing tools — spike hammer, twin tongs, folding bellows, a pouch of iron stakes."},
            {"name": "Special Attack", "level": 1, "cost_per_level": 4,
             "enhancements": ["Penetrating (Armour)"], "limiters": [], "page": 126,
             "note": "Hammer & Forge — a rising overhead strike that splits a shield like kindling."},
            {"name": "Cognition", "level": 1, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 84,
             "note": "Reads the grain of stone the way a tracker reads grass."},
        ],
        "skills": [
            {"group": "Ferrilith Discipline", "level": 3, "cost_per_level": 2, "page": 120,
             "note": "Lesser Group — shape stone, smith iron, raise wall and stair.",
             "components": [
                 {"name": "Smithing", "level": 1, "note": "Fold, draw, temper iron and bronze in a field forge."},
                 {"name": "Stone-Shaping", "level": 1, "note": "Coax slate, granite, basalt into stair, jack, barrier."},
                 {"name": "Engineering", "level": 1, "note": "Plan a passable bridge across a Montes ravine in under a turn."},
                 {"name": "Survivalist", "level": 1, "note": "Stone-hearth, banked fire, lichen tea."},
             ]},
        ],
        "defects": [
            {"name": "Inept", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 154,
             "note": "Inept · Social. Speaks in single words. Negotiates only through the work."},
            {"name": "Obscure", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 156,
             "note": "Eastern monkhood — few in Aurea know what a Ferrilith is sworn to."},
            {"name": "Vow", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 160,
             "note": "Will not strike a forge-mate, even in self-defence. Will break the forge before the bond."},
        ],
        "power_packs": [
            {"name": "Ferrilith's Anvil",
             "description": "A travelling artisan-monk's working set — folding bellows, twin tongs, a "
                            "spike-hammer wrapped in oiled leather, and a pouch of iron stakes hot "
                            "off the apprentice forge.",
             "references": ["Item", "Special Attack", "Heavy Armour", "Ferrilith Discipline"],
             "cost": 0},
        ],
        "folio": {
            "aliases": ["Laryk of Eagles Nest", "Stone-Foot"],
            "gender_species_age": "Human · 21 · man",
            "occupation": "Ferrilith apprentice, on Maiden Adventure",
            "physical_description": "Heavy-shouldered, weather-burnt, an iron prayer cord tied around "
                                    "the right wrist. Hair shaved to bristle. Always carries his hammer.",
            "personality_traits": "Stoic, observant, generous with strength. Lets others carry the words.",
            "motivations": "Bring the trio home alive. Earn a place at his master's forge again.",
            "fears_weaknesses": "Watching a forge-mate fall and being unable to lift them.",
            "edges": ["Carries twice his own weight without slowing", "Reads stone the way Eli reads herbs"],
            "obstacles": ["Cannot bargain", "Refuses to retreat from a wounded ally"],
            "goals": [
                {"title": "Forge a hammer at the Solar/Lunar Caldera", "kind": "long",
                 "note": "Cataclysm-glass + Aurean iron — Master Davalan's old riddle."},
            ],
            "family": [
                {"name": "Master Davalan", "relation": "Ferrilith master", "note": "Aging eastern monk-smith of Eagles Nest."},
            ],
            "history_events": [
                {"date": "age 9", "title": "First raised barrier",
                 "note": "Pulled a hip-high jack of slate up from a streambed during a flood drill."},
                {"date": "age 17", "title": "Took the iron cord",
                 "note": "Sworn into the Ferrilith order. The cord never leaves his wrist."},
            ],
            "journal": [],
        },
        "published": True,
    },

    # ---------- 3. Roney — Techgnostic (tinker apprentice) ----------
    {
        "name": "Roney",
        "concept": "Techgnostic apprentice — tinker-wright of Eagles Nest, builder of clever, dangerous things",
        "power_level": "Adventurous",
        "total_points": 80,
        "token_color": "#c87a32",  # tinker copper
        "size": "Medium",
        "stats": {"body": 4, "mind": 7, "soul": 5},  # 16
        "attributes": [
            {"name": "Item", "level": 8, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 100,
             "note": "Tinker harness — pocket gadgets, brass clockwork, a folding screwdriver, a pouch of springs."},
            {"name": "Special Attack", "level": 1, "cost_per_level": 4,
             "enhancements": ["Area Effect"], "limiters": ["Limited Shots"], "page": 126,
             "note": "Concussive Instrument — a cast-brass tube that unfolds into a horn-shape and detonates."},
            {"name": "Special Attack", "level": 1, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Limited Shots"], "page": 126,
             "note": "Pocket Lamp — a thumb-sized burst of unbearable white light. Three uses before recharge."},
            {"name": "Cognition", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 84,
             "note": "Sees the linkages — gears, fluids, springs, the hidden geometry of any mechanism."},
            {"name": "Speed", "level": 1, "cost_per_level": 2,
             "enhancements": [], "limiters": [], "page": 132,
             "note": "Quick hands. Rebinds a broken trap before it springs."},
            {"name": "Heightened Senses", "level": 1, "cost_per_level": 1,
             "enhancements": [], "limiters": [], "page": 96,
             "note": "Sharp eyes for hairline cracks and stress fatigue in metal and bone."},
            {"name": "Gadgets", "level": 1, "cost_per_level": 4,
             "enhancements": [], "limiters": [], "page": 92,
             "note": "Once per scene — pulls something useful out of the harness that he'd built earlier and forgot about."},
        ],
        "skills": [
            {"group": "Techgnostic Discipline", "level": 3, "cost_per_level": 2, "page": 120,
             "note": "Lesser Group — design, fabricate, repair, improvise.",
             "components": [
                 {"name": "Mechanics", "level": 1, "note": "Diagnose, dismantle, reassemble any mechanism in the field."},
                 {"name": "Tinkering", "level": 1, "note": "Improvise on the spot from scavenged parts."},
                 {"name": "Drafting", "level": 1, "note": "Sketches that other artisans can actually build from."},
                 {"name": "Lockpicking", "level": 1, "note": "Brass and bone locks — the Aurean travelling kind."},
             ]},
        ],
        "defects": [
            {"name": "Easily Distracted", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 152,
             "note": "Will follow a clever sound through any door — even a dangerous one."},
            {"name": "Marked", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 154,
             "note": "An Order of the Darkening Star sigil — burned into the inside lid of his harness, origin unknown."},
            {"name": "Awkward Size", "rank": 1, "points_per_rank": 1, "category": "Lesser", "page": 150,
             "note": "Carries a rescued Andrewsarchus cub in his pack. The pack is no longer a pack."},
        ],
        "power_packs": [
            {"name": "Techgnost's Workbench",
             "description": "A canvas harness on a folding brass frame — fingers can reach anywhere on his "
                            "body without dropping it. Pocket gadgets within easy reach: light burst, "
                            "concussive instrument, and an ever-changing assortment of springs and "
                            "half-finished prototypes.",
             "references": ["Item", "Special Attack", "Cognition", "Techgnostic Discipline"],
             "cost": 0},
        ],
        "folio": {
            "aliases": ["Roney of Eagles Nest", "Two-Hands"],
            "gender_species_age": "Human · 18 · man",
            "occupation": "Techgnostic apprentice, on Maiden Adventure",
            "physical_description": "Slight, copper-haired, freckled, hands black with grease no soap "
                                    "removes. A brass-framed canvas harness rides on his back — and "
                                    "from the top of it, a wide-eyed Andrewsarchus cub watches you.",
            "personality_traits": "Curious past sense. Enthusiastic past patience. Loyal past argument.",
            "motivations": "Build the impossible thing. Protect the cub. Make Master Halnen proud.",
            "fears_weaknesses": "The Order's sigil in his harness — he doesn't remember when it appeared.",
            "edges": ["Improvises a fix from any three objects", "Reads gear meshing the way a bard reads voice"],
            "obstacles": ["Will rush into a noise he can't explain", "Refuses to leave the cub"],
            "goals": [
                {"title": "Build the cub a working mechanical tail and hind-leg", "kind": "long",
                 "note": "Ongoing project — current limb is iteration four."},
                {"title": "Find out who burned the Order's sigil into his harness", "kind": "secret",
                 "note": "Has not told Eli or Laryk. Will. Eventually."},
            ],
            "family": [
                {"name": "Master Halnen", "relation": "Techgnostic master", "note": "Eagles Nest's tinker-wright; missing two fingers and prouder of it than of his guild rank."},
            ],
            "history_events": [
                {"date": "age 11", "title": "First gadget that did what it was supposed to",
                 "note": "A cooking-fire bellows that ran on a single wound spring for two whole minutes."},
                {"date": "age 18", "title": "Found the cub",
                 "note": "Maiden Adventure, week two — the Andrewsarchus mother dead, the cub crawling."},
            ],
            "journal": [],
        },
        "published": True,
    },
]


# ───────────────────────────── WORLD CODEX (NODES) ───────────────────────────

EVEREANTHA_NODES = [
    # ----- LOCATIONS -----
    {"type": "location", "title": "Aurea",
     "tags": ["country", "core"], "visibility": "shared",
     "content": (
         "The kingdom of Aurea spans a temperate, magic-soaked landscape — golden-leaved "
         "forests in the south, the Montes Inexpugnabilis range to the north, and the "
         "scarred basin of the Solar/Lunar Caldera at the centre. Aurea has no minted "
         "currency. All trade flows through Barter, regulated by the Artisans Guild and "
         "their network of master-certified shops. Prestige is the only true wealth."
     )},
    {"type": "location", "title": "Eagles Nest",
     "tags": ["hamlet", "starting-area"], "visibility": "shared",
     "content": (
         "A hamlet of about forty single-family huts, arranged around farm and irrigation "
         "ponds with a centrally located lord's manor. Six weeks' travel from Aurea's "
         "capital. Home to the three apprentices: Eli, Laryk, and Roney. The Mayor "
         "(also the manor lord) is the only authority empowered to award Barter "
         "Certificates on the apprentices' return."
     )},
    {"type": "location", "title": "Golden Forests of Aurea",
     "tags": ["wilderness", "biome"], "visibility": "shared",
     "content": (
         "A vast forest of golden-leaved trees that hold colour year-round. Home to "
         "rare flora the Apocophae harvest and to creatures of inherent magical "
         "essence. The Lancing Andrewsarchus does not hunt here — but its kin pass "
         "through the northern reaches in late autumn."
     )},
    {"type": "location", "title": "Montes Inexpugnabilis",
     "tags": ["mountains", "biome"], "visibility": "shared",
     "content": (
         "An impassable-by-name range. Internal running falls and underground ponds. "
         "Cave systems rich in luminescent rock and bio-luminescent flora. The "
         "Ferrilith order trains in its lower passes; the upper passes are where stone "
         "is said to listen back."
     )},
    {"type": "location", "title": "The Solar / Lunar Caldera",
     "tags": ["cataclysm", "lore"], "visibility": "gm_only",
     "content": (
         "Ancient site of the Solar and Lunar Temple, destroyed in a volcanic cataclysm "
         "whose cause the Order of the Darkening Star claims to know. The basin is "
         "scarred glass and black stone for ten miles around. Reagents harvested here "
         "behave wrongly — but powerfully."
     )},

    # ----- FACTIONS -----
    {"type": "faction", "title": "The Artisans Guild",
     "tags": ["guild", "barter-regulators"], "visibility": "shared",
     "content": (
         "The overarching organisation that ratifies Barter Certificates and chains "
         "masters to apprentices through the recognised Disciplines: Apocophae "
         "(alchemy), Ferrilith (smith-monk), Techgnostic (tinkering), Faunamimic "
         "(wild-empath), and others. Without a guild seal no Aurean shop will trade."
     )},
    {"type": "faction", "title": "The Order of the Darkening Star",
     "tags": ["nemesis", "secret"], "visibility": "gm_only",
     "content": (
         "A cult-fellowship that believes the Solar/Lunar Cataclysm was a victory, "
         "not a tragedy. Its sigil — a five-pointed star with one ray blackened — "
         "appears burned into objects across Aurea, often without the bearer's "
         "knowledge. The Order recruits artisans by leaving green coins with an "
         "implicit debt."
     )},

    # ----- NPCs -----
    {"type": "npc", "title": "Mayor of Eagles Nest",
     "tags": ["mayor", "manor-lord"], "visibility": "shared",
     "content": (
         "Reclusive manor lord. Issues Barter Certificates personally and only "
         "after a private interview. Is said to have once been an artisan himself, "
         "though his Discipline is no longer recorded in any guild ledger."
     )},
    {"type": "npc", "title": "The Maid",
     "tags": ["mystery", "manor"], "visibility": "gm_only",
     "content": (
         "A slim figure who keeps the manor's shadows. Watches every artisan who "
         "passes through. Has not been heard to speak in twelve years. Wears the "
         "Order's green coin on a chain under her apron."
     )},
    {"type": "npc", "title": "Nyaulis",
     "tags": ["faunamimic", "wilderness", "ally"], "visibility": "shared",
     "content": (
         "A Faunamimic — hunter, trapper, shape-changer between a grizzled fur-clad "
         "elder and a younger almost-human form. Empathetic to wildlife to a fault. "
         "Demands apologies for what is taken from his forest. Wears Laryk's iron "
         "stakes and a dark shin-guard set forged on the road."
     )},
    {"type": "npc", "title": "Mishtee",
     "tags": ["artisan", "bowyer"], "visibility": "shared",
     "content": (
         "Travelling artisan, sister-in-bond to Malshe. Carries a horn-tipped bow "
         "older than she is. Pragmatic, jaded, calls a thing a thing. Has lost two "
         "of her party already this year and will not lose another."
     )},
    {"type": "npc", "title": "Frock",
     "tags": ["artisan", "wounded", "mystery"], "visibility": "shared",
     "content": (
         "A travelling artisan with a wound that will not heal. The flesh around it "
         "darkens but does not rot in the usual way; Eli's tinctures cannot close it. "
         "Frock himself does not seem to know how he came by it."
     )},
    {"type": "npc", "title": "Malshe",
     "tags": ["artisan", "rumour-monger"], "visibility": "shared",
     "content": (
         "A travelling artisan with bracers of years' wear. Knows every Aurean "
         "rumour and the price of repeating each one. Fascinated by the cub in "
         "Roney's pack — and was the first to use the word 'Lancing' in earshot."
     )},

    # ----- BESTIARY -----
    {"type": "creature", "title": "Lancing Andrewsarchus",
     "tags": ["apex-predator", "magical", "northern"], "visibility": "shared",
     "content": (
         "Colossal solitary predator (over 9 ft at the shoulders, over 18 ft long, "
         "3+ tons). Magical essence fortifies bone and pelt against ordinary trauma. "
         "Razor-serrated teeth, robust shredding claws, whip-tail with spiked "
         "protrusions, mottled-fur camouflage. Eyes glow with predatory light; reads "
         "heat-signatures and magical auras. Its howl is a magical resonance that "
         "disorients prey across vast distances. Predatory reach: roughly 50 miles."
     )},

    # ----- LORE / QUEST HOOKS -----
    {"type": "lore", "title": "The Barter Economy",
     "tags": ["economy", "core-rule"], "visibility": "shared",
     "content": (
         "Aurea has no coin. Trade is regulated by Need, Desire, Availability, and "
         "Prestige. The Artisans Guild's Barter Certificates are the only universally "
         "honoured currency-equivalent. Without one, no recognised shop in the "
         "kingdom will deal with you above the level of bread and rope."
     )},
    {"type": "lore", "title": "Artisan Disciplines",
     "tags": ["guild", "core-rule"], "visibility": "shared",
     "content": (
         "Recognised Disciplines: Apocophae (alchemy / herbs), Ferrilith "
         "(smith-monkhood), Techgnostic (clever-thing crafting), Faunamimic "
         "(wild-empathy), and others region-specific. Each Discipline has its own "
         "Master-Apprentice chain and its own set of permissible Power Pack "
         "bundles in the Character Forge."
     )},
    {"type": "quest", "title": "The Maiden Adventure",
     "tags": ["main-thread", "starting-quest"], "visibility": "shared",
     "content": (
         "Six weeks into the Aurean wilds. Bring back proof of mastery — a "
         "physical artefact crafted under field conditions plus a witnessed story "
         "of risk faced. The Mayor of Eagles Nest will then award the Barter "
         "Certificate. The route is the apprentice's choice; the deadline is not."
     )},
    {"type": "quest", "title": "The Cataclysm Reagent",
     "tags": ["secondary", "apocophae"], "visibility": "shared",
     "content": (
         "Master Caryana has tasked Eli with bringing back a stoppered vial of "
         "soil from the Solar/Lunar Caldera basin. Cataclysm-soil is unstable and "
         "may not survive the trip — but a single working sample would let "
         "Caryana finish a tincture she has worked on for thirty years."
     )},
    {"type": "quest", "title": "The Forge-Glass Hammer",
     "tags": ["secondary", "ferrilith"], "visibility": "shared",
     "content": (
         "Master Davalan's old riddle: a hammer forged with cataclysm-glass in its "
         "head, to be carried by a Ferrilith who could lift it. None has, in two "
         "generations. Laryk has not been told the riddle was set for him."
     )},
    {"type": "quest", "title": "The Sigil in the Harness",
     "tags": ["secret", "techgnostic", "order-thread"], "visibility": "gm_only",
     "content": (
         "Roney's harness lid bears the Order's sigil — burned, not painted. He "
         "does not remember when it appeared. The Order has marked him for a "
         "reason. They will come for an answer before the journey ends."
     )},
]


# ────────────────────────── GENESIS / ATELIER PRE-FILL ───────────────────────

EVEREANTHA_GENESIS = {
    # Phase 1 — The Sentence
    "sentence_who": "Three apprentice artisans of Eagles Nest — an Apocophae, a Ferrilith, and a Techgnostic",
    "sentence_wants": "to return home from their Maiden Adventure with proof of mastery and a Barter Certificate",
    "sentence_badly_when": "before the Order of the Darkening Star eclipses Aurea's autumn moon",
    "sentence_using": "their craft, their fledgling power packs, and an uneasy bargain with a Faunamimic",
    "sentence_reasons": "the Order has marked one of them already, and the Cataclysm site is calling all three",
    # Phase 2 — Theme
    "theme": "Coming-of-age artisanry: nature is the crucible, prestige is the only currency, and craft is what stands between the apprentice and the dark.",
    "tone_words": ["mythic", "lyrical", "perilous", "warm-at-the-hearth", "ember-lit"],
    # Phase 3 — Nemesis
    "nemesis_name": "The Order of the Darkening Star",
    "nemesis_type": "cult-fellowship",
    "nemesis_motive": "to finish what the Solar/Lunar Cataclysm began — silence the sky over Aurea and rebuild the world in their sigil's shape",
    "nemesis_resources": "green coins (debts), the Maid in the manor, sigils burned into apprentice gear, agents inside two of Aurea's masters",
    "nemesis_weakness": "the Order cannot operate openly — every action they take must look like an accident, and every accident leaves a trace an alert apprentice could read",
    # Phase 4 — Master Plot acts
    "master_acts": [
        {"title": "Act I · The Maiden Road",
         "beat": "Departure from Eagles Nest. First creatures of the wild. First night under the Golden Forest canopy."},
        {"title": "Act II · Strangers on the Road",
         "beat": "Mishtee, Frock, and Malshe cross paths with the apprentices. Frock's wound. The first whispered name: 'Order of the Darkening Star'."},
        {"title": "Act III · The Faunamimic's Bargain",
         "beat": "Nyaulis's traps catch the apprentices. He demands an apology in craft. Laryk forges his stakes. An uneasy ally is made."},
        {"title": "Act IV · The Lancing Andrewsarchus",
         "beat": "An apex predator hunts the party. The cub is rescued. Roney's harness is now permanently changed."},
        {"title": "Act V · The Caldera",
         "beat": "The Solar/Lunar Caldera is reached. Cataclysm-soil is taken. The Order arrives openly for the first time."},
        {"title": "Act VI · The Mastery",
         "beat": "Return to Eagles Nest. The Mayor's interview. Barter Certificates earned (or refused). The Order's sigil is read in full."},
    ],
    # Phase 5 — Adventure outlines
    "adventures": [
        {"title": "The First Silence", "kind": "exploration",
         "hook": "The forest goes silent on the third night.",
         "stakes": "An Andrewsarchus is within 50 miles. The party must choose: hold ground, run, or hunt back.",
         "outcome": "If they hold, they catch a cub orphan; if they run, the cub is taken by the Order."},
        {"title": "The Faunamimic's Apology", "kind": "social",
         "hook": "Nyaulis's traps catch them in their sleep.",
         "stakes": "He will release them only if they craft something he names. He will only speak in elder-form.",
         "outcome": "Laryk's iron stakes — and a wary alliance that will reappear at the Caldera."},
        {"title": "Frock's Wound", "kind": "investigation",
         "hook": "An artisan's wound that no Apocophae can close.",
         "stakes": "If Eli helps, Frock will tell her what he saw on the Caldera. If Eli refuses, Frock will not last another moon.",
         "outcome": "A green coin found tucked into Frock's bandages. Mishtee swears she did not put it there."},
        {"title": "The Cataclysm Reagent", "kind": "expedition",
         "hook": "Cataclysm-soil at the Solar/Lunar basin.",
         "stakes": "The basin is unstable and tests every Discipline at once. The Order is also harvesting.",
         "outcome": "One vial of viable cataclysm-soil; one direct sighting of a senior Order agent."},
        {"title": "The Mayor's Interview", "kind": "denouement",
         "hook": "Return to Eagles Nest. The Mayor reads each apprentice in private.",
         "stakes": "Barter Certificate or refusal. The refused must do another Maiden Adventure — or leave Aurea.",
         "outcome": "Up to three certificates. The Mayor reveals he was once Apocophae. The Maid is missing."},
    ],
    # Phase 6 — NPCs to seed (the seed-nodes call generates these)
    "seed_npcs": [
        {"name": "Nyaulis", "role": "ally / Faunamimic",
         "note": "Fur-clad elder by day, almost-human youth by firelight. Demands apologies in craft."},
        {"name": "Mishtee", "role": "travelling artisan / bowyer",
         "note": "Pragmatic, has lost two already this year. Will not lose a third."},
        {"name": "Frock", "role": "travelling artisan / wounded",
         "note": "Carries an unhealable wound. Does not remember the cause. The Order knows."},
        {"name": "Malshe", "role": "travelling artisan / rumour-bearer",
         "note": "Bracers of years' wear. Knows every Aurean rumour, and the price of repeating each."},
        {"name": "Mayor of Eagles Nest", "role": "manor lord",
         "note": "Reclusive. Issues Barter Certificates personally. Once an artisan himself."},
        {"name": "The Maid", "role": "shadow of the manor",
         "note": "Has not spoken in twelve years. Wears the Order's green coin on a chain."},
    ],
    # Phase 7 — Beginning + Ending
    "beginning": (
        "The three apprentices receive their masters' farewell letters and the route token "
        "for the Maiden Adventure. The Mayor signs nothing in advance. The party leaves "
        "at dawn. The Maid watches them through the manor window."
    ),
    "ending": (
        "Six weeks later, the Mayor's interview decides whether each apprentice "
        "earns a Barter Certificate or is sent out again. Whatever the verdict, "
        "the Order's sigil in Roney's harness is no longer the only one — Eli's "
        "vial cabinet now bears a green smudge that wipes only at the third "
        "attempt, and Laryk's hammer rings a half-tone flat."
    ),
    "phase_completed": 7,
}


# ────────────────────── CAMPAIGN HEADER (for the wipe-and-reseed) ────────────

EVEREANTHA_CAMPAIGN = {
    "name": "Evereantha — The Maiden Adventure",
    "description": (
        "A coming-of-age tale across the kingdom of Aurea. Three apprentice artisans "
        "leave the hamlet of Eagles Nest on their Maiden Adventure: bring back proof "
        "of mastery, earn a Barter Certificate, and survive long enough to read the "
        "sigil that has begun appearing on apprentice gear across Aurea."
    ),
    "system": "BESM 4E",
    "system_id": "besm-4e",
    "tone": "Mythic, lyrical, perilous-but-warm",
    "genre": "High Fantasy / Artisan-Craft",
    "tags": ["evereantha", "artisans-tale", "BESM-4E", "Aurea"],
    "experience_level": "Beginner-friendly",
    "schedule": "Weekly · 3-hour sessions",
    "max_players": 6,
    "visibility": "public",
    "power_level": "Adventurous",
    "player_primer": (
        "You are an apprentice of the Artisans Guild on your Maiden Adventure. "
        "Your Discipline (Apocophae, Ferrilith, Techgnostic) defines what you "
        "can craft, what you can barter, and how the world reads you. Coin does "
        "not exist in Aurea. Prestige does. The Order of the Darkening Star "
        "exists. You will not see them clearly until Act V."
    ),
    "allowed_attributes": [],
    "prohibited_attributes": [
        # Setting-specific exclusions: no firearms, no off-world tech, no
        # straight-up gods. (Empty here = all allowed; flip to a list to gate.)
    ],
    "allowed_defects": [],
    "prohibited_defects": [],
    "allowed_skill_groups": [],
    "prohibited_skill_groups": [],
    "character_point_min": 70,
    "character_point_max": 90,
    "max_per_attribute_rank": 4,
    "time_period": "Pre-industrial · post-cataclysm fantasy",
    "default_character_size": "Medium",
    "damage_rating_baseline": 5,
}
