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
from core.vitals_broadcast import broadcast_character_vitals  # V6.25.50
# V6.25.51 — Macro grammar resolver extracted to core/macros.py.
# Keep the local _expand_macro_tokens alias so the rest of this file
# (and any cross-route imports) keeps working without sweeping changes.
from core.macros import expand_macro_tokens as _expand_macro_tokens
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
    # V6.25.9 — Quick-Roll Bar / character sheet macro fires send the
    # speaker's active character_id so token expansion reads from THAT
    # sheet rather than guessing the most-recently-touched one.
    character_id: Optional[str] = None


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
# V6.25.6 — Cut B chat hot-keys.
# /cast <spell name>            — narrative cast announcement; backend
#                                  resolves the spell from the campaign's
#                                  reference + custom_attributes pool.
# /use bundle <bundle name>     — power bundle invocation; resolves to
#                                  charges_max / energy_cost / cooldown.
# /spend xp <amount> for <reason>
#                                — proposes an XP spend on the SPEAKER's
#                                  active character (raise_total_points
#                                  patch) — GM still approves via the
#                                  existing /xp-spend queue.
_SLASH_CAST_RE = re.compile(r"^/cast\s+(.+)$", re.IGNORECASE)
_SLASH_USE_BUNDLE_RE = re.compile(r"^/use\s+bundle\s+(.+)$", re.IGNORECASE)
_SLASH_SPEND_XP_RE = re.compile(
    r"^/spend\s+xp\s+(\d+(?:\.\d+)?)\s+(?:for\s+|on\s+)?(.+)$", re.IGNORECASE)
# V6.25.7 — user-defined macro invocation. Matches `/<macroname>` with
# an optional trailing modifier injection (`+2`, `-1`, `+1d4`).
_SLASH_MACRO_RE = re.compile(
    r"^/([a-zA-Z][a-zA-Z0-9_-]{0,30})\s*([+-][0-9d+\- ]+)?\s*$")


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
    m = _SLASH_CAST_RE.match(body)
    if m:
        return {"kind": "cast", "name": m.group(1).strip()}
    m = _SLASH_USE_BUNDLE_RE.match(body)
    if m:
        return {"kind": "use_bundle", "name": m.group(1).strip()}
    m = _SLASH_SPEND_XP_RE.match(body)
    if m:
        return {"kind": "spend_xp",
                "amount": float(m.group(1)),
                "reason": m.group(2).strip()}
    # V6.25.7 — generic macro invocation. Reserved system slash names
    # are excluded so e.g. /roll / /me / /w / /cast / /use bundle / /spend
    # never collide. Macro look-up happens in the post handler — we
    # only flag the intent here.
    m = _SLASH_MACRO_RE.match(body)
    if m and m.group(1).lower() not in {
        "roll", "me", "w", "whisper", "cast", "use", "spend"
    }:
        return {"kind": "macro", "name": m.group(1),
                "modifier": (m.group(2) or "").strip()}
    return {}


def _camp_room(cid: str) -> str:
    """WS room id used to scope campaign-wide channel broadcasts.
    The session bus accepts arbitrary room keys; we re-use the existing
    Bus by namespacing under "campaign:{cid}" rather than session ids."""
    return f"campaign:{cid}"


# V6.25.6 — Cut B resolvers.
async def _resolve_spell_or_bundle(cid: str, name: str, mode: str) -> dict:
    """Look up `name` in the campaign's reference + custom_attributes
    pool. Returns a flat snapshot the client renders inline; on miss,
    returns `{"miss": true}` so the chat line shows a "not found"
    affordance without breaking the post."""
    needle = (name or "").strip().lower()
    if not needle:
        return {"miss": True}
    # references first (system spells / power_bundle / power_pack).
    # Note: the Reference Editor stores into `campaign_reference`, not
    # `references` — the former is the canonical collection (V6.3+).
    ref = await db.campaign_reference.find_one(
        {"campaign_id": cid,
         "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}},
        {"_id": 0})
    if ref:
        kind = (ref.get("kind") or "").lower()
        # Spell-like → expose level/school/cost/effect; bundle-like →
        # invocation / charges / EP cost.
        f = ref.get("fields") or {}
        if kind in ("spell", "spells") and mode == "spell":
            return {"hit": True, "kind": "spell", "name": ref.get("name"),
                    "level": ref.get("level") or f.get("level"),
                    "school": ref.get("school") or f.get("school"),
                    "cost": ref.get("cost") or f.get("cost"),
                    "effect": ref.get("effect") or f.get("description") or ref.get("summary"),
                    "source_id": ref.get("id")}
        if kind in ("power_bundle", "power_pack"):
            return {"hit": True, "kind": "power_bundle", "name": ref.get("name"),
                    "invocation": f.get("invocation"),
                    "charges_max": f.get("charges_max"),
                    "energy_cost": f.get("energy_cost"),
                    "cooldown": f.get("cooldown"),
                    "description": f.get("description") or ref.get("summary"),
                    "source_id": ref.get("id")}
    # Custom Rules pool — homebrew spells / power bundles / abilities.
    custom = await db.custom_attributes.find_one(
        {"campaign_id": cid,
         "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}},
        {"_id": 0})
    if custom:
        return {"hit": True, "kind": (custom.get("kind") or "custom"),
                "name": custom.get("name"),
                "description": custom.get("description_note", ""),
                "effects": custom.get("effects") or {},
                "source_id": custom.get("id")}
    return {"miss": True, "queried": name}


async def _queue_speaker_xp_spend(camp_id: str, user: dict,
                                    amount: float, reason: str) -> dict:
    """Queue an XP-spend proposal on the speaker's active character.
    Returns {character_id, character_name, status, error?}."""
    # Find the speaker's character on this campaign (most-recently
    # updated wins if they have multiple).
    char = await db.characters.find_one(
        {"campaign_id": camp_id, "owner_id": user["id"]},
        {"_id": 0}, sort=[("updated_at", -1), ("created_at", -1)])
    if not char:
        return {"error": "No character on this campaign for the speaker."}
    # Honour the toggleable per-campaign XP marketplace switch.
    camp = await db.campaigns.find_one({"id": camp_id},
                                          {"_id": 0, "xp_marketplace": 1, "gm_id": 1})
    if not (camp or {}).get("xp_marketplace", True):
        return {"character_id": char["id"], "character_name": char["name"],
                "error": "XP marketplace disabled by GM for this campaign."}
    unspent = float(char.get("xp_unspent", 0.0))
    if amount > unspent + 0.001:
        return {"character_id": char["id"], "character_name": char["name"],
                "error": (f"Insufficient unspent XP "
                           f"({unspent:.1f}). Asked for {amount:.1f}.")}
    proposal = {
        "id": new_id(),
        "character_id": char["id"], "character_name": char["name"],
        "campaign_id": camp_id,
        "owner_id": char.get("owner_id"),
        "owner_name": char.get("owner_name"),
        "proposed_by_id": user["id"], "proposed_by_name": user["name"],
        "cost": float(amount), "reason": reason,
        "change": {"raise_total_points": int(round(amount))},
        "summary": reason, "status": "pending",
        "gm_decision": None, "decided_at": None,
        "source": "chat-hotkey",
        "created_at": now_iso(),
    }
    await db.xp_pending.insert_one(proposal)
    return {"character_id": char["id"], "character_name": char["name"],
            "status": "queued", "proposal_id": proposal["id"]}


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

    # V6.25.6 — Cut B server-side resolution.
    # V6.25.7 — Hot-keys V2: /cast and /use bundle now also DEDUCT
    # charges / EP / spell-slots from the speaker's active character
    # folio when the resolver finds a hit. Each post stamps an
    # `undoable_until` timestamp (30s); the /undo endpoint reverses
    # the deduction within that window.
    elif slash.get("kind") == "cast":
        resolved = await _resolve_spell_or_bundle(camp["id"], slash["name"], "spell")
        deduct = await _deduct_for_post(camp["id"], user, "cast", resolved)
        doc["kind"] = "cast"
        doc["slash_meta"] = {**slash, "resolved": resolved, "deduct": deduct}
        if deduct.get("applied"):
            doc["undoable_until"] = _undo_window()

    elif slash.get("kind") == "use_bundle":
        resolved = await _resolve_spell_or_bundle(camp["id"], slash["name"], "bundle")
        deduct = await _deduct_for_post(camp["id"], user, "use_bundle", resolved)
        doc["kind"] = "use_bundle"
        doc["slash_meta"] = {**slash, "resolved": resolved, "deduct": deduct}
        if deduct.get("applied"):
            doc["undoable_until"] = _undo_window()

    elif slash.get("kind") == "spend_xp":
        # Find the speaker's active character on this campaign and queue
        # an XP-spend proposal (`raise_total_points` patch — easiest
        # narrative fit). GM still approves via the normal queue.
        proposal = await _queue_speaker_xp_spend(
            camp_id=camp["id"], user=user,
            amount=float(slash["amount"]), reason=slash["reason"])
        doc["kind"] = "spend_xp"
        doc["slash_meta"] = {**slash, "proposal": proposal}

    # V6.25.7 — user-defined macro invocation. Resolves a `/<name>`
    # against the macros collection (user-scope + campaign-scope on
    # this campaign), expands its formula via the same dice engine as
    # /roll, and supports a trailing modifier injection (`+2`) for
    # advantage / edges / Effort / obstacles.
    elif slash.get("kind") == "macro":
        from routes.sessions import roll_dice
        m = await db.macros.find_one({
            "campaign_id": camp["id"],
            "name": {"$regex": f"^{re.escape(slash['name'])}$", "$options": "i"},
            "$or": [
                {"scope": "campaign"},
                {"scope": "user", "owner_id": user["id"]},
            ],
        }, {"_id": 0})
        if not m:
            doc["kind"] = "macro"
            doc["slash_meta"] = {**slash, "miss": True}
        else:
            # V6.25.9 — prefer the explicit character_id sent by the
            # Quick-Roll Bar / sheet macro fire (so the player can have
            # multiple characters on a campaign and the macro still
            # resolves against the one they're rolling for). Falls back
            # to the most-recently-touched character when omitted.
            char = None
            if body.character_id:
                char = await db.characters.find_one(
                    {"id": body.character_id, "campaign_id": camp["id"]},
                    {"_id": 0})
            if not char:
                char = await db.characters.find_one(
                    {"campaign_id": camp["id"], "owner_id": user["id"]},
                    {"_id": 0}, sort=[("updated_at", -1), ("created_at", -1)])
            formula = _expand_macro_tokens(m["formula"], char)
            if slash.get("modifier"):
                formula = f"{formula}{slash['modifier']}"
            try:
                result = roll_dice(formula)
                doc["kind"] = "macro"
                doc["slash_meta"] = {**slash, "macro": {
                    "id": m["id"], "label": m.get("label") or m["name"],
                    "formula_raw": m["formula"],
                    "formula_expanded": formula,
                }, "result": result}
                # Bump usage so the Quick-Roll Bar can show "most used".
                await db.macros.update_one(
                    {"id": m["id"]},
                    {"$inc": {"use_count": 1},
                     "$set": {"last_used_at": now_iso()}})
            except HTTPException:
                doc["slash_meta"] = {**slash, "macro": {
                    "id": m["id"], "label": m.get("label") or m["name"],
                    "formula_raw": m["formula"], "formula_expanded": formula},
                    "error": "Invalid expanded formula"}

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


# ─── V6.25.7 helpers — Hot-Keys V2 deduct + macro expansion ──────────

from datetime import datetime, timedelta, timezone

UNDO_WINDOW_SECONDS = 30


def _undo_window() -> str:
    return (datetime.now(timezone.utc)
            + timedelta(seconds=UNDO_WINDOW_SECONDS)).isoformat()


async def _deduct_for_post(camp_id: str, user: dict, mode: str,
                              resolved: dict) -> dict:
    """Deduct the resource consumed by /cast (spell slot) or /use bundle
    (charges + EP). Writes to the speaker's most-recently-touched
    character's folio."""
    if not resolved or not resolved.get("hit"):
        return {"applied": False, "reason": "no resolved entry"}
    char = await db.characters.find_one(
        {"campaign_id": camp_id, "owner_id": user["id"]},
        {"_id": 0}, sort=[("updated_at", -1), ("created_at", -1)])
    if not char:
        return {"applied": False, "reason": "no character"}
    folio = dict(char.get("folio") or {})

    if mode == "cast":
        lvl = resolved.get("level")
        try:
            lvl_n = int(lvl) if lvl is not None else 0
        except (TypeError, ValueError):
            lvl_n = 0
        if lvl_n <= 0:
            return {"applied": False, "reason": "cantrip / unleveled"}
        dnd_state = dict(folio.get("dnd_state") or {})
        slots = dict(dnd_state.get("spell_slots") or {})
        cur = int(slots.get(str(lvl_n), 0) or 0)
        if cur <= 0:
            return {"applied": False, "reason": f"no L{lvl_n} slots remaining",
                    "character_id": char["id"], "character_name": char["name"]}
        slots[str(lvl_n)] = cur - 1
        dnd_state["spell_slots"] = slots
        folio["dnd_state"] = dnd_state
        await db.characters.update_one({"id": char["id"]},
            {"$set": {"folio": folio, "updated_at": now_iso()}})
        return {"applied": True, "character_id": char["id"],
                "character_name": char["name"], "mode": "spell_slot",
                "payload": {"level": lvl_n, "before": cur, "after": cur - 1}}

    if mode == "use_bundle":
        src = resolved.get("source_id") or resolved.get("name")
        max_charges = resolved.get("charges_max")
        ep_cost = int(resolved.get("energy_cost") or 0)
        bundle_charges = dict(folio.get("bundle_charges") or {})
        used = int(bundle_charges.get(src, 0) or 0)
        applied_payload = {}
        if max_charges is not None and int(max_charges) > 0:
            if used >= int(max_charges):
                return {"applied": False, "reason": "no charges remaining",
                        "character_id": char["id"],
                        "character_name": char["name"]}
            bundle_charges[src] = used + 1
            applied_payload["charges"] = {"max": int(max_charges),
                                            "used_before": used,
                                            "used_after": used + 1}
        ep_before = int(folio.get("energy_points", 0) or 0)
        if ep_cost:
            if ep_before < ep_cost:
                return {"applied": False,
                        "reason": f"insufficient EP ({ep_before}/{ep_cost})",
                        "character_id": char["id"],
                        "character_name": char["name"]}
            folio["energy_points"] = ep_before - ep_cost
            applied_payload["ep"] = {"cost": ep_cost,
                                       "before": ep_before,
                                       "after": ep_before - ep_cost}
        if not applied_payload:
            return {"applied": False,
                    "reason": "bundle has no consumable resource",
                    "character_id": char["id"],
                    "character_name": char["name"]}
        folio["bundle_charges"] = bundle_charges
        await db.characters.update_one({"id": char["id"]},
            {"$set": {"folio": folio, "updated_at": now_iso()}})
        # V6.25.50 — push the new HP/EP to every open battlemap that
        # has this character on its tokens list.
        await broadcast_character_vitals(char["id"],
            fresh_character={**char, "folio": folio})
        return {"applied": True, "character_id": char["id"],
                "character_name": char["name"], "mode": "bundle",
                "payload": {"source_id": src, **applied_payload}}

    return {"applied": False, "reason": f"unknown mode {mode}"}


async def _undo_deduct(msg: dict, user: dict) -> dict:
    """Reverse a deduct stamped on a /cast or /use bundle message
    within the 30s window."""
    deduct = (msg.get("slash_meta") or {}).get("deduct") or {}
    if not deduct.get("applied"):
        raise HTTPException(400, "Nothing to undo on this message.")
    if msg.get("author_id") != user["id"]:
        raise HTTPException(403, "Only the speaker can undo their own action.")
    until = msg.get("undoable_until")
    if not until:
        raise HTTPException(400, "Undo window already closed.")
    try:
        if datetime.fromisoformat(until) < datetime.now(timezone.utc):
            raise HTTPException(400, "Undo window expired.")
    except ValueError:
        raise HTTPException(400, "Undo window malformed.")
    char = await db.characters.find_one({"id": deduct["character_id"]},
                                            {"_id": 0})
    if not char:
        raise HTTPException(404, "Character vanished")
    folio = dict(char.get("folio") or {})
    pl = deduct.get("payload") or {}

    if deduct.get("mode") == "spell_slot":
        dnd_state = dict(folio.get("dnd_state") or {})
        slots = dict(dnd_state.get("spell_slots") or {})
        slots[str(pl["level"])] = pl["before"]
        dnd_state["spell_slots"] = slots
        folio["dnd_state"] = dnd_state
    elif deduct.get("mode") == "bundle":
        if "charges" in pl:
            charges = dict(folio.get("bundle_charges") or {})
            charges[pl["source_id"]] = pl["charges"]["used_before"]
            folio["bundle_charges"] = charges
        if "ep" in pl:
            folio["energy_points"] = pl["ep"]["before"]

    await db.characters.update_one({"id": char["id"]},
        {"$set": {"folio": folio, "updated_at": now_iso()}})
    # V6.25.50 — refresh battlemap rings after the undo restores HP/EP.
    await broadcast_character_vitals(char["id"],
        fresh_character={**char, "folio": folio})
    new_meta = {**(msg.get("slash_meta") or {}),
                "deduct": {**deduct, "undone": True,
                           "undone_at": now_iso()}}
    await db.channel_msgs.update_one({"id": msg["id"]},
        {"$set": {"slash_meta": new_meta, "undoable_until": None}})
    return {"ok": True}


@router.post("/messages/{mid}/undo")
async def undo_message_deduct(mid: str,
                                 user: dict = Depends(get_current_user)):
    """30-second undo for /cast and /use bundle deductions."""
    msg = await db.channel_msgs.find_one({"id": mid}, {"_id": 0})
    if not msg:
        raise HTTPException(404, "Message not found")
    return await _undo_deduct(msg, user)



