"""V6.25.41 — Player → GM approval queue for character + inventory diffs.

User asked: "Players submit to GM queue only for character/inventory
changes." Implements **strict permission gating** — when a player edits
their own character on a campaign with `gm_approval_required=true`, the
PATCH is intercepted, captured as a `change_requests` doc with the
before/after diff, and held until the GM approves or rejects. Admin and
GM are bypass-tier (their direct PATCHes write through immediately).

Routes:
    POST   /api/campaigns/{cid}/change-requests             — player submits a diff
    GET    /api/campaigns/{cid}/change-requests             — list queue (GM/admin/owner)
    POST   /api/campaigns/{cid}/change-requests/{rid}/approve  — apply diff (GM/admin)
    POST   /api/campaigns/{cid}/change-requests/{rid}/reject   — drop diff + reason
    POST   /api/campaigns/{cid}/change-requests/{rid}/cancel   — player withdraws

    PATCH  /api/campaigns/{cid}/settings/approval           — GM toggles the gate

Approval gate model: per-campaign opt-in (`Campaign.gm_approval_required`).
Off by default so existing campaigns keep current direct-edit behaviour.

The actual *interception* of player PATCH calls is handled by the
existing character + inventory routes — they call
`enforce_or_queue(...)` from this module which returns either
"apply-direct" or raises HTTPException(202, body=change_request).
"""
from typing import Optional, Literal, Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user


router = APIRouter(prefix="/api", tags=["change-requests"])


# ── Models ────────────────────────────────────────────────────────
class ChangeRequestIn(BaseModel):
    kind: Literal["character", "inventory"] = "character"
    target_id: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=2, max_length=400)
    diff: Dict[str, Any] = Field(default_factory=dict)
    proposed_value: Optional[Dict[str, Any]] = None


class ApprovalSettings(BaseModel):
    gm_approval_required: bool


class RejectIn(BaseModel):
    reason: str = Field(default="", max_length=600)


# ── Helpers ───────────────────────────────────────────────────────
async def _campaign_or_404(cid: str) -> dict:
    c = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Campaign not found.")
    return c


def _is_gm(camp: dict, user: dict) -> bool:
    return user.get("role") == "admin" or user["id"] == camp.get("gm_id")


def _is_seated(camp: dict, user: dict) -> bool:
    if user.get("role") == "admin":
        return True
    return (
        user["id"] == camp.get("gm_id")
        or user["id"] in (camp.get("member_ids") or [])
    )


# ── Settings ──────────────────────────────────────────────────────
@router.patch("/campaigns/{cid}/settings/approval")
async def patch_approval(cid: str, body: ApprovalSettings,
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may toggle approval gating.")
    await db.campaigns.update_one(
        {"id": cid},
        {"$set": {"gm_approval_required": bool(body.gm_approval_required),
                  "updated_at": now_iso()}},
    )
    return {"ok": True, "gm_approval_required": bool(body.gm_approval_required)}


# ── Player submits a diff ─────────────────────────────────────────
@router.post("/campaigns/{cid}/change-requests")
async def submit_change_request(cid: str, body: ChangeRequestIn,
                                  user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    # Validate the target belongs to this campaign + this player.
    if body.kind == "character":
        ch = await db.characters.find_one(
            {"id": body.target_id, "campaign_id": cid}, {"_id": 0, "owner_id": 1},
        )
        if not ch:
            raise HTTPException(404, "Character not found.")
        # Owner-or-GM submits.
        if not _is_gm(camp, user) and user["id"] != ch.get("owner_id"):
            raise HTTPException(403, "Only the character owner or GM may submit a change request.")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "kind": body.kind,
        "target_id": body.target_id,
        "summary": body.summary.strip(),
        "diff": body.diff,
        "proposed_value": body.proposed_value,
        "status": "pending",
        "submitted_by_id": user["id"],
        "submitted_by_name": user.get("name"),
        "submitted_at": now_iso(),
        "reviewed_by_id": None,
        "reviewed_at": None,
        "review_reason": "",
    }
    await db.change_requests.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{cid}/change-requests")
async def list_change_requests(cid: str, status: str = "pending",
                                 user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    where: dict = {"campaign_id": cid}
    if status != "all":
        where["status"] = status
    # Players only see their own; GM/admin see all.
    if not _is_gm(camp, user):
        where["submitted_by_id"] = user["id"]
    rows = await db.change_requests.find(where, {"_id": 0}).sort("submitted_at", -1).to_list(200)
    return {"items": rows, "total": len(rows)}


@router.post("/campaigns/{cid}/change-requests/{rid}/approve")
async def approve_change_request(cid: str, rid: str,
                                   user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may approve change requests.")
    req = await db.change_requests.find_one(
        {"id": rid, "campaign_id": cid}, {"_id": 0},
    )
    if not req:
        raise HTTPException(404, "Change request not found.")
    if req["status"] != "pending":
        raise HTTPException(409, f"Change request already {req['status']}.")
    applied: dict = {"approved": True}
    # Apply the diff.
    if req["kind"] == "character" and isinstance(req.get("proposed_value"), dict):
        # Whitelist fields a player may submit — never accept role / owner / system
        # overrides via the queue.
        FORBIDDEN = {"id", "campaign_id", "owner_id", "owner_name", "system_id",
                      "role", "created_at", "_id"}
        clean = {k: v for k, v in req["proposed_value"].items() if k not in FORBIDDEN}
        if clean:
            clean["updated_at"] = now_iso()
            r = await db.characters.update_one(
                {"id": req["target_id"], "campaign_id": cid},
                {"$set": clean},
            )
            applied["matched"] = r.matched_count
            applied["modified"] = r.modified_count
    elif req["kind"] == "inventory" and isinstance(req.get("proposed_value"), dict):
        # V6.25.41 — Inventory diffs are stamped on `characters.folio.inventory_state`.
        # The proposed_value already carries the merged folio dict (the
        # folio PATCH route packages it that way), so we just write it
        # through with a guard against forbidden fields.
        clean = {k: v for k, v in req["proposed_value"].items()
                 if k not in {"_id", "id", "owner_id", "campaign_id", "system_id"}}
        clean["updated_at"] = now_iso()
        r = await db.characters.update_one(
            {"id": req["target_id"]},
            {"$set": clean},
        )
        applied["matched"] = r.matched_count
        applied["modified"] = r.modified_count
    await db.change_requests.update_one(
        {"id": rid, "campaign_id": cid},
        {"$set": {
            "status": "approved",
            "reviewed_by_id": user["id"],
            "reviewed_at": now_iso(),
            "applied_result": applied,
        }},
    )
    fresh = await db.change_requests.find_one({"id": rid, "campaign_id": cid}, {"_id": 0})
    return sanitize(fresh)


@router.post("/campaigns/{cid}/change-requests/{rid}/reject")
async def reject_change_request(cid: str, rid: str, body: RejectIn,
                                  user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may reject change requests.")
    req = await db.change_requests.find_one(
        {"id": rid, "campaign_id": cid}, {"_id": 0},
    )
    if not req:
        raise HTTPException(404, "Change request not found.")
    if req["status"] != "pending":
        raise HTTPException(409, f"Change request already {req['status']}.")
    await db.change_requests.update_one(
        {"id": rid, "campaign_id": cid},
        {"$set": {
            "status": "rejected",
            "reviewed_by_id": user["id"],
            "reviewed_at": now_iso(),
            "review_reason": body.reason.strip(),
        }},
    )
    fresh = await db.change_requests.find_one({"id": rid, "campaign_id": cid}, {"_id": 0})
    return sanitize(fresh)


@router.post("/campaigns/{cid}/change-requests/{rid}/cancel")
async def cancel_change_request(cid: str, rid: str,
                                  user: dict = Depends(get_current_user)):
    """Filer (or admin) withdraws their own pending request."""
    req = await db.change_requests.find_one(
        {"id": rid, "campaign_id": cid}, {"_id": 0},
    )
    if not req:
        raise HTTPException(404, "Change request not found.")
    if user.get("role") != "admin" and user["id"] != req.get("submitted_by_id"):
        raise HTTPException(403, "Only the filer may cancel their own request.")
    if req["status"] != "pending":
        raise HTTPException(409, f"Change request already {req['status']}.")
    await db.change_requests.update_one(
        {"id": rid, "campaign_id": cid},
        {"$set": {"status": "cancelled", "reviewed_at": now_iso(),
                  "reviewed_by_id": user["id"]}},
    )
    return {"ok": True, "status": "cancelled"}


# ── Enforcement helper (called from character/inventory write routes) ──
async def enforce_or_queue(camp: dict, user: dict, kind: str, target_id: str,
                            proposed_value: Dict[str, Any],
                            summary: str = "") -> Optional[dict]:
    """Returns None if the caller should proceed with the direct write
    (admin, GM, or campaign hasn't enabled approval). Returns a
    `change_requests` document (and inserts it) if the call should be
    queued instead. Character/inventory write routes should call this
    early and, when given a doc, return it to the client with HTTP 202.
    """
    if not camp.get("gm_approval_required"):
        return None
    if user.get("role") == "admin" or user["id"] == camp.get("gm_id"):
        return None
    doc = {
        "id": new_id(),
        "campaign_id": camp["id"],
        "kind": kind,
        "target_id": target_id,
        "summary": (summary or f"{kind} diff").strip()[:400],
        "diff": {},
        "proposed_value": proposed_value,
        "status": "pending",
        "submitted_by_id": user["id"],
        "submitted_by_name": user.get("name"),
        "submitted_at": now_iso(),
        "reviewed_by_id": None,
        "reviewed_at": None,
        "review_reason": "",
        "auto_queued": True,
    }
    await db.change_requests.insert_one(doc)
    return sanitize(doc)
