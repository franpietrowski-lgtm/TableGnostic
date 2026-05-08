"""Campaign-scoped Reference editor (V4.4 Phase I).

GMs add custom Weapons / Armor / Items / Companions / Custom-rules entries
per campaign with page-reference validation. The validator cross-checks
the cited page against known book ranges from `besm_data.BOOK` so a GM
can't cite a page that doesn't exist.

Routes:
    GET    /api/campaigns/{cid}/reference?kind=weapon|armor|item|companion|custom
    POST   /api/campaigns/{cid}/reference          — create
    PATCH  /api/campaigns/{cid}/reference/{rid}    — update
    DELETE /api/campaigns/{cid}/reference/{rid}    — remove
    POST   /api/reference/validate-page            — utility cross-check helper
"""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

# Book page-ranges per system. Edit when new mechanic-only data is folded
# in (e.g. once Anime 5E SRD extraction lands, add anime-5e here).
KNOWN_BOOK_RANGES: Dict[str, Dict[str, Any]] = {
    "besm-4e": {"min": 1, "max": 320, "title": "BESM Fourth Edition"},
    "besm-3e": {"min": 1, "max": 256, "title": "BESM Third Edition"},
    "anime-5e": {"min": 1, "max": 200, "title": "Anime 5E SRD v1.01"},
    "cypher": {"min": 1, "max": 400, "title": "Cypher System (Numenera et al.)"},
    "dnd-5e": {"min": 1, "max": 320, "title": "D&D 5E PHB"},
    "_default": {"min": 1, "max": 999, "title": "Custom"},
}

REFERENCE_KINDS = {
    # Shared / legacy
    "weapon", "armor", "item", "companion", "custom",
    # BESM core
    "attribute", "skill", "defect",
    # V6.3 additions (BESM)
    "enhancement", "limiter", "power_pack", "power_bundle",
    # D&D 5E / Anime 5E content
    "spell", "feat", "background", "race_trait", "class_feature",
    # Cypher
    "cypher_ability", "cypher_item", "artifact", "descriptor", "focus", "type",
}

router = APIRouter(prefix="/api", tags=["reference-editor"])


# ─────── Pydantic ───────

class ReferenceItemIn(BaseModel):
    # V6.3 — expanded kinds for cross-system custom content authoring.
    # Atelier GMs can now seed enhancements, limiters, power packs, and
    # full power bundles (a narrative bundle with a CP estimate and a
    # list of component-attribute pointers) for BESM — and skills /
    # spells / feats / backgrounds for D&D 5E and Anime 5E, and
    # abilities / cyphers / artifacts for Cypher. `kind=custom` remains
    # as the catch-all for system-specific one-offs.
    kind: Literal[
        # Shared / legacy
        "weapon", "armor", "item", "companion", "custom",
        # BESM core
        "attribute", "skill", "defect",
        # BESM V6.3 additions
        "enhancement", "limiter", "power_pack", "power_bundle",
        # D&D 5E / Anime 5E
        "spell", "feat", "background", "race_trait", "class_feature",
        # Cypher
        "cypher_ability", "cypher_item", "artifact", "descriptor", "focus",
        "type",
    ]
    name: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=500)
    page: Optional[int] = None  # cited rulebook page
    book: Optional[str] = None  # system_id-style (e.g. "besm-4e"); falls back to campaign system
    cost: Optional[str] = None  # free-text mechanic cost ("2 pts/level", etc.)
    fields: Dict[str, Any] = Field(default_factory=dict)


class ReferenceItemPatch(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    page: Optional[int] = None
    book: Optional[str] = None
    cost: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None


class PageValidateIn(BaseModel):
    page: int
    book: str = "besm-4e"


# ─────── Helpers ───────

def _validate_page(page: Optional[int], book: Optional[str]) -> Dict[str, Any]:
    """Return {valid, reason, range, book}. Never raises — the GM should
    see *why* a page reference was rejected, not get a 500."""
    if page is None or page == 0:
        return {"valid": True, "reason": "no page cited (allowed)", "book": book}
    rng = KNOWN_BOOK_RANGES.get(book or "_default", KNOWN_BOOK_RANGES["_default"])
    if not (rng["min"] <= int(page) <= rng["max"]):
        return {"valid": False,
                "reason": f"p.{page} is outside the known range "
                           f"{rng['min']}-{rng['max']} for {rng['title']}.",
                "range": rng, "book": book}
    return {"valid": True, "book": book, "range": rng}


async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp


def _is_gm(camp: dict, user: dict) -> bool:
    return camp.get("gm_id") == user["id"] or user.get("role") == "admin"


# ─────── Endpoints ───────

@router.post("/reference/validate-page")
async def validate_page(body: PageValidateIn,
                          user: dict = Depends(get_current_user)):
    return _validate_page(body.page, body.book)


class BundleComponentIn(BaseModel):
    """One component of a BESM Power Bundle / Power Pack.

    `kind` is one of:
      - "attribute"    : a BESM Attribute reference. Cost = cost_per_level × level
                         minus item-defect refunds embedded in the component.
      - "skill"        : a BESM Skill Group. Cost = cost_per_level × level.
      - "defect"       : a BESM Defect. Cost = −(points_per_rank × rank).
      - "enhancement"  : Enhancement rows. We DON'T add CP for these directly
                         at the component level — Enhancements lower effective
                         Level; the character builder handles the math.
      - "limiter"      : Symmetric to enhancement (raises effective Level).
    """
    kind: Literal["attribute", "skill", "defect", "enhancement", "limiter"]
    name: str
    cost_per_level: float = 0
    level: int = 1
    points_per_rank: int = 0
    rank: int = 0
    refund: int = 0
    note: str = ""


class BundleEstimateIn(BaseModel):
    """Estimate the CP cost of a composed Power Bundle.

    Helps a GM authoring a custom Power Bundle in the Atelier see
    exactly what the bundle will cost a player before they save it as
    a reusable reference. Mirrors the character-validator CP math so
    there's no drift between the two surfaces.
    """
    components: List[BundleComponentIn] = Field(default_factory=list)


@router.post("/reference/estimate-bundle-cost")
async def estimate_bundle_cost(body: BundleEstimateIn,
                                 user: dict = Depends(get_current_user)):
    """Run the BESM CP math across a bundle's components and return a
    structured breakdown (per-line cost + net total)."""
    lines: List[Dict[str, Any]] = []
    total = 0
    for c in body.components:
        if c.kind == "attribute":
            gross = int(round(c.cost_per_level * c.level))
            net = max(0, gross - (c.refund or 0))
            lines.append({
                "kind": c.kind, "name": c.name, "level": c.level,
                "cost_per_level": c.cost_per_level, "gross": gross,
                "refund": c.refund or 0, "points": net,
                "note": c.note or f"{c.cost_per_level}×{c.level}"
                        + (f" − {c.refund}" if c.refund else ""),
            })
            total += net
        elif c.kind == "skill":
            cost = int(round(c.cost_per_level * c.level))
            lines.append({
                "kind": c.kind, "name": c.name, "level": c.level,
                "cost_per_level": c.cost_per_level, "points": cost,
                "note": f"{c.cost_per_level}×{c.level}",
            })
            total += cost
        elif c.kind == "defect":
            refund = (c.points_per_rank or 0) * (c.rank or 0)
            lines.append({
                "kind": c.kind, "name": c.name, "rank": c.rank,
                "points_per_rank": c.points_per_rank,
                "points": -refund,
                "note": f"{c.points_per_rank}×{c.rank} refund",
            })
            total -= refund
        elif c.kind in ("enhancement", "limiter"):
            lines.append({
                "kind": c.kind, "name": c.name, "points": 0,
                "note": "Effective-Level modifier — applied by the builder, not by bundle cost.",
            })
    return {
        "total_cost": total,
        "component_count": len(body.components),
        "lines": lines,
    }


@router.get("/campaigns/{cid}/reference")
async def list_reference(cid: str,
                          kind: Optional[str] = Query(default=None),
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    # Players see the reference table (read-only). GM-only "custom" rules
    # can be marked private via fields.gm_only — those are filtered for
    # non-GMs.
    q: Dict[str, Any] = {"campaign_id": cid}
    if kind:
        if kind not in REFERENCE_KINDS:
            raise HTTPException(400, f"Unknown kind {kind!r}. "
                                       f"Allowed: {sorted(REFERENCE_KINDS)}.")
        q["kind"] = kind
    rows = await db.campaign_reference.find(q, {"_id": 0}) \
                                        .sort("created_at", 1).to_list(500)
    if not _is_gm(camp, user):
        rows = [r for r in rows if not (r.get("fields") or {}).get("gm_only")]
    return rows


@router.post("/campaigns/{cid}/reference")
async def create_reference(cid: str, body: ReferenceItemIn,
                            user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    book = body.book or camp.get("system_id") or "_default"
    page_check = _validate_page(body.page, book)
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "kind": body.kind,
        "name": body.name,
        "summary": body.summary,
        "page": body.page,
        "book": book,
        "cost": body.cost,
        "fields": body.fields,
        "page_validation": page_check,
        "created_at": now_iso(),
        "created_by": user["name"],
    }
    await db.campaign_reference.insert_one(doc)
    return sanitize(doc)


@router.patch("/campaigns/{cid}/reference/{rid}")
async def update_reference(cid: str, rid: str, body: ReferenceItemPatch,
                            user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    existing = await db.campaign_reference.find_one(
        {"id": rid, "campaign_id": cid}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Reference item not found")
    patch = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if "page" in patch or "book" in patch:
        patch["page_validation"] = _validate_page(
            patch.get("page", existing.get("page")),
            patch.get("book", existing.get("book")),
        )
    patch["updated_at"] = now_iso()
    patch["updated_by"] = user["name"]
    await db.campaign_reference.update_one({"id": rid}, {"$set": patch})
    fresh = await db.campaign_reference.find_one({"id": rid}, {"_id": 0})
    return sanitize(fresh)


@router.delete("/campaigns/{cid}/reference/{rid}")
async def delete_reference(cid: str, rid: str,
                            user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "GM only.")
    res = await db.campaign_reference.delete_one(
        {"id": rid, "campaign_id": cid})
    return {"ok": True, "deleted": res.deleted_count}


@router.get("/reference/library")
async def reference_library(system_id: str = "",
                              kind: Optional[str] = None,
                              user: dict = Depends(get_current_user)):
    """V6.25.25 — Aggregate user-visible custom reference rows across ALL
    of the caller's campaigns, filtered by `system_id` (and optional `kind`).

    Powers the dashboard Reference page's "Custom" tab so GMs and players
    see every house-rule / Reference Editor / character-derived custom
    entry for the active system in ONE place — sidesteps having to walk
    each campaign individually.

    Visibility rules:
      * GMs see all of their own campaigns' custom rows.
      * Players see custom rows from campaigns they're rostered on,
        EXCLUDING `fields.gm_only` rows.
      * Admin users see everything tagged with the active `system_id`.
    """
    if not system_id:
        raise HTTPException(422, "system_id is required.")
    is_admin = user.get("role") == "admin"

    # Find every campaign the caller is involved in.
    if is_admin:
        camp_q: Dict[str, Any] = {}
    else:
        camp_q = {"$or": [
            {"gm_id": user["id"]},
            {"player_ids": user["id"]},
        ]}
    camp_q["system_id"] = system_id
    campaigns = await db.campaigns.find(
        camp_q, {"_id": 0, "id": 1, "name": 1, "gm_id": 1}).to_list(500)
    cid_to_name = {c["id"]: c["name"] for c in campaigns}
    gm_cids = {c["id"] for c in campaigns if c.get("gm_id") == user["id"]}

    if not cid_to_name:
        return {"system_id": system_id, "rows": [], "total": 0,
                "campaign_count": 0}

    q: Dict[str, Any] = {"campaign_id": {"$in": list(cid_to_name.keys())}}
    if kind:
        if kind not in REFERENCE_KINDS:
            raise HTTPException(400, f"Unknown kind {kind!r}.")
        q["kind"] = kind
    rows = await db.campaign_reference.find(q, {"_id": 0}) \
                                        .sort("created_at", -1).to_list(2000)
    # Strip GM-only rows for non-GMs of that campaign.
    visible: List[dict] = []
    for r in rows:
        if (r.get("fields") or {}).get("gm_only") and r["campaign_id"] not in gm_cids and not is_admin:
            continue
        r["campaign_name"] = cid_to_name.get(r["campaign_id"])
        visible.append(r)
    return {
        "system_id": system_id,
        "rows": visible,
        "total": len(visible),
        "campaign_count": len(cid_to_name),
    }

