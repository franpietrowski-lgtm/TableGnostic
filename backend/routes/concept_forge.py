"""Concept Forge — V6.25.33.

Player or GM types a free-form character concept. Claude returns **two**
mechanically-distinct build candidates appropriate to the campaign's system
(BESM 4E or Anime 5E supplement layer). Each candidate carries a race /
class suggestion, stat allocation, attributes / skills / defects with
levels, and an estimated CP total.

Workflow:
    1. Player POSTs concept → server calls Claude → 2 candidates returned.
    2. Server stores draft as `pending` in `concept_drafts` collection.
    3. GM reviews via PATCH (approve / reject + notes).
    4. On approval, Player can POST .../commit which marks `committed`
       and returns the picked candidate; the Character Builder consumes
       it via `?from_draft={id}` query.

Only BESM 4E and Anime 5E are supported at launch — D&D 5E and Cypher
will follow once their reference shape is normalised. For unsupported
systems we return a 400 with an actionable message.
"""
import json
import re
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.config import EMERGENT_LLM_KEY
from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["concept-forge"])

_SUPPORTED_SYSTEMS = {"besm-4e", "anime-5e"}


# ── Pydantic request / response models ─────────────────────────────
class ConceptForgeIn(BaseModel):
    concept_text: str = Field(..., min_length=10, max_length=4000)
    system_id: Optional[str] = None      # falls back to campaign.system_id
    power_level: Optional[str] = None    # e.g. "Heroic" / "Adventurous"


class DraftReviewIn(BaseModel):
    status: Literal["approved", "rejected"]
    gm_notes: Optional[str] = ""


class DraftCommitIn(BaseModel):
    picked_index: int = Field(..., ge=0, le=1)


# ── Helpers ────────────────────────────────────────────────────────
async def _campaign_or_404(cid: str) -> dict:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    return camp


def _is_seated(camp: dict, user: dict) -> bool:
    return (
        user.get("role") == "admin"
        or user["id"] == camp.get("gm_id")
        or user["id"] in (camp.get("member_ids") or [])
    )


def _build_system_prompt(system_id: str) -> str:
    """System message tailored per supported game system."""
    if system_id == "besm-4e":
        return (
            "You are a BESM 4E character-design assistant. Output STRICT JSON "
            "with the schema:\n\n"
            "{\n"
            "  \"candidates\": [\n"
            "    {\n"
            "      \"title\":  \"<short name for this build>\",\n"
            "      \"summary\":\"<2-3 sentence high-level pitch>\",\n"
            "      \"race\":   \"<canonical race or 'custom: <name>'>\",\n"
            "      \"class\":  \"<canonical archetype or 'custom: <name>'>\",\n"
            "      \"stats\":  {\"body\": <int>, \"mind\": <int>, \"soul\": <int>},\n"
            "      \"attributes\": [{\"name\": \"<canon BESM attribute>\", \"level\": <1-10>, \"note\": \"\"}],\n"
            "      \"skills\":     [{\"name\": \"<BESM skill_group>\", \"level\": <1-5>, \"note\": \"\"}],\n"
            "      \"defects\":    [{\"name\": \"<BESM defect>\", \"rank\": <1-3>, \"note\": \"\"}],\n"
            "      \"estimated_cp\": <int>,\n"
            "      \"rationale\":   \"<why this fits the concept, 1-2 sentences>\"\n"
            "    },\n"
            "    { …second mechanically-distinct candidate… }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Return EXACTLY 2 candidates, mechanically different from each other.\n"
            "- BESM 4E uses Body / Mind / Soul stats (4-8 baseline; Heroic 5-7).\n"
            "- Use canonical BESM attributes (Tough, Power Pack, Item, Companion, "
            "Heightened Senses, Combat Mastery, Special Defence, Aura of Inhuman "
            "Beauty, Massive Damage, Speed, Flight, Healing, Weapon, Heavy Armour, "
            "Insubstantial, Wealth, Alternate Form, Special Movement, etc.).\n"
            "- Attribute levels 1-6 typical, costs vary 1-10 CP/level.\n"
            "- Use canonical defects (Vow, Marked, Conditional Ownership, Wanted, "
            "Frail, Awkward Size, Inept, Phys-Imp, Restricted Activities, "
            "Vulnerability, Awkward, Owned).\n"
            "- Skill_groups (use one of): Athletics, Stealth, Burglary, Knowledge, "
            "Languages, Crafts, Mechanics, Performing Arts, Social, Streetwise, "
            "Survival, Animal Training, Military, Medical, Investigation.\n"
            "- estimated_cp must roughly match the sum of attribute*cost + skills "
            "- defect rebates (BESM 4E p.8). Aim for 100-150 CP for Heroic.\n"
            "- DO NOT output prose outside the JSON. DO NOT wrap in markdown "
            "fences. Just the JSON object."
        )
    # anime-5e
    return (
        "You are an Anime 5E character-design assistant. Anime 5E is D&D 5E "
        "with an OPTIONAL BESM-style point-buy supplement. Output STRICT "
        "JSON:\n\n"
        "{\n"
        "  \"candidates\": [\n"
        "    {\n"
        "      \"title\":  \"<short name>\",\n"
        "      \"summary\":\"<2-3 sentence pitch>\",\n"
        "      \"race\":   \"<heritage or D&D SRD race>\",\n"
        "      \"class\":  \"<Adept|Champion|Idol|Pilot|Tinker|Barbarian|Bard|"
        "Cleric|Druid|Fighter|Monk|Paladin|Ranger|Rogue|Sorcerer|Warlock|Wizard>\",\n"
        "      \"subclass\": \"<one of the canonical subclasses if applicable>\",\n"
        "      \"background\": \"<1 anime 5E background>\",\n"
        "      \"abilities\": {\"STR\": <8-15>, \"DEX\": <8-15>, \"CON\": <8-15>, "
        "\"INT\": <8-15>, \"WIS\": <8-15>, \"CHA\": <8-15>},\n"
        "      \"feats\":   [\"<feat name>\"],\n"
        "      \"point_buy_attributes\": [{\"name\":\"Combat Mastery\",\"level\":2,\"note\":\"\"}],\n"
        "      \"defects\": [{\"name\":\"Marked\",\"rank\":1,\"note\":\"\"}],\n"
        "      \"estimated_cp\": <int>,\n"
        "      \"rationale\":   \"<1-2 sentence why>\"\n"
        "    },\n"
        "    { …second candidate… }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Return EXACTLY 2 candidates, mechanically distinct.\n"
        "- The point-buy layer is OPTIONAL. If you skip it, leave "
        "`point_buy_attributes` and `defects` as empty arrays and "
        "estimated_cp=0.\n"
        "- abilities use D&D 5E's six (STR/DEX/CON/INT/WIS/CHA), 27-point "
        "buy budget by default.\n"
        "- DO NOT output prose outside the JSON. DO NOT wrap in markdown "
        "fences. Just the JSON object."
    )


def _build_user_prompt(concept_text: str, camp: dict, power_level: Optional[str]) -> str:
    pl = power_level or camp.get("power_level") or "Heroic"
    tone = camp.get("tone") or "balanced heroic"
    genre = camp.get("genre") or "fantasy"
    return (
        f"Campaign: \"{camp.get('name','Untitled')}\" — genre {genre}, "
        f"tone {tone}, power level {pl}.\n\n"
        f"Concept:\n{concept_text.strip()}\n\n"
        "Now produce two candidates per the schema."
    )


def _strip_fences(text: str) -> str:
    """Tolerate the LLM occasionally wrapping JSON in markdown fences."""
    s = text.strip()
    if s.startswith("```"):
        # remove leading ```json or ``` and trailing ```
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    return s


# ── Routes ─────────────────────────────────────────────────────────
@router.post("/campaigns/{cid}/concept-drafts")
async def forge_concept_drafts(cid: str, body: ConceptForgeIn,
                                user: dict = Depends(get_current_user)):
    """Generate 2 build candidates from a free-form concept.

    Player or GM may POST. Result is stored as `pending` so the GM can
    later approve/reject. Players may only see their own pending drafts;
    GM sees all.
    """
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    system_id = (body.system_id or camp.get("system_id") or "besm-4e").strip()
    if system_id not in _SUPPORTED_SYSTEMS:
        raise HTTPException(
            400,
            f"Concept Forge currently supports {sorted(_SUPPORTED_SYSTEMS)} "
            "only. D&D 5E and Cypher follow in a future iteration.",
        )
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured.")

    system_prompt = _build_system_prompt(system_id)
    user_prompt = _build_user_prompt(body.concept_text, camp, body.power_level)

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"concept-forge-{cid}-{user['id']}",
            system_message=system_prompt,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        raw = await chat_client.send_message(UserMessage(text=user_prompt))
    except Exception as e:
        print(f"[concept_forge:error] cid={cid} -> {e}")
        raise HTTPException(502, "Concept Forge generation failed — try again.")

    payload_text = _strip_fences(raw or "")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        # Salvage attempt: pull first {...} block
        m = re.search(r"\{[\s\S]*\}", payload_text)
        if not m:
            raise HTTPException(502, "Concept Forge produced unparseable output.")
        try:
            payload = json.loads(m.group(0))
        except json.JSONDecodeError:
            raise HTTPException(502, "Concept Forge produced unparseable output.")

    candidates: List[dict] = payload.get("candidates") or []
    if not isinstance(candidates, list) or len(candidates) < 1:
        raise HTTPException(502, "Concept Forge returned no candidates.")
    candidates = candidates[:2]

    doc = {
        "id":              new_id(),
        "campaign_id":     cid,
        "system_id":       system_id,
        "requester_id":    user["id"],
        "requester_name":  user.get("name", "Unknown"),
        "concept_text":    body.concept_text.strip(),
        "power_level":     body.power_level or camp.get("power_level") or "Heroic",
        "candidates":      candidates,
        "status":          "pending",
        "picked_index":    None,
        "gm_notes":        "",
        "created_at":      now_iso(),
        "updated_at":      now_iso(),
    }
    await db.concept_drafts.insert_one(dict(doc))
    doc.pop("_id", None)
    return {"draft": doc}


@router.get("/campaigns/{cid}/concept-drafts")
async def list_concept_drafts(cid: str, user: dict = Depends(get_current_user)):
    """List drafts. Players see own drafts; GM/admin see all."""
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    is_gm = user["id"] == camp.get("gm_id") or user.get("role") == "admin"
    q: dict = {"campaign_id": cid}
    if not is_gm:
        q["requester_id"] = user["id"]
    rows = await db.concept_drafts.find(q, {"_id": 0}) \
        .sort("created_at", -1).to_list(200)
    return {"campaign_id": cid, "drafts": rows, "count": len(rows), "is_gm": is_gm}


@router.patch("/campaigns/{cid}/concept-drafts/{did}")
async def review_concept_draft(cid: str, did: str, body: DraftReviewIn,
                                 user: dict = Depends(get_current_user)):
    """GM approves or rejects a draft, optionally with notes."""
    camp = await _campaign_or_404(cid)
    if user["id"] != camp.get("gm_id") and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM (or admin) can review drafts.")
    res = await db.concept_drafts.update_one(
        {"id": did, "campaign_id": cid},
        {"$set": {
            "status":     body.status,
            "gm_notes":   (body.gm_notes or "").strip(),
            "updated_at": now_iso(),
        }},
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Draft not found.")
    out = await db.concept_drafts.find_one({"id": did}, {"_id": 0})
    return {"draft": out}


@router.post("/campaigns/{cid}/concept-drafts/{did}/commit")
async def commit_concept_draft(cid: str, did: str, body: DraftCommitIn,
                                 user: dict = Depends(get_current_user)):
    """Player picks one of the 2 approved candidates and marks the draft
    committed. Returns the picked candidate so the Character Builder can
    pre-fill from it."""
    draft = await db.concept_drafts.find_one(
        {"id": did, "campaign_id": cid}, {"_id": 0},
    )
    if not draft:
        raise HTTPException(404, "Draft not found.")
    if draft["requester_id"] != user["id"] and user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "You did not request this draft.")
    if draft["status"] != "approved":
        raise HTTPException(400, "Draft must be GM-approved before commit.")
    candidates = draft.get("candidates") or []
    if body.picked_index >= len(candidates):
        raise HTTPException(400, "picked_index out of range.")
    await db.concept_drafts.update_one(
        {"id": did},
        {"$set": {
            "status":       "committed",
            "picked_index": body.picked_index,
            "updated_at":   now_iso(),
        }},
    )
    return {"draft_id": did, "picked": candidates[body.picked_index]}


@router.delete("/campaigns/{cid}/concept-drafts/{did}")
async def delete_concept_draft(cid: str, did: str,
                                 user: dict = Depends(get_current_user)):
    """Author or GM may delete a draft."""
    camp = await _campaign_or_404(cid)
    draft = await db.concept_drafts.find_one(
        {"id": did, "campaign_id": cid}, {"_id": 0},
    )
    if not draft:
        raise HTTPException(404, "Draft not found.")
    is_gm = user["id"] == camp.get("gm_id") or user.get("role") == "admin"
    if draft["requester_id"] != user["id"] and not is_gm:
        raise HTTPException(403, "Cannot delete someone else's draft.")
    await db.concept_drafts.delete_one({"id": did})
    return {"deleted": did}
