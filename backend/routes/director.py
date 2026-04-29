"""GM Director's Console — system-aware encounter design + CR analysis.

Aggregates everything the GM needs at the table:
  · the seated party (Character Sheets — `dnd_state` / `cypher_state` / BESM)
  · NPCs from three sources:
      - Genesis seed_npcs[] (from CampaignGenesis 7-phase)
      - Epic Campaign nemesis + villains (V5.1 Sclanders 8th tab)
      - Codex `npc`-typed nodes
  · current locations (free-text strings the GM keeps current)
  · system-aware Challenge Rating analysis from `core/cr_engine`
  · rule-based suggestions ("add minions", "drop AC", "add environmental clock")

State is persisted in `db.directors`, one document per campaign.
GM/admin only — players do not read or write the Director's Console.
"""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.cr_engine import analyse as cr_analyse
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["director"])


# ────────────────────────── Pydantic ──────────────────────────
class EncounterNpcIn(BaseModel):
    """A single NPC in an encounter draft. Stores both system-shape stat
    pointers AND a free-text location/state line so the GM can update at
    the table without going through a full character builder."""
    id: Optional[str] = None
    name: str = ""
    role: str = "minion"          # minion | henchman | villain | nemesis | ally
    source: str = "manual"        # manual | genesis | epic | codex
    source_id: Optional[str] = None  # codex node id, epic villain id, etc.
    location: str = ""
    state: str = "active"         # active | wounded | bloodied | fled | down
    intent: str = ""              # one-line current goal
    # Optional stat-block hints for CR engine. Different systems need different fields.
    cr: Optional[str] = None              # D&D
    level: Optional[int] = None           # Cypher / D&D NPC level
    total_points: Optional[int] = None    # BESM / Anime 5E PL points
    count: int = 1
    notes: str = ""


class EncounterIn(BaseModel):
    id: Optional[str] = None
    name: str = "Untitled Encounter"
    party_character_ids: List[str] = Field(default_factory=list)
    npcs: List[EncounterNpcIn] = Field(default_factory=list)
    environment: Dict[str, Any] = Field(default_factory=dict)  # {indoor: bool, weather, light, hazards}
    notes: str = ""
    # V5.4 — ecosystem nervous system. Free-form plot phase key — the same
    # one used on Sessions and Journal entries — so the Pulse panel can
    # correlate which encounters were live during which beat.
    plot_phase: str = ""
    # V5.4 — encounter type so the Director can plan social / puzzle /
    # exploration alongside combat (the user's vision: "social, combat,
    # puzzle, etc").
    kind: Literal["combat", "social", "puzzle", "exploration", "chase", "ritual"] = "combat"


class DirectorIn(BaseModel):
    encounters: List[EncounterIn] = Field(default_factory=list)
    current_location: str = ""        # the party's current geographic position
    current_phase_ref: str = ""        # which Atelier/Epic phase is "live" right now


# ────────────────────────── Helpers ──────────────────────────
async def _campaign_or_404(cid: str) -> Dict[str, Any]:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp


def _is_gm(user: Dict[str, Any], camp: Dict[str, Any]) -> bool:
    return user["id"] == camp["gm_id"] or user.get("role") == "admin"


def _empty_doc(cid: str) -> Dict[str, Any]:
    return {"campaign_id": cid, "encounters": [], "current_location": "",
            "current_phase_ref": "", "updated_at": now_iso()}


def _stamp_ids(doc: Dict[str, Any]) -> None:
    for e in doc.get("encounters", []) or []:
        e["id"] = e.get("id") or new_id()
        for n in e.get("npcs", []) or []:
            n["id"] = n.get("id") or new_id()


async def _gather_npc_pool(cid: str) -> List[Dict[str, Any]]:
    """Walk Genesis seed_npcs[], Epic Campaign nemesis+villains, and Codex
    `npc`-typed nodes — return one normalised list the GM can drag into an
    encounter without retyping anything."""
    pool: List[Dict[str, Any]] = []
    seen: set[str] = set()

    # Genesis seed NPCs (V3 — 7-phase plan).
    g = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if g:
        for n in (g.get("seed_npcs") or []):
            key = f"genesis:{n.get('name', '').strip().lower()}"
            if not n.get("name") or key in seen:
                continue
            seen.add(key)
            pool.append({
                "name": n["name"], "role": "ally",
                "source": "genesis", "source_id": None,
                "intent": n.get("role") or n.get("description") or "",
                "notes": n.get("relationship") or "",
            })

    # Epic Campaign nemesis + villains.
    ep = await db.epic_campaigns.find_one({"campaign_id": cid}, {"_id": 0})
    if ep:
        nem = ep.get("nemesis") or {}
        if nem.get("name"):
            seen.add(f"epic:{nem['name'].strip().lower()}")
            pool.append({
                "name": nem["name"], "role": "nemesis",
                "source": "epic", "source_id": nem.get("id"),
                "intent": nem.get("goal", ""),
                "notes": nem.get("notes", ""),
            })
        for v in (ep.get("villains") or []):
            if not v.get("name"):
                continue
            key = f"epic:{v['name'].strip().lower()}"
            if key in seen:
                continue
            seen.add(key)
            pool.append({
                "name": v["name"], "role": v.get("role") or "villain",
                "source": "epic", "source_id": v.get("id"),
                "intent": v.get("goal", ""),
                "notes": v.get("notes", ""),
            })

    # Codex — `npc` nodes.
    cursor = db.nodes.find({"campaign_id": cid, "type": "npc"}, {"_id": 0})
    async for nd in cursor:
        key = f"codex:{(nd.get('title') or '').strip().lower()}"
        if not nd.get("title") or key in seen:
            continue
        seen.add(key)
        pool.append({
            "name": nd["title"], "role": "neutral",
            "source": "codex", "source_id": nd["id"],
            "intent": (nd.get("fields") or {}).get("intent") or "",
            "notes": nd.get("content", "")[:200],
        })

    return pool


def _normalise_party(characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pull out just the bits the CR engine needs from each PC's folio."""
    out = []
    for c in characters:
        folio = c.get("folio") or {}
        out.append({
            "id": c["id"],
            "name": c.get("name"),
            "dnd_state": folio.get("dnd_state"),
            "cypher_state": folio.get("cypher_state"),
            "anime5e_state": folio.get("anime5e_state"),
            "total_points": c.get("total_points") or 0,
            "level": (folio.get("dnd_state") or {}).get("level"),
            "tier": (folio.get("cypher_state") or {}).get("tier"),
        })
    return out


# ────────────────────────── Routes ──────────────────────────
@router.get("/director/{cid}")
async def get_director(cid: str, user: Dict[str, Any] = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "GM/admin only.")
    doc = await db.directors.find_one({"campaign_id": cid}, {"_id": 0})
    if not doc:
        doc = _empty_doc(cid)
        await db.directors.insert_one(dict(doc))
    pool = await _gather_npc_pool(cid)
    return {
        **sanitize(doc),
        "system_id": camp.get("system_id") or "besm-4e",
        "npc_pool": pool,
    }


@router.put("/director/{cid}")
async def replace_director(cid: str, body: DirectorIn,
                           user: Dict[str, Any] = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "GM/admin only.")
    doc = body.model_dump()
    doc["campaign_id"] = cid
    doc["updated_at"] = now_iso()
    _stamp_ids(doc)
    await db.directors.replace_one({"campaign_id": cid}, doc, upsert=True)
    return sanitize(doc)


@router.post("/director/{cid}/cr-analyse")
async def cr_analyse_endpoint(cid: str, body: EncounterIn,
                              user: Dict[str, Any] = Depends(get_current_user)):
    """Lightweight — does NOT persist the encounter. Caller passes the draft
    and we return the rating + suggestions. UI calls this on every edit."""
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "GM/admin only.")
    sys_id = camp.get("system_id") or "besm-4e"
    party_chars = []
    if body.party_character_ids:
        cursor = db.characters.find(
            {"id": {"$in": body.party_character_ids}}, {"_id": 0})
        async for c in cursor:
            party_chars.append(c)
    party = _normalise_party(party_chars)
    npcs = [n.model_dump() for n in body.npcs]
    return cr_analyse(party, npcs, system_id=sys_id, env=body.environment or None)
