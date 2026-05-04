"""V6.25 follow-up — Campaign description inline edit + homebrew
race/class wiring.

Verifies:
1. `PUT /campaigns/{cid}` accepts a description patch and round-trips
   it (including markdown-lite syntax preserved as raw text).
2. Homebrew `race` and `class` custom_attributes appear in the
   `/campaigns/{cid}/custom` response so the builder's race/class
   dropdowns can merge them with SRD entries.
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
    payload = {"name": "V625 desc-test", "system_id": "dnd-5e"}
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_campaign_description_round_trip_with_markdown(gm_token, fresh_campaign):
    """The markdown-lite renderer is a frontend concern but the
    backend MUST preserve paragraph breaks + `**bold**` markers."""
    cid = fresh_campaign
    camp = requests.get(f"{BASE_URL}/api/campaigns/{cid}",
                         headers=H(gm_token)).json()
    new_desc = ("A **haunted** sea-town where the tide speaks names.\n\n"
                "*Run weekly. Safety tools on.*\n\n"
                "Reach out via the Hall of Whispers.")
    body = {**camp, "description": new_desc}
    # Strip server-managed / non-writable fields.
    for k in ("id", "gm_id", "gm_name", "member_ids", "invite_token",
              "created_at", "updated_at", "is_gm", "current_user_id"):
        body.pop(k, None)
    r = requests.put(f"{BASE_URL}/api/campaigns/{cid}",
                      headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    round_tripped = requests.get(f"{BASE_URL}/api/campaigns/{cid}",
                                   headers=H(gm_token)).json()
    assert round_tripped["description"] == new_desc
    # Paragraph breaks (double newline) survive.
    assert "\n\n" in round_tripped["description"]
    # Markdown-lite markers survive (frontend renders them).
    assert "**haunted**" in round_tripped["description"]


def test_homebrew_race_class_surface_via_custom_endpoint(gm_token, fresh_campaign):
    """The builder dropdowns read `/campaigns/{cid}/custom` and filter
    by kind. This test verifies race + class homebrew entries survive
    the round-trip and return the exact name + kind the frontend
    filter expects."""
    cid = fresh_campaign
    for kind, name, note in (
        ("race", "V625 Sunbound Wisp",
         "Translucent fae-kin. +2 CHA, light sensitivity."),
        ("class", "V625 Pact-Warden",
         "Half-caster melee. Pact-blade bond at L3."),
    ):
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                           headers=H(gm_token),
                           json={"campaign_id": cid, "kind": kind,
                                 "name": name, "cost_per_level": 1,
                                 "description_note": note})
        assert r.status_code == 200, (kind, r.text)
    rows = requests.get(f"{BASE_URL}/api/campaigns/{cid}/custom",
                         headers=H(gm_token)).json()
    races = [r for r in rows if r["kind"] == "race"]
    classes = [r for r in rows if r["kind"] == "class"]
    assert any(r["name"] == "V625 Sunbound Wisp" for r in races)
    assert any(r["name"] == "V625 Pact-Warden" for r in classes)
    # Description notes propagate so the builder's homebrew card
    # can render them.
    wisp = next(r for r in races if r["name"] == "V625 Sunbound Wisp")
    assert "fae-kin" in wisp["description_note"]
