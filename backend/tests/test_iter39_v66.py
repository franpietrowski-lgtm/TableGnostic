"""V6.6 backend tests — Cypher suggest, Anime 5E CR/encounter,
Mobile character PDF, Spell -> Power Bundle conversion.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://campaign-hub-288.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PASS = "PieGod08!!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
                      timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def campaigns(admin_headers):
    r = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def cypher_campaign(campaigns):
    cands = [c for c in campaigns if c.get("system_id") == "cypher"]
    if not cands:
        pytest.skip("No cypher campaign seeded")
    return cands[0]


@pytest.fixture(scope="module")
def non_cypher_campaign(campaigns):
    cands = [c for c in campaigns if c.get("system_id") != "cypher"]
    if not cands:
        pytest.skip("No non-cypher campaign")
    return cands[0]


# ─── Cypher suggest ────────────────────────────────────────────────

class TestCypherSuggest:
    def test_returns_ranked_axes(self, admin_headers, cypher_campaign):
        cid = cypher_campaign["id"]
        r = requests.get(f"{BASE_URL}/api/cypher/{cid}/suggest", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["campaign_id"] == cid
        assert "setting_genre" in data
        assert "plot_phase_seen" in data
        assert "motive_window" in data
        s = data["suggestions"]
        for key in ("descriptors", "foci", "types", "cyphers", "artifacts"):
            assert key in s, f"missing axis {key}"
            assert isinstance(s[key], list)
            if s[key]:
                row = s[key][0]
                assert "score" in row
                assert "why" in row
                assert "matched_hints" in row
                assert "entry" in row

    def test_400_on_non_cypher_campaign(self, admin_headers, non_cypher_campaign):
        cid = non_cypher_campaign["id"]
        r = requests.get(f"{BASE_URL}/api/cypher/{cid}/suggest", headers=admin_headers, timeout=15)
        assert r.status_code == 400, r.text

    def test_403_for_non_member(self, cypher_campaign):
        # Create throwaway player
        email = f"TEST_v66_noncypher_{uuid.uuid4().hex[:8]}@example.com"
        reg = requests.post(f"{BASE_URL}/api/auth/register",
                            json={"email": email, "password": "pass123!",
                                  "name": "nonmember", "role": "player"}, timeout=15)
        assert reg.status_code in (200, 201), reg.text
        login = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": "pass123!"}, timeout=15)
        assert login.status_code == 200
        tok = login.json()["access_token"]
        r = requests.get(f"{BASE_URL}/api/cypher/{cypher_campaign['id']}/suggest",
                         headers={"Authorization": f"Bearer {tok}"}, timeout=15)
        assert r.status_code == 403, r.text


# ─── Anime 5E encounter budget ────────────────────────────────────

class TestAnime5eEncounterBudget:
    def test_lvl5_hard_party4(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/anime5e/encounter-budget"
            "?party_level=5&party_size=4&difficulty=hard",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["xp_per_pc"] == 750
        assert d["total_xp_budget"] == 3000
        assert isinstance(d["slot_suggestions"], list)
        assert len(d["slot_suggestions"]) > 0
        for slot in d["slot_suggestions"]:
            for k in ("n_monsters", "cr", "effective_xp", "multiplier"):
                assert k in slot, f"slot missing {k}"
        assert "environmental_hazard_budget" in d
        assert isinstance(d["environmental_hazard_budget"], int)

    @pytest.mark.parametrize("diff", ["easy", "medium", "hard", "deadly"])
    def test_difficulty_enum(self, admin_headers, diff):
        r = requests.get(
            f"{BASE_URL}/api/anime5e/encounter-budget"
            f"?party_level=3&party_size=4&difficulty={diff}",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["difficulty"] == diff


# ─── Mobile character PDF ─────────────────────────────────────────

def _gather_chars(headers, campaigns):
    out = []
    for c in campaigns:
        r = requests.get(f"{BASE_URL}/api/campaigns/{c['id']}/characters",
                         headers=headers, timeout=15)
        if r.status_code == 200:
            for ch in r.json():
                ch["_system_id"] = c.get("system_id")
                out.append(ch)
    return out


class TestMobileCharacterPDF:
    def test_export_pdf_for_each_system(self, admin_headers, campaigns):
        chars = _gather_chars(admin_headers, campaigns)
        if not chars:
            pytest.skip("no characters to export")
        systems_seen = set()
        for ch in chars:
            sid = ch.get("_system_id") or "?"
            if sid in systems_seen:
                continue
            cid = ch.get("id")
            resp = requests.get(
                f"{BASE_URL}/api/characters/{cid}/export.pdf?mode=mobile",
                headers=admin_headers, timeout=30)
            if resp.status_code != 200:
                print(f"PDF export failed for {sid} / {cid}: {resp.status_code} {resp.text[:200]}")
                continue
            assert resp.headers.get("content-type", "").startswith("application/pdf"), resp.headers
            assert len(resp.content) > 500
            systems_seen.add(sid)
        assert len(systems_seen) >= 1, "No characters produced a PDF"
        print(f"PDF OK for systems: {systems_seen}")

    def test_403_for_non_member(self, admin_headers, campaigns):
        chars = _gather_chars(admin_headers, campaigns)
        if not chars:
            pytest.skip("no characters")
        cid = chars[0]["id"]
        # create non-member
        email = f"TEST_v66_pdfnm_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "pass123!",
                            "name": "nm", "role": "player"}, timeout=15)
        login = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": "pass123!"}, timeout=15)
        tok = login.json()["access_token"]
        r = requests.get(
            f"{BASE_URL}/api/characters/{cid}/export.pdf?mode=mobile",
            headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        assert r.status_code == 403, f"expected 403, got {r.status_code}"


# ─── Spell -> Power Bundle conversion ─────────────────────────────

class TestSpellAsPowerBundle:
    def test_fireball_converts(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/reference/spell-conversions/fireball/as-power-bundle",
            headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["name"].lower() == "fireball"
        assert d["source_spell_level"] == 3
        assert d["invocation"] == "per-day"
        assert d["charges_max"] == 2
        assert isinstance(d["components"], list)
        assert len(d["components"]) > 0
        assert "cost" in d

    def test_unknown_slug_404(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/reference/spell-conversions/notaspell-zzz/as-power-bundle",
            headers=admin_headers, timeout=15)
        assert r.status_code == 404
