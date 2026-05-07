"""Macros — V6.25.7

Per-campaign + per-user named dice macros. Players use them in chat as
`/<macro_name>` with an optional `+N` modifier injection for
advantage / edges / Effort / obstacles before the roll resolves.

Format example:
    name:    "strike"
    formula: "1d20+STR+prof"
    label:   "Sword Strike"   (optional)

Resolution path lives in `channels.py`'s `_resolve_macro`. This file
owns the CRUD + storage shape only.
"""
from __future__ import annotations
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["macros"])


_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,30}$")


class MacroIn(BaseModel):
    name: str
    formula: str = Field(min_length=1, max_length=200)
    label: str = Field(default="", max_length=80)
    scope: str = Field(default="user")  # "user" | "campaign"

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not _NAME_RE.match(v):
            raise ValueError("Macro name must start with a letter and only "
                              "contain letters, digits, '_' or '-' (max 31).")
        return v

    @field_validator("scope")
    @classmethod
    def _validate_scope(cls, v: str) -> str:
        if v not in ("user", "campaign"):
            raise ValueError("scope must be 'user' or 'campaign'")
        return v


@router.get("/campaigns/{cid}/macros")
async def list_macros(cid: str, user: dict = Depends(get_current_user)):
    """List macros visible on this campaign — that means the user's
    own + every campaign-scope macro authored on this campaign."""
    rows = await db.macros.find({
        "campaign_id": cid,
        "$or": [
            {"scope": "campaign"},
            {"scope": "user", "owner_id": user["id"]},
        ],
    }, {"_id": 0}).to_list(length=None)
    return rows


@router.post("/campaigns/{cid}/macros")
async def create_macro(cid: str, body: MacroIn,
                          user: dict = Depends(get_current_user)):
    """Create a macro. campaign-scope macros require GM."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if body.scope == "campaign" and camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can author campaign-scope macros")
    # Uniqueness within scope.
    dup_q = {"campaign_id": cid, "name": body.name, "scope": body.scope}
    if body.scope == "user":
        dup_q["owner_id"] = user["id"]
    if await db.macros.find_one(dup_q, {"_id": 0}):
        raise HTTPException(400,
            f"A {body.scope}-scope macro named '{body.name}' already exists.")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "owner_id": user["id"],
        "owner_name": user.get("name") or "",
        "name": body.name,
        "formula": body.formula,
        "label": body.label or body.name,
        "scope": body.scope,
        "use_count": 0,
        "last_used_at": None,
        "created_at": now_iso(),
    }
    await db.macros.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@router.delete("/campaigns/{cid}/macros/{mid}")
async def delete_macro(cid: str, mid: str,
                          user: dict = Depends(get_current_user)):
    m = await db.macros.find_one({"id": mid, "campaign_id": cid}, {"_id": 0})
    if not m:
        raise HTTPException(404, "Macro not found")
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if m["owner_id"] != user["id"] and camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only the macro owner or GM can delete it.")
    await db.macros.delete_one({"id": mid})
    return {"ok": True}


@router.put("/campaigns/{cid}/macros/{mid}")
async def update_macro(cid: str, mid: str, body: MacroIn,
                          user: dict = Depends(get_current_user)):
    m = await db.macros.find_one({"id": mid, "campaign_id": cid}, {"_id": 0})
    if not m:
        raise HTTPException(404, "Macro not found")
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if m["owner_id"] != user["id"] and camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only the macro owner or GM can edit it.")
    await db.macros.update_one({"id": mid}, {"$set": {
        "name": body.name, "formula": body.formula, "label": body.label,
        "scope": body.scope,
    }})
    return {"ok": True}
