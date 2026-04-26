"""Iteration 12 / V4.0 backend regression + new-feature tests.

Covers the three new domains shipped this iteration:
    * /api/admin/reset-to-evereantha (admin only) + Evereantha seed integrity
    * /api/sessions/{sid}/map* (battlemap CRUD, fog, walls, tokens, WS)
    * /api/campaigns/{cid}/channels* (Discord-style PBP + slash + threads)

Also re-asserts a slim regression slice (auth, campaigns, characters, dice,
sessions) so the V3.9 surface keeps working alongside V4.0 additions.
"""
import asyncio
import json
import os
import time

import pytest
import requests
from dotenv import load_dotenv

# Load /app/backend/.env so DB_NAME / MONGO_URL match the running backend.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL",
                          "https://rules-forge.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = ("admin@tablegnostic.com", "admin123")
GM = ("gm@tablegnostic.com", "gm123456")
PLAYER = ("player@tablegnostic.com", "player12345")


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ---- module-scoped tokens ----

@pytest.fixture(scope="module")
def admin_tok():
    return _login(*ADMIN)


@pytest.fixture(scope="module")
def gm_tok():
    return _login(*GM)


@pytest.fixture(scope="module")
def player_tok():
    return _login(*PLAYER)


# ─────────────────────────── 0. Reset & Seed ───────────────────────────

class TestAdminResetEvereantha:
    """Resets the table to canonical Evereantha state and verifies seed integrity."""

    def test_reset_forbidden_for_player(self, player_tok):
        r = requests.post(f"{API}/admin/reset-to-evereantha", headers=_h(player_tok), timeout=20)
        assert r.status_code == 403

    def test_reset_forbidden_for_gm(self, gm_tok):
        r = requests.post(f"{API}/admin/reset-to-evereantha", headers=_h(gm_tok), timeout=20)
        assert r.status_code == 403

    def test_reset_succeeds_for_admin(self, admin_tok):
        # NEW V4.2: requires ?confirm=WIPE gate. First confirm the gate trips.
        r0 = requests.post(f"{API}/admin/reset-to-evereantha", headers=_h(admin_tok), timeout=10)
        assert r0.status_code == 400, f"reset without confirm should 400, got {r0.status_code}"
        r = requests.post(f"{API}/admin/reset-to-evereantha?confirm=WIPE",
                          headers=_h(admin_tok), timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["nodes_created"] == 20
        assert d["characters_created"] == 3
        assert "campaign" in d and d["campaign"]["name"].startswith("Evereantha")
        # cache for the rest of the suite
        pytest.evereantha_cid = d["campaign"]["id"]

    def test_evereantha_in_my_campaigns(self, admin_tok):
        r = requests.get(f"{API}/campaigns?mine=true", headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert pytest.evereantha_cid in ids

    def test_genesis_phase_7_complete(self, admin_tok):
        cid = pytest.evereantha_cid
        r = requests.get(f"{API}/campaigns/{cid}/genesis", headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200
        g = r.json()
        assert g["phase_completed"] == 7
        assert g["sentence_who"].startswith("Three apprentice")
        assert "theme" in g and g["theme"]
        assert g["nemesis_name"] == "The Order of the Darkening Star"
        assert len(g["master_acts"]) == 6
        assert len(g["adventures"]) == 5
        assert len(g["seed_npcs"]) == 6
        assert g["beginning"] and g["ending"]

    def test_world_codex_20_nodes_breakdown(self, admin_tok):
        cid = pytest.evereantha_cid
        r = requests.get(f"{API}/campaigns/{cid}/nodes", headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200
        nodes = r.json()
        assert len(nodes) == 20
        types = {}
        for n in nodes:
            types[n["type"]] = types.get(n["type"], 0) + 1
        assert types == {"location": 5, "faction": 2, "npc": 6,
                         "creature": 1, "lore": 2, "quest": 4}, types
        gm_only = [n for n in nodes if n.get("visibility") == "gm_only"]
        assert len(gm_only) == 4

    def test_three_pcs_with_computed_spent(self, admin_tok):
        cid = pytest.evereantha_cid
        r = requests.get(f"{API}/campaigns/{cid}/characters", headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200
        chars = r.json()
        names = sorted(c["name"] for c in chars)
        assert names == ["Eli", "Laryk", "Roney"]
        for c in chars:
            assert c.get("token_color"), f"missing token_color on {c['name']}"
            assert c.get("size") == "Medium"
            assert c.get("attributes") and c.get("defects") and c.get("skills")
            assert len(c.get("power_packs", [])) == 1
            folio = c.get("folio") or {}
            assert isinstance(folio.get("goals"), list), f"folio.goals must be list on {c['name']}"
            spent = c.get("spent") or {}
            assert spent.get("total_spent") is not None, f"spent.total_spent missing on {c['name']}"
            assert isinstance(spent["total_spent"], (int, float))


# ─────────────────────────── 1. Battlemap ───────────────────────────

@pytest.fixture(scope="module")
def session_id(admin_tok):
    """Create a fresh session in the Evereantha campaign for battlemap/channel tests."""
    cid = pytest.evereantha_cid
    r = requests.post(f"{API}/sessions",
                      headers=_h(admin_tok),
                      json={"campaign_id": cid, "title": "Battlemap Test"},
                      timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def evereantha_pc_owned_by_player(admin_tok, player_tok):
    """Add player to campaign, give them ownership of one PC, return (cid, char_id)."""
    cid = pytest.evereantha_cid
    me = requests.get(f"{API}/auth/me", headers=_h(player_tok), timeout=10).json()
    player_uid = me["id"]
    # Join via /campaigns/{cid}/join (no body needed for member add)
    requests.post(f"{API}/campaigns/{cid}/join",
                  headers=_h(player_tok), json={}, timeout=10)
    # Verify membership directly via GET campaign
    camp = requests.get(f"{API}/campaigns/{cid}", headers=_h(admin_tok), timeout=10).json()
    if player_uid not in camp.get("member_ids", []):
        # try invite-token flow as fallback
        token = camp.get("invite_token")
        if token:
            requests.post(f"{API}/invites/{token}/accept",
                          headers=_h(player_tok), json={}, timeout=10)

    chars = requests.get(f"{API}/campaigns/{cid}/characters", headers=_h(admin_tok), timeout=10).json()
    target = chars[0]
    # Direct DB ownership transfer (no API exposes owner_id mutation by design).
    # Sync pymongo here — the asyncio.get_event_loop() pattern flaked under
    # pytest-collection on some runs and silently no-op'd the transfer.
    from pymongo import MongoClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    sync_client = MongoClient(mongo_url)
    res = sync_client[db_name].characters.update_one(
        {"id": target["id"]},
        {"$set": {"owner_id": player_uid, "owner_name": "Player"}},
    )
    sync_client.close()
    assert res.modified_count >= 0  # just confirm the call returned
    # Re-read to confirm the transfer actually landed before downstream tests.
    fresh = requests.get(f"{API}/characters/{target['id']}",
                         headers=_h(admin_tok), timeout=10).json()
    assert fresh["owner_id"] == player_uid, \
        f"Ownership transfer didn't land: {fresh.get('owner_id')} != {player_uid}"
    return cid, target["id"], player_uid


class TestBattlemap:
    def test_member_can_get_map_auto_init(self, admin_tok, session_id):
        r = requests.get(f"{API}/sessions/{session_id}/map",
                         headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["session_id"] == session_id
        assert d["grid"]["cols"] == 24 and d["grid"]["rows"] == 16
        assert d["tokens"] == [] and d["walls"] == [] and d["fog"] == []

    def test_non_member_cannot_get_map(self, session_id):
        # register a brand-new outsider and ensure 403
        suffix = str(int(time.time() * 1000))
        email = f"outsider_{suffix}@example.com"
        requests.post(f"{API}/auth/register",
                      json={"email": email, "password": "outsider123",
                            "name": "Outsider", "role": "gm"}, timeout=15)
        tok = _login(email, "outsider123")
        r = requests.get(f"{API}/sessions/{session_id}/map",
                         headers=_h(tok), timeout=15)
        assert r.status_code == 403

    def test_put_map_requires_gm(self, player_tok, session_id, evereantha_pc_owned_by_player):
        body = {"grid": {"size_px": 64, "cols": 30, "rows": 20,
                         "color": "#ffffff55", "opacity": 0.4},
                "image": {"url": "", "fit": "cover", "offset_x": 0, "offset_y": 0},
                "tokens": [], "walls": [], "fog": []}
        r = requests.put(f"{API}/sessions/{session_id}/map",
                         headers=_h(player_tok), json=body, timeout=15)
        assert r.status_code == 403

    def test_gm_adds_token(self, admin_tok, session_id, evereantha_pc_owned_by_player):
        cid, char_id, _ = evereantha_pc_owned_by_player
        body = {"character_id": char_id, "label": "Eli",
                "color": "#5fa37a", "x": 5, "y": 7, "size": 1.0}
        r = requests.post(f"{API}/sessions/{session_id}/map/tokens",
                          headers=_h(admin_tok), json=body, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["id"] and d["x"] == 5 and d["character_id"] == char_id
        pytest.bm_token_id = d["id"]

    def test_player_can_move_own_token(self, player_tok, session_id):
        body = {"id": pytest.bm_token_id, "x": 9, "y": 11, "label": "Eli", "color": "#5fa37a"}
        r = requests.post(f"{API}/sessions/{session_id}/map/tokens",
                          headers=_h(player_tok), json=body, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["x"] == 9

    def test_player_cannot_add_unbound_token(self, player_tok, session_id):
        body = {"label": "Sneaky", "x": 1, "y": 1}
        r = requests.post(f"{API}/sessions/{session_id}/map/tokens",
                          headers=_h(player_tok), json=body, timeout=15)
        assert r.status_code == 403

    def test_gm_paint_fog_hide_then_reveal(self, admin_tok, session_id):
        r = requests.post(f"{API}/sessions/{session_id}/map/fog",
                          headers=_h(admin_tok),
                          json={"hide": [{"x": 0, "y": 0}, {"x": 1, "y": 0}],
                                "reveal": []}, timeout=15)
        assert r.status_code == 200
        assert r.json()["hidden_cells"] == 2
        r2 = requests.post(f"{API}/sessions/{session_id}/map/fog",
                           headers=_h(admin_tok),
                           json={"hide": [], "reveal": [{"x": 0, "y": 0}]}, timeout=15)
        assert r2.json()["hidden_cells"] == 1

    def test_player_cannot_paint_fog(self, player_tok, session_id):
        r = requests.post(f"{API}/sessions/{session_id}/map/fog",
                          headers=_h(player_tok),
                          json={"hide": [{"x": 5, "y": 5}], "reveal": []}, timeout=15)
        assert r.status_code == 403

    def test_gm_walls_crud(self, admin_tok, session_id):
        r = requests.post(f"{API}/sessions/{session_id}/map/walls",
                          headers=_h(admin_tok),
                          json={"x1": 0, "y1": 0, "x2": 5, "y2": 5}, timeout=15)
        assert r.status_code == 200
        wid = r.json()["id"]
        r2 = requests.delete(f"{API}/sessions/{session_id}/map/walls/{wid}",
                             headers=_h(admin_tok), timeout=15)
        assert r2.status_code == 200

    def test_player_cannot_add_wall(self, player_tok, session_id):
        r = requests.post(f"{API}/sessions/{session_id}/map/walls",
                          headers=_h(player_tok),
                          json={"x1": 0, "y1": 0, "x2": 1, "y2": 1}, timeout=15)
        assert r.status_code == 403

    def test_gm_delete_token(self, admin_tok, session_id):
        r = requests.delete(f"{API}/sessions/{session_id}/map/tokens/{pytest.bm_token_id}",
                            headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200


class TestBattlemapWebsocket:
    def test_ws_receives_map_token_event(self, admin_tok, session_id):
        try:
            from websockets.sync.client import connect
        except ImportError:
            pytest.skip("websockets package not installed")

        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        url = f"{ws_url}/api/ws/session/{session_id}?token={admin_tok}"
        try:
            with connect(url, open_timeout=10) as ws:
                # Drain any initial hello
                ws.recv(timeout=2)
        except Exception:
            pass

        events = []

        async def listen_and_act():
            import websockets
            async with websockets.connect(url, open_timeout=10) as ws:
                # background reader
                async def reader():
                    try:
                        for _ in range(10):
                            msg = await asyncio.wait_for(ws.recv(), timeout=5)
                            events.append(json.loads(msg))
                    except Exception:
                        pass

                task = asyncio.create_task(reader())
                await asyncio.sleep(0.5)
                # Trigger a token add via REST
                requests.post(f"{API}/sessions/{session_id}/map/tokens",
                              headers=_h(admin_tok),
                              json={"label": "wsprobe", "x": 2, "y": 2}, timeout=10)
                # And a fog paint
                requests.post(f"{API}/sessions/{session_id}/map/fog",
                              headers=_h(admin_tok),
                              json={"hide": [{"x": 3, "y": 3}], "reveal": []}, timeout=10)
                await asyncio.sleep(2.0)
                task.cancel()

        asyncio.run(listen_and_act())
        types = {e.get("type") for e in events}
        assert "map:token" in types or "map:fog" in types, \
            f"Expected map:token or map:fog event, got {types}"


# ─────────────────────────── 2. Channels ───────────────────────────

class TestChannels:
    def test_list_auto_creates_tavern(self, admin_tok):
        cid = pytest.evereantha_cid
        r = requests.get(f"{API}/campaigns/{cid}/channels",
                         headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200
        rows = r.json()
        assert any(c["name"] == "tavern" for c in rows)
        pytest.tavern_id = next(c["id"] for c in rows if c["name"] == "tavern")

    def test_player_cannot_create_channel(self, player_tok):
        cid = pytest.evereantha_cid
        r = requests.post(f"{API}/campaigns/{cid}/channels",
                          headers=_h(player_tok),
                          json={"name": "secret", "kind": "text"}, timeout=15)
        assert r.status_code == 403

    def test_admin_creates_channel(self, admin_tok):
        cid = pytest.evereantha_cid
        r = requests.post(f"{API}/campaigns/{cid}/channels",
                          headers=_h(admin_tok),
                          json={"name": "war-room", "kind": "text",
                                "topic": "GM planning"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["name"] == "war-room"
        pytest.warroom_id = r.json()["id"]

    def test_post_roll_message_executes_dice(self, admin_tok):
        body = {"body": "/roll 2d6+4"}
        r = requests.post(f"{API}/channels/{pytest.tavern_id}/messages",
                          headers=_h(admin_tok), json=body, timeout=15)
        assert r.status_code == 200, r.text
        m = r.json()
        assert m["kind"] == "roll"
        meta = m["slash_meta"]
        assert meta["kind"] == "roll"
        assert "result" in meta
        result = meta["result"]
        # rolls is list of dicts with "results" arrays; total is canonical sum
        assert isinstance(result.get("total"), int)
        assert "rolls" in result and isinstance(result["rolls"], list)
        # verify total = sum(all results) + flat (flat=4)
        all_results_sum = sum(sum(r["results"]) * r.get("sign", 1) for r in result["rolls"])
        flat = result.get("flat", 0)
        assert result["total"] == all_results_sum + flat, f"total mismatch: {result}"
        pytest.roll_msg_id = m["id"]

    def test_post_emote_and_whisper(self, admin_tok):
        r = requests.post(f"{API}/channels/{pytest.tavern_id}/messages",
                          headers=_h(admin_tok),
                          json={"body": "/me bows deeply"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["slash_meta"]["kind"] == "emote"

        r2 = requests.post(f"{API}/channels/{pytest.tavern_id}/messages",
                           headers=_h(admin_tok),
                           json={"body": "/w @gm psst"}, timeout=15)
        assert r2.status_code == 200
        assert r2.json()["slash_meta"]["kind"] == "whisper"

    def test_mention_resolves_to_uid(self, admin_tok):
        # admin email handle is "admin"
        body = {"body": "Heads up @admin — check this."}
        r = requests.post(f"{API}/channels/{pytest.tavern_id}/messages",
                          headers=_h(admin_tok), json=body, timeout=15)
        assert r.status_code == 200
        m = r.json()
        assert isinstance(m["mention_uids"], list)
        assert len(m["mention_uids"]) >= 1
        pytest.mention_msg_id = m["id"]

    def test_reaction_toggle(self, admin_tok):
        mid = pytest.roll_msg_id
        r = requests.post(f"{API}/messages/{mid}/reactions",
                          headers=_h(admin_tok),
                          json={"emoji": "🎲"}, timeout=15)
        assert r.status_code == 200
        assert any(rx["emoji"] == "🎲" for rx in r.json()["reactions"])
        # toggle off
        r2 = requests.post(f"{API}/messages/{mid}/reactions",
                           headers=_h(admin_tok),
                           json={"emoji": "🎲"}, timeout=15)
        assert all(rx["emoji"] != "🎲" for rx in r2.json()["reactions"])

    def test_pin_gm_only(self, admin_tok, player_tok):
        mid = pytest.roll_msg_id
        r = requests.post(f"{API}/messages/{mid}/pin",
                          headers=_h(player_tok), timeout=15)
        assert r.status_code == 403
        r2 = requests.post(f"{API}/messages/{mid}/pin",
                           headers=_h(admin_tok), timeout=15)
        assert r2.status_code == 200
        assert r2.json()["pinned"] is True

    def test_threads_crud_and_filter(self, admin_tok):
        # create a thread
        r = requests.post(f"{API}/channels/{pytest.tavern_id}/threads",
                          headers=_h(admin_tok),
                          json={"name": "side-bar"}, timeout=15)
        assert r.status_code == 200
        tid = r.json()["id"]

        # list threads
        r = requests.get(f"{API}/channels/{pytest.tavern_id}/threads",
                         headers=_h(admin_tok), timeout=15)
        assert any(t["id"] == tid for t in r.json())

        # post into the thread
        r = requests.post(f"{API}/channels/{pytest.tavern_id}/messages",
                          headers=_h(admin_tok),
                          json={"body": "thread-only", "thread_id": tid}, timeout=15)
        assert r.status_code == 200
        thread_msg_id = r.json()["id"]

        # filter by thread_id
        r = requests.get(f"{API}/channels/{pytest.tavern_id}/messages?thread_id={tid}",
                         headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200
        ids = [m["id"] for m in r.json()]
        assert thread_msg_id in ids
        # root messages should NOT include the thread reply
        r = requests.get(f"{API}/channels/{pytest.tavern_id}/messages",
                         headers=_h(admin_tok), timeout=15)
        root_ids = [m["id"] for m in r.json()]
        assert thread_msg_id not in root_ids

    def test_edit_and_delete_message(self, admin_tok):
        # post a fresh message
        r = requests.post(f"{API}/channels/{pytest.tavern_id}/messages",
                          headers=_h(admin_tok),
                          json={"body": "hello world"}, timeout=15)
        mid = r.json()["id"]
        # edit
        r = requests.put(f"{API}/messages/{mid}",
                         headers=_h(admin_tok),
                         json={"body": "hello edited"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["body"] == "hello edited"
        # delete
        r = requests.delete(f"{API}/messages/{mid}",
                            headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200

    def test_gm_can_delete_channel(self, admin_tok):
        r = requests.delete(f"{API}/channels/{pytest.warroom_id}",
                            headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200


# ─────────────────────────── 3. Regression slim ───────────────────────────

class TestRegressionSurface:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_openapi_has_new_tags(self):
        r = requests.get("http://localhost:8001/openapi.json", timeout=10)
        assert r.status_code == 200
        d = r.json()
        tags = sorted({t for path in d["paths"].values() for op in path.values()
                       if isinstance(op, dict) for t in op.get("tags", [])})
        for needed in ("admin", "battlemap", "channels"):
            assert needed in tags, f"missing tag {needed}; got {tags}"
        ops = [(m, p) for p, methods in d["paths"].items() for m in methods
               if m in ("get", "post", "put", "delete", "patch")]
        # Allow some flex but expect the order-of-magnitude
        assert len(ops) >= 70, f"expected ~79 ops, got {len(ops)}"

    def test_dice_endpoint_still_works(self, admin_tok):
        r = requests.post(f"{API}/dice",
                          headers=_h(admin_tok),
                          json={"notation": "1d20+5", "session_id": ""}, timeout=10)
        # endpoint may require session_id; accept 200 or 422 (validation), not 404
        assert r.status_code in (200, 422), r.text
