"""V6.25.46 — supplemental writer-tools tests (iteration 79).

Covers gaps not already validated in test_v62546_writer_tools.py:
  * Atlas — reject map_x>1.0 with 422.
  * Atlas — pin existing location node (no new node created).
  * Manuscript — scene/beat parent gating + beat parent=chapter rejected.
  * Permission — non-GM member can read (writable:false) but cannot write.
  * Reseed checkpoint — db.reseed_checkpoints present, db.nodes count for
    the evereantha-bible-llm-seed-v3 tag is > 0 mid-run.
"""
from __future__ import annotations
import os
import time

import pytest
import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read()
        .split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
).rstrip("/") + "/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _make_camp(admin_token, name_prefix="WTSup"):
    name = f"{name_prefix}-{int(time.time()*1000)}"
    r = requests.post(f"{API}/campaigns", headers=_h(admin_token),
                      json={"name": name, "system_id": "besm-4e"}, timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _cleanup(admin_token, cid):
    try:
        requests.delete(f"{API}/campaigns/{cid}", headers=_h(admin_token),
                        timeout=10)
    except Exception:
        pass


# ---------- ATLAS edge cases ----------

def test_atlas_rejects_out_of_range_coords():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        r = requests.post(f"{API}/writer/atlas/{cid}/pins", headers=_h(admin),
                          json={"title": "Bad", "map_x": 1.5, "map_y": 0.3},
                          timeout=10)
        assert r.status_code == 422, r.text
        r = requests.post(f"{API}/writer/atlas/{cid}/pins", headers=_h(admin),
                          json={"title": "Bad", "map_x": 0.5, "map_y": -0.1},
                          timeout=10)
        assert r.status_code == 422, r.text
    finally:
        _cleanup(admin, cid)


def test_atlas_pin_existing_node_does_not_create_new():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # Create a location node via the atlas (no node_id) first.
        r = requests.post(f"{API}/writer/atlas/{cid}/pins", headers=_h(admin),
                          json={"title": "Origin", "map_x": 0.1, "map_y": 0.1},
                          timeout=10)
        assert r.status_code == 200
        existing_node_id = r.json()["node_id"]

        # Now unpin it (keeps the node).
        r = requests.delete(f"{API}/writer/atlas/{cid}/pins/{existing_node_id}",
                            headers=_h(admin), timeout=10)
        assert r.status_code == 200

        # Snapshot location-node count (pins + unpinned).
        d_before = requests.get(f"{API}/writer/atlas/{cid}", headers=_h(admin),
                                timeout=10).json()
        loc_count_before = len(d_before["pins"]) + len(d_before["unpinned_locations"])
        assert loc_count_before == 1

        # Pin existing node via node_id — should reuse, not create.
        r = requests.post(
            f"{API}/writer/atlas/{cid}/pins", headers=_h(admin),
            json={"node_id": existing_node_id, "title": "Origin (re-pinned)",
                  "map_x": 0.42, "map_y": 0.42, "description": "Updated"},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        assert r.json()["node_id"] == existing_node_id
        assert r.json().get("pinned") is True

        d_after = requests.get(f"{API}/writer/atlas/{cid}", headers=_h(admin),
                               timeout=10).json()
        loc_count_after = len(d_after["pins"]) + len(d_after["unpinned_locations"])
        assert loc_count_after == loc_count_before, (
            f"new location node was created on re-pin: "
            f"{loc_count_before} → {loc_count_after}"
        )
        assert len(d_after["pins"]) == 1
        assert d_after["pins"][0]["fields"]["map_x"] == 0.42
    finally:
        _cleanup(admin, cid)


# ---------- MANUSCRIPT parent-gating extras ----------

def test_manuscript_parent_gating_extras():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin)
    try:
        # Chapter (parent=null) → 200
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "chapter", "title": "C1"}, timeout=10)
        assert r.status_code == 200
        ch_id = r.json()["id"]

        # scene with no parent → 400
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "scene", "title": "orphan scene"},
                          timeout=10)
        assert r.status_code == 400, r.text

        # scene with chapter parent → 200
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "scene", "parent_id": ch_id,
                                "title": "S1"}, timeout=10)
        assert r.status_code == 200
        sc_id = r.json()["id"]

        # beat with chapter parent → 400 (must be scene)
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "beat", "parent_id": ch_id,
                                "title": "bad beat"}, timeout=10)
        assert r.status_code == 400, r.text

        # beat with scene parent → 200
        r = requests.post(f"{API}/writer/manuscript/{cid}", headers=_h(admin),
                          json={"kind": "beat", "parent_id": sc_id,
                                "title": "B1", "tension": 4}, timeout=10)
        assert r.status_code == 200
    finally:
        _cleanup(admin, cid)


# ---------- PERMISSION — non-GM ----------

def test_non_gm_cannot_write_but_can_read():
    """Register a fresh player, add as member to a fresh admin-owned campaign,
    then ensure player gets writable:false on GET and 403 on POST."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    cid = _make_camp(admin, "WTSupPerm")
    ts = int(time.time() * 1000)
    player_email = f"v62546-player-{ts}@gmail.com"
    try:
        # Register fresh player
        r = requests.post(
            f"{API}/auth/register",
            json={"email": player_email, "password": "TestPass123!",
                  "name": "V62546 Player", "role": "player"},
            timeout=15,
        )
        assert r.status_code in (200, 201), r.text
        player_id = r.json().get("id") or r.json().get("user", {}).get("id")
        player_token = r.json().get("access_token") or _login(
            player_email, "TestPass123!"
        )

        # Use the invite-token flow: fetch campaign as GM admin to get its
        # invite_token, then have the player accept it.
        r = requests.get(f"{API}/campaigns/{cid}", headers=_h(admin),
                         timeout=10)
        assert r.status_code == 200, r.text
        invite_token = r.json().get("invite_token")
        assert invite_token, "campaign has no invite_token"

        r = requests.post(f"{API}/invites/{invite_token}/accept",
                          headers=_h(player_token), json={}, timeout=10)
        assert r.status_code == 200, r.text

        # Player GET on writer endpoints — should be 200 with writable:false.
        r = requests.get(f"{API}/writer/atlas/{cid}",
                         headers=_h(player_token), timeout=10)
        assert r.status_code == 200, r.text
        assert r.json().get("writable") is False, r.json()

        r = requests.get(f"{API}/writer/magic/{cid}",
                         headers=_h(player_token), timeout=10)
        assert r.status_code == 200, r.text
        assert r.json().get("writable") is False

        # Player POST → 403.
        r = requests.post(
            f"{API}/writer/magic/{cid}", headers=_h(player_token),
            json={"name": "Forbidden", "kind": "primary"}, timeout=10,
        )
        assert r.status_code == 403, r.text

        r = requests.post(
            f"{API}/writer/atlas/{cid}/pins", headers=_h(player_token),
            json={"title": "x", "map_x": 0.1, "map_y": 0.1}, timeout=10,
        )
        assert r.status_code == 403, r.text

        r = requests.post(
            f"{API}/writer/manuscript/{cid}", headers=_h(player_token),
            json={"kind": "chapter", "title": "x"}, timeout=10,
        )
        assert r.status_code == 403, r.text
    finally:
        _cleanup(admin, cid)


# ---------- RESEED CHECKPOINT — DB inspection ----------

def test_reseed_checkpoint_persistence_and_nodes_present():
    """Verify the background re-seed script's checkpoint collection is
    populated AND db.nodes has rows tagged 'evereantha-bible-llm-seed-v3'.
    This is read-only — does not interfere with PID 319.
    """
    import asyncio
    import sys
    sys.path.insert(0, "/app/backend")
    from core.db import db  # noqa: E402

    async def _check():
        ck_total = await db.reseed_checkpoints.count_documents({})
        sample_ck = await db.reseed_checkpoints.find_one({}, {"_id": 0})
        # Has the expected shape?
        if sample_ck is not None:
            keys = set(sample_ck.keys())
            for k in ("source_tag", "chunk_no", "status"):
                assert k in keys, (
                    f"reseed_checkpoints row missing {k}: keys={keys}"
                )
        node_total = await db.nodes.count_documents(
            {"tags": "evereantha-bible-llm-seed-v3"}
        )
        return ck_total, node_total, sample_ck

    ck_total, node_total, sample_ck = asyncio.get_event_loop().run_until_complete(
        _check()
    )
    print(f"reseed_checkpoints rows: {ck_total}; sample={sample_ck}")
    print(f"nodes with evereantha-bible-llm-seed-v3 tag: {node_total}")
    assert ck_total > 0, (
        "db.reseed_checkpoints is empty — chunk-incremental persistence "
        "is not working (or script hasn't run any chunk yet)."
    )
    assert node_total > 0, (
        "db.nodes has 0 rows tagged evereantha-bible-llm-seed-v3 — "
        "expected >0 mid-run (NOT zero until script ends)."
    )
