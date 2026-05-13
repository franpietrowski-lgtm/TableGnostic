"""V6.25.47 — Backend tests for the 4 remaining writer tools promoted
from scaffold to real CRUD endpoints:

  * cultures     — flat list, free-form fields.
  * cosmology    — multi-kind ledger (planar_layer, calendar_month,
                   cosmic_event, omen, celestial_body).
  * pov-bibles   — flat list, voice/want/need/wound fields.
  * themes       — two-kind ledger (theme | motif).

Covers happy-path CRUD, kind-enum enforcement, and `extra="forbid"`
rejection of unknown fields on PATCH.
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
    name = f"WriterToolsTest47-{int(time.time()*1000)}"
    r = requests.post(f"{API}/campaigns", headers=_h(admin),
                      json={"name": name, "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _cleanup(admin, cid):
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin), timeout=10)
    except Exception:
        pass


# ----------------------------------------------------------------------
# CULTURES
# ----------------------------------------------------------------------

def test_cultures_crud_and_strict_fields():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # Empty list
        r = requests.get(f"{API}/writer/cultures/{cid}", headers=_h(admin), timeout=10)
        assert r.status_code == 200
        assert r.json()["cultures"] == []
        assert r.json()["writable"] is True

        # Create
        r = requests.post(f"{API}/writer/cultures/{cid}", headers=_h(admin),
                          json={"name": "Aurelian Confederation",
                                "summary": "Sun-touched merchant hegemony.",
                                "naming_conventions": "Patronymic, with -ven suffix."},
                          timeout=10)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]

        # List shows it
        rows = requests.get(f"{API}/writer/cultures/{cid}", headers=_h(admin),
                            timeout=10).json()["cultures"]
        assert len(rows) == 1
        assert rows[0]["name"] == "Aurelian Confederation"

        # Patch
        r = requests.patch(f"{API}/writer/cultures/{cid}/{rid}", headers=_h(admin),
                           json={"name": "Aurelian Confederation",
                                 "holidays": "Solstice of the First Coin."},
                           timeout=10)
        assert r.status_code == 200
        assert r.json()["holidays"].startswith("Solstice")

        # Unknown field rejected (extra=forbid)
        r = requests.patch(f"{API}/writer/cultures/{cid}/{rid}", headers=_h(admin),
                           json={"name": "Aurelian Confederation",
                                 "bogus_field": "no"},
                           timeout=10)
        assert r.status_code == 422, r.text

        # Delete
        r = requests.delete(f"{API}/writer/cultures/{cid}/{rid}",
                            headers=_h(admin), timeout=10)
        assert r.status_code == 200
        assert r.json()["deleted"] == 1
    finally:
        _cleanup(admin, cid)


# ----------------------------------------------------------------------
# COSMOLOGY
# ----------------------------------------------------------------------

def test_cosmology_kind_enum_and_grouping():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # Reject bad kind
        r = requests.post(f"{API}/writer/cosmology/{cid}", headers=_h(admin),
                          json={"kind": "bogus", "name": "Nope"}, timeout=10)
        assert r.status_code == 400

        # Create one of each accepted kind
        kinds = ["planar_layer", "calendar_month", "cosmic_event",
                 "omen", "celestial_body"]
        ids = []
        for k in kinds:
            r = requests.post(f"{API}/writer/cosmology/{cid}", headers=_h(admin),
                              json={"kind": k, "name": f"{k}-sample",
                                    "summary": f"sample {k}"}, timeout=10)
            assert r.status_code == 200, r.text
            ids.append(r.json()["id"])

        # List → 5 entries, sorted by kind then order
        rows = requests.get(f"{API}/writer/cosmology/{cid}", headers=_h(admin),
                            timeout=10).json()["entries"]
        assert len(rows) == 5
        # Auto-assigned order is 10 for each (one per kind bucket).
        assert all(r["order"] == 10 for r in rows)

        # Patch first entry's summary
        r = requests.patch(f"{API}/writer/cosmology/{cid}/{ids[0]}", headers=_h(admin),
                           json={"kind": "planar_layer",
                                 "name": "planar_layer-sample",
                                 "summary": "now-updated"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["summary"] == "now-updated"

        # Patch with bad kind rejected
        r = requests.patch(f"{API}/writer/cosmology/{cid}/{ids[0]}", headers=_h(admin),
                           json={"kind": "garbage", "name": "x"}, timeout=10)
        assert r.status_code == 400
    finally:
        _cleanup(admin, cid)


# ----------------------------------------------------------------------
# POV BIBLES
# ----------------------------------------------------------------------

def test_pov_bibles_full_field_roundtrip():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        r = requests.post(f"{API}/writer/pov-bibles/{cid}", headers=_h(admin),
                          json={"name": "Calenwë the Quiet",
                                "voice_quirks": "Speaks in half-finished thoughts.",
                                "want": "Reclaim the Aurelian sigil.",
                                "need": "Forgive the brother who broke it.",
                                "wound": "Watched the sigil shatter in a winter pond."},
                          timeout=10)
        assert r.status_code == 200, r.text
        rid = r.json()["id"]
        assert r.json()["wound"].startswith("Watched")

        # List
        rows = requests.get(f"{API}/writer/pov-bibles/{cid}", headers=_h(admin),
                            timeout=10).json()["bibles"]
        assert len(rows) == 1

        # Patch
        r = requests.patch(f"{API}/writer/pov-bibles/{cid}/{rid}", headers=_h(admin),
                           json={"name": "Calenwë the Quiet",
                                 "gait": "Walks heel-first like a cat."}, timeout=10)
        assert r.status_code == 200
        assert r.json()["gait"].startswith("Walks")

        # Unknown field → 422
        r = requests.patch(f"{API}/writer/pov-bibles/{cid}/{rid}", headers=_h(admin),
                           json={"name": "x", "trojan_horse": "evil"}, timeout=10)
        assert r.status_code == 422
    finally:
        _cleanup(admin, cid)


# ----------------------------------------------------------------------
# THEMES & MOTIFS
# ----------------------------------------------------------------------

def test_themes_motifs_kind_enum():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # Create a theme and a motif
        r1 = requests.post(f"{API}/writer/themes/{cid}", headers=_h(admin),
                           json={"kind": "theme",
                                 "name": "Mercy outlives memory",
                                 "intent": "Argue mercy is structural."},
                           timeout=10)
        assert r1.status_code == 200, r1.text
        tid = r1.json()["id"]

        r2 = requests.post(f"{API}/writer/themes/{cid}", headers=_h(admin),
                           json={"kind": "motif", "name": "Broken bell",
                                 "cadence": "accelerating"}, timeout=10)
        assert r2.status_code == 200, r2.text

        # Reject bad kind on POST
        r = requests.post(f"{API}/writer/themes/{cid}", headers=_h(admin),
                          json={"kind": "leitmotif", "name": "bad"}, timeout=10)
        assert r.status_code == 400

        # List shows both
        rows = requests.get(f"{API}/writer/themes/{cid}", headers=_h(admin),
                            timeout=10).json()["items"]
        assert len(rows) == 2

        # Patch a theme's cadence
        r = requests.patch(f"{API}/writer/themes/{cid}/{tid}", headers=_h(admin),
                           json={"kind": "theme",
                                 "name": "Mercy outlives memory",
                                 "cadence": "climactic"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["cadence"] == "climactic"

        # Reject bad kind on PATCH
        r = requests.patch(f"{API}/writer/themes/{cid}/{tid}", headers=_h(admin),
                           json={"kind": "fugue", "name": "x"}, timeout=10)
        assert r.status_code == 400
    finally:
        _cleanup(admin, cid)
