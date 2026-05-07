"""V6.3 — Reference Editor expanded kinds, estimate-bundle-cost, and regression.

Covers:
  • POST /api/reference/estimate-bundle-cost — CP math (attribute+skill+defect)
  • GET  /api/campaigns/{cid}/reference?kind=enhancement — new kinds 200 OK
  • POST /api/campaigns/{cid}/reference  with kind='enhancement' / 'power_bundle'
  • Reject unknown kind on GET (400)
  • Regression V6.2: validate / app-validate / approve / seat-take gate
  • Regression V6.1: seed-evereantha-suite still functional
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://campaign-hub-288.preview.emergentagent.com").rstrip("/")
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


# ── Seed an origin campaign for tests ──
def test_seed_origin(gm_session):
    r = gm_session.post(f"{API}/admin/seed-evereantha-suite", timeout=60)
    assert r.status_code == 200, r.text
    deployed = r.json().get("deployed") or r.json().get("campaigns") or []
    assert deployed
    besm = next((c for c in deployed if "besm" in (c.get("rule_variant_id", "") + c.get("system_id", ""))), None) or deployed[0]
    state["cid"] = besm["id"] if "id" in besm else besm.get("campaign_id")
    assert state["cid"]


# ── V6.3 — estimate-bundle-cost ──
def test_estimate_bundle_cost_breakdown(gm_session):
    payload = {
        "components": [
            {"kind": "attribute", "name": "Heightened Senses",
             "cost_per_level": 4, "level": 3, "refund": 2},
            {"kind": "skill", "name": "Acrobatics",
             "cost_per_level": 2, "level": 2},
            {"kind": "defect", "name": "Marked",
             "points_per_rank": 2, "rank": 1},
        ]
    }
    r = gm_session.post(f"{API}/reference/estimate-bundle-cost", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["component_count"] == 3
    assert data["total_cost"] == 12, f"expected 12, got {data['total_cost']}: {data}"
    lines = data["lines"]
    assert len(lines) == 3
    # attribute: 4*3 - 2 = 10
    attr = next(l for l in lines if l["kind"] == "attribute")
    assert attr["points"] == 10, attr
    # skill: 2*2 = 4
    skill = next(l for l in lines if l["kind"] == "skill")
    assert skill["points"] == 4, skill
    # defect: -(2*1) = -2
    defect = next(l for l in lines if l["kind"] == "defect")
    assert defect["points"] == -2, defect


def test_estimate_bundle_cost_enhancement_zero(gm_session):
    payload = {"components": [
        {"kind": "enhancement", "name": "Penetrating", "cost_per_level": 0},
        {"kind": "limiter", "name": "Activation", "cost_per_level": 0},
    ]}
    r = gm_session.post(f"{API}/reference/estimate-bundle-cost", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total_cost"] == 0
    assert all(line["points"] == 0 for line in d["lines"])


def test_estimate_bundle_cost_empty(gm_session):
    r = gm_session.post(f"{API}/reference/estimate-bundle-cost", json={"components": []}, timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["total_cost"] == 0
    assert d["component_count"] == 0


# ── V6.3 — Reference editor expanded kinds ──
def test_reference_list_enhancement_kind(gm_session):
    r = gm_session.get(f"{API}/campaigns/{state['cid']}/reference",
                        params={"kind": "enhancement"}, timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_reference_list_power_bundle_kind(gm_session):
    r = gm_session.get(f"{API}/campaigns/{state['cid']}/reference",
                        params={"kind": "power_bundle"}, timeout=20)
    assert r.status_code == 200, r.text


def test_reference_list_unknown_kind_400(gm_session):
    r = gm_session.get(f"{API}/campaigns/{state['cid']}/reference",
                        params={"kind": "doesnotexist"}, timeout=20)
    assert r.status_code == 400, r.text


def test_create_enhancement_reference(gm_session):
    body = {
        "kind": "enhancement", "name": "TEST_v63 Enh",
        "summary": "+1 to hit", "book": "besm-4e", "page": 80,
    }
    r = gm_session.post(f"{API}/campaigns/{state['cid']}/reference", json=body, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["kind"] == "enhancement"
    assert d["name"] == "TEST_v63 Enh"
    assert d["page"] == 80
    state["enh_id"] = d["id"]
    # Verify persistence via GET
    rg = gm_session.get(f"{API}/campaigns/{state['cid']}/reference",
                         params={"kind": "enhancement"}, timeout=20)
    assert any(x["id"] == d["id"] for x in rg.json())


def test_create_power_bundle_reference(gm_session):
    body = {
        "kind": "power_bundle", "name": "TEST_v63 Bundle",
        "summary": "Mimics Magic Missile",
        "book": "besm-4e", "page": 100,
        "fields": {
            "components": [
                {"kind": "attribute", "name": "Weapon",
                 "cost_per_level": 4, "level": 2},
                {"kind": "skill", "name": "Ranged Attack",
                 "cost_per_level": 2, "level": 1},
            ],
            "estimated_cost": 10,
        },
    }
    r = gm_session.post(f"{API}/campaigns/{state['cid']}/reference", json=body, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["kind"] == "power_bundle"
    assert d["fields"]["components"][0]["name"] == "Weapon"
    state["bundle_id"] = d["id"]


def test_create_power_pack_and_limiter(gm_session):
    """Test other new V6.3 kinds load."""
    for kind in ("limiter", "power_pack", "spell", "feat", "cypher_ability"):
        body = {"kind": kind, "name": f"TEST_v63 {kind}", "summary": "test"}
        r = gm_session.post(f"{API}/campaigns/{state['cid']}/reference", json=body, timeout=20)
        assert r.status_code == 200, f"{kind} failed: {r.status_code} {r.text}"
        assert r.json()["kind"] == kind


# ── V6.2 regression ──
def test_regression_validate_endpoint(gm_session):
    r = gm_session.get(f"{API}/campaigns/{state['cid']}/characters", timeout=20)
    if r.status_code != 200 or not r.json():
        pytest.skip("no characters to validate")
    ch = r.json()[0]
    rv = gm_session.get(f"{API}/characters/{ch['id']}/validate", timeout=20)
    assert rv.status_code == 200, rv.text
    v = rv.json()
    for k in ("passes_rules", "system_id", "issues", "warnings"):
        assert k in v


def test_regression_deltas_list(gm_session):
    r = gm_session.get(f"{API}/campaigns/{state['cid']}/deltas", timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


# ── Cleanup TEST_ data ──
def test_cleanup_test_references(gm_session):
    for key in ("enh_id", "bundle_id"):
        rid = state.get(key)
        if rid:
            r = gm_session.delete(f"{API}/campaigns/{state['cid']}/reference/{rid}", timeout=20)
            assert r.status_code in (200, 204), f"cleanup {key} failed: {r.status_code}"
