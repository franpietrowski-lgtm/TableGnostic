"""Session room — sessions, chat, dice, initiative, effects, damage, WebSocket bus.

This is the live-play surface. Future LiveKit / Daily / Agora migration
will swap the WebRTC mesh signalling parts (everything in `bus.py` plus
the `webrtc:offer/answer/ice` relay below) for SFU-mediated signalling
without touching the chat / dice / initiative routes.

Health endpoint also lives here since this file owns the `/api` shape.
"""
import json as _json
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

import jwt
from fastapi import (
    APIRouter, Depends, HTTPException,
    WebSocket, WebSocketDisconnect,
)

from core.bus import broadcast, bus
from core.config import JWT_ALGORITHM, JWT_SECRET
from core.db import db, new_id, now_iso, sanitize
from core.models import (
    ChatIn, DamageIn, DiceIn, EffectIn, InitiativeEntryIn, SessionIn,
)
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["sessions"])
ws_router = APIRouter()


# -------- Sessions --------

@router.post("/sessions")
async def create_session(body: SessionIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": body.campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can create sessions")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    doc["status"] = "open"
    doc["round"] = 0
    await db.sessions.insert_one(doc)
    # Auto-pin: drop the campaign's most recent recap as a system chat
    # message — "What happened last time…"
    try:
        prev_recap = await db.recaps.find_one(
            {"campaign_id": body.campaign_id},
            {"_id": 0}, sort=[("created_at", -1)],
        )
        if prev_recap and prev_recap.get("text"):
            pinned = {
                "id": new_id(), "session_id": doc["id"],
                "message": f"📜 What happened last time…\n\n{prev_recap['text']}",
                "kind": "system", "user_id": "system",
                "user_name": "LOREMASTER",
                "pinned": True,
                "created_at": now_iso(),
            }
            await db.chat_logs.insert_one(pinned)
    except Exception as e:
        print(f"[auto-pin recap] {e}")
    return sanitize(doc)


@router.get("/campaigns/{cid}/sessions")
async def list_sessions(cid: str, user: dict = Depends(get_current_user)):
    rows = await db.sessions.find({"campaign_id": cid}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return rows


@router.get("/sessions/{sid}")
async def get_session(sid: str, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Not found")
    return s


# -------- Chat --------

@router.post("/chat")
async def post_chat(body: ChatIn, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": body.session_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "No session")
    doc = {
        "id": new_id(), "session_id": body.session_id, "message": body.message,
        "kind": body.kind, "user_id": user["id"], "user_name": user["name"],
        "created_at": now_iso(),
    }
    await db.chat_logs.insert_one(doc)
    await broadcast(body.session_id, {"type": "chat", "data": sanitize(doc)})
    return sanitize(doc)


@router.get("/sessions/{sid}/chat")
async def list_chat(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.chat_logs.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return rows


# -------- Dice --------

DICE_TOKEN = re.compile(r"^\s*(\d+)d(\d+)\s*$")


def roll_dice(notation: str, stat_values: Dict[str, int] = None) -> Dict[str, Any]:
    stat_values = stat_values or {}
    notation = notation.strip()
    parts = re.split(r"([+\-])", notation)
    sign = 1
    rolls: List[Dict[str, Any]] = []
    flat = 0
    total = 0
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p == "+":
            sign = 1
            continue
        if p == "-":
            sign = -1
            continue
        m = DICE_TOKEN.match(p)
        if m:
            n, d = int(m.group(1)), int(m.group(2))
            if n <= 0 or d <= 0 or n > 30 or d > 1000:
                raise HTTPException(400, "Invalid dice")
            these = [random.randint(1, d) for _ in range(n)]
            rolls.append({"notation": p, "sides": d, "results": these, "sign": sign})
            total += sign * sum(these)
        else:
            try:
                v = int(p)
                flat += sign * v
                total += sign * v
            except ValueError:
                key = p.lower()
                v = int(stat_values.get(key, 0))
                flat += sign * v
                total += sign * v
                rolls.append({"notation": p, "ref": p, "value": v, "sign": sign})
    return {"rolls": rolls, "flat": flat, "total": total}


@router.post("/dice")
async def post_dice(body: DiceIn, user: dict = Depends(get_current_user)):
    stats: Dict[str, int] = {}
    if body.character_id:
        ch = await db.characters.find_one({"id": body.character_id}, {"_id": 0})
        if ch:
            s = ch.get("stats", {})
            d = ch.get("derived", {})
            stats = {
                "body": s.get("body", 0), "mind": s.get("mind", 0), "soul": s.get("soul", 0),
                "cv": d.get("combat_value", 0), "atk": d.get("attack_value", 0),
                "def": d.get("defence_value", 0),
                "combat_value": d.get("combat_value", 0),
                "attack_value": d.get("attack_value", 0),
                "defence_value": d.get("defence_value", 0),
            }
    result = roll_dice(body.notation, stats)
    doc = {
        "id": new_id(), "session_id": body.session_id, "user_id": user["id"],
        "user_name": user["name"], "notation": body.notation, "label": body.label,
        "result": result, "target": body.target, "character_id": body.character_id,
        "private": body.private, "created_at": now_iso(),
    }
    success = None
    if body.target is not None:
        # BESM is roll-under for Stat/Skill 2d6 vs Target Number after mods.
        # We simply expose both sides; GM can interpret.
        success = result["total"] <= body.target
    doc["success"] = success
    await db.dice_rolls.insert_one(doc)
    await broadcast(body.session_id, {"type": "dice", "data": sanitize(doc)})
    return sanitize(doc)


@router.get("/sessions/{sid}/dice")
async def list_dice(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.dice_rolls.find({"session_id": sid}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return rows


# -------- Initiative --------

@router.post("/initiative")
async def add_initiative(body: InitiativeEntryIn,
                         user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": body.session_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "No session")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    doc["active"] = True
    await db.initiative.insert_one(doc)
    await broadcast(body.session_id, {"type": "initiative", "data": sanitize(doc)})
    return sanitize(doc)


@router.get("/sessions/{sid}/initiative")
async def list_initiative(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.initiative.find({"session_id": sid}, {"_id": 0}).sort("roll", -1).to_list(100)
    return rows


@router.delete("/initiative/{iid}")
async def remove_initiative(iid: str, user: dict = Depends(get_current_user)):
    row = await db.initiative.find_one({"id": iid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Not found")
    await db.initiative.delete_one({"id": iid})
    await broadcast(row["session_id"], {"type": "initiative_remove", "data": {"id": iid}})
    return {"ok": True}


@router.post("/sessions/{sid}/round/advance")
async def advance_round(sid: str, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    if user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Only GM")
    new_round = s.get("round", 0) + 1
    await db.sessions.update_one({"id": sid}, {"$set": {"round": new_round}})
    await db.effects.update_many({"session_id": sid, "active": True},
                                 {"$inc": {"duration_rounds": -1}})
    expired = await db.effects.find(
        {"session_id": sid, "duration_rounds": {"$lte": 0}, "active": True},
        {"_id": 0},
    ).to_list(200)
    for e in expired:
        await db.effects.update_one({"id": e["id"]}, {"$set": {"active": False}})
    await broadcast(sid, {"type": "round", "data": {"round": new_round, "expired": expired}})
    return {"round": new_round, "expired": expired}


# -------- Effects / Damage --------

@router.post("/effects")
async def add_effect(body: EffectIn, user: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    doc["active"] = True
    doc["applied_by"] = user["name"]
    await db.effects.insert_one(doc)
    await broadcast(body.session_id, {"type": "effect", "data": sanitize(doc)})
    return sanitize(doc)


@router.get("/sessions/{sid}/effects")
async def list_effects(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.effects.find({"session_id": sid, "active": True}, {"_id": 0}).to_list(200)
    return rows


@router.delete("/effects/{eid}")
async def remove_effect(eid: str, user: dict = Depends(get_current_user)):
    row = await db.effects.find_one({"id": eid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Not found")
    await db.effects.update_one({"id": eid}, {"$set": {"active": False}})
    await broadcast(row["session_id"], {"type": "effect_remove", "data": {"id": eid}})
    return {"ok": True}


@router.post("/damage")
async def apply_damage(body: DamageIn, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": body.session_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Not found")
    msg = f"{body.target_name} took {body.amount} {body.kind.upper()} damage"
    doc = {
        "id": new_id(), "session_id": body.session_id, "message": msg,
        "kind": "system", "user_id": user["id"], "user_name": "SYSTEM",
        "created_at": now_iso(),
    }
    await db.chat_logs.insert_one(doc)
    await broadcast(body.session_id, {"type": "chat", "data": sanitize(doc)})
    return sanitize(doc)


# -------- Health --------

@router.get("/health")
async def health():
    return {"ok": True, "service": "table-gnostic", "time": now_iso()}


# -------- WebSocket bus (presence + WebRTC mesh signalling) --------

@ws_router.websocket("/api/ws/session/{sid}")
async def ws_session(ws: WebSocket, sid: str, token: str = None):
    """Token-authed live session WebSocket.
    Accepts: presence:av-state (state broadcast) + webrtc:offer/answer/ice
    (targeted relay to a specific peer via `to: conn_id`).
    Chat / dice / initiative are pushed via REST endpoints — they broadcast
    over the same bus, but the WS itself ignores inbound chat-shaped messages.

    Auth/lookup checks ACCEPT the socket before closing so client libraries
    can read the policy code (4401 / 4404 / 4403) rather than an HTTP-level
    handshake rejection.
    """
    await ws.accept()
    if not token:
        await ws.close(code=4401)
        return
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            await ws.close(code=4401)
            return
    except jwt.PyJWTError:
        await ws.close(code=4401)
        return
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        await ws.close(code=4404)
        return
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    uid = payload.get("sub")
    if not camp or (camp["gm_id"] != uid
                    and uid not in camp.get("member_ids", [])
                    and camp.get("visibility") != "public"):
        await ws.close(code=4403)
        return

    user = await db.users.find_one({"id": uid}, {"_id": 0}) or {}
    name = user.get("name") or user.get("email") or "Adventurer"
    is_gm = (camp.get("gm_id") == uid)

    me = await bus.join(sid, ws, uid, name, accepted=True)

    # 1. Tell the joiner who's already in the room.
    others = [
        {"conn_id": p.conn_id, "uid": p.uid, "name": p.name}
        for p in bus.peers(sid) if p.conn_id != me.conn_id
    ]
    await bus._safe_send(me, {
        "type": "presence:room",
        "data": {
            "you": {"conn_id": me.conn_id, "uid": me.uid, "name": me.name, "is_gm": is_gm},
            "peers": others,
        },
    })
    # 2. Tell everyone else a new peer arrived.
    await bus.send(sid, {
        "type": "presence:join",
        "data": {"conn_id": me.conn_id, "uid": me.uid, "name": me.name, "is_gm": is_gm},
    }, exclude_ws=ws)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = _json.loads(raw)
            except Exception:
                continue
            t = msg.get("type")
            if t in ("webrtc:offer", "webrtc:answer", "webrtc:ice"):
                target = msg.get("to")
                data = msg.get("data") or {}
                if not target:
                    continue
                await bus.send_to(sid, target, {
                    "type": t,
                    "data": {**data, "from": me.conn_id, "from_name": me.name},
                })
            elif t == "presence:av-state":
                data = msg.get("data") or {}
                await bus.send(sid, {
                    "type": "presence:av-state",
                    "data": {"conn_id": me.conn_id, **data},
                }, exclude_ws=ws)
            # Other inbound types ignored — REST routes own chat/dice/init.
    except WebSocketDisconnect:
        gone = bus.leave(sid, ws)
        if gone:
            await bus.send(sid, {
                "type": "presence:leave",
                "data": {"conn_id": gone.conn_id, "uid": gone.uid, "name": gone.name},
            })



# -------- Campaign-room WebSocket (channels real-time, V4.2) --------

@ws_router.websocket("/api/ws/campaign/{cid}")
async def ws_campaign(ws: WebSocket, cid: str, token: str = None):
    """Token-authed campaign-room WebSocket. Joins the bus room
    `campaign:{cid}` so REST channel routes' `broadcast(...)` deliveries
    arrive in real time. Inbound payloads are NO-OP — clients only
    listen here; channel writes still go through REST so server-side
    slash-command parsing + persistence happen exactly once.

    Accept-then-close pattern so 4401/4404/4403 codes are wire-visible.
    """
    await ws.accept()
    if not token:
        await ws.close(code=4401)
        return
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            await ws.close(code=4401)
            return
    except jwt.PyJWTError:
        await ws.close(code=4401)
        return
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        await ws.close(code=4404)
        return
    uid = payload.get("sub")
    if (camp["gm_id"] != uid
            and uid not in camp.get("member_ids", [])
            and camp.get("visibility") != "public"):
        await ws.close(code=4403)
        return

    user = await db.users.find_one({"id": uid}, {"_id": 0}) or {}
    name = user.get("name") or user.get("email") or "Adventurer"
    room = f"campaign:{cid}"
    await bus.join(room, ws, uid, name, accepted=True)  # subscribe-only

    try:
        while True:
            await ws.receive_text()  # ignore inbound; subscriber-only socket
    except WebSocketDisconnect:
        bus.leave(room, ws)
