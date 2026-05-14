"""V6.25.53 — Phase B backend tests.

Hard-seeded Evereantha cosmology (Faces of Aurae × Faces of Mortiscura
+ opposition matrix) — endpoints + payload shape + per-row lookup.
"""
from __future__ import annotations
import os

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


def test_cosmology_payload_shape():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    r = requests.get(f"{API}/cosmology/evereantha", headers=_h(admin), timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    # Exactly 4 Aurae faces and 4 Mortiscura faces.
    assert len(d["aurae"]) == 4
    assert len(d["mortiscura"]) == 4
    # Each face has 3 nodes.
    for f in d["aurae"] + d["mortiscura"]:
        assert len(f["nodes"]) == 3, f"{f['name']} should have 3 nodes"
        for n in f["nodes"]:
            for k in ("name", "domain", "rank_1", "rank_3", "failure"):
                assert n.get(k), f"{f['name']}.{n.get('name')} missing {k}"
    # Opposition matrix has at least the 8 cardinal pairs.
    assert len(d["opposition"]) >= 8
    # Magnitude legend exists.
    for mag in ("advantage", "edge", "neutral", "obstacle"):
        assert mag in d["magnitude_legend"]


def test_cosmology_required_canon_faces_present():
    """The bible's canon names must round-trip — these are referenced
    by name in seeded campaign content."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    d = requests.get(f"{API}/cosmology/evereantha", headers=_h(admin),
                     timeout=10).json()
    aurae_ids = {f["id"] for f in d["aurae"]}
    mortis_ids = {f["id"] for f in d["mortiscura"]}
    assert {"luxantia", "cryptosha", "confluo", "expanzis"} == aurae_ids
    assert {"obscuritia", "spectros", "exutus", "stasis"} == mortis_ids


def test_cosmology_opposition_direct_pairs_are_advantage():
    """The 4 cardinal opposite pairings must return `advantage`
    magnitude — fiction-wise, these are the cosmological clashes."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    pairs = [
        ("luxantia",  "obscuritia"),
        ("cryptosha", "spectros"),
        ("confluo",   "exutus"),
        ("expanzis",  "stasis"),
    ]
    for a, d in pairs:
        r = requests.get(
            f"{API}/cosmology/evereantha/opposition?attacker={a}&defender={d}",
            headers=_h(admin), timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["magnitude"] == "advantage", \
            f"{a} vs {d} should be advantage, got {r.json()['magnitude']}"
        # And reverse should also be advantage (both sides have edge in
        # cardinal clashes — Aurae beats shadow, Mortiscura corrupts light).
        r2 = requests.get(
            f"{API}/cosmology/evereantha/opposition?attacker={d}&defender={a}",
            headers=_h(admin), timeout=10)
        assert r2.status_code == 200
        assert r2.json()["magnitude"] == "advantage"


def test_cosmology_opposition_unknown_face_404():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    r = requests.get(
        f"{API}/cosmology/evereantha/opposition?attacker=bogus&defender=luxantia",
        headers=_h(admin), timeout=10)
    assert r.status_code == 404
    r = requests.get(
        f"{API}/cosmology/evereantha/opposition?attacker=luxantia&defender=bogus",
        headers=_h(admin), timeout=10)
    assert r.status_code == 404


def test_cosmology_neutral_fallback_for_unknown_pair():
    """Same-side pairings (Aurae vs Aurae) return synthetic neutral row
    rather than 404 — they're valid pairings, just not pre-tabulated."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    r = requests.get(
        f"{API}/cosmology/evereantha/opposition?attacker=luxantia&defender=cryptosha",
        headers=_h(admin), timeout=10)
    assert r.status_code == 200
    assert r.json()["magnitude"] == "neutral"
    assert "Fiction-led" in r.json()["note"]


def test_cosmology_auth_required():
    """No token → 401/403 — cosmology is auth-gated, even though canon."""
    r = requests.get(f"{API}/cosmology/evereantha", timeout=10)
    assert r.status_code in (401, 403), r.text
