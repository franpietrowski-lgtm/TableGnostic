"""V6.17 — Advancement Checker + Spell/Cooldown Tracker.

Two related player-quality-of-life features unified in one router:

  * GET  /api/characters/{cid}/advancement
  * POST /api/characters/{cid}/advancement/apply
  * GET  /api/characters/{cid}/spell-tracker
  * POST /api/characters/{cid}/spell-tracker/cast
  * POST /api/characters/{cid}/spell-tracker/restore
  * POST /api/admin/seed-anime5e-reference (campaign_id) — bulk-seed
        SRD-safe Anime 5E reference items into a campaign's library.

All endpoints honour standard table-member permissions.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso
from core.security import get_current_user
from system_data.anime5e_reference_seed import SEED_ENTRIES as ANIME5E_SEED
from routes.character_validation import anime5e_xp_to_cp


router = APIRouter(prefix="/api", tags=["advancement", "spell-tracker"])


# ─── Helpers ────────────────────────────────────────────────────────────

async def _load_character_with_permission(cid: str, user: dict):
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    allowed = (
        user["id"] == ch.get("owner_id")
        or user["id"] == camp["gm_id"]
        or user["id"] in (camp.get("member_ids") or [])
        or user.get("role") == "admin"
    )
    if not allowed:
        raise HTTPException(403, "Not a table member.")
    is_owner_or_gm = (
        user["id"] == ch.get("owner_id")
        or user["id"] == camp["gm_id"]
        or user.get("role") == "admin"
    )
    return ch, camp, is_owner_or_gm


# ─── ASI levels by class for D&D 5E (PHB standard pattern) ──────────────
DND_ASI_LEVELS = {4, 8, 12, 16, 19}  # All classes
DND_FIGHTER_BONUS = {6, 14}  # Fighter-only bonus ASI
DND_ROGUE_BONUS = {10}        # Rogue-only bonus ASI

# Cypher tier benefits — at each tier-up the PC chooses 4 benefits from
# the SRD pool (stat increase, edge, effort, skill, ability, cypher cap).
# We surface these as a flat checklist for the wizard.
CYPHER_TIER_BENEFITS = [
    {"key": "stat_increase",
     "label": "+4 to stat pools (distributed)",
     "blurb": "Add 4 points distributed across Might / Speed / Intellect."},
    {"key": "edge",
     "label": "+1 Edge",
     "blurb": "Increase one Edge (Might / Speed / Intellect) by 1."},
    {"key": "effort",
     "label": "+1 Effort",
     "blurb": "Increase your maximum Effort by 1."},
    {"key": "skill",
     "label": "+1 Skill (train or specialise)",
     "blurb": "Train in a new skill, or specialise in one you're trained in."},
    {"key": "ability",
     "label": "+1 Type/Focus ability",
     "blurb": "Pick a new ability from your Type or Focus list."},
    {"key": "cypher_limit",
     "label": "+1 Cypher carry limit",
     "blurb": "Carry one extra cypher at a time."},
]


# ─── Advancement detection ──────────────────────────────────────────────

def _detect_advancement(ch: Dict[str, Any], camp: Dict[str, Any]) -> Dict[str, Any]:
    """Return a list of pending choices the character owes.

    System-aware:
      * D&D 5E: ASI/feat at levels 4/8/12/16/19 (+ Fighter/Rogue bonus).
                Class features whose `level <= cur_level` but `chosen` is
                False (e.g. Fighting Style at 1).
      * Anime 5E: D&D 5E rules + BESM-style point-buy underspend warning.
      * Cypher: 4 unallocated tier benefits per tier-up.
      * BESM 4E: unspent XP > 5 → suggest spending.

    Returns: {pending: [...], system_id, level, summary}
    """
    folio = ch.get("folio") or {}
    dnd_state = folio.get("dnd_state") or {}
    cypher_state = folio.get("cypher_state") or {}
    anime_state = folio.get("anime5e_state") or {}
    sys_id = camp.get("system_id") or "besm-4e"

    pending: List[Dict[str, Any]] = []

    # ── D&D 5E / Anime 5E chassis advancement ──
    if sys_id in ("dnd-5e", "anime-5e") and dnd_state:
        cls = dnd_state.get("class") or ""
        lvl = int(dnd_state.get("level") or 1)
        applied = (dnd_state.get("advancement_log") or [])
        applied_lvls = {int(a.get("level") or 0) for a in applied}

        # ASI / feat windows at 4/8/12/16/19, +6/14 Fighter, +10 Rogue
        asi_levels = set(DND_ASI_LEVELS)
        if cls == "Fighter":
            asi_levels |= DND_FIGHTER_BONUS
        if cls == "Rogue":
            asi_levels |= DND_ROGUE_BONUS
        for asi_lvl in sorted(asi_levels):
            if lvl >= asi_lvl and asi_lvl not in applied_lvls:
                pending.append({
                    "id": f"asi-{asi_lvl}",
                    "kind": "asi_or_feat",
                    "system_id": sys_id,
                    "level": asi_lvl,
                    "title": f"ASI / Feat choice (Level {asi_lvl})",
                    "blurb": (
                        "Increase one ability score by 2, or two scores by 1, "
                        "OR pick a feat from the campaign's allowed list."
                    ),
                    "options": [
                        {"key": "asi_2",   "label": "+2 to one ability score"},
                        {"key": "asi_1_1", "label": "+1 to two ability scores"},
                        {"key": "feat",    "label": "Pick a feat (campaign-allowed)"},
                    ],
                })

        # Fighting Style — Fighter / Paladin / Ranger at level 1 (or 2 for Ranger)
        if cls in ("Fighter", "Paladin", "Ranger") and lvl >= 1:
            if not dnd_state.get("fighting_style"):
                pending.append({
                    "id": "fighting-style",
                    "kind": "fighting_style",
                    "system_id": sys_id,
                    "level": 1,
                    "title": "Fighting Style",
                    "blurb": "Pick one fighting style at level 1 (or 2 for Ranger).",
                    "options": [
                        {"key": "Archery",            "label": "Archery — +2 to ranged weapon attacks"},
                        {"key": "Defense",            "label": "Defense — +1 AC while wearing armor"},
                        {"key": "Dueling",            "label": "Dueling — +2 damage with a one-handed melee weapon"},
                        {"key": "Great Weapon Fighting", "label": "Great Weapon Fighting — re-roll 1s and 2s on damage"},
                        {"key": "Protection",         "label": "Protection — impose disadvantage on attacks vs allies"},
                        {"key": "Two-Weapon Fighting","label": "Two-Weapon Fighting — add ability mod to off-hand damage"},
                    ],
                })

        # Subclass — most classes pick at level 3 (Cleric/Sorcerer/Warlock at 1).
        subclass_level = {"Cleric": 1, "Sorcerer": 1, "Warlock": 1}.get(cls, 3)
        if lvl >= subclass_level and not dnd_state.get("subclass"):
            pending.append({
                "id": f"subclass-{subclass_level}",
                "kind": "subclass",
                "system_id": sys_id,
                "level": subclass_level,
                "title": f"{cls} Subclass",
                "blurb": (
                    f"{cls}s choose their archetype/path/circle/etc. at "
                    f"level {subclass_level}. Open the campaign's allowed-list "
                    f"in the primer for available picks."
                ),
                "options": [],  # GM-curated, free-text
            })

    # ── Anime 5E specific: BESM-style point-buy underspend ──
    if sys_id == "anime-5e" and anime_state:
        budget = int(anime_state.get("point_budget") or 0)
        buys = anime_state.get("point_buys") or []
        spent = sum(
            int(b.get("cost_per_level") or 0) * int(b.get("level") or 1)
            for b in buys
        )
        unspent = budget - spent
        if unspent >= 2:
            pending.append({
                "id": "anime5e-pointbuy-unspent",
                "kind": "anime5e_point_buy",
                "system_id": sys_id,
                "level": int((dnd_state or {}).get("level") or 1),
                "title": f"BESM Point-Buy: {unspent} pts unspent",
                "blurb": (
                    "Anime 5E BESM-style point-buy supplement has unspent "
                    "points. Add a genre-flair Attribute (Combat Mastery, "
                    "Heightened Sense, Tough, etc.) on the sheet."
                ),
                "options": [],  # Player adds via supplement card
                "extra": {"unspent": unspent, "budget": budget, "spent": spent},
            })

    # ── Cypher tier-up benefits ──
    if sys_id == "cypher" and cypher_state:
        tier = int(cypher_state.get("tier") or 1)
        benefits_log = cypher_state.get("tier_benefits_log") or {}
        # Each tier above 1 owes 4 benefit picks.
        for t in range(2, tier + 1):
            chosen = benefits_log.get(str(t)) or []
            owed = 4 - len(chosen)
            if owed > 0:
                pending.append({
                    "id": f"cypher-tier-{t}",
                    "kind": "cypher_tier_benefits",
                    "system_id": sys_id,
                    "level": t,
                    "title": f"Tier {t}: {owed} benefit{'s' if owed != 1 else ''} pending",
                    "blurb": (
                        f"At tier-up, choose 4 benefits from the SRD pool. "
                        f"You have {len(chosen)}/4 picked for Tier {t}."
                    ),
                    "options": CYPHER_TIER_BENEFITS,
                    "extra": {"tier": t, "chosen": chosen, "owed": owed},
                })

    # ── BESM 4E: unspent XP advisory ──
    if sys_id == "besm-4e":
        xp_unspent = float(ch.get("xp_unspent") or 0)
        if xp_unspent >= 5:
            pending.append({
                "id": "besm-xp-unspent",
                "kind": "besm_xp",
                "system_id": sys_id,
                "level": 0,
                "title": f"{xp_unspent:.1f} XP unspent",
                "blurb": (
                    "BESM 4E: 1 XP ≈ 1 CP. Submit an XP-spend proposal "
                    "(Attribute level-up, new Skill Group, etc.) for GM "
                    "approval via the XP Approval Queue."
                ),
                "options": [],
                "extra": {"xp_unspent": xp_unspent},
            })

    return {
        "character_id": ch.get("id"),
        "system_id": sys_id,
        "level": int((dnd_state or {}).get("level")
                      or (cypher_state or {}).get("tier") or 1),
        "pending": pending,
        "pending_count": len(pending),
    }


@router.get("/characters/{cid}/advancement")
async def get_advancement(cid: str, user: dict = Depends(get_current_user)):
    """Return the per-system pending advancement choices for this character."""
    ch, camp, _ = await _load_character_with_permission(cid, user)
    return _detect_advancement(ch, camp)


class AdvancementApplyIn(BaseModel):
    advancement_id: str = Field(min_length=1)
    choice_key: str = Field(default="", max_length=120)
    detail: Dict[str, Any] = Field(default_factory=dict)
    note: str = ""


@router.post("/characters/{cid}/advancement/apply")
async def apply_advancement(cid: str, body: AdvancementApplyIn,
                              user: dict = Depends(get_current_user)):
    """Apply a guided advancement choice and persist it on the character.

    Supported `advancement_id` patterns:
      * asi-{lvl}        → stamps {level: lvl, choice: ..., detail: ...} into folio.dnd_state.advancement_log
      * fighting-style   → sets folio.dnd_state.fighting_style
      * subclass-{lvl}   → sets folio.dnd_state.subclass
      * cypher-tier-{t}  → appends choice_key to folio.cypher_state.tier_benefits_log[t]
    """
    ch, camp, is_owner_or_gm = await _load_character_with_permission(cid, user)
    if not is_owner_or_gm:
        raise HTTPException(403, "Owner or GM only.")
    folio = dict(ch.get("folio") or {})
    aid = body.advancement_id
    applied: Dict[str, Any] = {"id": aid, "key": body.choice_key,
                                "detail": body.detail, "note": body.note,
                                "applied_at": now_iso(),
                                "applied_by": user.get("name")}

    if aid.startswith("asi-"):
        lvl = int(aid.split("-", 1)[1])
        dnd = dict(folio.get("dnd_state") or {})
        log = list(dnd.get("advancement_log") or [])
        # Persist the chosen ASI / feat into the log.
        log.append({**applied, "level": lvl})
        # If the player picked +2 / +1+1 / feat, push the actual ASI deltas
        # into ability_scores so the sheet reflects them.
        scores = dict(dnd.get("ability_scores") or {})
        if body.choice_key == "asi_2":
            ab = body.detail.get("ability") or "Strength"
            scores[ab] = int(scores.get(ab, 10)) + 2
        elif body.choice_key == "asi_1_1":
            for ab in body.detail.get("abilities", [])[:2]:
                scores[ab] = int(scores.get(ab, 10)) + 1
        dnd["advancement_log"] = log
        dnd["ability_scores"] = scores
        folio["dnd_state"] = dnd
    elif aid == "fighting-style":
        dnd = dict(folio.get("dnd_state") or {})
        dnd["fighting_style"] = body.choice_key or body.detail.get("style") or ""
        folio["dnd_state"] = dnd
    elif aid.startswith("subclass-"):
        dnd = dict(folio.get("dnd_state") or {})
        dnd["subclass"] = body.choice_key or body.detail.get("subclass") or ""
        folio["dnd_state"] = dnd
    elif aid.startswith("cypher-tier-"):
        t = int(aid.rsplit("-", 1)[1])
        cy = dict(folio.get("cypher_state") or {})
        log = dict(cy.get("tier_benefits_log") or {})
        chosen = list(log.get(str(t)) or [])
        chosen.append({"key": body.choice_key, "detail": body.detail,
                        "note": body.note, "applied_at": now_iso()})
        log[str(t)] = chosen
        cy["tier_benefits_log"] = log
        folio["cypher_state"] = cy
    else:
        raise HTTPException(400, f"Unknown advancement id: {aid}")

    await db.characters.update_one(
        {"id": cid},
        {"$set": {"folio": folio, "updated_at": now_iso()}},
    )
    fresh = await db.characters.find_one({"id": cid}, {"_id": 0})
    return {"ok": True, "applied": applied,
             "advancement": _detect_advancement(fresh, camp)}


# ─── Spell / Cooldown tracker ───────────────────────────────────────────

def _build_spell_tracker_state(ch: Dict[str, Any]) -> Dict[str, Any]:
    """Return the live spell-tracker state for the character.

    Combines:
      - D&D / Anime 5E spell slots from the SRD class table (driven by
        DndSheetView's class table, mirrored here).
      - Power Bundle charges (BESM / Anime 5E hybrid).
      - Cypher pool spends are tracked separately (no slot system).
    """
    folio = ch.get("folio") or {}
    dnd = folio.get("dnd_state") or {}
    cls = dnd.get("class") or ""
    lvl = max(1, int(dnd.get("level") or 1))

    FULL = {"Bard","Cleric","Druid","Sorcerer","Wizard","Adept"}
    HALF = {"Paladin","Ranger","Pilot","Tinker"}
    is_full = cls in FULL
    is_half = cls in HALF
    is_warlock = cls == "Warlock"

    FULL_TBL = [[2,0,0,0,0,0,0,0,0],[3,0,0,0,0,0,0,0,0],[4,2,0,0,0,0,0,0,0],
                 [4,3,0,0,0,0,0,0,0],[4,3,2,0,0,0,0,0,0],[4,3,3,0,0,0,0,0,0],
                 [4,3,3,1,0,0,0,0,0],[4,3,3,2,0,0,0,0,0],[4,3,3,3,1,0,0,0,0],
                 [4,3,3,3,2,0,0,0,0],[4,3,3,3,2,1,0,0,0],[4,3,3,3,2,1,0,0,0],
                 [4,3,3,3,2,1,1,0,0],[4,3,3,3,2,1,1,0,0],[4,3,3,3,2,1,1,1,0],
                 [4,3,3,3,2,1,1,1,0],[4,3,3,3,2,1,1,1,1],[4,3,3,3,3,1,1,1,1],
                 [4,3,3,3,3,2,1,1,1],[4,3,3,3,3,2,2,1,1]]
    HALF_TBL = [[0,0,0,0,0,0,0,0,0],[2,0,0,0,0,0,0,0,0],[3,0,0,0,0,0,0,0,0],
                 [3,0,0,0,0,0,0,0,0],[4,2,0,0,0,0,0,0,0],[4,2,0,0,0,0,0,0,0],
                 [4,3,0,0,0,0,0,0,0],[4,3,0,0,0,0,0,0,0],[4,3,2,0,0,0,0,0,0],
                 [4,3,2,0,0,0,0,0,0],[4,3,3,0,0,0,0,0,0],[4,3,3,0,0,0,0,0,0],
                 [4,3,3,1,0,0,0,0,0],[4,3,3,1,0,0,0,0,0],[4,3,3,2,0,0,0,0,0],
                 [4,3,3,2,0,0,0,0,0],[4,3,3,3,1,0,0,0,0],[4,3,3,3,1,0,0,0,0],
                 [4,3,3,3,2,0,0,0,0],[4,3,3,3,2,0,0,0,0]]
    WARLOCK_TBL = [[1,1],[2,1],[2,2],[2,2],[2,3],[2,3],[2,4],[2,4],[2,5],
                    [2,5],[3,5],[3,5],[3,5],[3,5],[3,5],[3,5],[4,5],[4,5],
                    [4,5],[4,5]]

    used = dict(dnd.get("slot_usage") or {})  # {1: 0, 2: 1, ...} keys are str/int
    slots: List[Dict[str, Any]] = []
    if is_full or is_half:
        tbl = (FULL_TBL if is_full else HALF_TBL)[lvl - 1]
        for i, max_n in enumerate(tbl):
            if max_n > 0:
                u = int(used.get(str(i + 1)) or used.get(i + 1) or 0)
                slots.append({
                    "slot_level": i + 1,
                    "max": max_n,
                    "used": u,
                    "remaining": max(0, max_n - u),
                })
    elif is_warlock:
        n_slots, slot_lvl = WARLOCK_TBL[lvl - 1]
        u = int(used.get(str(slot_lvl)) or used.get(slot_lvl) or 0)
        slots.append({
            "slot_level": slot_lvl,
            "max": n_slots,
            "used": u,
            "remaining": max(0, n_slots - u),
            "rest": "short",  # warlock recovers on short rest
        })

    # Power Bundle charges (BESM / Anime 5E hybrid)
    bundles: List[Dict[str, Any]] = []
    for b in (ch.get("power_bundles") or []):
        if int(b.get("charges_max") or 0) > 0:
            bundles.append({
                "name": b.get("name"),
                "invocation": b.get("invocation") or "per-charge",
                "charges_max": int(b.get("charges_max") or 0),
                "charges_current": int(b.get("charges_current") or 0),
                "energy_cost": int(b.get("energy_cost") or 0),
                "cooldown": b.get("cooldown") or "",
                "source_spell": b.get("source_spell_name") or "",
            })

    return {
        "character_id": ch.get("id"),
        "class": cls,
        "level": lvl,
        "spell_slots": slots,
        "warlock_short_rest": is_warlock,
        "power_bundles": bundles,
        "ep_max": int(folio.get("anime5e_state", {}).get("ep_max") or 0),
        "ep_current": int(folio.get("anime5e_state", {}).get("ep_current") or 0),
    }


@router.get("/characters/{cid}/spell-tracker")
async def get_spell_tracker(cid: str, user: dict = Depends(get_current_user)):
    ch, _, _ = await _load_character_with_permission(cid, user)
    return _build_spell_tracker_state(ch)


class SpellCastIn(BaseModel):
    """Spend a slot or charge.

    `kind` ∈ {"slot", "bundle", "ep"}
    For slot: `slot_level` 1-9.
    For bundle: `bundle_name`.
    For ep: `amount`.
    """
    kind: str = Field(default="slot")  # slot | bundle | ep
    slot_level: Optional[int] = None
    bundle_name: Optional[str] = None
    amount: int = 1
    note: str = ""


@router.post("/characters/{cid}/spell-tracker/cast")
async def cast_spell(cid: str, body: SpellCastIn,
                      user: dict = Depends(get_current_user)):
    ch, _, is_owner_or_gm = await _load_character_with_permission(cid, user)
    if not is_owner_or_gm:
        raise HTTPException(403, "Owner or GM only.")
    folio = dict(ch.get("folio") or {})
    if body.kind == "slot":
        if not body.slot_level:
            raise HTTPException(400, "slot_level required for kind=slot")
        dnd = dict(folio.get("dnd_state") or {})
        used = dict(dnd.get("slot_usage") or {})
        key = str(body.slot_level)
        used[key] = int(used.get(key) or 0) + 1
        dnd["slot_usage"] = used
        folio["dnd_state"] = dnd
        await db.characters.update_one({"id": cid}, {"$set": {"folio": folio, "updated_at": now_iso()}})
    elif body.kind == "bundle":
        if not body.bundle_name:
            raise HTTPException(400, "bundle_name required for kind=bundle")
        bundles = list(ch.get("power_bundles") or [])
        for b in bundles:
            if b.get("name") == body.bundle_name:
                cur = int(b.get("charges_current") or 0)
                if cur <= 0:
                    raise HTTPException(400, f"No charges remaining on {body.bundle_name}.")
                b["charges_current"] = cur - 1
                break
        else:
            raise HTTPException(404, f"Bundle {body.bundle_name!r} not found.")
        await db.characters.update_one({"id": cid}, {"$set": {"power_bundles": bundles, "updated_at": now_iso()}})
    elif body.kind == "ep":
        anime = dict(folio.get("anime5e_state") or {})
        cur = int(anime.get("ep_current") or 0)
        anime["ep_current"] = max(0, cur - max(0, int(body.amount or 0)))
        folio["anime5e_state"] = anime
        await db.characters.update_one({"id": cid}, {"$set": {"folio": folio, "updated_at": now_iso()}})
    else:
        raise HTTPException(400, f"Unknown cast kind: {body.kind}")

    fresh = await db.characters.find_one({"id": cid}, {"_id": 0})
    return _build_spell_tracker_state(fresh)


class SpellRestoreIn(BaseModel):
    rest_type: str = "long"  # long | short


@router.post("/characters/{cid}/spell-tracker/restore")
async def restore_spells(cid: str, body: SpellRestoreIn,
                          user: dict = Depends(get_current_user)):
    """Restore slots / charges per rest type.

      * long  — restore all slots (full + half + warlock), all bundle
                charges (per-charge / per-day / per-scene), reset EP.
      * short — restore warlock pact slots + bundles tagged 'per-scene'
                or with cooldown: 'short rest'.
    """
    ch, _, is_owner_or_gm = await _load_character_with_permission(cid, user)
    if not is_owner_or_gm:
        raise HTTPException(403, "Owner or GM only.")
    folio = dict(ch.get("folio") or {})
    dnd = dict(folio.get("dnd_state") or {})
    bundles = list(ch.get("power_bundles") or [])

    if body.rest_type == "long":
        # Reset all slot usage, all bundle charges, EP.
        dnd["slot_usage"] = {}
        folio["dnd_state"] = dnd
        for b in bundles:
            if int(b.get("charges_max") or 0) > 0:
                b["charges_current"] = int(b.get("charges_max") or 0)
        anime = dict(folio.get("anime5e_state") or {})
        if "ep_max" in anime:
            anime["ep_current"] = int(anime.get("ep_max") or 0)
        folio["anime5e_state"] = anime
    else:
        # Short rest: Warlock-only slot reset + per-scene bundles.
        if dnd.get("class") == "Warlock":
            dnd["slot_usage"] = {}
            folio["dnd_state"] = dnd
        for b in bundles:
            inv = (b.get("invocation") or "").lower()
            cd = (b.get("cooldown") or "").lower()
            if inv == "per-scene" or "short" in cd:
                if int(b.get("charges_max") or 0) > 0:
                    b["charges_current"] = int(b.get("charges_max") or 0)

    await db.characters.update_one(
        {"id": cid},
        {"$set": {"folio": folio, "power_bundles": bundles, "updated_at": now_iso()}},
    )
    fresh = await db.characters.find_one({"id": cid}, {"_id": 0})
    return _build_spell_tracker_state(fresh)


# ─── Anime 5E reference seed import ─────────────────────────────────────

# Map a (description / page_ref / kind) seed entry → reference_editor schema.
_PAGE_INT_RE = re.compile(r"p\.?\s*(\d+)", re.IGNORECASE)


def _normalize_seed_to_reference(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Translate the SRD-safe seed shape to the reference_editor schema."""
    # Accept plural 'weapons'/'items' from the seed file but coerce to singular.
    kind = entry.get("kind", "custom")
    kind = {"weapons": "weapon", "items": "item"}.get(kind, kind)
    page_int = None
    pr = entry.get("page_ref") or ""
    m = _PAGE_INT_RE.search(pr)
    if m:
        try:
            page_int = int(m.group(1))
        except Exception:
            page_int = None
    summary_text = entry.get("description") or ""
    if len(summary_text) > 500:
        summary_text = summary_text[:497].rstrip() + "…"
    return {
        "kind": kind,
        "name": entry.get("name") or "Unnamed",
        "summary": summary_text,
        "page": page_int,
        "book": "anime-5e",
        "cost": entry.get("cost"),
        "fields": dict(entry.get("fields") or {}),
        "tags": list(entry.get("tags") or []),
        "page_ref_text": pr,
    }


@router.post("/admin/seed-anime5e-reference")
async def seed_anime5e_reference(
    campaign_id: str,
    overwrite: bool = False,
    user: dict = Depends(get_current_user),
):
    """Bulk-seed the SRD-safe Anime 5E reference library into a campaign.

    GM/admin only. Idempotent — by default skips entries whose (kind,
    name) already exist in the campaign's reference library. Pass
    `overwrite=true` to replace existing entries.

    Returns counts: {inserted, skipped, total_in_seed}.
    """
    camp = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp.get("gm_id") != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    if camp.get("system_id") != "anime-5e":
        raise HTTPException(400, "Anime 5E reference seed is for anime-5e campaigns only.")

    inserted = 0
    skipped = 0
    overwritten = 0

    for raw in ANIME5E_SEED:
        norm = _normalize_seed_to_reference(raw)
        existing = await db.campaign_reference.find_one(
            {"campaign_id": campaign_id, "kind": norm["kind"], "name": norm["name"]},
            {"_id": 0},
        )
        doc = {
            "id": existing.get("id") if existing else new_id(),
            "campaign_id": campaign_id,
            "kind": norm["kind"],
            "name": norm["name"],
            "summary": norm["summary"],
            "page": norm["page"],
            "book": norm["book"],
            "cost": norm.get("cost"),
            "fields": {**(norm.get("fields") or {}),
                        "page_ref_text": norm.get("page_ref_text"),
                        "tags": norm.get("tags") or [],
                        "seeded_from": "anime5e_reference_seed_v1"},
            "page_validation": {"valid": True, "book": "anime-5e"},
            "created_at": existing.get("created_at") if existing else now_iso(),
            "created_by": (existing.get("created_by") if existing else user["name"]),
        }
        if existing:
            if overwrite:
                doc["updated_at"] = now_iso()
                doc["updated_by"] = user["name"]
                await db.campaign_reference.update_one(
                    {"id": existing["id"]}, {"$set": doc},
                )
                overwritten += 1
            else:
                skipped += 1
        else:
            await db.campaign_reference.insert_one(doc)
            inserted += 1

    return {
        "campaign_id": campaign_id,
        "system_id": camp.get("system_id"),
        "inserted": inserted,
        "skipped_existing": skipped,
        "overwritten": overwritten,
        "total_in_seed": len(ANIME5E_SEED),
    }


# ─── Anime 5E XP→CP formula honoring (defaults the point_budget) ────────

@router.post("/characters/{cid}/anime5e-recompute-budget")
async def anime5e_recompute_budget(cid: str, user: dict = Depends(get_current_user)):
    """Recompute and persist `folio.anime5e_state.point_budget` using the
    campaign's `anime5e_xp_formula` and the chassis level.

    Owner / GM / admin only. Useful after a level-up or formula change."""
    ch, camp, is_owner_or_gm = await _load_character_with_permission(cid, user)
    if not is_owner_or_gm:
        raise HTTPException(403, "Owner or GM only.")
    if camp.get("system_id") != "anime-5e":
        raise HTTPException(400, "Anime 5E only.")
    folio = dict(ch.get("folio") or {})
    dnd = folio.get("dnd_state") or {}
    lvl = int(dnd.get("level") or camp.get("primer_level_min") or 1)
    formula = (camp.get("anime5e_xp_formula") or "flat").lower()
    new_budget = anime5e_xp_to_cp(lvl, formula)
    anime = dict(folio.get("anime5e_state") or {})
    old = int(anime.get("point_budget") or 0)
    anime["point_budget"] = new_budget
    folio["anime5e_state"] = anime
    await db.characters.update_one(
        {"id": cid}, {"$set": {"folio": folio, "updated_at": now_iso()}})
    return {
        "ok": True, "character_id": cid,
        "level": lvl, "formula": formula,
        "previous_point_budget": old,
        "new_point_budget": new_budget,
    }
