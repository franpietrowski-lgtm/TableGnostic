"""V6.25.10 — Apocophea AutoMakers Bag end-to-end demo + acceptance test.

This test builds the Apocophea AutoMakers Bag exactly as the user
specified, using the new BESM Extras item-specific Enhancement +
Limiter pool, then assigns the item to a character ("Eli") and
verifies the macro builder grammar resolves a roll formula that
references the bag's effective Level.

The bag specification (paraphrased from the user's request, kept
mechanical-only — no rulebook prose reproduced):

  Apocophea AutoMakers Bag
  ── Item attribute, Level 4, 1 pt/level (BESM Item base)
     ──   Enhancements
            • Auto-Refining ×2 (BESM Extras p.44)  — refines closed-bag
              contents into useful substances on its own schedule.
            • Compact ×1   (p.42) — the bag is conveniently small.
     ──   Limiters
            • Unwarned Eject ×1 (p.48) — auto-functioning items expel
              by-products without notifying the wielder. The user must
              manually search for ejected rubbish.
            • No Selection ×1   (p.49) — the bag picks WHICH substance
              gets refined; the wielder cannot command it.
            • Tied to Owner ×1  (p.48) — only Eli (an Apocophea) can
              activate the refining process.
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
def besm_eli(gm_token):
    """Spin up a BESM 4E campaign + 'Eli' character to receive the bag."""
    cp = requests.post(f"{BASE_URL}/api/campaigns",
                        headers=H(gm_token),
                        json={"name": "V62510 Apocophea Demo",
                              "system_id": "besm-4e"})
    assert cp.status_code == 200, cp.text
    cid = cp.json()["id"]

    eli = {
        "campaign_id": cid,
        "name": "Eli (Apocophea)",
        "concept": "Apocophea materials-refiner with throwing flask staff",
        "power_level": "Heroic",
        "total_points": 120,
        "stats": {"body": 5, "mind": 7, "soul": 6},
        "attributes": [],
        "skills": [{"group": "Artisan", "level": 4, "cost_per_level": 1}],
        "defects": [],
        "power_packs": [],
    }
    rch = requests.post(f"{BASE_URL}/api/characters",
                         headers=H(gm_token), json=eli)
    assert rch.status_code == 200, rch.text
    yield (cid, rch.json()["id"])
    requests.delete(f"{BASE_URL}/api/characters/{rch.json()['id']}", headers=H(gm_token))
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_besm_reference_exposes_item_specific_pools(gm_token):
    """V6.25.10 — the BESM reference endpoint should expose four new
    pools so the Reference Editor + Custom Rules forms can pick from them
    when building Item / Weapon Attributes."""
    r = requests.get(f"{BASE_URL}/api/besm/reference", headers=H(gm_token))
    assert r.status_code == 200, r.text
    body = r.json()

    # Item / Weapon mod pools all present.
    assert len(body.get("weapon_enhancements", [])) >= 8
    assert len(body.get("weapon_limiters", []))     >= 6
    assert len(body.get("item_enhancements", []))   >= 6
    assert len(body.get("item_limiters", []))       >= 6

    # The key Apocophea-bag mods are present.
    item_enh_names = [e["name"] for e in body["item_enhancements"]]
    item_lim_names = [l["name"] for l in body["item_limiters"]]
    assert "Auto-Refining" in item_enh_names
    assert "Compact"       in item_enh_names
    assert "Unwarned Eject" in item_lim_names
    assert "No Selection"   in item_lim_names
    assert "Tied to Owner"  in item_lim_names

    # Source book is "BESM Extras" + page reference is set.
    auto_refining = next(e for e in body["item_enhancements"]
                          if e["name"] == "Auto-Refining")
    assert auto_refining["source"]["book"] == "BESM Extras"
    assert auto_refining["source"]["page"] >= 40
    # And the descriptive note (not rulebook prose, but explanatory).
    assert auto_refining.get("blurb")


def test_apocophea_bag_assigns_to_eli_and_macro_resolves(gm_token, besm_eli):
    """The bag round-trips through the character endpoint with rank-aware
    item-mods, and a `{attr:Apocophea AutoMakers Bag}` token in a macro
    formula resolves to the bag's effective Level."""
    cid, eli_id = besm_eli

    # Compose the bag and assign it to Eli.
    bag_attr = {
        "name": "Item",
        "display_name": "Apocophea AutoMakers Bag",
        "level": 4,
        "cost_per_level": 1,
        "page": None,  # custom item — no core attribute page
        "note": ("A hand-me-down satchel that auto-refines closed contents "
                 "into powders / extracts / cleaned raw materials. Ejects "
                 "rubbish unannounced; the bag chooses what gets made."),
        "enhancements": [
            {"name": "Auto-Refining", "rank": 2, "value": -2},
            {"name": "Compact",       "rank": 1, "value": -1},
        ],
        "limiters": [
            {"name": "Unwarned Eject", "rank": 1, "value": 1},
            {"name": "No Selection",   "rank": 1, "value": 1},
            {"name": "Tied to Owner",  "rank": 1, "value": 1},
        ],
        "defects": [],
    }

    # Read-modify-write Eli's attributes list.
    rd = requests.get(f"{BASE_URL}/api/characters/{eli_id}", headers=H(gm_token))
    assert rd.status_code == 200, rd.text
    eli = rd.json()
    eli["attributes"] = [bag_attr]
    eli["campaign_id"] = cid
    rp = requests.put(f"{BASE_URL}/api/characters/{eli_id}",
                       headers=H(gm_token), json=eli)
    assert rp.status_code == 200, rp.text
    saved = rp.json()
    bag = next(a for a in saved["attributes"] if a.get("display_name") == "Apocophea AutoMakers Bag")
    assert bag["level"] == 4
    assert bag["enhancements"][0]["name"] == "Auto-Refining"
    assert bag["enhancements"][0]["rank"] == 2
    assert bag["limiters"][0]["name"] == "Unwarned Eject"

    # Effective Level = 4 (base) + 3 (Σ limiter ranks 1+1+1) − 3 (Σ enh ranks 2+1) = 4.
    # Author a macro that references {attr:Item} (the underlying name)
    # and verify the resolver substitutes the right effective level.
    rm = requests.post(f"{BASE_URL}/api/campaigns/{cid}/macros",
                        headers=H(gm_token),
                        json={"name": "bagrefine", "label": "Bag refine roll",
                              "scope": "user",
                              "formula": "1d6+{attr:Item}+{skill:Artisan}"})
    assert rm.status_code == 200, rm.text

    # Find a usable channel.
    rch = requests.get(f"{BASE_URL}/api/campaigns/{cid}/channels", headers=H(gm_token))
    assert rch.status_code == 200, rch.text
    chid = rch.json()[0]["id"]

    # Fire the macro against Eli.
    rfire = requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                            headers=H(gm_token),
                            json={"body": "/bagrefine", "character_id": eli_id})
    assert rfire.status_code == 200, rfire.text
    expanded = rfire.json()["slash_meta"]["macro"]["formula_expanded"]
    # eff Item = 4 + 3 lim − 3 enh = 4. Artisan skill = 4. 1d6+4+4.
    assert "+4+4" in expanded, f"expected +4+4 in expansion, got: {expanded}"


def test_apocophea_materials_can_be_seeded_as_codex_nodes(gm_token, besm_eli):
    """The user's spec: 'Materials should be tracked in the codex as
    entries for GMs to use in generating loot during play or in the
    director's console for encounter designs.' — verify the codex
    accepts the materials catalog as nodes."""
    cid, _eli = besm_eli

    # Sample of refined materials the bag generates from rubbish input.
    materials = [
        {"name": "Powdered Mithral",   "type": "item",
         "tags": ["material", "rare"], "summary": "Refined ore dust — light, magic-conductive."},
        {"name": "Cleaned Spider Silk", "type": "item",
         "tags": ["material", "fibre"], "summary": "Stripped of barbs; tensile-strong."},
        {"name": "Charming Scent Extract", "type": "item",
         "tags": ["material", "alchemy", "ranged"], "summary": "Volatile alchemical input for throwing flasks."},
        {"name": "Pickling Brine (mundane)", "type": "item",
         "tags": ["material", "mundane"], "summary": "Salvage waste from prior refining; low value."},
    ]
    created = []
    for m in materials:
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                            headers=H(gm_token), json=m)
        assert r.status_code in (200, 201), r.text
        created.append(r.json())
    assert len(created) == 4

    # Verify they show in the codex list.
    rl = requests.get(f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                        headers=H(gm_token))
    assert rl.status_code == 200, rl.text
    names = [n.get("name") or n.get("title") for n in rl.json()]
    for m in materials:
        assert m["name"] in names, f"{m['name']} missing from codex"
