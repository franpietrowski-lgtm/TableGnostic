"""V6.25.20 — Classifier wired into POST /api/nodes + PUT /api/nodes/{nid}.

The legacy NodeIn shape (`type + title + content`) is now transparently
lifted into the V6.25.19 unified shape (`name + node_kind +
creation_tree.section`) on every mutation. Manual pins authored via
PATCH /codex-nodes/{nid}/place are NEVER re-classified.
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _gm():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200
    return r.json()["access_token"]


def _spin(gm, name="V62520 Demo"):
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": name, "system_id": "anime-5e"})
    return cp.json()["id"]


def test_post_nodes_runs_classifier_for_legacy_shape():
    """A legacy POST /nodes with `type='concept'` and a name that
    matches a regex pattern (e.g. 'Empire of the Eternal Sun') must
    land in Geography.Countries on the World Tree."""
    gm = _gm()
    cid = _spin(gm, "V62520 POST classifier")
    try:
        rs = requests.post(
            f"{BASE_URL}/api/nodes", headers=H(gm),
            json={
                "campaign_id": cid,
                "type": "concept",
                "title": "Empire of the Eternal Sun",
                "content": "A vast solar empire on the eastern continent.",
            })
        assert rs.status_code == 200, rs.text
        body = rs.json()
        # Classifier output must be on the persisted row.
        assert body["node_kind"] == "country"
        assert body["name"] == "Empire of the Eternal Sun"
        ct = body.get("creation_tree") or {}
        assert ct.get("section") == "Geography.Countries"
        assert ct.get("auto_classified") is True
        assert ct.get("classifier_confidence") and ct["classifier_confidence"] > 0

        # World Tree picks it up immediately.
        tree = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/creation-tree",
            headers=H(gm)).json()
        names = {n["name"] for n in tree["populated"].get("Geography.Countries", [])}
        assert "Empire of the Eternal Sun" in names
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_put_nodes_reclassifies_when_title_changes():
    """Create a node with one name → classifier picks kind A. Edit
    the title to a new pattern → classifier picks kind B (because
    the original placement was auto)."""
    gm = _gm()
    cid = _spin(gm, "V62520 PUT classifier")
    try:
        # Step 1 — create with a faction-flavoured name.
        rs = requests.post(
            f"{BASE_URL}/api/nodes", headers=H(gm),
            json={
                "campaign_id": cid,
                "type": "concept",
                "title": "The Brotherhood of Iron",
                "content": "",
            })
        body = rs.json()
        nid = body["id"]
        assert body["node_kind"] == "faction"
        assert body["creation_tree"]["section"] == "Population.Factions"

        # Step 2 — rename to a country-flavoured title via PUT.
        rs2 = requests.put(
            f"{BASE_URL}/api/nodes/{nid}", headers=H(gm),
            json={
                "campaign_id": cid,
                "type": "concept",
                "title": "Republic of the Iron Coast",
                "content": "",
            })
        assert rs2.status_code == 200
        body2 = rs2.json()
        assert body2["node_kind"] == "country"
        assert body2["creation_tree"]["section"] == "Geography.Countries"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_put_nodes_respects_manual_pin():
    """When a GM has manually pinned a node via PATCH .../place, a
    subsequent PUT /nodes/{nid} must NOT re-classify — the manual
    placement is sacrosanct."""
    gm = _gm()
    cid = _spin(gm, "V62520 manual pin")
    try:
        # Step 1 — create a node that auto-classifies into Factions.
        rs = requests.post(
            f"{BASE_URL}/api/nodes", headers=H(gm),
            json={
                "campaign_id": cid, "type": "concept",
                "title": "The Brotherhood of Iron", "content": "",
            })
        nid = rs.json()["id"]

        # Step 2 — GM manually pins it to History.Of the People.
        pin = requests.patch(
            f"{BASE_URL}/api/campaigns/{cid}/codex-nodes/{nid}/place",
            headers=H(gm),
            json={"section": "History.Of the People"})
        assert pin.status_code == 200, pin.text

        # Step 3 — GM edits the title (which would normally re-route).
        rs2 = requests.put(
            f"{BASE_URL}/api/nodes/{nid}", headers=H(gm),
            json={
                "campaign_id": cid, "type": "concept",
                "title": "Republic of the Iron Coast",  # would route to Geography.Countries
                "content": "",
            })
        assert rs2.status_code == 200
        body2 = rs2.json()
        # Manual pin honoured — section unchanged.
        assert body2["creation_tree"]["section"] == "History.Of the People", \
            f"manual pin lost: {body2['creation_tree']}"
        # auto_classified must still be False (we set it on pin).
        assert body2["creation_tree"].get("auto_classified") is False
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_post_nodes_caller_hint_wins_over_regex():
    """The caller's `type` hint (when canonical) wins over the regex
    layer — important so the legacy editor's explicit `type` choice
    is never silently overridden by name pattern matching."""
    gm = _gm()
    cid = _spin(gm, "V62520 hint over regex")
    try:
        rs = requests.post(
            f"{BASE_URL}/api/nodes", headers=H(gm),
            json={
                "campaign_id": cid,
                "type": "lore",  # caller insists this is lore
                "title": "The Brotherhood of Iron",  # regex would pick faction
                "content": "",
                "fields": {},
            })
        body = rs.json()
        # Hint wins — lore stays.
        assert body["node_kind"] == "lore"
        assert body["creation_tree"]["section"] == "History.Of the People"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))
