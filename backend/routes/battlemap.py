"""Battlemap — per-session canvas state.

Storage shape (single doc per session, upserted on every change):
    {
      session_id,
      grid: { size_px, cols, rows, color, opacity },
      image: { url?, fit: "cover"|"contain", offset_x, offset_y },
      tokens: [{ id, character_id?, label, color, x, y, size, hp_pct, status[] }],
      walls:  [{ id, x1, y1, x2, y2 }],            # GM-drawn line segments
      fog:    [{ x, y }],                          # cell-coords still hidden
      measurements: [{ id, x1, y1, x2, y2, label }],   # ephemeral GM rulers
      revealed_to: ["uid"],                         # players who can see GM-fog removals (always all currently)
      updated_at,
    }

WebSocket broadcasts (re-uses the existing session bus):
    map:state    full state replace  (after PUT /map)
    map:token    one token upsert   (drag + add)
    map:token-remove  { id }
    map:fog      delta cell-list { reveal: [...], hide: [...] }
    map:wall     wall add/remove  { added?, removed? }
    map:measure  measurement add/clear (GM rulers)

GM-only writes; all members read. Players can move tokens whose
character_id matches one they own; GM can move any token.
"""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.bus import broadcast
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["battlemap"])


# ───────────────────────── Pydantic in-models ─────────────────────────

class GridIn(BaseModel):
    size_px: int = 48
    cols: int = 24
    rows: int = 16
    color: str = "#c8a34a55"
    opacity: float = 0.45


class ImageIn(BaseModel):
    url: str = ""
    fit: Literal["cover", "contain"] = "cover"
    offset_x: int = 0
    offset_y: int = 0


class TokenIn(BaseModel):
    id: Optional[str] = None
    character_id: Optional[str] = None
    label: str = ""
    color: str = "#c8a34a"
    x: float = 0
    y: float = 0
    size: float = 1.0  # multiplier of grid_size_px (1 = single cell)
    hp_pct: int = 100
    status: List[str] = []


class WallIn(BaseModel):
    id: Optional[str] = None
    x1: float
    y1: float
    x2: float
    y2: float


class MapStateIn(BaseModel):
    grid: GridIn = GridIn()
    image: ImageIn = ImageIn()
    tokens: List[TokenIn] = []
    walls: List[WallIn] = []
    fog: List[Dict[str, int]] = Field(default_factory=list)


class FogPaintIn(BaseModel):
    """Cell-list deltas. Cells use grid coords, not pixels."""
    reveal: List[Dict[str, int]] = Field(default_factory=list)
    hide: List[Dict[str, int]] = Field(default_factory=list)


# ───────────────────────── Helpers ─────────────────────────

async def _load_session_with_camp(sid: str) -> tuple:
    sess = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not sess:
        raise HTTPException(404, "Session not found")
    camp = await db.campaigns.find_one({"id": sess["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return sess, camp


def _is_member(user, camp) -> bool:
    return camp["gm_id"] == user["id"] or user["id"] in camp.get("member_ids", [])


def _is_gm(user, camp) -> bool:
    return camp["gm_id"] == user["id"] or user.get("role") == "admin"


async def _get_or_init_map(sid: str) -> dict:
    doc = await db.battlemaps.find_one({"session_id": sid}, {"_id": 0})
    if doc:
        return doc
    fresh = {
        "session_id": sid,
        "grid": GridIn().model_dump(),
        "image": ImageIn().model_dump(),
        "tokens": [],
        "walls": [],
        "fog": [],
        "measurements": [],
        "updated_at": now_iso(),
    }
    await db.battlemaps.insert_one(fresh)
    return fresh


# ───────────────────────── Routes ─────────────────────────

@router.get("/sessions/{sid}/map")
async def get_map(sid: str, user: dict = Depends(get_current_user)):
    sess, camp = await _load_session_with_camp(sid)
    if not _is_member(user, camp):
        raise HTTPException(403, "Not seated at this table")
    state = await _get_or_init_map(sid)
    return sanitize(state)


@router.put("/sessions/{sid}/map")
async def replace_map(sid: str, body: MapStateIn,
                      user: dict = Depends(get_current_user)):
    """GM-only: full-state replace (image/grid + tokens/walls/fog wholesale)."""
    sess, camp = await _load_session_with_camp(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may rewrite the map")
    new_state = body.model_dump()
    # Stamp ids on any tokens/walls that arrived without one.
    for t in new_state["tokens"]:
        t["id"] = t.get("id") or new_id()
    for w in new_state["walls"]:
        w["id"] = w.get("id") or new_id()
    new_state["session_id"] = sid
    new_state["measurements"] = []
    new_state["updated_at"] = now_iso()
    await db.battlemaps.replace_one({"session_id": sid}, new_state, upsert=True)
    await broadcast(sid, {"type": "map:state", "data": sanitize(new_state)})
    return sanitize(new_state)


@router.post("/sessions/{sid}/map/tokens")
async def upsert_token(sid: str, body: TokenIn,
                       user: dict = Depends(get_current_user)):
    """Player may move a token tied to a character they own; GM may move any."""
    sess, camp = await _load_session_with_camp(sid)
    if not _is_member(user, camp):
        raise HTTPException(403, "Not seated at this table")
    state = await _get_or_init_map(sid)

    incoming = body.model_dump()
    incoming["id"] = incoming.get("id") or new_id()

    existing = next((t for t in state["tokens"] if t["id"] == incoming["id"]), None)
    is_gm = _is_gm(user, camp)
    if existing and not is_gm:
        # Player moves: must own the linked character OR be an
        # explicitly-assigned companion owner (V6.9 sidekick model).
        cid = existing.get("character_id")
        if not cid:
            raise HTTPException(403, "Only the GM may move unbound tokens")
        ch = await db.characters.find_one(
            {"id": cid}, {"_id": 0, "owner_id": 1, "companion_owners": 1},
        )
        if not ch:
            raise HTTPException(403, "Linked character not found")
        is_owner = ch.get("owner_id") == user["id"]
        is_companion = user["id"] in (ch.get("companion_owners") or [])
        if not (is_owner or is_companion):
            raise HTTPException(403, "You do not own that character or its companion seat")
    if not existing and not is_gm:
        raise HTTPException(403, "Only the GM may add tokens")

    if existing:
        existing.update({k: v for k, v in incoming.items() if v is not None or k in ("character_id",)})
        token = existing
    else:
        state["tokens"].append(incoming)
        token = incoming

    state["updated_at"] = now_iso()
    await db.battlemaps.replace_one({"session_id": sid}, state, upsert=True)
    await broadcast(sid, {"type": "map:token", "data": token})
    return token


@router.delete("/sessions/{sid}/map/tokens/{tid}")
async def remove_token(sid: str, tid: str,
                       user: dict = Depends(get_current_user)):
    sess, camp = await _load_session_with_camp(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may remove tokens")
    state = await _get_or_init_map(sid)
    state["tokens"] = [t for t in state["tokens"] if t["id"] != tid]
    state["updated_at"] = now_iso()
    await db.battlemaps.replace_one({"session_id": sid}, state, upsert=True)
    await broadcast(sid, {"type": "map:token-remove", "data": {"id": tid}})
    return {"ok": True}


@router.post("/sessions/{sid}/map/fog")
async def paint_fog(sid: str, body: FogPaintIn,
                    user: dict = Depends(get_current_user)):
    """GM only: hide/reveal grid cells. Storage holds *hidden* cells; reveal
    removes from the list, hide adds to it. Players never receive raw fog
    state — they get the same map but with hidden cells masked client-side."""
    sess, camp = await _load_session_with_camp(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may paint fog")
    state = await _get_or_init_map(sid)
    fog = {(c["x"], c["y"]) for c in state.get("fog", [])}
    for c in body.hide:
        fog.add((int(c["x"]), int(c["y"])))
    for c in body.reveal:
        fog.discard((int(c["x"]), int(c["y"])))
    state["fog"] = [{"x": x, "y": y} for (x, y) in fog]
    state["updated_at"] = now_iso()
    await db.battlemaps.replace_one({"session_id": sid}, state, upsert=True)
    await broadcast(sid, {"type": "map:fog", "data": {
        "reveal": body.reveal, "hide": body.hide,
    }})
    return {"ok": True, "hidden_cells": len(state["fog"])}


@router.post("/sessions/{sid}/map/walls")
async def add_wall(sid: str, body: WallIn,
                   user: dict = Depends(get_current_user)):
    sess, camp = await _load_session_with_camp(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may draw walls")
    state = await _get_or_init_map(sid)
    wall = body.model_dump()
    wall["id"] = wall.get("id") or new_id()
    state["walls"].append(wall)
    state["updated_at"] = now_iso()
    await db.battlemaps.replace_one({"session_id": sid}, state, upsert=True)
    await broadcast(sid, {"type": "map:wall", "data": {"added": wall}})
    return wall


@router.delete("/sessions/{sid}/map/walls/{wid}")
async def remove_wall(sid: str, wid: str,
                      user: dict = Depends(get_current_user)):
    sess, camp = await _load_session_with_camp(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may remove walls")
    state = await _get_or_init_map(sid)
    state["walls"] = [w for w in state["walls"] if w["id"] != wid]
    state["updated_at"] = now_iso()
    await db.battlemaps.replace_one({"session_id": sid}, state, upsert=True)
    await broadcast(sid, {"type": "map:wall", "data": {"removed": wid}})
    return {"ok": True}
