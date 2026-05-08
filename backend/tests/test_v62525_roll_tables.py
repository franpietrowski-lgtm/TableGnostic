"""V6.25.25 (Cycle D) — Director's Console roll-table designer."""
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
                       json={"name": "V62525 roll-tables", "system_id": "besm-4e"})
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


@pytest.fixture()
def seeded_ref(gm_token, campaign):
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/reference",
                       headers=H(gm_token),
                       json={"kind": "item",
                             "name": "Vial of Sun-touched Ash",
                             "summary": "Burns even when cold."})
    return r.json()["id"]


def test_rarity_tiers_static_metadata():
    r = requests.get(f"{BASE_URL}/api/roll-tables/rarity-tiers")
    assert r.status_code == 200, r.text
    body = r.json()
    keys = {t["key"] for t in body["tiers"]}
    assert {"common", "uncommon", "rare", "very_rare", "legendary"}.issubset(keys)


def test_create_table_with_reference_entry(gm_token, campaign, seeded_ref):
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Common loot", "rarity_tier": "common",
                             "entries": [
                                 {"weight": 3, "label": "", "reference_id": seeded_ref},
                                 {"weight": 1, "label": "Coin purse", "body": "1d6 silver."},
                             ]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["min_party_tier"] == 1
    assert len(body["entries"]) == 2


def test_silent_freetext_is_rejected(gm_token, campaign):
    """An entry with NO source must 422."""
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Bad table",
                             "entries": [{"weight": 1, "label": "drift"}]})
    assert r.status_code == 422, r.text


def test_two_sources_rejected(gm_token, campaign, seeded_ref):
    """An entry with TWO sources must 422 (must pick exactly one)."""
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Conflicted",
                             "entries": [{"weight": 1, "label": "x",
                                          "reference_id": seeded_ref,
                                          "body": "also a body"}]})
    assert r.status_code == 422, r.text


def test_rarity_gate_auto_snaps_up(gm_token, campaign):
    """Min_party_tier auto-snaps to the rarity floor when GM tries to lower it."""
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Legendary loot",
                             "rarity_tier": "legendary",
                             "min_party_tier": 1,    # GM tried to lower it
                             "entries": [{"weight": 1, "label": "treasure",
                                          "body": "A solar engine."}]})
    body = r.json()
    assert body["min_party_tier"] == 9, body  # legendary floor


def test_roll_below_gate_returns_403(gm_token, campaign):
    """Rolling a legendary table at party tier 1 → 403."""
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Mythic Hoard",
                             "rarity_tier": "legendary",
                             "entries": [{"weight": 1, "label": "treasure",
                                          "body": "Crown of all winds."}]})
    tid = r.json()["id"]
    rr = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign}/roll-tables/{tid}/roll?party_tier=1",
        headers=H(gm_token))
    assert rr.status_code == 403, rr.text


def test_roll_at_gate_returns_pick(gm_token, campaign, seeded_ref):
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Common loot",
                             "rarity_tier": "common",
                             "entries": [
                                 {"weight": 1, "label": "", "reference_id": seeded_ref},
                             ]})
    tid = r.json()["id"]
    rr = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign}/roll-tables/{tid}/roll?party_tier=2",
        headers=H(gm_token))
    assert rr.status_code == 200, rr.text
    body = rr.json()
    assert body["table_id"] == tid
    assert body["result"]["source"]["kind"] == "reference"
    assert body["result"]["label"] == "Vial of Sun-touched Ash"


def test_unknown_reference_id_rejected(gm_token, campaign):
    """An entry pointing at a NON-EXISTENT reference must 422."""
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token),
                       json={"name": "Phantom",
                             "entries": [{"weight": 1, "label": "ghost",
                                          "reference_id": "does-not-exist-xx"}]})
    assert r.status_code == 422, r.text


def test_player_cannot_create_table(gm_token, campaign):
    """Non-GM users get 403."""
    rp = requests.post(f"{BASE_URL}/api/auth/login",
                        json={"email": "albanaszak@ymail.com",
                              "password": "AuroraTest123!"})
    if rp.status_code != 200:
        pytest.skip("Aurora seed not present.")
    pt = rp.json()["access_token"]
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(pt),
                       json={"name": "Sneaky", "entries": [{"weight": 1, "body": "x"}]})
    assert r.status_code == 403, r.text


def test_list_and_delete_round_trip(gm_token, campaign, seeded_ref):
    cr = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                        headers=H(gm_token),
                        json={"name": "Throwaway",
                              "entries": [{"weight": 1, "reference_id": seeded_ref}]})
    tid = cr.json()["id"]
    lr = requests.get(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                       headers=H(gm_token))
    assert any(t["id"] == tid for t in lr.json()["rows"])
    dr = requests.delete(
        f"{BASE_URL}/api/campaigns/{campaign}/roll-tables/{tid}",
        headers=H(gm_token))
    assert dr.status_code == 200 and dr.json()["deleted"] == 1
    lr2 = requests.get(f"{BASE_URL}/api/campaigns/{campaign}/roll-tables",
                        headers=H(gm_token))
    assert not any(t["id"] == tid for t in lr2.json()["rows"])
