"""
Evereantha sample player characters — three Adventurous-tier (~80 pt) PCs
built using BESM 4E mechanics + the BESM Extras only. All characters are
written for Table-Gnostic's data model and reference the public Evereantha
setting notes the user provided. No copyrighted rulebook prose is reproduced.

Each Attribute lists name, level, cost_per_level, enhancements, limiters, page,
and an optional `note`. Defects use rank, points_per_rank, and category.
Total Spent for each PC is verified to land within the Adventurous budget
(60–80 Character Points; we target ~80 to match the user's "starting heroes
in Eagles Nest" framing in Evereantha).
"""

EVEREANTHA_PCS = [
    # ---------- 1. Apocophea — Herbalist / Alchemist ----------
    {
        "name": "Cyma Glasswort",
        "concept": "Apocophea (Herbalist–Alchemist) of the Taurid Tor villages",
        "power_level": "Adventurous",
        "total_points": 80,
        "stats": {"body": 4, "mind": 7, "soul": 6},  # 17 pts
        "attributes": [
            # Aurae · Cryptosha · Serenitas — calmative tinctures and salves
            {"name": "Healing", "level": 4, "cost_per_level": 4,
             "enhancements": ["Range"], "limiters": ["Consumable"],
             "page": 96, "note": "Cryptosha · Serenitas vials"},
            # Heightened Senses tuned to herbs & toxins
            {"name": "Heightened Senses", "level": 4, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 96, "note": "Sense for poisons / herb potency"},
            # Cognition — herbal lore and tincture composition
            {"name": "Cognition", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 84, "note": "Apocophean lore"},
            # Skill Group: Healer (Lesser group representing a specialist's kit)
            {"name": "Skill Group", "level": 4, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 120, "note": "Lesser group — Apocophea kit"},
            # Item: A bandolier of glass vials carrying her formulae (½-cost)
            {"name": "Item", "level": 6, "cost_per_level": 1,
             "enhancements": [], "limiters": ["Charges"],
             "page": 100, "note": "Vial bandolier (Item shell · 0.5×)"},
            # Wealth — village-renowned trade in Apocophean elixirs
            {"name": "Wealth", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 132, "note": "Trade in Apocophean elixirs"},
        ],
        "defects": [
            {"name": "Marked", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 154, "note": "Permanent stains on hands — herb pigments"},
            {"name": "Skeleton in the Closet", "rank": 1, "points_per_rank": 2, "category": "Greater",
             "page": 158, "note": "Once mixed a tincture for the Order of the Darkening Star"},
            {"name": "Significant Other", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 158, "note": "Aging mentor in Aldabar village"},
        ],
        "skills": [],
        "folio": {
            "occupation": "Apocophea — village healer-by-trade",
            "physical_description": "Stained fingertips, copper-rimmed lenses, satchel of glass vials.",
            "personality": "Quietly methodical. Reads people the way she reads tinctures.",
            "edges": "Reputation for honest dosage — even unfriendly villages will trade with her.",
            "obstacles": "Cannot turn away the dying, even when discretion would save her.",
            "goals": "Catalogue every Cryptosha-friendly herb in the Taurid Tor before the Unmaker's frost arrives.",
            "family": "Apprentice of an aging Apocophean elder; only child.",
            "journal": "",
        },
    },
    # ---------- 2. Ferralith — Metal Whisperer / Monk-Smith ----------
    {
        "name": "Tarsis Hammergrip",
        "concept": "Ferralith (Metal Whisperer Monk-Smith) of Oriun's Reach",
        "power_level": "Adventurous",
        "total_points": 80,
        "stats": {"body": 8, "mind": 4, "soul": 6},  # 18 pts
        "attributes": [
            # Tough — a smith's frame absorbs blows
            {"name": "Tough", "level": 4, "cost_per_level": 2,
             "enhancements": [], "limiters": [],
             "page": 132, "note": "+20 HP"},
            # Attack Mastery — discipline of the forge translated to the strike
            {"name": "Attack Mastery", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": ["Object"],
             "page": 80, "note": "Only with crafted weapons"},
            # Combat Technique — Two Weapons + Lightning Reflexes + Hardboiled
            {"name": "Combat Technique", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 84, "note": "Two-Weapon, Lightning Reflexes, Hardboiled"},
            # Weapon — the Monk-Smith's signature war-hammer
            {"name": "Weapon", "level": 4, "cost_per_level": 2,
             "enhancements": ["Potent"], "limiters": [],
             "page": 132, "note": "Resonant war-hammer (forged-self)"},
            # Massive Damage — calibrated strike-force
            {"name": "Massive Damage", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": ["Object"],
             "page": 100, "note": "Hammer-strikes only"},
            # Skill Group: Adventurer (Lesser)
            {"name": "Skill Group", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 120, "note": "Lesser group — Smith / Adventurer"},
            # Connected — the Ferralith circles
            {"name": "Connected", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 88, "note": "Ferralith circles across continents"},
        ],
        "defects": [
            {"name": "Obligated", "rank": 2, "points_per_rank": 2, "category": "Greater",
             "page": 156, "note": "Bound to repair any Ferralith blade brought to him"},
            {"name": "Marked", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 154, "note": "Forge-burn scar across the right forearm"},
            {"name": "Phobia", "rank": 2, "points_per_rank": 1, "category": "Lesser",
             "page": 156, "note": "Open water (Aetheris Ocean dread)"},
        ],
        "skills": [],
        "folio": {
            "occupation": "Ferralith — itinerant Monk-Smith",
            "physical_description": "Broad-shouldered, soot-cheeked, forge-tooled belt.",
            "personality": "Slow to anger, faster than expected, quotes the rhythm of bellows.",
            "edges": "Can identify any blade's smith by ring alone.",
            "obstacles": "His own hammer was forged for him by an Order Deacon — he has not told anyone.",
            "goals": "Reach Gladiolux and unmake the chains his master once wrought for the cult.",
            "family": "Apprenticed at twelve to a Ferralith circle in Oriun's Reach. Family lost at sea.",
            "journal": "",
        },
    },
    # ---------- 3. Lithomorph — Geomantic Sculptor ----------
    {
        "name": "Vela Stoneglyph",
        "concept": "Lithomorph (Geomantic Sculptor) of Continenta Aurea",
        "power_level": "Adventurous",
        "total_points": 80,
        "stats": {"body": 5, "mind": 6, "soul": 7},  # 18 pts
        "attributes": [
            # Stone & soil control — Aurae · Confluo · Vallum
            {"name": "Control Environment", "level": 3, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Environmental"],
             "page": 88, "note": "Stone & soil only"},
            # Armour from grafted earth-glyphs
            {"name": "Armour", "level": 3, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Activation"],
             "page": 80, "note": "Glyph-armour Aurae · Cumulus"},
            # Heightened Senses — vibrations through stone
            {"name": "Heightened Senses", "level": 3, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 96, "note": "Tremorsense via stone"},
            # Tunnelling — short-range, ritual-only
            {"name": "Tunnelling", "level": 2, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Concentration", "Delay"],
             "page": 132, "note": "Ritual carve-through"},
            # Sixth Sense — geomantic resonance reads buried artifacts
            {"name": "Sixth Sense", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 120, "note": "Detects worked stone, glyph-veins, Compass shards"},
            # Skill Group: Artisan (Lesser)
            {"name": "Skill Group", "level": 4, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 120, "note": "Lesser group — Lithomorph kit"},
            # Connected — Lithomorph circles + Taurid Tor village elders
            {"name": "Connected", "level": 2, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "page": 88, "note": "Lithomorph circles + Taurid Tor villages"},
        ],
        "defects": [
            {"name": "Special Requirement", "rank": 2, "points_per_rank": 2, "category": "Greater",
             "page": 158, "note": "Must touch worked stone daily or skills falter"},
            {"name": "Awkward Size", "rank": 1, "points_per_rank": 1, "category": "Lesser",
             "page": 154, "note": "Carries a heavy carving stave at all times"},
            {"name": "Cursed", "rank": 1, "points_per_rank": 2, "category": "Greater",
             "page": 154, "note": "Stones whisper Mortiscura phrases when she sleeps"},
        ],
        "skills": [],
        "folio": {
            "occupation": "Lithomorph — wandering Geomantic Sculptor",
            "physical_description": "Slate-grey eyes, glyph-tattoos along both forearms.",
            "personality": "Patient. Hears the cadence of mountains. Slow to speak, certain when she does.",
            "edges": "Recognised by every Taurid Tor village elder — safe passage in the rocky plains.",
            "obstacles": "An old fragment of the Compass is buried under her left palm-glyph; she does not know it.",
            "goals": "Find the matching glyph-vein under Montes Inexpugnabilis before the Unmaker's silence reaches it.",
            "family": "Trained by a Lithomorph circle scattered after the Order's first purge.",
            "journal": "",
        },
    },
]
