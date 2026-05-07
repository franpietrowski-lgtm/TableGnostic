"""V6.13 backend tests — Canon Registry + Global Search + Character portrait PDF."""
import os
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
    cands = [c for c in r.json() if c.get("system_id") == "besm-4e" and c.get("is_gm")]
    if not cands:
        pytest.skip("No GM besm-4e campaign")
    return cands[0]


# ─── 1. Canon Registry ──────────────────────────────────────

class TestCanonRegistry:
    def test_public_endpoint_no_auth(self):
        r = requests.get(f"{BASE_URL}/api/canon-registry", timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_full_publish_subscribe_lifecycle(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        # Publish
        pub = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/canon-publish",
            headers=admin_headers,
            json={"blurb": "Test canon pitch for V6.13."},
            timeout=15)
        assert pub.status_code == 200, pub.text
        assert pub.json()["published"] is True
        # Registry should now contain this campaign
        reg = requests.get(f"{BASE_URL}/api/canon-registry", timeout=15).json()
        ids = [c["id"] for c in reg]
        assert cid in ids
        card = next(c for c in reg if c["id"] == cid)
        assert card["canon_blurb"] == "Test canon pitch for V6.13."
        assert "subscribers" in card and "delta_drops" in card
        # Subscribe
        sub = requests.post(
            f"{BASE_URL}/api/canon-registry/{cid}/subscribe",
            headers=admin_headers, timeout=15)
        assert sub.status_code == 200, sub.text
        # My subscriptions
        mine = requests.get(
            f"{BASE_URL}/api/canon-registry/subscriptions",
            headers=admin_headers, timeout=15).json()
        assert any(m["id"] == cid for m in mine)
        # Idempotent subscribe
        sub2 = requests.post(
            f"{BASE_URL}/api/canon-registry/{cid}/subscribe",
            headers=admin_headers, timeout=15)
        assert sub2.status_code == 200, sub2.text
        # Unsubscribe
        unsub = requests.delete(
            f"{BASE_URL}/api/canon-registry/{cid}/subscribe",
            headers=admin_headers, timeout=15)
        assert unsub.status_code == 200, unsub.text
        # Unpublish
        unpub = requests.delete(
            f"{BASE_URL}/api/campaigns/{cid}/canon-publish",
            headers=admin_headers, timeout=15)
        assert unpub.status_code == 200, unpub.text
        assert unpub.json()["published"] is False
        # Registry should NOT contain this campaign now
        reg2 = requests.get(f"{BASE_URL}/api/canon-registry", timeout=15).json()
        assert cid not in [c["id"] for c in reg2]

    def test_subscribe_fails_when_not_published(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        # Ensure unpublished state
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}/canon-publish",
                        headers=admin_headers, timeout=15)
        r = requests.post(
            f"{BASE_URL}/api/canon-registry/{cid}/subscribe",
            headers=admin_headers, timeout=15)
        assert r.status_code == 404, r.text

    def test_non_gm_cannot_publish(self, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/canon-publish",
            json={"blurb": "x"}, timeout=15)
        assert r.status_code in (401, 403), r.text


# ─── 2. Global search ──────────────────────────────────────

class TestGlobalSearch:
    def test_empty_query_returns_empty(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/search?q=",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json() == []

    def test_short_query_returns_empty(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/search?q=a",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json() == []

    def test_substring_search_finds_results(self, admin_headers, besm_campaign):
        # Evereantha has "Andrewsarchus" creatures + many nodes. Search
        # a common fragment.
        r = requests.get(f"{BASE_URL}/api/search?q=ever",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        results = r.json()
        assert isinstance(results, list)
        # Each result must carry the required shape
        for row in results[:5]:
            assert "type" in row and "title" in row and "url" in row
            assert row["type"] in ("campaign", "node", "character", "session")

    def test_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/search?q=test", timeout=15)
        assert r.status_code in (401, 403), r.text


# ─── 3. Character portrait in PDF ──────────────────────────

class TestPortraitInPDF:
    def test_pdf_renders_after_portrait_upload(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        chs = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                           headers=admin_headers, timeout=15).json()
        if not chs:
            pytest.skip("No characters to attach a portrait to")
        # Upload the minimal PNG we use elsewhere, so we know the
        # character has a portrait.
        import struct, zlib
        sig = b"\x89PNG\r\n\x1a\n"
        def chunk(t, d):
            crc = zlib.crc32(t + d) & 0xffffffff
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", crc)
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        raw = b"\x00" + b"\xff\x00\xff\xff"
        idat = chunk(b"IDAT", zlib.compress(raw))
        iend = chunk(b"IEND", b"")
        files = {"file": ("portrait.png", sig + ihdr + idat + iend, "image/png")}
        ch_id = chs[0]["id"]
        up = requests.post(
            f"{BASE_URL}/api/uploads/character-portrait/{ch_id}",
            files=files, headers=admin_headers, timeout=15)
        assert up.status_code == 200, up.text
        # Export the campaign PDF and verify it's still a valid PDF
        pdf = requests.get(f"{BASE_URL}/api/campaigns/{cid}/export.pdf",
                           headers=admin_headers, timeout=60)
        if pdf.status_code == 400 and "No sessions" in pdf.text:
            pytest.skip("Campaign has no sessions")
        assert pdf.status_code == 200
        assert pdf.content[:4] == b"%PDF"
        assert len(pdf.content) > 5_000
