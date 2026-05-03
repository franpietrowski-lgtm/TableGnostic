"""V6.23 — pin-to-pillar + Anime 5E DP server-side gate."""
from __future__ import annotations
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _anime_camp(tok):
    cs = requests.get(f"{BASE_URL}/api/campaigns", headers=H(tok)).json()
    return next(c for c in cs if c["system_id"] == "anime-5e" and c.get("is_gm"))


# ─── Pin-to-pillar (PATCH /codex-nodes/{nid}/place) ────────────────────


def test_patch_codex_node_place_endpoint_works(gm_token):
    camp = _anime_camp(gm_token)
    cid = camp["id"]
    # Find an existing untagged codex node (db.nodes).
    nodes = requests.get(f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                          headers=H(gm_token)).json()
    assert len(nodes) > 0
    target = nodes[0]
    # Pin to a different section.
    section = "Population.Factions"
    r = requests.patch(
        f"{BASE_URL}/api/campaigns/{cid}/codex-nodes/{target['id']}/place",
        headers=H(gm_token), json={"section": section},
    )
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True

    # Verify the tree reflects the new placement.
    tree = requests.get(f"{BASE_URL}/api/campaigns/{cid}/creation-tree",
                         headers=H(gm_token)).json()
    placed = tree["populated"].get(section, [])
    assert any(n["id"] == target["id"] for n in placed)


def test_patch_codex_node_place_404_on_missing(gm_token):
    camp = _anime_camp(gm_token)
    r = requests.patch(
        f"{BASE_URL}/api/campaigns/{camp['id']}/codex-nodes/does-not-exist/place",
        headers=H(gm_token), json={"section": "Geography.Locations"},
    )
    assert r.status_code == 404


# ─── Anime 5E DP server-side gate (POST/PUT /characters) ───────────────


def _make_anime_payload(camp_id: str, *, abilities: dict, race: str,
                          level: int = 1, point_buys=None,
                          gm_override: bool = False):
    return {
        "campaign_id": camp_id,
        "name": "DP Gate Tester",
        "system_id": "anime-5e",
        "folio": {
            "dnd_state": {
                "level": level,
                "race": race,
                "ability_scores": abilities,
                "class_levels": {"Fighter": level},
            },
            "anime5e_state": {
                "race": race,
                "point_buys": point_buys or [],
                "point_budget": 80 + (level - 1),
                "gm_dp_override": gm_override,
            },
        },
    }


def test_anime5e_dp_gate_blocks_overspend(gm_token):
    camp = _anime_camp(gm_token)
    # 6 × 18 = 108 ability cost + race human (7) = 115. Budget = 80.
    payload = _make_anime_payload(
        camp["id"],
        abilities={"Strength": 18, "Dexterity": 18, "Constitution": 18,
                    "Intelligence": 18, "Wisdom": 18, "Charisma": 18},
        race="human",
    )
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 400, r.text
    detail = r.json()["detail"]
    assert "DP overspend" in detail
    assert "115/80" in detail or "over by 35" in detail


def test_anime5e_dp_gate_passes_when_under_budget(gm_token):
    camp = _anime_camp(gm_token)
    # 6 × 12 = 72 ability cost + race fairy (4) = 76. Budget = 80. OK.
    payload = _make_anime_payload(
        camp["id"],
        abilities={"Strength": 12, "Dexterity": 12, "Constitution": 12,
                    "Intelligence": 12, "Wisdom": 12, "Charisma": 12},
        race="fairy",
    )
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    # Cleanup.
    requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))


def test_anime5e_dp_gate_allowed_with_gm_override(gm_token):
    camp = _anime_camp(gm_token)
    payload = _make_anime_payload(
        camp["id"],
        abilities={"Strength": 18, "Dexterity": 18, "Constitution": 18,
                    "Intelligence": 18, "Wisdom": 18, "Charisma": 18},
        race="human", gm_override=True,
    )
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))


def test_anime5e_dp_gate_does_not_apply_to_dnd_camps(gm_token):
    cs = requests.get(f"{BASE_URL}/api/campaigns", headers=H(gm_token)).json()
    dnd = next((c for c in cs if c["system_id"] == "dnd-5e" and c.get("is_gm")), None)
    if not dnd:
        pytest.skip("No D&D 5E GM campaign for tester.")
    payload = _make_anime_payload(
        dnd["id"],
        abilities={"Strength": 18, "Dexterity": 18, "Constitution": 18,
                    "Intelligence": 18, "Wisdom": 18, "Charisma": 18},
        race="human",
    )
    payload["system_id"] = "dnd-5e"
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    # System != anime-5e → gate is a no-op.
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))
