"""V6.25.26 — Anti-railroad encounter library.

Encounters become first-class artifacts the GM authors in bulk and
selects from INSIDE a session, instead of being pre-bound per-session.
This allows GMs to:

  * Bulk-create combat / social / exploration scenes.
  * Browse the archive during a session and pick which one fits the
    direction the table just took.
  * Mark encounters completed (with notes) when used.
  * Clone a successful encounter as a template for re-use.

Encounter status lifecycle:
    draft     — author still tweaking
    ready     — ready for the GM to drop into a live session
    running   — currently being run (linked_session_id is set)
    completed — used and resolved
    template  — preserved as a re-use scaffold

Endpoints:
    POST   /api/campaigns/{cid}/encounters-library             create
    GET    /api/campaigns/{cid}/encounters-library             list
    GET    /api/campaigns/{cid}/encounters-library/{eid}       read
    PATCH  /api/campaigns/{cid}/encounters-library/{eid}       update
    DELETE /api/campaigns/{cid}/encounters-library/{eid}       delete
    POST   .../{eid}/run?session_id=...                        link to session
    POST   .../{eid}/complete                                  mark completed
    POST   .../{eid}/clone                                     clone as template
"""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["encounters-library"])


EncounterStatus = Literal["draft", "ready", "running", "completed", "template"]


class EncounterLibIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    summary: str = Field(default="", max_length=600)
    encounter_type: str = Field(default="combat", max_length=40,
                                  description="combat | social | exploration | puzzle | mixed")
    cr_target: Optional[float] = Field(default=None,
                                          description="System-agnostic challenge rating target.")
    monsters: List[Dict[str, Any]] = Field(default_factory=list,
                                              description="List of {name, count, level/cr, ref}.")
    complications: List[str] = Field(default_factory=list)
    terrain: str = Field(default="", max_length=300)
    rewards: List[Dict[str, Any]] = Field(default_factory=list,
                                              description="List of {kind: 'material'|'reference'|'xp', id?, label, amount?}.")
    tags: List[str] = Field(default_factory=list)
    status: EncounterStatus = "draft"
    notes: str = Field(default="", max_length=2000)


async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    return camp


def _is_gm(camp: dict, user: dict) -> bool:
    return camp.get("gm_id") == user["id"] or user.get("role") == "admin"


@router.post("/campaigns/{cid}/encounters-library")
async def create_encounter(cid: str, body: EncounterLibIn,
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    row = {
        "id": new_id(),
        "campaign_id": cid,
        "name": body.name.strip(),
        "summary": (body.summary or "").strip(),
        "encounter_type": body.encounter_type,
        "cr_target": body.cr_target,
        "monsters": body.monsters,
        "complications": body.complications,
        "terrain": body.terrain.strip(),
        "rewards": body.rewards,
        "tags": body.tags,
        "status": body.status,
        "notes": body.notes,
        "linked_session_id": None,
        "completed_at": None,
        "completion_notes": "",
        "cloned_from_id": None,
        "created_at": now_iso(),
        "created_by_id": user["id"],
        "created_by_name": user.get("name") or user.get("email"),
    }
    await db.encounters_library.insert_one(row)
    row.pop("_id", None)
    return row


@router.get("/campaigns/{cid}/encounters-library")
async def list_encounters(cid: str,
                              status: Optional[str] = None,
                              template: Optional[bool] = None,
                              encounter_type: Optional[str] = None,
                              session_id: Optional[str] = Query(default=None,
                                description="If set, list encounters linked to this session."),
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    q: Dict[str, Any] = {"campaign_id": cid}
    if status:
        q["status"] = status
    if template is True:
        q["status"] = "template"
    if encounter_type:
        q["encounter_type"] = encounter_type
    if session_id:
        q["linked_session_id"] = session_id
    cursor = db.encounters_library.find(q, {"_id": 0}).sort("created_at", -1)
    return {"rows": [r async for r in cursor]}


@router.get("/campaigns/{cid}/encounters-library/{eid}")
async def get_encounter(cid: str, eid: str,
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    row = await db.encounters_library.find_one(
        {"campaign_id": cid, "id": eid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Encounter not found.")
    return row


@router.patch("/campaigns/{cid}/encounters-library/{eid}")
async def update_encounter(cid: str, eid: str, body: EncounterLibIn,
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.encounters_library.update_one(
        {"campaign_id": cid, "id": eid},
        {"$set": {
            "name": body.name.strip(),
            "summary": (body.summary or "").strip(),
            "encounter_type": body.encounter_type,
            "cr_target": body.cr_target,
            "monsters": body.monsters,
            "complications": body.complications,
            "terrain": body.terrain.strip(),
            "rewards": body.rewards,
            "tags": body.tags,
            "status": body.status,
            "notes": body.notes,
            "updated_at": now_iso(),
        }})
    if res.matched_count == 0:
        raise HTTPException(404, "Encounter not found.")
    row = await db.encounters_library.find_one(
        {"campaign_id": cid, "id": eid}, {"_id": 0})
    return row


@router.delete("/campaigns/{cid}/encounters-library/{eid}")
async def delete_encounter(cid: str, eid: str,
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.encounters_library.delete_one(
        {"campaign_id": cid, "id": eid})
    return {"ok": True, "deleted": res.deleted_count}


@router.post("/campaigns/{cid}/encounters-library/{eid}/run")
async def run_encounter(cid: str, eid: str, session_id: str = Query(...),
                          user: dict = Depends(get_current_user)):
    """Link an encounter to a session and mark it as running. The
    anti-railroad flow: GM picks from the library WHILE running the
    session, instead of pre-binding encounters at planning time."""
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.encounters_library.update_one(
        {"campaign_id": cid, "id": eid},
        {"$set": {"linked_session_id": session_id, "status": "running",
                    "started_at": now_iso()}})
    if res.matched_count == 0:
        raise HTTPException(404, "Encounter not found.")
    return await db.encounters_library.find_one(
        {"campaign_id": cid, "id": eid}, {"_id": 0})


@router.post("/campaigns/{cid}/encounters-library/{eid}/complete")
async def complete_encounter(cid: str, eid: str,
                                completion_notes: str = "",
                                user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.encounters_library.update_one(
        {"campaign_id": cid, "id": eid},
        {"$set": {"status": "completed",
                    "completion_notes": completion_notes,
                    "completed_at": now_iso()}})
    if res.matched_count == 0:
        raise HTTPException(404, "Encounter not found.")
    return await db.encounters_library.find_one(
        {"campaign_id": cid, "id": eid}, {"_id": 0})


@router.post("/campaigns/{cid}/encounters-library/{eid}/clone")
async def clone_encounter(cid: str, eid: str,
                              as_template: bool = True,
                              user: dict = Depends(get_current_user)):
    """Clone the encounter for re-use. Defaults to template status so
    the GM can edit + fork it without disturbing the original record."""
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    src = await db.encounters_library.find_one(
        {"campaign_id": cid, "id": eid}, {"_id": 0})
    if not src:
        raise HTTPException(404, "Encounter not found.")
    new_row = dict(src)
    new_row["id"] = new_id()
    new_row["name"] = src["name"] + (" · template" if as_template else " · copy")
    new_row["status"] = "template" if as_template else "draft"
    new_row["linked_session_id"] = None
    new_row["completed_at"] = None
    new_row["completion_notes"] = ""
    new_row["cloned_from_id"] = src["id"]
    new_row["created_at"] = now_iso()
    new_row["created_by_id"] = user["id"]
    new_row["created_by_name"] = user.get("name") or user.get("email")
    new_row.pop("started_at", None)
    new_row.pop("updated_at", None)
    await db.encounters_library.insert_one(new_row)
    new_row.pop("_id", None)
    return new_row
