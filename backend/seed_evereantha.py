"""
Evereantha sample player characters — three Adventurous-tier (~80 pt) PCs
built using BESM 4E mechanics + the BESM Extras only. All characters are
written for Table-Gnostic's data model and reference the public Evereantha
setting notes the user provided. No copyrighted rulebook prose is reproduced.

Each Attribute lists name, level, cost_per_level, enhancements, limiters, page,
and an optional `note` — the in-setting flavor description shown as the
PRIMARY description on the character sheet (e.g. "Cryptosha · Serenitas vials"
instead of the generic mechanic blurb).

Skill Groups are populated on the dedicated `skills` array (NOT as Attributes)
with proper component-skill breakdowns matching BESM 4E p.120's Lesser/Greater
groups. Each component cites a typical sub-skill expressed in setting-flavored
language so a player understands what the group lets them do at the table.

Power Packs (BESM Extras p.42 — "Power Packs / Bundles") are added as a
narrative source-of-power grouping. They are FREE by default (cost: 0); a GM
who wants to charge for them can edit cost via the Character Builder.
"""

EVEREANTHA_PCS = [
    # ---------- 1. Apocophea — Herbalist / Alchemist ----------
    {
        "name": "Cyma Glasswort",
        "concept": "Apocophea (Herbalist–Alchemist) of the Taurid Tor villages",
        "power_level": "Adventurous",
        "total_points": 80,
        "token_color": "#5fa37a",  # apothecary green
        "stats": {"body": 4, "mind": 7, "soul": 6},  # 17 pts
        "attributes": [
            {"name": "Healing", "level": 4, "cost_per_level": 4,
             "enhancements": ["Range"], "limiters": ["Consumable"],
             "page": 96,
             "note": "Cryptosha · Serenitas calmative tincture, distilled in glass and warmed before pour."},
            {"name": "Heightened Senses", "level": 4, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 96,
             "note": "Trained nose for poisons & herb potency — names a tincture by scent at five paces."},
            {"name": "Cognition", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 84,
             "note": "Apocophean lore: composition tables, dosage by body-mass, antidote chains."},
            {"name": "Item", "level": 6, "cost_per_level": 1,
             "enhancements": [], "limiters": ["Charges"],
             "page": 100,
             "note": "Vial bandolier — twelve cut-glass tinctures keyed to her formulary (Item shell · 0.5×)."},
            {"name": "Wealth", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 132,
             "note": "Brisk trade in Apocophean elixirs — reliable barter across the Taurid Tor."},
        ],
        "defects": [
            {"name": "Marked", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 154,
             "note": "Permanent herb-pigment stains on hands and forearms."},
            {"name": "Skeleton in the Closet", "rank": 1, "points_per_rank": 2, "category": "Greater",
             "page": 158,
             "note": "Once mixed a tincture for the Order of the Darkening Star — discovery would unmake her."},
            {"name": "Significant Other", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 158,
             "note": "Aging mentor in Aldabar village — kidnap-leverage walking on a stick."},
        ],
        # Skill Groups live HERE, not in attributes. Each entry has a `components`
        # list of in-setting sub-skills so the player sees exactly what the
        # group lets them do.
        "skills": [
            {"group": "Apocophea Kit", "level": 2, "cost_per_level": 2, "page": 120,
             "note": "Lesser Group · the Apocophean's working repertoire: gather, infuse, dose, dispense.",
             "components": [
                 {"name": "Survivalist", "level": 1, "note": "Foraging, weather-reading, camp-craft."},
                 {"name": "Apocophea Training", "level": 1, "note": "Autobag handling, staff-and-vial discipline."},
                 {"name": "Flora Library", "level": 1, "note": "Recall and identify a region's flora and toxins."},
                 {"name": "Encumbrance", "level": 1, "note": "GM-approved · carry the bandolier full without penalty."},
             ]},
        ],
        # Free narrative grouping — the source of Cyma's craft.
        "power_packs": [
            {"name": "Cryptosha · Serenitas",
             "description": "The Cryptosha-Face Subdivision of Aurae Magic. Calmative, halting, clarifying. "
                            "Cyma's tinctures are the visible expression of this Aurae Subdivision; "
                            "her Healing, Cognition, and Vial Bandolier all draw from it.",
             "references": ["Healing", "Cognition", "Vial Bandolier"], "cost": 0},
        ],
        "folio": {
            "occupation": "Apocophea — village healer-by-trade",
            "physical_description": "Stained fingertips, copper-rimmed lenses, satchel of glass vials.",
            "personality": "Quietly methodical. Reads people the way she reads tinctures.",
            "edges": ["Honest dosage — even unfriendly villages will trade with her.",
                      "Recognised by every Apocophean elder along the Taurid Tor."],
            "obstacles": ["Cannot turn away the dying, even when discretion would save her.",
                          "Sleeps lightly when she's owed a favour."],
            "goals": [
                {"title": "Catalogue every Cryptosha-friendly herb in the Taurid Tor",
                 "kind": "long",
                 "note": "Before the Unmaker's frost reaches the southern villages."},
                {"title": "Find a stable Serenitas tincture for grieving children",
                 "kind": "short",
                 "note": "The current dose works once and only once."},
                {"title": "Confess the Order tincture",
                 "kind": "secret",
                 "note": "She must — but she won't, until the day a friend dies of it."},
            ],
            "family": [
                {"name": "Vael Glasswort", "relation": "Mentor",
                 "note": "Aging Apocophean elder in Aldabar village. Walks with a stick."},
            ],
            "history_events": [],
            "journal": [],
        },
    },
    # ---------- 2. Ferralith — Metal Whisperer / Monk-Smith ----------
    {
        "name": "Tarsis Hammergrip",
        "concept": "Ferralith (Metal Whisperer Monk-Smith) of Oriun's Reach",
        "power_level": "Adventurous",
        "total_points": 80,
        "token_color": "#c47a3d",  # forge ember
        "stats": {"body": 8, "mind": 4, "soul": 6},  # 18 pts
        "attributes": [
            {"name": "Tough", "level": 4, "cost_per_level": 2,
             "enhancements": [], "limiters": [],
             "page": 132,
             "note": "Forge-conditioned frame absorbs blows like an anvil receives strikes (+20 HP)."},
            {"name": "Attack Mastery", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": ["Object"],
             "page": 80,
             "note": "Discipline of the forge — swings true only with weapons crafted by his own hand."},
            {"name": "Combat Technique", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 84,
             "note": "Two-Weapon · Lightning Reflexes · Hardboiled — taught at the Ferralith circles."},
            {"name": "Weapon", "level": 4, "cost_per_level": 2,
             "enhancements": ["Potent"], "limiters": [],
             "page": 132,
             "note": "Resonant war-hammer, forged-self — the metal sings when his strikes are aligned."},
            {"name": "Massive Damage", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": ["Object"],
             "page": 100,
             "note": "Calibrated strike-force — only with his hammer."},
            {"name": "Connected", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 88,
             "note": "Ferralith circles — every continent has one, every circle owes him a meal."},
        ],
        "defects": [
            {"name": "Obligated", "rank": 2, "points_per_rank": 2, "category": "Greater",
             "page": 156,
             "note": "Bound by Ferralith oath to repair any circle-marked blade brought to him."},
            {"name": "Marked", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 154,
             "note": "Forge-burn scar across the right forearm — the outline of his master's anvil."},
            {"name": "Phobia", "rank": 2, "points_per_rank": 1, "category": "Lesser",
             "page": 156,
             "note": "Open water — the Aetheris Ocean took everyone he'd named."},
        ],
        "skills": [
            {"group": "Smith of the Road", "level": 2, "cost_per_level": 2, "page": 120,
             "note": "Lesser Group · the itinerant Monk-Smith's survival kit.",
             "components": [
                 {"name": "Smithing", "level": 2, "note": "Forge, temper, finish. Recognises smiths by ring alone."},
                 {"name": "Survivalist", "level": 1, "note": "Roads, weather, tinder, wind-shelter."},
                 {"name": "Etiquette · Circle", "level": 1, "note": "Ferralith circle protocols, oath-tongue."},
             ]},
            {"group": "Combat Discipline", "level": 2, "cost_per_level": 1, "page": 120,
             "note": "Lesser Group · the monk-side of Monk-Smith.",
             "components": [
                 {"name": "Melee Attack · Hammer", "level": 2, "note": "His own forged hammers only."},
                 {"name": "Athletics", "level": 1, "note": "Footwork, balance on uneven ground."},
                 {"name": "Body Discipline", "level": 1, "note": "Breath-rhythm to bellows-rhythm — slows panic."},
             ]},
        ],
        "power_packs": [
            {"name": "The Ferralith Circle",
             "description": "Trade-fellowship of itinerant Monk-Smiths. Their oath-tongue, their forge-songs, "
                            "and the resonance-temper their hammers carry are the source of Tarsis' martial "
                            "discipline and the war-hammer's signature ring.",
             "references": ["Resonant war-hammer", "Combat Discipline", "Connected"], "cost": 0},
        ],
        "folio": {
            "occupation": "Ferralith — itinerant Monk-Smith",
            "physical_description": "Broad-shouldered, soot-cheeked, forge-tooled belt.",
            "personality": "Slow to anger, faster than expected, quotes the rhythm of bellows.",
            "edges": ["Identifies any blade's smith by ring alone.",
                      "Owed a meal at every Ferralith circle on three continents."],
            "obstacles": ["His own hammer was forged for him by an Order Deacon — a secret he keeps.",
                          "Avoids open water; long ferries cost him a session of focus."],
            "goals": [
                {"title": "Reach Gladiolux", "kind": "long",
                 "note": "Unmake the chains his master once wrought for the cult."},
                {"title": "Forge a hammer for an apprentice he hasn't met yet", "kind": "short",
                 "note": "He keeps a billet of unalloyed iron wrapped in oil-cloth."},
                {"title": "Confess the hammer", "kind": "secret",
                 "note": "Tell the next circle the truth of who forged it."},
            ],
            "family": [
                {"name": "Master Vorrun", "relation": "Forge-master / Order Deacon",
                 "note": "Believed dead. Tarsis is not certain."},
            ],
            "history_events": [],
            "journal": [],
        },
    },
    # ---------- 3. Lithomorph — Geomantic Sculptor ----------
    {
        "name": "Vela Stoneglyph",
        "concept": "Lithomorph (Geomantic Sculptor) of Continenta Aurea",
        "power_level": "Adventurous",
        "total_points": 80,
        "token_color": "#6b7a99",  # slate blue
        "stats": {"body": 5, "mind": 6, "soul": 7},  # 18 pts
        "attributes": [
            {"name": "Control Environment", "level": 3, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Environmental"],
             "page": 88,
             "note": "Stone & soil only — Aurae · Confluo · Vallum, traced through palm-glyphs."},
            {"name": "Armour", "level": 3, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Activation"],
             "page": 80,
             "note": "Glyph-armour — Aurae · Cumulus stone-skin layered over the body on a chant."},
            {"name": "Heightened Senses", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 96,
             "note": "Tremorsense — the rocky plains speak through her bare feet."},
            {"name": "Tunnelling", "level": 2, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Concentration", "Delay"],
             "page": 132,
             "note": "Ritual carve-through — slow, but the stone yields if she remembers its name."},
            {"name": "Sixth Sense", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 120,
             "note": "Geomantic resonance — detects worked stone, glyph-veins, Compass shards."},
            {"name": "Connected", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 88,
             "note": "Lithomorph circles + Taurid Tor village elders — safe passage in the rocky plains."},
        ],
        "defects": [
            {"name": "Special Requirement", "rank": 2, "points_per_rank": 2, "category": "Greater",
             "page": 158,
             "note": "Must touch worked stone daily — cathedrals, hearthstones, milestones — or her glyphs dim."},
            {"name": "Awkward Size", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 154,
             "note": "Carries a heavy carving stave at all times — the only tool she trusts."},
            {"name": "Cursed", "rank": 1, "points_per_rank": 2, "category": "Greater",
             "page": 154,
             "note": "Stones whisper Mortiscura phrases when she sleeps — she dreams in cypher."},
        ],
        "skills": [
            {"group": "Lithomorph Kit", "level": 3, "cost_per_level": 1, "page": 120,
             "note": "Lesser Group · the Geomantic Sculptor's working set.",
             "components": [
                 {"name": "Stoneworking", "level": 2, "note": "Quarry, dress, carve, glyph."},
                 {"name": "Geomancy Lore", "level": 2, "note": "Glyph-vein maps, ley-stone reading."},
                 {"name": "Survivalist · Mountain", "level": 1, "note": "Cliff, scree, snow-line, alt sickness."},
                 {"name": "Etiquette · Taurid Tor", "level": 1, "note": "Village protocols and elder-speech."},
             ]},
        ],
        "power_packs": [
            {"name": "Aurae · Confluo · Vallum",
             "description": "Subdivision of Aurae Magic concerned with energy-shaping into walls, shells, "
                            "and worked stone. Vela's Control Environment, Armour, and Tunnelling are all "
                            "expressions of this single Aurae current; the glyphs on her arms are its keys.",
             "references": ["Control Environment", "Armour", "Tunnelling"], "cost": 0},
        ],
        "folio": {
            "occupation": "Lithomorph — wandering Geomantic Sculptor",
            "physical_description": "Slate-grey eyes, glyph-tattoos along both forearms.",
            "personality": "Patient. Hears the cadence of mountains. Slow to speak, certain when she does.",
            "edges": ["Recognised by every Taurid Tor village elder — safe passage in the rocky plains.",
                      "Reads the age of any worked stone by touch."],
            "obstacles": ["Stones whisper Mortiscura phrases in her sleep.",
                          "Cannot bring herself to leave a cracked cathedral wall un-sung."],
            "goals": [
                {"title": "Find the matching glyph-vein under Montes Inexpugnabilis", "kind": "long",
                 "note": "Before the Unmaker's silence reaches it."},
                {"title": "Re-carve the road-sigil at Bell-Crossing", "kind": "short",
                 "note": "The merchant guild keeps asking; she keeps saying yes."},
                {"title": "Speak the name buried in her left palm", "kind": "secret",
                 "note": "She still doesn't know it's a Compass shard."},
            ],
            "family": [
                {"name": "Circle of the Slate Door", "relation": "Lithomorph training-circle",
                 "note": "Scattered after the Order's first purge. She still hears their carving rhythms."},
            ],
            "history_events": [],
            "journal": [],
        },
    },
]
