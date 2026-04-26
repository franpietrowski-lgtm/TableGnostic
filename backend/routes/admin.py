"""Admin — destructive content management.

`POST /api/admin/reset-to-evereantha` (admin role only)
Wipes all non-user data and reseeds the canonical Evereantha campaign with
its full World Codex, Atelier/Genesis pre-fill, and three apprentice PCs.

This is a one-shot demo-table reset. Users (auth records, login attempts,
password reset tokens) are explicitly preserved.
"""
from fastapi import APIRouter, Depends, HTTPException

from core.cost_engine import calc_derived, calc_spent_points
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user
from seed_evereantha import (
    EVEREANTHA_CAMPAIGN, EVEREANTHA_GENESIS,
    EVEREANTHA_NODES, EVEREANTHA_PCS,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Collections to clear on a full reset (everything except auth-related ones).
_GAME_COLLECTIONS = (
    "campaigns", "characters", "sessions", "chat_logs", "dice_rolls",
    "initiative", "effects", "nodes", "edges", "recaps",
    "custom_attributes", "genesis",
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
            "fields": {},
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

    return {
        "ok": True,
        "wiped": wiped,
        "campaign": sanitize(camp),
        "nodes_created": nodes_inserted,
        "characters_created": len(chars_inserted),
        "characters": chars_inserted,
    }
