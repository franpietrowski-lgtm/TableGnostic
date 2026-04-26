"""XP-Spend GM Approval Queue (V4.4 Phase H).

Players propose attribute / level / stat boosts funded by their unspent XP.
The proposal goes into `xp_pending` collection. The GM sees a queue and can
approve (apply + deduct XP) or reject (refund/no-op).

Endpoints:
    POST /api/characters/{cid}/xp-spend     — player proposes (returns pending row)
    GET  /api/campaigns/{cid}/xp-pending    — GM lists open proposals
    POST /api/xp-pending/{pid}/approve      — GM applies the change
    POST /api/xp-pending/{pid}/reject       — GM rejects (with reason)
    GET  /api/characters/{cid}/xp-pending   — owner sees their open proposals

Until approved, the character sheet's stats / attributes / level are NOT
modified — so live roll-resolution logic during play continues to read the
last GM-approved snapshot.

Per BESM 4E p.232: 1 XP = 1 Character Point at GM discretion. We hold the
proposed XP "in escrow" by recording it on the pending row but NOT debiting
xp_unspent until approval. (Simpler audit trail — no refund step needed.)
"""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["xp-approval"])


# ─────────── Pydantic ───────────

class XPSpendIn(BaseModel):
    """Player's proposal — what to change + what XP it costs."""
    cost: float = Field(gt=0, lt=200)
    reason: str = Field(min_length=1, max_length=500)
    # The change as a dotted-path patch (e.g. "stats.body" → +1 means
    # increase Body by 1 for `cost` XP). The backend stores the patch
    # verbatim and applies it on approve.
    change: Dict[str, Any] = Field(...)
    # Optional GM-friendly summary so the queue is readable at a glance.
    summary: Optional[str] = None


class RejectIn(BaseModel):
    reason: str = Field(default="", max_length=400)


# ─────────── Helpers ───────────

async def _character_or_404(cid: str) -> dict:
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    return ch


async def _is_gm(camp_id: str, user: dict) -> bool:
    camp = await db.campaigns.find_one({"id": camp_id}, {"_id": 0, "gm_id": 1})
    return bool(camp and (camp.get("gm_id") == user["id"] or user.get("role") == "admin"))


def _apply_change(ch: dict, change: Dict[str, Any]) -> Dict[str, Any]:
    """Mutate `ch` according to the change patch.

    Supported patches (V4.4 — keep narrow until we have UX for everything):
      * {"stats.body" | "stats.mind" | "stats.soul": +N | -N}
      * {"attribute_level": {"name": str, "delta": int}}
      * {"raise_total_points": int}   (1 XP = 1 CP)

    Returns the resulting `ch` dict (caller persists). Raises 400 on bad input.
    """
    if not isinstance(change, dict) or not change:
        raise HTTPException(400, "Empty change patch.")
    for k, v in change.items():
        if k in ("stats.body", "stats.mind", "stats.soul"):
            stat = k.split(".", 1)[1]
            try:
                delta = int(v)
            except Exception:
                raise HTTPException(400, f"Stat delta must be int, got {v!r}")
            ch["stats"][stat] = max(1, int(ch["stats"].get(stat, 1)) + delta)
        elif k == "attribute_level":
            if not isinstance(v, dict) or "name" not in v or "delta" not in v:
                raise HTTPException(400, "attribute_level needs {name, delta}")
            name = v["name"]
            try:
                delta = int(v["delta"])
            except Exception:
                raise HTTPException(400, "attribute_level.delta must be int")
            for a in ch.get("attributes", []):
                if a.get("name") == name:
                    a["level"] = max(1, int(a.get("level", 1)) + delta)
                    break
            else:
                raise HTTPException(400, f"No attribute named {name!r}")
        elif k == "raise_total_points":
            try:
                delta = int(v)
            except Exception:
                raise HTTPException(400, "raise_total_points must be int")
            ch["total_points"] = int(ch.get("total_points", 120)) + delta
        else:
            raise HTTPException(400, f"Unsupported change key: {k!r}. "
                                      "Allowed: stats.{body,mind,soul}, "
                                      "attribute_level, raise_total_points.")
    return ch


# ─────────── Endpoints ───────────

@router.post("/characters/{cid}/xp-spend")
async def propose_xp_spend(cid: str, body: XPSpendIn,
                            user: dict = Depends(get_current_user)):
    ch = await _character_or_404(cid)
    is_gm = await _is_gm(ch["campaign_id"], user)
    is_owner = ch.get("owner_id") == user["id"]
    if not (is_gm or is_owner):
        raise HTTPException(403, "Only the character owner or GM may propose XP spends.")
    unspent = float(ch.get("xp_unspent", 0.0))
    if body.cost > unspent + 0.001:
        raise HTTPException(400, f"Insufficient unspent XP ({unspent}). "
                                   f"Asked for {body.cost}.")
    # Validate patch shape early so the GM doesn't see broken proposals.
    _apply_change({"stats": dict(ch["stats"]),
                   "attributes": [dict(a) for a in ch.get("attributes", [])],
                   "total_points": ch.get("total_points", 120)},
                   body.change)

    doc = {
        "id": new_id(),
        "character_id": cid,
        "character_name": ch["name"],
        "campaign_id": ch["campaign_id"],
        "owner_id": ch.get("owner_id"),
        "owner_name": ch.get("owner_name"),
        "proposed_by_id": user["id"],
        "proposed_by_name": user["name"],
        "cost": float(body.cost),
        "reason": body.reason,
        "change": body.change,
        "summary": body.summary or body.reason,
        "status": "pending",  # pending | approved | rejected
        "gm_decision": None,
        "decided_at": None,
        "created_at": now_iso(),
    }
    await db.xp_pending.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{cid}/xp-pending")
async def list_campaign_xp_pending(cid: str,
                                    user: dict = Depends(get_current_user)):
    if not await _is_gm(cid, user):
        raise HTTPException(403, "GM only.")
    rows = await db.xp_pending.find({"campaign_id": cid, "status": "pending"},
                                      {"_id": 0}).sort("created_at", 1).to_list(200)
    return rows


@router.get("/characters/{cid}/xp-pending")
async def list_character_xp_pending(cid: str,
                                     user: dict = Depends(get_current_user)):
    ch = await _character_or_404(cid)
    if ch.get("owner_id") != user["id"] and not await _is_gm(ch["campaign_id"], user):
        raise HTTPException(403, "Owner or GM only.")
    rows = await db.xp_pending.find({"character_id": cid},
                                      {"_id": 0}).sort("created_at", -1).to_list(60)
    return rows


@router.post("/xp-pending/{pid}/approve")
async def approve_xp_spend(pid: str,
                            user: dict = Depends(get_current_user)):
    pend = await db.xp_pending.find_one({"id": pid}, {"_id": 0})
    if not pend:
        raise HTTPException(404, "Proposal not found")
    if not await _is_gm(pend["campaign_id"], user):
        raise HTTPException(403, "GM only.")
    if pend["status"] != "pending":
        raise HTTPException(400, f"Proposal already {pend['status']}.")

    ch = await _character_or_404(pend["character_id"])
    cost = float(pend["cost"])
    unspent = float(ch.get("xp_unspent", 0.0))
    if cost > unspent + 0.001:
        raise HTTPException(400, f"Insufficient unspent XP ({unspent}) "
                                   f"to cover proposal ({cost}).")
    # Apply + persist.
    _apply_change(ch, pend["change"])
    new_unspent = round(unspent - cost, 2)
    xp_entry = {
        "id": new_id(),
        "amount": -cost,
        "reason": f"XP spend approved: {pend['summary']}",
        "source": "convert",
        "session_id": None,
        "by_gm_id": user["id"],
        "by_gm_name": user["name"],
        "awarded_at": now_iso(),
        "applied_change": pend["change"],
    }
    await db.characters.update_one(
        {"id": ch["id"]},
        {
            "$set": {
                "stats": ch["stats"],
                "attributes": ch["attributes"],
                "total_points": ch["total_points"],
                "xp_unspent": new_unspent,
            },
            "$push": {"xp_log": xp_entry},
        },
    )
    await db.xp_pending.update_one(
        {"id": pid},
        {"$set": {"status": "approved",
                  "gm_decision": "approved",
                  "decided_by": user["name"],
                  "decided_at": now_iso()}},
    )
    return {"ok": True, "approved": True, "character_id": ch["id"],
            "xp_unspent": new_unspent, "applied_change": pend["change"]}


@router.post("/xp-pending/{pid}/reject")
async def reject_xp_spend(pid: str, body: RejectIn,
                           user: dict = Depends(get_current_user)):
    pend = await db.xp_pending.find_one({"id": pid}, {"_id": 0})
    if not pend:
        raise HTTPException(404, "Proposal not found")
    if not await _is_gm(pend["campaign_id"], user):
        raise HTTPException(403, "GM only.")
    if pend["status"] != "pending":
        raise HTTPException(400, f"Proposal already {pend['status']}.")
    await db.xp_pending.update_one(
        {"id": pid},
        {"$set": {"status": "rejected",
                  "gm_decision": "rejected",
                  "decided_by": user["name"],
                  "decided_at": now_iso(),
                  "rejection_reason": body.reason}},
    )
    return {"ok": True, "rejected": True, "reason": body.reason}
