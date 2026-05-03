"""V6.20 backend tests — Cut D (World Creation Tree, Codex Links),
Surprise Bag/Scene-Break PBP auto-post, and admin repair-dnd-states.

Auth: GMFran admin (franpietrowski@gmail.com / PieGod08!!),
      Aurora player (albanaszak@ymail.com / AuroraTest123!).
Live anime-5e campaign id passed via env or hardcoded:
2d31c25354e4415f84a31704fe78a795.
"""
import os
import pytest
import requests

def _read_base_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return ""

BASE_URL = _read_base_url()
ANIME_CID = "2d31c25354e4415f84a31704fe78a795"

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"
PLAYER_EMAIL = "albanaszak@ymail.com"
PLAYER_PASS = "AuroraTest123!"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password},
                      timeout=15)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json().get("access_token")


@pytest.fixture(scope="module")
def gm_token():
    return _login(GM_EMAIL, GM_PASS)


@pytest.fixture(scope="module")
def player_token():
    return _login(PLAYER_EMAIL, PLAYER_PASS)


def _h(t):
    return {"Authorization": f"Bearer {t}"}


# ── Bug #3 backfill: admin repair-dnd-states ────────────────────────────
class TestRepairDndStates:
    def test_admin_only(self, player_token):
        r = requests.post(f"{BASE_URL}/api/admin/repair-dnd-states",
                          headers=_h(player_token), timeout=30)
        assert r.status_code == 403

    def test_admin_succeeds(self, gm_token):
        r = requests.post(f"{BASE_URL}/api/admin/repair-dnd-states",
                          headers=_h(gm_token), timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert isinstance(data.get("scanned"), int)
        assert isinstance(data.get("repaired"), int)
        assert data["scanned"] >= 0


# ── Cut D · Creation Tree ───────────────────────────────────────────────
class TestCreationTree:
    def test_get_creation_tree(self, gm_token):
        r = requests.get(f"{BASE_URL}/api/campaigns/{ANIME_CID}/creation-tree",
                         headers=_h(gm_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["campaign_id"] == ANIME_CID
        sch = data["schema"]
        assert set(sch["pillars"].keys()) == {"Population", "Geography", "History"}
        assert len(sch["cross_pillar_links"]) >= 18
        assert "populated" in data
        assert "node_count" in data


# ── Cut D · Creation Myth ───────────────────────────────────────────────
class TestCreationMyth:
    created_id = None

    def test_create_root_myth(self, gm_token):
        body = {"title": "TEST_V620 Origin",
                "body": "In the beginning was the test.",
                "pillar_seeds": {"Population": "first humans"}}
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/creation-myths",
            json=body, headers=_h(gm_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        myth = data["myth"]
        assert myth["title"] == "TEST_V620 Origin"
        assert "id" in myth
        assert "_id" not in myth
        TestCreationMyth.created_id = myth["id"]

    def test_list_includes_created(self, gm_token):
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/creation-myths",
            headers=_h(gm_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        ids = [m["id"] for m in data["myths"]]
        assert TestCreationMyth.created_id in ids

    def test_player_blocked_from_create(self, player_token):
        body = {"title": "TEST_V620 player", "body": "hack"}
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/creation-myths",
            json=body, headers=_h(player_token), timeout=15)
        assert r.status_code == 403

    def test_cleanup(self, gm_token):
        if TestCreationMyth.created_id:
            r = requests.delete(
                f"{BASE_URL}/api/campaigns/{ANIME_CID}/creation-myths/{TestCreationMyth.created_id}",
                headers=_h(gm_token), timeout=15)
            assert r.status_code == 200


# ── Cut D · Codex Links ─────────────────────────────────────────────────
class TestCodexLinks:
    edge_id = None

    def test_create_edge(self, gm_token):
        body = {"source_id": "test-src", "target_id": "test-tgt",
                "relationship_type": "TEST_V620_allies",
                "color": "#C9A876", "weight": 7,
                "bidirectional": True, "notes": "test"}
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/codex-links",
            json=body, headers=_h(gm_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        edge = data["edge"]
        assert edge["weight"] == 7
        assert edge["color"] == "#C9A876"
        assert edge["relationship_type"] == "TEST_V620_allies"
        assert "_id" not in edge
        TestCodexLinks.edge_id = edge["id"]

    def test_weight_validation(self, gm_token):
        body = {"source_id": "a", "target_id": "b", "weight": 99}
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/codex-links",
            json=body, headers=_h(gm_token), timeout=15)
        assert r.status_code == 422

    def test_color_validation(self, gm_token):
        body = {"source_id": "a", "target_id": "b", "color": "notacolor"}
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/codex-links",
            json=body, headers=_h(gm_token), timeout=15)
        assert r.status_code == 422

    def test_list_includes(self, gm_token):
        r = requests.get(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/codex-links",
            headers=_h(gm_token), timeout=15)
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()["edges"]]
        assert TestCodexLinks.edge_id in ids

    def test_cleanup(self, gm_token):
        if TestCodexLinks.edge_id:
            r = requests.delete(
                f"{BASE_URL}/api/campaigns/{ANIME_CID}/codex-links/{TestCodexLinks.edge_id}",
                headers=_h(gm_token), timeout=15)
            assert r.status_code == 200


# ── Surprise Bag draw with PBP auto-post ────────────────────────────────
class TestSurpriseBagDraw:
    def test_draw_returns_posted_flag(self, gm_token):
        # Ensure seeded
        requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/surprise-bag/seed",
            headers=_h(gm_token), timeout=15)
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/surprise-bag/draw",
            json={}, headers=_h(gm_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "drawn" in data
        assert "posted_to_session" in data
        assert isinstance(data["posted_to_session"], bool)
        assert "_id" not in data["drawn"]

    def test_player_blocked(self, player_token):
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/surprise-bag/draw",
            json={}, headers=_h(player_token), timeout=15)
        assert r.status_code == 403


# ── Scene-Break draw with PBP auto-post ─────────────────────────────────
class TestSceneBreakDraw:
    def test_draw_returns_posted_flag(self, gm_token):
        requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/scene-break-cards/seed",
            headers=_h(gm_token), timeout=15)
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CID}/scene-break-cards/draw",
            json={}, headers=_h(gm_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "drawn" in data
        assert "posted_to_session" in data
        assert "_id" not in data["drawn"]
