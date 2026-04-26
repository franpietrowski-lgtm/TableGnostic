"""Admin — destructive content management.

`POST /api/admin/reset-to-evereantha` (admin role only)
Wipes all non-user data and reseeds the canonical Evereantha campaign with
its full World Codex, Atelier/Genesis pre-fill, three apprentice PCs, and
an 8-session opening-arc Chronicle (chat dialogue + dice rolls + GM notes).

This is a one-shot demo-table reset. Users (auth records, login attempts,
password reset tokens) are explicitly preserved.
"""
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from core.cost_engine import calc_derived, calc_spent_points
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user
from seed_evereantha import (
    EVEREANTHA_CAMPAIGN, EVEREANTHA_GENESIS,
    EVEREANTHA_NODES, EVEREANTHA_PCS, EVEREANTHA_SESSIONS,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Collections to clear on a full reset (everything except auth-related ones).
_GAME_COLLECTIONS = (
    "campaigns", "characters", "sessions", "chat_logs", "dice_rolls",
    "initiative", "effects", "nodes", "edges", "recaps",
    "custom_attributes", "genesis", "atelier", "ingestions",
    "battlemaps", "channels", "channel_messages",
)


@router.post("/reset-to-evereantha")
async def reset_to_evereantha(confirm: str = "", user: dict = Depends(get_current_user)):
    """Admin-only. Wipes all game content and seeds the Evereantha demo table.

    DESTRUCTIVE — must pass `?confirm=WIPE` query param. Without it returns 400
    so a stray POST from automation or a UI typo can't nuke the table.

    Preserves: users, login_attempts, password_reset_tokens.
    Wipes:     campaigns, characters, sessions, chat, dice, initiative,
               effects, nodes, edges, recaps, custom_attributes, genesis.
    """
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    if confirm != "WIPE":
        raise HTTPException(400, "This endpoint is destructive. "
                                  "Pass ?confirm=WIPE to proceed.")

    # ---- 1. wipe ----
    wiped = {}
    for c in _GAME_COLLECTIONS:
        result = await db[c].delete_many({})
        wiped[c] = result.deleted_count

    # ---- 2. campaign owned by the calling admin ----
    camp_id = new_id()
    camp = {
        **EVEREANTHA_CAMPAIGN,
        "id": camp_id,
        "gm_id": user["id"],
        "gm_name": user["name"],
        "member_ids": [],
        "invite_token": new_id(),  # 32-char hex
        "created_at": now_iso(),
    }
    await db.campaigns.insert_one(camp)

    # ---- 3. World Codex nodes ----
    nodes_inserted = 0
    for n in EVEREANTHA_NODES:
        await db.nodes.insert_one({
            "id": new_id(),
            "campaign_id": camp_id,
            "type": n["type"],
            "title": n["title"],
            "content": n.get("content", ""),
            "tags": n.get("tags", []),
            "visibility": n.get("visibility", "shared"),
            "revealed_to": [],
            "links": [],
            "fields": n.get("fields", {}),
            "author_id": user["id"],
            "author_name": user["name"],
            "created_at": now_iso(),
        })
        nodes_inserted += 1

    # ---- 4. Genesis (Atelier) pre-fill ----
    await db.genesis.insert_one({
        "id": new_id(),
        "campaign_id": camp_id,
        **EVEREANTHA_GENESIS,
        "created_at": now_iso(),
    })

    # ---- 5. Three apprentice PCs ----
    chars_inserted = []
    chars_by_name: Dict[str, str] = {}  # name -> character_id (for chat user_name fallback)
    for pc in EVEREANTHA_PCS:
        doc = {
            "id": new_id(),
            "campaign_id": camp_id,
            "owner_id": user["id"],
            "owner_name": user["name"],
            "created_at": now_iso(),
            "name": pc["name"],
            "concept": pc["concept"],
            "power_level": pc["power_level"],
            "total_points": pc["total_points"],
            "token_color": pc.get("token_color", ""),
            "size": pc.get("size", "Medium"),
            "stats": pc["stats"],
            "attributes": pc["attributes"],
            "defects": pc["defects"],
            "skills": pc.get("skills", []),
            "power_packs": pc.get("power_packs", []),
            "notes": "Evereantha Maiden Adventure — apprentice (Adventurous tier).",
            "published": pc.get("published", True),
            "folio": pc.get("folio", {}),
        }
        doc["derived"] = calc_derived(doc, camp)
        doc["spent"] = calc_spent_points(doc)
        await db.characters.insert_one(doc)
        chars_inserted.append(sanitize(doc))
        chars_by_name[pc["name"]] = doc["id"]

    # ---- 6. 8-Session Chronicle (V4.4) ----
    sessions_inserted = 0
    chat_lines_inserted = 0
    dice_rolls_inserted = 0
    for idx, sess_seed in enumerate(EVEREANTHA_SESSIONS, start=1):
        sid = new_id()
        await db.sessions.insert_one({
            "id": sid,
            "campaign_id": camp_id,
            "title": sess_seed["title"],
            "scheduled_at": None,
            "created_at": now_iso(),
            "status": "closed" if idx < len(EVEREANTHA_SESSIONS) else "open",
            "round": 0,
            "gm_notes": sess_seed.get("gm_notes", ""),
            "recaps": [],
        })
        sessions_inserted += 1
        # Replay the session log: each entry becomes a chat_log row OR a
        # dice_rolls row. created_at is staggered by 30s so the timeline reads
        # in order; absolute timestamps are not significant for a seed.
        base = datetime.now(timezone.utc).timestamp() + (idx * 86400)  # space sessions one day apart
        for j, line in enumerate(sess_seed.get("log", [])):
            ts = datetime.fromtimestamp(base + (j * 30), tz=timezone.utc).isoformat()
            speaker = line.get("speaker", "")
            char_id = chars_by_name.get(speaker)
            if line.get("kind") == "dice":
                await db.dice_rolls.insert_one({
                    "id": new_id(),
                    "session_id": sid,
                    "user_id": user["id"],
                    "user_name": speaker or user["name"],
                    "notation": line.get("notation", "2d6"),
                    "label": line.get("label", ""),
                    "result": line.get("result", {"total": 0, "rolls": [], "flat": 0}),
                    "target": None,
                    "character_id": char_id,
                    "private": False,
                    "created_at": ts,
                })
                dice_rolls_inserted += 1
            else:
                await db.chat_logs.insert_one({
                    "id": new_id(),
                    "session_id": sid,
                    "message": line.get("text", ""),
                    "kind": line.get("kind", "chat"),
                    "user_id": user["id"],
                    "user_name": speaker or "GM",
                    "created_at": ts,
                })
                chat_lines_inserted += 1

    return {
        "ok": True,
        "wiped": wiped,
        "campaign": sanitize(camp),
        "nodes_created": nodes_inserted,
        "characters_created": len(chars_inserted),
        "characters": chars_inserted,
        "sessions_created": sessions_inserted,
        "chat_lines_seeded": chat_lines_inserted,
        "dice_rolls_seeded": dice_rolls_inserted,
    }
