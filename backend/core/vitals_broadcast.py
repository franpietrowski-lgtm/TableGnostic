"""V6.25.50 — Vitals push-broadcast helper.

Shared by every code path that mutates a character's live HP/EP
(channels.py BESM bundle spend + undo, advancement.py Anime 5E damage,
direct admin edits, etc.). Computes the same percentages the
Battlemap's GET /map/vitals endpoint would return, then broadcasts a
`map:vitals` WebSocket event to every open session whose map
references the affected character.

Why centralised: the existing polling loop (every 6s) is wasteful
once we have a push channel. With this helper in place the frontend
can drop polling to a 30-second safety net (heartbeat for stale
clients) and otherwise update tokens instantly when a spend lands.

API:
    await broadcast_character_vitals(character_id)
    await broadcast_character_vitals(character_id, fresh_character=row)

Pass `fresh_character` when you already have the updated document
in scope — saves a round-trip to Mongo.
"""
from __future__ import annotations
from typing import Optional

from core.bus import broadcast
from core.db import db


def _pc_vitals_for(character: dict) -> dict:
    """Mirrors routes/battlemap.py:_pc_vitals_for — kept in sync so
    polled and pushed vitals look identical to the client. (Both
    helpers will eventually call this one once we refactor.)"""
    derived = character.get("derived") or {}
    folio = character.get("folio") or {}

    hp_max = (derived.get("health_points")
              or folio.get("hp_max")
              or folio.get("health_points_max")
              or 0)
    hp_cur = folio.get("health_points")
    if hp_cur is None:
        hp_cur = folio.get("hp_current") or folio.get("hp_now")
    if hp_cur is None:
        dnd = folio.get("dnd5e_state") or folio.get("dnd_state") or {}
        hp_cur = dnd.get("hp_current")
        if not hp_max:
            hp_max = dnd.get("hp_max") or 0

    ep_max = (derived.get("energy_points")
              or folio.get("ep_max")
              or folio.get("energy_points_max")
              or 0)
    ep_cur = folio.get("energy_points")
    if ep_cur is None:
        ep_cur = folio.get("ep_current")
    if ep_cur is None:
        anime = folio.get("anime5e_state") or {}
        ep_cur = anime.get("ep_current")
        if not ep_max:
            ep_max = anime.get("ep_max") or 0

    def _pct(cur, mx):
        try:
            mx = int(mx or 0)
            if mx <= 0:
                return 100
            cur = int(cur if cur is not None else mx)
            return max(0, min(100, int(round(cur / mx * 100))))
        except (TypeError, ValueError):
            return 100

    return {
        "hp_pct": _pct(hp_cur, hp_max),
        "ep_pct": _pct(ep_cur, ep_max),
        "hp_current": hp_cur if hp_cur is not None else hp_max,
        "hp_max": hp_max,
        "ep_current": ep_cur if ep_cur is not None else ep_max,
        "ep_max": ep_max,
    }


async def broadcast_character_vitals(
    character_id: str,
    fresh_character: Optional[dict] = None,
) -> None:
    """Push a `map:vitals` event to every session whose battlemap has
    a token bound to this character. Idempotent and best-effort —
    never raise; the spend/damage path that called us is more
    important than a delivery hiccup.
    """
    if not character_id:
        return
    try:
        char = fresh_character
        if char is None:
            char = await db.characters.find_one(
                {"id": character_id},
                {"_id": 0, "id": 1, "derived": 1, "folio": 1},
            )
        if not char:
            return

        vitals = _pc_vitals_for(char)
        payload = {character_id: vitals}

        # Find every battlemap that references this character on at
        # least one token. The collection is small (one doc per
        # session) and tokens is an embedded array — `$elemMatch` is
        # cheap and avoids per-token unwinding.
        cursor = db.battlemaps.find(
            {"tokens": {"$elemMatch": {"character_id": character_id}}},
            {"_id": 0, "session_id": 1},
        )
        async for row in cursor:
            sid = row.get("session_id")
            if not sid:
                continue
            await broadcast(sid, {"type": "map:vitals", "data": payload})
    except Exception:
        # Hard rule: vitals broadcasting is a refresh nicety. If it
        # blows up we silently swallow rather than killing the spend
        # response path that called us.
        return
