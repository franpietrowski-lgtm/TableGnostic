"""Public Canon Registry — V6.13.

Lets GMs publish their campaign to a cross-table registry so other GMs can
discover the campaign's Delta Drops and subscribe. Players are NOT exposed
here — this is author-to-author sharing, distinct from Discover (which
surfaces open player seats).

Storage:
    * `campaigns.canon_published` (bool) + `campaigns.canon_blurb` (str)
      — owned by the GM; toggles the campaign's presence in the registry.
    * `canon_subscriptions` collection — doc per (user_id, campaign_id) —
      — tracks which GMs follow which published canons.

Routes:
    GET    /api/canon-registry                         — public list
    POST   /api/campaigns/{cid}/canon-publish          — GM publishes
    DELETE /api/campaigns/{cid}/canon-publish          — GM unpublishes
    POST   /api/canon-registry/{cid}/subscribe         — auth'd subscribe
    DELETE /api/canon-registry/{cid}/subscribe         — unsubscribe
    GET    /api/canon-registry/subscriptions           — my subscriptions
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["canon-registry"])


class PublishIn(BaseModel):
    blurb: str = Field(default="", max_length=500)


def _card_from_campaign(c: dict, subs_count: int, deltas_count: int) -> dict:
    return {
        "id": c["id"],
        "name": c.get("name", ""),
        "system": c.get("system", ""),
        "system_id": c.get("system_id", ""),
        "setting_name": c.get("setting_name") or "",
        "genre": c.get("genre", ""),
        "tone": c.get("tone") or "",
        "tags": c.get("tags") or [],
        "gm_name": c.get("gm_name", ""),
        "canon_blurb": c.get("canon_blurb") or c.get("description") or "",
        "member_count": len(c.get("member_ids") or []),
        "subscribers": subs_count,
        "delta_drops": deltas_count,
        "created_at": c.get("created_at", ""),
    }


@router.get("/canon-registry")
async def list_canon_registry():
    """Public — no auth required. Returns all campaigns whose GM has
    toggled `canon_published=true`, with per-campaign subscriber &
    delta-drop counts baked in.
    """
    rows = await db.campaigns.find(
        {"canon_published": True}, {"_id": 0},
    ).sort("created_at", -1).to_list(200)
    cards = []
    for c in rows:
        subs_count = await db.canon_subscriptions.count_documents(
            {"campaign_id": c["id"]})
        deltas_count = await db.deltas.count_documents(
            {"campaign_id": c["id"]}) if "deltas" in await db.list_collection_names() else 0
        cards.append(_card_from_campaign(c, subs_count, deltas_count))
    return sanitize(cards)


@router.post("/campaigns/{cid}/canon-publish")
async def publish_to_canon(cid: str, body: PublishIn,
                           user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may publish to the Canon Registry")
    await db.campaigns.update_one(
        {"id": cid},
        {"$set": {"canon_published": True,
                   "canon_blurb": body.blurb.strip(),
                   "updated_at": now_iso()}},
    )
    return {"ok": True, "published": True}


@router.delete("/campaigns/{cid}/canon-publish")
async def unpublish_from_canon(cid: str,
                                user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may unpublish")
    await db.campaigns.update_one(
        {"id": cid},
        {"$set": {"canon_published": False, "updated_at": now_iso()}},
    )
    return {"ok": True, "published": False}


@router.post("/canon-registry/{cid}/subscribe")
async def subscribe_to_canon(cid: str,
                              user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one(
        {"id": cid, "canon_published": True}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Canon not found or not published")
    existing = await db.canon_subscriptions.find_one(
        {"user_id": user["id"], "campaign_id": cid}, {"_id": 0})
    if existing:
        return existing
    doc = {
        "id": new_id(),
        "user_id": user["id"],
        "campaign_id": cid,
        "created_at": now_iso(),
    }
    await db.canon_subscriptions.insert_one(doc)
    return sanitize(doc)


@router.delete("/canon-registry/{cid}/subscribe")
async def unsubscribe_from_canon(cid: str,
                                  user: dict = Depends(get_current_user)):
    await db.canon_subscriptions.delete_one(
        {"user_id": user["id"], "campaign_id": cid})
    return {"ok": True}


@router.get("/canon-registry/subscriptions")
async def my_subscriptions(user: dict = Depends(get_current_user)):
    subs = await db.canon_subscriptions.find(
        {"user_id": user["id"]}, {"_id": 0}).to_list(200)
    # Hydrate with campaign cards.
    out = []
    for s in subs:
        c = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
        if not c or not c.get("canon_published"):
            continue
        subs_count = await db.canon_subscriptions.count_documents(
            {"campaign_id": c["id"]})
        deltas_count = 0
        try:
            deltas_count = await db.deltas.count_documents(
                {"campaign_id": c["id"]})
        except Exception:
            pass
        out.append({**_card_from_campaign(c, subs_count, deltas_count),
                    "subscribed_at": s["created_at"]})
    return sanitize(out)
