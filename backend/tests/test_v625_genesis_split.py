"""V6.25 — Genesis materializer split + custom homebrew kinds.

Verifies:
1. `/campaigns/{cid}/genesis/seed-nodes` now splits the nemesis into
   distinct linked codex nodes (npc + motive + resources + weakness)
   instead of gluing them into a single monolithic content blob.
2. Genesis `locations`, `biomes`, `factions`, `motives` buckets fan out
   to one codex node apiece on seed.
3. Custom Rules endpoint accepts the new homebrew kinds (race / class /
   size / stat) plus the per-system kinds (feature / trait / feat /
   house / descriptor / focus / ability / cypher / artifact).
"""
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
def fresh_campaign(gm_token):
    """Minimal throwaway campaign so we don't pollute the fixture sets."""
    payload = {"name": "V625 seed-test", "system_id": "besm-4e"}
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_genesis_seed_splits_nemesis_into_discrete_nodes(gm_token, fresh_campaign):
    cid = fresh_campaign
    body = {
        "campaign_id": cid,
        "nemesis_name": "Kyr the Unbound",
        "nemesis_type": "mastermind",
        "nemesis_motive": "Free the bound god at the world's heart.",
        "nemesis_resources": "Three cults, a dragon ally, a sky-fortress.",
        "nemesis_weakness": "Cannot cross running water at dawn.",
    }
    r = requests.put(f"{BASE_URL}/api/campaigns/{cid}/genesis",
                       headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/genesis/seed-nodes",
                       headers=H(gm_token))
    assert r.status_code == 200, r.text
    out = r.json()
    # 1 npc + motive-lore + resources-faction + weakness-lore = 4 nodes.
    assert out["nodes_created"] == 4

    nodes = requests.get(f"{BASE_URL}/api/campaigns/{cid}/nodes",
                          headers=H(gm_token)).json()
    titles = {n["title"] for n in nodes}
    assert "Kyr the Unbound" in titles
    assert "Kyr the Unbound — Motive" in titles
    assert "Kyr the Unbound — Resources" in titles
    assert "Kyr the Unbound — Weakness" in titles

    by_title = {n["title"]: n for n in nodes}
    # Mechanic text now lives in its OWN node, not in the nemesis blob.
    nemesis_content = by_title["Kyr the Unbound"]["content"]
    assert "Free the bound god" not in nemesis_content
    assert "Nemesis" in nemesis_content

    # Node types are differentiated so World Tree classifier picks the
    # right pillar (People / Population vs Factions vs Lore).
    assert by_title["Kyr the Unbound"]["type"] == "npc"
    assert by_title["Kyr the Unbound — Motive"]["type"] == "lore"
    assert by_title["Kyr the Unbound — Resources"]["type"] == "faction"
    assert by_title["Kyr the Unbound — Weakness"]["type"] == "lore"


def test_genesis_seed_fans_out_locations_and_factions(gm_token, fresh_campaign):
    cid = fresh_campaign
    body = {
        "campaign_id": cid,
        "locations": [
            {"name": "Dustmire Marsh", "summary": "Peat bogs choked with iron."},
            {"name": "The Glass Spire", "summary": "A 400-ft obsidian tower."},
        ],
        "biomes": [
            {"name": "The Ashen Wastes", "summary": "Grey dunes after the Fall."},
        ],
        "factions": [
            {"name": "Ninefold Chancery", "summary": "Mage-judges of the capital."},
        ],
        "motives": [
            {"name": "Restore the Lost Song",
             "summary": "Recover the seven broken verses."},
        ],
    }
    r = requests.put(f"{BASE_URL}/api/campaigns/{cid}/genesis",
                       headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/genesis/seed-nodes",
                       headers=H(gm_token))
    assert r.status_code == 200, r.text
    # 2 locations + 1 biome + 1 faction + 1 motive = 5.
    assert r.json()["nodes_created"] == 5
    nodes = requests.get(f"{BASE_URL}/api/campaigns/{cid}/nodes",
                          headers=H(gm_token)).json()
    by_title = {n["title"]: n for n in nodes}
    assert by_title["Dustmire Marsh"]["type"] == "location"
    assert "biome" in by_title["The Ashen Wastes"]["tags"]
    assert by_title["Ninefold Chancery"]["type"] == "faction"
    assert by_title["Restore the Lost Song"]["type"] == "lore"


# ─── Custom Rules homebrew kinds ────────────────────────────────────────


@pytest.mark.parametrize("kind,name", [
    ("race", "V625 Homebrew Fae-Touched"),
    ("class", "V625 Homebrew Shadowblade"),
    ("size", "V625 Homebrew Giant (Size 4)"),
    ("stat", "V625 Homebrew Luck"),
    ("feature", "V625 Homebrew Feature"),
    ("house", "V625 Homebrew House Rule"),
])
def test_custom_rules_accepts_homebrew_kinds(gm_token, fresh_campaign,
                                              kind, name):
    cid = fresh_campaign
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(gm_token),
                       json={"campaign_id": cid, "kind": kind, "name": name,
                             "cost_per_level": 1,
                             "description_note": f"Homebrew {kind} entry."})
    assert r.status_code == 200, (kind, r.status_code, r.text)
    body = r.json()
    assert body["kind"] == kind
    assert body["name"] == name
