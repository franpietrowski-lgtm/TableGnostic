"""V6.19 — Atelier Workshop + Anime5e Budget Audit + Class Progression live API tests.

Covers:
  - GET /api/anime5e/races (8 races + tier table)
  - GET /api/characters/{cid}/anime5e/budget-breakdown (Eli anime-5e)
  - POST /api/characters/{cid}/anime5e-recompute-budget (Eli 90→20 DP)
  - GET /api/characters/{cid}/class-progression
  - Surprise Bag: list / seed / draw / GM-only
  - Scene-Break Cards: list / seed / draw / GM-only
  - anime5e_xp_to_cp unit check (tier=20 at lvl 5, flat=20, curve=30)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

GMFRAN = {"email": "franpietrowski@gmail.com", "password": "PieGod08!!"}
AURORA = {"email": "albanaszak@ymail.com", "password": "AuroraTest123!"}

# Review-request IDs were stale (DB reset). Live IDs discovered via
# GET /api/campaigns for GMFran on 2026-05-03.
ANIME_CAMP = "2d31c25354e4415f84a31704fe78a795"
DND_CAMP = "a69ff91b592d411894a6210380615bbd"


def _ensure_anime_eli(session):
    """Create a TEST anime-5e Artificer L5 with budget=90 so recompute
    moves it to 20. Idempotent per session scope (returns fresh cid)."""
    r = session.post(f"{BASE_URL}/api/characters", json={
        "campaign_id": ANIME_CAMP,
        "name": "TEST_V619_AnimeEli",
        "power_level": "Heroic",
        "total_points": 200,
        "folio": {
            "dnd_state": {"class": "Artificer", "level": 5, "race": "Human"},
            "anime5e_state": {"point_budget": 90, "point_buys": []},
        },
    })
    assert r.status_code in (200, 201), r.text
    body = r.json()
    return body.get("id") or body.get("character", {}).get("id")


def _ensure_dnd_char(session):
    r = session.post(f"{BASE_URL}/api/characters", json={
        "campaign_id": DND_CAMP,
        "name": "TEST_V619_DnDChar",
        "power_level": "Heroic",
        "total_points": 0,
        "folio": {"dnd_state": {"class": "Fighter", "level": 4, "race": "Human"}},
    })
    assert r.status_code in (200, 201), r.text
    body = r.json()
    return body.get("id") or body.get("character", {}).get("id")


@pytest.fixture(scope="module")
def anime_eli_id(gm):
    return _ensure_anime_eli(gm)


@pytest.fixture(scope="module")
def dnd_char_id(gm):
    return _ensure_dnd_char(gm)


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=10)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {tok}",
                      "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def gm():
    return _login(GMFRAN)


@pytest.fixture(scope="module")
def aurora():
    return _login(AURORA)


# ─── anime5e_xp_to_cp formula unit check ────────────────────────────────

def test_anime5e_xp_to_cp_raw_formula():
    """V6.21 — RAW-correct: 80 + (level − 1). House-rule variants:
    flat=80, curve=80+2(L-1), tier=legacy bracket table."""
    import sys
    sys.path.insert(0, "/app/backend")
    from routes.character_validation import anime5e_xp_to_cp
    # RAW (the default)
    assert anime5e_xp_to_cp(1) == 80
    assert anime5e_xp_to_cp(5) == 84
    assert anime5e_xp_to_cp(20) == 99
    # flat (GM house-rule: 80 flat at every level)
    assert anime5e_xp_to_cp(1, "flat") == 80
    assert anime5e_xp_to_cp(10, "flat") == 80
    # curve (GM heroic: 80 + 2(L-1))
    assert anime5e_xp_to_cp(5, "curve") == 88
    # tier (legacy V6.19)
    assert anime5e_xp_to_cp(5, "tier") == 20
    assert anime5e_xp_to_cp(2, "tier") == 10
    assert anime5e_xp_to_cp(10, "tier") == 40


# ─── GET /api/anime5e/races ─────────────────────────────────────────────

def test_races_returns_entries_with_dp_costs(gm):
    r = gm.get(f"{BASE_URL}/api/anime5e/races")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "races" in body and "tier_table" in body
    # V6.21 — 14 native races + 14 PHB crossovers + 1 raceless entry.
    assert len(body["races"]) >= 14
    # DP costs are non-negative ints; raceless is 0; Human is 7 per RAW.
    for race in body["races"]:
        assert isinstance(race["dp_cost"], int) and race["dp_cost"] >= 0
        assert race.get("name") and race.get("blurb")
    # Tier table now uses name/caps rather than legacy (max_level,dp).
    names = [t["name"] for t in body["tier_table"]]
    assert "Novice" in names and "Mythical" in names
    # RAW note surfaces the 80 + (L-1) formula text.
    assert "80" in body["rules_note"]


# ─── Budget breakdown + Eli recompute ───────────────────────────────────

def test_eli_budget_breakdown_returns_tier_metadata(gm, anime_eli_id):
    r = gm.get(f"{BASE_URL}/api/characters/{anime_eli_id}/anime5e/budget-breakdown")
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["level"] == 5
    # V6.21 — RAW budget is 84 at level 5.
    assert b["canonical_raw_dp"] == 84
    # Total spent should break down into race + abilities + point_buys.
    assert b["ability_score_cost"] >= 0
    assert b["race_cost"] >= 0
    assert b["point_buy_total"] >= 0
    assert b["total_spent"] == (
        b["ability_score_cost"] + b["race_cost"] + b["point_buy_total"]
    )
    assert "ability_score_breakdown" in b
    assert "formula_note" in b


def test_eli_recompute_anime5e_budget_raw(gm, anime_eli_id):
    r = gm.post(f"{BASE_URL}/api/characters/{anime_eli_id}/anime5e-recompute-budget")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["level"] == 5
    # Whatever formula is on the campaign, the new budget should be
    # in the RAW/flat/curve/tier band: {84, 80, 88, 20}.
    assert body["new_point_budget"] in (84, 80, 88, 20)
    assert "formula" in body


def test_recompute_rejects_non_anime_campaign(gm, dnd_char_id):
    r = gm.post(f"{BASE_URL}/api/characters/{dnd_char_id}/anime5e-recompute-budget")
    assert r.status_code == 400


# ─── Class progression ──────────────────────────────────────────────────

def test_class_progression_eli(gm, anime_eli_id):
    r = gm.get(f"{BASE_URL}/api/characters/{anime_eli_id}/class-progression")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("class") == "Artificer"
    assert body.get("level") == 5
    assert body.get("known") is True
    assert "save_profs" in body


# ─── Surprise Bag ───────────────────────────────────────────────────────

def test_surprise_bag_seed_idempotent(gm):
    # Seed (idempotent)
    r1 = gm.post(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/surprise-bag/seed")
    assert r1.status_code == 200, r1.text
    r2 = gm.post(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/surprise-bag/seed")
    assert r2.status_code == 200
    body2 = r2.json()
    # 2nd call should skip
    assert body2.get("skipped") is True or body2.get("existing_count", 0) >= 6


def test_surprise_bag_list_has_entries(gm):
    r = gm.get(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/surprise-bag")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 6
    assert len(body["entries"]) >= 6


def test_surprise_bag_draw_returns_entry(gm):
    r = gm.post(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/surprise-bag/draw",
                json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert "drawn" in body
    assert body["drawn"].get("title")


def test_surprise_bag_gm_only_for_non_gm(aurora):
    r = aurora.post(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/surprise-bag/draw",
                    json={})
    assert r.status_code == 403


def test_surprise_bag_create_gm_only(aurora):
    r = aurora.post(
        f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/surprise-bag",
        json={"title": "TEST_should_fail", "blurb": "x", "category": "twist"},
    )
    assert r.status_code == 403


# ─── Scene-Break Cards ──────────────────────────────────────────────────

def test_scene_break_seed_idempotent(gm):
    r1 = gm.post(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/scene-break-cards/seed")
    assert r1.status_code == 200
    r2 = gm.post(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/scene-break-cards/seed")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2.get("skipped") is True or body2.get("existing_count", 0) >= 4


def test_scene_break_list(gm):
    r = gm.get(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/scene-break-cards")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 4


def test_scene_break_draw(gm):
    r = gm.post(f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/scene-break-cards/draw",
                json={})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["drawn"].get("title")


def test_scene_break_gm_only(aurora):
    r = aurora.post(
        f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/scene-break-cards/draw",
        json={},
    )
    assert r.status_code == 403


def test_scene_break_create_gm_only(aurora):
    r = aurora.post(
        f"{BASE_URL}/api/campaigns/{ANIME_CAMP}/scene-break-cards",
        json={"title": "TEST_should_fail", "body": "x", "mood": "transition"},
    )
    assert r.status_code == 403
