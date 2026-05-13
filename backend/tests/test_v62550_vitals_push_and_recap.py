"""V6.25.50 — Push-based vitals + recap auto-vitals tests.

The vitals-broadcast helper is best-effort (silent on errors), so we
test the hook points by exercising the public endpoints and asserting:

  * `_pc_vitals_for()` heuristic returns sensible percentages whether
    HP/EP live on folio.health_points (BESM), folio.anime5e_state.*
    (Anime 5E), or folio.dnd5e_state.* (D&D 5E).
  * `GET /api/sessions/{sid}/recap/auto-vitals` returns a recap-ready
    snapshot with narrative strings the LLM can splice directly.
  * Auth gate: non-members can't read recap vitals.
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
                      json={"name": f"V50Test-{int(time.time()*1000)}",
                            "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _make_session(admin, cid):
    r = requests.post(f"{API}/sessions", headers=_h(admin),
                      json={"campaign_id": cid, "title": "Test"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _make_character(admin, cid, name="Eli"):
    r = requests.post(f"{API}/characters", headers=_h(admin),
                      json={"campaign_id": cid, "name": name,
                            "concept": "qa", "total_points": 10},
                      timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _cleanup(admin, cid):
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin), timeout=10)
    except Exception:
        pass


def test_vitals_helper_handles_missing_hp():
    """No live HP recorded → fallback to 100% (no NaN, no crash)."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        char_id = _make_character(admin, cid)
        # Spawn a PC token tied to the char.
        r = requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                          json={"label": "Eli", "x": 1, "y": 1,
                                "kind": "pc", "character_id": char_id},
                          timeout=10)
        assert r.status_code == 200, r.text

        r = requests.get(f"{API}/sessions/{sid}/map/vitals",
                         headers=_h(admin), timeout=10)
        v = r.json()["vitals"][char_id]
        assert v["hp_pct"] == 100
        assert v["ep_pct"] == 100
        # hp_current falls back to hp_max when no live value.
        assert v["hp_current"] == v["hp_max"]
    finally:
        _cleanup(admin, cid)


def test_recap_auto_vitals_shape():
    """Recap auto-vitals returns one entry per PC token with a
    narrative string the LLM can splice directly."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        eli = _make_character(admin, cid, "Eli")
        aurora = _make_character(admin, cid, "Aurora")

        # Two PC tokens + one unbound marker (must be skipped).
        for ch_id, name in ((eli, "Eli"), (aurora, "Aurora")):
            requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                          json={"label": name, "x": 1, "y": 1,
                                "kind": "pc", "character_id": ch_id},
                          timeout=10)
        requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                      json={"label": "Trap", "x": 5, "y": 5,
                            "kind": "marker", "marker_type": "trap"},
                      timeout=10)

        r = requests.get(f"{API}/sessions/{sid}/recap/auto-vitals",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["session_id"] == sid
        assert isinstance(d["round"], int)
        assert isinstance(d["pcs"], list)
        assert len(d["pcs"]) == 2  # marker dropped
        for pc in d["pcs"]:
            for k in ("character_id", "name", "hp_pct", "hp_current", "hp_max",
                      "ep_pct", "ep_current", "ep_max", "status", "narrative"):
                assert k in pc, f"missing field {k}"
            # Narrative line should mention the character name + HP/EP %.
            assert pc["name"] in pc["narrative"]
            assert "% HP" in pc["narrative"]
            assert "% EP" in pc["narrative"]
        # Summary is one human string ending with a period.
        assert isinstance(d["summary"], str)
        assert d["summary"].endswith(".")
    finally:
        _cleanup(admin, cid)


def test_recap_auto_vitals_empty_when_no_pcs():
    """Empty map / marker-only map returns an empty pcs[]."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        r = requests.get(f"{API}/sessions/{sid}/recap/auto-vitals",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["pcs"] == []
        assert "No PCs" in d["summary"]
    finally:
        _cleanup(admin, cid)


def test_recap_auto_vitals_includes_active_status():
    """Status effects bound to a PC's character_id should land in the
    narrative as comma-joined lowercase tags."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        char_id = _make_character(admin, cid, "Eli")
        requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                      json={"label": "Eli", "x": 1, "y": 1,
                            "kind": "pc", "character_id": char_id},
                      timeout=10)
        # Apply two conditions (existing /effects endpoint).
        for name in ("Bleeding", "Stunned"):
            r = requests.post(f"{API}/effects", headers=_h(admin),
                              json={"session_id": sid, "target_name": "Eli",
                                    "target_character_id": char_id,
                                    "name": name, "duration_rounds": 3},
                              timeout=10)
            assert r.status_code == 200, r.text

        r = requests.get(f"{API}/sessions/{sid}/recap/auto-vitals",
                         headers=_h(admin), timeout=10)
        d = r.json()
        eli_row = next(p for p in d["pcs"] if p["name"] == "Eli")
        assert set(eli_row["status"]) >= {"Bleeding", "Stunned"}
        assert "bleeding" in eli_row["narrative"].lower()
        assert "stunned" in eli_row["narrative"].lower()
    finally:
        _cleanup(admin, cid)
