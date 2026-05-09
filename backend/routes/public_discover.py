"""Public Discover Showcase — V6.25.13.

Lets a GM publish their campaign as a SEO-indexed public showcase page at
`tablegnostic.com/discover/{slug}`. Independent of:
  * `visibility=public`         — open-seat Discover (player recruitment)
  * `canon_published=true`      — GM-to-GM Canon Registry (delta drops)

The showcase MERGES three already-existing surfaces into one public read:
  * Campaign metadata (name, blurb, system, GM credit, tone, genre, tags)
  * Public codex nodes — only those with `visibility="shared"`
  * Marketplace listings — `source_campaign_id == cid` AND access ∈ public/paywall
  * Canon Registry blurb / delta-drop count when `canon_published=true`

Why a NEW gate (`discover_published`) instead of reusing `visibility` or
`canon_published`?
  * `visibility=public` defaults to TRUE on every new campaign — turning
    that into "show my whole world to the internet" would silently expose
    existing tables. Bad consent.
  * `canon_published` is GM-to-GM (registry of deltas / forking). The
    showcase is GM-to-WORLD (marketing / discovery). Different audience.

Routes:
    POST   /api/campaigns/{cid}/discover-publish    — GM publishes (auth)
    DELETE /api/campaigns/{cid}/discover-publish    — GM unpublishes (auth)
    GET    /api/public/discover                     — public gallery list
    GET    /api/public/discover/{slug}              — public showcase detail
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["public-discover"])


class DiscoverPublishIn(BaseModel):
    blurb: str = Field(default="", max_length=600)


SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    s = SLUG_RE.sub("-", (name or "").lower()).strip("-")
    return s[:60] or "table"


async def _unique_slug(base: str, current_cid: str) -> str:
    """Find a slug that doesn't collide with another published campaign."""
    candidate = base
    n = 2
    while True:
        clash = await db.campaigns.find_one(
            {"discover_slug": candidate,
             "discover_published": True,
             "id": {"$ne": current_cid}},
            {"_id": 0, "id": 1},
        )
        if not clash:
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def _card(c: dict, marketplace_count: int) -> dict:
    return {
        "slug": c.get("discover_slug") or "",
        "id": c["id"],
        "name": c.get("name", ""),
        "blurb": (c.get("canon_blurb") or c.get("description") or "").strip(),
        "system": c.get("system", ""),
        "system_id": c.get("system_id", ""),
        "tone": c.get("tone") or "",
        "genre": c.get("genre") or "",
        "tags": c.get("tags") or [],
        "gm_name": c.get("gm_name", ""),
        "setting_name": c.get("setting_name") or "",
        "power_level": c.get("power_level") or "",
        "canon_published": bool(c.get("canon_published")),
        "marketplace_count": marketplace_count,
        "created_at": c.get("created_at", ""),
    }


@router.post("/campaigns/{cid}/discover-publish")
async def publish_to_discover(cid: str, body: DiscoverPublishIn,
                                user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may publish a public showcase.")

    base = camp.get("discover_slug") or slugify(camp.get("name") or "table")
    slug = await _unique_slug(base, cid)

    update = {
        "discover_published": True,
        "discover_slug": slug,
        "updated_at": now_iso(),
    }
    if body.blurb.strip():
        update["canon_blurb"] = body.blurb.strip()

    await db.campaigns.update_one({"id": cid}, {"$set": update})
    return {"ok": True, "published": True, "slug": slug}


@router.delete("/campaigns/{cid}/discover-publish")
async def unpublish_from_discover(cid: str,
                                    user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may unpublish")
    await db.campaigns.update_one(
        {"id": cid},
        {"$set": {"discover_published": False, "updated_at": now_iso()}},
    )
    return {"ok": True, "published": False}


@router.get("/public/discover")
async def list_public_discover(limit: int = 60, skip: int = 0,
                                 system: Optional[str] = None,
                                 q: Optional[str] = None):
    """Public gallery — no auth. Returns published campaign cards."""
    where: dict = {"discover_published": True}
    if system:
        where["system_id"] = system
    if q:
        where["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"canon_blurb": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    limit = max(1, min(120, int(limit)))
    skip = max(0, int(skip))

    rows = await db.campaigns.find(where, {"_id": 0}) \
        .sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)
    cards = []
    for c in rows:
        mp_count = await db.marketplace_listings.count_documents({
            "source_campaign_id": c["id"],
            "access": {"$in": ["public", "paywall"]},
        })
        cards.append(_card(c, mp_count))
    total = await db.campaigns.count_documents(where)
    return {"items": cards, "total": total, "limit": limit, "skip": skip}


@router.get("/public/discover/{slug}")
async def get_public_discover(slug: str):
    """Public showcase detail — no auth. Returns campaign meta + shared
    codex nodes + marketplace listings + canon summary for the slug."""
    camp = await db.campaigns.find_one(
        {"discover_slug": slug, "discover_published": True},
        {"_id": 0},
    )
    if not camp:
        raise HTTPException(404, "Showcase not found or unpublished.")
    cid = camp["id"]

    # Public codex nodes — only "shared" visibility (GM has consciously
    # surfaced these to non-seat readers). Cap to 200 for page size.
    nodes = await db.nodes.find(
        {"campaign_id": cid, "visibility": "shared"},
        {"_id": 0, "revealed_to": 0},
    ).sort("created_at", -1).to_list(length=200)

    # Edges between visible nodes (so the public graph links up).
    visible_ids = {n["id"] for n in nodes}
    edges_raw = await db.edges.find(
        {"campaign_id": cid}, {"_id": 0},
    ).to_list(length=400)
    edges = [
        e for e in edges_raw
        if e.get("from_node") in visible_ids and e.get("to_node") in visible_ids
    ]

    # Marketplace listings sourced from this campaign.
    listings = await db.marketplace_listings.find(
        {"source_campaign_id": cid,
         "access": {"$in": ["public", "paywall"]}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=120)

    # Canon delta-drop count (Canon Registry surface — surfaces only when
    # the GM has separately enabled canon_published).
    deltas_count = 0
    if camp.get("canon_published"):
        try:
            deltas_count = await db.deltas.count_documents({"campaign_id": cid})
        except Exception:
            deltas_count = 0

    mp_count = await db.marketplace_listings.count_documents({
        "source_campaign_id": cid,
        "access": {"$in": ["public", "paywall"]},
    })

    return sanitize({
        "campaign": _card(camp, mp_count),
        "nodes": nodes,
        "edges": edges,
        "marketplace": listings,
        "canon": {
            "published": bool(camp.get("canon_published")),
            "blurb": camp.get("canon_blurb") or "",
            "deltas_count": deltas_count,
        },
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "marketplace_count": len(listings),
        },
    })
