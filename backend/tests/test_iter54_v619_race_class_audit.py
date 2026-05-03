"""V6.21 — Race DP costs + class progression + RAW DP math tests.

Replaces V6.19 assertions. The RACE table was expanded to 28 entries
(14 native Anime 5E races + 14 PHB crossovers). The DP formula is
RAW-correct: 80 + (level − 1) per core p.20.
"""
from __future__ import annotations
import sys

sys.path.insert(0, "/app/backend")

from system_data.anime5e_race_costs import (  # noqa: E402
    RACE_DP_COSTS, ANIME5E_TIER_TABLE, get_race, anime5e_tier_for_level,
    dp_budget_for_level, ANIME_5E_RACES, RACELESS,
)
from system_data.class_progression import (  # noqa: E402
    cumulative_features, CLASS_PROGRESSION,
)
from routes.character_validation import anime5e_xp_to_cp  # noqa: E402


# ─── Race DP table ──────────────────────────────────────────────────────


def test_race_table_has_native_and_phb_entries():
    assert len(RACE_DP_COSTS) >= 14  # native races
    # Verify the RACE_DP_COSTS alias still points at ANIME_5E_RACES.
    assert RACE_DP_COSTS is ANIME_5E_RACES


def test_every_race_has_dp_cost_and_blurb():
    for r in RACE_DP_COSTS:
        assert isinstance(r["dp_cost"], int) and r["dp_cost"] >= 0
        assert r["name"]
        assert r["key"]
        assert r["blurb"]


def test_get_race_case_insensitive_and_raceless():
    assert get_race("Human")["key"] == "human"
    assert get_race("HUMAN")["key"] == "human"
    assert get_race("human")["dp_cost"] == 7  # RAW Table 04
    assert get_race("raceless") is RACELESS
    assert get_race("none") is RACELESS
    assert get_race("") is None  # empty string → no match
    assert get_race("xyz") is None


def test_known_race_costs_match_raw_table_04():
    """Spot-check canonical RAW DP costs per Anime 5E Table 04."""
    assert get_race("human")["dp_cost"] == 7
    assert get_race("fairy")["dp_cost"] == 4
    assert get_race("satyr")["dp_cost"] == 7
    assert get_race("tiefling")["dp_cost"] == 12
    assert get_race("dragonborn")["dp_cost"] == 9


# ─── Combat tier table (NOT the DP budget) ─────────────────────────────


def test_anime5e_tier_table_levels():
    # The combat tier table caps scaling, NOT the DP budget.
    tier1 = anime5e_tier_for_level(1)
    assert tier1["name"] == "Novice"
    assert tier1["caps"]["max_ability_high"] == 18
    tier20 = anime5e_tier_for_level(20)
    assert tier20["name"] == "Mythical"
    assert tier20["caps"]["max_ability_high"] == 24


# ─── DP budget (RAW p.20) ──────────────────────────────────────────────


def test_dp_budget_raw_formula():
    assert dp_budget_for_level(1) == 80
    assert dp_budget_for_level(2) == 81
    assert dp_budget_for_level(5) == 84
    assert dp_budget_for_level(10) == 89
    assert dp_budget_for_level(20) == 99


def test_xp_to_cp_raw_is_default():
    assert anime5e_xp_to_cp(1) == 80
    assert anime5e_xp_to_cp(5) == 84
    assert anime5e_xp_to_cp(20) == 99


def test_xp_to_cp_formula_variants():
    # flat: 80 DP at every level (GM house-rule)
    assert anime5e_xp_to_cp(1, "flat") == 80
    assert anime5e_xp_to_cp(10, "flat") == 80
    # curve: 80 + 2(L-1) (GM heroic house-rule)
    assert anime5e_xp_to_cp(1, "curve") == 80
    assert anime5e_xp_to_cp(5, "curve") == 88
    assert anime5e_xp_to_cp(10, "curve") == 98
    # tier legacy bracket still works for back-compat
    assert anime5e_xp_to_cp(5, "tier") == 20
    assert anime5e_xp_to_cp(1, "tier") == 10


def test_xp_to_cp_unknown_formula_falls_back_to_raw():
    # Unknown formula should fall back to RAW (was tier in V6.19).
    assert anime5e_xp_to_cp(5, "homebrew") == 84


# ─── Class progression ──────────────────────────────────────────────────


def test_class_progression_contains_known_classes():
    for cls in ("Artificer", "Wizard", "Fighter", "Adept", "Idol", "Pilot", "Tinker"):
        assert cls in CLASS_PROGRESSION
        prog = CLASS_PROGRESSION[cls]
        assert prog["hit_die"]
        assert isinstance(prog["save_profs"], list)
        assert isinstance(prog["levels"], dict)
        assert 1 in prog["levels"]


def test_cumulative_features_artificer_level_5():
    out = cumulative_features("Artificer (Alchemist)", 5)
    assert out["known"] is True
    assert out["class"] == "Artificer"
    assert out["level"] == 5
    levels = [row["level"] for row in out["timeline"]]
    assert levels == [1, 2, 3, 4, 5]
    assert out["spell_progression"] == "half_caster"
    assert "Constitution" in out["save_profs"]
    assert "Intelligence" in out["save_profs"]


def test_cumulative_features_unknown_class_returns_advice():
    out = cumulative_features("Necromancer of the Fourth Wall", 3)
    assert out["known"] is False
    assert "homebrew" in out["advice"].lower()


def test_cumulative_features_strips_parenthetical():
    out1 = cumulative_features("Artificer", 3)
    out2 = cumulative_features("Artificer (Alchemist)", 3)
    assert out1["timeline"] == out2["timeline"]
    assert out1["save_profs"] == out2["save_profs"]


def test_anime5e_originals_have_chassis_data():
    for cls in ("Adept", "Idol", "Pilot", "Tinker"):
        out = cumulative_features(cls, 1)
        assert out["known"]
        assert out["hit_die"]
        assert out["save_profs"]
