"""V6.25.11 — Canonical BESM 4E weapon mods + Item half-cost + materials."""
from __future__ import annotations
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_canonical_weapon_enhancements_p135(gm_token):
    """All 35 canonical p.135 Weapon Enhancements present with correct rank ranges."""
    r = requests.get(f"{BASE_URL}/api/besm/reference", headers=H(gm_token))
    assert r.status_code == 200
    pool = r.json()["weapon_enhancements"]
    names = {e["name"] for e in pool}

    # Every canonical p.135 Enhancement must be exposed.
    canonical = {
        "Accurate", "Aura", "Autofire", "Blight", "Contact", "Contagious",
        "Continuing", "Drain", "Enervation", "Flare", "Flexible", "Helper",
        "Homing", "Incapacitating", "Inconspicuous", "Incurable", "Indirect",
        "Insidious", "Irritant", "Linked", "Multidimensional", "Muscle",
        "Penetrating", "Piercing", "Psychic", "Quake", "Reach", "Selective",
        "Spreading", "Stun", "Tangle", "Targetted", "Trap", "Unique", "Vampiric",
    }
    missing = canonical - names
    assert not missing, f"Missing p.135 Weapon Enhancements: {missing}"

    # Spot-check a non-trivial entry: Incapacitating "2 or 4".
    incap = next(e for e in pool if e["name"] == "Incapacitating")
    assert incap["rank_range"] == "2 or 4"
    assert incap["page"] == 135
    assert incap["source"]["book"] == "BESM 4E"

    # Open-ended ranks carry None upper bound.
    pen = next(e for e in pool if e["name"] == "Penetrating")
    assert pen["rank_range"] == [1, None]


def test_canonical_weapon_limiters_p142(gm_token):
    """All 13 canonical p.142 Weapon Limiters present."""
    r = requests.get(f"{BASE_URL}/api/besm/reference", headers=H(gm_token))
    pool = r.json()["weapon_limiters"]
    names = {e["name"] for e in pool}
    canonical = {
        "Alt-Munition", "Ammo", "Backblast", "Exclusive", "Fieldless",
        "Hands", "Inaccurate", "Ingest", "Non-Penetrating", "Stoppable",
        "Toxic", "Unique", "Unreliable",
    }
    missing = canonical - names
    assert not missing, f"Missing p.142 Weapon Limiters: {missing}"
    # Alt-Munition has the special-string rank descriptor.
    am = next(e for e in pool if e["name"] == "Alt-Munition")
    assert am["rank_range"] == "special"


@pytest.fixture()
def item_campaign(gm_token):
    cp = requests.post(f"{BASE_URL}/api/campaigns",
                        headers=H(gm_token),
                        json={"name": "V62511 Item HalfCost", "system_id": "besm-4e"})
    cid = cp.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_item_attribute_pays_half_cost(gm_token, item_campaign):
    """An Item Attribute at level 4 / 1 pt-per-level should cost
    `ceil(4/2) = 2` points (BESM 4E p.135 Item half-cost rule), NOT 4."""
    cid = item_campaign
    char = {
        "campaign_id": cid,
        "name": "Half-Cost Test", "concept": "item-rule sanity",
        "power_level": "Heroic", "total_points": 120,
        "stats": {"body": 4, "mind": 4, "soul": 4},
        "attributes": [{"name": "Item", "level": 4, "cost_per_level": 1,
                         "enhancements": [], "limiters": []}],
        "skills": [], "defects": [], "power_packs": [],
    }
    r = requests.post(f"{BASE_URL}/api/characters", headers=H(gm_token), json=char)
    assert r.status_code == 200, r.text
    cid_ch = r.json()["id"]

    # Pull the validator output through the audit endpoint.
    rv = requests.get(f"{BASE_URL}/api/characters/{cid_ch}/validate",
                       headers=H(gm_token))
    assert rv.status_code == 200, rv.text
    body = rv.json()
    item_line = next(line for line in body["breakdown"]["lines"]
                       if line["kind"] == "attribute" and line["name"] == "Item")
    assert item_line["is_item_container"] is True
    assert item_line["item_raw_cost"] == 4
    # ceil(4/2) = 2 — the listed cost on the audit / sheet.
    assert item_line["points"] == 2, f"Item half-cost wrong: {item_line}"

    requests.delete(f"{BASE_URL}/api/characters/{cid_ch}", headers=H(gm_token))


def test_item_with_contents_uses_assault_mecha_pattern(gm_token, item_campaign):
    """Assault Mecha (BESM 4E p.219) — internal sum 130 → 65 Item.

    We replicate a slimmed version: Item Attribute carrying a single
    sub-attribute with raw cost 8. Outer Item itself is level 4 / 1pt
    so its self-cost is 4. Raw = 4 + 8 = 12. ceil(12/2) = 6."""
    cid = item_campaign
    char = {
        "campaign_id": cid,
        "name": "Mini Mecha", "concept": "p.219 pattern",
        "power_level": "Adventurous", "total_points": 200,
        "stats": {"body": 5, "mind": 5, "soul": 5},
        "attributes": [{
            "name": "Item", "level": 4, "cost_per_level": 1,
            "item_contents": [
                {"name": "Armour", "level": 4, "cost_per_level": 2},
            ],
        }],
        "skills": [], "defects": [], "power_packs": [],
    }
    r = requests.post(f"{BASE_URL}/api/characters", headers=H(gm_token), json=char)
    assert r.status_code == 200, r.text
    cid_ch = r.json()["id"]

    rv = requests.get(f"{BASE_URL}/api/characters/{cid_ch}/validate",
                       headers=H(gm_token))
    body = rv.json()
    item_line = next(line for line in body["breakdown"]["lines"]
                       if line["kind"] == "attribute" and line["name"] == "Item")
    # raw = 4 (Item self) + 8 (Armour 4×2) = 12 → ceil(12/2) = 6
    assert item_line["item_raw_cost"] == 12
    assert item_line["points"] == 6

    # The sub-attribute appears as its own line (informational only).
    contents = [line for line in body["breakdown"]["lines"]
                  if line["kind"] == "attribute_contents"]
    assert any(c["name"] == "Armour" and c["points"] == 8 for c in contents)

    requests.delete(f"{BASE_URL}/api/characters/{cid_ch}", headers=H(gm_token))


def test_material_byproduct_craft_output_codex_kinds(gm_token, item_campaign):
    """V6.25.11 — codex accepts the new `material`, `byproduct`, and
    `craft_output` node_kinds for the artisan / materials pipeline."""
    cid = item_campaign
    samples = [
        ("material",     "Powdered Mithral",      "Refined ore dust — magic-conductive."),
        ("byproduct",    "Pickling Brine (mundane)", "Salvage from prior refining cycles."),
        ("craft_output", "Charming Scent Flask",  "Throwing flask — alchemy recipe output."),
    ]
    created = []
    for kind, name, summary in samples:
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                            headers=H(gm_token),
                            json={"name": name, "node_kind": kind, "summary": summary})
        assert r.status_code in (200, 201), f"{kind}: {r.text}"
        created.append(r.json())
    assert len(created) == 3

    rl = requests.get(f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                        headers=H(gm_token))
    assert rl.status_code == 200
    seen_kinds = {n.get("node_kind") or n.get("type") for n in rl.json()}
    for k in ("material", "byproduct", "craft_output"):
        assert k in seen_kinds, f"{k} missing from codex"
