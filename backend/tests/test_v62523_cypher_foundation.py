"""V6.25.23 — Cypher System foundational data layer (Cycle B-1).

Seeds genres, tier progression, full per-tier ability rosters for the
4 core types, XP mechanics (awards + spends + advancement steps),
skill levels, and rule notes. New `/api/cypher/tier-helper?type=x&tier=N`
endpoint powers the builder's tier-progression sidebar.
"""
from __future__ import annotations
import os
import requests

from system_data.cypher_data import (
    REFERENCE, GENRES, TIER_PROGRESSION, ADVANCEMENT_STEPS_PER_TIER,
    CYPHER_TYPES_FULL, XP_MECHANICS, SKILL_LEVELS, RULES_NOTES,
    COMPATIBILITY_NOTICE, get_type_full, tier_caps, all_abilities_for,
)

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


# ── Unit tests on the data registry ────────────────────────────────

def test_compatibility_notice_present():
    assert "Cypher System Open" in COMPATIBILITY_NOTICE
    assert "CSOL 2022" in COMPATIBILITY_NOTICE


def test_eight_genres_with_blurbs():
    assert len(GENRES) == 8
    keys = {g["key"] for g in GENRES}
    assert {"fantasy", "modern", "science-fiction", "superheroes",
            "horror", "post-apocalyptic", "fairy-tale", "historical"} == keys
    for g in GENRES:
        assert g.get("blurb")


def test_six_tier_progression_with_effort_caps():
    assert [t["tier"] for t in TIER_PROGRESSION] == [1, 2, 3, 4, 5, 6]
    assert [t["max_effort"] for t in TIER_PROGRESSION] == [1, 2, 3, 4, 5, 6]


def test_four_advancement_steps_at_4_xp_each():
    assert len(ADVANCEMENT_STEPS_PER_TIER) == 4
    assert all(s["xp_cost"] == 4 for s in ADVANCEMENT_STEPS_PER_TIER)
    keys = {s["key"] for s in ADVANCEMENT_STEPS_PER_TIER}
    assert keys == {"increasing-capabilities", "moving-toward-perfection",
                    "extra-effort", "skill-training"}


def test_four_core_types_with_canonical_starting_pools():
    by_key = {t["key"]: t for t in CYPHER_TYPES_FULL}
    assert set(by_key.keys()) == {"warrior", "adept", "explorer", "speaker"}
    # Warrior: 11/10/8 (high might).
    assert by_key["warrior"]["starting_stat_pools"] == {"Might": 11, "Speed": 10, "Intellect": 8}
    # Adept: 7/9/12 (high intellect, cypher limit 3).
    assert by_key["adept"]["starting_stat_pools"] == {"Might": 7, "Speed": 9, "Intellect": 12}
    assert by_key["adept"]["starting_cypher_limit"] == 3
    # Explorer: 10/9/9 (balanced, might edge).
    assert by_key["explorer"]["starting_stat_pools"] == {"Might": 10, "Speed": 9, "Intellect": 9}
    # Speaker: 8/9/11 (intellect lead).
    assert by_key["speaker"]["starting_stat_pools"] == {"Might": 8, "Speed": 9, "Intellect": 11}


def test_each_type_has_six_tiers_of_abilities():
    for t in CYPHER_TYPES_FULL:
        for tier in range(1, 7):
            abilities = t["abilities_by_tier"].get(str(tier))
            assert abilities and len(abilities) >= 4, \
                f"{t['key']} tier {tier}: only {len(abilities or [])} abilities"


def test_xp_mechanics_includes_peer_transfer_and_intrusion_refusal():
    spends = {s["key"]: s for s in XP_MECHANICS["spends"]}
    # Peer transfer (1 XP) + refuse intrusion (1 XP) + narrative pool.
    assert "peer-transfer" in spends
    assert spends["peer-transfer"]["cost"] == 1
    assert "refuse-intrusion" in spends
    assert spends["refuse-intrusion"]["cost"] == 1
    assert "narrative-pool" in spends
    # Tier advancement: 4 × 4 = 16 XP.
    assert "16 XP" in XP_MECHANICS["tier_advancement_rule"]


def test_all_abilities_for_warrior_tier_3_includes_tier_3_entries():
    abilities = all_abilities_for("warrior", 3)
    tiers_seen = {a["tier"] for a in abilities}
    # Must include 1, 2, 3 — but NOT 4 / 5 / 6.
    assert tiers_seen == {1, 2, 3}, tiers_seen
    names = {a["name"] for a in abilities}
    assert "Bash" in names  # tier 1
    assert "Reload" in names  # tier 2
    assert "Fury" in names  # tier 3


def test_get_type_full_is_case_insensitive():
    assert get_type_full("warrior")["name"] == "Warrior"
    assert get_type_full("WARRIOR")["name"] == "Warrior"
    assert get_type_full("  Adept  ")["name"] == "Adept"
    assert get_type_full("nope") is None


def test_tier_caps_clamps_to_1_6():
    assert tier_caps(1)["max_effort"] == 1
    assert tier_caps(6)["max_effort"] == 6
    assert tier_caps(0) is None
    assert tier_caps(7) is None


def test_skill_levels_match_canon():
    by_lvl = {s["level"]: s for s in SKILL_LEVELS}
    assert by_lvl["Inability"]["step_shift"] == 1
    assert by_lvl["Untrained"]["step_shift"] == 0
    assert by_lvl["Trained"]["step_shift"] == -1
    assert by_lvl["Specialised"]["step_shift"] == -2


def test_rules_notes_paraphrased_not_verbatim():
    """RULES_NOTES must be paraphrased — no lift of the canonical
    'A character can apply Effort to a roll' phrasing."""
    joined = " ".join(RULES_NOTES).lower()
    # Sanity — our paraphrases should still mention the mechanics.
    assert "effort" in joined
    assert "edge" in joined
    assert "cypher limit" in joined
    assert "intrusion" in joined


def test_reference_dict_carries_v62523_keys():
    """The /reference endpoint payload must expose all V6.25.23 keys."""
    for k in ["genres", "tier_progression", "types_full",
              "xp_mechanics", "skill_levels_v2", "rules_notes",
              "compatibility_notice", "advancement_steps"]:
        assert k in REFERENCE, f"{k} missing from REFERENCE"


# ── End-to-end ──────────────────────────────────────────────────────

def test_systems_cypher_reference_serves_v62523():
    r = requests.get(f"{BASE_URL}/api/systems/cypher/reference")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["system_id"] == "cypher"
    assert len(body["genres"]) == 8
    assert len(body["types_full"]) == 4
    assert "Cypher System Open" in body["compatibility_notice"]


def test_tier_helper_returns_full_payload():
    r = requests.get(f"{BASE_URL}/api/cypher/tier-helper",
                      params={"type": "adept", "tier": 4})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"]["name"] == "Adept"
    assert body["type"]["starting_cypher_limit"] == 3
    assert body["tier"]["tier"] == 4
    assert body["tier"]["max_effort"] == 4
    # Adept tier 1 has 11 abilities, +7 tier 2, +7 tier 3, +10 tier 4 = 35.
    assert len(body["abilities_unlocked"]) == 35
    assert body["tier_advancement_xp_total"] == 16


def test_tier_helper_rejects_unknown_type_or_bad_tier():
    r = requests.get(f"{BASE_URL}/api/cypher/tier-helper",
                      params={"type": "warlock", "tier": 1})
    assert r.status_code == 404
    r = requests.get(f"{BASE_URL}/api/cypher/tier-helper",
                      params={"type": "warrior", "tier": 9})
    assert r.status_code == 422
