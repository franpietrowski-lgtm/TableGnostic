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

def test_anime5e_xp_to_cp_formula_rebalanced():
    import sys
    sys.path.insert(0, "/app/backend")
    from routes.character_validation import anime5e_xp_to_cp
    # tier = canonical tier table (Tier 2 at level 5 = 20)
    assert anime5e_xp_to_cp(5, "tier") == 20
    assert anime5e_xp_to_cp(2, "tier") == 10
    assert anime5e_xp_to_cp(10, "tier") == 40
    # flat = 5 + 3L  (was 50+8L)
    assert anime5e_xp_to_cp(5, "flat") == 20
    assert anime5e_xp_to_cp(1, "flat") == 8
    # curve = 5 + 5L (was 40+10L)
    assert anime5e_xp_to_cp(5, "curve") == 30


# ─── GET /api/anime5e/races ─────────────────────────────────────────────

def test_races_returns_8_entries_with_dp_costs(gm):
    r = gm.get(f"{BASE_URL}/api/anime5e/races")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "races" in body and "tier_table" in body
    assert len(body["races"]) == 8
    # DP costs within 1-5
    for race in body["races"]:
        assert 1 <= race["dp_cost"] <= 5
        assert race.get("name") and race.get("traits")
    # tier table 10/20/40/60/80
    dps = [t["dp"] for t in body["tier_table"]]
    assert dps == [10, 20, 40, 60, 80]


# ─── Budget breakdown + Eli recompute ───────────────────────────────────

def test_eli_budget_breakdown_returns_tier_metadata(gm, anime_eli_id):
    r = gm.get(f"{BASE_URL}/api/characters/{anime_eli_id}/anime5e/budget-breakdown")
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["level"] == 5
    assert b["tier"]["dp"] == 20  # Tier 2 at level 5 = 20 DP (core p.7-8)
    assert b["canonical_tier_dp"] == 20
    assert b["stored_point_budget"] == 90
    assert b["suspicious_budget"] is True  # 90 > 1.5 * 20
    assert b["tier"]["name"].startswith("Tier 2")


def test_eli_recompute_anime5e_budget_to_tier(gm, anime_eli_id):
    r = gm.post(f"{BASE_URL}/api/characters/{anime_eli_id}/anime5e-recompute-budget")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["level"] == 5
    # Whatever the campaign formula, the new budget should be reasonable
    # (not 90). tier=20, flat=20, curve=30.
    assert body["new_point_budget"] in (20, 30, 40)
    assert body["previous_point_budget"] >= 20
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
