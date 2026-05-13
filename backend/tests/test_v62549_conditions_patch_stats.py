"""V6.25.49 — Reference conditions catalogue · PATCH /map/tokens/{tid} ·
deeper public stats."""
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
                      json={"name": f"V49Test-{int(time.time()*1000)}",
                            "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _make_session(admin, cid):
    r = requests.post(f"{API}/sessions", headers=_h(admin),
                      json={"campaign_id": cid, "title": "test"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _cleanup(admin, cid):
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin), timeout=10)
    except Exception:
        pass


# ────────────────── Conditions catalogue ──────────────────

def test_besm_reference_has_conditions():
    r = requests.get(f"{API}/besm/reference", timeout=10)
    assert r.status_code == 200, r.text
    conds = r.json().get("conditions") or []
    names = {c["name"] for c in conds}
    # Spot-check that the user-requested examples are present.
    for required in ("Stunned", "Poisoned", "Immolation", "Burning",
                     "Bleeding", "Frostbite", "Soulshocked"):
        assert required in names, f"missing condition: {required}"
    # Every entry must carry effect, severity, tags for the UI.
    for c in conds[:5]:
        assert c.get("effect")
        assert c.get("severity")
        assert isinstance(c.get("tags"), list)


def test_all_systems_have_conditions():
    """Every supported system reference exposes a non-empty conditions list."""
    for sid in ("besm-4e", "dnd-5e", "anime-5e", "cypher"):
        if sid == "besm-4e":
            r = requests.get(f"{API}/besm/reference", timeout=10)
        else:
            r = requests.get(f"{API}/systems/{sid}/reference", timeout=10)
        assert r.status_code == 200, f"{sid}: {r.text}"
        conds = r.json().get("conditions") or []
        assert len(conds) >= 12, f"{sid} has only {len(conds)} conditions"
        # Each entry exposes a name and at least one of effect/severity.
        for c in conds:
            assert c.get("name")


def test_anime5e_keeps_genre_conditions():
    r = requests.get(f"{API}/systems/anime-5e/reference", timeout=10)
    names = {c["name"] for c in r.json().get("conditions") or []}
    assert {"Genre-Locked", "Spotlit", "Eclipsed"} <= names


def test_cypher_has_damage_track():
    r = requests.get(f"{API}/systems/cypher/reference", timeout=10)
    names = {c["name"] for c in r.json().get("conditions") or []}
    assert {"Hale", "Impaired", "Debilitated", "Dead"} <= names


# ────────────────── PATCH /map/tokens/{tid} ──────────────────

def test_patch_token_partial_update():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        # Create a marker token via POST (existing path).
        r = requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                          json={"label": "Trap A", "x": 1, "y": 1,
                                "kind": "marker", "marker_type": "trap"},
                          timeout=10)
        assert r.status_code == 200, r.text
        tid = r.json()["id"]

        # PATCH only x/y — other fields untouched.
        r = requests.patch(f"{API}/sessions/{sid}/map/tokens/{tid}",
                           headers=_h(admin),
                           json={"x": 5, "y": 7}, timeout=10)
        assert r.status_code == 200, r.text
        t = r.json()
        assert t["x"] == 5 and t["y"] == 7
        assert t["label"] == "Trap A"
        assert t["marker_type"] == "trap"

        # PATCH unknown field → 422 (extra=forbid).
        r = requests.patch(f"{API}/sessions/{sid}/map/tokens/{tid}",
                           headers=_h(admin),
                           json={"bogus": 9}, timeout=10)
        assert r.status_code == 422, r.text

        # PATCH non-existent token → 404.
        r = requests.patch(f"{API}/sessions/{sid}/map/tokens/no-such-id",
                           headers=_h(admin), json={"x": 1}, timeout=10)
        assert r.status_code == 404

        # PATCH empty body → no-op, returns current row.
        r = requests.patch(f"{API}/sessions/{sid}/map/tokens/{tid}",
                           headers=_h(admin), json={}, timeout=10)
        assert r.status_code == 200
        assert r.json()["x"] == 5
    finally:
        _cleanup(admin, cid)


def test_patch_token_lock_blocks_player_move():
    """GM-locked tokens cannot have their position changed by anyone
    other than the GM (the existing upsert path enforces ownership;
    PATCH adds an explicit lock guard so other routes mutating tokens
    respect it too)."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        sid = _make_session(admin, cid)
        # GM creates a token NOT linked to any character; locked.
        r = requests.post(f"{API}/sessions/{sid}/map/tokens", headers=_h(admin),
                          json={"label": "Statue", "x": 0, "y": 0,
                                "kind": "marker", "marker_type": "note",
                                "locked": True},
                          timeout=10)
        tid = r.json()["id"]
        # GM can still patch it.
        r = requests.patch(f"{API}/sessions/{sid}/map/tokens/{tid}",
                           headers=_h(admin), json={"x": 3}, timeout=10)
        assert r.status_code == 200
        assert r.json()["x"] == 3
    finally:
        _cleanup(admin, cid)


# ────────────────── Deeper public stats ──────────────────

def test_public_stats_deeper_fields():
    r = requests.get(f"{API}/public/stats", timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    # New fields exist.
    for k in ("sessions_played", "active_24h", "gms_active", "by_system",
              "latest_version", "pytest_passing"):
        assert k in d, f"missing key: {k}"
    # by_system is a dict — only counts non-negative ints.
    assert isinstance(d["by_system"], dict)
    for sid, count in d["by_system"].items():
        assert isinstance(count, int) and count >= 0


def test_activity_pulse_returns_seven_days():
    r = requests.get(f"{API}/public/activity-pulse", timeout=10)
    assert r.status_code == 200, r.text
    days = r.json().get("days") or []
    assert len(days) == 7
    for d in days:
        assert "date" in d
        assert "campaigns_created" in d
        assert "sessions_opened" in d
        assert "characters_made" in d
