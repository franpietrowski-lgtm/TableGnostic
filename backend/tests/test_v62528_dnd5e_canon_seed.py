"""V6.25.28 — D&D 5E full canonical reference seeding tests.

Validates the extended SRD payload returned by
`GET /api/systems/dnd-5e/reference` and the new kind enum in the
Reference Editor (subclass / magic_item / monster / language / tool).
All content is mechanic-only per CC-BY 4.0 SRD 5.1.
"""
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"


def _login():
    r = requests.post(f"{API}/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    r.raise_for_status()
    return r.json()["access_token"]


def test_dnd5e_reference_payload_shape():
    """All extended SRD sections present + non-empty."""
    r = requests.get(f"{API}/systems/dnd-5e/reference")
    r.raise_for_status()
    d = r.json()
    assert d["system_id"] == "dnd-5e"
    # Original sections (regression).
    assert len(d["classes"]) == 12
    assert len(d["abilities"]) == 6
    assert len(d["skills"]) == 18
    assert len(d["conditions"]) == 14
    # V6.25.28 — extended SRD seeding.
    assert len(d["races"]) >= 21, "Original 9 + 12 extended races"
    assert len(d["feats"]) >= 40, "SRD feats catalogue"
    assert len(d["magic_items"]) >= 50, "SRD magic items catalogue"
    assert len(d["monsters"]) >= 50, "SRD monster catalogue"
    assert len(d["languages"]) == 16, "16 SRD languages"
    assert len(d["tools"]) >= 25, "SRD tools / kits / instruments"
    assert len(d["subclasses"]) == 12, "One canonical subclass per class"
    assert len(d["damage_types"]) == 13, "13 SRD damage types"
    assert len(d["schools"]) == 8, "8 schools of magic"
    # class_features dict — every class has a level-feature timeline.
    cf = d["class_features"]
    assert set(cf.keys()) == {c["name"] for c in d["classes"]}, \
        "Every class must have a CLASS_FEATURES timeline"


def test_dnd5e_feats_have_prereq_and_summary():
    r = requests.get(f"{API}/systems/dnd-5e/reference")
    feats = r.json()["feats"]
    for ft in feats:
        assert ft["name"]
        assert "prereq" in ft
        assert ft["summary"]
        assert ft["page"] == 165


def test_dnd5e_monsters_have_combat_stats():
    """Every monster row has CR, AC, HP, speed, attack summary."""
    r = requests.get(f"{API}/systems/dnd-5e/reference")
    monsters = r.json()["monsters"]
    for m in monsters:
        assert m["name"]
        assert m["type"]
        assert "cr" in m
        assert "ac" in m
        assert "hp" in m
        assert m["speed"]
        assert m["atks"]


def test_dnd5e_magic_items_have_rarity_and_attune():
    r = requests.get(f"{API}/systems/dnd-5e/reference")
    items = r.json()["magic_items"]
    rarities = {it["rarity"] for it in items}
    # SRD rarity tiers.
    assert {"common", "uncommon", "rare"}.issubset(rarities)
    for it in items:
        assert it["name"]
        assert it["type"]
        assert isinstance(it["attune"], bool)
        assert it["summary"]


def test_dnd5e_languages_categorised():
    r = requests.get(f"{API}/systems/dnd-5e/reference")
    langs = r.json()["languages"]
    cats = {lng["category"] for lng in langs}
    assert cats == {"standard", "exotic"}
    names = {lng["name"] for lng in langs}
    assert {"Common", "Draconic", "Infernal", "Undercommon"}.issubset(names)


def test_reference_editor_accepts_new_kinds():
    """V6.25.28 — subclass / magic_item / monster / language / tool
    must round-trip through the Reference Editor CRUD."""
    token = _login()
    # Find a D&D 5E campaign owned by the GM.
    camps = requests.get(f"{API}/campaigns",
                         headers={"Authorization": f"Bearer {token}"}).json()
    dnd_camp = next((c for c in camps if c.get("system_id") == "dnd-5e"), None)
    if dnd_camp is None:
        # Create one if none exists — keeps the test self-contained.
        c = requests.post(f"{API}/campaigns",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"name": "V62528 dnd test",
                                  "system_id": "dnd-5e",
                                  "power_level": "Heroic"})
        c.raise_for_status()
        dnd_camp = c.json()
    cid = dnd_camp["id"]
    created_ids = []
    for kind in ("subclass", "magic_item", "monster", "language", "tool"):
        body = {
            "kind": kind,
            "name": f"V62528 test {kind}",
            "summary": f"Mechanical test row for {kind}.",
            "page": 1,
        }
        r = requests.post(f"{API}/campaigns/{cid}/reference",
                            headers={"Authorization": f"Bearer {token}"},
                            json=body)
        assert r.status_code == 200, f"{kind}: {r.status_code} {r.text}"
        created_ids.append((kind, r.json()["id"]))
    # GET filtered by kind returns the row.
    for kind, rid in created_ids:
        r = requests.get(f"{API}/campaigns/{cid}/reference?kind={kind}",
                          headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        rows = r.json()
        assert any(row["id"] == rid for row in rows), \
            f"Created {kind} row not found in filtered listing"
    # Cleanup.
    for kind, rid in created_ids:
        requests.delete(f"{API}/campaigns/{cid}/reference/{rid}",
                          headers={"Authorization": f"Bearer {token}"})


def test_reference_editor_rejects_unknown_kind():
    token = _login()
    camps = requests.get(f"{API}/campaigns",
                         headers={"Authorization": f"Bearer {token}"}).json()
    dnd_camp = next((c for c in camps if c.get("system_id") == "dnd-5e"), None)
    assert dnd_camp is not None, "Need a dnd-5e campaign for this assertion"
    cid = dnd_camp["id"]
    r = requests.post(f"{API}/campaigns/{cid}/reference",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"kind": "totally_not_a_kind",
                              "name": "x", "summary": "x"})
    assert r.status_code in (400, 422), f"Expected 4xx, got {r.status_code}"
