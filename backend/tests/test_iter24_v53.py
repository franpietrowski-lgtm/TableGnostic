"""V5.3 — Director's Console + One-Shot Scaffold backend tests.

Exercises:
  · GET/PUT /api/director/{cid} (GM-only, npc_pool aggregation)
  · POST /api/director/{cid}/cr-analyse (system-aware ratings + suggestions)
  · POST /api/campaigns/{cid}/scaffold-oneshot (signature/route smoke test;
    Claude live-call only if EMERGENT_LLM_KEY is present)
"""
import io
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
    "http://localhost:8001"

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"
CYPHER_CID = "22ee28aaf79541c395255e144b5aab42"
CYPHER_CHAR = "a129db2a8eb44e3b849de6fff876e9f5"


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": GM_EMAIL, "password": GM_PASS}, timeout=15)
    assert r.status_code == 200, f"GM login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def gm_headers(gm_token):
    return {"Authorization": f"Bearer {gm_token}"}


@pytest.fixture(scope="module")
def player_token():
    """Register a throw-away player for the 403 check."""
    email = f"TEST_iter24_player_{int(time.time())}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "playerpass1!",
                            "name": "iter24 player", "role": "player"}, timeout=15)
    if r.status_code not in (200, 201):
        pytest.skip(f"Could not register test player: {r.status_code} {r.text}")
    tok = r.json().get("access_token")
    if not tok:
        # Fall back to login
        r2 = requests.post(f"{BASE_URL}/api/auth/login",
                           json={"email": email, "password": "playerpass1!"}, timeout=15)
        tok = r2.json().get("access_token")
    return tok


# ───────────────────────── Director GET / PUT ─────────────────────────
class TestDirectorEndpoints:
    def test_get_director_as_gm(self, gm_headers):
        r = requests.get(f"{BASE_URL}/api/director/{CYPHER_CID}",
                         headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "encounters" in body
        assert "npc_pool" in body and isinstance(body["npc_pool"], list)
        assert body.get("system_id") == "cypher", \
            f"Expected system_id=cypher, got {body.get('system_id')}"

    def test_get_director_as_player_403(self, player_token):
        if not player_token:
            pytest.skip("no player token")
        r = requests.get(f"{BASE_URL}/api/director/{CYPHER_CID}",
                         headers={"Authorization": f"Bearer {player_token}"}, timeout=15)
        assert r.status_code == 403, f"Expected 403 for player, got {r.status_code}"

    def test_put_director_roundtrip(self, gm_headers):
        body = {
            "encounters": [{
                "name": "TEST_iter24_enc",
                "party_character_ids": [CYPHER_CHAR],
                "npcs": [{"name": "Bandit", "role": "minion", "level": 2,
                          "count": 3, "intent": "ambush", "location": "alley"}],
                "environment": {"indoor": True, "weather": "rain", "light": "dim"},
            }],
            "current_location": "TEST_iter24_loc",
            "current_phase_ref": "TEST_iter24_phase",
        }
        r = requests.put(f"{BASE_URL}/api/director/{CYPHER_CID}",
                         json=body, headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text
        saved = r.json()
        assert saved["current_location"] == "TEST_iter24_loc"
        assert saved["current_phase_ref"] == "TEST_iter24_phase"
        assert len(saved["encounters"]) == 1
        enc = saved["encounters"][0]
        assert enc.get("id"), "encounter id should be stamped"
        assert enc["npcs"][0].get("id"), "npc id should be stamped"
        # Verify GET round-trips
        r2 = requests.get(f"{BASE_URL}/api/director/{CYPHER_CID}",
                          headers=gm_headers, timeout=15)
        assert r2.status_code == 200
        got = r2.json()
        assert got["current_location"] == "TEST_iter24_loc"
        assert len(got["encounters"]) == 1

    def test_zz_cleanup_director(self, gm_headers):
        # restore to empty state
        r = requests.put(f"{BASE_URL}/api/director/{CYPHER_CID}",
                         json={"encounters": [], "current_location": "",
                               "current_phase_ref": ""},
                         headers=gm_headers, timeout=15)
        assert r.status_code == 200


# ───────────────────────── CR-analyse ─────────────────────────
class TestCrAnalyse:
    def test_cr_cypher_tier1_vs_l4_plus_minions(self, gm_headers):
        body = {
            "party_character_ids": [CYPHER_CHAR],
            "npcs": [
                {"name": "L4 NPC", "role": "villain", "level": 4, "count": 1},
                {"name": "Minion", "role": "minion", "level": 2, "count": 3},
            ],
            "environment": {"indoor": False},
        }
        r = requests.post(f"{BASE_URL}/api/director/{CYPHER_CID}/cr-analyse",
                          json=body, headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["system_id"] == "cypher"
        assert d["rating"] in ("Hard", "Punishing"), \
            f"Expected Hard/Punishing for tier-1 vs L4+3xL2, got {d['rating']}"
        assert d.get("party_label") and "PCs" in d["party_label"]
        assert isinstance(d.get("suggestions"), list)
        kinds = {s.get("kind") for s in d["suggestions"]}
        # Hard or Punishing should suggest remove_npc and/or armor / feat
        assert kinds & {"remove_npc", "armor", "feat"}, \
            f"Expected remove_npc/armor/feat, got {kinds}"

    def test_cr_empty_npcs_pushover(self, gm_headers):
        body = {"party_character_ids": [CYPHER_CHAR], "npcs": []}
        r = requests.post(f"{BASE_URL}/api/director/{CYPHER_CID}/cr-analyse",
                          json=body, headers=gm_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["rating"] == "Pushover"

    def test_cr_empty_party_unknown(self, gm_headers):
        body = {"party_character_ids": [],
                "npcs": [{"name": "x", "level": 3, "count": 1}]}
        r = requests.post(f"{BASE_URL}/api/director/{CYPHER_CID}/cr-analyse",
                          json=body, headers=gm_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["rating"] == "Unknown"


# ───────────────────────── Scaffold One-Shot ─────────────────────────
class TestScaffold:
    @pytest.fixture(scope="class")
    def has_llm_key(self):
        try:
            with open("/app/backend/.env") as f:
                env = f.read()
            return "EMERGENT_LLM_KEY=" in env and \
                not any(line.strip() == "EMERGENT_LLM_KEY=" for line in env.splitlines())
        except Exception:
            return False

    def test_scaffold_route_exists_no_file_422(self, gm_headers):
        # No multipart file → expect 422 (validation), not 404
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CYPHER_CID}/scaffold-oneshot?commit=false",
            headers=gm_headers, timeout=15)
        assert r.status_code != 404, f"Route missing! got {r.status_code}"
        assert r.status_code in (400, 415, 422), \
            f"Expected 4xx for missing file, got {r.status_code}: {r.text[:200]}"

    def test_scaffold_preview(self, gm_headers, has_llm_key):
        if not has_llm_key:
            pytest.skip("EMERGENT_LLM_KEY missing — skipping live Claude call")
        files = {
            "file": ("oneshot.md", io.BytesIO(
                b"# The Bell of Quiet Hours\n\nA short one-shot. The party "
                b"investigates a haunted bell tower in the village of Mire. "
                b"NPCs: Sister Vell (cloistered priestess), Old Tobin (drunk "
                b"caretaker). Antagonist: a bound revenant in the bell. "
                b"Three scenes: arrival, the chapel, the climb.\n"),
             "text/markdown"),
        }
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CYPHER_CID}/scaffold-oneshot?commit=false",
            files=files, headers=gm_headers, timeout=120)
        if r.status_code == 502:
            pytest.skip(f"Claude upstream 502 — {r.text[:120]}")
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d.get("committed") is False
        assert "preview" in d
