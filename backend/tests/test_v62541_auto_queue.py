"""V6.25.41 — Auto-queue wiring for character PUT + folio inventory PATCH.

When the campaign has `gm_approval_required=true`, player edits to
their own character (`PUT /characters/{id}`) and inventory state
(`PATCH /characters/{id}/folio` with bucket=`inventory_state`) should
return HTTP 202 with a queued change_request, NOT write directly.

GM + admin always bypass.
"""
import os
import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"
MAIDEN_CID = "af461ae004364002932f93c5b71cd483"


def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json().get("token") or r.json()["access_token"]


def _h(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def _ensure_test_player(admin_tok: str):
    """Make sure a dedicated test player exists, is seated on the Maiden
    campaign via the invite-token flow, and owns a character there.
    Returns (player_tok, char_id, player_id)."""
    email = "auto-queue-player@tablegnostic-test.com"
    password = "AutoQueueTest123!"
    requests.post(f"{API}/auth/register",
                  json={"name": "Auto Queue Player", "email": email,
                        "password": password},
                  timeout=10)
    player_tok = _login(email, password)
    me = requests.get(f"{API}/auth/me", headers=_h(player_tok), timeout=10).json()
    # Seat via invite token (idempotent — accept is a no-op if already member).
    camp = requests.get(f"{API}/campaigns/{MAIDEN_CID}", headers=_h(admin_tok), timeout=10).json()
    if me["id"] not in (camp.get("member_ids") or []):
        token = camp.get("invite_token")
        assert token, "campaign missing invite_token — admin must regenerate"
        r = requests.post(f"{API}/invites/{token}/accept",
                           headers=_h(player_tok), timeout=10)
        assert r.status_code in (200, 409), r.text
    # Ensure player has a character on this campaign.
    chars = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                          headers=_h(admin_tok), timeout=10).json()
    mine = [c for c in chars if c.get("owner_id") == me["id"]]
    if not mine:
        r = requests.post(
            f"{API}/characters", headers=_h(player_tok),
            json={"campaign_id": MAIDEN_CID, "name": "AutoQueue Hero",
                  "system_id": "besm-4e", "concept": "test",
                  "stats": {"body": 4, "mind": 4, "soul": 4},
                  "attributes": [], "skills": [], "defects": []},
            timeout=10,
        )
        assert r.status_code == 200, r.text
        char_id = r.json()["id"]
    else:
        char_id = mine[0]["id"]
    return player_tok, char_id, me["id"]


def _set_gate(admin_tok: str, on: bool):
    r = requests.patch(f"{API}/campaigns/{MAIDEN_CID}/settings/approval",
                       headers=_h(admin_tok),
                       json={"gm_approval_required": on}, timeout=10)
    assert r.status_code == 200, r.text


class TestAutoQueueCharacterPUT:
    def test_player_put_queued_when_gate_on(self):
        admin_tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        player_tok, char_id, _pid = _ensure_test_player(admin_tok)
        _set_gate(admin_tok, True)
        try:
            r = requests.put(
                f"{API}/characters/{char_id}", headers=_h(player_tok),
                json={"campaign_id": MAIDEN_CID, "name": "Renamed by Player",
                      "system_id": "besm-4e", "concept": "renamed",
                      "stats": {"body": 4, "mind": 4, "soul": 4},
                      "attributes": [], "skills": [], "defects": []},
                timeout=15,
            )
            assert r.status_code == 202, r.text
            body = r.json()
            assert body["queued"] is True
            assert body["change_request"]["status"] == "pending"
            assert body["change_request"]["auto_queued"] is True
            # Character should NOT yet be renamed.
            chk = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                                headers=_h(admin_tok), timeout=10).json()
            ch = next(c for c in chk if c["id"] == char_id)
            assert ch["name"] != "Renamed by Player", \
                "character must not be renamed until GM approves"
        finally:
            _set_gate(admin_tok, False)

    def test_gm_put_writes_through_even_when_gate_on(self):
        admin_tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        _player_tok, char_id, _pid = _ensure_test_player(admin_tok)
        _set_gate(admin_tok, True)
        try:
            # Admin (= GM here) writes directly.
            r = requests.put(
                f"{API}/characters/{char_id}", headers=_h(admin_tok),
                json={"campaign_id": MAIDEN_CID, "name": "GM Direct Edit",
                      "system_id": "besm-4e", "concept": "direct",
                      "stats": {"body": 4, "mind": 4, "soul": 4},
                      "attributes": [], "skills": [], "defects": []},
                timeout=15,
            )
            assert r.status_code == 200, r.text
            # Confirm direct write.
            chk = requests.get(f"{API}/campaigns/{MAIDEN_CID}/characters",
                                headers=_h(admin_tok), timeout=10).json()
            ch = next(c for c in chk if c["id"] == char_id)
            assert ch["name"] == "GM Direct Edit"
        finally:
            _set_gate(admin_tok, False)

    def test_player_put_direct_when_gate_off(self):
        admin_tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        player_tok, char_id, _pid = _ensure_test_player(admin_tok)
        _set_gate(admin_tok, False)  # already off, but be explicit
        r = requests.put(
            f"{API}/characters/{char_id}", headers=_h(player_tok),
            json={"campaign_id": MAIDEN_CID, "name": "Renamed Direct",
                  "system_id": "besm-4e", "concept": "direct",
                  "stats": {"body": 4, "mind": 4, "soul": 4},
                  "attributes": [], "skills": [], "defects": []},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Renamed Direct"


class TestAutoQueueFolioInventory:
    def test_inventory_patch_queued_when_gate_on(self):
        admin_tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        player_tok, char_id, _pid = _ensure_test_player(admin_tok)
        _set_gate(admin_tok, True)
        try:
            r = requests.patch(
                f"{API}/characters/{char_id}/folio", headers=_h(player_tok),
                json={"bucket": "inventory_state",
                      "patch": {"readied_ids": ["test-item-queued"]}},
                timeout=15,
            )
            assert r.status_code == 202, r.text
            assert r.json()["queued"] is True
        finally:
            _set_gate(admin_tok, False)

    def test_non_inventory_folio_not_queued(self):
        """Other folio buckets (dnd_state spell prep, recovery toggles)
        are during-play state and should NOT route through approval."""
        admin_tok = _login(ADMIN_EMAIL, ADMIN_PASS)
        player_tok, char_id, _pid = _ensure_test_player(admin_tok)
        _set_gate(admin_tok, True)
        try:
            r = requests.patch(
                f"{API}/characters/{char_id}/folio", headers=_h(player_tok),
                json={"bucket": "dnd_state",
                      "patch": {"spells_prepared": ["fireball"]}},
                timeout=15,
            )
            # 200 — direct write since not inventory.
            assert r.status_code == 200, r.text
            assert r.json()["ok"] is True
        finally:
            _set_gate(admin_tok, False)
