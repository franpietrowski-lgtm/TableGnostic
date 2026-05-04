"""V6.25 — Universal Power Bundle Architecture.

Verifies:
1. Custom Attributes can host bundle-style components in `fields.components`
   with a live CP estimate from `/api/reference/estimate-bundle-cost`.
2. Custom Attributes/Skills accept a `size_modifier` field.
3. Custom Power Bundles created via the Reference Editor round-trip via
   `GET /api/campaigns/{cid}/reference` and are picked up by the
   character sheet's reference picker (same endpoint it calls).
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


@pytest.fixture(scope="module")
def anime_campaign(gm_token):
    cs = requests.get(f"{BASE_URL}/api/campaigns", headers=H(gm_token)).json()
    anime = next((c for c in cs if c["system_id"] == "anime-5e"
                   and c.get("is_gm")), None)
    if not anime:
        pytest.skip("No Anime 5E GM-owned campaign in this environment.")
    return anime["id"]


def test_estimate_bundle_cost_attribute_with_limiter(gm_token):
    """Attribute + Limiter nets out just the attribute cost; limiter is
    an effective-level modifier, not a direct CP deduction."""
    body = {"components": [
        {"kind": "attribute", "name": "Weapon",
         "cost_per_level": 2, "level": 3},
        {"kind": "limiter", "name": "Concentration"},
    ]}
    r = requests.post(f"{BASE_URL}/api/reference/estimate-bundle-cost",
                       headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["total_cost"] == 6  # 2 × 3
    assert out["component_count"] == 2


def test_estimate_bundle_cost_defect_refund(gm_token):
    """A Lesser Defect (1 pt/rank × 3) refunds 3 CP."""
    body = {"components": [
        {"kind": "defect", "name": "Marked",
         "points_per_rank": 1, "rank": 3},
    ]}
    r = requests.post(f"{BASE_URL}/api/reference/estimate-bundle-cost",
                       headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    assert r.json()["total_cost"] == -3


def test_custom_attribute_with_attached_modifiers(gm_token, anime_campaign):
    """A Custom Attribute reference stores components + size_modifier
    so the sheet picker can render attached modifiers."""
    payload = {
        "kind": "attribute",
        "name": "V625 Sealed Flame",
        "summary": "Limited-use elemental burst attribute.",
        "fields": {
            "cost_per_level": 2,
            "description": "Fire pulse tied to an anchored focus.",
            "size_modifier": 1,
            "size_note": "Reach 10 ft cone",
            "components": [
                {"kind": "attribute", "name": "Weapon (Fire)",
                 "cost_per_level": 2, "level": 2},
                {"kind": "limiter", "name": "Charges: 3/scene"},
                {"kind": "defect", "name": "Marked (Sigil)",
                 "points_per_rank": 1, "rank": 1},
            ],
        },
    }
    r = requests.post(f"{BASE_URL}/api/campaigns/{anime_campaign}/reference",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    rid = created["id"]
    try:
        assert created["fields"]["size_modifier"] == 1
        assert created["fields"]["size_note"] == "Reach 10 ft cone"
        assert len(created["fields"]["components"]) == 3
        # Round-trip via GET → confirm the picker URL returns it.
        r2 = requests.get(f"{BASE_URL}/api/campaigns/{anime_campaign}/reference",
                           headers=H(gm_token))
        assert r2.status_code == 200
        rows = r2.json()
        match = next((x for x in rows if x["id"] == rid), None)
        assert match is not None
        assert match["fields"]["size_modifier"] == 1
        assert match["kind"] == "attribute"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{anime_campaign}/reference/{rid}",
                         headers=H(gm_token))


def test_custom_power_bundle_visible_to_spell_picker(gm_token, anime_campaign):
    """A custom power_bundle survives the GET the spell picker calls.
    This is the contract the ReferencePicker relies on to surface
    custom Anime 5E spell-mimic bundles."""
    payload = {
        "kind": "power_bundle",
        "name": "V625 Starfire Volley",
        "summary": "A pulse of starfire arrows — 3/day.",
        "fields": {
            "description": "Twin arrows of starlight, 3d8 radiant.",
            "invocation": "per-day",
            "charges_max": 3,
            "energy_cost": 0,
            "cooldown": "long rest",
            "source_spell_level": 3,
            "cost": 9,
            "components": [
                {"kind": "attribute", "name": "Weapon: Starfire (3d8 radiant)",
                 "cost_per_level": 1, "level": 9},
            ],
        },
    }
    r = requests.post(f"{BASE_URL}/api/campaigns/{anime_campaign}/reference",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    try:
        r2 = requests.get(f"{BASE_URL}/api/campaigns/{anime_campaign}/reference",
                           headers=H(gm_token))
        rows = r2.json()
        match = next((x for x in rows if x["id"] == rid), None)
        assert match is not None
        assert match["kind"] == "power_bundle"
        assert match["fields"]["source_spell_level"] == 3
        assert match["fields"]["charges_max"] == 3
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{anime_campaign}/reference/{rid}",
                         headers=H(gm_token))
