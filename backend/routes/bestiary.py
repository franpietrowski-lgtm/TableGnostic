"""V6.25.57 — Phase F: GM Bestiary endpoint.

Returns a unified list of monsters/creatures the GM may spawn onto the
Battlemap as NPC tokens. Aggregates:
  • System-native bestiaries (D&D 5E MONSTERS · Anime 5E MONSTERS ·
    Cypher BESTIARY · BESM has no canon monster list, falls through).
  • Custom Reference rows the GM has authored on this campaign whose
    `kind` is in the entity set (monster / creature / npc).

Returns a flat array of `{id, name, system?, source, cr?, hp?, ac?,
type?, atks?, page?, tooltip, color}` rows the BattlemapSidebar can
render & spawn from.

Endpoint:
  GET /api/campaigns/{cid}/bestiary[?q=&limit=]
      → GM / admin only — players don't get to spoil the encounter table.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.db import db
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["bestiary"])


def _color_for(cr) -> str:
    """Pick a token tint band based on CR / level. Mirrors the existing
    landing-page palette so a CR 1/4 reads green and a CR 17 reads rose."""
    try:
        n = float(cr) if cr is not None else 1
    except (TypeError, ValueError):
        n = 1
    if n < 1:    return "#7FB069"   # leaf — chaff
    if n < 5:    return "#C8A34A"   # gold — adventure-tier
    if n < 11:   return "#E03A8E"   # rose — heroic
    if n < 17:   return "#7A88C7"   # arcane — paragon
    return "#B22222"                # rust — apocalyptic


def _row_from_dnd_monster(m: Dict[str, Any]) -> Dict[str, Any]:
    cr = m.get("cr")
    return {
        "id": f"dnd5e:{m['name'].lower().replace(' ', '-')}",
        "name": m["name"],
        "system": "dnd-5e",
        "source": "srd",
        "cr": cr,
        "hp": m.get("hp"),
        "ac": m.get("ac"),
        "type": m.get("type"),
        "size": m.get("size"),
        "speed": m.get("speed"),
        "atks": m.get("atks"),
        "page": m.get("page"),
        "color": _color_for(cr),
        "tooltip": f"{m['name']} · CR {cr} · {m.get('type','?')} · HP {m.get('hp','?')} · AC {m.get('ac','?')}",
    }


def _row_from_anime_monster(m: Dict[str, Any]) -> Dict[str, Any]:
    r = _row_from_dnd_monster(m)
    r["id"] = f"anime5e:{m['name'].lower().replace(' ', '-')}"
    r["system"] = "anime-5e"
    return r


def _row_from_cypher(c: Dict[str, Any]) -> Dict[str, Any]:
    lvl = c.get("level")
    return {
        "id": f"cypher:{c['name'].lower().replace(' ', '-')}",
        "name": c["name"],
        "system": "cypher",
        "source": "srd",
        "cr": lvl,
        "hp": c.get("health"),
        "ac": c.get("armor"),
        "type": c.get("role"),
        "size": None,
        "speed": None,
        "atks": c.get("damage"),
        "page": None,
        "color": _color_for(lvl),
        "tooltip": f"{c['name']} · L{lvl} · {c.get('role','?')} · HP {c.get('health','?')} · Dmg {c.get('damage','?')}",
    }


def _row_from_custom(n: Dict[str, Any]) -> Dict[str, Any]:
    fields = n.get("fields") or {}
    cr = fields.get("cr") or fields.get("level") or fields.get("tier")
    return {
        "id": f"custom:{n.get('id','')}",
        "name": n.get("name") or "(unnamed)",
        "system": None,
        "source": "custom",
        "cr": cr,
        "hp": fields.get("hp"),
        "ac": fields.get("ac"),
        "type": n.get("node_kind") or n.get("type"),
        "size": fields.get("size"),
        "speed": fields.get("speed"),
        "atks": fields.get("atks") or fields.get("damage"),
        "page": None,
        "color": _color_for(cr),
        "tooltip": (
            f"{n.get('name','?')} · {n.get('node_kind') or 'custom'}"
            + (f" · CR {cr}" if cr is not None else "")
            + (f" · HP {fields.get('hp')}" if fields.get('hp') is not None else "")
        ),
    }


def _system_rows(system_id: Optional[str]) -> List[Dict[str, Any]]:
    sid = (system_id or "").lower()
    out: List[Dict[str, Any]] = []
    if sid in ("dnd-5e", "dnd5e"):
        from system_data.dnd5e_data import REFERENCE as DND_LIB
        out.extend(_row_from_dnd_monster(m) for m in DND_LIB.get("monsters", []))
    elif sid in ("anime-5e", "anime5e"):
        from system_data.anime5e_data import REFERENCE as ANI_LIB
        out.extend(_row_from_anime_monster(m) for m in ANI_LIB.get("monsters", []))
    elif sid == "cypher":
        from system_data.cypher_data import list_bestiary
        out.extend(_row_from_cypher(c) for c in list_bestiary(""))
    # BESM has no canon monster table — falls through to custom-only.
    return out


@router.get("/campaigns/{cid}/bestiary")
async def campaign_bestiary(
    cid: str,
    q: Optional[str] = Query(None, description="Substring filter (name/type/source)."),
    limit: int = Query(200, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """GM-only — returns the merged monster roster for this campaign."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user.get("role") != "admin" and user.get("id") != camp.get("gm_id"):
        raise HTTPException(403, "Bestiary is GM-only — don't spoil the table.")

    rows = _system_rows(camp.get("system_id"))

    # Custom Reference entity-typed rows. The campaign_reference collection
    # stores generic homebrew; nodes with kinds in the entity set are
    # treated as spawnable NPCs.
    ENTITY = {"npc", "creature", "monster", "person", "faction"}
    try:
        custom = await db.nodes.find(
            {"campaign_id": cid,
             "$or": [{"node_kind": {"$in": list(ENTITY)}},
                     {"type": {"$in": list(ENTITY)}}]},
            {"_id": 0},
        ).to_list(1000)
        rows.extend(_row_from_custom(n) for n in custom)
    except Exception:
        pass

    if q:
        ql = q.lower()
        rows = [r for r in rows
                if ql in (r.get("name") or "").lower()
                or ql in (r.get("type") or "").lower()
                or ql in (r.get("source") or "").lower()]
    rows.sort(key=lambda r: ((r.get("cr") if isinstance(r.get("cr"), (int, float)) else 99),
                              r.get("name") or ""))
    return {"campaign_id": cid, "system_id": camp.get("system_id"),
            "rows": rows[:limit], "total": len(rows)}
