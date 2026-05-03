"""V6.19 — GM Surprise Bag + Scene-Break Card.

Atelier · Workshop fixture for table delight: a queryable bag of
surprise complications and scene-break ritual cards. GM seeds the bag
with custom entries (system-tagged), then draws one at the table either
manually or via a 'Random pull' button on the Director's Console.

Endpoints
─────────
  GET    /api/campaigns/{cid}/surprise-bag
  POST   /api/campaigns/{cid}/surprise-bag           (create entry)
  PATCH  /api/campaigns/{cid}/surprise-bag/{eid}     (edit entry)
  DELETE /api/campaigns/{cid}/surprise-bag/{eid}
  POST   /api/campaigns/{cid}/surprise-bag/draw      (random draw)
  GET    /api/campaigns/{cid}/scene-break-cards
  POST   /api/campaigns/{cid}/scene-break-cards      (create card)
  POST   /api/campaigns/{cid}/scene-break-cards/draw (random draw)

Storage: Mongo `campaign_surprise_bag` and `campaign_scene_breaks`.
"""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["surprise-bag", "scene-break"])


# ─── Helpers ────────────────────────────────────────────────────────────

async def _post_to_active_pbp(cid: str, user: dict, line: str):
    """V6.20 — Post a /system line into the active session's PBP channel.

    Looks up the most recent in-progress session for the campaign and
    inserts a system-kind chat log entry. Silent no-op if no session is
    active (so Workshop draws stay usable in pre-prep).
    """
    try:
        active = await db.sessions.find_one(
            {"campaign_id": cid, "status": {"$in": ["in_progress", "scheduled", None]}},
            {"_id": 0},
            sort=[("created_at", -1)],
        )
        if not active:
            return False
        await db.chat_logs.insert_one({
            "id": new_id(), "session_id": active["id"],
            "message": line,
            "kind": "system", "user_id": "system",
            "user_name": "WORKSHOP",
            "pinned": False,
            "created_at": now_iso(),
        })
        return True
    except Exception as e:
        print(f"[surprise-bag pbp post] {e}")
        return False



async def _campaign_or_404(cid: str, user: dict, gm_only: bool = False):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    is_gm = user["id"] == camp["gm_id"] or user.get("role") == "admin"
    if gm_only and not is_gm:
        raise HTTPException(403, "GM/admin only.")
    if not gm_only:
        if (user["id"] != camp["gm_id"]
            and user["id"] not in (camp.get("member_ids") or [])
            and user.get("role") != "admin"):
            raise HTTPException(403, "Not a table member.")
    return camp, is_gm


# ─── GM Surprise Bag ────────────────────────────────────────────────────

class SurpriseEntryIn(BaseModel):
    """A single surprise / complication seed."""
    title: str = Field(min_length=1, max_length=120)
    blurb: str = ""
    category: str = "complication"  # complication / boon / twist / mood
    weight: int = 1                  # draw weight (1-10)
    tags: List[str] = []
    system_id: Optional[str] = None  # tag for system-specific complications
    use_count_max: int = 0  # 0 = unlimited; otherwise removes after N draws


@router.get("/campaigns/{cid}/surprise-bag")
async def list_surprise_bag(cid: str,
                              user: dict = Depends(get_current_user)):
    await _campaign_or_404(cid, user)
    cur = db.campaign_surprise_bag.find({"campaign_id": cid}, {"_id": 0})
    rows = await cur.to_list(length=2000)
    rows.sort(key=lambda r: (r.get("category"), r.get("title")))
    return {"campaign_id": cid, "entries": rows, "total": len(rows)}


@router.post("/campaigns/{cid}/surprise-bag")
async def create_surprise_entry(
    cid: str, body: SurpriseEntryIn,
    user: dict = Depends(get_current_user),
):
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "title": body.title.strip(),
        "blurb": body.blurb.strip(),
        "category": body.category.strip().lower(),
        "weight": max(1, min(10, int(body.weight or 1))),
        "tags": list(body.tags or []),
        "system_id": body.system_id,
        "use_count_max": int(body.use_count_max or 0),
        "use_count": 0,
        "created_by": user.get("name"),
        "created_at": now_iso(),
    }
    await db.campaign_surprise_bag.insert_one(doc)
    doc.pop("_id", None)
    return {"ok": True, "entry": doc}


class SurpriseEntryPatch(BaseModel):
    title: Optional[str] = None
    blurb: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[int] = None
    tags: Optional[List[str]] = None
    system_id: Optional[str] = None
    use_count_max: Optional[int] = None


@router.patch("/campaigns/{cid}/surprise-bag/{eid}")
async def patch_surprise_entry(
    cid: str, eid: str, body: SurpriseEntryPatch,
    user: dict = Depends(get_current_user),
):
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    upd: Dict[str, Any] = {"updated_at": now_iso()}
    for k in ("title", "blurb", "category", "tags", "system_id"):
        v = getattr(body, k)
        if v is not None:
            upd[k] = v
    if body.weight is not None:
        upd["weight"] = max(1, min(10, int(body.weight)))
    if body.use_count_max is not None:
        upd["use_count_max"] = int(body.use_count_max)
    res = await db.campaign_surprise_bag.update_one(
        {"id": eid, "campaign_id": cid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "Entry not found")
    return {"ok": True}


@router.delete("/campaigns/{cid}/surprise-bag/{eid}")
async def delete_surprise_entry(
    cid: str, eid: str, user: dict = Depends(get_current_user),
):
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    res = await db.campaign_surprise_bag.delete_one(
        {"id": eid, "campaign_id": cid})
    return {"ok": True, "deleted": res.deleted_count}


class DrawIn(BaseModel):
    category: Optional[str] = None
    system_id: Optional[str] = None
    tags: Optional[List[str]] = None  # all-of filter


@router.post("/campaigns/{cid}/surprise-bag/draw")
async def draw_surprise(
    cid: str, body: DrawIn, user: dict = Depends(get_current_user),
):
    """Weighted random draw from the bag with optional category /
    system_id / tag filters. GM/admin only — players don't pull their
    own surprises.
    """
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    q: Dict[str, Any] = {"campaign_id": cid}
    if body.category:
        q["category"] = body.category.lower()
    if body.system_id:
        q["system_id"] = body.system_id
    cur = db.campaign_surprise_bag.find(q, {"_id": 0})
    rows = await cur.to_list(length=2000)
    if body.tags:
        wanted = set(body.tags)
        rows = [r for r in rows if wanted.issubset(set(r.get("tags") or []))]
    # Filter exhausted entries.
    rows = [r for r in rows
            if not (r.get("use_count_max") and r.get("use_count", 0) >= r["use_count_max"])]
    if not rows:
        raise HTTPException(404, "No matching entries in the bag.")
    weights = [max(1, int(r.get("weight") or 1)) for r in rows]
    pick = random.choices(rows, weights=weights, k=1)[0]
    # Increment use_count for tracking & exhaustion.
    await db.campaign_surprise_bag.update_one(
        {"id": pick["id"]},
        {"$inc": {"use_count": 1},
         "$set": {"last_drawn_at": now_iso(),
                  "last_drawn_by": user.get("name")}},
    )
    # V6.20 — auto-post the draw into the active session's PBP channel.
    line = (
        f'🎲 GM drew "{pick.get("title", "Untitled")}" '
        f'({pick.get("category", "surprise")}): '
        f'{pick.get("blurb", "—")}'
    )
    posted = await _post_to_active_pbp(cid, user, line)
    return {"ok": True, "drawn": pick, "pool_size": len(rows),
             "posted_to_session": posted}


# ─── Scene-Break Cards ──────────────────────────────────────────────────

class SceneBreakIn(BaseModel):
    """A scene-break ritual card — flavour-text the GM reads aloud
    before a major shift in pacing/tone."""
    title: str = Field(min_length=1, max_length=120)
    body: str = ""
    mood: str = "transition"  # transition / cliffhanger / cooldown / arrival
    music_cue: str = ""        # optional Spotify uri / room link / etc.


@router.get("/campaigns/{cid}/scene-break-cards")
async def list_scene_breaks(cid: str,
                              user: dict = Depends(get_current_user)):
    await _campaign_or_404(cid, user)
    rows = await db.campaign_scene_breaks.find(
        {"campaign_id": cid}, {"_id": 0}).to_list(length=500)
    rows.sort(key=lambda r: (r.get("mood"), r.get("title")))
    return {"campaign_id": cid, "cards": rows, "total": len(rows)}


@router.post("/campaigns/{cid}/scene-break-cards")
async def create_scene_break(
    cid: str, body: SceneBreakIn,
    user: dict = Depends(get_current_user),
):
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "title": body.title.strip(),
        "body": body.body.strip(),
        "mood": body.mood.strip().lower(),
        "music_cue": body.music_cue.strip(),
        "created_by": user.get("name"),
        "created_at": now_iso(),
    }
    await db.campaign_scene_breaks.insert_one(doc)
    doc.pop("_id", None)
    return {"ok": True, "card": doc}


@router.delete("/campaigns/{cid}/scene-break-cards/{eid}")
async def delete_scene_break(
    cid: str, eid: str, user: dict = Depends(get_current_user),
):
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    res = await db.campaign_scene_breaks.delete_one(
        {"id": eid, "campaign_id": cid})
    return {"ok": True, "deleted": res.deleted_count}


class SceneBreakDrawIn(BaseModel):
    mood: Optional[str] = None


@router.post("/campaigns/{cid}/scene-break-cards/draw")
async def draw_scene_break(
    cid: str, body: SceneBreakDrawIn,
    user: dict = Depends(get_current_user),
):
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    q: Dict[str, Any] = {"campaign_id": cid}
    if body.mood:
        q["mood"] = body.mood.lower()
    rows = await db.campaign_scene_breaks.find(q, {"_id": 0}).to_list(length=500)
    if not rows:
        raise HTTPException(404, "No scene-break cards match.")
    pick = random.choice(rows)
    # V6.20 — auto-post the draw into the active session's PBP channel.
    music = f' ♪ {pick.get("music_cue")}' if pick.get("music_cue") else ""
    line = (
        f'🎴 Scene break · {pick.get("mood", "transition")} · '
        f'{pick.get("title", "Untitled")}\n\n{pick.get("body", "")}{music}'
    )
    posted = await _post_to_active_pbp(cid, user, line)
    return {"ok": True, "drawn": pick, "pool_size": len(rows),
             "posted_to_session": posted}


# ─── Bulk seed shortcut (helper for first-time GM onboarding) ───────────

DEFAULT_SCENE_BREAKS = [
    {"title": "Rain Break", "mood": "transition",
     "body": "The scene fades; let one player describe what their character watches as the rain begins. Pause. Then forward."},
    {"title": "Cliffhanger", "mood": "cliffhanger",
     "body": "We end here — but not because we're done. Each player in one sentence: what does your character feel right now?"},
    {"title": "Cooldown Tea", "mood": "cooldown",
     "body": "Take 5 real minutes. The party returns to camp / inn / cockpit. No mechanics. Just describe one quiet moment."},
    {"title": "Arrival", "mood": "arrival",
     "body": "The new place. GM reads the establishing shot in three short sentences. Then party goes around the table for first impressions."},
]

DEFAULT_SURPRISE_ENTRIES = [
    {"title": "Sudden weather change", "blurb": "Rain becomes sleet, sun becomes overcast — affects ranged attacks for 1 round.", "category": "twist", "weight": 3, "tags": ["weather"]},
    {"title": "Old contact reappears", "blurb": "An NPC from the party's past walks into the scene at the worst moment.", "category": "twist", "weight": 2, "tags": ["social"]},
    {"title": "Equipment hiccup", "blurb": "One PC's signature gear malfunctions briefly — narrate the embarrassing moment.", "category": "complication", "weight": 4, "tags": ["mechanical"]},
    {"title": "A small kindness", "blurb": "A passing stranger offers help, food, or a ride. No strings (this time).", "category": "boon", "weight": 2, "tags": ["social"]},
    {"title": "Unexpected ally", "blurb": "An NPC the party expected to fight reveals a shared interest.", "category": "twist", "weight": 1, "tags": ["social"]},
    {"title": "Mood shift", "blurb": "Music in the room changes; the lighting feels different. Describe how the scene's tone has shifted.", "category": "mood", "weight": 5, "tags": ["atmosphere"]},
]


@router.post("/campaigns/{cid}/surprise-bag/seed")
async def seed_surprise_bag(
    cid: str, user: dict = Depends(get_current_user),
):
    """One-shot seeder for the GM Surprise Bag. Adds 6 generic entries
    if the bag is empty; no-op if already populated."""
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    existing = await db.campaign_surprise_bag.count_documents({"campaign_id": cid})
    if existing > 0:
        return {"ok": True, "skipped": True, "existing_count": existing}
    inserted = 0
    for entry in DEFAULT_SURPRISE_ENTRIES:
        doc = {"id": new_id(), "campaign_id": cid,
                "system_id": None, "use_count_max": 0, "use_count": 0,
                "created_by": user.get("name"), "created_at": now_iso(),
                **entry}
        await db.campaign_surprise_bag.insert_one(doc)
        inserted += 1
    return {"ok": True, "inserted": inserted}


@router.post("/campaigns/{cid}/scene-break-cards/seed")
async def seed_scene_breaks(
    cid: str, user: dict = Depends(get_current_user),
):
    """One-shot seeder for scene-break cards. Adds 4 generic mood
    cards if the deck is empty; no-op if already populated."""
    _, _ = await _campaign_or_404(cid, user, gm_only=True)
    existing = await db.campaign_scene_breaks.count_documents({"campaign_id": cid})
    if existing > 0:
        return {"ok": True, "skipped": True, "existing_count": existing}
    inserted = 0
    for card in DEFAULT_SCENE_BREAKS:
        doc = {"id": new_id(), "campaign_id": cid,
                "music_cue": "", "created_by": user.get("name"),
                "created_at": now_iso(), **card}
        await db.campaign_scene_breaks.insert_one(doc)
        inserted += 1
    return {"ok": True, "inserted": inserted}
