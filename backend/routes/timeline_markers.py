"""Timeline Markers — V6.9 cross-link between Codex Chart and Timeline.

GMs annotate their narrative spine by clicking a Codex node in the Chart View;
this writes a `timeline_marker` doc bound to a specific session. The Timeline
Panel then renders a small badge attached to that session's column.

Storage shape (`db.timeline_markers`, one doc per marker):
    {
      id,
      campaign_id,
      session_id,
      codex_node_id,            # may be empty for free-text annotations
      label,                    # short caption (auto-filled from node title)
      kind,                     # "node" | "note" | "milestone"
      color,                    # accent color for the badge
      created_by,
      created_at,
    }

Routes:
    GET    /api/campaigns/{cid}/timeline-markers       — all markers (members)
    POST   /api/campaigns/{cid}/timeline-markers       — GM creates new marker
    DELETE /api/campaigns/{cid}/timeline-markers/{mid} — GM deletes
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["timeline-markers"])


class MarkerIn(BaseModel):
    session_id: str
    codex_node_id: Optional[str] = None
    label: str = Field(min_length=1, max_length=120)
    kind: Literal["node", "note", "milestone"] = "node"
    color: str = "#C8A34A"


async def _load_camp(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp


def _is_member(user, camp) -> bool:
    return camp["gm_id"] == user["id"] or user["id"] in camp.get("member_ids", [])


def _is_gm(user, camp) -> bool:
    return camp["gm_id"] == user["id"] or user.get("role") == "admin"


@router.get("/campaigns/{cid}/timeline-markers")
async def list_markers(cid: str, user: dict = Depends(get_current_user)):
    camp = await _load_camp(cid)
    if not _is_member(user, camp):
        raise HTTPException(403, "Not at this table")
    rows = await db.timeline_markers.find(
        {"campaign_id": cid}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    return sanitize(rows)


@router.post("/campaigns/{cid}/timeline-markers")
async def create_marker(cid: str, body: MarkerIn,
                        user: dict = Depends(get_current_user)):
    camp = await _load_camp(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may pin timeline markers")
    # Confirm session belongs to this campaign.
    sess = await db.sessions.find_one(
        {"id": body.session_id, "campaign_id": cid}, {"_id": 0, "id": 1},
    )
    if not sess:
        raise HTTPException(400, "Session not found in this campaign")
    # If a node is referenced, confirm it's in this campaign too.
    if body.codex_node_id:
        node = await db.nodes.find_one(
            {"id": body.codex_node_id, "campaign_id": cid}, {"_id": 0, "id": 1},
        )
        if not node:
            raise HTTPException(400, "Codex node not found in this campaign")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "session_id": body.session_id,
        "codex_node_id": body.codex_node_id,
        "label": body.label.strip(),
        "kind": body.kind,
        "color": body.color,
        "created_by": user["id"],
        "created_at": now_iso(),
    }
    await db.timeline_markers.insert_one(doc)
    return sanitize(doc)


@router.delete("/campaigns/{cid}/timeline-markers/{mid}")
async def delete_marker(cid: str, mid: str,
                        user: dict = Depends(get_current_user)):
    camp = await _load_camp(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may remove timeline markers")
    res = await db.timeline_markers.delete_one(
        {"id": mid, "campaign_id": cid},
    )
    if res.deleted_count == 0:
        raise HTTPException(404, "Marker not found")
    return {"ok": True}
