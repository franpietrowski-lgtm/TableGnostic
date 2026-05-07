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
                "Beliefs", "Religions", "Technology", "Wars",
                "Prominent People", "Laws", "Conflicts", "Factions",
                "Races", "Nations", "Languages",
            ],
            "blurb": "Who lives in this world and what they make of it.",
        },
        "Geography": {
            "branches": [
                "Continents", "Countries", "Man-made Borders", "Locations",
                "Biomes", "Natural Divides", "Natural Laws",
                "Connected Worlds", "Gods", "Magic", "Dimensions",
                "Uniqueness",
            ],
            "blurb": "Where it all happens — physical, metaphysical, multiversal.",
        },
        "History": {
            "branches": [
                "Truth", "Lies", "Written", "Oral",
                "Of the People", "Natural History",
            ],
            "blurb": "How the past is remembered, told, and falsified.",
        },
    },
    # V6.25.14 — bridge layout matches the canonical World Building Charts
    # infographic (Shieldice Studio). Each tuple is
    # (src "Pillar.Branch", tgt "Pillar.Branch", relationship_label).
    # The frontend lattice renders these as dotted SVG arrows between
    # the staggered pillar columns; each one is also a clickable seed
    # prompt that GMs can spawn linked codex nodes from.
    "cross_pillar_links": [
        # ── Population ⤳ Geography ────────────────────────────────────
        ("Population.Laws",            "Geography.Countries",       "governs"),
        ("Population.Wars",            "Geography.Continents",      "redraws"),
        ("Population.Conflicts",       "Geography.Man-made Borders", "redraws"),
        ("Population.Factions",        "Geography.Locations",       "operates from"),
        ("Population.Nations",         "Geography.Countries",       "claims"),
        ("Population.Nations",         "Geography.Biomes",          "settles"),
        ("Population.Races",           "Geography.Biomes",          "native to"),
        ("Population.Religions",       "Geography.Gods",            "worships"),
        ("Population.Technology",      "Geography.Natural Laws",    "tensions"),
        # ── Geography ⤳ Geography (canonical chart triangles) ────────
        ("Geography.Connected Worlds", "Geography.Gods",            "shares"),
        ("Geography.Connected Worlds", "Geography.Magic",           "shares"),
        ("Geography.Magic",            "Geography.Natural Laws",    "bends"),
        ("Geography.Dimensions",       "Geography.Connected Worlds", "leads to"),
        ("Geography.Dimensions",       "Geography.Uniqueness",      "defines"),
        # ── Population ⤳ History ──────────────────────────────────────
        ("Population.Beliefs",         "History.Truth",             "anchors"),
        ("Population.Beliefs",         "History.Lies",              "denies"),
        ("Population.Wars",            "History.Written",           "documented in"),
        ("Population.Conflicts",       "History.Of the People",     "remembered as"),
        ("Population.Prominent People", "History.Of the People",    "central to"),
        ("Population.Religions",       "History.Truth",             "claims as"),
        ("Population.Languages",       "History.Oral",              "carries"),
        # ── History ⤳ History (truth ↔ lies, written ↔ oral) ─────────
        ("History.Truth",              "History.Lies",              "contradicts"),
        ("History.Written",            "History.Oral",              "tensions"),
        ("History.Natural History",    "History.Of the People",     "predates"),
        # ── Population ⤳ Population (beliefs shape religion) ─────────
        ("Population.Beliefs",         "Population.Religions",      "shapes"),
    ],
    # V6.25.14 — History lenses (chart bottom strip). Five common
    # interpretive lenses every History entry can be tagged with so
    # GMs can filter the history pillar by axis.
    "history_lenses": [
        "Political", "Cultural", "Social", "Economic", "Diplomatic",
    ],
    "logic_notes": [
        "Population, Geography, History are a triangular dependency.",
        "Magic emerges from Natural Laws + Gods + Dimensions.",
        "Conflict is the central connector across all three pillars.",
        "Cross-pillar bridges are first-class narrative seeds — click "
        "any to author a linked node on both sides.",
    ],
}


# V6.25.14 — Bridge prompt templates. Maps (src, tgt) → a sentence the
# GM can drop into the bridge-sow modal. Templates that aren't in this
# map fall back to a generic "How does {src} affect {tgt}?" sentence.
BRIDGE_PROMPTS: Dict[str, str] = {
    "Population.Laws|Geography.Countries":
        "What law of {src} shapes the moral fibre of {tgt}? Whose crime "
        "is unforgivable here, and whose is winked at?",
    "Population.Wars|Geography.Continents":
        "Which war redrew the map of {tgt}? What border moved, what "
        "people were displaced, and what scars still mark the land?",
    "Population.Conflicts|Geography.Man-made Borders":
        "What ongoing conflict keeps {tgt} contested? Who walks the wall, "
        "and who slips around it?",
    "Population.Factions|Geography.Locations":
        "Where in {tgt} does this faction operate? What landmark do "
        "locals point to when they whisper its name?",
    "Population.Nations|Geography.Countries":
        "What does {src}'s claim on {tgt} look like — sovereignty, "
        "occupation, or unrecognised diaspora?",
    "Population.Nations|Geography.Biomes":
        "How did {src} settle into {tgt}? What did the land demand of them?",
    "Population.Races|Geography.Biomes":
        "What about {tgt} shaped {src} — physiology, custom, song?",
    "Population.Religions|Geography.Gods":
        "Which god does {src} worship, and what does the god demand back?",
    "Population.Technology|Geography.Natural Laws":
        "What natural law of {tgt} does {src}'s technology bend, break, "
        "or politely ignore?",
    "Geography.Connected Worlds|Geography.Gods":
        "Which gods cross between worlds via {src}? What do they leave "
        "behind on each side?",
    "Geography.Connected Worlds|Geography.Magic":
        "What kind of magic only works when both sides of {src} are aligned?",
    "Geography.Magic|Geography.Natural Laws":
        "Which natural law breaks when this magic is invoked? What's the "
        "cost paid by the world?",
    "Geography.Dimensions|Geography.Connected Worlds":
        "How does one travel from {src} to {tgt}? What survives the crossing?",
    "Geography.Dimensions|Geography.Uniqueness":
        "What single rule of {src} defines its uniqueness — and what "
        "happens to anyone who breaks it?",
    "Population.Beliefs|History.Truth":
        "Which fact of {tgt} is held sacred because of {src}? Who would "
        "bleed to keep it canon?",
    "Population.Beliefs|History.Lies":
        "What lie of {tgt} survives because {src} cannot live without it?",
    "Population.Wars|History.Written":
        "Which scribe wrote the official account of {src}? What did they "
        "leave out, and who paid them to leave it out?",
    "Population.Conflicts|History.Of the People":
        "How is {src} remembered around the hearth? Whose version is "
        "told to the children?",
    "Population.Prominent People|History.Of the People":
        "Which deed of {src} is told and retold? Which deed is buried?",
    "Population.Religions|History.Truth":
        "What does {src} claim as historical truth that outsiders dispute?",
    "Population.Languages|History.Oral":
        "What story can ONLY be told in {src} — and dies in translation?",
    "History.Truth|History.Lies":
        "Pick one event: write the truth and the lie side by side. Who "
        "benefits from each version?",
    "History.Written|History.Oral":
        "Where do the written and oral records of this event diverge? "
        "Which is older — and which is more accurate?",
    "History.Natural History|History.Of the People":
        "What did {src} record about this land that {tgt}'s memory has "
        "since forgotten?",
    "Population.Beliefs|Population.Religions":
        "Which folk belief was codified into {tgt}'s doctrine? What was "
        "scrubbed off in the codification?",
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
        "bridge_prompts": BRIDGE_PROMPTS,
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
    tree's sow() flow to seed new entries directly into a pillar.

    V6.25.19 — when the caller doesn't ship a `creation_tree.section`
    AND the supplied `node_kind == "concept"`, run the canonical
    classifier (`core.codex_classifier.codexify_node`) so the node
    auto-routes to the right Pillar.Branch instead of piling up in
    the unplaced tray.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")

    ct = dict(body.creation_tree or {})
    explicit_sec = ct.get("section")
    name = body.name.strip()
    summary = body.summary.strip()

    # If the caller already pinned a section, honour it. Otherwise run
    # the classifier (using the caller's node_kind as a hint).
    if explicit_sec:
        node_kind = body.node_kind
        ct.setdefault("color", None)
        ct.setdefault("auto_classified", False)
    else:
        from core.codex_classifier import codexify_node
        cls_payload = codexify_node(
            name=name, content=summary, summary=summary,
            tags=[], hint=body.node_kind,
        )
        node_kind = cls_payload["node_kind"]
        if "creation_tree" in cls_payload:
            ct = cls_payload["creation_tree"]

    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "name": name,
        "title": name,
        "node_kind": node_kind,
        "type": node_kind,
        "summary": summary,
        "content": summary,
        "creation_tree": ct,
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


@router.post("/campaigns/{cid}/codex/auto-classify")
async def auto_classify_codex(
    cid: str, user: dict = Depends(get_current_user),
):
    """V6.25.19 — backfill: re-run the canonical classifier on every
    codex node that doesn't yet carry a `creation_tree.section`.

    Idempotent: nodes that already have an explicit section are NEVER
    overwritten. Returns the number of nodes that landed somewhere
    they weren't before, plus the count that stayed unplaced (no
    signal in name / content / tags).
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")

    from core.codex_classifier import classify_concept

    rows = await db.nodes.find(
        {"campaign_id": cid}, {"_id": 0},
    ).to_list(length=5000)

    classified = 0
    still_unplaced = 0
    skipped = 0
    placements: List[Dict[str, Any]] = []

    for r in rows:
        ct = r.get("creation_tree") or {}
        if ct.get("section"):
            skipped += 1
            continue
        # Run classifier on (name|title) + content + tags, with the
        # legacy `type` value as a hint when present.
        name = r.get("name") or r.get("title") or ""
        cls = classify_concept(
            name=name,
            content=r.get("content") or r.get("summary") or "",
            tags=r.get("tags") or [],
            hint=(r.get("node_kind") or r.get("type")),
        )
        sec = cls["creation_tree_section"]
        if not sec:
            still_unplaced += 1
            continue
        upd = {
            "creation_tree": {
                "section": sec,
                "color": ct.get("color"),
                "auto_classified": True,
                "classifier_confidence": cls["confidence"],
                "classifier_reasoning": cls["reasoning"],
            },
            "node_kind": cls["node_kind"],
            "type": cls["type"],
            "updated_at": now_iso(),
        }
        await db.nodes.update_one({"id": r["id"]}, {"$set": upd})
        classified += 1
        placements.append({
            "id": r["id"], "name": name, "section": sec,
            "confidence": cls["confidence"], "reasoning": cls["reasoning"],
        })

    return {
        "ok": True,
        "classified": classified,
        "still_unplaced": still_unplaced,
        "already_placed": skipped,
        "placements": placements[:50],  # cap echo so the response stays small
    }


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



# ─── V6.25.14 — World Tree bridge-sow ──────────────────────────────────

class BridgeSowIn(BaseModel):
    """Spawn a pair of linked codex nodes from a cross-pillar bridge.
    The lattice UI calls this when the GM clicks a bridge prompt and
    types a narrative seed: it creates ONE node on each side of the
    bridge and a `relationship_type`-tagged codex edge connecting them.
    """
    src_section: str = Field(min_length=3, max_length=80)   # "Pillar.Branch"
    tgt_section: str = Field(min_length=3, max_length=80)
    relationship: str = Field(default="related", max_length=60)
    src_name: str = Field(min_length=1, max_length=200)
    src_summary: str = Field(default="", max_length=2000)
    tgt_name: str = Field(min_length=1, max_length=200)
    tgt_summary: str = Field(default="", max_length=2000)
    color: str = Field(default="#9CC4FF", pattern=r"^#[0-9A-Fa-f]{6}$")


def _section_to_kind(section: str) -> str:
    """Coarse 'Pillar.Branch' → node_kind mapping for the seeded node.

    V6.25.19 — delegates to the canonical
    `core.codex_classifier._kind_from_section` so the lattice and
    classifier never drift out of sync.
    """
    from core.codex_classifier import _kind_from_section
    return _kind_from_section(section)


@router.post("/campaigns/{cid}/world-tree/bridge-sow")
async def bridge_sow(
    cid: str, body: BridgeSowIn,
    user: dict = Depends(get_current_user),
):
    """Author twin codex nodes connected by a relationship edge.
    Each side is docked to its `Pillar.Branch` section so the World
    Tree lattice picks them up immediately.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")

    # Confirm both sections are well-formed against the schema.
    valid_sections = set()
    for pillar, meta in CREATION_TREE_SCHEMA["pillars"].items():
        for branch in meta["branches"]:
            valid_sections.add(f"{pillar}.{branch}")
    for sec in (body.src_section, body.tgt_section):
        if sec not in valid_sections:
            raise HTTPException(422, f"Unknown section: {sec}")

    src_doc = {
        "id": new_id(), "campaign_id": cid,
        "name": body.src_name.strip(), "title": body.src_name.strip(),
        "node_kind": _section_to_kind(body.src_section),
        "type": _section_to_kind(body.src_section),
        "summary": body.src_summary.strip(),
        "content": body.src_summary.strip(),
        "creation_tree": {"section": body.src_section,
                          "color": body.color,
                          "via_bridge": body.tgt_section},
        "tags": ["bridge-sown"], "fields": {}, "visibility": "gm",
        "revealed_to": [], "author_id": user["id"],
        "author_name": user.get("name"),
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    tgt_doc = {
        "id": new_id(), "campaign_id": cid,
        "name": body.tgt_name.strip(), "title": body.tgt_name.strip(),
        "node_kind": _section_to_kind(body.tgt_section),
        "type": _section_to_kind(body.tgt_section),
        "summary": body.tgt_summary.strip(),
        "content": body.tgt_summary.strip(),
        "creation_tree": {"section": body.tgt_section,
                          "color": body.color,
                          "via_bridge": body.src_section},
        "tags": ["bridge-sown"], "fields": {}, "visibility": "gm",
        "revealed_to": [], "author_id": user["id"],
        "author_name": user.get("name"),
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.nodes.insert_many([dict(src_doc), dict(tgt_doc)])

    edge = {
        "id": new_id(), "campaign_id": cid,
        "source_id": src_doc["id"], "target_id": tgt_doc["id"],
        "relationship_type": body.relationship.strip(),
        "color": body.color, "weight": 6, "bidirectional": False,
        "notes": f"Bridge: {body.src_section} ⤳ {body.tgt_section}",
        "created_by": user.get("name"),
        "created_at": now_iso(),
    }
    await db.codex_edges.insert_one(dict(edge))
    src_doc.pop("_id", None)
    tgt_doc.pop("_id", None)
    edge.pop("_id", None)
    return {"ok": True, "src_node": src_doc, "tgt_node": tgt_doc, "edge": edge}
