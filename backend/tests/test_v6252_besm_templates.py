"""V6.25.2 — BESM Race/Class templates with numeric effects.

Verifies:
1. `CustomAttributeIn` accepts an `effects` object and round-trips it.
2. A BESM race template with stat_adjustments + components + total_cp
   survives the create → list → read flow so the character builder's
   template picker can consume it.
3. A BESM class template with a defect-heavy components block round-
   trips (per the Werewolf / Martial Artist sample cards the user
   attached).
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
    payload = {"name": "V6252 besm-template-test", "system_id": "besm-4e"}
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_besm_race_template_round_trip(gm_token, besm_campaign):
    """Half-Dragon template from the user's attachment:
       Body +2 (4pts) + Immunity(Heat) L5 (15pts) + Immutable L1 (1pt)
       + Flight L2 (6pts) + Superstrength L1 (4pts) + Tough L1 (1pt)
       + Weapon: Fire Breath L2 (4pts) = 35 CP total."""
    cid = besm_campaign
    payload = {
        "campaign_id": cid,
        "kind": "race",
        "name": "V6252 Half-Dragon",
        "cost_per_level": 1,
        "description_note": "Born of storm and flame.",
        "effects": {
            "stat_adjustments": {"body": 2, "mind": 0, "soul": 0},
            "components": [
                {"kind": "attribute", "name": "Immunity (Heat)",
                 "cost_per_level": 3, "level": 5},
                {"kind": "attribute", "name": "Immutable",
                 "cost_per_level": 1, "level": 1},
                {"kind": "attribute", "name": "Flight",
                 "cost_per_level": 3, "level": 2},
                {"kind": "attribute", "name": "Superstrength",
                 "cost_per_level": 4, "level": 1},
                {"kind": "attribute", "name": "Tough",
                 "cost_per_level": 1, "level": 1},
                {"kind": "attribute", "name": "Weapon: Fire Breath",
                 "cost_per_level": 2, "level": 2,
                 "note": "Continuing -1; Range -1; Deplete +2"},
            ],
            "total_cp": 35,
        },
    }
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["kind"] == "race"
    assert created["effects"]["stat_adjustments"]["body"] == 2
    assert created["effects"]["total_cp"] == 35
    assert len(created["effects"]["components"]) == 6
    # Surface via the list endpoint the builder picker calls.
    rows = requests.get(f"{BASE_URL}/api/campaigns/{cid}/custom",
                         headers=H(gm_token)).json()
    match = next((x for x in rows if x["name"] == "V6252 Half-Dragon"), None)
    assert match is not None
    assert match["effects"]["total_cp"] == 35


def test_besm_class_template_with_defects(gm_token, besm_campaign):
    """Werewolf Base Form template — stat Body +2 (4) plus attribute
    mix plus defects netting 5 CP total."""
    cid = besm_campaign
    payload = {
        "campaign_id": cid,
        "kind": "class",
        "name": "V6252 Werewolf (Base Form)",
        "cost_per_level": 1,
        "description_note": "Lycanthropic base form.",
        "effects": {
            "stat_adjustments": {"body": 2, "mind": 0, "soul": 0},
            "components": [
                {"kind": "attribute", "name": "Alternate Form (Wolf)",
                 "cost_per_level": 4, "level": 1},
                {"kind": "attribute", "name": "Connected (Lycanthrope)",
                 "cost_per_level": 1, "level": 1},
                {"kind": "attribute", "name": "Heightened Awareness",
                 "cost_per_level": 1, "level": 2},
                {"kind": "attribute", "name": "Regeneration",
                 "cost_per_level": 5, "level": 1},
                {"kind": "attribute", "name": "Sixth Sense (Blood)",
                 "cost_per_level": 1, "level": 1},
                {"kind": "defect", "name": "Cursed (Werewolf)",
                 "points_per_rank": 2, "rank": 2},
                {"kind": "defect", "name": "Involuntary Change (Full Moon)",
                 "points_per_rank": 1, "rank": 1},
                {"kind": "defect", "name": "Nightmares",
                 "points_per_rank": 1, "rank": 1},
                {"kind": "defect", "name": "Skeleton in the Closet (Werewolf)",
                 "points_per_rank": 2, "rank": 3},
            ],
            "total_cp": 5,
        },
    }
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    defects = [c for c in created["effects"]["components"] if c["kind"] == "defect"]
    assert len(defects) == 4
    # Defect fields preserved verbatim (points_per_rank stored positive;
    # frontend handles sign flip).
    cursed = next(d for d in defects if d["name"].startswith("Cursed"))
    assert cursed["rank"] == 2
    assert cursed["points_per_rank"] == 2


def test_dnd_homebrew_race_accepts_asi_effects(gm_token, besm_campaign):
    """D&D-style race with ASI effects object — narrative-only for now
    but the schema must preserve it so a future follow-up can auto-
    apply ability score increases."""
    cid = besm_campaign
    payload = {
        "campaign_id": cid,
        "kind": "race",
        "name": "V6252 Sunbound Wisp",
        "cost_per_level": 1,
        "effects": {
            "asi": {"Charisma": 2, "Constitution": 1},
            "size": "Small",
            "speed": 25,
            "traits": ["Luminescent", "Vulnerable to Iron"],
        },
    }
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["effects"]["asi"]["Charisma"] == 2
    assert created["effects"]["size"] == "Small"
    assert "Luminescent" in created["effects"]["traits"]
