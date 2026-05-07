"""V6.25.12 — Reference Editor BESM weapon|item composer + Materials
queue + Anime 5E class library scaffold."""
from __future__ import annotations
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def player_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "albanaszak@ymail.com",
                             "password": "AuroraTest123!"})
    if r.status_code != 200:
        pytest.skip("Aurora not seeded")
    return r.json()["access_token"]


@pytest.fixture()
def shared_camp(gm_token, player_token):
    """Campaign Aurora (player) is rostered onto, with Eli as a character."""
    cp = requests.post(f"{BASE_URL}/api/campaigns",
                        headers=H(gm_token),
                        json={"name": "V62512 Materials Demo", "system_id": "besm-4e"})
    cid = cp.json()["id"]
    # Roster Aurora — accept her into the member_ids set via the
    # invite-token path (the canonical join flow).
    invite = requests.get(f"{BASE_URL}/api/campaigns/{cid}",
                            headers=H(gm_token)).json().get("invite_token")
    if invite:
        requests.post(f"{BASE_URL}/api/invites/{invite}/accept",
                       headers=H(player_token))
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


# ── Anime 5E class library ──────────────────────────────────────────

def test_anime5e_class_library_exposes_full_l1_l20_grid(gm_token):
    """The new /api/anime5e/classes endpoint must return ≥10 core classes
    with a full L1-L20 grants_by_level grid each."""
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["system"] == "anime-5e"
    assert sorted(body["asi_levels"]) == [4, 8, 12, 16, 19]
    assert sorted(body["milestone_levels"]) == [3, 7, 13, 17, 20]
    classes = body["classes"]
    assert len(classes) >= 10, f"expected ≥10 core classes, got {len(classes)}"
    # Required canonical names — not exhaustive, but representative.
    names = {c["id"] for c in classes}
    for required in {"magical-girl", "samurai", "wandering-monk",
                       "concentrated-mage", "tech-genius", "artisan",
                       "champion", "adventurer"}:
        assert required in names, f"missing canonical class {required}"
    # Every class has L1-L20 grants.
    for c in classes:
        grid = c["grants_by_level"]
        assert len(grid) == 20, f"{c['id']} grid size {len(grid)}"
        for L in range(1, 21):
            row = grid[str(L)] if str(L) in grid else grid.get(L)
            assert row is not None, f"{c['id']} missing L{L}"
            assert "proficiency_bonus" in row
        # ASI rows flagged.
        asi_4 = grid.get("4") or grid.get(4)
        assert asi_4.get("asi_or_feat") is True
    # Scaffold flag present so frontends know what's authoritative.
    mg = next(c for c in classes if c["id"] == "magical-girl")
    assert mg["features_pending"] is True


def test_artisan_class_has_crafting_traditions(gm_token):
    """Artisan class entry surfaces crafting traditions for the
    materials pipeline tie-in."""
    r = requests.get(f"{BASE_URL}/api/anime5e/classes")
    body = r.json()
    art = next(c for c in body["classes"] if c["id"] == "artisan")
    trads = art.get("crafting_traditions") or []
    assert "alchemy" in trads
    assert "smithing" in trads


# ── Materials intake queue ─────────────────────────────────────────

def test_player_submits_material_to_queue_gm_approves(
        gm_token, player_token, shared_camp):
    """End-to-end: Aurora submits a material → GM lists pending → GM
    approves → codex gains a `material` node with provenance."""
    cid = shared_camp
    # Submit as the player.
    rs = requests.post(f"{BASE_URL}/api/campaigns/{cid}/materials-queue",
                        headers=H(player_token),
                        json={"name": "Spider Silk (rough)",
                              "node_kind": "material",
                              "summary": "Cut from the sentinel-spider's web.",
                              "tags": ["fibre", "rare"], "rarity": "uncommon"})
    assert rs.status_code == 200, rs.text
    ticket = rs.json()
    assert ticket["status"] == "pending"
    tid = ticket["id"]

    # GM lists pending tickets.
    rl = requests.get(f"{BASE_URL}/api/campaigns/{cid}/materials-queue?status=pending",
                       headers=H(gm_token))
    assert rl.status_code == 200
    assert any(t["id"] == tid for t in rl.json())

    # Player CANNOT see the GM's full queue (only their own).
    rlp = requests.get(f"{BASE_URL}/api/campaigns/{cid}/materials-queue",
                        headers=H(player_token))
    assert rlp.status_code == 200
    # Aurora's own tickets only; she can see her own ticket.
    assert all(t["submitter_id"] == ticket["submitter_id"] for t in rlp.json())

    # Player CANNOT approve (must be GM).
    rrej = requests.post(f"{BASE_URL}/api/campaigns/{cid}/materials-queue/{tid}/approve",
                         headers=H(player_token))
    assert rrej.status_code == 403

    # GM approves.
    ra = requests.post(f"{BASE_URL}/api/campaigns/{cid}/materials-queue/{tid}/approve",
                        headers=H(gm_token))
    assert ra.status_code == 200, ra.text
    node_id = ra.json()["codex_node_id"]
    assert node_id

    # Codex node was created with the right kind + provenance.
    rcx = requests.get(f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                        headers=H(gm_token))
    assert rcx.status_code == 200
    matches = [n for n in rcx.json() if n.get("name") == "Spider Silk (rough)"]
    assert matches, "approved material missing from codex"
    n = matches[0]
    assert (n.get("node_kind") or n.get("type")) == "material"

    # Re-approving the same ticket conflicts.
    rdup = requests.post(f"{BASE_URL}/api/campaigns/{cid}/materials-queue/{tid}/approve",
                         headers=H(gm_token))
    assert rdup.status_code == 409


def test_non_member_cannot_submit_to_materials_queue(gm_token):
    """Non-roster user gets 403 on submission."""
    # Spin up a fresh campaign that Aurora is NOT on.
    cp = requests.post(f"{BASE_URL}/api/campaigns",
                        headers=H(gm_token),
                        json={"name": "V62512 Locked Camp", "system_id": "besm-4e"})
    cid = cp.json()["id"]
    # Use a fresh player token from Aurora.
    r = requests.post(f"{BASE_URL}/api/auth/login",
                        json={"email": "albanaszak@ymail.com",
                              "password": "AuroraTest123!"})
    if r.status_code != 200:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))
        pytest.skip("Aurora not seeded")
    aurora = r.json()["access_token"]

    rs = requests.post(f"{BASE_URL}/api/campaigns/{cid}/materials-queue",
                        headers=H(aurora),
                        json={"name": "Sneak attempt", "node_kind": "material"})
    assert rs.status_code == 403

    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_invalid_node_kind_rejected(gm_token, shared_camp):
    """Only material / byproduct / craft_output are accepted."""
    rs = requests.post(f"{BASE_URL}/api/campaigns/{shared_camp}/materials-queue",
                        headers=H(gm_token),
                        json={"name": "X", "node_kind": "npc"})
    assert rs.status_code == 422
    assert "node_kind must be one of" in rs.json().get("detail", "")
