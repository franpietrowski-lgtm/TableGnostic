"""Concept Forge V2 — V6.25.34.

Player or GM types a structured character brief (BESM 4E character-quiz
inspired). Claude returns **two** mechanically-distinct build candidates
that respect the campaign's Player Primer (CP cap, max-attr-rank,
allow/prohibit lists, benchmarks). Each candidate carries:

  • Identity   — appearance, origin, role, signature traits
  • Mechanics  — race, class, stats, attributes, skills, defects,
                 power-packs (BESM bundles)
  • Inventory  — items, weapons, weapon-items (item-half-cost rule)
  • Folio      — goals, dreams, personality knots, history
  • Estimated CP

Drafts → GM review → Player commits → CharacterBuilder pre-fills fully.

Supported on BESM 4E + Anime 5E.
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
    """Multi-field structured concept brief.

    `concept_text` remains supported as a free-form catch-all. Any other
    field that's blank is simply omitted from the prompt. The Player Primer
    is fetched server-side from the campaign — clients don't supply it.
    """
    concept_text:       Optional[str] = ""
    appearance:         Optional[str] = ""
    origin:             Optional[str] = ""
    role:               Optional[str] = ""        # role at the table
    signature_traits:   Optional[str] = ""        # 2-3 standout abilities
    carried_gear:       Optional[str] = ""        # items / weapons player wants
    goals:              Optional[str] = ""
    dreams:             Optional[str] = ""
    personality_knots:  Optional[str] = ""        # flaws, vows, weaknesses
    history:            Optional[str] = ""        # background events
    system_id:          Optional[str] = None      # falls back to campaign.system_id
    power_level:        Optional[str] = None      # e.g. "Heroic"
    imported_codex_node_ids: List[str] = []       # entity import from Knowledge Web

    def has_content(self) -> bool:
        fields = [self.concept_text, self.appearance, self.origin, self.role,
                  self.signature_traits, self.carried_gear, self.goals,
                  self.dreams, self.personality_knots, self.history]
        return any(((s or "").strip()) for s in fields)


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


def _format_primer_block(camp: dict) -> str:
    """Render the campaign's player primer + caps into the prompt."""
    bits = [
        f"- Power Level: {camp.get('power_level','Heroic')}",
        f"- Genre: {camp.get('genre','—')}",
        f"- Tone: {camp.get('tone','—')}",
        f"- Time Period: {camp.get('time_period','—')}",
        f"- Default Size: {camp.get('default_character_size','Medium')}",
        f"- Damage Rating Baseline: {camp.get('damage_rating_baseline',5)}",
    ]
    cp_max = camp.get("character_point_max") or 0
    cp_min = camp.get("character_point_min") or 0
    max_attr = camp.get("max_per_attribute_rank") or 0
    if cp_max > 0:
        bits.append(f"- CP budget cap: {cp_max} CP. STAY AT OR UNDER THIS.")
    if cp_min > 0:
        bits.append(f"- CP budget floor: {cp_min} CP.")
    if max_attr > 0:
        bits.append(
            f"- Max Attribute Level (BENCHMARK): {max_attr}. "
            f"Do NOT exceed this on any attribute. "
            f"NOTE: Weapons / Items are exempt from this cap (Anime-inspired)."
        )
    if camp.get("allowed_attributes"):
        bits.append(f"- Allowed attributes (whitelist): {', '.join(camp['allowed_attributes'])}")
    if camp.get("prohibited_attributes"):
        bits.append(f"- Prohibited attributes: {', '.join(camp['prohibited_attributes'])}")
    if camp.get("allowed_defects"):
        bits.append(f"- Allowed defects (whitelist): {', '.join(camp['allowed_defects'])}")
    if camp.get("prohibited_defects"):
        bits.append(f"- Prohibited defects: {', '.join(camp['prohibited_defects'])}")
    if camp.get("allowed_skill_groups"):
        bits.append(f"- Allowed skill groups: {', '.join(camp['allowed_skill_groups'])}")
    if camp.get("prohibited_skill_groups"):
        bits.append(f"- Prohibited skill groups: {', '.join(camp['prohibited_skill_groups'])}")
    primer = (camp.get("player_primer") or "").strip()
    if primer:
        bits.append(f"\nPlayer Primer (must respect):\n{primer}\n")
    house = (camp.get("house_rules") or "").strip()
    if house:
        bits.append(f"\nHouse Rules:\n{house}\n")
    return "\n".join(bits)


def _format_brief(body: ConceptForgeIn) -> str:
    """Render the multi-field player brief into a structured prompt section."""
    fields = [
        ("Free-form concept",  body.concept_text),
        ("Role at the table",  body.role),
        ("Signature traits",   body.signature_traits),
        ("Appearance",         body.appearance),
        ("Origin",             body.origin),
        ("Carried gear / weapons", body.carried_gear),
        ("Goals",              body.goals),
        ("Dreams",             body.dreams),
        ("Personality knots / flaws / vows", body.personality_knots),
        ("History / background events", body.history),
    ]
    out = []
    for label, val in fields:
        v = (val or "").strip()
        if v:
            out.append(f"### {label}\n{v}\n")
    return "\n".join(out) or "(No structured fields supplied.)"


async def _format_codex_imports(cid: str, node_ids: List[str]) -> str:
    if not node_ids:
        return ""
    rows = await db.nodes.find(
        {"campaign_id": cid, "id": {"$in": node_ids}},
        {"_id": 0, "title": 1, "node_kind": 1, "type": 1, "summary": 1, "fields": 1}
    ).to_list(50)
    if not rows:
        return ""
    bits = ["", "### Imported Codex entities (use as canon for this character)"]
    for r in rows:
        kind = r.get("node_kind") or r.get("type") or "node"
        title = r.get("title") or "Untitled"
        summ = (r.get("summary") or "").strip()
        bits.append(f"- {kind}: {title}{' — ' + summ if summ else ''}")
    return "\n".join(bits)


def _build_system_prompt(system_id: str) -> str:
    nuance = (
        "\n\nIMPORTANT NUANCE — please observe carefully:\n"
        "- Resistance can be: (a) STAT-DERIVED (a high Body or Mind grants natural toughness), "
        "(b) AN ATTRIBUTE (Tough / Special Defence / Resilience — bought directly with CP), "
        "or (c) ARMOR-BASED (worn item / Item attribute with Armour limiter). "
        "Pick the framing that best fits the concept and explicitly say which.\n"
        "- Range is either: (a) a CHARACTER-LEVEL Attribute "
        "(Range Enhancement on a base attribute, applies to all the character's "
        "ranged effects), or (b) WEAPON-INHERENT (the Weapon attribute / Item carries its own range). "
        "Disambiguate which.\n"
        "- POWER PACKS bundle several effects under one narrative theme "
        "(e.g. \"Phoenix Magic\" might bundle Healing 2 + Massive Damage 1 + Flight 1 + a defect). "
        "Use power_packs[] when the concept is a *signature suite* of effects, not a single ability.\n"
        "- WEAPON-ITEMS — a Weapon attribute that is also an Item gets the Item half-cost "
        "(BESM 4E p.135). Tag such entries `kind: 'weapon-item'` so the builder applies it.\n"
        "- WEAPONS are EXEMPT from benchmark caps. They can run 1-30 ranks freely. "
        "It's on the GM to balance.\n"
        "- DUPLICATE attributes should be COLLAPSED (one row, higher level). The downstream "
        "validator will warn if not.\n"
    )
    if system_id == "besm-4e":
        return (
            "You are a BESM 4E character-design assistant. Output STRICT JSON."
            + nuance +
            "\n\nSchema (return EXACTLY this shape — no markdown fences, no prose):\n"
            "{\n"
            "  \"candidates\": [\n"
            "    {\n"
            "      \"title\":   \"<short build name>\",\n"
            "      \"summary\": \"<2-3 sentence high-level pitch>\",\n"
            "      \"appearance\": \"<1-2 sentence physical description>\",\n"
            "      \"origin\":     \"<short origin / homeland / heritage>\",\n"
            "      \"goals\":   [\"<short goal>\"],\n"
            "      \"dreams\":  [\"<short dream>\"],\n"
            "      \"personality_knots\": \"<1 paragraph of flaws / vows / weaknesses>\",\n"
            "      \"history\": [\"<short event>\"],\n"
            "      \"race\":   \"<canonical race or 'custom: <name>'>\",\n"
            "      \"class\":  \"<canonical archetype or 'custom: <name>'>\",\n"
            "      \"stats\":  {\"body\": <int 4-8>, \"mind\": <int 4-8>, \"soul\": <int 4-8>},\n"
            "      \"attributes\": [{\"name\": \"<canon attr>\", \"level\": <int>, \"note\": \"\", "
            "\"resistance_kind\": \"stat|attribute|armor|none\", "
            "\"range_kind\": \"character|weapon|none\"}],\n"
            "      \"skills\":     [{\"name\": \"<canon skill_group>\", \"level\": <int>, \"note\": \"\"}],\n"
            "      \"defects\":    [{\"name\": \"<canon defect>\", \"rank\": <int>, \"note\": \"\"}],\n"
            "      \"power_packs\":[{\"name\": \"<theme name>\", \"effects\": [\"Healing 2\", "
            "\"Massive Damage 1\", \"Flight 1\"], \"defect\": \"Vow 1\", \"total_cp\": <int>, \"narrative\": \"<1 sentence>\"}],\n"
            "      \"items\":      [{\"name\": \"<item>\", \"category\": \"Carry|Tool|Medical|Illumination\", \"note\": \"\"}],\n"
            "      \"weapons\":    [{\"name\": \"<weapon>\", \"class\": \"Melee|Ranged|Thrown|Firearm|Special\", "
            "\"damage_mod\": <int>, \"rank\": <int 1-30>, \"is_weapon_item\": <bool>, \"range_m\": <int|null>, \"note\": \"\"}],\n"
            "      \"estimated_cp\": <int>,\n"
            "      \"rationale\":   \"<1-2 sentence why this fits the brief and primer>\"\n"
            "    },\n"
            "    { …second mechanically-distinct candidate… }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- EXACTLY 2 candidates, mechanically distinct (e.g. one heavy-combat one utility).\n"
            "- Stats: BESM 4E uses Body / Mind / Soul (4-8 baseline; Heroic 5-7).\n"
            "- Attributes: Tough, Power Pack, Item, Companion, Heightened Senses, Combat Mastery, "
            "Special Defence, Aura of Inhuman Beauty, Massive Damage, Speed, Flight, Healing, Weapon, "
            "Heavy Armour, Insubstantial, Wealth, Alternate Form, Special Movement, Unique Attribute.\n"
            "- Defects: Vow, Marked, Conditional Ownership, Wanted, Frail, Awkward Size, Inept, "
            "Phys-Imp, Restricted Activities, Vulnerability, Awkward, Owned.\n"
            "- Skill_groups: Athletics, Stealth, Burglary, Knowledge, Languages, Crafts, Mechanics, "
            "Performing Arts, Social, Streetwise, Survival, Animal Training, Military, Medical, Investigation.\n"
            "- DO NOT duplicate an attribute name in a single character's `attributes` list — "
            "if the concept needs two flavours of the same thing, pick the higher level once.\n"
            "- estimated_cp must respect the Primer's CP budget cap if present.\n"
            "- Respect ALL primer caps + allow/prohibit lists strictly.\n"
            "- DO NOT output prose outside the JSON. DO NOT wrap in markdown fences."
        )
    # anime-5e
    return (
        "You are an Anime 5E character-design assistant. Anime 5E is D&D 5E "
        "with an OPTIONAL BESM-style point-buy supplement layer. Output STRICT JSON."
        + nuance +
        "\n\nSchema:\n"
        "{\n"
        "  \"candidates\": [\n"
        "    {\n"
        "      \"title\":   \"<short>\", \"summary\": \"<2-3 sent>\",\n"
        "      \"appearance\": \"\", \"origin\": \"\",\n"
        "      \"goals\":[], \"dreams\":[], \"personality_knots\":\"\", \"history\":[],\n"
        "      \"race\":   \"<heritage or D&D SRD race>\",\n"
        "      \"class\":  \"<Adept|Champion|Idol|Pilot|Tinker|Barbarian|Bard|Cleric|"
        "Druid|Fighter|Monk|Paladin|Ranger|Rogue|Sorcerer|Warlock|Wizard>\",\n"
        "      \"subclass\":   \"<canonical subclass>\",\n"
        "      \"background\": \"<background>\",\n"
        "      \"abilities\":  {\"STR\":<8-15>,\"DEX\":<8-15>,\"CON\":<8-15>,\"INT\":<8-15>,\"WIS\":<8-15>,\"CHA\":<8-15>},\n"
        "      \"feats\":      [\"<feat>\"],\n"
        "      \"point_buy_attributes\": [{\"name\":\"Combat Mastery\",\"level\":2,\"note\":\"\","
        "\"resistance_kind\":\"none\",\"range_kind\":\"none\"}],\n"
        "      \"defects\":    [{\"name\":\"Marked\",\"rank\":1,\"note\":\"\"}],\n"
        "      \"power_packs\":[{\"name\":\"<theme>\",\"effects\":[],\"defect\":\"\",\"total_cp\":<int>,\"narrative\":\"\"}],\n"
        "      \"items\":      [{\"name\":\"\",\"category\":\"\",\"note\":\"\"}],\n"
        "      \"weapons\":    [{\"name\":\"\",\"class\":\"\",\"damage_mod\":<int>,\"rank\":<int>,"
        "\"is_weapon_item\":<bool>,\"range_m\":<int|null>,\"note\":\"\"}],\n"
        "      \"estimated_cp\": <int>,\n"
        "      \"rationale\":   \"<short>\"\n"
        "    },\n"
        "    { …second candidate… }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- EXACTLY 2 candidates.\n"
        "- abilities use D&D 5E's six (STR/DEX/CON/INT/WIS/CHA), 27-point buy.\n"
        "- The point-buy layer is OPTIONAL — leave empty + estimated_cp=0 if skipped.\n"
        "- Respect ALL primer caps + allow/prohibit lists.\n"
        "- DO NOT duplicate attribute names within a candidate.\n"
        "- DO NOT output prose outside the JSON. DO NOT wrap in markdown fences."
    )


def _build_user_prompt(body: ConceptForgeIn, camp: dict, codex_block: str,
                        power_level: Optional[str]) -> str:
    pl = power_level or camp.get("power_level") or "Heroic"
    primer_block = _format_primer_block(camp)
    brief = _format_brief(body)
    return (
        f"## Campaign\n"
        f"\"{camp.get('name','Untitled')}\" — power level {pl}\n\n"
        f"## Primer (RESPECT STRICTLY)\n{primer_block}\n\n"
        f"## Player Brief\n{brief}\n"
        f"{codex_block}\n\n"
        f"## Output\nReturn the two candidates per the schema above. "
        f"NO markdown, NO prose outside the JSON object."
    )


def _strip_fences(text: str) -> str:
    s = (text or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    return s


# ── Routes ─────────────────────────────────────────────────────────
@router.post("/campaigns/{cid}/concept-drafts")
async def forge_concept_drafts(cid: str, body: ConceptForgeIn,
                                user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    system_id = (body.system_id or camp.get("system_id") or "besm-4e").strip()
    if system_id not in _SUPPORTED_SYSTEMS:
        raise HTTPException(
            400,
            f"Concept Forge currently supports {sorted(_SUPPORTED_SYSTEMS)} only. "
            "D&D 5E and Cypher follow in a future iteration.",
        )
    if not body.has_content():
        raise HTTPException(400, "At least one concept field is required.")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured.")

    codex_block = await _format_codex_imports(cid, body.imported_codex_node_ids)
    system_prompt = _build_system_prompt(system_id)
    user_prompt = _build_user_prompt(body, camp, codex_block, body.power_level)

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

    # Snapshot of primer state at forge-time for audit.
    primer_snapshot = {
        "power_level":              camp.get("power_level"),
        "character_point_max":      camp.get("character_point_max", 0),
        "character_point_min":      camp.get("character_point_min", 0),
        "max_per_attribute_rank":   camp.get("max_per_attribute_rank", 0),
        "genre":                    camp.get("genre", ""),
        "time_period":              camp.get("time_period", ""),
        "default_character_size":   camp.get("default_character_size", "Medium"),
        "damage_rating_baseline":   camp.get("damage_rating_baseline", 5),
    }

    doc = {
        "id":              new_id(),
        "campaign_id":     cid,
        "system_id":       system_id,
        "requester_id":    user["id"],
        "requester_name":  user.get("name", "Unknown"),
        "concept_text":    (body.concept_text or "").strip(),
        "brief":           body.dict(exclude_none=False, exclude={"system_id"}),
        "primer_snapshot": primer_snapshot,
        "imported_codex_node_ids": body.imported_codex_node_ids or [],
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
