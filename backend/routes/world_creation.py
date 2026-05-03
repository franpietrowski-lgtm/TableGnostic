"""V6.20 — World Creation Tree + Creation Myth + Codex Link Widget.

Backend for Cut D (per user roadmap):

  * Creation Tree — 3-pillar (Population / Geography / History) hierarchy
    with cross-pillar links. Stored as Codex nodes tagged with
    `creation_tree.section`. Re-uses the existing `codex_nodes` collection
    so graph visualisation is automatic.

  * Creation Myth — a free-form "origin lore" doc per campaign. Codex
    entries (locations, factions, characters) can opt-in via
    `has_creation_myth=true`, which creates a child myth doc auto-linked
    back to the parent.

  * Codex Link Widget — extends the existing edge schema with
    `relationship_type`, `color`, `weight (1-10)`. Honoured by the graph
    layout.

Endpoints
─────────
  GET  /api/campaigns/{cid}/creation-tree                  — tree shape
  POST /api/campaigns/{cid}/creation-tree/seed             — seed empty tree
  GET  /api/campaigns/{cid}/creation-myths                 — list myths
  POST /api/campaigns/{cid}/creation-myths                 — new root or child
  PATCH /api/campaigns/{cid}/creation-myths/{mid}
  GET  /api/campaigns/{cid}/codex-links                    — list edges with new fields
  POST /api/campaigns/{cid}/codex-links                    — create / upsert
  PATCH /api/campaigns/{cid}/codex-links/{eid}
  DELETE /api/campaigns/{cid}/codex-links/{eid}
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["world-creation"])


# ─── Canonical Creation Tree shape (per user spec) ──────────────────────
# This is the static skeleton of categories the GM populates with codex
# nodes. Cross-pillar links are explicit so the tree can render an
# arrow-set on the graph view.

CREATION_TREE_SCHEMA: Dict[str, Any] = {
    "root": {
        "label": "Creation / Beginning",
        "blurb": "Everything flows from origin. Ground all worldbuilding here.",
    },
    "pillars": {
        "Population": {
            "branches": [
                "Races", "Nations", "Languages", "Factions",
                "Prominent People", "Technology", "Religions",
                "Beliefs", "Laws",
            ],
            "blurb": "Who lives in this world and what they make of it.",
        },
        "Geography": {
            "branches": [
                "Biomes", "Locations", "Man-made Borders", "Countries",
                "Continents", "Natural Divides", "Natural Laws", "Magic",
                "Gods", "Dimensions", "Connected Worlds", "Uniqueness",
            ],
            "blurb": "Where it all happens — physical, metaphysical, multiversal.",
        },
        "History": {
            "branches": [
                "Natural History", "Of the People", "Written", "Oral",
                "Truth", "Lies",
            ],
            "blurb": "How the past is remembered, told, and falsified.",
        },
    },
    "cross_pillar_links": [
        # (source pillar.branch → target pillar.branch, relationship)
        ("Population.Laws", "Geography.Countries", "governs"),
        ("Population.Nations", "Geography.Countries", "claims"),
        ("Population.Conflicts", "Geography.Locations", "occurs at"),
        ("Population.Factions", "Geography.Locations", "based at"),
        ("Population.Races", "Geography.Biomes", "native to"),
        ("Population.Religions", "Geography.Gods", "worships"),
        ("Population.Beliefs", "Population.Religions", "shapes"),
        ("Population.Technology", "Geography.Natural Laws", "tensions"),
        ("Geography.Dimensions", "Geography.Connected Worlds", "leads to"),
        ("Geography.Connected Worlds", "Geography.Magic", "shares"),
        ("Geography.Connected Worlds", "Geography.Gods", "shares"),
        ("Population.Conflicts", "History.Of the People", "remembered as"),
        ("Population.Wars", "History.Written", "documented in"),
        ("Population.Prominent People", "History.Of the People", "central to"),
        ("Population.Religions", "History.Truth", "claims as"),
        ("History.Truth", "History.Lies", "contradicts"),
        ("History.Written", "History.Oral", "tensions"),
        ("History.Natural History", "History.Of the People", "predates"),
    ],
    "logic_notes": [
        "Population, Geography, History are a triangular dependency.",
        "Magic emerges from Natural Laws + Gods + Dimensions.",
        "Conflict is the central connector across all three pillars.",
    ],
}


@router.get("/campaigns/{cid}/creation-tree")
async def get_creation_tree(cid: str,
                              user: dict = Depends(get_current_user)):
    """Return the canonical Creation Tree schema PLUS the campaign's
    populated codex nodes grouped by tree section. Front-end uses this
    to render the tree UI with prompt fields per branch."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if (user["id"] != camp["gm_id"]
        and user["id"] not in (camp.get("member_ids") or [])
        and user.get("role") != "admin"):
        raise HTTPException(403, "Not a table member.")
    # Pull codex nodes tagged with creation_tree.section
    rows = await db.codex_nodes.find(
        {"campaign_id": cid, "creation_tree": {"$exists": True}},
        {"_id": 0},
    ).to_list(length=2000)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        sec = (r.get("creation_tree") or {}).get("section")
        if not sec:
            continue
        grouped.setdefault(sec, []).append({
            "id": r.get("id"), "name": r.get("name"),
            "node_kind": r.get("node_kind"),
            "color": (r.get("creation_tree") or {}).get("color"),
            "weight": (r.get("creation_tree") or {}).get("weight"),
            "summary": r.get("summary") or "",
        })
    return {
        "campaign_id": cid,
        "schema": CREATION_TREE_SCHEMA,
        "populated": grouped,
        "node_count": len(rows),
    }


# ─── Creation Myth ──────────────────────────────────────────────────────

class CreationMythIn(BaseModel):
    """A creation-myth document. A campaign has at most one root myth;
    additional myths attach to a parent codex entry (location / faction
    / character) for orgs/people with their own origin lore."""
    title: str = Field(min_length=1, max_length=120)
    body: str = ""
    parent_node_id: Optional[str] = None  # codex node ID (None = root)
    pillar_seeds: Dict[str, str] = Field(default_factory=dict)  # Pop/Geo/Hist/etc.
    contradicts_root: bool = False  # narrative tension flag


@router.get("/campaigns/{cid}/creation-myths")
async def list_creation_myths(cid: str,
                                user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if (user["id"] != camp["gm_id"]
        and user["id"] not in (camp.get("member_ids") or [])
        and user.get("role") != "admin"):
        raise HTTPException(403, "Not a table member.")
    rows = await db.creation_myths.find(
        {"campaign_id": cid}, {"_id": 0}).to_list(length=500)
    rows.sort(key=lambda r: (r.get("parent_node_id") or "", r.get("created_at", "")))
    return {"campaign_id": cid, "myths": rows, "total": len(rows)}


@router.post("/campaigns/{cid}/creation-myths")
async def create_creation_myth(
    cid: str, body: CreationMythIn,
    user: dict = Depends(get_current_user),
):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "title": body.title.strip(),
        "body": body.body.strip(),
        "parent_node_id": body.parent_node_id,
        "pillar_seeds": dict(body.pillar_seeds or {}),
        "contradicts_root": bool(body.contradicts_root),
        "created_by": user.get("name"),
        "created_at": now_iso(),
    }
    await db.creation_myths.insert_one(doc)
    doc.pop("_id", None)
    # Auto-link the myth back to its parent node by stamping the node.
    if body.parent_node_id:
        await db.codex_nodes.update_one(
            {"id": body.parent_node_id, "campaign_id": cid},
            {"$set": {"has_creation_myth": True,
                       "creation_myth_id": doc["id"],
                       "updated_at": now_iso()}},
        )
    return {"ok": True, "myth": doc}


class CreationMythPatch(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    pillar_seeds: Optional[Dict[str, str]] = None
    contradicts_root: Optional[bool] = None


@router.patch("/campaigns/{cid}/creation-myths/{mid}")
async def patch_creation_myth(
    cid: str, mid: str, body: CreationMythPatch,
    user: dict = Depends(get_current_user),
):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    upd: Dict[str, Any] = {"updated_at": now_iso()}
    for k in ("title", "body", "pillar_seeds", "contradicts_root"):
        v = getattr(body, k)
        if v is not None:
            upd[k] = v
    res = await db.creation_myths.update_one(
        {"id": mid, "campaign_id": cid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "Myth not found")
    return {"ok": True}


@router.delete("/campaigns/{cid}/creation-myths/{mid}")
async def delete_creation_myth(
    cid: str, mid: str, user: dict = Depends(get_current_user),
):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    myth = await db.creation_myths.find_one({"id": mid, "campaign_id": cid})
    if myth and myth.get("parent_node_id"):
        await db.codex_nodes.update_one(
            {"id": myth["parent_node_id"], "campaign_id": cid},
            {"$set": {"has_creation_myth": False, "creation_myth_id": None}},
        )
    res = await db.creation_myths.delete_one({"id": mid, "campaign_id": cid})
    return {"ok": True, "deleted": res.deleted_count}


# ─── Codex Link Widget — extended edge schema ───────────────────────────

class CodexLinkIn(BaseModel):
    """Edge between two codex nodes with relationship + color + weight.

    The graph view renders weight as edge length and color as stroke. The
    same-relationship edges share a label so the user can tell at-a-glance
    'these three nodes are all enemies of X'.
    """
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    relationship_type: str = Field(default="related", max_length=60)
    color: str = Field(default="#C9A876", pattern=r"^#[0-9A-Fa-f]{6}$")
    weight: int = Field(default=5, ge=1, le=10)
    bidirectional: bool = False
    notes: str = ""


@router.get("/campaigns/{cid}/codex-links")
async def list_codex_links(cid: str,
                             user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if (user["id"] != camp["gm_id"]
        and user["id"] not in (camp.get("member_ids") or [])
        and user.get("role") != "admin"):
        raise HTTPException(403, "Not a table member.")
    rows = await db.codex_edges.find(
        {"campaign_id": cid}, {"_id": 0}).to_list(length=5000)
    return {"campaign_id": cid, "edges": rows, "total": len(rows)}


@router.post("/campaigns/{cid}/codex-links")
async def create_codex_link(
    cid: str, body: CodexLinkIn,
    user: dict = Depends(get_current_user),
):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "source_id": body.source_id,
        "target_id": body.target_id,
        "relationship_type": body.relationship_type.strip(),
        "color": body.color,
        "weight": body.weight,
        "bidirectional": body.bidirectional,
        "notes": body.notes.strip(),
        "created_by": user.get("name"),
        "created_at": now_iso(),
    }
    await db.codex_edges.insert_one(doc)
    doc.pop("_id", None)
    return {"ok": True, "edge": doc}


class CodexLinkPatch(BaseModel):
    relationship_type: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    weight: Optional[int] = Field(default=None, ge=1, le=10)
    bidirectional: Optional[bool] = None
    notes: Optional[str] = None


@router.patch("/campaigns/{cid}/codex-links/{eid}")
async def patch_codex_link(
    cid: str, eid: str, body: CodexLinkPatch,
    user: dict = Depends(get_current_user),
):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    upd: Dict[str, Any] = {"updated_at": now_iso()}
    for k in ("relationship_type", "color", "weight", "bidirectional", "notes"):
        v = getattr(body, k)
        if v is not None:
            upd[k] = v
    res = await db.codex_edges.update_one(
        {"id": eid, "campaign_id": cid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "Edge not found")
    return {"ok": True}


@router.delete("/campaigns/{cid}/codex-links/{eid}")
async def delete_codex_link(
    cid: str, eid: str, user: dict = Depends(get_current_user),
):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    res = await db.codex_edges.delete_one({"id": eid, "campaign_id": cid})
    return {"ok": True, "deleted": res.deleted_count}
