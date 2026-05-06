"""V6.25.3 — BESM template persistence + homebrew class progression
fallback + custom-rule picker contract.

Verifies:
1. A character with `from_template_id` on attributes / skills / defects
   round-trips through CharacterIn (those fields are now declared so
   pydantic stops stripping them).
2. `folio.applied_templates` survives the CharacterIn round-trip
   (folio is Dict[str, Any]).
3. `/characters/{cid}/class-progression` falls back to a homebrew
   class lookup via custom_attributes when the canonical library
   doesn't recognise the name. The advice / homebrew flag flips and
   the timeline row 1 surfaces the GM-authored description + comps.
4. `GET /campaigns/{cid}/custom` returns ALL the kinds the picker now
   surfaces (feat / trait / feature / race / class / focus /
   descriptor / ability / cypher / artifact / house).
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
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token),
                       json={"name": "V6253 besm-template-persist", "system_id": "besm-4e"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def _make_template(token, cid, kind, name):
    """Author a BESM-shape template with effects."""
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(token),
                       json={"campaign_id": cid, "kind": kind, "name": name,
                             "cost_per_level": 1,
                             "description_note": f"GM-authored {kind}.",
                             "effects": {
                                 "stat_adjustments": {"body": 1, "mind": 0, "soul": 0},
                                 "components": [
                                     {"kind": "attribute", "name": "Tough",
                                      "cost_per_level": 1, "level": 2},
                                     {"kind": "skill", "name": "Athletics",
                                      "cost_per_level": 1, "level": 1},
                                     {"kind": "defect", "name": "Marked",
                                      "points_per_rank": 1, "rank": 1},
                                 ],
                                 "total_cp": 2,
                             }})
    assert r.status_code == 200, r.text
    return r.json()


def test_character_round_trip_persists_template_provenance(gm_token, besm_campaign):
    """Build a character with template-tagged rows + folio.applied_templates
    and confirm the backend preserves both."""
    cid = besm_campaign
    tpl = _make_template(gm_token, cid, "race", "V6253 Half-Stoneborn")
    payload = {
        "campaign_id": cid,
        "name": "V6253 Nyaulis",
        "concept": "Stoneborn warden.",
        "power_level": "Heroic",
        "total_points": 120,
        "stats": {"body": 5, "mind": 4, "soul": 4},
        "attributes": [
            {"name": "Tough", "level": 2, "cost_per_level": 1,
             "from_template_id": tpl["id"]},
        ],
        "skills": [
            {"group": "Athletics", "level": 1, "cost_per_level": 1,
             "components": [], "from_template_id": tpl["id"]},
        ],
        "defects": [
            {"name": "Marked", "rank": 1, "points_per_rank": 1,
             "category": "Template", "from_template_id": tpl["id"]},
        ],
        "folio": {"applied_templates": [
            {"id": tpl["id"], "name": tpl["name"], "kind": "race",
             "total_cp": 2,
             "stat_adjustments": {"body": 1, "mind": 0, "soul": 0},
             "description": tpl["description_note"]},
        ]},
    }
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    char = r.json()
    char_id = char["id"]
    try:
        # Per-row provenance survives.
        assert char["attributes"][0]["from_template_id"] == tpl["id"]
        assert char["skills"][0]["from_template_id"] == tpl["id"]
        assert char["defects"][0]["from_template_id"] == tpl["id"]
        # folio.applied_templates survives.
        applied = (char.get("folio") or {}).get("applied_templates") or []
        assert len(applied) == 1
        assert applied[0]["name"] == tpl["name"]
        assert applied[0]["stat_adjustments"]["body"] == 1
    finally:
        requests.delete(f"{BASE_URL}/api/characters/{char_id}",
                         headers=H(gm_token))


def test_class_progression_falls_back_to_homebrew_class(gm_token, besm_campaign):
    """A character whose folio.dnd_state.class names a homebrew class
    on the campaign should get a `known: True, homebrew: True` response
    from /class-progression with description + total CP surfaced."""
    cid = besm_campaign
    tpl = _make_template(gm_token, cid, "class", "V6253 Stormcaller")
    # Build a character that 'is' the homebrew class.
    payload = {
        "campaign_id": cid,
        "name": "V6253 Test Stormcaller",
        "stats": {"body": 4, "mind": 5, "soul": 4},
        "folio": {"dnd_state": {"class": "V6253 Stormcaller", "level": 1}},
    }
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    char_id = r.json()["id"]
    try:
        prog = requests.get(f"{BASE_URL}/api/characters/{char_id}/class-progression",
                              headers=H(gm_token))
        assert prog.status_code == 200, prog.text
        out = prog.json()
        assert out["class"] == "V6253 Stormcaller"
        assert out["known"] is True
        assert out["homebrew"] is True
        # Timeline level 1 features include the description note + comp names.
        feats = out["timeline"][0]["features"]
        assert any("GM-authored class" in f for f in feats)
        assert any("Tough" in f for f in feats)
        # Advice line points to the homebrew class' name + CP.
        assert "V6253 Stormcaller" in out["advice"]
        assert "CP" in out["advice"]
    finally:
        requests.delete(f"{BASE_URL}/api/characters/{char_id}",
                         headers=H(gm_token))


def test_class_progression_unknown_advice_no_atelier_reference(gm_token, besm_campaign):
    """Regression — the V6.19 advice text used to point users to a
    removed 'Atelier · References / kind: custom_class' destination.
    Now it should point to the Custom Rules tab."""
    cid = besm_campaign
    payload = {
        "campaign_id": cid,
        "name": "V6253 Unknown class",
        "stats": {"body": 4, "mind": 4, "soul": 4},
        "folio": {"dnd_state": {"class": "V6253 NoSuchClass", "level": 1}},
    }
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    char_id = r.json()["id"]
    try:
        out = requests.get(f"{BASE_URL}/api/characters/{char_id}/class-progression",
                             headers=H(gm_token)).json()
        assert out["known"] is False
        # New advice mentions Custom Rules; old advice mentioned Atelier
        # · References — that string MUST NOT appear anymore.
        assert "Custom Rules" in out["advice"]
        assert "Atelier" not in out["advice"]
    finally:
        requests.delete(f"{BASE_URL}/api/characters/{char_id}",
                         headers=H(gm_token))


@pytest.mark.parametrize("kind", [
    "feat", "trait", "feature", "race", "class",
    "focus", "descriptor", "ability", "cypher", "artifact", "house",
])
def test_custom_rule_kinds_round_trip_for_picker(gm_token, besm_campaign, kind):
    """Every kind the ReferencePicker surfaces in V6.25.3 must round-
    trip through POST /custom + GET /custom so the picker can consume
    it across systems."""
    cid = besm_campaign
    name = f"V6253 picker-{kind}"
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(gm_token),
                       json={"campaign_id": cid, "kind": kind, "name": name,
                             "cost_per_level": 1,
                             "description_note": f"GM {kind} for picker test."})
    assert r.status_code == 200, (kind, r.text)
    rows = requests.get(f"{BASE_URL}/api/campaigns/{cid}/custom",
                         headers=H(gm_token)).json()
    match = next((x for x in rows if x["name"] == name), None)
    assert match is not None
    assert match["kind"] == kind
