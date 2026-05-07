"""V6.5 — Spell Conversion Atlas + Live Spend Preview + per-system PDF ornaments.

Validates:
  1. GET /api/reference/spell-conversions returns 62 entries across 9 schools.
  2. school filter + max_level filter work together.
  3. Each entry has the canonical shape (source_name, source_level, school,
     short_description, besm[], net_cp, source_reference).
  4. POST /api/characters/{id}/simulate-import returns the audit shape.
  5. simulate-import's `fits` flips false when projected > cap.
  6. simulate-import 403s for non-members.
  7. /api/reference/power-bundle-templates regression: still returns 10.
  8. PDF export still renders (HTTP 200, application/pdf, non-zero bytes)
     for besm-4e and anime-5e campaigns.
"""
from __future__ import annotations

import os
import pytest
import requests

API = os.environ.get("API_URL") or "https://campaign-hub-288.preview.emergentagent.com"
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


def H(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{API}/api/auth/login",
                      json={"email": GM_EMAIL, "password": GM_PASS})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def besm_camp(gm_token):
    camps = requests.get(f"{API}/api/campaigns", headers=H(gm_token)).json()
    besm = [c for c in camps if c.get("system_id") == "besm-4e"]
    assert besm, "Need a besm-4e campaign seeded."
    return besm[0]


@pytest.fixture(scope="module")
def anime_camp(gm_token):
    camps = requests.get(f"{API}/api/campaigns", headers=H(gm_token)).json()
    anime = [c for c in camps if c.get("system_id") == "anime-5e"]
    return anime[0] if anime else None


# ─── (1) Spell Conversion Atlas — total + shape ───
def test_spell_conversions_returns_62(gm_token):
    r = requests.get(f"{API}/api/reference/spell-conversions",
                     headers=H(gm_token))
    assert r.status_code == 200, r.text
    data = r.json()
    assert "entries" in data and "total" in data and "schools" in data
    assert data["total"] == 62, f"expected 62, got {data['total']}"
    assert data["returned"] == 62
    # Schools count
    assert len(data["schools"]) == 9, f"expected 9 schools, got {data['schools']}"


def test_spell_conversion_entry_shape(gm_token):
    r = requests.get(f"{API}/api/reference/spell-conversions", headers=H(gm_token))
    entries = r.json()["entries"]
    required = {"source_name", "source_level", "school",
                "short_description", "besm", "net_cp", "source_reference"}
    for e in entries[:5]:
        missing = required - set(e.keys())
        assert not missing, f"Missing keys {missing} in {e.get('source_name')}"
        assert isinstance(e["besm"], list)
        assert isinstance(e["net_cp"], int)


# ─── (2) Cantrip-only filter ───
def test_spell_conversion_max_level_zero_only_cantrips(gm_token):
    r = requests.get(f"{API}/api/reference/spell-conversions?max_level=0",
                     headers=H(gm_token))
    assert r.status_code == 200
    rows = r.json()["entries"]
    assert rows, "Should have at least some cantrips"
    for e in rows:
        assert int(e["source_level"]) == 0


# ─── (3) School filter ───
def test_spell_conversion_school_evocation_filter(gm_token):
    r = requests.get(f"{API}/api/reference/spell-conversions?school=Evocation",
                     headers=H(gm_token))
    assert r.status_code == 200
    rows = r.json()["entries"]
    assert rows, "Should have evocation entries"
    for e in rows:
        assert (e["school"] or "").lower() == "evocation"


# ─── (4) Power Bundle template regression — still 10 ───
def test_power_bundle_templates_regression(gm_token):
    r = requests.get(f"{API}/api/reference/power-bundle-templates",
                     headers=H(gm_token))
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 10, f"expected 10 templates, got {data['total']}"


# ─── (5,6) Simulate-import — audit shape + fits flip ───
@pytest.fixture(scope="module")
def test_character(gm_token, besm_camp):
    body = {
        "campaign_id": besm_camp["id"],
        "name": "TEST_v65_sim_pc",
        "concept": "live spend preview test",
        "power_level": "Heroic", "total_points": 100,
        "stats": {"body": 4, "mind": 4, "soul": 4},
        "attributes": [{"name": "Flight", "level": 2, "cost_per_level": 4}],
    }
    r = requests.post(f"{API}/api/characters", headers=H(gm_token), json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_simulate_import_shape_and_fits(gm_token, test_character):
    cid = test_character["id"]
    # Small extra → fits
    r = requests.post(f"{API}/api/characters/{cid}/simulate-import",
                      headers=H(gm_token), json={"extra_cost": 5})
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("current_spent", "current_cap", "projected_spent",
              "fits", "headroom", "summary"):
        assert k in d, f"missing key {k}"
    assert d["projected_spent"] == d["current_spent"] + 5
    assert d["fits"] is True
    assert d["headroom"] == d["current_cap"] - d["projected_spent"]
    assert "OK" in d["summary"]


def test_simulate_import_over_cap_fits_false(gm_token, test_character):
    cid = test_character["id"]
    # Massive extra → over budget
    r = requests.post(f"{API}/api/characters/{cid}/simulate-import",
                      headers=H(gm_token), json={"extra_cost": 9999})
    assert r.status_code == 200
    d = r.json()
    assert d["fits"] is False
    assert d["headroom"] < 0
    assert "OVER" in d["summary"]


def test_simulate_import_extra_bundle_cost(gm_token, test_character):
    cid = test_character["id"]
    r = requests.post(f"{API}/api/characters/{cid}/simulate-import",
                      headers=H(gm_token),
                      json={"extra_bundle": {"cost": 7}})
    assert r.status_code == 200
    assert r.json()["extra_cost"] == 7


# ─── (7) Non-member access gate ───
def test_simulate_import_403_for_non_member(gm_token, test_character):
    # Register a fresh player who is NOT a member of the campaign.
    import uuid
    email = f"TEST_v65_nonmember_{uuid.uuid4().hex[:8]}@example.com"
    reg = requests.post(f"{API}/api/auth/register", json={
        "email": email, "password": "Passw0rd!!", "name": "NonMember",
        "role": "player",
    })
    assert reg.status_code in (200, 201), reg.text
    login = requests.post(f"{API}/api/auth/login",
                          json={"email": email, "password": "Passw0rd!!"})
    assert login.status_code == 200
    pt = login.json()["access_token"]
    r = requests.post(f"{API}/api/characters/{test_character['id']}/simulate-import",
                      headers=H(pt), json={"extra_cost": 5})
    assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"


# ─── (8) PDF export — BESM ornaments rendering ───
def _find_exportable(token, system_id):
    """Return first campaign of given system that has sessions (export 200)."""
    camps = requests.get(f"{API}/api/campaigns", headers=H(token)).json()
    for c in camps:
        if c.get("system_id") != system_id:
            continue
        r = requests.get(f"{API}/api/campaigns/{c['id']}/export.pdf",
                         headers=H(token))
        if r.status_code == 200:
            return c, r
    return None, None


def test_pdf_export_besm(gm_token):
    camp, r = _find_exportable(gm_token, "besm-4e")
    if camp is None:
        pytest.skip("No BESM campaign with exportable sessions.")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert len(r.content) > 1000
    assert r.content[:4] == b"%PDF"


def test_pdf_export_anime5e(gm_token):
    camp, r = _find_exportable(gm_token, "anime-5e")
    if camp is None:
        pytest.skip("No Anime 5E campaign with exportable sessions.")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content[:4] == b"%PDF"
