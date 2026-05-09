"""V6.25.13 — Canonical Anime 5E core class library (PDF-extracted).

Replaces V6.25.12 scaffold tests. Now we have the actual 14 canonical
core classes with verbatim L1-L20 features extracted from the
dys_anime5e_rpg_v1.3.6 core rulebook.
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


def test_anime5e_class_library_returns_canonical_14_classes():
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["system"] == "anime-5e"

    # The canonical 14-class roster from the Anime 5E core rulebook.
    expected_ids = {
        "adventurer", "bender", "broker", "dynamic-spellbinder",
        "hunter", "isekai-student", "magical-girl-guy", "ninja",
        "pet-monster-trainer", "psionicist", "samurai",
        "shadow-warrior", "techknight", "warder",
    }
    got_ids = {c["id"] for c in body["classes"]}
    assert got_ids == expected_ids, f"roster mismatch: {got_ids ^ expected_ids}"

    # Proficiency-bonus ladder is universal: +2 → +6 stepping every 4.
    pb = body["proficiency_bonus_by_level"]
    assert pb["1"] == 2 and pb["4"] == 2
    assert pb["5"] == 3 and pb["9"] == 4
    assert pb["13"] == 5 and pb["17"] == 6 and pb["20"] == 6


def test_every_class_has_full_l1_l20_grid_with_ashi_flags():
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    body = r.json()
    for c in body["classes"]:
        grid = c["grants_by_level"]
        assert len(grid) == 20, f"{c['id']} grid size {len(grid)}"
        for L in range(1, 21):
            row = grid[str(L)]
            assert row.get("proficiency_bonus") == {
                1: 2, 2: 2, 3: 2, 4: 2,
                5: 3, 6: 3, 7: 3, 8: 3,
                9: 4, 10: 4, 11: 4, 12: 4,
                13: 5, 14: 5, 15: 5, 16: 5,
                17: 6, 18: 6, 19: 6, 20: 6,
            }[L]
            assert "features" in row
            assert "asi_or_feat" in row
            assert "points_granted" in row


def test_samurai_l5_features_match_canonical():
    """Samurai L5: +2 Combat Technique (Two Weapons) [2], +1 Inspire [1],
    +1 Skill Proficiency [1] — verbatim from page 82 of core book."""
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    body = r.json()
    samurai = next(c for c in body["classes"] if c["id"] == "samurai")
    L5 = samurai["grants_by_level"]["5"]
    feats = L5["features"]
    assert any("Combat Technique (Two Weapons)" in f for f in feats)
    assert any("Inspire" in f for f in feats)
    # Points budget for L5 sums to 4 (2+1+1).
    assert L5["points_granted"] == 4


def test_techknight_armour_zero_cost_grant():
    """Techknight L1 grants 'Techknight Armour [0]' — a story-flag
    grant that costs 0 points (lookup-table edge case)."""
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    body = r.json()
    tk = next(c for c in body["classes"] if c["id"] == "techknight")
    L1 = tk["grants_by_level"]["1"]
    assert any("Techknight Armour" in f for f in L1["features"])


def test_class_specific_asi_levels_exposed():
    """Each class advertises which levels carry an ASI prompt — the
    builder uses this for the AdvancementBadge surfacing."""
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    body = r.json()
    # Bender ASIs: 4, 8, 12, 16, 19 (verbatim from page 28).
    bender = next(c for c in body["classes"] if c["id"] == "bender")
    assert bender["asi_levels"] == [4, 8, 12, 16, 19]
    # Adventurer has no ASI prompts (only point grants).
    adv = next(c for c in body["classes"] if c["id"] == "adventurer")
    assert adv["asi_levels"] == []


def test_class_starting_kit_round_trips():
    """Save proficiencies / hit die / weapon profs round-trip on every
    class entry (frontend builder uses these for character creation)."""
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    body = r.json()
    samurai = next(c for c in body["classes"] if c["id"] == "samurai")
    assert samurai["hit_die"] == 10
    assert samurai["primary_ability"] == "Strength"
    assert "Strength" in samurai["save_proficiencies"]
    assert "Wisdom" in samurai["save_proficiencies"]
    assert "martial" in samurai["weapon_proficiencies"]
    assert "heavy" in samurai["armour_proficiencies"]
