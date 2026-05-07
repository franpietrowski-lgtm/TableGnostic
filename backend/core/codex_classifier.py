"""V6.25.19 — Codex auto-classifier for concepts.

A single source-of-truth that turns a raw concept (name + content +
tags + optional hint) into a canonical codex node shape:

    {
      "node_kind":    one of NODE_KINDS  (e.g. "npc", "location", "law", …)
      "type":         alias of node_kind for legacy compatibility
      "creation_tree_section": "Pillar.Branch" or None
      "confidence":   0.0-1.0
      "reasoning":    short string explaining the classification
    }

The classifier is consumed by:
  * world_creation.bridge_sow / get_creation_tree fallthrough
  * campaigns.seed_nodes_from_genesis (Genesis → codex pipeline)
  * epic_campaign.seed_to_codex (Epic → codex pipeline)
  * codex_nodes.create_node (POST /codex-nodes)
  * a new POST /campaigns/{cid}/codex/auto-classify backfill endpoint

Design rules:
  1. KEEP THE SHAPE STABLE — every node landed in `db.nodes` after this
     module ships exposes name + title + type + node_kind +
     creation_tree.section + tags + summary + content.
  2. CLASSIFICATION IS LAYERED — explicit hints win, then tags, then a
     contextual heuristic on the name + content. Confidence reflects
     the layer that fired.
  3. NEVER OVERWRITE A USER CHOICE — if the upstream record already
     carries a `creation_tree.section`, classify_concept must echo it.
"""
from __future__ import annotations
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ── Canonical node kinds (lowercase) ────────────────────────────────
# Mirror the world_creation TYPE_TO_SECTION map keys so the World Tree
# auto-routing stays in lock-step.
NODE_KINDS = {
    # Population
    "npc", "person", "pc", "character", "faction", "creature",
    "race", "nation", "language", "religion", "law", "war",
    "conflict", "technology", "belief",
    # Geography
    "location", "place", "region", "biome", "landmark", "country",
    "continent", "god", "dimension", "magic",
    # History
    "lore", "event", "chronicle", "quest", "era", "treaty", "myth",
    # Generic
    "concept", "item", "material", "byproduct", "craft_output",
}


# ── Pillar.Branch routing for each canonical node kind ──────────────
# Single source of truth — this drives BOTH the upstream classifier
# (where unknown kinds land) AND the legacy fallback in
# world_creation.get_creation_tree.
KIND_TO_SECTION: Dict[str, str] = {
    # Population
    "npc": "Population.Factions",
    "person": "Population.Prominent People",
    "character": "Population.Prominent People",
    "pc": "Population.Prominent People",
    "faction": "Population.Factions",
    "creature": "Population.Races",
    "race": "Population.Races",
    "nation": "Population.Nations",
    "language": "Population.Languages",
    "religion": "Population.Religions",
    "law": "Population.Laws",
    "war": "Population.Wars",
    "conflict": "Population.Conflicts",
    "technology": "Population.Technology",
    "belief": "Population.Beliefs",
    # Geography
    "location": "Geography.Locations",
    "place": "Geography.Locations",
    "landmark": "Geography.Locations",
    "region": "Geography.Continents",
    "biome": "Geography.Biomes",
    "country": "Geography.Countries",
    "continent": "Geography.Continents",
    "god": "Geography.Gods",
    "dimension": "Geography.Dimensions",
    "magic": "Geography.Magic",
    # History
    "lore": "History.Of the People",
    "event": "History.Of the People",
    "chronicle": "History.Written",
    "quest": "History.Of the People",
    "era": "History.Natural History",
    "treaty": "History.Written",
    "myth": "History.Oral",
}


# ── Tag → kind heuristics ───────────────────────────────────────────
TAG_TO_KIND: Dict[str, str] = {
    "nemesis": "npc", "villain": "npc", "ally": "npc",
    "patron": "npc", "captain": "npc", "merchant": "npc",
    "hero": "pc", "player-character": "pc",
    "guild": "faction", "cult": "faction", "house": "faction",
    "organisation": "faction", "organization": "faction",
    "city": "location", "town": "location", "village": "location",
    "fortress": "location", "ruin": "location", "tower": "location",
    "shrine": "location", "tavern": "location", "dungeon": "location",
    "kingdom": "country", "empire": "country", "republic": "country",
    "ocean": "biome", "forest": "biome", "desert": "biome",
    "tundra": "biome", "mountain": "biome", "swamp": "biome",
    "deity": "god", "pantheon": "god",
    "spell": "magic", "cantrip": "magic", "ritual": "magic",
    "incident": "event", "battle": "event", "siege": "war",
    "campaign-arc": "lore",
    "saga": "chronicle", "legend": "myth", "fable": "myth",
    "tongue": "language", "dialect": "language",
    "edict": "law", "decree": "law", "code": "law",
}


# ── Name regex matchers (last-resort heuristic) ─────────────────────
# Order MATTERS — first hit wins. Patterns are case-insensitive.
NAME_PATTERNS: List[Tuple[str, str]] = [
    (r"\b(king|queen|prince|princess|lord|lady|baron|duke|duchess|knight|sir|dame|emperor|empress|sage|elder|chief|captain|admiral|general|warden|seer)\b", "person"),
    (r"\b(guild|order|league|consortium|cabal|cult|house|clan|fellowship|covenant|circle|brotherhood|sisterhood|alliance|coalition|syndicate|company)\b", "faction"),
    (r"\b(empire|kingdom|republic|federation|principality|sultanate|caliphate|tsardom|khanate|dominion)\b", "country"),
    (r"\b(continent|landmass)\b", "continent"),
    (r"\b(ocean|sea|forest|mountain|desert|jungle|tundra|swamp|river|valley|plain|reef|archipelago|wasteland|moor|steppe)\b", "biome"),
    (r"\b(citadel|fortress|tower|temple|shrine|sanctum|cavern|cave|ruin|palace|keep|hall|spire|tavern|inn|bridge|gate|harbour|harbor|port|crypt|tomb|catacomb|library|academy|monastery|abbey|cathedral|chapel)\b", "location"),
    (r"\b(god|goddess|deity|patron-saint|saint|angel|archangel|demon|archdemon|primarch)\b", "god"),
    (r"\b(realm|plane|dimension|astral|ethereal|abyss|heaven|underworld|fae[a-z]*)\b", "dimension"),
    (r"\b(spell|cantrip|incantation|enchantment|hex|curse|blessing|ward|glyph|rune|sigil|magic|sorcery|art|invocation|ritual)\b", "magic"),
    (r"\b(war|crusade|jihad|skirmish|conflict|rebellion|uprising|revolt)\b", "war"),
    (r"\b(treaty|pact|accord|concordat|edict|decree|charter|constitution|act|code-of)\b", "treaty"),
    (r"\b(saga|chronicle|annals|annal|history-of|memoir)\b", "chronicle"),
    (r"\b(myth|legend|fable|folklore|folktale|fairytale)\b", "myth"),
    (r"\b(era|age-of|epoch|aeon|eon)\b", "era"),
    (r"\b(quest|mission|expedition|hunt|errand)\b", "quest"),
    (r"\b(law|edict|decree|writ|ordinance|statute|code)\b", "law"),
    (r"\b(tribe|race|species|kin|kindred|folk)\b", "race"),
    (r"\b(language|tongue|dialect|cant|patois|lingo)\b", "language"),
    (r"\b(faith|belief|creed|doctrine|tenet|dogma)\b", "belief"),
    (r"\b(religion|church|temple-of|cult-of)\b", "religion"),
    (r"\b(nation|people-of)\b", "nation"),
    (r"\b(technology|machine|engine|construct|invention|device)\b", "technology"),
]


def _normalise_tags(tags: Optional[Iterable[str]]) -> List[str]:
    if not tags:
        return []
    return [t.strip().lower() for t in tags if (t or "").strip()]


def classify_concept(
    name: str,
    content: str = "",
    tags: Optional[Iterable[str]] = None,
    hint: Optional[str] = None,
    explicit_section: Optional[str] = None,
) -> Dict[str, Any]:
    """Best-effort concept → codex shape.

    `hint` may be an existing `type` / `node_kind` value (e.g. coming
    out of Genesis) — that wins over content heuristics. An explicit
    `creation_tree.section` ALWAYS wins (caller-supplied placement is
    sacrosanct).
    """
    tags_l = _normalise_tags(tags)
    name_l = (name or "").lower()
    content_l = (content or "").lower()

    # 1. Explicit section → echo straight back, derive kind from it.
    if explicit_section:
        kind_from_section = _kind_from_section(explicit_section)
        return {
            "node_kind": kind_from_section,
            "type": kind_from_section,
            "creation_tree_section": explicit_section,
            "confidence": 1.0,
            "reasoning": "explicit creation_tree.section provided",
        }

    # 2. Hint (caller's existing `type` / `node_kind`).
    #    "concept" is the catch-all — we MUST NOT let it short-circuit
    #    the regex matchers, otherwise every concept node lands
    #    unplaced even when the name has obvious signal.
    if hint and hint.lower() in NODE_KINDS and hint.lower() != "concept":
        h = hint.lower()
        return {
            "node_kind": h,
            "type": h,
            "creation_tree_section": KIND_TO_SECTION.get(h),
            "confidence": 0.95,
            "reasoning": f"caller hint `{h}`",
        }

    # 3. Tag matchers.
    for t in tags_l:
        if t in TAG_TO_KIND:
            k = TAG_TO_KIND[t]
            return {
                "node_kind": k,
                "type": k,
                "creation_tree_section": KIND_TO_SECTION.get(k),
                "confidence": 0.85,
                "reasoning": f"tag `{t}` → `{k}`",
            }
        if t in NODE_KINDS:
            return {
                "node_kind": t,
                "type": t,
                "creation_tree_section": KIND_TO_SECTION.get(t),
                "confidence": 0.85,
                "reasoning": f"tag `{t}` is a canonical node kind",
            }

    # 4. Regex patterns on name (then on content as a fallback).
    for haystack, label in ((name_l, "name"), (content_l, "content")):
        if not haystack:
            continue
        for pat, kind in NAME_PATTERNS:
            if re.search(pat, haystack):
                return {
                    "node_kind": kind,
                    "type": kind,
                    "creation_tree_section": KIND_TO_SECTION.get(kind),
                    "confidence": 0.7 if label == "name" else 0.55,
                    "reasoning": f"{label} matched pattern → `{kind}`",
                }

    # 5. Hint that didn't match a canonical kind — still echo it.
    if hint:
        return {
            "node_kind": hint.lower(),
            "type": hint.lower(),
            "creation_tree_section": KIND_TO_SECTION.get(hint.lower()),
            "confidence": 0.4,
            "reasoning": f"non-canonical hint `{hint}`",
        }

    # 6. Give up — concept lands in unplaced.
    return {
        "node_kind": "concept",
        "type": "concept",
        "creation_tree_section": None,
        "confidence": 0.0,
        "reasoning": "no signal — concept retained, awaiting GM placement",
    }


def _kind_from_section(section: str) -> str:
    """Reverse-lookup: 'Pillar.Branch' → most-likely node_kind.

    Uses the inverse of KIND_TO_SECTION, preferring the more specific
    kind (e.g. `country` over `region` for `Geography.Countries`).
    Falls back to a per-branch override table for World Tree branches
    that share a section with a more specific kind (e.g. `Truth` /
    `Lies` both reverse-map to `lore`, but the World Tree wants them
    to STAY in their History branches when the classifier is invoked
    via bridge-sow).
    """
    sec = section.strip()
    # 1. Direct reverse-lookup.
    for k, v in KIND_TO_SECTION.items():
        if v == sec:
            return k
    # 2. Branch-specific overrides for sections that don't have a
    #    1-to-1 kind alias — chosen so the seeded codex node still
    #    routes BACK to the same Pillar.Branch on read.
    branch = (sec.split(".", 1)[1] if "." in sec else sec).strip().lower()
    overrides = {
        "natural divides": "landmark",
        "natural laws": "lore",
        "connected worlds": "dimension",
        "uniqueness": "lore",
        "man-made borders": "location",
        "truth": "lore",
        "lies": "lore",
        "prominent people": "person",
    }
    return overrides.get(branch, "concept")


def codexify_node(
    *,
    name: str,
    content: str = "",
    summary: str = "",
    tags: Optional[List[str]] = None,
    hint: Optional[str] = None,
    explicit_section: Optional[str] = None,
    explicit_color: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the canonical V6.25.19 codex-node shape.

    Caller still supplies `id` / `campaign_id` / `author_*` /
    `created_at` / `updated_at` / `visibility` — this helper only
    computes the four discovery fields (`name`, `title`, `type`,
    `node_kind`) plus the `creation_tree` block plus the `tags` list.
    """
    cls = classify_concept(
        name=name, content=content, tags=tags,
        hint=hint, explicit_section=explicit_section,
    )
    payload: Dict[str, Any] = {
        "name": name.strip(),
        "title": name.strip(),
        "type": cls["type"],
        "node_kind": cls["node_kind"],
        "summary": (summary or content or "")[:1000],
        "content": content or summary or "",
        "tags": _normalise_tags(tags),
        "fields": dict(extra_fields or {}),
    }
    sec = cls["creation_tree_section"]
    if sec:
        payload["creation_tree"] = {
            "section": sec,
            "color": explicit_color,
            "auto_classified": not bool(explicit_section),
            "classifier_confidence": cls["confidence"],
            "classifier_reasoning": cls["reasoning"],
        }
    return payload
