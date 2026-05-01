"""V6.16 — Cross-system Content Converter.

A Claude-assisted bridge that takes a mechanic, ability, character, or any
piece of structured content from ANY supported system and produces a
target-system equivalent.

Endpoints (all `/api`-prefixed):

  POST /api/convert/content
       Body: {
         source_system: "besm-4e" | "anime-5e" | "dnd-5e" | "cypher" | …,
         target_system: "...",            # same set
         source_kind: "attribute" | "spell" | "focus" | "feat" |
                      "feature" | "skill" | "defect" | "item" |
                      "monster" | "character" | …,
         payload: { … arbitrary source-system shape … },
         target_constraints?: { power_level: ..., level: ..., tier: ... },
       }
       → returns a structured target-system object with:
         { name, kind, target_system, summary, target_payload, citations }

  POST /api/convert/character
       Body: {
         source_character_id: "...",
         target_campaign_id: "...",       # must already exist; system inferred
         new_owner_id?: "...",            # GM may pre-assign
         keep_folio?: true,               # journal + bio carries over
       }
       → creates the character in the target campaign and returns it.
       Calls /api/convert/content under the hood for each mechanic block.

The converter is bidirectional: any → any.

Compliance: We never echo back rulebook prose verbatim. Claude is instructed
to summarise mechanic-only and to produce the canonical numeric shape for
the target system (CP cost for BESM, level + class for D&D, tier+sentence
for Cypher, etc.).
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.config import EMERGENT_LLM_KEY
from core.cost_engine import calc_derived, calc_spent_points
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["convert"])


# ──────────────────────────────────────────────────────────────────────────
# System-target shape hints — what the LLM should produce for each ruleset.
# Kept short; the LLM does the heavy lifting from training data.

TARGET_SHAPE = {
    "besm-4e": (
        "BESM 4E — Tri-Stat point-buy. Express mechanics as Attributes "
        "(name, level, cost_per_level, enhancements[], limiters[], note), "
        "Defects (name, rank, points_per_rank, category, note), Skills "
        "(name, group, level, cost_per_level, components[]). Stats are "
        "Body/Mind/Soul (1-12). Page hints from BESM 4E (1-320)."
    ),
    "anime-5e": (
        "Anime 5E — hybrid 5E + Tri-Stat. Either express mechanics in "
        "Tri-Stat shape (anime5e_state.points = CP budget like BESM) OR "
        "in 5E shape (class, level, ability_scores, features). Pick the "
        "shape that matches the source content's flavour. Stats are "
        "Body/Mind/Soul, NOT 5E ability scores."
    ),
    "dnd-5e": (
        "D&D 5E — strict CC-BY SRD 5.1 only. Express mechanics as a 5E "
        "PC: class (str), level (1-20), race (str), background (str), "
        "ability_scores (Strength/Dex/Con/Int/Wis/Cha 8-20), spells[] "
        "(name, level, school), features[] (name, source, description), "
        "equipment[] (name, type, properties[]). For non-PC content "
        "(monsters, items), use stat-block shape. NEVER reference "
        "Forgotten Realms, Mind Flayers, Beholders, or any "
        "Wizards-trademarked content."
    ),
    "cypher": (
        "Cypher System — Sentence: Descriptor + Type + Focus. Express "
        "mechanics as cypher_state {tier (1-6), descriptor (str), type "
        "(Warrior/Adept/Explorer/Speaker/...), focus (str), pools "
        "{Might/Speed/Intellect}, edge {Might/Speed/Intellect}, abilities "
        "[]}. For non-PC content: foci, cyphers (one-shot, level 1-10), "
        "artifacts (level + depletion). TN = level × 3."
    ),
}

SUPPORTED_SYSTEMS = list(TARGET_SHAPE.keys())


# ──────────────────────────────────────────────────────────────────────────
# Pydantic

class ConvertContentIn(BaseModel):
    source_system: str
    target_system: str
    source_kind: str  # "attribute" | "spell" | "focus" | "character" | …
    payload: Dict[str, Any]
    target_constraints: Optional[Dict[str, Any]] = None


class ConvertCharacterIn(BaseModel):
    source_character_id: str
    target_campaign_id: str
    new_owner_id: Optional[str] = None
    keep_folio: bool = True
    name_override: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────
# Claude prompt scaffolding

SYSTEM_PROMPT_CONTENT = """You are TableGnostic's Cross-System Content Converter.

Given a piece of mechanic content from ONE tabletop RPG system, produce a
faithful equivalent in a DIFFERENT system. Preserve narrative intent and
power level; translate the math into the target system's native shape.

Hard rules:
  1. Output MUST be valid JSON. No markdown fences. No commentary.
  2. NEVER reproduce rulebook prose verbatim. Summarise mechanic-only.
     This is a Tri-Stat Emporium / Cypher System Creator licence
     requirement.
  3. NEVER reference trademark-protected content (Forgotten Realms,
     Mind Flayer, Beholder, Cthulhu, Vampire: the Masquerade clans, etc.).
     If the source mentions any, replace with a generic descriptor.
  4. The target_payload must follow the target system's CANONICAL shape —
     no inventing fields. If a source feature has no clean target
     equivalent, document it in `caveats` and approximate as best you can.
  5. Preserve power level. If the source is "level 3 spell" the target
     should be roughly equivalent in difficulty/cost.
  6. Stats / pools / abilities use TARGET SYSTEM names always. e.g. when
     converting to D&D 5E use Strength/Dexterity/etc, NOT Body/Mind/Soul.

Top-level shape:
{
  "name": "Target-system display name",
  "kind": "attribute|spell|focus|feat|character|item|...",
  "target_system": "besm-4e|anime-5e|dnd-5e|cypher",
  "summary": "≤ 200 chars mechanic-only flavour line.",
  "target_payload": { /* canonical target-system shape */ },
  "caveats": ["short bullet on lossy conversions, optional"],
  "citations": [
    { "source_ref": "BESM 4E p.96", "target_ref": "Cypher SRD - Healing focus" }
  ]
}
"""


async def _call_claude_convert(prompt: str, session_seed: str) -> Dict[str, Any]:
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"convert-{session_seed[:32]}",
            system_message=SYSTEM_PROMPT_CONTENT,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        raw = await chat.send_message(UserMessage(text=prompt))
    except Exception as e:
        raise HTTPException(502, f"Claude call failed: {e}")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned).strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract the first {...} block.
        m = re.search(r"\{.*\}", cleaned, re.S)
        if not m:
            raise HTTPException(502, "Claude returned non-JSON output")
        return json.loads(m.group(0))


def _validate_systems(src: str, tgt: str):
    if src not in SUPPORTED_SYSTEMS:
        raise HTTPException(400, f"Unsupported source_system: {src}. Use one of {SUPPORTED_SYSTEMS}.")
    if tgt not in SUPPORTED_SYSTEMS:
        raise HTTPException(400, f"Unsupported target_system: {tgt}. Use one of {SUPPORTED_SYSTEMS}.")


def _build_content_prompt(body: ConvertContentIn) -> str:
    constraints = body.target_constraints or {}
    return (
        f"# Source system: {body.source_system}\n"
        f"# Target system: {body.target_system}\n"
        f"# Source kind: {body.source_kind}\n"
        f"# Target shape hint:\n{TARGET_SHAPE[body.target_system]}\n\n"
        f"# Source payload (JSON):\n{json.dumps(body.payload, indent=2)[:8000]}\n\n"
        f"# Target constraints:\n{json.dumps(constraints, indent=2)[:1000]}\n\n"
        f"Produce the canonical {body.target_system} equivalent now. "
        f"Output JSON only — no markdown, no commentary."
    )


# ──────────────────────────────────────────────────────────────────────────
# Endpoint — single-content convert

@router.post("/convert/content")
async def convert_content(body: ConvertContentIn,
                          user: dict = Depends(get_current_user)):
    """Translate one mechanic between any two supported systems.

    GM/admin only — players can read converted content via the
    Reference page after a GM commits it. Stamping the writer guards
    against abuse + budget tracking.
    """
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "GM/admin only — players cannot trigger conversions.")
    _validate_systems(body.source_system, body.target_system)
    if body.source_system == body.target_system:
        # Same-system "convert" is a no-op — just echo the payload through.
        return {
            "name": body.payload.get("name") or body.payload.get("title") or "Untitled",
            "kind": body.source_kind,
            "target_system": body.target_system,
            "summary": "Same source/target — no conversion needed.",
            "target_payload": body.payload,
            "caveats": [],
            "citations": [],
        }
    prompt = _build_content_prompt(body)
    out = await _call_claude_convert(prompt, f"{body.source_system}-to-{body.target_system}-{body.source_kind}")
    # Stamp + return.
    out.setdefault("target_system", body.target_system)
    out.setdefault("kind", body.source_kind)
    out.setdefault("converted_by_user_id", user["id"])
    out.setdefault("converted_at", now_iso())
    return out


# ──────────────────────────────────────────────────────────────────────────
# Endpoint — full-character convert

def _coerce_to_dict_list(items, default_keys: Optional[Dict[str, Any]] = None):
    """Defensive — Claude sometimes returns strings or non-dict entries
    where we expect Tri-Stat objects. Wrap each into a dict so the cost
    engine doesn't AttributeError. Non-Tri-Stat systems use this for
    display-only purposes."""
    out = []
    base = default_keys or {}
    for it in (items or []):
        if isinstance(it, dict):
            out.append(it)
        elif isinstance(it, str):
            out.append({**base, "name": it})
        # Drop anything else (None, int, etc.) silently.
    return out


async def _materialise_character(target_payload: Dict[str, Any],
                                 target_system: str,
                                 target_camp: Dict[str, Any],
                                 source_ch: Dict[str, Any],
                                 owner_id: str,
                                 owner_name: str,
                                 keep_folio: bool,
                                 name_override: Optional[str]) -> Dict[str, Any]:
    """Take Claude's target_payload and shape it into our `characters`
    document. The LLM produces a free-form blob; this function maps the
    obvious bits (attributes/skills/defects for BESM, folio dictionaries
    for Cypher/D&D state, etc.) into the existing schema."""
    name = name_override or target_payload.get("name") or source_ch.get("name", "Untitled")
    concept = target_payload.get("concept") or target_payload.get("summary") or source_ch.get("concept", "")
    base = {
        "id": new_id(),
        "name": name,
        "campaign_id": target_camp["id"],
        "owner_id": owner_id,
        "owner_name": owner_name,
        "created_at": now_iso(),
        "concept": concept,
        "system_id": target_system,
        "total_points": int(target_payload.get("total_points")
                            or source_ch.get("total_points") or 100),
        "stats": target_payload.get("stats") or {"body": 4, "mind": 4, "soul": 4},
        "attributes": _coerce_to_dict_list(target_payload.get("attributes")),
        "skills": _coerce_to_dict_list(target_payload.get("skills"),
                                       default_keys={"cost_per_level": 0, "level": 0}),
        "defects": _coerce_to_dict_list(target_payload.get("defects"),
                                        default_keys={"points_per_rank": 0, "rank": 0}),
        "items": _coerce_to_dict_list(target_payload.get("items")),
        "weapons": _coerce_to_dict_list(target_payload.get("weapons")),
        # Per-system state blocks (populated when Claude returns them).
        "folio": {},
    }
    # Carry the source folio (journal, bio, motivations) when keep_folio.
    if keep_folio and source_ch.get("folio"):
        base["folio"] = {**(source_ch.get("folio") or {})}
    # Per-system state — Claude produces these as siblings in target_payload.
    # Some prompts give us a wrapped sub-dict (`cypher_state: {...}`),
    # others return the canonical fields directly at the top level.
    # Tolerate both shapes by merging the wrapper (if any) with a plucked
    # set of canonical fields.
    def _extract(keys):
        plucked = {k: target_payload[k] for k in keys if k in target_payload}
        return plucked

    if target_system == "dnd-5e":
        wrapped = target_payload.get("dnd_state") or {}
        plucked = _extract(["class", "level", "race", "background",
                            "ability_scores", "skills", "spells",
                            "features", "equipment", "armor_class",
                            "hit_points", "proficiency_bonus", "alignment",
                            "saving_throws", "spell_slots"])
        base["folio"]["dnd_state"] = {**plucked, **wrapped}
    elif target_system == "cypher":
        wrapped = target_payload.get("cypher_state") or {}
        plucked = _extract(["tier", "descriptor", "type", "focus", "pools",
                            "edge", "effort", "abilities", "cyphers",
                            "artifacts", "shins", "background_connection"])
        base["folio"]["cypher_state"] = {**plucked, **wrapped}
    elif target_system == "anime-5e":
        wrapped = target_payload.get("anime5e_state") or {}
        plucked = _extract(["points", "stats", "derived", "level",
                            "ability_scores", "class"])
        base["folio"]["anime5e_state"] = {**plucked, **wrapped}
    # Stamp a converted-from breadcrumb so cloners can audit.
    base["converted_from"] = {
        "source_character_id": source_ch.get("id"),
        "source_system": source_ch.get("system_id") or "besm-4e",
        "converted_at": now_iso(),
    }
    # Tri-Stat-shape cost engine only applies to BESM/Anime 5E. For D&D /
    # Cypher we compute a simplified "spent" so the sheet header is happy.
    if target_system in ("besm-4e", "anime-5e"):
        try:
            base["derived"] = calc_derived(base, target_camp)
            base["spent"] = calc_spent_points(base)
        except Exception:
            base["derived"] = {}
            base["spent"] = {"total_spent": 0}
    else:
        base["derived"] = {}
        base["spent"] = {"total_spent": 0}
    return base


@router.post("/convert/character")
async def convert_character(body: ConvertCharacterIn,
                             user: dict = Depends(get_current_user)):
    """Take an existing character and produce a working sheet in the
    target campaign's system. The new character is saved + returned.

    Permission model: caller must be the source campaign's GM (or admin),
    AND the target campaign's GM (or admin). This prevents content
    laundering — a GM can't fork another GM's character.
    """
    src_ch = await db.characters.find_one({"id": body.source_character_id}, {"_id": 0})
    if not src_ch:
        raise HTTPException(404, "Source character not found.")
    src_camp = await db.campaigns.find_one({"id": src_ch["campaign_id"]}, {"_id": 0})
    tgt_camp = await db.campaigns.find_one({"id": body.target_campaign_id}, {"_id": 0})
    if not tgt_camp:
        raise HTTPException(404, "Target campaign not found.")
    is_admin = user.get("role") == "admin"
    if not is_admin:
        if src_camp and src_camp.get("gm_id") != user["id"]:
            raise HTTPException(403, "Only the source campaign's GM (or admin) may convert.")
        if tgt_camp.get("gm_id") != user["id"]:
            raise HTTPException(403, "Only the target campaign's GM (or admin) may receive a converted character.")
    src_system = src_ch.get("system_id") or src_camp.get("system_id") or "besm-4e"
    tgt_system = tgt_camp.get("system_id") or "besm-4e"
    _validate_systems(src_system, tgt_system)

    # Build a compact payload for Claude. We ship attributes, skills,
    # defects, total_points + stats — the things that meaningfully change
    # between systems. Folio (bio/journal) is left out of the LLM call;
    # we carry it verbatim instead.
    payload = {
        "name": src_ch.get("name"),
        "concept": src_ch.get("concept"),
        "total_points": src_ch.get("total_points"),
        "stats": src_ch.get("stats"),
        "attributes": src_ch.get("attributes") or [],
        "skills": src_ch.get("skills") or [],
        "defects": src_ch.get("defects") or [],
        "items": src_ch.get("items") or [],
        "weapons": src_ch.get("weapons") or [],
        "folio_bio": {
            "physical_description": (src_ch.get("folio") or {}).get("physical_description"),
            "personality_traits": (src_ch.get("folio") or {}).get("personality_traits"),
            "motivations": (src_ch.get("folio") or {}).get("motivations"),
            "fears_weaknesses": (src_ch.get("folio") or {}).get("fears_weaknesses"),
        },
    }
    constraints = {
        "target_power_level": tgt_camp.get("power_level"),
        "target_anime5e_xp_formula": tgt_camp.get("anime5e_xp_formula"),
        "target_house_rules": tgt_camp.get("house_rules"),
    }
    in_body = ConvertContentIn(
        source_system=src_system,
        target_system=tgt_system,
        source_kind="character",
        payload=payload,
        target_constraints=constraints,
    )
    out = await _call_claude_convert(_build_content_prompt(in_body),
                                     f"char-{src_ch['id']}-to-{tgt_system}")
    target_payload = out.get("target_payload") or out  # tolerate either shape
    # Decide owner.
    owner_id = body.new_owner_id or src_ch.get("owner_id") or user["id"]
    owner_name = user["name"]
    if body.new_owner_id:
        u = await db.users.find_one({"id": body.new_owner_id}, {"_id": 0, "name": 1, "email": 1})
        if u:
            owner_name = u.get("name") or u.get("email") or "?"
            # Auto-add the new owner as a campaign member (mirror /transfer logic).
            if (body.new_owner_id != tgt_camp["gm_id"]
                    and body.new_owner_id not in tgt_camp.get("member_ids", [])):
                await db.campaigns.update_one({"id": tgt_camp["id"]},
                                              {"$addToSet": {"member_ids": body.new_owner_id}})
    new_ch = await _materialise_character(
        target_payload, tgt_system, tgt_camp, src_ch,
        owner_id, owner_name, body.keep_folio, body.name_override,
    )
    await db.characters.insert_one(new_ch)
    return {
        "character": sanitize(new_ch),
        "caveats": out.get("caveats") or [],
        "citations": out.get("citations") or [],
    }
