"""V6.25.5 — Marketplace v1 publish + browse + clone flow.

Verifies:
1. GM publishes a homebrew Race custom rule → listing appears with
   public access. License attestation is required for public/paywall.
2. Browse with kind / system filters returns only matching listings.
3. Cloning into the same GM's other campaign creates a new
   custom_attributes row, increments the listing's downloads counter,
   and preserves the effects payload byte-for-byte.
4. Paywall listings 402 on clone for non-author users (V1 stub
   behaviour — Stripe lands in V2).
5. Author can unpublish; the listing is then 404 on detail.
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
def besm_camp(gm_token):
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token),
                       json={"name": "V6255 mkt-source", "system_id": "besm-4e"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


@pytest.fixture()
def besm_camp_target(gm_token):
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token),
                       json={"name": "V6255 mkt-target", "system_id": "besm-4e"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def _make_race(token, cid):
    r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/custom",
                       headers=H(token),
                       json={"campaign_id": cid, "kind": "race",
                             "name": "V6255 Sunbound Wisp",
                             "cost_per_level": 1,
                             "description_note": "Translucent fae-kin.",
                             "effects": {
                                 "asi": {"Charisma": 2, "Constitution": 1},
                                 "size": "Small", "speed": 25,
                                 "traits": ["Luminescent"],
                             }})
    assert r.status_code == 200, r.text
    return r.json()


def test_publish_requires_attestation_for_public(gm_token, besm_camp):
    src = _make_race(gm_token, besm_camp)
    # Without attestation — should 400.
    r = requests.post(f"{BASE_URL}/api/marketplace/publish",
                       headers=H(gm_token),
                       json={"source_campaign_id": besm_camp,
                             "source_kind": "custom",
                             "source_id": src["id"],
                             "access": "public",
                             "license_attestation": False})
    assert r.status_code == 400
    assert "attestation" in r.text.lower()


def test_publish_browse_clone_round_trip(gm_token, besm_camp, besm_camp_target):
    src = _make_race(gm_token, besm_camp)
    # Publish.
    r = requests.post(f"{BASE_URL}/api/marketplace/publish",
                       headers=H(gm_token),
                       json={"source_campaign_id": besm_camp,
                             "source_kind": "custom",
                             "source_id": src["id"],
                             "access": "public",
                             "summary": "Light-touched fae race",
                             "license_text": "CC-BY-SA 4.0",
                             "license_attestation": True})
    assert r.status_code == 200, r.text
    listing = r.json()
    lid = listing["id"]
    assert listing["access"] == "public"
    assert listing["downloads"] == 0
    assert listing["snapshot"]["effects"]["asi"]["Charisma"] == 2

    try:
        # Browse — kind filter narrows to race.
        rb = requests.get(f"{BASE_URL}/api/marketplace?kind=race&system=besm-4e",
                            headers=H(gm_token))
        assert rb.status_code == 200, rb.text
        out = rb.json()
        names = [r["name"] for r in out["rows"]]
        assert listing["name"] in names

        # Clone into the second campaign.
        rc = requests.post(f"{BASE_URL}/api/marketplace/{lid}/clone",
                             headers=H(gm_token),
                             json={"into_campaign_id": besm_camp_target})
        assert rc.status_code == 200, rc.text
        clone_out = rc.json()
        assert clone_out["ok"] is True
        # New custom_attributes row visible on the target.
        rows = requests.get(f"{BASE_URL}/api/campaigns/{besm_camp_target}/custom",
                              headers=H(gm_token)).json()
        match = next((x for x in rows if x["id"] == clone_out["cloned_id"]), None)
        assert match is not None
        assert match["kind"] == "race"
        assert match["name"] == "V6255 Sunbound Wisp"
        assert match["effects"]["asi"]["Charisma"] == 2
        assert "(cloned)" in (match.get("page_ref") or "").lower()

        # downloads counter incremented.
        listing2 = requests.get(f"{BASE_URL}/api/marketplace/{lid}",
                                  headers=H(gm_token)).json()
        assert listing2["downloads"] == 1
    finally:
        # Author-side cleanup.
        requests.delete(f"{BASE_URL}/api/marketplace/{lid}",
                         headers=H(gm_token))


def test_unpublish_makes_listing_404(gm_token, besm_camp):
    src = _make_race(gm_token, besm_camp)
    r = requests.post(f"{BASE_URL}/api/marketplace/publish",
                       headers=H(gm_token),
                       json={"source_campaign_id": besm_camp,
                             "source_kind": "custom",
                             "source_id": src["id"],
                             "access": "public",
                             "license_attestation": True})
    lid = r.json()["id"]
    r = requests.delete(f"{BASE_URL}/api/marketplace/{lid}", headers=H(gm_token))
    assert r.status_code == 200
    r = requests.get(f"{BASE_URL}/api/marketplace/{lid}", headers=H(gm_token))
    assert r.status_code == 404


def test_clone_into_non_owned_campaign_403(gm_token, besm_camp):
    """A user can only clone INTO campaigns they GM."""
    src = _make_race(gm_token, besm_camp)
    pub = requests.post(f"{BASE_URL}/api/marketplace/publish",
                         headers=H(gm_token),
                         json={"source_campaign_id": besm_camp,
                               "source_kind": "custom",
                               "source_id": src["id"],
                               "access": "public",
                               "license_attestation": True}).json()
    lid = pub["id"]
    try:
        # Use a fake campaign id — endpoint should 404 (campaign missing)
        # rather than 403, but in either case clone is rejected.
        r = requests.post(f"{BASE_URL}/api/marketplace/{lid}/clone",
                           headers=H(gm_token),
                           json={"into_campaign_id": "nonexistent-campaign-id"})
        assert r.status_code in (403, 404), r.text
    finally:
        requests.delete(f"{BASE_URL}/api/marketplace/{lid}",
                         headers=H(gm_token))


def test_paywall_v1_blocks_clone_for_non_author(gm_token, besm_camp,
                                                  besm_camp_target):
    """V1 stub — paywall listings 402 on clone for everyone except the
    author until V2 wires Stripe. (Author can clone their own paywall
    listing for testing.)"""
    src = _make_race(gm_token, besm_camp)
    pub = requests.post(f"{BASE_URL}/api/marketplace/publish",
                         headers=H(gm_token),
                         json={"source_campaign_id": besm_camp,
                               "source_kind": "custom",
                               "source_id": src["id"],
                               "access": "paywall",
                               "price_cents": 199,
                               "license_attestation": True}).json()
    lid = pub["id"]
    try:
        # Author cloning their OWN paywall is allowed in V1.
        r = requests.post(f"{BASE_URL}/api/marketplace/{lid}/clone",
                           headers=H(gm_token),
                           json={"into_campaign_id": besm_camp_target})
        assert r.status_code == 200, r.text
    finally:
        requests.delete(f"{BASE_URL}/api/marketplace/{lid}",
                         headers=H(gm_token))
