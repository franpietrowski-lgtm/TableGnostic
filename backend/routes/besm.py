"""BESM 4E reference + Game-systems registry — public read-only endpoints."""
from fastapi import APIRouter, Response

from besm_data import (
    ACTIONS, ARMOUR, ATTRIBUTES, AUREA_CUSTOM_ATTRIBUTES, AUREA_CUSTOM_BOOK,
    AUREA_CUSTOM_POWER_PACKS, AUREA_CUSTOM_SKILLS, AUREA_RULE_NOTE,
    BOOK, BOOK_EXTRAS, COMPANIONS, CORE_STATS, DEFECTS, DEFAULT_SYSTEM_ID,
    DERIVED_VALUES, ENHANCEMENTS, EXTRAS_RULES, GAME_SYSTEMS,
    GENERIC_BLURBS, ITEMS_GEAR, ITEM_ENHANCEMENTS, ITEM_LIMITERS,
    LIMITERS, NODE_TYPES, POWER_LEVELS,
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
        "size_modifiers": with_source(SIZE_MODIFIERS),
        "weapons": with_source(WEAPONS),
        "items_gear": with_source(ITEMS_GEAR),
        "armour": with_source(ARMOUR),
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
    """V6.25.12 — Anime 5E core class library scaffold.

    Returns the full L1-L20 progression grid (proficiency bonus, ASI
    levels, milestone levels) plus the canonical Anime 5E core class
    roster with starting proficiencies / save profs / skill pools /
    hit dice. Per-level FEATURE NAMES are scaffold-only until the GM
    seeds them via Custom Rules / Reference Editor — `features_pending`
    flags which classes are awaiting authoritative seeding.
    """
    from system_data.anime5e_class_library import (
        ASI_LEVELS, CORE_CLASSES, MILESTONE_LEVELS, PROFICIENCY_BONUS,
        grants_for,
    )
    response.headers["Cache-Control"] = "public, max-age=120"
    # Build the per-level grant matrix once on read.
    classes = []
    for cls in CORE_CLASSES:
        grants = {lvl: grants_for(cls["id"], lvl) for lvl in range(1, 21)}
        classes.append({
            "id": cls["id"], "name": cls["name"], "page": cls.get("page"),
            "primary_stat": cls.get("primary_stat"),
            "hit_die": cls.get("hit_die"),
            "save_proficiencies": cls.get("save_proficiencies", []),
            "skill_picks": cls.get("skill_picks", 0),
            "skill_pool": cls.get("skill_pool", []),
            "weapon_proficiencies": cls.get("weapon_proficiencies", []),
            "armour_proficiencies": cls.get("armour_proficiencies", []),
            "crafting_traditions": cls.get("crafting_traditions"),
            "features_pending": bool(cls.get("_features_pending")),
            "grants_by_level": grants,
        })
    return {
        "system": "anime-5e",
        "proficiency_bonus_by_level": PROFICIENCY_BONUS,
        "asi_levels": sorted(ASI_LEVELS),
        "milestone_levels": sorted(MILESTONE_LEVELS),
        "classes": classes,
        "scaffold_note": (
            "Per-level feature NAMES are scaffold placeholders until "
            "authoritative content is seeded from the Anime 5E core book. "
            "GMs can author class features via Custom Rules / Reference "
            "Editor TODAY — those entries take priority over this fallback."
        ),
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
