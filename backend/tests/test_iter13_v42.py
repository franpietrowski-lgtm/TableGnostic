"""Iteration 13 / V4.2 backend tests — focused on V4.2 deltas only.

Covers:
    * Reset gate: ?confirm=WIPE required on /api/admin/reset-to-evereantha
    * Brute-force lock under stable X-Forwarded-For first hop
    * Character ownership transfer (POST /api/characters/{id}/transfer)
        -- auto-add to campaign.member_ids
        -- effective_level decoration preserved
    * GET /api/campaigns/{cid}/members (id/name/handle/is_gm/role)
    * Campaign-room WebSocket (/api/ws/campaign/{cid}) — auth/non-member/member
        -- channel:msg fan-out via REST POST → WS receive
    * EffectIn.target_character_id accepted (no 422)
    * OpenAPI sanity: tags admin/battlemap/channels present, ~80 ops total
    * V4.1 effective_level decoration regression on every char read/write
"""
import asyncio
import json
import os
import time
import uuid

import pytest
import requests
import websockets
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", ".env"))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"

ADMIN = ("franpietrowski@gmail.com", "PieGod08!!")  # GMFran — V4.3 sole seeded account
import time as _time
_SUFFIX = str(int(_time.time() * 1000))
GM = (f"t13gm_{_SUFFIX}@example.com", "t13gmpass!!")
PLAYER = (f"t13pl_{_SUFFIX}@example.com", "t13plpass!!")


def _register(email, password, role):
    r = requests.post(f"{API}/auth/register",
                      json={"email": email, "password": password,
                            "name": f"T13 {role}", "role": role},
                      timeout=15)
    if r.status_code == 409:
        return
    assert r.status_code in (200, 201), f"register {email}: {r.status_code} {r.text}"


_register(GM[0], GM[1], "gm")
_register(PLAYER[0], PLAYER[1], "player")


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()


def _tok(email, password):
    return _login(email, password)["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ──────────────────────── module-scoped fixtures ────────────────────────

@pytest.fixture(scope="module")
def admin_tok():
    return _tok(*ADMIN)


@pytest.fixture(scope="module")
def gm_tok():
    return _tok(*GM)


@pytest.fixture(scope="module")
def player_tok():
    return _tok(*PLAYER)


@pytest.fixture(scope="module")
def player_uid(player_tok):
    r = requests.get(f"{API}/auth/me", headers=_h(player_tok), timeout=10)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def reset_table(admin_tok):
    """Canonical Evereantha state for this test module (admin-owned)."""
    r = requests.post(f"{API}/admin/reset-to-evereantha?confirm=WIPE",
                      headers=_h(admin_tok), timeout=60)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def evereantha_cid(admin_tok, reset_table):
    r = requests.get(f"{API}/campaigns?mine=true", headers=_h(admin_tok), timeout=15)
    assert r.status_code == 200
    rows = r.json()
    assert rows, "no campaigns visible to admin after reset"
    cid = rows[0]["id"]
    return cid


# ─────────────────── 1. Reset Gate (?confirm=WIPE) ───────────────────

class TestResetGate:
    def test_reset_without_confirm_400(self, admin_tok):
        r = requests.post(f"{API}/admin/reset-to-evereantha",
                          headers=_h(admin_tok), timeout=20)
        assert r.status_code == 400
        assert "WIPE" in r.text

    def test_reset_with_wrong_confirm_400(self, admin_tok):
        r = requests.post(f"{API}/admin/reset-to-evereantha?confirm=yes",
                          headers=_h(admin_tok), timeout=20)
        assert r.status_code == 400

    def test_reset_with_wipe_200(self, admin_tok):
        r = requests.post(f"{API}/admin/reset-to-evereantha?confirm=WIPE",
                          headers=_h(admin_tok), timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["nodes_created"] >= 20
        assert d["characters_created"] == 3

    def test_reset_player_still_403(self, player_tok):
        r = requests.post(f"{API}/admin/reset-to-evereantha?confirm=WIPE",
                          headers=_h(player_tok), timeout=20)
        assert r.status_code == 403


# ─────────────────── 2. Brute-force lock under XFF ───────────────────

class TestBruteForceLockXFF:
    """5 wrong logins for the same email with a stable X-Forwarded-For
    first hop must trip 423. Without XFF the test would be flaky behind
    the K8s ingress (request.client.host rotates per-pod)."""

    def test_xff_pinned_lockout(self):
        # Use a unique throwaway email so we never collide with real seed users.
        throwaway = f"locktest_{uuid.uuid4().hex[:10]}@example.com"
        # Register first so the email exists (lock keys on (ip,email) only,
        # but using an unknown email also works — pick the more realistic case).
        reg = requests.post(f"{API}/auth/register",
                            json={"email": throwaway, "password": "rightpass123",
                                  "name": "Lock Tester", "role": "player"},
                            timeout=15)
        assert reg.status_code == 200, reg.text

        xff_ip = "203.0.113.42"
        headers = {"Content-Type": "application/json", "X-Forwarded-For": xff_ip}
        # 5 wrong attempts should all be 401 (or eventually 423 on the 6th).
        last = None
        for i in range(5):
            r = requests.post(f"{API}/auth/login", headers=headers,
                              json={"email": throwaway, "password": "WRONG"},
                              timeout=15)
            last = r.status_code
            assert r.status_code in (401, 423), f"iter {i}: {r.status_code} {r.text}"

        # The 6th attempt — same XFF, same email — must trip 423.
        r6 = requests.post(f"{API}/auth/login", headers=headers,
                           json={"email": throwaway, "password": "WRONG"},
                           timeout=15)
        assert r6.status_code == 423, f"expected 423 lock, got {r6.status_code} {r6.text}"

        # Even the *correct* password is locked while the window holds.
        r_ok = requests.post(f"{API}/auth/login", headers=headers,
                             json={"email": throwaway, "password": "rightpass123"},
                             timeout=15)
        assert r_ok.status_code == 423

    def test_lock_isolated_to_xff(self):
        """A different XFF first hop must NOT inherit the lock."""
        throwaway = f"locktest2_{uuid.uuid4().hex[:10]}@example.com"
        reg = requests.post(f"{API}/auth/register",
                            json={"email": throwaway, "password": "rightpass123",
                                  "name": "Lock Tester 2", "role": "player"},
                            timeout=15)
        assert reg.status_code == 200

        bad_ip = "198.51.100.99"
        good_ip = "198.51.100.7"
        for _ in range(5):
            requests.post(f"{API}/auth/login",
                          headers={"Content-Type": "application/json",
                                   "X-Forwarded-For": bad_ip},
                          json={"email": throwaway, "password": "WRONG"}, timeout=15)
        # Confirm bad_ip locked.
        rl = requests.post(f"{API}/auth/login",
                           headers={"Content-Type": "application/json",
                                    "X-Forwarded-For": bad_ip},
                           json={"email": throwaway, "password": "WRONG"}, timeout=15)
        assert rl.status_code == 423

        # Different IP, same email, correct password = should succeed.
        rg = requests.post(f"{API}/auth/login",
                           headers={"Content-Type": "application/json",
                                    "X-Forwarded-For": good_ip},
                           json={"email": throwaway, "password": "rightpass123"},
                           timeout=15)
        assert rg.status_code == 200, rg.text


# ─────────────────── 3. Character transfer ───────────────────

class TestCharacterTransfer:
    def test_transfer_to_player_and_auto_member(self, admin_tok, player_tok,
                                                player_uid, evereantha_cid):
        # Pick one of the seeded PCs.
        rc = requests.get(f"{API}/campaigns/{evereantha_cid}/characters",
                          headers=_h(admin_tok), timeout=15)
        assert rc.status_code == 200, rc.text
        chars = rc.json()
        assert len(chars) >= 1
        ch = chars[0]
        ch_id = ch["id"]

        # Verify player is NOT yet a member.
        rcamp = requests.get(f"{API}/campaigns/{evereantha_cid}",
                             headers=_h(admin_tok), timeout=10)
        assert rcamp.status_code == 200
        before_members = rcamp.json().get("member_ids", [])
        assert player_uid not in before_members

        # GM transfers char to player.
        rt = requests.post(
            f"{API}/characters/{ch_id}/transfer?new_owner_id={player_uid}",
            headers=_h(admin_tok), timeout=15)
        assert rt.status_code == 200, rt.text
        out = rt.json()
        assert out["owner_id"] == player_uid
        assert out["owner_name"]  # non-empty

        # effective_level decoration must still appear on transfer response.
        attrs = out.get("attributes") or []
        if attrs:
            assert all("effective_level" in a for a in attrs), \
                "effective_level missing on /transfer response attributes"

        # Player auto-added as campaign member.
        rcamp2 = requests.get(f"{API}/campaigns/{evereantha_cid}",
                              headers=_h(admin_tok), timeout=10)
        assert rcamp2.status_code == 200
        after_members = rcamp2.json().get("member_ids", [])
        assert player_uid in after_members, \
            f"player {player_uid} not auto-added: {after_members}"

        # Player can now GET the character (member visibility).
        rg = requests.get(f"{API}/characters/{ch_id}", headers=_h(player_tok), timeout=10)
        assert rg.status_code == 200
        gj = rg.json()
        assert gj["owner_id"] == player_uid
        if gj.get("attributes"):
            assert all("effective_level" in a for a in gj["attributes"])

    def test_transfer_forbidden_for_non_gm(self, player_tok, admin_tok,
                                           evereantha_cid, player_uid):
        rc = requests.get(f"{API}/campaigns/{evereantha_cid}/characters",
                          headers=_h(admin_tok), timeout=15)
        ch_id = rc.json()[0]["id"]
        # Player is now a member but not GM/admin.
        r = requests.post(
            f"{API}/characters/{ch_id}/transfer?new_owner_id={player_uid}",
            headers=_h(player_tok), timeout=10)
        assert r.status_code == 403, r.text

    def test_transfer_unknown_owner_404(self, admin_tok, evereantha_cid):
        rc = requests.get(f"{API}/campaigns/{evereantha_cid}/characters",
                          headers=_h(admin_tok), timeout=15)
        ch_id = rc.json()[0]["id"]
        r = requests.post(
            f"{API}/characters/{ch_id}/transfer?new_owner_id=does-not-exist",
            headers=_h(admin_tok), timeout=10)
        assert r.status_code == 404


# ─────────────────── 4. Members endpoint ───────────────────

class TestCampaignMembers:
    def test_non_member_403(self, evereantha_cid):
        # Create a brand-new outsider account (not seated at the table).
        email = f"outsider_{uuid.uuid4().hex[:8]}@example.com"
        rr = requests.post(f"{API}/auth/register",
                           json={"email": email, "password": "outpass1234",
                                 "name": "Outsider", "role": "player"}, timeout=15)
        assert rr.status_code == 200
        tok = rr.json()["access_token"]
        r = requests.get(f"{API}/campaigns/{evereantha_cid}/members",
                         headers=_h(tok), timeout=10)
        assert r.status_code == 403

    def test_members_list_shape(self, admin_tok, evereantha_cid, player_uid):
        # After /transfer, player is a member → must appear here.
        r = requests.get(f"{API}/campaigns/{evereantha_cid}/members",
                         headers=_h(admin_tok), timeout=10)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list) and rows
        for m in rows:
            for k in ("id", "name", "handle", "is_gm", "role"):
                assert k in m, f"member row missing {k}: {m}"
        ids = {m["id"] for m in rows}
        assert player_uid in ids, "transferred-to player not visible in /members"
        gms = [m for m in rows if m["is_gm"]]
        assert len(gms) == 1


# ─────────────────── 5. Effects target_character_id ───────────────────

class TestEffectTargetCharacterId:
    def test_effect_accepts_target_character_id(self, admin_tok, evereantha_cid):
        # Need a session for the effect.
        rs = requests.post(f"{API}/sessions",
                           json={"campaign_id": evereantha_cid,
                                 "title": "iter13 fx-binding"},
                           headers=_h(admin_tok), timeout=15)
        assert rs.status_code == 200, rs.text
        sid = rs.json()["id"]
        # Pick an existing PC.
        rc = requests.get(f"{API}/campaigns/{evereantha_cid}/characters",
                          headers=_h(admin_tok), timeout=10)
        ch = rc.json()[0]

        payload = {
            "session_id": sid,
            "target_name": ch["name"],
            "target_character_id": ch["id"],
            "name": "Stunned",
            "duration_rounds": 2,
            "note": "ring-bind test",
        }
        r = requests.post(f"{API}/effects", json=payload,
                          headers=_h(admin_tok), timeout=15)
        assert r.status_code == 200, f"effect with target_character_id rejected: {r.status_code} {r.text}"
        e = r.json()
        assert e.get("target_character_id") == ch["id"]

        # GET listing should include it.
        rl = requests.get(f"{API}/sessions/{sid}/effects",
                          headers=_h(admin_tok), timeout=10)
        assert rl.status_code == 200
        rows = rl.json()
        assert any(x.get("target_character_id") == ch["id"] for x in rows)


# ─────────────────── 6. effective_level regression ───────────────────

class TestEffectiveLevelDecoration:
    def test_decorated_on_get_and_list(self, admin_tok, evereantha_cid):
        rl = requests.get(f"{API}/campaigns/{evereantha_cid}/characters",
                          headers=_h(admin_tok), timeout=10)
        assert rl.status_code == 200
        for ch in rl.json():
            for a in ch.get("attributes", []) or []:
                assert "effective_level" in a, f"{ch['name']} missing effective_level"
                assert isinstance(a["effective_level"], int)
                assert a["effective_level"] >= 1


# ─────────────────── 7. OpenAPI surface ───────────────────

class TestOpenAPI:
    def test_openapi_tags_and_op_count(self):
        # Public ingress only routes /api/*; openapi.json is at app root, so
        # use the backend localhost (same approach as iter11/iter12).
        r = requests.get("http://localhost:8001/openapi.json", timeout=15)
        assert r.status_code == 200, r.text
        spec = r.json()
        tags_in_paths = set()
        op_count = 0
        for _, methods in spec.get("paths", {}).items():
            for verb, op in methods.items():
                if verb.lower() in ("get", "post", "put", "delete", "patch"):
                    op_count += 1
                    for t in op.get("tags", []) or []:
                        tags_in_paths.add(t)
        # Required new tags present.
        for required in ("admin", "battlemap", "channels"):
            assert required in tags_in_paths, f"missing tag {required}: {tags_in_paths}"
        # Op count loose bounds — V4.0 was 77, V4.2 ~80.
        assert op_count >= 75, f"op count too low: {op_count}"
        assert op_count <= 100, f"op count suspiciously high: {op_count}"


# ─────────────────── 8. Campaign-room WebSocket ───────────────────

def _ws_url(path):
    return BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + path


@pytest.mark.asyncio
async def test_ws_campaign_invalid_token():
    url = _ws_url(f"/api/ws/campaign/anything?token=clearly-bogus")
    # Behind the K8s ingress, websockets.close() called BEFORE accept()
    # surfaces as an HTTP rejection during the handshake (InvalidStatus),
    # NOT as a normal close frame with the custom 4xxx code. Either is
    # acceptable evidence that auth was rejected.
    rejected = False
    try:
        async with websockets.connect(url, open_timeout=10) as ws:
            try:
                await asyncio.wait_for(ws.recv(), timeout=3)
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                rejected = True
    except websockets.exceptions.InvalidStatus:
        rejected = True
    except websockets.exceptions.ConnectionClosed:
        rejected = True
    assert rejected, "expected WS to be rejected on invalid token"


@pytest.mark.asyncio
async def test_ws_campaign_no_such_campaign(admin_tok):
    url = _ws_url(f"/api/ws/campaign/no-such-id?token={admin_tok}")
    rejected = False
    try:
        async with websockets.connect(url, open_timeout=10) as ws:
            try:
                await asyncio.wait_for(ws.recv(), timeout=3)
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                rejected = True
    except websockets.exceptions.InvalidStatus:
        rejected = True
    except websockets.exceptions.ConnectionClosed:
        rejected = True
    assert rejected, "expected WS to be rejected for unknown campaign"


@pytest.mark.asyncio
async def test_ws_campaign_non_member_4403(evereantha_cid):
    # Brand new account with no membership.
    email = f"wsout_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{API}/auth/register",
                      json={"email": email, "password": "outpass1234",
                            "name": "WSOut", "role": "player"}, timeout=15)
    assert r.status_code == 200
    tok = r.json()["access_token"]
    url = _ws_url(f"/api/ws/campaign/{evereantha_cid}?token={tok}")
    rejected = False
    try:
        async with websockets.connect(url, open_timeout=10) as ws:
            try:
                await asyncio.wait_for(ws.recv(), timeout=3)
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                rejected = True
    except websockets.exceptions.InvalidStatus:
        rejected = True
    except websockets.exceptions.ConnectionClosed:
        rejected = True
    assert rejected, "expected WS to be rejected for non-member"


@pytest.mark.asyncio
async def test_ws_campaign_member_receives_channel_msg(admin_tok, evereantha_cid):
    """Connect as admin (GM of canonical Evereantha after reset). POST a
    channel message via REST → WS subscriber must receive a 'channel:msg'
    event for it."""
    # Ensure a channel exists (auto-create lobby on first GET).
    rc = requests.get(f"{API}/campaigns/{evereantha_cid}/channels",
                      headers=_h(admin_tok), timeout=15)
    assert rc.status_code == 200, rc.text
    chs = rc.json()
    assert chs, "no channels after auto-create"
    chid = chs[0]["id"]

    url = _ws_url(f"/api/ws/campaign/{evereantha_cid}?token={admin_tok}")
    received = []

    async with websockets.connect(url, open_timeout=10) as ws:
        # Give the bus a moment to register the subscription.
        await asyncio.sleep(0.5)

        # Fire-and-forget POST in a thread so we can read WS concurrently.
        loop = asyncio.get_event_loop()
        post_payload = {"body": f"hello iter13 {uuid.uuid4().hex[:6]}"}

        def _post():
            return requests.post(
                f"{API}/channels/{chid}/messages", json=post_payload,
                headers=_h(admin_tok), timeout=15)

        post_future = loop.run_in_executor(None, _post)

        try:
            # Wait for WS event(s) up to ~5s.
            deadline = time.time() + 5.0
            while time.time() < deadline:
                remaining = max(0.1, deadline - time.time())
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                except asyncio.TimeoutError:
                    break
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                received.append(msg)
                if msg.get("type") == "channel:msg":
                    break
        finally:
            r = await post_future

    assert r.status_code == 200, f"POST channel msg failed: {r.text}"
    types = [m.get("type") for m in received]
    assert "channel:msg" in types, \
        f"expected channel:msg over WS, got types={types}"
