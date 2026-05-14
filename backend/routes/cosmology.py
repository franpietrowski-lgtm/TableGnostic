"""V6.25.53 — Evereantha cosmology API.

Exposes the hard-seeded Faces of Aurae × Faces of Mortiscura tables
+ the Cosmological Tension opposition matrix.

  GET /api/cosmology/evereantha
      → full payload (Magic Architect quick-ref consumes this).
  GET /api/cosmology/evereantha/opposition?attacker=<id>&defender=<id>
      → single row (encounter chat roller consumes this).

Both endpoints are auth-required (any signed-in user can read; no GM
gate, since the cosmology is canon for every Evereantha campaign and
players need to reference it from the Magic Architect view too).
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query

from system_data.evereantha_cosmology import (
    get_cosmology_payload, get_face, get_opposition,
)
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["cosmology"])


@router.get("/cosmology/evereantha")
async def cosmology_evereantha(user: dict = Depends(get_current_user)):
    """Magic Architect quick-ref / encounter roller — same payload."""
    return get_cosmology_payload()


@router.get("/cosmology/evereantha/opposition")
async def cosmology_opposition(
    attacker: str = Query(..., description="Attacker Face id (e.g. luxantia)"),
    defender: str = Query(..., description="Defender Face id (e.g. obscuritia)"),
    user: dict = Depends(get_current_user),
):
    """Lookup the tension between two Faces. Returns a single row
    suitable for splicing into a chat-roller dropdown."""
    if not get_face(attacker):
        raise HTTPException(404, f"Unknown attacker face: {attacker}")
    if not get_face(defender):
        raise HTTPException(404, f"Unknown defender face: {defender}")
    return get_opposition(attacker, defender)
