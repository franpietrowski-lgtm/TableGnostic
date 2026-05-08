"""V6.25.22 — Anime 5E race templates (bundled attrs/defects/ASI/speed)
+ floating CP balance widget data contract.

Race entries returned by `/api/anime5e/races` are now MERGED with
their bundled templates so the character sheet can render the full
profile (CP cost, size, speed, ability_score_increase, bundled_attributes,
bundled_defects, languages) without a second round-trip.
"""
from __future__ import annotations
import os
import requests

from system_data.anime5e_race_templates import (
    ANIME_5E_RACE_TEMPLATES, race_template, merged_race_entry,
)
from system_data.anime5e_race_costs import (
    ANIME_5E_RACES, dp_budget_for_level, get_race,
)

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _gm():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200
    return r.json()["access_token"]


# ── Unit-tests on the template registry ────────────────────────────

def test_every_native_race_has_a_template():
    """All 14 native Anime 5E races (excluding the PHB cross-overs)
    must have a bundled template entry."""
    native_keys = {
        "archfiend", "asrai", "blinkbeast", "demonaga", "fairy",
        "grey", "half-dragon", "half-troll", "haud", "kodama",
        "nekojin", "parasite", "satyr", "slime",
    }
    assert native_keys.issubset(set(ANIME_5E_RACE_TEMPLATES.keys()))


def test_template_carries_required_keys():
    """Every template MUST have speed (int), bundled_attributes (list),
    bundled_defects (list), languages (list), ability_score_increase
    (dict)."""
    for key, t in ANIME_5E_RACE_TEMPLATES.items():
        assert isinstance(t.get("speed"), int) and t["speed"] > 0, key
        assert isinstance(t.get("bundled_attributes"), list), key
        assert isinstance(t.get("bundled_defects"), list), key
        assert isinstance(t.get("languages"), list), key
        assert isinstance(t.get("ability_score_increase"), dict), key


def test_signature_race_templates_match_pdf():
    """Spot-check signature races against the printed values."""
    arch = race_template("archfiend")
    assert arch["speed"] == 120
    # Augmented (Strength) ranks 4 — Anime 5E p.32.
    augmented = next((a for a in arch["bundled_attributes"]
                       if a["name"].startswith("Augmented")), None)
    assert augmented and augmented["ranks"] == 4
    # Vulnerability (Lightning) defect — Anime 5E p.32.
    assert any("Lightning" in d["name"] for d in arch["bundled_defects"])

    fairy = race_template("fairy")
    assert fairy["speed"] == 4  # ÷8 of 30ft baseline
    assert fairy["ability_score_increase"] == {"Wisdom": 1, "Charisma": 2}

    nek = race_template("nekojin")
    assert nek["ability_score_increase"] == {"Dexterity": 2}
    # Mulligan ranks 2 = 4 re-rolls/session per the printed entry.
    mull = next((a for a in nek["bundled_attributes"]
                  if a["name"].startswith("Mulligan")), None)
    assert mull and mull["ranks"] == 2


def test_merged_race_entry_preserves_dp_cost():
    """Merging the template into a base ANIME_5E_RACES entry must
    NEVER overwrite the published dp_cost."""
    arch_base = next(r for r in ANIME_5E_RACES if r["key"] == "archfiend")
    merged = merged_race_entry(arch_base)
    assert merged["dp_cost"] == arch_base["dp_cost"]  # 15
    # Template fields are now present on the merged entry.
    assert merged["speed"] == 120
    assert merged["bundled_attributes"]
    assert merged["bundled_defects"]
    assert merged["languages"] == ["Common", "Infernal"]


def test_get_race_then_merge_is_idempotent():
    """Calling get_race + merged_race_entry twice yields the same shape."""
    r = get_race("nekojin")
    once = merged_race_entry(r)
    twice = merged_race_entry(once)
    # The second merge must NOT duplicate or shift any keys.
    assert once == twice


# ── End-to-end: /api/anime5e/races returns merged shape ────────────

def test_anime5e_races_endpoint_returns_merged_templates():
    gm = _gm()
    r = requests.get(f"{BASE_URL}/api/anime5e/races",
                      headers=H(gm))
    assert r.status_code == 200
    body = r.json()
    by_key = {row["key"]: row for row in body["races"]}

    for key in ["archfiend", "fairy", "nekojin", "slime"]:
        assert key in by_key, f"missing {key} in /races response"
        row = by_key[key]
        # CP cost preserved.
        assert isinstance(row["dp_cost"], int) and row["dp_cost"] >= 0
        # Bundled fields present.
        assert "bundled_attributes" in row
        assert "bundled_defects" in row
        assert "languages" in row
        assert "speed" in row
        assert "ability_score_increase" in row

    # Raceless entry stays cost 0 and lists nothing.
    rl = by_key["raceless"]
    assert rl["dp_cost"] == 0
    assert rl["bundled_attributes"] == []
    # rules_note text mentions the new template surface.
    assert "p.28-45" in body["rules_note"]


# ── DP budget formula validation ───────────────────────────────────

def test_dp_budget_formula_is_80_plus_level_minus_one():
    """Anime 5E core p.20: 80 DP + 1/level above 1st."""
    cases = [(1, 80), (2, 81), (5, 84), (10, 89), (20, 99)]
    for lvl, expected in cases:
        assert dp_budget_for_level(lvl) == expected, \
            f"L{lvl}: expected {expected}, got {dp_budget_for_level(lvl)}"
