"""V6.25.9 — character-aware macro token grammar.

The macro resolver reads from the LIVE character sheet (not the
SRD reference / custom-rules editor). Tokens this suite covers:

  • {attr:Name}    — effective Level (rank-summed)
  • {skill:Name}   — assigned Level
  • {def:Name}     — Defect rank
  • {stat:body|...} — raw stat / ability score
  • {derived:hp|ep|cv|atk|dfn|dm|ac|init}
  • Legacy scalar tokens (BODY/MIND/SOUL etc.) still resolve.
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
def besm_with_char(gm_token):
    """A BESM 4E campaign + GM-owned character with a Weapon attribute
    holding rank-aware enhancements + a Combat skill + Berserk defect."""
    cp = requests.post(f"{BASE_URL}/api/campaigns",
                        headers=H(gm_token),
                        json={"name": "V6259 macro-grammar", "system_id": "besm-4e"})
    assert cp.status_code == 200, cp.text
    cid = cp.json()["id"]

    char = {
        "campaign_id": cid,
        "name": "Macro Grammar Test",
        "concept": "rank-aware macro target",
        "power_level": "Heroic",
        "total_points": 120,
        "stats": {"body": 6, "mind": 4, "soul": 5},
        "attributes": [{
            "name": "Weapon", "level": 3, "cost_per_level": 1,
            "enhancements": [{"name": "Penetrating", "rank": 2, "value": -2}],
            "limiters":     [{"name": "Backlash",     "rank": 4, "value": 4}],
        }],
        "skills": [{"group": "Combat", "level": 5, "cost_per_level": 2}],
        "defects": [{"name": "Berserk", "rank": 2, "points_per_rank": 1, "category": "Lesser"}],
        "power_packs": [],
    }
    rch = requests.post(f"{BASE_URL}/api/characters",
                         headers=H(gm_token), json=char)
    assert rch.status_code == 200, rch.text
    yield (cid, rch.json()["id"])
    requests.delete(f"{BASE_URL}/api/characters/{rch.json()['id']}", headers=H(gm_token))
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def _get_pbp_channel(cid, token):
    r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/channels",
                      headers=H(token))
    assert r.status_code == 200, r.text
    chs = r.json()
    if chs:
        return chs[0]["id"]
    cr = requests.post(f"{BASE_URL}/api/campaigns/{cid}/channels",
                        headers=H(token),
                        json={"name": "general", "kind": "text"})
    assert cr.status_code == 200, cr.text
    return cr.json()["id"]


def test_attr_token_resolves_effective_level(gm_token, besm_with_char):
    """{attr:Weapon} on a Weapon with level=3, lim=+4, enh=-2 should
    expand to +5 (effective level), NOT +3 (assigned level)."""
    cid, char_id = besm_with_char

    # Create a macro that uses the new grammar.
    rm = requests.post(f"{BASE_URL}/api/campaigns/{cid}/macros",
                        headers=H(gm_token),
                        json={"name": "weaponhit", "label": "Weapon hit",
                              "scope": "user",
                              "formula": "2d6+{attr:Weapon}+{skill:Combat}"})
    assert rm.status_code == 200, rm.text

    # Fire it.
    chid = _get_pbp_channel(cid, gm_token)
    rp = requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                        headers=H(gm_token),
                        json={"body": "/weaponhit", "character_id": char_id})
    assert rp.status_code == 200, rp.text
    data = rp.json()
    assert data["kind"] == "macro"
    expanded = data["slash_meta"]["macro"]["formula_expanded"]
    # eff = 3 + 4 (lim) - 2 (enh) = 5; skill = 5; → 2d6+5+5
    assert "+5+5" in expanded, f"expected +5+5 in {expanded}"


def test_def_and_derived_tokens(gm_token, besm_with_char):
    """{def:Berserk} should resolve to rank 2; {derived:cv} should
    resolve to (6+4+5)/3 = 5."""
    cid, char_id = besm_with_char

    rm = requests.post(f"{BASE_URL}/api/campaigns/{cid}/macros",
                        headers=H(gm_token),
                        json={"name": "berserkfury", "label": "Berserk fury",
                              "scope": "user",
                              "formula": "1d6+{def:Berserk}+{derived:cv}"})
    assert rm.status_code == 200, rm.text

    chid = _get_pbp_channel(cid, gm_token)
    rp = requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                        headers=H(gm_token),
                        json={"body": "/berserkfury", "character_id": char_id})
    assert rp.status_code == 200, rp.text
    expanded = rp.json()["slash_meta"]["macro"]["formula_expanded"]
    assert "+2+5" in expanded, f"expected +2+5 in {expanded}"


def test_stat_token_body(gm_token, besm_with_char):
    """{stat:body} should resolve to BODY = 6."""
    cid, char_id = besm_with_char

    rm = requests.post(f"{BASE_URL}/api/campaigns/{cid}/macros",
                        headers=H(gm_token),
                        json={"name": "bodycheck", "label": "Body check",
                              "scope": "user",
                              "formula": "2d6+{stat:body}"})
    assert rm.status_code == 200, rm.text

    chid = _get_pbp_channel(cid, gm_token)
    rp = requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                        headers=H(gm_token),
                        json={"body": "/bodycheck", "character_id": char_id})
    assert rp.status_code == 200, rp.text
    expanded = rp.json()["slash_meta"]["macro"]["formula_expanded"]
    assert "+6" in expanded, f"expected +6 in {expanded}"


def test_legacy_scalar_tokens_still_resolve(gm_token, besm_with_char):
    """V6.25.7 macros that wrote BODY / MIND / SOUL bare must keep
    working — back-compat."""
    cid, char_id = besm_with_char

    rm = requests.post(f"{BASE_URL}/api/campaigns/{cid}/macros",
                        headers=H(gm_token),
                        json={"name": "legacy", "label": "Legacy",
                              "scope": "user",
                              "formula": "1d20+BODY+MIND"})
    assert rm.status_code == 200, rm.text

    chid = _get_pbp_channel(cid, gm_token)
    rp = requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                        headers=H(gm_token),
                        json={"body": "/legacy", "character_id": char_id})
    assert rp.status_code == 200, rp.text
    expanded = rp.json()["slash_meta"]["macro"]["formula_expanded"]
    # BODY=6, MIND=4
    assert "+6+4" in expanded, f"expected +6+4 in {expanded}"


def test_unknown_token_collapses_to_zero(gm_token, besm_with_char):
    """Unknown attribute / skill names should resolve to +0 — not 422."""
    cid, char_id = besm_with_char

    rm = requests.post(f"{BASE_URL}/api/campaigns/{cid}/macros",
                        headers=H(gm_token),
                        json={"name": "unknownattr", "label": "?",
                              "scope": "user",
                              "formula": "1d6+{attr:DoesNotExist}"})
    assert rm.status_code == 200, rm.text

    chid = _get_pbp_channel(cid, gm_token)
    rp = requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                        headers=H(gm_token),
                        json={"body": "/unknownattr", "character_id": char_id})
    assert rp.status_code == 200, rp.text
    expanded = rp.json()["slash_meta"]["macro"]["formula_expanded"]
    assert "+0" in expanded
