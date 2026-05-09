"""V6.25.13 — Public Discover Showcase backend tests.

Exercises:
  * GET  /api/public/discover                   — list / filter
  * GET  /api/public/discover/{slug}            — detail / 404
  * POST /api/campaigns/{cid}/discover-publish  — auth/role enforcement + slug uniqueness
  * DELETE /api/campaigns/{cid}/discover-publish
  * Showcase node visibility filtering (shared only).
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://campaign-hub-288.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PASSWORD = "PieGod08!!"
SEEDED_SLUG = "apocophea-veil"
SEEDED_CID = "81ffab383c004f9d817b6cf5f0f477dc"


# ---- fixtures --------------------------------------------------------------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
    }, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:160]}")
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def non_admin_headers():
    """Register a fresh GM user to exercise 403 paths."""
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_nongm_{suffix}@tablegnostic-test.com"
    pwd = "TestPass123!"
    r = requests.post(f"{API}/auth/register", json={
        "email": email, "password": pwd, "name": f"TestGM-{suffix}",
        "display_name": f"TestGM-{suffix}", "role": "gm",
    }, timeout=15)
    if r.status_code not in (200, 201):
        pytest.skip(f"Could not register non-admin user: {r.status_code} {r.text[:160]}")
    tok = r.json().get("access_token") or r.json().get("token")
    if not tok:
        login = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=15)
        tok = login.json().get("access_token") or login.json().get("token")
    assert tok
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ---- public list -----------------------------------------------------------
class TestPublicDiscoverList:
    def test_list_no_auth_returns_200_with_shape(self):
        r = requests.get(f"{API}/public/discover", timeout=10)
        assert r.status_code == 200
        body = r.json()
        for k in ("items", "total", "limit", "skip"):
            assert k in body, f"missing key {k} in {body}"
        assert isinstance(body["items"], list)
        assert any(it["slug"] == SEEDED_SLUG for it in body["items"]), \
            f"seeded slug {SEEDED_SLUG} missing from items"

    def test_filter_by_system(self):
        r = requests.get(f"{API}/public/discover", params={"system": "besm-4e"}, timeout=10)
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(it["system_id"] == "besm-4e" for it in items)
        assert any(it["slug"] == SEEDED_SLUG for it in items)

    def test_filter_by_q_apocophea(self):
        r = requests.get(f"{API}/public/discover", params={"q": "apocophea"}, timeout=10)
        assert r.status_code == 200
        slugs = [it["slug"] for it in r.json()["items"]]
        assert SEEDED_SLUG in slugs

    def test_filter_by_unknown_system_excludes_seed(self):
        r = requests.get(f"{API}/public/discover", params={"system": "no-such-system"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["items"] == []


# ---- public detail ---------------------------------------------------------
class TestPublicDiscoverDetail:
    def test_seeded_slug_returns_full_payload(self):
        r = requests.get(f"{API}/public/discover/{SEEDED_SLUG}", timeout=15)
        assert r.status_code == 200
        body = r.json()
        for k in ("campaign", "nodes", "edges", "marketplace", "canon", "stats"):
            assert k in body
        assert body["campaign"]["slug"] == SEEDED_SLUG
        assert body["campaign"]["name"].lower() == "apocophea veil"
        assert body["campaign"]["gm_name"] == "GMFran"
        # Should be at least the 5 seeded shared nodes.
        node_titles = {n.get("title") for n in body["nodes"]}
        expected = {
            "Eli the Apprentice", "The Forge-Cathedral", "The Apocophea Guild",
            "The Cooling Heart", "The Sealed Vault",
        }
        missing = expected - node_titles
        assert not missing, f"missing seeded nodes: {missing}; got titles {node_titles}"
        # Every node must be visibility='shared' (gm_only must NOT leak).
        for n in body["nodes"]:
            assert n.get("visibility") == "shared", f"non-shared node leaked: {n}"

    def test_unknown_slug_returns_404(self):
        r = requests.get(f"{API}/public/discover/no-such-slug-xyz", timeout=10)
        assert r.status_code == 404


# ---- publish/unpublish -----------------------------------------------------
class TestDiscoverPublish:
    def test_publish_no_auth_returns_401(self):
        r = requests.post(f"{API}/campaigns/{SEEDED_CID}/discover-publish", json={}, timeout=10)
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_publish_non_gm_returns_403(self, non_admin_headers):
        r = requests.post(f"{API}/campaigns/{SEEDED_CID}/discover-publish",
                          json={}, headers=non_admin_headers, timeout=10)
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text[:160]}"

    def test_publish_as_gm_returns_ok(self, admin_headers):
        r = requests.post(f"{API}/campaigns/{SEEDED_CID}/discover-publish",
                          json={}, headers=admin_headers, timeout=15)
        assert r.status_code == 200, f"got {r.status_code} {r.text[:200]}"
        body = r.json()
        assert body["ok"] is True
        assert body["published"] is True
        assert body["slug"] == SEEDED_SLUG


# ---- slug uniqueness + delete round-trip -----------------------------------
class TestSlugUniquenessAndUnpublish:
    """Creates a 2nd 'Apocophea Veil' campaign as GMFran, publishes it, asserts
    distinct slug. Then unpublishes the seeded campaign and asserts the public
    GET 404s, and re-publishes to restore the seeded state."""

    def test_slug_collision_increments_suffix(self, admin_headers):
        # Create a 2nd campaign with the same name.
        create = requests.post(f"{API}/campaigns", json={
            "name": "Apocophea Veil",
            "system_id": "besm-4e",
            "description": "TEST_ duplicate-name campaign for slug uniqueness check.",
        }, headers=admin_headers, timeout=15)
        if create.status_code not in (200, 201):
            pytest.skip(f"campaign create failed: {create.status_code} {create.text[:160]}")
        cid2 = create.json().get("id") or create.json().get("campaign", {}).get("id")
        assert cid2, f"no id in {create.json()}"
        try:
            pub = requests.post(f"{API}/campaigns/{cid2}/discover-publish",
                                json={}, headers=admin_headers, timeout=15)
            assert pub.status_code == 200, f"{pub.status_code} {pub.text[:160]}"
            slug2 = pub.json()["slug"]
            assert slug2 != SEEDED_SLUG, f"expected distinct slug, got '{slug2}'"
            assert slug2.startswith("apocophea-veil-"), f"unexpected slug pattern: {slug2}"
            # And it should be reachable.
            det = requests.get(f"{API}/public/discover/{slug2}", timeout=10)
            assert det.status_code == 200
            assert det.json()["campaign"]["id"] == cid2
        finally:
            # Cleanup: unpublish + delete.
            requests.delete(f"{API}/campaigns/{cid2}/discover-publish",
                            headers=admin_headers, timeout=10)
            requests.delete(f"{API}/campaigns/{cid2}",
                            headers=admin_headers, timeout=10)

    def test_unpublish_then_repub_seeded(self, admin_headers):
        # Unpublish seeded.
        d = requests.delete(f"{API}/campaigns/{SEEDED_CID}/discover-publish",
                            headers=admin_headers, timeout=10)
        assert d.status_code == 200, f"{d.status_code} {d.text[:160]}"
        body = d.json()
        assert body["ok"] is True and body["published"] is False
        # Public GET should now 404.
        gone = requests.get(f"{API}/public/discover/{SEEDED_SLUG}", timeout=10)
        assert gone.status_code == 404
        # Restore (CRITICAL — this is the seeded fixture for the rest of the test run).
        rp = requests.post(f"{API}/campaigns/{SEEDED_CID}/discover-publish",
                           json={}, headers=admin_headers, timeout=15)
        assert rp.status_code == 200
        assert rp.json()["slug"] == SEEDED_SLUG
        # And confirm restored.
        back = requests.get(f"{API}/public/discover/{SEEDED_SLUG}", timeout=10)
        assert back.status_code == 200


# ---- node visibility filter ------------------------------------------------
class TestSharedNodesOnly:
    def test_gm_only_node_does_not_leak(self, admin_headers):
        # Create a gm_only node on the seeded campaign and ensure the public
        # showcase does NOT include it.
        before = requests.get(f"{API}/public/discover/{SEEDED_SLUG}", timeout=10).json()
        before_ids = {n["id"] for n in before["nodes"]}
        title = f"TEST_gm_only_{uuid.uuid4().hex[:8]}"
        node_ids_to_cleanup = []
        # Try a couple of likely endpoints; whichever works we use.
        candidates = [
            (f"{API}/campaigns/{SEEDED_CID}/nodes",
             {"title": title, "type": "lore", "content": "secret", "visibility": "gm_only"}),
            (f"{API}/nodes",
             {"campaign_id": SEEDED_CID, "title": title, "type": "lore",
              "content": "secret", "visibility": "gm_only"}),
        ]
        nid = None
        for url, payload in candidates:
            r = requests.post(url, json=payload, headers=admin_headers, timeout=10)
            if r.status_code in (200, 201):
                body = r.json() if r.text else {}
                nid = body.get("id") or body.get("node", {}).get("id")
                if nid:
                    node_ids_to_cleanup.append((url, nid))
                    break
        if not nid:
            pytest.skip("Could not create a gm_only node via known endpoints — "
                        "test relies on existing visibility filter only.")
        try:
            after = requests.get(f"{API}/public/discover/{SEEDED_SLUG}", timeout=10).json()
            after_ids = {n["id"] for n in after["nodes"]}
            assert nid not in after_ids, (
                f"gm_only node {nid} leaked into public showcase"
            )
            # And it should not have appeared as a new shared id either.
            new_ids = after_ids - before_ids
            assert nid not in new_ids
        finally:
            for url, _id in node_ids_to_cleanup:
                # Try DELETE on the same path style.
                if url.endswith("/nodes"):
                    requests.delete(f"{url}/{_id}", headers=admin_headers, timeout=10)
                else:
                    requests.delete(f"{url}/{_id}", headers=admin_headers, timeout=10)
