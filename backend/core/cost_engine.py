"""BESM 4E cost engine — single source of truth.

attribute_cost(a)       → net cost of an Attribute entry (clamp ≥1/Level + nested defects)
calc_derived(ch, camp)  → ATK / DEF / HP / EP / DM (campaign DR-baseline aware)
calc_spent_points(ch)   → stat / attribute / skill / defect totals
_resolve_system_id(d)   → validate + sync system_id ↔ system label on campaigns
"""
from typing import Dict, Optional

from fastapi import HTTPException

from besm_data import GAME_SYSTEMS_BY_ID, DEFAULT_SYSTEM_ID


def attribute_cost(a) -> float:
    """Compute the BESM 4E net cost of an Attribute entry.

    BESM 4E (Mark MacKinnon, Dyskami primer): Enhancements and Limiters do NOT
    change point cost — they change the *effective Level* at which the
    Attribute functions:
        cost          = assigned_level × cost_per_level
        effective_lvl = assigned_level + #Limiters − #Enhancements    (see effective_level())

    This is the opposite of the prior convention. Limiters narrow what the
    Attribute can do but make it more powerful per assigned point (effective
    level rises). Enhancements broaden what it can do but make each assigned
    point less powerful (effective level falls).

    Item / Weapon-class Attributes may carry nested Defects whose refunds
    reduce the parent's net cost; result floored at 0.
    """
    if hasattr(a, "model_dump"):
        a = a.model_dump()
    level = max(1, int(a.get("level", 1)))
    base_per_level = float(a.get("cost_per_level", 0))
    subtotal = base_per_level * level
    nested = 0
    for d in a.get("defects", []) or []:
        if hasattr(d, "model_dump"):
            d = d.model_dump()
        nested += int(d.get("points_per_rank", 0)) * int(d.get("rank", 0))
    return max(0.0, subtotal - nested)


def effective_level(a) -> int:
    """Effective functioning Level for an Attribute entry.

    BESM 4E: assigned Level + 1 per Limiter − 1 per Enhancement, floored at 1
    (an Attribute cannot function below its base — if Enhancements exceed
    Limiters + assigned Level, the GM rules whether it functions at all).
    """
    if hasattr(a, "model_dump"):
        a = a.model_dump()
    level = max(1, int(a.get("level", 1)))
    enh = len(a.get("enhancements", []) or [])
    lim = len(a.get("limiters", []) or [])
    return max(1, level + lim - enh)


def calc_derived(ch: dict, campaign: Optional[dict] = None) -> dict:
    s = ch.get("stats", {})
    body, mind, soul = s.get("body", 0), s.get("mind", 0), s.get("soul", 0)
    # Use *effective* Level (BESM 4E) so Limiters/Enhancements feed derived
    # outputs like HP, EP, ATK, etc. Maps name → effective level (≥1).
    eff = {a["name"]: effective_level(a) for a in ch.get("attributes", []) if a.get("name")}
    lv = lambda n: eff.get(n, 0)  # noqa: E731

    dm_base = 5
    if campaign and isinstance(campaign.get("damage_rating_baseline"), int) and campaign["damage_rating_baseline"] > 0:
        dm_base = campaign["damage_rating_baseline"]

    cv = (body + mind + soul) // 3
    return {
        "combat_value": cv,
        "attack_value": cv + lv("Attack Mastery"),
        "defence_value": cv - 2 + lv("Defence Mastery"),
        "health_points": (body + soul) * 5 + lv("Tough") * 5,
        "energy_points": (mind + soul) * 5 + lv("Energised") * 5,
        "damage_multiplier": dm_base + lv("Massive Damage") * 5,
        "damage_rating_baseline": dm_base,
    }


def calc_spent_points(ch: dict) -> Dict[str, float]:
    s = ch.get("stats", {})
    stat_cost = s.get("body", 0) + s.get("mind", 0) + s.get("soul", 0)
    attr_cost = sum(attribute_cost(a) for a in ch.get("attributes", []))
    skill_cost = sum(int(sk.get("cost_per_level", 0)) * int(sk.get("level", 0))
                     for sk in ch.get("skills", []))
    defect_points = sum(int(d.get("points_per_rank", 0)) * int(d.get("rank", 0))
                        for d in ch.get("defects", []))
    # Defect refunds are SUBTRACTED from total (returned to player).
    return {
        "stat_cost": stat_cost,
        "attribute_cost": attr_cost,
        "skill_cost": skill_cost,
        "defect_points": defect_points,
        "total_spent": stat_cost + attr_cost + skill_cost - defect_points,
    }


def resolve_system_id(data: dict) -> tuple:
    """Validate `data['system_id']` and sync `data['system']` with the canonical name."""
    sid = data.get("system_id") or DEFAULT_SYSTEM_ID
    if sid not in GAME_SYSTEMS_BY_ID:
        raise HTTPException(400, f"Unknown game system '{sid}'.")
    meta = GAME_SYSTEMS_BY_ID[sid]
    data["system_id"] = sid
    data["system"] = meta["name"]
    return sid, meta["name"]
