"""V6.25.38 — Gazette / News system.

Covers:
  * POST   /api/campaigns/{cid}/news/articles      — manual create (GM only)
  * GET    /api/campaigns/{cid}/news/articles      — list (any seated)
  * PATCH  /api/campaigns/{cid}/news/articles/{id} — edit (GM only)
  * DELETE /api/campaigns/{cid}/news/articles/{id} — delete (GM only)
  * POST   /api/campaigns/{cid}/news/issues        — Press the Issue (GM only)
  * GET    /api/campaigns/{cid}/news/issues        — list issues
  * POST   /api/campaigns/{cid}/news/log-kill      — record a kill (GM only)
  * GET    /api/campaigns/{cid}/news/leaderboards  — kills/xp/sessions/players
  * GET    /api/public/news/{slug}/issues/latest   — public, no auth
  * GET    /api/public/news/{slug}/leaderboards    — public, no auth
"""
import os
import requests

API = os.environ["REACT_APP_BACKEND_URL"] = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
)
API = f"{API}/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"
SEEDED_CID = "af461ae004364002932f93c5b71cd483"  # Evereantha BESM (preview-pod seed)


def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json().get("token") or r.json()["access_token"]


def _h(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def _ensure_published(tok: str) -> str:
    """Make sure the seeded campaign is `discover_published` so public
    routes can reach it. Returns the slug."""
    r = requests.post(
        f"{API}/campaigns/{SEEDED_CID}/discover-publish",
        json={"blurb": "Gazette test fixture"},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["slug"]


class TestArticleCRUD:
    def test_unauth_create_blocked(self):
        r = requests.post(f"{API}/campaigns/{SEEDED_CID}/news/articles",
                          json={"headline": "X", "body": "Y", "column": "front"},
                          timeout=10)
        assert r.status_code in (401, 403)

    def test_admin_lifecycle(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # create
        r = requests.post(
            f"{API}/campaigns/{SEEDED_CID}/news/articles",
            json={"headline": "Test Headline", "kicker": "TEST", "byline": "By Pytest",
                  "body": "A body of the test article.", "column": "front"},
            headers=_h(tok), timeout=10,
        )
        assert r.status_code == 200, r.text
        aid = r.json()["id"]
        assert r.json()["status"] == "draft"
        assert r.json()["generated_by_llm"] is False
        # patch — approve
        r = requests.patch(f"{API}/campaigns/{SEEDED_CID}/news/articles/{aid}",
                           json={"status": "approved"}, headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "approved"
        # cannot patch to published directly
        r = requests.patch(f"{API}/campaigns/{SEEDED_CID}/news/articles/{aid}",
                           json={"status": "published"}, headers=_h(tok), timeout=10)
        assert r.status_code == 400
        # list contains it
        r = requests.get(f"{API}/campaigns/{SEEDED_CID}/news/articles",
                         headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert any(a["id"] == aid for a in r.json()["articles"])
        # delete
        r = requests.delete(f"{API}/campaigns/{SEEDED_CID}/news/articles/{aid}",
                            headers=_h(tok), timeout=10)
        assert r.status_code == 200

    def test_invalid_column_400(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        r = requests.post(
            f"{API}/campaigns/{SEEDED_CID}/news/articles",
            json={"headline": "h", "body": "b", "column": "garbage"},
            headers=_h(tok), timeout=10,
        )
        assert r.status_code == 400


class TestPressTheIssue:
    def test_no_approved_returns_400(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # Drain any approved articles first
        r = requests.get(f"{API}/campaigns/{SEEDED_CID}/news/articles",
                         headers=_h(tok), timeout=10)
        for a in r.json()["articles"]:
            if a["status"] == "approved":
                requests.patch(f"{API}/campaigns/{SEEDED_CID}/news/articles/{a['id']}",
                               json={"status": "draft"}, headers=_h(tok), timeout=10)
        r = requests.post(f"{API}/campaigns/{SEEDED_CID}/news/issues", json={},
                          headers=_h(tok), timeout=10)
        assert r.status_code == 400

    def test_press_lifecycle(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # Seed an approved article
        c = requests.post(
            f"{API}/campaigns/{SEEDED_CID}/news/articles",
            json={"headline": "Press Test", "body": "Body", "column": "front"},
            headers=_h(tok), timeout=10,
        ).json()
        aid = c["id"]
        requests.patch(f"{API}/campaigns/{SEEDED_CID}/news/articles/{aid}",
                       json={"status": "approved"}, headers=_h(tok), timeout=10)
        # Press
        r = requests.post(f"{API}/campaigns/{SEEDED_CID}/news/issues",
                          json={"masthead": "Test Daily", "date_label": "May 9 1885"},
                          headers=_h(tok), timeout=10)
        assert r.status_code == 200, r.text
        issue = r.json()
        assert issue["issue_number"] >= 1
        assert aid in issue["article_ids"]
        # The article is now published, locked from press again
        r = requests.get(f"{API}/campaigns/{SEEDED_CID}/news/articles",
                         headers=_h(tok), timeout=10)
        a = next(x for x in r.json()["articles"] if x["id"] == aid)
        assert a["status"] == "published"
        assert a["issue_id"] == issue["id"]
        # Cleanup
        requests.delete(f"{API}/campaigns/{SEEDED_CID}/news/articles/{aid}",
                        headers=_h(tok), timeout=10)


class TestKillsAndLeaderboards:
    def test_log_kill_and_leaderboard(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        chars = requests.get(f"{API}/campaigns/{SEEDED_CID}/characters",
                             headers=_h(tok), timeout=10).json()
        assert len(chars) >= 1, "No characters on seeded BESM campaign"
        char = chars[0]
        r = requests.post(
            f"{API}/campaigns/{SEEDED_CID}/news/log-kill",
            json={"character_id": char["id"], "foe_name": "Pytest Foe", "foe_kind": "test"},
            headers=_h(tok), timeout=10,
        )
        assert r.status_code == 200, r.text
        assert r.json()["character_name"] == char["name"]
        # Leaderboard reflects it
        r = requests.get(f"{API}/campaigns/{SEEDED_CID}/news/leaderboards",
                         headers=_h(tok), timeout=10)
        assert r.status_code == 200
        kills = r.json()["kills"]
        match = next((k for k in kills if k["character_id"] == char["id"]), None)
        assert match is not None
        assert match["kills"] >= 1


class TestPublicSurfaces:
    def test_public_endpoints_no_auth(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        slug = _ensure_published(tok)
        # latest issue (no auth)
        r = requests.get(f"{API}/public/news/{slug}/issues/latest", timeout=10)
        assert r.status_code == 200, r.text
        assert "campaign" in r.json()
        # leaderboards
        r = requests.get(f"{API}/public/news/{slug}/leaderboards", timeout=10)
        assert r.status_code == 200
        assert "kills" in r.json()
        assert "xp" in r.json()

    def test_public_404_on_unknown_slug(self):
        r = requests.get(f"{API}/public/news/no-such-slug-12345/issues/latest", timeout=10)
        assert r.status_code == 404
