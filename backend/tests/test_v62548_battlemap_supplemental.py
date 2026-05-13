"""V6.25.48 — supplemental tests.

Covers gaps not in test_v62548_battlemap_sidebar.py:
  * /map/vitals returns 403 for non-members.
  * Existing token PATCH/DELETE still works after schema bump.
  * Marker tokens with all curated marker_type values round-trip cleanly.
"""
from __future__ import annotations
import os
import time
import uuid

import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read()
        .split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"

MARKER_TYPES = ["door", "trap", "treasure", "chest",
                "stairs", "portal", "ladder", "note"]


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t): return {"Authorization": f"Bearer {t}"}


def _make_camp(admin):
    r = requests.post(f"{API}/campaigns", headers=_h(admin),
                      json={"name": f"BMS-{int(time.time()*1000)}",
                            "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _make_session(admin, cid):
    r = requests.post(f"{API}/sessions", headers=_h(admin),
                      json={"campaign_id": cid, "title": "Map test"},
                      timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _register_outsider():
    suffix = uuid.uuid4().hex[:8]
    email = f"v62548-outsider-{suffix}@example.com"
    pw = "OutsiderPass123!"
    r = requests.post(f"{API}/auth/register",
                      json={"email": email, "password": pw,
                            "name": "Outsider"}, timeout=10)
    if r.status_code not in (200, 201):
        return None
    return _login(email, pw)


def _cleanup(admin, cid):
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin), timeout=10)
    except Exception:
        pass


def test_vitals_non_member_403():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        outsider = _register_outsider()
        if outsider is None:
            import pytest
            pytest.skip("registration endpoint unavailable")
        r = requests.get(f"{API}/sessions/{sid}/map/vitals",
                         headers=_h(outsider), timeout=10)
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text}"
    finally:
        _cleanup(admin, cid)


def test_marker_palette_all_types_roundtrip():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        ids = {}
        for mt in MARKER_TYPES:
            r = requests.post(f"{API}/sessions/{sid}/map/tokens",
                              headers=_h(admin),
                              json={"label": mt.title(), "x": 1, "y": 1,
                                    "kind": "marker", "marker_type": mt},
                              timeout=10)
            assert r.status_code == 200, f"{mt}: {r.text}"
            ids[mt] = r.json()["id"]
            assert r.json()["marker_type"] == mt

        m = requests.get(f"{API}/sessions/{sid}/map",
                         headers=_h(admin), timeout=10).json()
        present = {t["marker_type"] for t in m["tokens"]
                   if t.get("kind") == "marker"}
        for mt in MARKER_TYPES:
            assert mt in present, f"missing marker_type={mt} after GET"
    finally:
        _cleanup(admin, cid)


def test_token_patch_and_delete_still_work():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        r = requests.post(f"{API}/sessions/{sid}/map/tokens",
                          headers=_h(admin),
                          json={"label": "Eli", "x": 1, "y": 1, "kind": "pc"},
                          timeout=10)
        assert r.status_code == 200
        tid = r.json()["id"]

        # POST upsert acts as PATCH (id present → update)
        r = requests.post(f"{API}/sessions/{sid}/map/tokens",
                          headers=_h(admin),
                          json={"id": tid, "label": "Eli", "x": 5.5, "y": 6.5,
                                "kind": "pc"}, timeout=10)
        assert r.status_code == 200, r.text

        m = requests.get(f"{API}/sessions/{sid}/map",
                         headers=_h(admin), timeout=10).json()
        tok = next(t for t in m["tokens"] if t["id"] == tid)
        assert abs(tok["x"] - 5.5) < 0.01
        assert abs(tok["y"] - 6.5) < 0.01

        # DELETE
        r = requests.delete(f"{API}/sessions/{sid}/map/tokens/{tid}",
                            headers=_h(admin), timeout=10)
        assert r.status_code in (200, 204)
        m = requests.get(f"{API}/sessions/{sid}/map",
                         headers=_h(admin), timeout=10).json()
        assert all(t["id"] != tid for t in m["tokens"])
    finally:
        _cleanup(admin, cid)
