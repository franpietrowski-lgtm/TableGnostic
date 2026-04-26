"""BESM 4E reference + Game-systems registry — public read-only endpoints."""
from fastapi import APIRouter, Response

from besm_data import (
    ACTIONS, ARMOUR, ATTRIBUTES, AUREA_CUSTOM_ATTRIBUTES, AUREA_CUSTOM_BOOK,
    AUREA_CUSTOM_POWER_PACKS, AUREA_CUSTOM_SKILLS, AUREA_RULE_NOTE,
    BOOK, BOOK_EXTRAS, COMPANIONS, CORE_STATS, DEFECTS, DEFAULT_SYSTEM_ID,
    DERIVED_VALUES, ENHANCEMENTS, EXTRAS_RULES, GAME_SYSTEMS,
    GENERIC_BLURBS, ITEMS_GEAR, LIMITERS, NODE_TYPES, POWER_LEVELS,
    RACE_TEMPLATES, SIZE_MODIFIERS, SIZE_TEMPLATES, SKILL_GROUPS,
    TARGET_NUMBERS, WEAPONS, attribute_blurb, attribute_whitelist,
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
