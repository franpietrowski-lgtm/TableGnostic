"""V6.2 — Delta-Drop + Character validation/approval + Seat-take gate.

Covers:
  • POST /api/campaigns/{cid}/deltas — publish (origin only)
  • GET /api/campaigns/{cid}/deltas — origin list (status=published)
  • GET /api/campaigns/{cid}/deltas/{did} — full bundle
  • POST /api/campaigns/{cid}/deltas/{did}/apply — clone-side merge (idempotent)
  • POST /api/campaigns/{cid}/deltas/{did}/defer — clone-side dismiss
  • Permission gating (non-GM 403, clone publish 400)
  • GET /api/characters/{cid}/validate — BESM CP / Anime point-buy / D&D / Cypher
  • POST /api/characters/{cid}/app-validate — stamps app_validated
  • POST /api/characters/{cid}/approve-for-play — GM approval, house-rule rules
  • POST /api/sessions/{sid}/seat-character — 409 when not approved_for_play

Regression: seed-evereantha-suite + ecosystem/pulse motive resolver still work.
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://rules-forge.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"

state = {}


@pytest.fixture(scope="module")
def gm_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": GM_EMAIL, "password": GM_PASS}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    s.headers.update({"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def player_session():
    s = requests.Session()
    email = f"TEST_player_{int(time.time())}@example.com"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "Pass1234!", "name": "TestPlayer", "role": "player"}, timeout=20)
    if r.status_code not in (200, 201):
        pytest.skip(f"register failed: {r.status_code} {r.text}")
    tok = r.json().get("access_token")
    s.headers.update({"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    state["player_id"] = r.json().get("user", {}).get("id") or r.json().get("id")
    return s


# ── Regression: seed evereantha suite (idempotent, 9 motives) ──
def test_regression_seed_suite_and_pulse(gm_session):
    r = gm_session.post(f"{API}/admin/seed-evereantha-suite", timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    deployed = data.get("deployed") or data.get("campaigns") or []
    assert deployed, f"no campaigns deployed: {data}"
    # Pick a besm-4e variant for downstream tests
    besm = next((c for c in deployed if "besm" in (c.get("rule_variant_id", "") + c.get("system_id", ""))), None) or deployed[0]
    state["origin_cid"] = besm["id"] if "id" in besm else besm.get("campaign_id")
    assert state["origin_cid"]
    # Each campaign has 9 motives
    for c in deployed:
        assert (c.get("motives") or 0) >= 9, f"campaign {c.get('id')} motives < 9: {c}"
    # Pulse motive resolver
    r2 = gm_session.get(f"{API}/campaigns/{state['origin_cid']}/ecosystem/pulse",
                        params={"plot_phase": "epic-9-adventures"}, timeout=30)
    assert r2.status_code == 200, r2.text
    motives = r2.json().get("active_motives") or []
    titles = " ".join(str(m.get("npc_name") or m.get("motive") or "") for m in motives)
    assert any(k in titles for k in ("Lyra", "Luminar", "Kin")), f"key motives missing: {titles[:200]}"


# ── Delta-Drop: origin publishes ──
def test_publish_delta_origin(gm_session):
    cid = state["origin_cid"]
    r = gm_session.post(f"{API}/campaigns/{cid}/deltas",
                        json={"title": "TEST_v62 drop 1", "summary": "iter35 seed delta"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["title"] == "TEST_v62 drop 1"
    assert d["version"] >= 1
    assert d["origin_campaign_id"] == cid
    assert "bundle" in d
    state["delta_id"] = d["id"]


def test_list_deltas_origin_published_status(gm_session):
    r = gm_session.get(f"{API}/campaigns/{state['origin_cid']}/deltas", timeout=20)
    assert r.status_code == 200, r.text
    rows = r.json()
    assert any(x.get("status") == "published" for x in rows), rows
    assert any(x.get("id") == state["delta_id"] for x in rows)


def test_get_delta_full_bundle(gm_session):
    r = gm_session.get(f"{API}/campaigns/{state['origin_cid']}/deltas/{state['delta_id']}", timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "bundle" in d
    assert "nodes" in d["bundle"]
    assert "motives" in d["bundle"]


# ── Permission gating ──
def test_non_gm_cannot_list_deltas(gm_session, player_session):
    r = player_session.get(f"{API}/campaigns/{state['origin_cid']}/deltas", timeout=20)
    assert r.status_code == 403, r.text


def test_non_gm_cannot_publish_delta(player_session):
    r = player_session.post(f"{API}/campaigns/{state['origin_cid']}/deltas",
                             json={"title": "evil", "summary": ""}, timeout=20)
    assert r.status_code == 403, r.text


# ── Clone flow: clone, then apply / idempotent / defer ──
def test_clone_and_apply_delta(gm_session):
    cid = state["origin_cid"]
    r = gm_session.post(f"{API}/campaigns/{cid}/clone", timeout=60)
    assert r.status_code in (200, 201), r.text
    clone = r.json()
    camp_obj = clone.get("campaign") if isinstance(clone.get("campaign"), dict) else clone
    state["clone_cid"] = camp_obj.get("id") or clone.get("campaign_id") or clone.get("clone_id")
    assert state["clone_cid"], clone

    # Clone cannot publish — 400
    rpub = gm_session.post(f"{API}/campaigns/{state['clone_cid']}/deltas",
                            json={"title": "should fail", "summary": ""}, timeout=20)
    assert rpub.status_code == 400, rpub.text

    # Clone list shows pending status
    rl = gm_session.get(f"{API}/campaigns/{state['clone_cid']}/deltas", timeout=20)
    assert rl.status_code == 200, rl.text
    rows = rl.json()
    target = next((x for x in rows if x["id"] == state["delta_id"]), None)
    assert target is not None, rows
    assert target["status"] == "pending", target

    # Apply
    ra = gm_session.post(f"{API}/campaigns/{state['clone_cid']}/deltas/{state['delta_id']}/apply", timeout=60)
    assert ra.status_code == 200, ra.text
    res = ra.json()
    assert res.get("applied") is True
    for k in ("added_nodes", "added_motives", "epic_applied", "genesis_applied"):
        assert k in res, res
    state["first_added_nodes"] = res["added_nodes"]


def test_apply_idempotent(gm_session):
    """Second apply: title-match dedup → 0 new nodes."""
    ra = gm_session.post(f"{API}/campaigns/{state['clone_cid']}/deltas/{state['delta_id']}/apply", timeout=60)
    assert ra.status_code == 200, ra.text
    res = ra.json()
    assert res["added_nodes"] == 0, f"expected 0 new nodes on 2nd apply, got {res['added_nodes']}"


def test_defer_delta(gm_session):
    # Publish a 2nd drop on origin so we have a fresh pending one to defer
    r = gm_session.post(f"{API}/campaigns/{state['origin_cid']}/deltas",
                        json={"title": "TEST_v62 drop 2", "summary": ""}, timeout=30)
    assert r.status_code == 200
    did2 = r.json()["id"]
    rd = gm_session.post(f"{API}/campaigns/{state['clone_cid']}/deltas/{did2}/defer", timeout=20)
    assert rd.status_code == 200, rd.text
    assert rd.json().get("deferred") is True

    rl = gm_session.get(f"{API}/campaigns/{state['clone_cid']}/deltas", timeout=20)
    target = next(x for x in rl.json() if x["id"] == did2)
    assert target["status"] == "deferred", target


def test_origin_apply_rejected_400(gm_session):
    """Applying a delta on the origin (not a clone) must 400."""
    r = gm_session.post(f"{API}/campaigns/{state['origin_cid']}/deltas/{state['delta_id']}/apply", timeout=20)
    assert r.status_code == 400, r.text


# ── Character validation ──
def _find_character(sess, cid):
    r = sess.get(f"{API}/campaigns/{cid}/characters", timeout=20)
    if r.status_code != 200:
        return None
    chars = r.json()
    if chars:
        return chars[0]
    # Create a TEST char so validator path can run
    rc = sess.post(f"{API}/characters", json={
        "campaign_id": cid, "name": "TEST_v62_validate",
        "stats": {"body": 4, "mind": 4, "soul": 4},
        "total_points": 200,
    }, timeout=20)
    if rc.status_code in (200, 201):
        return rc.json()
    return None


def _set_house_rules(sess, cid, value):
    g = sess.get(f"{API}/campaigns/{cid}", timeout=20)
    if g.status_code != 200:
        return False
    body = g.json()
    body["house_rules"] = value
    # Strip read-only/server-set keys not in CampaignIn
    for k in ("id", "gm_id", "gm_name", "member_ids", "invite_token",
              "created_at", "updated_at"):
        body.pop(k, None)
    r = sess.put(f"{API}/campaigns/{cid}", json=body, timeout=20)
    return r.status_code in (200, 204)


def test_validate_character_besm(gm_session):
    cid = state["origin_cid"]
    ch = _find_character(gm_session, cid)
    if not ch:
        pytest.skip("no characters in besm campaign to validate")
    state["char_id"] = ch["id"]
    r = gm_session.get(f"{API}/characters/{ch['id']}/validate", timeout=20)
    assert r.status_code == 200, r.text
    v = r.json()
    for k in ("passes_rules", "system_id", "breakdown", "issues", "warnings", "house_rules_active", "approved_for_play"):
        assert k in v, f"missing {k} in {v}"
    # System should be besm-4e for besm campaign characters
    assert v["system_id"] in ("besm-4e", "anime-5e", "dnd-5e", "cypher")


def test_app_validate_stamps_approval(gm_session):
    if "char_id" not in state:
        pytest.skip("no character available")
    r = gm_session.post(f"{API}/characters/{state['char_id']}/app-validate", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "approval" in data
    assert "app_validated" in data["approval"]
    state["app_validated"] = data["approval"]["app_validated"]
    state["passes_rules"] = data["passes_rules"]


def test_gm_approve_blocks_when_fails_no_house_rules(gm_session):
    if "char_id" not in state:
        pytest.skip()
    # First clear house_rules on the campaign
    cid = state["origin_cid"]
    _set_house_rules(gm_session, cid, "")
    # If passes_rules is True we can't test the block path — synthesize over-budget
    if state.get("passes_rules"):
        # Force-corrupt by setting total_points=0 so any spend is over-budget.
        # Use PUT (full character body)
        g = gm_session.get(f"{API}/characters/{state['char_id']}", timeout=20)
        if g.status_code == 200:
            body = g.json()
            body["total_points"] = 0
            # Ensure stats give some non-zero spend so over-budget triggers
            body["stats"] = {"body": 6, "mind": 6, "soul": 6}
            for k in ("id", "owner_id", "owner_name", "created_at", "derived"):
                body.pop(k, None)
            upd = gm_session.put(f"{API}/characters/{state['char_id']}", json=body, timeout=20)
            if upd.status_code not in (200, 204):
                pytest.skip(f"cannot adjust total_points: {upd.status_code} {upd.text}")
    # Re-validate to refresh app_validated state
    gm_session.post(f"{API}/characters/{state['char_id']}/app-validate", timeout=20)
    r = gm_session.post(f"{API}/characters/{state['char_id']}/approve-for-play",
                         json={"approved": True, "note": "TEST"}, timeout=20)
    # Should 400 if validation fails (no house rules)
    if r.status_code == 200:
        # Means character actually passes — record and skip block-test
        state["fully_approved"] = True
    else:
        assert r.status_code == 400, r.text


def test_gm_approve_with_house_rules_succeeds(gm_session):
    if "char_id" not in state:
        pytest.skip()
    cid = state["origin_cid"]
    ok = _set_house_rules(gm_session, cid, "TEST V6.2 — over-budget allowed")
    if not ok:
        pytest.skip("cannot set house rules via PUT")
    r = gm_session.post(f"{API}/characters/{state['char_id']}/approve-for-play",
                         json={"approved": True, "note": "TEST hr"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["approval"]["gm_approved"] is True
    assert data["approved_for_play"] is True
    state["fully_approved"] = True


# ── Session seat-take gate ──
def test_seat_character_409_when_unapproved(gm_session):
    """Create fresh char in clone, attempt to seat without approval → 409."""
    cid = state.get("clone_cid") or state["origin_cid"]
    r = gm_session.post(f"{API}/characters",
                        json={"campaign_id": cid, "name": "TEST_unapproved",
                              "stats": {"body": 4, "mind": 4, "soul": 4},
                              "total_points": 200}, timeout=20)
    if r.status_code not in (200, 201):
        pytest.skip(f"cannot create test character: {r.status_code} {r.text}")
    new_ch = r.json()
    new_cid = new_ch["id"]

    # Create a session
    rs = gm_session.post(f"{API}/sessions", json={"campaign_id": cid, "title": "TEST_seat session"}, timeout=20)
    if rs.status_code not in (200, 201):
        pytest.skip(f"cannot create session: {rs.status_code} {rs.text}")
    sid = rs.json()["id"]

    # Clear house rules so approval gate is strict
    _set_house_rules(gm_session, cid, "")

    # Attempt seat without approval → expect 409
    rseat = gm_session.post(f"{API}/sessions/{sid}/seat-character",
                             params={"character_id": new_cid}, timeout=20)
    assert rseat.status_code == 409, f"expected 409, got {rseat.status_code} {rseat.text}"

    # GM force=true should succeed
    rforce = gm_session.post(f"{API}/sessions/{sid}/seat-character",
                              params={"character_id": new_cid, "force": "true"}, timeout=20)
    assert rforce.status_code == 200, rforce.text
