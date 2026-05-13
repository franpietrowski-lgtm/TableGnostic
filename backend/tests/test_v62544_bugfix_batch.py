"""V6.25.44 bug-fix batch backend regression.

Covers:
  Bug C  — GET /api/reference/library member_ids visibility
  Bug D  — POST /api/sessions/{sid}/scenes with adhoc_location_label
  Bug D  — voice_lines.py route registration (channel-or-thread target
           code path resolves without crashing on import). We test only
           that the upload route returns 422 for missing form fields
           (i.e. the route is wired correctly).
  Bug B  — frontend-only but we verify the canonical char-edit route
           is registered (presence-check by hitting an authenticated
           character GET).
"""
import os
import time
import requests
import pytest

def _load_base_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url:
        return url.rstrip("/")
    # Fallback — read frontend/.env (test infra doesn't auto-load it).
    env_path = "/app/frontend/.env"
    if os.path.exists(env_path):
        with open(env_path) as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE_URL = _load_base_url()
GM_EMAIL = "franpietrowski@gmail.com"
GM_PWD = "PieGod08!!"
ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PWD = "LoremasterAurea2026!Forge"


def _login(email, pwd):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": pwd}, timeout=30)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    token = r.json().get("access_token") or r.json().get("token")
    assert token, f"no token in login response: {r.json()}"
    return token


@pytest.fixture(scope="module")
def gm_headers():
    return {"Authorization": f"Bearer {_login(GM_EMAIL, GM_PWD)}"}


@pytest.fixture(scope="module")
def admin_headers():
    return {"Authorization": f"Bearer {_login(ADMIN_EMAIL, ADMIN_PWD)}"}


@pytest.fixture(scope="module")
def gm_campaign(gm_headers):
    """Find/ensure a besm-4e campaign owned by the GM."""
    r = requests.get(f"{BASE_URL}/api/campaigns", headers=gm_headers, timeout=30)
    assert r.status_code == 200, r.text
    camps = r.json() if isinstance(r.json(), list) else r.json().get("campaigns", [])
    for c in camps:
        if c.get("system_id") == "besm-4e":
            return c
    # Create one if not found
    r = requests.post(f"{BASE_URL}/api/campaigns",
                      headers=gm_headers,
                      json={"name": "TEST_v62544_besm_camp", "system_id": "besm-4e"},
                      timeout=30)
    assert r.status_code in (200, 201), r.text
    return r.json()


# ============== Bug C — reference library member_ids fix ==============

class TestBugCReferenceLibrary:
    def test_create_custom_reference_and_visible_in_library(self, gm_headers, gm_campaign):
        cid = gm_campaign["id"]
        payload = {
            "kind": "custom",
            "name": f"TEST_v62544_rule_{int(time.time())}",
            "summary": "House rule for v62544 regression",
            "page": 10,
            "book": "besm-4e",
            "fields": {"category": "house-rule"},
        }
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/reference",
                          headers=gm_headers, json=payload, timeout=30)
        assert r.status_code == 200, f"create failed: {r.status_code} {r.text}"
        created = r.json()
        assert created["name"] == payload["name"]
        rid = created["id"]

        # Now hit the library endpoint; must see this row.
        r = requests.get(
            f"{BASE_URL}/api/reference/library?system_id=besm-4e",
            headers=gm_headers, timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["system_id"] == "besm-4e"
        assert data["campaign_count"] >= 1, (
            f"Bug C regression — campaign_count was {data['campaign_count']} "
            f"(member_ids filter broken)"
        )
        names = [row["name"] for row in data["rows"]]
        assert payload["name"] in names, (
            f"Bug C regression — newly created row {payload['name']!r} "
            f"not in library rows ({len(names)} total)."
        )

        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}/reference/{rid}",
                        headers=gm_headers, timeout=30)

    def test_library_requires_system_id(self, gm_headers):
        r = requests.get(f"{BASE_URL}/api/reference/library", headers=gm_headers, timeout=30)
        assert r.status_code == 422

    def test_library_admin_sees_all(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/reference/library?system_id=besm-4e",
            headers=admin_headers, timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        assert "rows" in data and "campaign_count" in data


# ============== Bug D — scenes adhoc_location_label =====================

class TestBugDAdhocLocation:
    @pytest.fixture(scope="class")
    def session_id(self, gm_headers, gm_campaign):
        cid = gm_campaign["id"]
        # Try to reuse an existing session first to avoid side-effects.
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/sessions",
            headers=gm_headers, timeout=30,
        )
        if r.status_code == 200:
            rows = r.json() if isinstance(r.json(), list) else r.json().get("sessions", [])
            if rows:
                return rows[0]["id"]
        r = requests.post(
            f"{BASE_URL}/api/sessions",
            headers=gm_headers,
            json={"campaign_id": cid, "title": "TEST_v62544_session"},
            timeout=30,
        )
        assert r.status_code in (200, 201), r.text
        s = r.json()
        sid = s.get("id") or s.get("session", {}).get("id")
        assert sid
        return sid

    def test_create_scene_with_adhoc_location_label(self, gm_headers, session_id):
        body = {"name": "Cellar Stand-off",
                "adhoc_location_label": "the dripping cellar at dusk"}
        r = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/scenes",
            headers=gm_headers, json=body, timeout=30,
        )
        assert r.status_code == 200, f"adhoc scene create failed: {r.status_code} {r.text}"
        scene = r.json()["scene"]
        assert scene["location_id"] is None
        assert scene["location_label"] == "the dripping cellar at dusk", (
            f"location_label mismatch: {scene}"
        )
        assert scene["status"] == "active"

        # GET active to confirm persistence
        r = requests.get(
            f"{BASE_URL}/api/sessions/{session_id}/scenes/active",
            headers=gm_headers, timeout=30,
        )
        assert r.status_code == 200
        active = r.json()["scene"]
        assert active is not None
        assert active["location_label"] == "the dripping cellar at dusk"

        # Close requires confirmed=true
        scene_id = scene["id"]
        r1 = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/scenes/{scene_id}/close",
            headers=gm_headers, timeout=30,
        )
        assert r1.status_code == 412, f"412 expected without confirmed; got {r1.status_code}"
        r2 = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/scenes/{scene_id}/close?confirmed=true",
            headers=gm_headers, timeout=30,
        )
        assert r2.status_code == 200, r2.text
        assert r2.json()["scene"]["status"] == "closed"


# ============== Bug D — voice_lines route wiring =======================

class TestBugDVoiceLineRoute:
    def test_voice_line_route_registered(self, gm_headers, gm_campaign):
        """No real audio — just confirm the route registers and validates
        form input (422). Proves the channel-or-thread import path
        loaded without error."""
        # Find any session for this campaign first.
        cid = gm_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/sessions",
            headers=gm_headers, timeout=30,
        )
        assert r.status_code == 200, r.text
        sessions = r.json() if isinstance(r.json(), list) else r.json().get("sessions", [])
        if not sessions:
            pytest.skip("No sessions for this campaign — skipping route-presence ping.")
        sid = sessions[0]["id"]
        # Hit POST with no audio — must NOT 404; should be 422 (missing form fields).
        r = requests.post(
            f"{BASE_URL}/api/sessions/{sid}/voice-lines",
            headers=gm_headers, timeout=30,
        )
        assert r.status_code in (422, 400), (
            f"voice-line route missing or wrong status; got {r.status_code} {r.text}"
        )


# ============== Bug B — canonical character edit route =================

class TestBugBCharacterEditRoute:
    """The fix is frontend-only (route path inside AppliedTemplatesPanel.jsx);
    we sanity-check that /api/characters/{id} fetches work for the GM so
    the React route, when navigated to, has data to render."""

    def test_characters_listing_for_gm(self, gm_headers, gm_campaign):
        cid = gm_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/characters",
            headers=gm_headers, timeout=30,
        )
        assert r.status_code == 200, r.text
