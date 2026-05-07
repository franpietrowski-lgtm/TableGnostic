"""V6.9 extended tests — companion seat with real 2nd user + battlemap move-token rights."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://campaign-hub-288.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PASS = "PieGod08!!"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin_headers():
    return _login(ADMIN_EMAIL, ADMIN_PASS)


@pytest.fixture(scope="module")
def player_account():
    """Register a fresh test player + return (headers, user_id)."""
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_companion_{suffix}@example.com"
    pw = "TestPass123!"
    rr = requests.post(f"{BASE_URL}/api/auth/register",
                       json={"email": email, "password": pw,
                             "name": f"CompTest{suffix}", "role": "player"},
                       timeout=15)
    assert rr.status_code in (200, 201), rr.text
    headers = _login(email, pw)
    me = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=15).json()
    return headers, me["id"]


@pytest.fixture(scope="module")
def besm_campaign(admin_headers):
    r = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers, timeout=15)
    cands = [c for c in r.json() if c.get("system_id") == "besm-4e" and c.get("is_gm")]
    if not cands:
        pytest.skip("No GM-owned besm-4e campaign")
    return cands[0]


@pytest.fixture(scope="module")
def joined_player(besm_campaign, admin_headers, player_account):
    """Add player to campaign via invite-accept. Returns (headers, player_id)."""
    cid = besm_campaign["id"]
    headers, pid = player_account
    # Get invite token (admin)
    detail = requests.get(f"{BASE_URL}/api/campaigns/{cid}",
                          headers=admin_headers, timeout=15).json()
    token = detail.get("invite_token")
    if not token:
        # Try to surface via separate route
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/join",
                          headers=headers, json={}, timeout=15)
        assert r.status_code in (200, 400), r.text
    else:
        r = requests.post(f"{BASE_URL}/api/invites/{token}/accept",
                          headers=headers, timeout=15)
        assert r.status_code == 200, r.text
    return headers, pid


class TestCompanionFull:
    def test_assign_companion_to_real_member(self, admin_headers, besm_campaign, joined_player):
        cid = besm_campaign["id"]
        player_headers, pid = joined_player
        chs = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                           headers=admin_headers, timeout=15).json()
        if not chs:
            pytest.skip("No characters")
        # Pick a character not owned by this player
        ch = next((c for c in chs if c.get("owner_id") != pid), None)
        if not ch:
            pytest.skip("No suitable character")
        ch_id = ch["id"]
        # Assign
        a = requests.post(
            f"{BASE_URL}/api/characters/{ch_id}/companions?player_id={pid}",
            headers=admin_headers, timeout=15)
        assert a.status_code == 200, a.text
        result = a.json()
        assert pid in (result.get("companion_owners") or [])

        # Verify via GET that it persisted
        ch_get = requests.get(f"{BASE_URL}/api/characters/{ch_id}",
                              headers=admin_headers, timeout=15).json()
        assert pid in (ch_get.get("companion_owners") or [])

        # Revoke
        d = requests.delete(
            f"{BASE_URL}/api/characters/{ch_id}/companions/{pid}",
            headers=admin_headers, timeout=15)
        assert d.status_code == 200, d.text
        result = d.json()
        assert pid not in (result.get("companion_owners") or [])

    def test_companion_can_move_token_on_battlemap(self, admin_headers, besm_campaign, joined_player):
        cid = besm_campaign["id"]
        player_headers, pid = joined_player
        # Get/create a session
        sessions = requests.get(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                                headers=admin_headers, timeout=15).json()
        if not sessions:
            cr = requests.post(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                               headers=admin_headers,
                               json={"name": "V6.9 companion test"}, timeout=15)
            assert cr.status_code in (200, 201)
            sid = cr.json()["id"]
        else:
            sid = sessions[0]["id"]

        chs = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                           headers=admin_headers, timeout=15).json()
        if not chs:
            pytest.skip("No characters")
        ch = next((c for c in chs if c.get("owner_id") != pid), chs[0])
        ch_id = ch["id"]

        # Assign companion seat
        ar = requests.post(
            f"{BASE_URL}/api/characters/{ch_id}/companions?player_id={pid}",
            headers=admin_headers, timeout=15)
        assert ar.status_code == 200

        # GM creates a token bound to this character
        tok = requests.post(
            f"{BASE_URL}/api/sessions/{sid}/map/tokens",
            headers=admin_headers,
            json={"character_id": ch_id, "label": "T", "x": 1, "y": 1, "size": 1.0},
            timeout=15,
        )
        assert tok.status_code == 200, tok.text
        tid = tok.json()["id"]

        # Companion player attempts to move
        mv = requests.post(
            f"{BASE_URL}/api/sessions/{sid}/map/tokens",
            headers=player_headers,
            json={"id": tid, "character_id": ch_id,
                  "label": "T", "x": 5, "y": 5, "size": 1.0},
            timeout=15,
        )
        assert mv.status_code == 200, mv.text
        body = mv.json()
        assert body["x"] == 5 and body["y"] == 5

        # Revoke companion → player can no longer move
        rr = requests.delete(
            f"{BASE_URL}/api/characters/{ch_id}/companions/{pid}",
            headers=admin_headers, timeout=15)
        assert rr.status_code == 200

        mv2 = requests.post(
            f"{BASE_URL}/api/sessions/{sid}/map/tokens",
            headers=player_headers,
            json={"id": tid, "character_id": ch_id,
                  "label": "T", "x": 9, "y": 9, "size": 1.0},
            timeout=15,
        )
        assert mv2.status_code == 403, f"Expected 403 after revoke, got {mv2.status_code}"

        # Cleanup token
        requests.delete(f"{BASE_URL}/api/sessions/{sid}/map/tokens/{tid}",
                        headers=admin_headers, timeout=15)
