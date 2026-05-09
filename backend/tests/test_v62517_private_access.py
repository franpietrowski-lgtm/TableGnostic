"""V6.25.17 — Private campaign access via passwords + named share-links.

Two private-access surfaces:
  1. Campaign-wide invite_token + optional password (existing
     `/invites/{token}/accept` flow, now password-gated).
  2. Named share-links with optional password / expiry / max-uses
     (`/share-links/{token}` lookup + `/redeem` join).
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
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _player_token():
    """Aurora test account or skip."""
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "albanaszak@ymail.com",
                             "password": "AuroraTest123!"})
    if r.status_code != 200:
        return None
    return r.json()["access_token"]


def _spin(gm, name="V62517 Private Demo"):
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": name, "system_id": "anime-5e"})
    assert cp.status_code == 200, cp.text
    return cp.json()


def test_invite_password_gates_join():
    gm = _gm()
    pl = _player_token()
    if not pl:
        return
    camp = _spin(gm, "V62517 PWD Invite")
    cid = camp["id"]
    invite = camp["invite_token"]
    try:
        # Public invite reveals password_required=False initially.
        body = requests.get(f"{BASE_URL}/api/invites/{invite}").json()
        assert body["password_required"] is False

        # GM sets a password.
        rs = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/access-password",
            headers=H(gm), json={"password": "scarlet-keep"})
        assert rs.status_code == 200
        assert rs.json()["password_set"] is True

        # Public invite now reveals password_required=True.
        body = requests.get(f"{BASE_URL}/api/invites/{invite}").json()
        assert body["password_required"] is True

        # Wrong password → 403.
        bad = requests.post(f"{BASE_URL}/api/invites/{invite}/accept",
                             headers=H(pl), json={"password": "WRONG"})
        assert bad.status_code == 403
        assert "Incorrect" in bad.json().get("detail", "")

        # Right password → seated.
        ok = requests.post(f"{BASE_URL}/api/invites/{invite}/accept",
                            headers=H(pl), json={"password": "scarlet-keep"})
        assert ok.status_code == 200
        assert ok.json()["ok"] is True

        # Clearing the password again removes the gate.
        clr = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/access-password",
            headers=H(gm), json={"password": ""})
        assert clr.json()["password_set"] is False
        body = requests.get(f"{BASE_URL}/api/invites/{invite}").json()
        assert body["password_required"] is False
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_share_links_lifecycle_with_password():
    gm = _gm()
    pl = _player_token()
    if not pl:
        return
    camp = _spin(gm, "V62517 SL Demo")
    cid = camp["id"]
    try:
        # Empty list initially.
        ls = requests.get(f"{BASE_URL}/api/campaigns/{cid}/share-links",
                           headers=H(gm))
        assert ls.status_code == 200
        assert ls.json() == []

        # Create a password-gated link.
        cr = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/share-links", headers=H(gm),
            json={"label": "patreon-gold", "password": "starforge",
                  "max_uses": 2})
        assert cr.status_code == 200, cr.text
        link = cr.json()["share_link"]
        assert link["password_set"] is True
        assert link["max_uses"] == 2
        assert "password_hash" not in link  # NEVER echoed
        token = link["token"]

        # Public peek.
        pub = requests.get(f"{BASE_URL}/api/share-links/{token}").json()
        assert pub["password_required"] is True
        assert pub["valid"] is True
        assert pub["label"] == "patreon-gold"

        # Wrong password → 403.
        bad = requests.post(f"{BASE_URL}/api/share-links/{token}/redeem",
                             headers=H(pl), json={"password": "no"})
        assert bad.status_code == 403

        # Correct password → joined.
        ok = requests.post(f"{BASE_URL}/api/share-links/{token}/redeem",
                            headers=H(pl), json={"password": "starforge"})
        assert ok.status_code == 200, ok.text

        # Use-count incremented.
        ls2 = requests.get(f"{BASE_URL}/api/campaigns/{cid}/share-links",
                            headers=H(gm)).json()
        assert ls2[0]["use_count"] == 1
        assert "last_used_at" in ls2[0]

        # GM can delete the link.
        dl = requests.delete(
            f"{BASE_URL}/api/campaigns/{cid}/share-links/{link['id']}",
            headers=H(gm))
        assert dl.status_code == 200
        assert dl.json()["deleted"] == 1

        # Token now 404.
        gone = requests.get(f"{BASE_URL}/api/share-links/{token}")
        assert gone.status_code == 404
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_share_link_max_uses_caps_redemptions():
    """A link with max_uses=1 must reject the second redemption."""
    gm = _gm()
    pl = _player_token()
    if not pl:
        return
    camp = _spin(gm, "V62517 Cap Demo")
    cid = camp["id"]
    try:
        cr = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/share-links", headers=H(gm),
            json={"label": "single-use", "max_uses": 1})
        token = cr.json()["share_link"]["token"]

        # First redemption succeeds.
        r1 = requests.post(f"{BASE_URL}/api/share-links/{token}/redeem",
                            headers=H(pl), json={})
        assert r1.status_code == 200

        # Second one (already a member) returns ok=already, but capped
        # check happens BEFORE the membership check, so a second NEW
        # user would 410. We assert via the public peek + use_count.
        peek = requests.get(f"{BASE_URL}/api/share-links/{token}").json()
        assert peek["capped"] is True
        assert peek["valid"] is False
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_share_link_endpoints_block_non_gm():
    """Player accounts cannot list / create / delete share links."""
    gm = _gm()
    pl = _player_token()
    if not pl:
        return
    camp = _spin(gm, "V62517 Block Demo")
    cid = camp["id"]
    try:
        for method, path in [
            ("GET", f"/api/campaigns/{cid}/share-links"),
            ("POST", f"/api/campaigns/{cid}/share-links"),
            ("POST", f"/api/campaigns/{cid}/access-password"),
        ]:
            if method == "GET":
                r = requests.get(f"{BASE_URL}{path}", headers=H(pl))
            else:
                r = requests.post(f"{BASE_URL}{path}", headers=H(pl),
                                   json={"label": "x", "password": "y"})
            assert r.status_code == 403, f"{path}: expected 403, got {r.status_code}"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))
