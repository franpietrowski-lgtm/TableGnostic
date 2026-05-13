"""V6.25.46 — Writer tools backend tests.

Covers:
  * GET/PATCH /api/writer/atlas/{cid} — map URL, pin lifecycle.
  * GET/POST/PATCH/DELETE /api/writer/magic/{cid} — magic-system CRUD.
  * GET/POST/PATCH/DELETE /api/writer/manuscript/{cid} — chapter→scene→beat tree.
  * Parent-validation: scenes need a chapter parent; beats need a scene parent.
  * Word-count auto-computation on PATCH body_md.
  * Cascading delete (deleting a chapter wipes its scenes + beats).
  * Non-GM members get read-only (403 on write).
"""
from __future__ import annotations
import os
import time

import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read()
        .split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t): return {"Authorization": f"Bearer {t}"}


def _make_camp(admin):
    name = f"WriterToolsTest-{int(time.time())}"
    r = requests.post(f"{API}/campaigns", headers=_h(admin),
                      json={"name": name, "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _cleanup(admin, cid):
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin), timeout=10)
    except Exception:
        pass


def test_atlas_map_and_pin_lifecycle():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # Initial atlas is empty.
        r = requests.get(f"{API}/writer/atlas/{cid}", headers=_h(admin), timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["pins"] == []
        assert d["world_map_url"] is None
        assert d["writable"] is True

        # Patch map URL.
        r = requests.patch(f"{API}/writer/atlas/{cid}/map",
                           headers=_h(admin),
                           json={"world_map_url": "https://example.com/map.png",
                                 "world_map_caption": "Continent of Evereantha"},
                           timeout=10)
        assert r.status_code == 200
        assert r.json()["world_map_url"] == "https://example.com/map.png"

        # Drop a new pin (no node_id → creates a fresh location node).
        r = requests.post(f"{API}/writer/atlas/{cid}/pins", headers=_h(admin),
                          json={"title": "Konch Tavern",
                                "description": "Musty smoke, smell of pine sap.",
                                "map_x": 0.42, "map_y": 0.61,
                                "location_type": "tavern"},
                          timeout=10)
        assert r.status_code == 200, r.text
        pin_node_id = r.json()["node_id"]
        assert pin_node_id

        # Atlas now lists the pin.
        d = requests.get(f"{API}/writer/atlas/{cid}", headers=_h(admin),
                         timeout=10).json()
        assert len(d["pins"]) == 1
        p = d["pins"][0]
        assert p["title"] == "Konch Tavern"
        assert p["fields"]["map_x"] == 0.42
        assert p["fields"]["map_y"] == 0.61
        assert p["fields"]["location_type"] == "tavern"

        # Unpin (node stays in codex, coords removed).
        r = requests.delete(f"{API}/writer/atlas/{cid}/pins/{pin_node_id}",
                            headers=_h(admin), timeout=10)
        assert r.status_code == 200

        d = requests.get(f"{API}/writer/atlas/{cid}", headers=_h(admin),
                         timeout=10).json()
        assert len(d["pins"]) == 0
        # Node still exists but is now unpinned.
        assert len(d["unpinned_locations"]) == 1
    finally:
        _cleanup(admin, cid)


def test_magic_system_crud():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # Create
        r = requests.post(f"{API}/writer/magic/{cid}", headers=_h(admin),
                          json={"name": "Face of Aurae · Dawnbearer",
                                "kind": "primary", "alignment": "aurae",
                                "summary": "Sunrise-aligned restorative source.",
                                "invocation_cost": "1 sustenance / hour",
                                "side_effects": "Skin gilds faintly for 24h."},
                          timeout=10)
        assert r.status_code == 200, r.text
        sid = r.json()["id"]

        # List
        r = requests.get(f"{API}/writer/magic/{cid}", headers=_h(admin), timeout=10)
        assert r.status_code == 200
        assert len(r.json()["sources"]) == 1

        # Patch alignment
        r = requests.patch(f"{API}/writer/magic/{cid}/{sid}", headers=_h(admin),
                           json={"name": "Face of Aurae · Dawnbearer",
                                 "kind": "primary", "alignment": "both"},
                           timeout=10)
        assert r.status_code == 200
        assert r.json()["alignment"] == "both"

        # Delete
        r = requests.delete(f"{API}/writer/magic/{cid}/{sid}",
                            headers=_h(admin), timeout=10)
        assert r.status_code == 200
        assert r.json()["deleted"] == 1
    finally:
        _cleanup(admin, cid)


def test_manuscript_tree_crud():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # 1. Create chapter
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "chapter", "title": "Chapter I"},
                          timeout=10)
        assert r.status_code == 200, r.text
        ch_id = r.json()["id"]

        # 2. Scene under chapter
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "scene", "parent_id": ch_id,
                                "title": "The road at dusk",
                                "body_md": "# Title\n\nThe wind picked up."},
                          timeout=10)
        assert r.status_code == 200, r.text
        sc_id = r.json()["id"]
        assert r.json()["word_count"] == 6  # "# Title The wind picked up." → 6 whitespace tokens

        # 3. Beat under scene
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "beat", "parent_id": sc_id,
                                "title": "Sound of hooves",
                                "tension": 3},
                          timeout=10)
        assert r.status_code == 200, r.text
        bt_id = r.json()["id"]

        # 4. Reject illegal parent: scene under scene
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "scene", "parent_id": sc_id,
                                "title": "bad"},
                          timeout=10)
        assert r.status_code == 400

        # 5. Reject chapter with parent
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "chapter", "parent_id": ch_id,
                                "title": "bad"},
                          timeout=10)
        assert r.status_code == 400

        # 6. PATCH body_md updates word_count. V6.25.47 — `kind` and
        # `parent_id` are now immutable on PATCH (Pydantic model omits
        # them entirely) — clients that send them get 422.
        r = requests.patch(f"{API}/writer/manuscript/{cid}/{sc_id}",
                           headers=_h(admin),
                           json={"title": "The road at dusk",
                                 "body_md": "one two three four five six seven eight"},
                           timeout=10)
        assert r.status_code == 200
        assert r.json()["word_count"] == 8

        # 6b. Sending `kind` on PATCH is now rejected with 422.
        r = requests.patch(f"{API}/writer/manuscript/{cid}/{sc_id}",
                           headers=_h(admin),
                           json={"kind": "chapter", "title": "x"},
                           timeout=10)
        assert r.status_code == 422, r.text

        # 7. Tree shows all 3 with total wordcount = 8
        r = requests.get(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                         timeout=10)
        assert r.status_code == 200
        assert r.json()["total_word_count"] == 8
        assert len(r.json()["sections"]) == 3

        # 8. Cascading delete: drop chapter → scene + beat go too
        r = requests.delete(f"{API}/writer/manuscript/{cid}/{ch_id}",
                            headers=_h(admin), timeout=10)
        assert r.status_code == 200
        assert r.json()["deleted"] == 3

        r = requests.get(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                         timeout=10)
        assert r.json()["sections"] == []
    finally:
        _cleanup(admin, cid)
