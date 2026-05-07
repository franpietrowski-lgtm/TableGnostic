"""V6.7 backend tests — BESM encounter budget, NPC sheet auto-generation,
and anime5e soft-cap warning.
"""
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
def besm_campaign(campaigns):
    cands = [c for c in campaigns if c.get("system_id") == "besm-4e"]
    if not cands:
        pytest.skip("No besm-4e campaign seeded")
    return cands[0]


@pytest.fixture(scope="module")
def non_besm_campaign(campaigns):
    cands = [c for c in campaigns if c.get("system_id") != "besm-4e"]
    if not cands:
        pytest.skip("No non-besm campaign")
    return cands[0]


# ─── Anime 5E soft-cap warning (V6.7) ───────────────────────────────

class TestAnime5eSoftCapWarning:
    def test_party8_warns_soft_cap(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/anime5e/encounter-budget"
            "?party_level=5&party_size=8&difficulty=hard",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "warnings" in d
        assert isinstance(d["warnings"], list)
        assert len(d["warnings"]) > 0
        joined = " ".join(d["warnings"]).lower()
        assert "cap of 6" in joined

    def test_party4_no_warning(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/anime5e/encounter-budget"
            "?party_level=5&party_size=4&difficulty=hard",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("warnings", []) == []


# ─── BESM encounter budget (V6.7 new endpoint) ──────────────────────

class TestBesmEncounterBudget:
    def test_happy_path_hard_party4(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/besm/encounter-budget"
            f"?campaign_id={cid}&party_size=4&difficulty=hard",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for key in ("pc_cp", "party_total_cp", "encounter_budget",
                    "threat_slots", "warnings", "note"):
            assert key in d, f"missing key {key}"
        assert d["system_id"] == "besm-4e"
        assert isinstance(d["pc_cp"], int)
        assert d["party_total_cp"] == d["pc_cp"] * 4
        assert d["encounter_budget"] == int(d["party_total_cp"] * 1.25)
        assert isinstance(d["threat_slots"], list)
        assert len(d["threat_slots"]) > 0
        tiers_found = set()
        for slot in d["threat_slots"]:
            for k in ("tier", "foe_cp", "ratio_to_pc", "max_count",
                     "budget_fit_pct", "note"):
                assert k in slot, f"slot missing {k}"
            tiers_found.add(slot["tier"])
        # All 4 tiers should fit in the 'hard' budget for party of 4.
        assert {"underling", "equal", "boss"}.issubset(tiers_found)

    def test_soft_cap_warning_party8(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/besm/encounter-budget"
            f"?campaign_id={cid}&party_size=8&difficulty=equal",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert len(d["warnings"]) > 0
        assert "cap of 6" in " ".join(d["warnings"]).lower()

    def test_400_on_non_besm(self, admin_headers, non_besm_campaign):
        cid = non_besm_campaign["id"]
        r = requests.get(
            f"{BASE_URL}/api/besm/encounter-budget"
            f"?campaign_id={cid}&party_size=4&difficulty=equal",
            headers=admin_headers, timeout=15)
        assert r.status_code == 400, r.text

    def test_403_for_non_member(self, besm_campaign):
        email = f"TEST_v67_besmnm_{uuid.uuid4().hex[:8]}@example.com"
        reg = requests.post(f"{BASE_URL}/api/auth/register",
                            json={"email": email, "password": "pass123!",
                                  "name": "nm", "role": "player"}, timeout=15)
        assert reg.status_code in (200, 201), reg.text
        login = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": "pass123!"},
                              timeout=15)
        tok = login.json()["access_token"]
        r = requests.get(
            f"{BASE_URL}/api/besm/encounter-budget"
            f"?campaign_id={besm_campaign['id']}&party_size=4&difficulty=equal",
            headers={"Authorization": f"Bearer {tok}"}, timeout=15)
        assert r.status_code == 403, r.text


# ─── NPC / Creature auto-stat-block generator (V6.7) ────────────────

def _first_node(admin_headers, campaign_id):
    """Return the first codex node id for a campaign, or None."""
    r = requests.get(
        f"{BASE_URL}/api/campaigns/{campaign_id}/nodes",
        headers=admin_headers, timeout=15)
    if r.status_code != 200:
        return None
    nodes = r.json()
    if not nodes:
        return None
    # Prefer npc / creature kinds if present
    for k in ("npc", "creature"):
        for n in nodes:
            if n.get("kind") == k:
                return n.get("id")
    return nodes[0].get("id")


class TestGenerateNPCSheet:
    def test_besm_boss_block(self, admin_headers, besm_campaign):
        cid = besm_campaign["id"]
        nid = _first_node(admin_headers, cid)
        if not nid:
            pytest.skip("No codex node available in besm-4e campaign")
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/{nid}/generate-sheet"
            "?threat_tier=boss",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["node_id"] == nid
        assert d["saved"] is False
        sb = d["stat_block"]
        assert sb["system_id"] == "besm-4e"
        assert sb["threat_tier"] == "boss"
        assert "stats" in sb
        assert "attributes" in sb
        assert "skills" in sb
        assert "total_cp" in sb
        # boss = 1.5× pc_cp
        assert sb["total_cp"] >= 1

    @pytest.mark.parametrize("system_id", ["anime-5e", "dnd-5e"])
    def test_d5e_compatible_block(self, admin_headers, campaigns, system_id):
        cands = [c for c in campaigns if c.get("system_id") == system_id]
        if not cands:
            pytest.skip(f"No {system_id} campaign seeded")
        camp = cands[0]
        nid = _first_node(admin_headers, camp["id"])
        if not nid:
            pytest.skip(f"No codex node in {system_id}")
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{camp['id']}/npcs/{nid}/generate-sheet"
            "?threat_tier=equal",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        sb = r.json()["stat_block"]
        assert sb["system_id"] == system_id
        assert "ac" in sb
        assert "hp" in sb
        assert "abilities" in sb
        assert "actions" in sb
        assert isinstance(sb["actions"], list)

    def test_cypher_block(self, admin_headers, campaigns):
        cands = [c for c in campaigns if c.get("system_id") == "cypher"]
        if not cands:
            pytest.skip("No cypher campaign")
        camp = cands[0]
        nid = _first_node(admin_headers, camp["id"])
        if not nid:
            pytest.skip("No codex node in cypher")
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{camp['id']}/npcs/{nid}/generate-sheet"
            "?threat_tier=underling",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        sb = r.json()["stat_block"]
        assert sb["system_id"] == "cypher"
        assert "level" in sb
        assert "target_number" in sb
        assert "health" in sb
        assert "damage" in sb
        assert sb["target_number"] == 3 * sb["level"]

    def test_403_for_non_gm(self, besm_campaign, admin_headers):
        cid = besm_campaign["id"]
        nid = _first_node(admin_headers, cid)
        if not nid:
            pytest.skip("No node")
        email = f"TEST_v67_npcsh_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "pass123!",
                            "name": "nm", "role": "player"}, timeout=15)
        login = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": "pass123!"},
                              timeout=15)
        tok = login.json()["access_token"]
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/npcs/{nid}/generate-sheet"
            "?threat_tier=boss",
            headers={"Authorization": f"Bearer {tok}"}, timeout=15)
        assert r.status_code == 403, r.text
