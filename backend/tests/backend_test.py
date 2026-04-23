"""Table-Gnostic backend pytest suite.

Covers: health, auth, BESM reference, campaigns, custom rules, characters
(including derived calc), nodes + visibility/reveal, edges, sessions, chat,
dice (notation variations with stat refs), initiative, round advance,
effects, damage, RBAC negatives, and websocket broadcast behaviour.
"""

import asyncio
import json
import os
import uuid

import pytest
import requests
import websockets

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
# Running inside container — read frontend .env directly to keep contract
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
ADMIN_EMAIL = "admin@tablegnostic.com"
ADMIN_PASS = "admin123"


# ---------------- fixtures ----------------

@pytest.fixture(scope="session")
def gm_token():
    r = requests.post(f"{API}/auth/login", json={"email": GM_EMAIL, "password": GM_PASS})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def player_token():
    r = requests.post(f"{API}/auth/login", json={"email": PLAYER_EMAIL, "password": PLAYER_PASS})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="session")
def gm_user(gm_token):
    return requests.get(f"{API}/auth/me", headers=h(gm_token)).json()


@pytest.fixture(scope="session")
def player_user(player_token):
    return requests.get(f"{API}/auth/me", headers=h(player_token)).json()


@pytest.fixture(scope="session")
def campaign(gm_token):
    payload = {"name": f"TEST_Campaign_{uuid.uuid4().hex[:6]}",
               "description": "pytest", "visibility": "public", "max_players": 6}
    r = requests.post(f"{API}/campaigns", json=payload, headers=h(gm_token))
    assert r.status_code == 200, r.text
    camp = r.json()
    assert "id" in camp
    yield camp
    # teardown
    requests.delete(f"{API}/campaigns/{camp['id']}", headers=h(gm_token))


# ---------------- Health ----------------

class TestHealth:
    def test_health(self):
        r = requests.get(f"{API}/health")
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["service"] == "table-gnostic"


# ---------------- Auth ----------------

class TestAuth:
    def test_login_seeded_gm(self, gm_token):
        assert isinstance(gm_token, str) and len(gm_token) > 20

    def test_login_seeded_player(self, player_token):
        assert isinstance(player_token, str) and len(player_token) > 20

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": "nope@x.com", "password": "badpass"})
        assert r.status_code == 401

    def test_register_new_user(self):
        email = f"TEST_{uuid.uuid4().hex[:8]}@tablegnostic.com"
        r = requests.post(f"{API}/auth/register",
                          json={"email": email, "password": "password123",
                                "name": "Tester"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["email"] == email.lower()  # backend lowercases
        assert "access_token" in d and len(d["access_token"]) > 20
        # cookies set
        assert "access_token" in r.cookies
        assert "refresh_token" in r.cookies

    def test_me_with_bearer(self, gm_token):
        r = requests.get(f"{API}/auth/me", headers=h(gm_token))
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == GM_EMAIL
        assert "password_hash" not in d

    def test_me_with_cookie(self):
        s = requests.Session()
        lr = s.post(f"{API}/auth/login",
                    json={"email": GM_EMAIL, "password": GM_PASS})
        assert lr.status_code == 200
        # Send without Authorization header — cookies jar should carry it
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == GM_EMAIL

    def test_me_requires_auth(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401


# ---------------- BESM Reference ----------------

class TestBESMReference:
    def test_reference_counts_and_source(self):
        r = requests.get(f"{API}/besm/reference")
        assert r.status_code == 200
        d = r.json()
        assert d["book"] == "BESM 4E" or "BESM" in str(d["book"])
        assert len(d["attributes"]) == 86, f"attributes={len(d['attributes'])}"
        assert len(d["defects"]) == 36
        assert len(d["enhancements"]) == 5
        assert len(d["limiters"]) == 23
        assert "skill_groups" in d
        assert "power_levels" in d
        assert "target_numbers" in d
        # source metadata
        sample = d["attributes"][0]
        assert "source" in sample
        assert sample["source"].get("book", "").startswith("BESM")
        assert isinstance(sample["source"].get("page"), int)


# ---------------- Campaigns ----------------

class TestCampaigns:
    def test_list_includes_campaign(self, gm_token, campaign):
        r = requests.get(f"{API}/campaigns", headers=h(gm_token))
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert campaign["id"] in ids

    def test_get_campaign_is_gm(self, gm_token, campaign):
        r = requests.get(f"{API}/campaigns/{campaign['id']}", headers=h(gm_token))
        assert r.status_code == 200
        d = r.json()
        assert d["is_gm"] is True

    def test_player_join(self, player_token, campaign):
        r = requests.post(f"{API}/campaigns/{campaign['id']}/join",
                          json={"message": "hi"}, headers=h(player_token))
        assert r.status_code == 200
        # verify
        r2 = requests.get(f"{API}/campaigns/{campaign['id']}",
                          headers=h(player_token))
        assert r2.status_code == 200
        assert r2.json()["is_gm"] is False

    def test_gm_cannot_join_own(self, gm_token, campaign):
        r = requests.post(f"{API}/campaigns/{campaign['id']}/join",
                          json={}, headers=h(gm_token))
        assert r.status_code == 400

    def test_player_cannot_delete_campaign(self, player_token, campaign):
        r = requests.delete(f"{API}/campaigns/{campaign['id']}",
                            headers=h(player_token))
        assert r.status_code == 403


# ---------------- Custom rules (GM-only) ----------------

class TestCustomRules:
    def test_gm_create_custom(self, gm_token, campaign):
        r = requests.post(f"{API}/campaigns/{campaign['id']}/custom",
                          json={"campaign_id": campaign["id"], "kind": "attribute",
                                "name": "TEST_Arcane", "cost_per_level": 3,
                                "description_note": "custom"},
                          headers=h(gm_token))
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "TEST_Arcane"

    def test_player_cannot_create_custom(self, player_token, campaign):
        r = requests.post(f"{API}/campaigns/{campaign['id']}/custom",
                          json={"campaign_id": campaign["id"], "kind": "defect",
                                "name": "TEST_Hex", "cost_per_level": 1},
                          headers=h(player_token))
        assert r.status_code == 403


# ---------------- Characters & derived calc ----------------

@pytest.fixture(scope="session")
def player_character(player_token, campaign):
    # ensure player joined
    requests.post(f"{API}/campaigns/{campaign['id']}/join",
                  json={}, headers=h(player_token))
    payload = {
        "campaign_id": campaign["id"],
        "name": "TEST_Hero",
        "power_level": "Heroic",
        "total_points": 120,
        "stats": {"body": 5, "mind": 5, "soul": 5},
        "attributes": [
            {"name": "Tough", "level": 2, "cost_per_level": 2},
            {"name": "Attack Mastery", "level": 1, "cost_per_level": 2},
        ],
        "defects": [],
        "skills": [],
    }
    r = requests.post(f"{API}/characters", json=payload, headers=h(player_token))
    assert r.status_code == 200, r.text
    return r.json()


class TestCharacters:
    def test_derived_values(self, player_character):
        d = player_character["derived"]
        # CV = (5+5+5)//3 = 5; ATK = 5+1=6; DEF = 5-2+0=3;
        # HP = (5+5)*5 + 2*5 = 60; EP = (5+5)*5 + 0 = 50; DM = 5
        assert d["combat_value"] == 5
        assert d["attack_value"] == 6
        assert d["defence_value"] == 3
        assert d["health_points"] == 60
        assert d["energy_points"] == 50
        assert d["damage_multiplier"] == 5

    def test_spent_points_present(self, player_character):
        sp = player_character["spent"]
        assert "total_spent" in sp
        assert sp["stat_cost"] == 15  # 5+5+5

    def test_list_characters(self, player_token, campaign, player_character):
        r = requests.get(f"{API}/campaigns/{campaign['id']}/characters",
                         headers=h(player_token))
        assert r.status_code == 200
        assert any(c["id"] == player_character["id"] for c in r.json())

    def test_non_owner_cannot_edit(self, gm_token, player_character):
        # GM is allowed actually; test another random user
        # Register a random user
        email = f"TEST_{uuid.uuid4().hex[:6]}@t.com"
        reg = requests.post(f"{API}/auth/register",
                            json={"email": email, "password": "password123",
                                  "name": "Rando"}).json()
        tok = reg["access_token"]
        r = requests.put(f"{API}/characters/{player_character['id']}",
                         json={"campaign_id": player_character["campaign_id"],
                               "name": "Hijack",
                               "stats": {"body": 1, "mind": 1, "soul": 1}},
                         headers=h(tok))
        assert r.status_code == 403

    def test_update_character_recomputes_derived(self, player_token, player_character):
        payload = {
            "campaign_id": player_character["campaign_id"],
            "name": player_character["name"],
            "stats": {"body": 6, "mind": 6, "soul": 6},
            "attributes": [],
            "defects": [],
            "skills": [],
        }
        r = requests.put(f"{API}/characters/{player_character['id']}",
                         json=payload, headers=h(player_token))
        assert r.status_code == 200, r.text
        d = r.json()["derived"]
        assert d["combat_value"] == 6
        assert d["attack_value"] == 6
        assert d["defence_value"] == 4
        assert d["health_points"] == 60  # (6+6)*5

    def test_delete_character(self, player_token, campaign):
        payload = {"campaign_id": campaign["id"], "name": "TEST_Temp",
                   "stats": {"body": 4, "mind": 4, "soul": 4}}
        r = requests.post(f"{API}/characters", json=payload,
                          headers=h(player_token))
        cid = r.json()["id"]
        dr = requests.delete(f"{API}/characters/{cid}", headers=h(player_token))
        assert dr.status_code == 200
        gr = requests.get(f"{API}/characters/{cid}", headers=h(player_token))
        assert gr.status_code == 404


# ---------------- Nodes & visibility ----------------

class TestNodes:
    def test_gm_gm_only_hidden_from_player(self, gm_token, player_token,
                                            player_user, campaign):
        # GM creates gm_only node
        r = requests.post(f"{API}/nodes",
                          json={"campaign_id": campaign["id"], "type": "Lore",
                                "title": "TEST_Secret", "content": "hidden",
                                "visibility": "gm_only"},
                          headers=h(gm_token))
        assert r.status_code == 200, r.text
        node = r.json()
        # Player listing shouldn't include it
        lp = requests.get(f"{API}/campaigns/{campaign['id']}/nodes",
                          headers=h(player_token))
        assert lp.status_code == 200
        assert all(n["id"] != node["id"] for n in lp.json())
        # GM list should include
        lg = requests.get(f"{API}/campaigns/{campaign['id']}/nodes",
                          headers=h(gm_token))
        assert any(n["id"] == node["id"] for n in lg.json())

        # Reveal to player
        rv = requests.post(f"{API}/nodes/{node['id']}/reveal",
                           json={"user_ids": [player_user["id"]]},
                           headers=h(gm_token))
        assert rv.status_code == 200
        lp2 = requests.get(f"{API}/campaigns/{campaign['id']}/nodes",
                           headers=h(player_token))
        assert any(n["id"] == node["id"] for n in lp2.json())

    def test_player_cannot_reveal(self, gm_token, player_token, player_user, campaign):
        r = requests.post(f"{API}/nodes",
                          json={"campaign_id": campaign["id"], "type": "Lore",
                                "title": "TEST_Lock", "visibility": "gm_only"},
                          headers=h(gm_token))
        nid = r.json()["id"]
        rv = requests.post(f"{API}/nodes/{nid}/reveal",
                           json={"user_ids": [player_user["id"]]},
                           headers=h(player_token))
        assert rv.status_code == 403

    def test_player_node_is_shared(self, player_token, campaign):
        r = requests.post(f"{API}/nodes",
                          json={"campaign_id": campaign["id"], "type": "Note",
                                "title": "TEST_Player", "visibility": "gm_only"},
                          headers=h(player_token))
        assert r.status_code == 200
        assert r.json()["visibility"] == "shared"


# ---------------- Edges ----------------

class TestEdges:
    def test_create_and_list(self, gm_token, campaign):
        # create two nodes
        a = requests.post(f"{API}/nodes",
                          json={"campaign_id": campaign["id"], "type": "NPC",
                                "title": "TEST_A", "visibility": "shared"},
                          headers=h(gm_token)).json()
        b = requests.post(f"{API}/nodes",
                          json={"campaign_id": campaign["id"], "type": "NPC",
                                "title": "TEST_B", "visibility": "shared"},
                          headers=h(gm_token)).json()
        e = requests.post(f"{API}/edges",
                          json={"campaign_id": campaign["id"],
                                "from_node": a["id"], "to_node": b["id"],
                                "label": "ally"},
                          headers=h(gm_token))
        assert e.status_code == 200, e.text
        lst = requests.get(f"{API}/campaigns/{campaign['id']}/edges",
                           headers=h(gm_token))
        assert lst.status_code == 200
        assert any(ed["id"] == e.json()["id"] for ed in lst.json())


# ---------------- Sessions / Chat / Dice / Initiative / Effects ----------------

@pytest.fixture(scope="session")
def session(gm_token, campaign):
    r = requests.post(f"{API}/sessions",
                      json={"campaign_id": campaign["id"], "title": "TEST_S1"},
                      headers=h(gm_token))
    assert r.status_code == 200, r.text
    return r.json()


class TestSessions:
    def test_player_cannot_create_session(self, player_token, campaign):
        r = requests.post(f"{API}/sessions",
                          json={"campaign_id": campaign["id"], "title": "nope"},
                          headers=h(player_token))
        assert r.status_code == 403

    def test_chat_create_and_list(self, gm_token, session):
        r = requests.post(f"{API}/chat",
                          json={"session_id": session["id"], "message": "hello",
                                "kind": "chat"},
                          headers=h(gm_token))
        assert r.status_code == 200
        assert r.json()["message"] == "hello"
        lst = requests.get(f"{API}/sessions/{session['id']}/chat",
                           headers=h(gm_token))
        assert lst.status_code == 200
        assert any(c["message"] == "hello" for c in lst.json())


class TestDice:
    def test_simple_2d6(self, gm_token, session):
        r = requests.post(f"{API}/dice",
                          json={"session_id": session["id"], "notation": "2d6"},
                          headers=h(gm_token))
        assert r.status_code == 200, r.text
        d = r.json()["result"]
        assert 2 <= d["total"] <= 12
        assert len(d["rolls"]) == 1
        assert d["rolls"][0]["sides"] == 6
        assert len(d["rolls"][0]["results"]) == 2

    def test_2d6_plus3(self, gm_token, session):
        r = requests.post(f"{API}/dice",
                          json={"session_id": session["id"], "notation": "2d6+3"},
                          headers=h(gm_token))
        d = r.json()["result"]
        assert 5 <= d["total"] <= 15
        assert d["flat"] == 3

    def test_1d20(self, gm_token, session):
        r = requests.post(f"{API}/dice",
                          json={"session_id": session["id"], "notation": "1d20"},
                          headers=h(gm_token))
        d = r.json()["result"]
        assert 1 <= d["total"] <= 20

    def test_stat_reference_body(self, player_token, session, player_character):
        # body is 6 after update in TestCharacters.test_update_character_recomputes_derived
        r = requests.post(f"{API}/dice",
                          json={"session_id": session["id"],
                                "notation": "2d6+body",
                                "character_id": player_character["id"]},
                          headers=h(player_token))
        assert r.status_code == 200, r.text
        d = r.json()["result"]
        # with body=6 total range = [2+6, 12+6] = [8, 18]
        assert 8 <= d["total"] <= 18
        # rolls include a stat-ref entry
        refs = [x for x in d["rolls"] if x.get("ref")]
        assert refs and refs[0]["value"] == 6

    def test_2d6_minus_body(self, player_token, session, player_character):
        r = requests.post(f"{API}/dice",
                          json={"session_id": session["id"],
                                "notation": "2d6-body",
                                "character_id": player_character["id"]},
                          headers=h(player_token))
        d = r.json()["result"]
        assert 2 - 6 <= d["total"] <= 12 - 6

    def test_3d6_plus_mind_minus_2(self, player_token, session, player_character):
        # mind = 6
        r = requests.post(f"{API}/dice",
                          json={"session_id": session["id"],
                                "notation": "3d6+mind-2",
                                "character_id": player_character["id"]},
                          headers=h(player_token))
        d = r.json()["result"]
        # range [3+6-2, 18+6-2] = [7, 22]
        assert 7 <= d["total"] <= 22


class TestInitiative:
    def test_add_and_list_sorted_desc(self, gm_token, session):
        for name, roll in [("Goblin", 7), ("Hero", 15), ("Ogre", 10)]:
            requests.post(f"{API}/initiative",
                          json={"session_id": session["id"], "name": name,
                                "roll": roll, "side": "npc"},
                          headers=h(gm_token))
        r = requests.get(f"{API}/sessions/{session['id']}/initiative",
                         headers=h(gm_token))
        assert r.status_code == 200
        rolls = [x["roll"] for x in r.json() if x["name"] in ("Goblin", "Hero", "Ogre")]
        # sorted desc
        assert rolls == sorted(rolls, reverse=True)

    def test_delete_initiative(self, gm_token, session):
        r = requests.post(f"{API}/initiative",
                          json={"session_id": session["id"], "name": "TempEntry",
                                "roll": 1, "side": "neutral"},
                          headers=h(gm_token))
        iid = r.json()["id"]
        dr = requests.delete(f"{API}/initiative/{iid}", headers=h(gm_token))
        assert dr.status_code == 200


class TestRoundAndEffects:
    def test_round_advance_and_effect_expiry(self, gm_token, player_token, session):
        # player cannot advance
        bad = requests.post(f"{API}/sessions/{session['id']}/round/advance",
                            headers=h(player_token))
        assert bad.status_code == 403
        # create effect duration=1
        ef = requests.post(f"{API}/effects",
                           json={"session_id": session["id"],
                                 "target_name": "Hero", "name": "TEST_Bless",
                                 "duration_rounds": 1},
                           headers=h(gm_token))
        assert ef.status_code == 200
        eff_id = ef.json()["id"]
        # advance round; effect should expire & deactivate
        adv = requests.post(f"{API}/sessions/{session['id']}/round/advance",
                            headers=h(gm_token))
        assert adv.status_code == 200
        d = adv.json()
        assert d["round"] >= 1
        assert any(e["id"] == eff_id for e in d["expired"])
        # list only active excludes it
        lst = requests.get(f"{API}/sessions/{session['id']}/effects",
                           headers=h(gm_token))
        assert all(e["id"] != eff_id for e in lst.json())

    def test_effect_delete(self, gm_token, session):
        ef = requests.post(f"{API}/effects",
                           json={"session_id": session["id"],
                                 "target_name": "X", "name": "TEST_Buff",
                                 "duration_rounds": 5},
                           headers=h(gm_token)).json()
        dr = requests.delete(f"{API}/effects/{ef['id']}", headers=h(gm_token))
        assert dr.status_code == 200


class TestDamage:
    def test_damage_posts_system_chat(self, gm_token, session):
        r = requests.post(f"{API}/damage",
                          json={"session_id": session["id"],
                                "target_name": "Hero", "amount": 10, "kind": "hp"},
                          headers=h(gm_token))
        assert r.status_code == 200
        lst = requests.get(f"{API}/sessions/{session['id']}/chat",
                           headers=h(gm_token)).json()
        assert any("Hero took 10 HP damage" in c["message"] and c["kind"] == "system"
                   for c in lst)


# ---------------- WebSocket ----------------

def _ws_url(sid: str, token: str = None) -> str:
    base = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
    url = f"{base}/api/ws/session/{sid}"
    if token is not None:
        url += f"?token={token}"
    return url


class TestWebSocket:
    def test_ws_receives_chat_broadcast(self, gm_token, session):
        """Valid token + GM (authorized) should receive broadcast."""
        async def _run():
            url = _ws_url(session["id"], gm_token)
            async with websockets.connect(url) as ws:
                msg = f"TEST_WS_{uuid.uuid4().hex[:6]}"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(f"{API}/chat",
                                          json={"session_id": session["id"],
                                                "message": msg, "kind": "chat"},
                                          headers=h(gm_token)),
                )
                frame = await asyncio.wait_for(ws.recv(), timeout=10)
                payload = json.loads(frame)
                assert payload["type"] == "chat"
                assert payload["data"]["message"] == msg

        asyncio.run(_run())

    def test_ws_no_token_closes_4401(self, session):
        async def _run():
            url = _ws_url(session["id"], token=None)
            try:
                async with websockets.connect(url) as ws:
                    await asyncio.wait_for(ws.recv(), timeout=5)
                    pytest.fail("Expected connection to close")
            except websockets.exceptions.ConnectionClosed as e:
                assert e.code == 4401, f"expected 4401 got {e.code}"
            except websockets.exceptions.InvalidStatusCode as e:
                # Some stacks surface handshake reject as InvalidStatusCode
                assert e.status_code in (401, 403), f"unexpected {e.status_code}"
        asyncio.run(_run())

    def test_ws_invalid_token_closes_4401(self, session):
        async def _run():
            url = _ws_url(session["id"], token="not-a-real-token")
            try:
                async with websockets.connect(url) as ws:
                    await asyncio.wait_for(ws.recv(), timeout=5)
                    pytest.fail("Expected connection to close")
            except websockets.exceptions.ConnectionClosed as e:
                assert e.code == 4401, f"expected 4401 got {e.code}"
            except websockets.exceptions.InvalidStatusCode as e:
                assert e.status_code in (401, 403)
        asyncio.run(_run())

    def test_ws_private_campaign_non_member_closes_4403(self, gm_token, player_token):
        """Create a PRIVATE campaign + session, connect as non-member player → 4403."""
        # create private campaign (GM is owner, player not a member)
        pr = requests.post(f"{API}/campaigns",
                           json={"name": f"TEST_Private_{uuid.uuid4().hex[:6]}",
                                 "description": "private", "visibility": "private",
                                 "max_players": 4},
                           headers=h(gm_token))
        assert pr.status_code == 200, pr.text
        priv = pr.json()
        sr = requests.post(f"{API}/sessions",
                           json={"campaign_id": priv["id"], "title": "TEST_PrivS"},
                           headers=h(gm_token))
        assert sr.status_code == 200, sr.text
        priv_session = sr.json()

        async def _run():
            url = _ws_url(priv_session["id"], player_token)
            try:
                async with websockets.connect(url) as ws:
                    await asyncio.wait_for(ws.recv(), timeout=5)
                    pytest.fail("Expected connection to close with 4403")
            except websockets.exceptions.ConnectionClosed as e:
                assert e.code == 4403, f"expected 4403 got {e.code}"
            except websockets.exceptions.InvalidStatusCode as e:
                assert e.status_code in (401, 403)

        try:
            asyncio.run(_run())
        finally:
            requests.delete(f"{API}/campaigns/{priv['id']}", headers=h(gm_token))

    def test_ws_public_campaign_any_member_connects(self, player_token, session):
        """Valid token on PUBLIC campaign (fixture) → player (not explicit member) can connect and broadcast is received."""
        async def _run():
            url = _ws_url(session["id"], player_token)
            async with websockets.connect(url) as ws:
                msg = f"TEST_PUB_{uuid.uuid4().hex[:6]}"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(f"{API}/chat",
                                          json={"session_id": session["id"],
                                                "message": msg, "kind": "chat"},
                                          headers=h(player_token)),
                )
                frame = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(frame)
                assert data["type"] == "chat"
                assert data["data"]["message"] == msg
        asyncio.run(_run())


# ---------------- Campaign Genesis (new) ----------------

@pytest.fixture(scope="session")
def fresh_campaign(gm_token):
    """Separate public campaign used for genesis tests so it's isolated."""
    payload = {"name": f"TEST_Genesis_{uuid.uuid4().hex[:6]}",
               "description": "genesis", "visibility": "public",
               "max_players": 4, "power_level": "Heroic"}
    r = requests.post(f"{API}/campaigns", json=payload, headers=h(gm_token))
    assert r.status_code == 200, r.text
    camp = r.json()
    yield camp
    requests.delete(f"{API}/campaigns/{camp['id']}", headers=h(gm_token))


class TestGenesis:
    def test_get_genesis_auto_creates(self, gm_token, fresh_campaign):
        r = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                         headers=h(gm_token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["campaign_id"] == fresh_campaign["id"]
        # defaults
        assert d.get("phase_completed", 0) == 0
        assert d.get("tone_words", []) == []
        assert d.get("master_acts", []) == []
        assert "id" in d
        assert "created_at" in d

    def test_get_genesis_idempotent(self, gm_token, fresh_campaign):
        r1 = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                          headers=h(gm_token)).json()
        r2 = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                          headers=h(gm_token)).json()
        assert r1["id"] == r2["id"]

    def test_get_genesis_non_gm_403(self, player_token, fresh_campaign):
        r = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                         headers=h(player_token))
        assert r.status_code == 403

    def test_get_genesis_404(self, gm_token):
        r = requests.get(f"{API}/campaigns/nonexistent-id-xyz/genesis",
                         headers=h(gm_token))
        assert r.status_code == 404

    def test_put_genesis_full_payload(self, gm_token, fresh_campaign):
        body = {
            "campaign_id": fresh_campaign["id"],
            "sentence_who": "A fallen star-priest",
            "sentence_wants": "to restore the Sundered Choir",
            "sentence_badly_when": "before the Eclipse of Ashes",
            "sentence_using": "a chorus of heretic singers",
            "sentence_reasons": "the Archon has silenced their chord",
            "theme": "Hope rekindled in exile",
            "tone_words": ["mythic", "brooding", "sacred"],
            "nemesis_name": "Archon Velvyn",
            "nemesis_type": "villain",
            "nemesis_motive": "Impose perfect silence",
            "nemesis_resources": "Silent Choir, Dream-Wardens",
            "nemesis_weakness": "True name sung in thirds",
            "master_acts": [
                {"title": "Act I: Ember", "beat": "The priest returns"},
                {"title": "Act II: Storm", "beat": "The Choir hunts"},
            ],
            "adventures": [
                {"title": "The Silver Bell", "kind": "quest",
                 "hook": "Bell silenced", "stakes": "village silence",
                 "outcome": "song restored"},
            ],
            "seed_npcs": [
                {"name": "Sister Oru", "role": "ally", "note": "keeps the third"},
                {"name": "Khev the Still", "role": "rival", "note": "former student"},
            ],
            "beginning": "A lone bell in a deaf village",
            "ending": "The Sundered Choir sings again",
            "phase_completed": 7,
        }
        r = requests.put(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                         json=body, headers=h(gm_token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["theme"] == "Hope rekindled in exile"
        assert d["tone_words"] == ["mythic", "brooding", "sacred"]
        assert len(d["master_acts"]) == 2
        assert len(d["seed_npcs"]) == 2
        assert d["phase_completed"] == 7
        assert "updated_at" in d

        # GET confirms persistence
        g = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                         headers=h(gm_token)).json()
        assert g["nemesis_name"] == "Archon Velvyn"
        assert len(g["adventures"]) == 1

    def test_put_genesis_is_idempotent_upsert(self, gm_token, fresh_campaign):
        """Second PUT should update same doc (same id), not create a new one."""
        before = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                              headers=h(gm_token)).json()
        payload = {"campaign_id": fresh_campaign["id"],
                   "theme": "Twice-revised", "phase_completed": 3}
        r = requests.put(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                         json=payload, headers=h(gm_token))
        assert r.status_code == 200
        after = r.json()
        assert after["id"] == before["id"]
        assert after["theme"] == "Twice-revised"

    def test_put_genesis_non_gm_403(self, player_token, fresh_campaign):
        r = requests.put(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                         json={"campaign_id": fresh_campaign["id"], "theme": "x"},
                         headers=h(player_token))
        assert r.status_code == 403

    def test_seed_nodes_creates_4(self, gm_token, fresh_campaign):
        # ensure genesis has nemesis + 2 npcs + 1 adv (may already from previous test,
        # but re-PUT with the exact canonical payload to ensure)
        canon = {
            "campaign_id": fresh_campaign["id"],
            "nemesis_name": "Archon Velvyn",
            "nemesis_type": "villain",
            "seed_npcs": [
                {"name": "Sister Oru", "role": "ally", "note": "a"},
                {"name": "Khev the Still", "role": "rival", "note": "b"},
            ],
            "adventures": [
                {"title": "The Silver Bell", "kind": "quest",
                 "hook": "h", "stakes": "s", "outcome": "o"},
            ],
        }
        requests.put(f"{API}/campaigns/{fresh_campaign['id']}/genesis",
                     json=canon, headers=h(gm_token))

        # count existing nodes before seed
        before = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/nodes",
                              headers=h(gm_token)).json()
        before_ids = {n["id"] for n in before}

        r = requests.post(f"{API}/campaigns/{fresh_campaign['id']}/genesis/seed-nodes",
                          headers=h(gm_token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["nodes_created"] == 4

        # GM listing should now contain 4 new gm_only nodes: 3 npc + 1 quest
        after = requests.get(f"{API}/campaigns/{fresh_campaign['id']}/nodes",
                             headers=h(gm_token)).json()
        new_nodes = [n for n in after if n["id"] not in before_ids]
        assert len(new_nodes) == 4
        types = sorted(n["type"] for n in new_nodes)
        assert types == ["npc", "npc", "npc", "quest"]
        assert all(n["visibility"] == "gm_only" for n in new_nodes)
        # nemesis title present
        titles = [n["title"] for n in new_nodes]
        assert "Archon Velvyn" in titles
        assert "Sister Oru" in titles
        assert "Khev the Still" in titles
        assert "The Silver Bell" in titles

    def test_seed_nodes_player_forbidden(self, player_token, fresh_campaign):
        r = requests.post(f"{API}/campaigns/{fresh_campaign['id']}/genesis/seed-nodes",
                          headers=h(player_token))
        assert r.status_code == 403


# ---------------- CORS ----------------

class TestCORS:
    def test_preflight_preview_origin_ok(self):
        origin = "https://test-preview.preview.emergentagent.com"
        r = requests.options(
            f"{API}/campaigns",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        # 200 or 204 both acceptable for preflight
        assert r.status_code in (200, 204), f"status={r.status_code}"
        aco = r.headers.get("access-control-allow-origin")
        assert aco == origin, f"allow-origin={aco}"

    def test_preflight_unknown_origin_no_cors(self):
        r = requests.options(
            f"{API}/campaigns",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        aco = r.headers.get("access-control-allow-origin")
        # Should NOT echo evil.example.com
        assert aco != "https://evil.example.com", f"unexpected allow-origin={aco}"


# ---------------- Iteration 4: BESM Extras ----------------

class TestBESMExtras:
    def test_extras_book_and_rules_count(self):
        r = requests.get(f"{API}/besm/reference")
        assert r.status_code == 200
        d = r.json()
        assert d.get("extras_book") == "BESM Extras"
        assert "extras_rules" in d
        assert len(d["extras_rules"]) == 21, f"got {len(d['extras_rules'])} extras rules"

    def test_extras_rules_source_and_page(self):
        d = requests.get(f"{API}/besm/reference").json()
        for item in d["extras_rules"]:
            assert "name" in item
            assert "source" in item
            assert item["source"]["book"] == "BESM Extras"
            assert isinstance(item["source"]["page"], int)

    def test_extras_rules_contain_key_items(self):
        d = requests.get(f"{API}/besm/reference").json()
        names = [x["name"] for x in d["extras_rules"]]
        for n in ["Shock Value", "Sanity Points", "Skill Ranks", "Power Packs"]:
            assert n in names, f"missing extras rule {n}"


# ---------------- Iteration 4: Campaign primer + invite token ----------------

@pytest.fixture(scope="session")
def primer_campaign(gm_token):
    """Campaign with primer + allow/prohibit lists — used for invite tests."""
    payload = {
        "name": f"TEST_Primer_{uuid.uuid4().hex[:6]}",
        "description": "primer test",
        "visibility": "public",
        "max_players": 3,
        "player_primer": "Only human-scope powers",
        "prohibited_attributes": ["Mind Control", "Dynamic Powers"],
        "allowed_attributes": [],
        "prohibited_defects": [],
        "prohibited_skill_groups": ["Warrior"],
    }
    r = requests.post(f"{API}/campaigns", json=payload, headers=h(gm_token))
    assert r.status_code == 200, r.text
    camp = r.json()
    yield camp
    requests.delete(f"{API}/campaigns/{camp['id']}", headers=h(gm_token))


class TestCampaignPrimer:
    def test_create_returns_primer_and_invite(self, primer_campaign):
        assert primer_campaign["player_primer"] == "Only human-scope powers"
        assert primer_campaign["prohibited_attributes"] == ["Mind Control", "Dynamic Powers"]
        assert primer_campaign["prohibited_skill_groups"] == ["Warrior"]
        # invite_token: non-empty URL-safe ~22 chars (token_urlsafe(16) = 22)
        tok = primer_campaign.get("invite_token")
        assert isinstance(tok, str) and len(tok) >= 16

    def test_get_campaign_returns_primer(self, gm_token, primer_campaign):
        r = requests.get(f"{API}/campaigns/{primer_campaign['id']}", headers=h(gm_token))
        assert r.status_code == 200
        d = r.json()
        assert d["player_primer"] == "Only human-scope powers"
        assert d["prohibited_attributes"] == ["Mind Control", "Dynamic Powers"]
        assert d.get("invite_token") == primer_campaign["invite_token"]

    def test_put_campaign_updates_primer_and_preserves_meta(self, gm_token, primer_campaign):
        original_token = primer_campaign["invite_token"]
        original_gm = primer_campaign["gm_id"]
        original_created = primer_campaign["created_at"]
        payload = {
            "name": primer_campaign["name"],
            "description": primer_campaign["description"],
            "visibility": "public",
            "max_players": primer_campaign["max_players"],
            "power_level": "Heroic",
            "player_primer": "Updated primer — street-level only",
            "prohibited_attributes": ["Mind Control"],
            "allowed_attributes": [],
        }
        r = requests.put(f"{API}/campaigns/{primer_campaign['id']}",
                         json=payload, headers=h(gm_token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["player_primer"] == "Updated primer — street-level only"
        assert d["prohibited_attributes"] == ["Mind Control"]
        # preserved fields
        assert d["id"] == primer_campaign["id"]
        assert d["gm_id"] == original_gm
        assert d["invite_token"] == original_token
        assert d["created_at"] == original_created

    def test_put_campaign_non_gm_403(self, player_token, primer_campaign):
        r = requests.put(f"{API}/campaigns/{primer_campaign['id']}",
                         json={"name": "hijack", "description": "x"},
                         headers=h(player_token))
        assert r.status_code == 403


# ---------------- Iteration 4: Invite token flow ----------------

class TestInviteFlow:
    def test_public_invite_lookup_no_auth(self, primer_campaign):
        tok = primer_campaign["invite_token"]
        r = requests.get(f"{API}/invites/{tok}")  # NO auth header
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["campaign_id"] == primer_campaign["id"]
        assert d["name"] == primer_campaign["name"]
        assert d["gm_name"]
        assert "seated" in d and "max_players" in d and "full" in d
        assert d["full"] is False

    def test_invite_lookup_invalid_404(self):
        r = requests.get(f"{API}/invites/bogus-token-xyz")
        assert r.status_code == 404

    def test_accept_invite_requires_auth(self, primer_campaign):
        tok = primer_campaign["invite_token"]
        r = requests.post(f"{API}/invites/{tok}/accept")
        assert r.status_code == 401

    def test_accept_invite_adds_player(self, gm_token, player_token, primer_campaign):
        tok = primer_campaign["invite_token"]
        r = requests.post(f"{API}/invites/{tok}/accept", headers=h(player_token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["campaign_id"] == primer_campaign["id"]
        # Verify membership
        cr = requests.get(f"{API}/campaigns/{primer_campaign['id']}", headers=h(gm_token))
        member_ids = cr.json().get("member_ids", [])
        player_me = requests.get(f"{API}/auth/me", headers=h(player_token)).json()
        assert player_me["id"] in member_ids

    def test_accept_invite_idempotent_already_member(self, player_token, primer_campaign):
        tok = primer_campaign["invite_token"]
        r = requests.post(f"{API}/invites/{tok}/accept", headers=h(player_token))
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d.get("already") in (True, "gm")

    def test_accept_invite_as_gm_returns_already_gm(self, gm_token, primer_campaign):
        tok = primer_campaign["invite_token"]
        r = requests.post(f"{API}/invites/{tok}/accept", headers=h(gm_token))
        assert r.status_code == 200
        assert r.json().get("already") == "gm"

    def test_regenerate_invite_gm_only(self, gm_token, player_token, primer_campaign):
        # Non-GM forbidden
        bad = requests.post(
            f"{API}/campaigns/{primer_campaign['id']}/regenerate-invite",
            headers=h(player_token))
        assert bad.status_code == 403

        old_token = primer_campaign["invite_token"]
        r = requests.post(
            f"{API}/campaigns/{primer_campaign['id']}/regenerate-invite",
            headers=h(gm_token))
        assert r.status_code == 200, r.text
        new_token = r.json()["invite_token"]
        assert new_token and new_token != old_token

        # Old token should now 404
        old_lookup = requests.get(f"{API}/invites/{old_token}")
        assert old_lookup.status_code == 404

        # New token should resolve
        new_lookup = requests.get(f"{API}/invites/{new_token}")
        assert new_lookup.status_code == 200
        assert new_lookup.json()["campaign_id"] == primer_campaign["id"]

    def test_accept_invite_table_full(self, gm_token):
        """Create a 1-seat campaign, fill it, and have a 2nd user hit 'Table full'."""
        r = requests.post(f"{API}/campaigns",
                          json={"name": f"TEST_Full_{uuid.uuid4().hex[:6]}",
                                "description": "full test",
                                "visibility": "public", "max_players": 1},
                          headers=h(gm_token))
        assert r.status_code == 200
        camp = r.json()
        tok = camp["invite_token"]
        try:
            # Register user A, accept
            ea = f"TEST_{uuid.uuid4().hex[:6]}@t.com"
            ra = requests.post(f"{API}/auth/register",
                               json={"email": ea, "password": "password123",
                                     "name": "A"}).json()
            acc_a = requests.post(f"{API}/invites/{tok}/accept",
                                  headers=h(ra["access_token"]))
            assert acc_a.status_code == 200

            # Register user B, accept → should be 400 table full
            eb = f"TEST_{uuid.uuid4().hex[:6]}@t.com"
            rb = requests.post(f"{API}/auth/register",
                               json={"email": eb, "password": "password123",
                                     "name": "B"}).json()
            acc_b = requests.post(f"{API}/invites/{tok}/accept",
                                  headers=h(rb["access_token"]))
            assert acc_b.status_code == 400, acc_b.text
        finally:
            requests.delete(f"{API}/campaigns/{camp['id']}", headers=h(gm_token))


# ---------------- Iteration 4: Forgot password (Resend stub) ----------------

class TestForgotPassword:
    def test_forgot_password_known_email_returns_ok(self):
        """RESEND_API_KEY empty → should NOT error, returns {ok:true} and logs link."""
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": GM_EMAIL})
        assert r.status_code == 200, r.text
        assert r.json() == {"ok": True}

    def test_forgot_password_unknown_email_returns_ok(self):
        """Does not leak whether email exists."""
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": f"nope_{uuid.uuid4().hex[:6]}@nowhere.xyz"})
        assert r.status_code == 200
        assert r.json() == {"ok": True}
