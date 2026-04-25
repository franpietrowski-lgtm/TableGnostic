"""Sample-content seeding (Evereantha PCs).

GM-only endpoint that drops three Adventurous-tier sample PCs into a
BESM 4E campaign so a freshly minted table has bodies to push around.
Idempotent in the sense that re-runs append fresh copies — the GM
should clean up duplicates manually if reseeding.
"""
from fastapi import APIRouter, Depends, HTTPException

from core.cost_engine import calc_derived, calc_spent_points
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["seed"])


@router.post("/campaigns/{cid}/seed/evereantha")
async def seed_evereantha_pcs(cid: str, user: dict = Depends(get_current_user)):
    """GM-only: insert three Adventurous-tier sample PCs from the public
    Evereantha setting. They become NPCs / pre-built sheets the GM can hand
    to players who want to drop in fast.
    Only allowed on BESM 4E system campaigns; samples use core BESM mechanics.
    """
    from seed_evereantha import EVEREANTHA_PCS

    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may seed sample characters")
    if camp.get("system_id", "besm-4e") != "besm-4e":
        raise HTTPException(400, "Evereantha sample PCs are BESM 4E builds. "
                                  "Switch the campaign system to BESM 4E first.")
    created = []
    for pc in EVEREANTHA_PCS:
        doc = {
            "id": new_id(),
            "campaign_id": cid,
            "owner_id": user["id"],
            "owner_name": user["name"],
            "created_at": now_iso(),
            "name": pc["name"],
            "concept": pc["concept"],
            "power_level": pc["power_level"],
            "total_points": pc["total_points"],
            "token_color": pc.get("token_color", ""),
            "size": pc.get("size", "Medium"),
            "stats": pc["stats"],
            "attributes": pc["attributes"],
            "defects": pc["defects"],
            "skills": pc.get("skills", []),
            "power_packs": pc.get("power_packs", []),
            "notes": "Evereantha sample PC — Adventurous tier (~80 pts).",
            "published": True,
            "folio": pc.get("folio", {}),
        }
        doc["derived"] = calc_derived(doc, camp)
        doc["spent"] = calc_spent_points(doc)
        await db.characters.insert_one(doc)
        created.append(sanitize(doc))
    return {"created": len(created), "characters": created}
