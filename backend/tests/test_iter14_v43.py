"""Iteration 14 / V4.3 — backend regression for the V4.3 deliverables.

Coverage:
  * Demo accounts retired: admin@/gm@/player@tablegnostic.com all 401 on /login
  * GMFran (franpietrowski@gmail.com / PieGod08!!) still works and is admin
  * Bidirectional node visibility flip (gm_only/shared/revealed) + clear-revealed_to on gm_only
  * Bulk visibility with updated count + invalid value + non-GM 403
  * Player journal auto-uploads to codex (player_journal node, gm_only) + chat echo
  * Recap auto-mirrors to codex (session_record node, is_finalized=False)
  * Finalize chronicle endpoint: 400 missing recap_node_id / invalid tone,
    404 cross-campaign recap, 403 non-GM, 503/positive on LLM call.

Module DOES NOT call /admin/reset-to-evereantha — it builds its own throwaway
campaign so it doesn't wipe in-flight state.
"""
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"

# Sole authoritative admin (GMFran).
GMFRAN = ("franpietrowski@gmail.com", "PieGod08!!")

_SUFFIX = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
GM = (f"t14gm_{_SUFFIX}@example.com", "t14gmpass!!")
PLAYER = (f"t14pl_{_SUFFIX}@example.com", "t14plpass!!")


# ──────────────────────── helpers ────────────────────────

def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _register(email, password, role, name=None):
    r = requests.post(f"{API}/auth/register",
                      json={"email": email, "password": password,
                            "name": name or f"T14 {role}", "role": role},
                      timeout=15)
    if r.status_code == 409:
        return
    assert r.status_code in (200, 201), f"register {email}: {r.status_code} {r.text}"


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()


def _tok(email, password):
    return _login(email, password)["access_token"]


# Register transient gm/player at module import time.
_register(GM[0], GM[1], "gm")
_register(PLAYER[0], PLAYER[1], "player")


# ──────────────────────── module-scoped fixtures ────────────────────────

@pytest.fixture(scope="module")
def gmfran_tok():
    return _tok(*GMFRAN)


@pytest.fixture(scope="module")
def gm_tok():
    return _tok(*GM)


@pytest.fixture(scope="module")
def player_tok():
    return _tok(*PLAYER)


@pytest.fixture(scope="module")
def gm_uid(gm_tok):
    r = requests.get(f"{API}/auth/me", headers=_h(gm_tok), timeout=10)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def player_uid(player_tok):
    r = requests.get(f"{API}/auth/me", headers=_h(player_tok), timeout=10)
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def campaign_id(gm_tok, player_tok, player_uid):
    """Create a throwaway campaign owned by GM; player joins via invite."""
    r = requests.post(f"{API}/campaigns",
                      headers=_h(gm_tok),
                      json={"name": f"V43-Iter14-{_SUFFIX}",
                            "system": "BESM 4E", "visibility": "public"},
                      timeout=15)
    assert r.status_code in (200, 201), r.text
    cid = r.json()["id"]
    invite = r.json()["invite_token"]
    # Player joins via invite.
    j = requests.post(f"{API}/invites/{invite}/accept",
                      headers=_h(player_tok), timeout=10)
    assert j.status_code in (200, 201), j.text
    return cid


@pytest.fixture(scope="module")
def session_id(gm_tok, campaign_id):
    r = requests.post(f"{API}/sessions",
                      headers=_h(gm_tok),
                      json={"campaign_id": campaign_id, "title": "Iter14 chronicle session"},
                      timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def player_character(player_tok, campaign_id):
    """Create a minimal character owned by player."""
    r = requests.post(f"{API}/characters",
                      headers=_h(player_tok),
                      json={"campaign_id": campaign_id,
                            "name": f"PC-{_SUFFIX}",
                            "concept": "wandering scribe"},
                      timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


# ──────────────────────── tests ────────────────────────

# Module: V4.3 demo retirement
class TestDemoAccountsRetired:
    @pytest.mark.parametrize("email,password", [
        ("admin@tablegnostic.com", "admin123"),
        ("gm@tablegnostic.com", "gm123456"),
        ("player@tablegnostic.com", "player12345"),
    ])
    def test_retired_demo_login_401(self, email, password):
        r = requests.post(f"{API}/auth/login",
                          json={"email": email, "password": password}, timeout=15)
        assert r.status_code == 401, (
            f"Retired demo {email} should return 401 (got {r.status_code}: {r.text[:200]})"
        )

    def test_gmfran_login_ok_admin(self):
        out = _login(*GMFRAN)
        assert "access_token" in out and isinstance(out["access_token"], str)
        me = requests.get(f"{API}/auth/me",
                          headers=_h(out["access_token"]), timeout=10)
        assert me.status_code == 200
        body = me.json()
        assert body.get("role") == "admin", body
        assert body.get("email") == GMFRAN[0]


# Module: bidirectional node visibility (PUT /api/nodes/{nid}/visibility)
class TestNodeVisibilityFlip:
    @pytest.fixture
    def node_id(self, gm_tok, campaign_id):
        r = requests.post(f"{API}/nodes",
                          headers=_h(gm_tok),
                          json={"campaign_id": campaign_id, "type": "lore",
                                "title": "Visibility-test", "content": "secret",
                                "visibility": "gm_only"},
                          timeout=10)
        assert r.status_code in (200, 201), r.text
        return r.json()["id"]

    def test_flip_to_shared(self, gm_tok, node_id):
        r = requests.put(f"{API}/nodes/{node_id}/visibility",
                         headers=_h(gm_tok),
                         json={"visibility": "shared"}, timeout=10)
        assert r.status_code == 200, r.text
        assert r.json() == {"ok": True, "visibility": "shared"}

    def test_flip_to_revealed_then_back_to_gm_only_clears_revealed_to(
            self, gm_tok, campaign_id, node_id, player_uid):
        # First, mark revealed (use the legacy /reveal which appends to revealed_to)
        r = requests.post(f"{API}/nodes/{node_id}/reveal",
                          headers=_h(gm_tok),
                          json={"user_ids": [player_uid]}, timeout=10)
        assert r.status_code == 200, r.text
        # Confirm node has revealed_to populated and visibility=revealed
        rows = requests.get(f"{API}/campaigns/{campaign_id}/nodes",
                            headers=_h(gm_tok), timeout=10).json()
        node = next(n for n in rows if n["id"] == node_id)
        assert node["visibility"] == "revealed"
        assert player_uid in node.get("revealed_to", [])

        # Now flip back to gm_only via the V4.3 bidirectional endpoint
        r2 = requests.put(f"{API}/nodes/{node_id}/visibility",
                          headers=_h(gm_tok),
                          json={"visibility": "gm_only"}, timeout=10)
        assert r2.status_code == 200, r2.text
        rows2 = requests.get(f"{API}/campaigns/{campaign_id}/nodes",
                             headers=_h(gm_tok), timeout=10).json()
        node2 = next(n for n in rows2 if n["id"] == node_id)
        assert node2["visibility"] == "gm_only"
        # Critical V4.3 requirement: revealed_to MUST be cleared
        assert node2.get("revealed_to", []) == [], (
            f"revealed_to should be cleared on gm_only flip, got {node2.get('revealed_to')}"
        )

    def test_invalid_visibility_400(self, gm_tok, node_id):
        r = requests.put(f"{API}/nodes/{node_id}/visibility",
                         headers=_h(gm_tok),
                         json={"visibility": "public"}, timeout=10)
        assert r.status_code == 400, r.text

    def test_player_cannot_change_visibility(self, player_tok, node_id):
        r = requests.put(f"{API}/nodes/{node_id}/visibility",
                         headers=_h(player_tok),
                         json={"visibility": "shared"}, timeout=10)
        assert r.status_code == 403, r.text


# Module: bulk visibility (POST /api/campaigns/{cid}/nodes/bulk-visibility)
class TestBulkVisibility:
    def test_bulk_shared_then_gm_only_returns_count(
            self, gm_tok, campaign_id):
        # Create a few nodes.
        ids = []
        for i in range(3):
            rr = requests.post(f"{API}/nodes",
                               headers=_h(gm_tok),
                               json={"campaign_id": campaign_id, "type": "lore",
                                     "title": f"Bulk-{i}", "content": "x",
                                     "visibility": "gm_only"},
                               timeout=10)
            assert rr.status_code in (200, 201), rr.text
            ids.append(rr.json()["id"])

        r1 = requests.post(f"{API}/campaigns/{campaign_id}/nodes/bulk-visibility",
                           headers=_h(gm_tok),
                           json={"visibility": "shared"}, timeout=10)
        assert r1.status_code == 200, r1.text
        body = r1.json()
        assert body["ok"] is True
        assert body["visibility"] == "shared"
        # Should have updated AT LEAST the 3 we just created (other tests may have added more).
        assert body["updated"] >= 3, body

        r2 = requests.post(f"{API}/campaigns/{campaign_id}/nodes/bulk-visibility",
                           headers=_h(gm_tok),
                           json={"visibility": "gm_only"}, timeout=10)
        assert r2.status_code == 200, r2.text
        assert r2.json()["visibility"] == "gm_only"

    def test_bulk_invalid_visibility_400(self, gm_tok, campaign_id):
        r = requests.post(f"{API}/campaigns/{campaign_id}/nodes/bulk-visibility",
                          headers=_h(gm_tok),
                          json={"visibility": "revealed"}, timeout=10)
        assert r.status_code == 400, r.text

    def test_bulk_player_403(self, player_tok, campaign_id):
        r = requests.post(f"{API}/campaigns/{campaign_id}/nodes/bulk-visibility",
                          headers=_h(player_tok),
                          json={"visibility": "shared"}, timeout=10)
        assert r.status_code == 403, r.text


# Module: player journal → codex node
class TestPlayerJournalToCodex:
    def test_journal_creates_codex_node_and_keeps_folio_copy(
            self, player_tok, gm_tok, campaign_id, session_id, player_character):
        text = f"Iter14 journal entry — {_SUFFIX}"
        r = requests.post(f"{API}/characters/{player_character}/journal",
                          headers=_h(player_tok),
                          json={"text": text, "session_id": session_id},
                          timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        # V4.3 contract: response carries codex_node_id
        assert "codex_node_id" in body and body["codex_node_id"], body
        assert body["ok"] is True
        assert body["entry"]["text"] == text
        node_id = body["codex_node_id"]

        # (a) folio.journal contains the entry
        ch = requests.get(f"{API}/characters/{player_character}",
                          headers=_h(player_tok), timeout=10).json()
        folio_journal = (ch.get("folio") or {}).get("journal", [])
        assert any(e.get("text") == text for e in folio_journal), folio_journal

        # (b) New codex node — type=player_journal, gm_only, fields populated, content matches
        rows = requests.get(f"{API}/campaigns/{campaign_id}/nodes",
                            headers=_h(gm_tok), timeout=10).json()
        node = next((n for n in rows if n["id"] == node_id), None)
        assert node is not None, "new codex node not visible to GM"
        assert node["type"] == "player_journal"
        assert node["visibility"] == "gm_only"
        assert node["content"] == text
        assert node["fields"]["character_id"] == player_character
        assert node["fields"]["session_id"] == session_id

        # Player must NOT see this gm_only node
        prows = requests.get(f"{API}/campaigns/{campaign_id}/nodes",
                             headers=_h(player_tok), timeout=10).json()
        assert all(n["id"] != node_id for n in prows), \
            "player should not see gm_only player_journal node"

        # (c) Chat echo present in session log
        chat = requests.get(f"{API}/sessions/{session_id}/chat",
                            headers=_h(gm_tok), timeout=10)
        assert chat.status_code == 200, chat.text
        assert any(("[journal]" in m.get("message", "") and text in m.get("message", ""))
                   for m in chat.json()), "chat echo of journal not found"


# Module: recap auto-mirror + finalize chronicle
class TestRecapAndFinalize:
    @pytest.fixture(scope="class")
    def session_record_node(self, gm_tok, campaign_id):
        """Manually create a session_record node so finalize tests don't depend
        on the LLM-backed /recap endpoint succeeding."""
        r = requests.post(f"{API}/nodes",
                          headers=_h(gm_tok),
                          json={"campaign_id": campaign_id,
                                "type": "session_record",
                                "title": "Manual recap node",
                                "content": "Original recap content for finalize tests.",
                                "visibility": "gm_only",
                                "fields": {"is_finalized": False}},
                          timeout=10)
        assert r.status_code in (200, 201), r.text
        return r.json()["id"]

    def test_finalize_missing_recap_node_id_400(
            self, gm_tok, session_id):
        r = requests.post(f"{API}/sessions/{session_id}/finalize",
                          headers=_h(gm_tok),
                          json={"journal_node_ids": [], "tone": "lyrical"},
                          timeout=15)
        assert r.status_code == 400, r.text

    def test_finalize_invalid_tone_400(
            self, gm_tok, session_id, session_record_node):
        r = requests.post(f"{API}/sessions/{session_id}/finalize",
                          headers=_h(gm_tok),
                          json={"recap_node_id": session_record_node,
                                "journal_node_ids": [],
                                "tone": "epic"},
                          timeout=15)
        assert r.status_code == 400, r.text

    def test_finalize_cross_campaign_recap_404(
            self, gmfran_tok, gm_tok, session_id, campaign_id):
        # Build a foreign campaign owned by GMFran with its own session_record node.
        c = requests.post(f"{API}/campaigns",
                          headers=_h(gmfran_tok),
                          json={"name": f"V43-Iter14-foreign-{_SUFFIX}",
                                "visibility": "private"},
                          timeout=15)
        assert c.status_code in (200, 201), c.text
        foreign_cid = c.json()["id"]
        n = requests.post(f"{API}/nodes",
                          headers=_h(gmfran_tok),
                          json={"campaign_id": foreign_cid,
                                "type": "session_record",
                                "title": "Foreign recap",
                                "content": "foreign",
                                "visibility": "gm_only"},
                          timeout=10)
        assert n.status_code in (200, 201), n.text
        foreign_node_id = n.json()["id"]

        r = requests.post(f"{API}/sessions/{session_id}/finalize",
                          headers=_h(gm_tok),
                          json={"recap_node_id": foreign_node_id,
                                "journal_node_ids": [],
                                "tone": "lyrical"},
                          timeout=15)
        assert r.status_code == 404, r.text

    def test_finalize_player_403(
            self, player_tok, session_id, session_record_node):
        r = requests.post(f"{API}/sessions/{session_id}/finalize",
                          headers=_h(player_tok),
                          json={"recap_node_id": session_record_node,
                                "journal_node_ids": [],
                                "tone": "lyrical"},
                          timeout=15)
        assert r.status_code == 403, r.text

    def test_recap_creates_session_record_node(
            self, gm_tok, campaign_id, session_id):
        # Seed at least one chat message — recap requires history.
        c = requests.post(f"{API}/chat",
                          headers=_h(gm_tok),
                          json={"session_id": session_id,
                                "message": "The party reached the iron gates of Iter14.",
                                "kind": "chat"},
                          timeout=10)
        assert c.status_code in (200, 201), c.text

        r = requests.post(f"{API}/sessions/{session_id}/recap",
                          headers=_h(gm_tok),
                          json={"style": "narrative"},
                          timeout=120)
        if r.status_code == 503:
            pytest.skip("EMERGENT_LLM_KEY not configured — recap LLM path skipped")
        if r.status_code in (429, 502):
            pytest.skip(f"Recap LLM transient ({r.status_code}): {r.text[:200]}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "codex_node_id" in body and body["codex_node_id"]
        node_id = body["codex_node_id"]

        rows = requests.get(f"{API}/campaigns/{campaign_id}/nodes",
                            headers=_h(gm_tok), timeout=10).json()
        node = next((n for n in rows if n["id"] == node_id), None)
        assert node is not None
        assert node["type"] == "session_record"
        assert node["visibility"] == "gm_only"
        assert node["fields"]["session_id"] == session_id
        assert node["fields"]["is_finalized"] is False
        assert node["content"] == body["text"]

    def test_finalize_positive_path(
            self, gm_tok, campaign_id, session_id, session_record_node, player_tok,
            player_character):
        # Ensure at least one player_journal node exists in this campaign.
        jr = requests.post(f"{API}/characters/{player_character}/journal",
                           headers=_h(player_tok),
                           json={"text": "I scribbled a final entry before the gate.",
                                 "session_id": session_id},
                           timeout=15)
        assert jr.status_code == 200, jr.text
        journal_node_id = jr.json()["codex_node_id"]

        r = requests.post(f"{API}/sessions/{session_id}/finalize",
                          headers=_h(gm_tok),
                          json={"recap_node_id": session_record_node,
                                "journal_node_ids": [journal_node_id],
                                "tone": "terse"},
                          timeout=120)
        if r.status_code == 503:
            pytest.skip("EMERGENT_LLM_KEY not configured — finalize LLM path skipped")
        if r.status_code in (429, 502):
            pytest.skip(f"Finalize LLM transient ({r.status_code}): {r.text[:200]}")
        assert r.status_code == 200, r.text
        node = r.json()
        assert node["id"] == session_record_node
        assert node["type"] == "session_record"
        f = node["fields"]
        assert f.get("is_finalized") is True
        assert f.get("tone") == "terse"
        assert f.get("journal_ids") == [journal_node_id]
        # Original recap is preserved for audit.
        assert "original_recap" in f and f["original_recap"], f
        # Title now reads "Chronicle — ..." per recap.py finalize block.
        assert node["title"].startswith("Chronicle"), node["title"]
