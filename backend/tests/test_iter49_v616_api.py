"""V6.16 API smoke tests — converter endpoints + Aurora cross-account access + Eli character shape."""
from __future__ import annotations
import os, pytest, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / "frontend" / ".env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"
AURORA_EMAIL = "albanaszak@ymail.com"
AURORA_PASS = "AuroraTest123!"

ELI_BESM = "244db025742b4bd9a9662f6240e40729"
ELI_CYPHER = "3c37c7ab36004eb3b902d22f4c4c186b"
ELI_DND = "733ff0dc6bb64709b63fea31c16f2afc"
ELI_ANIME = "7da6f4f5d17848ab871ac91b5f1cf0d4"

CAMP_BESM = "3f2ed01a034f4fdb8f5d686089f2e3a9"
CAMP_CYPHER = "7e510c2be80440708622f6a3b2f3dae4"
CAMP_DND = "0b22785861b64c70bf1fae181ca38f84"
CAMP_ANIME = "f68e1b235fbe4f1bab702a05aa7b4467"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def gm_token():
    return _login(GM_EMAIL, GM_PASS)


@pytest.fixture(scope="module")
def aurora_token():
    return _login(AURORA_EMAIL, AURORA_PASS)


# ──────────────── Converter endpoint permission / validation ────────────────
class TestConverterEndpointPermissions:
    def test_player_role_gets_403_on_content_convert(self, aurora_token):
        r = requests.post(
            f"{BASE_URL}/api/convert/content",
            headers={"Authorization": f"Bearer {aurora_token}"},
            json={"source_system": "dnd-5e", "target_system": "cypher", "source_kind": "spell", "payload": {"name": "Fireball"}},
            timeout=15,
        )
        assert r.status_code == 403, f"Expected 403 for player, got {r.status_code}: {r.text[:200]}"

    def test_player_role_gets_403_on_character_convert(self, aurora_token):
        r = requests.post(
            f"{BASE_URL}/api/convert/character",
            headers={"Authorization": f"Bearer {aurora_token}"},
            json={"source_character_id": ELI_BESM, "target_campaign_id": CAMP_CYPHER},
            timeout=15,
        )
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:200]}"

    def test_gm_unknown_target_system_rejected(self, gm_token):
        r = requests.post(
            f"{BASE_URL}/api/convert/content",
            headers={"Authorization": f"Bearer {gm_token}"},
            json={"source_system": "dnd-5e", "target_system": "pathfinder-2e", "source_kind": "spell", "payload": {"name": "Fireball"}},
            timeout=15,
        )
        assert r.status_code in (400, 422), f"Expected 400/422 for bad system, got {r.status_code}: {r.text[:200]}"

    def test_gm_missing_content_rejected(self, gm_token):
        r = requests.post(
            f"{BASE_URL}/api/convert/content",
            headers={"Authorization": f"Bearer {gm_token}"},
            json={"source_system": "dnd-5e", "target_system": "cypher", "source_kind": "spell"},
            timeout=15,
        )
        assert r.status_code in (400, 422), f"Expected 400/422 for missing content, got {r.status_code}"

    def test_gm_convert_character_unknown_source_returns_404_or_400(self, gm_token):
        r = requests.post(
            f"{BASE_URL}/api/convert/character",
            headers={"Authorization": f"Bearer {gm_token}"},
            json={"source_character_id": "nonexistent-zzz", "target_campaign_id": CAMP_CYPHER},
            timeout=15,
        )
        assert r.status_code in (400, 404, 422), f"Expected 400/404/422, got {r.status_code}: {r.text[:200]}"


# ──────────────── Eli character documents shape ────────────────
class TestEliCharacterShapes:
    def test_cypher_eli_has_cypher_state(self, gm_token):
        r = requests.get(f"{BASE_URL}/api/characters/{ELI_CYPHER}",
                         headers={"Authorization": f"Bearer {gm_token}"}, timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        data = r.json()
        assert data["system_id"] == "cypher"
        st = data.get("folio", {}).get("cypher_state", {})
        assert st, "cypher_state missing from folio"
        # At least some of the primitives
        has_tier = "tier" in st
        has_descriptor = "descriptor" in st
        has_type = "type" in st
        has_focus = "focus" in st
        has_pools = "pools" in st
        assert sum([has_tier, has_descriptor, has_type, has_focus, has_pools]) >= 3, f"cypher_state too sparse: {st}"

    def test_dnd_eli_has_dnd_state(self, gm_token):
        r = requests.get(f"{BASE_URL}/api/characters/{ELI_DND}",
                         headers={"Authorization": f"Bearer {gm_token}"}, timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        data = r.json()
        assert data["system_id"] == "dnd-5e"
        st = data.get("folio", {}).get("dnd_state", {})
        assert st, "dnd_state missing"
        present = sum(k in st for k in ("class", "level", "race", "ability_scores", "spells"))
        assert present >= 3, f"dnd_state too sparse: keys={list(st.keys())}"

    def test_anime5e_eli_has_anime5e_state(self, gm_token):
        r = requests.get(f"{BASE_URL}/api/characters/{ELI_ANIME}",
                         headers={"Authorization": f"Bearer {gm_token}"}, timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        data = r.json()
        assert data["system_id"] == "anime-5e"
        # Tri-Stat primitives
        assert "stats" in data
        assert "attributes" in data or "skills" in data or "defects" in data
        # anime5e_state slot
        st = data.get("folio", {}).get("anime5e_state")
        assert st is not None, "anime5e_state missing from folio"

    def test_besm_eli_baseline(self, gm_token):
        r = requests.get(f"{BASE_URL}/api/characters/{ELI_BESM}",
                         headers={"Authorization": f"Bearer {gm_token}"}, timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        data = r.json()
        # BESM characters don't embed system_id at top level — derived from campaign
        assert "stats" in data
        assert "attributes" in data or "skills" in data


# ──────────────── Aurora cross-account access ────────────────
class TestAuroraAccess:
    def test_aurora_owns_all_four_eli(self, aurora_token):
        for cid in (ELI_BESM, ELI_CYPHER, ELI_DND, ELI_ANIME):
            r = requests.get(f"{BASE_URL}/api/characters/{cid}",
                             headers={"Authorization": f"Bearer {aurora_token}"}, timeout=15)
            assert r.status_code == 200, f"Aurora cannot fetch {cid}: {r.status_code} {r.text[:120]}"

    def test_aurora_sees_four_evereantha_campaigns(self, aurora_token):
        r = requests.get(f"{BASE_URL}/api/campaigns",
                         headers={"Authorization": f"Bearer {aurora_token}"}, timeout=15)
        assert r.status_code == 200
        camps = r.json()
        ids = {c["id"] for c in camps}
        for cid in (CAMP_BESM, CAMP_CYPHER, CAMP_DND, CAMP_ANIME):
            assert cid in ids, f"Aurora missing campaign {cid}. She has: {ids}"


# ──────────────── Ingest size bump ────────────────
class TestIngestSize:
    def test_ingest_accepts_large_payload(self, gm_token):
        # Build ~30 MB markdown blob (well over old 24 MB cap, well under new 64 MB cap)
        blob = ("# Session log\n\n" + ("Lorem ipsum dolor sit amet. " * 500 + "\n") * 2200)
        size_mb = len(blob) / (1024 * 1024)
        assert size_mb > 24, f"test blob only {size_mb:.1f} MB — adjust"
        files = {"file": ("bigdoc.md", blob.encode("utf-8"), "text/markdown")}
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{CAMP_BESM}/ingest",
            headers={"Authorization": f"Bearer {gm_token}"},
            files=files,
            timeout=120,
        )
        # Not expecting 413 (payload too large). Any 2xx / 202 / 400 (validation) is acceptable.
        # The key assertion: NOT a 413 "payload too large".
        assert r.status_code != 413, f"413 payload too large — cap not raised? {r.text[:200]}"
        # Most likely 200/201/202 or 400 if content-shape is funny; should not be 413/500.
        assert r.status_code < 500, f"Server error on ingest: {r.status_code} {r.text[:200]}"
