"""Cross-system Challenge Rating engine.

Each TTRPG values "balanced encounter" differently — D&D uses XP thresholds
per PC level (DMG p.82), Cypher converts difficulty rating × 3 = TN with
party effort/edge as the lowering lever, BESM 4E balances by total point
total within ±15%, and Anime 5E (the hybrid) blends both.

This module exposes one entry point — `analyse(party, npcs, system_id, env)` —
that returns a dict shaped:

    {
        "system_id": "...",
        "rating": "Easy|Medium|Hard|Deadly|Pushover|Fair|Punishing",
        "score":   0.0..1.0,    # raw difficulty index
        "reason":  "human-readable explanation",
        "party_label": "...",    # e.g. "4 PCs · party threshold 1500 XP"
        "npc_label":   "...",    # e.g. "3 NPCs · combined CR 5 · 1800 XP"
        "suggestions": [
            {"kind": "add_minion|remove_npc|env|armor|feat|reposition",
             "icon": "swords|shield|...",
             "label": "Add a Bandit minion to keep it engaging",
             "delta": +50},
            ...
        ],
    }

The suggestion engine is rule-based, not LLM. It walks a small heuristic
ladder so the GM gets actionable nudges with deterministic latency.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ────────────────────── D&D 5E DMG p.82 XP thresholds ──────────────────────
# Per-character XP threshold by encounter difficulty.
DND_XP_THRESHOLDS = [
    # (lvl, easy, medium, hard, deadly)
    (1,  25,  50,  75,  100),
    (2,  50,  100, 150, 200),
    (3,  75,  150, 225, 400),
    (4,  125, 250, 375, 500),
    (5,  250, 500, 750, 1100),
    (6,  300, 600, 900, 1400),
    (7,  350, 750, 1100, 1700),
    (8,  450, 900, 1400, 2100),
    (9,  550, 1100, 1600, 2400),
    (10, 600, 1200, 1900, 2800),
    (11, 800, 1600, 2400, 3600),
    (12, 1000, 2000, 3000, 4500),
    (13, 1100, 2200, 3400, 5100),
    (14, 1250, 2500, 3800, 5700),
    (15, 1400, 2800, 4300, 6400),
    (16, 1600, 3200, 4800, 7200),
    (17, 2000, 3900, 5900, 8800),
    (18, 2100, 4200, 6300, 9500),
    (19, 2400, 4900, 7300, 10900),
    (20, 2800, 5700, 8500, 12700),
]
# CR → XP (DMG p.275)
CR_TO_XP = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800,
    "6": 2300, "7": 2900, "8": 3900, "9": 5000, "10": 5900,
    "11": 7200, "12": 8400, "13": 10000, "14": 11500, "15": 13000,
    "16": 15000, "17": 18000, "18": 20000, "19": 22000, "20": 25000,
}
# Encounter multiplier by NPC count (DMG p.82) — solo / pair / trio / group / clump.
DND_GROUP_MULT = [
    (1, 1.0), (2, 1.5), (3, 2.0), (7, 2.5), (11, 3.0), (15, 4.0),
]


def _dnd_party_threshold(party: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sum each PC's threshold table row to get the four party thresholds."""
    out = {"easy": 0, "medium": 0, "hard": 0, "deadly": 0}
    for pc in party:
        lvl = max(1, min(20, int((pc.get("dnd_state") or {}).get("level") or pc.get("level") or 1)))
        row = DND_XP_THRESHOLDS[lvl - 1]
        out["easy"]   += row[1]
        out["medium"] += row[2]
        out["hard"]   += row[3]
        out["deadly"] += row[4]
    return out


def _dnd_npc_xp(npcs: List[Dict[str, Any]]) -> int:
    """Multiplier-adjusted XP total for the encounter."""
    raw = 0
    for n in npcs:
        cr = str(n.get("cr") or "1")
        raw += CR_TO_XP.get(cr, 200) * int(n.get("count", 1) or 1)
    count = sum(int(n.get("count", 1) or 1) for n in npcs) or 1
    mult = 1.0
    for ceiling, m in DND_GROUP_MULT:
        if count <= ceiling:
            mult = m
            break
    return int(raw * mult)


def analyse_dnd(party: List[Dict[str, Any]], npcs: List[Dict[str, Any]],
                env: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    th = _dnd_party_threshold(party)
    npc_xp = _dnd_npc_xp(npcs)
    if not party:
        rating = "Unknown"
        score = 0.5
    elif npc_xp <= th["easy"]:
        rating = "Pushover"
        score = max(0.05, npc_xp / max(1, th["easy"]) * 0.3)
    elif npc_xp <= th["medium"]:
        rating = "Easy"
        score = 0.3 + (npc_xp - th["easy"]) / max(1, th["medium"] - th["easy"]) * 0.2
    elif npc_xp <= th["hard"]:
        rating = "Medium"
        score = 0.5 + (npc_xp - th["medium"]) / max(1, th["hard"] - th["medium"]) * 0.2
    elif npc_xp <= th["deadly"]:
        rating = "Hard"
        score = 0.7 + (npc_xp - th["hard"]) / max(1, th["deadly"] - th["hard"]) * 0.2
    else:
        rating = "Deadly"
        score = min(1.0, 0.9 + (npc_xp - th["deadly"]) / max(1, th["deadly"]) * 0.1)
    return {
        "system_id": "dnd-5e",
        "rating": rating,
        "score": round(score, 3),
        "reason": (
            f"Adjusted encounter XP {npc_xp} vs party deadly threshold {th['deadly']} "
            f"(medium {th['medium']}, hard {th['hard']})."
        ),
        "party_label": f"{len(party)} PCs · medium {th['medium']} XP · deadly {th['deadly']} XP",
        "npc_label": f"{sum(int(n.get('count', 1) or 1) for n in npcs)} NPCs · {npc_xp} adj. XP",
        "suggestions": _dnd_suggestions(rating, score, party, npcs, th, npc_xp, env),
    }


def _dnd_suggestions(rating: str, score: float, party, npcs, th, npc_xp, env):
    s = []
    if rating in ("Pushover", "Easy"):
        s.append({"kind": "add_minion", "icon": "swords", "delta": +1,
                  "label": "Add 1-2 minions (CR 1/4 ≈ 50 XP each) — keeps it engaging without one-shotting the party"})
        s.append({"kind": "env",        "icon": "mountain", "delta": 0,
                  "label": "Add an environmental hazard — shifting terrain, falling debris, or a ticking clock — for tension without raising raw XP"})
    elif rating == "Medium":
        s.append({"kind": "feat",       "icon": "sparkles", "delta": +1,
                  "label": "Give the lead NPC a single Legendary Action — pushes drama, not raw lethality"})
        s.append({"kind": "reposition", "icon": "compass", "delta": 0,
                  "label": "Position NPCs in cover or elevated terrain — costs the party a turn to engage"})
    elif rating == "Hard":
        s.append({"kind": "armor", "icon": "shield", "delta": -1,
                  "label": "Drop the BBEG's AC by 1 OR shave 10% HP — sustains pressure without one-shotting"})
        s.append({"kind": "env",   "icon": "flame",  "delta": 0,
                  "label": "Add a ticking environmental clock — escape route closing, ritual completing — to make the fight a race, not a slog"})
    elif rating == "Deadly":
        s.append({"kind": "remove_npc", "icon": "x", "delta": -1,
                  "label": "Remove one minion or downgrade the BBEG's CR by 1 — the table risks a TPK as it stands"})
        s.append({"kind": "feat",       "icon": "scroll", "delta": 0,
                  "label": "Plant an exit / negotiation lever — a surrender clause, a bystander hostage, a way out that costs the party something less than their lives"})
    if env and env.get("indoor"):
        s.append({"kind": "env", "icon": "door", "delta": 0,
                  "label": "Indoor — consider line-of-sight breaks (pillars, overturned tables) so casters can't dominate by initiative alone"})
    return s


# ────────────────────────── Cypher difficulty engine ──────────────────────────
def analyse_cypher(party: List[Dict[str, Any]], npcs: List[Dict[str, Any]],
                   env: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Cypher resolves at TN = level × 3. The encounter difficulty here is
    the AVERAGE NPC level vs the party's tier-weighted ability to lower
    difficulty (Trained / Specialised / Effort / Edge / Asset = each lower 1).
    """
    if not party:
        return {"system_id": "cypher", "rating": "Unknown", "score": 0.5,
                "reason": "No party seated.", "party_label": "0 PCs",
                "npc_label": f"{len(npcs)} NPCs", "suggestions": []}
    pc_count = len(party)
    avg_tier = sum(int((p.get("cypher_state") or {}).get("tier") or p.get("tier") or 1) for p in party) / pc_count
    # Party's combined "step lowering" capacity — heuristic.
    avg_steps = avg_tier * 1.5  # ~1.5 steps per tier on average
    # Encounter level — weighted average + bonus per extra NPC.
    npc_levels = []
    for n in npcs:
        lvl = int(n.get("level") or 3)
        for _ in range(int(n.get("count", 1) or 1)):
            npc_levels.append(lvl)
    if not npc_levels:
        return {"system_id": "cypher", "rating": "Pushover", "score": 0.1,
                "reason": "No NPCs in encounter.", "party_label": f"{pc_count} PCs",
                "npc_label": "0 NPCs", "suggestions": []}
    enc_level = sum(npc_levels) / len(npc_levels)
    # +0.5 per extra NPC beyond the party size.
    overflow = max(0, len(npc_levels) - pc_count) * 0.5
    raw_difficulty = enc_level + overflow
    effective = raw_difficulty - avg_steps
    if effective <= 0:
        rating = "Pushover"
        score = max(0.05, 0.2 + effective * 0.05)
    elif effective <= 1:
        rating = "Easy"
        score = 0.3
    elif effective <= 2:
        rating = "Fair"
        score = 0.5
    elif effective <= 3:
        rating = "Hard"
        score = 0.7
    else:
        rating = "Punishing"
        score = min(1.0, 0.9 + (effective - 3) * 0.05)
    return {
        "system_id": "cypher",
        "rating": rating,
        "score": round(score, 3),
        "reason": (
            f"Effective level {round(effective, 1)} (encounter {round(enc_level, 1)} + "
            f"overflow {round(overflow, 1)} − party step-down {round(avg_steps, 1)})."
        ),
        "party_label": f"{pc_count} PCs · avg Tier {round(avg_tier, 1)} · ~{round(avg_steps, 1)} step-downs",
        "npc_label":   f"{len(npc_levels)} NPCs · avg level {round(enc_level, 1)}",
        "suggestions": _cypher_suggestions(rating, party, npcs, env),
    }


def _cypher_suggestions(rating, party, npcs, env):
    s = []
    if rating in ("Pushover", "Easy"):
        s.append({"kind": "add_minion", "icon": "swords", "delta": +1,
                  "label": "Add 2-3 level-2 minions — Cypher mob-rules give the table real risk without raising the boss"})
        s.append({"kind": "env", "icon": "compass", "delta": 0,
                  "label": "Add an environmental task running parallel — sealing a portal, rescuing a NPC — splits party attention"})
    elif rating == "Fair":
        s.append({"kind": "feat", "icon": "sparkles", "delta": +1,
                  "label": "Hand the BBEG a one-shot Cypher (Tier+2 effect) — drama spike without raw level inflation"})
        s.append({"kind": "reposition", "icon": "mountain", "delta": 0,
                  "label": "Stage the encounter on uneven ground — Speed defense penalties for the squishy PCs"})
    elif rating == "Hard":
        s.append({"kind": "armor", "icon": "shield", "delta": -1,
                  "label": "GM Intrusion at the climax — gives an XP back to the player you target, eases pressure narratively"})
        s.append({"kind": "env", "icon": "flame", "delta": 0,
                  "label": "Telegraph the BBEG's signature attack the round before — the table earns the win by adapting"})
    elif rating == "Punishing":
        s.append({"kind": "remove_npc", "icon": "x", "delta": -1,
                  "label": "Remove one minion or drop the BBEG's level by 1 — Punishing lands when one wrong roll TPKs"})
        s.append({"kind": "feat", "icon": "scroll", "delta": 0,
                  "label": "Plant a lever the players can pull (collapse a beam, exploit a phase) for an automatic step-down"})
    return s


# ────────────────────────── BESM 4E / Anime 5E PL engine ─────────────────────
def analyse_besm(party: List[Dict[str, Any]], npcs: List[Dict[str, Any]],
                 env: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """BESM balances by total Character Points. ±15% = fair fight."""
    party_total = sum(int(p.get("total_points") or p.get("character_points") or 100) for p in party)
    npc_total = sum(int(n.get("total_points") or 0) * int(n.get("count", 1) or 1) for n in npcs)
    if party_total == 0:
        return {"system_id": "besm-4e", "rating": "Unknown", "score": 0.5,
                "reason": "Party has no point total — set Power Level on each PC.",
                "party_label": "—", "npc_label": "—", "suggestions": []}
    ratio = npc_total / party_total
    if ratio < 0.5:
        rating = "Pushover"
        score = 0.15
    elif ratio < 0.85:
        rating = "Easy"
        score = 0.35
    elif ratio < 1.15:
        rating = "Fair"
        score = 0.55
    elif ratio < 1.5:
        rating = "Hard"
        score = 0.75
    else:
        rating = "Punishing"
        score = min(1.0, 0.85 + (ratio - 1.5) * 0.1)
    return {
        "system_id": "besm-4e",
        "rating": rating,
        "score": round(score, 3),
        "reason": f"NPC total {npc_total} vs party total {party_total} (ratio {round(ratio, 2)}).",
        "party_label": f"{len(party)} PCs · {party_total} CP",
        "npc_label":   f"{sum(int(n.get('count', 1) or 1) for n in npcs)} NPCs · {npc_total} CP",
        "suggestions": _besm_suggestions(rating, party, npcs, ratio, env),
    }


def _besm_suggestions(rating, party, npcs, ratio, env):
    s = []
    if rating in ("Pushover", "Easy"):
        s.append({"kind": "add_minion", "icon": "swords", "delta": +1,
                  "label": "Add 1-2 light-CP henchmen (≈25% of party total each) for engagement"})
        s.append({"kind": "feat", "icon": "sparkles", "delta": 0,
                  "label": "Give a key NPC a Special Movement Attribute or a tactical Companion — narrative weight without overwhelming"})
    elif rating == "Fair":
        s.append({"kind": "env", "icon": "mountain", "delta": 0,
                  "label": "Add an environmental complication — a hostage, a collapsing structure, a moving deadline"})
        s.append({"kind": "reposition", "icon": "compass", "delta": 0,
                  "label": "Position the BBEG with a tactical advantage (high ground, ranged-only line) for thematic tension"})
    elif rating in ("Hard", "Punishing"):
        s.append({"kind": "armor", "icon": "shield", "delta": -1,
                  "label": "Drop NPC armor / health by 10-15% OR remove a Companion — keeps difficulty narratively but winnable"})
        s.append({"kind": "feat", "icon": "scroll", "delta": 0,
                  "label": "Plant a moral lever — the BBEG can be talked down, sworn to oath, or convinced to flee"})
    return s


# ────────────────────────── Dispatcher ──────────────────────────
def analyse(party: List[Dict[str, Any]], npcs: List[Dict[str, Any]],
            system_id: str = "besm-4e",
            env: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if system_id == "dnd-5e":
        return analyse_dnd(party, npcs, env)
    if system_id == "cypher":
        return analyse_cypher(party, npcs, env)
    # Anime 5E uses the BESM engine when stat blocks have point totals; D&D
    # engine when the encounter is a class+slot fight. Default to BESM.
    if system_id == "anime-5e":
        # If any NPC has CR set, use D&D engine.
        if any(n.get("cr") for n in npcs):
            return analyse_dnd(party, npcs, env)
        return analyse_besm(party, npcs, env)
    return analyse_besm(party, npcs, env)
