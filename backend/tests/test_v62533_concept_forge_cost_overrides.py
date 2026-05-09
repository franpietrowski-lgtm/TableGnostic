"""V6.25.33 — Concept Forge + GM Cost Overrides backend regression."""
import os
import time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://rules-forge.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"
PLAYER_PASS = "PieBan18!!"


# ── Auth helpers ───────────────────────────────────────────────────
def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password},
                      timeout=15)
    assert r.status_code == 200, f"Login failed {r.status_code}: {r.text}"
    j = r.json()
    return j.get("access_token") or j.get("token")


@pytest.fixture(scope="module")
def gm_token():
    return _login(GM_EMAIL, GM_PASS)


@pytest.fixture(scope="module")
def player_token():
    # Same email, different password = different persona per V6.25.30
    return _login(GM_EMAIL, PLAYER_PASS)


@pytest.fixture(scope="module")
def gm_headers(gm_token):
    return {"Authorization": f"Bearer {gm_token}"}


@pytest.fixture(scope="module")
def player_headers(player_token):
    return {"Authorization": f"Bearer {player_token}"}


@pytest.fixture(scope="module")
def besm_campaign_id(gm_headers):
    """Find a BESM 4E campaign owned by GM."""
    r = requests.get(f"{API}/campaigns", headers=gm_headers, timeout=15)
    assert r.status_code == 200, r.text
    camps = r.json() if isinstance(r.json(), list) else r.json().get("campaigns", [])
    me = requests.get(f"{API}/auth/me", headers=gm_headers, timeout=10).json()
    gm_id = me.get("id") or me.get("user", {}).get("id")
    for c in camps:
        if c.get("system_id") == "besm-4e" and c.get("gm_id") == gm_id:
            return c["id"]
    pytest.skip("No BESM 4E GM campaign found for GMFran")


@pytest.fixture(scope="module")
def non_besm_campaign_id(gm_headers):
    r = requests.get(f"{API}/campaigns", headers=gm_headers, timeout=15)
    camps = r.json() if isinstance(r.json(), list) else r.json().get("campaigns", [])
    me = requests.get(f"{API}/auth/me", headers=gm_headers, timeout=10).json()
    gm_id = me.get("id") or me.get("user", {}).get("id")
    for c in camps:
        if c.get("system_id") in ("dnd-5e", "cypher") and c.get("gm_id") == gm_id:
            return c["id"]
    pytest.skip("No non-BESM GM campaign found")


# ── Cost Overrides ─────────────────────────────────────────────────
class TestCostOverrides:
    def test_list_initial(self, gm_headers, besm_campaign_id):
        r = requests.get(f"{API}/campaigns/{besm_campaign_id}/cost-overrides",
                         headers=gm_headers, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "overrides" in body and "count" in body
        assert isinstance(body["overrides"], list)

    def test_upsert_create_then_idempotent(self, gm_headers, besm_campaign_id):
        # Cleanup any prior identical override for clean test
        r0 = requests.get(f"{API}/campaigns/{besm_campaign_id}/cost-overrides",
                          headers=gm_headers, timeout=10)
        for ov in r0.json().get("overrides", []):
            if ov.get("kind") == "attribute" and ov.get("name") == "Tough":
                requests.delete(
                    f"{API}/campaigns/{besm_campaign_id}/cost-overrides/{ov['id']}",
                    headers=gm_headers, timeout=10)

        body = {"kind": "attribute", "name": "Tough",
                "override_cost": 1, "note": "Aurea house rule"}
        r1 = requests.put(f"{API}/campaigns/{besm_campaign_id}/cost-overrides",
                          headers=gm_headers, json=body, timeout=10)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert d1["created"] is True
        assert d1["override"]["override_cost"] == 1
        assert d1["override"]["name"] == "Tough"

        r2 = requests.put(f"{API}/campaigns/{besm_campaign_id}/cost-overrides",
                          headers=gm_headers, json=body, timeout=10)
        assert r2.status_code == 200
        assert r2.json()["created"] is False
        # Save oid for later tests
        TestCostOverrides.oid = d1["override"]["id"]

    def test_patch_to_zero(self, gm_headers, besm_campaign_id):
        oid = TestCostOverrides.oid
        r = requests.patch(
            f"{API}/campaigns/{besm_campaign_id}/cost-overrides/{oid}",
            headers=gm_headers, json={"override_cost": 0}, timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["override"]["override_cost"] == 0

    def test_player_put_forbidden(self, player_headers, besm_campaign_id):
        body = {"kind": "attribute", "name": "Speed", "override_cost": 2}
        r = requests.put(f"{API}/campaigns/{besm_campaign_id}/cost-overrides",
                         headers=player_headers, json=body, timeout=10)
        assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"

    def test_bad_kind_400(self, gm_headers, besm_campaign_id):
        body = {"kind": "garbage", "name": "X", "override_cost": 1}
        r = requests.put(f"{API}/campaigns/{besm_campaign_id}/cost-overrides",
                         headers=gm_headers, json=body, timeout=10)
        assert r.status_code == 400, r.text

    def test_delete(self, gm_headers, besm_campaign_id):
        oid = TestCostOverrides.oid
        r = requests.delete(
            f"{API}/campaigns/{besm_campaign_id}/cost-overrides/{oid}",
            headers=gm_headers, timeout=10)
        assert r.status_code == 200
        assert r.json()["deleted"] == oid


# ── Concept Forge ──────────────────────────────────────────────────
_CONCEPT = (
    "A reformed thief turned wandering apothecary, blessed by a phoenix spirit, "
    "who heals villagers by burning bandages soaked in spirit fire. They carry "
    "a small bandolier of salves and an ember-lantern. Roughly 200 chars."
)


class TestConceptForge:
    draft_id = None

    def test_post_draft_besm(self, gm_headers, besm_campaign_id):
        body = {"concept_text": _CONCEPT}
        # LLM call may take 15-40s
        r = requests.post(
            f"{API}/campaigns/{besm_campaign_id}/concept-drafts",
            headers=gm_headers, json=body, timeout=90)
        assert r.status_code == 200, f"{r.status_code} {r.text[:500]}"
        draft = r.json()["draft"]
        assert draft["status"] == "pending"
        cands = draft["candidates"]
        assert isinstance(cands, list) and len(cands) == 2
        for c in cands:
            assert "title" in c and "summary" in c
            assert "stats" in c and isinstance(c["stats"], dict)
            assert "attributes" in c and "defects" in c
            assert "estimated_cp" in c
        TestConceptForge.draft_id = draft["id"]

    def test_post_draft_unsupported_system(self, gm_headers, non_besm_campaign_id):
        body = {"concept_text": _CONCEPT}
        r = requests.post(
            f"{API}/campaigns/{non_besm_campaign_id}/concept-drafts",
            headers=gm_headers, json=body, timeout=30)
        assert r.status_code == 400, r.text
        assert "besm" in r.text.lower() or "anime" in r.text.lower() \
            or "support" in r.text.lower()

    def test_list_player_sees_own(self, player_headers, besm_campaign_id):
        r = requests.get(f"{API}/campaigns/{besm_campaign_id}/concept-drafts",
                         headers=player_headers, timeout=10)
        if r.status_code == 403:
            pytest.skip("Player persona not seated at this BESM campaign")
        assert r.status_code == 200
        body = r.json()
        assert body["is_gm"] is False

    def test_list_gm_sees_all(self, gm_headers, besm_campaign_id):
        r = requests.get(f"{API}/campaigns/{besm_campaign_id}/concept-drafts",
                         headers=gm_headers, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["is_gm"] is True
        assert any(d["id"] == TestConceptForge.draft_id for d in body["drafts"])

    def test_commit_before_approval_400(self, gm_headers, besm_campaign_id):
        did = TestConceptForge.draft_id
        r = requests.post(
            f"{API}/campaigns/{besm_campaign_id}/concept-drafts/{did}/commit",
            headers=gm_headers, json={"picked_index": 0}, timeout=10)
        assert r.status_code == 400, r.text

    def test_gm_approve(self, gm_headers, besm_campaign_id):
        did = TestConceptForge.draft_id
        r = requests.patch(
            f"{API}/campaigns/{besm_campaign_id}/concept-drafts/{did}",
            headers=gm_headers,
            json={"status": "approved", "gm_notes": "looks good"},
            timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["draft"]["status"] == "approved"

    def test_commit_after_approval(self, gm_headers, besm_campaign_id):
        did = TestConceptForge.draft_id
        r = requests.post(
            f"{API}/campaigns/{besm_campaign_id}/concept-drafts/{did}/commit",
            headers=gm_headers, json={"picked_index": 0}, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["draft_id"] == did
        assert "picked" in body
        assert "title" in body["picked"]

    def test_delete_other_player_403(self, besm_campaign_id):
        # Create a draft as Aurora and try delete as GM-Player persona
        # Simpler: try delete with a fake user — skipping since we only have 2 personas
        # Use Aurora: albanaszak@ymail.com / AuroraTest123!
        try:
            aurora_tok = _login("albanaszak@ymail.com", "AuroraTest123!")
        except Exception:
            pytest.skip("Aurora login unavailable")
        aurora_headers = {"Authorization": f"Bearer {aurora_tok}"}
        # Aurora may not be seated — verify by GET; if 403, skip
        r = requests.get(f"{API}/campaigns/{besm_campaign_id}/concept-drafts",
                         headers=aurora_headers, timeout=10)
        if r.status_code != 200:
            pytest.skip("Aurora not seated at this campaign")
        did = TestConceptForge.draft_id
        r2 = requests.delete(
            f"{API}/campaigns/{besm_campaign_id}/concept-drafts/{did}",
            headers=aurora_headers, timeout=10)
        assert r2.status_code == 403

    def test_delete_as_requester(self, gm_headers, besm_campaign_id):
        did = TestConceptForge.draft_id
        r = requests.delete(
            f"{API}/campaigns/{besm_campaign_id}/concept-drafts/{did}",
            headers=gm_headers, timeout=10)
        assert r.status_code == 200
        assert r.json()["deleted"] == did
