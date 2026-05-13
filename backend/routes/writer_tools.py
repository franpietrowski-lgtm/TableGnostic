"""V6.25.46 — Writer-role real authoring tools (backend).

Routes for the four writer surfaces being promoted from scaffold to
working tools in this drop:

  • Atlas (Worldbuilder)            — campaign world map + pin tokens.
      Map image lives on `campaign.world_map_url`. Pins live on the
      existing `nodes` collection (type=location); the pin position is
      stored on `node.fields.map_x` / `map_y` (0..1 normalised).
  • Magic Architect (Worldbuilder)  — Primary Sources, channels, costs.
      New collection: `magic_systems`.
  • Manuscript (Storyteller)        — chapter / scene tree + markdown body.
      New collection: `manuscript_sections`.
  • Outline & Beats (Storyteller)   — beats per scene with tension rating.
      Reuses `manuscript_sections` with kind="beat".

All endpoints are scoped to a single campaign and require the caller
to be the GM (campaign.gm_id) OR a campaign member with the
worldbuilder/storyteller role on the campaign membership. Admins
bypass every check.

For writer-role accounts, every campaign they create is implicitly
their own — so the GM check passes trivially. For player/gm accounts
seated at a writer-role's campaign, they need a documented invite
flow before they can edit these surfaces (read-only is OK).
"""
from __future__ import annotations
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, conint

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api/writer", tags=["writer-tools"])


# -------- shared helpers --------

async def _camp_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    return camp


def _can_write(user: dict, camp: dict) -> bool:
    if user.get("role") == "admin":
        return True
    if camp.get("gm_id") == user["id"]:
        return True
    # Writer-role-only campaigns: the writer IS the gm by construction.
    return False


def _can_read(user: dict, camp: dict) -> bool:
    if _can_write(user, camp):
        return True
    return user["id"] in (camp.get("member_ids") or [])


async def _require_write(user: dict, cid: str) -> dict:
    camp = await _camp_or_404(cid)
    if not _can_write(user, camp):
        raise HTTPException(403, "Worldbuilder/Storyteller tools are "
                                 "GM-write / admin-write only.")
    return camp


# ======================================================================
# ATLAS — Worldbuilder
# ======================================================================

class WorldMapPatchIn(BaseModel):
    world_map_url: Optional[str] = Field(None, max_length=2000)
    world_map_caption: Optional[str] = Field(None, max_length=400)


class AtlasPinIn(BaseModel):
    node_id: Optional[str] = None       # link to existing location node
    title: str = Field(..., max_length=160)
    description: Optional[str] = Field(None, max_length=1000)
    map_x: float = Field(..., ge=0.0, le=1.0)   # normalised 0..1
    map_y: float = Field(..., ge=0.0, le=1.0)
    location_type: Optional[str] = Field(None, max_length=40)


@router.get("/atlas/{cid}")
async def atlas_get(cid: str, user: dict = Depends(get_current_user)):
    camp = await _camp_or_404(cid)
    if not _can_read(user, camp):
        raise HTTPException(403, "Not a member of this campaign.")
    # Pull every location node — pin coords live on node.fields.
    pins = await db.nodes.find(
        {"campaign_id": cid, "type": "location",
         "fields.map_x": {"$exists": True}},
        {"_id": 0},
    ).to_list(1000)
    # Also surface locations WITHOUT a pin so the GM can drop them on the map.
    unpinned = await db.nodes.find(
        {"campaign_id": cid, "type": "location",
         "fields.map_x": {"$exists": False}},
        {"_id": 0},
    ).to_list(400)
    return {
        "world_map_url":     camp.get("world_map_url"),
        "world_map_caption": camp.get("world_map_caption"),
        "pins": pins,
        "unpinned_locations": unpinned,
        "writable": _can_write(user, camp),
    }


@router.patch("/atlas/{cid}/map")
async def atlas_patch_map(cid: str, body: WorldMapPatchIn,
                          user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    upd: dict = {}
    if body.world_map_url is not None:
        upd["world_map_url"] = body.world_map_url
    if body.world_map_caption is not None:
        upd["world_map_caption"] = body.world_map_caption
    if upd:
        await db.campaigns.update_one({"id": cid}, {"$set": upd})
    out = await db.campaigns.find_one({"id": cid}, {"_id": 0,
                                                    "world_map_url": 1,
                                                    "world_map_caption": 1})
    return out or {}


@router.post("/atlas/{cid}/pins")
async def atlas_create_pin(cid: str, body: AtlasPinIn,
                           user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    if body.node_id:
        node = await db.nodes.find_one({"id": body.node_id, "campaign_id": cid},
                                       {"_id": 0})
        if not node or node.get("type") != "location":
            raise HTTPException(400, "node_id must reference a location node "
                                     "in this campaign.")
        # Place the pin on the existing node.
        fields = dict(node.get("fields") or {})
        fields["map_x"] = body.map_x
        fields["map_y"] = body.map_y
        if body.location_type and not fields.get("location_type"):
            fields["location_type"] = body.location_type
        await db.nodes.update_one(
            {"id": node["id"]},
            {"$set": {"fields": fields,
                      "content": body.description or node.get("content") or ""}},
        )
        return {"node_id": node["id"], "pinned": True}
    # No node_id → mint a fresh location node anchored at this pin.
    new_node = {
        "id": new_id(),
        "campaign_id": cid,
        "type": "location",
        "title": body.title[:160],
        "content": (body.description or "")[:8000],
        "tags": ["worldbuilder-atlas-pin"],
        "visibility": "gm_only",
        "revealed_to": [],
        "links": [],
        "fields": {
            "map_x": body.map_x,
            "map_y": body.map_y,
            "location_type": body.location_type or "other",
            "created_via": "atlas-pin",
        },
        "created_at": now_iso(),
    }
    await db.nodes.insert_one(new_node)
    new_node.pop("_id", None)
    return {"node_id": new_node["id"], "pinned": True, "node": new_node}


@router.delete("/atlas/{cid}/pins/{node_id}")
async def atlas_unpin(cid: str, node_id: str,
                      user: dict = Depends(get_current_user)):
    """Unpin a node (does NOT delete it — just clears its map coords)."""
    await _require_write(user, cid)
    await db.nodes.update_one(
        {"id": node_id, "campaign_id": cid},
        {"$unset": {"fields.map_x": "", "fields.map_y": ""}},
    )
    return {"node_id": node_id, "unpinned": True}


# ======================================================================
# MAGIC ARCHITECT — Worldbuilder
# ======================================================================

class MagicSourceIn(BaseModel):
    name: str = Field(..., max_length=160)
    kind: str = Field("primary", max_length=40)   # primary | channel | effect
    alignment: Optional[str] = Field(None, max_length=40)  # aurae|mortiscure|both|none
    summary: Optional[str] = Field(None, max_length=4000)
    invocation_cost: Optional[str] = Field(None, max_length=400)
    side_effects: Optional[str] = Field(None, max_length=1000)


@router.get("/magic/{cid}")
async def magic_list(cid: str, user: dict = Depends(get_current_user)):
    camp = await _camp_or_404(cid)
    if not _can_read(user, camp):
        raise HTTPException(403, "Not a member of this campaign.")
    rows = await db.magic_systems.find(
        {"campaign_id": cid}, {"_id": 0},
    ).sort("created_at", 1).to_list(500)
    return {"sources": rows, "writable": _can_write(user, camp)}


@router.post("/magic/{cid}")
async def magic_create(cid: str, body: MagicSourceIn,
                       user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    doc = {
        "id": new_id(), "campaign_id": cid,
        "name": body.name[:160], "kind": body.kind,
        "alignment": body.alignment, "summary": body.summary,
        "invocation_cost": body.invocation_cost,
        "side_effects": body.side_effects,
        "created_at": now_iso(),
    }
    await db.magic_systems.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


@router.patch("/magic/{cid}/{sid}")
async def magic_patch(cid: str, sid: str, body: MagicSourceIn,
                      user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    upd = {k: v for k, v in body.model_dump().items() if v is not None}
    upd["updated_at"] = now_iso()
    await db.magic_systems.update_one(
        {"id": sid, "campaign_id": cid}, {"$set": upd},
    )
    out = await db.magic_systems.find_one({"id": sid}, {"_id": 0})
    return out or {}


@router.delete("/magic/{cid}/{sid}")
async def magic_delete(cid: str, sid: str,
                       user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    r = await db.magic_systems.delete_one({"id": sid, "campaign_id": cid})
    return {"deleted": r.deleted_count}


# ======================================================================
# MANUSCRIPT (chapter/scene tree + markdown) — Storyteller
# Also drives OUTLINE & BEATS (kind=beat is just a child of scene).
# ======================================================================

class ManuscriptSectionIn(BaseModel):
    kind: str = Field(..., max_length=20)   # chapter | scene | beat
    title: str = Field(..., max_length=200)
    parent_id: Optional[str] = None
    body_md: Optional[str] = Field(None, max_length=200_000)
    order: Optional[conint(ge=0, le=10_000)] = None
    status: Optional[str] = Field(None, max_length=30)  # planned | drafted | revised | cut
    tension: Optional[conint(ge=0, le=5)] = None        # outline pacing graph 0..5


@router.get("/manuscript/{cid}")
async def manuscript_tree(cid: str, user: dict = Depends(get_current_user)):
    camp = await _camp_or_404(cid)
    if not _can_read(user, camp):
        raise HTTPException(403, "Not a member of this campaign.")
    rows = await db.manuscript_sections.find(
        {"campaign_id": cid}, {"_id": 0},
    ).sort("order", 1).to_list(2000)
    total_words = sum((r.get("word_count") or 0) for r in rows)
    return {"sections": rows,
            "total_word_count": total_words,
            "writable": _can_write(user, camp)}


@router.get("/manuscript/{cid}/{sid}")
async def manuscript_get(cid: str, sid: str,
                         user: dict = Depends(get_current_user)):
    camp = await _camp_or_404(cid)
    if not _can_read(user, camp):
        raise HTTPException(403, "Not a member of this campaign.")
    row = await db.manuscript_sections.find_one(
        {"id": sid, "campaign_id": cid}, {"_id": 0},
    )
    if not row:
        raise HTTPException(404, "Section not found.")
    return row


@router.post("/manuscript/{cid}")
async def manuscript_create(cid: str, body: ManuscriptSectionIn,
                            user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    if body.kind not in {"chapter", "scene", "beat"}:
        raise HTTPException(400, "kind must be chapter|scene|beat.")
    # Validate parent relationship: scenes must parent under chapters,
    # beats under scenes; chapters have no parent.
    parent = None
    if body.parent_id:
        parent = await db.manuscript_sections.find_one(
            {"id": body.parent_id, "campaign_id": cid}, {"_id": 0},
        )
        if not parent:
            raise HTTPException(400, "parent_id not found in this campaign.")
        if body.kind == "chapter":
            raise HTTPException(400, "chapters have no parent.")
        if body.kind == "scene" and parent["kind"] != "chapter":
            raise HTTPException(400, "scene parent must be a chapter.")
        if body.kind == "beat" and parent["kind"] != "scene":
            raise HTTPException(400, "beat parent must be a scene.")
    elif body.kind != "chapter":
        raise HTTPException(400, f"{body.kind} requires a parent_id.")
    # Compute order: append by default.
    if body.order is None:
        last = await db.manuscript_sections.find_one(
            {"campaign_id": cid, "parent_id": body.parent_id},
            {"_id": 0, "order": 1}, sort=[("order", -1)],
        )
        order = ((last or {}).get("order") or 0) + 10
    else:
        order = body.order
    word_count = len((body.body_md or "").split()) if body.body_md else 0
    doc = {
        "id": new_id(), "campaign_id": cid,
        "owner_id": user["id"],
        "kind": body.kind, "title": body.title[:200],
        "parent_id": body.parent_id, "order": order,
        "body_md": body.body_md or "",
        "word_count": word_count,
        "status": body.status or "planned",
        "tension": body.tension,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.manuscript_sections.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


@router.patch("/manuscript/{cid}/{sid}")
async def manuscript_patch(cid: str, sid: str, body: ManuscriptSectionIn,
                           user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    upd = {k: v for k, v in body.model_dump().items() if v is not None}
    if "body_md" in upd:
        upd["word_count"] = len(upd["body_md"].split())
    upd["updated_at"] = now_iso()
    # Never mutate parent or kind on patch — that requires a delete + recreate.
    upd.pop("parent_id", None)
    upd.pop("kind", None)
    r = await db.manuscript_sections.update_one(
        {"id": sid, "campaign_id": cid}, {"$set": upd},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "Section not found.")
    out = await db.manuscript_sections.find_one({"id": sid}, {"_id": 0})
    return out or {}


@router.delete("/manuscript/{cid}/{sid}")
async def manuscript_delete(cid: str, sid: str,
                            user: dict = Depends(get_current_user)):
    await _require_write(user, cid)
    # Cascade — delete children too (chapter wipes its scenes + beats).
    descendants = []
    queue = [sid]
    while queue:
        nxt = queue.pop()
        descendants.append(nxt)
        rows = await db.manuscript_sections.find(
            {"campaign_id": cid, "parent_id": nxt},
            {"_id": 0, "id": 1},
        ).to_list(2000)
        queue.extend(r["id"] for r in rows)
    r = await db.manuscript_sections.delete_many(
        {"campaign_id": cid, "id": {"$in": descendants}},
    )
    return {"deleted": r.deleted_count}
