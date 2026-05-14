"""V6.25.55 — Phase D: Virtual "The Game Master" character.

Each campaign gets a single canonical GM character — owned by the
campaign's GM, marked `is_gm_voice=True`, `omniscient=True`, all stats
zeroed, `published=True`. This is the canonical speaker identity the
GM uses for in-character narration, NPC voices, and Push-to-Talk lines
that don't belong to any seated PC.

Why it's a separate character row (not a special-case flag on the
session): voice_lines / chat / recap pipelines already key off
`character_id`. Reusing the existing model means PTT, chat-mirror,
recap-bucketing, and Player-Hearth surfaces all work without
per-pipeline branching.

Foundation for Phase E (audio overhaul): the per-user mixer keys
microphone streams by the speaker's character_id; the virtual GM
character provides a stable id for the GM's mic.

Endpoints:
  GET /api/campaigns/{cid}/gm-voice-character
      → returns the virtual GM character row, lazy-creating it on
        first read. Any seated member may read; the GM owns the row.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["gm-voice"])

VIRTUAL_GM_NAME = "The Game Master"


async def _ensure_gm_voice_character(camp: dict) -> dict:
    """Find-or-create the per-campaign virtual GM character.

    Idempotent — repeated calls return the same row. Created lazily so
    legacy campaigns get one on their first GET without a migration.
    """
    cid = camp["id"]
    existing = await db.characters.find_one(
        {"campaign_id": cid, "is_gm_voice": True}, {"_id": 0},
    )
    if existing:
        return existing

    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "name": VIRTUAL_GM_NAME,
        "concept": "The omniscient voice behind the screen.",
        "power_level": "Narrator",
        "total_points": 0,
        "size": "Medium",
        "token_color": "#C8A34A",  # gold — matches GM accents app-wide.
        # Zero stats — this character never rolls; it speaks.
        "stats": {"body": 0, "mind": 0, "soul": 0,
                  "acv": 0, "dcv": 0, "damage_mult": 0, "armour": 0},
        "attributes": [],
        "defects": [],
        "skills": [],
        "power_packs": [],
        "power_bundles": [],
        "notes": "Auto-created virtual GM character. Used as the speaker "
                 "identity for narration, NPC voices, and any GM line "
                 "that doesn't belong to a seated PC.",
        "published": True,  # show in pickers from the moment it exists
        "folio": {},
        "companion_owners": [],
        # Phase D flags — checked by the frontend to render this row
        # distinctly (gold ring, locked from editing, opaque to dice
        # rollers since it has no stats).
        "is_gm_voice": True,
        "omniscient": True,
        "owner_id": camp["gm_id"],
        "owner_name": camp.get("gm_name", ""),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.characters.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{cid}/gm-voice-character")
async def get_gm_voice_character(cid: str, user: dict = Depends(get_current_user)):
    """Lazy-fetch the campaign's virtual GM character. Any seated
    member / GM / admin may read; the GM owns the row."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if (user.get("role") != "admin"
            and user["id"] != camp.get("gm_id")
            and user["id"] not in (camp.get("member_ids") or [])):
        raise HTTPException(403, "Only seated members may read the GM voice character.")
    return sanitize(await _ensure_gm_voice_character(camp))
