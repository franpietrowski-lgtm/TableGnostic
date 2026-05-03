"""Cross-system Content Conversion engine — V6.16.3 refactor.

Pure logic for translating mechanic content (characters, creatures,
spells, foci, attributes, items) between supported tabletop systems.
No FastAPI dependencies — endpoints live in `routes/conversion.py`.

Public surface:
    SUPPORTED_SYSTEMS               # ["besm-4e", "anime-5e", "dnd-5e", "cypher"]
    TARGET_SHAPE                    # per-system "what the LLM should produce"
    SYSTEM_PROMPT_CONTENT           # the Claude system message
    validate_systems(src, tgt)
    build_content_prompt(...)
    call_claude_convert(...)         # async — wraps emergentintegrations
    coerce_to_dict_list(...)
    normalise_tristat_cost_fields(...)
    materialise_character(...)       # async
    materialise_creature(...)        # async — V6.16.3 NEW

Each materialise_* function returns a fully-shaped database document
ready to insert into `db.characters` or `db.nodes` respectively.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from fastapi import HTTPException

from core.config import EMERGENT_LLM_KEY
from core.cost_engine import calc_derived, calc_spent_points
from core.db import new_id, now_iso


# ──────────────────────────────────────────────────────────────────────────
# System-target shape hints — what the LLM should produce for each ruleset.

TARGET_SHAPE = {
    "besm-4e": (
        "BESM 4E — Tri-Stat point-buy. Express mechanics as Attributes "
        "(name, level, cost_per_level, enhancements[], limiters[], note), "
        "Defects (name, rank, points_per_rank, category, note), Skills "
        "(name, group, level, cost_per_level, components[]). Stats are "
        "Body/Mind/Soul (1-12). Page hints from BESM 4E (1-320). For "
        "creatures: stat-block shape with stats, attributes (mostly "
        "Special Movement / Sensory / Item-of-Power / Elemental Control), "
        "defects, total_points (creature CP), and threat_tier."
    ),
    "anime-5e": (
        "Anime 5E — D&D 5E OGL chassis with a Tri-Stat point-buy "
        "SUPPLEMENT layer. PRIMARY shape MUST be D&D 5E: class (str), "
        "level (1-20), race (str), background (str), ability_scores "
        "(Strength/Dexterity/Constitution/Intelligence/Wisdom/Charisma "
        "8-20), hit_points, hit_dice (e.g. '5d8+10'), proficiency_bonus, "
        "armor_class, saving_throws (list of ability names), skills "
        "(list with proficient flag), features (per class/race/"
        "background, level-gated), spells (if class casts), spell_slots, "
        "equipment (with type & properties — including converted weapons), "
        "alignment. Anime-5E classes/races/backgrounds extend the SRD "
        "(Magical Girl, Mech Pilot, Sentai, Espers, Demihuman, Neko, "
        "etc.) — favour those when the source flavour fits. "
        "ADDITIONALLY, produce `point_buys` — a list of residual "
        "BESM-style attributes/defects that DON'T cleanly map to a 5E "
        "feature (e.g. Sixth Sense, Heightened Senses, Item-of-Power-"
        "style genre powers). Each entry: {name, level, cost_per_level, "
        "blurb_role, source_attribute}. These layer on top of the d20 "
        "chassis to capture genre flair the SRD can't carry. Aim for "
        "the bulk of source mechanics to land in the 5E chassis (class "
        "features, spells, ability scores) and only the genre-specific "
        "anime extras to land in `point_buys`. Stats are 5E ability "
        "scores, NOT Body/Mind/Soul. For creatures: standard 5E monster "
        "stat block + an `anime_traits` array for genre-specific flair."
    ),
    "dnd-5e": (
        "D&D 5E — strict CC-BY SRD 5.1 only. Express mechanics as a 5E "
        "PC: class (str), level (1-20), race (str), background (str), "
        "ability_scores (Strength/Dex/Con/Int/Wis/Cha 8-20), spells[] "
        "(name, level, school), features[] (name, source, description), "
        "equipment[] (name, type, properties[]). For creatures: "
        "monster stat block — size, type, alignment, AC, HP (with "
        "hit_dice), speed, ability_scores, saving_throws, skills, "
        "damage_resistances, damage_immunities, condition_immunities, "
        "senses, languages, challenge_rating (str: '1/4', '5', '11'), "
        "actions[] (name + description), legendary_actions[] (optional), "
        "lair_actions[] (optional). NEVER reference Forgotten Realms, "
        "Mind Flayers, Beholders, or any Wizards-trademarked content."
    ),
    "cypher": (
        "Cypher System — Sentence: Descriptor + Type + Focus. Express "
        "mechanics as cypher_state {tier (1-6), descriptor (str), type "
        "(Warrior/Adept/Explorer/Speaker/...), focus (str), pools "
        "{Might/Speed/Intellect}, edge {Might/Speed/Intellect}, abilities "
        "[]}. For creatures: antagonist stat block — level (1-10), "
        "target_difficulty (level × 3 by default), health, damage, armor, "
        "movement, modifications[] (which task pools the creature "
        "naturally lowers/raises difficulty for), special_abilities[], "
        "interaction (TN to talk down). For non-PC content: foci, "
        "cyphers (one-shot, level 1-10), artifacts (level + depletion). "
        "TN = level × 3."
    ),
}

SUPPORTED_SYSTEMS = list(TARGET_SHAPE.keys())


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
  "kind": "attribute|spell|focus|feat|character|creature|item|...",
  "target_system": "besm-4e|anime-5e|dnd-5e|cypher",
  "summary": "≤ 200 chars mechanic-only flavour line.",
  "target_payload": { /* canonical target-system shape */ },
  "caveats": ["short bullet on lossy conversions, optional"],
  "citations": [
    { "source_ref": "BESM 4E p.96", "target_ref": "Cypher SRD - Healing focus" }
  ]
}
"""


# ──────────────────────────────────────────────────────────────────────────
# Validation + prompt building

def validate_systems(src: str, tgt: str):
    """Raise HTTPException(400) if either system is unsupported."""
    if src not in SUPPORTED_SYSTEMS:
        raise HTTPException(400, f"Unsupported source_system: {src}. Use one of {SUPPORTED_SYSTEMS}.")
    if tgt not in SUPPORTED_SYSTEMS:
        raise HTTPException(400, f"Unsupported target_system: {tgt}. Use one of {SUPPORTED_SYSTEMS}.")


def build_content_prompt(source_system: str, target_system: str,
                         source_kind: str, payload: Dict[str, Any],
                         target_constraints: Optional[Dict[str, Any]] = None) -> str:
    constraints = target_constraints or {}
    return (
        f"# Source system: {source_system}\n"
        f"# Target system: {target_system}\n"
        f"# Source kind: {source_kind}\n"
        f"# Target shape hint:\n{TARGET_SHAPE[target_system]}\n\n"
        f"# Source payload (JSON):\n{json.dumps(payload, indent=2)[:8000]}\n\n"
        f"# Target constraints:\n{json.dumps(constraints, indent=2)[:1000]}\n\n"
        f"Produce the canonical {target_system} equivalent now. "
        f"Output JSON only — no markdown, no commentary."
    )


# ──────────────────────────────────────────────────────────────────────────
# Claude wrapper

async def call_claude_convert(prompt: str, session_seed: str) -> Dict[str, Any]:
    """Async — fires one Claude Sonnet 4.5 request via emergentintegrations
    and returns the parsed JSON response. Tolerates ```json fences and
    trailing commentary by extracting the first {...} block on JSON parse
    failure."""
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


# ──────────────────────────────────────────────────────────────────────────
# Defensive coercion

def coerce_to_dict_list(items, default_keys: Optional[Dict[str, Any]] = None):
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


def normalise_tristat_cost_fields(items, kind: str):
    """Tri-Stat-specific post-processor.

    Claude's response shape varies per call: an Attribute might come
    back with `cost: 12` (TOTAL) instead of `cost_per_level: 4` (per-tier
    rate, which the BESM cost engine multiplies by `level`). A Defect
    might return `points: 1` instead of `points_per_rank: 1`. Without
    correction the rendered "x3 = NaN PTS" tag appears on every entry.

    `kind` ∈ {"attribute", "skill", "defect"}. Mutates entries in place.
    """
    for it in (items or []):
        if not isinstance(it, dict):
            continue
        if kind in ("attribute", "skill"):
            level = int(it.get("level") or 0) or 1
            cpl = it.get("cost_per_level")
            if cpl is None:
                total = it.get("cost") or it.get("total_cost")
                if total is not None and level > 0:
                    try:
                        it["cost_per_level"] = round(float(total) / level, 2)
                    except (ValueError, TypeError):
                        it["cost_per_level"] = 0
            # Backfill `level` if Claude omitted it but gave a cost.
            if it.get("level") is None and it.get("cost") is not None:
                it["level"] = 1
        elif kind == "defect":
            rank = int(it.get("rank") or 0) or 1
            ppr = it.get("points_per_rank")
            if ppr is None:
                total = it.get("points") or it.get("refund")
                if total is not None and rank > 0:
                    try:
                        it["points_per_rank"] = round(float(total) / rank, 2)
                    except (ValueError, TypeError):
                        it["points_per_rank"] = 0
                else:
                    # Bare narrative defect — default to 1 pt/rank (BESM
                    # "Lesser" baseline). The GM can reweight in the editor.
                    it["points_per_rank"] = 1
                    if "category" not in it:
                        it["category"] = "Lesser"
            if it.get("rank") is None and it.get("points") is not None:
                it["rank"] = 1
            elif it.get("rank") is None:
                it["rank"] = 1
    return items


# ──────────────────────────────────────────────────────────────────────────
# Per-system wrapper extraction

# V6.20 — Defaults to splice into any 5E-chassis state dict that came
# back from the LLM converter without a complete shape. Prevents the
# downstream sheet from rendering all-zero ability scores or the editor
# from crashing on undefined `.includes()` calls.
_DND_STATE_DEFAULTS: Dict[str, Any] = {
    "ability_scores": {"Strength": 10, "Dexterity": 10, "Constitution": 10,
                        "Intelligence": 10, "Wisdom": 10, "Charisma": 10},
    "saving_throw_profs": [],
    "skill_profs": [],
    "inventory": [],
    "spells_known": [],
}


def _hydrate_dnd_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Splice missing baseline fields into a 5E-chassis state dict.

    - ability_scores: any of the 6 abilities ≤ 0 or missing → 10
    - saving_throw_profs / skill_profs / inventory / spells_known → []
    """
    out = dict(state or {})
    scores = dict(out.get("ability_scores") or {})
    for ab, default in _DND_STATE_DEFAULTS["ability_scores"].items():
        v = scores.get(ab)
        if not isinstance(v, (int, float)) or v <= 0:
            scores[ab] = default
    out["ability_scores"] = scores
    for k, default in _DND_STATE_DEFAULTS.items():
        if k == "ability_scores":
            continue
        if not isinstance(out.get(k), list):
            out[k] = list(default)
    return out


def _resolve_wrapper(target_payload: Dict[str, Any], target_system: str):
    """Build the canonical wrapper(s) for the target system.

    Returns (wrapper, per_system_state) where:
      - wrapper        : dict used for top-level field resolution
      - per_system_state: dict of {state_name: state_dict} written to folio

    Anime 5E is unique: it produces BOTH a 5E chassis (`dnd_state`) AND a
    BESM supplement layer (`anime5e_state.point_buys`). Other systems
    produce a single state dict.
    """
    if target_system == "anime-5e":
        dnd_keys = ["class", "level", "race", "background",
                    "ability_scores", "skills", "spells", "features",
                    "class_features", "equipment", "armor_class",
                    "hit_points", "hit_dice", "proficiency_bonus",
                    "alignment", "saving_throws", "spell_slots",
                    # Creature-shape keys (5E monster stat block).
                    "challenge_rating", "cr", "size", "creature_type",
                    "speed", "damage_resistances", "damage_immunities",
                    "condition_immunities", "senses", "languages",
                    "actions", "legendary_actions", "lair_actions",
                    "reactions", "anime_traits"]
        dnd_wrapper = {**{k: target_payload[k] for k in dnd_keys if k in target_payload},
                       **(target_payload.get("dnd_state") or {})}
        if "features" in dnd_wrapper and "class_features" not in dnd_wrapper:
            dnd_wrapper["class_features"] = dnd_wrapper["features"]
        # V6.20 — hydrate baseline so the sheet never renders 0-stat scores.
        dnd_wrapper = _hydrate_dnd_state(dnd_wrapper)
        supp_keys = ["point_buys", "point_budget", "stats", "derived",
                     "hp", "ep", "acp", "anime_traits"]
        supp_wrapper = {**{k: target_payload[k] for k in supp_keys if k in target_payload},
                        **(target_payload.get("anime5e_state") or {})}
        return dnd_wrapper, {"dnd_state": dnd_wrapper, "anime5e_state": supp_wrapper}

    if target_system == "cypher":
        keys = ["tier", "descriptor", "type", "focus", "pools",
                "edge", "effort", "abilities", "cyphers",
                "artifacts", "shins", "background_connection",
                # Creature-shape keys (Cypher antagonist).
                "level", "target_difficulty", "health", "damage",
                "armor", "movement", "modifications", "special_abilities",
                "interaction"]
        wrapper = {**{k: target_payload[k] for k in keys if k in target_payload},
                   **(target_payload.get("cypher_state") or {})}
        return wrapper, {"cypher_state": wrapper}

    if target_system == "dnd-5e":
        keys = ["class", "level", "race", "background", "ability_scores",
                "skills", "spells", "features", "class_features",
                "equipment", "armor_class", "hit_points", "hit_dice",
                "proficiency_bonus", "alignment", "saving_throws",
                "spell_slots",
                # Creature-shape keys (5E monster stat block).
                "challenge_rating", "cr", "size", "creature_type",
                "speed", "damage_resistances", "damage_immunities",
                "condition_immunities", "senses", "languages",
                "actions", "legendary_actions", "lair_actions",
                "reactions"]
        wrapper = {**{k: target_payload[k] for k in keys if k in target_payload},
                   **(target_payload.get("dnd_state") or {})}
        if "features" in wrapper and "class_features" not in wrapper:
            wrapper["class_features"] = wrapper["features"]
        # V6.20 — hydrate baseline so the sheet never renders 0-stat scores.
        wrapper = _hydrate_dnd_state(wrapper)
        return wrapper, {"dnd_state": wrapper}

    return {}, {}


def _resolve_tristat_top_level(target_payload, target_system, wrapper):
    """For BESM ports the top-level Tri-Stat fields (stats / attributes /
    skills / defects) ARE the canonical surface. For Anime 5E the 5E
    chassis is canonical so top-level Tri-Stat is suppressed. For D&D /
    Cypher the top-level fields are vestigial defaults."""
    if target_system == "anime-5e":
        return ({"body": 4, "mind": 4, "soul": 4}, [], [], [])
    stats = (wrapper.get("stats")
             or target_payload.get("stats")
             or {"body": 4, "mind": 4, "soul": 4})
    if target_system == "besm-4e":
        attrs = wrapper.get("attributes") or target_payload.get("attributes")
        skills = wrapper.get("skills") or target_payload.get("skills")
        defects = wrapper.get("defects") or target_payload.get("defects")
    else:
        attrs = target_payload.get("attributes")
        skills = target_payload.get("skills")
        defects = target_payload.get("defects")
    return (stats, attrs, skills, defects)


# ──────────────────────────────────────────────────────────────────────────
# Materialisers

async def materialise_character(target_payload: Dict[str, Any],
                                 target_system: str,
                                 target_camp: Dict[str, Any],
                                 source_ch: Dict[str, Any],
                                 owner_id: str,
                                 owner_name: str,
                                 keep_folio: bool,
                                 name_override: Optional[str]) -> Dict[str, Any]:
    """Take Claude's target_payload and shape it into our `characters`
    document. The LLM produces a free-form blob; this function maps the
    obvious bits into the existing schema."""
    name = name_override or target_payload.get("name") or source_ch.get("name", "Untitled")
    concept = (target_payload.get("concept") or target_payload.get("summary")
               or source_ch.get("concept", ""))

    wrapper, per_system_state = _resolve_wrapper(target_payload, target_system)
    tristat_stats, tristat_attrs, tristat_skills, tristat_defects = \
        _resolve_tristat_top_level(target_payload, target_system, wrapper)

    pts = target_payload.get("total_points")
    if pts is None and isinstance(wrapper.get("points"), dict):
        pts = wrapper["points"].get("total")
    if pts is None:
        pts = source_ch.get("total_points") or 100

    base = {
        "id": new_id(),
        "name": name,
        "campaign_id": target_camp["id"],
        "owner_id": owner_id,
        "owner_name": owner_name,
        "created_at": now_iso(),
        "concept": concept,
        "system_id": target_system,
        "total_points": int(pts),
        "stats": tristat_stats,
        "attributes": normalise_tristat_cost_fields(coerce_to_dict_list(tristat_attrs), "attribute"),
        "skills": normalise_tristat_cost_fields(coerce_to_dict_list(
                                       tristat_skills,
                                       default_keys={"cost_per_level": 0, "level": 0}), "skill"),
        "defects": normalise_tristat_cost_fields(coerce_to_dict_list(
                                        tristat_defects,
                                        default_keys={"points_per_rank": 0, "rank": 0}), "defect"),
        "items": coerce_to_dict_list(target_payload.get("items")
                                     or wrapper.get("equipment")),
        "weapons": coerce_to_dict_list(target_payload.get("weapons")),
        "folio": {},
    }
    if keep_folio and source_ch.get("folio"):
        base["folio"] = {**(source_ch.get("folio") or {})}
    for k, v in (per_system_state or {}).items():
        base["folio"][k] = v
    base["converted_from"] = {
        "source_character_id": source_ch.get("id"),
        "source_system": source_ch.get("system_id") or "besm-4e",
        "converted_at": now_iso(),
    }
    if target_system == "besm-4e":
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


async def materialise_creature(target_payload: Dict[str, Any],
                               target_system: str,
                               target_camp: Dict[str, Any],
                               source_node: Dict[str, Any],
                               name_override: Optional[str]) -> Dict[str, Any]:
    """V6.16.3 — produce a `nodes`-shaped document representing a creature
    in the target system. Lives under the campaign's Knowledge Web with
    `motive: "creature"` so the Director's Console + Codex Chart pick it
    up automatically.

    The wrapper resolution mirrors `materialise_character`: per-system
    state dicts (dnd_state for D&D + Anime 5E, cypher_state for Cypher)
    are persisted into `fields` so the Director's Console can read
    canonical stats off the same path it already uses for PC characters.
    """
    name = name_override or target_payload.get("name") or source_node.get("title", "Unknown Creature")
    flavour = (target_payload.get("summary") or target_payload.get("description")
               or source_node.get("summary", ""))
    wrapper, per_system_state = _resolve_wrapper(target_payload, target_system)

    fields: Dict[str, Any] = {
        "kind": "creature",
        "system_id": target_system,
        "summary": flavour,
        "converted_from_node": source_node.get("id"),
        "source_system": source_node.get("fields", {}).get("system_id") or "besm-4e",
    }
    # Per-system canonical block.
    for k, v in (per_system_state or {}).items():
        fields[k] = v
    # System-specific top-level convenience fields the Director's Console
    # reads when shopping NPCs into encounters.
    if target_system == "dnd-5e":
        fields["cr"] = str(target_payload.get("challenge_rating")
                           or target_payload.get("cr")
                           or wrapper.get("challenge_rating") or "1")
        fields["hp"] = int(target_payload.get("hit_points")
                           or wrapper.get("hit_points") or 0)
        fields["ac"] = int(target_payload.get("armor_class")
                           or wrapper.get("armor_class") or 10)
    elif target_system == "anime-5e":
        fields["cr"] = str(target_payload.get("challenge_rating")
                           or target_payload.get("cr") or "1")
        fields["anime_traits"] = (target_payload.get("anime_traits")
                                  or per_system_state.get("anime5e_state", {}).get("anime_traits") or [])
    elif target_system == "cypher":
        fields["level"] = int(target_payload.get("level")
                              or wrapper.get("level") or 3)
        fields["target_difficulty"] = int(
            target_payload.get("target_difficulty")
            or fields["level"] * 3
        )
        fields["health"] = int(target_payload.get("health")
                               or wrapper.get("health") or fields["level"] * 3)
    elif target_system == "besm-4e":
        fields["total_points"] = int(target_payload.get("total_points") or 100)
        fields["stats"] = (target_payload.get("stats")
                           or {"body": 4, "mind": 4, "soul": 4})
        fields["attributes"] = normalise_tristat_cost_fields(
            coerce_to_dict_list(target_payload.get("attributes")), "attribute")
        fields["defects"] = normalise_tristat_cost_fields(
            coerce_to_dict_list(target_payload.get("defects")), "defect")
    return {
        "id": new_id(),
        "campaign_id": target_camp["id"],
        "title": name,
        "type": "creature",
        "motive": "creature",
        "fields": fields,
        "created_at": now_iso(),
    }
