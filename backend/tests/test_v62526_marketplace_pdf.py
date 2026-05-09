"""V6.25.26 — Marketplace per-archive share + PDF chronicle export."""
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
def campaign_with_archive(gm_token):
    # Create fresh campaign
    r = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm_token),
                       json={"name": "V62526 mkt-pdf", "system_id": "besm-4e"})
    cid = r.json()["id"]
    # Seed initial genesis (creates record)
    g1 = requests.put(f"{BASE_URL}/api/campaigns/{cid}/genesis", headers=H(gm_token),
                       json={"campaign_id": cid, "logline": "First draft",
                             "title": "TestArchive"})
    assert g1.status_code == 200, g1.text
    # Update again — that triggers archive creation of v1
    g2 = requests.put(f"{BASE_URL}/api/campaigns/{cid}/genesis", headers=H(gm_token),
                       json={"campaign_id": cid, "logline": "Second draft",
                             "title": "TestArchive"})
    assert g2.status_code == 200, g2.text
    arch_list = requests.get(f"{BASE_URL}/api/campaigns/{cid}/genesis/archives",
                               headers=H(gm_token)).json()
    assert isinstance(arch_list, list) and len(arch_list) >= 1
    aid = arch_list[0]["archive_id"]
    yield cid, aid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


# ── Marketplace per-archive share ─────────────────────────────────────


def test_marketplace_share_requires_attestation(gm_token, campaign_with_archive):
    cid, aid = campaign_with_archive
    r = requests.post(
        f"{BASE_URL}/api/campaigns/{cid}/genesis/archives/{aid}/marketplace-share"
        f"?access=public&license_attestation=false",
        headers=H(gm_token))
    assert r.status_code == 422
    assert "attestation" in r.text.lower()


def test_marketplace_share_paywall_requires_price(gm_token, campaign_with_archive):
    cid, aid = campaign_with_archive
    r = requests.post(
        f"{BASE_URL}/api/campaigns/{cid}/genesis/archives/{aid}/marketplace-share"
        f"?access=paywall&price_cents=0&license_attestation=true",
        headers=H(gm_token))
    assert r.status_code == 422
    assert "price" in r.text.lower() or "paywall" in r.text.lower()


def test_marketplace_share_success_then_duplicate_409(gm_token, campaign_with_archive):
    cid, aid = campaign_with_archive
    r = requests.post(
        f"{BASE_URL}/api/campaigns/{cid}/genesis/archives/{aid}/marketplace-share"
        f"?access=public&license_attestation=true&summary=Cool+seed",
        headers=H(gm_token))
    assert r.status_code == 200, r.text
    listing = r.json()
    assert listing["kind"] == "genesis_archive"
    assert listing["source_id"] == aid
    assert listing["access"] == "public"
    lid = listing["id"]

    # Second share should 409
    r2 = requests.post(
        f"{BASE_URL}/api/campaigns/{cid}/genesis/archives/{aid}/marketplace-share"
        f"?access=public&license_attestation=true",
        headers=H(gm_token))
    assert r2.status_code == 409

    # Clone into a NEW campaign
    nc = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm_token),
                        json={"name": "V62526 mkt-target", "system_id": "besm-4e"}).json()
    target_cid = nc["id"]
    try:
        clone = requests.post(
            f"{BASE_URL}/api/marketplace/{lid}/clone-genesis-archive"
            f"?into_campaign_id={target_cid}",
            headers=H(gm_token))
        assert clone.status_code == 200, clone.text
        body = clone.json()
        assert body["ok"] is True
        assert "archive_id" in body
        # Confirm it shows up in target's archive list
        arch = requests.get(f"{BASE_URL}/api/campaigns/{target_cid}/genesis/archives",
                              headers=H(gm_token)).json()
        assert any(a["archive_id"] == body["archive_id"] for a in arch)
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{target_cid}", headers=H(gm_token))


# ── PDF chronicle export ─────────────────────────────────────────────


def test_pdf_export_returns_valid_stream(gm_token):
    # Create campaign with one session so the PDF has something to render
    c = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm_token),
                       json={"name": "V62526 pdf", "system_id": "besm-4e"}).json()
    cid = c["id"]
    try:
        # Seed a session
        s = requests.post(f"{BASE_URL}/api/sessions", headers=H(gm_token),
                           json={"campaign_id": cid, "title": "Session 1",
                                 "summary": "Bandits routed.",
                                 "narrative": "It was a dark and stormy night."})
        assert s.status_code in (200, 201), s.text
        # Seed material
        requests.post(f"{BASE_URL}/api/campaigns/{cid}/materials", headers=H(gm_token),
                        json={"tier": "raw", "name": "Chronicled Ore",
                              "summary": "Used in pdf appendix."})
        # Seed encounter
        requests.post(f"{BASE_URL}/api/campaigns/{cid}/encounters-library",
                        headers=H(gm_token),
                        json={"name": "Chronicle Skirmish", "encounter_type": "combat"})
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/export.pdf", headers=H(gm_token))
        assert r.status_code == 200, r.text[:300]
        ctype = r.headers.get("content-type", "")
        assert "pdf" in ctype.lower(), f"unexpected content-type: {ctype}"
        # PDF magic header
        assert r.content[:4] == b"%PDF", f"not a PDF stream: {r.content[:20]!r}"
        assert len(r.content) > 500
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))
