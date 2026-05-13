"""V6.25.43 supplemental — covers extras from review request:
   - GET /api/sessions/{sid}/scenes returns array (list endpoint)
   - POST /api/chat with NO active scene must NOT include scene_id (or null)
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
    j = r.json()
    return j.get("token") or j["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _make(admin):
    cname = f"SceneSupCampaign-{int(time.time())}"
    r = requests.post(f"{API}/campaigns", headers=_h(admin),
                      json={"name": cname, "system_id": "besm-4e"}, timeout=10)
    assert r.status_code in (200, 201), r.text
    cid = r.json()["id"]
    r = requests.post(f"{API}/sessions", headers=_h(admin),
                      json={"campaign_id": cid, "title": "SceneSup Session"}, timeout=10)
    assert r.status_code == 200, r.text
    return cid, r.json()["id"]


def _cleanup(admin, cid, sid):
    for u in (f"{API}/sessions/{sid}", f"{API}/campaigns/{cid}"):
        try:
            requests.delete(u, headers=_h(admin), timeout=10)
        except Exception:
            pass


def test_scenes_list_endpoint_returns_array():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid, sid = _make(admin)
    try:
        # empty initial list
        r = requests.get(f"{API}/sessions/{sid}/scenes",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200, r.text
        j = r.json()
        scenes = j["scenes"] if isinstance(j, dict) and "scenes" in j else j
        assert isinstance(scenes, list)
        assert len(scenes) == 0

        # create two scenes
        requests.post(f"{API}/sessions/{sid}/scenes", headers=_h(admin),
                      json={"name": "A"}, timeout=10)
        requests.post(f"{API}/sessions/{sid}/scenes", headers=_h(admin),
                      json={"name": "B"}, timeout=10)
        r = requests.get(f"{API}/sessions/{sid}/scenes",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200
        j = r.json()
        scenes = j["scenes"] if isinstance(j, dict) and "scenes" in j else j
        assert isinstance(scenes, list)
        assert len(scenes) == 2
        nums = sorted(s["scene_no"] for s in scenes)
        assert nums == [1, 2]
    finally:
        _cleanup(admin, cid, sid)


def test_chat_with_no_active_scene_has_no_scene_id():
    """POST /api/chat with NO active scene must not have scene_id set."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid, sid = _make(admin)
    try:
        # ensure no active scene
        r = requests.get(f"{API}/sessions/{sid}/scenes/active",
                         headers=_h(admin), timeout=10)
        assert r.status_code == 200
        assert r.json()["scene"] is None

        # post chat with NO active scene
        r = requests.post(f"{API}/chat", headers=_h(admin),
                          json={"session_id": sid, "message": "no scene yet",
                                "kind": "chat"}, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        # scene_id must be absent OR null
        assert body.get("scene_id") in (None, "", 0)
        assert body.get("scene_slug") in (None, "", 0)
    finally:
        _cleanup(admin, cid, sid)
