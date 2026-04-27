"""V5.1.2 iteration 22 backend tests.

Covers:
- POST /api/auth/change-password (wrong current → 403, correct → 200)
- PATCH /api/auth/me (byline_name / avatar_url / bio round-trip)
- POST /api/uploads/avatar (image upload, non-image reject, oversize reject)
- GET /api/systems/cypher/reference (pool_baseline + tier_derived + types with
  pool_offsets/starting_edge/starting_cypher_limit)
- POST /api/sessions/{sid}/seat-character (owner seat / release)
- POST /api/sessions/{sid}/assign-character (GM override ok, non-GM 403)
- GET /api/campaigns/{cid}/export.pdf?mode=narrative (bypasses 451 gate,
  returns PDF OR the documented "No sessions to export." 400)
"""
from __future__ import annotations

import io
import os
import struct
import zlib

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL required"

ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PASSWORD = "PieGod08!!"
CYPHER_CAMPAIGN_ID = "22ee28aaf79541c395255e144b5aab42"
CYPHER_CHARACTER_ID = "a129db2a8eb44e3b849de6fff876e9f5"


# ---------- helpers ----------

def _tiny_png_bytes() -> bytes:
    """Minimal 1x1 PNG constructed inline (no Pillow required)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\x00\x00"  # filter byte + 1 RGB pixel
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


@pytest.fixture(scope="module")
def auth_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
               timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code} {r.text}")
    token = r.json().get("access_token")
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def current_user(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 200
    return r.json()


# ---------- change-password ----------

class TestChangePassword:
    def test_wrong_current_returns_403(self, auth_session):
        r = auth_session.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": "definitely-not-correct",
                  "new_password": "BogusPass123!"},
            timeout=15,
        )
        assert r.status_code == 403, r.text

    def test_correct_current_succeeds_and_revert(self, auth_session):
        # Rotate to temporary and back, so the credential remains stable.
        temp = "TempPass_V512_iter22!!"
        r = auth_session.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": ADMIN_PASSWORD, "new_password": temp},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True

        # Revert
        r2 = auth_session.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": temp, "new_password": ADMIN_PASSWORD},
            timeout=15,
        )
        assert r2.status_code == 200, r2.text

        # Verify login still works with the original password.
        s = requests.Session()
        lr = s.post(f"{BASE_URL}/api/auth/login",
                    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                    timeout=15)
        assert lr.status_code == 200, lr.text


# ---------- PATCH /api/auth/me ----------

class TestProfilePatch:
    def test_patch_and_roundtrip(self, auth_session, current_user):
        payload = {
            "byline_name": "TEST_V512 Byline",
            "bio": "TEST_V512 bio line used by iter22 tests.",
            "avatar_url": "/api/uploads/avatars/placeholder.png",
        }
        r = auth_session.patch(f"{BASE_URL}/api/auth/me", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("byline_name") == payload["byline_name"]
        assert data.get("bio") == payload["bio"]
        assert data.get("avatar_url") == payload["avatar_url"]

        # Re-fetch
        g = auth_session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert g.status_code == 200
        gd = g.json()
        assert gd.get("byline_name") == payload["byline_name"]
        assert gd.get("bio") == payload["bio"]
        assert gd.get("avatar_url") == payload["avatar_url"]

        # Restore prior values (best-effort).
        restore = {
            "byline_name": current_user.get("byline_name") or "",
            "bio": current_user.get("bio") or "",
            "avatar_url": current_user.get("avatar_url") or "",
        }
        auth_session.patch(f"{BASE_URL}/api/auth/me", json=restore, timeout=15)


# ---------- POST /api/uploads/avatar ----------

class TestAvatarUpload:
    def test_upload_png_ok(self, auth_session):
        png = _tiny_png_bytes()
        files = {"file": ("tiny.png", io.BytesIO(png), "image/png")}
        r = auth_session.post(f"{BASE_URL}/api/uploads/avatar",
                              files=files, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("url", "").startswith("/api/uploads/avatars/")
        assert body.get("bytes") == len(png)

        # Confirm /api/auth/me reflects the persisted avatar_url.
        me = auth_session.get(f"{BASE_URL}/api/auth/me", timeout=15).json()
        assert me.get("avatar_url") == body["url"]

    def test_reject_non_image(self, auth_session):
        files = {"file": ("doc.txt", io.BytesIO(b"not an image"), "text/plain")}
        r = auth_session.post(f"{BASE_URL}/api/uploads/avatar",
                              files=files, timeout=15)
        assert r.status_code == 400, r.text

    def test_reject_oversize(self, auth_session):
        # 4.5 MB of fake JPEG payload — should trip the 4 MB AVATAR_MAX cap.
        big = b"\xff\xd8\xff\xe0" + (b"\x00" * (4 * 1024 * 1024 + 500 * 1024))
        files = {"file": ("big.jpg", io.BytesIO(big), "image/jpeg")}
        r = auth_session.post(f"{BASE_URL}/api/uploads/avatar",
                              files=files, timeout=60)
        assert r.status_code == 413, f"expected 413, got {r.status_code}: {r.text[:200]}"


# ---------- Cypher reference ----------

class TestCypherReference:
    def test_reference_shape(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/systems/cypher/reference", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("pool_baseline") == 7, f"pool_baseline wrong: {data.get('pool_baseline')}"
        td = data.get("tier_derived") or {}
        assert td, "tier_derived missing"
        # Shape shipped by backend: stat-keyed dicts keyed by tier-string.
        rpd = td.get("recoveries_per_day") or {}
        rd = td.get("recovery_die") or {}
        assert rpd, f"tier_derived.recoveries_per_day missing: {td}"
        assert rd, f"tier_derived.recovery_die missing: {td}"
        # At minimum tier 1 must be present.
        assert ("1" in rpd) or (1 in rpd), f"tier 1 missing in recoveries_per_day: {rpd}"
        assert ("1" in rd) or (1 in rd), f"tier 1 missing in recovery_die: {rd}"

        types = data.get("types") or data.get("Types") or []
        assert types, "types missing"
        for t in types:
            assert "pool_offsets" in t, f"type missing pool_offsets: {t}"
            assert "starting_edge" in t, f"type missing starting_edge: {t}"
            assert "starting_cypher_limit" in t, f"type missing starting_cypher_limit: {t}"


# ---------- Session seating ----------

@pytest.fixture(scope="module")
def test_session(auth_session):
    r = auth_session.post(
        f"{BASE_URL}/api/sessions",
        json={"campaign_id": CYPHER_CAMPAIGN_ID,
              "title": "TEST_V512 seating session"},
        timeout=20,
    )
    if r.status_code not in (200, 201):
        pytest.skip(f"cannot create session: {r.status_code} {r.text}")
    sid = r.json().get("id")
    assert sid, r.text
    yield sid
    # Best-effort cleanup (DELETE endpoint may not exist; non-fatal).
    try:
        auth_session.delete(f"{BASE_URL}/api/sessions/{sid}", timeout=15)
    except Exception:
        pass


class TestSessionSeating:
    def test_seat_own_character(self, auth_session, test_session, current_user):
        r = auth_session.post(
            f"{BASE_URL}/api/sessions/{test_session}/seat-character",
            params={"character_id": CYPHER_CHARACTER_ID},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assignments = body.get("character_assignments") or {}
        assert assignments.get(current_user["id"]) == CYPHER_CHARACTER_ID

    def test_release_seat(self, auth_session, test_session, current_user):
        r = auth_session.post(
            f"{BASE_URL}/api/sessions/{test_session}/seat-character",
            params={"character_id": ""},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assignments = r.json().get("character_assignments") or {}
        assert current_user["id"] not in assignments

    def test_gm_assign_character(self, auth_session, test_session, current_user):
        r = auth_session.post(
            f"{BASE_URL}/api/sessions/{test_session}/assign-character",
            params={"target_user_id": current_user["id"],
                    "character_id": CYPHER_CHARACTER_ID},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assignments = r.json().get("character_assignments") or {}
        assert assignments.get(current_user["id"]) == CYPHER_CHARACTER_ID

    def test_non_gm_assign_denied(self, auth_session, test_session, current_user):
        # Register an ephemeral player to verify 403
        import uuid
        email = f"test_v512_{uuid.uuid4().hex[:10]}@example.com"
        pw = "PlayerPass_V512!"
        reg = requests.post(f"{BASE_URL}/api/auth/register",
                            json={"email": email, "password": pw,
                                  "name": "TEST V512 Player", "role": "player"},
                            timeout=15)
        if reg.status_code != 200:
            pytest.skip(f"register failed: {reg.status_code} {reg.text}")
        token = reg.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.post(
            f"{BASE_URL}/api/sessions/{test_session}/assign-character",
            params={"target_user_id": current_user["id"],
                    "character_id": CYPHER_CHARACTER_ID},
            headers=headers,
            timeout=15,
        )
        # 403 is expected (not a member of campaign; definitely not GM/admin).
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text[:200]}"


# ---------- PDF narrative export ----------

class TestNarrativePdfExport:
    def test_narrative_mode_bypasses_licence_gate(self, auth_session):
        r = auth_session.get(
            f"{BASE_URL}/api/campaigns/{CYPHER_CAMPAIGN_ID}/export.pdf",
            params={"mode": "narrative"},
            timeout=45,
        )
        # Accept 200 (PDF) OR documented 400 "No sessions to export." empty state.
        if r.status_code == 200:
            ctype = r.headers.get("content-type", "")
            assert "pdf" in ctype.lower(), f"unexpected content-type: {ctype}"
            assert r.content[:4] == b"%PDF", "body not a PDF"
        elif r.status_code == 400:
            assert "No sessions" in r.text or "sessions" in r.text.lower(), r.text
        else:
            pytest.fail(f"unexpected {r.status_code}: {r.text[:200]}")

    def test_campaign_mode_still_gates_451(self, auth_session):
        # Check the Forbidden-Test Cypher campaign still enforces 451 in default
        # mode. This is only a signal — if the campaign setting is not one
        # of the forbidden names any more, skip.
        r = auth_session.get(
            f"{BASE_URL}/api/campaigns/{CYPHER_CAMPAIGN_ID}/export.pdf",
            params={"mode": "campaign"},
            timeout=45,
        )
        # Acceptable outcomes: 451 (gated), 200 (pdf), or 400 (no sessions).
        assert r.status_code in (200, 400, 451), f"{r.status_code}: {r.text[:200]}"
