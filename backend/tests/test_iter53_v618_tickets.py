"""V6.18 — Level-Up Ticket workflow + subclass option enrichment tests."""
from __future__ import annotations

import sys
sys.path.insert(0, "/app/backend")

from routes.advancement import (  # noqa: E402
    SUBCLASS_OPTIONS,
    _commit_advancement,
    _detect_advancement,
    _resolve_subclass_options,
    _validate_ticket_compliance,
)


def test_subclass_options_strips_parentheticals():
    # "Artificer (Alchemist)" should look up Artificer.
    opts = _resolve_subclass_options("Artificer (Alchemist)")
    assert any(o["key"] == "Alchemist" for o in opts)
    assert any(o["key"] == "Battle Smith" for o in opts)


def test_subclass_options_unknown_class_returns_empty():
    assert _resolve_subclass_options("Imaginary Class") == []


def test_subclass_options_anime5e_classes_present():
    for cls in ["Adept", "Champion", "Idol", "Pilot", "Tinker"]:
        opts = SUBCLASS_OPTIONS[cls]
        assert len(opts) >= 2
        for o in opts:
            assert o.get("key") and o.get("blurb")


def test_advancement_subclass_step_carries_options():
    ch = {"id": "x", "folio": {"dnd_state": {
        "class": "Wizard", "level": 5
    }}}
    camp = {"system_id": "dnd-5e"}
    out = _detect_advancement(ch, camp)
    sub = next(p for p in out["pending"] if p["id"].startswith("subclass-"))
    keys = [o["key"] for o in sub["options"]]
    assert "School of Evocation" in keys
    assert all("blurb" in o for o in sub["options"])


def test_commit_advancement_asi_2_charisma():
    folio = {"dnd_state": {"class": "Bard", "level": 4,
                            "ability_scores": {"Charisma": 14}}}
    new = _commit_advancement(folio, "asi-4", "asi_2", {"ability": "Charisma"})
    assert new["dnd_state"]["ability_scores"]["Charisma"] == 16
    log = new["dnd_state"]["advancement_log"]
    assert log[-1]["id"] == "asi-4"


def test_commit_advancement_subclass_writes_field():
    folio = {"dnd_state": {"class": "Wizard", "level": 3}}
    new = _commit_advancement(folio, "subclass-3", "School of Evocation", {})
    assert new["dnd_state"]["subclass"] == "School of Evocation"


def test_compliance_blocks_asi_when_under_level():
    ch = {"folio": {"dnd_state": {"class": "Bard", "level": 3}}}
    camp = {"system_id": "dnd-5e"}
    ticket = {"advancement_id": "asi-4", "cp_cost": 0}
    r = _validate_ticket_compliance(ch, camp, ticket)
    assert not r["passes"]
    assert any("level" in i.lower() for i in r["issues"])


def test_compliance_passes_asi_when_at_level():
    ch = {"folio": {"dnd_state": {"class": "Bard", "level": 4}}}
    camp = {"system_id": "dnd-5e"}
    ticket = {"advancement_id": "asi-4", "cp_cost": 0}
    r = _validate_ticket_compliance(ch, camp, ticket)
    assert r["passes"]


def test_compliance_blocks_anime5e_overspend():
    ch = {"folio": {
        "dnd_state": {"class": "Idol", "level": 5},
        "anime5e_state": {"point_budget": 10, "point_buys": [
            {"name": "Tough", "cost_per_level": 2, "level": 4}
        ]},
    }}
    camp = {"system_id": "anime-5e"}
    # 8 spent + 5 cost = 13 > 10 budget
    ticket = {"advancement_id": "asi-4", "cp_cost": 5}
    r = _validate_ticket_compliance(ch, camp, ticket)
    assert not r["passes"]
    assert any("over" in i.lower() for i in r["issues"])


def test_compliance_blocks_duplicate_subclass():
    ch = {"folio": {"dnd_state": {
        "class": "Wizard", "level": 5, "subclass": "School of Evocation"
    }}}
    camp = {"system_id": "dnd-5e"}
    ticket = {"advancement_id": "subclass-3", "cp_cost": 0}
    r = _validate_ticket_compliance(ch, camp, ticket)
    assert not r["passes"]
    assert any("subclass" in i.lower() for i in r["issues"])
