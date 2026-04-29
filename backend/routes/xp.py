"""Experience Points (BESM 4E p.232 — Advancement).

This module implements the XP economy described in the BESM 4E Advancement
chapter: GMs award 1–3 XP per session by default (1 = light, 2 = standard,
3 = climactic), with bonus XP for major milestones. XP can later be
converted to Character Points 1:1 by the GM (book guidance: 1 XP per CP
spent on advancement).

V4.4 design — engagement-bonus scorecard:
  * Every session, /api/sessions/{sid}/xp/suggest tallies each PC's
    engagement quanta (chat lines weighted IC > OOC, dice rolls, journal
    entries, GM-flagged spotlights) and returns a *suggested* per-PC XP
    award.
  * GMs review the scorecard, edit values, and explicitly Commit. There
    is no auto-award path. (User choice — V4.4 ask_human #2 = a.)

XP audit trail lives at character.xp_log[] and character.xp_total /
character.xp_unspent (a float; the engagement bonus is fractional).
"""
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["xp"])


# ─────────────────────────── Pydantic models ────────────────────────────

class XPAwardIn(BaseModel):
    amount: float = Field(gt=-100, lt=100)  # negatives allowed for corrections
    reason: str = Field(min_length=1, max_length=500)
    session_id: Optional[str] = None
    source: Literal[
        "gm_award", "session_baseline", "engagement_bonus",
        "milestone", "correction", "convert",
    ] = "gm_award"


class XPConvertIn(BaseModel):
    """Convert unspent XP to Character Points (raises total_points)."""
    amount: float = Field(gt=0, lt=200)
    reason: str = Field(default="XP → Character Points (Advancement)", max_length=300)


class XPCommitIn(BaseModel):
    """Bulk-commit a session's XP scorecard.
    Each item: {character_id, base, bonus, note}. base + bonus is awarded
    in a single xp_log row tagged source=session_baseline."""
    awards: List[Dict] = Field(default_factory=list)


# ──────────────────────────── Engagement scoring ────────────────────────

# Per-quantum weights. All caps tunable; total bonus is hard-capped per session.
# Values chosen to keep "the point system loose" per BESM 4E p.232: even
# a heavily-engaged player rarely earns more than +1.0 over the GM baseline.
WEIGHTS = {
    "chat_ic":     0.05,   # in-character chat / action lines
    "chat_ooc":    0.01,   # out-of-character (kept low per user choice 'c')
    "dice_macro":  0.10,   # dice rolls posted by this character
    "journal":     0.25,   # folio.journal entries during the session
    "spotlight":   0.50,   # GM-flagged "you carried this scene" toggle
}
BONUS_CAP_PER_SESSION = 2.0
DEFAULT_BASELINE = 2.0  # BESM 4E p.232 "standard" session = 2 XP


def _engagement_score(counts: Dict[str, int]) -> tuple[float, Dict[str, float]]:
    """Tally a character's per-session engagement bonus from raw counts.

    Returns (bonus, breakdown) where breakdown is a per-quantum {label: xp}
    map for GM transparency. Total is floored at 0 and capped at
    BONUS_CAP_PER_SESSION."""
    breakdown: Dict[str, float] = {}
    for k, w in WEIGHTS.items():
        n = int(counts.get(k, 0))
        if n > 0:
            breakdown[k] = round(n * w, 2)
    raw = sum(breakdown.values())
    return min(BONUS_CAP_PER_SESSION, max(0.0, round(raw, 2))), breakdown


async def _session_window(sid: str) -> tuple[Optional[str], Optional[str]]:
    """Return (start_iso, end_iso) for a session — start = session.created_at,
    end = newest chat_log timestamp or now."""
    s = await db.sessions.find_one({"id": sid}, {"_id": 0, "created_at": 1})
    if not s:
        return None, None
    start = s.get("created_at")
    last = await db.chat_logs.find({"session_id": sid}, {"_id": 0, "created_at": 1}) \
                              .sort("created_at", -1).limit(1).to_list(1)
    end = last[0]["created_at"] if last else now_iso()
    return start, end


# ─────────────────────────── Endpoints ────────────────────────────

@router.get("/characters/{cid}/xp")
async def get_xp(cid: str, user: dict = Depends(get_current_user)):
    """Return the character's XP totals + audit log."""
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    return {
        "character_id": cid,
        "xp_total": float(ch.get("xp_total", 0.0)),
        "xp_unspent": float(ch.get("xp_unspent", 0.0)),
        "xp_log": ch.get("xp_log", []),
    }


@router.post("/characters/{cid}/xp")
async def award_xp(cid: str, body: XPAwardIn,
                   user: dict = Depends(get_current_user)):
    """GM-only: award (or deduct) XP on a single character, with reason."""
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may award XP.")

    entry = {
        "id": new_id(),
        "amount": float(body.amount),
        "reason": body.reason,
        "source": body.source,
        "session_id": body.session_id,
        "by_gm_id": user["id"],
        "by_gm_name": user["name"],
        "awarded_at": now_iso(),
    }
    new_total = float(ch.get("xp_total", 0.0)) + float(body.amount)
    new_unspent = float(ch.get("xp_unspent", 0.0)) + float(body.amount)
    await db.characters.update_one(
        {"id": cid},
        {
            "$push": {"xp_log": entry},
            "$set": {"xp_total": new_total, "xp_unspent": new_unspent},
        },
    )
    return {"ok": True, "entry": entry, "xp_total": new_total, "xp_unspent": new_unspent}


@router.post("/characters/{cid}/xp/convert")
async def convert_xp_to_cp(cid: str, body: XPConvertIn,
                            user: dict = Depends(get_current_user)):
    """Convert unspent XP to Character Points (total_points += amount).

    BESM 4E p.232: 1 XP = 1 Character Point at the GM's discretion. Both
    GM and the character's owner may initiate; GM-or-admin override
    enforces the rule.
    """
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    is_gm = camp and (camp["gm_id"] == user["id"] or user.get("role") == "admin")
    is_owner = ch.get("owner_id") == user["id"]
    if not (is_gm or is_owner):
        raise HTTPException(403, "Only the character's owner or GM may spend XP.")
    unspent = float(ch.get("xp_unspent", 0.0))
    if body.amount > unspent + 0.001:
        raise HTTPException(400, f"Insufficient unspent XP ({unspent}). Asked for {body.amount}.")

    new_total_pts = int(ch.get("total_points", 120)) + int(round(body.amount))
    new_unspent = round(unspent - body.amount, 2)
    entry = {
        "id": new_id(),
        "amount": -float(body.amount),
        "reason": body.reason,
        "source": "convert",
        "session_id": None,
        "by_gm_id": user["id"],
        "by_gm_name": user["name"],
        "awarded_at": now_iso(),
        "converted_to_points": int(round(body.amount)),
    }
    await db.characters.update_one(
        {"id": cid},
        {
            "$push": {"xp_log": entry},
            "$set": {"xp_unspent": new_unspent, "total_points": new_total_pts},
        },
    )
    return {"ok": True, "entry": entry,
            "xp_unspent": new_unspent, "total_points": new_total_pts}


@router.get("/sessions/{sid}/xp/suggest")
async def suggest_session_xp(sid: str, user: dict = Depends(get_current_user)):
    """GM-only: for every published character in the session's campaign,
    tally engagement quanta within the session window and return a
    suggested XP award (base + bonus). The GM reviews & commits via
    /sessions/{sid}/xp/commit."""
    sess = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not sess:
        raise HTTPException(404, "Session not found")
    camp = await db.campaigns.find_one({"id": sess["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may view the XP scorecard.")

    start, end = await _session_window(sid)
    chars = await db.characters.find({"campaign_id": camp["id"]},
                                      {"_id": 0}).to_list(200)
    rows: List[Dict] = []
    for ch in chars:
        if not ch.get("published"):
            continue
        # Counts within the session window. user_name is the speaker
        # column we wrote in seed/replay; matches PC `name` for our seed.
        ic_q = {"session_id": sid, "user_name": ch["name"],
                "kind": {"$in": ["chat", "action"]}}
        ooc_q = {"session_id": sid, "user_name": ch["name"], "kind": "ooc"}
        ic_count = await db.chat_logs.count_documents(ic_q)
        ooc_count = await db.chat_logs.count_documents(ooc_q)
        dice_count = await db.dice_rolls.count_documents(
            {"session_id": sid, "$or": [
                {"character_id": ch["id"]},
                {"user_name": ch["name"]},
            ]}
        )
        # Journal entries written in this session window (folio.journal items
        # whose date OR created_at falls inside [start, end]).
        journal_count = 0
        for j in (ch.get("folio", {}) or {}).get("journal", []) or []:
            ts = j.get("created_at") or j.get("date")
            if not ts:
                continue
            try:
                if (not start or ts >= start[:10]) and (not end or ts <= end[:19] + "Z"):
                    journal_count += 1
            except Exception:
                pass

        counts = {
            "chat_ic": ic_count,
            "chat_ooc": ooc_count,
            "dice_macro": dice_count,
            "journal": journal_count,
            "spotlight": 0,  # GM toggles in UI before commit
        }
        bonus, breakdown = _engagement_score(counts)
        rows.append({
            "character_id": ch["id"],
            "character_name": ch["name"],
            "owner_name": ch.get("owner_name"),
            "token_color": ch.get("token_color", ""),
            "counts": counts,
            "weights": WEIGHTS,
            "bonus": bonus,
            "bonus_cap": BONUS_CAP_PER_SESSION,
            "bonus_breakdown": breakdown,
            "suggested_base": DEFAULT_BASELINE,
            "suggested_total": round(DEFAULT_BASELINE + bonus, 2),
        })

    return {
        "session_id": sid,
        "campaign_id": camp["id"],
        "session_window": {"start": start, "end": end},
        "rows": rows,
        "default_baseline": DEFAULT_BASELINE,
        "bonus_cap": BONUS_CAP_PER_SESSION,
        "weights": WEIGHTS,
        "guidance": (
            "BESM 4E p.232 — light session 1 XP, standard 2 XP, climactic 3 XP. "
            "Engagement bonus is loose: each row is a fraction; total bonus is "
            "capped at +%s. Suggest-only; nothing commits until you click Commit."
            % BONUS_CAP_PER_SESSION
        ),
    }


@router.post("/sessions/{sid}/xp/commit")
async def commit_session_xp(sid: str, body: XPCommitIn,
                             user: dict = Depends(get_current_user)):
    """GM-only: bulk-award the GM-edited scorecard. One xp_log row per
    character; the row carries `base`, `bonus`, and combined `amount`."""
    sess = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not sess:
        raise HTTPException(404, "Session not found")
    camp = await db.campaigns.find_one({"id": sess["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may commit the scorecard.")

    committed = []
    for award in body.awards:
        cid = award.get("character_id")
        if not cid:
            continue
        base = float(award.get("base", 0))
        bonus = float(award.get("bonus", 0))
        amount = round(base + bonus, 2)
        if abs(amount) < 0.001:
            continue
        ch = await db.characters.find_one({"id": cid}, {"_id": 0})
        if not ch or ch.get("campaign_id") != camp["id"]:
            continue
        entry = {
            "id": new_id(),
            "amount": amount,
            "base": base,
            "bonus": bonus,
            "reason": award.get("note") or sess.get("title", "Session XP"),
            "source": "session_baseline",
            "session_id": sid,
            "by_gm_id": user["id"],
            "by_gm_name": user["name"],
            "awarded_at": now_iso(),
        }
        new_total = float(ch.get("xp_total", 0.0)) + amount
        new_unspent = float(ch.get("xp_unspent", 0.0)) + amount
        await db.characters.update_one(
            {"id": cid},
            {
                "$push": {"xp_log": entry},
                "$set": {"xp_total": round(new_total, 2),
                         "xp_unspent": round(new_unspent, 2)},
            },
        )
        committed.append({
            "character_id": cid,
            "amount": amount,
            "xp_total": round(new_total, 2),
            "xp_unspent": round(new_unspent, 2),
        })
    return {"ok": True, "committed": committed, "session_id": sid}


@router.get("/campaigns/{cid}/xp/ledger")
async def campaign_xp_ledger(cid: str, user: dict = Depends(get_current_user)):
    """Campaign-level XP ledger.

    Rolls up every character's `xp_log[]` into a single reverse-chronological
    feed with per-character totals + campaign totals. GM/admin-only so
    players can't audit the absolute XP pool of every PC.

    Returns:
      - characters[]: {id, name, owner_name, xp_total, xp_unspent, converted}
      - entries[]:    {awarded_at, character_id, character_name, amount,
                       base, bonus, reason, source, session_id, by_gm_name}
                       reverse-chrono
      - totals: {awarded, converted, unspent}
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may view the campaign ledger.")

    chars = await db.characters.find({"campaign_id": cid}, {"_id": 0}).to_list(500)

    characters_out: List[Dict] = []
    entries: List[Dict] = []
    total_awarded = 0.0
    total_converted = 0.0
    total_unspent = 0.0

    for ch in chars:
        xp_total = float(ch.get("xp_total", 0.0))
        xp_unspent = float(ch.get("xp_unspent", 0.0))
        # Converted = total awarded minus unspent minus positive log sum that's
        # still unspent. Practical derivation: sum of entries where
        # source=="convert" (stored as negative amounts).
        converted = 0.0
        for e in ch.get("xp_log", []) or []:
            if e.get("source") == "convert":
                converted += abs(float(e.get("amount", 0.0)))
        characters_out.append({
            "id": ch["id"],
            "name": ch.get("name"),
            "owner_name": ch.get("owner_name"),
            "token_color": ch.get("token_color", ""),
            "xp_total": round(xp_total, 2),
            "xp_unspent": round(xp_unspent, 2),
            "xp_converted": round(converted, 2),
        })
        total_awarded += xp_total
        total_converted += converted
        total_unspent += xp_unspent

        for e in ch.get("xp_log", []) or []:
            entries.append({
                "id": e.get("id"),
                "awarded_at": e.get("awarded_at"),
                "character_id": ch["id"],
                "character_name": ch.get("name"),
                "owner_name": ch.get("owner_name"),
                "amount": float(e.get("amount", 0.0)),
                "base": float(e.get("base", 0.0)) if "base" in e else None,
                "bonus": float(e.get("bonus", 0.0)) if "bonus" in e else None,
                "reason": e.get("reason"),
                "source": e.get("source"),
                "session_id": e.get("session_id"),
                "by_gm_name": e.get("by_gm_name"),
                "converted_to_points": e.get("converted_to_points"),
            })

    entries.sort(key=lambda x: (x.get("awarded_at") or ""), reverse=True)

    return {
        "campaign_id": cid,
        "campaign_name": camp.get("name"),
        "characters": characters_out,
        "entries": entries,
        "totals": {
            "awarded": round(total_awarded, 2),
            "converted": round(total_converted, 2),
            "unspent": round(total_unspent, 2),
        },
        "weights": WEIGHTS,
        "bonus_cap": BONUS_CAP_PER_SESSION,
        "default_baseline": DEFAULT_BASELINE,
    }
