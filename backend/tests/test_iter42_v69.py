"""V6.9 backend tests — Timeline markers + Companion seats."""
import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://rules-forge.preview.emergentagent.com",
).rstrip("/")

ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PASS = "PieGod08!!"


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
                      timeout=15)
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def campaigns(admin_headers):
    r = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    return r.json()


@pytest.fixture(scope="module")
def besm_campaign(campaigns):
    cands = [c for c in campaigns if c.get("system_id") == "besm-4e" and c.get("is_gm")]
    if not cands:
        pytest.skip("No GM-owned besm-4e campaign seeded")
    return cands[0]


# ─── Timeline markers ──────────────────────────────────────────────

class TestTimelineMarkers:
    def test_list_empty_or_array(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/timeline-markers",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_create_marker_full_lifecycle(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        # Find a session
        sess_r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                              headers=admin_headers, timeout=15)
        assert sess_r.status_code == 200
        sessions = sess_r.json()
        if not sessions:
            # Create one quickly
            cr = requests.post(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                               headers=admin_headers,
                               json={"name": "Test Session V6.9"},
                               timeout=15)
            assert cr.status_code in (200, 201), cr.text
            sid = cr.json()["id"]
        else:
            sid = sessions[0]["id"]
        # Find a node
        node_r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/nodes",
                              headers=admin_headers, timeout=15)
        assert node_r.status_code == 200
        nodes = node_r.json() or []
        node_id = nodes[0]["id"] if nodes else None

        # Create marker
        body = {
            "session_id": sid,
            "codex_node_id": node_id,
            "label": "V6.9 marker",
            "kind": "node",
            "color": "#C8A34A",
        }
        cr = requests.post(f"{BASE_URL}/api/campaigns/{cid}/timeline-markers",
                           headers=admin_headers, json=body, timeout=15)
        assert cr.status_code == 200, cr.text
        marker = cr.json()
        assert marker["session_id"] == sid
        assert marker["label"] == "V6.9 marker"
        assert marker["kind"] == "node"
        mid = marker["id"]

        # List should include it
        ls = requests.get(f"{BASE_URL}/api/campaigns/{cid}/timeline-markers",
                          headers=admin_headers, timeout=15).json()
        assert any(m["id"] == mid for m in ls)

        # Delete
        d = requests.delete(f"{BASE_URL}/api/campaigns/{cid}/timeline-markers/{mid}",
                            headers=admin_headers, timeout=15)
        assert d.status_code == 200, d.text

        # No longer present
        ls2 = requests.get(f"{BASE_URL}/api/campaigns/{cid}/timeline-markers",
                           headers=admin_headers, timeout=15).json()
        assert all(m["id"] != mid for m in ls2)

    def test_invalid_session_rejected(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        body = {
            "session_id": "fake-id-zzz",
            "codex_node_id": None,
            "label": "broken",
        }
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/timeline-markers",
                          headers=admin_headers, json=body, timeout=15)
        assert r.status_code == 400


# ─── Companion seats ──────────────────────────────────────────────

class TestCompanionSeats:
    def test_assign_revoke_companion(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        # Find a character we own
        chs_r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                             headers=admin_headers, timeout=15)
        assert chs_r.status_code == 200
        chs = chs_r.json()
        if not chs:
            pytest.skip("No characters in this campaign")
        ch = chs[0]
        ch_id = ch["id"]

        # Need another user to assign — use members listing
        members = requests.get(f"{BASE_URL}/api/campaigns/{cid}/members",
                               headers=admin_headers, timeout=15).json()
        owner_id = ch.get("owner_id")
        candidates = [m for m in members if m["id"] != owner_id]
        if not candidates:
            pytest.skip("No non-owner members to assign")
        target_id = candidates[0]["id"]

        # Assign
        a = requests.post(
            f"{BASE_URL}/api/characters/{ch_id}/companions?player_id={target_id}",
            headers=admin_headers, timeout=15)
        assert a.status_code == 200, a.text
        result = a.json()
        assert target_id in (result.get("companion_owners") or [])

        # Revoke
        r = requests.delete(
            f"{BASE_URL}/api/characters/{ch_id}/companions/{target_id}",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        result = r.json()
        assert target_id not in (result.get("companion_owners") or [])

    def test_cannot_assign_owner_as_companion(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        chs = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                           headers=admin_headers, timeout=15).json()
        if not chs:
            pytest.skip("No characters")
        ch = chs[0]
        owner_id = ch.get("owner_id")
        if not owner_id:
            pytest.skip("Character has no owner")
        r = requests.post(
            f"{BASE_URL}/api/characters/{ch['id']}/companions?player_id={owner_id}",
            headers=admin_headers, timeout=15)
        assert r.status_code == 400, r.text
