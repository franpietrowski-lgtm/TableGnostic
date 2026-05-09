"""Leads — public landing-page lead capture + admin viewer.

POST /api/leads         (public)  — name, email, phone, location, role,
                                    primary_system, message, consent
GET  /api/leads         (admin)   — paginated list, newest first
GET  /api/leads/count   (admin)   — total count + last-7-days count
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, field_validator

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api/leads", tags=["leads"])


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=40)
    location: Optional[str] = Field(default=None, max_length=120)
    role: str = Field(min_length=1, max_length=40)
    primary_system: Optional[str] = Field(default=None, max_length=80)
    message: Optional[str] = Field(default=None, max_length=2000)
    consent: bool

    @field_validator("role")
    @classmethod
    def _role_ok(cls, v: str) -> str:
        allowed = {"gm", "player", "worldbuilder", "homebrew_creator", "publisher"}
        if v.lower().replace(" ", "_").replace("-", "_") not in allowed:
            raise ValueError("invalid role")
        return v.lower().replace(" ", "_").replace("-", "_")


@router.post("")
async def create_lead(body: LeadIn, request: Request):
    """Public landing-page lead capture.

    Stores the visitor's contact in MongoDB. Idempotent on (email, role)
    within 24h: the same email+role submitted twice in a day is upserted
    rather than duplicated, so we don't accumulate spam from form re-tries.
    """
    if not body.consent:
        raise HTTPException(400, "Consent is required.")

    email = body.email.lower()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    existing = await db.leads.find_one({
        "email": email, "role": body.role, "created_at": {"$gte": cutoff}
    })

    doc_update = {
        "email": email,
        "name": body.name.strip(),
        "phone": (body.phone or "").strip() or None,
        "location": (body.location or "").strip() or None,
        "role": body.role,
        "primary_system": (body.primary_system or "").strip() or None,
        "message": (body.message or "").strip() or None,
        "consent": True,
        "user_agent": request.headers.get("user-agent", "")[:300],
        "ip": (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
               or (request.client.host if request.client else "")),
        "updated_at": now_iso(),
    }

    if existing:
        await db.leads.update_one({"id": existing["id"]}, {"$set": doc_update})
        return {"ok": True, "id": existing["id"], "deduped": True}

    lead_id = new_id()
    doc = {"id": lead_id, "created_at": now_iso(), **doc_update}
    await db.leads.insert_one(doc)
    return {"ok": True, "id": lead_id, "deduped": False}


@router.get("")
async def list_leads(limit: int = 100, skip: int = 0,
                     user: dict = Depends(get_current_user)):
    """Admin-only paginated list of leads, newest first."""
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    limit = max(1, min(500, int(limit)))
    skip = max(0, int(skip))
    cursor = db.leads.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = [sanitize(d) async for d in cursor]
    total = await db.leads.count_documents({})
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.get("/count")
async def lead_counts(user: dict = Depends(get_current_user)):
    """Admin-only — totals + last-7-day rolling count for a quick KPI badge."""
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    total = await db.leads.count_documents({})
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    last_7 = await db.leads.count_documents({"created_at": {"$gte": week_ago}})
    return {"total": total, "last_7_days": last_7}
