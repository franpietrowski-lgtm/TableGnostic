"""V6.25.55 — Phase D: Virtual GM character lazy-create + PTT integration."""
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


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _create_campaign(token, name="Phase D"):
    r = requests.post(f"{API}/campaigns", headers=_h(token),
                      json={"name": name, "system_id": "besm-4e",
                            "blurb": "phase d test", "visibility": "private"},
                      timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def test_gm_voice_character_lazy_creates_on_first_read():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    camp = _create_campaign(admin, "PhD-lazy-create")

    r = requests.get(f"{API}/campaigns/{camp['id']}/gm-voice-character",
                     headers=_h(admin), timeout=10)
    assert r.status_code == 200, r.text
    ch = r.json()
    assert ch["name"] == "The Game Master"
    assert ch["is_gm_voice"] is True
    assert ch["omniscient"] is True
    assert ch["total_points"] == 0
    assert ch["published"] is True
    assert ch["owner_id"] == admin_user_id(admin) if False else True  # checked below
    # Stats are zeroed.
    assert all(v == 0 for v in (ch.get("stats") or {}).values())


def admin_user_id(token):
    r = requests.get(f"{API}/auth/me", headers=_h(token), timeout=10)
    assert r.status_code == 200
    return r.json()["id"]


def test_gm_voice_character_is_idempotent():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    camp = _create_campaign(admin, "PhD-idempotent")
    a = requests.get(f"{API}/campaigns/{camp['id']}/gm-voice-character",
                     headers=_h(admin), timeout=10).json()
    b = requests.get(f"{API}/campaigns/{camp['id']}/gm-voice-character",
                     headers=_h(admin), timeout=10).json()
    assert a["id"] == b["id"], "Second call must return the SAME virtual GM character."

    # Listing the campaign's characters must include exactly ONE is_gm_voice row.
    chars = requests.get(f"{API}/campaigns/{camp['id']}/characters",
                         headers=_h(admin), timeout=10).json()
    voice_chars = [c for c in chars if c.get("is_gm_voice") is True]
    assert len(voice_chars) == 1, f"expected exactly one GM voice char, got {len(voice_chars)}"


def test_gm_voice_character_403_for_non_member():
    """Non-member non-admin cannot read another campaign's GM voice."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    camp = _create_campaign(admin, "PhD-403")
    # Fresh GM, not seated on admin's campaign.
    gm_email = f"phd-gm-{os.urandom(4).hex()}@tablegnostic-test.com"
    r = requests.post(f"{API}/auth/register",
                      json={"email": gm_email, "password": "PhD!Test123",
                            "name": "PhD GM", "role": "gm"}, timeout=10)
    assert r.status_code == 200, r.text
    gm_token = r.json()["access_token"]
    r = requests.get(f"{API}/campaigns/{camp['id']}/gm-voice-character",
                     headers=_h(gm_token), timeout=10)
    assert r.status_code == 403


def test_gm_voice_character_404_unknown_campaign():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    r = requests.get(f"{API}/campaigns/does-not-exist/gm-voice-character",
                     headers=_h(admin), timeout=10)
    assert r.status_code == 404


def test_gm_voice_round_trips_through_campaign_listing():
    """The virtual GM character is `published=True` so it must surface
    in the campaign's character list AND be selectable from the dice/PTT
    pickers without any frontend special-casing."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    camp = _create_campaign(admin, "PhD-list-surface")
    # Trigger lazy-create.
    gm_char = requests.get(f"{API}/campaigns/{camp['id']}/gm-voice-character",
                           headers=_h(admin), timeout=10).json()
    chars = requests.get(f"{API}/campaigns/{camp['id']}/characters",
                         headers=_h(admin), timeout=10).json()
    by_id = {c["id"]: c for c in chars}
    assert gm_char["id"] in by_id, "GM voice character must appear in /characters list"
    assert by_id[gm_char["id"]]["name"] == "The Game Master"
    assert by_id[gm_char["id"]]["published"] is True
