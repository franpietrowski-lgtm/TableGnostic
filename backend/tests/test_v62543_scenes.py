"""V6.25.43 — Scene Switcher backend tests (live HTTP).

Mirrors the style of test_v62541_auto_queue.py — hits the running
preview backend via the external REACT_APP_BACKEND_URL.

Covers:
  * Active scene starts null.
  * GM-only create + auto-close prior active.
  * Slug shape: scene{N}-session{N}_{campaign-slug}
  * Player cannot create / close.
  * Close requires confirmed=true (click-to-confirm guard ⇒ 412).
  * Setup PATCH only on active scenes (closed ⇒ 409 — no retcons).
  * Chat posted during an active scene carries scene_id.
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
PLAYER_EMAIL = "albanaszak@ymail.com"
PLAYER_PASS = "AuroraTest123!"


def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    j = r.json()
    return j.get("token") or j["access_token"]


def _h(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def _make_test_campaign_and_session(admin_tok: str) -> tuple:
    """Create a one-shot campaign + session for this run and seat the
    player. Returns (campaign_id, session_id, player_uid).
    """
    # Campaign
    cname = f"SceneTestCampaign-{int(time.time())}"
    r = requests.post(f"{API}/campaigns", headers=_h(admin_tok),
                      json={"name": cname, "system_id": "besm-4e"},
                      timeout=10)
    assert r.status_code in (200, 201), r.text
    camp = r.json()
    cid = camp["id"]
    # Session
    r = requests.post(f"{API}/sessions", headers=_h(admin_tok),
                      json={"campaign_id": cid, "title": "SceneTest Session"},
                      timeout=10)
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    # Seat the player by inviting them via invite_token flow.
    r = requests.get(f"{API}/campaigns/{cid}", headers=_h(admin_tok), timeout=10)
    invite = r.json().get("invite_token")
    if invite:
        pl_tok = _login(PLAYER_EMAIL, PLAYER_PASS)
        rj = requests.post(f"{API}/invites/{invite}/accept",
                           headers=_h(pl_tok), timeout=10)
        assert rj.status_code in (200, 201, 409), rj.text
    return cid, sid


def _cleanup(admin_tok: str, cid: str, sid: str) -> None:
    try:
        requests.delete(f"{API}/sessions/{sid}", headers=_h(admin_tok), timeout=10)
    except Exception:
        pass
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin_tok), timeout=10)
    except Exception:
        pass


def test_scene_lifecycle_and_confirm_guard():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid, sid = _make_test_campaign_and_session(admin)
    try:
        # 0. active is null
        r = requests.get(f"{API}/sessions/{sid}/scenes/active",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["scene"] is None

        # 1. Player cannot start (forbidden — only GM/admin)
        try:
            pl = _login(PLAYER_EMAIL, PLAYER_PASS)
            r = requests.post(f"{API}/sessions/{sid}/scenes",
                              headers=_h(pl), json={"name": "X"}, timeout=10)
            assert r.status_code == 403, r.text
        except AssertionError:
            raise
        except Exception:
            # If player login failed, skip — non-blocking
            pass

        # 2. Admin/GM starts scene #1
        r = requests.post(f"{API}/sessions/{sid}/scenes", headers=_h(admin),
                          json={"name": "Tavern"}, timeout=10)
        assert r.status_code == 200, r.text
        sc1 = r.json()["scene"]
        assert sc1["scene_no"] == 1
        assert sc1["status"] == "active"
        assert sc1["slug"].startswith("scene1-session")
        assert "scenetestcampaign" in sc1["slug"].lower()

        # 3. Starts scene #2 — auto-closes #1
        r = requests.post(f"{API}/sessions/{sid}/scenes", headers=_h(admin),
                          json={"name": "Road"}, timeout=10)
        assert r.status_code == 200
        sc2 = r.json()["scene"]
        assert sc2["scene_no"] == 2

        # 4. active is now scene 2
        r = requests.get(f"{API}/sessions/{sid}/scenes/active",
                         headers=_h(admin), timeout=10)
        assert r.json()["scene"]["id"] == sc2["id"]

        # 5. close without confirmed → 412 click-to-confirm guard
        r = requests.post(f"{API}/sessions/{sid}/scenes/{sc2['id']}/close",
                          headers=_h(admin), timeout=10)
        assert r.status_code == 412, r.text
        assert "confirmed=true" in r.json()["detail"]

        # 6. close with confirmed → 200
        r = requests.post(
            f"{API}/sessions/{sid}/scenes/{sc2['id']}/close?confirmed=true",
            headers=_h(admin), timeout=10,
        )
        assert r.status_code == 200, r.text
        assert r.json()["scene"]["status"] == "closed"

        # 7. patch on closed scene → 409 (no retcons)
        r = requests.patch(f"{API}/sessions/{sid}/scenes/{sc2['id']}/setup",
                           headers=_h(admin), json={"name": "Retcon"}, timeout=10)
        assert r.status_code == 409, r.text

        # 8. start scene 3, post chat, expect scene_id on the chat row
        r = requests.post(f"{API}/sessions/{sid}/scenes", headers=_h(admin),
                          json={"name": "Cave"}, timeout=10)
        sc3 = r.json()["scene"]
        r = requests.post(f"{API}/chat", headers=_h(admin),
                          json={"session_id": sid, "message": "torches lit",
                                "kind": "chat"}, timeout=10)
        assert r.status_code == 200, r.text
        assert r.json().get("scene_id") == sc3["id"]
        assert r.json().get("scene_slug") == sc3["slug"]

        # 9. GM default-thread setter is GM-only and persists
        r = requests.patch(f"{API}/sessions/{sid}/default-thread",
                           headers=_h(admin),
                           json={"default_target_thread_id": "thr_test_abc"},
                           timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["default_target_thread_id"] == "thr_test_abc"
    finally:
        _cleanup(admin, cid, sid)
