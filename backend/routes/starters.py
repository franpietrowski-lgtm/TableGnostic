"""V6.25.58 — Featured Starter Campaigns gallery.

An admin-curated list of `.tgcampaign.json` bundles ready for one-click
download from the public landing page. Provides a discoverability flywheel
for new GMs who don't want to forge an empty campaign — they pick a
starter (Evereantha, Cypher one-shot, BESM-Anime tutorial, etc.),
download the bundle, and re-upload through the Phase C import flow.

Schema (`starter_campaigns` collection):
  {
    id            : str  (uuid)
    slug          : str  (kebab-case, unique, url-safe)
    title         : str
    system_id     : str  (`besm-4e` | `dnd-5e` | `cypher` | `anime-5e`)
    blurb         : str  (≤200 chars, shown on the gallery tile)
    blurb_long    : str  (≤2000 chars, shown on the detail expand)
    featured      : bool (rendered above non-featured)
    order         : int  (ascending sort; ties broken by created_at desc)
    downloads     : int  (incremented on each public download)
    bytes         : int  (size of the bundle in bytes)
    bundle        : dict (the .tgcampaign.json payload)
    created_at    : iso
    created_by    : str  (admin user id)
    created_by_name : str
  }

Endpoints:
  Public (no auth):
    GET  /api/public/starters
    GET  /api/public/starters/{slug}/download
  Admin only:
    POST   /api/admin/starters/from-campaign/{cid}    — export an
        existing campaign owned by anyone & store as a starter.
    POST   /api/admin/starters                         — upload a
        .tgcampaign.json file directly + metadata.
    PATCH  /api/admin/starters/{slug}                  — edit metadata.
    DELETE /api/admin/starters/{slug}
"""
from __future__ import annotations
import io
import json
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["starters"])


_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slugify(s: str) -> str:
    out = _SLUG_RE.sub("-", (s or "").strip().lower()).strip("-")
    return out or "starter"


async def _next_order() -> int:
    last = await db.starter_campaigns.find(
        {}, {"_id": 0, "order": 1},
    ).sort([("order", -1)]).limit(1).to_list(1)
    return (last[0]["order"] + 10) if last and isinstance(last[0].get("order"), int) else 10


def _public_view(row: Dict[str, Any]) -> Dict[str, Any]:
    """Strip the heavy bundle payload + admin-only fields for public list."""
    return {
        "slug": row.get("slug"),
        "title": row.get("title"),
        "system_id": row.get("system_id"),
        "blurb": row.get("blurb") or "",
        "blurb_long": row.get("blurb_long") or "",
        "featured": bool(row.get("featured")),
        "order": row.get("order", 0),
        "downloads": row.get("downloads", 0),
        "bytes": row.get("bytes", 0),
        "created_at": row.get("created_at"),
        "stats": row.get("stats") or {},
    }


# ─────────────────────── PUBLIC ───────────────────────

@router.get("/public/starters")
async def list_starters():
    """Public — landing-page gallery. Featured first, then by order ASC."""
    rows = await db.starter_campaigns.find({}, {"_id": 0, "bundle": 0}).to_list(200)
    rows.sort(key=lambda r: (
        0 if r.get("featured") else 1,
        r.get("order", 9999),
        -((r.get("created_at") or "")).__hash__(),
    ))
    return {"rows": [_public_view(r) for r in rows], "total": len(rows)}


@router.get("/public/starters/{slug}/download")
async def download_starter(slug: str):
    """Public — streams the `.tgcampaign.json` bundle. Increments downloads."""
    row = await db.starter_campaigns.find_one({"slug": slug}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Starter not found")
    body = json.dumps(row.get("bundle") or {}, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    # Fire-and-forget download counter; never blocks the actual download.
    try:
        await db.starter_campaigns.update_one(
            {"slug": slug}, {"$inc": {"downloads": 1}},
        )
    except Exception:
        pass
    fname = f"{slug}.tgcampaign.json"
    return StreamingResponse(
        io.BytesIO(body),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{fname}"',
            "X-TG-Bundle-Schema": str((row.get("bundle") or {}).get("schema_version", 1)),
            "X-TG-Bundle-Bytes": str(len(body)),
        },
    )


# ─────────────────────── ADMIN ───────────────────────

class StarterMetaIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    system_id: str = Field(min_length=1, max_length=20)
    blurb: str = Field("", max_length=200)
    blurb_long: str = Field("", max_length=2000)
    featured: bool = False
    order: Optional[int] = None
    slug: Optional[str] = None


class StarterPatchIn(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    blurb: Optional[str] = Field(None, max_length=200)
    blurb_long: Optional[str] = Field(None, max_length=2000)
    featured: Optional[bool] = None
    order: Optional[int] = None


def _require_admin(user: dict):
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only.")


@router.post("/admin/starters/from-campaign/{cid}")
async def starter_from_campaign(
    cid: str,
    body: StarterMetaIn,
    user: dict = Depends(get_current_user),
):
    """Capture an existing campaign as a public starter — runs the same
    export logic from Phase C internally so we never drift between
    "what users get" and "what GMs download from their own export"."""
    _require_admin(user)
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Source campaign not found")

    # Reuse the bundle assembly from Phase C — keeps the schema in sync.
    from routes.campaign_export import (
        CAMPAIGN_BOUND, PER_SESSION, EXPORT_SCHEMA_VERSION,
    )
    bundle: Dict[str, Any] = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": now_iso(),
        "exported_by": {"id": user["id"], "name": user.get("name", "")},
        "source": {
            "campaign_id": cid,
            "name": camp.get("name", ""),
            "system_id": camp.get("system_id"),
        },
        "campaign": sanitize(camp),
        "collections": {},
        "per_session": {},
        "stats": {},
    }
    session_ids = []
    for col in CAMPAIGN_BOUND:
        try:
            docs = await db[col].find({"campaign_id": cid}, {"_id": 0}).to_list(50000)
        except Exception:
            docs = []
        if docs:
            bundle["collections"][col] = docs
            bundle["stats"][col] = len(docs)
            if col == "sessions":
                session_ids = [d["id"] for d in docs if isinstance(d.get("id"), str)]
    if session_ids:
        for col in PER_SESSION:
            try:
                docs = await db[col].find(
                    {"session_id": {"$in": session_ids}}, {"_id": 0},
                ).to_list(200000)
            except Exception:
                docs = []
            if docs:
                bundle["per_session"][col] = docs

    raw = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return await _persist_starter(body, raw, bundle, user)


@router.post("/admin/starters")
async def upload_starter(
    file: UploadFile = File(...),
    title: str = Form(...),
    system_id: str = Form(...),
    blurb: str = Form(""),
    blurb_long: str = Form(""),
    featured: bool = Form(False),
    order: Optional[int] = Form(None),
    slug: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
):
    """Upload a pre-existing `.tgcampaign.json` (e.g. one a user emailed in)
    directly as a starter, without going through an in-pod campaign first."""
    _require_admin(user)
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty upload.")
    if len(raw) > 64 * 1024 * 1024:
        raise HTTPException(413, "Bundle exceeds 64 MB limit.")
    try:
        bundle = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise HTTPException(400, f"Bundle is not valid JSON: {e}")
    if not isinstance(bundle, dict) or "campaign" not in bundle:
        raise HTTPException(400, "Bundle missing required `campaign` field.")

    meta = StarterMetaIn(
        title=title, system_id=system_id, blurb=blurb,
        blurb_long=blurb_long, featured=featured, order=order, slug=slug,
    )
    return await _persist_starter(meta, raw, bundle, user)


async def _persist_starter(
    body: StarterMetaIn, raw: bytes, bundle: Dict[str, Any], user: dict,
) -> Dict[str, Any]:
    slug = body.slug or _slugify(body.title)
    # Unique-slug guard: bump with -2 / -3 … if needed so admin can re-upload.
    base = slug
    n = 1
    while await db.starter_campaigns.find_one({"slug": slug}, {"_id": 0, "slug": 1}):
        n += 1
        slug = f"{base}-{n}"

    order = body.order if body.order is not None else await _next_order()

    doc = {
        "id": new_id(),
        "slug": slug,
        "title": body.title,
        "system_id": body.system_id,
        "blurb": body.blurb or "",
        "blurb_long": body.blurb_long or "",
        "featured": bool(body.featured),
        "order": int(order),
        "downloads": 0,
        "bytes": len(raw),
        "stats": bundle.get("stats") or {},
        "bundle": bundle,
        "created_at": now_iso(),
        "created_by": user["id"],
        "created_by_name": user.get("name", ""),
    }
    await db.starter_campaigns.insert_one(doc)
    return {"ok": True, "starter": _public_view(doc)}


@router.patch("/admin/starters/{slug}")
async def patch_starter(slug: str, body: StarterPatchIn,
                        user: dict = Depends(get_current_user)):
    _require_admin(user)
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update:
        return {"ok": True, "noop": True}
    r = await db.starter_campaigns.update_one({"slug": slug}, {"$set": update})
    if r.matched_count == 0:
        raise HTTPException(404, "Starter not found")
    row = await db.starter_campaigns.find_one({"slug": slug}, {"_id": 0, "bundle": 0})
    return {"ok": True, "starter": _public_view(row)}


@router.delete("/admin/starters/{slug}")
async def delete_starter(slug: str, user: dict = Depends(get_current_user)):
    _require_admin(user)
    r = await db.starter_campaigns.delete_one({"slug": slug})
    if r.deleted_count == 0:
        raise HTTPException(404, "Starter not found")
    return {"ok": True, "deleted": slug}


@router.get("/admin/starters")
async def list_starters_admin(user: dict = Depends(get_current_user)):
    """Admin queue — shows download counts + bundle sizes."""
    _require_admin(user)
    rows = await db.starter_campaigns.find(
        {}, {"_id": 0, "bundle": 0},
    ).sort([("order", 1)]).to_list(500)
    return {"rows": [_public_view(r) for r in rows], "total": len(rows)}
