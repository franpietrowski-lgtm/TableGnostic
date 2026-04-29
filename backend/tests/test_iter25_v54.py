"""V5.4 — Living Ecosystem backend tests.

Exercises:
  · POST /api/admin/seed-demo (GM/admin gated; deploys Evereantha + Artisan's Tale)
  · GET  /api/campaigns/{cid}/ecosystem/pulse?plot_phase=X (GM-only)
  · POST /api/nodes/{nid}/motive  +  GET /api/nodes/{nid}/motives (gm_only filter)
  · Player → 403 on /ecosystem/pulse
  · Player role gets 403 from /admin/seed-demo
"""
import os
import time

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
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def player_headers():
    email = f"TEST_iter25_player_{int(time.time())}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "playerpass1!",
                            "name": "iter25 player", "role": "player"}, timeout=15)
    if r.status_code not in (200, 201):
        pytest.skip(f"Could not register test player: {r.status_code} {r.text}")
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
    assert "besm-4e" in by_system and "cypher" in by_system, \
        f"Missing systems: {list(by_system.keys())}"
    return by_system


# ───────────────────────── seed-demo ─────────────────────────
class TestSeedDemo:
    def test_seed_demo_returns_two_campaigns(self, deploy):
        ev = deploy["besm-4e"]
        ar = deploy["cypher"]
        # Validate Evereantha shape
        assert ev["name"].startswith("Evereantha")
        assert ev["nodes"] >= 5
        assert ev["motives"] >= 1
        assert ev["milestones"] >= 1
        assert ev["encounter"] == "Pass-of-Aurea Ambush"
        # Validate Artisan's Tale shape
        assert ar["name"].startswith("Artisan")
        assert ar["nodes"] >= 5
        assert ar["motives"] >= 1
        assert ar["milestones"] >= 1
        assert ar["encounter"]  # any name OK

    def test_seed_demo_player_403(self, player_headers):
        r = requests.post(f"{BASE_URL}/api/admin/seed-demo",
                          headers=player_headers, timeout=30)
        assert r.status_code == 403, f"Expected 403 for player, got {r.status_code}"


# ───────────────────────── Pulse ─────────────────────────
class TestEcosystemPulse:
    def test_pulse_evereantha_phase_filter(self, gm_headers, deploy):
        ev_cid = deploy["besm-4e"]["id"]
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{ev_cid}/ecosystem/pulse",
            params={"plot_phase": "epic-7-milestones"},
            headers=gm_headers, timeout=20)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        # Required keys
        for k in ("active_motives", "encounters", "sessions", "journal_entries"):
            assert k in d, f"Missing key {k}"
            assert isinstance(d[k], list)
        # Malshe Darkening's evolving motive at this phase
        motive_texts = " | ".join(m.get("motive", "") for m in d["active_motives"])
        assert "Forge-Glass Hammer" in motive_texts or "Malshe" in (
            " | ".join(m.get("node_label", "") for m in d["active_motives"])), \
            f"Expected Malshe Darkening evolving motive; got: {d['active_motives']}"
        # Encounter at epic-7-milestones
        names = [e.get("name") for e in d["encounters"]]
        assert "Pass-of-Aurea Ambush" in names, \
            f"Expected Pass-of-Aurea Ambush in encounters: {names}"

    def test_pulse_player_403(self, player_headers, deploy):
        ev_cid = deploy["besm-4e"]["id"]
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{ev_cid}/ecosystem/pulse",
            headers=player_headers, timeout=15)
        assert r.status_code == 403, f"Expected 403 for player, got {r.status_code}"


# ───────────────────────── Node motives round-trip ─────────────────────────
class TestNodeMotives:
    def _find_npc_node(self, gm_headers, cid):
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/nodes",
                         headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        for n in r.json():
            if n.get("type") == "npc":
                return n
        pytest.fail("No npc node found in seeded campaign")

    def test_post_motive_and_get_roundtrip(self, gm_headers, deploy):
        ev_cid = deploy["besm-4e"]["id"]
        node = self._find_npc_node(gm_headers, ev_cid)
        nid = node["id"]
        body = {
            "motive": "TEST_iter25 — chase the apprentices through the pass.",
            "plot_phase": "epic-7-milestones",
            "state": "active",
            "visibility": "gm_only",
        }
        r = requests.post(f"{BASE_URL}/api/nodes/{nid}/motive",
                          json=body, headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text[:300]
        created = r.json()
        assert created["motive"] == body["motive"]
        assert created["state"] == "active"
        assert created["visibility"] == "gm_only"
        assert "id" in created

        # GET as GM should see the new entry
        r2 = requests.get(f"{BASE_URL}/api/nodes/{nid}/motives",
                          headers=gm_headers, timeout=15)
        assert r2.status_code == 200
        gm_list = r2.json()
        assert any(m.get("motive") == body["motive"] for m in gm_list), \
            "Newly-posted motive not returned to GM"

    def test_gm_only_motive_hidden_from_player(self, gm_headers, player_headers,
                                                deploy):
        """Verify visibility=gm_only entries are filtered out for players."""
        ev_cid = deploy["besm-4e"]["id"]
        node = self._find_npc_node(gm_headers, ev_cid)
        nid = node["id"]
        # Post a gm_only entry (already done in previous test, but be explicit)
        marker = f"TEST_iter25_gmonly_{int(time.time())}"
        requests.post(f"{BASE_URL}/api/nodes/{nid}/motive",
                      json={"motive": marker, "state": "active",
                            "visibility": "gm_only"},
                      headers=gm_headers, timeout=15)
        # GM sees it
        r_gm = requests.get(f"{BASE_URL}/api/nodes/{nid}/motives",
                            headers=gm_headers, timeout=15)
        assert r_gm.status_code == 200
        assert any(m.get("motive") == marker for m in r_gm.json())

        # Player request — endpoint requires the player to at least be able to
        # see the node. The node belongs to a campaign they're not in; the
        # endpoint returns 404 (node permission) OR 200 with empty list.
        r_pl = requests.get(f"{BASE_URL}/api/nodes/{nid}/motives",
                            headers=player_headers, timeout=15)
        # Either denied access entirely OR allowed but stripped
        if r_pl.status_code == 200:
            assert not any(m.get("motive") == marker for m in r_pl.json()), \
                "gm_only motive leaked to player viewer"
        else:
            assert r_pl.status_code in (403, 404), \
                f"Unexpected status for player on motives: {r_pl.status_code}"

    def test_post_motive_player_forbidden(self, player_headers, gm_headers,
                                           deploy):
        ev_cid = deploy["besm-4e"]["id"]
        node = self._find_npc_node(gm_headers, ev_cid)
        nid = node["id"]
        r = requests.post(f"{BASE_URL}/api/nodes/{nid}/motive",
                          json={"motive": "TEST_iter25_player_attempt",
                                "state": "active", "visibility": "gm_only"},
                          headers=player_headers, timeout=15)
        assert r.status_code in (403, 404), \
            f"Expected 403/404 for player posting motive, got {r.status_code}"
