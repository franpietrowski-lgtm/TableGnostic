"""V4.4 Phase A+B / Iteration 16 backend tests.

Coverage:
  - XP system:
    * GET /api/sessions/{sid}/xp/suggest (admin 200, structure, weights, rows)
    * GET /api/sessions/{sid}/xp/suggest as non-GM → 403
    * POST /api/sessions/{sid}/xp/commit persists xp_log + xp_total/xp_unspent
    * POST /api/characters/{cid}/xp with negative amount (correction)
    * POST /api/characters/{cid}/xp/convert reduces xp_unspent + raises total_points
    * convert with amount > unspent → 400

  - Atelier system:
    * GET /api/atelier/{cid} (admin GM full doc)
    * GET /api/atelier/{cid} as player → safety subset only with player_view:true
    * PUT /api/atelier/{cid} upserts session_zero + arcs + beats
    * POST /api/atelier/{cid}/continuity → finds missing_node when arc
      references a non-existent NPC ('NobodyWhoExists')
    * Non-GM cannot PUT or run continuity → 403
"""
from __future__ import annotations

import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://rules-forge.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PW = "PieGod08!!"


# ---------- module-scoped fixtures ----------

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def reset_payload(admin_token):
    """Destructive reset once per module run."""
    r = requests.post(
        f"{BASE_URL}/api/admin/reset-to-evereantha?confirm=WIPE",
        headers={"Authorization": f"Bearer {admin_token}"}, timeout=90,
    )
    assert r.status_code == 200, f"reset failed: {r.status_code} {r.text[:400]}"
    return r.json()


@pytest.fixture(scope="module")
def campaign_id(reset_payload):
    return reset_payload["campaign"]["id"]


@pytest.fixture(scope="module")
def session_ids(campaign_id, admin_headers):
    r = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/sessions",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200
    sessions = sorted(r.json(), key=lambda s: s.get("created_at", ""))
    assert len(sessions) >= 6, f"expected >=6 sessions got {len(sessions)}"
    return [s["id"] for s in sessions]


@pytest.fixture(scope="module")
def session6_id(session_ids):
    # Index 5 = Session 6
    return session_ids[5]


@pytest.fixture(scope="module")
def characters(campaign_id, admin_headers):
    r = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/characters",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    chars = r.json()
    assert len(chars) >= 3, f"expected 3 PCs got {len(chars)}"
    return chars


@pytest.fixture(scope="module")
def player_token():
    suffix = str(int(time.time()))[-6:]
    email = f"t16pl_{suffix}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "password": "playerpw1",
        "name": f"P16-{suffix}", "role": "player",
    }, timeout=15)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    if "access_token" in body:
        return body["access_token"]
    r2 = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": email, "password": "playerpw1"}, timeout=15)
    assert r2.status_code == 200
    return r2.json()["access_token"]


# ============================================================
# XP — engagement scorecard suggest
# ============================================================

class TestXPSuggest:

    def test_suggest_admin_returns_structure(self, session6_id, admin_headers):
        r = requests.get(f"{BASE_URL}/api/sessions/{session6_id}/xp/suggest",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["default_baseline"] == 2
        assert data["bonus_cap"] == 2
        w = data["weights"]
        # IC chat weighted higher than OOC (user choice)
        assert w["chat_ic"] == 0.05
        assert w["chat_ooc"] == 0.01
        assert w["dice_macro"] == 0.10
        assert w["journal"] == 0.25
        assert w["spotlight"] == 0.50
        rows = data["rows"]
        assert len(rows) >= 1, f"expected at least 1 PC row, got {len(rows)}"
        for row in rows:
            assert "character_id" in row and "character_name" in row
            assert "counts" in row
            for k in ("chat_ic", "chat_ooc", "dice_macro", "journal", "spotlight"):
                assert k in row["counts"]
            assert "suggested_base" in row and "suggested_total" in row
            assert row["suggested_base"] == 2

    def test_suggest_player_403(self, session6_id, player_token):
        r = requests.get(f"{BASE_URL}/api/sessions/{session6_id}/xp/suggest",
                         headers={"Authorization": f"Bearer {player_token}"}, timeout=15)
        assert r.status_code == 403, f"player should get 403, got {r.status_code}"


# ============================================================
# XP — commit + per-character award + convert
# ============================================================

class TestXPCommitAndConvert:

    def test_commit_persists_xp(self, session6_id, characters, admin_headers):
        # Build awards list — base 2 + bonus 0.5 spotlight on first PC
        awards = []
        for i, ch in enumerate(characters[:3]):
            awards.append({
                "character_id": ch["id"],
                "base": 2,
                "bonus": 0.5 if i == 0 else 0,
                "note": f"iter16-test-commit-{i}",
            })
        r = requests.post(f"{BASE_URL}/api/sessions/{session6_id}/xp/commit",
                          headers=admin_headers,
                          json={"awards": awards}, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        committed = body["committed"]
        assert len(committed) == 3
        # Verify GET /characters/{cid} reflects xp_total/xp_unspent
        first_cid = characters[0]["id"]
        gr = requests.get(f"{BASE_URL}/api/characters/{first_cid}/xp",
                          headers=admin_headers, timeout=15)
        assert gr.status_code == 200
        d = gr.json()
        assert d["xp_total"] >= 2.5, f"expected xp_total >= 2.5, got {d['xp_total']}"
        assert d["xp_unspent"] >= 2.5
        # xp_log entry exists
        entries = [e for e in d["xp_log"] if e.get("session_id") == session6_id]
        assert entries, "expected at least one xp_log entry for the session"
        e0 = entries[-1]
        assert e0.get("source") == "session_baseline"
        assert e0.get("base") == 2.0 or e0.get("base") == 2
        assert abs(e0.get("amount") - 2.5) < 0.01

    def test_negative_award_correction(self, characters, admin_headers):
        cid = characters[1]["id"]
        # Get current
        cur = requests.get(f"{BASE_URL}/api/characters/{cid}/xp",
                           headers=admin_headers, timeout=15).json()
        before = cur["xp_total"]
        r = requests.post(f"{BASE_URL}/api/characters/{cid}/xp",
                          headers=admin_headers,
                          json={"amount": -0.5, "reason": "iter16 correction",
                                "source": "correction"}, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert abs(body["xp_total"] - (before - 0.5)) < 0.01

    def test_convert_reduces_unspent_and_raises_total_points(self, characters, admin_headers):
        cid = characters[0]["id"]
        # Snapshot character before
        ch_before = requests.get(f"{BASE_URL}/api/characters/{cid}",
                                 headers=admin_headers, timeout=15).json()
        tp_before = int(ch_before.get("total_points", 120))
        xp_before = requests.get(f"{BASE_URL}/api/characters/{cid}/xp",
                                 headers=admin_headers, timeout=15).json()
        unspent_before = float(xp_before["xp_unspent"])
        assert unspent_before >= 2.0, f"need >=2 unspent for convert; got {unspent_before}"
        r = requests.post(f"{BASE_URL}/api/characters/{cid}/xp/convert",
                          headers=admin_headers,
                          json={"amount": 2, "reason": "iter16 convert"}, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["total_points"] == tp_before + 2
        assert abs(body["xp_unspent"] - (unspent_before - 2)) < 0.01

    def test_convert_over_unspent_400(self, characters, admin_headers):
        cid = characters[2]["id"]
        # Try to convert 999 — should fail
        r = requests.post(f"{BASE_URL}/api/characters/{cid}/xp/convert",
                          headers=admin_headers,
                          json={"amount": 99, "reason": "should fail"}, timeout=15)
        assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text}"


# ============================================================
# Atelier — GET / PUT / continuity
# ============================================================

class TestAtelier:

    def test_get_atelier_admin_default(self, campaign_id, admin_headers):
        r = requests.get(f"{BASE_URL}/api/atelier/{campaign_id}",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["campaign_id"] == campaign_id
        assert "session_zero" in d
        assert isinstance(d.get("arcs", []), list)

    def test_put_atelier_upserts_arcs(self, campaign_id, admin_headers):
        body = {
            "session_zero": {
                "table_contract": "Show up on time, IC always.",
                "lines": ["graphic torture"],
                "veils": ["romance fade-to-black"],
                "safety_tools": ["X-card"],
                "schedule": "Saturdays 7pm",
                "character_integration": "Each PC has ties to Aurea.",
                "recurring_themes": ["faith vs reason"],
                "expectations": "Heroic but consequential",
                "completed": True,
            },
            "arcs": [
                {
                    "title": "Arc 1: The Mayor's Note",
                    "sequence": 1,
                    "summary": "Roney decodes a desperate message.",
                    "expected_sessions": 3,
                    "status": "active",
                    "beats": [
                        {"title": "Hook: Arrival of the messenger", "kind": "hook", "note": ""},
                        {"title": "Turn: Identity revealed", "kind": "turn", "note": ""},
                    ],
                    "referenced_npcs": ["NobodyWhoExists"],   # missing_node trigger
                    "referenced_locations": [],
                    "contradictions_with_master_plot": [],
                }
            ],
        }
        r = requests.put(f"{BASE_URL}/api/atelier/{campaign_id}",
                         headers=admin_headers, json=body, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert len(d["arcs"]) == 1
        arc = d["arcs"][0]
        assert arc["title"].startswith("Arc 1")
        assert "id" in arc, "arc should be stamped with id"
        assert len(arc["beats"]) == 2
        assert all("id" in b for b in arc["beats"])
        assert d["session_zero"]["completed"] is True

    def test_continuity_finds_missing_node(self, campaign_id, admin_headers):
        r = requests.post(f"{BASE_URL}/api/atelier/{campaign_id}/continuity",
                          headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        findings = d["findings"]
        missing = [f for f in findings if f["kind"] == "missing_node"]
        assert any(f.get("missing") == "NobodyWhoExists" for f in missing), \
            f"expected missing_node finding for NobodyWhoExists, got {findings}"

    def test_player_view_returns_safety_subset_only(self, campaign_id, player_token):
        r = requests.get(f"{BASE_URL}/api/atelier/{campaign_id}",
                         headers={"Authorization": f"Bearer {player_token}"}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("player_view") is True
        sz = d.get("session_zero", {})
        # Safety subset keys present
        for k in ("lines", "veils", "safety_tools", "schedule", "table_contract"):
            assert k in sz, f"missing {k} in player view"
        # Should NOT expose arcs or expectations or completed flag
        assert "arcs" not in d, "player view leaked arcs"
        assert "expectations" not in sz, "player view leaked expectations"
        assert "character_integration" not in sz, "player view leaked character_integration"

    def test_player_cannot_put_atelier(self, campaign_id, player_token):
        r = requests.put(f"{BASE_URL}/api/atelier/{campaign_id}",
                         headers={"Authorization": f"Bearer {player_token}",
                                  "Content-Type": "application/json"},
                         json={"session_zero": {}, "arcs": []}, timeout=15)
        assert r.status_code == 403, f"expected 403, got {r.status_code}"

    def test_player_cannot_run_continuity(self, campaign_id, player_token):
        r = requests.post(f"{BASE_URL}/api/atelier/{campaign_id}/continuity",
                          headers={"Authorization": f"Bearer {player_token}"}, timeout=15)
        assert r.status_code == 403
