"""V6.19 — Race DP costs + class progression + budget audit + workshop tests."""
from __future__ import annotations
import sys

sys.path.insert(0, "/app/backend")

from system_data.anime5e_race_costs import (  # noqa: E402
    RACE_DP_COSTS, ANIME5E_TIER_TABLE, get_race, anime5e_tier_for_level,
)
from system_data.class_progression import (  # noqa: E402
    cumulative_features, CLASS_PROGRESSION,
)
from routes.character_validation import anime5e_xp_to_cp  # noqa: E402


# ─── Race DP table ──────────────────────────────────────────────────────


def test_all_8_anime5e_races_present():
    assert len(RACE_DP_COSTS) == 8
    keys = {r["key"] for r in RACE_DP_COSTS}
    assert keys == {"human", "beastfolk", "construct", "half-demon",
                     "faerie", "spirit", "animal", "apprentice"}


def test_every_race_has_dp_cost_and_traits():
    for r in RACE_DP_COSTS:
        assert isinstance(r["dp_cost"], int) and r["dp_cost"] >= 1
        assert isinstance(r["traits"], list) and len(r["traits"]) >= 1
        assert r["page_ref"]


def test_get_race_case_insensitive():
    assert get_race("Human")["key"] == "human"
    assert get_race("HUMAN")["key"] == "human"
    assert get_race("beastfolk")["dp_cost"] == 3
    assert get_race("xyz") is None


# ─── Tier table & budget formula ────────────────────────────────────────


def test_anime5e_tier_for_level_brackets():
    assert anime5e_tier_for_level(1)["dp"] == 10  # Tier 1
    assert anime5e_tier_for_level(2)["dp"] == 10
    assert anime5e_tier_for_level(3)["dp"] == 20  # Tier 2
    assert anime5e_tier_for_level(5)["dp"] == 20
    assert anime5e_tier_for_level(6)["dp"] == 40  # Tier 3
    assert anime5e_tier_for_level(10)["dp"] == 40
    assert anime5e_tier_for_level(15)["dp"] == 60  # Tier 4
    assert anime5e_tier_for_level(20)["dp"] == 80  # Tier 5


def test_xp_to_cp_tier_formula_matches_canonical():
    # 'tier' formula should match the canonical Tier table.
    for L in [1, 3, 5, 7, 12, 18]:
        assert anime5e_xp_to_cp(L, "tier") == anime5e_tier_for_level(L)["dp"]


def test_xp_to_cp_flat_no_longer_overscales():
    # Old V6.4 formula 50+8L was 90 at level 5. New flat is 5+3L = 20.
    assert anime5e_xp_to_cp(5, "flat") == 20
    assert anime5e_xp_to_cp(10, "flat") == 35


def test_xp_to_cp_curve_heroic_house_rule():
    # 5 + 5L
    assert anime5e_xp_to_cp(1, "curve") == 10
    assert anime5e_xp_to_cp(5, "curve") == 30


def test_xp_to_cp_unknown_formula_falls_back_to_tier():
    assert anime5e_xp_to_cp(5, "homebrew") == 20


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
    # Should include levels with content. Artificer has level 1, 2, 3, 4, 5.
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
    """Anime 5E original classes should expose D&D-5E-flavoured chassis
    fields (hit die, saves, weapons/armor profs)."""
    for cls in ("Adept", "Idol", "Pilot", "Tinker"):
        out = cumulative_features(cls, 1)
        assert out["known"]
        assert out["hit_die"]
        assert out["save_profs"]
