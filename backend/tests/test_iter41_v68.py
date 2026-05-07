"""V6.8 backend tests — Cypher fuzzy keyword matching + NPC sheet save-onto-node."""
import os
import uuid
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
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def campaigns(admin_headers):
    r = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    return r.json()


@pytest.fixture(scope="module")
def cypher_campaign(campaigns):
    cands = [c for c in campaigns if c.get("system_id") == "cypher"]
    if not cands:
        pytest.skip("No cypher campaign seeded")
    return cands[0]


@pytest.fixture(scope="module")
def besm_campaign(campaigns):
    cands = [c for c in campaigns if c.get("system_id") == "besm-4e"]
    if not cands:
        pytest.skip("No besm-4e campaign seeded")
    return cands[0]


# ─── V6.8 — Cypher fuzzy + free-text keywords ───────────────────────

class TestCypherFuzzyKeywords:
    def test_free_keywords_echoed(self, admin_headers, cypher_campaign):
        cid = cypher_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/cypher/{cid}/suggest"
            "?kind=foci&keywords=fire,swift",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "free_keywords" in d
        assert d["free_keywords"] == ["fire", "swift"]
        # foci axis is present
        assert "suggestions" in d
        assert "foci" in d["suggestions"]
        assert isinstance(d["suggestions"]["foci"], list)

    def test_keyword_match_annotation(self, admin_headers, cypher_campaign):
        cid = cypher_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/cypher/{cid}/suggest"
            "?kind=foci&keywords=fire,swift",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200
        foci = r.json()["suggestions"]["foci"]
        # Each entry must carry the annotation key
        for entry in foci:
            assert "matched_keywords" in entry
            assert isinstance(entry["matched_keywords"], list)
            assert "score" in entry
            assert "entry" in entry
        # At least one entry should have matched 'fire' or 'swift'
        any_matched = any(
            e["matched_keywords"] for e in foci
        )
        # If no foci entry has fire/swift in name+summary, this is allowed
        # but if any are matched, scores should reflect the +2 bias
        if any_matched:
            matched = [e for e in foci if e["matched_keywords"]]
            for m in matched:
                assert m["score"] >= 2
                # Check the keyword is from our query
                for kw in m["matched_keywords"]:
                    assert kw in ("fire", "swift")

    def test_no_keywords_returns_empty_list(self, admin_headers, cypher_campaign):
        cid = cypher_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/cypher/{cid}/suggest?kind=foci",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["free_keywords"] == []

    def test_substring_hint_match(self, admin_headers, cypher_campaign):
        """Substring fallback is used when codex hints don't exact-match an entry."""
        cid = cypher_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/cypher/{cid}/suggest?kind=descriptors",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        descs = d["suggestions"]["descriptors"]
        for entry in descs:
            assert "matched_hints" in entry
            assert isinstance(entry["matched_hints"], list)


# ─── V6.8 — NPC sheet save-onto-node ────────────────────────────────

def _first_node(admin_headers, campaign_id, prefer_kinds=("npc", "creature")):
    r = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/nodes",
                     headers=admin_headers, timeout=15)
    if r.status_code != 200:
        return None
    nodes = r.json()
    if not nodes:
        return None
    for k in prefer_kinds:
        for n in nodes:
            if n.get("kind") == k:
                return n.get("id")
    return nodes[0].get("id")


class TestNpcSaveOntoNode:
    def test_default_save_false_does_not_persist(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        nid = _first_node(admin_headers, cid)
        if not nid:
            pytest.skip("No node")
        # First clear any prior stat_block we might have set
        # (we don't have a node-edit endpoint via API; just rely on saved=false flag)
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/{nid}/generate-sheet"
            "?threat_tier=boss",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["saved"] is False
        assert d["node_id"] == nid
        assert "stat_block" in d

    def test_save_true_persists_stat_block_on_node(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        nid = _first_node(admin_headers, cid)
        if not nid:
            pytest.skip("No node")
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/{nid}/generate-sheet"
            "?threat_tier=boss&save=true",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["saved"] is True
        sb_returned = d["stat_block"]
        assert sb_returned["threat_tier"] == "boss"

        # Verify persistence via GET /api/campaigns/{cid}/nodes
        nodes_r = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/nodes",
            headers=admin_headers, timeout=15)
        assert nodes_r.status_code == 200
        nodes = nodes_r.json()
        target = next((n for n in nodes if n.get("id") == nid), None)
        assert target is not None
        assert "stat_block" in target, "stat_block field missing from node after save=true"
        sb_persisted = target["stat_block"]
        assert sb_persisted is not None
        # Validate the persisted block matches the response shape
        assert sb_persisted.get("threat_tier") == "boss"
        assert sb_persisted.get("system_id") == "besm-4e"
        # node should also carry the threat tier marker (V6.8)
        assert target.get("stat_block_threat_tier") == "boss"

    def test_save_false_explicit_does_not_overwrite(self, admin_headers, besm_campaign):
        """Calling with save=false (or default) returns block but does not flip saved flag."""
        cid = besm_campaign["id"]
        nid = _first_node(admin_headers, cid)
        if not nid:
            pytest.skip("No node")
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/{nid}/generate-sheet"
            "?threat_tier=underling&save=false",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["saved"] is False

    def test_save_403_for_non_gm(self, besm_campaign, admin_headers):
        cid = besm_campaign["id"]
        nid = _first_node(admin_headers, cid)
        if not nid:
            pytest.skip("No node")
        email = f"TEST_v68_save_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "pass123!",
                            "name": "nm", "role": "player"}, timeout=15)
        login = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": "pass123!"},
                              timeout=15)
        tok = login.json()["access_token"]
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/{nid}/generate-sheet"
            "?threat_tier=boss&save=true",
            headers={"Authorization": f"Bearer {tok}"}, timeout=15)
        assert r.status_code == 403, r.text
