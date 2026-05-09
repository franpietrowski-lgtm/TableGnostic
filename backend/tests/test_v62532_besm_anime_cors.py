"""V6.25.32 — BESM canonical templates + Anime 5E parity expansion + CORS regex regression.

Targets:
- GET /api/besm/reference must expose race_templates (8) and class_templates (12)
- GET /api/systems/anime-5e/reference must contain new keys with required minimums
- GET /api/systems/dnd-5e/reference must remain at parity (regression after re-export)
- /api/auth/login Origin=https://tablegnostic.com must echo allow-origin (CORS regex fix)
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


# ------------------------------------------------------------------
# BESM /reference race_templates + class_templates
# ------------------------------------------------------------------
def test_besm_reference_has_race_and_class_templates():
    r = requests.get(f"{BASE_URL}/api/besm/reference", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "race_templates" in data, "race_templates missing"
    assert "class_templates" in data, "class_templates missing"
    races = data["race_templates"]
    classes = data["class_templates"]
    assert len(races) == 8, f"expected 8 races, got {len(races)}"
    assert len(classes) == 12, f"expected 12 classes, got {len(classes)}"
    # Shape contract
    for tpl in races + classes:
        for fld in ("name", "cp_cost", "summary", "bundle"):
            assert fld in tpl, f"template missing {fld}: {tpl.get('name')}"
        assert isinstance(tpl["bundle"], list)  # may be empty for 0-cost baseline
        for entry in tpl["bundle"]:
            assert "kind" in entry and "name" in entry, f"bad bundle entry in {tpl['name']}: {entry}"


def test_besm_class_adventurer_generalist_present():
    """The frontend test below applies this exact one — it must exist."""
    r = requests.get(f"{BASE_URL}/api/besm/reference", timeout=20)
    assert r.status_code == 200
    classes = r.json()["class_templates"]
    names = [c["name"] for c in classes]
    assert any("Adventurer" in n and "Generalist" in n for n in names), \
        f"'Adventurer (Generalist)' missing — got {names}"


# ------------------------------------------------------------------
# Anime 5E /reference parity expansion
# ------------------------------------------------------------------
def test_anime5e_reference_parity_minimums():
    r = requests.get(f"{BASE_URL}/api/systems/anime-5e/reference", timeout=20)
    assert r.status_code == 200, r.text
    ref = r.json()
    minimums = {
        "subclasses": 22,
        "feats": 57,
        "tools": 35,
        "languages": 21,
        "magic_items": 76,
        "monsters": 77,
    }
    exacts = {"damage_types": 13, "schools": 8}
    for k, m in minimums.items():
        assert k in ref, f"key {k} missing"
        assert len(ref[k]) >= m, f"{k} {len(ref[k])} < {m}"
    for k, exact in exacts.items():
        assert k in ref, f"key {k} missing"
        assert len(ref[k]) == exact, f"{k} {len(ref[k])} != {exact}"


def test_anime5e_reference_anime_originals_present():
    r = requests.get(f"{BASE_URL}/api/systems/anime-5e/reference", timeout=20)
    assert r.status_code == 200
    ref = r.json()
    sub_names = [s.get("name", "") for s in ref.get("subclasses", [])]
    assert any("Way of the Mind" in n for n in sub_names), f"Mind's Eye subclass missing: {sub_names[:5]}"
    mon_names = [m.get("name", "") for m in ref.get("monsters", [])]
    assert any("Kaiju (Lesser)" in n for n in mon_names), "Kaiju (Lesser) missing"
    feat_names = [f.get("name", "") for f in ref.get("feats", [])]
    assert any("Transformation Sequence" in n for n in feat_names), "Transformation Sequence missing"
    mi_names = [i.get("name", "") for i in ref.get("magic_items", [])]
    assert any("Henshin Pendant" in n for n in mi_names), "Henshin Pendant missing"


# ------------------------------------------------------------------
# D&D 5E /reference regression after re-export by anime5e_extended
# ------------------------------------------------------------------
def test_dnd5e_reference_regression():
    r = requests.get(f"{BASE_URL}/api/systems/dnd-5e/reference", timeout=20)
    assert r.status_code == 200, r.text
    ref = r.json()
    minimums = {"subclasses": 12, "feats": 42, "tools": 18, "monsters": 60}
    for k, m in minimums.items():
        assert k in ref, f"key {k} missing"
        assert len(ref[k]) >= m, f"dnd {k}: {len(ref[k])} < {m}"


# ------------------------------------------------------------------
# CORS regex production-domain fix
# ------------------------------------------------------------------
def test_cors_login_tablegnostic_origin():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "franpietrowski@gmail.com", "password": "PieGod08!!"},
        headers={"Origin": "https://tablegnostic.com", "Content-Type": "application/json"},
        timeout=20,
    )
    assert r.status_code == 200, f"login failed for tablegnostic origin: {r.status_code} {r.text}"
    aco = r.headers.get("access-control-allow-origin", "")
    assert aco == "https://tablegnostic.com", \
        f"allow-origin mismatch: '{aco}' (expected https://tablegnostic.com)"
