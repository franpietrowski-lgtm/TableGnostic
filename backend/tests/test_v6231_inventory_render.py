"""V6.23.1 — CharacterSheet inventory render regression test.

Regression for bug: picking a weapon via ReferencePicker added a rich
object (`{name, kind, damage, props, __kind}`) to the inventory array.
The inventory panel on the character sheet rendered items with bare
`· {it}` and crashed with "Objects are not valid as a React child"
when React met the dict.

Covered here: the backend POST+GET round-trip preserves the rich
object shape (no crash; no silent string coercion).
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


def test_rich_inventory_object_persisted_round_trip(gm_token):
    """The character POST/GET should preserve rich picker objects as-is."""
    cs = requests.get(f"{BASE_URL}/api/campaigns", headers=H(gm_token)).json()
    dnd = next((c for c in cs if c["system_id"] == "dnd-5e" and c.get("is_gm")), None)
    if not dnd:
        pytest.skip("No D&D 5E GM campaign for tester.")

    payload = {
        "campaign_id": dnd["id"],
        "name": "V6231 InventoryRegression",
        "system_id": "dnd-5e",
        "folio": {
            "dnd_state": {
                "level": 1,
                "class_levels": {"Fighter": 1},
                "ability_scores": {
                    "Strength": 10, "Dexterity": 10, "Constitution": 10,
                    "Intelligence": 10, "Wisdom": 10, "Charisma": 10,
                },
                "inventory": [
                    # Rich picker entry (weapon)
                    {"name": "Longsword", "kind": "Martial Melee",
                     "damage": "1d8 slashing",
                     "props": ["versatile (1d10)"], "__kind": "weapons"},
                    # Legacy plain-string entry
                    "Backpack",
                    # Rich picker entry (armor)
                    {"name": "Chain Mail", "category": "Heavy",
                     "base_ac": 16, "__kind": "armor"},
                ],
                "spells_known": [
                    {"name": "Fire Bolt", "level": 0,
                     "school": "Evocation", "__kind": "spells"},
                ],
            },
        },
    }
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    try:
        ch = requests.get(f"{BASE_URL}/api/characters/{cid}",
                            headers=H(gm_token)).json()
        inv = ch["folio"]["dnd_state"]["inventory"]
        assert len(inv) == 3
        # Position 0 is the picker object — shape preserved.
        assert isinstance(inv[0], dict)
        assert inv[0]["name"] == "Longsword"
        assert inv[0]["damage"] == "1d8 slashing"
        assert inv[0]["props"] == ["versatile (1d10)"]
        assert inv[0]["__kind"] == "weapons"
        # Position 1 is the legacy string — preserved as string.
        assert inv[1] == "Backpack"
        # Position 2 is the armor dict.
        assert isinstance(inv[2], dict)
        assert inv[2]["name"] == "Chain Mail"

        spells = ch["folio"]["dnd_state"]["spells_known"]
        assert isinstance(spells[0], dict)
        assert spells[0]["name"] == "Fire Bolt"
        assert spells[0]["level"] == 0
    finally:
        requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))
