"""V6.6 — Cypher codex-aware suggestion engine + Anime 5E CR kit.

Two endpoints live here:

  * `GET /api/cypher/{campaign_id}/suggest` — inspects the campaign's
    codex (genre, tone, plot phase, motive cluster) and returns a
    ranked list of Descriptors / Foci / Types / Cyphers / Artifacts
    that fit the setting. Suggestions are reasoned — the response
    carries a `why` string per row so players can see WHY an option
    was surfaced.

  * `GET /api/anime5e/encounter-budget` — pure math endpoint. Takes
    party_level + party_size + difficulty and returns the Anime 5E
    CR/XP budget with slot-by-CR guidance and environmental-hazard
    allowance.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from core.db import db
from core.security import get_current_user
from system_data.cypher_data import REFERENCE as CYPHER_REF


router = APIRouter(prefix="/api", tags=["cypher-suggest", "anime5e-cr"])


# ─── Cypher — codex-aware suggestions ────────────────────────────

def _score_genre(entry_genres: List[str], camp_genre: str) -> int:
    """Return 0 (no match), 1 (generic "any"), 2 (explicit match)."""
    if not entry_genres:
        return 1
    if "any" in entry_genres:
        return 1
    return 2 if camp_genre in entry_genres else 0


def _tone_hints(phase: str, motive_text: str) -> Dict[str, List[str]]:
    """Map the campaign's plot phase + dominant motive to a set of
    keyword hints we'll weight descriptor/focus names against."""
    phase = (phase or "").lower()
    motive = (motive_text or "").lower()
    keys = {
        "descriptors": [],
        "foci": [],
        "types": [],
    }
    # Phase-driven descriptor bias.
    if "doomed" in phase or "tragic" in motive or "sacrifice" in motive:
        keys["descriptors"] += ["Doomed", "Mystical", "Hideous"]
        keys["foci"] += ["Bears a Halo of Fire", "Works Miracles"]
    if "rising" in phase or "ascend" in motive:
        keys["descriptors"] += ["Brash", "Impulsive", "Swift"]
        keys["foci"] += ["Leads", "Masters Weaponry"]
    if "mystery" in phase or "investig" in motive or "unearth" in motive:
        keys["descriptors"] += ["Clever", "Mysterious", "Intelligent"]
        keys["foci"] += ["Explores Dark Places", "Commands Mental Might"]
    if "heist" in phase or "infiltrat" in motive:
        keys["descriptors"] += ["Stealthy", "Charming", "Swift"]
        keys["foci"] += ["Murders", "Wields Two Weapons at Once"]
    if "revolution" in phase or "uprising" in motive or "resist" in motive:
        keys["descriptors"] += ["Resilient", "Tough"]
        keys["foci"] += ["Leads", "Defends the Weak"]
    if "war" in phase or "conflict" in motive or "battle" in motive:
        keys["descriptors"] += ["Tough", "Vicious"]
        keys["foci"] += ["Masters Weaponry", "Fights with Panache"]
    return keys


def _score_entry(entry: Dict[str, Any], camp_genre: str, hints: List[str]) -> Dict[str, Any]:
    score = _score_genre(entry.get("genres", []), camp_genre)
    matched_hints = [h for h in hints if entry.get("name") == h]
    score += len(matched_hints) * 3
    return {
        "entry": entry,
        "score": score,
        "matched_hints": matched_hints,
        "why": (
            ("Strongly suggested by codex tone" if matched_hints else
             "Genre fit" if score >= 2 else
             "Genre-neutral choice")
        ),
    }


@router.get("/cypher/{campaign_id}/suggest")
async def cypher_suggest(
    campaign_id: str,
    kind: str = "all",  # "descriptors"|"foci"|"types"|"cyphers"|"artifacts"|"all"
    limit: int = 6,
    user: dict = Depends(get_current_user),
):
    """Return codex-aware Cypher pick suggestions for the campaign.

    Reads the campaign's `setting_genre`, `genre`, the first-plot-phase
    motive cluster (top 5 motives by recency), and the session-level
    `plot_phase` if any sessions exist. Feeds these into a scoring pass
    over Descriptors / Foci / Types / Cyphers / Artifacts and returns
    the top N per axis with a `why` line per row.
    """
    camp = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp.get("system_id") != "cypher":
        raise HTTPException(400, "Codex suggestions available on Cypher campaigns only.")
    allowed = (
        user["id"] == camp["gm_id"]
        or user["id"] in (camp.get("member_ids") or [])
        or user.get("role") == "admin"
    )
    if not allowed:
        raise HTTPException(403, "Not a table member.")

    camp_genre = (camp.get("setting_genre") or camp.get("genre") or "any").lower()

    # Pull the last 5 motives and the most recent session's plot_phase.
    motives_cursor = db.nodes.find(
        {"campaign_id": campaign_id, "motive": {"$exists": True, "$ne": ""}},
        {"_id": 0, "motive": 1, "plot_phase": 1},
    ).sort("updated_at", -1).limit(5)
    motives = [m async for m in motives_cursor]
    motive_blob = " ".join([m.get("motive", "") for m in motives]).strip()
    phase_blob = " ".join([m.get("plot_phase", "") for m in motives]).strip()
    sess = await db.sessions.find_one(
        {"campaign_id": campaign_id}, {"_id": 0, "plot_phase": 1}
    )
    if sess and sess.get("plot_phase"):
        phase_blob = sess["plot_phase"] + " " + phase_blob

    hints_map = _tone_hints(phase_blob, motive_blob)

    def top_n(pool: List[Dict[str, Any]], hint_list: List[str]) -> List[Dict[str, Any]]:
        scored = sorted(
            [_score_entry(e, camp_genre, hint_list) for e in pool],
            key=lambda r: r["score"], reverse=True,
        )
        return scored[:limit]

    axes = {
        "descriptors": top_n(CYPHER_REF["descriptors"], hints_map["descriptors"]),
        "foci":        top_n(CYPHER_REF["foci"],        hints_map["foci"]),
        "types":       top_n(CYPHER_REF["types"],       hints_map["types"]),
        "cyphers":     top_n(CYPHER_REF["cyphers"],     []),
        "artifacts":   top_n(CYPHER_REF["artifacts"],   []),
    }
    if kind != "all":
        axes = {kind: axes.get(kind, [])}

    return {
        "campaign_id": campaign_id,
        "setting_genre": camp_genre,
        "plot_phase_seen": phase_blob or None,
        "motive_window": motive_blob or None,
        "suggestions": axes,
    }


# ─── Anime 5E — encounter CR / XP budget kit ─────────────────────

# Anime 5E / D&D 5E XP budget table (DMG p.82) per character per day.
# We implement the encounter-difficulty budgets (easy / medium / hard / deadly).
ENCOUNTER_XP_BUDGET = [
    # level, easy, medium, hard, deadly
    (1, 25, 50, 75, 100),
    (2, 50, 100, 150, 200),
    (3, 75, 150, 225, 400),
    (4, 125, 250, 375, 500),
    (5, 250, 500, 750, 1100),
    (6, 300, 600, 900, 1400),
    (7, 350, 750, 1100, 1700),
    (8, 450, 900, 1400, 2100),
    (9, 550, 1100, 1600, 2400),
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

# XP by CR (DMG p.274-5).
XP_BY_CR = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800, "6": 2300,
    "7": 2900, "8": 3900, "9": 5000, "10": 5900, "11": 7200,
    "12": 8400, "13": 10000, "14": 11500, "15": 13000, "16": 15000,
    "17": 18000, "18": 20000, "19": 22000, "20": 25000,
}

# Encounter-multiplier curve by number of monsters (DMG p.82).
ENCOUNTER_MULTIPLIER = [
    (1, 1.0), (2, 1.5), (3, 2.0), (7, 2.5), (11, 3.0), (15, 4.0),
]


def _xp_budget(level: int, difficulty: str) -> int:
    lvl = max(1, min(20, int(level)))
    row = next(r for r in ENCOUNTER_XP_BUDGET if r[0] == lvl)
    idx = {"easy": 1, "medium": 2, "hard": 3, "deadly": 4}.get(difficulty, 2)
    return row[idx]


def _multiplier_for(n_monsters: int) -> float:
    n = max(1, int(n_monsters))
    mult = 1.0
    for threshold, m in ENCOUNTER_MULTIPLIER:
        if n >= threshold:
            mult = m
    return mult


@router.get("/anime5e/encounter-budget")
async def anime5e_encounter_budget(
    party_level: int = 1, party_size: int = 4, difficulty: str = "medium",
    user: dict = Depends(get_current_user),
):
    """Compute an Anime 5E / D&D 5E-compatible encounter XP budget and
    return slot-by-CR suggestions.

    * `party_level` 1-20; `party_size` ≥ 1.
    * `difficulty` ∈ {easy, medium, hard, deadly}.

    Returns:
      {
        party_level, party_size, difficulty,
        xp_per_pc, total_xp_budget,
        slot_suggestions: [{ n_monsters, cr, xp_per, effective_xp }],
        environmental_hazard_budget: int,
      }
    """
    per_pc = _xp_budget(party_level, difficulty.lower())
    total = per_pc * max(1, party_size)

    # Slot suggestions — walk common group-size slots and pick the
    # highest CR that fits within total_xp × multiplier.
    slots = []
    for n in (1, 2, 4, 6, 8):
        mult = _multiplier_for(n)
        target_xp = total / mult
        # Find highest CR ≤ target_xp / n.
        best_cr, best_xp = None, 0
        for cr, xp in XP_BY_CR.items():
            if xp * n <= target_xp and xp > best_xp:
                best_cr, best_xp = cr, xp
        if best_cr:
            slots.append({
                "n_monsters": n,
                "cr": best_cr,
                "xp_per": best_xp,
                "effective_xp": int(best_xp * n * mult),
                "budget_fit_pct": round(100 * best_xp * n * mult / total),
                "multiplier": mult,
            })

    # Environmental hazards — DMG convention: half a "medium" budget.
    hazard_medium = _xp_budget(party_level, "medium") * max(1, party_size)
    return {
        "party_level": party_level,
        "party_size": party_size,
        "difficulty": difficulty,
        "xp_per_pc": per_pc,
        "total_xp_budget": total,
        "slot_suggestions": slots,
        "environmental_hazard_budget": hazard_medium // 2,
        "note": (
            f"Budget is {per_pc} XP per PC × {party_size} PCs. "
            f"Apply multiplier by monster count (1×, ×1.5 for pairs, ×2 for 3-6, …)."
        ),
    }
