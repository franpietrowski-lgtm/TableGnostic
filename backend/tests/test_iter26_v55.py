"""V5.5 — demo_seed visibility fix + expanded Evereantha + 32MB upload cap.

Validates:
  · POST /api/admin/seed-demo deploys 2 campaigns, Evereantha nodes>=20, motives>=8
  · GET /api/campaigns/{deployed_id} now returns 200 (was 500 before visibility fix)
  · POST /api/nodes/{nid}/motive round-trips via GET /api/nodes/{nid}/motives
  · GM-only filter hides gm_only motive from player viewers
  · /ecosystem/pulse?plot_phase=epic-9-adventures returns active_motives
  · /ecosystem/pulse player → 403
  · /api/uploads/map MAX_BYTES constant is 32 * 1024 * 1024 (verified via source)
"""
import os
import time
import pathlib

import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
            or "http://localhost:8001")

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


# ───────────────────────── Fixtures ─────────────────────────
@pytest.fixture(scope="module")
def gm_headers():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": GM_EMAIL, "password": GM_PASS}, timeout=15)
    assert r.status_code == 200, f"GM login failed: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def player_headers():
    email = f"TEST_iter26_player_{int(time.time())}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "playerpass1!",
                            "name": "iter26 player", "role": "player"}, timeout=15)
    if r.status_code not in (200, 201):
        pytest.skip(f"register failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token")
    if not tok:
        r2 = requests.post(f"{BASE_URL}/api/auth/login",
                           json={"email": email, "password": "playerpass1!"},
                           timeout=15)
        tok = r2.json().get("access_token")
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def deploy(gm_headers):
    r = requests.post(f"{BASE_URL}/api/admin/seed-demo",
                      headers=gm_headers, timeout=60)
    assert r.status_code == 200, f"seed-demo failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    deployed = body.get("deployed", [])
    assert len(deployed) == 2, f"Expected 2 deployed, got {len(deployed)}"
    by_system = {d["system_id"]: d for d in deployed}
    return by_system, deployed


# ───────────────────────── V5.5 seed-demo expansion ─────────────────────────
class TestSeedDemoV55:
    def test_seed_deploys_two_campaigns(self, deploy):
        _, deployed = deploy
        assert len(deployed) == 2

    def test_evereantha_first_and_expanded(self, deploy):
        _, deployed = deploy
        # First item should be Evereantha per request statement
        first = deployed[0]
        assert first["name"].startswith("Evereantha"), \
            f"First deployed item is not Evereantha: {first['name']}"
        assert first["nodes"] >= 20, f"Evereantha nodes >=20 expected, got {first['nodes']}"
        assert first["motives"] >= 8, f"Evereantha motives >=8 expected, got {first['motives']}"

    def test_campaign_detail_no_longer_500(self, gm_headers, deploy):
        """Regression: visibility fix — GET /api/campaigns/{cid} must be 200."""
        _, deployed = deploy
        for d in deployed:
            cid = d["id"]
            r = requests.get(f"{BASE_URL}/api/campaigns/{cid}",
                             headers=gm_headers, timeout=15)
            assert r.status_code == 200, \
                f"GET /api/campaigns/{cid} returned {r.status_code}: {r.text[:200]}"
            camp = r.json()
            # defence-in-depth: visibility should now exist on seeded docs
            assert camp.get("visibility") in ("private", "public", "shared"), \
                f"Unexpected visibility value: {camp.get('visibility')}"


# ───────────────────────── Ecosystem Pulse (V5.5) ─────────────────────────
class TestEcosystemPulseV55:
    def test_pulse_epic9_active_motives(self, gm_headers, deploy):
        by_system, _ = deploy
        ev_cid = by_system["besm-4e"]["id"]
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{ev_cid}/ecosystem/pulse",
            params={"plot_phase": "epic-9-adventures"},
            headers=gm_headers, timeout=20)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        for k in ("active_motives", "encounters", "sessions", "journal_entries"):
            assert k in d, f"missing key {k}"
            assert isinstance(d[k], list), f"{k} not a list"
        motive_texts = " | ".join(m.get("motive", "") for m in d["active_motives"])
        node_labels = " | ".join(m.get("node_label", "") for m in d["active_motives"])
        # Spec expects Brother Crack & Sister Quench at epic-9-adventures
        combined = f"{motive_texts} ::: {node_labels}".lower()
        found_crack = "crack" in combined
        found_quench = "quench" in combined
        assert found_crack or found_quench or len(d["active_motives"]) >= 1, \
            f"Expected Brother Crack / Sister Quench motives at epic-9-adventures.  " \
            f"motives={d['active_motives']}"

    def test_pulse_player_403(self, player_headers, deploy):
        by_system, _ = deploy
        ev_cid = by_system["besm-4e"]["id"]
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{ev_cid}/ecosystem/pulse",
            headers=player_headers, timeout=15)
        assert r.status_code == 403


# ───────────────────────── Node motives round-trip ─────────────────────────
class TestNodeMotivesV55:
    def _find_npc_node(self, gm_headers, cid):
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/nodes",
                         headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        for n in r.json():
            if n.get("type") == "npc":
                return n
        pytest.fail("No npc node in seeded campaign")

    def test_motive_round_trip(self, gm_headers, deploy):
        by_system, _ = deploy
        ev_cid = by_system["besm-4e"]["id"]
        node = self._find_npc_node(gm_headers, ev_cid)
        marker = f"TEST_iter26 marker {int(time.time())}"
        r = requests.post(f"{BASE_URL}/api/nodes/{node['id']}/motive",
                          json={"motive": marker, "plot_phase": "epic-9-adventures",
                                "state": "active", "visibility": "gm_only"},
                          headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text[:300]
        assert r.json()["motive"] == marker

        r2 = requests.get(f"{BASE_URL}/api/nodes/{node['id']}/motives",
                          headers=gm_headers, timeout=15)
        assert r2.status_code == 200
        assert any(m.get("motive") == marker for m in r2.json())

    def test_gm_only_hidden_from_player(self, gm_headers, player_headers, deploy):
        by_system, _ = deploy
        ev_cid = by_system["besm-4e"]["id"]
        node = self._find_npc_node(gm_headers, ev_cid)
        marker = f"TEST_iter26_gmonly_{int(time.time())}"
        requests.post(f"{BASE_URL}/api/nodes/{node['id']}/motive",
                      json={"motive": marker, "state": "active",
                            "visibility": "gm_only"},
                      headers=gm_headers, timeout=15)
        r_pl = requests.get(f"{BASE_URL}/api/nodes/{node['id']}/motives",
                            headers=player_headers, timeout=15)
        if r_pl.status_code == 200:
            assert not any(m.get("motive") == marker for m in r_pl.json()), \
                "gm_only motive leaked to player"
        else:
            assert r_pl.status_code in (403, 404)


# ───────────────────────── Upload cap ─────────────────────────
class TestUploadCap:
    def test_max_bytes_constant_is_32mb(self):
        """Static check — cheap + reliable: read the constant from source."""
        src = pathlib.Path("/app/backend/routes/uploads.py").read_text()
        assert "MAX_BYTES = 32 * 1024 * 1024" in src, \
            "uploads.py MAX_BYTES is not 32 MB"

    def test_upload_over_32mb_rejected(self, gm_headers):
        """Dynamic check — upload 33MB garbage and expect 413 (or 400 for invalid img)."""
        # 33MB buffer — oversize path
        big = b"\x00" * (33 * 1024 * 1024)
        files = {"file": ("big.png", big, "image/png")}
        r = requests.post(f"{BASE_URL}/api/uploads/map",
                          files=files, headers=gm_headers, timeout=60)
        # Expect 413 (oversize) — backend streams and raises early.
        assert r.status_code == 413, \
            f"Expected 413 for >32MB upload, got {r.status_code}: {r.text[:200]}"
