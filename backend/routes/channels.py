"""Discord-style PBP (play-by-post) channels — per-campaign text channels
with threads, markdown bodies, reactions, pinning, attachments, and inline
slash-commands (/roll, /whisper, /me).

Storage:
    campaign_channels  { id, campaign_id, name, kind: "text"|"forum",
                         topic, position, archived, created_at }
    threads            { id, channel_id, parent_msg_id?, name, created_by,
                         created_at, archived, last_msg_at }
    channel_msgs       { id, channel_id, thread_id?, author_id, author_name,
                         body (markdown), kind: "msg"|"roll"|"system",
                         attachments[], reactions[{emoji,uids[]}], pinned,
                         mention_uids[], slash_meta?, created_at, edited_at? }

WebSocket broadcasts (re-uses session bus, scoped by campaign room
"campaign:{cid}"):
    channel:msg            new or edited message
    channel:msg-delete     { id }
    channel:reaction       { msg_id, emoji, uids[] }
    channel:pin            { msg_id, pinned: bool }
    channel:thread         new or archived thread
    channel:typing         (ephemeral, future)

Notes
- Markdown is stored AS-IS; the frontend renders.
- /roll <notation> is parsed inline and produces a kind=\"roll\" message.
- Mentions are extracted at write time (@username → user-id) and stored
  on the message so the frontend can highlight them.
"""
import re
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.bus import broadcast
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["channels"])


# ─────────────────────────── Pydantic models ───────────────────────────

class ChannelIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    kind: Literal["text", "forum"] = "text"
    topic: str = ""
    position: int = 0


class ChannelEditIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    topic: Optional[str] = None
    position: Optional[int] = None
    archived: Optional[bool] = None


class ThreadIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    parent_msg_id: Optional[str] = None


class AttachmentIn(BaseModel):
    name: str
    url: str
    kind: str = "file"  # "file" | "image" | "audio"
    size: int = 0


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=8000)
    thread_id: Optional[str] = None
    attachments: List[AttachmentIn] = []


class MessageEditIn(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class ReactionIn(BaseModel):
    emoji: str = Field(min_length=1, max_length=16)


# ─────────────────────────── Helpers ───────────────────────────

async def _camp_or_403(cid: str, user: dict, gm_only: bool = False) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    is_gm = camp["gm_id"] == user["id"] or user.get("role") == "admin"
    is_member = is_gm or user["id"] in camp.get("member_ids", [])
    if not is_member:
        raise HTTPException(403, "Not seated at this table")
    if gm_only and not is_gm:
        raise HTTPException(403, "GM only")
    return camp


async def _channel_or_403(chid: str, user: dict, gm_only: bool = False) -> tuple:
    ch = await db.campaign_channels.find_one({"id": chid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Channel not found")
    camp = await _camp_or_403(ch["campaign_id"], user, gm_only=gm_only)
    return ch, camp


_MENTION_RE = re.compile(r"@([A-Za-z0-9_-]{2,40})")
_SLASH_ROLL_RE = re.compile(r"^/roll\s+(.+)$", re.IGNORECASE)
_SLASH_ME_RE = re.compile(r"^/me\s+(.+)$", re.IGNORECASE)
_SLASH_WHISPER_RE = re.compile(r"^/w(?:hisper)?\s+@([A-Za-z0-9_-]+)\s+(.+)$", re.IGNORECASE)


async def _resolve_mentions(camp: dict, body: str) -> List[str]:
    """Find @handles in the body and resolve them to user-ids the campaign knows."""
    handles = set(m.group(1).lower() for m in _MENTION_RE.finditer(body))
    if not handles:
        return []
    member_ids = list(set([camp["gm_id"]] + camp.get("member_ids", [])))
    rows = await db.users.find(
        {"id": {"$in": member_ids}},
        {"_id": 0, "id": 1, "name": 1, "email": 1},
    ).to_list(50)
    out = []
    for u in rows:
        nm = (u.get("name") or "").lower().replace(" ", "_")
        em = (u.get("email") or "").split("@")[0].lower()
        if nm in handles or em in handles:
            out.append(u["id"])
    return out


def _parse_slash(body: str) -> Dict[str, Any]:
    """Detect a leading slash-command. Returns {kind, ...} or {} if none."""
    body = body.strip()
    m = _SLASH_ROLL_RE.match(body)
    if m:
        return {"kind": "roll", "notation": m.group(1).strip()}
    m = _SLASH_ME_RE.match(body)
    if m:
        return {"kind": "emote", "text": m.group(1).strip()}
    m = _SLASH_WHISPER_RE.match(body)
    if m:
        return {"kind": "whisper", "to_handle": m.group(1).lower(), "text": m.group(2).strip()}
    return {}


def _camp_room(cid: str) -> str:
    """WS room id used to scope campaign-wide channel broadcasts.
    The session bus accepts arbitrary room keys; we re-use the existing
    Bus by namespacing under "campaign:{cid}" rather than session ids."""
    return f"campaign:{cid}"


# ─────────────────────────── Channels ───────────────────────────

@router.get("/campaigns/{cid}/channels")
async def list_channels(cid: str, user: dict = Depends(get_current_user)):
    await _camp_or_403(cid, user)
    rows = await db.campaign_channels.find(
        {"campaign_id": cid, "archived": {"$ne": True}}, {"_id": 0},
    ).sort([("position", 1), ("created_at", 1)]).to_list(200)
    if not rows:
        # Auto-create a default "tavern" text channel on first read so a
        # fresh campaign always has somewhere to start a conversation.
        default = {
            "id": new_id(), "campaign_id": cid, "name": "tavern",
            "kind": "text", "topic": "Open conversation. /roll works here.",
            "position": 0, "archived": False, "created_at": now_iso(),
        }
        await db.campaign_channels.insert_one(default)
        rows = [sanitize(default)]
    return rows


@router.post("/campaigns/{cid}/channels")
async def create_channel(cid: str, body: ChannelIn,
                         user: dict = Depends(get_current_user)):
    await _camp_or_403(cid, user, gm_only=True)
    doc = {**body.model_dump(), "id": new_id(), "campaign_id": cid,
           "archived": False, "created_at": now_iso()}
    await db.campaign_channels.insert_one(doc)
    return sanitize(doc)


@router.put("/channels/{chid}")
async def edit_channel(chid: str, body: ChannelEditIn,
                       user: dict = Depends(get_current_user)):
    ch, _ = await _channel_or_403(chid, user, gm_only=True)
    upd = {k: v for k, v in body.model_dump().items() if v is not None}
    if upd:
        upd["updated_at"] = now_iso()
        await db.campaign_channels.update_one({"id": chid}, {"$set": upd})
    return {**ch, **upd}


@router.delete("/channels/{chid}")
async def delete_channel(chid: str, user: dict = Depends(get_current_user)):
    ch, _ = await _channel_or_403(chid, user, gm_only=True)
    await db.campaign_channels.delete_one({"id": chid})
    await db.channel_msgs.delete_many({"channel_id": chid})
    await db.threads.delete_many({"channel_id": chid})
    return {"ok": True}


# ─────────────────────────── Threads ───────────────────────────

@router.get("/channels/{chid}/threads")
async def list_threads(chid: str, user: dict = Depends(get_current_user)):
    await _channel_or_403(chid, user)
    rows = await db.threads.find({"channel_id": chid}, {"_id": 0}).sort("last_msg_at", -1).to_list(200)
    return rows


@router.post("/channels/{chid}/threads")
async def create_thread(chid: str, body: ThreadIn,
                        user: dict = Depends(get_current_user)):
    ch, camp = await _channel_or_403(chid, user)
    doc = {
        "id": new_id(), "channel_id": chid, "campaign_id": ch["campaign_id"],
        "parent_msg_id": body.parent_msg_id, "name": body.name.strip(),
        "created_by": user["id"], "created_by_name": user["name"],
        "created_at": now_iso(), "last_msg_at": now_iso(),
        "archived": False,
    }
    await db.threads.insert_one(doc)
    await broadcast(_camp_room(camp["id"]), {"type": "channel:thread", "data": sanitize(doc)})
    return sanitize(doc)


# ─────────────────────────── Messages ───────────────────────────

@router.get("/channels/{chid}/messages")
async def list_messages(chid: str, thread_id: Optional[str] = None,
                        user: dict = Depends(get_current_user)):
    await _channel_or_403(chid, user)
    q: Dict[str, Any] = {"channel_id": chid}
    q["thread_id"] = thread_id  # explicit None matches root channel posts
    rows = await db.channel_msgs.find(q, {"_id": 0}).sort("created_at", 1).to_list(500)
    return rows


@router.post("/channels/{chid}/messages")
async def post_message(chid: str, body: MessageIn,
                       user: dict = Depends(get_current_user)):
    ch, camp = await _channel_or_403(chid, user)
    if body.thread_id:
        th = await db.threads.find_one({"id": body.thread_id}, {"_id": 0})
        if not th or th["channel_id"] != chid:
            raise HTTPException(404, "Thread not found")

    text = body.body.strip()
    slash = _parse_slash(text)
    mention_uids = await _resolve_mentions(camp, text)

    doc = {
        "id": new_id(), "channel_id": chid, "thread_id": body.thread_id,
        "campaign_id": camp["id"],
        "author_id": user["id"], "author_name": user["name"],
        "body": text, "kind": "msg",
        "attachments": [a.model_dump() for a in body.attachments],
        "reactions": [], "pinned": False,
        "mention_uids": mention_uids,
        "slash_meta": slash or None,
        "created_at": now_iso(),
    }

    # Server-side dice expansion for /roll commands (so the result is
    # canonical and survives client refresh).
    if slash.get("kind") == "roll":
        from routes.sessions import roll_dice  # local import: avoids cycle
        try:
            result = roll_dice(slash["notation"])
            doc["kind"] = "roll"
            doc["slash_meta"] = {**slash, "result": result}
        except HTTPException:
            doc["slash_meta"] = {**slash, "error": "Invalid dice notation"}

    await db.channel_msgs.insert_one(doc)
    if body.thread_id:
        await db.threads.update_one(
            {"id": body.thread_id},
            {"$set": {"last_msg_at": doc["created_at"]}},
        )
    await broadcast(_camp_room(camp["id"]),
                    {"type": "channel:msg", "data": sanitize(doc)})
    return sanitize(doc)


@router.put("/messages/{mid}")
async def edit_message(mid: str, body: MessageEditIn,
                       user: dict = Depends(get_current_user)):
    msg = await db.channel_msgs.find_one({"id": mid}, {"_id": 0})
    if not msg:
        raise HTTPException(404, "Message not found")
    if msg["author_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the author may edit")
    new_text = body.body.strip()
    await db.channel_msgs.update_one(
        {"id": mid},
        {"$set": {"body": new_text, "edited_at": now_iso()}},
    )
    msg["body"] = new_text
    msg["edited_at"] = now_iso()
    await broadcast(_camp_room(msg["campaign_id"]),
                    {"type": "channel:msg", "data": sanitize(msg)})
    return sanitize(msg)


@router.delete("/messages/{mid}")
async def delete_message(mid: str, user: dict = Depends(get_current_user)):
    msg = await db.channel_msgs.find_one({"id": mid}, {"_id": 0})
    if not msg:
        raise HTTPException(404, "Message not found")
    camp = await db.campaigns.find_one({"id": msg["campaign_id"]}, {"_id": 0})
    is_gm = camp and (camp["gm_id"] == user["id"] or user.get("role") == "admin")
    if msg["author_id"] != user["id"] and not is_gm:
        raise HTTPException(403, "Only the author or the GM may delete")
    await db.channel_msgs.delete_one({"id": mid})
    await broadcast(_camp_room(msg["campaign_id"]),
                    {"type": "channel:msg-delete", "data": {"id": mid}})
    return {"ok": True}


@router.post("/messages/{mid}/reactions")
async def toggle_reaction(mid: str, body: ReactionIn,
                          user: dict = Depends(get_current_user)):
    msg = await db.channel_msgs.find_one({"id": mid}, {"_id": 0})
    if not msg:
        raise HTTPException(404, "Message not found")
    await _camp_or_403(msg["campaign_id"], user)  # member check

    reactions = msg.get("reactions") or []
    entry = next((r for r in reactions if r["emoji"] == body.emoji), None)
    if entry:
        if user["id"] in entry["uids"]:
            entry["uids"] = [u for u in entry["uids"] if u != user["id"]]
        else:
            entry["uids"].append(user["id"])
        if not entry["uids"]:
            reactions = [r for r in reactions if r["emoji"] != body.emoji]
    else:
        reactions.append({"emoji": body.emoji, "uids": [user["id"]]})

    await db.channel_msgs.update_one({"id": mid}, {"$set": {"reactions": reactions}})
    payload = {"msg_id": mid, "emoji": body.emoji,
               "reactions": reactions}
    await broadcast(_camp_room(msg["campaign_id"]),
                    {"type": "channel:reaction", "data": payload})
    return payload


@router.post("/messages/{mid}/pin")
async def toggle_pin(mid: str, user: dict = Depends(get_current_user)):
    msg = await db.channel_msgs.find_one({"id": mid}, {"_id": 0})
    if not msg:
        raise HTTPException(404, "Message not found")
    await _camp_or_403(msg["campaign_id"], user, gm_only=True)
    new_state = not bool(msg.get("pinned"))
    await db.channel_msgs.update_one({"id": mid}, {"$set": {"pinned": new_state}})
    await broadcast(_camp_room(msg["campaign_id"]),
                    {"type": "channel:pin", "data": {"msg_id": mid, "pinned": new_state}})
    return {"id": mid, "pinned": new_state}
