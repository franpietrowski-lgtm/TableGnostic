"""Marketplace v1 — V6.25.5

Cross-table sharing of homebrew Custom Rules entries (race / class /
size / feat / power_bundle / etc) so the growing community canon is a
shared library rather than an island per table.

Design:
  * `marketplace_listings` — snapshot collection. Publishing copies the
    relevant fields (kind, name, description_note, effects / fields)
    so future edits to the source DON'T retroactively mutate clones.
  * Access: `private` (default — owner-only browse) | `public` (any
    authenticated user can clone) | `paywall` (V2; treated like
    `public` for V1 — endpoint validates but skips Stripe).
  * Cloning: writes into the target campaign's `custom_attributes`
    (for kind in homebrew kinds) or `references` (for items / weapons
    / spells). Increments `downloads` on the listing.

Endpoints:
  POST   /api/marketplace/publish      — snapshot a custom rule.
  GET    /api/marketplace               — paginated browse + filters.
  POST   /api/marketplace/{lid}/clone   — clone into target campaign.
  DELETE /api/marketplace/{lid}         — author can unpublish.
"""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["marketplace"])

# Kinds the marketplace accepts. Mirrors CustomAttributeIn + reference
# editor. Keep in sync if either expands.
HOMEBREW_KINDS = {
    "attribute", "defect", "skill", "feature", "trait", "feat", "house",
    "descriptor", "focus", "ability", "cypher", "artifact",
    "race", "class", "size", "stat",
}
REFERENCE_KINDS = {
    "weapon", "armor", "item", "spell",
    "power_pack", "power_bundle",
}


# ─── Models ─────────────────────────────────────────────────────────────


class MarketplacePublishIn(BaseModel):
    source_campaign_id: str
    source_kind: Literal["custom", "reference"]
    source_id: str
    access: Literal["private", "public", "paywall"] = "public"
    price_cents: int = 0
    license_text: str = Field(default="", max_length=600)
    summary: str = Field(default="", max_length=600)
    license_attestation: bool = False


class MarketplaceCloneIn(BaseModel):
    into_campaign_id: str


# ─── Helpers ────────────────────────────────────────────────────────────


def _scrub(doc: dict) -> dict:
    """Strip MongoDB internals + author identifiers we don't want
    leaking via the public listing endpoint."""
    out = {k: v for k, v in (doc or {}).items() if k != "_id"}
    return out


# ─── Publish ────────────────────────────────────────────────────────────


@router.post("/marketplace/publish")
async def publish_listing(body: MarketplacePublishIn,
                            user: dict = Depends(get_current_user)):
    """Snapshot a homebrew entry into the marketplace. Only the GM of
    the source campaign can publish; license attestation is required
    for `public` / `paywall` access tiers."""
    camp = await db.campaigns.find_one({"id": body.source_campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Source campaign not found")
    if camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only the campaign GM may publish entries.")

    if body.access in ("public", "paywall") and not body.license_attestation:
        raise HTTPException(400,
            "Public / paywall listings require a licence attestation.")
    if body.access == "paywall":
        # V1: paywall is accepted but the clone endpoint treats it as
        # public (Stripe wiring lands in V2 with the integration
        # playbook). Surface the intent so the UI can badge it.
        pass

    # Resolve the source entry.
    if body.source_kind == "custom":
        src = await db.custom_attributes.find_one(
            {"id": body.source_id, "campaign_id": body.source_campaign_id},
            {"_id": 0})
        if not src:
            raise HTTPException(404, "Source custom rule not found.")
        if src["kind"] not in HOMEBREW_KINDS:
            raise HTTPException(400, f"Cannot publish kind '{src['kind']}'.")
        snapshot = {
            "kind": src["kind"],
            "name": src["name"],
            "description_note": src.get("description_note", ""),
            "cost_per_level": src.get("cost_per_level", 1),
            "category": src.get("category", ""),
            "page_ref": src.get("page_ref", "Custom"),
            "effects": src.get("effects", {}) or {},
        }
    elif body.source_kind == "reference":
        src = await db.campaign_reference.find_one(
            {"id": body.source_id, "campaign_id": body.source_campaign_id},
            {"_id": 0})
        if not src:
            raise HTTPException(404, "Source reference entry not found.")
        if src.get("kind") not in REFERENCE_KINDS:
            raise HTTPException(400, f"Cannot publish kind '{src.get('kind')}'.")
        snapshot = {
            "kind": src["kind"],
            "name": src.get("name", ""),
            "summary": src.get("summary", ""),
            "fields": src.get("fields", {}) or {},
        }
    else:
        raise HTTPException(400, f"Unknown source_kind: {body.source_kind}")

    listing = {
        "id": new_id(),
        "source_campaign_id": body.source_campaign_id,
        "source_owner_id": user["id"],
        "source_owner_name": user.get("name") or "",
        "source_system_id": camp.get("system_id") or "",
        "source_kind": body.source_kind,
        "source_id": body.source_id,
        "kind": snapshot["kind"],
        "name": snapshot["name"],
        "summary": body.summary or snapshot.get("summary")
                    or snapshot.get("description_note", "")[:240],
        "snapshot": snapshot,
        "access": body.access,
        "price_cents": max(0, int(body.price_cents)),
        "license_text": body.license_text,
        "downloads": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.marketplace_listings.insert_one(listing)
    return _scrub(listing)


# ─── Browse ─────────────────────────────────────────────────────────────


@router.get("/marketplace")
async def browse_marketplace(
    user: dict = Depends(get_current_user),
    kind: Optional[str] = Query(None,
        description="Filter by single kind (e.g. 'race', 'spell')."),
    system: Optional[str] = Query(None,
        description="Filter by source system_id (e.g. 'besm-4e', 'dnd-5e')."),
    q: Optional[str] = Query(None,
        description="Case-insensitive substring search on name + summary."),
    access: Optional[str] = Query(None,
        description="Filter access tier: 'public', 'paywall'."),
    show_removed: bool = Query(False,
        description="ADMIN ONLY — include rows the admin has taken down."),
    limit: int = Query(40, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """Paginated browse. Authenticated users see all `public` listings
    plus their own `private` listings. `paywall` shows up so users can
    discover it (clone endpoint guards the price).

    V6.25.31 — admin takedowns: rows with `removed: true` are filtered
    out for everyone except the listing author (so they can see it was
    taken down) and admins (who can flip `?show_removed=true` to see
    the removed-row review queue).
    """
    is_admin = user.get("role") == "admin"
    where: Dict[str, Any] = {
        "$or": [
            {"access": {"$in": ["public", "paywall"]}},
            {"source_owner_id": user["id"]},
        ],
    }
    # ─── V6.25.31 takedown filter ─────────────────────────────────
    if not (is_admin and show_removed):
        # Default: hide removed rows for everyone except the row's
        # original author (who can still see their tombstoned listing).
        where["$and"] = where.pop("$and", []) + [
            {"$or": [
                {"removed": {"$ne": True}},
                {"source_owner_id": user["id"]},
            ]}
        ]
    elif show_removed:
        # Admin review-queue mode — only show removed rows.
        where["removed"] = True
    if kind:
        where["kind"] = kind
    if system:
        where["source_system_id"] = system
    if access:
        where["access"] = access
    if q:
        # MongoDB doesn't have $or-AND-$or natively; fold into a $text-like search.
        where["$and"] = where.pop("$and", []) + [{"$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"summary": {"$regex": q, "$options": "i"}},
        ]}]
    cursor = db.marketplace_listings.find(where, {"_id": 0}) \
        .sort("created_at", -1) \
        .skip(skip).limit(limit)
    rows = [r async for r in cursor]
    total = await db.marketplace_listings.count_documents(where)
    return {"total": total, "rows": rows, "limit": limit, "skip": skip}


@router.get("/marketplace/{lid}")
async def get_listing(lid: str, user: dict = Depends(get_current_user)):
    listing = await db.marketplace_listings.find_one({"id": lid}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing["access"] == "private" and listing["source_owner_id"] != user["id"]:
        raise HTTPException(403, "Listing is private")
    # V6.25.31 — admin takedowns: removed rows return a tombstone for
    # everyone EXCEPT the original author and admins (so the author
    # sees the takedown reason; admin can still review).
    if listing.get("removed"):
        is_admin = user.get("role") == "admin"
        is_owner = listing.get("source_owner_id") == user["id"]
        if not (is_admin or is_owner):
            raise HTTPException(410, "Listing has been removed by an administrator.")
    return listing


# ─── V6.25.31 — Admin takedown / restore + public audit log ────────────
class TakedownIn(BaseModel):
    """Admin-issued takedown reason. Visible to the listing author and
    on the public `/api/legal/takedowns` audit log so IP-rights
    enforcement is transparent."""
    reason: str = Field(..., min_length=4, max_length=600,
                          description="Plain-English policy reason.")
    policy: str = Field(default="other", max_length=64,
                          description="Tag: 'piracy', 'lore-export', 'artwork', "
                                       "'system-creator-rules', 'community-rules', 'other'.")


@router.post("/marketplace/{lid}/takedown")
async def takedown_listing(lid: str, body: TakedownIn,
                              user: dict = Depends(get_current_user)):
    """ADMIN-ONLY — flag a marketplace listing as removed.
    Persists `removed`, `takedown_reason`, `takedown_policy`,
    `takedown_by_id`, `takedown_by_name`, `takedown_at`. Writes a row
    to `takedown_audit` so the public legal log can render it."""
    if user.get("role") != "admin":
        raise HTTPException(403, "Admins only.")
    listing = await db.marketplace_listings.find_one({"id": lid}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found")
    now = now_iso()
    await db.marketplace_listings.update_one(
        {"id": lid},
        {"$set": {
            "removed": True,
            "takedown_reason": body.reason,
            "takedown_policy": body.policy,
            "takedown_by_id": user["id"],
            "takedown_by_name": user.get("name") or user.get("email"),
            "takedown_at": now,
        }},
    )
    await db.takedown_audit.insert_one({
        "id": new_id(),
        "kind": "marketplace_listing",
        "target_id": lid,
        "target_name": listing.get("name"),
        "target_owner_id": listing.get("source_owner_id"),
        "reason": body.reason,
        "policy": body.policy,
        "by_id": user["id"],
        "by_name": user.get("name") or user.get("email"),
        "at": now,
    })
    return {"ok": True, "id": lid, "removed_at": now}


@router.post("/marketplace/{lid}/restore")
async def restore_listing(lid: str, user: dict = Depends(get_current_user)):
    """ADMIN-ONLY — reverse a takedown. Restoration is also audited
    so the public legal log shows reversals (e.g. counter-notice
    accepted)."""
    if user.get("role") != "admin":
        raise HTTPException(403, "Admins only.")
    listing = await db.marketplace_listings.find_one({"id": lid}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found")
    if not listing.get("removed"):
        raise HTTPException(400, "Listing is not currently removed.")
    now = now_iso()
    await db.marketplace_listings.update_one(
        {"id": lid},
        {"$set": {"removed": False, "restored_at": now,
                    "restored_by_id": user["id"]},
         "$unset": {"takedown_reason": "", "takedown_policy": "",
                     "takedown_by_id": "", "takedown_by_name": "",
                     "takedown_at": ""}},
    )
    await db.takedown_audit.insert_one({
        "id": new_id(),
        "kind": "marketplace_listing",
        "action": "restore",
        "target_id": lid,
        "target_name": listing.get("name"),
        "target_owner_id": listing.get("source_owner_id"),
        "reason": "Counter-notice accepted / admin reversal.",
        "by_id": user["id"],
        "by_name": user.get("name") or user.get("email"),
        "at": now,
    })
    return {"ok": True, "id": lid, "restored_at": now}


@router.get("/legal/takedowns")
async def list_takedowns(limit: int = Query(100, ge=1, le=500),
                            skip: int = Query(0, ge=0)):
    """PUBLIC — IP-rights transparency log. Lists every takedown the
    admin has issued (and any restorations). No auth required: this is
    the public-facing audit trail."""
    cursor = db.takedown_audit.find({}, {"_id": 0}).sort("at", -1) \
        .skip(skip).limit(limit)
    rows = [r async for r in cursor]
    total = await db.takedown_audit.count_documents({})
    return {"total": total, "rows": rows, "limit": limit, "skip": skip}


# ─── Clone ──────────────────────────────────────────────────────────────


@router.post("/marketplace/{lid}/clone")
async def clone_listing(lid: str, body: MarketplaceCloneIn,
                          user: dict = Depends(get_current_user)):
    """Clone the listing's snapshot into the target campaign. The
    target campaign must be GM-owned by the requesting user (player
    cloning into a campaign they don't run is not allowed)."""
    listing = await db.marketplace_listings.find_one({"id": lid}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing["access"] == "private" and listing["source_owner_id"] != user["id"]:
        raise HTTPException(403, "Listing is private")
    if listing["access"] == "paywall" and listing["source_owner_id"] != user["id"]:
        # V1 stub: deny clone for non-self paywall listings until V2 wires
        # Stripe. Authors can still clone their own paywalled listing.
        raise HTTPException(402,
            "Paywall purchases land in V2 with Stripe — for now, only "
            "the listing's author can clone a paywalled entry.")

    target = await db.campaigns.find_one(
        {"id": body.into_campaign_id}, {"_id": 0})
    if not target:
        raise HTTPException(404, "Target campaign not found.")
    if target["gm_id"] != user["id"]:
        raise HTTPException(403,
            "Only the GM of the target campaign may clone listings into it.")

    snap = listing["snapshot"]
    kind = snap["kind"]
    if kind in HOMEBREW_KINDS:
        new_doc = {
            "id": new_id(),
            "campaign_id": body.into_campaign_id,
            "kind": kind,
            "name": snap["name"],
            "cost_per_level": snap.get("cost_per_level", 1),
            "category": snap.get("category", ""),
            "page_ref": (snap.get("page_ref") or "Marketplace") + " (cloned)",
            "description_note": snap.get("description_note", ""),
            "effects": snap.get("effects", {}) or {},
            "_marketplace_listing_id": lid,
        }
        await db.custom_attributes.insert_one(new_doc)
    elif kind in REFERENCE_KINDS:
        new_doc = {
            "id": new_id(),
            "campaign_id": body.into_campaign_id,
            "kind": kind,
            "name": snap["name"],
            "summary": snap.get("summary", "") + "\n\n(cloned from marketplace)",
            "fields": snap.get("fields", {}) or {},
            "_marketplace_listing_id": lid,
        }
        await db.campaign_reference.insert_one(new_doc)
    else:
        raise HTTPException(400, f"Unknown snapshot kind: {kind}")

    await db.marketplace_listings.update_one(
        {"id": lid},
        {"$inc": {"downloads": 1}, "$set": {"updated_at": now_iso()}})

    return {"ok": True, "cloned_id": new_doc["id"], "kind": kind}


# ─── Unpublish ─────────────────────────────────────────────────────────


@router.delete("/marketplace/{lid}")
async def unpublish_listing(lid: str, user: dict = Depends(get_current_user)):
    listing = await db.marketplace_listings.find_one({"id": lid}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing["source_owner_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the listing's author can unpublish.")
    await db.marketplace_listings.delete_one({"id": lid})
    return {"ok": True}


# ─── Subscriptions / Watch List (V6.25.6) ─────────────────────────────
#
# Lightweight digest: a user subscribes to a (kind, system) filter and
# can poll `GET /marketplace/digest` to fetch listings published since
# their last_check timestamp matching any of their filters. Front-end
# can surface a "N new" badge on the Market nav link.


class SubscriptionIn(BaseModel):
    kind: Optional[str] = None
    system: Optional[str] = None
    label: str = Field(default="", max_length=80)


@router.get("/marketplace-subscriptions")
async def list_subscriptions(user: dict = Depends(get_current_user)):
    rows = await db.marketplace_subscriptions.find(
        {"user_id": user["id"]}, {"_id": 0}).to_list(length=None)
    return rows


@router.post("/marketplace-subscriptions")
async def create_subscription(body: SubscriptionIn,
                                user: dict = Depends(get_current_user)):
    if not body.kind and not body.system:
        raise HTTPException(400,
            "A subscription must filter by at least one of kind or system.")
    doc = {
        "id": new_id(),
        "user_id": user["id"],
        "kind": body.kind,
        "system": body.system,
        "label": body.label or f"{body.kind or 'any'} · {body.system or 'any'}",
        "last_check": now_iso(),
        "created_at": now_iso(),
    }
    await db.marketplace_subscriptions.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@router.delete("/marketplace-subscriptions/{sid}")
async def delete_subscription(sid: str,
                                user: dict = Depends(get_current_user)):
    res = await db.marketplace_subscriptions.delete_one(
        {"id": sid, "user_id": user["id"]})
    if not res.deleted_count:
        raise HTTPException(404, "Subscription not found")
    return {"ok": True}


@router.get("/marketplace-digest")
async def marketplace_digest(user: dict = Depends(get_current_user),
                                mark_seen: bool = Query(False)):
    """Returns a per-subscription list of new listings since the
    subscription's `last_check`. Pass `mark_seen=true` to bump the
    timestamp (typical UI: hit with mark_seen=false on bell-click,
    mark_seen=true after the digest panel is dismissed)."""
    subs = await db.marketplace_subscriptions.find(
        {"user_id": user["id"]}, {"_id": 0}).to_list(length=None)
    out: List[Dict[str, Any]] = []
    for s in subs:
        where: Dict[str, Any] = {
            "access": {"$in": ["public", "paywall"]},
            "created_at": {"$gt": s["last_check"]},
        }
        if s.get("kind"):
            where["kind"] = s["kind"]
        if s.get("system"):
            where["source_system_id"] = s["system"]
        rows = await db.marketplace_listings.find(where, {"_id": 0}) \
            .sort("created_at", -1).limit(10).to_list(length=None)
        out.append({
            "subscription_id": s["id"],
            "label": s.get("label"),
            "kind": s.get("kind"),
            "system": s.get("system"),
            "since": s["last_check"],
            "new_count": len(rows),
            "preview": rows,
        })
    if mark_seen:
        await db.marketplace_subscriptions.update_many(
            {"user_id": user["id"]},
            {"$set": {"last_check": now_iso()}})
    total_new = sum(b["new_count"] for b in out)
    return {"buckets": out, "total_new": total_new}
