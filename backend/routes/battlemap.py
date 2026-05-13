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
    # V6.25.48 — sidebar overhaul fields.
    # `kind` distinguishes PC tokens from GM-placed map-markers (doors,
    # traps, treasure, etc.). Markers render a lucide icon instead of
    # the initial-letter circle and are not subject to LoS occlusion.
    kind: Literal["pc", "npc", "marker"] = "pc"
    marker_type: Optional[str] = None  # door|trap|treasure|chest|stairs|portal|ladder|monster|note
    ep_pct: int = 100
    initiative_order: Optional[int] = None
    tooltip: Optional[str] = None
    atlas_node_id: Optional[str] = None   # P2 — link a map-marker back to its codex location node
    locked: bool = False                  # GM-locked tokens can't be moved by players


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


# ───────────── V6.25.49 — PATCH /map/tokens/{tid} ─────────────
# Companion to POST upsert: an explicit partial-update path so other
# routes (HP-from-sheet, status-from-encounter, atlas-relink) can
# mutate a single field on a single token without resending the full
# payload. `extra="forbid"` so unknown fields fail loudly (no silent
# drops). Players are still gated to tokens they own / their companion
# seats, identical to the existing upsert auth model.

class TokenPatchIn(BaseModel):
    """All fields optional — only the keys present in the body are
    written. `id` and `session_id` are deliberately not patchable."""
    model_config = {"extra": "forbid"}
    character_id: Optional[str] = None
    label: Optional[str] = None
    color: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    size: Optional[float] = None
    hp_pct: Optional[int] = None
    ep_pct: Optional[int] = None
    status: Optional[List[str]] = None
    kind: Optional[Literal["pc", "npc", "marker"]] = None
    marker_type: Optional[str] = None
    initiative_order: Optional[int] = None
    tooltip: Optional[str] = None
    atlas_node_id: Optional[str] = None
    locked: Optional[bool] = None


@router.patch("/sessions/{sid}/map/tokens/{tid}")
async def patch_token(sid: str, tid: str, body: TokenPatchIn,
                      user: dict = Depends(get_current_user)):
    """Partial-update a single token. GM-write for any token; players
    may only mutate tokens linked to characters they own or sit a
    companion seat on (identical gate to the POST upsert).
    """
    sess, camp = await _load_session_with_camp(sid)
    if not _is_member(user, camp):
        raise HTTPException(403, "Not seated at this table")
    state = await _get_or_init_map(sid)
    existing = next((t for t in state["tokens"] if t["id"] == tid), None)
    if not existing:
        raise HTTPException(404, "Token not found")

    is_gm = _is_gm(user, camp)
    if not is_gm:
        cid = existing.get("character_id")
        if not cid:
            raise HTTPException(403, "Only the GM may mutate unbound tokens")
        ch = await db.characters.find_one(
            {"id": cid}, {"_id": 0, "owner_id": 1, "companion_owners": 1},
        )
        if not ch:
            raise HTTPException(403, "Linked character not found")
        is_owner = ch.get("owner_id") == user["id"]
        is_companion = user["id"] in (ch.get("companion_owners") or [])
        if not (is_owner or is_companion):
            raise HTTPException(403, "You do not own that character or its companion seat")
        # GM-locked tokens cannot be moved by players, only the GM can
        # patch them — but a locked token's owner can still toggle
        # status / hp if explicitly allowed (none of those are gated
        # by `locked`; lock only blocks position drift).
        if existing.get("locked") and (body.x is not None or body.y is not None):
            raise HTTPException(403, "Token is GM-locked — position cannot be changed")

    # Apply only the fields the caller actually sent.
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if not patch:
        return existing
    existing.update(patch)
    state["updated_at"] = now_iso()
    await db.battlemaps.replace_one({"session_id": sid}, state, upsert=True)
    await broadcast(sid, {"type": "map:token", "data": existing})
    return existing


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


# ───────────────────────── V6.25.48 — PC vitals snapshot ─────────────────────────
# Auto-fills battlemap token HP/EP rings from each linked character's
# live derived stats. Polled by the frontend (no need to wire HP
# broadcasts through every spend/damage code path) — cheap because we
# only look up the characters the map actually references.

# V6.25.51 — `_pc_vitals_for` consolidated into core/vitals_broadcast.
# Same heuristic; one source-of-truth so push (vitals_broadcast) and
# poll (this module) can never drift apart.
from core.vitals_broadcast import _pc_vitals_for  # noqa: E402


@router.get("/sessions/{sid}/map/vitals")
async def get_pc_vitals(sid: str, user: dict = Depends(get_current_user)):
    """Return {character_id: {hp_pct, ep_pct, hp_current, hp_max, ...}} for
    every PC token currently on this session's map. Polled by the
    Battlemap to keep token rings in sync with the character sheets
    (no per-route HP broadcast needed)."""
    sess, camp = await _load_session_with_camp(sid)
    if not _is_member(user, camp):
        raise HTTPException(403, "Not seated at this table")
    state = await _get_or_init_map(sid)
    char_ids = list({t.get("character_id") for t in state.get("tokens", [])
                     if t.get("character_id")})
    if not char_ids:
        return {"vitals": {}}
    chars = await db.characters.find(
        {"id": {"$in": char_ids}}, {"_id": 0},
    ).to_list(200)
    return {"vitals": {c["id"]: _pc_vitals_for(c) for c in chars}}


# ───────────────────── V6.25.50 — recap auto-vitals ─────────────────────
# Cross-pollinates Battlemap vitals into the LLM Voice-Recap pipeline.
# When the GM runs an auto-recap, the recap prompt can pull this
# snapshot to anchor lines like "Eli ended Round 5 at 22% HP" instead
# of guessing or omitting combat state. Read-only; no mutation.

@router.get("/sessions/{sid}/recap/auto-vitals")
async def recap_auto_vitals(sid: str,
                              user: dict = Depends(get_current_user)):
    """Return a recap-ready snapshot of every linked PC token's
    current vitals. Includes a `narrative` list of pre-formatted
    one-liners the LLM can splice directly into the recap prompt
    without any further processing.

    Shape:
        {
          "session_id": "...",
          "round": 5,                          # may be 0 if no combat
          "pcs": [
            {
              "character_id": "...",
              "name": "Eli",
              "hp_pct": 22, "hp_current": 11, "hp_max": 50,
              "ep_pct": 60, "ep_current": 24, "ep_max": 40,
              "status": ["Bleeding", "Spotlit"],
              "narrative": "Eli ended Round 5 at 22% HP and 60% EP — bleeding, spotlit."
            }, ...
          ],
          "summary": "Eli at 22% HP; Aurora untouched; Calenwë spent."
        }

    Members-only — read-gated to anyone seated at the table.
    """
    sess, camp = await _load_session_with_camp(sid)
    if not _is_member(user, camp):
        raise HTTPException(403, "Not seated at this table")
    state = await _get_or_init_map(sid)

    # Pull the current initiative round (set by the dice/initiative
    # endpoints). Falls back to 0 if no combat is currently running.
    round_no = int((sess or {}).get("current_round") or 0)

    # Walk the tokens that are bound to a character — markers and
    # unbound NPCs don't carry vitals.
    char_ids = list({t.get("character_id") for t in state.get("tokens", [])
                     if t.get("character_id") and t.get("kind", "pc") != "marker"})
    if not char_ids:
        return {"session_id": sid, "round": round_no,
                "pcs": [], "summary": "No PCs on the map this session."}

    chars = await db.characters.find(
        {"id": {"$in": char_ids}}, {"_id": 0},
    ).to_list(200)
    by_id = {c["id"]: c for c in chars}

    # Live status effects bound to those characters (manual + applied).
    eff_rows = await db.effects.find(
        {"session_id": sid, "active": True,
         "target_character_id": {"$in": char_ids}},
        {"_id": 0, "target_character_id": 1, "name": 1},
    ).to_list(500)
    by_char_status: dict = {}
    for e in eff_rows:
        by_char_status.setdefault(e["target_character_id"], []).append(e["name"])

    out_pcs = []
    short_lines = []
    for tok in state.get("tokens", []):
        cid = tok.get("character_id")
        if not cid or cid not in by_id:
            continue
        ch = by_id[cid]
        v = _pc_vitals_for(ch)
        status = sorted(set((tok.get("status") or []) + by_char_status.get(cid, [])))
        name = ch.get("name") or tok.get("label") or "Unnamed"

        # Build the narrative line for the LLM. Use natural ranges so
        # the recap doesn't sound clinical ("at 22% HP" reads better
        # than "with 11/50 HP" in a recap voice).
        round_clause = f"ended Round {round_no}" if round_no > 0 else "left the scene"
        status_clause = (" — " + ", ".join(s.lower() for s in status)) if status else ""
        narrative = (f"{name} {round_clause} at {v['hp_pct']}% HP "
                     f"and {v['ep_pct']}% EP{status_clause}.")

        out_pcs.append({
            "character_id": cid,
            "name": name,
            "hp_pct": v["hp_pct"], "hp_current": v["hp_current"], "hp_max": v["hp_max"],
            "ep_pct": v["ep_pct"], "ep_current": v["ep_current"], "ep_max": v["ep_max"],
            "status": status,
            "narrative": narrative,
        })

        # Compact one-liner for the summary string.
        if v["hp_pct"] <= 30:
            short_lines.append(f"{name} bloodied ({v['hp_pct']}% HP)")
        elif v["hp_pct"] <= 60:
            short_lines.append(f"{name} hurting ({v['hp_pct']}% HP)")
        elif v["ep_pct"] <= 25:
            short_lines.append(f"{name} drained ({v['ep_pct']}% EP)")
        else:
            short_lines.append(f"{name} steady")

    summary = "; ".join(short_lines) + "."
    return {
        "session_id": sid,
        "round": round_no,
        "pcs": out_pcs,
        "summary": summary,
    }
