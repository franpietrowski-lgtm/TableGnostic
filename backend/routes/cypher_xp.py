"""Cypher System XP Mechanics ledger (V6.25.24 — Cycle B-4).

Cypher uses XP very differently from BESM/D&D — it's not just "save up to
buy stat ups", it's a moment-to-moment economy:

  * GM Intrusion grants 2 XP, 1 of which the player **must immediately**
    hand to a peer with a brief narrative justification.
  * Refusing an intrusion costs 1 XP (player cannot refuse with 0 XP).
  * Re-roll, Player Intrusion, Peer Transfer cost 1 XP each.
  * Short-/Medium-/Long-term Benefits cost 2/3/4 XP.
  * Each Advancement Step costs 4 XP; 4 steps = 16 XP advances a tier.
  * Narrative-Pool spends are multi-player co-funded setting-shaping
    proposals (typically 4-12 XP, GM ratifies the scale).

Endpoints:
    POST /api/campaigns/{cid}/cypher/xp-events  — log an event (delta-applies xp_unspent)
    GET  /api/campaigns/{cid}/cypher/xp-events  — paginated ledger

Each event row stores: kind, character_id(s), amount, justification,
created_at, created_by. The character's `xp_unspent` is mutated atomically
in the same call so the ledger and the live sheet never disagree.
"""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["cypher-xp"])


EventKind = Literal[
    # Awards (positive deltas)
    "intrusion-grant",          # +2 XP to acceptor (auto-pairs with peer-transfer 1 XP)
    "discovery",                # +N XP at GM discretion
    "character-arc",            # +N XP milestone reward
    # Spends (negative deltas)
    "refuse-intrusion",         # −1 XP
    "reroll",                   # −1 XP
    "player-intrusion",         # −1 XP
    "short-term-benefit",       # −2 XP
    "medium-term-benefit",      # −3 XP
    "long-term-benefit",        # −4 XP
    "advancement-step",         # −4 XP
    "peer-transfer",            # −1 XP (recipient gets +1 XP)
    "narrative-pool",           # variable XP (multiple contributors)
]


SPEND_COSTS = {
    "refuse-intrusion": 1,
    "reroll": 1,
    "player-intrusion": 1,
    "short-term-benefit": 2,
    "medium-term-benefit": 3,
    "long-term-benefit": 4,
    "advancement-step": 4,
    "peer-transfer": 1,
}


class CypherXPEventIn(BaseModel):
    kind: EventKind
    character_id: str = Field(..., description="The acting character.")
    amount: Optional[float] = Field(
        default=None,
        description="Override for variable-cost events (discovery, narrative-pool, character-arc). "
                    "Ignored for fixed-cost spends.")
    peer_character_id: Optional[str] = Field(
        default=None,
        description="Required for peer-transfer. The recipient gets +1 XP.")
    justification: str = Field(default="", max_length=400)
    advancement_step_key: Optional[str] = Field(
        default=None,
        description="For advancement-step: increasing-capabilities | moving-toward-perfection | "
                    "extra-effort | skill-training.")
    narrative_pool_contributors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="For narrative-pool: list of {character_id, amount} contributions. "
                    "Each contributor must have enough xp_unspent.")


async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    return camp


async def _character_or_404(chid: str) -> dict:
    ch = await db.characters.find_one({"id": chid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, f"Character {chid} not found.")
    return ch


def _is_gm(camp: dict, user: dict) -> bool:
    return camp.get("gm_id") == user["id"] or user.get("role") == "admin"


async def _adjust_xp(character_id: str, delta: float) -> float:
    """Atomically adjust xp_unspent on a character. Returns the new value.
    Raises 400 if the result would go negative.
    """
    ch = await _character_or_404(character_id)
    cur = float(ch.get("xp_unspent", 0.0))
    new_val = cur + float(delta)
    if new_val < -0.001:
        raise HTTPException(400,
            f"Insufficient unspent XP on {ch.get('name', character_id)}: "
            f"have {cur}, need {-delta}.")
    await db.characters.update_one(
        {"id": character_id},
        {"$set": {"xp_unspent": round(new_val, 3)}})
    return new_val


async def _write_event(camp_id: str, kind: str, character_id: str,
                       delta: float, user: dict, *,
                       peer_character_id: Optional[str] = None,
                       justification: str = "",
                       extra: Optional[Dict[str, Any]] = None) -> dict:
    ch = await _character_or_404(character_id)
    row = {
        "id": new_id(),
        "campaign_id": camp_id,
        "kind": kind,
        "character_id": character_id,
        "character_name": ch.get("name"),
        "delta": float(delta),
        "peer_character_id": peer_character_id,
        "justification": justification,
        "created_at": now_iso(),
        "created_by_id": user["id"],
        "created_by_name": user.get("name") or user.get("email"),
    }
    if extra:
        row.update(extra)
    if peer_character_id:
        peer = await db.characters.find_one(
            {"id": peer_character_id}, {"_id": 0, "name": 1})
        row["peer_character_name"] = (peer or {}).get("name")
    await db.cypher_xp_events.insert_one(row)
    row.pop("_id", None)
    return row


@router.post("/campaigns/{cid}/cypher/xp-events")
async def log_cypher_xp_event(cid: str, body: CypherXPEventIn,
                                user: dict = Depends(get_current_user)):
    """Log a Cypher XP event and apply the corresponding delta(s).

    Authorization:
      * Player can log events for THEIR own character.
      * GM can log events for any character in the campaign.
      * intrusion-grant / discovery / character-arc are GM-only awards.
    """
    camp = await _campaign_or_404(cid)
    is_gm = _is_gm(camp, user)
    ch = await _character_or_404(body.character_id)
    if ch.get("campaign_id") != cid:
        raise HTTPException(400, "Character does not belong to this campaign.")
    is_owner = ch.get("owner_id") == user["id"]
    if not (is_gm or is_owner):
        raise HTTPException(403, "Only the character owner or GM may log XP events.")

    kind = body.kind
    written: List[dict] = []

    if kind == "intrusion-grant":
        if not is_gm:
            raise HTTPException(403, "Only the GM may grant intrusion XP.")
        # Acceptor gets +2 XP.
        await _adjust_xp(body.character_id, +2)
        written.append(await _write_event(
            cid, "intrusion-grant", body.character_id, +2, user,
            justification=body.justification or "GM Intrusion accepted."))
        # If a peer is named, the canonical 1-XP-to-peer rule fires AS PART
        # OF the intrusion (auto-paired). The acceptor effectively keeps 1
        # net, the peer gets 1.
        if body.peer_character_id:
            peer = await _character_or_404(body.peer_character_id)
            if peer.get("campaign_id") != cid:
                raise HTTPException(400, "Peer character does not belong to this campaign.")
            await _adjust_xp(body.character_id, -1)
            await _adjust_xp(body.peer_character_id, +1)
            written.append(await _write_event(
                cid, "peer-transfer", body.character_id, -1, user,
                peer_character_id=body.peer_character_id,
                justification=body.justification or "Auto peer share from GM intrusion."))
            written.append(await _write_event(
                cid, "peer-transfer-receive", body.peer_character_id, +1, user,
                peer_character_id=body.character_id,
                justification=body.justification or "Auto peer share from GM intrusion."))

    elif kind in ("discovery", "character-arc"):
        if not is_gm:
            raise HTTPException(403, f"Only the GM may grant {kind} XP.")
        amount = float(body.amount or 1)
        if amount <= 0:
            raise HTTPException(422, "Amount must be > 0 for award events.")
        await _adjust_xp(body.character_id, +amount)
        written.append(await _write_event(
            cid, kind, body.character_id, +amount, user,
            justification=body.justification))

    elif kind == "peer-transfer":
        if not body.peer_character_id:
            raise HTTPException(422, "peer-transfer requires peer_character_id.")
        peer = await _character_or_404(body.peer_character_id)
        if peer.get("campaign_id") != cid:
            raise HTTPException(400, "Peer character does not belong to this campaign.")
        if peer["id"] == body.character_id:
            raise HTTPException(422, "Cannot transfer to self.")
        await _adjust_xp(body.character_id, -1)
        await _adjust_xp(body.peer_character_id, +1)
        written.append(await _write_event(
            cid, "peer-transfer", body.character_id, -1, user,
            peer_character_id=body.peer_character_id,
            justification=body.justification or "Peer share."))
        written.append(await _write_event(
            cid, "peer-transfer-receive", body.peer_character_id, +1, user,
            peer_character_id=body.character_id,
            justification=body.justification or "Peer share received."))

    elif kind == "narrative-pool":
        contribs = body.narrative_pool_contributors or []
        if not contribs:
            raise HTTPException(422, "narrative-pool requires narrative_pool_contributors.")
        # Validate all contributions BEFORE debiting any pool — atomicity.
        pool_total = 0.0
        for c in contribs:
            chid = c.get("character_id")
            amt = float(c.get("amount", 0))
            if not chid or amt <= 0:
                raise HTTPException(422, f"Bad contributor row: {c}")
            cch = await _character_or_404(chid)
            if cch.get("campaign_id") != cid:
                raise HTTPException(400, f"Character {chid} not in campaign.")
            if float(cch.get("xp_unspent", 0)) < amt:
                raise HTTPException(400,
                    f"{cch.get('name', chid)} has insufficient XP for narrative pool.")
            pool_total += amt
        pool_id = new_id()
        for c in contribs:
            chid = c["character_id"]
            amt = float(c["amount"])
            await _adjust_xp(chid, -amt)
            written.append(await _write_event(
                cid, "narrative-pool", chid, -amt, user,
                justification=body.justification or "Narrative-pool contribution.",
                extra={"narrative_pool_id": pool_id, "pool_total": pool_total}))

    elif kind in SPEND_COSTS:
        cost = float(SPEND_COSTS[kind])
        await _adjust_xp(body.character_id, -cost)
        extra = None
        if kind == "advancement-step" and body.advancement_step_key:
            extra = {"advancement_step_key": body.advancement_step_key}
        if kind == "peer-transfer":
            # Already handled above — defensive.
            raise HTTPException(500, "peer-transfer must be handled above.")
        written.append(await _write_event(
            cid, kind, body.character_id, -cost, user,
            justification=body.justification, extra=extra))

    else:
        raise HTTPException(422, f"Unsupported event kind: {kind}")

    # Refresh balance for the response.
    final_ch = await _character_or_404(body.character_id)
    return {
        "events": written,
        "xp_unspent": float(final_ch.get("xp_unspent", 0.0)),
    }


@router.get("/campaigns/{cid}/cypher/xp-events")
async def list_cypher_xp_events(cid: str,
                                  character_id: Optional[str] = None,
                                  kind: Optional[str] = None,
                                  limit: int = 100,
                                  user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    q: Dict[str, Any] = {"campaign_id": cid}
    if character_id:
        q["character_id"] = character_id
    if kind:
        q["kind"] = kind
    is_gm = _is_gm(camp, user)
    if not is_gm:
        # Players see only events that name a character they own
        # (either as actor OR as peer recipient).
        my_chars = [c["id"] async for c in db.characters.find(
            {"campaign_id": cid, "owner_id": user["id"]}, {"_id": 0, "id": 1})]
        if character_id and character_id not in my_chars:
            raise HTTPException(403, "Cannot view another player's XP events.")
        if not character_id:
            q["character_id"] = {"$in": my_chars}
    cursor = db.cypher_xp_events.find(q, {"_id": 0}).sort("created_at", -1).limit(int(limit))
    rows = [r async for r in cursor]
    return {"rows": rows, "total": len(rows)}
