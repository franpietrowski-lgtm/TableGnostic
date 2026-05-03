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


# ─── Subclass option library ────────────────────────────────────────────
# Per-class subclass lists. SRD 5.1 / Anime 5E SRD-safe — names + short
# in-house blurbs only. Used by the Advancement Wizard's toggle picker.
SUBCLASS_OPTIONS = {
    # D&D 5E SRD subclasses
    "Barbarian": [
        {"key": "Path of the Berserker", "blurb": "Frenzy state, intimidating presence, mindless rage."},
        {"key": "Path of the Totem Warrior", "blurb": "Animal totem spirits grant resistance & traits."},
    ],
    "Bard": [
        {"key": "College of Lore", "blurb": "Cutting words, magical secrets, three skill expertises."},
        {"key": "College of Valor", "blurb": "Combat-leaning bard — armor, martial weapons, extra attack."},
    ],
    "Cleric": [
        {"key": "Life Domain", "blurb": "Disciple of life — healing bonuses, heavy armor, channel divinity preserve life."},
        {"key": "Light Domain", "blurb": "Warding flare, radiant burst, corona of light."},
        {"key": "Knowledge Domain", "blurb": "Blessings of knowledge, channel divinity for read thoughts."},
        {"key": "Nature Domain", "blurb": "Druid cantrip, nature acolyte, charm animals & plants."},
        {"key": "Tempest Domain", "blurb": "Wrath of the storm, thunderous strike, destructive wrath."},
        {"key": "Trickery Domain", "blurb": "Blessing of the trickster, invoke duplicity, cloak of shadows."},
        {"key": "War Domain", "blurb": "War priest, channel divinity guided strike, war god's blessing."},
    ],
    "Druid": [
        {"key": "Circle of the Land", "blurb": "Nature-based wizardry, bonus cantrip, natural recovery."},
        {"key": "Circle of the Moon", "blurb": "Combat wild-shape, primal strike, beast forms scale to high CR."},
    ],
    "Fighter": [
        {"key": "Champion", "blurb": "Improved critical 19-20, remarkable athlete, additional fighting style."},
        {"key": "Battle Master", "blurb": "Combat superiority dice + 3 maneuvers chosen from a tactical menu."},
        {"key": "Eldritch Knight", "blurb": "Wizard spellcasting + weapon bond + war magic."},
    ],
    "Monk": [
        {"key": "Way of the Open Hand", "blurb": "Manipulate opponent stance, ki strikes that knock prone or push."},
        {"key": "Way of Shadow", "blurb": "Ninja toolkit — pass without trace, darkness, darkvision."},
        {"key": "Way of the Four Elements", "blurb": "Ki-fueled elemental strikes & disciplines."},
    ],
    "Paladin": [
        {"key": "Oath of Devotion", "blurb": "Sacred weapon, turn the unholy, classic paladin."},
        {"key": "Oath of the Ancients", "blurb": "Nature's wrath, turn the faithless, woodland defender."},
        {"key": "Oath of Vengeance", "blurb": "Abjure enemy, vow of enmity — the punisher."},
    ],
    "Ranger": [
        {"key": "Hunter", "blurb": "Hunter's prey, defensive tactics, multiattack tricks."},
        {"key": "Beast Master", "blurb": "Companion animal that fights alongside you."},
    ],
    "Rogue": [
        {"key": "Thief", "blurb": "Fast hands, second-story work, supreme sneak."},
        {"key": "Assassin", "blurb": "Bonus to surprise damage, infiltration expertise."},
        {"key": "Arcane Trickster", "blurb": "Wizard spellcasting + mage hand legerdemain."},
    ],
    "Sorcerer": [
        {"key": "Draconic Bloodline", "blurb": "Draconic resilience, elemental affinity, dragon wings."},
        {"key": "Wild Magic", "blurb": "Wild magic surge — chaos table on every spell."},
    ],
    "Warlock": [
        {"key": "The Archfey", "blurb": "Fey presence, misty escape, beguiling defenses."},
        {"key": "The Fiend", "blurb": "Dark one's blessing, hurl through hell, fiendish vigor."},
        {"key": "The Great Old One", "blurb": "Awakened mind, entropic ward, thought shield."},
    ],
    "Wizard": [
        {"key": "School of Evocation", "blurb": "Sculpt spells, potent cantrip, overchannel for max damage."},
        {"key": "School of Abjuration", "blurb": "Arcane ward, projected ward, improved abjuration."},
        {"key": "School of Conjuration", "blurb": "Minor conjuration, benign transposition, focused conjuration."},
        {"key": "School of Divination", "blurb": "Portent — replace any d20 roll twice per long rest."},
        {"key": "School of Enchantment", "blurb": "Hypnotic gaze, instinctive charm, alter memories."},
        {"key": "School of Illusion", "blurb": "Improved minor illusion, malleable illusions, illusory reality."},
        {"key": "School of Necromancy", "blurb": "Grim harvest, undead thralls, command undead."},
        {"key": "School of Transmutation", "blurb": "Minor alchemy, transmuter's stone, master transmuter."},
    ],
    # Anime 5E original classes (SRD-safe in-house blurbs).
    "Adept": [
        {"key": "Way of the Empath", "blurb": "Telepathic resonance, share emotions, mental healing."},
        {"key": "Way of the Aether", "blurb": "Aetheric strike, levitation, force-based projections."},
    ],
    "Champion": [
        {"key": "Heart of the Lion", "blurb": "Roar that rallies allies, inspire courage in adversity."},
        {"key": "Iron Crusader", "blurb": "Heavy armor mastery, bulwark stance, smite-style strikes."},
    ],
    "Idol": [
        {"key": "Stage Maven", "blurb": "Charm an audience, encore performance grants bonus actions."},
        {"key": "Idol of Hope", "blurb": "Healing songs, anthem of resilience, group fortify."},
    ],
    "Pilot": [
        {"key": "Sortie Specialist", "blurb": "Vehicle-bonded, advanced cockpit weaponry, manoeuvre repertoire."},
        {"key": "Mecha Knight", "blurb": "Bonded blade, charged strike, sortie-only feats."},
    ],
    "Tinker": [
        {"key": "Alchemist", "blurb": "Brewed elixirs, flask-based AoEs, healing potions on the fly."},
        {"key": "Artillerist", "blurb": "Eldritch cannon, magical shell rounds, explosive cantrips."},
        {"key": "Battle Smith", "blurb": "Steel defender companion, magical tinkering, infusion mastery."},
    ],
    # D&D 5E SRD Artificer subclasses (Anime 5E imports them via Tinker).
    "Artificer": [
        {"key": "Alchemist", "blurb": "Experimental elixirs, alchemical savant — bonus to spell heal/damage by INT mod."},
        {"key": "Artillerist", "blurb": "Eldritch cannon, arcane firearm — magical shell-fire support."},
        {"key": "Battle Smith", "blurb": "Steel defender — a mechanical dog companion that scales with you."},
    ],
}


def _resolve_subclass_options(class_name: str) -> List[Dict[str, str]]:
    """Resolve subclass options for a class. Strips parenthetical
    annotations like 'Artificer (Alchemist)' so the lookup matches."""
    if not class_name:
        return []
    # Try exact match first, then strip parenthetical.
    if class_name in SUBCLASS_OPTIONS:
        return SUBCLASS_OPTIONS[class_name]
    base = class_name.split("(")[0].strip()
    return SUBCLASS_OPTIONS.get(base, [])


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
            sub_opts = _resolve_subclass_options(cls)
            pending.append({
                "id": f"subclass-{subclass_level}",
                "kind": "subclass",
                "system_id": sys_id,
                "level": subclass_level,
                "title": f"{cls} Subclass",
                "blurb": (
                    f"{cls}s choose their archetype/path/circle/etc. at "
                    f"level {subclass_level}. Pick a subclass below — "
                    f"each option's flavour is shown in the toggle."
                ),
                "options": [
                    {"key": s["key"], "label": s["key"],
                     "blurb": s.get("blurb") or "",
                     "cp_cost": 0}
                    for s in sub_opts
                ],
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
    # V6.18 — pending workflow.
    # When True (default for non-GM callers), the choice is filed as a
    # Level-Up Ticket awaiting GM approval rather than committed
    # straight to the character document. GMs / admins may set False
    # to commit immediately (e.g. NPC sheets, GM-driven retcons).
    pending: bool = True
    # CP cost the player believes this choice consumes — surfaced in
    # the pending panel so the GM can sanity-check before approving.
    cp_cost: int = 0


def _commit_advancement(folio: Dict[str, Any], aid: str,
                          choice_key: str, detail: Dict[str, Any]) -> Dict[str, Any]:
    """Pure-function commit of a single advancement choice into a folio.

    Returns the modified folio dict (does not persist). Used both by the
    immediate-commit path and the GM-approval path.
    """
    folio = dict(folio or {})
    if aid.startswith("asi-"):
        lvl = int(aid.split("-", 1)[1])
        dnd = dict(folio.get("dnd_state") or {})
        log = list(dnd.get("advancement_log") or [])
        log.append({"id": aid, "level": lvl, "key": choice_key,
                     "detail": detail, "applied_at": now_iso()})
        scores = dict(dnd.get("ability_scores") or {})
        if choice_key == "asi_2":
            ab = detail.get("ability") or "Strength"
            scores[ab] = int(scores.get(ab, 10)) + 2
        elif choice_key == "asi_1_1":
            for ab in detail.get("abilities", [])[:2]:
                scores[ab] = int(scores.get(ab, 10)) + 1
        dnd["advancement_log"] = log
        dnd["ability_scores"] = scores
        folio["dnd_state"] = dnd
    elif aid == "fighting-style":
        dnd = dict(folio.get("dnd_state") or {})
        dnd["fighting_style"] = choice_key or detail.get("style") or ""
        folio["dnd_state"] = dnd
    elif aid.startswith("subclass-"):
        dnd = dict(folio.get("dnd_state") or {})
        dnd["subclass"] = choice_key or detail.get("subclass") or ""
        folio["dnd_state"] = dnd
    elif aid.startswith("cypher-tier-"):
        t = int(aid.rsplit("-", 1)[1])
        cy = dict(folio.get("cypher_state") or {})
        log = dict(cy.get("tier_benefits_log") or {})
        chosen = list(log.get(str(t)) or [])
        chosen.append({"key": choice_key, "detail": detail,
                        "applied_at": now_iso()})
        log[str(t)] = chosen
        cy["tier_benefits_log"] = log
        folio["cypher_state"] = cy
    return folio


@router.post("/characters/{cid}/advancement/apply")
async def apply_advancement(cid: str, body: AdvancementApplyIn,
                              user: dict = Depends(get_current_user)):
    """V6.18 — file an advancement choice as a Level-Up Ticket (default)
    OR commit immediately (GM/admin override via `pending=False`).

    Pending tickets queue under `character.pending_advancements[]` so both
    player and GM can see them on the sheet's Pending Approval panel.
    The GM approves via `/advancement/approve/{ticket_id}` which runs
    `_commit_advancement` against the folio and stamps the ticket
    approved.
    """
    ch, camp, is_owner_or_gm = await _load_character_with_permission(cid, user)
    if not is_owner_or_gm:
        raise HTTPException(403, "Owner or GM only.")
    is_gm = user["id"] == camp["gm_id"] or user.get("role") == "admin"

    aid = body.advancement_id

    if body.pending and not is_gm:
        # Player is filing a ticket. Persist into pending queue, do NOT
        # mutate the folio yet.
        ticket = {
            "id": new_id(),
            "advancement_id": aid,
            "choice_key": body.choice_key or "",
            "detail": body.detail or {},
            "note": body.note or "",
            "cp_cost": int(body.cp_cost or 0),
            "filed_by": user.get("name"),
            "filed_by_id": user["id"],
            "filed_at": now_iso(),
            "status": "pending",  # pending | approved | rejected
        }
        await db.characters.update_one(
            {"id": cid},
            {"$push": {"pending_advancements": ticket},
             "$set": {"updated_at": now_iso()}},
        )
        fresh = await db.characters.find_one({"id": cid}, {"_id": 0})
        return {"ok": True, "ticket": ticket, "filed": True,
                 "advancement": _detect_advancement(fresh, camp)}

    # Immediate commit path (GM/admin only or explicit pending=False).
    folio = ch.get("folio") or {}
    new_folio = _commit_advancement(folio, aid, body.choice_key or "",
                                       body.detail or {})
    await db.characters.update_one(
        {"id": cid},
        {"$set": {"folio": new_folio, "updated_at": now_iso()}},
    )
    fresh = await db.characters.find_one({"id": cid}, {"_id": 0})
    return {"ok": True, "applied": {
        "id": aid, "key": body.choice_key, "detail": body.detail,
        "applied_at": now_iso(), "applied_by": user.get("name")},
            "filed": False,
            "advancement": _detect_advancement(fresh, camp)}


# ─── V6.18 — Pending Level-Up Ticket queue ──────────────────────────────

@router.get("/characters/{cid}/advancement/pending")
async def list_pending_advancements(cid: str,
                                      user: dict = Depends(get_current_user)):
    """Return the pending Level-Up Tickets for this character. Visible to
    both player and GM (read-only for non-GMs)."""
    ch, _, _ = await _load_character_with_permission(cid, user)
    return {
        "character_id": cid,
        "tickets": list(ch.get("pending_advancements") or []),
    }


def _validate_ticket_compliance(ch: Dict[str, Any], camp: Dict[str, Any],
                                  ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Pre-flight check for a ticket before GM approves.

    Catches the most common rules-balance issues:
      - CP / DP balance after ticket would commit
      - ASI level matches the chassis level (no asi-12 if level 5)
      - Subclass valid for class
      - Cypher tier-benefit only when at appropriate tier
    """
    issues: List[str] = []
    folio = ch.get("folio") or {}
    dnd = folio.get("dnd_state") or {}
    cypher = folio.get("cypher_state") or {}
    aid = ticket.get("advancement_id") or ""
    cur_level = int(dnd.get("level") or 1)

    if aid.startswith("asi-"):
        try:
            req_lvl = int(aid.split("-", 1)[1])
            if cur_level < req_lvl:
                issues.append(
                    f"ASI ticket requires character level ≥ {req_lvl}, "
                    f"current level is {cur_level}."
                )
        except (ValueError, IndexError):
            issues.append(f"Malformed ASI advancement id: {aid}")

    if aid.startswith("subclass-"):
        if dnd.get("subclass"):
            issues.append(
                f"Character already has a subclass: {dnd.get('subclass')}. "
                f"Reject and retcon instead, or this ticket is a duplicate."
            )

    if aid.startswith("cypher-tier-"):
        try:
            req_tier = int(aid.rsplit("-", 1)[1])
            cur_tier = int(cypher.get("tier") or 1)
            if cur_tier < req_tier:
                issues.append(
                    f"Cypher tier-benefit ticket targets tier {req_tier}, "
                    f"current tier is {cur_tier}."
                )
        except (ValueError, IndexError):
            issues.append(f"Malformed cypher-tier advancement id: {aid}")

    # CP/DP budget check for Anime 5E (only system that flexes the budget on
    # advancement). BESM uses XP queue, D&D uses ASI auto-grant.
    if camp.get("system_id") == "anime-5e":
        anime = folio.get("anime5e_state") or {}
        budget = int(anime.get("point_budget") or 0)
        spent = sum(int(b.get("cost_per_level") or 0) * int(b.get("level") or 1)
                     for b in (anime.get("point_buys") or []))
        cost = int(ticket.get("cp_cost") or 0)
        if cost and spent + cost > budget:
            issues.append(
                f"Approving this ticket would put point-buy at "
                f"{spent + cost}/{budget} ({spent + cost - budget} over)."
            )

    return {
        "passes": not issues,
        "issues": issues,
        "current_level": cur_level,
        "current_tier": int(cypher.get("tier") or 1),
    }


class TicketActionIn(BaseModel):
    note: str = ""


@router.post("/characters/{cid}/advancement/approve/{ticket_id}")
async def approve_pending_advancement(
    cid: str, ticket_id: str, body: TicketActionIn,
    user: dict = Depends(get_current_user),
):
    """GM/admin approves a pending Level-Up Ticket. Runs the rules
    pre-flight; on pass commits the choice to the folio and marks the
    ticket approved. Returns the ticket + a compliance report."""
    ch, camp, _ = await _load_character_with_permission(cid, user)
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    tickets = list(ch.get("pending_advancements") or [])
    target = next((t for t in tickets if t.get("id") == ticket_id), None)
    if not target:
        raise HTTPException(404, "Ticket not found")
    if target.get("status") != "pending":
        raise HTTPException(400, f"Ticket already {target.get('status')}")

    compliance = _validate_ticket_compliance(ch, camp, target)
    if not compliance["passes"]:
        return {
            "ok": False,
            "ticket_id": ticket_id,
            "blocked_by_compliance": True,
            "compliance": compliance,
            "advice": (
                "Resolve the listed issues, or have the player edit the "
                "ticket. Use /reject if the ticket is invalid."
            ),
        }

    # Commit.
    folio = _commit_advancement(
        ch.get("folio") or {},
        target.get("advancement_id") or "",
        target.get("choice_key") or "",
        target.get("detail") or {},
    )
    target["status"] = "approved"
    target["approved_by"] = user.get("name")
    target["approved_by_id"] = user["id"]
    target["approved_at"] = now_iso()
    target["approval_note"] = body.note or ""
    target["compliance_at_approval"] = compliance
    await db.characters.update_one(
        {"id": cid},
        {"$set": {"folio": folio, "pending_advancements": tickets,
                   "updated_at": now_iso()}},
    )
    return {"ok": True, "ticket": target, "compliance": compliance}


@router.post("/characters/{cid}/advancement/reject/{ticket_id}")
async def reject_pending_advancement(
    cid: str, ticket_id: str, body: TicketActionIn,
    user: dict = Depends(get_current_user),
):
    """GM/admin rejects a pending ticket with a note. The folio is NOT
    mutated; the ticket is stamped rejected and stays in history."""
    ch, camp, _ = await _load_character_with_permission(cid, user)
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM/admin only.")
    tickets = list(ch.get("pending_advancements") or [])
    target = next((t for t in tickets if t.get("id") == ticket_id), None)
    if not target:
        raise HTTPException(404, "Ticket not found")
    if target.get("status") != "pending":
        raise HTTPException(400, f"Ticket already {target.get('status')}")
    target["status"] = "rejected"
    target["rejected_by"] = user.get("name")
    target["rejected_at"] = now_iso()
    target["rejection_note"] = body.note or ""
    await db.characters.update_one(
        {"id": cid},
        {"$set": {"pending_advancements": tickets, "updated_at": now_iso()}},
    )
    return {"ok": True, "ticket": target}


@router.post("/characters/{cid}/advancement/withdraw/{ticket_id}")
async def withdraw_pending_advancement(
    cid: str, ticket_id: str,
    user: dict = Depends(get_current_user),
):
    """Player who filed the ticket may withdraw it before GM approves."""
    ch, _, is_owner_or_gm = await _load_character_with_permission(cid, user)
    if not is_owner_or_gm:
        raise HTTPException(403, "Filer / owner / GM only.")
    tickets = list(ch.get("pending_advancements") or [])
    target = next((t for t in tickets if t.get("id") == ticket_id), None)
    if not target:
        raise HTTPException(404, "Ticket not found")
    if target.get("status") != "pending":
        raise HTTPException(400, f"Ticket already {target.get('status')}")
    if (target.get("filed_by_id") and
        target["filed_by_id"] != user["id"] and
        user["id"] != ch.get("owner_id") and
        user.get("role") != "admin"):
        raise HTTPException(403, "Only the filer, character owner, or admin may withdraw.")
    target["status"] = "withdrawn"
    target["withdrawn_at"] = now_iso()
    await db.characters.update_one(
        {"id": cid},
        {"$set": {"pending_advancements": tickets, "updated_at": now_iso()}},
    )
    return {"ok": True, "ticket": target}


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
