"""Character rules-compliance validator + dual-approval workflow.

Purpose
───────
BESM 4E and Anime 5E (via the BESM-style point-buy supplement) both run
on a recorded-scale Character-Point economy tied to the campaign's
chosen Power Level. A player at the table must not exceed the cap
agreed to by the GM — otherwise the encounter / CR math goes sideways.

This module gives every character a verifiable mechanical audit and a
dual approval gate before they can be seated for play:

  1. **App-internal review** (`/api/characters/{id}/validate`)
     Runs a rules-only compliance check — sums the paid cost of
     Attributes × Level minus Defect refunds, Skills × Level, plus
     stat-point spend (Body/Mind/Soul — BESM) or the BESM point-buy
     layer (Anime 5E), compares against the character's declared
     `total_points` (which equals the Power Level cap plus any
     discretionary award the GM recorded). Returns `passes_rules: bool`
     + a structured breakdown with any over-spend flagged.

  2. **GM review** (`/api/characters/{id}/approve-for-play`)
     Only the campaign GM (or admin) may toggle this. GM sees the same
     validator output and explicitly ratifies. Setting a per-campaign
     `house_rules: "…"` string short-circuits the app-internal gate
     (the GM is declaring the rules are bent by design); in that case
     only the GM approval is required, and a visible badge communicates
     the house-rules exception on the sheet.

A character with `app_validated=True` AND `gm_approved=True` (or
`gm_approved=True` alone if house rules are in effect) is "Approved for
Play". Session seat-take will refuse to seat an un-approved PC unless
the GM overrides.

This module is intentionally ADDITIVE — we do NOT block existing
characters; the new fields default to `False` and surface as a warning
on the sheet until explicitly approved.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.db import db, now_iso
from core.security import get_current_user


router = APIRouter(prefix="/api", tags=["character-validation"])


# ─── BESM 4E stat-point economics (p.21 BESM 4E) ───
# Body / Mind / Soul each cost 2 CP per point above the base.
# Base for an adult human Heroic hero is typically 4. The rulebook
# allows dropping to 1 for a refund or raising toward 10/12 for more
# CP spend — but the sanctioned MINIMUM varies by campaign style.
STAT_COST_PER_POINT = 2  # BESM 4E p.21 — fixed for Body/Mind/Soul
STAT_BASE = 4  # standard adult human baseline


def _besm_points_breakdown(ch: Dict[str, Any]) -> Dict[str, Any]:
    """Sum the paid Character-Point cost for a BESM 4E sheet (also
    the BESM-style point-buy layer of an Anime 5E hybrid sheet).

    Returns a structured dict that the UI can render row-by-row.
    """
    lines: List[Dict[str, Any]] = []

    # ── Core stats — Body/Mind/Soul × 2 CP each above baseline.
    stats = ch.get("stats") or {}
    stat_total = 0
    for k in ("body", "mind", "soul"):
        v = int(stats.get(k, STAT_BASE) or 0)
        cost = max(0, (v - STAT_BASE) * STAT_COST_PER_POINT)
        stat_total += cost
        lines.append({
            "kind": "stat", "name": k.capitalize(),
            "level": v, "cost_per_level": STAT_COST_PER_POINT,
            "baseline": STAT_BASE,
            "points": cost,
            "note": f"{v} − {STAT_BASE} baseline × {STAT_COST_PER_POINT} CP/pt",
        })

    # ── Attributes (paid at cost_per_level × level). Item-defect
    # refunds are applied per-attribute (BESM 4E V4.1 — Items p.82).
    # V6.4: Enhancement / Limiter VALUES (BESM Extras ch.3) shift the
    # effective level AND the per-level cost modifier. Syntax examples:
    #   Flight (Lvl 1) with no modifiers      → cost_mod = cpl, eff_lvl = 1
    #   Flight Range 1 (4) [+3 Limiters]      → eff_lvl = 4, cost_mod = cpl × 4/1
    # Canonical rule: positive values are Limiters (increase eff level,
    # pay more per CP), negative are Enhancements (decrease eff level,
    # power is broader). We track BOTH sides as explicit value rows on
    # the attribute; legacy string tags default to ±1 based on list.
    attr_total = 0
    warnings: List[str] = []
    for a in (ch.get("attributes") or []):
        lvl = int(a.get("level") or 1)
        cpl = float(a.get("cost_per_level") or 0)

        # Sum enhancement + limiter value deltas.
        def _mods_sum(items, legacy_sign):
            total = 0
            for m in (items or []):
                if isinstance(m, dict):
                    total += int(m.get("value") or 0)
                else:
                    total += legacy_sign  # bare string → ±1
            return total

        enh_delta = _mods_sum(a.get("enhancements"), -1)  # enhancements lower eff
        lim_delta = _mods_sum(a.get("limiters"), +1)       # limiters raise eff
        net_delta = enh_delta + lim_delta

        # Warn-only on out-of-range modifier values (Absolute Power allows beyond).
        for m in (a.get("enhancements") or []) + (a.get("limiters") or []):
            if isinstance(m, dict):
                v = int(m.get("value") or 0)
                if abs(v) > 12:
                    warnings.append(
                        f"Attribute '{a.get('name')}' modifier '{m.get('name')}' "
                        f"has value {v} (outside canonical ±12 range; "
                        f"Absolute Power supplement only)."
                    )

        # Effective level can be explicitly set on the attribute; else
        # compute from level + net delta (floored at 1).
        eff_lvl_override = a.get("effective_level")
        eff_lvl = int(eff_lvl_override) if eff_lvl_override else max(1, lvl + net_delta)

        # Cost is paid on the POST-modifier line, not the assigned level:
        # `cost_modifier` (if set) takes precedence, else we recompute
        # from cpl scaled by (eff_lvl / lvl) rounded up.
        cost_mod_override = a.get("cost_modifier")
        if cost_mod_override:
            gross = float(cost_mod_override) * lvl
        else:
            # Canonical BESM Extras: each +1 value on a Limiter means you
            # pay cpl × 1 extra per level. Each −1 on an Enhancement means
            # you pay cpl × 1 less per level (floor at 1 CP total).
            gross = max(1, cpl * lvl + net_delta * lvl)

        refund = sum(
            float(d.get("points_per_rank") or 0) * int(d.get("rank") or 0)
            for d in (a.get("defects") or [])
        )
        paid = max(0, int(round(gross)) - int(round(refund)))
        attr_total += paid
        lines.append({
            "kind": "attribute",
            "name": a.get("display_name") or a.get("name"),
            "level": lvl, "effective_level": eff_lvl,
            "cost_per_level": cpl,
            "enhancement_delta": enh_delta,
            "limiter_delta": lim_delta,
            "gross": int(round(gross)), "item_defect_refund": int(round(refund)),
            "points": paid,
            "note": (
                f"{cpl}×{lvl}"
                + (f" ±{net_delta} mods" if net_delta else "")
                + (f" − {int(round(refund))} item-defect refund" if refund else "")
            ),
        })

    # ── Skill Groups (cost_per_level × level).
    skill_total = 0
    for s in (ch.get("skills") or []):
        lvl = int(s.get("level") or 1)
        cpl = int(s.get("cost_per_level") or 0)
        cost = cpl * lvl
        skill_total += cost
        lines.append({
            "kind": "skill",
            "name": s.get("display_name") or s.get("group"),
            "level": lvl, "cost_per_level": cpl,
            "points": cost,
            "note": f"{cpl}×{lvl}",
        })

    # ── Power Packs (narrative bundles; usually 0-cost but may carry
    # an explicit `cost` field).
    pack_total = 0
    for p in (ch.get("power_packs") or []):
        cost = int(p.get("cost") or 0)
        if cost:
            pack_total += cost
            lines.append({
                "kind": "power_pack",
                "name": p.get("name"),
                "points": cost, "note": "narrative source-of-power bundle (always-on)",
            })

    # ── Power Bundles (activatable spell-like effects — BESM Extras ch.5).
    # A bundle's CP cost is paid like any attribute bundle; its invocation
    # mode (per-scene / per-charge / energy-cost) is NOT a CP modifier —
    # that's a narrative gate, not a point-spend rebate.
    bundle_total = 0
    for b in (ch.get("power_bundles") or []):
        cost = int(b.get("cost") or 0)
        if cost:
            bundle_total += cost
            lines.append({
                "kind": "power_bundle",
                "name": b.get("name"),
                "points": cost,
                "note": (
                    f"activatable · {b.get('invocation', 'per-scene')}"
                    + (f" · {b.get('charges_max')} charges" if b.get('charges_max') else "")
                    + (f" · {b.get('energy_cost')} EP/cast" if b.get('energy_cost') else "")
                ),
            })

    # ── Defects (character-level only — refund back to the pool).
    defect_refund = 0
    for d in (ch.get("defects") or []):
        refund = int(d.get("points_per_rank") or 0) * int(d.get("rank") or 0)
        defect_refund += refund
        lines.append({
            "kind": "defect",
            "name": d.get("display_name") or d.get("name"),
            "level": int(d.get("rank") or 0),
            "points": -refund,
            "note": f"{d.get('points_per_rank')}×{d.get('rank')} refund",
        })

    spent = stat_total + attr_total + skill_total + pack_total + bundle_total - defect_refund
    return {
        "stat_total": stat_total,
        "attribute_total": attr_total,
        "skill_total": skill_total,
        "power_pack_total": pack_total,
        "power_bundle_total": bundle_total,
        "defect_refund": defect_refund,
        "total_spent": spent,
        "lines": lines,
        "modifier_warnings": warnings,
    }


def _anime5e_point_buy_breakdown(folio: Dict[str, Any]) -> Dict[str, Any]:
    """Sum the BESM-style point-buy layer on an Anime 5E hybrid sheet."""
    state = (folio or {}).get("anime5e_state") or {}
    buys = state.get("point_buys") or []
    lines: List[Dict[str, Any]] = []
    total = 0
    for b in buys:
        lvl = int(b.get("level") or 1)
        cpl = float(b.get("cost_per_level") or 0)
        cost = int(cpl * lvl)
        total += cost
        lines.append({
            "kind": "point_buy",
            "name": b.get("name"),
            "level": lvl, "cost_per_level": cpl,
            "points": cost,
            "note": f"{cpl}×{lvl}",
        })
    budget = int(state.get("point_budget") or 0)
    return {"total_spent": total, "budget": budget, "lines": lines}


def _validate_character(ch: Dict[str, Any]) -> Dict[str, Any]:
    """System-aware rules validator.

    Returns:
        {
          "passes_rules": bool,
          "system_id": str,
          "total_points": int,
          "breakdown": {...},
          "issues": [str],
          "warnings": [str],
        }
    """
    folio = ch.get("folio") or {}
    dnd_state = folio.get("dnd_state")
    cypher_state = folio.get("cypher_state")
    anime_state = folio.get("anime5e_state")

    issues: List[str] = []
    warnings: List[str] = []
    sys_id = (
        "anime-5e" if anime_state else
        "dnd-5e" if dnd_state else
        "cypher" if cypher_state else
        "besm-4e"
    )

    total_points = int(ch.get("total_points") or 0)

    if sys_id == "besm-4e":
        breakdown = _besm_points_breakdown(ch)
        spent = breakdown["total_spent"]
        # Propagate modifier warnings from the breakdown helper.
        warnings.extend(breakdown.get("modifier_warnings") or [])
        if spent > total_points:
            issues.append(
                f"Over budget: {spent} CP spent vs {total_points} CP cap "
                f"(over by {spent - total_points})."
            )
        elif spent < total_points - 5:
            warnings.append(
                f"{total_points - spent} CP unspent — a lot of headroom left."
            )
        return {
            "passes_rules": not issues,
            "system_id": sys_id,
            "total_points": total_points,
            "breakdown": breakdown,
            "issues": issues,
            "warnings": warnings,
        }

    if sys_id == "anime-5e":
        # Anime 5E = D&D 5E chassis + optional BESM-style point-buy layer.
        # Compliance = the point-buy layer (if any) respects its declared
        # budget. D&D chassis compliance is class/level self-consistent —
        # we can't cleanly validate that without the full SRD state, so
        # we report a soft "chassis ok" note.
        pb = _anime5e_point_buy_breakdown(folio)
        budget = pb["budget"] or total_points or 0
        if budget > 0 and pb["total_spent"] > budget:
            issues.append(
                f"BESM-style point-buy over budget: "
                f"{pb['total_spent']} pts vs {budget} pts "
                f"(over by {pb['total_spent'] - budget})."
            )
        if dnd_state:
            lvl = int(dnd_state.get("level") or 1)
            if lvl < 1 or lvl > 20:
                issues.append(f"Chassis level {lvl} outside legal 1-20 range.")
        return {
            "passes_rules": not issues,
            "system_id": sys_id,
            "total_points": budget,
            "breakdown": {
                "point_buy": pb,
                "chassis_note": (
                    f"D&D 5E chassis: {dnd_state.get('class', '?')} "
                    f"{dnd_state.get('level', '?')} · "
                    f"{dnd_state.get('race', '?')}"
                    if dnd_state else "No chassis state recorded."
                ),
            },
            "issues": issues,
            "warnings": warnings,
        }

    if sys_id == "dnd-5e":
        lvl = int((dnd_state or {}).get("level") or 1)
        if lvl < 1 or lvl > 20:
            issues.append(f"Level {lvl} outside legal 1-20 range.")
        if not (dnd_state or {}).get("class"):
            warnings.append("No class selected on the chassis.")
        return {
            "passes_rules": not issues,
            "system_id": sys_id,
            "total_points": 0,
            "breakdown": {
                "chassis_note": f"{dnd_state.get('class', '?')} "
                                f"{dnd_state.get('level', '?')} · "
                                f"{dnd_state.get('race', '?')}",
            },
            "issues": issues,
            "warnings": warnings,
        }

    # Cypher — tier 1-6, at least descriptor/type/focus set.
    tier = int((cypher_state or {}).get("tier") or 1)
    if tier < 1 or tier > 6:
        issues.append(f"Tier {tier} outside legal 1-6 range.")
    for k in ("descriptor", "type", "focus"):
        if not (cypher_state or {}).get(k):
            warnings.append(f"No {k} selected.")
    return {
        "passes_rules": not issues,
        "system_id": sys_id,
        "total_points": 0,
        "breakdown": {
            "chassis_note": (
                f"{cypher_state.get('descriptor', '?')} "
                f"{cypher_state.get('type', '?')} who "
                f"{cypher_state.get('focus', '?')} · Tier {tier}"
            ),
        },
        "issues": issues,
        "warnings": warnings,
    }


@router.get("/characters/{cid}/validate")
async def validate_character(cid: str, user: dict = Depends(get_current_user)):
    """Read-only audit. Returns the compliance breakdown + pass/fail
    + any current app_validated / gm_approved flags (for UI state)."""
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    # Access: owner, GM, or campaign member.
    allowed = (
        user["id"] == ch.get("owner_id")
        or user["id"] == camp["gm_id"]
        or user["id"] in (camp.get("member_ids") or [])
        or user.get("role") == "admin"
    )
    if not allowed:
        raise HTTPException(403, "Not a table member.")
    v = _validate_character(ch)
    approval = ch.get("approval") or {}
    house_rules_active = bool((camp.get("house_rules") or "").strip())
    v.update({
        "character_id": cid,
        "character_name": ch.get("name"),
        "house_rules_active": house_rules_active,
        "app_validated": bool(approval.get("app_validated")),
        "gm_approved": bool(approval.get("gm_approved")),
        "approved_for_play": bool(
            (approval.get("app_validated") or house_rules_active)
            and approval.get("gm_approved")
        ),
        "approval": approval,
    })
    return v


class ApprovalIn(BaseModel):
    approved: bool = True
    note: Optional[str] = ""


@router.post("/characters/{cid}/app-validate")
async def app_validate_character(cid: str, user: dict = Depends(get_current_user)):
    """Recompute the rules validator and stamp `approval.app_validated`
    on the character. Callable by the owner (self-check) or the GM.
    Idempotent — always reflects current sheet state."""
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    allowed = (
        user["id"] == ch.get("owner_id")
        or user["id"] == camp["gm_id"]
        or user.get("role") == "admin"
    )
    if not allowed:
        raise HTTPException(403, "Only the owner or GM may run app-validation.")
    v = _validate_character(ch)
    approval = dict(ch.get("approval") or {})
    approval["app_validated"] = bool(v["passes_rules"])
    approval["app_validated_at"] = now_iso()
    approval["last_breakdown"] = v["breakdown"]
    approval["issues"] = v.get("issues") or []
    approval["warnings"] = v.get("warnings") or []
    # Any sheet change invalidates a prior GM approval — the GM must
    # re-ratify after rules-state changes (classic airlock safety).
    if approval.get("gm_approved") and approval.get("app_validated_at") != approval.get("gm_approved_sheet_version"):
        approval["gm_approved"] = False
        approval["gm_approval_stale_reason"] = "Sheet changed since last GM review."
    await db.characters.update_one({"id": cid}, {"$set": {"approval": approval}})
    return {**v, "approval": approval}


@router.post("/characters/{cid}/approve-for-play")
async def gm_approve_for_play(cid: str, body: ApprovalIn,
                               user: dict = Depends(get_current_user)):
    """GM/admin ratifies the character for live-session seating.

    Policy:
    • If the campaign has `house_rules` set, GM approval alone suffices
      (the house-rule override is recorded and the sheet shows a
      visible "House Rules" badge).
    • Otherwise the character must ALSO have `approval.app_validated`
      set — i.e. the rules compliance check must have passed. This is
      a non-bypassable guard so a GM can't accidentally approve an
      over-budget PC.
    """
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")

    house_rules = bool((camp.get("house_rules") or "").strip())
    approval = dict(ch.get("approval") or {})

    if body.approved:
        # Re-run validator so the stamped approval can't go stale by
        # the time the GM clicks the button.
        v = _validate_character(ch)
        approval["last_breakdown"] = v["breakdown"]
        approval["issues"] = v.get("issues") or []
        approval["warnings"] = v.get("warnings") or []
        approval["app_validated"] = bool(v["passes_rules"])
        approval["app_validated_at"] = now_iso()

        if not house_rules and not v["passes_rules"]:
            raise HTTPException(
                400,
                "Cannot approve — character fails app-internal rules validation "
                "and campaign has no house-rules exception. Either fix the "
                "sheet, or record a house-rule in the campaign settings."
            )

        approval["gm_approved"] = True
        approval["gm_approved_at"] = now_iso()
        approval["gm_approved_by"] = user["id"]
        approval["gm_approved_by_name"] = user["name"]
        approval["gm_approval_note"] = body.note or ""
        approval["house_rules_override"] = house_rules
        approval.pop("gm_approval_stale_reason", None)
    else:
        # Revoke.
        approval["gm_approved"] = False
        approval["gm_approved_at"] = now_iso()
        approval["gm_approval_note"] = body.note or "Approval revoked."

    await db.characters.update_one({"id": cid}, {"$set": {"approval": approval}})
    return {
        "ok": True, "character_id": cid,
        "approval": approval,
        "approved_for_play": bool(
            approval.get("gm_approved")
            and (approval.get("app_validated") or house_rules)
        ),
    }


# ─── V6.4 — Anime 5E XP→CP conversion ────────────────────────────────

def anime5e_xp_to_cp(level: int, formula: str = "flat") -> int:
    """Return the CP budget for a new Anime 5E character at the given
    adventure level, using the campaign's configured formula.

    Formulas (both user-approved for V6.4):
      * "flat"  — CP = 50 + 8 × level
      * "curve" — CP = 40 + level × (10 if level ≤ 5
                                      else 12 if level ≤ 10
                                      else 15)
    """
    lvl = max(0, int(level or 0))
    if formula == "curve":
        per = 10 if lvl <= 5 else (12 if lvl <= 10 else 15)
        return 40 + lvl * per
    return 50 + lvl * 8


@router.get("/campaigns/{cid}/anime5e-xp-curve")
async def anime5e_xp_curve(cid: str, user: dict = Depends(get_current_user)):
    """Return the CP-budget curve for the campaign's configured formula.
    Used by the Anime 5E character builder to set the default point-buy
    budget on a freshly-forged character at `primer_level_min`."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    formula = (camp.get("anime5e_xp_formula") or "flat").lower()
    level = int(camp.get("primer_level_min") or 1)
    return {
        "campaign_id": cid,
        "formula": formula,
        "primer_level_min": level,
        "cp_budget_at_level": anime5e_xp_to_cp(level, formula),
        "curve": [
            {"level": L, "cp": anime5e_xp_to_cp(L, formula)}
            for L in range(1, 21)
        ],
    }


# ─── V6.5 — Live Spend Preview for Power Bundle templates ────────
# Lets GMs hover/tap a seeded template card and see "if I import this
# onto Aeris — her 175/200 spend becomes 182/200 (fits)." Pure audit;
# nothing is persisted.

from pydantic import BaseModel as _PydBaseModel


class SimulateImportIn(_PydBaseModel):
    """What to pretend-apply. Either provide a full template (with
    components + cost) from the template library, or a raw cost to
    add on top of the existing sheet."""
    extra_cost: int = 0
    extra_bundle: Dict[str, Any] = {}


@router.post("/characters/{cid}/simulate-import")
async def simulate_import(cid: str, body: SimulateImportIn,
                           user: dict = Depends(get_current_user)):
    """Return a before/after CP-budget view for the sheet if the
    declared bundle were imported. Read-only."""
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign missing")
    # Access gate — owner / GM / member / admin.
    allowed = (
        user["id"] == ch.get("owner_id")
        or user["id"] == camp["gm_id"]
        or user["id"] in (camp.get("member_ids") or [])
        or user.get("role") == "admin"
    )
    if not allowed:
        raise HTTPException(403, "Not a table member.")

    current = _validate_character(ch)
    current_spent = current["breakdown"].get("total_spent") or 0
    current_cap = current.get("total_points") or int(ch.get("total_points") or 0)

    # Project the spend after the import.
    extra = int(body.extra_cost or 0)
    if not extra and body.extra_bundle:
        extra = int(body.extra_bundle.get("cost") or 0)
    projected_spent = current_spent + extra
    fits = projected_spent <= current_cap
    headroom = current_cap - projected_spent

    return {
        "character_id": cid,
        "character_name": ch.get("name"),
        "power_level": ch.get("power_level"),
        "current_spent": current_spent,
        "current_cap": current_cap,
        "extra_cost": extra,
        "projected_spent": projected_spent,
        "fits": fits,
        "headroom": headroom,
        "summary": (
            f"{ch.get('name')} · {ch.get('power_level')} · "
            f"{projected_spent}/{current_cap} CP"
            + (f" · OVER by {-headroom}" if not fits else f" · OK ({headroom} spare)")
        ),
    }


# ─── V6.4/V6.5 — D&D-spell-mimic Power Bundle templates + conversion ref ───
from system_data.power_bundle_templates import POWER_BUNDLE_TEMPLATES
from system_data.spell_conversion_library import SPELL_CONVERSIONS


@router.get("/reference/power-bundle-templates")
async def list_power_bundle_templates(
    max_level: int = 9, user: dict = Depends(get_current_user)
):
    """Return the seeded D&D-spell-mimic Power Bundle templates up to
    `max_level` (0 = cantrips, 9 = 9th-level spells)."""
    return {
        "templates": [
            t for t in POWER_BUNDLE_TEMPLATES
            if int(t.get("source_spell_level") or 0) <= max_level
        ],
        "total": len(POWER_BUNDLE_TEMPLATES),
    }


@router.get("/reference/spell-conversions")
async def list_spell_conversions(
    max_level: int = 9,
    school: str = "",
    user: dict = Depends(get_current_user),
):
    """Read-only reference library: D&D spells & class abilities
    translated to BESM Attributes with enhancement/limiter values.

    Visible to players to understand how rule X in their SRD book
    gets represented on a BESM / Anime 5E sheet. Each entry cites
    its SRD source (page-equivalent) and offers the BESM conversion
    with the same CP math the validator would use.
    """
    school_lc = school.strip().lower()
    rows = [
        r for r in SPELL_CONVERSIONS
        if int(r.get("source_level") or 0) <= max_level
           and (not school_lc or (r.get("school") or "").lower() == school_lc)
    ]
    schools = sorted({r.get("school") for r in SPELL_CONVERSIONS if r.get("school")})
    return {
        "entries": rows,
        "total": len(SPELL_CONVERSIONS),
        "returned": len(rows),
        "schools": schools,
    }



