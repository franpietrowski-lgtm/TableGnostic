"""V6.25.6 — Cut B chat hot-keys: /cast /use bundle /spend xp.

Verifies:
1. /cast resolves a spell from the campaign reference or custom pool;
   shows a "miss" envelope when the name doesn't match (so the chat
   line still renders as flavour).
2. /use bundle resolves a power_bundle from references.
3. /spend xp queues a proper XP-pending row on the speaker's active
   character — visible in the GM XP Approval Queue endpoint.
4. The per-campaign `xp_marketplace` toggle gates /spend xp.
"""
from __future__ import annotations
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def campaign(gm_token):
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token),
                       json={"name": "V6256 hotkey-test", "system_id": "anime-5e"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


@pytest.fixture()
def channel(gm_token, campaign):
    rs = requests.get(f"{BASE_URL}/api/campaigns/{campaign}/channels",
                       headers=H(gm_token))
    assert rs.status_code == 200, rs.text
    rows = rs.json()
    if rows:
        return rows[0]["id"]
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/channels",
                       headers=H(gm_token),
                       json={"name": "general", "kind": "text"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


@pytest.fixture()
def character_with_xp(gm_token, campaign):
    """A character owned by the GM-as-speaker with enough unspent XP."""
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token),
                       json={"campaign_id": campaign,
                             "name": "V6256 Spellslinger",
                             "stats": {"body": 4, "mind": 5, "soul": 4}})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    # Award unspent XP via the canonical endpoint.
    awd = requests.post(f"{BASE_URL}/api/characters/{cid}/xp",
                          headers=H(gm_token),
                          json={"amount": 12.0,
                                "reason": "test seed for hot-key spend"})
    assert awd.status_code == 200, awd.text
    yield cid
    requests.delete(f"{BASE_URL}/api/characters/{cid}",
                     headers=H(gm_token))


def _post_msg(token, chid, text):
    r = requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                       headers=H(token), json={"body": text, "attachments": []})
    assert r.status_code == 200, r.text
    return r.json()


def test_cast_resolves_a_known_spell(gm_token, campaign, channel):
    """A custom spell-shaped reference resolves through /cast."""
    # Author a spell-mimic homebrew via custom_attributes (kind=ability)
    # which the server-side resolver treats as a generic hit.
    requests.post(f"{BASE_URL}/api/campaigns/{campaign}/custom",
                   headers=H(gm_token),
                   json={"campaign_id": campaign, "kind": "ability",
                         "name": "V6256 Sunbolt",
                         "cost_per_level": 1,
                         "description_note": "A bolt of sun-fire, 3d6 radiant."})
    msg = _post_msg(gm_token, channel, "/cast V6256 Sunbolt")
    assert msg["kind"] == "cast"
    assert msg["slash_meta"]["kind"] == "cast"
    assert msg["slash_meta"]["name"] == "V6256 Sunbolt"
    res = msg["slash_meta"]["resolved"]
    assert res.get("hit") is True
    assert res["name"] == "V6256 Sunbolt"
    assert "Sun-fire" in res["description"] or "sun-fire" in res["description"]


def test_cast_unknown_spell_renders_miss(gm_token, campaign, channel):
    msg = _post_msg(gm_token, channel, "/cast Doesnotexistforreal")
    assert msg["kind"] == "cast"
    assert msg["slash_meta"]["resolved"]["miss"] is True


def test_use_bundle_resolves_power_bundle(gm_token, campaign, channel):
    # Reference Editor authored bundle.
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/reference",
                       headers=H(gm_token),
                       json={"kind": "power_bundle",
                             "name": "V6256 Star Volley",
                             "summary": "Twin starlight arrows.",
                             "fields": {"description": "3d8 radiant arrows.",
                                         "invocation": "per-day",
                                         "charges_max": 3,
                                         "energy_cost": 0,
                                         "cooldown": "long rest"}})
    assert r.status_code == 200, r.text
    msg = _post_msg(gm_token, channel, "/use bundle V6256 Star Volley")
    assert msg["kind"] == "use_bundle"
    res = msg["slash_meta"]["resolved"]
    assert res["hit"] is True
    assert res["charges_max"] == 3
    assert res["invocation"] == "per-day"


def test_spend_xp_queues_a_proposal(gm_token, campaign, channel,
                                      character_with_xp):
    # Sanity — ensure the character has unspent XP to draw against.
    ch = requests.get(f"{BASE_URL}/api/characters/{character_with_xp}",
                        headers=H(gm_token)).json()
    assert ch.get("xp_unspent", 0) >= 5

    msg = _post_msg(gm_token, channel,
                     "/spend xp 5 for raise Body to 5")
    assert msg["kind"] == "spend_xp"
    p = msg["slash_meta"]["proposal"]
    assert p.get("error") is None, p
    assert p["status"] == "queued"
    assert p["character_id"] == character_with_xp

    # The GM XP-approval queue should now contain the proposal.
    q = requests.get(f"{BASE_URL}/api/campaigns/{campaign}/xp-pending",
                       headers=H(gm_token))
    assert q.status_code == 200, q.text
    pending = q.json()
    match = next((r for r in pending if r["id"] == p["proposal_id"]), None)
    assert match is not None
    assert match["cost"] == 5.0
    assert match["change"] == {"raise_total_points": 5}
    assert match["source"] == "chat-hotkey"


def test_spend_xp_blocked_when_marketplace_disabled(gm_token, campaign,
                                                      channel, character_with_xp):
    """GM toggle off → /spend xp returns an error envelope, no queue
    row created."""
    cur = requests.get(f"{BASE_URL}/api/campaigns/{campaign}",
                         headers=H(gm_token)).json()
    payload = {**cur, "xp_marketplace": False}
    for k in ("id", "gm_id", "gm_name", "member_ids", "invite_token",
              "created_at", "updated_at", "is_gm", "current_user_id"):
        payload.pop(k, None)
    upd = requests.put(f"{BASE_URL}/api/campaigns/{campaign}",
                         headers=H(gm_token), json=payload)
    assert upd.status_code == 200, upd.text

    before = len(requests.get(f"{BASE_URL}/api/campaigns/{campaign}/xp-pending",
                                headers=H(gm_token)).json())
    msg = _post_msg(gm_token, channel,
                     "/spend xp 3 for buy Mind feat")
    p = msg["slash_meta"]["proposal"]
    assert "disabled" in (p.get("error") or "").lower(), p
    after = len(requests.get(f"{BASE_URL}/api/campaigns/{campaign}/xp-pending",
                               headers=H(gm_token)).json())
    assert before == after  # no proposal added when toggle is off


def test_spend_xp_insufficient_balance_error(gm_token, campaign, channel,
                                                character_with_xp):
    """Asking for more than xp_unspent returns an error envelope."""
    msg = _post_msg(gm_token, channel,
                     "/spend xp 999 for break the budget")
    p = msg["slash_meta"]["proposal"]
    assert "insufficient" in (p.get("error") or "").lower(), p
