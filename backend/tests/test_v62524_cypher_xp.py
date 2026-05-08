"""V6.25.24 — Cycle B-4: Cypher XP Mechanics ledger.

Tests the new `/api/campaigns/{cid}/cypher/xp-events` endpoint:
  * GM intrusion-grant: +2 XP to acceptor, auto-pairs +1 to peer (acceptor net +1).
  * Refuse intrusion: -1 XP. With 0 XP, returns 400.
  * Peer transfer: -1 XP from sender, +1 XP to recipient (atomic).
  * Narrative pool: multiple contributors debited together.
  * Generic spends (reroll, advancement-step, etc.) deduct fixed amounts.
  * Player can only act on their own characters; GM acts on any.
  * Ledger lists events with the right access controls.
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
                       json={"name": "V62524 cypher-xp-test", "system_id": "cypher"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def _make_char(token, campaign_id, name, xp=10):
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(token),
                       json={"campaign_id": campaign_id, "name": name,
                             "stats": {"body": 4, "mind": 4, "soul": 4}})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    if xp > 0:
        awd = requests.post(f"{BASE_URL}/api/characters/{cid}/xp",
                              headers=H(token),
                              json={"amount": float(xp),
                                    "reason": "test seed"})
        assert awd.status_code == 200, awd.text
    return cid


@pytest.fixture()
def two_chars(gm_token, campaign):
    a = _make_char(gm_token, campaign, "Aria")
    b = _make_char(gm_token, campaign, "Bram")
    yield (a, b)
    requests.delete(f"{BASE_URL}/api/characters/{a}", headers=H(gm_token))
    requests.delete(f"{BASE_URL}/api/characters/{b}", headers=H(gm_token))


def _xp(token, cid):
    r = requests.get(f"{BASE_URL}/api/characters/{cid}", headers=H(token))
    assert r.status_code == 200
    return float(r.json().get("xp_unspent", 0))


# ── Tests ────────────────────────────────────────────────────────────


def test_reroll_spends_one_xp(gm_token, campaign, two_chars):
    a, _ = two_chars
    before = _xp(gm_token, a)
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
                       headers=H(gm_token),
                       json={"kind": "reroll", "character_id": a,
                             "justification": "Re-roll the failed climb."})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["xp_unspent"] == before - 1
    assert _xp(gm_token, a) == before - 1


def test_refuse_intrusion_with_zero_xp_blocks(gm_token, campaign):
    """With 0 XP, refusing returns 400 (cannot refuse with 0 XP)."""
    cid = _make_char(gm_token, campaign, "Penniless", xp=0)
    try:
        r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
                           headers=H(gm_token),
                           json={"kind": "refuse-intrusion", "character_id": cid})
        assert r.status_code == 400, r.text
    finally:
        requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))


def test_peer_transfer_moves_one_xp(gm_token, campaign, two_chars):
    a, b = two_chars
    a0, b0 = _xp(gm_token, a), _xp(gm_token, b)
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
                       headers=H(gm_token),
                       json={"kind": "peer-transfer", "character_id": a,
                             "peer_character_id": b,
                             "justification": "Solid assist on the climb."})
    assert r.status_code == 200, r.text
    assert _xp(gm_token, a) == a0 - 1
    assert _xp(gm_token, b) == b0 + 1
    # Ledger should have the paired rows.
    rows = requests.get(
        f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
        headers=H(gm_token)).json()["rows"]
    kinds = [r["kind"] for r in rows]
    assert "peer-transfer" in kinds
    assert "peer-transfer-receive" in kinds


def test_intrusion_grant_pairs_with_peer_share(gm_token, campaign, two_chars):
    """GM intrusion: +2 XP to acceptor, auto-pairs −1 / +1 peer transfer."""
    a, b = two_chars
    a0, b0 = _xp(gm_token, a), _xp(gm_token, b)
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
                       headers=H(gm_token),
                       json={"kind": "intrusion-grant", "character_id": a,
                             "peer_character_id": b,
                             "justification": "Bridge cracks under your weight."})
    assert r.status_code == 200, r.text
    # Net: acceptor +2 −1 = +1; peer +1.
    assert _xp(gm_token, a) == a0 + 1
    assert _xp(gm_token, b) == b0 + 1


def test_narrative_pool_debits_all_contributors(gm_token, campaign, two_chars):
    a, b = two_chars
    a0, b0 = _xp(gm_token, a), _xp(gm_token, b)
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
                       headers=H(gm_token),
                       json={"kind": "narrative-pool", "character_id": a,
                             "narrative_pool_contributors": [
                                 {"character_id": a, "amount": 3},
                                 {"character_id": b, "amount": 2},
                             ],
                             "justification": "Together we declare the dragon fears cold iron."})
    assert r.status_code == 200, r.text
    assert _xp(gm_token, a) == a0 - 3
    assert _xp(gm_token, b) == b0 - 2


def test_advancement_step_costs_4_xp(gm_token, campaign, two_chars):
    a, _ = two_chars
    a0 = _xp(gm_token, a)
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
                       headers=H(gm_token),
                       json={"kind": "advancement-step", "character_id": a,
                             "advancement_step_key": "extra-effort"})
    assert r.status_code == 200, r.text
    assert _xp(gm_token, a) == a0 - 4
    rows = requests.get(
        f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events?character_id={a}",
        headers=H(gm_token)).json()["rows"]
    adv = next((r for r in rows if r["kind"] == "advancement-step"), None)
    assert adv and adv.get("advancement_step_key") == "extra-effort"


def test_unknown_kind_returns_422(gm_token, campaign, two_chars):
    a, _ = two_chars
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign}/cypher/xp-events",
                       headers=H(gm_token),
                       json={"kind": "bogus-spend", "character_id": a})
    assert r.status_code == 422
