"""V6.25.40 — Dynamic public endpoints + flag threads + roadmap CRUD.

Covers:
  * GET    /api/public/stats           — counters
  * GET    /api/public/marketplace     — public listings only
  * GET    /api/public/roadmap         — public=true items only
  * GET    /api/public/recent-gazettes — recently pressed issues
  * GET    /api/public/featured        — admin-curated or fallback
  * GET/POST/PATCH/DELETE /api/admin/roadmap
  * POST   /api/campaigns/{cid}/request-feature  (GM owner)
  * GET    /api/admin/featured-requests
  * POST   /api/admin/campaigns/{cid}/feature
  * GET    /api/flags/{fid}            — filer or admin only
  * POST   /api/flags/{fid}/messages   — filer or admin only
"""
import os
import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"
MAIDEN_CID = "af461ae004364002932f93c5b71cd483"


def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json().get("token") or r.json()["access_token"]


def _h(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


class TestPublicEndpoints:
    def test_stats_shape_no_auth(self):
        r = requests.get(f"{API}/public/stats", timeout=10)
        assert r.status_code == 200
        b = r.json()
        # Keys must be present (counters may be zero on a fresh pod).
        for k in ("campaigns", "public_campaigns", "characters",
                   "marketplace_listings", "gazettes_pressed", "codex_nodes"):
            assert k in b, f"missing key {k}"
            assert isinstance(b[k], int)

    def test_roadmap_public_filter(self):
        r = requests.get(f"{API}/public/roadmap", timeout=10)
        assert r.status_code == 200
        for it in r.json()["items"]:
            assert it.get("public") is True

    def test_featured_no_auth(self):
        r = requests.get(f"{API}/public/featured", timeout=10)
        assert r.status_code == 200
        # `item` may be None if no showcase is published.
        assert "item" in r.json()

    def test_marketplace_no_auth(self):
        r = requests.get(f"{API}/public/marketplace", timeout=10)
        assert r.status_code == 200
        # Output items must NOT contain private fields.
        for it in r.json()["items"]:
            for forbidden in ("buyer_id", "audit", "secret", "_id"):
                assert forbidden not in it

    def test_recent_gazettes(self):
        r = requests.get(f"{API}/public/recent-gazettes?limit=5", timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json()["items"], list)


class TestRoadmapCRUD:
    def test_admin_create_patch_delete(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # Create
        r = requests.post(f"{API}/admin/roadmap", headers=_h(tok),
                          json={"title": "Pytest item", "status": "later",
                                "body_md": "**testing**", "eta": "Q9", "order": 99},
                          timeout=10)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        assert r.json()["status"] == "later"
        # Patch
        r = requests.patch(f"{API}/admin/roadmap/{rid}", headers=_h(tok),
                           json={"status": "shipped"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "shipped"
        # Delete
        r = requests.delete(f"{API}/admin/roadmap/{rid}", headers=_h(tok), timeout=10)
        assert r.status_code == 200

    def test_admin_only(self):
        r = requests.post(f"{API}/admin/roadmap",
                          json={"title": "x", "status": "next"}, timeout=10)
        assert r.status_code in (401, 403)


class TestFeaturedFlow:
    def test_request_then_approve_then_clear(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # Request feature (admin is GM of the Maiden campaign now)
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/request-feature",
                          headers=_h(tok),
                          json={"requested": True, "note": "pytest"}, timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["requested"] is True
        # Admin approve
        r = requests.post(f"{API}/admin/campaigns/{MAIDEN_CID}/feature",
                          headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert r.json()["featured"] is True
        # Public reflects it
        r = requests.get(f"{API}/public/featured", timeout=10)
        item = r.json()["item"]
        assert item is not None
        assert item["id"] == MAIDEN_CID
        assert item["featured"] is True
        # Cleanup unfeature so other tests aren't sticky
        requests.delete(f"{API}/admin/campaigns/{MAIDEN_CID}/feature",
                         headers=_h(tok), timeout=10)


class TestFlagThreads:
    def test_post_message_and_read_thread(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # File a flag
        r = requests.post(f"{API}/flags", headers=_h(tok),
                          json={"target_kind": "campaign",
                                "target_id": MAIDEN_CID,
                                "reason": "pytest thread"},
                          timeout=10)
        fid = r.json()["id"]
        # Post a message
        r = requests.post(f"{API}/flags/{fid}/messages", headers=_h(tok),
                          json={"body": "Following up — please share evidence."},
                          timeout=10)
        assert r.status_code == 200
        assert r.json()["author_role"] == "admin"
        # Read thread
        r = requests.get(f"{API}/flags/{fid}", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["flag"]["id"] == fid
        assert len(body["messages"]) >= 1

    def test_thread_unauth_blocked(self):
        r = requests.get(f"{API}/flags/nonexistent", timeout=10)
        assert r.status_code in (401, 403, 404)
