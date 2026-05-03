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
    to render the tree UI with prompt fields per branch.

    V6.22 — codex-aware merge: ALL codex nodes (not just those already
    tagged with `creation_tree.section`) are returned, with untagged
    entries auto-classified into a pillar by their `type` field so the
    World Tree reflects the campaign's real codex instead of appearing
    empty on campaigns that predate the Creation Tree feature.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if (user["id"] != camp["gm_id"]
        and user["id"] not in (camp.get("member_ids") or [])
        and user.get("role") != "admin"):
        raise HTTPException(403, "Not a table member.")
    # ALL codex nodes for this campaign (not just creation_tree-tagged).
    rows = await db.nodes.find(
        {"campaign_id": cid}, {"_id": 0},
    ).to_list(length=2000)

    # V6.22 — fall-through classifier: map node `type` → pillar.branch
    # section (matches the frontend PillarPanel's `${pillar}.${branch}`
    # key format). This keeps legacy codex nodes from vanishing when
    # the Creation Tree view is opened.
    TYPE_TO_SECTION = {
        # Population
        "npc": "Population.Factions",
        "person": "Population.Prominent People",
        "character": "Population.Prominent People",
        "faction": "Population.Factions",
        "creature": "Population.Races",
        "pc": "Population.Prominent People",
        "nation": "Population.Nations",
        "religion": "Population.Religions",
        "language": "Population.Languages",
        "law": "Population.Laws",
        "technology": "Population.Technology",
        # Geography
        "location": "Geography.Locations",
        "place": "Geography.Locations",
        "region": "Geography.Continents",
        "biome": "Geography.Biomes",
        "landmark": "Geography.Locations",
        "country": "Geography.Countries",
        "continent": "Geography.Continents",
        "god": "Geography.Gods",
        "dimension": "Geography.Dimensions",
        # History
        "lore": "History.Of the People",
        "event": "History.Of the People",
        "chronicle": "History.Written",
        "quest": "History.Of the People",
        "era": "History.Natural History",
        "treaty": "History.Written",
        "myth": "History.Oral",
    }

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    unplaced: List[Dict[str, Any]] = []

    for r in rows:
        ct = r.get("creation_tree") or {}
        sec = ct.get("section")
        if not sec:
            # Auto-classify by node type.
            node_type = (r.get("type") or r.get("node_kind") or "").lower()
            sec = TYPE_TO_SECTION.get(node_type)
        # Legacy rows may store the display text under `title` (codex
        # editor) or `name` (world-tree seeder). Prefer `title` and
        # fall back to `name` so both paths render.
        display_name = r.get("title") or r.get("name") or "(unnamed)"
        entry = {
            "id": r.get("id"),
            "name": display_name,
            "title": display_name,
            "node_kind": r.get("node_kind") or r.get("type"),
            "type": r.get("type"),
            "color": ct.get("color"),
            "weight": ct.get("weight"),
            "auto_placed": not bool((r.get("creation_tree") or {}).get("section")),
            "summary": (r.get("summary") or r.get("content") or "")[:400],
        }
        if sec:
            grouped.setdefault(sec, []).append(entry)
        else:
            unplaced.append(entry)

    return {
        "campaign_id": cid,
        "schema": CREATION_TREE_SCHEMA,
        "populated": grouped,
        "unplaced": unplaced,
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
        await db.nodes.update_one(
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
        await db.nodes.update_one(
            {"id": myth["parent_node_id"], "campaign_id": cid},
            {"$set": {"has_creation_myth": False, "creation_myth_id": None}},
        )
    res = await db.creation_myths.delete_one({"id": mid, "campaign_id": cid})
    return {"ok": True, "deleted": res.deleted_count}


# ─── Codex nodes helper endpoints (V6.22) ──────────────────────────────
#
# The WorldCreationTree UI sow() flow POSTs to `/codex-nodes` with a
# `creation_tree.section` tag; the CodexLinkWidget GETs `/codex-nodes`
# to populate source/target dropdowns. Both were missing pre-V6.22, so
# the world tree was never codex-aware and link widgets had empty
# selectors. These endpoints close the gap by re-using `db.nodes`
# (same collection as /nodes) with creation-tree-specific shape.


class CreationTreeSow(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    node_kind: str = Field(default="concept", max_length=40)
    summary: str = ""
    creation_tree: Dict[str, Any] = Field(default_factory=dict)


@router.get("/campaigns/{cid}/codex-nodes")
async def list_codex_nodes(cid: str,
                            user: dict = Depends(get_current_user)):
    """List every codex node for the campaign. Returns `title`, `name`,
    `id`, `type`, `node_kind` on every row so the link-widget dropdowns
    work whether the node was created via the world tree sow() (uses
    `name`) or the legacy codex editor (uses `title`)."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if (user["id"] != camp["gm_id"]
        and user["id"] not in (camp.get("member_ids") or [])
        and user.get("role") != "admin"):
        raise HTTPException(403, "Not a table member.")
    rows = await db.nodes.find(
        {"campaign_id": cid},
        {"_id": 0, "id": 1, "name": 1, "title": 1, "node_kind": 1,
         "type": 1, "summary": 1, "content": 1, "creation_tree": 1},
    ).to_list(length=5000)
    out = []
    for r in rows:
        display = r.get("title") or r.get("name") or "(unnamed)"
        out.append({
            "id": r.get("id"),
            "name": display,
            "title": display,
            "node_kind": r.get("node_kind") or r.get("type") or "concept",
            "type": r.get("type"),
            "summary": (r.get("summary") or r.get("content") or "")[:300],
            "creation_tree": r.get("creation_tree") or {},
        })
    out.sort(key=lambda x: x["name"].lower())
    return out


@router.post("/campaigns/{cid}/codex-nodes")
async def sow_codex_node(
    cid: str, body: CreationTreeSow,
    user: dict = Depends(get_current_user),
):
    """Create a creation-tree-tagged codex node. Used by the world
    tree's sow() flow to seed new entries directly into a pillar."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "name": body.name.strip(),
        "title": body.name.strip(),
        "node_kind": body.node_kind,
        "type": body.node_kind,
        "summary": body.summary.strip(),
        "content": body.summary.strip(),
        "creation_tree": dict(body.creation_tree or {}),
        "tags": [],
        "fields": {},
        "visibility": "gm",
        "revealed_to": [],
        "author_id": user["id"],
        "author_name": user.get("name"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.nodes.insert_one(dict(doc))
    return {"ok": True, "node": doc}


class CodexNodePlacement(BaseModel):
    section: str = Field(min_length=1, max_length=80)
    color: Optional[str] = None
    weight: Optional[int] = Field(default=None, ge=1, le=10)


@router.patch("/campaigns/{cid}/codex-nodes/{nid}/place")
async def place_codex_node(
    cid: str, nid: str, body: CodexNodePlacement,
    user: dict = Depends(get_current_user),
):
    """V6.22 — explicitly dock an untagged codex node into a specific
    pillar.branch section on the World Tree. Used by the 'pin to
    pillar' control on the Graph view's unplaced tray."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    upd = {
        "creation_tree.section": body.section,
        "updated_at": now_iso(),
    }
    if body.color is not None:
        upd["creation_tree.color"] = body.color
    if body.weight is not None:
        upd["creation_tree.weight"] = body.weight
    res = await db.nodes.update_one(
        {"id": nid, "campaign_id": cid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(404, "Node not found")
    return {"ok": True}


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
