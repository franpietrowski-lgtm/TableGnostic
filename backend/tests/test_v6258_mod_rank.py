"""V6.25.8 — BESM enhancement / limiter rank persistence.

Validates that the new rank-aware mod shape ({name, rank, value})
round-trips through the character endpoint, and that legacy bare-string
mods still load without error (back-compat).
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
def besm_campaign(gm_token):
    payload = {"name": "V6258 mod-rank-test", "system_id": "besm-4e"}
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_attribute_with_rank_mods_round_trips(gm_token, besm_campaign):
    """A BESM attribute with rank-4 Range and rank-2 Backlash should
    survive POST → GET with the rank values intact, AND the character
    validator should not 422 on the dict shape."""
    char = {
        "campaign_id": besm_campaign,
        "name": "Mod Rank Test",
        "concept": "rank-aware modifier round-trip",
        "power_level": "Heroic",
        "total_points": 120,
        "stats": {"body": 4, "mind": 4, "soul": 4},
        "attributes": [{
            "name": "Weapon",
            "level": 3,
            "cost_per_level": 1,
            "enhancements": [{"name": "Range", "rank": 4, "value": -4}],
            "limiters":     [{"name": "Backlash", "rank": 2, "value": 2}],
        }],
        "skills": [],
        "defects": [],
        "power_packs": [],
    }
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=char)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]

    rr = requests.get(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))
    assert rr.status_code == 200, rr.text
    got = rr.json()
    a = got["attributes"][0]
    assert a["enhancements"][0]["name"] == "Range"
    assert a["enhancements"][0]["rank"] == 4
    assert a["enhancements"][0]["value"] == -4
    assert a["limiters"][0]["name"] == "Backlash"
    assert a["limiters"][0]["rank"] == 2
    assert a["limiters"][0]["value"] == 2

    requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))


def test_legacy_string_mods_still_load(gm_token, besm_campaign):
    """V6.25.7-and-earlier characters wrote bare strings — those should
    still POST without 422 so older saves keep working."""
    char = {
        "campaign_id": besm_campaign,
        "name": "Legacy Mod Char",
        "concept": "string-shape back-compat",
        "power_level": "Heroic",
        "total_points": 120,
        "stats": {"body": 4, "mind": 4, "soul": 4},
        "attributes": [{
            "name": "Weapon",
            "level": 2,
            "cost_per_level": 1,
            "enhancements": ["Range", "Range"],   # legacy duplicate stack
            "limiters":     ["Activation"],
        }],
        "skills": [],
        "defects": [],
        "power_packs": [],
    }
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=char)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]

    rr = requests.get(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))
    assert rr.status_code == 200, rr.text
    a = rr.json()["attributes"][0]
    assert a["enhancements"] == ["Range", "Range"]
    assert a["limiters"] == ["Activation"]

    requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))


def test_genesis_archive_endpoint_returns_list(gm_token, besm_campaign):
    """V6.25.8 — Genesis archive list endpoint should respond 200 with
    a list (possibly empty) for the GM."""
    r = requests.get(f"{BASE_URL}/api/campaigns/{besm_campaign}/genesis/archives",
                       headers=H(gm_token))
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
