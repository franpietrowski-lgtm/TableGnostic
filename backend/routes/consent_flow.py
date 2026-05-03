"""V6.21 — GM / Player consent flow + seat applications.

Adds three capabilities on top of the existing invite-token system:

1. **Consent record** (`db.campaign_consents`) — a player acknowledges
   the primer, house rules, and any safety/content tags before their
   seat becomes active. The GM can require consent via the campaign's
   `consent_required` flag. Without a current consent record the
   player's character sheet locks into read-only.

2. **Seat application** (`db.seat_applications`) — a player on a
   public campaign listing can apply with a character-pitch note; the
   GM sees a queue on the Invite tab and approves or rejects without
   sharing the raw invite token.

3. **Leave seat** — a player can leave a campaign they no longer play
   in. The GM keeps the character but the seat frees up.

All endpoints are prefixed with `/api`.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

from core.security import get_current_user
from core.db import db, now_iso


router = APIRouter(prefix="/api", tags=["consent"])


# ─── Consent records ──────────────────────────────────────────────────

class ConsentIn(BaseModel):
    primer_acknowledged: bool = True
    house_rules_acknowledged: bool = True
    safety_tags_acknowledged: bool = True
    note: str = ""


class ConsentOut(BaseModel):
    id: str
    campaign_id: str
    user_id: str
    user_name: str
    primer_acknowledged: bool
    house_rules_acknowledged: bool
    safety_tags_acknowledged: bool
    primer_hash: str
    note: str
    agreed_at: str


def _primer_snapshot_hash(camp: dict) -> str:
    """A simple snapshot hash of primer + house-rules text so we can
    tell whether the consent record is still current against the
    campaign's active primer. Changes invalidate consent."""
    import hashlib
    txt = "|".join([
        camp.get("player_primer") or "",
        camp.get("house_rules") or "",
        camp.get("setting_name") or "",
    ])
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]


@router.get("/campaigns/{cid}/consent")
async def get_consent(cid: str, user: dict = Depends(get_current_user)):
    """Return the caller's consent record + campaign consent requirements."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp.get("visibility", "private") != "public" \
       and user["id"] != camp["gm_id"] \
       and user["id"] not in camp.get("member_ids", []):
        raise HTTPException(403, "Not permitted")
    rec = await db.campaign_consents.find_one(
        {"campaign_id": cid, "user_id": user["id"]}, {"_id": 0})
    current_hash = _primer_snapshot_hash(camp)
    return {
        "campaign_id": cid,
        "consent_required": bool(camp.get("consent_required", False)),
        "current_primer_hash": current_hash,
        "consent": rec,
        "up_to_date": bool(rec) and rec.get("primer_hash") == current_hash,
    }


@router.post("/campaigns/{cid}/consent")
async def record_consent(cid: str, body: ConsentIn,
                          user: dict = Depends(get_current_user)):
    """Record a fresh consent from the caller against the current primer."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] not in camp.get("member_ids", []) \
       and user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Not a member of this campaign")
    rec_id = str(uuid.uuid4())
    rec = {
        "id": rec_id,
        "campaign_id": cid,
        "user_id": user["id"],
        "user_name": user.get("name") or user.get("email"),
        "primer_acknowledged": body.primer_acknowledged,
        "house_rules_acknowledged": body.house_rules_acknowledged,
        "safety_tags_acknowledged": body.safety_tags_acknowledged,
        "primer_hash": _primer_snapshot_hash(camp),
        "note": body.note,
        "agreed_at": now_iso(),
    }
    # Upsert — one consent record per (campaign, user).
    await db.campaign_consents.update_one(
        {"campaign_id": cid, "user_id": user["id"]},
        {"$set": rec}, upsert=True,
    )
    return {"ok": True, "consent": rec}


@router.delete("/campaigns/{cid}/consent")
async def withdraw_consent(cid: str, user: dict = Depends(get_current_user)):
    """Withdraw a previous consent. The sheet snaps read-only until the
    player re-consents or leaves."""
    r = await db.campaign_consents.delete_one(
        {"campaign_id": cid, "user_id": user["id"]})
    return {"ok": True, "deleted": r.deleted_count}


@router.get("/campaigns/{cid}/consent-roll")
async def consent_roll(cid: str, user: dict = Depends(get_current_user)):
    """GM-only — list every member's consent status for the Invite tab."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM only")
    current_hash = _primer_snapshot_hash(camp)
    consents = await db.campaign_consents.find(
        {"campaign_id": cid}, {"_id": 0}).to_list(200)
    members = await db.users.find(
        {"id": {"$in": camp.get("member_ids", [])}},
        {"_id": 0, "password_hash": 0},
    ).to_list(200)
    by_user = {c["user_id"]: c for c in consents}
    rows = []
    for m in members:
        c = by_user.get(m["id"])
        rows.append({
            "user_id": m["id"],
            "user_name": m.get("name") or m.get("email"),
            "has_consent": bool(c),
            "up_to_date": bool(c) and c.get("primer_hash") == current_hash,
            "agreed_at": (c or {}).get("agreed_at"),
        })
    return {
        "campaign_id": cid,
        "consent_required": bool(camp.get("consent_required", False)),
        "rows": rows,
        "current_primer_hash": current_hash,
    }


# ─── Seat applications ────────────────────────────────────────────────

class SeatApplicationIn(BaseModel):
    character_pitch: str = ""
    preferred_system_familiarity: str = ""  # "new" / "some" / "expert"
    note: str = ""


@router.get("/campaigns/{cid}/seat-applications")
async def list_seat_applications(cid: str,
                                  user: dict = Depends(get_current_user)):
    """GM-only list of pending / resolved seat applications."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM only")
    apps = await db.seat_applications.find(
        {"campaign_id": cid}, {"_id": 0}
    ).sort("applied_at", 1).to_list(200)
    return {"applications": apps}


@router.post("/campaigns/{cid}/seat-applications")
async def apply_for_seat(cid: str, body: SeatApplicationIn,
                          user: dict = Depends(get_current_user)):
    """Player applies for a seat on a public-visibility campaign."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp.get("visibility", "private") != "public":
        raise HTTPException(400, "This campaign is not publicly listed")
    if user["id"] == camp["gm_id"]:
        raise HTTPException(400, "You are the GM")
    if user["id"] in camp.get("member_ids", []):
        raise HTTPException(400, "You are already seated")
    existing = await db.seat_applications.find_one(
        {"campaign_id": cid, "user_id": user["id"], "status": "pending"},
        {"_id": 0})
    if existing:
        return {"ok": True, "application": existing, "already_pending": True}
    if len(camp.get("member_ids", [])) >= camp.get("max_players", 6):
        raise HTTPException(400, "Table full")
    aid = str(uuid.uuid4())
    app_doc = {
        "id": aid,
        "campaign_id": cid,
        "user_id": user["id"],
        "user_name": user.get("name") or user.get("email"),
        "character_pitch": body.character_pitch,
        "preferred_system_familiarity": body.preferred_system_familiarity,
        "note": body.note,
        "status": "pending",
        "applied_at": now_iso(),
        "resolved_at": None,
        "resolved_by": None,
        "gm_note": "",
    }
    await db.seat_applications.insert_one(dict(app_doc))
    return {"ok": True, "application": app_doc}


class SeatDecisionIn(BaseModel):
    gm_note: str = ""


@router.post("/campaigns/{cid}/seat-applications/{aid}/approve")
async def approve_seat_application(cid: str, aid: str, body: SeatDecisionIn,
                                     user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM only")
    app = await db.seat_applications.find_one({"id": aid, "campaign_id": cid},
                                                {"_id": 0})
    if not app:
        raise HTTPException(404, "Application not found")
    if len(camp.get("member_ids", [])) >= camp.get("max_players", 6):
        raise HTTPException(400, "Table is full — free a seat first")
    # Seat the player.
    await db.campaigns.update_one(
        {"id": cid},
        {"$addToSet": {"member_ids": app["user_id"]}},
    )
    await db.seat_applications.update_one(
        {"id": aid},
        {"$set": {"status": "approved", "gm_note": body.gm_note,
                   "resolved_at": now_iso(), "resolved_by": user["id"]}},
    )
    return {"ok": True, "seated_user_id": app["user_id"]}


@router.post("/campaigns/{cid}/seat-applications/{aid}/reject")
async def reject_seat_application(cid: str, aid: str, body: SeatDecisionIn,
                                    user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM only")
    r = await db.seat_applications.update_one(
        {"id": aid, "campaign_id": cid},
        {"$set": {"status": "rejected", "gm_note": body.gm_note,
                   "resolved_at": now_iso(), "resolved_by": user["id"]}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "Application not found")
    return {"ok": True}


@router.post("/campaigns/{cid}/leave")
async def leave_campaign(cid: str, user: dict = Depends(get_current_user)):
    """Player leaves a campaign seat. Characters remain with their
    owner (they can be reassigned by the GM)."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] == camp["gm_id"]:
        raise HTTPException(400, "GMs cannot leave their own campaign")
    if user["id"] not in camp.get("member_ids", []):
        raise HTTPException(400, "You are not seated here")
    await db.campaigns.update_one(
        {"id": cid},
        {"$pull": {"member_ids": user["id"]}},
    )
    # Clear the player's active consent record.
    await db.campaign_consents.delete_many(
        {"campaign_id": cid, "user_id": user["id"]})
    return {"ok": True}
