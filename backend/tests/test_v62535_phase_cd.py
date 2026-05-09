"""V6.25.35 Phase C+D + GM Table Health badge backend tests."""
import os, time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://rules-forge.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"
PLAYER_PASS = "PieBan18!!"

BESM_CID = "88c44628d6c44bf596185030d2f6743b"     # V62526 pdf-test
DND_CID  = "368d4e21b86641b7a184befff3f9b559"
CYPHER_CID = "dac42099dfcf4f7b8deabd1ed043ec00"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"Login {r.status_code} {r.text[:200]}"
    j = r.json()
    return j.get("access_token") or j.get("token")


@pytest.fixture(scope="module")
def gm_h():
    return {"Authorization": f"Bearer {_login(GM_EMAIL, GM_PASS)}"}


@pytest.fixture(scope="module")
def player_h():
    return {"Authorization": f"Bearer {_login(GM_EMAIL, PLAYER_PASS)}"}


@pytest.fixture(scope="module")
def gm_id(gm_h):
    r = requests.get(f"{API}/auth/me", headers=gm_h, timeout=10).json()
    return r.get("id") or r.get("user", {}).get("id")


# ── PHASE C: Cost overrides → CP math ─────────────────────────────
class TestCostOverrides:
    char_id = None

    def _create_besm(self, gm_h, gm_id, attrs, defs=None):
        payload = {
            "campaign_id": BESM_CID, "user_id": gm_id,
            "name": "TEST_v62535_overrides",
            "system_id": "besm-4e",
            "stats": {"body": 4, "mind": 4, "soul": 4},
            "attributes": attrs, "skills": [], "defects": defs or [],
            "total_points": 200,
        }
        r = requests.post(f"{API}/characters", headers=gm_h, json=payload, timeout=15)
        assert r.status_code in (200, 201), r.text[:300]
        cid = r.json().get("id") or r.json().get("character", {}).get("id")
        return cid

    def _set_override(self, gm_h, kind, name, override_cost):
        r = requests.put(f"{API}/campaigns/{BESM_CID}/cost-overrides",
                         headers=gm_h,
                         json={"kind": kind, "name": name, "override_cost": override_cost},
                         timeout=10)
        assert r.status_code in (200, 201), f"override set: {r.status_code} {r.text[:200]}"
        return r

    def _del_override(self, gm_h, kind, name):
        # GET list, find matching, DELETE by id
        r = requests.get(f"{API}/campaigns/{BESM_CID}/cost-overrides",
                         headers=gm_h, timeout=10)
        if r.status_code != 200:
            return r
        rows = r.json()
        if isinstance(rows, dict):
            rows = rows.get("overrides") or rows.get("rows") or []
        for row in rows:
            if (row.get("kind") or "").lower() == kind.lower() \
               and (row.get("name") or "").lower() == name.lower():
                oid = row.get("id") or row.get("_id")
                if oid:
                    return requests.delete(
                        f"{API}/campaigns/{BESM_CID}/cost-overrides/{oid}",
                        headers=gm_h, timeout=10)
        return r

    def test_attribute_override(self, gm_h, gm_id):
        # ensure clean override state
        self._del_override(gm_h, "attribute", "Tough")
        ch_id = self._create_besm(gm_h, gm_id,
            attrs=[{"name": "Tough", "level": 3, "cost_per_level": 4}])
        TestCostOverrides.char_id = ch_id
        # baseline
        r = requests.get(f"{API}/characters/{ch_id}/validate", headers=gm_h, timeout=15)
        assert r.status_code == 200, r.text[:300]
        bd = r.json()["breakdown"]
        assert bd["attribute_total"] == 12, f"baseline expected 12 got {bd['attribute_total']}"

        # set override Tough=1
        self._set_override(gm_h, "attribute", "Tough", 1)
        r2 = requests.get(f"{API}/characters/{ch_id}/validate", headers=gm_h, timeout=15)
        bd2 = r2.json()["breakdown"]
        assert bd2["attribute_total"] == 3, f"override expected 3 got {bd2['attribute_total']}: {bd2.get('lines')}"
        line = next((l for l in bd2["lines"] if l.get("kind") == "attribute"
                     and (l.get("name") or "").lower() == "tough"), None)
        assert line, "Tough attribute line missing"
        assert line.get("override_applied") is True
        assert float(line.get("cost_per_level")) == 1.0
        assert float(line.get("cost_per_level_canon")) == 4.0
        assert "GM override" in (line.get("note") or "")

        # remove override → back to 12
        self._del_override(gm_h, "attribute", "Tough")
        r3 = requests.get(f"{API}/characters/{ch_id}/validate", headers=gm_h, timeout=15)
        bd3 = r3.json()["breakdown"]
        assert bd3["attribute_total"] == 12, f"after delete expected 12 got {bd3['attribute_total']}"

    def test_skill_group_override(self, gm_h, gm_id):
        # create char with Athletics L3 cost 2
        payload = {"campaign_id": BESM_CID, "user_id": gm_id,
                   "name": "TEST_v62535_skill_ov", "system_id": "besm-4e",
                   "stats": {"body": 4, "mind": 4, "soul": 4},
                   "attributes": [],
                   "skills": [{"name": "Athletics", "group": "Athletics",
                               "level": 3, "cost_per_level": 2}],
                   "defects": [], "total_points": 100}
        r = requests.post(f"{API}/characters", headers=gm_h, json=payload, timeout=15)
        assert r.status_code in (200, 201), r.text[:300]
        cid = r.json().get("id") or r.json().get("character", {}).get("id")

        self._set_override(gm_h, "skill_group", "Athletics", 0)
        v = requests.get(f"{API}/characters/{cid}/validate", headers=gm_h, timeout=15).json()
        assert v["breakdown"]["skill_total"] == 0, v["breakdown"]
        line = next((l for l in v["breakdown"]["lines"] if l.get("kind") == "skill"), None)
        assert line and line.get("override_applied") is True
        # cleanup
        self._del_override(gm_h, "skill_group", "Athletics")
        requests.delete(f"{API}/characters/{cid}", headers=gm_h, timeout=10)

    def test_defect_override(self, gm_h, gm_id):
        payload = {"campaign_id": BESM_CID, "user_id": gm_id,
                   "name": "TEST_v62535_defect_ov", "system_id": "besm-4e",
                   "stats": {"body": 4, "mind": 4, "soul": 4},
                   "attributes": [],
                   "skills": [],
                   "defects": [{"name": "Vow", "rank": 2, "points_per_rank": 1, "category": "social"}],
                   "total_points": 100}
        r = requests.post(f"{API}/characters", headers=gm_h, json=payload, timeout=15)
        cid = r.json().get("id") or r.json().get("character", {}).get("id")

        self._set_override(gm_h, "defect", "Vow", 0)
        v = requests.get(f"{API}/characters/{cid}/validate", headers=gm_h, timeout=15).json()
        assert v["breakdown"]["defect_refund"] == 0, v["breakdown"]
        line = next((l for l in v["breakdown"]["lines"] if l.get("kind") == "defect"), None)
        assert line and line.get("override_applied") is True
        assert line.get("points_per_rank_canon") == 1
        self._del_override(gm_h, "defect", "Vow")
        requests.delete(f"{API}/characters/{cid}", headers=gm_h, timeout=10)

    def test_cleanup_main(self, gm_h):
        if TestCostOverrides.char_id:
            requests.delete(f"{API}/characters/{TestCostOverrides.char_id}",
                            headers=gm_h, timeout=10)


# ── Reference endpoints (D) ───────────────────────────────────────
class TestReference:
    def test_dnd_reference_patrons_pacts(self, gm_h):
        r = requests.get(f"{API}/systems/dnd-5e/reference", headers=gm_h, timeout=15)
        assert r.status_code == 200, r.text[:300]
        ref = r.json()
        assert len(ref.get("patrons") or []) >= 8, f"patrons={len(ref.get('patrons') or [])}"
        assert len(ref.get("pacts") or []) >= 4
        assert len(ref.get("invocations") or []) >= 14
        pact_names = {p["name"] for p in ref["pacts"]}
        for nm in ("Pact of the Tome", "Pact of the Blade", "Pact of the Chain", "Pact of the Talisman"):
            assert nm in pact_names, f"missing {nm} in {pact_names}"

    def test_anime5e_reference_demon_heritages(self, gm_h):
        r = requests.get(f"{API}/systems/anime-5e/reference", headers=gm_h, timeout=15)
        assert r.status_code == 200, r.text[:300]
        ref = r.json()
        assert len(ref.get("patrons") or []) >= 8
        assert len(ref.get("pacts") or []) >= 4
        assert len(ref.get("invocations") or []) >= 14
        heritages = ref.get("demon_heritages") or []
        assert len(heritages) >= 8, f"demon_heritages={len(heritages)}"
        names = {h["name"] for h in heritages}
        for required in ("Tiefling (Standard)", "Half-Demon (Anime)",
                         "Cursed Bloodline (Anime)", "Oni-blooded (Anime)", "Hellspawn"):
            assert required in names, f"missing heritage {required} in {names}"


# ── Phase D: Concept Forge — D&D 5E + Cypher ──────────────────────
class TestConceptForge:
    def test_dnd_warlock_concept(self, gm_h):
        body = {
            "concept_text": "A grim warlock who bargained with a fiend for power.",
            "role": "Striker",
            "signature_traits": "eldritch blast, infernal pact, dark whispers",
        }
        r = requests.post(f"{API}/campaigns/{DND_CID}/concept-drafts",
                          headers=gm_h, json=body, timeout=120)
        assert r.status_code == 200, f"{r.status_code} {r.text[:600]}"
        cands = r.json()["draft"]["candidates"]
        assert len(cands) >= 2
        for c in cands[:2]:
            assert (c.get("class") or "").lower() == "warlock", f"class={c.get('class')}"
            assert c.get("subclass"), "subclass empty"
            assert 1 <= int(c.get("tier") or 0) <= 4
            assert int(c.get("level") or 0) >= 1
            ab = c.get("abilities") or {}
            for k in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
                assert k in ab, f"missing ability {k}"
            assert len(c.get("cantrips") or []) >= 1
            assert len(c.get("spells") or []) >= 2
            assert c.get("patron"), "patron empty"
            assert c.get("pact") in ("Tome", "Blade", "Chain", "Talisman"), f"pact={c.get('pact')}"
            assert len(c.get("invocations") or []) >= 1
        # cleanup
        did = r.json()["draft"]["id"]
        requests.delete(f"{API}/campaigns/{DND_CID}/concept-drafts/{did}",
                        headers=gm_h, timeout=10)

    def test_cypher_concept(self, gm_h):
        body = {
            "concept_text": "A wandering machine-talker who scavenges relics.",
            "role": "Explorer",
            "signature_traits": "talks to machines, mystic insight",
        }
        r = requests.post(f"{API}/campaigns/{CYPHER_CID}/concept-drafts",
                          headers=gm_h, json=body, timeout=120)
        assert r.status_code == 200, f"{r.status_code} {r.text[:600]}"
        cands = r.json()["draft"]["candidates"]
        assert len(cands) >= 2
        for c in cands[:2]:
            assert "sentence" in c and "who" in (c["sentence"] or "").lower()
            assert c.get("descriptor")
            assert c.get("type") in ("Warrior", "Adept", "Explorer", "Speaker")
            assert c.get("focus")
            assert 1 <= int(c.get("tier") or 0) <= 6
            pools = c.get("pools") or {}
            assert all(k in pools for k in ("Might", "Speed", "Intellect"))
            assert "edges" in c
            assert "effort" in c
            for k in ("cyphers", "artifacts", "abilities"):
                assert isinstance(c.get(k), list)
        did = r.json()["draft"]["id"]
        requests.delete(f"{API}/campaigns/{CYPHER_CID}/concept-drafts/{did}",
                        headers=gm_h, timeout=10)


# ── Table Health aggregator ────────────────────────────────────────
class TestTableHealth:
    def test_gm_aggregator(self, gm_h):
        r = requests.get(f"{API}/campaigns/{BESM_CID}/validations",
                         headers=gm_h, timeout=15)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        for k in ("total_warnings", "characters_dirty", "characters"):
            assert k in body, f"missing {k} in {list(body.keys())}"
        for ch in body["characters"]:
            assert "character_id" in ch
            assert "character_name" in ch
            assert "warnings" in ch

    def test_non_gm_403(self, player_h):
        r = requests.get(f"{API}/campaigns/{BESM_CID}/validations",
                         headers=player_h, timeout=10)
        assert r.status_code in (403, 404), f"expected 403/404 got {r.status_code}"
