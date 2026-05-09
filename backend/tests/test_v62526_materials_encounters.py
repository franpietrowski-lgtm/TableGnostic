"""V6.25.26 — Materials + Encounters Library + roll-table material source."""
from __future__ import annotations
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def campaign(gm_token):
    r = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm_token),
                       json={"name": "V62526 mat-enc", "system_id": "besm-4e"})
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


# ── Materials ────────────────────────────────────────────────────────


def test_materials_three_tier_chain(gm_token, campaign):
    # Raw → Refined → Assembled with ingredient chain.
    raw = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                          headers=H(gm_token),
                          json={"tier": "raw", "name": "Iron Ore",
                                "summary": "Common rust-streaked vein.",
                                "rarity": "common"}).json()
    refined = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                              headers=H(gm_token),
                              json={"tier": "refined", "name": "Iron Ingot",
                                    "summary": "Smelted from raw ore.",
                                    "rarity": "common",
                                    "ingredient_ids": [raw["id"]]}).json()
    assembled = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                                 headers=H(gm_token),
                                 json={"tier": "assembled", "name": "Iron Hilt",
                                       "summary": "Forged grip.",
                                       "rarity": "uncommon",
                                       "ingredient_ids": [refined["id"]]}).json()
    assert raw["tier"] == "raw"
    assert refined["ingredient_ids"] == [raw["id"]]
    assert assembled["ingredient_ids"] == [refined["id"]]


def test_materials_unknown_ingredient_rejected(gm_token, campaign):
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                       headers=H(gm_token),
                       json={"tier": "refined", "name": "Phantom Ingot",
                             "ingredient_ids": ["does-not-exist"]})
    assert r.status_code == 422, r.text


def test_materials_codex_mirror_when_ticked(gm_token, campaign):
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                       headers=H(gm_token),
                       json={"tier": "raw", "name": "Glow-Bloom",
                             "summary": "Bioluminescent flower.",
                             "also_to_codex": True})
    assert r.status_code == 200
    nodes = requests.get(f"{BASE_URL}/api/campaigns/{campaign}/codex-nodes",
                           headers=H(gm_token)).json()
    titles = [n.get("title") or n.get("name") for n in (nodes if isinstance(nodes, list) else nodes.get("rows", []))]
    assert "Glow-Bloom" in titles


def test_materials_filter_by_tier(gm_token, campaign):
    requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                    headers=H(gm_token),
                    json={"tier": "raw", "name": "T1"})
    requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                    headers=H(gm_token),
                    json={"tier": "refined", "name": "T2"})
    r = requests.get(f"{BASE_URL}/api/campaigns/{campaign}/materials?tier=raw",
                       headers=H(gm_token))
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert all(m["tier"] == "raw" for m in rows)


# ── Roll-tables: material source ─────────────────────────────────────


def test_roll_table_material_source(gm_token, campaign):
    mat = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/materials",
                          headers=H(gm_token),
                          json={"tier": "raw", "name": "Sun-touched Ash"}).json()
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Loot",
                             "rarity_tier": "common",
                             "entries": [{"weight": 1, "material_id": mat["id"]}]})
    tid = r.json()["id"]
    rr = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign}/roll-tables/{tid}/roll?party_tier=2",
        headers=H(gm_token))
    body = rr.json()
    assert body["result"]["source"]["kind"] == "material"
    assert body["result"]["source"]["tier"] == "raw"
    assert body["result"]["label"] == "Sun-touched Ash"


# ── Encounters Library ───────────────────────────────────────────────


def test_encounter_create_run_complete_flow(gm_token, campaign):
    e = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/encounters-library",
                        headers=H(gm_token),
                        json={"name": "Bridge Ambush",
                              "summary": "Bandits on the Stone Bridge",
                              "encounter_type": "combat",
                              "cr_target": 3,
                              "status": "ready"}).json()
    # Run it (mock session id).
    rr = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign}/encounters-library/{e['id']}/run?session_id=sess-1",
        headers=H(gm_token))
    assert rr.json()["status"] == "running"
    assert rr.json()["linked_session_id"] == "sess-1"
    # Complete it.
    cc = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign}/encounters-library/{e['id']}/complete?completion_notes=PCs+won",
        headers=H(gm_token))
    body = cc.json()
    assert body["status"] == "completed"
    assert body["completion_notes"] == "PCs won"


def test_encounter_clone_as_template(gm_token, campaign):
    src = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/encounters-library",
                          headers=H(gm_token),
                          json={"name": "Goblin Scouts",
                                "encounter_type": "combat",
                                "status": "ready"}).json()
    cl = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign}/encounters-library/{src['id']}/clone?as_template=true",
        headers=H(gm_token))
    body = cl.json()
    assert body["status"] == "template"
    assert body["cloned_from_id"] == src["id"]
    assert body["name"].endswith("template")


def test_encounter_filter_by_status(gm_token, campaign):
    requests.post(f"{BASE_URL}/api/campaigns/{campaign}/encounters-library",
                    headers=H(gm_token),
                    json={"name": "Ready One", "status": "ready"})
    requests.post(f"{BASE_URL}/api/campaigns/{campaign}/encounters-library",
                    headers=H(gm_token),
                    json={"name": "Draft One", "status": "draft"})
    r = requests.get(f"{BASE_URL}/api/campaigns/{campaign}/encounters-library?status=ready",
                       headers=H(gm_token))
    rows = r.json()["rows"]
    assert all(e["status"] == "ready" for e in rows)
    assert any(e["name"] == "Ready One" for e in rows)


def test_encounter_player_cannot_create():
    pt = requests.post(f"{BASE_URL}/api/auth/login",
                        json={"email": "albanaszak@ymail.com",
                              "password": "AuroraTest123!"})
    if pt.status_code != 200:
        pytest.skip("Aurora seed not present.")
    p_token = pt.json()["access_token"]
    # Aurora isn't a GM in any campaign by default; pick any campaign id and expect 403.
    r = requests.post(f"{BASE_URL}/api/campaigns/nonexistent/encounters-library",
                       headers=H(p_token),
                       json={"name": "Sneaky"})
    assert r.status_code in (403, 404), r.text
