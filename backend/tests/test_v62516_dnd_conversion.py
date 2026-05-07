"""V6.25.16 — D&D 5E → Anime 5E class conversion table (PDF pp.82-88).

Every D&D class maps to:
  * an Anime 5E core class id (from the canonical 14-class roster)
  * a curated list of Anime 5E approved attributes (each with a starter
    rank) — every attribute MUST exist in the canonical attribute table
  * a list of suggested defects (free-form)
  * a notes blurb describing the deconstruction
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


CANONICAL_ANIME5E_CLASS_IDS = {
    "adventurer", "bender", "broker", "dynamic-spellbinder", "hunter",
    "isekai-student", "magical-girl-guy", "ninja", "pet-monster-trainer",
    "psionicist", "samurai", "shadow-warrior", "techknight", "warder",
}


def test_dnd_conversion_lists_all_12_classes():
    r = requests.get(f"{BASE_URL}/api/anime5e/dnd-conversion")
    assert r.status_code == 200, r.text
    body = r.json()
    classes = {row["dnd_class"] for row in body["mapping"]}
    expected = {"Barbarian", "Bard", "Cleric", "Druid", "Fighter",
                "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer",
                "Warlock", "Wizard"}
    assert classes == expected
    assert "pp.82-88" in body["source_pages"]


def test_dnd_conversion_anime5e_class_ids_are_canonical():
    """Every recommended Anime 5E class id must exist in the canonical
    14-class roster (anime5e_class_library)."""
    r = requests.get(f"{BASE_URL}/api/anime5e/dnd-conversion")
    body = r.json()
    for row in body["mapping"]:
        assert row["anime5e_class_id"] in CANONICAL_ANIME5E_CLASS_IDS, row


def test_dnd_conversion_attributes_match_canonical_roster():
    """The recommendation table must only reference Anime 5E attributes
    that ACTUALLY exist in the approved roster (system_data
    POINT_BUY_ATTRIBUTES). Catches silent drift between the two seeds."""
    canon = {a["name"] for a in
             requests.get(f"{BASE_URL}/api/systems/anime-5e/reference")
             .json()["point_buy_attributes"]}
    r = requests.get(f"{BASE_URL}/api/anime5e/dnd-conversion")
    body = r.json()
    for row in body["mapping"]:
        for attr_name, rank in row["anime5e_attributes"]:
            assert attr_name in canon, (
                f"{row['dnd_class']} recommends `{attr_name}` "
                f"which isn't in the canonical attribute roster."
            )
            assert isinstance(rank, int) and rank >= 1


def test_dnd_conversion_single_class_lookup():
    r = requests.get(f"{BASE_URL}/api/anime5e/dnd-conversion?dnd_class=Fighter")
    assert r.status_code == 200
    body = r.json()
    assert body["dnd_class"] == "Fighter"
    assert body["anime5e_class_id"] == "samurai"
    # Combat Mastery should be in the recommendations.
    names = {n for n, _ in body["anime5e_attributes"]}
    assert "Combat Mastery" in names


def test_dnd_conversion_unknown_class_returns_helpful_404ish():
    r = requests.get(f"{BASE_URL}/api/anime5e/dnd-conversion?dnd_class=Artificer")
    assert r.status_code == 200  # endpoint always 200, but error shape
    body = r.json()
    assert body.get("error") == "Unknown D&D class"
    assert "Fighter" in body["available"]
