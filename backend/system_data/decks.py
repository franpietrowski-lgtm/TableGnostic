"""System-aware card decks.

Each system gets one or more curated decks. BESM 4E does not natively use
cards but TableGnostic ships a system-agnostic Mood Deck so any table can
opt in to ceremonial card-pulls (e.g. a Session 0 tone-set).

Card schema:
    {
      "id":      str,           # stable id, lowercase-snake
      "name":    str,           # card name
      "suit":    Optional[str], # for grouped decks
      "rank":    Optional[str], # for grouped decks
      "effect":  str,           # mechanic-only text
      "page":    Optional[int], # SRD/CSC page reference
    }

Compliance: all entries are mechanic-only. The Deck of Many Things entries
restate game effects in mechanic terms; no reproduced rulebook prose.
"""

# ─── D&D 5E · Deck of Many Things (22-card SRD-aligned variant) ───
DND_DECK_OF_MANY = [
    {"id": "balance",     "name": "Balance",      "suit": "trump", "effect": "Alignment shifts one step toward neutral."},
    {"id": "comet",       "name": "Comet",        "suit": "trump", "effect": "Defeat next single hostile encounter alone → +1 XP level."},
    {"id": "donjon",      "name": "Donjon",       "suit": "trump", "effect": "Imprisoned in extra-dimensional cell · DC 20 to escape."},
    {"id": "euryale",     "name": "Euryale",      "suit": "trump", "effect": "−1 to all saving throws (permanent until magically removed)."},
    {"id": "fates",       "name": "The Fates",    "suit": "trump", "effect": "Reality-edit one event in your past."},
    {"id": "flames",      "name": "Flames",       "suit": "trump", "effect": "Powerful devil becomes your enemy."},
    {"id": "fool",        "name": "The Fool",     "suit": "trump", "effect": "Lose 10 000 XP · draw again."},
    {"id": "gem",         "name": "Gem",          "suit": "trump", "effect": "Gain 25 jewels (2 000 gp each) or 50 pieces of jewelry."},
    {"id": "idiot",       "name": "Idiot",        "suit": "trump", "effect": "−1 INT (permanent · floor 1) · choose to draw 1 extra card."},
    {"id": "jester",      "name": "Jester",       "suit": "trump", "effect": "+10 000 XP or draw 2 more cards."},
    {"id": "key",         "name": "Key",          "suit": "trump", "effect": "Materialise a +2 rare-rarity weapon of choice."},
    {"id": "knight",      "name": "Knight",       "suit": "trump", "effect": "4th-level fighter loyal companion appears."},
    {"id": "moon",        "name": "Moon",         "suit": "trump", "effect": "Granted 1d3 wishes (player choice; DM ruling on each)."},
    {"id": "rogue",       "name": "Rogue",        "suit": "trump", "effect": "An NPC closest to you becomes a hostile rival."},
    {"id": "ruin",        "name": "Ruin",         "suit": "trump", "effect": "All non-magical possessions destroyed."},
    {"id": "skull",       "name": "Skull",        "suit": "trump", "effect": "Avatar of Death attacks (CR equal to your level)."},
    {"id": "star",        "name": "Star",         "suit": "trump", "effect": "+2 to one ability score (cap raises by 2 if needed)."},
    {"id": "sun",         "name": "Sun",          "suit": "trump", "effect": "+50 000 XP · gain wondrous item (medium rarity)."},
    {"id": "talons",      "name": "Talons",       "suit": "trump", "effect": "All magic items in possession vanish."},
    {"id": "throne",      "name": "Throne",       "suit": "trump", "effect": "Persuasion expertise · own a small keep."},
    {"id": "vizier",      "name": "Vizier",       "suit": "trump", "effect": "Within 1 year, ask one question · receive truthful answer."},
    {"id": "void",        "name": "The Void",     "suit": "trump", "effect": "Soul trapped in dark sphere on another plane until rescued."},
]

# ─── Cypher · Cypher draw deck (subset for the active Cypher SRD list) ───
# Re-references CYPHERS in cypher_data; the deck endpoint draws from
# system_data.cypher_data.CYPHERS at request time.

# ─── Anime 5E · Character Card / Bestiary deck ───
# Used as a "Stage Reset" or "Genre Shift" ceremonial deck. Mechanic-only.
ANIME5E_GENRE_DECK = [
    {"id": "spotlight",      "name": "Spotlight",      "effect": "Drawer gains advantage on next ability check."},
    {"id": "rivalry",        "name": "Rivalry",        "effect": "Establish a named rival NPC who shares one PC's class."},
    {"id": "training_montage","name": "Training Montage","effect": "Skip 1 in-fiction week · all PCs gain 1 skill rank temporarily."},
    {"id": "transformation", "name": "Transformation", "effect": "Once per session, drawer's stats double for 3 rounds."},
    {"id": "clone_double",   "name": "Clone Double",   "effect": "An evil/good twin of one PC appears in the next scene."},
    {"id": "memory_lapse",   "name": "Memory Lapse",   "effect": "PC forgets 1 skill until next long rest."},
    {"id": "tournament",     "name": "Tournament Arc", "effect": "Next session is structured as a bracket-style competition."},
    {"id": "ally_arrives",   "name": "Ally Arrives",   "effect": "GM introduces a new helpful NPC immediately."},
    {"id": "school_break",   "name": "School Break",   "effect": "Heal all wounds; recover all expendables; non-combat session."},
    {"id": "secret_revealed","name": "Secret Revealed","effect": "GM reveals one previously hidden plot fact about a PC's past."},
    {"id": "world_changes",  "name": "World Changes",  "effect": "A major NPC undergoes alignment shift · world-tone drifts 1 step."},
    {"id": "monster_of_week","name": "Monster of the Week","effect": "Next session features a one-shot themed antagonist."},
]

# ─── Universal · TableGnostic Mood Deck (BESM-friendly, opt-in for any system) ───
TABLEGNOSTIC_MOOD_DECK = [
    {"id": "the_promise",      "name": "The Promise",      "effect": "Open the session by naming a promise a PC is keeping."},
    {"id": "the_reluctant_ally","name": "The Reluctant Ally","effect": "An NPC the party distrusts must be relied upon this session."},
    {"id": "the_cost_of_fire", "name": "The Cost of Fire", "effect": "What did one PC sacrifice to gain a power they now wield?"},
    {"id": "the_unspoken",     "name": "The Unspoken",     "effect": "Two PCs share a secret no one else at the table knows."},
    {"id": "heart_of_the_tale","name": "Heart of the Tale","effect": "Identify the emotional centre of this session before play."},
    {"id": "the_witness",      "name": "The Witness",      "effect": "Introduce an NPC who watches but does not act."},
    {"id": "the_bargain",      "name": "The Bargain",      "effect": "A PC will be offered something they cannot refuse this session."},
    {"id": "the_homecoming",   "name": "The Homecoming",   "effect": "A familiar place is returned to · how has it changed?"},
    {"id": "the_severance",    "name": "The Severance",    "effect": "End the session with one tie cut · which?"},
    {"id": "the_invitation",   "name": "The Invitation",   "effect": "Begin in medias res with a summons or call to action."},
    {"id": "the_quiet_hour",   "name": "The Quiet Hour",   "effect": "Open with a calm beat · everyone roleplays without rolling for 10 mins."},
    {"id": "the_storm",        "name": "The Storm",        "effect": "Something the party loves will be threatened, broken, or lost."},
]

# Per-system deck registry. The /api/cards/decks endpoint exposes this.
DECKS = {
    "dnd-5e": [
        {"id": "deck_of_many_things", "name": "Deck of Many Things",
         "kind": "trump", "size": len(DND_DECK_OF_MANY),
         "compliance": "SRD 5.1 mechanics-only restatement"},
        {"id": "tablegnostic_mood",   "name": "TableGnostic Mood Deck",
         "kind": "ceremonial", "size": len(TABLEGNOSTIC_MOOD_DECK),
         "compliance": "Original TableGnostic content"},
    ],
    "anime-5e": [
        {"id": "anime5e_genre",       "name": "Genre Shift Deck",
         "kind": "narrative", "size": len(ANIME5E_GENRE_DECK),
         "compliance": "Original TableGnostic content"},
        {"id": "tablegnostic_mood",   "name": "TableGnostic Mood Deck",
         "kind": "ceremonial", "size": len(TABLEGNOSTIC_MOOD_DECK),
         "compliance": "Original TableGnostic content"},
    ],
    "cypher": [
        {"id": "cypher_draw",         "name": "Cypher Draw",
         "kind": "single-use", "size": 12,
         "compliance": "Cypher System Creator licence — mechanic-only restatement",
         "note": "Drawn from the active Cypher SRD cyphers list"},
        {"id": "tablegnostic_mood",   "name": "TableGnostic Mood Deck",
         "kind": "ceremonial", "size": len(TABLEGNOSTIC_MOOD_DECK),
         "compliance": "Original TableGnostic content"},
    ],
    "besm-4e": [
        {"id": "tablegnostic_mood",   "name": "TableGnostic Mood Deck",
         "kind": "ceremonial", "size": len(TABLEGNOSTIC_MOOD_DECK),
         "compliance": "Original TableGnostic content · opt-in for BESM tables"},
    ],
}


def deck_cards(system_id: str, deck_id: str):
    """Return the actual card list for a (system, deck) pair, or None."""
    if deck_id == "deck_of_many_things":
        return DND_DECK_OF_MANY
    if deck_id == "anime5e_genre":
        return ANIME5E_GENRE_DECK
    if deck_id == "tablegnostic_mood":
        return TABLEGNOSTIC_MOOD_DECK
    if deck_id == "cypher_draw":
        # late import to avoid circular
        from .cypher_data import CYPHERS
        # Project cypher items into card shape.
        return [{"id": c["name"].lower().replace(" ", "_"), "name": c["name"],
                 "suit": "cypher", "rank": c.get("level", "—"),
                 "effect": f"{c.get('form', '—')} · {c.get('effect', '—')}"}
                for c in CYPHERS]
    return None
