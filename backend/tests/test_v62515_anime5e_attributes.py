"""V6.25.15 — Canonical Anime 5E Attributes seed (PDF p.91-130).

Replaces the V6.21 9-entry placeholder with the full 64-entry approved
roster from the Anime 5E core rulebook, categorised and page-cited.
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


def test_anime5e_reference_exposes_canonical_attribute_roster():
    r = requests.get(f"{BASE_URL}/api/systems/anime-5e/reference")
    assert r.status_code == 200, r.text
    body = r.json()
    attrs = body["point_buy_attributes"]
    assert len(attrs) >= 60, f"expected ≥60 canonical attributes, got {len(attrs)}"

    # Spot-check signature attributes from the Anime 5E core book.
    by_name = {a["name"]: a for a in attrs}
    for required in [
        "AC Bonus", "Combat Mastery", "Combat Technique",
        "Dynamic Powers", "Dynamic Powers – Lesser", "Edge",
        "Extra Actions", "Extra Actions – Lesser",
        "Item", "Companion", "Mulligan", "Pocket Dimension",
        "Telepathy", "Telepathy – Lesser",
        "Size Change", "Size Change – Lesser",
        "Massive Damage", "Massive Damage – Lesser",
        "Inspire", "Inspire – Greater", "Wealth",
    ]:
        assert required in by_name, f"missing canonical attribute {required}"

    # Every entry is well-formed.
    valid_cats = {
        "combat", "defensive", "mental", "physical", "social",
        "supernatural", "utility",
    }
    for a in attrs:
        assert isinstance(a["name"], str) and a["name"]
        assert isinstance(a["cost_per_level"], int)
        assert a["cost_per_level"] >= 1
        assert a["category"] in valid_cats, a
        assert "page" in a and isinstance(a["page"], int)


def test_anime5e_signature_attribute_costs_match_pdf():
    """Verify a handful of CP costs against the printed Anime 5E core
    book values (page 91 onwards)."""
    r = requests.get(f"{BASE_URL}/api/systems/anime-5e/reference")
    by_name = {a["name"]: a for a in r.json()["point_buy_attributes"]}
    canonical = {
        "AC Bonus": 1,
        "Combat Mastery": 1,
        "Companion": 5,
        "Dynamic Powers": 10,
        "Dynamic Powers – Lesser": 5,
        "Extra Actions": 4,
        "Extra Actions – Lesser": 2,
        "Item": 4,
        "Mind Control": 3,
        "Mind Control – Lesser": 1,
        "Mulligan": 1,
        "Regeneration": 1,
        "Size Change": 5,
        "Telepathy": 3,
        "Teleport": 5,
    }
    for name, cost in canonical.items():
        got = by_name[name]["cost_per_level"]
        assert got == cost, f"{name}: expected {cost} pts/lvl, got {got}"
