"""V6.25.13 — Item-Container reference round-trip + GM materials queue
end-to-end (already exercised by V6.25.12, but extended here for the
new approval queue UI).
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_reference_item_round_trips_with_item_contents():
    """An `item` reference row with a nested `item_contents` array must
    round-trip through the Reference Editor's POST/GET endpoints. The
    backend stores `fields` as Dict[str, Any], so the nested attribute
    list is preserved verbatim — the V6.25.13 ReferenceEditor UI relies
    on this for the Mecha pattern."""
    gm = _gm_token()

    # Spin up a BESM campaign for the test.
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": "V62513 Item Container", "system_id": "besm-4e"})
    assert cp.status_code == 200, cp.text
    cid = cp.json()["id"]
    try:
        # Compose an item with nested contents (Mecha pattern, p.219).
        body = {
            "kind": "item",
            "name": "V62513 Pocket Workshop",
            "summary": "Item ×4 carrying nested attributes.",
            "fields": {
                "level": 4,
                "cost_per_level": 1,
                "also_an_item": True,
                "enhancements": [],
                "limiters": [],
                "item_contents": [
                    {"name": "Weapon", "level": 2, "cost_per_level": 2,
                     "note": "compact crafting tool"},
                    {"name": "Sensors", "level": 1, "cost_per_level": 2, "note": ""},
                ],
                "description": "Demo item for the Mecha pattern.",
            },
        }
        rp = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/reference",
            headers=H(gm), json=body)
        assert rp.status_code == 200, rp.text
        rid = rp.json()["id"]

        # Fetch back via the campaign reference list.
        rl = requests.get(f"{BASE_URL}/api/campaigns/{cid}/reference",
                           headers=H(gm))
        assert rl.status_code == 200
        match = next((r for r in rl.json() if r["id"] == rid), None)
        assert match is not None, "reference row missing on read-back"
        f = match["fields"]
        assert f["also_an_item"] is True
        assert f["level"] == 4
        contents = f.get("item_contents") or []
        assert len(contents) == 2
        names = {c["name"] for c in contents}
        assert names == {"Weapon", "Sensors"}
        wpn = next(c for c in contents if c["name"] == "Weapon")
        assert wpn["level"] == 2
        assert wpn["cost_per_level"] == 2
        assert wpn["note"] == "compact crafting tool"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_gm_can_reject_pending_material_ticket():
    """Reject path is exercised end-to-end so the GM Approval Queue UI
    has a verified backend contract for the X / reject button."""
    gm = _gm_token()
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": "V62513 Reject Demo", "system_id": "besm-4e"})
    cid = cp.json()["id"]
    try:
        # GM submits a ticket (GMs are also on roster).
        sub = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/materials-queue",
            headers=H(gm),
            json={"name": "Cursed Bone", "node_kind": "byproduct"})
        assert sub.status_code == 200, sub.text
        tid = sub.json()["id"]

        # GM rejects.
        rej = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/materials-queue/{tid}/reject",
            headers=H(gm))
        assert rej.status_code == 200, rej.text

        # The ticket no longer surfaces under the pending filter.
        pend = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/materials-queue?status=pending",
            headers=H(gm))
        assert pend.status_code == 200
        assert all(t["id"] != tid for t in pend.json())

        # Re-rejecting yields 404 (already resolved).
        again = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/materials-queue/{tid}/reject",
            headers=H(gm))
        assert again.status_code == 404
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))
