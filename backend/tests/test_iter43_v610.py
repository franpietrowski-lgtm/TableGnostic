"""V6.10 backend tests — Auto-status rings, NPC bulk auto-generate, expanded export."""
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


# ─── 1. Auto-status rings — character effects endpoint ────────────────

class TestCharacterStatusRings:
    def test_endpoint_returns_array(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        chars = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                             headers=admin_headers, timeout=15).json()
        if not chars:
            pytest.skip("No characters")
        ch_id = chars[0]["id"]
        r = requests.get(f"{BASE_URL}/api/characters/{ch_id}/effects",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)


# ─── 2. NPC bulk auto-generate ────────────────────────────────────────

class TestBulkAutoGenerate:
    def test_bulk_generate_returns_counts(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/auto-generate-all"
            "?threat_tier=equal&overwrite=false",
            headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("campaign_id", "system_id", "candidates",
                  "generated", "skipped_already_populated", "by_tier"):
            assert k in d, f"missing key: {k}"
        assert isinstance(d["generated"], int)
        assert isinstance(d["candidates"], int)
        assert d["candidates"] >= 0

    def test_idempotent_second_call_skips(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        # Run twice; second call should generate 0 new sheets (all populated).
        first = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/auto-generate-all?overwrite=false",
            headers=admin_headers, timeout=30).json()
        second = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/auto-generate-all?overwrite=false",
            headers=admin_headers, timeout=30).json()
        assert second["generated"] == 0
        # Skipped count >= first.generated
        assert second["skipped_already_populated"] >= first.get("generated", 0)

    def test_non_gm_forbidden(self, besm_campaign):
        # No auth = 401; basic permission check.
        cid = besm_campaign["id"]
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/auto-generate-all",
            timeout=15)
        assert r.status_code in (401, 403), r.text


# ─── 3. seed-evereantha-suite auto_generated_npc_sheets ───────────────

class TestSeedEvereanthaSuiteAuto:
    def test_seed_returns_auto_generated_npc_sheets(self, admin_headers):
        r = requests.post(f"{BASE_URL}/api/admin/seed-evereantha-suite",
                          headers=admin_headers, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "deployed" in d
        assert "auto_generated_npc_sheets" in d
        assert isinstance(d["auto_generated_npc_sheets"], list)
        # Each entry must have expected keys (when non-empty)
        for entry in d["auto_generated_npc_sheets"]:
            assert "campaign_id" in entry
            assert "system_id" in entry
            assert "auto_npc_sheets" in entry
            assert isinstance(entry["auto_npc_sheets"], int)


# ─── 4. Campaign export PDF — chronicle bundle expansion ──────────────

class TestExportPdfBundle:
    def test_pdf_streams(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/export.pdf",
            headers=admin_headers, timeout=60)
        # Either we get a PDF or 400 if no sessions
        if r.status_code == 400 and "No sessions" in r.text:
            pytest.skip("Campaign has no sessions to export")
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf")
        body = r.content
        # PDF magic number
        assert body[:4] == b"%PDF", "Output is not a PDF"
        # Must be non-trivially sized.
        assert len(body) > 5_000, f"PDF only {len(body)} bytes"
