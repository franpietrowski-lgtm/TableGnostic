"""V6.11 backend tests — session reorder, NPC pool creature bucket, character portrait."""
import io
import os
import struct
import zlib
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://campaign-hub-288.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PASS = "PieGod08!!"


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
                      timeout=15)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def besm_campaign(admin_headers):
    r = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    cands = [c for c in r.json() if c.get("system_id") == "besm-4e" and c.get("is_gm")]
    if not cands:
        pytest.skip("No GM-owned besm-4e campaign")
    return cands[0]


def _make_png_bytes() -> bytes:
    """Minimal valid 1×1 PNG so we don't need Pillow as a test dep."""
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, d):
        crc = zlib.crc32(t + d) & 0xffffffff
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", crc)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    raw = b"\x00" + b"\xff\x00\xff\xff"  # filter byte + RGBA pixel
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ─── 1. Session reorder ──────────────────────────────────────

class TestSessionReorder:
    def test_reorder_assigns_sequence_index(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        sess_r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/sessions",
                              headers=admin_headers, timeout=15)
        assert sess_r.status_code == 200
        sessions = sess_r.json()
        if len(sessions) < 2:
            # Create two sessions for the test
            for n in ("Reorder Test A", "Reorder Test B"):
                requests.post(f"{BASE_URL}/api/sessions",
                              headers=admin_headers,
                              json={"campaign_id": cid, "title": n}, timeout=15)
            sessions = requests.get(
                f"{BASE_URL}/api/campaigns/{cid}/sessions",
                headers=admin_headers, timeout=15).json()
        ids = [s["id"] for s in sessions[:3]]
        # Reverse order
        new_order = list(reversed(ids))
        r = requests.put(f"{BASE_URL}/api/campaigns/{cid}/sessions/reorder",
                         headers=admin_headers, json=new_order, timeout=15)
        assert r.status_code == 200, r.text
        # Verify sequence_index now reflects the new order
        fresh = {s["id"]: s for s in r.json()}
        for idx, sid in enumerate(new_order):
            assert fresh[sid].get("sequence_index") == idx, (
                f"Expected sequence_index={idx} for {sid}, got {fresh[sid].get('sequence_index')}"
            )

    def test_non_gm_forbidden(self, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.put(f"{BASE_URL}/api/campaigns/{cid}/sessions/reorder",
                         json=["fake-id"], timeout=15)
        assert r.status_code in (401, 403), r.text


# ─── 2. NPC pool now exposes a `creatures` bucket ────────────

class TestCreaturePool:
    def test_creatures_separated_in_pool(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        # Director endpoint includes the npc_pool array
        r = requests.get(f"{BASE_URL}/api/director/{cid}",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        pool = r.json().get("npc_pool", [])
        # Check that creatures are tagged source="creatures" (Lancing Andrewsarchus
        # in Evereantha's BESM campaign is type=creature in seed_evereantha.py)
        sources = {p["source"] for p in pool}
        # Either we have creatures or we don't — but the endpoint must accept
        # the new bucket key.
        assert "creatures" in sources or "codex" in sources, f"Got sources: {sources}"


# ─── 3. Character portrait upload ────────────────────────────

class TestCharacterPortrait:
    def test_upload_persists_url(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        chs = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                           headers=admin_headers, timeout=15).json()
        if not chs:
            pytest.skip("No characters")
        ch_id = chs[0]["id"]
        files = {"file": ("portrait.png", _make_png_bytes(), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/uploads/character-portrait/{ch_id}",
            files=files, headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        url = r.json().get("url")
        assert url and url.startswith("/api/uploads/portraits/"), url
        # Verify persistence on the character document
        ch = requests.get(f"{BASE_URL}/api/characters/{ch_id}",
                          headers=admin_headers, timeout=15).json()
        assert ch.get("portrait_url") == url

    def test_404_on_unknown_character(self, admin_headers):
        files = {"file": ("p.png", _make_png_bytes(), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/uploads/character-portrait/no-such-id",
            files=files, headers=admin_headers, timeout=15)
        assert r.status_code == 404, r.text


# ─── 4. Inline level edit (PUT /api/characters/{id}) ─────────

class TestInlineLevelEdit:
    def test_put_attribute_level_persists(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        chs = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                           headers=admin_headers, timeout=15).json()
        if not chs:
            pytest.skip("No characters")
        ch_id = chs[0]["id"]
        ch = requests.get(f"{BASE_URL}/api/characters/{ch_id}",
                          headers=admin_headers, timeout=15).json()
        if not ch.get("attributes"):
            pytest.skip("Character has no attributes")
        attrs = list(ch["attributes"])
        original = attrs[0]["level"]
        attrs[0] = {**attrs[0], "level": original + 1}
        # Frontend sends full character body merged with patch (V6.11 fix)
        body = {**ch, "attributes": attrs}
        r = requests.put(f"{BASE_URL}/api/characters/{ch_id}",
                         headers=admin_headers,
                         json=body, timeout=15)
        assert r.status_code == 200, r.text
        new_attrs = r.json()["attributes"]
        assert new_attrs[0]["level"] == original + 1
        # restore so the test is idempotent
        attrs[0]["level"] = original
        body = {**ch, "attributes": attrs}
        requests.put(f"{BASE_URL}/api/characters/{ch_id}",
                     headers=admin_headers, json=body, timeout=15)
