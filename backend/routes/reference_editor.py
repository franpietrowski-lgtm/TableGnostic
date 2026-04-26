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

REFERENCE_KINDS = {"weapon", "armor", "item", "companion", "custom"}

router = APIRouter(prefix="/api", tags=["reference-editor"])


# ─────── Pydantic ───────

class ReferenceItemIn(BaseModel):
    kind: Literal["weapon", "armor", "item", "companion", "custom"]
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
