"""V6.25.36 — Super-admin seed + Voice Lines + Macro Resolver (Cypher / Anime5E)."""
import io
import os
import time
import uuid
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://rules-forge.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"
PLAYER_PASS = "PieBan18!!"

CYPHER_CAMP = "dac42099dfcf4f7b8deabd1ed043ec00"
VEX_ID = "7fb9f4341cf741c5a1f16fd42b4764cf"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    return r


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


# ------------ super-admin seed ------------
class TestSuperAdminSeed:
    def test_admin_login(self):
        r = _login(ADMIN_EMAIL, ADMIN_PASS)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("role") == "admin"
        assert d.get("name") == "TableGnostic Admin"
        assert "access_token" in d


# ------------ shared fixtures ------------
@pytest.fixture(scope="module")
def admin_token():
    r = _login(ADMIN_EMAIL, ADMIN_PASS)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def gm_token():
    r = _login(GM_EMAIL, GM_PASS)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def cypher_session(gm_token):
    """Create or reuse a session under the cypher campaign."""
    r = requests.post(f"{API}/sessions",
                      json={"campaign_id": CYPHER_CAMP, "title": "TEST_v62536_voice_session"},
                      headers=_hdr(gm_token), timeout=30)
    assert r.status_code in (200, 201), r.text
    return r.json()


# ------------ voice lines ------------
class TestVoiceLines:
    def test_create_voice_line_synthetic(self, gm_token, cypher_session):
        sid = cypher_session["id"]
        # 4KB of bytes — synthetic; Whisper will likely fail/return empty, but row stored.
        audio = b"\x1aE\xdf\xa3" + os.urandom(4096)
        files = {"audio": ("voice.webm", io.BytesIO(audio), "audio/webm")}
        data = {
            "character_id": VEX_ID,
            "started_at": "2026-01-15T10:00:00+00:00",
            "ended_at": "2026-01-15T10:00:02+00:00",
        }
        r = requests.post(f"{API}/sessions/{sid}/voice-lines",
                          files=files, data=data, headers=_hdr(gm_token), timeout=60)
        assert r.status_code == 200, r.text
        out = r.json().get("voice_line")
        assert out and out.get("id") and out.get("character_name")
        assert "transcribed" in out
        # save id for downstream tests
        TestVoiceLines.created_id = out["id"]

    def test_empty_body_400(self, gm_token, cypher_session):
        sid = cypher_session["id"]
        files = {"audio": ("v.webm", io.BytesIO(b""), "audio/webm")}
        data = {"character_id": VEX_ID, "started_at": "2026-01-15T10:00:00+00:00", "ended_at": "2026-01-15T10:00:01+00:00"}
        r = requests.post(f"{API}/sessions/{sid}/voice-lines", files=files, data=data,
                          headers=_hdr(gm_token), timeout=30)
        assert r.status_code == 400, r.text

    def test_bogus_mime_415(self, gm_token, cypher_session):
        sid = cypher_session["id"]
        files = {"audio": ("v.txt", io.BytesIO(b"hello world"), "text/plain")}
        data = {"character_id": VEX_ID, "started_at": "2026-01-15T10:00:00+00:00", "ended_at": "2026-01-15T10:00:01+00:00"}
        r = requests.post(f"{API}/sessions/{sid}/voice-lines", files=files, data=data,
                          headers=_hdr(gm_token), timeout=30)
        assert r.status_code == 415, r.text

    def test_oversize_413(self, gm_token, cypher_session):
        sid = cypher_session["id"]
        big = os.urandom(13 * 1024 * 1024)
        files = {"audio": ("v.webm", io.BytesIO(big), "audio/webm")}
        data = {"character_id": VEX_ID, "started_at": "2026-01-15T10:00:00+00:00", "ended_at": "2026-01-15T10:00:01+00:00"}
        r = requests.post(f"{API}/sessions/{sid}/voice-lines", files=files, data=data,
                          headers=_hdr(gm_token), timeout=120)
        assert r.status_code == 413, r.text

    def test_list_voice_lines(self, gm_token, cypher_session):
        sid = cypher_session["id"]
        r = requests.get(f"{API}/sessions/{sid}/voice-lines", headers=_hdr(gm_token), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "voice_lines" in d and "count" in d
        assert isinstance(d["voice_lines"], list)
        # Should contain the one created
        ids = [v["id"] for v in d["voice_lines"]]
        assert getattr(TestVoiceLines, "created_id", None) in ids

    def test_patch_text_as_gm(self, gm_token, cypher_session):
        sid = cypher_session["id"]
        vid = getattr(TestVoiceLines, "created_id", None)
        if not vid:
            pytest.skip("no created id")
        r = requests.patch(f"{API}/sessions/{sid}/voice-lines/{vid}",
                           json={"text": "corrected line"}, headers=_hdr(gm_token), timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["voice_line"]["text"] == "corrected line"

    def test_delete_as_gm(self, gm_token, cypher_session):
        sid = cypher_session["id"]
        vid = getattr(TestVoiceLines, "created_id", None)
        if not vid:
            pytest.skip("no created id")
        r = requests.delete(f"{API}/sessions/{sid}/voice-lines/{vid}", headers=_hdr(gm_token), timeout=30)
        assert r.status_code == 200, r.text


# ------------ Macro Resolver (Cypher + Anime5E) — unit tests ------------
class TestMacroResolver:
    def test_cypher_tokens(self):
        from routes.channels import _expand_macro_tokens
        char = {
            "folio": {
                "cypher_state": {
                    "pools": {"Might": 14, "Speed": 12, "Intellect": 18},
                    "edges": {"Might": 1, "Speed": 0, "Intellect": 2},
                    "effort": 2, "tier": 3,
                }
            }
        }
        out = _expand_macro_tokens(
            "1d20 {stat:Might} {stat:Intellect} {derived:edge_intellect} {derived:effort} {derived:tier}",
            char)
        # tokens substitute as +N (signed)
        assert "+14" in out
        assert "+18" in out
        assert "+2" in out
        assert "+3" in out

    def test_anime5e_point_buys(self):
        from routes.channels import _expand_macro_tokens
        char = {
            "folio": {
                "anime5e_state": {
                    "point_buys": [{"name": "Combat Mastery", "level": 2, "cost_per_level": 3}]
                }
            },
            "attributes": [],
        }
        out = _expand_macro_tokens("1d20 {attr:Combat Mastery}", char)
        assert "+2" in out
