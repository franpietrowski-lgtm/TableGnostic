"""V6.25.39 — Admin moderation console endpoints.

Covers:
  * GET    /api/admin/campaigns           — admin-only list
  * GET    /api/admin/showcases           — discover_published=true
  * GET    /api/admin/marketplace         — all listings
  * GET    /api/admin/users               — minimal user list
  * GET    /api/admin/audit               — paginated audit log
  * POST   /api/admin/campaigns/{cid}/force-unpublish
  * POST   /api/flags                     — any auth user files a flag
  * GET    /api/admin/flags               — admin lists flag queue
  * PATCH  /api/admin/flags/{fid}         — admin reviews flag
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


class TestAdminGates:
    def test_list_campaigns_admin_only(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        r = requests.get(f"{API}/admin/campaigns", headers=_h(tok), timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body and "total" in body
        assert body["total"] >= 1

    def test_no_auth_403_on_admin_endpoints(self):
        r = requests.get(f"{API}/admin/campaigns", timeout=10)
        assert r.status_code in (401, 403)

    def test_admin_showcases(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        r = requests.get(f"{API}/admin/showcases", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        # Every item must be discover_published=true
        for c in r.json()["items"]:
            assert c.get("discover_published") is True

    def test_admin_users_admin_only(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # Use the new `q` filter — admin is otherwise paginated past the
        # 500-row default given the test-user accretion in this pod.
        r = requests.get(f"{API}/admin/users?q=tablegnostic-admin", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        rows = r.json()["items"]
        assert any(u["email"] == ADMIN_EMAIL and u.get("role") == "admin" for u in rows), \
            "super-admin user should be findable via /admin/users?q=…"


class TestFlags:
    def test_file_flag_then_admin_dismiss(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # File
        r = requests.post(
            f"{API}/flags", headers=_h(tok),
            json={"target_kind": "campaign", "target_id": MAIDEN_CID,
                  "reason": "pytest moderation flag"},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        fid = r.json()["id"]
        assert r.json()["status"] == "open"
        # List queue
        r = requests.get(f"{API}/admin/flags?status=open", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert any(f["id"] == fid for f in r.json()["items"])
        # Dismiss
        r = requests.patch(f"{API}/admin/flags/{fid}",
                           json={"status": "dismissed", "notes": "test pass"},
                           headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "dismissed"
        # Bad status rejected
        r = requests.patch(f"{API}/admin/flags/{fid}",
                           json={"status": "garbage"},
                           headers=_h(tok), timeout=10)
        assert r.status_code == 422


class TestAuditTrail:
    def test_audit_log_records_actions(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # Trigger an auditable action — file & dismiss a flag.
        r = requests.post(
            f"{API}/flags", headers=_h(tok),
            json={"target_kind": "campaign", "target_id": MAIDEN_CID,
                  "reason": "audit trail test"},
            timeout=10,
        )
        fid = r.json()["id"]
        requests.patch(f"{API}/admin/flags/{fid}",
                       json={"status": "dismissed", "notes": "audit test"},
                       headers=_h(tok), timeout=10)
        # Read audit
        r = requests.get(f"{API}/admin/audit", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 1
        # Most recent entry should be our flag dismissal.
        latest = items[0]
        assert latest["actor_email"] == ADMIN_EMAIL
        assert latest["action"] in {"flag_dismissed", "flag_actioned"}


class TestForceUnpublish:
    def test_unpublish_then_re_publish_admin_audited(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        # First make sure the Maiden campaign is published.
        requests.post(f"{API}/campaigns/{MAIDEN_CID}/discover-publish",
                      json={"blurb": "audit test"}, headers=_h(tok), timeout=10)
        # Admin force-unpublish via admin route
        r = requests.post(f"{API}/admin/campaigns/{MAIDEN_CID}/force-unpublish",
                          json={"reason": "audit test"}, headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert r.json()["published"] is False
        # Re-publish for downstream tests
        requests.post(f"{API}/campaigns/{MAIDEN_CID}/discover-publish",
                      json={"blurb": "audit test restore"}, headers=_h(tok), timeout=10)
