"""V6.25.25 (Cycle D) — Director's Console roll-table designer.

A roll-table is a weighted list of outcomes the GM rolls during play to
inject randomness into prep ("which patron walks in?", "what's tonight's
omen?", "loot found in the sarcophagus?"). The user requested two
canonical guard-rails:

  1. **Gated to seeded materials** — every entry MUST point at an
     existing Reference Editor row (campaign_reference) OR a Codex node
     OR a literal text body. We reject silent free-text edits that
     drift from the seeded catalogue.

  2. **Rarity-tier thresholds** — each table declares a `rarity_tier`
     (common | uncommon | rare | very_rare | legendary) and a
     `min_party_tier` gate; rolling the table when the party tier is
     below the threshold returns a polite 403 with the gating note,
     so a level-1 party doesn't accidentally pull a legendary artifact.

Endpoints:
    POST   /api/campaigns/{cid}/roll-tables               (create)
    GET    /api/campaigns/{cid}/roll-tables               (list)
    GET    /api/campaigns/{cid}/roll-tables/{tid}         (read)
    PATCH  /api/campaigns/{cid}/roll-tables/{tid}         (update)
    DELETE /api/campaigns/{cid}/roll-tables/{tid}         (delete)
    POST   /api/campaigns/{cid}/roll-tables/{tid}/roll    (roll once)
"""
from __future__ import annotations
import random
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["roll-tables"])


RARITY_TIERS = {
    "common":     {"min_party_tier": 1,  "die": "1d6",   "blurb": "Anyone might see this."},
    "uncommon":   {"min_party_tier": 2,  "die": "1d10",  "blurb": "Slightly off the beaten path."},
    "rare":       {"min_party_tier": 4,  "die": "1d20",  "blurb": "Hidden, hunted, or hand-crafted."},
    "very_rare":  {"min_party_tier": 6,  "die": "1d50",  "blurb": "Storied. Whispered about."},
    "legendary":  {"min_party_tier": 9,  "die": "1d100", "blurb": "Singular. World-altering."},
}


class RollTableEntry(BaseModel):
    """One row in a weighted roll table.

    Exactly ONE of `reference_id`, `node_id`, `material_id`, or `body`
    must be set — this is the seeded-materials gate.
    """
    weight: int = Field(default=1, ge=1, le=100)
    label: str = Field(default="", max_length=200,
                        description="Short display name. Auto-fills from the linked source when empty.")
    reference_id: Optional[str] = Field(default=None,
                        description="campaign_reference row id.")
    node_id: Optional[str] = Field(default=None,
                        description="codex node id.")
    material_id: Optional[str] = Field(default=None,
                        description="crafting material id (raw / refined / assembled).")
    body: Optional[str] = Field(default=None, max_length=2000,
                        description="Literal text body when no seeded source exists. Authored deliberately.")


class RollTableIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    rarity_tier: Literal["common", "uncommon", "rare", "very_rare", "legendary"] = "common"
    min_party_tier: int = Field(default=1, ge=1, le=10,
                                  description="Minimum party tier needed to roll. Defaults to the rarity tier's canonical threshold.")
    entries: List[RollTableEntry] = Field(default_factory=list)


async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    return camp


def _is_gm(camp: dict, user: dict) -> bool:
    return camp.get("gm_id") == user["id"] or user.get("role") == "admin"


async def _validate_entries(cid: str, entries: List[Dict[str, Any]]):
    """Enforce the seeded-materials gate."""
    if not entries:
        raise HTTPException(422, "A roll table must have at least one entry.")
    ref_ids = [e.get("reference_id") for e in entries if e.get("reference_id")]
    node_ids = [e.get("node_id") for e in entries if e.get("node_id")]
    mat_ids = [e.get("material_id") for e in entries if e.get("material_id")]
    valid_refs = set()
    valid_nodes = set()
    valid_mats = set()
    if ref_ids:
        rows = await db.campaign_reference.find(
            {"campaign_id": cid, "id": {"$in": ref_ids}},
            {"_id": 0, "id": 1}).to_list(500)
        valid_refs = {r["id"] for r in rows}
    if node_ids:
        rows = await db.nodes.find(
            {"campaign_id": cid, "id": {"$in": node_ids}},
            {"_id": 0, "id": 1}).to_list(500)
        valid_nodes = {r["id"] for r in rows}
    if mat_ids:
        rows = await db.materials.find(
            {"campaign_id": cid, "id": {"$in": mat_ids}},
            {"_id": 0, "id": 1}).to_list(500)
        valid_mats = {r["id"] for r in rows}
    for i, e in enumerate(entries):
        sources = sum(bool(e.get(k)) for k in ("reference_id", "node_id", "material_id", "body"))
        if sources == 0:
            raise HTTPException(422, f"Entry {i}: must point at a seeded reference, codex node, material, or carry a literal body. No silent free-text drift allowed.")
        if sources > 1:
            raise HTTPException(422, f"Entry {i}: pick exactly one source (reference / node / material / body), got {sources}.")
        if e.get("reference_id") and e["reference_id"] not in valid_refs:
            raise HTTPException(422, f"Entry {i}: reference_id {e['reference_id']!r} is not a seeded reference in this campaign.")
        if e.get("node_id") and e["node_id"] not in valid_nodes:
            raise HTTPException(422, f"Entry {i}: node_id {e['node_id']!r} is not a codex node in this campaign.")
        if e.get("material_id") and e["material_id"] not in valid_mats:
            raise HTTPException(422, f"Entry {i}: material_id {e['material_id']!r} is not a campaign material.")


@router.post("/campaigns/{cid}/roll-tables")
async def create_roll_table(cid: str, body: RollTableIn,
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    rarity_default = RARITY_TIERS[body.rarity_tier]["min_party_tier"]
    min_tier = body.min_party_tier or rarity_default
    if min_tier < rarity_default:
        # Don't let a GM accidentally undermine the rarity gate.
        min_tier = rarity_default
    entries = [e.model_dump() for e in body.entries]
    await _validate_entries(cid, entries)
    row = {
        "id": new_id(),
        "campaign_id": cid,
        "name": body.name.strip(),
        "description": (body.description or "").strip(),
        "rarity_tier": body.rarity_tier,
        "min_party_tier": min_tier,
        "entries": entries,
        "created_at": now_iso(),
        "created_by_id": user["id"],
        "created_by_name": user.get("name") or user.get("email"),
    }
    await db.roll_tables.insert_one(row)
    row.pop("_id", None)
    return row


@router.get("/campaigns/{cid}/roll-tables")
async def list_roll_tables(cid: str,
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    cursor = db.roll_tables.find({"campaign_id": cid}, {"_id": 0}) \
                              .sort("created_at", -1)
    return {"rows": [r async for r in cursor]}


@router.get("/campaigns/{cid}/roll-tables/{tid}")
async def get_roll_table(cid: str, tid: str,
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    row = await db.roll_tables.find_one(
        {"campaign_id": cid, "id": tid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Roll table not found.")
    return row


@router.patch("/campaigns/{cid}/roll-tables/{tid}")
async def update_roll_table(cid: str, tid: str, body: RollTableIn,
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    rarity_default = RARITY_TIERS[body.rarity_tier]["min_party_tier"]
    min_tier = max(body.min_party_tier or rarity_default, rarity_default)
    entries = [e.model_dump() for e in body.entries]
    await _validate_entries(cid, entries)
    res = await db.roll_tables.update_one(
        {"campaign_id": cid, "id": tid},
        {"$set": {
            "name": body.name.strip(),
            "description": (body.description or "").strip(),
            "rarity_tier": body.rarity_tier,
            "min_party_tier": min_tier,
            "entries": entries,
            "updated_at": now_iso(),
        }})
    if res.matched_count == 0:
        raise HTTPException(404, "Roll table not found.")
    row = await db.roll_tables.find_one(
        {"campaign_id": cid, "id": tid}, {"_id": 0})
    return row


@router.delete("/campaigns/{cid}/roll-tables/{tid}")
async def delete_roll_table(cid: str, tid: str,
                              user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.roll_tables.delete_one(
        {"campaign_id": cid, "id": tid})
    return {"ok": True, "deleted": res.deleted_count}


@router.post("/campaigns/{cid}/roll-tables/{tid}/roll")
async def roll_table(cid: str, tid: str,
                       party_tier: int = 1,
                       user: dict = Depends(get_current_user)):
    """Roll the table once. Enforces the rarity-tier party threshold."""
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    row = await db.roll_tables.find_one(
        {"campaign_id": cid, "id": tid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Roll table not found.")
    if int(party_tier) < int(row["min_party_tier"]):
        raise HTTPException(403,
            f"Party tier {party_tier} is below this table's gate "
            f"(needs ≥{row['min_party_tier']} for {row['rarity_tier']}).")
    entries = row["entries"] or []
    if not entries:
        raise HTTPException(400, "Empty roll table.")
    weights = [int(e.get("weight", 1)) for e in entries]
    pick = random.choices(entries, weights=weights, k=1)[0]
    # Hydrate the pick with its source row (label + body).
    hydrated = dict(pick)
    if pick.get("reference_id"):
        ref = await db.campaign_reference.find_one(
            {"id": pick["reference_id"]}, {"_id": 0})
        if ref:
            if not hydrated.get("label"):
                hydrated["label"] = ref.get("name")
            hydrated["source"] = {"kind": "reference",
                                    "name": ref.get("name"),
                                    "summary": ref.get("summary"),
                                    "ref_kind": ref.get("kind")}
    elif pick.get("node_id"):
        node = await db.nodes.find_one(
            {"id": pick["node_id"]}, {"_id": 0})
        if node:
            if not hydrated.get("label"):
                hydrated["label"] = node.get("title") or node.get("name")
            hydrated["source"] = {"kind": "node",
                                    "name": node.get("title") or node.get("name"),
                                    "summary": node.get("summary"),
                                    "node_kind": node.get("node_kind")}
    elif pick.get("material_id"):
        mat = await db.materials.find_one(
            {"id": pick["material_id"]}, {"_id": 0})
        if mat:
            if not hydrated.get("label"):
                hydrated["label"] = mat.get("name")
            hydrated["source"] = {"kind": "material",
                                    "name": mat.get("name"),
                                    "summary": mat.get("summary"),
                                    "tier": mat.get("tier"),
                                    "rarity": mat.get("rarity")}
    else:
        hydrated["source"] = {"kind": "body"}
    return {
        "table_id": tid,
        "table_name": row["name"],
        "rarity_tier": row["rarity_tier"],
        "die": RARITY_TIERS[row["rarity_tier"]]["die"],
        "result": hydrated,
    }


@router.get("/roll-tables/rarity-tiers")
async def get_rarity_tiers():
    """Static metadata for the rarity-tier gates the designer UI uses."""
    return {"tiers": [
        {"key": k, **v} for k, v in RARITY_TIERS.items()
    ]}
