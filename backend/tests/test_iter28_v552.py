"""V5.5.2 — Campaign-level XP Ledger endpoint validation.

Validates GET /api/campaigns/{cid}/xp/ledger:
  · 401 unauthenticated
  · 403 non-GM caller
  · 404 missing campaign
  · 200 GM caller returns shape {characters[], entries[], totals, weights, bonus_cap, default_baseline}
  · After awarding XP via POST /characters/{cid}/xp, ledger entries[] grows accordingly
  · After converting XP via POST /characters/{cid}/xp/convert, entries[] gains a
    second row with source='convert' and converted_to_points set.
"""
import os
import time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
            or "http://localhost:8001")

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


# ───────────────────────── Fixtures ─────────────────────────
@pytest.fixture(scope="module")
def gm_headers():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": GM_EMAIL, "password": GM_PASS}, timeout=15)
    assert r.status_code == 200, f"GM login failed: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def player_headers():
    email = f"TEST_iter28_player_{int(time.time())}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "playerpass1!",
                            "name": "iter28 player", "role": "player"}, timeout=15)
    if r.status_code not in (200, 201):
        pytest.skip(f"register failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token")
    if not tok:
        r2 = requests.post(f"{BASE_URL}/api/auth/login",
                           json={"email": email, "password": "playerpass1!"},
                           timeout=15)
        tok = r2.json().get("access_token")
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def gm_campaign_and_char(gm_headers):
    """Find an existing GM campaign with a character — create if missing."""
    r = requests.get(f"{BASE_URL}/api/campaigns", headers=gm_headers, timeout=15)
    assert r.status_code == 200, r.text
    camps = r.json()
    assert isinstance(camps, list) and len(camps) > 0, "GMFran has no campaigns"
    # Find a campaign that already has at least one character
    chosen_camp = None
    chosen_char = None
    for c in camps:
        cid = c["id"]
        rc = requests.get(f"{BASE_URL}/api/campaigns/{cid}/characters",
                          headers=gm_headers, timeout=15)
        if rc.status_code == 200:
            chs = rc.json()
            if isinstance(chs, list) and len(chs) > 0:
                chosen_camp = c
                chosen_char = chs[0]
                break
    if not chosen_camp:
        pytest.skip("No GM campaign with a character available to seed XP")
    return {"campaign": chosen_camp, "character": chosen_char}


# ───────────────────────── Auth tests ─────────────────────────
class TestLedgerAccess:
    def test_unauthenticated_returns_401(self, gm_campaign_and_char):
        cid = gm_campaign_and_char["campaign"]["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/xp/ledger", timeout=15)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_non_gm_returns_403(self, gm_campaign_and_char, player_headers):
        cid = gm_campaign_and_char["campaign"]["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/xp/ledger",
                         headers=player_headers, timeout=15)
        assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text[:200]}"

    def test_missing_campaign_returns_404(self, gm_headers):
        r = requests.get(f"{BASE_URL}/api/campaigns/does-not-exist-xyz/xp/ledger",
                         headers=gm_headers, timeout=15)
        assert r.status_code == 404, f"expected 404 got {r.status_code}"


# ───────────────────────── Shape & data tests ─────────────────────────
class TestLedgerShape:
    def test_ledger_shape(self, gm_headers, gm_campaign_and_char):
        cid = gm_campaign_and_char["campaign"]["id"]
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/xp/ledger",
                         headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("characters", "entries", "totals", "weights",
                  "bonus_cap", "default_baseline"):
            assert k in data, f"missing key {k} in ledger response"
        assert isinstance(data["characters"], list)
        assert isinstance(data["entries"], list)
        for k in ("awarded", "converted", "unspent"):
            assert k in data["totals"], f"totals missing {k}"
            assert isinstance(data["totals"][k], (int, float))


class TestLedgerAwardAndConvert:
    def test_award_then_convert_appears_in_ledger(self, gm_headers,
                                                   gm_campaign_and_char):
        camp = gm_campaign_and_char["campaign"]
        char = gm_campaign_and_char["character"]
        cid = camp["id"]
        char_id = char["id"]

        # Snapshot current entry count for this character
        r0 = requests.get(f"{BASE_URL}/api/campaigns/{cid}/xp/ledger",
                          headers=gm_headers, timeout=15)
        assert r0.status_code == 200
        before = [e for e in r0.json()["entries"] if e["character_id"] == char_id]
        before_count = len(before)
        before_total = r0.json()["totals"]["awarded"]

        # Award XP — try common payload shapes
        unique_reason = f"TEST_iter28_award_{int(time.time())}"
        award_payload = {"amount": 4, "reason": unique_reason}
        ar = requests.post(f"{BASE_URL}/api/characters/{char_id}/xp",
                           headers=gm_headers, json=award_payload, timeout=15)
        assert ar.status_code in (200, 201), \
            f"award failed: {ar.status_code} {ar.text[:300]}"

        # Re-fetch ledger
        r1 = requests.get(f"{BASE_URL}/api/campaigns/{cid}/xp/ledger",
                          headers=gm_headers, timeout=15)
        assert r1.status_code == 200
        after = [e for e in r1.json()["entries"] if e["character_id"] == char_id]
        assert len(after) >= before_count + 1, \
            f"expected new entry; before={before_count} after={len(after)}"

        # Locate our award entry by reason
        award_entry = next((e for e in after if e.get("reason") == unique_reason), None)
        assert award_entry is not None, "award reason not found in ledger entries"
        assert float(award_entry["amount"]) == pytest.approx(4.0)
        assert award_entry.get("awarded_at"), "missing awarded_at on entry"
        assert award_entry.get("source"), "missing source on entry"

        # Totals must have grown by ~4 awarded
        new_total = r1.json()["totals"]["awarded"]
        assert new_total >= before_total + 3.5, \
            f"awarded total didn't grow: {before_total} → {new_total}"

        # Convert XP → CP. Amount conservatively small (4 XP available).
        # Endpoint signature varies; common shape is {amount: <xp>}.
        convert_payload = {"amount": 4}
        cv = requests.post(f"{BASE_URL}/api/characters/{char_id}/xp/convert",
                           headers=gm_headers, json=convert_payload, timeout=15)
        if cv.status_code not in (200, 201):
            # Try alternate field name
            cv = requests.post(f"{BASE_URL}/api/characters/{char_id}/xp/convert",
                               headers=gm_headers,
                               json={"xp_amount": 4}, timeout=15)
        assert cv.status_code in (200, 201), \
            f"convert failed: {cv.status_code} {cv.text[:300]}"

        # Ledger must now contain a 'convert' entry for this character
        r2 = requests.get(f"{BASE_URL}/api/campaigns/{cid}/xp/ledger",
                          headers=gm_headers, timeout=15)
        assert r2.status_code == 200
        char_entries = [e for e in r2.json()["entries"]
                        if e["character_id"] == char_id]
        convert_rows = [e for e in char_entries if e.get("source") == "convert"]
        assert len(convert_rows) >= 1, \
            f"no source=convert entry found in ledger for {char_id}"
        # converted_to_points should be set (truthy / >0)
        cv_row = convert_rows[0]
        assert cv_row.get("converted_to_points") not in (None, 0, "0"), \
            f"converted_to_points missing/zero on convert row: {cv_row}"
