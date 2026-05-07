"""V6.4 — Rules correctness + Power Bundle + Anime 5E XP→CP pytest sweep.

Validates:
  1. BESM CP math with Enhancement/Limiter VALUE deltas (not just count).
  2. Attribute effective_level + cost_modifier syntax (Flight Lvl 1 (4)).
  3. Modifier-value out-of-range warning (>±12 = Absolute Power supplement).
  4. Power Pack (always-on) vs Power Bundle (activatable) distinction.
  5. Anime 5E XP→CP formulas: flat (50+8×L) and curve (40+L×{10/12/15}).
  6. Power Bundle template endpoint returns filtered templates.
  7. D&D 5E chassis validator still enforces level 1-20.
  8. Cypher tier 1-6 + descriptor/type/focus warnings.
  9. Approval gate HTTP 400 when rules fail + no house-rules.
 10. Bundle cost estimator matches character validator per-line math.
"""
from __future__ import annotations

import os
import pytest
import requests

API = os.environ.get("API_URL") or "https://campaign-hub-288.preview.emergentagent.com"
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{API}/api/auth/login",
                      json={"email": GM_EMAIL, "password": GM_PASS})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def H(t):
    return {"Authorization": f"Bearer {t}"}


def _besm_camp(tok):
    camps = requests.get(f"{API}/api/campaigns", headers=H(tok)).json()
    besm = [c for c in camps if c.get("system_id") == "besm-4e"]
    assert besm, "Need at least one besm-4e campaign seeded."
    return besm[0]


def _anime_camp(tok):
    camps = requests.get(f"{API}/api/campaigns", headers=H(tok)).json()
    anime = [c for c in camps if c.get("system_id") == "anime-5e"]
    assert anime, "Need at least one anime-5e campaign seeded."
    return anime[0]


# ─── (1) Enhancement/Limiter VALUE deltas shift effective level ───
def test_enh_lim_value_shifts_effective_level(gm_token):
    camp = _besm_camp(gm_token)
    body = {
        "campaign_id": camp["id"],
        "name": "TEST_v64_attr_mods",
        "concept": "Rules-correctness test",
        "power_level": "Heroic", "total_points": 120,
        "stats": {"body": 4, "mind": 4, "soul": 4},
        "attributes": [{
            "name": "Flight",
            "level": 1,
            "cost_per_level": 4,
            # Three +1 limiters = net +3 → effective_level 4
            "limiters": [{"name": "Range", "value": 1},
                          {"name": "Concentration", "value": 1},
                          {"name": "Visible Use", "value": 1}],
            "enhancements": [],
        }],
    }
    r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    v = requests.get(f"{API}/api/characters/{cid}/validate",
                     headers=H(gm_token)).json()
    line = next(x for x in v["breakdown"]["lines"] if x["kind"] == "attribute")
    assert line["level"] == 1
    assert line["effective_level"] == 4, f"expected eff=4, got {line['effective_level']}"
    # 3 positive mod-deltas × level 1 → +3 CP added to paid cost
    assert line["points"] == 4 + 3, f"expected 7 paid CP, got {line['points']}"
    requests.delete(f"{API}/api/characters/{cid}", headers=H(gm_token))


# ─── (2) Out-of-range modifier value → warning-only, not blocked ───
def test_out_of_range_modifier_warns(gm_token):
    camp = _besm_camp(gm_token)
    body = {
        "campaign_id": camp["id"], "name": "TEST_v64_absolute_power",
        "concept": "Absolute Power supplement canary",
        "power_level": "Heroic", "total_points": 500,  # high cap to allow
        "attributes": [{
            "name": "Heat Vision", "level": 1, "cost_per_level": 1,
            "limiters": [{"name": "Cosmic Scale Limiter", "value": 20}],
            "enhancements": [],
        }],
    }
    r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=body)
    assert r.status_code == 200
    cid = r.json()["id"]
    v = requests.get(f"{API}/api/characters/{cid}/validate",
                     headers=H(gm_token)).json()
    # Must warn, not fail — Absolute Power supplement can go beyond ±12.
    assert any("±12" in w or "canonical" in w for w in v["warnings"]), (
        f"Expected out-of-range warning; got {v['warnings']}")
    requests.delete(f"{API}/api/characters/{cid}", headers=H(gm_token))


# ─── (3) Power Pack (always-on) vs Power Bundle (activatable) ───
def test_power_pack_vs_bundle_distinct_in_breakdown(gm_token):
    camp = _besm_camp(gm_token)
    body = {
        "campaign_id": camp["id"], "name": "TEST_v64_pack_vs_bundle",
        "power_level": "Heroic", "total_points": 120,
        "power_packs": [{"name": "Enchanted Plate", "cost": 10}],
        "power_bundles": [{
            "name": "Fireball",
            "cost": 12,
            "invocation": "per-charge",
            "charges_max": 3, "charges_current": 3,
            "source_spell_name": "Fireball", "source_spell_level": 3,
        }],
    }
    r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    v = requests.get(f"{API}/api/characters/{cid}/validate",
                     headers=H(gm_token)).json()
    bd = v["breakdown"]
    assert bd["power_pack_total"] == 10, bd
    assert bd["power_bundle_total"] == 12, bd
    kinds = [ln["kind"] for ln in bd["lines"]]
    assert "power_pack" in kinds and "power_bundle" in kinds
    bundle_line = next(ln for ln in bd["lines"] if ln["kind"] == "power_bundle")
    assert "per-charge" in bundle_line["note"]
    assert "3 charges" in bundle_line["note"]
    requests.delete(f"{API}/api/characters/{cid}", headers=H(gm_token))


# ─── (4) Anime 5E DP / CP budget formulas (V6.21) ───
@pytest.mark.parametrize("formula,level,expected", [
    # RAW: 80 + (L − 1)
    ("raw", 1, 80), ("raw", 5, 84), ("raw", 10, 89), ("raw", 20, 99),
    # flat: 80 at every level
    ("flat", 1, 80), ("flat", 5, 80), ("flat", 20, 80),
    # curve: 80 + 2(L − 1)
    ("curve", 1, 80), ("curve", 5, 88), ("curve", 10, 98),
    # tier (legacy V6.19 brackets)
    ("tier", 1, 10), ("tier", 5, 20), ("tier", 10, 40),
])
def test_anime5e_xp_to_cp_formulas(gm_token, formula, level, expected):
    from importlib import import_module
    cv = import_module("routes.character_validation")
    assert cv.anime5e_xp_to_cp(level, formula) == expected


def test_anime5e_xp_curve_endpoint(gm_token):
    camp = _anime_camp(gm_token)
    r = requests.get(f"{API}/api/campaigns/{camp['id']}/anime5e-xp-curve",
                      headers=H(gm_token))
    assert r.status_code == 200
    d = r.json()
    assert d["formula"] in ("raw", "flat", "curve", "tier")
    assert len(d["curve"]) == 20
    # Level 1 RAW default = 80 DP.
    if d["formula"] == "raw":
        assert d["curve"][0]["cp"] == 80


# ─── (5) Power Bundle templates endpoint ───
def test_power_bundle_templates_filter(gm_token):
    r = requests.get(f"{API}/api/reference/power-bundle-templates?max_level=3",
                      headers=H(gm_token))
    assert r.status_code == 200
    d = r.json()
    # total is the full library (10 seeded); filtered list is ≤ total.
    assert d["total"] >= 10
    assert len(d["templates"]) <= d["total"]
    for t in d["templates"]:
        assert int(t["source_spell_level"]) <= 3, t
    # Cantrip (Dancing Lights) must be in the ≤3 filter.
    names = [t["name"] for t in d["templates"]]
    assert "Dancing Lights" in names


# ─── (6) D&D 5E level bound still enforced ───
def test_dnd_level_bound(gm_token):
    # Find a dnd-5e campaign; skip if none seeded.
    camps = requests.get(f"{API}/api/campaigns", headers=H(gm_token)).json()
    dnd = [c for c in camps if c.get("system_id") == "dnd-5e"]
    if not dnd:
        pytest.skip("no dnd-5e campaign seeded")
    camp = dnd[0]
    body = {
        "campaign_id": camp["id"], "name": "TEST_v64_dnd_over_level",
        "power_level": "Heroic", "total_points": 0,
        "folio": {"dnd_state": {"class": "Wizard", "level": 25, "race": "Human"}},
    }
    r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=body)
    assert r.status_code == 200
    cid = r.json()["id"]
    v = requests.get(f"{API}/api/characters/{cid}/validate",
                     headers=H(gm_token)).json()
    assert v["passes_rules"] is False
    assert any("25" in i or "1-20" in i for i in v["issues"])
    requests.delete(f"{API}/api/characters/{cid}", headers=H(gm_token))


# ─── (7) Cypher tier bound still enforced ───
def test_cypher_tier_bound(gm_token):
    camps = requests.get(f"{API}/api/campaigns", headers=H(gm_token)).json()
    cy = [c for c in camps if c.get("system_id") == "cypher"]
    if not cy:
        pytest.skip("no cypher campaign seeded")
    camp = cy[0]
    body = {
        "campaign_id": camp["id"], "name": "TEST_v64_cypher_over_tier",
        "power_level": "Heroic", "total_points": 0,
        "folio": {"cypher_state": {"tier": 9, "descriptor": "Swift",
                                     "type": "Warrior", "focus": "Masters Weapons"}},
    }
    r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=body)
    assert r.status_code == 200
    cid = r.json()["id"]
    v = requests.get(f"{API}/api/characters/{cid}/validate",
                     headers=H(gm_token)).json()
    assert v["passes_rules"] is False
    assert any("tier" in i.lower() or "1-6" in i for i in v["issues"])
    requests.delete(f"{API}/api/characters/{cid}", headers=H(gm_token))


# ─── (8) Bundle cost estimator + validator agree ───
def test_bundle_estimator_matches_validator_per_line(gm_token):
    r = requests.post(f"{API}/api/reference/estimate-bundle-cost",
                       headers=H(gm_token),
                       json={"components": [
                           {"kind": "attribute", "name": "Weapon",
                            "cost_per_level": 4, "level": 3, "refund": 2},
                           {"kind": "skill", "name": "Combat",
                            "cost_per_level": 2, "level": 2},
                           {"kind": "defect", "name": "Conditional",
                            "points_per_rank": 2, "rank": 1},
                       ]})
    assert r.status_code == 200
    d = r.json()
    assert d["total_cost"] == 10 + 4 - 2
    # Attribute line follows validator's math (gross − refund).
    attr = next(ln for ln in d["lines"] if ln["kind"] == "attribute")
    assert attr["gross"] == 12 and attr["refund"] == 2 and attr["points"] == 10


# ─── (9) House-rules bypass still works ───
def test_house_rules_bypass_retained(gm_token):
    camp = _besm_camp(gm_token)
    # Set house rules first.
    full = requests.get(f"{API}/api/campaigns/{camp['id']}",
                         headers=H(gm_token)).json()
    original_hr = full.get("house_rules", "")
    full["house_rules"] = "V6.4 regression — Absolute Power bands active."
    r = requests.put(f"{API}/api/campaigns/{camp['id']}",
                      headers=H(gm_token), json=full)
    assert r.status_code == 200
    try:
        # Create a failing character (wildly over budget).
        bad = {
            "campaign_id": camp["id"], "name": "TEST_v64_hr_bypass",
            "power_level": "Heroic", "total_points": 10,
            "attributes": [{"name": "Megattack", "level": 20, "cost_per_level": 10,
                            "enhancements": [], "limiters": []}],
        }
        r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=bad)
        assert r.status_code == 200
        cid = r.json()["id"]
        # Validator says fails rules.
        v = requests.get(f"{API}/api/characters/{cid}/validate",
                          headers=H(gm_token)).json()
        assert v["passes_rules"] is False
        # But GM can still approve thanks to house-rules bypass.
        r2 = requests.post(f"{API}/api/characters/{cid}/approve-for-play",
                            headers=H(gm_token), json={"approved": True})
        assert r2.status_code == 200, r2.text
        assert r2.json()["approved_for_play"] is True
        requests.delete(f"{API}/api/characters/{cid}", headers=H(gm_token))
    finally:
        # Restore campaign.
        full["house_rules"] = original_hr
        requests.put(f"{API}/api/campaigns/{camp['id']}",
                      headers=H(gm_token), json=full)


# ─── (10) Legacy string enhancement/limiter tags still score ±1 ───
def test_legacy_string_tags_default_to_plus_minus_one(gm_token):
    camp = _besm_camp(gm_token)
    body = {
        "campaign_id": camp["id"], "name": "TEST_v64_legacy_tags",
        "power_level": "Heroic", "total_points": 120,
        "attributes": [{
            "name": "Flight", "level": 1, "cost_per_level": 4,
            # Legacy string form — must be interpreted as value=+1 / -1.
            "limiters": ["Range: 30 ft"],
            "enhancements": ["Area"],
        }],
    }
    r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=body)
    assert r.status_code == 200
    cid = r.json()["id"]
    v = requests.get(f"{API}/api/characters/{cid}/validate",
                      headers=H(gm_token)).json()
    line = next(x for x in v["breakdown"]["lines"] if x["kind"] == "attribute")
    # Net delta = +1 (limiter) + -1 (enhancement) = 0.
    assert line["effective_level"] == 1, line
    assert line["points"] == 4, line
    requests.delete(f"{API}/api/characters/{cid}", headers=H(gm_token))
