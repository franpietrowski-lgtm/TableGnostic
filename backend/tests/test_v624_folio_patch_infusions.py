"""V6.24 — folio PATCH + advancement infusion picker tests."""
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
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def test_character(gm_token):
    cs = requests.get(f"{BASE_URL}/api/campaigns", headers=H(gm_token)).json()
    dnd = next(c for c in cs if c["system_id"] == "dnd-5e" and c.get("is_gm"))
    payload = {
        "campaign_id": dnd["id"],
        "name": "V6.24 Folio Test",
        "system_id": "dnd-5e",
        "folio": {"dnd_state": {
            "level": 5, "class": "Artificer",
            "class_levels": {"Artificer": 5},
            "ability_scores": {"Strength": 10, "Dexterity": 10, "Constitution": 10,
                                "Intelligence": 14, "Wisdom": 10, "Charisma": 10},
            "spells_known": [{"name": "Fire Bolt", "level": 0}, "Mage Hand"],
        }},
    }
    r = requests.post(f"{BASE_URL}/api/characters", headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))


# ─── PATCH /folio mutator ──────────────────────────────────────────────


def test_patch_folio_persists_spell_prep(gm_token, test_character):
    r = requests.patch(
        f"{BASE_URL}/api/characters/{test_character}/folio",
        headers=H(gm_token),
        json={"bucket": "dnd_state", "patch": {"spells_prepared": ["Fire Bolt"]}},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # Verify GET round-trips.
    ch = requests.get(f"{BASE_URL}/api/characters/{test_character}",
                       headers=H(gm_token)).json()
    assert ch["folio"]["dnd_state"]["spells_prepared"] == ["Fire Bolt"]


def test_patch_folio_equip_weapon(gm_token, test_character):
    weapon = {"name": "Longsword", "damage": "1d8 slashing",
               "props": ["versatile (1d10)"], "category": "Martial"}
    r = requests.patch(
        f"{BASE_URL}/api/characters/{test_character}/folio",
        headers=H(gm_token),
        json={"bucket": "dnd_state", "patch": {"weapon_equipped": weapon}},
    )
    assert r.status_code == 200
    ch = requests.get(f"{BASE_URL}/api/characters/{test_character}",
                       headers=H(gm_token)).json()
    assert ch["folio"]["dnd_state"]["weapon_equipped"]["name"] == "Longsword"


def test_patch_folio_unequip(gm_token, test_character):
    r = requests.patch(
        f"{BASE_URL}/api/characters/{test_character}/folio",
        headers=H(gm_token),
        json={"bucket": "dnd_state", "patch": {"weapon_equipped": None}},
    )
    assert r.status_code == 200
    ch = requests.get(f"{BASE_URL}/api/characters/{test_character}",
                       headers=H(gm_token)).json()
    assert ch["folio"]["dnd_state"].get("weapon_equipped") is None


def test_patch_folio_404_on_missing_character(gm_token):
    r = requests.patch(
        f"{BASE_URL}/api/characters/does-not-exist/folio",
        headers=H(gm_token),
        json={"bucket": "dnd_state", "patch": {"spells_prepared": []}},
    )
    assert r.status_code == 404


# ─── Artificer infusion advancement ────────────────────────────────────


def test_artificer_infusions_surface_in_pending_advancements(gm_token, test_character):
    """At Artificer L5, the player should owe 4 known infusions."""
    r = requests.get(
        f"{BASE_URL}/api/characters/{test_character}/advancement",
        headers=H(gm_token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    pending = body.get("pending") or body.get("steps") or body
    infusion_steps = [s for s in pending if isinstance(s, dict) and s.get("kind") == "artificer_infusions"]
    assert len(infusion_steps) >= 1, f"No infusion step in pending: {pending}"
    step = infusion_steps[0]
    assert step["extra"]["known_count"] == 4
    assert step["extra"]["active_count"] == 2
    assert step["extra"]["owed"] == 4
    assert any(o["key"] == "Enhanced Weapon" for o in step["options"])
    assert any(o["key"] == "Replicate Magic Item" for o in step["options"])
    # Every option has a blurb so the picker can show descriptions
    # before the player commits.
    assert all(o["blurb"] for o in step["options"])


def test_artificer_infusion_pick_via_apply(gm_token, test_character):
    """Filing an infusion advancement should append to infusions_known."""
    r = requests.post(
        f"{BASE_URL}/api/characters/{test_character}/advancement/apply",
        headers=H(gm_token),
        json={"advancement_id": "infusions-4",
              "choice_key": "Enhanced Weapon",
              "pending": False},  # GM commit-now bypasses ticket queue
    )
    assert r.status_code == 200, r.text
    ch = requests.get(f"{BASE_URL}/api/characters/{test_character}",
                       headers=H(gm_token)).json()
    assert "Enhanced Weapon" in ch["folio"]["dnd_state"]["infusions_known"]


def test_anime5e_idol_armor_uses_cha_not_sol(gm_token):
    """V6.24 — armor reference uses 'CHA mod' (was 'SOL mod' which is
    not an Anime 5E ability score)."""
    r = requests.get(f"{BASE_URL}/api/systems/anime-5e/reference",
                      headers=H(gm_token))
    assert r.status_code == 200
    armor = r.json().get("armor", [])
    idol = next((a for a in armor if a.get("name") == "Idol Stage Garb"), None)
    assert idol is not None, "Idol Stage Garb missing from armor list"
    assert "SOL" not in (idol.get("ac") or "")
    assert "CHA" in (idol.get("ac") or "")
