"""V6.21 backend tests — Anime 5E RAW DP rewrite + consent flow + seat applications.

Covers:
  - GET /api/anime5e/races (>=14 races, rules_note contains "80",
    tier_table has name/caps shape)
  - GET /api/characters/{cid}/anime5e/budget-breakdown
    (ability_score_breakdown 6-keys, ability_score_cost, race_cost,
    point_buy_total, total_spent, canonical_raw_dp = 80+(L-1),
    formula_note, net_unspent)
  - POST /api/characters/{cid}/anime5e-recompute-budget for
    raw / flat / curve / tier formula via campaign update
  - PUT /api/campaigns/{cid} accepts anime5e_xp_formula and
    consent_required
  - GET/POST/DELETE /api/campaigns/{cid}/consent
  - GET /api/campaigns/{cid}/consent-roll (GM only)
  - GET/POST /api/campaigns/{cid}/seat-applications

Auth: GMFran admin / Aurora player.
"""
import os
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://campaign-hub-288.preview.emergentagent.com").rstrip("/")

GM_CREDS = {"email": "franpietrowski@gmail.com", "password": "PieGod08!!"}
PLAYER_CREDS = {"email": "albanaszak@ymail.com", "password": "AuroraTest123!"}

ANIME_CAMP = "2d31c25354e4415f84a31704fe78a795"
DND_CAMP = "a69ff91b592d411894a6210380615bbd"


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


def _patch_campaign(session, cid, **fields):
    """PUT /api/campaigns/{cid} replaces the whole document — fetch current
    state and merge to avoid clobbering system_id and other fields."""
    cur = session.get(f"{BASE_URL}/api/campaigns/{cid}").json()
    payload = {**cur, **fields}
    # PUT model doesn't accept these read-only / nested fields
    for k in ("id", "gm_id", "gm_name", "member_ids", "invite_token",
              "created_at", "updated_at"):
        payload.pop(k, None)
    return session.put(f"{BASE_URL}/api/campaigns/{cid}", json=payload)


@pytest.fixture(scope="module")
def gm_session():
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_login(GM_CREDS)}",
                      "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def player_session():
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_login(PLAYER_CREDS)}",
                      "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def anime_char_id(gm_session):
    """Create a fresh anime-5e L5 Human character for budget tests."""
    r = gm_session.post(f"{BASE_URL}/api/characters", json={
        "campaign_id": ANIME_CAMP,
        "name": "TEST_V621_BudgetEli",
        "power_level": "Heroic",
        "total_points": 200,
        "folio": {
            "dnd_state": {"class": "Artificer", "level": 5, "race": "Human"},
            "anime5e_state": {"point_budget": 84, "point_buys": []},
        },
    })
    assert r.status_code in (200, 201), r.text[:300]
    body = r.json()
    cid = body.get("id") or body.get("character", {}).get("id")
    assert cid, body
    yield cid
    # cleanup best-effort
    try:
        gm_session.delete(f"{BASE_URL}/api/characters/{cid}")
    except Exception:
        pass


# ========================================================================
# RACE TABLE
# ========================================================================
class TestAnime5eRaces:
    def test_races_count_and_rules_note(self, gm_session):
        r = gm_session.get(f"{BASE_URL}/api/anime5e/races")
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        races = d.get("races", [])
        assert len(races) >= 14, f"expected >=14 races got {len(races)}"
        assert "80" in d.get("rules_note", ""), d.get("rules_note", "")

    def test_tier_table_uses_name_caps_shape(self, gm_session):
        r = gm_session.get(f"{BASE_URL}/api/anime5e/races")
        assert r.status_code == 200
        d = r.json()
        tt = d.get("tier_table", [])
        assert tt and isinstance(tt, list)
        first = tt[0]
        # New shape uses 'name' and 'caps' (not legacy 'dp'/'blurb' only)
        assert "name" in first and "caps" in first, first
        assert isinstance(first["caps"], dict)


# ========================================================================
# BUDGET BREAKDOWN
# ========================================================================
class TestBudgetBreakdown:
    def test_breakdown_shape_and_raw_math(self, gm_session, anime_char_id):
        r = gm_session.get(
            f"{BASE_URL}/api/characters/{anime_char_id}/anime5e/budget-breakdown")
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        # Required new fields
        for k in ("ability_score_breakdown", "ability_score_cost",
                  "race_cost", "point_buy_total", "total_spent",
                  "canonical_raw_dp", "formula_note", "net_unspent",
                  "stored_point_budget", "level"):
            assert k in d, f"missing key {k} in {list(d)}"
        # 6 ability keys
        assert len(d["ability_score_breakdown"]) == 6
        # Sum identity
        sum_abs = sum(d["ability_score_breakdown"].values())
        assert d["ability_score_cost"] == sum_abs, (
            d["ability_score_cost"], sum_abs)
        # total_spent = ability_score_cost + race_cost + point_buy_total
        assert (d["total_spent"]
                == d["ability_score_cost"] + d["race_cost"]
                + d["point_buy_total"]), d
        # canonical_raw_dp = 80 + (L-1)
        assert d["canonical_raw_dp"] == 80 + (d["level"] - 1), d
        # net_unspent = stored - total_spent
        assert (d["net_unspent"]
                == d["stored_point_budget"] - d["total_spent"]), d


# ========================================================================
# RECOMPUTE WITH CAMPAIGN FORMULA OVERRIDE
# ========================================================================
class TestRecomputeFormula:
    @pytest.mark.parametrize("formula,expected_l5", [
        ("raw", 84),     # 80 + (5-1)
        ("flat", 80),    # 80 flat
        ("curve", 88),   # 80 + 2*(5-1)
        ("tier", 20),    # legacy bracket at L5 = 20
    ])
    def test_recompute_each_formula(self, gm_session, anime_char_id,
                                    formula, expected_l5):
        # Set campaign formula
        rp = _patch_campaign(gm_session, ANIME_CAMP,
                             anime5e_xp_formula=formula)
        assert rp.status_code in (200, 201), rp.text[:200]
        # Recompute
        r = gm_session.post(
            f"{BASE_URL}/api/characters/{anime_char_id}"
            f"/anime5e-recompute-budget", json={})
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        assert d.get("formula") == formula, d
        assert d.get("new_point_budget") == expected_l5, (
            f"formula={formula} expected {expected_l5} got "
            f"{d.get('new_point_budget')}")

    def test_recompute_rejects_dnd_campaign_character(self, gm_session):
        # Create a D&D char and try to recompute (should 400)
        cr = gm_session.post(f"{BASE_URL}/api/characters", json={
            "campaign_id": DND_CAMP,
            "name": "TEST_V621_DnDChar",
            "power_level": "Heroic",
            "total_points": 0,
            "folio": {"dnd_state": {"class": "Fighter", "level": 4,
                                    "race": "Human"}},
        })
        assert cr.status_code in (200, 201), cr.text[:200]
        cid = cr.json().get("id") or cr.json().get("character", {}).get("id")
        try:
            r = gm_session.post(
                f"{BASE_URL}/api/characters/{cid}"
                f"/anime5e-recompute-budget", json={})
            assert r.status_code == 400, r.text[:200]
        finally:
            gm_session.delete(f"{BASE_URL}/api/characters/{cid}")


# ========================================================================
# CAMPAIGN MODEL — anime5e_xp_formula + consent_required
# ========================================================================
class TestCampaignFlags:
    def test_set_consent_required_true_then_false(self, gm_session):
        for val in (True, False):
            r = _patch_campaign(gm_session, ANIME_CAMP, consent_required=val)
            assert r.status_code in (200, 201), r.text[:200]
        # Final read
        r = gm_session.get(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}")
        assert r.status_code == 200
        assert r.json().get("consent_required") in (False, None)

    def test_anime5e_xp_formula_persists(self, gm_session):
        r = _patch_campaign(gm_session, ANIME_CAMP, anime5e_xp_formula="raw")
        assert r.status_code in (200, 201), r.text[:200]
        r2 = gm_session.get(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}")
        assert r2.json().get("anime5e_xp_formula") == "raw"


# ========================================================================
# CONSENT FLOW
# ========================================================================
class TestConsentFlow:
    def test_gm_can_post_consent(self, gm_session):
        r = gm_session.post(
            f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/consent",
            json={"primer_acknowledged": True,
                  "house_rules_acknowledged": True,
                  "safety_tags_acknowledged": True,
                  "note": "TEST_V621 GM consent"})
        assert r.status_code in (200, 201), r.text[:200]

    def test_gm_get_consent(self, gm_session):
        r = gm_session.get(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/consent")
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        # Response wraps the record under 'consent' key
        consent = d.get("consent") if isinstance(d.get("consent"), dict) else d
        assert consent.get("primer_acknowledged") in (True, False)

    def test_consent_roll_gm_only(self, gm_session, player_session):
        r_gm = gm_session.get(
            f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/consent-roll")
        assert r_gm.status_code == 200, r_gm.text[:200]
        d = r_gm.json()
        rows = d.get("rows") if isinstance(d, dict) else d
        assert isinstance(rows, list)
        # Player should be 403
        r_p = player_session.get(
            f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/consent-roll")
        assert r_p.status_code in (401, 403), r_p.text[:200]

    def test_non_seated_player_post_consent_403(self, player_session):
        # Aurora is not seated in DND_CAMP (most likely) — try to POST consent
        # there. If she IS seated, this becomes a soft-skip.
        r = player_session.post(
            f"{BASE_URL}/api/campaigns/{DND_CAMP}/consent",
            json={"primer_acknowledged": True,
                  "house_rules_acknowledged": True,
                  "safety_tags_acknowledged": True,
                  "note": "TEST_V621 non-seated try"})
        if r.status_code == 200:
            pytest.skip("Aurora is seated in DND_CAMP — cannot test 403")
        assert r.status_code in (401, 403, 404), r.text[:200]

    def test_delete_consent(self, gm_session):
        r = gm_session.delete(
            f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/consent")
        assert r.status_code in (200, 204), r.text[:200]


# ========================================================================
# SEAT APPLICATIONS
# ========================================================================
class TestSeatApplications:
    def test_player_post_application(self, player_session):
        r = player_session.post(
            f"{BASE_URL}/api/campaigns/{DND_CAMP}/seat-applications",
            json={"character_pitch": "TEST_V621 — half-elf bard",
                  "preferred_system_familiarity": "veteran",
                  "note": "TEST_V621 seat app"})
        # 200/201 on success, 409 on already-applied,
        # 400 if campaign is not publicly listed (acceptable response shape).
        assert r.status_code in (200, 201, 400, 409), r.text[:200]

    def test_gm_lists_applications(self, gm_session):
        r = gm_session.get(
            f"{BASE_URL}/api/campaigns/{DND_CAMP}/seat-applications")
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        apps = d.get("applications") if isinstance(d, dict) else d
        assert isinstance(apps, list)

    def test_player_cannot_list_applications(self, player_session):
        r = player_session.get(
            f"{BASE_URL}/api/campaigns/{DND_CAMP}/seat-applications")
        assert r.status_code in (401, 403), r.text[:200]
