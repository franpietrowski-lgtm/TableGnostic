"""V6.25.4 — Homebrew effects integration round-trip.

Verifies the persistence contract for the ASI / Size effects schema
that the frontend D&D builder & sheet auto-apply, and that the BESM
back-fill flow can save a character with extra `from_template_id` tags
+ a `folio.applied_templates` flagged backfilled=True.
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
def dnd_campaign(gm_token):
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token),
                       json={"name": "V6254 dnd-asi-test", "system_id": "dnd-5e"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_dnd_homebrew_race_with_asi_round_trip(gm_token, dnd_campaign):
    """A homebrew D&D race carrying `effects.asi` round-trips so the
    builder + sheet can both look it up and auto-apply ASI bonuses."""
    cid = dnd_campaign
    race_payload = {
        "campaign_id": cid, "kind": "race",
        "name": "V6254 Sunbound Wisp",
        "cost_per_level": 1,
        "description_note": "Translucent fae-kin.",
        "effects": {
            "asi": {"Charisma": 2, "Constitution": 1},
            "size": "Small", "speed": 25,
            "traits": ["Luminescent", "Vulnerable to Iron"],
        },
    }
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(gm_token), json=race_payload)
    assert r.status_code == 200, r.text
    rows = requests.get(f"{BASE_URL}/api/campaigns/{cid}/custom",
                         headers=H(gm_token)).json()
    match = next((x for x in rows
                   if x["kind"] == "race"
                   and x["name"].lower() == "v6254 sunbound wisp"), None)
    assert match is not None
    assert match["effects"]["asi"]["Charisma"] == 2
    assert match["effects"]["asi"]["Constitution"] == 1
    assert match["effects"]["size"] == "Small"
    assert match["effects"]["speed"] == 25
    assert "Luminescent" in match["effects"]["traits"]


def test_besm_size_homebrew_round_trip(gm_token, dnd_campaign):
    """Custom Rules entries of kind=size persist with description so the
    BESM character builder's size dropdown can surface them as a
    Campaign Homebrew optgroup option."""
    cid = dnd_campaign
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(gm_token),
                       json={"campaign_id": cid, "kind": "size",
                             "name": "V6254 Giant (Size 4)",
                             "cost_per_level": 1,
                             "description_note": "9 ft tall · +2 reach · -2 stealth"})
    assert r.status_code == 200, r.text
    rows = requests.get(f"{BASE_URL}/api/campaigns/{cid}/custom",
                         headers=H(gm_token)).json()
    sizes = [x for x in rows if x["kind"] == "size"]
    assert any(s["name"] == "V6254 Giant (Size 4)" for s in sizes)
    homebrew = next(s for s in sizes if s["name"] == "V6254 Giant (Size 4)")
    assert "9 ft tall" in homebrew["description_note"]


def test_character_with_size_string_round_trips(gm_token, dnd_campaign):
    """Size on the character is a free string so a homebrew size name
    saves cleanly even though it's not in the canonical BESM table."""
    cid = dnd_campaign
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token),
                       json={"campaign_id": cid,
                             "name": "V6254 Big Friend",
                             "size": "V6254 Giant (Size 4)",
                             "stats": {"body": 6, "mind": 4, "soul": 4}})
    assert r.status_code == 200, r.text
    cid2 = r.json()["id"]
    try:
        ch = requests.get(f"{BASE_URL}/api/characters/{cid2}",
                            headers=H(gm_token)).json()
        assert ch["size"] == "V6254 Giant (Size 4)"
    finally:
        requests.delete(f"{BASE_URL}/api/characters/{cid2}",
                         headers=H(gm_token))


def test_backfilled_template_marker_persists(gm_token, dnd_campaign):
    """The back-fill flow stores `backfilled: True` + `tagged_rows: N`
    on each entry inside folio.applied_templates so the sheet can show
    a "back-filled" badge later."""
    cid = dnd_campaign
    # Create a template the back-fill should match against.
    tpl = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                          headers=H(gm_token),
                          json={"campaign_id": cid, "kind": "class",
                                "name": "V6254 Stoneborn",
                                "cost_per_level": 1,
                                "effects": {"stat_adjustments": {"body": 2},
                                             "components": [
                                                 {"kind": "attribute",
                                                  "name": "Tough",
                                                  "cost_per_level": 1,
                                                  "level": 2}],
                                             "total_cp": 4}}).json()
    payload = {
        "campaign_id": cid,
        "name": "V6254 Backfilled Char",
        "stats": {"body": 5, "mind": 4, "soul": 4},
        # Pre-existing attribute that matches the template's component.
        "attributes": [{"name": "Tough", "level": 2, "cost_per_level": 1,
                         "from_template_id": tpl["id"]}],
        "folio": {"applied_templates": [
            {"id": tpl["id"], "name": tpl["name"], "kind": "class",
             "total_cp": 4, "stat_adjustments": {"body": 2},
             "description": "", "backfilled": True, "tagged_rows": 1},
        ]},
    }
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    ch_id = r.json()["id"]
    try:
        ch = requests.get(f"{BASE_URL}/api/characters/{ch_id}",
                            headers=H(gm_token)).json()
        applied = (ch.get("folio") or {}).get("applied_templates") or []
        assert len(applied) == 1
        assert applied[0]["backfilled"] is True
        assert applied[0]["tagged_rows"] == 1
    finally:
        requests.delete(f"{BASE_URL}/api/characters/{ch_id}",
                         headers=H(gm_token))
