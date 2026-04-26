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
    # ---------- 4. Nyaulis — Faunamimic (joins Session 2) ----------
    {
        "name": "Nyaulis",
        "concept": "Faunamimic hermit — shape-shifter, trapper, sworn keeper of a stretch of the Golden Forests",
        "power_level": "Adventurous",
        "total_points": 90,  # slightly above the apprentices — he's seasoned
        "token_color": "#7a5a36",  # weathered fur-cloak brown
        "size": "Medium",
        "stats": {"body": 7, "mind": 6, "soul": 7},
        "attributes": [
            {"name": "Alternate Form (firelight youth ↔ elder hermit)", "level": 2,
             "cost_per_level": 8, "page": 110,
             "enhancements": [], "limiters": ["Fire-source proximity (firelight only)"]},
            {"name": "Heightened Senses (all five, forest-tuned)", "level": 3,
             "cost_per_level": 1, "page": 156,
             "enhancements": ["Detect heat-signature"], "limiters": []},
            {"name": "Tracking", "level": 4, "cost_per_level": 1, "page": 188,
             "enhancements": [], "limiters": ["Native ecosystem only"]},
            {"name": "Companion (forest creatures, summoned)", "level": 2,
             "cost_per_level": 4, "page": 124,
             "enhancements": [], "limiters": ["Local biome only"]},
            {"name": "Weapon (twin iron stakes, by Laryk)", "level": 2,
             "cost_per_level": 2, "page": 196,
             "enhancements": ["Penetrating"], "limiters": ["Reach 1m"]},
        ],
        "defects": [
            {"name": "Marked", "category": "Marked", "rank": 2, "points_per_rank": 1,
             "page": 212, "note": "Three Order green-coin scars on the back of his hand. Refused them all — but they remember him."},
            {"name": "Code of Conduct (forest-keeper's apology rule)", "category": "Conduct",
             "rank": 1, "points_per_rank": 1, "page": 208,
             "note": "Demands an apology in craft from any who take from his stretch of the Golden Forests. Won't bargain on that."},
        ],
        "skills": [
            {"group": "Wilderness", "level": 4, "cost_per_level": 1, "page": 84,
             "components": [
                 {"name": "Tracking", "level": 4, "note": "Reads heat and bent leaves alike."},
                 {"name": "Survival", "level": 4, "note": "Has not slept indoors in nine winters."},
                 {"name": "Animal Handling", "level": 3, "note": "Forest fauna only — will not work with livestock."},
             ]},
            {"group": "Stealth", "level": 3, "cost_per_level": 2, "page": 76,
             "components": [
                 {"name": "Hide", "level": 3, "note": "His pack-brother's lesson — stillness is the first weapon."},
                 {"name": "Move silently", "level": 3, "note": "Even with iron stakes."},
             ]},
        ],
        "power_packs": [],
        "notes": "Joins the apprentices' Maiden Adventure in Session 2 after Laryk forges him twin iron stakes (apology in craft).",
        "folio": {
            "aliases": ["the Elder-In-Furs", "Nyaulis the Trapper"],
            "gender_species_age": "Human · Faunamimic · indeterminate (firelight ~25, elder ~60+)",
            "physical_description": (
                "Grizzled fur-clad elder by daylight. Almost-human youth in firelight — "
                "the same forest patience in either body. Eyes like a forest reading you back."
            ),
            "personality": (
                "Empathetic to wildlife to a fault. Speaks rarely in elder form, almost "
                "never. Demands apologies for what is taken from his forest."
            ),
            "fears": [
                {"title": "A fourth green coin", "kind": "secret",
                 "note": "He has refused three. Suspects a fourth will not be offered."},
            ],
            "goals": [
                {"title": "Protect his stretch of Golden Forests", "kind": "ongoing"},
                {"title": "Repay the apprentices for the iron stakes", "kind": "active",
                 "note": "Walking with them through the Caldera arc."},
            ],
            "family": [
                {"name": "(former pack-brother, deceased)", "relation": "lost twelve winters past",
                 "note": "Killed by a Lancing Andrewsarchus during a kin-pass through the northern reaches."},
            ],
            "history_events": [
                {"date": "12 winters past", "title": "Lost his pack-brother",
                 "note": "Has not crossed the Caldera since."},
                {"date": "Maiden Adventure · S2", "title": "Apology in iron",
                 "note": "Laryk forged twin stakes for the snare-anchors. Joined the apprentices."},
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
     "fields": {
         "scale": "country",
         "loc_type": "kingdom",
         "parent_location": None,
         "geography": "Temperate. Golden-leaved forests in the south, the Montes Inexpugnabilis range to the north, the scarred Solar/Lunar Caldera at the centre.",
         "government": "Decentralised. Manor lords + Artisans Guild councils.",
         "economy": "Pure barter — no coin minted. The Artisans Guild's Barter Certificates are the only universally honoured equivalent of currency.",
         "landmarks": "Solar/Lunar Caldera; Eagles Nest hamlet; Montes Inexpugnabilis pass.",
         "history": "The Solar/Lunar Cataclysm scarred the central basin; the Order of the Darkening Star is rumoured to have known the cause.",
         "inhabitants": "Apocophae, Ferrilith, Techgnostic, Faunamimic — the recognised Disciplines.",
     },
     "content": (
         "The kingdom of Aurea spans a temperate, magic-soaked landscape — golden-leaved "
         "forests in the south, the Montes Inexpugnabilis range to the north, and the "
         "scarred basin of the Solar/Lunar Caldera at the centre. Aurea has no minted "
         "currency. All trade flows through Barter, regulated by the Artisans Guild and "
         "their network of master-certified shops. Prestige is the only true wealth."
     )},
    {"type": "location", "title": "Eagles Nest",
     "tags": ["hamlet", "starting-area"], "visibility": "shared",
     "fields": {
         "scale": "hamlet",
         "loc_type": "hamlet",
         "parent_location": "Aurea",
         "geography": "Forty single-family huts arranged around farm and irrigation ponds. Six weeks' travel from Aurea's capital.",
         "population": "~120 souls (forty households).",
         "government": "Manor lord (the Mayor) — issues Barter Certificates personally.",
         "economy": "Subsistence farming + apprentice-level artisan workshops (Apocophae, Ferrilith, Techgnostic).",
         "landmarks": "The Mayor's manor; the dyer's stall; Master Caryana's apothecary; Master Davalan's forge.",
         "inhabitants": "Eli (Apocophae apprentice); Laryk (Ferrilith apprentice); Roney (Techgnostic apprentice); Master Caryana; Master Davalan; Master Halnen; The Maid.",
         "connections": "Golden Forests to the south; Montes Inexpugnabilis to the north; Solar/Lunar Caldera at the centre.",
     },
     "content": (
         "A hamlet of about forty single-family huts, arranged around farm and irrigation "
         "ponds with a centrally located lord's manor. Six weeks' travel from Aurea's "
         "capital. Home to the three apprentices: Eli, Laryk, and Roney. The Mayor "
         "(also the manor lord) is the only authority empowered to award Barter "
         "Certificates on the apprentices' return."
     )},
    {"type": "location", "title": "Golden Forests of Aurea",
     "tags": ["wilderness", "biome"], "visibility": "shared",
     "fields": {
         "scale": "biome",
         "loc_type": "forest",
         "parent_location": "Aurea",
         "geography": "Vast forest of golden-leaved trees that hold colour year-round. Spans the southern third of Aurea.",
         "inhabitants": "Faunamimic hermits (Nyaulis among them); rare magical flora harvested by the Apocophae.",
         "connections": "Borders Eagles Nest to the south; Montes Inexpugnabilis at the northern treeline.",
     },
     "content": (
         "A vast forest of golden-leaved trees that hold colour year-round. Home to "
         "rare flora the Apocophae harvest and to creatures of inherent magical "
         "essence. The Lancing Andrewsarchus does not hunt here — but its kin pass "
         "through the northern reaches in late autumn."
     )},
    {"type": "location", "title": "Montes Inexpugnabilis",
     "tags": ["mountains", "biome", "border"], "visibility": "shared",
     "fields": {
         "scale": "mountain-range",
         "loc_type": "mountain range",
         "parent_location": "Aurea",
         "geography": "Impassable-by-name range. Forms the southern border of Aurea, separating the kingdom from the lands beyond. Internal running falls and underground ponds; cave systems rich in luminescent rock.",
         "inhabitants": "Ferrilith order trainees in the lower passes; rumoured stone-singers in the upper passes.",
         "connections": "South border of Aurea; northern reach abuts the Golden Forests; Master's Pass cuts through to Eagles Nest.",
     },
     "content": (
         "An impassable-by-name range. Internal running falls and underground ponds. "
         "Cave systems rich in luminescent rock and bio-luminescent flora. The "
         "Ferrilith order trains in its lower passes; the upper passes are where stone "
         "is said to listen back."
     )},
    {"type": "location", "title": "The Solar / Lunar Caldera",
     "tags": ["cataclysm", "lore"], "visibility": "gm_only",
     "fields": {
         "scale": "landmark",
         "loc_type": "scarred basin",
         "parent_location": "Aurea",
         "geography": "Centre of Aurea — ten miles of black-glass basin and basalt scar where the ancient Solar/Lunar Temple stood before the Cataclysm.",
     },
     "content": (
         "Ancient site of the Solar and Lunar Temple, destroyed in a volcanic cataclysm "
         "whose cause the Order of the Darkening Star claims to know. The basin is "
         "scarred glass and black stone for ten miles around. Reagents harvested here "
         "behave wrongly — but powerfully."
     )},

    # ----- PC TWIN NODES (bi-directional sync with character sheets) -----
    # Each PC has a public-facing NPC node so other tables / readers see them
    # in the Knowledge Web. The character sheet remains the source of truth
    # for stats; the node holds narrative description + image hooks.
    {"type": "npc", "title": "Eli",
     "tags": ["pc", "apocophae", "alchemist", "eagles-nest"], "visibility": "shared",
     "fields": {
         "is_player_character": True,
         "linked_character_name": "Eli",
         "discipline": "Apocophae (alchemist)",
         "homeland": "Eagles Nest, Aurea",
         "physical_description": "Wiry build, green-stained fingers, a leather bandolier of corked vials worn high on the ribs. Eyes that read herbs before they read faces.",
         "personality": "Methodical to a fault. Trusts what she can clot, distill, or buffer. Slow to laugh, slower to forget a debt.",
         "motivations": "Earn Barter Certification from Master Caryana. Find what the Stranger wanted with her father.",
         "fears": "That the Stranger came back for her, not him.",
         "affiliations": "Apocophae apprenticeship under Master Caryana. Maiden Adventure trio with Laryk and Roney.",
         "inventory": "Bandolier (cataclysm-soil vial · serenitas-leaf bundle · golden lichen · clotting tincture). Apothecary kit.",
     },
     "content": (
         "Apocophae apprentice from Eagles Nest. Methodical, vial-handed, "
         "scarred by the Stranger her father knew. Travelling the Maiden "
         "Adventure to earn her Barter Certificate."
     )},
    {"type": "npc", "title": "Laryk",
     "tags": ["pc", "ferrilith", "smith-monk", "eagles-nest"], "visibility": "shared",
     "fields": {
         "is_player_character": True,
         "linked_character_name": "Laryk",
         "discipline": "Ferrilith (earth-smith monk)",
         "homeland": "Eagles Nest, Aurea",
         "physical_description": "Bronze-skinned, hands like hearth-stones, a spike-hammer slung across his back. Speaks rarely; what he forges, he says.",
         "personality": "Quiet. Acts in iron. Apologies are stakes; promises are ridges welded into a blade.",
         "motivations": "Match Master Davalan's Hammer-and-Forge stance in the field. Repay Nyaulis in craft, not in word.",
         "fears": "The day a strike doesn't land where the breath says it will.",
         "affiliations": "Ferrilith apprenticeship under Master Davalan. Maiden Adventure trio with Eli and Roney. Sworn-debt to Nyaulis (iron stakes).",
         "inventory": "Spike-hammer (Penetrating, Ferrilith Hammer-and-Forge stance). Travel anvil. Iron ingots, three.",
     },
     "content": (
         "Ferrilith apprentice from Eagles Nest. Earth-smith monk whose "
         "apologies are forged, not spoken. Travelling the Maiden Adventure "
         "to earn his Barter Certificate."
     )},
    {"type": "npc", "title": "Roney",
     "tags": ["pc", "techgnostic", "tinker", "eagles-nest"], "visibility": "shared",
     "fields": {
         "is_player_character": True,
         "linked_character_name": "Roney",
         "discipline": "Techgnostic (tinker)",
         "homeland": "Eagles Nest, Aurea",
         "physical_description": "Lean, copper-haired, a brass-frame harness worn over the shoulders that hosts a half-clockwork creature companion (the cub). Always one tool short of finished.",
         "personality": "Warm, jittery, talks in OOC even when the cub doesn't. Loyal in a way that ignores the cost.",
         "motivations": "Build a harness frame the cub doesn't outgrow. Find out who marked his harness with the Order's sigil — and when.",
         "fears": "That the sigil was always there. That the cub knows.",
         "affiliations": "Techgnostic apprenticeship under Master Halnen. Maiden Adventure trio. Bonded (literally) with the Lancing Andrewsarchus cub.",
         "inventory": "Brass-frame harness (cub mounted). Tinker's tool roll. Pocket lens. A coin Eli told him not to touch — he kept it anyway.",
     },
     "content": (
         "Techgnostic apprentice from Eagles Nest. Brass-harness tinker. "
         "Bonded with a half-clockwork Andrewsarchus cub. Vanished mid-line "
         "at Master's Pass, sigil flaring."
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
     "tags": ["faunamimic", "wilderness", "ally", "pc"], "visibility": "shared",
     "fields": {
         "is_player_character": True,
         "linked_character_name": "Nyaulis",
         "aliases": "Nyaulis the Trapper · the Elder-In-Furs",
         "gender_species_age": "Human · Faunamimic · indeterminate (appears 60+ in elder form, 25 in firelight form)",
         "occupation": "Faunamimic — hunter, trapper, shape-changer; sworn keeper of a stretch of the Golden Forests.",
         "physical_description": "Grizzled fur-clad elder by daylight; in firelight a younger, almost-human form. Eyes hold the same forest patience in both shapes.",
         "personality": "Empathetic to wildlife to a fault. Demands apologies for what is taken from his forest. Speaks rarely, and almost never in elder form.",
         "motivations": "Protect his stretch of forest. Repay the apprentices for the iron stakes Laryk forged him.",
         "fears": "The Order's green coins — he has refused three. He suspects a fourth will not be offered.",
         "affiliations": "Faunamimic Discipline; uneasy alliance with the apprentices after Session 2.",
         "inventory": "Horn-handled knife · twin iron stakes (Laryk's work) · dark shin-guard set forged on the road · a pouch of dried smoke-leaf.",
         "backstory": "Lost his pack-brother to a Lancing Andrewsarchus twelve winters past. Has not crossed the Caldera since. Joined the apprentices in Session 2 after Laryk apologised in craft, not in word.",
     },
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
     "fields": {
         "biology": "Colossal solitary predator (over 9 ft at the shoulders, over 18 ft long, 3+ tons). Magical essence fortifies bone and pelt against ordinary trauma. Razor-serrated teeth, robust shredding claws, whip-tail with spiked protrusions, mottled-fur camouflage.",
         "lifespan": "60–80 years; solitary except during cubbing.",
         "abilities": "Heat-signature and magical-aura sight. Howl is a magical resonance that disorients prey across vast distances. Predatory reach: roughly 50 miles.",
         "weaknesses": "Sated young — a cub raised by humans loses the howl's magical resonance. Pelt seam under the foreleg admits a Penetrating strike (Ferrilith hammer-and-forge style).",
         "relations": "Hunts solo; will not enter the Golden Forests proper, but its kin pass through the northern reaches in late autumn.",
         "origin": "Tradition holds the Lancing Andrewsarchus is a survivor of the pre-Cataclysm bestiary — a creature whose magic predates the Solar/Lunar Temple's fall.",
     },
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



# ────────────────────── 8-SESSION CHRONICLE (V4.4) ──────────────────────────
#
# Pre-recorded chat dialogue, dice rolls, and GM notes for an entire opening
# arc — eight sequential sessions of the Maiden Adventure. Drops into a
# freshly reset Evereantha campaign so a GM can walk into the platform and
# *immediately* see the table at work: in-character lines, /roll outputs,
# GM scene-set narration, and a final cliffhanger.
#
# Continuity rules (per the Artisan's Tale manuscript):
#   * Session 1: departure + first night in Golden Forests.
#   * Session 2: Nyaulis (Faunamimic) traps + apologies-in-craft → JOINS THE PARTY.
#   * Sessions 3–4: travelling artisans (Mishtee, Frock, Malshe) — Frock's wound.
#   * Session 5: First sighting of the Lancing Andrewsarchus + cub rescue.
#   * Session 6: Solar/Lunar Caldera — cataclysm-soil harvest, Order encountered.
#   * Session 7: Frock dies; green coin found; nightmare visions begin.
#   * Session 8: Order ambush at Master's Pass · ends on cliffhanger
#                (Roney's harness sigil flares; he vanishes mid-line).
#
# Format note: each line is either {"speaker", "kind", "text"} or
# {"speaker", "kind": "dice", "notation", "result", "label"}.
# `speaker` matches a PC name (Eli/Laryk/Roney/Nyaulis), "GM" for narration,
# or "" for system-bot messages. `kind` ∈ {chat, action, ooc, system, dice}.

EVEREANTHA_SESSIONS = [
    # ============================ SESSION 1 ============================
    {
        "title": "Session 1 — The Maiden Road",
        "gm_notes": "Departure from Eagles Nest at dawn. The Mayor refuses to sign anything in advance. The Maid watches them through the manor window. First night beneath the Golden Forests' canopy; the trees hold colour even by moonlight.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "Dawn. The hamlet's irrigation ponds steam. Master Caryana, Master Davalan, and Master Halnen stand at the manor gate. The Mayor does not. A folded route token passes from hand to hand. The Maid watches from the upper window."},
            {"speaker": "Eli", "kind": "action", "text": "tucks the cataclysm-soil vial into the third loop of her bandolier — the one closest to her ribs."},
            {"speaker": "Laryk", "kind": "chat", "text": "Six weeks."},
            {"speaker": "Roney", "kind": "chat", "text": "Five weeks if we run. Eight if the cub eats again."},
            {"speaker": "GM", "kind": "system", "text": "The cub trills from the brass-frame harness. Its mechanical hind-leg ticks, off-rhythm by half a beat."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Read the route token", "result": {"total": 11, "rolls": [{"results": [4, 5]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "The token reads simply: GOLDEN FORESTS · MONTES PASS · CALDERA · RETURN. Three weeks out, three back. The Mayor's hand is unmistakable."},
            {"speaker": "Laryk", "kind": "action", "text": "shoulders his spike-hammer and steps onto the road first. Says nothing."},
            {"speaker": "GM", "kind": "system", "text": "The Golden Forest closes around them by midday. Leaves do not fall here — they hold colour. Every branch hums faintly with the Discipline-magic Aurea breathes."},
            {"speaker": "Roney", "kind": "chat", "text": "It's louder than I thought. The trees, I mean. They sound like clockwork."},
            {"speaker": "Eli", "kind": "chat", "text": "That's not the trees. That's the fauna. Listen for the spaces between."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Reagent foraging", "result": {"total": 14, "rolls": [{"results": [5, 2]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "Eli finds Serenitas-leaf and a stand of golden lichen the Apocophae texts prize for clotting. Three doses' worth."},
            {"speaker": "GM", "kind": "system", "text": "Dusk. They make camp in a hollow ringed by gold-barked oaks. The silence is comfortable. For now."},
            {"speaker": "Laryk", "kind": "action", "text": "stacks stones into a hearth and bank-fires it the Ferrilith way — three flat slabs, draught-channel beneath."},
            {"speaker": "Roney", "kind": "ooc", "text": "(everyone roll Soul to see if you sleep — first night out always gets one)"},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+soul", "label": "First-night sleep", "result": {"total": 10, "rolls": [{"results": [3, 1]}, {"ref": "soul", "value": 6}], "flat": 6}},
            {"speaker": "Laryk", "kind": "dice", "notation": "2d6+soul", "label": "First-night sleep", "result": {"total": 13, "rolls": [{"results": [4, 4]}, {"ref": "soul", "value": 5}], "flat": 5}},
            {"speaker": "Roney", "kind": "dice", "notation": "2d6+soul", "label": "First-night sleep", "result": {"total": 8, "rolls": [{"results": [2, 1]}, {"ref": "soul", "value": 5}], "flat": 5}},
            {"speaker": "GM", "kind": "system", "text": "Roney does not sleep. Around the third bell of night the cub climbs out of his harness, wraps itself around his neck, and growls — once — at the dark."},
            {"speaker": "GM", "kind": "system", "text": "End of session. Three apprentices on a road they have never walked. Something hummed back."},
        ],
    },
    # ============================ SESSION 2 ============================
    {
        "title": "Session 2 — The Faunamimic's Apology",
        "gm_notes": "Nyaulis's traps catch the apprentices in their sleep. He demands an apology in craft, not in word. Laryk forges his iron stakes at the road-side hearth. Nyaulis JOINS the party as an uneasy ally for the rest of the arc.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "Pre-dawn. A snare hisses tight. Then a second. Then a third."},
            {"speaker": "Roney", "kind": "ooc", "text": "WHAT"},
            {"speaker": "GM", "kind": "system", "text": "All three are hung from a gold-barked branch by the ankle. Politely. The cub remains in Roney's harness, unimpressed."},
            {"speaker": "GM", "kind": "system", "text": "A figure walks into the clearing. Fur-clad. Grizzled. Older than any of them by forty years. The Faunamimic's eyes hold a forest's patience."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "You took from this wood."},
            {"speaker": "Eli", "kind": "chat", "text": "Three Serenitas leaves. Lichen, two handfuls. I left the roots."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "I know what you took. The forest told me. I am asking what you will give back."},
            {"speaker": "Laryk", "kind": "action", "text": "looks at his hammer. Then at the road. Then back at Nyaulis."},
            {"speaker": "Laryk", "kind": "chat", "text": "Iron."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "Iron is not an apology. Craft is."},
            {"speaker": "GM", "kind": "system", "text": "Nyaulis cuts them down. Sets them on the ground without ceremony. Sits across from the dead hearth. Waits."},
            {"speaker": "Laryk", "kind": "dice", "notation": "2d6+body", "label": "Re-light the hearth + raise stake-anvil", "result": {"total": 10, "rolls": [{"results": [3, 1]}, {"ref": "body", "value": 6}], "flat": 6}},
            {"speaker": "Laryk", "kind": "dice", "notation": "2d6+mind", "label": "Forge twin iron stakes (Smithing)", "result": {"total": 12, "rolls": [{"results": [4, 4]}, {"ref": "mind", "value": 4}], "flat": 4}},
            {"speaker": "GM", "kind": "system", "text": "Two stakes. One for each of Nyaulis's snare-anchors. Hammered while Eli hums something only Apocophae apprentices know."},
            {"speaker": "Nyaulis", "kind": "action", "text": "weighs the stakes in each hand. One. Then the other. Sets them across his thighs."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "I will walk the next ridge with you. You will not be ambushed. After the ridge, we will speak of payment."},
            {"speaker": "Roney", "kind": "ooc", "text": "BRO WE GOT A FAUNAMIMIC"},
            {"speaker": "GM", "kind": "system", "text": "Nyaulis joins the party as ally — fur-clad elder by daylight, almost-human youth by firelight. He does not introduce himself in any other way."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+soul", "label": "Read his bearing — is he Order?", "result": {"total": 9, "rolls": [{"results": [2, 1]}, {"ref": "soul", "value": 6}], "flat": 6}},
            {"speaker": "GM", "kind": "system", "text": "Eli sees no green coin on him. She sees three small scars on the back of his hand — the kind a green coin leaves when refused fast enough."},
            {"speaker": "GM", "kind": "system", "text": "End of session. The trio is now four. The forest goes quiet around them — politely."},
        ],
    },
    # ============================ SESSION 3 ============================
    {
        "title": "Session 3 — Strangers on the Road",
        "gm_notes": "Mishtee, Frock, and Malshe — three travelling artisans — cross paths at the forest's edge. Frock's unhealable wound is revealed; first whispered name 'Order of the Darkening Star'.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "The forest thins. A road-camp ahead — three artisans, a hobbled mule, a fire too large for the company. Bracers of a bowyer flash in the light."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "Mishtee. She has lost two already this year."},
            {"speaker": "Mishtee", "kind": "chat", "text": "Faunamimic. You pick odd company."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "They paid in iron."},
            {"speaker": "GM", "kind": "system", "text": "The wounded one — Frock — half-rises from his bedroll. The bandage on his side is dark, but not the dark of fresh blood. The dark beneath it is older."},
            {"speaker": "Eli", "kind": "action", "text": "kneels beside Frock with two vials uncorked already. Doesn't ask permission."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Diagnose Frock's wound", "result": {"total": 8, "rolls": [{"results": [1, 0]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "Whatever did this is not a creature Eli's training names. The flesh around the wound darkens but does not rot. Her clotting tincture beads on the surface and rolls off."},
            {"speaker": "Frock", "kind": "chat", "text": "Don't waste it. I've had three Apocophae try."},
            {"speaker": "Malshe", "kind": "chat", "text": "Four, if you count the road one."},
            {"speaker": "Roney", "kind": "chat", "text": "Where did you get it?"},
            {"speaker": "Frock", "kind": "chat", "text": "I don't remember. That's the worst of it."},
            {"speaker": "Malshe", "kind": "action", "text": "leans across the fire and drops it like a coin: 'Order of the Darkening Star. Go on. Say it back.'"},
            {"speaker": "Eli", "kind": "ooc", "text": "(everyone hold for a beat. We say it back.)"},
            {"speaker": "Eli", "kind": "chat", "text": "Order of the Darkening Star."},
            {"speaker": "GM", "kind": "system", "text": "Nothing happens. Which is, in its own way, a thing happening."},
            {"speaker": "Mishtee", "kind": "chat", "text": "The wound tracks something the Order does. We've seen it twice this season. The third one we found dead. Nobody finds Frock dead. Not on my watch."},
            {"speaker": "Laryk", "kind": "chat", "text": "We walk together to the ridge."},
            {"speaker": "Mishtee", "kind": "chat", "text": "We walk together to the Caldera."},
            {"speaker": "GM", "kind": "system", "text": "End of session. Six on the road now. One of them dying slowly."},
        ],
    },
    # ============================ SESSION 4 ============================
    {
        "title": "Session 4 — Frock's Wound",
        "gm_notes": "Eli works the wound across the next two days. The bandage hides a green coin pressed into Frock's flesh — Mishtee swears she did not put it there. First confirmed Order signature.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "Three days on. The party climbs the lower passes of the Montes Inexpugnabilis. Frock walks slower each morning. Eli has rebandaged the wound four times."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Apocophae deep-clean — fifth attempt", "result": {"total": 13, "rolls": [{"results": [3, 3]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "Eli pulls back the dressing. Beneath the dark — pressed flat into the flesh — is a green coin. Five-pointed star, one ray blackened."},
            {"speaker": "Roney", "kind": "ooc", "text": "no. NO."},
            {"speaker": "Mishtee", "kind": "chat", "text": "I did NOT put that there. He has not been alone for three weeks."},
            {"speaker": "Frock", "kind": "chat", "text": "I did not feel it go in."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "It would not announce itself. The forest does not announce a snare."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+soul", "label": "Steady-hand removal — coin", "result": {"total": 11, "rolls": [{"results": [3, 2]}, {"ref": "soul", "value": 6}], "flat": 6}},
            {"speaker": "GM", "kind": "system", "text": "The coin lifts free with a sound like ice cracking. Frock exhales for the first time in days without rattling."},
            {"speaker": "Eli", "kind": "action", "text": "wraps the coin in waxed leather and stows it in the bottom of her bandolier — separate."},
            {"speaker": "Malshe", "kind": "chat", "text": "Don't touch it again. Don't even look at it. It hears."},
            {"speaker": "Frock", "kind": "chat", "text": "Ask me what I saw at the Caldera."},
            {"speaker": "Eli", "kind": "chat", "text": "What did you see at the Caldera?"},
            {"speaker": "Frock", "kind": "chat", "text": "A robed one. Not in fur, not in armour. Robe. They were planting coins in the soil itself. Like seeds."},
            {"speaker": "GM", "kind": "system", "text": "End of session. The wound will close. The coin in Eli's bandolier will not stop humming."},
        ],
    },
    # ============================ SESSION 5 ============================
    {
        "title": "Session 5 — The First Silence",
        "gm_notes": "The forest goes silent on the third night past the ridge. A Lancing Andrewsarchus is within fifty miles. Combat is brief; survival depends on a cub rescue Roney refuses to abandon.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "Night four. The forest goes silent in a way that has no analogue. Even the wind stops. Nyaulis is on his feet before any of them register why."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "Andrewsarchus. North-northwest. We have one bell."},
            {"speaker": "Roney", "kind": "ooc", "text": "ROLLING INITIATIVE"},
            {"speaker": "Roney", "kind": "dice", "notation": "1d6+mind", "label": "Initiative", "result": {"total": 11, "rolls": [{"results": [4]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "Eli", "kind": "dice", "notation": "1d6+mind", "label": "Initiative", "result": {"total": 10, "rolls": [{"results": [3]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "Laryk", "kind": "dice", "notation": "1d6+mind", "label": "Initiative", "result": {"total": 8, "rolls": [{"results": [4]}, {"ref": "mind", "value": 4}], "flat": 4}},
            {"speaker": "GM", "kind": "system", "text": "The Andrewsarchus crashes through the upper treeline. Three tons of mottled fur. Eyes that read heat. Roney sees a cub stumbling at the creature's flank — the mother is wounded already, by something the party did not do."},
            {"speaker": "Roney", "kind": "chat", "text": "It's already dying. The cub — the cub is alive."},
            {"speaker": "Laryk", "kind": "action", "text": "raises the Hammer & Forge stance. The strike that splits a shield."},
            {"speaker": "Laryk", "kind": "dice", "notation": "2d6+atk", "label": "Hammer & Forge — Penetrating", "result": {"total": 12, "rolls": [{"results": [5, 3]}, {"ref": "atk", "value": 4}], "flat": 4}},
            {"speaker": "GM", "kind": "system", "text": "The hammer lands beneath the foreleg. The Andrewsarchus does not roar. It exhales — once — and folds. The forest's silence breaks. Birds, abruptly, again."},
            {"speaker": "Roney", "kind": "action", "text": "drops the harness frame and crawls under the dying mother to the cub. Waist-high. Wide-eyed. Mechanical-tail-already-broken-eyed."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Andrewsarchus magical-essence reading", "result": {"total": 14, "rolls": [{"results": [5, 2]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "The mother carried a green coin in her pelt — sewn there, not embedded. Someone sent her at them. The Order can mark beasts now. Or always could, and the party did not know."},
            {"speaker": "Roney", "kind": "chat", "text": "The cub is mine."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "The cub is the forest's. You will tend it for the forest."},
            {"speaker": "GM", "kind": "system", "text": "End of session. The harness is now permanent. The cub does not howl. It hums — off-rhythm, like Roney's clockwork."},
        ],
    },
    # ============================ SESSION 6 ============================
    {
        "title": "Session 6 — The Caldera",
        "gm_notes": "The Solar/Lunar Caldera is reached. Cataclysm-soil is harvested — and the Order is already there, harvesting too. First face-to-face contact. The robed one Frock saw is real.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "The Montes Inexpugnabilis open. The Caldera is below — ten miles of black glass and scarred basalt. The air is hot in a way that has nothing to do with sun."},
            {"speaker": "Eli", "kind": "action", "text": "uncorks the empty soil-vial. Hands tremble once. Steady on the second try."},
            {"speaker": "GM", "kind": "system", "text": "Down the slope, three figures in dark robes. They are not wearing the green coin. They ARE the green coin — that same five-pointed sigil sewn at the throat."},
            {"speaker": "Mishtee", "kind": "chat", "text": "Don't speak first. Order procedure."},
            {"speaker": "GM", "kind": "system", "text": "The middle robed one steps forward. Voice not loud. Voice pleasant."},
            {"speaker": "Order Agent", "kind": "chat", "text": "Apprentices. We are also harvesting. There is enough soil for both parties. Will you walk down?"},
            {"speaker": "Roney", "kind": "ooc", "text": "EVERY INSTINCT IS NO"},
            {"speaker": "Laryk", "kind": "chat", "text": "We walk down. We do not stand near."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Cataclysm-soil harvest under hostile witness", "result": {"total": 13, "rolls": [{"results": [3, 3]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "The vial fills. The soil does not move like soil. It moves like water with thought."},
            {"speaker": "Order Agent", "kind": "chat", "text": "Tell Master Caryana the Order remembers her."},
            {"speaker": "Eli", "kind": "action", "text": "freezes. Does not look up. Does not acknowledge."},
            {"speaker": "Frock", "kind": "chat", "text": "That's the one. That's the robe I saw."},
            {"speaker": "Nyaulis", "kind": "action", "text": "draws the iron stakes and steps between the apprentices and the agents. Does not say a word."},
            {"speaker": "GM", "kind": "system", "text": "The Order does not press. They withdraw up the opposite slope. Their footprints in the black glass smoke for an hour after they leave."},
            {"speaker": "Malshe", "kind": "chat", "text": "They knew her name. Eli — they knew Caryana's name."},
            {"speaker": "Eli", "kind": "chat", "text": "She told me they would. I did not believe her."},
            {"speaker": "GM", "kind": "system", "text": "End of session. Soil in the vial. Three names known on the other side. The road back is six weeks long and does not feel that long anymore."},
        ],
    },
    # ============================ SESSION 7 ============================
    {
        "title": "Session 7 — The Wound Closes Wrong",
        "gm_notes": "Frock dies in the night despite the coin's removal. A second green coin is found in his bedroll — placed AFTER the party fell asleep. The Order has someone in the company.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "Three days back from the Caldera. A road-camp at the lip of the Montes pass. Frock has been walking unaided for two days. The party allows itself, for the first time, to hope."},
            {"speaker": "GM", "kind": "system", "text": "Pre-dawn. Frock does not wake."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Diagnose — cause of death", "result": {"total": 11, "rolls": [{"results": [3, 1]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "The wound is closed. The wound is perfectly closed. The skin around it is unmarked. Frock has died of nothing visible."},
            {"speaker": "Roney", "kind": "ooc", "text": "no no no no no"},
            {"speaker": "Mishtee", "kind": "action", "text": "tears the bedroll apart. Finds it in the third fold."},
            {"speaker": "GM", "kind": "system", "text": "A green coin. Fresh. Five-pointed star, one ray blackened. Placed there in the night."},
            {"speaker": "Laryk", "kind": "chat", "text": "Someone here did this."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "Someone here, or something close enough to here."},
            {"speaker": "Mishtee", "kind": "chat", "text": "I did not. Malshe did not. We have been bonded for nine years. I would know."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+soul", "label": "Read the camp — who slept where", "result": {"total": 8, "rolls": [{"results": [1, 1]}, {"ref": "soul", "value": 6}], "flat": 6}},
            {"speaker": "GM", "kind": "system", "text": "Eli sees nothing useful. The camp is the camp. The Order does not leave footprints when it does not want to."},
            {"speaker": "Malshe", "kind": "chat", "text": "The cub."},
            {"speaker": "Roney", "kind": "chat", "text": "What."},
            {"speaker": "Malshe", "kind": "chat", "text": "The Order can mark beasts. You said so yourself, Eli."},
            {"speaker": "Roney", "kind": "action", "text": "checks the cub. Inside lid of the harness. The sigil is there. THE SIGIL HAS ALWAYS BEEN THERE."},
            {"speaker": "GM", "kind": "system", "text": "Roney remembers, in pieces, the sigil. The cub did not put it there. Roney's harness has had the sigil since week two of the Maiden Adventure. Since the cub joined the harness."},
            {"speaker": "Roney", "kind": "ooc", "text": "what do I do guys. WHAT DO I DO."},
            {"speaker": "Eli", "kind": "chat", "text": "We bury Frock. We don't sleep. We get to Master's Pass."},
            {"speaker": "GM", "kind": "system", "text": "End of session. One down. The road home is shorter than the road out, and longer than any of them have words for."},
        ],
    },
    # ============================ SESSION 8 ============================ CLIFFHANGER
    {
        "title": "Session 8 — Master's Pass",
        "gm_notes": "Cliffhanger session. The Order ambushes the party at the narrow throat of Master's Pass. Roney's harness sigil flares mid-line — and Roney is gone. Vanished. Mid-sentence. End of arc.",
        "log": [
            {"speaker": "GM", "kind": "system", "text": "Master's Pass. Four days from Eagles Nest. The road narrows to a throat between two basalt cliffs. The mule is hobbled at the entrance. The party walks the throat in single file."},
            {"speaker": "Nyaulis", "kind": "chat", "text": "I do not like this geometry."},
            {"speaker": "Mishtee", "kind": "chat", "text": "Nobody likes this geometry."},
            {"speaker": "GM", "kind": "system", "text": "Robes appear at the upper rim. Five of them. The same agent from the Caldera at the centre. The voice is the same. Pleasant."},
            {"speaker": "Order Agent", "kind": "chat", "text": "We will not ask twice. The Techgnostic comes with us. The rest may go."},
            {"speaker": "Roney", "kind": "ooc", "text": "OH. OH."},
            {"speaker": "Laryk", "kind": "action", "text": "raises his hammer. Says nothing. Does not need to."},
            {"speaker": "Eli", "kind": "dice", "notation": "2d6+mind", "label": "Read the agents' positions — find the weakest", "result": {"total": 12, "rolls": [{"results": [4, 1]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "GM", "kind": "system", "text": "The eastern agent is shaking. Young. The middle agent is holding something Eli has no name for — a coin too large for any pouch."},
            {"speaker": "Nyaulis", "kind": "dice", "notation": "1d6+mind", "label": "Initiative", "result": {"total": 9, "rolls": [{"results": [4]}, {"ref": "mind", "value": 5}], "flat": 5}},
            {"speaker": "Roney", "kind": "dice", "notation": "1d6+mind", "label": "Initiative", "result": {"total": 12, "rolls": [{"results": [5]}, {"ref": "mind", "value": 7}], "flat": 7}},
            {"speaker": "Roney", "kind": "chat", "text": "I'm not going with you. I'm staying with my—"},
            {"speaker": "GM", "kind": "system", "text": "The sigil in Roney's harness FLARES. Green. Bright enough to read by. The cub yowls — once. Roney does not finish his sentence."},
            {"speaker": "Eli", "kind": "ooc", "text": "RONEY"},
            {"speaker": "Laryk", "kind": "ooc", "text": "WHERE IS HE"},
            {"speaker": "GM", "kind": "system", "text": "Roney is not in the throat. The harness is on the ground. The cub is alone in it, eyes wide, completely silent. The Order agents are gone too — the upper rim is empty. The robe of the middle agent is on the ground at the apprentices' feet. There is nothing inside it but a single green coin and a folded scrap of parchment."},
            {"speaker": "GM", "kind": "system", "text": "Eli unfolds the parchment. The handwriting is unmistakable."},
            {"speaker": "GM", "kind": "system", "text": "It is the Mayor of Eagles Nest's hand. It reads: 'You will not bring him home. — M.'"},
            {"speaker": "GM", "kind": "system", "text": "END OF ARC. End of Session 8. Roney is gone. The Order is gone. The Mayor signed something they did not ask him to sign. Three weeks of road still lies between the apprentices and a hamlet that may not be the hamlet they left."},
            {"speaker": "GM", "kind": "ooc", "text": "Take a breath, table. Next session begins with the cub."},
        ],
    },
]
