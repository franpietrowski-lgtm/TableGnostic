"""V6.25.8 — Genesis archive endpoint authorization.

Confirms GM gets 200 (list) and non-GM (player) gets 403 on
GET /api/campaigns/{cid}/genesis/archives.
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


@pytest.fixture(scope="module")
def player_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "albanaszak@ymail.com",
                            "password": "AuroraTest123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def besm_campaign(gm_token):
    payload = {"name": "TEST_V6258 genesis-403", "system_id": "besm-4e"}
    r = requests.post(f"{BASE_URL}/api/campaigns",
                      headers=H(gm_token), json=payload)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm_token))


def test_genesis_archives_gm_200(gm_token, besm_campaign):
    r = requests.get(f"{BASE_URL}/api/campaigns/{besm_campaign}/genesis/archives",
                     headers=H(gm_token))
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_genesis_archives_non_gm_403(player_token, besm_campaign):
    r = requests.get(f"{BASE_URL}/api/campaigns/{besm_campaign}/genesis/archives",
                     headers=H(player_token))
    assert r.status_code == 403, r.text
