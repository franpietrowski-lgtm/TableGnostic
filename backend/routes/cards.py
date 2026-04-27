"""Card-deck routes — system-aware draw/return mechanics.

Each campaign session can spawn a deck instance (`db.deck_instances`) which
tracks which cards have been drawn vs. remaining. Drawing is GM-only by
default; the GM can flip a deck to "open" so any seated player may draw.

Schema (`db.deck_instances`):
    {
      id:             str,
      campaign_id:    str,
      session_id:     Optional[str],
      system_id:      str,            # snapshot at create-time
      deck_id:        str,            # e.g. "deck_of_many_things"
      drawn_card_ids: List[str],
      log:            List[{by_uid, by_name, card_id, ts}],
      mode:           "gm-only" | "open",
      created_at:     iso,
      created_by:     str,
    }
"""
from random import shuffle as rshuffle
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.bus import broadcast
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user
from system_data import DECKS
from system_data.decks import deck_cards

router = APIRouter(prefix="/api", tags=["cards"])


# ─────── Pydantic ───────

class DeckCreateIn(BaseModel):
    campaign_id: str
    session_id: Optional[str] = None
    deck_id: str
    mode: str = "gm-only"


class DeckDrawIn(BaseModel):
    count: int = 1


# ─────── Helpers ───────

async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp


def _is_gm(camp: dict, user: dict) -> bool:
    return camp.get("gm_id") == user["id"] or user.get("role") == "admin"


def _is_member(camp: dict, user: dict) -> bool:
    return (_is_gm(camp, user) or
            user["id"] in (camp.get("member_ids") or []))


# ─────── Endpoints ───────

@router.get("/cards/decks/{system_id}")
async def list_decks(system_id: str, user: dict = Depends(get_current_user)):
    """Public catalogue of available decks for a given system."""
    return {"system_id": system_id,
            "decks": DECKS.get(system_id, DECKS.get("besm-4e", []))}


@router.get("/cards/decks/{system_id}/{deck_id}/preview")
async def preview_deck(system_id: str, deck_id: str,
                        user: dict = Depends(get_current_user)):
    """Show the full card list for a deck (read-only, no campaign state).

    GMs use this to plan; players see this only as a reference."""
    cards = deck_cards(system_id, deck_id)
    if cards is None:
        raise HTTPException(404, f"Unknown deck {deck_id!r} for system {system_id!r}")
    return {"deck_id": deck_id, "cards": cards}


@router.post("/cards/instances")
async def create_instance(body: DeckCreateIn, user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(body.campaign_id)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    cards = deck_cards(camp.get("system_id") or "besm-4e", body.deck_id)
    if cards is None:
        raise HTTPException(404, f"Unknown deck {body.deck_id!r} for system "
                                 f"{camp.get('system_id')!r}")
    doc = {
        "id": new_id(),
        "campaign_id": body.campaign_id,
        "session_id": body.session_id,
        "system_id": camp.get("system_id") or "besm-4e",
        "deck_id": body.deck_id,
        "drawn_card_ids": [],
        "log": [],
        "mode": body.mode if body.mode in ("gm-only", "open") else "gm-only",
        "created_at": now_iso(),
        "created_by": user["name"],
    }
    await db.deck_instances.insert_one(doc)
    return sanitize(doc)


@router.get("/cards/instances")
async def list_instances(campaign_id: str,
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(campaign_id)
    if not _is_member(camp, user):
        raise HTTPException(403, "Not a member of this campaign.")
    rows = await db.deck_instances.find(
        {"campaign_id": campaign_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return rows


@router.get("/cards/instances/{instance_id}")
async def get_instance(instance_id: str, user: dict = Depends(get_current_user)):
    inst = await db.deck_instances.find_one({"id": instance_id}, {"_id": 0})
    if not inst:
        raise HTTPException(404, "Deck instance not found")
    camp = await _campaign_or_404(inst["campaign_id"])
    if not _is_member(camp, user):
        raise HTTPException(403, "Not a member of this campaign.")
    return inst


@router.post("/cards/instances/{instance_id}/draw")
async def draw_cards(instance_id: str, body: DeckDrawIn,
                     user: dict = Depends(get_current_user)):
    inst = await db.deck_instances.find_one({"id": instance_id}, {"_id": 0})
    if not inst:
        raise HTTPException(404, "Deck instance not found")
    camp = await _campaign_or_404(inst["campaign_id"])
    is_gm = _is_gm(camp, user)
    if not is_gm and inst.get("mode") != "open":
        raise HTTPException(403, "This deck is GM-only · ask your GM to open it.")
    if not _is_member(camp, user):
        raise HTTPException(403, "Not a member of this campaign.")

    cards = deck_cards(inst["system_id"], inst["deck_id"]) or []
    drawn = list(inst.get("drawn_card_ids") or [])
    available = [c for c in cards if c["id"] not in drawn]
    if not available:
        raise HTTPException(400, "Deck is exhausted · shuffle to reuse.")

    n = max(1, min(body.count or 1, len(available)))
    rshuffle(available)
    taken = available[:n]
    log_entries: List[dict] = list(inst.get("log") or [])
    ts = now_iso()
    for c in taken:
        drawn.append(c["id"])
        log_entries.append({"by_uid": user["id"], "by_name": user["name"],
                              "card_id": c["id"], "card_name": c["name"], "ts": ts})

    await db.deck_instances.update_one(
        {"id": instance_id},
        {"$set": {"drawn_card_ids": drawn, "log": log_entries,
                  "updated_at": ts}}
    )
    payload = {"instance_id": instance_id, "cards": taken,
                "remaining": len(available) - n,
                "drawn_count": len(drawn), "by_name": user["name"]}
    # Real-time fan-out so any open table sheet sees the draw.
    if inst.get("session_id"):
        await broadcast(f"session:{inst['session_id']}",
                        {"type": "card:drawn", "data": payload})
    await broadcast(f"campaign:{inst['campaign_id']}",
                    {"type": "card:drawn", "data": payload})
    return payload


@router.post("/cards/instances/{instance_id}/shuffle")
async def shuffle_deck(instance_id: str, user: dict = Depends(get_current_user)):
    inst = await db.deck_instances.find_one({"id": instance_id}, {"_id": 0})
    if not inst:
        raise HTTPException(404, "Deck instance not found")
    camp = await _campaign_or_404(inst["campaign_id"])
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    await db.deck_instances.update_one(
        {"id": instance_id},
        {"$set": {"drawn_card_ids": [], "updated_at": now_iso()}}
    )
    if inst.get("session_id"):
        await broadcast(f"session:{inst['session_id']}",
                        {"type": "card:shuffled", "data": {"instance_id": instance_id}})
    return {"ok": True, "drawn_count": 0}


@router.post("/cards/instances/{instance_id}/mode")
async def set_mode(instance_id: str, mode: str,
                    user: dict = Depends(get_current_user)):
    if mode not in ("gm-only", "open"):
        raise HTTPException(400, "Mode must be 'gm-only' or 'open'.")
    inst = await db.deck_instances.find_one({"id": instance_id}, {"_id": 0})
    if not inst:
        raise HTTPException(404, "Deck instance not found")
    camp = await _campaign_or_404(inst["campaign_id"])
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    await db.deck_instances.update_one(
        {"id": instance_id}, {"$set": {"mode": mode, "updated_at": now_iso()}}
    )
    return {"ok": True, "mode": mode}


@router.delete("/cards/instances/{instance_id}")
async def delete_instance(instance_id: str, user: dict = Depends(get_current_user)):
    inst = await db.deck_instances.find_one({"id": instance_id}, {"_id": 0})
    if not inst:
        raise HTTPException(404, "Deck instance not found")
    camp = await _campaign_or_404(inst["campaign_id"])
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.deck_instances.delete_one({"id": instance_id})
    return {"ok": True, "deleted": res.deleted_count}
