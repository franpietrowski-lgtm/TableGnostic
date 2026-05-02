"""V6.17 — Advancement + Spell tracker + Anime 5E reference seed tests."""
from __future__ import annotations

import asyncio
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "/app/backend")

from server import app  # noqa: E402
from core.db import db  # noqa: E402
from system_data.anime5e_reference_seed import SEED_ENTRIES  # noqa: E402
from routes.advancement import (  # noqa: E402
    _build_spell_tracker_state,
    _detect_advancement,
    _normalize_seed_to_reference,
)


client = TestClient(app)


# ─── Pure-function unit tests ────────────────────────────────────────────


def test_seed_has_at_least_50_entries():
    assert len(SEED_ENTRIES) >= 50
    # Every entry has the required schema keys.
    for e in SEED_ENTRIES:
        assert e.get("kind"), f"kind missing on {e}"
        assert e.get("name"), f"name missing on {e}"
        assert e.get("description"), f"description missing on {e['name']}"
        assert e.get("page_ref"), f"page_ref missing on {e['name']}"


def test_seed_normalizer_extracts_page_int():
    n = _normalize_seed_to_reference({
        "kind": "feat", "name": "Test Feat", "description": "Hi.",
        "page_ref": "Anime 5E SRD p.118 (test)",
        "fields": {"prereq": "—"}, "tags": ["feat"],
    })
    assert n["page"] == 118
    assert n["book"] == "anime-5e"
    assert n["kind"] == "feat"


def test_seed_normalizer_coerces_plural_kinds():
    n = _normalize_seed_to_reference({
        "kind": "weapons", "name": "Test Sword",
        "description": "x", "page_ref": "p.10"})
    assert n["kind"] == "weapon"
    n = _normalize_seed_to_reference({
        "kind": "items", "name": "Test Item",
        "description": "x", "page_ref": "p.20"})
    assert n["kind"] == "item"


def test_advancement_detects_dnd_asi_at_level_4():
    ch = {
        "id": "test1",
        "folio": {"dnd_state": {"class": "Wizard", "level": 4}},
    }
    camp = {"system_id": "dnd-5e"}
    out = _detect_advancement(ch, camp)
    ids = [p["id"] for p in out["pending"]]
    assert "asi-4" in ids
    # Wizard subclass at level 3 — pending if not chosen.
    assert "subclass-3" in ids


def test_advancement_detects_cypher_tier_benefits():
    ch = {
        "id": "test2",
        "folio": {"cypher_state": {"tier": 3, "tier_benefits_log": {
            "2": [{"key": "edge"}, {"key": "skill"}]
        }}},
    }
    camp = {"system_id": "cypher"}
    out = _detect_advancement(ch, camp)
    pending = out["pending"]
    # Tier 2 owes 4 - 2 = 2; Tier 3 owes 4.
    t2 = next((p for p in pending if p["id"] == "cypher-tier-2"), None)
    t3 = next((p for p in pending if p["id"] == "cypher-tier-3"), None)
    assert t2 and t2["extra"]["owed"] == 2
    assert t3 and t3["extra"]["owed"] == 4


def test_advancement_detects_anime5e_underspend():
    ch = {
        "id": "test3",
        "folio": {
            "dnd_state": {"class": "Bard", "level": 1},
            "anime5e_state": {"point_budget": 10, "point_buys": [
                {"name": "Tough", "cost_per_level": 2, "level": 1}
            ]},
        },
    }
    camp = {"system_id": "anime-5e"}
    out = _detect_advancement(ch, camp)
    ids = [p["id"] for p in out["pending"]]
    assert "anime5e-pointbuy-unspent" in ids


def test_advancement_no_dnd_asi_before_level_4():
    ch = {"id": "x", "folio": {"dnd_state": {"class": "Bard", "level": 3}}}
    camp = {"system_id": "dnd-5e"}
    out = _detect_advancement(ch, camp)
    ids = [p["id"] for p in out["pending"]]
    assert "asi-4" not in ids


def test_spell_tracker_full_caster_level_5_wizard():
    ch = {"id": "x", "folio": {"dnd_state": {"class": "Wizard", "level": 5}}}
    state = _build_spell_tracker_state(ch)
    levels = [s["slot_level"] for s in state["spell_slots"]]
    assert levels == [1, 2, 3]
    # Lv1 Wizard at 5 has 4/3/2 slots
    by_lvl = {s["slot_level"]: s for s in state["spell_slots"]}
    assert by_lvl[1]["max"] == 4
    assert by_lvl[2]["max"] == 3
    assert by_lvl[3]["max"] == 2


def test_spell_tracker_warlock_level_3():
    ch = {"id": "x", "folio": {"dnd_state": {"class": "Warlock", "level": 3}}}
    state = _build_spell_tracker_state(ch)
    assert state["warlock_short_rest"] is True
    # Level 3 Warlock = 2 slots at slot level 2.
    s = state["spell_slots"][0]
    assert s["max"] == 2 and s["slot_level"] == 2


def test_spell_tracker_used_slots_reduce_remaining():
    ch = {"id": "x", "folio": {"dnd_state": {
        "class": "Wizard", "level": 5,
        "slot_usage": {"1": 2, "2": 1},
    }}}
    state = _build_spell_tracker_state(ch)
    by_lvl = {s["slot_level"]: s for s in state["spell_slots"]}
    assert by_lvl[1]["remaining"] == 4 - 2
    assert by_lvl[2]["remaining"] == 3 - 1


def test_spell_tracker_includes_power_bundles():
    ch = {
        "id": "x",
        "folio": {"dnd_state": {"class": "Fighter", "level": 1}},
        "power_bundles": [
            {"name": "Beam Cannon", "invocation": "per-charge",
             "charges_max": 1, "charges_current": 1, "cost": 5},
            {"name": "No-charge bundle", "invocation": "per-scene",
             "charges_max": 0, "charges_current": 0, "cost": 0},
        ],
    }
    state = _build_spell_tracker_state(ch)
    names = [b["name"] for b in state["power_bundles"]]
    assert "Beam Cannon" in names
    # No-charge bundles are filtered out.
    assert "No-charge bundle" not in names
