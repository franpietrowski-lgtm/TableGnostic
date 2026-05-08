"""V6.25.26 — Crafting Service Materials.

The user requested a Crafting Service surface in the Workshop with three
tiers of materials:

    Raw       — off-the-ground / out-of-the-ground / off-an-entity raw
                products: ore, hide, flowers, roots, bark, nectar, etc.
    Refined   — raw transformed: ore→ingot, gem→polished gem, flower→dye.
    Assembled — refined transformed into a finished good: ingot→hilt,
                gem set in jewelry, nectar→ale, hide→armor, etc.

Each entry is a small Pydantic-validated row with optional ingredient
chains (Refined cites which Raw it derives from; Assembled cites which
Refined / Raw rows it consumed). The chain is purely informational — we
don't deduct supply on craft, we just record the recipe so the
Director's Console can offer materials as injectable loot drops and the
character sheet can list owned materials.

Endpoints:
    POST   /api/campaigns/{cid}/materials              create
    GET    /api/campaigns/{cid}/materials[?tier=]      list (optional tier filter)
    GET    /api/campaigns/{cid}/materials/{mid}        read
    PATCH  /api/campaigns/{cid}/materials/{mid}        update
    DELETE /api/campaigns/{cid}/materials/{mid}        delete
"""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["materials"])


MaterialTier = Literal["raw", "refined", "assembled"]


class MaterialIn(BaseModel):
    tier: MaterialTier
    name: str = Field(..., min_length=1, max_length=120)
    summary: str = Field(default="", max_length=500)
    rarity: str = Field(default="common", max_length=40,
                          description="common | uncommon | rare | very_rare | legendary")
    ingredient_ids: List[str] = Field(default_factory=list,
                          description="material ids that compose this row (refined cites raw; assembled cites refined+raw).")
    yields: int = Field(default=1, ge=1,
                         description="How many units one craft produces.")
    fields: Dict[str, Any] = Field(default_factory=dict,
                          description="Free-form: cost, weight, source biome, etc.")
    also_to_codex: bool = Field(default=False,
                          description="Mirror as a codex node when first saved.")


async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    return camp


def _is_gm(camp: dict, user: dict) -> bool:
    return camp.get("gm_id") == user["id"] or user.get("role") == "admin"


@router.post("/campaigns/{cid}/materials")
async def create_material(cid: str, body: MaterialIn,
                            user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    # Validate ingredient chain — every cited id must exist on this campaign.
    if body.ingredient_ids:
        existing = await db.materials.find(
            {"campaign_id": cid, "id": {"$in": body.ingredient_ids}},
            {"_id": 0, "id": 1}).to_list(200)
        existing_ids = {r["id"] for r in existing}
        bad = [i for i in body.ingredient_ids if i not in existing_ids]
        if bad:
            raise HTTPException(422, f"Unknown ingredient ids: {bad}")
    row = {
        "id": new_id(),
        "campaign_id": cid,
        "tier": body.tier,
        "name": body.name.strip(),
        "summary": (body.summary or "").strip(),
        "rarity": body.rarity,
        "ingredient_ids": body.ingredient_ids,
        "yields": body.yields,
        "fields": body.fields or {},
        "created_at": now_iso(),
        "created_by_id": user["id"],
        "created_by_name": user.get("name") or user.get("email"),
    }
    await db.materials.insert_one(row)
    row.pop("_id", None)
    if body.also_to_codex:
        try:
            node = {
                "id": new_id(),
                "campaign_id": cid,
                "title": row["name"],
                "name": row["name"],
                "type": "concept",
                "node_kind": "material",
                "summary": row["summary"] or f"{row['tier'].title()} crafting material.",
                "content": row["summary"] or "",
                "tags": ["from-material", row["tier"], row["rarity"]],
                "fields": {"source_material_id": row["id"], "tier": row["tier"]},
                "visibility": "gm",
                "created_at": row["created_at"],
                "owner_id": user["id"],
                "creation_tree": {"section": "Codex"},
            }
            await db.nodes.insert_one(node)
        except Exception:
            pass
    return row


@router.get("/campaigns/{cid}/materials")
async def list_materials(cid: str, tier: Optional[str] = None,
                            user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    is_gm = _is_gm(camp, user)
    if not is_gm and user["id"] not in (camp.get("player_ids") or []):
        raise HTTPException(403, "Not a member of this campaign.")
    q: Dict[str, Any] = {"campaign_id": cid}
    if tier:
        if tier not in ("raw", "refined", "assembled"):
            raise HTTPException(422, "tier must be raw | refined | assembled.")
        q["tier"] = tier
    cursor = db.materials.find(q, {"_id": 0}).sort("created_at", -1)
    return {"rows": [r async for r in cursor]}


@router.get("/campaigns/{cid}/materials/{mid}")
async def get_material(cid: str, mid: str,
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    is_gm = _is_gm(camp, user)
    if not is_gm and user["id"] not in (camp.get("player_ids") or []):
        raise HTTPException(403, "Not a member of this campaign.")
    row = await db.materials.find_one(
        {"campaign_id": cid, "id": mid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Material not found.")
    return row


@router.patch("/campaigns/{cid}/materials/{mid}")
async def update_material(cid: str, mid: str, body: MaterialIn,
                            user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.materials.update_one(
        {"campaign_id": cid, "id": mid},
        {"$set": {
            "tier": body.tier,
            "name": body.name.strip(),
            "summary": (body.summary or "").strip(),
            "rarity": body.rarity,
            "ingredient_ids": body.ingredient_ids,
            "yields": body.yields,
            "fields": body.fields or {},
            "updated_at": now_iso(),
        }})
    if res.matched_count == 0:
        raise HTTPException(404, "Material not found.")
    row = await db.materials.find_one(
        {"campaign_id": cid, "id": mid}, {"_id": 0})
    return row


@router.delete("/campaigns/{cid}/materials/{mid}")
async def delete_material(cid: str, mid: str,
                            user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.materials.delete_one(
        {"campaign_id": cid, "id": mid})
    return {"ok": True, "deleted": res.deleted_count}
