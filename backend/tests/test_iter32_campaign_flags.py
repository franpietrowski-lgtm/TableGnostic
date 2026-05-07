"""Iter32 V6.0 regression test — GET /api/campaigns must hydrate is_gm + is_member per row.
This validates the campaigns.py list_campaigns fix at lines ~149-156."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://campaign-hub-288.preview.emergentagent.com").rstrip("/")
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": GM_EMAIL, "password": GM_PASS}, timeout=15)
    assert r.status_code == 200, f"GMFran login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def gm_headers(gm_token):
    return {"Authorization": f"Bearer {gm_token}"}


# Backend regression — list endpoint flag hydration
class TestCampaignListFlags:
    def test_mine_true_all_rows_have_flags(self, gm_headers):
        r = requests.get(f"{BASE_URL}/api/campaigns?mine=true", headers=gm_headers, timeout=15)
        assert r.status_code == 200
        rows = r.json()
        assert isinstance(rows, list)
        assert len(rows) > 0, "GMFran should own at least 1 campaign"
        for row in rows:
            assert "is_gm" in row, f"Row missing is_gm: {row.get('id')}"
            assert "is_member" in row, f"Row missing is_member: {row.get('id')}"
            assert isinstance(row["is_gm"], bool)
            assert isinstance(row["is_member"], bool)

    def test_mine_true_at_least_one_is_gm(self, gm_headers):
        r = requests.get(f"{BASE_URL}/api/campaigns?mine=true", headers=gm_headers, timeout=15)
        rows = r.json()
        gm_count = sum(1 for r in rows if r.get("is_gm"))
        assert gm_count > 0, f"GMFran should be GM of >0 campaigns, got {gm_count}"
        print(f"GMFran is_gm count = {gm_count} (Dashboard dash-stat-gm should match)")

    def test_no_mine_flag_public_rows_also_hydrated(self, gm_headers):
        r = requests.get(f"{BASE_URL}/api/campaigns", headers=gm_headers, timeout=15)
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) > 0
        for row in rows:
            assert "is_gm" in row
            assert "is_member" in row

    def test_detail_and_list_flags_consistent(self, gm_headers):
        r = requests.get(f"{BASE_URL}/api/campaigns?mine=true", headers=gm_headers, timeout=15)
        rows = r.json()
        gm_rows = [r for r in rows if r.get("is_gm")]
        assert len(gm_rows) > 0
        cid = gm_rows[0]["id"]
        d = requests.get(f"{BASE_URL}/api/campaigns/{cid}", headers=gm_headers, timeout=15)
        assert d.status_code == 200
        detail = d.json()
        assert detail.get("is_gm") == gm_rows[0]["is_gm"]
        assert detail.get("is_member") == gm_rows[0]["is_member"]
