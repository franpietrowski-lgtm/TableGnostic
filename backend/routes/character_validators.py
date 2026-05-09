"""Character Validators — V6.25.34.

Live validation pass over a character sheet. Returns warnings the player
or GM should resolve (or dismiss):

  • duplicate_attribute   — same attribute name appears twice on the sheet
  • over_benchmark_attr   — attribute level > primer.max_per_attribute_rank
  • over_benchmark_stat   — Body/Mind/Soul > genre/power-level cap
  • over_benchmark_defect — defect rank above what the primer permits

All warnings can be dismissed individually. A dismissed warning is
recorded on `character.folio.dismissed_validations` so it doesn't
re-appear *unless* the underlying state changes (a NEW duplicate of
a DIFFERENT attribute, a new over-benchmark row, etc.).

Weapons / Items are EXEMPT from benchmark caps — they routinely run 1-30
ranks and balance is the GM's responsibility (Anime-style cinematic).
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["validation"])


# ── Genre / power-level → stat / defect benchmarks ─────────────────
# Conservative defaults from BESM 4E p.21-25 + Anime 5E SRD norms.
# A campaign primer's `max_per_attribute_rank` overrides our attribute cap.
# When a campaign sets a value of 0 we fall back to these defaults.
_DEFAULT_STAT_CAP_BY_PL = {
    "Slice-of-Life":  6,
    "Adventurous":    7,
    "Heroic":         8,
    "Mythic":        10,
    "Cosmic":        12,
}
_DEFAULT_ATTR_CAP_BY_PL = {
    "Slice-of-Life":  3,
    "Adventurous":    5,
    "Heroic":         6,
    "Mythic":         8,
    "Cosmic":        10,
}
_DEFAULT_DEFECT_RANK_CAP = 3


def _benchmarks_for(camp: dict) -> Dict[str, int]:
    pl = (camp.get("power_level") or "Heroic")
    attr_override = int(camp.get("max_per_attribute_rank") or 0)
    return {
        "stat_cap":        _DEFAULT_STAT_CAP_BY_PL.get(pl, 8),
        "attr_cap":        attr_override or _DEFAULT_ATTR_CAP_BY_PL.get(pl, 6),
        "defect_rank_cap": _DEFAULT_DEFECT_RANK_CAP,
    }


def _signature(kind: str, target_name: str, level_or_rank: Optional[int] = None) -> str:
    """Stable signature for a warning — used for dismissal idempotency.

    By default we tie the dismissal to (kind, target_name); for benchmark
    warnings we also include the level / rank so that **raising** the
    same row above benchmark surfaces a fresh warning even if a previous
    over-benchmark warning was dismissed.
    """
    if level_or_rank is not None:
        return f"{kind}:{target_name}:{level_or_rank}"
    return f"{kind}:{target_name}"


def _is_weapon_row(row: dict) -> bool:
    """Return True for any attribute row that the GM marked as a weapon
    (kind / category contains 'weapon') — these are exempt from caps."""
    n = (row.get("name") or "").lower()
    cat = (row.get("category") or "").lower()
    kind = (row.get("kind") or "").lower()
    if "weapon" in n:
        return True
    if "weapon" in cat:
        return True
    if "weapon" in kind:
        return True
    return False


def _scan(character: dict, camp: dict) -> List[dict]:
    bench = _benchmarks_for(camp)
    dismissed = {(d.get("signature") or _signature(d.get("kind",""), d.get("target_name","")))
                  for d in (character.get("folio") or {}).get("dismissed_validations", [])}
    warnings: List[dict] = []

    # ---- duplicate attributes (collapsing rule, BESM 4E p.96) ----
    seen: Dict[str, List[int]] = {}
    for i, a in enumerate(character.get("attributes") or []):
        if _is_weapon_row(a):
            continue
        n = (a.get("name") or "").strip().lower()
        if not n:
            continue
        seen.setdefault(n, []).append(i)
    for n, idxs in seen.items():
        if len(idxs) <= 1:
            continue
        sig = _signature("duplicate_attribute", n)
        if sig in dismissed:
            continue
        warnings.append({
            "id":           new_id(),
            "kind":         "duplicate_attribute",
            "target_name":  n,
            "signature":    sig,
            "indices":      idxs,
            "message":      f"Attribute '{n}' is listed {len(idxs)} times. "
                            "BESM/Anime 5E rule: collapse to one row at the "
                            "highest level and refund the duplicate's CP.",
            "severity":     "warning",
            "weapon_exempt": False,
        })

    # ---- over-benchmark attribute level ----
    for i, a in enumerate(character.get("attributes") or []):
        if _is_weapon_row(a):
            continue
        lvl = int(a.get("level") or 0)
        if lvl > bench["attr_cap"]:
            sig = _signature("over_benchmark_attr", (a.get("name") or "").lower(), lvl)
            if sig in dismissed:
                continue
            warnings.append({
                "id":           new_id(),
                "kind":         "over_benchmark_attr",
                "target_name":  a.get("name") or "Unnamed",
                "level":        lvl,
                "cap":          bench["attr_cap"],
                "signature":    sig,
                "message":      f"Attribute '{a.get('name')}' L{lvl} exceeds the "
                                f"primer benchmark of L{bench['attr_cap']} for "
                                f"this Power Level.",
                "severity":     "warning",
                "weapon_exempt": False,
            })

    # ---- over-benchmark stat (Body/Mind/Soul) ----
    stats = character.get("stats") or {}
    for k, v in stats.items():
        v = int(v or 0)
        if v > bench["stat_cap"]:
            sig = _signature("over_benchmark_stat", k, v)
            if sig in dismissed:
                continue
            warnings.append({
                "id":           new_id(),
                "kind":         "over_benchmark_stat",
                "target_name":  k.title(),
                "level":        v,
                "cap":          bench["stat_cap"],
                "signature":    sig,
                "message":      f"Stat '{k.title()}' = {v} exceeds the "
                                f"benchmark of {bench['stat_cap']} for this "
                                f"Power Level.",
                "severity":     "warning",
                "weapon_exempt": False,
            })

    # ---- over-benchmark defect rank ----
    for d in (character.get("defects") or []):
        rk = int(d.get("rank") or 0)
        if rk > bench["defect_rank_cap"]:
            sig = _signature("over_benchmark_defect",
                              (d.get("name") or "").lower(), rk)
            if sig in dismissed:
                continue
            warnings.append({
                "id":           new_id(),
                "kind":         "over_benchmark_defect",
                "target_name":  d.get("name") or "Unnamed",
                "level":        rk,
                "cap":          bench["defect_rank_cap"],
                "signature":    sig,
                "message":      f"Defect '{d.get('name')}' R{rk} exceeds the "
                                f"benchmark rank cap of R{bench['defect_rank_cap']}.",
                "severity":     "warning",
                "weapon_exempt": False,
            })

    return warnings


# ── Routes ─────────────────────────────────────────────────────────
class DismissIn(BaseModel):
    signature: str
    note: Optional[str] = ""


@router.get("/characters/{cid}/validations")
async def list_character_validations(cid: str,
                                      user: dict = Depends(get_current_user)):
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found.")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    is_gm = user["id"] == camp.get("gm_id") or user.get("role") == "admin"
    is_owner = ch.get("user_id") == user["id"]
    if not (is_gm or is_owner):
        raise HTTPException(403, "Not authorised for this character.")
    warnings = _scan(ch, camp)
    return {
        "character_id": cid,
        "campaign_id":  camp["id"],
        "benchmarks":   _benchmarks_for(camp),
        "warnings":     warnings,
        "count":        len(warnings),
    }


@router.post("/characters/{cid}/validations/dismiss")
async def dismiss_character_validation(cid: str, body: DismissIn,
                                        user: dict = Depends(get_current_user)):
    """Dismiss a warning by its stable signature. Persists on
    `folio.dismissed_validations`. Re-issues if state changes (a new
    duplicate of a different attribute, a new over-benchmark, etc.)."""
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found.")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    is_gm = user["id"] == camp.get("gm_id") or user.get("role") == "admin"
    is_owner = ch.get("user_id") == user["id"]
    if not (is_gm or is_owner):
        raise HTTPException(403, "Not authorised for this character.")
    folio = ch.get("folio") or {}
    rows = list(folio.get("dismissed_validations") or [])
    if body.signature in {(r.get("signature") or "") for r in rows}:
        return {"already_dismissed": True}
    parts = body.signature.split(":")
    rows.append({
        "signature":    body.signature,
        "kind":         parts[0] if parts else "",
        "target_name":  parts[1] if len(parts) > 1 else "",
        "note":         (body.note or "").strip(),
        "dismissed_at": now_iso(),
        "dismissed_by": user["id"],
    })
    folio["dismissed_validations"] = rows
    await db.characters.update_one({"id": cid}, {"$set": {"folio": folio}})
    return {"dismissed": body.signature, "total_dismissed": len(rows)}


@router.get("/campaigns/{cid}/validations")
async def list_campaign_validations(cid: str,
                                     user: dict = Depends(get_current_user)):
    """GM dashboard view: scans every character on the campaign and
    returns aggregated warnings. Useful surface for the Director Console."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    if user["id"] != camp.get("gm_id") and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM (or admin) can scan the table.")
    chars = await db.characters.find(
        {"campaign_id": cid}, {"_id": 0}
    ).to_list(200)
    by_char = []
    total = 0
    for ch in chars:
        ws = _scan(ch, camp)
        if ws:
            by_char.append({
                "character_id":   ch["id"],
                "character_name": ch.get("name") or "Unnamed",
                "owner_id":       ch.get("user_id"),
                "warnings":       ws,
            })
            total += len(ws)
    return {
        "campaign_id":      cid,
        "benchmarks":       _benchmarks_for(camp),
        "characters":       by_char,
        "total_warnings":   total,
        "characters_dirty": len(by_char),
    }
