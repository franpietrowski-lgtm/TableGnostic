"""Scene Switcher — V6.25.43.

GM-only segmentation of a live session into discrete "scenes" so that
recaps, PTT transcriptions, and chat messages can be grouped by
narrative beat instead of one continuous event.

Design rules (from the product owner):
  * No pre-defined scene catalogue. Each scene is created on the fly.
  * No editing UI. Once a scene is created and confirmed, its metadata
    is frozen for the duration of the session (no retcons).
  * GM-only action. Players see scene boundaries but cannot mutate them.
  * Closing a scene REQUIRES `confirmed=true` (click-to-confirm guard).
  * Each scene gets an id-slug `scene{N}-session{N}_{CampaignName}`
    that the recap engine uses as a section header.
  * If the GM set a `target_thread_id` (via PATCH on the scene, or via
    `default_target_thread_id` on the session at setup), the PTT pipeline
    auto-forwards each transcription into that thread plus the live chat.

Data model — `scenes` collection:

    {
      id:                  str (uuid)
      campaign_id:         str
      session_id:          str
      scene_no:            int                # 1-indexed per session
      name:                str                # short label (free text)
      slug:                str                # scene{N}-session{N}_{Camp}
      location_id:         str | null         # codex node (kind=location)
      location_label:      str | null         # cached title
      location_description:str | null         # cached short blurb
      target_thread_id:    str | null         # thread to mirror PTT/chat into
      participant_character_ids: [str]        # auto-collected from PTT
      gm_narration:        [ {text, ts} ]     # appended via PATCH
      chat_message_ids:    [str]              # ids of chat_logs in this scene
      voice_line_ids:      [str]              # ids of voice_lines in this scene
      status:              "active" | "closed"
      started_at:          iso str
      ended_at:            iso str | null
      created_by:          user id
    }

Sessions also gain two optional fields:
    default_target_thread_id  — fallback thread for new scenes
    current_scene_id          — pointer to the active scene (cached)
"""
from __future__ import annotations
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.bus import broadcast
from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["scenes"])


# ---------- helpers ---------------------------------------------------

async def _session_camp_or_404(sid: str) -> tuple:
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found.")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    return s, camp


def _is_gm(user: dict, camp: dict) -> bool:
    return user["id"] == camp.get("gm_id") or user.get("role") == "admin"


async def _seated_or_403(sid: str, user: dict) -> tuple:
    s, camp = await _session_camp_or_404(sid)
    if not (_is_gm(user, camp)
            or user["id"] in (camp.get("member_ids") or [])):
        raise HTTPException(403, "Not seated at this table.")
    return s, camp


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "campaign"


# ---------- models ----------------------------------------------------

class SceneCreateIn(BaseModel):
    name: str = Field("", max_length=120)
    location_id: Optional[str] = None
    adhoc_location_label: Optional[str] = Field(None, max_length=200)
    target_thread_id: Optional[str] = None


class SceneSetupPatchIn(BaseModel):
    """Limited setup patch — only callable while the scene is still
    `active`. Used right after creation to attach a location / thread
    target / cosmetic label before the first PTT line lands.
    """
    name: Optional[str] = None
    location_id: Optional[str] = None
    target_thread_id: Optional[str] = None


class SceneNarrationIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class SessionDefaultThreadIn(BaseModel):
    default_target_thread_id: Optional[str] = None


# ---------- endpoints -------------------------------------------------

@router.get("/sessions/{sid}/scenes")
async def list_scenes(sid: str, user: dict = Depends(get_current_user)):
    await _seated_or_403(sid, user)
    rows = await db.scenes.find(
        {"session_id": sid}, {"_id": 0},
    ).sort("scene_no", 1).to_list(500)
    return {"session_id": sid, "scenes": rows, "count": len(rows)}


@router.get("/sessions/{sid}/scenes/active")
async def active_scene(sid: str, user: dict = Depends(get_current_user)):
    await _seated_or_403(sid, user)
    row = await db.scenes.find_one(
        {"session_id": sid, "status": "active"}, {"_id": 0},
    )
    return {"scene": row}


@router.post("/sessions/{sid}/scenes")
async def create_scene(sid: str, body: SceneCreateIn,
                       user: dict = Depends(get_current_user)):
    """Start a new scene. GM only.

    If a prior scene is still `active` it is auto-closed (status →
    closed, ended_at = now). The new scene becomes `current_scene_id`
    on the session.
    """
    s, camp = await _session_camp_or_404(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM can switch scenes.")

    # Auto-close any still-active scene on this session.
    await db.scenes.update_many(
        {"session_id": sid, "status": "active"},
        {"$set": {"status": "closed", "ended_at": now_iso(),
                  "auto_closed": True}},
    )

    last = await db.scenes.find_one(
        {"session_id": sid}, {"_id": 0, "scene_no": 1},
        sort=[("scene_no", -1)],
    )
    next_no = (last or {}).get("scene_no", 0) + 1
    camp_slug = _slugify(camp.get("name") or "campaign")
    sess_no = s.get("session_no") or 1
    slug = f"scene{next_no}-session{sess_no}_{camp_slug}"

    # Optional: cache location label/description if a node was provided.
    loc_label = None
    loc_desc = None
    if body.location_id:
        node = await db.nodes.find_one(
            {"id": body.location_id, "campaign_id": s["campaign_id"]},
            {"_id": 0, "title": 1, "content": 1, "type": 1, "fields": 1},
        )
        if not node or node.get("type") != "location":
            raise HTTPException(400, "location_id must reference a "
                                     "location node in this campaign.")
        loc_label = node.get("title")
        # Prefer the explicit `description` field if the LLM extractor
        # populated one; else use a snippet of the content.
        f = node.get("fields") or {}
        loc_desc = (f.get("description") or node.get("content") or "")[:600]
    elif body.adhoc_location_label:
        # V6.25.44 — on-the-fly custom location (no codex node). The
        # scene records the label only; nothing is created in the codex.
        loc_label = body.adhoc_location_label.strip()[:200]
        loc_desc = None

    # Fall back to the session's default thread if none provided.
    target_thread = body.target_thread_id or s.get("default_target_thread_id")

    scene = {
        "id": new_id(),
        "campaign_id": s["campaign_id"],
        "session_id": sid,
        "scene_no": next_no,
        "name": (body.name or f"Scene {next_no}")[:120],
        "slug": slug,
        "location_id": body.location_id,
        "location_label": loc_label,
        "location_description": loc_desc,
        "target_thread_id": target_thread,
        "participant_character_ids": [],
        "gm_narration": [],
        "chat_message_ids": [],
        "voice_line_ids": [],
        "status": "active",
        "started_at": now_iso(),
        "ended_at": None,
        "created_by": user["id"],
    }
    await db.scenes.insert_one(dict(scene))
    scene.pop("_id", None)

    # Cache pointer on the session for fast lookup from PTT / chat paths.
    await db.sessions.update_one(
        {"id": sid},
        {"$set": {"current_scene_id": scene["id"]}},
    )

    # Broadcast to every connected client so PTT button etc. can re-render.
    await broadcast(f"session:{sid}", {"type": "scene:start", "data": scene})

    # Also drop a system chat marker so the timeline shows the scene cut.
    sys_msg = {
        "id": new_id(),
        "session_id": sid,
        "user_id": "system",
        "user_name": "LOREMASTER",
        "kind": "system",
        "message": (f"🎬 **{scene['name']}** — `{scene['slug']}`"
                    + (f"\n📍 _{loc_label}_" if loc_label else "")),
        "scene_id": scene["id"],
        "scene_slug": scene["slug"],
        "created_at": now_iso(),
    }
    await db.chat_logs.insert_one(dict(sys_msg))
    sys_msg.pop("_id", None)
    await broadcast(sid, {"type": "chat", "data": sys_msg})

    return {"scene": scene}


@router.patch("/sessions/{sid}/scenes/{scene_id}/setup")
async def patch_scene_setup(sid: str, scene_id: str,
                            body: SceneSetupPatchIn,
                            user: dict = Depends(get_current_user)):
    """GM-only, ACTIVE-scene-only metadata setup.

    Lets the GM attach the location / target thread / label right after
    creation. Once the scene is closed this endpoint returns 409.
    """
    s, camp = await _session_camp_or_404(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM can edit scenes.")
    sc = await db.scenes.find_one({"id": scene_id, "session_id": sid},
                                  {"_id": 0})
    if not sc:
        raise HTTPException(404, "Scene not found.")
    if sc.get("status") != "active":
        raise HTTPException(409, "Scene already closed; no edits allowed "
                                 "(no retcons).")
    upd: dict = {}
    if body.name is not None:
        upd["name"] = body.name[:120]
    if body.target_thread_id is not None:
        upd["target_thread_id"] = body.target_thread_id
    if body.location_id is not None:
        node = await db.nodes.find_one(
            {"id": body.location_id, "campaign_id": s["campaign_id"]},
            {"_id": 0, "title": 1, "content": 1, "type": 1, "fields": 1},
        )
        if not node or node.get("type") != "location":
            raise HTTPException(400, "location_id must reference a "
                                     "location node in this campaign.")
        upd["location_id"] = body.location_id
        upd["location_label"] = node.get("title")
        f = node.get("fields") or {}
        upd["location_description"] = (f.get("description") or
                                       node.get("content") or "")[:600]
    if not upd:
        return {"scene": sc}
    await db.scenes.update_one({"id": scene_id}, {"$set": upd})
    out = await db.scenes.find_one({"id": scene_id}, {"_id": 0})
    await broadcast(f"session:{sid}", {"type": "scene:update", "data": out})
    return {"scene": out}


@router.post("/sessions/{sid}/scenes/{scene_id}/narration")
async def append_narration(sid: str, scene_id: str,
                           body: SceneNarrationIn,
                           user: dict = Depends(get_current_user)):
    """GM appends a narration beat to the ACTIVE scene's buffer.

    Stored on the scene only (does NOT also broadcast as chat — chat
    happens via the regular /chat route which now also tags scene_id).
    """
    s, camp = await _session_camp_or_404(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM can add scene narration.")
    sc = await db.scenes.find_one({"id": scene_id, "session_id": sid},
                                  {"_id": 0})
    if not sc:
        raise HTTPException(404, "Scene not found.")
    if sc.get("status") != "active":
        raise HTTPException(409, "Scene is closed.")
    entry = {"text": body.text, "ts": now_iso()}
    await db.scenes.update_one(
        {"id": scene_id},
        {"$push": {"gm_narration": entry}},
    )
    return {"ok": True, "appended": entry}


@router.post("/sessions/{sid}/scenes/{scene_id}/close")
async def close_scene(sid: str, scene_id: str, confirmed: bool = False,
                      user: dict = Depends(get_current_user)):
    """GM closes the scene. `confirmed=true` REQUIRED — this is the
    click-to-confirm guard against premature scene slicing.
    """
    s, camp = await _session_camp_or_404(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM can close scenes.")
    if not confirmed:
        raise HTTPException(412, "confirmed=true is required (click-to-"
                                 "confirm guard).")
    sc = await db.scenes.find_one({"id": scene_id, "session_id": sid},
                                  {"_id": 0})
    if not sc:
        raise HTTPException(404, "Scene not found.")
    if sc.get("status") == "closed":
        return {"scene": sc, "already_closed": True}
    await db.scenes.update_one(
        {"id": scene_id},
        {"$set": {"status": "closed", "ended_at": now_iso(),
                  "closed_by": user["id"], "auto_closed": False}},
    )
    await db.sessions.update_one(
        {"id": sid, "current_scene_id": scene_id},
        {"$set": {"current_scene_id": None}},
    )
    out = await db.scenes.find_one({"id": scene_id}, {"_id": 0})
    await broadcast(f"session:{sid}", {"type": "scene:end", "data": out})

    sys_msg = {
        "id": new_id(),
        "session_id": sid,
        "user_id": "system",
        "user_name": "LOREMASTER",
        "kind": "system",
        "message": f"🎬✂︎ **End of {out['name']}** — _{out['slug']}_",
        "scene_id": scene_id,
        "scene_slug": out["slug"],
        "created_at": now_iso(),
    }
    await db.chat_logs.insert_one(dict(sys_msg))
    sys_msg.pop("_id", None)
    await broadcast(sid, {"type": "chat", "data": sys_msg})
    return {"scene": out}


@router.patch("/sessions/{sid}/default-thread")
async def patch_default_thread(sid: str, body: SessionDefaultThreadIn,
                               user: dict = Depends(get_current_user)):
    """GM-only — set/clear the session-wide default thread that new
    scenes (and PTT lines outside any scene) mirror into.
    """
    s, camp = await _session_camp_or_404(sid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM can change session settings.")
    await db.sessions.update_one(
        {"id": sid},
        {"$set": {"default_target_thread_id": body.default_target_thread_id}},
    )
    return {"ok": True, "default_target_thread_id": body.default_target_thread_id}


# Helper exposed for other route modules (voice_lines, chat) so they
# can tag inbound rows with the active scene + optionally mirror into a
# thread without duplicating the lookup.
async def attach_active_scene(sid: str) -> Optional[dict]:
    """Return the currently-active scene dict (or None)."""
    s = await db.sessions.find_one({"id": sid},
                                   {"_id": 0, "current_scene_id": 1,
                                    "default_target_thread_id": 1})
    if not s:
        return None
    csid = s.get("current_scene_id")
    if csid:
        sc = await db.scenes.find_one({"id": csid, "status": "active"},
                                      {"_id": 0})
        if sc:
            return sc
    return None


async def attach_message_to_scene(sid: str, message_id: str,
                                  voice_line_id: Optional[str] = None,
                                  character_id: Optional[str] = None) -> Optional[str]:
    """Tag a chat / voice line to the active scene if any.

    Returns the active scene's id (or None). Also adds the character id
    to participant_character_ids if not already present.
    """
    sc = await attach_active_scene(sid)
    if not sc:
        return None
    upd: dict = {}
    if message_id:
        upd.setdefault("$push", {})["chat_message_ids"] = message_id
    if voice_line_id:
        push = upd.setdefault("$push", {})
        # Mongo: can't push to two arrays with same $push key; need $each merge.
        if "chat_message_ids" in push:
            # Use two updates to keep this simple.
            await db.scenes.update_one({"id": sc["id"]}, {"$push": push})
            upd = {}
        if voice_line_id:
            upd.setdefault("$push", {})["voice_line_ids"] = voice_line_id
    if character_id:
        upd.setdefault("$addToSet", {})["participant_character_ids"] = character_id
    if upd:
        await db.scenes.update_one({"id": sc["id"]}, upd)
    return sc["id"]
