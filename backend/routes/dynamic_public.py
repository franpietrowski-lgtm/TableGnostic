"""V6.25.40 — Dynamic public surfaces + admin roadmap + flag threads.

Implements the "landing page reflects live app state" pipeline:

  Public (no auth):
    GET    /api/public/stats             — counters for the hero strip
    GET    /api/public/marketplace       — recent public listings
    GET    /api/public/roadmap           — admin-curated Now/Next/Later
    GET    /api/public/recent-gazettes   — last 3 pressed issues
    GET    /api/public/featured          — currently featured showcase

  Admin (role=admin):
    GET    /api/admin/roadmap            — list all items (incl. drafts)
    POST   /api/admin/roadmap            — create
    PATCH  /api/admin/roadmap/{rid}      — edit
    DELETE /api/admin/roadmap/{rid}      — delete
    GET    /api/admin/featured-requests  — GMs who requested featured slot
    POST   /api/admin/campaigns/{cid}/feature    — set featured=true
    DELETE /api/admin/campaigns/{cid}/feature    — clear featured

  GM (campaign owner):
    POST   /api/campaigns/{cid}/request-feature  — flip featured_requested

  Flags-as-threads (any user can post on a flag they filed; admin always):
    GET    /api/flags/{fid}              — read thread (filer or admin)
    POST   /api/flags/{fid}/messages     — append a message

All public surfaces strip private fields (player names, emails, gm_only
codex content, audit trail). Featured/roadmap content is admin-curated
so no PII leakage.
"""
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["dynamic"])


VALID_STATUSES = {"now", "next", "later", "shipped"}


# ── Models ────────────────────────────────────────────────────────
class RoadmapIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    body_md: str = Field(default="", max_length=2400)
    status: Literal["now", "next", "later", "shipped"] = "next"
    eta: Optional[str] = Field(default="", max_length=40)
    order: int = 0
    public: bool = True


class RoadmapPatch(BaseModel):
    title: Optional[str] = Field(default=None, max_length=160)
    body_md: Optional[str] = Field(default=None, max_length=2400)
    status: Optional[Literal["now", "next", "later", "shipped"]] = None
    eta: Optional[str] = Field(default=None, max_length=40)
    order: Optional[int] = None
    public: Optional[bool] = None


class FeatureRequestIn(BaseModel):
    requested: bool = True
    note: Optional[str] = Field(default="", max_length=400)


class FlagMessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


# ── Helpers ───────────────────────────────────────────────────────
def _require_admin(user: dict) -> None:
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin role required.")


# ── Public stats / marketplace / featured / gazettes ──────────────
@router.get("/public/stats")
async def public_stats():
    """Top-line counters for the landing page. Counts only public-safe
    aggregates — no PII, no per-user totals.

    V6.25.49 — deeper landing-page stats:
      * sessions_played    — total sessions ever opened (any status)
      * active_24h         — campaigns updated in the last 24 hours
      * gms_active         — distinct GMs whose campaigns updated in 7d
      * by_system          — per-system campaign counts (one row per
                              supported system_id)
      * latest_version     — the most-recent milestone tag (read from
                              /app/memory/PRD.md so it stays in sync
                              with the actual changelog, no manual
                              version-bumping in JSX).
      * pytest_passing     — `N / N` tests passing string (parsed from
                              the most-recent test report).
    """
    import os
    import re
    from datetime import datetime, timedelta, timezone

    campaign_count = await db.campaigns.count_documents({})
    public_count = await db.campaigns.count_documents({"discover_published": True})
    char_count = await db.characters.count_documents({})
    listing_count = await db.marketplace_listings.count_documents(
        {"$and": [{"$or": [{"taken_down": {"$ne": True}}, {"taken_down": {"$exists": False}}]},
                  {"$or": [{"visibility": "public"}, {"is_public": True}]}]}
    )
    gazette_count = await db.news_issues.count_documents({})
    node_count = await db.nodes.count_documents({})
    sessions_played = await db.sessions.count_documents({})

    # Activity windows.
    now = datetime.now(timezone.utc)
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    cutoff_7d = (now - timedelta(days=7)).isoformat()
    active_24h = await db.campaigns.count_documents({"updated_at": {"$gte": cutoff_24h}})
    gm_ids_7d = await db.campaigns.distinct("gm_id", {"updated_at": {"$gte": cutoff_7d}})
    gms_active = len([g for g in gm_ids_7d if g])

    # Per-system breakdown (aggregation pipeline). Limited to the
    # systems we actually advertise on /api/systems.
    by_system_rows = await db.campaigns.aggregate([
        {"$group": {"_id": "$system_id", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$in": ["besm-4e", "anime-5e", "dnd-5e", "cypher"]}}},
    ]).to_list(20)
    by_system = {r["_id"]: r["count"] for r in by_system_rows}

    # Latest milestone tag — first "### V" heading in PRD.md.
    latest_version = ""
    try:
        prd = open("/app/memory/PRD.md", encoding="utf-8").read()
        m = re.search(r"###\s+(V[\d.]+)", prd)
        if m:
            latest_version = m.group(1)
    except Exception:
        latest_version = ""

    # Cumulative pytest-pass total: look for the most-recent test
    # report JSON. Pull `success_rate.backend` if it parses as N/N.
    pytest_passing = ""
    try:
        reports_dir = "/app/test_reports"
        if os.path.isdir(reports_dir):
            files = [f for f in os.listdir(reports_dir) if f.startswith("iteration_") and f.endswith(".json")]
            files.sort(key=lambda f: int(re.search(r"(\d+)", f).group(1) or 0), reverse=True)
            if files:
                import json
                latest = json.load(open(os.path.join(reports_dir, files[0]), encoding="utf-8"))
                sr = latest.get("success_rate") or {}
                rate = sr.get("backend") or ""
                pm = re.search(r"\((\d+/\d+)\)", str(rate))
                if pm:
                    pytest_passing = pm.group(1)
    except Exception:
        pytest_passing = ""

    return {
        "campaigns": campaign_count,
        "public_campaigns": public_count,
        "characters": char_count,
        "marketplace_listings": listing_count,
        "gazettes_pressed": gazette_count,
        "codex_nodes": node_count,
        # V6.25.49 deeper stats:
        "sessions_played": sessions_played,
        "active_24h": active_24h,
        "gms_active": gms_active,
        "by_system": by_system,
        "latest_version": latest_version,
        "pytest_passing": pytest_passing,
    }


@router.get("/public/activity-pulse")
async def public_activity_pulse():
    """V6.25.49 — last-7-day timeseries for the landing-page sparkline.

    Returns one row per day for the past 7 calendar days (UTC), each
    with `campaigns_created`, `sessions_opened`, `characters_made`.
    Cheap aggregate — no PII surfaced.
    """
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    days = []
    for i in range(6, -1, -1):
        d_start = now - timedelta(days=i)
        d_end = d_start + timedelta(days=1)
        s, e = d_start.isoformat(), d_end.isoformat()
        camps = await db.campaigns.count_documents({"created_at": {"$gte": s, "$lt": e}})
        sess = await db.sessions.count_documents({"created_at": {"$gte": s, "$lt": e}})
        chars = await db.characters.count_documents({"created_at": {"$gte": s, "$lt": e}})
        days.append({
            "date": d_start.date().isoformat(),
            "campaigns_created": camps,
            "sessions_opened": sess,
            "characters_made": chars,
        })
    return {"days": days}


@router.get("/public/marketplace")
async def public_marketplace(limit: int = 12):
    """Recent public marketplace listings. Hides taken-down, private,
    and admin-only fields."""
    where = {
        "$and": [
            {"$or": [{"taken_down": {"$ne": True}}, {"taken_down": {"$exists": False}}]},
            {"$or": [{"visibility": "public"}, {"is_public": True}]},
        ]
    }
    rows = await db.marketplace_listings.find(
        where, {"_id": 0}
    ).sort("created_at", -1).limit(int(limit)).to_list(int(limit))
    # Strip private fields.
    out = []
    for r in rows:
        out.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "kind": r.get("kind"),
            "blurb": (r.get("blurb") or r.get("description") or "")[:300],
            "price": r.get("price", 0),
            "currency": r.get("currency", ""),
            "system_id": r.get("system_id"),
            "created_at": r.get("created_at"),
        })
    return {"items": out, "total": len(out)}


@router.get("/public/recent-gazettes")
async def public_recent_gazettes(limit: int = 6):
    """Most-recently-pressed issues across all `discover_published`
    campaigns. One row per issue with masthead + date + slug so the
    landing can deep-link readers into `/discover/{slug}/gazette`."""
    pubs = await db.campaigns.find(
        {"discover_published": True}, {"_id": 0, "id": 1, "name": 1, "discover_slug": 1}
    ).to_list(500)
    by_id = {c["id"]: c for c in pubs}
    if not by_id:
        return {"items": []}
    issues = await db.news_issues.find(
        {"campaign_id": {"$in": list(by_id.keys())}}, {"_id": 0}
    ).sort("published_at", -1).limit(int(limit)).to_list(int(limit))
    out = []
    for i in issues:
        c = by_id.get(i["campaign_id"]) or {}
        out.append({
            "issue_number": i.get("issue_number"),
            "masthead": i.get("masthead"),
            "date_label": i.get("date_label"),
            "published_at": i.get("published_at"),
            "campaign_name": c.get("name"),
            "campaign_slug": c.get("discover_slug"),
        })
    return {"items": out}


@router.get("/public/featured")
async def public_featured():
    """Admin-curated featured showcase. Falls back to the
    most-recently-published showcase if none has been featured yet so
    the landing always has something to surface."""
    c = await db.campaigns.find_one(
        {"featured": True, "discover_published": True}, {"_id": 0},
    )
    if not c:
        c = await db.campaigns.find_one(
            {"discover_published": True}, {"_id": 0},
            sort=[("featured_at", -1), ("created_at", -1)],
        )
    if not c:
        return {"item": None}
    return {"item": {
        "id": c.get("id"),
        "name": c.get("name"),
        "slug": c.get("discover_slug"),
        "system_id": c.get("system_id"),
        "blurb": c.get("canon_blurb", ""),
        "gm_name": c.get("gm_name"),
        "featured": bool(c.get("featured")),
        "featured_at": c.get("featured_at"),
    }}


# ── Public roadmap ────────────────────────────────────────────────
@router.get("/public/roadmap")
async def public_roadmap():
    rows = await db.roadmap_items.find(
        {"public": True}, {"_id": 0}
    ).sort([("status", 1), ("order", 1), ("created_at", -1)]).to_list(500)
    return {"items": rows}


# ── Admin: roadmap CRUD ───────────────────────────────────────────
@router.get("/admin/roadmap")
async def admin_list_roadmap(user: dict = Depends(get_current_user)):
    _require_admin(user)
    rows = await db.roadmap_items.find({}, {"_id": 0}).sort([
        ("status", 1), ("order", 1), ("created_at", -1)
    ]).to_list(500)
    return {"items": rows}


@router.post("/admin/roadmap")
async def admin_create_roadmap(body: RoadmapIn,
                                user: dict = Depends(get_current_user)):
    _require_admin(user)
    doc = {
        "id": new_id(),
        "title": body.title.strip(),
        "body_md": body.body_md,
        "status": body.status,
        "eta": (body.eta or "").strip(),
        "order": int(body.order),
        "public": bool(body.public),
        "created_at": now_iso(),
        "created_by": user["id"],
        "updated_at": now_iso(),
    }
    await db.roadmap_items.insert_one(doc)
    return sanitize(doc)


@router.patch("/admin/roadmap/{rid}")
async def admin_patch_roadmap(rid: str, body: RoadmapPatch,
                                user: dict = Depends(get_current_user)):
    _require_admin(user)
    cur = await db.roadmap_items.find_one({"id": rid}, {"_id": 0})
    if not cur:
        raise HTTPException(404, "Roadmap item not found.")
    update: dict = {"updated_at": now_iso()}
    for field in ("title", "body_md", "status", "eta", "order", "public"):
        v = getattr(body, field)
        if v is not None:
            update[field] = v.strip() if isinstance(v, str) else v
    if "status" in update and update["status"] not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")
    await db.roadmap_items.update_one({"id": rid}, {"$set": update})
    fresh = await db.roadmap_items.find_one({"id": rid}, {"_id": 0})
    return sanitize(fresh)


@router.delete("/admin/roadmap/{rid}")
async def admin_delete_roadmap(rid: str,
                                 user: dict = Depends(get_current_user)):
    _require_admin(user)
    r = await db.roadmap_items.delete_one({"id": rid})
    if r.deleted_count == 0:
        raise HTTPException(404, "Roadmap item not found.")
    return {"ok": True}


# ── Featured request / approve flow ──────────────────────────────
@router.post("/campaigns/{cid}/request-feature")
async def request_feature(cid: str, body: FeatureRequestIn,
                            user: dict = Depends(get_current_user)):
    """Campaign owner (or admin) flips `featured_requested=true` to
    enter the queue. Admin approves via the admin console."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    if user.get("role") != "admin" and user["id"] != camp.get("gm_id"):
        raise HTTPException(403, "Only the GM may request a featured slot.")
    if body.requested and not camp.get("discover_published"):
        raise HTTPException(400, "Publish the campaign to /discover before requesting a featured slot.")
    update = {
        "featured_requested": bool(body.requested),
        "featured_request_note": (body.note or "").strip(),
        "featured_requested_at": now_iso() if body.requested else None,
        "updated_at": now_iso(),
    }
    await db.campaigns.update_one({"id": cid}, {"$set": update})
    return {"ok": True, "requested": bool(body.requested)}


@router.get("/admin/featured-requests")
async def admin_featured_requests(user: dict = Depends(get_current_user)):
    _require_admin(user)
    rows = await db.campaigns.find(
        {"featured_requested": True, "featured": {"$ne": True}}, {"_id": 0}
    ).sort("featured_requested_at", -1).to_list(200)
    return {"items": rows}


@router.post("/admin/campaigns/{cid}/feature")
async def admin_feature(cid: str, user: dict = Depends(get_current_user)):
    _require_admin(user)
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    # Clear any previously-featured campaign to keep `featured=true`
    # singleton-ish (still allow batch by removing this if needed).
    await db.campaigns.update_many({"featured": True}, {"$set": {"featured": False}})
    await db.campaigns.update_one(
        {"id": cid},
        {"$set": {
            "featured": True, "featured_at": now_iso(),
            "featured_requested": False, "updated_at": now_iso(),
        }},
    )
    # Audit trail.
    try:
        await db.admin_actions.insert_one({
            "id": new_id(),
            "actor_id": user["id"],
            "actor_email": user.get("email"),
            "actor_role": user.get("role"),
            "action": "feature_campaign",
            "target_kind": "campaign",
            "target_id": cid,
            "reason": "Featured on landing page",
            "extras": {"name": camp.get("name")},
            "at": now_iso(),
        })
    except Exception:
        pass
    return {"ok": True, "featured": True}


@router.delete("/admin/campaigns/{cid}/feature")
async def admin_unfeature(cid: str, user: dict = Depends(get_current_user)):
    _require_admin(user)
    await db.campaigns.update_one(
        {"id": cid},
        {"$set": {"featured": False, "updated_at": now_iso()}},
    )
    return {"ok": True, "featured": False}


# ── Flag thread (filer + admin) ───────────────────────────────────
@router.get("/flags/{fid}")
async def read_flag_thread(fid: str, user: dict = Depends(get_current_user)):
    flag = await db.flags.find_one({"id": fid}, {"_id": 0})
    if not flag:
        raise HTTPException(404, "Flag not found.")
    if user.get("role") != "admin" and user["id"] != flag.get("filed_by_id"):
        raise HTTPException(403, "Only the filer or an admin may view this thread.")
    msgs = await db.flag_messages.find(
        {"flag_id": fid}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    return {"flag": flag, "messages": msgs}


@router.post("/flags/{fid}/messages")
async def post_flag_message(fid: str, body: FlagMessageIn,
                              user: dict = Depends(get_current_user)):
    flag = await db.flags.find_one({"id": fid}, {"_id": 0, "filed_by_id": 1, "status": 1})
    if not flag:
        raise HTTPException(404, "Flag not found.")
    is_admin = user.get("role") == "admin"
    if not is_admin and user["id"] != flag.get("filed_by_id"):
        raise HTTPException(403, "Only the filer or an admin may post to this thread.")
    msg = {
        "id": new_id(),
        "flag_id": fid,
        "author_id": user["id"],
        "author_name": user.get("name"),
        "author_role": "admin" if is_admin else "user",
        "body": body.body.strip(),
        "created_at": now_iso(),
    }
    await db.flag_messages.insert_one(msg)
    return sanitize(msg)
