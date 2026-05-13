"""V6.25.41 — SEO + cost-balance + change-request approval queue."""
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


class TestSEO:
    def test_sitemap_xml(self):
        r = requests.get(f"{API}/seo/sitemap.xml", timeout=10)
        assert r.status_code == 200
        assert "application/xml" in r.headers["content-type"]
        body = r.text
        assert "<urlset" in body
        assert "<loc>https://tablegnostic.com/" in body
        # Public showcase should be enumerated (the seeded Maiden campaign).
        assert "/discover/evereantha-the-maiden-adventure" in body

    def test_robots_txt(self):
        r = requests.get(f"{API}/seo/robots.txt", timeout=10)
        assert r.status_code == 200
        assert "User-agent: *" in r.text
        assert "Disallow: /app" in r.text
        assert "Sitemap:" in r.text

    def test_og_svg_for_published_showcase(self):
        r = requests.get(f"{API}/seo/og/evereantha-the-maiden-adventure.svg", timeout=10)
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/svg+xml"
        assert b"<svg" in r.content
        assert b"Maiden" in r.content or b"MAIDEN" in r.content.upper()

    def test_og_svg_404_unknown_slug(self):
        r = requests.get(f"{API}/seo/og/no-such-thing.svg", timeout=10)
        assert r.status_code == 404


class TestCostBalance:
    def test_preview_returns_shape(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        chars = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                              headers=_h(tok), timeout=10).json()
        assert len(chars) >= 1
        ch = chars[0]
        r = requests.post(f"{API}/convert/preview-cost-balance",
                          headers=_h(tok),
                          json={"source_character_id": ch["id"],
                                "target_system": "cypher"},
                          timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("source_budget", "target_budget", "delta", "delta_pct",
                  "within_tolerance", "tolerance_pct", "notes"):
            assert k in d
        assert d["tolerance_pct"] == 10.0
        assert isinstance(d["notes"], list)

    def test_preview_unsupported_400(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        chars = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                              headers=_h(tok), timeout=10).json()
        r = requests.post(f"{API}/convert/preview-cost-balance",
                          headers=_h(tok),
                          json={"source_character_id": chars[0]["id"],
                                "target_system": "garbage"},
                          timeout=10)
        assert r.status_code == 400


class TestChangeRequests:
    def test_approve_lifecycle(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        chars = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                              headers=_h(tok), timeout=10).json()
        chid = chars[0]["id"]
        # Submit
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests",
                          headers=_h(tok),
                          json={"kind": "character", "target_id": chid,
                                "summary": "pytest concept bump",
                                "proposed_value": {"concept": "pytest concept v1"}},
                          timeout=10)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        assert r.json()["status"] == "pending"
        # Approve
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests/{rid}/approve",
                          headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "approved"
        assert r.json()["applied_result"]["modified"] == 1
        # Double-approve rejected
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests/{rid}/approve",
                          headers=_h(tok), timeout=10)
        assert r.status_code == 409

    def test_reject_lifecycle(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        chars = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                              headers=_h(tok), timeout=10).json()
        chid = chars[0]["id"]
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests",
                          headers=_h(tok),
                          json={"kind": "character", "target_id": chid,
                                "summary": "reject test",
                                "proposed_value": {"concept": "should never apply"}},
                          timeout=10)
        rid = r.json()["id"]
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests/{rid}/reject",
                          headers=_h(tok),
                          json={"reason": "Not approved by GM"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"
        assert r.json()["review_reason"] == "Not approved by GM"

    def test_forbidden_fields_stripped_on_approve(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        chars = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                              headers=_h(tok), timeout=10).json()
        chid = chars[0]["id"]
        # Mix forbidden + safe: GM can write `concept`, must strip `owner_id`.
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests",
                          headers=_h(tok),
                          json={"kind": "character", "target_id": chid,
                                "summary": "Mixed escalation test",
                                "proposed_value": {"owner_id": "hacker",
                                                    "system_id": "garbage",
                                                    "concept": "mixed-safe"}},
                          timeout=10)
        rid = r.json()["id"]
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests/{rid}/approve",
                          headers=_h(tok), timeout=10)
        assert r.status_code == 200
        # concept persisted, but owner_id/system_id stripped.
        chk = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                            headers=_h(tok), timeout=10).json()
        match = next((c for c in chk if c["id"] == chid), None)
        assert match is not None
        assert match.get("owner_id") != "hacker", \
            "forbidden field `owner_id` must NEVER be writable via change-requests queue"
        assert match.get("system_id") != "garbage", \
            "forbidden field `system_id` must NEVER be writable via change-requests queue"

    def test_all_forbidden_no_write(self):
        """When the proposed_value is 100% forbidden fields, no DB write
        should occur (clean dict ends up empty)."""
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        chars = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                              headers=_h(tok), timeout=10).json()
        chid = chars[0]["id"]
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests",
                          headers=_h(tok),
                          json={"kind": "character", "target_id": chid,
                                "summary": "All-forbidden test",
                                "proposed_value": {"owner_id": "hacker"}},
                          timeout=10)
        rid = r.json()["id"]
        r = requests.post(f"{API}/campaigns/{MAIDEN_CID}/change-requests/{rid}/approve",
                          headers=_h(tok), timeout=10)
        assert r.status_code == 200
        # `applied_result` reflects no DB write happened.
        assert "modified" not in r.json()["applied_result"]

    def test_settings_toggle_gm_only(self):
        tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        r = requests.patch(f"{API}/campaigns/{MAIDEN_CID}/settings/approval",
                           headers=_h(tok),
                           json={"gm_approval_required": True}, timeout=10)
        assert r.status_code == 200
        assert r.json()["gm_approval_required"] is True
        # Restore
        requests.patch(f"{API}/campaigns/{MAIDEN_CID}/settings/approval",
                       headers=_h(tok),
                       json={"gm_approval_required": False}, timeout=10)
