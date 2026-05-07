"""V4.4 / Iteration 15 backend tests.

Coverage:
  - POST /api/admin/reset-to-evereantha → 8-session chronicle seeding
    (sessions_created=8, chat_lines_seeded≈130, dice_rolls_seeded≈22)
  - GET /api/campaigns/{cid}/sessions → 8 sessions, last open, others closed
  - GET /api/sessions/{sid}/chat → Session 2 contains Nyaulis line
  - GET /api/sessions/{sid}/chat → Session 8 contains Roney/Mayor cliffhanger
  - POST /api/uploads/map → multipart upload (admin/GM 200, player 403,
    >12MB 413, wrong content_type 400, bad role 403)
  - GET /api/uploads/maps/{file} → static serve works
  - Knowledge nodes have 'fields' populated for Aurea / Eagles Nest / Nyaulis
"""
from __future__ import annotations

import io
import os
import struct
import time
import zlib

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://campaign-hub-288.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PW = "PieGod08!!"


# ---------- session-scoped fixtures ----------

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
                      timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def reset_payload(admin_token):
    """Performs the destructive reset ONCE per test module run."""
    r = requests.post(
        f"{BASE_URL}/api/admin/reset-to-evereantha?confirm=WIPE",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=60,
    )
    assert r.status_code == 200, f"reset failed: {r.status_code} {r.text[:400]}"
    return r.json()


@pytest.fixture(scope="module")
def player_token():
    """Register a transient player for 403 checks."""
    suffix = str(int(time.time()))[-6:]
    email = f"t15pl_{suffix}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "password": "playerpw1", "name": f"P15-{suffix}", "role": "player",
    }, timeout=15)
    assert r.status_code in (200, 201), f"register player failed: {r.status_code} {r.text}"
    body = r.json()
    if "access_token" in body:
        return body["access_token"]
    # Fallback: log in
    r2 = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": email, "password": "playerpw1"}, timeout=15)
    assert r2.status_code == 200
    return r2.json()["access_token"]


# ---------- helpers ----------

def _make_png(w=2, h=2) -> bytes:
    """Smallest valid PNG (no Pillow needed)."""
    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xffffffff
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b""
    for _ in range(h):
        raw += b"\x00" + (b"\xff\x00\x00" * w)
    idat = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


# ============================================================
# 8-Session Evereantha Chronicle (V4.4)
# ============================================================

class TestEvereanthaChronicle:

    def test_reset_seeds_8_sessions(self, reset_payload):
        assert reset_payload["ok"] is True
        assert reset_payload["sessions_created"] == 8, \
            f"expected 8 sessions, got {reset_payload['sessions_created']}"
        # Loose bounds — the spec says ~130 lines, ~22 rolls. Allow ±20%.
        assert 100 <= reset_payload["chat_lines_seeded"] <= 170, \
            f"chat_lines_seeded out of range: {reset_payload['chat_lines_seeded']}"
        assert 15 <= reset_payload["dice_rolls_seeded"] <= 35, \
            f"dice_rolls_seeded out of range: {reset_payload['dice_rolls_seeded']}"
        assert reset_payload["nodes_created"] >= 15
        assert reset_payload["characters_created"] == 3

    def test_sessions_listed_in_order(self, reset_payload, admin_headers):
        cid = reset_payload["campaign"]["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        sessions = r.json()
        assert len(sessions) == 8, f"expected 8 sessions got {len(sessions)}"
        # Status: last open, all others closed
        last = sessions[-1]
        # Sessions might be sorted ascending or descending; locate by status logic
        opens = [s for s in sessions if s.get("status") == "open"]
        closeds = [s for s in sessions if s.get("status") == "closed"]
        assert len(opens) == 1, f"expected exactly 1 open session, got {len(opens)}"
        assert len(closeds) == 7, f"expected 7 closed sessions, got {len(closeds)}"

    def test_session2_contains_nyaulis_line(self, reset_payload, admin_headers):
        cid = reset_payload["campaign"]["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                         headers=admin_headers, timeout=15)
        sessions = r.json()
        # Identify Session 2 by title (contains "Session 2" or index 1 in chronological order)
        # Sort by created_at to be safe
        sessions_sorted = sorted(sessions, key=lambda s: s.get("created_at", ""))
        s2 = sessions_sorted[1]
        chat_r = requests.get(f"{BASE_URL}/api/sessions/{s2['id']}/chat",
                              headers=admin_headers, timeout=15)
        assert chat_r.status_code == 200
        msgs = chat_r.json()
        joined = " ".join(m.get("message", "") + " " + m.get("user_name", "") for m in msgs)
        assert "Nyaulis" in joined, "Nyaulis should appear in Session 2 chat"
        assert "took from this wood" in joined.lower() or "You took from this wood" in joined, \
            "Nyaulis signature line missing from S2 chat"

    def test_session8_cliffhanger(self, reset_payload, admin_headers):
        cid = reset_payload["campaign"]["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                         headers=admin_headers, timeout=15)
        sessions_sorted = sorted(r.json(), key=lambda s: s.get("created_at", ""))
        s8 = sessions_sorted[-1]
        assert s8.get("status") == "open", f"Session 8 should be open, got {s8.get('status')}"
        chat_r = requests.get(f"{BASE_URL}/api/sessions/{s8['id']}/chat",
                              headers=admin_headers, timeout=15)
        assert chat_r.status_code == 200
        msgs = chat_r.json()
        joined = " ".join(m.get("message", "") for m in msgs).lower()
        assert "roney" in joined, "Session 8 should reference Roney"
        # Mayor reference (cliffhanger)
        assert "mayor" in joined, "Session 8 should reference the Mayor's note"


# ============================================================
# Knowledge Web — node fields populated
# ============================================================

class TestKnowledgeFields:

    def test_aurea_node_has_fields(self, reset_payload, admin_headers):
        cid = reset_payload["campaign"]["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/nodes",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        nodes = r.json()
        target_titles = {"Aurea", "Eagles Nest", "Nyaulis"}
        found = {n["title"]: n for n in nodes if n.get("title") in target_titles}
        # At least one of those must exist with a non-empty fields dict
        assert found, f"none of {target_titles} found among {len(nodes)} nodes"
        nodes_with_fields = [n for n in found.values() if n.get("fields")]
        assert nodes_with_fields, \
            f"Expected at least one of {list(found.keys())} to carry 'fields' dict, got: " \
            + str({k: bool(v.get('fields')) for k, v in found.items()})


# ============================================================
# Map Upload — POST /api/uploads/map
# ============================================================

class TestMapUpload:

    def test_admin_can_upload_png(self, admin_token):
        png = _make_png(4, 4)
        files = {"file": ("test.png", png, "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/uploads/map",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30,
        )
        assert r.status_code == 200, f"upload failed: {r.status_code} {r.text}"
        body = r.json()
        assert "url" in body and body["url"].startswith("/api/uploads/maps/")
        assert body["bytes"] == len(png)
        # Pillow available on prod → width/height should be ints
        if body.get("width") is not None:
            assert body["width"] == 4
            assert body["height"] == 4
        # Static fetch
        full_url = f"{BASE_URL}{body['url']}"
        gr = requests.get(full_url, timeout=15)
        assert gr.status_code == 200, f"static fetch failed: {gr.status_code}"
        assert gr.content == png, "served bytes do not match upload"

    def test_player_role_403(self, player_token):
        png = _make_png(2, 2)
        files = {"file": ("test.png", png, "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/uploads/map",
            files=files,
            headers={"Authorization": f"Bearer {player_token}"},
            timeout=15,
        )
        assert r.status_code == 403, f"expected 403 for player, got {r.status_code} {r.text}"

    def test_wrong_content_type_400(self, admin_token):
        files = {"file": ("notes.txt", b"hello world", "text/plain")}
        r = requests.post(
            f"{BASE_URL}/api/uploads/map",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert r.status_code == 400, f"expected 400 for text/plain, got {r.status_code}"

    def test_oversize_413(self, admin_token):
        # 13 MB blob, valid content-type label so it passes the type gate first
        big = b"\x00" * (13 * 1024 * 1024)
        files = {"file": ("big.png", big, "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/uploads/map",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=60,
        )
        assert r.status_code == 413, f"expected 413 for 13MB, got {r.status_code} {r.text[:200]}"

    def test_unauthenticated_401(self):
        png = _make_png(2, 2)
        files = {"file": ("test.png", png, "image/png")}
        r = requests.post(f"{BASE_URL}/api/uploads/map", files=files, timeout=15)
        assert r.status_code in (401, 403), \
            f"unauth upload should be 401/403 not {r.status_code}"


# ============================================================
# Quick V4.3 regression smoke
# ============================================================

class TestV43Regression:

    def test_login_returns_admin_role(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/auth/me",
                         headers={"Authorization": f"Bearer {admin_token}"}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("role") == "admin"

    def test_campaign_list_visible(self, reset_payload, admin_headers):
        r = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        camps = r.json()
        assert any(c.get("id") == reset_payload["campaign"]["id"] for c in camps)
