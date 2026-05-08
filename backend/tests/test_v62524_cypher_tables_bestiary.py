"""V6.25.24 — Cycle B-5 + B-6: Cypher random-table + bestiary endpoints."""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


# ── B-5: random-table ──────────────────────────────────────────────


def test_random_cypher_returns_full_payload():
    r = requests.get(f"{BASE_URL}/api/cypher/random-table",
                       params={"kind": "cypher"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["kind"] == "cypher"
    assert "entry" in body and body["entry"].get("name")
    roll = body.get("roll", {})
    assert 1 <= roll.get("result", 0) <= 6
    assert roll.get("level") == roll["result"] + roll["printed_modifier"] + roll.get("extra_modifier", 0)
    # Cyphers are one-shot — charges defaults to 1.
    assert body.get("charges") == 1


def test_random_artifact_carries_depletion():
    r = requests.get(f"{BASE_URL}/api/cypher/random-table",
                       params={"kind": "artifact"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["kind"] == "artifact"
    # Artifacts ship with `depletion` (mostly).
    assert "depletion" in body  # may be None or "—"


def test_random_table_rejects_bad_kind():
    r = requests.get(f"{BASE_URL}/api/cypher/random-table",
                       params={"kind": "bogus"})
    assert r.status_code == 422, r.text


def test_random_with_level_modifier_shifts_result():
    r = requests.get(f"{BASE_URL}/api/cypher/random-table",
                       params={"kind": "cypher", "level_modifier": 5})
    assert r.status_code == 200
    body = r.json()
    roll = body["roll"]
    # level = die + printed + extra_modifier(5)
    assert roll["level"] == roll["result"] + roll["printed_modifier"] + 5


# ── B-6: bestiary ──────────────────────────────────────────────────


def test_bestiary_full_listing():
    r = requests.get(f"{BASE_URL}/api/cypher/bestiary")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 12, body
    rows = body["rows"]
    # All rows have the canonical keys.
    for row in rows:
        for k in ("id", "name", "level", "health", "damage", "armor", "role", "genres"):
            assert k in row, f"missing {k} in {row.get('name')}"
        assert 1 <= row["level"] <= 10


def test_bestiary_genre_filter():
    r = requests.get(f"{BASE_URL}/api/cypher/bestiary",
                       params={"genre": "horror"})
    assert r.status_code == 200, r.text
    rows = r.json()["rows"]
    assert len(rows) >= 1
    for row in rows:
        # Every returned creature must tag horror (or "any").
        assert "horror" in row["genres"] or "any" in row["genres"]


def test_bestiary_level_band():
    r = requests.get(f"{BASE_URL}/api/cypher/bestiary",
                       params={"level_min": 5, "level_max": 7})
    assert r.status_code == 200, r.text
    rows = r.json()["rows"]
    for row in rows:
        assert 5 <= row["level"] <= 7


def test_reference_payload_includes_bestiary():
    r = requests.get(f"{BASE_URL}/api/systems/cypher/reference")
    assert r.status_code == 200
    body = r.json()
    assert "bestiary" in body
    assert len(body["bestiary"]) >= 12
