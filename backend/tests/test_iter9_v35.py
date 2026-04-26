"""V3.5 backend tests: cost-engine clamp, defects-on-items, defect-refund-direction,
campaign benchmarks (genre/period/size/DR baseline), attribute whitelist enforcement."""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"

GM_EMAIL = "gm@tablegnostic.com"
GM_PASS = "gm123456"
PLAYER_EMAIL = "player@tablegnostic.com"
PLAYER_PASS = "player12345"


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{API}/auth/login", json={"email": GM_EMAIL, "password": GM_PASS})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def player_token():
    r = requests.post(f"{API}/auth/login", json={"email": PLAYER_EMAIL, "password": PLAYER_PASS})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def v35_campaign(gm_token):
    payload = {"name": f"TEST_V35_{uuid.uuid4().hex[:6]}",
               "description": "V3.5 cost engine + benchmarks",
               "visibility": "public", "max_players": 6}
    r = requests.post(f"{API}/campaigns", json=payload, headers=h(gm_token))
    assert r.status_code == 200, r.text
    camp = r.json()
    yield camp
    requests.delete(f"{API}/campaigns/{camp['id']}", headers=h(gm_token))


# ---------------- Whitelist via /api/besm/reference ----------------

class TestWhitelist:
    @pytest.fixture(scope="class")
    def ref(self):
        r = requests.get(f"{API}/besm/reference")
        assert r.status_code == 200
        return r.json()

    def test_attributes_have_whitelist_keys(self, ref):
        attrs = ref["attributes"]
        sample = attrs[0]
        assert "allowed_enhancements" in sample
        assert "allowed_limiters" in sample
        assert "open_mods" in sample

    def _by_name(self, ref, name):
        for a in ref["attributes"]:
            if a["name"] == name:
                return a
        pytest.fail(f"attribute {name} not in reference")

    def test_tough_no_enhancements(self, ref):
        a = self._by_name(ref, "Tough")
        assert a["open_mods"] is False
        assert a["allowed_enhancements"] == []

    def test_item_open_kit_full_lists(self, ref):
        a = self._by_name(ref, "Item")
        assert a["open_mods"] is False
        assert len(a["allowed_enhancements"]) == 5
        assert len(a["allowed_limiters"]) == 23

    def test_wealth_no_enhancements(self, ref):
        a = self._by_name(ref, "Wealth")
        assert a["allowed_enhancements"] == []

    def test_mind_control_all_5_enh(self, ref):
        a = self._by_name(ref, "Mind Control")
        assert len(a["allowed_enhancements"]) == 5

    def test_heightened_senses_only_range(self, ref):
        a = self._by_name(ref, "Heightened Senses")
        assert a["allowed_enhancements"] == ["Range"]


# ---------------- Cost engine clamp + nested defects ----------------

class TestCostEngineClamp:
    def _create(self, token, campaign_id, attrs, defects=None):
        payload = {
            "campaign_id": campaign_id,
            "name": f"TEST_CE_{uuid.uuid4().hex[:5]}",
            "stats": {"body": 4, "mind": 4, "soul": 4},
            "attributes": attrs,
            "defects": defects or [],
            "skills": [],
        }
        r = requests.post(f"{API}/characters", json=payload, headers=h(token))
        assert r.status_code == 200, r.text
        return r.json()

    def test_cost_unchanged_by_limiters_v41(self, gm_token, v35_campaign):
        # V4.1 rule fix: cost is base × level, NEVER changed by limiters
        # or enhancements. The old clamp behaviour (max(1, base+enh-lim))
        # was reversed/incorrect per the BESM 4E primer.
        # Tunnelling level=2, cpl=2, no enh, 2 limiters →
        #   cost = 2 × 2 = 4 (regardless of limiters)
        #   effective_level = 2 + 2 − 0 = 4 (limiters raise effective)
        ch = self._create(gm_token, v35_campaign["id"], [
            {"name": "Tunnelling", "level": 2, "cost_per_level": 2,
             "enhancements": [], "limiters": ["Concentration", "Delay"]}
        ])
        assert ch["spent"]["attribute_cost"] == 4, ch["spent"]
        # GET round-trip should also stamp effective_level on the attribute.
        g = requests.get(f"{API}/characters/{ch['id']}", headers=h(gm_token)).json()
        assert g["spent"]["attribute_cost"] == 4
        attr = g["attributes"][0]
        assert attr.get("effective_level") == 4, \
            f"V4.1 effective_level should be 4 (level 2 + 2 limiters), got {attr.get('effective_level')}"
        requests.delete(f"{API}/characters/{ch['id']}", headers=h(gm_token))

    def test_clamp_extreme_negative_still_floors(self, gm_token, v35_campaign):
        # cpl=1, no enh, 5 limiters → 1+(0-5)=-4 → max(1,-4)=1; ×3 = 3
        ch = self._create(gm_token, v35_campaign["id"], [
            {"name": "Telekinesis", "level": 3, "cost_per_level": 1,
             "enhancements": [],
             "limiters": ["Activation", "Concentration", "Delay",
                          "Detectable", "Environmental"]}
        ])
        assert ch["spent"]["attribute_cost"] == 3
        requests.delete(f"{API}/characters/{ch['id']}", headers=h(gm_token))

    def test_item_with_nested_defect(self, gm_token, v35_campaign):
        # Item lvl=6 cpl=1, defect Achilles Heel rank=1 ppr=2 → max(1,1)*6 - 2 = 4
        ch = self._create(gm_token, v35_campaign["id"], [
            {"name": "Item", "level": 6, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "defects": [{"name": "Achilles Heel", "rank": 1,
                          "points_per_rank": 2, "category": "Greater",
                          "page": 154}]}
        ])
        assert ch["spent"]["attribute_cost"] == 4
        requests.delete(f"{API}/characters/{ch['id']}", headers=h(gm_token))

    def test_nested_defect_refund_floors_at_zero(self, gm_token, v35_campaign):
        # Item lvl=1 cpl=1 → subtotal 1, defect refund 5 → max(0, 1-5)=0
        ch = self._create(gm_token, v35_campaign["id"], [
            {"name": "Item", "level": 1, "cost_per_level": 1,
             "enhancements": [], "limiters": [],
             "defects": [{"name": "Big Flaw", "rank": 5,
                          "points_per_rank": 1, "category": "Lesser"}]}
        ])
        assert ch["spent"]["attribute_cost"] == 0
        requests.delete(f"{API}/characters/{ch['id']}", headers=h(gm_token))

    def test_defect_subtracted_from_total(self, gm_token, v35_campaign):
        # stats 4/4/4 = 12; one defect rank=1 ppr=1 → total = 12 - 1 = 11
        payload = {
            "campaign_id": v35_campaign["id"],
            "name": f"TEST_DEF_{uuid.uuid4().hex[:5]}",
            "stats": {"body": 4, "mind": 4, "soul": 4},
            "attributes": [],
            "defects": [{"name": "Marked", "rank": 1,
                         "points_per_rank": 1, "category": "Lesser"}],
            "skills": [],
        }
        r = requests.post(f"{API}/characters", json=payload, headers=h(gm_token))
        assert r.status_code == 200, r.text
        ch = r.json()
        assert ch["spent"]["stat_cost"] == 12
        assert ch["spent"]["defect_points"] == 1
        assert ch["spent"]["total_spent"] == 11
        requests.delete(f"{API}/characters/{ch['id']}", headers=h(gm_token))


# ---------------- Campaign benchmarks ----------------

class TestCampaignBenchmarks:
    def test_put_and_get_benchmarks(self, gm_token, v35_campaign):
        payload = {
            "name": v35_campaign["name"],
            "description": v35_campaign["description"],
            "visibility": "public",
            "max_players": v35_campaign["max_players"],
            "genre": "Cosmic Horror",
            "time_period": "Modern",
            "default_character_size": "Medium",  # V3.7 replaced size_scale (per-entity templates)
            "damage_rating_baseline": 7,
        }
        r = requests.put(f"{API}/campaigns/{v35_campaign['id']}",
                         json=payload, headers=h(gm_token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["genre"] == "Cosmic Horror"
        assert d["time_period"] == "Modern"
        assert d["default_character_size"] == "Medium"
        assert d["damage_rating_baseline"] == 7

        # GET round-trip
        g = requests.get(f"{API}/campaigns/{v35_campaign['id']}",
                         headers=h(gm_token)).json()
        assert g["genre"] == "Cosmic Horror"
        assert g["time_period"] == "Modern"
        assert g["default_character_size"] == "Medium"
        assert g["damage_rating_baseline"] == 7

    def test_character_uses_campaign_dm_baseline(self, gm_token, v35_campaign):
        # Campaign has DR baseline 7 from previous test. Create char with no
        # Massive Damage → DM should equal 7 (not 5).
        payload = {
            "campaign_id": v35_campaign["id"],
            "name": f"TEST_DM_{uuid.uuid4().hex[:5]}",
            "stats": {"body": 5, "mind": 5, "soul": 5},
            "attributes": [],
            "defects": [],
            "skills": [],
        }
        r = requests.post(f"{API}/characters", json=payload, headers=h(gm_token))
        assert r.status_code == 200, r.text
        ch = r.json()
        assert ch["derived"]["damage_rating_baseline"] == 7
        assert ch["derived"]["damage_multiplier"] == 7  # 7 + 0*5

        # Add Massive Damage level 2 → DM = 7 + 10 = 17
        upd = {
            "campaign_id": v35_campaign["id"],
            "name": ch["name"],
            "stats": {"body": 5, "mind": 5, "soul": 5},
            "attributes": [{"name": "Massive Damage", "level": 2,
                            "cost_per_level": 5}],
            "defects": [],
            "skills": [],
        }
        u = requests.put(f"{API}/characters/{ch['id']}", json=upd,
                         headers=h(gm_token))
        assert u.status_code == 200, u.text
        assert u.json()["derived"]["damage_multiplier"] == 17
        requests.delete(f"{API}/characters/{ch['id']}", headers=h(gm_token))
