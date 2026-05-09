"""GM Cost Overrides — V6.25.33.

Per-campaign overrides for the canonical CP cost of any reference-mechanic
entry (BESM attribute / defect / skill_group / race_template / class_template,
Anime 5E point-buy attribute / defect). The GM enters a single number that
**replaces** the canon cost outright; level / effective level / mechanics
stay intact, only the price changes.

Schema (collection: `cost_overrides`):
    {
        "id":            "<uuid>",
        "campaign_id":   "<campaign-uuid>",
        "kind":          "attribute" | "defect" | "skill_group"
                       | "race_template" | "class_template"
                       | "point_buy_attribute",   # Anime 5E
        "name":          "Tough" | "Apocophae" | "Apprentice Artisan" | …,
        "override_cost": 3,          # CP per level (attribute/skill/defect)
                                     # OR total CP (race/class template)
        "note":          "Aurea house rule — Tough is half-price for clergy",
        "gm_id":         "<user-uuid>",
        "created_at":    "<iso-date>",
        "updated_at":    "<iso-date>",
    }

The frontend Builder + Picker call `GET /api/campaigns/{cid}/cost-overrides`
once per campaign load and apply them to the displayed costs locally.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["cost-overrides"])


_ALLOWED_KINDS = {
    "attribute",            # BESM attribute / Anime 5E point-buy attr
    "defect",               # BESM / Anime 5E defect
    "skill_group",          # BESM skill_group
    "race_template",        # BESM canonical race
    "class_template",       # BESM canonical class
    "point_buy_attribute",  # Anime 5E supplement layer
    "heritage",             # Anime 5E heritage (race-equivalent)
}


class CostOverrideIn(BaseModel):
    kind: str
    name: str
    override_cost: float
    note: Optional[str] = ""


class CostOverrideUpdate(BaseModel):
    override_cost: Optional[float] = None
    note: Optional[str] = None


async def _require_gm(campaign_id: str, user: dict) -> dict:
    camp = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp.get("gm_id") and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM (or admin) can manage cost overrides.")
    return camp


@router.get("/campaigns/{cid}/cost-overrides")
async def list_cost_overrides(cid: str, user: dict = Depends(get_current_user)):
    """List active cost overrides for a campaign. Anyone seated at the table can read."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    is_gm = user["id"] == camp.get("gm_id")
    is_member = user["id"] in (camp.get("member_ids") or [])
    if not (is_gm or is_member or user.get("role") == "admin"):
        raise HTTPException(403, "Not seated at this table.")
    rows = await db.cost_overrides.find(
        {"campaign_id": cid}, {"_id": 0}
    ).sort("name", 1).to_list(500)
    return {"campaign_id": cid, "overrides": rows, "count": len(rows)}


@router.put("/campaigns/{cid}/cost-overrides")
async def upsert_cost_override(cid: str, body: CostOverrideIn,
                                user: dict = Depends(get_current_user)):
    """GM sets / replaces the override for a (kind, name) pair. Idempotent."""
    await _require_gm(cid, user)
    if body.kind not in _ALLOWED_KINDS:
        raise HTTPException(400, f"Unsupported kind '{body.kind}'. "
                                 f"Allowed: {sorted(_ALLOWED_KINDS)}")
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(400, "Name is required.")
    existing = await db.cost_overrides.find_one(
        {"campaign_id": cid, "kind": body.kind, "name": name},
        {"_id": 0},
    )
    payload = {
        "campaign_id":   cid,
        "kind":          body.kind,
        "name":          name,
        "override_cost": float(body.override_cost),
        "note":          (body.note or "").strip(),
        "gm_id":         user["id"],
        "updated_at":    now_iso(),
    }
    if existing:
        await db.cost_overrides.update_one(
            {"id": existing["id"]},
            {"$set": payload},
        )
        out = {**existing, **payload}
        return {"override": out, "created": False}
    payload["id"] = new_id()
    payload["created_at"] = now_iso()
    await db.cost_overrides.insert_one(dict(payload))
    payload.pop("_id", None)
    return {"override": payload, "created": True}


@router.delete("/campaigns/{cid}/cost-overrides/{oid}")
async def delete_cost_override(cid: str, oid: str,
                                user: dict = Depends(get_current_user)):
    await _require_gm(cid, user)
    res = await db.cost_overrides.delete_one({"id": oid, "campaign_id": cid})
    if res.deleted_count == 0:
        raise HTTPException(404, "Override not found.")
    return {"deleted": oid}


@router.patch("/campaigns/{cid}/cost-overrides/{oid}")
async def patch_cost_override(cid: str, oid: str, body: CostOverrideUpdate,
                                user: dict = Depends(get_current_user)):
    await _require_gm(cid, user)
    update: dict = {"updated_at": now_iso()}
    if body.override_cost is not None:
        update["override_cost"] = float(body.override_cost)
    if body.note is not None:
        update["note"] = body.note.strip()
    if len(update) == 1:
        raise HTTPException(400, "Nothing to update.")
    res = await db.cost_overrides.update_one(
        {"id": oid, "campaign_id": cid},
        {"$set": update},
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Override not found.")
    out = await db.cost_overrides.find_one({"id": oid}, {"_id": 0})
    return {"override": out}
