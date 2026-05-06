"""V6.25.6 — Marketplace subscription / digest tests.

Verifies:
1. Create subscription with kind+system filters, list mine, delete.
2. Subscription requires at least one filter (kind OR system).
3. Digest returns 0 new for fresh sub, then N new after a publish that
   matches the filter.
4. mark_seen=true bumps last_check so subsequent digests are 0 again.
"""
from __future__ import annotations
import os
import time
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
                       json={"name": "V6256 mkt-sub-src", "system_id": "besm-4e"})
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_subscription_requires_filter(gm_token):
    r = requests.post(f"{BASE_URL}/api/marketplace-subscriptions",
                       headers=H(gm_token), json={})
    assert r.status_code == 400


def test_subscription_crud_and_digest(gm_token, besm_camp):
    # 1. Subscribe to BESM races.
    r = requests.post(f"{BASE_URL}/api/marketplace-subscriptions",
                       headers=H(gm_token),
                       json={"kind": "race", "system": "besm-4e",
                             "label": "BESM races"})
    assert r.status_code == 200, r.text
    sub = r.json()
    sid = sub["id"]
    try:
        # 2. List mine → at least our new sub appears.
        rows = requests.get(f"{BASE_URL}/api/marketplace-subscriptions",
                              headers=H(gm_token)).json()
        assert any(s["id"] == sid for s in rows)

        # 3. Initial digest → 0 new (the sub was just created).
        d0 = requests.get(f"{BASE_URL}/api/marketplace-digest",
                            headers=H(gm_token)).json()
        bucket0 = next((b for b in d0["buckets"] if b["subscription_id"] == sid), None)
        assert bucket0 is not None
        assert bucket0["new_count"] == 0

        # 4. Publish a matching listing.
        # Author the source first.
        time.sleep(1)  # ensure created_at > sub.last_check
        custom = requests.post(f"{BASE_URL}/api/campaigns/{besm_camp}/custom",
                                 headers=H(gm_token),
                                 json={"campaign_id": besm_camp, "kind": "race",
                                       "name": "V6256 sub-test Sun-Wisp",
                                       "cost_per_level": 1,
                                       "description_note": "Test race for sub digest."}).json()
        pub = requests.post(f"{BASE_URL}/api/marketplace/publish",
                              headers=H(gm_token),
                              json={"source_campaign_id": besm_camp,
                                    "source_kind": "custom",
                                    "source_id": custom["id"],
                                    "access": "public",
                                    "license_attestation": True}).json()
        try:
            # 5. Digest should now show 1 new for this bucket.
            d1 = requests.get(f"{BASE_URL}/api/marketplace-digest",
                                 headers=H(gm_token)).json()
            bucket1 = next(b for b in d1["buckets"] if b["subscription_id"] == sid)
            assert bucket1["new_count"] == 1
            assert any(p["name"] == "V6256 sub-test Sun-Wisp" for p in bucket1["preview"])

            # 6. mark_seen=true → digest goes back to 0.
            requests.get(f"{BASE_URL}/api/marketplace-digest?mark_seen=true",
                          headers=H(gm_token))
            d2 = requests.get(f"{BASE_URL}/api/marketplace-digest",
                                headers=H(gm_token)).json()
            bucket2 = next(b for b in d2["buckets"] if b["subscription_id"] == sid)
            assert bucket2["new_count"] == 0
        finally:
            requests.delete(f"{BASE_URL}/api/marketplace/{pub['id']}",
                             headers=H(gm_token))
    finally:
        # Delete sub.
        rd = requests.delete(f"{BASE_URL}/api/marketplace-subscriptions/{sid}",
                               headers=H(gm_token))
        assert rd.status_code == 200


def test_subscription_kind_filter_excludes_other_kinds(gm_token, besm_camp):
    """A sub for kind=class shouldn't see a kind=race listing."""
    sub = requests.post(f"{BASE_URL}/api/marketplace-subscriptions",
                         headers=H(gm_token),
                         json={"kind": "class", "system": "besm-4e"}).json()
    try:
        time.sleep(1)
        custom = requests.post(f"{BASE_URL}/api/campaigns/{besm_camp}/custom",
                                 headers=H(gm_token),
                                 json={"campaign_id": besm_camp, "kind": "race",
                                       "name": "V6256 kind-filter test",
                                       "cost_per_level": 1}).json()
        pub = requests.post(f"{BASE_URL}/api/marketplace/publish",
                              headers=H(gm_token),
                              json={"source_campaign_id": besm_camp,
                                    "source_kind": "custom",
                                    "source_id": custom["id"],
                                    "access": "public",
                                    "license_attestation": True}).json()
        try:
            d = requests.get(f"{BASE_URL}/api/marketplace-digest",
                               headers=H(gm_token)).json()
            bucket = next(b for b in d["buckets"]
                            if b["subscription_id"] == sub["id"])
            # Filter is kind=class but the listing was kind=race → 0.
            assert bucket["new_count"] == 0
        finally:
            requests.delete(f"{BASE_URL}/api/marketplace/{pub['id']}",
                             headers=H(gm_token))
    finally:
        requests.delete(f"{BASE_URL}/api/marketplace-subscriptions/{sub['id']}",
                         headers=H(gm_token))
