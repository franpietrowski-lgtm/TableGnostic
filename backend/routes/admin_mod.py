"""Admin Moderation Console — V6.25.39.

Admin-only moderation surface. The super-admin
(`tablegnostic-admin@tablegnostic.com`) can:

  * List every campaign in the system.
  * Force-unpublish a campaign from `/discover` and `/discover/browse`.
  * Take-down (hide) a marketplace listing.
  * Review the **flag queue** — content reported by users. Flags do NOT
    auto-hide content (per user pref ii): they enter a review queue, and
    only admin action removes the content. Status flows
    open → dismissed | actioned.
  * Audit trail — every moderation action is recorded in
    `admin_actions` with actor, target, reason, timestamp.

Read endpoints are admin-only. Write endpoints are admin-only.

Routes:
    GET    /api/admin/campaigns                            — list ALL
    GET    /api/admin/showcases                            — discover_published=true
    GET    /api/admin/marketplace                          — all listings
    GET    /api/admin/users                                — minimal user list
    GET    /api/admin/audit                                — paginated audit log

    POST   /api/admin/campaigns/{cid}/force-unpublish      — flip discover_published=false
    POST   /api/admin/marketplace/{lid}/take-down          — set takedown
    POST   /api/admin/marketplace/{lid}/reinstate          — unset takedown
    DELETE /api/admin/campaigns/{cid}                      — force-delete a campaign

    POST   /api/flags                                      — ANY auth user files a flag
    GET    /api/admin/flags                                — admin: list flag queue
    PATCH  /api/admin/flags/{fid}                          — admin: review (dismiss/action)
"""
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["admin"])


# ── Models ─────────────────────────────────────────────────────────
class FlagIn(BaseModel):
    target_kind: Literal["campaign", "character", "listing", "node",
                          "showcase", "article", "user"]
    target_id: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=3, max_length=600)


class FlagReview(BaseModel):
    status: Literal["dismissed", "actioned"]
    notes: Optional[str] = Field(default="", max_length=1000)


class ModerationActionIn(BaseModel):
    reason: Optional[str] = Field(default="", max_length=600)


# ── Helpers ───────────────────────────────────────────────────────
def _require_admin(user: dict) -> None:
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin role required.")


async def _audit(user: dict, action: str, target_kind: str, target_id: str,
                  reason: str = "", extras: Optional[dict] = None) -> None:
    """Append a row to `admin_actions`. Never raises — audit must never
    block the moderation action itself."""
    try:
        await db.admin_actions.insert_one({
            "id": new_id(),
            "actor_id": user["id"],
            "actor_email": user.get("email"),
            "actor_role": user.get("role"),
            "action": action,
            "target_kind": target_kind,
            "target_id": target_id,
            "reason": (reason or "").strip(),
            "extras": extras or {},
            "at": now_iso(),
        })
    except Exception as e:
        print(f"[admin._audit:warn] failed to log {action} {target_kind} {target_id}: {e}")


# ── List endpoints (admin) ────────────────────────────────────────
@router.get("/admin/campaigns")
async def list_all_campaigns(limit: int = 200, skip: int = 0,
                              user: dict = Depends(get_current_user)):
    _require_admin(user)
    cur = db.campaigns.find({}, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(int(limit))
    rows = await cur.to_list(int(limit))
    total = await db.campaigns.count_documents({})
    return {"items": rows, "total": total, "limit": limit, "skip": skip}


@router.get("/admin/showcases")
async def list_published_showcases(user: dict = Depends(get_current_user)):
    _require_admin(user)
    rows = await db.campaigns.find(
        {"discover_published": True}, {"_id": 0}
    ).to_list(500)
    return {"items": rows, "total": len(rows)}


@router.get("/admin/marketplace")
async def list_all_marketplace(user: dict = Depends(get_current_user)):
    _require_admin(user)
    rows = await db.marketplace_listings.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"items": rows, "total": len(rows)}


@router.get("/admin/users")
async def list_all_users(limit: int = 500, skip: int = 0, q: str = "",
                         user: dict = Depends(get_current_user)):
    _require_admin(user)
    where: dict = {}
    if q.strip():
        # Simple OR over email + name (case-insensitive).
        rx = {"$regex": q.strip(), "$options": "i"}
        where = {"$or": [{"email": rx}, {"name": rx}]}
    # Admins first (so the super-admin is always visible at the top
    # regardless of how many test users have accumulated), then most
    # recent.
    rows = await db.users.find(
        where, {"_id": 0, "id": 1, "email": 1, "name": 1, "role": 1, "created_at": 1},
    ).sort([("role", -1), ("created_at", -1)]).skip(int(skip)).limit(int(limit)).to_list(int(limit))
    total = await db.users.count_documents(where)
    return {"items": rows, "total": total, "limit": limit, "skip": skip}


@router.get("/admin/audit")
async def list_audit_log(limit: int = 100, skip: int = 0,
                          user: dict = Depends(get_current_user)):
    _require_admin(user)
    rows = await db.admin_actions.find({}, {"_id": 0}).sort("at", -1).skip(int(skip)).limit(int(limit)).to_list(int(limit))
    total = await db.admin_actions.count_documents({})
    return {"items": rows, "total": total, "limit": limit, "skip": skip}


# ── Moderation actions (admin) ────────────────────────────────────
@router.post("/admin/campaigns/{cid}/force-unpublish")
async def force_unpublish_campaign(cid: str, body: ModerationActionIn,
                                     user: dict = Depends(get_current_user)):
    _require_admin(user)
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    await db.campaigns.update_one(
        {"id": cid},
        {"$set": {"discover_published": False, "updated_at": now_iso()}},
    )
    await _audit(user, "force_unpublish", "campaign", cid, body.reason,
                  extras={"name": camp.get("name"), "slug": camp.get("discover_slug")})
    return {"ok": True, "published": False}


@router.delete("/admin/campaigns/{cid}")
async def force_delete_campaign(cid: str, reason: str = "",
                                  user: dict = Depends(get_current_user)):
    _require_admin(user)
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    # Wipe associated data too — codex nodes, sessions, characters,
    # marketplace listings sourced from this campaign — so we don't leave
    # orphaned records.
    await db.campaigns.delete_one({"id": cid})
    deleted = {"campaign": 1}
    for (col, key) in [
        ("characters", "campaign_id"),
        ("nodes", "campaign_id"),
        ("sessions", "campaign_id"),
        ("chat_logs", "campaign_id"),
        ("voice_lines", "campaign_id"),
        ("news_articles", "campaign_id"),
        ("news_issues", "campaign_id"),
        ("news_kills", "campaign_id"),
    ]:
        r = await db[col].delete_many({key: cid})
        deleted[col] = r.deleted_count
    await _audit(user, "force_delete", "campaign", cid, reason,
                  extras={"name": camp.get("name"), "deleted": deleted})
    return {"ok": True, "deleted": deleted}


@router.post("/admin/marketplace/{lid}/take-down")
async def take_down_listing(lid: str, body: ModerationActionIn,
                              user: dict = Depends(get_current_user)):
    _require_admin(user)
    listing = await db.marketplace_listings.find_one({"id": lid}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found.")
    await db.marketplace_listings.update_one(
        {"id": lid},
        {"$set": {"taken_down": True, "taken_down_reason": body.reason,
                  "taken_down_at": now_iso(), "updated_at": now_iso()}},
    )
    await _audit(user, "take_down", "listing", lid, body.reason,
                  extras={"title": listing.get("title")})
    return {"ok": True, "taken_down": True}


@router.post("/admin/marketplace/{lid}/reinstate")
async def reinstate_listing(lid: str, body: ModerationActionIn,
                              user: dict = Depends(get_current_user)):
    _require_admin(user)
    listing = await db.marketplace_listings.find_one({"id": lid}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found.")
    await db.marketplace_listings.update_one(
        {"id": lid},
        {"$set": {"taken_down": False, "taken_down_reason": "",
                  "updated_at": now_iso()}, "$unset": {"taken_down_at": ""}},
    )
    await _audit(user, "reinstate", "listing", lid, body.reason,
                  extras={"title": listing.get("title")})
    return {"ok": True, "taken_down": False}


# ── Flags (any auth user can file; admin reviews) ─────────────────
@router.post("/flags")
async def file_flag(body: FlagIn, user: dict = Depends(get_current_user)):
    """Any authenticated user can file a flag against any content.
    Flags do NOT auto-hide content — admin reviews and chooses to
    dismiss or action (per user-stated pref: stay visible until admin
    acts)."""
    doc = {
        "id": new_id(),
        "target_kind": body.target_kind,
        "target_id": body.target_id,
        "reason": body.reason.strip(),
        "filed_by_id": user["id"],
        "filed_by_name": user.get("name"),
        "status": "open",
        "filed_at": now_iso(),
        "reviewed_at": None,
        "reviewed_by_id": None,
        "review_notes": "",
    }
    await db.flags.insert_one(doc)
    return sanitize(doc)


@router.get("/admin/flags")
async def list_flags(status: str = "open",
                     user: dict = Depends(get_current_user)):
    _require_admin(user)
    where: dict = {} if status == "all" else {"status": status}
    rows = await db.flags.find(where, {"_id": 0}).sort("filed_at", -1).to_list(500)
    return {"items": rows, "total": len(rows)}


@router.patch("/admin/flags/{fid}")
async def review_flag(fid: str, body: FlagReview,
                       user: dict = Depends(get_current_user)):
    _require_admin(user)
    flag = await db.flags.find_one({"id": fid}, {"_id": 0})
    if not flag:
        raise HTTPException(404, "Flag not found.")
    await db.flags.update_one(
        {"id": fid},
        {"$set": {
            "status": body.status,
            "reviewed_at": now_iso(),
            "reviewed_by_id": user["id"],
            "review_notes": body.notes or "",
        }},
    )
    await _audit(user, f"flag_{body.status}", flag["target_kind"], flag["target_id"],
                  body.notes or "", extras={"flag_id": fid})
    fresh = await db.flags.find_one({"id": fid}, {"_id": 0})
    return sanitize(fresh)
