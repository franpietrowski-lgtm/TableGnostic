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
            {"kind": "add_minion|remove_npc|env|armor|feat|reposition|tune",
             "icon": "swords|shield|...",
             "label": "Add a Bandit minion to keep it engaging",
             "delta": +50},
            ...
        ],
    }

The suggestion engine is rule-based, not LLM. It walks a small heuristic
ladder so the GM gets actionable nudges with deterministic latency.

V6.15 parity pass — D&D 5E and Cypher now share the same robust
suggestion scaffold as BESM/Anime 5E: environmental levers, NPC role-mix
nudges, party-spread warnings, and concrete "tune to target rating"
deltas. Every analyser still returns system-authentic math — this layer
only enriches the *advice* so the GM gets 3-6 actionable nudges per
encounter regardless of system.
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


def _dnd_suggestions(rating, score, party, npcs, th, npc_xp, env):
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
    # Shared layers (V6.15 parity pass) — only fire once there IS something to react to.
    if party and npcs:
        s.extend(_env_suggestions(env, "dnd-5e"))
        s.extend(_role_mix_suggestions(npcs, rating))
        s.extend(_party_spread_suggestions(party, "dnd-5e"))
        s.extend(_tune_to_target_dnd(rating, npc_xp, th))
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
        "suggestions": _cypher_suggestions(rating, party, npcs, env, effective, enc_level, avg_steps),
    }


def _cypher_suggestions(rating, party, npcs, env, effective=0.0, enc_level=0.0, avg_steps=0.0):
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
    # Shared layers (V6.15 parity pass).
    if party and npcs:
        s.extend(_env_suggestions(env, "cypher"))
        s.extend(_role_mix_suggestions(npcs, rating))
        s.extend(_party_spread_suggestions(party, "cypher"))
        s.extend(_tune_to_target_cypher(rating, effective, enc_level, avg_steps))
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
        "suggestions": _besm_suggestions(rating, party, npcs, ratio, env, party_total, npc_total),
    }


def _besm_suggestions(rating, party, npcs, ratio, env, party_total=0, npc_total=0):
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
    # Shared layers (V6.15 parity pass).
    if party and npcs:
        s.extend(_env_suggestions(env, "besm-4e"))
        s.extend(_role_mix_suggestions(npcs, rating))
        s.extend(_party_spread_suggestions(party, "besm-4e"))
        s.extend(_tune_to_target_besm(rating, ratio, party_total, npc_total))
    return s


# ────────────────────────── Shared V6.15 parity helpers ───────────────────
# These layer on top of each system's authentic math so every encounter
# analysis surfaces ~3-6 actionable nudges regardless of ruleset.

def _env_suggestions(env: Optional[Dict[str, Any]], system_id: str) -> List[Dict[str, Any]]:
    """Translate GM-set environment flags (indoor/weather/light/hazard) into
    tactical-lever suggestions. Safe on empty/None input.
    """
    if not env:
        return []
    out = []
    if env.get("indoor"):
        out.append({"kind": "env", "icon": "door", "delta": 0,
                    "label": "Indoor — add line-of-sight breaks (pillars, overturned tables) so casters and ranged PCs can't dominate by initiative alone."})
    weather = (env.get("weather") or "").strip()
    wl = weather.lower()
    if wl:
        if any(k in wl for k in ("fog", "mist", "smoke", "haze", "dust")):
            out.append({"kind": "env", "icon": "mountain", "delta": 0,
                        "label": f"Weather: {weather} — halve ranged targeting past short range; reward close-work and perception checks."})
        elif any(k in wl for k in ("storm", "wind", "rain", "snow", "blizzard", "hail")):
            out.append({"kind": "env", "icon": "flame", "delta": 0,
                        "label": f"Weather: {weather} — difficult terrain + ranged penalty; lightning/ice foes shine while torch-bearers suffer."})
        elif "heat" in wl or "sun" in wl or "desert" in wl:
            out.append({"kind": "env", "icon": "flame", "delta": 0,
                        "label": f"Weather: {weather} — exhaustion clock every few rounds; armoured PCs pay first."})
    light = (env.get("light") or "").strip()
    ll = light.lower()
    if ll:
        if any(k in ll for k in ("dim", "dark", "shadow", "gloom", "night", "pitch")):
            out.append({"kind": "env", "icon": "scroll", "delta": 0,
                        "label": f"Light: {light} — darkvision/stealth foes get advantage; PCs without dark-adapted vision pay a toll to engage."})
        elif any(k in ll for k in ("magical", "ward", "daylight", "radiance")):
            out.append({"kind": "env", "icon": "sparkles", "delta": 0,
                        "label": f"Light: {light} — disrupts invisibility/illusion; plant a dispel or blind-spot beat the PCs can exploit."})
    hazard = (env.get("hazard") or "").strip()
    if hazard:
        out.append({"kind": "env", "icon": "flame", "delta": 0,
                    "label": f"Hazard: {hazard} — weave a ticking clock; the scene costs something each round it's not addressed."})
    return out


def _role_mix_suggestions(npcs: List[Dict[str, Any]], rating: str) -> List[Dict[str, Any]]:
    """Nudges based on the *composition* of NPC roles, not raw math."""
    if not npcs:
        return []
    roles: Dict[str, int] = {}
    for n in npcs:
        r = (n.get("role") or "minion").lower()
        roles[r] = roles.get(r, 0) + int(n.get("count", 1) or 1)
    total = sum(roles.values())
    if total == 0:
        return []
    minions = roles.get("minion", 0)
    leaders = roles.get("villain", 0) + roles.get("nemesis", 0) + roles.get("henchman", 0)
    out = []
    if minions >= 3 and leaders == 0 and rating not in ("Pushover",):
        out.append({"kind": "feat", "icon": "crown", "delta": 0,
                    "label": f"{minions} minions, no leader — promote one to Henchman/Villain with a signature move to give the scene a silhouette."})
    if leaders >= 2 and minions == 0:
        out.append({"kind": "add_minion", "icon": "skull", "delta": 0,
                    "label": f"{leaders} leader-class foes and no rank-and-file — add 2-3 minions so the PCs have lower-risk targets to cleave through for pace."})
    if total == 1 and rating in ("Hard", "Deadly", "Punishing"):
        out.append({"kind": "reposition", "icon": "compass", "delta": 0,
                    "label": "Solo boss fights risk action-economy blowouts — give it a Lair/Legendary beat or a Phase-2 transition instead of raw HP."})
    return out


def _party_spread_suggestions(party: List[Dict[str, Any]], system_id: str) -> List[Dict[str, Any]]:
    """Warn when party level/tier/CP spread is wide enough to unbalance fairness."""
    if not party or len(party) < 2:
        return []
    out = []
    if system_id == "dnd-5e":
        lvls = [max(1, int((p.get("dnd_state") or {}).get("level") or p.get("level") or 1)) for p in party]
        if lvls and (max(lvls) - min(lvls)) >= 3:
            out.append({"kind": "feat", "icon": "sparkles", "delta": 0,
                        "label": f"Party level spread {min(lvls)}–{max(lvls)} — consider parallel objectives so the lower-level PC isn't overshadowed."})
    elif system_id == "cypher":
        tiers = [int((p.get("cypher_state") or {}).get("tier") or p.get("tier") or 1) for p in party]
        if tiers and (max(tiers) - min(tiers)) >= 2:
            out.append({"kind": "feat", "icon": "sparkles", "delta": 0,
                        "label": f"Party tier spread {min(tiers)}–{max(tiers)} — split objectives or grant the lower-tier PC a borrowed Cypher to equalise."})
    elif system_id in ("besm-4e", "anime-5e"):
        pts = [int(p.get("total_points") or p.get("character_points") or 0) for p in party]
        pts = [p for p in pts if p > 0]
        if pts and len(pts) >= 2 and (max(pts) - min(pts)) > max(pts) * 0.25:
            out.append({"kind": "feat", "icon": "sparkles", "delta": 0,
                        "label": f"Party CP spread {min(pts)}–{max(pts)} — give the lower-CP PC a borrowed Item or bring-own-Companion moment for parity."})
    return out


def _tune_to_target_dnd(rating: str, npc_xp: int, th: Dict[str, int]) -> List[Dict[str, Any]]:
    """Concrete 'how to shift into the next band' advice for D&D 5E."""
    out = []
    if rating == "Deadly":
        delta = max(1, npc_xp - th["deadly"])
        out.append({"kind": "tune", "icon": "x", "delta": -1,
                    "label": f"Tune: trim ≈ {delta} adj. XP (e.g. drop one CR-2 foe = 450 XP pre-multiplier) to land in Hard."})
    elif rating == "Pushover":
        delta = max(1, th["medium"] - npc_xp)
        out.append({"kind": "tune", "icon": "swords", "delta": +1,
                    "label": f"Tune: add ≈ {delta} adj. XP (e.g. 2× CR 1/4 = 100 XP pre-multiplier) to land in Easy/Medium."})
    elif rating == "Hard":
        delta = max(1, th["deadly"] - npc_xp)
        out.append({"kind": "tune", "icon": "swords", "delta": 0,
                    "label": f"Headroom: ~{delta} adj. XP before Deadly — safe to add a legendary action or second-wind beat."})
    return out


def _tune_to_target_cypher(rating: str, effective: float, enc_level: float, avg_steps: float) -> List[Dict[str, Any]]:
    """Concrete step-shift advice for Cypher. Each level-drop ≈ 1 effective."""
    out = []
    if rating == "Punishing":
        drop = max(1, int(round(effective - 3)))
        out.append({"kind": "tune", "icon": "x", "delta": -1,
                    "label": f"Tune: drop ≈ {drop} encounter level (one foe level-down, or remove a minion) to land in Hard."})
    elif rating == "Pushover":
        bump = max(1, int(round(1 - effective)) + 1)
        out.append({"kind": "tune", "icon": "swords", "delta": +1,
                    "label": f"Tune: raise encounter by ~{bump} level (upgrade one foe or add a level-2 minion) to land in Easy/Fair."})
    elif rating == "Hard":
        out.append({"kind": "tune", "icon": "swords", "delta": 0,
                    "label": f"Headroom: effective {round(effective,1)} — one more GM Intrusion or terrain penalty tips into Punishing. Hold the line."})
    return out


def _tune_to_target_besm(rating: str, ratio: float, party_total: int, npc_total: int) -> List[Dict[str, Any]]:
    """Concrete CP-shift advice for BESM/Anime 5E."""
    out = []
    if rating == "Punishing":
        # Target ratio ceiling for Hard is 1.5; aim for 1.35 to leave headroom.
        target = int(party_total * 1.35)
        shave = max(1, npc_total - target)
        out.append({"kind": "tune", "icon": "x", "delta": -1,
                    "label": f"Tune: shave ≈ {shave} NPC CP (drop a Companion or trim Attack Combat) to land in Hard."})
    elif rating == "Pushover":
        target = int(party_total * 0.9)
        add = max(1, target - npc_total)
        out.append({"kind": "tune", "icon": "swords", "delta": +1,
                    "label": f"Tune: add ≈ {add} NPC CP (a light henchman or a Special Movement) to land in Easy/Fair."})
    elif rating == "Fair":
        out.append({"kind": "tune", "icon": "sparkles", "delta": 0,
                    "label": f"Sweet spot: ratio {round(ratio,2)} — within BESM's ±15% fairness band. Lean on environment + drama, not CP."})
    return out


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
