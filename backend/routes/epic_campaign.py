"""Epic Campaign — Sclanders' "Epic Campaigns" framework as an Atelier sub-plane.

Companion to the existing 7-phase Genesis (Sclanders' first book). This module
implements the follow-up book's structure so a GM can use either tool, both in
tandem, or one-or-the-other — purely a writer's brainstorming kit.

Storage: one document per campaign in `db.epic_campaigns`, keyed by
`campaign_id`. GM-only — players can't read or write; the API returns 403.

Surfaces (in chapter order from the book):

  Part 1 — Fundamentals
    Plan summary, Constraints (system, longevity, table)
  Part 2 — Preparation
    OGAS framework (Occupation/Attitude/Goal/Stake) for the Nemesis + a
    `villains[]` list of Henchmen / Rival NPCs · what the Nemesis WANTS
    (Power/Status/Wealth/Revenge/Justification/Love) · Theme (not Tone) ·
    The Sentence (Someone wants something in a timeframe by a method) ·
    Nemesis psychology (BFT / Never-Present / Mentor) · Expanding Goal Table
  Part 3 — Plan
    Milestones each carrying obstacles / resources-have / resources-needed
    + a POE design (Problem-Obstacle-Event) · Adventures with mode +
    type tags · Villain Weakness · Seeding (names/places/objects/
    people/dreams/portents) · Beginning Adventure templates ·
    Climax (Coolness Factors + Chaos&Calm + Contingency + Consequences)

The "Sync to Codex" action below pushes the Nemesis + each villain + each
Seed as gm_only Knowledge-Web nodes so the GM doesn't have to retype them.
Linkage to existing characters/nodes is by id (no duplication on re-sync).
"""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["epic-campaign"])


# ───────────────────── Pydantic models (mirrors the book chapters) ─────────────────────

class OGASNpcIn(BaseModel):
    """OGAS framework — Sclanders ch.3.
    Occupation = what they DO.  Attitude = how they BEHAVE.
    Goal = what they WANT.       Stake = what they LOSE if they fail.
    """
    id: Optional[str] = None
    name: str = ""
    role: Literal["nemesis", "villain", "henchman", "ally", "neutral"] = "villain"
    occupation: str = ""
    attitude: str = ""
    goal: str = ""
    stake: str = ""
    # ch.4 — what they want at the deepest level
    desire: Literal["power", "status", "wealth", "revenge", "justification", "love", "other"] = "other"
    # ch.8 — three nemesis psychologies
    psychology: Literal["bft", "never-present", "mentor", "other"] = "other"
    # ch.11 — Villain weakness pattern
    weakness: str = ""
    weakness_kind: Literal["desired", "ignorant", "respected", "hated", "none"] = "none"
    notes: str = ""
    linked_node_id: Optional[str] = None  # if synced into the Codex


class SentenceIn(BaseModel):
    """Sclanders ch.7 — 'Someone wants something, in a timeframe, by a method.'"""
    someone: str = ""           # 7.1
    wants: str = ""             # 7.2 — the McGuffin
    timeframe: str = ""         # 7.3
    method: Literal["manipulation", "minions", "objects", "mixed", ""] = ""
    method_detail: str = ""     # 7.4 free-text
    refined: str = ""           # 7.5 — final assembled sentence


class MilestoneIn(BaseModel):
    """Sclanders ch.9 — Goal → Milestones → Obstacles → Resources → Tasks."""
    id: Optional[str] = None
    title: str = ""
    sequence: int = 1
    obstacles: List[str] = Field(default_factory=list)
    resources_have: List[str] = Field(default_factory=list)
    resources_needed: List[str] = Field(default_factory=list)
    # POE design (Problem · Obstacle · Event) per ch.9.2
    poe_problem: str = ""
    poe_obstacle: str = ""
    poe_event: str = ""
    completed: bool = False


class AdventureIn(BaseModel):
    """Sclanders ch.10 — adventure mode + type."""
    id: Optional[str] = None
    title: str = ""
    mode: Literal["advancing-campaign", "advancing-pcs", "enhancing-game"] = "advancing-campaign"
    type: Literal[
        "nemesis-on-track", "nemesis-revenge", "ah-ha",
        "backstory", "pc-goal", "emergent",
        "chaos", "pacing"
    ] = "nemesis-on-track"
    summary: str = ""
    events: List[str] = Field(default_factory=list)  # 5-step method — events that drive the plot
    linked_milestone_id: Optional[str] = None
    linked_pc_ids: List[str] = Field(default_factory=list)  # for backstory / pc-goal modes


class SeedIn(BaseModel):
    """Sclanders ch.12 — make-it-seem-planned via early seeded callbacks."""
    id: Optional[str] = None
    kind: Literal["name", "place", "object", "person", "dream", "portent", "omen"] = "name"
    label: str = ""
    payoff: str = ""
    seeded_in: str = ""   # session number / scene reference
    paid_off: bool = False
    linked_node_id: Optional[str] = None


class BeginningIn(BaseModel):
    """Sclanders ch.13 — 9 POE adventure-design templates for Session 0/1."""
    kind: Literal[
        "gigantic-battle", "common-backstory", "awkward-inn", "common-problem",
        "pre-game-game", "prologue-cutaway", "flash-forward", "order-hire", "personal-attack", ""
    ] = ""
    notes: str = ""


class CoolnessIn(BaseModel):
    """Sclanders ch.14.1 — Coolness Factor checklist for the climax."""
    location: str = ""
    abilities: str = ""
    npcs: str = ""
    situation: str = ""
    pressure: str = ""


class EpicCampaignIn(BaseModel):
    """Top-level Epic Campaign Plan — fully optional, save as you brainstorm."""
    # Part 1 — Fundamentals
    plan_summary: str = ""
    constraints_system: str = ""
    constraints_longevity: str = ""
    constraints_table: str = ""

    # Part 2 — Preparation
    theme: str = ""
    theme_evolution: str = ""
    sentence: SentenceIn = SentenceIn()
    nemesis: OGASNpcIn = OGASNpcIn(role="nemesis")
    villains: List[OGASNpcIn] = Field(default_factory=list)
    expanding_goal: List[str] = Field(default_factory=list)

    # Part 3 — Plan
    milestones: List[MilestoneIn] = Field(default_factory=list)
    adventures: List[AdventureIn] = Field(default_factory=list)
    seeds: List[SeedIn] = Field(default_factory=list)

    # Beginning + Ending
    beginning: BeginningIn = BeginningIn()
    ending_coolness: CoolnessIn = CoolnessIn()
    ending_chaos_calm: str = ""
    ending_contingency: str = ""
    ending_consequences: str = ""
    ending_climax: str = ""

    # Tie-ins
    linked_node_ids: List[str] = Field(default_factory=list)
    linked_character_ids: List[str] = Field(default_factory=list)
    linked_reference_ids: List[str] = Field(default_factory=list)


# ───────────────────── Helpers ─────────────────────

async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp


def _is_gm(user: dict, camp: dict) -> bool:
    return camp["gm_id"] == user["id"] or user.get("role") == "admin"


def _empty_state(cid: str) -> dict:
    state = EpicCampaignIn().model_dump()
    state["campaign_id"] = cid
    state["updated_at"] = now_iso()
    return state


def _stamp_ids(state: Dict[str, Any]) -> None:
    """Ensure every list-item has a stable id so the frontend can address rows."""
    if state.get("nemesis"):
        state["nemesis"]["id"] = state["nemesis"].get("id") or new_id()
    for v in state.get("villains", []) or []:
        v["id"] = v.get("id") or new_id()
    for m in state.get("milestones", []) or []:
        m["id"] = m.get("id") or new_id()
    for a in state.get("adventures", []) or []:
        a["id"] = a.get("id") or new_id()
    for s in state.get("seeds", []) or []:
        s["id"] = s.get("id") or new_id()


# ───────────────────── Routes ─────────────────────

@router.get("/epic/{cid}")
async def get_epic(cid: str, user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may view the Epic Campaign Plan.")
    doc = await db.epic_campaigns.find_one({"campaign_id": cid}, {"_id": 0})
    if not doc:
        doc = _empty_state(cid)
        await db.epic_campaigns.insert_one(dict(doc))
    return sanitize(doc)


@router.put("/epic/{cid}")
async def replace_epic(cid: str, body: EpicCampaignIn,
                       user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may edit the Epic Campaign Plan.")
    doc = body.model_dump()
    doc["campaign_id"] = cid
    doc["updated_at"] = now_iso()
    _stamp_ids(doc)
    await db.epic_campaigns.replace_one({"campaign_id": cid}, doc, upsert=True)
    # Mongo would inject _id into doc — sanitize before return.
    return sanitize(doc)


@router.post("/epic/{cid}/seed-codex")
async def seed_to_codex(cid: str, user: dict = Depends(get_current_user)):
    """Idempotent — push the Nemesis + each Villain + each Seed into the
    World Codex as `gm_only` knowledge nodes. Re-running won't duplicate;
    each entity's `linked_node_id` field is the dedup key.
    Returns the count of new nodes created.
    """
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "GM only.")
    doc = await db.epic_campaigns.find_one({"campaign_id": cid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "No Epic Campaign yet — save once before syncing.")

    created = 0
    updated_doc = dict(doc)

    async def upsert_node(entity: dict, node_type: str, content_lines: list[str], title: str):
        nonlocal created
        if not title.strip():
            return
        existing_id = entity.get("linked_node_id")
        if existing_id:
            existing = await db.nodes.find_one({"id": existing_id, "campaign_id": cid}, {"_id": 0})
            if existing:
                # Refresh content but keep visibility & metadata.
                await db.nodes.update_one(
                    {"id": existing_id},
                    {"$set": {
                        "title": title,
                        "content": "\n\n".join([line for line in content_lines if line]),
                        "updated_at": now_iso(),
                    }}
                )
                return
        new_node = {
            "id": new_id(),
            "campaign_id": cid,
            "title": title,
            "type": node_type,
            "content": "\n\n".join([line for line in content_lines if line]),
            "tags": ["epic-campaign", node_type],
            "visibility": "gm_only",
            "revealed_to": [],
            "fields": {"source": "epic_campaign"},
            "author_id": user["id"],
            "author_name": user.get("name") or user.get("email"),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        await db.nodes.insert_one(dict(new_node))
        entity["linked_node_id"] = new_node["id"]
        created += 1

    # Nemesis
    nem = updated_doc.get("nemesis") or {}
    if nem.get("name"):
        await upsert_node(
            nem, "npc",
            [
                f"Role: Nemesis · Psychology: {nem.get('psychology', 'other')}",
                f"Occupation: {nem.get('occupation', '')}" if nem.get('occupation') else "",
                f"Attitude: {nem.get('attitude', '')}" if nem.get('attitude') else "",
                f"Goal: {nem.get('goal', '')}" if nem.get('goal') else "",
                f"Stake: {nem.get('stake', '')}" if nem.get('stake') else "",
                f"Driving Desire: {nem.get('desire', 'other')}",
                f"Weakness ({nem.get('weakness_kind', 'none')}): {nem.get('weakness', '')}" if nem.get('weakness') else "",
                nem.get("notes", ""),
            ],
            nem["name"],
        )

    # Villains / Henchmen
    for v in updated_doc.get("villains", []) or []:
        if not v.get("name"):
            continue
        await upsert_node(
            v, "npc",
            [
                f"Role: {v.get('role', 'villain')} · OGAS",
                f"Occupation: {v.get('occupation', '')}" if v.get('occupation') else "",
                f"Attitude: {v.get('attitude', '')}" if v.get('attitude') else "",
                f"Goal: {v.get('goal', '')}" if v.get('goal') else "",
                f"Stake: {v.get('stake', '')}" if v.get('stake') else "",
                f"Weakness ({v.get('weakness_kind', 'none')}): {v.get('weakness', '')}" if v.get('weakness') else "",
                v.get("notes", ""),
            ],
            v["name"],
        )

    # Seeds — placed as `lore` nodes so they show in the codex but stay GM-only
    for s in updated_doc.get("seeds", []) or []:
        if not s.get("label"):
            continue
        await upsert_node(
            s, "lore",
            [
                f"Seed kind: {s.get('kind', 'name')}",
                f"Seeded in: {s.get('seeded_in', '')}" if s.get('seeded_in') else "",
                f"Pay-off: {s.get('payoff', '')}" if s.get('payoff') else "",
                "Status: PAID OFF" if s.get("paid_off") else "Status: still seeded",
            ],
            s["label"],
        )

    updated_doc["updated_at"] = now_iso()
    _stamp_ids(updated_doc)
    await db.epic_campaigns.replace_one({"campaign_id": cid}, updated_doc, upsert=True)

    return {
        "ok": True,
        "campaign_id": cid,
        "nodes_created": created,
        "epic": sanitize(updated_doc),
    }
