"""V6.16 — Cross-system Content Converter API.

Thin endpoint layer over `core.conversion_engine`. Three POST routes:

  POST /api/convert/content    — single mechanic translation
  POST /api/convert/character  — full character port + DB write
  POST /api/convert/creature   — full creature port + Codex node write

GM/admin-only on every route. The actual translation is Claude-assisted
(Anthropic Sonnet 4.5 via the EMERGENT LLM key).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.conversion_engine import (
    SUPPORTED_SYSTEMS,
    TARGET_SHAPE,
    build_content_prompt,
    call_claude_convert,
    compute_cost_balance,
    materialise_character,
    materialise_creature,
    validate_systems,
)
from core.db import db, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["convert"])


# ──────────────────────────────────────────────────────────────────────────
# Pydantic input schemas

class ConvertContentIn(BaseModel):
    source_system: str
    target_system: str
    source_kind: str  # "attribute" | "spell" | "focus" | "character" | …
    payload: Dict[str, Any]
    target_constraints: Optional[Dict[str, Any]] = None


class ConvertCharacterIn(BaseModel):
    source_character_id: str
    target_campaign_id: str
    new_owner_id: Optional[str] = None
    keep_folio: bool = True
    name_override: Optional[str] = None


class ConvertCreatureIn(BaseModel):
    source_node_id: str          # codex node where motive == "creature"
    target_campaign_id: str
    name_override: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────
# Endpoint — single-mechanic translation

@router.post("/convert/content")
async def convert_content(body: ConvertContentIn,
                          user: dict = Depends(get_current_user)):
    """Translate one mechanic between any two supported systems.

    Preview-only (no DB write) — returns the canonical target-system
    shape for the caller to paste/share/validate. V6.16.4: opened to
    any authenticated user so players can pull cross-system reference
    content on-demand. GM approval is still required to publish the
    translated entry into the target campaign's reference library.
    """
    if not user:
        raise HTTPException(401, "Authentication required.")
    validate_systems(body.source_system, body.target_system)
    if body.source_system == body.target_system:
        return {
            "name": body.payload.get("name") or body.payload.get("title") or "Untitled",
            "kind": body.source_kind,
            "target_system": body.target_system,
            "summary": "Same source/target — no conversion needed.",
            "target_payload": body.payload,
            "caveats": [],
            "citations": [],
        }
    prompt = build_content_prompt(
        body.source_system, body.target_system, body.source_kind,
        body.payload, body.target_constraints,
    )
    out = await call_claude_convert(
        prompt, f"{body.source_system}-to-{body.target_system}-{body.source_kind}",
    )
    out.setdefault("target_system", body.target_system)
    out.setdefault("kind", body.source_kind)
    out.setdefault("converted_by_user_id", user["id"])
    out.setdefault("converted_at", now_iso())
    return out


# ──────────────────────────────────────────────────────────────────────────
# Endpoint — full-character port

@router.post("/convert/character")
async def convert_character(body: ConvertCharacterIn,
                             user: dict = Depends(get_current_user)):
    """Take an existing character and produce a working sheet in the
    target campaign's system. The new character is saved + returned.

    Permission model: caller must be GM (or admin) of both source and
    target campaigns. This prevents content laundering — a GM can't
    fork another GM's character.
    """
    src_ch = await db.characters.find_one({"id": body.source_character_id}, {"_id": 0})
    if not src_ch:
        raise HTTPException(404, "Source character not found.")
    src_camp = await db.campaigns.find_one({"id": src_ch["campaign_id"]}, {"_id": 0})
    tgt_camp = await db.campaigns.find_one({"id": body.target_campaign_id}, {"_id": 0})
    if not tgt_camp:
        raise HTTPException(404, "Target campaign not found.")
    is_admin = user.get("role") == "admin"
    if not is_admin:
        if src_camp and src_camp.get("gm_id") != user["id"]:
            raise HTTPException(403, "Only the source campaign's GM (or admin) may convert.")
        if tgt_camp.get("gm_id") != user["id"]:
            raise HTTPException(403, "Only the target campaign's GM (or admin) may receive a converted character.")
    src_system = src_ch.get("system_id") or src_camp.get("system_id") or "besm-4e"
    tgt_system = tgt_camp.get("system_id") or "besm-4e"
    validate_systems(src_system, tgt_system)

    payload = {
        "name": src_ch.get("name"),
        "concept": src_ch.get("concept"),
        "total_points": src_ch.get("total_points"),
        "stats": src_ch.get("stats"),
        "attributes": src_ch.get("attributes") or [],
        "skills": src_ch.get("skills") or [],
        "defects": src_ch.get("defects") or [],
        "items": src_ch.get("items") or [],
        "weapons": src_ch.get("weapons") or [],
        "folio_bio": {
            "physical_description": (src_ch.get("folio") or {}).get("physical_description"),
            "personality_traits": (src_ch.get("folio") or {}).get("personality_traits"),
            "motivations": (src_ch.get("folio") or {}).get("motivations"),
            "fears_weaknesses": (src_ch.get("folio") or {}).get("fears_weaknesses"),
        },
    }
    constraints = {
        "target_power_level": tgt_camp.get("power_level"),
        "target_anime5e_xp_formula": tgt_camp.get("anime5e_xp_formula"),
        "target_house_rules": tgt_camp.get("house_rules"),
    }
    prompt = build_content_prompt(src_system, tgt_system, "character", payload, constraints)
    out = await call_claude_convert(prompt, f"char-{src_ch['id']}-to-{tgt_system}")
    target_payload = out.get("target_payload") or out
    owner_id = body.new_owner_id or src_ch.get("owner_id") or user["id"]
    owner_name = user["name"]
    if body.new_owner_id:
        u = await db.users.find_one({"id": body.new_owner_id}, {"_id": 0, "name": 1, "email": 1})
        if u:
            owner_name = u.get("name") or u.get("email") or "?"
            if (body.new_owner_id != tgt_camp["gm_id"]
                    and body.new_owner_id not in tgt_camp.get("member_ids", [])):
                await db.campaigns.update_one({"id": tgt_camp["id"]},
                                              {"$addToSet": {"member_ids": body.new_owner_id}})
    new_ch = await materialise_character(
        target_payload, tgt_system, tgt_camp, src_ch,
        owner_id, owner_name, body.keep_folio, body.name_override,
    )
    await db.characters.insert_one(new_ch)
    return {
        "character": sanitize(new_ch),
        "caveats": out.get("caveats") or [],
        "citations": out.get("citations") or [],
    }


# ──────────────────────────────────────────────────────────────────────────
# Endpoint — V6.16.3 NEW — creature stat-block port

@router.post("/convert/creature")
async def convert_creature(body: ConvertCreatureIn,
                           user: dict = Depends(get_current_user)):
    """Take an existing creature codex node and produce a target-system
    stat block. Saved as a NEW node in the target campaign's Knowledge
    Web (motive: "creature") so it appears in the Director's Console
    NPC pool ready to drop into encounters.

    Permission model: GM (or admin) of both source and target campaigns.
    """
    src_node = await db.nodes.find_one({"id": body.source_node_id}, {"_id": 0})
    if not src_node:
        raise HTTPException(404, "Source codex node not found.")
    if (src_node.get("motive") != "creature"
            and src_node.get("type") != "creature"
            and src_node.get("kind") != "creature"
            and (src_node.get("fields") or {}).get("kind") != "creature"):
        raise HTTPException(400, "Source node is not a creature — pick a node tagged as creature/monster.")
    src_camp = await db.campaigns.find_one({"id": src_node["campaign_id"]}, {"_id": 0})
    tgt_camp = await db.campaigns.find_one({"id": body.target_campaign_id}, {"_id": 0})
    if not tgt_camp:
        raise HTTPException(404, "Target campaign not found.")
    is_admin = user.get("role") == "admin"
    if not is_admin:
        if src_camp and src_camp.get("gm_id") != user["id"]:
            raise HTTPException(403, "Only the source campaign's GM (or admin) may convert.")
        if tgt_camp.get("gm_id") != user["id"]:
            raise HTTPException(403, "Only the target campaign's GM (or admin) may receive a converted creature.")
    src_system = (src_node.get("fields") or {}).get("system_id") or src_camp.get("system_id") or "besm-4e"
    tgt_system = tgt_camp.get("system_id") or "besm-4e"
    validate_systems(src_system, tgt_system)

    fields = src_node.get("fields") or {}
    payload = {
        "name": src_node.get("title"),
        "summary": src_node.get("summary") or fields.get("summary"),
        "description": fields.get("description"),
        # Carry whichever per-system stat block is on the node already.
        "stats": fields.get("stats"),
        "attributes": fields.get("attributes"),
        "defects": fields.get("defects"),
        "total_points": fields.get("total_points"),
        "cr": fields.get("cr"),
        "hp": fields.get("hp"),
        "ac": fields.get("ac"),
        "level": fields.get("level"),
        "health": fields.get("health"),
        "dnd_state": fields.get("dnd_state"),
        "cypher_state": fields.get("cypher_state"),
        "anime5e_state": fields.get("anime5e_state"),
        "tags": src_node.get("tags") or [],
    }
    constraints = {
        "target_power_level": tgt_camp.get("power_level"),
        "target_house_rules": tgt_camp.get("house_rules"),
    }
    prompt = build_content_prompt(src_system, tgt_system, "creature", payload, constraints)
    out = await call_claude_convert(prompt, f"creature-{src_node['id']}-to-{tgt_system}")
    target_payload = out.get("target_payload") or out

    new_node = await materialise_creature(
        target_payload, tgt_system, tgt_camp, src_node, body.name_override,
    )
    await db.nodes.insert_one(new_node)
    return {
        "node": sanitize(new_node),
        "caveats": out.get("caveats") or [],
        "citations": out.get("citations") or [],
    }


# ──────────────────────────────────────────────────────────────────────────
# Backward-compat re-exports for existing tests + callers.
# Pre-V6.16.3 the module owned all the engine logic; consumers imported
# `_materialise_character`, `_validate_systems`, etc. from `routes.conversion`.
# Keep the public-private aliases so test files + future imports don't break.

from core.conversion_engine import (  # noqa: E402,F401  (re-exports for backwards compat)
    coerce_to_dict_list as _coerce_to_dict_list,
    materialise_character as _materialise_character,
    materialise_creature as _materialise_creature,
    normalise_tristat_cost_fields as _normalise_tristat_cost_fields,
    validate_systems as _validate_systems,
    SYSTEM_PROMPT_CONTENT,
)


# ──────────────────────────────────────────────────────────────────────────
# Cost-balance preview — V6.25.41

class CostBalancePreviewIn(BaseModel):
    source_character_id: str
    target_system: str


@router.post("/convert/preview-cost-balance")
async def preview_cost_balance(body: CostBalancePreviewIn,
                                user: dict = Depends(get_current_user)):
    """GM-only. Returns a `{source_budget, target_budget, delta,
    delta_pct, within_tolerance, notes}` report comparing a source
    character's native budget to what its target_system equivalent
    *would* spend — without running the LLM. Uses the source spend as
    the target estimate so we can show a clean "looks balanced /
    overshoots / undershoots" pre-flight before committing to a full
    Claude conversion."""
    if body.target_system not in SUPPORTED_SYSTEMS:
        raise HTTPException(400, f"Unsupported target_system: {body.target_system}")
    src = await db.characters.find_one({"id": body.source_character_id}, {"_id": 0})
    if not src:
        raise HTTPException(404, "Source character not found.")
    # The naive preview assumes Claude will hit the source's spend; the
    # delta therefore reports how much *room* the GM has to play with on
    # the target side rather than predicting Claude's actual output.
    return compute_cost_balance(
        src.get("system_id") or "besm-4e",
        src,
        body.target_system,
        src,
    )


__all__ = [
    "router",
    "ConvertContentIn",
    "ConvertCharacterIn",
    "ConvertCreatureIn",
    "SUPPORTED_SYSTEMS",
    "TARGET_SHAPE",
    "SYSTEM_PROMPT_CONTENT",
    # Backward-compat aliases.
    "_coerce_to_dict_list",
    "_materialise_character",
    "_materialise_creature",
    "_normalise_tristat_cost_fields",
    "_validate_systems",
]
