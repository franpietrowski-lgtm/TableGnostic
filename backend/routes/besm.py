"""BESM 4E reference + Game-systems registry — public read-only endpoints."""
from fastapi import APIRouter, HTTPException, Response

from besm_data import (
    ACTIONS, ARMOUR, ATTRIBUTES, AUREA_CUSTOM_ATTRIBUTES, AUREA_CUSTOM_BOOK,
    AUREA_CUSTOM_POWER_PACKS, AUREA_CUSTOM_SKILLS, AUREA_RULE_NOTE,
    BOOK, BOOK_EXTRAS, CLASS_TEMPLATES, COMPANIONS, CONDITIONS, CORE_STATS,
    DEFECTS, DEFAULT_SYSTEM_ID, DERIVED_VALUES, ENHANCEMENTS, EXTRAS_RULES,
    GAME_SYSTEMS, GENERIC_BLURBS, ITEMS_GEAR, ITEM_ENHANCEMENTS,
    ITEM_LIMITERS, LIMITERS, NODE_TYPES, POWER_LEVELS,
    RACE_TEMPLATES, SIZE_MODIFIERS, SIZE_TEMPLATES, SKILL_GROUPS,
    TARGET_NUMBERS, WEAPONS, WEAPON_ENHANCEMENTS, WEAPON_LIMITERS,
    attribute_blurb, attribute_whitelist,
    defect_blurb, enhancement_blurb, extras_blurb, limiter_blurb,
    power_level_blurb, with_source,
)

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/besm/reference")
async def besm_reference():
    def enrich_attr(a):
        wl = attribute_whitelist(a["name"])
        return {**a, "blurb": attribute_blurb(a["name"]),
                "allowed_enhancements": wl["enhancements"],
                "allowed_limiters": wl["limiters"],
                "open_mods": wl["open"]}

    def enrich_def(d):
        return {**d, "blurb": defect_blurb(d.get("category", ""), d.get("name", ""))}

    def enrich_pl(p):
        return {**p, "blurb": power_level_blurb(p["name"])}

    return {
        "book": BOOK,
        "core_stats": with_source(CORE_STATS),
        "derived_values": with_source(DERIVED_VALUES),
        "attributes": [enrich_attr(a) for a in with_source(ATTRIBUTES)],
        "defects": [enrich_def(d) for d in with_source(DEFECTS)],
        "enhancements": [{**e, "blurb": enhancement_blurb(e["name"])} for e in with_source(ENHANCEMENTS)],
        "limiters": [{**lim, "blurb": limiter_blurb(lim["name"])} for lim in with_source(LIMITERS)],
        # V6.25.11 — Weapon Enhancements / Limiters are CORE (p.135 / p.142),
        # not Extras. Item mods remain a TableGnostic companion pool
        # (labelled via `source_book=BOOK` + the Item cost-halving rule
        # enforced in the validator regardless of which item mods are picked).
        "weapon_enhancements": [
            {**e, "blurb": e.get("note") or "Weapon-specific Enhancement (BESM 4E p.135)."}
            for e in with_source(WEAPON_ENHANCEMENTS)],
        "weapon_limiters": [
            {**lim, "blurb": lim.get("note") or "Weapon-specific Limiter (BESM 4E p.142)."}
            for lim in with_source(WEAPON_LIMITERS)],
        "item_enhancements": [
            {**e, "blurb": e.get("note") or "Item-specific Enhancement (TableGnostic flavour pool)."}
            for e in with_source(ITEM_ENHANCEMENTS, source_book=BOOK_EXTRAS)],
        "item_limiters": [
            {**lim, "blurb": lim.get("note") or "Item-specific Limiter (TableGnostic flavour pool)."}
            for lim in with_source(ITEM_LIMITERS, source_book=BOOK_EXTRAS)],
        "skill_groups": with_source(SKILL_GROUPS),
        "power_levels": [enrich_pl(p) for p in with_source(POWER_LEVELS)],
        "node_types": NODE_TYPES,
        "target_numbers": with_source(TARGET_NUMBERS),
        "extras_book": BOOK_EXTRAS,
        "extras_rules": [{**r, "blurb": extras_blurb(r["name"]),
                          "source": {"book": BOOK_EXTRAS, "page": r.get("page")}}
                         for r in EXTRAS_RULES],
        "generic_blurbs": [{"name": k, "blurb": v} for k, v in GENERIC_BLURBS.items()],
        "size_templates": SIZE_TEMPLATES,
        # New expanded reference sections (V4.1)
        "actions": with_source(ACTIONS),
        "companions": with_source(COMPANIONS),
        "race_templates": with_source(RACE_TEMPLATES),
        # V6.25.32 — BESM 4E class / archetype templates with bundled
        # attribute / defect / skill rows. Builder applies wholesale,
        # GM-primer can scope which are available per genre/setting.
        "class_templates": with_source(CLASS_TEMPLATES),
        "size_modifiers": with_source(SIZE_MODIFIERS),
        "weapons": with_source(WEAPONS),
        "items_gear": with_source(ITEMS_GEAR),
        "armour": with_source(ARMOUR),
        # V6.25.49 — universal status conditions / ailments catalogue.
        "conditions": CONDITIONS,
        # Custom / Created — Aurea magic system as a worked BESM example.
        "custom": {
            "book": AUREA_CUSTOM_BOOK,
            "rule_note": AUREA_RULE_NOTE,
            "attributes": AUREA_CUSTOM_ATTRIBUTES,
            "power_packs": AUREA_CUSTOM_POWER_PACKS,
            "skills": AUREA_CUSTOM_SKILLS,
        },
    }


@router.get("/systems")
async def list_game_systems(response: Response):
    """Public list of game systems advertised by Table-Gnostic."""
    response.headers["Cache-Control"] = "public, max-age=300"
    return {"default": DEFAULT_SYSTEM_ID, "systems": GAME_SYSTEMS}


@router.get("/anime5e/classes")
async def anime5e_class_library(response: Response):
    """V6.25.13 — Anime 5E core class library (CANONICAL).

    Returns the canonical 14-class roster with full L1-L20 progression
    extracted from the Anime 5E core rulebook (dys_anime5e_rpg_v1.3.6).
    Each class entry surfaces:
      • starting proficiencies (saves / skills / weapons / armour / tools)
      • hit die + primary ability
      • per-level features (verbatim mechanic NAMES + Point grants)
      • parsed `asi_or_feat` flag + total `points_granted` per level

    Per-class feature tables are now authoritative — the V6.25.12
    `features_pending` scaffold flag is retired.
    """
    from system_data.anime5e_class_library import (
        CORE_CLASSES, CORE_RULES_NOTES, PROFICIENCY_BONUS, grants_for,
    )
    response.headers["Cache-Control"] = "public, max-age=120"
    # Build the per-level grant matrix once on read.
    classes = []
    for cls in CORE_CLASSES:
        grants = {lvl: grants_for(cls["id"], lvl) for lvl in range(1, 21)}
        # Class-specific ASI levels parsed from the per-level grants.
        asi_levels = sorted(
            lvl for lvl, g in grants.items() if g.get("asi_or_feat")
        )
        classes.append({
            "id": cls["id"],
            "name": cls["name"],
            "page": cls.get("page"),
            "primary_ability": cls.get("primary_ability"),
            "hit_die": cls.get("hit_die"),
            "save_proficiencies": cls.get("save_proficiencies", []),
            "skill_picks": cls.get("skill_picks", 0),
            "weapon_proficiencies": cls.get("weapon_proficiencies", []),
            "armour_proficiencies": cls.get("armour_proficiencies", []),
            "tool_proficiencies": cls.get("tool_proficiencies", []),
            "asi_levels": asi_levels,
            "grants_by_level": grants,
        })
    return {
        "system": "anime-5e",
        "proficiency_bonus_by_level": PROFICIENCY_BONUS,
        "classes": classes,
        "rules_notes": CORE_RULES_NOTES,
    }


@router.get("/anime5e/dnd-conversion")
async def anime5e_dnd_conversion(response: Response, dnd_class: str | None = None):
    """V6.25.16 — D&D 5E → Anime 5E legacy class deconstruction.

    Source: Anime 5E core rulebook pp.82-88. Each D&D class maps to an
    Anime 5E core class id + a curated list of canonical Anime 5E
    attributes (with starter ranks) and suggested defects. The wizard
    surfaces this as "Convert from D&D" — the player can accept or
    override every recommendation.

    `?dnd_class=Fighter` → returns the single record for Fighter.
    No parameter → returns the full mapping.
    """
    from system_data.dnd_to_anime5e_conversion import (
        DND_TO_ANIME5E_CLASS_MAP, convert,
    )
    response.headers["Cache-Control"] = "public, max-age=300"
    if dnd_class:
        rec = convert(dnd_class)
        if not rec:
            return {
                "dnd_class": dnd_class,
                "error": "Unknown D&D class",
                "available": sorted(DND_TO_ANIME5E_CLASS_MAP.keys()),
            }
        return rec
    return {
        "source_pages": "Anime 5E core rulebook pp.82-88",
        "mapping": [
            {"dnd_class": k, **v}
            for k, v in DND_TO_ANIME5E_CLASS_MAP.items()
        ],
    }



@router.get("/systems/{system_id}/reference")
async def system_reference(system_id: str, response: Response):
    """System-aware reference data — D&D 5E, Anime 5E, Cypher, etc.

    Returns mechanic-only content extracted from each system's open licence
    (CC-BY SRD 5.1 for D&D, OGL for Anime 5E, Cypher System Creator for
    Cypher). For BESM 4E the canonical /api/besm/reference is returned to
    preserve the deeper attribute/skill/defect content already shipped.
    """
    response.headers["Cache-Control"] = "public, max-age=300"
    if system_id == "besm-4e":
        # Deep BESM content already lives on /api/besm/reference.
        return await besm_reference()
    from system_data import REFERENCE_BY_SYSTEM
    if system_id not in REFERENCE_BY_SYSTEM:
        return {"system_id": system_id, "kind": "scaffold",
                "rule_note": "Reference content for this system has not yet been "
                              "extracted. GMs may use the Atelier Reference Editor "
                              "to seed campaign-scoped Attributes / Skills / "
                              "Defects / Weapons / Items / Companions / Custom rules."}
    return REFERENCE_BY_SYSTEM[system_id]



@router.get("/cypher/flavors")
async def cypher_flavors(genre: str = ""):
    """V6.25.25 — Cypher Flavor catalogue.

    Flavors re-skin canonical Type / Descriptor / Foci / Cypher / Artifact
    mechanics so the SAME rules fit a different genre vocabulary at the
    table. They never add new mechanics — they substitute names.
    Returns the full set when no `genre` is given.
    """
    from system_data.cypher_data import flavors_for_genre
    rows = flavors_for_genre(genre)
    return {"genre": genre or "any", "rows": rows, "total": len(rows)}


@router.get("/cypher/besm-conversion")
async def cypher_besm_conversion(type: str = "", descriptor: str = "",
                                   focus: str = "", tier: int = 1):
    """V6.25.25 — Cypher → BESM 4E character converter.

    Maps a "[descriptor] [type] who [focus]" sentence to a BESM 4E
    starter build (stats + attribute list + defects + estimated CP).
    Use to re-instantiate the same fictional concept under BESM rules.
    """
    from system_data.cypher_to_besm_conversion import convert_to_besm
    return convert_to_besm(cypher_type=type, descriptor=descriptor,
                            focus=focus, tier=int(tier or 1))


@router.get("/cypher/bestiary")
async def cypher_bestiary(genre: str = "", level_min: int = 0, level_max: int = 10):
    """V6.25.24 (Cycle B-6) — Cypher creature roster.

    Returns the seeded bestiary filtered by optional `genre` and a level
    band [level_min, level_max]. Each row is mechanic-only (level,
    health, damage, armor, role, genre tags) — no rulebook prose.
    """
    from system_data.cypher_data import list_bestiary
    rows = list_bestiary(genre)
    rows = [r for r in rows if level_min <= r["level"] <= level_max]
    return {
        "rows": rows,
        "total": len(rows),
        "genre": genre or "any",
        "level_band": [level_min, level_max],
    }


@router.get("/cypher/random-table")
async def cypher_random_table(kind: str = "cypher", genre: str = "",
                                level_modifier: int = 0):
    """V6.25.24 (Cycle B-5) — Cypher / Artifact random-roll table.

    Rolls a 1d<N> against the seeded cypher (12) or artifact (6) list,
    optionally filtered by genre tag. Returns the chosen entry plus a
    rolled level (1d6 + entry's printed modifier + caller `level_modifier`).
    Designed for GM table-side play — "the lucky draw paid out a Spatial
    Warp at level 5".

    Charges convention:
      * Cyphers ship with `charges: 1` by default — they're one-shot
        consumables.
      * Artifacts carry the printed `depletion` roll (e.g. "1 in 1d20")
        that the GM rolls after each significant use; on a depleted
        result the artifact is spent unless it has a `recharge` field.
    """
    import random
    import re
    from system_data.cypher_data import CYPHERS, ARTIFACTS

    if kind == "cypher":
        pool = list(CYPHERS)
    elif kind == "artifact":
        pool = list(ARTIFACTS)
    else:
        raise HTTPException(422, f"kind must be cypher | artifact (got {kind!r})")

    if genre and genre != "any":
        # Most rows don't carry explicit genre tags yet — those count as
        # genre-agnostic (always available). If a row HAS tags, gate by them.
        pool = [
            r for r in pool
            if not r.get("genres")
            or genre in (r.get("genres") or [])
            or "any" in (r.get("genres") or [])
        ]

    if not pool:
        raise HTTPException(404, f"No {kind}s available for genre={genre!r}.")

    pick = random.choice(pool)
    # Roll the level — parse "1d6+N" / "1d6"
    m = re.match(r"^\s*1d6\s*(?:\+\s*(\d+))?\s*$", str(pick.get("level", "1d6")))
    bonus = int(m.group(1)) if m and m.group(1) else 0
    rolled_die = random.randint(1, 6)
    rolled_level = rolled_die + bonus + int(level_modifier or 0)

    out = {
        "kind": kind,
        "genre": genre or "any",
        "entry": pick,
        "roll": {
            "die": "1d6",
            "result": rolled_die,
            "printed_modifier": bonus,
            "extra_modifier": int(level_modifier or 0),
            "level": rolled_level,
        },
        "charges": pick.get("charges", 1 if kind == "cypher" else None),
        "depletion": pick.get("depletion"),
        "recharge": pick.get("recharge"),
    }
    return out



@router.get("/cypher/tier-helper")
async def cypher_tier_helper(type: str = "warrior", tier: int = 1):
    """V6.25.23 — Cypher tier-progression helper.

    For a given character `type` (warrior / adept / explorer / speaker)
    and `tier` (1-6), returns:
      * the tier's effort cap + advancement step list (4 × 4 XP)
      * full ability roster up to and including that tier (with
        `tier` per row so the builder can colour-band them)
      * starting-stat snapshot the builder uses to seed pools / edge
      * unlocked tier blurb / role blurb for the wizard banner

    This is what the Cycle B-2 character builder calls when a player
    picks their type + tier; the response is everything the builder
    needs to render a tier-progression sidebar without re-fetching
    /reference.
    """
    from system_data.cypher_data import (
        get_type_full, tier_caps, all_abilities_for, ADVANCEMENT_STEPS_PER_TIER,
    )
    t = get_type_full(type)
    if not t:
        raise HTTPException(404, f"Unknown Cypher type: {type}")
    cap = tier_caps(tier)
    if not cap:
        raise HTTPException(422, f"Tier must be 1-6 (got {tier})")
    return {
        "type": {
            "key": t["key"],
            "name": t["name"],
            "role_blurb": t["role_blurb"],
            "starting_stat_pools": t["starting_stat_pools"],
            "starting_edge": t["starting_edge"],
            "free_pool_points": t["free_pool_points"],
            "starting_effort": t["starting_effort"],
            "starting_cypher_limit": t["starting_cypher_limit"],
        },
        "tier": cap,
        "abilities_unlocked": all_abilities_for(t["key"], int(tier)),
        "advancement_steps_per_tier": ADVANCEMENT_STEPS_PER_TIER,
        "tier_advancement_xp_total": 16,
    }
