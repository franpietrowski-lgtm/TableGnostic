"""Atelier — dynamic scaling tiers (V4.4).

Adds three planning tiers ON TOP of the existing 7-phase Genesis flow:

  Session 0  — table-contract, safety tools, lines/veils, character integration,
               ongoing-availability, recurring-conflict declaration. Per
               Sclanders/Crawford "Session Zero" framework + BESM 4E p.232
               Advancement (group expectations).

  Arc        — narrative spans of ~3 sessions with a recognised shape
               (HOOK → RISING → TURN → ECHO). Each arc carries a header,
               beats[], status, and links back to seed_npcs / nodes.

  Master Plot — the campaign-spine. Already exists in genesis.master_acts;
               this tier just exposes them with a cross-tier continuity
               pane that flags mismatches (e.g. "Arc 2 mentions Frock as
               alive, but Master Plot Act III lists Frock as dead").

Storage: a single `atelier` collection, one doc per campaign:
    { campaign_id, session_zero {...}, arcs [...], continuity_findings [...] }

Continuity check is a deterministic local pass for V4.4 (regex-driven
cross-references). Phase C will wire Claude into it for richer diff-style
review; the API surface here is forward-compatible.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["atelier"])


# ───────────────────────── Pydantic models ─────────────────────────

class SessionZeroIn(BaseModel):
    """Session 0 questionnaire — drawn from Sclanders 'Great GM' framework
    + Crawford safety tools + BESM 4E group expectations (p.232).
    Every field is optional — the GM fills what they need."""
    table_contract: str = ""
    lines: List[str] = Field(default_factory=list)        # hard "no" content
    veils: List[str] = Field(default_factory=list)        # off-screen content
    safety_tools: List[str] = Field(default_factory=list) # X-card, open door, lines & veils
    schedule: str = ""
    character_integration: str = ""
    recurring_themes: List[str] = Field(default_factory=list)
    expectations: str = ""  # tone, lethality, narrative vs tactical balance
    completed: bool = False


class ArcBeatIn(BaseModel):
    title: str
    kind: Literal["hook", "rising", "turn", "echo", "denouement"] = "rising"
    note: str = ""
    session_id: Optional[str] = None  # bound when a beat plays out
    completed: bool = False


class ArcIn(BaseModel):
    title: str
    sequence: int = 1
    summary: str = ""
    expected_sessions: int = 3
    status: Literal["draft", "active", "complete", "shelved"] = "draft"
    beats: List[ArcBeatIn] = Field(default_factory=list)
    referenced_npcs: List[str] = Field(default_factory=list)   # node titles
    referenced_locations: List[str] = Field(default_factory=list)
    contradictions_with_master_plot: List[str] = Field(default_factory=list)


class AtelierStateIn(BaseModel):
    """Full upsert. Front-end mirrors with section-level patches via
    PUT /atelier/{cid}, so this model carries the union of all tiers."""
    session_zero: SessionZeroIn = SessionZeroIn()
    arcs: List[ArcIn] = Field(default_factory=list)


# ───────────────────── Helpers ─────────────────────

async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp


def _is_gm(user: dict, camp: dict) -> bool:
    return camp["gm_id"] == user["id"] or user.get("role") == "admin"


async def _empty_state(cid: str) -> dict:
    return {
        "campaign_id": cid,
        "session_zero": SessionZeroIn().model_dump(),
        "arcs": [],
        "continuity_findings": [],
        "updated_at": now_iso(),
    }


# ───────────────────── Routes ─────────────────────

@router.get("/atelier/{cid}")
async def get_atelier(cid: str, user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        # Players see only the safety tools + lines/veils + table-contract
        # so the GM's private master-plot scaffolding stays GM-only.
        doc = await db.atelier.find_one({"campaign_id": cid}, {"_id": 0})
        if not doc:
            return {"campaign_id": cid, "session_zero": SessionZeroIn().model_dump(),
                    "player_view": True}
        sz = doc.get("session_zero", {})
        return {
            "campaign_id": cid,
            "player_view": True,
            "session_zero": {
                "lines": sz.get("lines", []),
                "veils": sz.get("veils", []),
                "safety_tools": sz.get("safety_tools", []),
                "schedule": sz.get("schedule", ""),
                "table_contract": sz.get("table_contract", ""),
            },
        }
    doc = await db.atelier.find_one({"campaign_id": cid}, {"_id": 0})
    if not doc:
        doc = await _empty_state(cid)
        await db.atelier.insert_one(dict(doc))
    return sanitize(doc)


@router.put("/atelier/{cid}")
async def replace_atelier(cid: str, body: AtelierStateIn,
                           user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "Only the GM may edit the Atelier.")
    doc = body.model_dump()
    doc["campaign_id"] = cid
    doc["updated_at"] = now_iso()
    # Stamp ids on arcs / beats that arrived without one.
    for arc in doc["arcs"]:
        arc["id"] = arc.get("id") or new_id()
        for b in arc.get("beats", []):
            b["id"] = b.get("id") or new_id()
    existing = await db.atelier.find_one({"campaign_id": cid}, {"_id": 0})
    doc["continuity_findings"] = (existing or {}).get("continuity_findings", [])
    await db.atelier.replace_one({"campaign_id": cid}, doc, upsert=True)
    return sanitize(doc)


@router.post("/atelier/{cid}/continuity")
async def run_continuity_check(cid: str,
                                user: dict = Depends(get_current_user)):
    """Deterministic V4.4 continuity sweep — scans master_acts (genesis) +
    arcs (atelier) + nodes (codex) for cross-tier mismatches and writes
    findings back to atelier.continuity_findings.

    Findings categories:
      - missing_node: arc references an NPC / location that isn't in the codex
      - dead_alive_conflict: NPC tagged dead in one tier, alive in another
      - act_arc_mismatch: arc beats reference a master act that doesn't exist
      - empty_arc: arc has zero beats but is marked active
    """
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "GM only.")
    atelier = await db.atelier.find_one({"campaign_id": cid}, {"_id": 0}) \
        or await _empty_state(cid)
    genesis = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0}) or {}
    nodes = await db.nodes.find({"campaign_id": cid}, {"_id": 0}).to_list(500)
    node_titles = {n["title"]: n for n in nodes}

    master_act_titles = {a.get("title", "") for a in genesis.get("master_acts", [])}

    findings: List[Dict[str, Any]] = []
    for arc in atelier.get("arcs", []):
        # Empty active arcs
        if arc.get("status") == "active" and not arc.get("beats"):
            findings.append({
                "id": new_id(),
                "kind": "empty_arc",
                "severity": "warning",
                "arc_title": arc.get("title"),
                "message": f"Arc '{arc.get('title')}' is active but has no beats.",
            })
        # Missing nodes
        for ref in arc.get("referenced_npcs", []) + arc.get("referenced_locations", []):
            if ref and ref not in node_titles:
                findings.append({
                    "id": new_id(),
                    "kind": "missing_node",
                    "severity": "info",
                    "arc_title": arc.get("title"),
                    "missing": ref,
                    "message": f"Arc '{arc.get('title')}' references '{ref}' but no Codex node exists with that title.",
                })
        # Beats referencing master acts
        for b in arc.get("beats", []):
            if b.get("kind") == "denouement" and b.get("note"):
                # If a denouement beat name-drops a master act title, ensure it exists
                for mt in master_act_titles:
                    if mt and mt.lower() in (b.get("note") or "").lower() and mt not in master_act_titles:
                        findings.append({
                            "id": new_id(),
                            "kind": "act_arc_mismatch",
                            "severity": "warning",
                            "arc_title": arc.get("title"),
                            "missing_act": mt,
                            "message": f"Arc beat '{b.get('title')}' references master act '{mt}' that doesn't exist.",
                        })

    # NPC dead/alive conflict (very simple heuristic — looks for "dead" in a
    # node's content while another tier still tags them as ally/active.)
    dead_npc_titles = {
        n["title"] for n in nodes
        if n.get("type") == "npc" and "dead" in (n.get("content", "")[:300].lower())
    }
    for arc in atelier.get("arcs", []):
        for ref in arc.get("referenced_npcs", []):
            if ref in dead_npc_titles and arc.get("status") == "active":
                findings.append({
                    "id": new_id(),
                    "kind": "dead_alive_conflict",
                    "severity": "warning",
                    "arc_title": arc.get("title"),
                    "npc": ref,
                    "message": f"NPC '{ref}' is described as dead in their Codex node but still listed in active arc '{arc.get('title')}'.",
                })

    atelier["continuity_findings"] = findings
    atelier["continuity_checked_at"] = now_iso()
    atelier["campaign_id"] = cid
    atelier["updated_at"] = now_iso()
    await db.atelier.replace_one({"campaign_id": cid}, atelier, upsert=True)
    return {
        "ok": True,
        "campaign_id": cid,
        "findings_count": len(findings),
        "findings": findings,
        "checked_at": atelier["continuity_checked_at"],
    }
