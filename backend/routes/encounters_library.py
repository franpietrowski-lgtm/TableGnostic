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


class CasualtyIn(BaseModel):
    node_id: str
    death_reason: str = Field(default="", max_length=600)
    witnesses: List[str] = Field(default_factory=list,
                                    description="Codex node IDs of witnesses")
    killed_by_character_id: Optional[str] = None


class KillTallyIn(BaseModel):
    monster_name: str = Field(..., min_length=1, max_length=160)
    monster_ref_id: Optional[str] = None
    count: int = Field(default=1, ge=1, le=999)
    cr: Optional[float] = None
    system: Optional[str] = None
    killed_by_character_id: Optional[str] = None


class EncounterCompleteIn(BaseModel):
    completion_notes: str = Field(default="", max_length=2000)
    session_id: Optional[str] = None
    casualties: List[CasualtyIn] = Field(default_factory=list)
    kills: List[KillTallyIn] = Field(default_factory=list)


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
                                body: Optional[EncounterCompleteIn] = None,
                                completion_notes: str = "",
                                user: dict = Depends(get_current_user)):
    """V6.25.29 — encounter completion now propagates to the codex.

    Body (all fields optional, GM may also pass simple completion_notes
    as query for backwards compat):
      • completion_notes  — free-text resolution notes
      • session_id        — the session in which the encounter resolved
      • casualties[]      — entity codex nodes that died IN this encounter
                              {node_id, death_reason, witnesses[node_id…],
                               killed_by_character_id?}
      • kills[]           — monster/creature kill tally
                              {monster_name, monster_ref_id?, count,
                               killed_by_character_id?, cr?, system?}

    Side-effects:
      * Each casualty: codex node receives `fields.deceased=True`,
        `fields.death_log` appended (vigilization). Death reason +
        witnesses + session id + timestamp recorded.
      * Each kill: a row is inserted into `kill_logs` for running tally
        (per monster type, per character, per campaign).
    """
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    enc = await db.encounters_library.find_one(
        {"campaign_id": cid, "id": eid}, {"_id": 0})
    if not enc:
        raise HTTPException(404, "Encounter not found.")

    # Body may be None (legacy call w/ ?completion_notes=...).
    body = body or EncounterCompleteIn()
    notes = (body.completion_notes or completion_notes or "").strip()
    sid = body.session_id or enc.get("linked_session_id")

    update_fields: Dict[str, Any] = {
        "status": "completed",
        "completion_notes": notes,
        "completed_at": now_iso(),
    }
    if sid:
        update_fields["linked_session_id"] = sid

    # ─── Vigilize NPC casualties ────────────────────────────────
    propagated_casualties: List[Dict[str, Any]] = []
    for cas in (body.casualties or []):
        if not cas.node_id:
            continue
        node = await db.nodes.find_one(
            {"id": cas.node_id, "campaign_id": cid}, {"_id": 0})
        if not node:
            continue
        fields = dict(node.get("fields") or {})
        fields["deceased"] = True
        log = list(fields.get("death_log") or [])
        log.append({
            "encounter_id": eid,
            "encounter_name": enc.get("name"),
            "session_id": sid,
            "death_reason": (cas.death_reason or "").strip()
                              or "Killed in encounter.",
            "witnesses": list(cas.witnesses or []),
            "killed_by_character_id": cas.killed_by_character_id,
            "recorded_at": now_iso(),
            "recorded_by_id": user["id"],
            "recorded_by_name": user.get("name") or user.get("email"),
        })
        fields["death_log"] = log
        await db.nodes.update_one(
            {"id": cas.node_id, "campaign_id": cid},
            {"$set": {"fields": fields, "updated_at": now_iso()}})
        propagated_casualties.append({
            "node_id": cas.node_id,
            "title": node.get("title") or node.get("name"),
            "deceased": True,
        })

    # ─── Tally monster/creature kills ───────────────────────────
    propagated_kills: List[Dict[str, Any]] = []
    for kill in (body.kills or []):
        name = (kill.monster_name or "").strip()
        if not name or kill.count <= 0:
            continue
        row = {
            "id": new_id(),
            "campaign_id": cid,
            "encounter_id": eid,
            "encounter_name": enc.get("name"),
            "session_id": sid,
            "monster_name": name,
            "monster_ref_id": kill.monster_ref_id,
            "system": kill.system or camp.get("system_id"),
            "cr": kill.cr,
            "count": int(kill.count),
            "killed_by_character_id": kill.killed_by_character_id,
            "logged_at": now_iso(),
            "logged_by_id": user["id"],
            "logged_by_name": user.get("name") or user.get("email"),
        }
        await db.kill_logs.insert_one(row)
        row.pop("_id", None)
        propagated_kills.append(row)

    await db.encounters_library.update_one(
        {"campaign_id": cid, "id": eid}, {"$set": update_fields})
    out = await db.encounters_library.find_one(
        {"campaign_id": cid, "id": eid}, {"_id": 0})
    out["propagated_casualties"] = propagated_casualties
    out["propagated_kills"] = propagated_kills
    return out


# ─── V6.25.29 — Entity catalogue + kill tally ──────────────────────
ENTITY_KINDS = {"npc", "character", "creature", "monster", "person", "faction"}


@router.get("/campaigns/{cid}/entities")
async def list_entities(cid: str,
                          kind: Optional[str] = None,
                          include_deceased: bool = True,
                          user: dict = Depends(get_current_user)):
    """V6.25.29 — Per-spec, monsters/creatures/characters/NPCs are all
    Entities. Returns codex nodes whose node_kind is in the entity
    family. The encounter completion modal uses this to populate
    casualty + witness pickers without forcing the GM to retype names.
    """
    camp = await _campaign_or_404(cid)
    is_gm = _is_gm(camp, user)
    is_member = (user["id"] in (camp.get("member_ids") or [])
                  or user["id"] == camp["gm_id"]
                  or user.get("role") == "admin")
    if not is_member:
        raise HTTPException(403, "Not a campaign member.")
    q: Dict[str, Any] = {"campaign_id": cid}
    if kind:
        q["$or"] = [{"node_kind": kind}, {"type": kind}]
    else:
        q["$or"] = [
            {"node_kind": {"$in": list(ENTITY_KINDS)}},
            {"type":      {"$in": list(ENTITY_KINDS)}},
        ]
    cursor = db.nodes.find(q, {"_id": 0}).sort("title", 1)
    rows = await cursor.to_list(2000)
    if not is_gm:
        # Players only see shared/revealed nodes.
        rows = [r for r in rows
                  if r.get("visibility") == "shared"
                     or user["id"] in (r.get("revealed_to") or [])]
    if not include_deceased:
        rows = [r for r in rows
                  if not (r.get("fields") or {}).get("deceased")]
    return {"rows": rows, "total": len(rows)}


@router.get("/campaigns/{cid}/kill-tally")
async def kill_tally(cid: str, user: dict = Depends(get_current_user)):
    """V6.25.29 — Running totals of monsters/creatures killed during
    completed encounters. Per-monster-type + per-character + grand
    total. Feeds the future "mer der hoh bohs" leaderboard.
    """
    camp = await _campaign_or_404(cid)
    is_member = (user["id"] in (camp.get("member_ids") or [])
                  or user["id"] == camp["gm_id"]
                  or user.get("role") == "admin")
    if not is_member:
        raise HTTPException(403, "Not a campaign member.")
    rows = await db.kill_logs.find(
        {"campaign_id": cid}, {"_id": 0}).to_list(20000)
    by_monster: Dict[str, int] = {}
    by_character: Dict[str, int] = {}
    by_monster_by_character: Dict[str, Dict[str, int]] = {}
    grand = 0
    for r in rows:
        n = r.get("monster_name") or "Unknown"
        c = int(r.get("count") or 0)
        grand += c
        by_monster[n] = by_monster.get(n, 0) + c
        kby = r.get("killed_by_character_id")
        if kby:
            by_character[kby] = by_character.get(kby, 0) + c
            slot = by_monster_by_character.setdefault(kby, {})
            slot[n] = slot.get(n, 0) + c
    # Resolve character names for the by_character map (helps the UI).
    char_ids = list(by_character.keys())
    char_lookup: Dict[str, str] = {}
    if char_ids:
        ch_rows = await db.characters.find(
            {"id": {"$in": char_ids}}, {"_id": 0, "id": 1, "name": 1}
        ).to_list(2000)
        char_lookup = {c["id"]: c.get("name") or c["id"] for c in ch_rows}
    return {
        "campaign_id": cid,
        "grand_total": grand,
        "by_monster": [
            {"monster_name": k, "kills": v}
            for k, v in sorted(by_monster.items(),
                                  key=lambda kv: -kv[1])
        ],
        "by_character": [
            {"character_id": k, "character_name": char_lookup.get(k, k),
             "kills": v}
            for k, v in sorted(by_character.items(),
                                  key=lambda kv: -kv[1])
        ],
        "by_monster_by_character": by_monster_by_character,
        "log_count": len(rows),
    }


# (CasualtyIn / KillTallyIn / EncounterCompleteIn defined at the top of
# this module so the complete_encounter handler can reference them
# directly without forward-ref strings.)


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
