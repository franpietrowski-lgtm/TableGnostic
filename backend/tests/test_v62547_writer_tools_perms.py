"""V6.25.47 — Permission tests for the 4 remaining writer tools.

Verifies the explicit review-request asks:
  • non-GM/non-admin gets 403 on writes (cultures, cosmology, pov-bibles, themes)
  • non-member gets 403 on reads (same 4 surfaces)
"""
from __future__ import annotations
import os
import time
import secrets

import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read()
        .split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"


def _h(t): return {"Authorization": f"Bearer {t}"}


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _register(email, password, display_name):
    r = requests.post(f"{API}/auth/register",
                      json={"email": email, "password": password,
                            "name": display_name, "role": "player"},
                      timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json().get("access_token") or _login(email, password)


def _make_camp(admin):
    r = requests.post(f"{API}/campaigns", headers=_h(admin),
                      json={"name": f"WTPerm-{int(time.time()*1000)}",
                            "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _accept_invite(admin, cid, player_token):
    """Get the invite token from admin GET, then have player accept it."""
    cresp = requests.get(f"{API}/campaigns/{cid}",
                         headers=_h(admin), timeout=10).json()
    tok = cresp.get("invite_token")
    assert tok, f"no invite_token in campaign response: {cresp.keys()}"
    r = requests.post(f"{API}/invites/{tok}/accept",
                      headers=_h(player_token), timeout=10)
    assert r.status_code in (200, 201), r.text


SURFACES = [
    ("cultures",   "cultures",  {"name": "X"}),
    ("cosmology",  "entries",   {"kind": "omen", "name": "X"}),
    ("pov-bibles", "bibles",    {"name": "X"}),
    ("themes",     "items",     {"kind": "theme", "name": "X"}),
]


def test_perms_non_member_403_read_non_gm_403_write():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        salt = secrets.token_hex(4)
        outsider_email = f"v62547-outsider-{salt}@example.com"
        member_email = f"v62547-member-{salt}@example.com"
        outsider = _register(outsider_email, "GoodPass123!", "Outsider")
        member = _register(member_email, "GoodPass123!", "Member")

        # Outsider gets 403 on ALL reads.
        for path, _, _ in SURFACES:
            r = requests.get(f"{API}/writer/{path}/{cid}",
                             headers=_h(outsider), timeout=10)
            assert r.status_code == 403, f"{path} outsider read: {r.status_code} {r.text}"

        # Make `member` an actual member via invite.
        _accept_invite(admin, cid, member)

        # Member reads OK (200, writable=False).
        for path, key, _ in SURFACES:
            r = requests.get(f"{API}/writer/{path}/{cid}",
                             headers=_h(member), timeout=10)
            assert r.status_code == 200, f"{path} member read: {r.status_code} {r.text}"
            assert r.json().get("writable") is False
            assert key in r.json()

        # Member writes blocked with 403.
        for path, _, payload in SURFACES:
            r = requests.post(f"{API}/writer/{path}/{cid}",
                              headers=_h(member), json=payload, timeout=10)
            assert r.status_code == 403, f"{path} member write: {r.status_code} {r.text}"
    finally:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin), timeout=10)
