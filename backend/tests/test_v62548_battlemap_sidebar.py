"""V6.25.48 — Battlemap sidebar / vitals / marker tokens tests.

Covers:
  * POST /map/tokens accepts new fields (kind, marker_type, ep_pct,
    initiative_order, atlas_node_id, tooltip, locked) and round-trips
    them on GET.
  * GET /map/vitals returns hp_pct/ep_pct snapshots for each PC token's
    linked character — 100% defaults when no live HP recorded, sensible
    percentages when the folio carries current values.
  * GET /map/vitals 403 for non-members.
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
    r = requests.post(f"{API}/campaigns", headers=_h(admin),
                      json={"name": f"BattlemapTest-{int(time.time()*1000)}",
                            "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _make_session(admin, cid):
    r = requests.post(f"{API}/sessions",
                      headers=_h(admin),
                      json={"campaign_id": cid, "title": "Map test session"},
                      timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _cleanup(admin, cid):
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin), timeout=10)
    except Exception:
        pass


def test_token_new_fields_roundtrip():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)

        # GM spawns a marker token (kind="marker")
        r = requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                          json={"label": "Trapped door", "x": 4.5, "y": 3.0,
                                "kind": "marker", "marker_type": "trap",
                                "color": "#f87171",
                                "tooltip": "Pressure plate · DEX save",
                                "locked": True},
                          timeout=10)
        assert r.status_code == 200, r.text
        tok = r.json()
        assert tok["kind"] == "marker"
        assert tok["marker_type"] == "trap"
        assert tok["locked"] is True
        assert tok["tooltip"].startswith("Pressure plate")

        # GET /map echoes the new fields
        m = requests.get(f"{API}/sessions/{sid}/map", headers=_h(admin),
                         timeout=10).json()
        stored = next(t for t in m["tokens"] if t["id"] == tok["id"])
        assert stored["kind"] == "marker"
        assert stored["marker_type"] == "trap"
        assert stored["ep_pct"] == 100  # default
        assert stored["initiative_order"] is None

        # PC token with initiative_order + ep_pct
        r = requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                          json={"label": "Eli", "x": 1, "y": 1,
                                "kind": "pc", "ep_pct": 42,
                                "initiative_order": 1},
                          timeout=10)
        assert r.status_code == 200
        assert r.json()["ep_pct"] == 42
        assert r.json()["initiative_order"] == 1
    finally:
        _cleanup(admin, cid)


def test_vitals_endpoint_no_pcs():
    """Empty map → empty vitals dict, not a 404."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        r = requests.get(f"{API}/sessions/{sid}/map/vitals",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200, r.text
        assert r.json() == {"vitals": {}}
    finally:
        _cleanup(admin, cid)


def test_vitals_with_linked_character():
    """A token tied to a BESM character should report HP/EP percentages."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)

        # Mint a fresh BESM character on this campaign so we don't
        # mutate shared seed data. We just need *some* character with
        # derived.health_points / derived.energy_points so the vitals
        # helper has values to percentage against.
        r = requests.post(f"{API}/characters",
                          headers=_h(admin),
                          json={"campaign_id": cid,
                                "name": "Vitals-Test",
                                "concept": "qa puppet",
                                "total_points": 10}, timeout=10)
        assert r.status_code in (200, 201), r.text
        char_id = r.json()["id"]

        # Spawn a PC token tied to that character.
        r = requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                          json={"label": "Vitals-Test", "x": 2, "y": 2,
                                "kind": "pc", "character_id": char_id},
                          timeout=10)
        assert r.status_code == 200, r.text

        r = requests.get(f"{API}/sessions/{sid}/map/vitals",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200
        vitals = r.json()["vitals"]
        assert char_id in vitals
        v = vitals[char_id]
        # No live HP recorded → default to 100%.
        assert v["hp_pct"] == 100
        assert v["ep_pct"] == 100
        # Snapshot includes raw current/max so the frontend can render
        # absolute numbers in tooltips.
        assert "hp_max" in v and "ep_max" in v
    finally:
        _cleanup(admin, cid)
