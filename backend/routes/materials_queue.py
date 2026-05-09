"""V6.25.12 — Player materials intake → GM approval queue.

Players can record material / byproduct / craft-output sightings inside
their character journals. These do NOT directly mutate the codex —
instead they enqueue a per-campaign approval ticket (GM-only). On
approval, the entry is committed as a codex node with the appropriate
`node_kind`. On rejection, the player is notified and the journal entry
is preserved (still readable in their journal but flagged 'rejected').

The flow respects the V6.25.11 permission rule: players cannot
directly add to codex / genesis / epic; they submit, GM reviews.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from core.db import db, new_id
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["materials_queue"])

ALLOWED_KINDS = {"material", "byproduct", "craft_output"}


class MaterialIntakeIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    node_kind: str = Field(min_length=1, max_length=24)
    summary: Optional[str] = Field(default="", max_length=2000)
    tags: List[str] = []
    rarity: Optional[str] = Field(default=None, max_length=24)


@router.post("/campaigns/{cid}/materials-queue")
async def submit_material_intake(
    cid: str, body: MaterialIntakeIn,
    user: dict = Depends(get_current_user),
):
    """Player-facing submission endpoint. Anyone on the campaign roster
    may submit. The GM resolves via the approval routes below."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")

    # Confirm the user is actually on this campaign (player or GM).
    on_roster = (
        user["id"] == camp.get("gm_id")
        or user["id"] in (camp.get("member_ids") or [])
    )
    if not on_roster:
        raise HTTPException(403, "Not a member of this campaign.")

    if body.node_kind not in ALLOWED_KINDS:
        raise HTTPException(
            422, f"node_kind must be one of {sorted(ALLOWED_KINDS)}")

    ticket = {
        "id": new_id(),
        "campaign_id": cid,
        "submitter_id": user["id"],
        "submitter_name": user.get("name") or user.get("email"),
        "name": body.name,
        "node_kind": body.node_kind,
        "summary": body.summary or "",
        "tags": body.tags or [],
        "rarity": body.rarity,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
        "resolver_id": None,
        "codex_node_id": None,
    }
    await db.material_intake_queue.insert_one(ticket)
    return {k: v for k, v in ticket.items() if k != "_id"}


@router.get("/campaigns/{cid}/materials-queue")
async def list_material_queue(
    cid: str, status: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """List approval tickets. GM sees all; player sees only their own."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    is_gm = (user["id"] == camp.get("gm_id"))
    q = {"campaign_id": cid}
    if not is_gm:
        q["submitter_id"] = user["id"]
    if status:
        q["status"] = status
    rows = await db.material_intake_queue.find(q, {"_id": 0}).sort("submitted_at", -1).to_list(length=500)
    return rows


@router.post("/campaigns/{cid}/materials-queue/{tid}/approve")
async def approve_material(
    cid: str, tid: str,
    user: dict = Depends(get_current_user),
):
    """GM approves a ticket → seeds a codex node with the right kind."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp.get("gm_id"):
        raise HTTPException(403, "Only the GM can resolve materials queue tickets.")

    ticket = await db.material_intake_queue.find_one(
        {"id": tid, "campaign_id": cid}, {"_id": 0})
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if ticket["status"] != "pending":
        raise HTTPException(409, f"Ticket already {ticket['status']}.")

    node = {
        "id": new_id(),
        "campaign_id": cid,
        "name": ticket["name"],
        "type": ticket["node_kind"],            # legacy field
        "node_kind": ticket["node_kind"],
        "summary": ticket["summary"],
        "tags": ticket["tags"],
        "rarity": ticket.get("rarity"),
        "submitted_by": ticket["submitter_id"],
        "approved_by": user["id"],
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.nodes.insert_one(node)

    await db.material_intake_queue.update_one(
        {"id": tid}, {"$set": {
            "status": "approved",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolver_id": user["id"],
            "codex_node_id": node["id"],
        }})
    return {"ok": True, "codex_node_id": node["id"]}


@router.post("/campaigns/{cid}/materials-queue/{tid}/reject")
async def reject_material(
    cid: str, tid: str,
    user: dict = Depends(get_current_user),
):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp.get("gm_id"):
        raise HTTPException(403, "Only the GM can resolve materials queue tickets.")
    res = await db.material_intake_queue.update_one(
        {"id": tid, "campaign_id": cid, "status": "pending"},
        {"$set": {"status": "rejected",
                  "resolved_at": datetime.now(timezone.utc).isoformat(),
                  "resolver_id": user["id"]}})
    if res.matched_count == 0:
        raise HTTPException(404, "Ticket not found or already resolved")
    return {"ok": True}
