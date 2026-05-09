"""V6.25.34 — Concept Forge V2 (multi-field) + Smart Validators backend regression."""
import os
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://rules-forge.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"
PLAYER_PASS = "PieBan18!!"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"Login failed {r.status_code}: {r.text}"
    j = r.json()
    return j.get("access_token") or j.get("token")


@pytest.fixture(scope="module")
def gm_headers():
    return {"Authorization": f"Bearer {_login(GM_EMAIL, GM_PASS)}"}


@pytest.fixture(scope="module")
def player_headers():
    return {"Authorization": f"Bearer {_login(GM_EMAIL, PLAYER_PASS)}"}


@pytest.fixture(scope="module")
def gm_id(gm_headers):
    r = requests.get(f"{API}/auth/me", headers=gm_headers, timeout=10).json()
    return r.get("id") or r.get("user", {}).get("id")


@pytest.fixture(scope="module")
def besm_campaign(gm_headers, gm_id):
    r = requests.get(f"{API}/campaigns", headers=gm_headers, timeout=15)
    camps = r.json() if isinstance(r.json(), list) else r.json().get("campaigns", [])
    for c in camps:
        if c.get("system_id") == "besm-4e" and c.get("gm_id") == gm_id:
            return c
    pytest.skip("No BESM 4E GM campaign")


# ── Concept Forge V2 ───────────────────────────────────────────────
class TestConceptForgeV2:
    draft_id = None

    def test_multi_field_brief(self, gm_headers, besm_campaign):
        cid = besm_campaign["id"]
        body = {
            "role": "Battlefield medic",
            "signature_traits": "Phoenix-blessed healing fire, ember lantern, sworn pacifism",
            "appearance": "Tall, lean, ash-streaked silver hair, robes scorched at the hem.",
            "origin": "Refugee from the Cinder Steppes; raised by phoenix monks.",
            "carried_gear": "Bandolier of healing salves, ember-lantern, ritual staff.",
            "goals": "Find the last phoenix nest; redeem her brother.",
            "dreams": "A world where wounds close before they bleed.",
            "personality_knots": "Vow of nonviolence; haunted by past as a thief.",
            "history": "Stole from a phoenix shrine, was burned, then blessed; wanders ever since.",
        }
        r = requests.post(f"{API}/campaigns/{cid}/concept-drafts",
                          headers=gm_headers, json=body, timeout=120)
        assert r.status_code == 200, f"{r.status_code} {r.text[:600]}"
        draft = r.json()["draft"]
        TestConceptForgeV2.draft_id = draft["id"]
        # persisted audit fields
        assert "brief" in draft and isinstance(draft["brief"], dict)
        assert draft["brief"].get("role") == "Battlefield medic"
        assert "primer_snapshot" in draft and isinstance(draft["primer_snapshot"], dict)
        assert "imported_codex_node_ids" in draft
        cands = draft["candidates"]
        assert isinstance(cands, list) and len(cands) >= 1
        # Inspect first candidate for the expanded V2 schema
        c = cands[0]
        # Identity
        for k in ("appearance", "origin", "goals", "dreams", "personality_knots", "history"):
            assert k in c, f"candidate missing {k}: keys={list(c.keys())}"
        # Mechanics
        assert "race" in c and "class" in c
        stats = c["stats"]
        assert all(k in stats for k in ("body", "mind", "soul"))
        # Attributes carry resistance/range disambiguation
        assert isinstance(c["attributes"], list) and len(c["attributes"]) > 0
        attr_with_res = [a for a in c["attributes"] if "resistance_kind" in a and "range_kind" in a]
        assert len(attr_with_res) >= 1, f"no attrs with resistance/range disambiguation: {c['attributes'][:2]}"
        # power_packs / items / weapons
        assert "power_packs" in c
        assert "items" in c and isinstance(c["items"], list)
        assert "weapons" in c and isinstance(c["weapons"], list)
        # weapons may carry is_weapon_item flag if any present
        for w in c["weapons"]:
            assert "is_weapon_item" in w, f"weapon missing is_weapon_item: {w}"
        assert "estimated_cp" in c and "rationale" in c

    def test_with_imported_codex_no_500(self, gm_headers, besm_campaign):
        cid = besm_campaign["id"]
        # Get any existing node id (or empty list — endpoint must not 500)
        r = requests.get(f"{API}/campaigns/{cid}/nodes", headers=gm_headers, timeout=15)
        node_ids = []
        if r.status_code == 200:
            payload = r.json()
            rows = payload if isinstance(payload, list) else payload.get("nodes", [])
            node_ids = [n["id"] for n in rows[:1] if n.get("id")]
        body = {"concept_text": "An apothecary blessed by phoenix fire.",
                "imported_codex_node_ids": node_ids}
        r2 = requests.post(f"{API}/campaigns/{cid}/concept-drafts",
                           headers=gm_headers, json=body, timeout=120)
        assert r2.status_code == 200, f"{r2.status_code} {r2.text[:400]}"
        draft = r2.json()["draft"]
        assert draft["imported_codex_node_ids"] == node_ids
        # cleanup
        requests.delete(f"{API}/campaigns/{cid}/concept-drafts/{draft['id']}",
                        headers=gm_headers, timeout=10)

    def test_empty_brief_400(self, gm_headers, besm_campaign):
        r = requests.post(f"{API}/campaigns/{besm_campaign['id']}/concept-drafts",
                          headers=gm_headers, json={}, timeout=15)
        assert r.status_code == 400
        assert "concept" in r.text.lower() or "field" in r.text.lower()

    def test_cleanup_draft(self, gm_headers, besm_campaign):
        if TestConceptForgeV2.draft_id:
            requests.delete(
                f"{API}/campaigns/{besm_campaign['id']}/concept-drafts/{TestConceptForgeV2.draft_id}",
                headers=gm_headers, timeout=10)


# ── Validators ─────────────────────────────────────────────────────
class TestValidators:
    clean_cid = None
    dirty_cid = None

    def _make_char(self, gm_headers, cid, name, body, attrs, defs, gm_id):
        payload = {
            "campaign_id": cid,
            "user_id": gm_id,
            "name": name,
            "system_id": "besm-4e",
            "stats": {"body": body, "mind": 6, "soul": 6},
            "attributes": attrs,
            "skills": [],
            "defects": defs,
        }
        r = requests.post(f"{API}/characters", headers=gm_headers, json=payload, timeout=15)
        assert r.status_code in (200, 201), f"create char failed: {r.status_code} {r.text[:300]}"
        return r.json().get("id") or r.json().get("character", {}).get("id")

    def test_clean_character_zero_warnings(self, gm_headers, besm_campaign, gm_id):
        cid = besm_campaign["id"]
        ch_id = self._make_char(
            gm_headers, cid, "TEST_clean_v62534", body=6,
            attrs=[{"name": "Healing", "level": 3, "cost_per_level": 4}],
            defs=[{"name": "Marked", "rank": 1, "points_per_rank": 1, "category": "physical"}],
            gm_id=gm_id)
        TestValidators.clean_cid = ch_id
        r = requests.get(f"{API}/characters/{ch_id}/validations",
                         headers=gm_headers, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["count"] == 0, f"expected 0 warnings, got {body}"

    def test_dirty_character_warnings(self, gm_headers, besm_campaign, gm_id):
        cid = besm_campaign["id"]
        ch_id = self._make_char(
            gm_headers, cid, "TEST_dirty_v62534", body=15,
            attrs=[
                {"name": "Tough", "level": 3, "cost_per_level": 2},
                {"name": "Tough", "level": 2, "cost_per_level": 2},
                {"name": "Massive Damage", "level": 9, "cost_per_level": 4},
                {"name": "Weapon", "level": 25, "cost_per_level": 1},  # exempt
            ],
            defs=[{"name": "Vulnerability", "rank": 5, "points_per_rank": 1, "category": "physical"}],
            gm_id=gm_id)
        TestValidators.dirty_cid = ch_id
        r = requests.get(f"{API}/characters/{ch_id}/validations",
                         headers=gm_headers, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        ws = body["warnings"]
        kinds = [w["kind"] for w in ws]
        assert "over_benchmark_stat" in kinds, f"missing stat warn: {kinds}"
        assert "duplicate_attribute" in kinds, f"missing dup warn: {kinds}"
        assert "over_benchmark_attr" in kinds, f"missing attr warn: {kinds}"
        assert "over_benchmark_defect" in kinds, f"missing defect warn: {kinds}"
        # Weapon EXEMPT — must not flag the L25 Weapon attribute
        weapon_warns = [w for w in ws if w.get("target_name", "").lower() == "weapon"
                        and w["kind"] == "over_benchmark_attr"]
        assert len(weapon_warns) == 0, f"weapon should be exempt: {weapon_warns}"
        assert body["count"] >= 4

    def test_dismiss_persists_and_idempotent(self, gm_headers):
        ch_id = TestValidators.dirty_cid
        # Get a duplicate signature
        r = requests.get(f"{API}/characters/{ch_id}/validations",
                         headers=gm_headers, timeout=10).json()
        dup = next(w for w in r["warnings"] if w["kind"] == "duplicate_attribute")
        sig = dup["signature"]
        before = r["count"]
        r2 = requests.post(f"{API}/characters/{ch_id}/validations/dismiss",
                           headers=gm_headers, json={"signature": sig}, timeout=10)
        assert r2.status_code == 200
        assert r2.json().get("dismissed") == sig
        # Re-dismiss
        r3 = requests.post(f"{API}/characters/{ch_id}/validations/dismiss",
                           headers=gm_headers, json={"signature": sig}, timeout=10)
        assert r3.status_code == 200 and r3.json().get("already_dismissed") is True
        # Subsequent GET has fewer
        r4 = requests.get(f"{API}/characters/{ch_id}/validations",
                          headers=gm_headers, timeout=10).json()
        assert r4["count"] == before - 1, f"expected {before-1} got {r4['count']}"

    def test_signature_changes_on_level_bump(self, gm_headers):
        """Dismiss over-benchmark Massive Damage L9, then bump to L10 — fresh warning fires."""
        ch_id = TestValidators.dirty_cid
        r = requests.get(f"{API}/characters/{ch_id}/validations",
                         headers=gm_headers, timeout=10).json()
        attr_w = next((w for w in r["warnings"]
                       if w["kind"] == "over_benchmark_attr"
                       and "massive" in w["target_name"].lower()), None)
        assert attr_w, f"no Massive Damage warn to dismiss: {r['warnings']}"
        sig_old = attr_w["signature"]
        requests.post(f"{API}/characters/{ch_id}/validations/dismiss",
                      headers=gm_headers, json={"signature": sig_old}, timeout=10)
        # Bump level via PUT/PATCH
        ch = requests.get(f"{API}/characters/{ch_id}", headers=gm_headers, timeout=10).json()
        ch_obj = ch.get("character") or ch
        for a in ch_obj.get("attributes", []):
            if "massive" in (a.get("name") or "").lower():
                a["level"] = 10
        # try PATCH then fall back to PUT
        rp = requests.patch(f"{API}/characters/{ch_id}", headers=gm_headers,
                            json={"attributes": ch_obj["attributes"]}, timeout=10)
        if rp.status_code not in (200, 201):
            rp = requests.put(f"{API}/characters/{ch_id}", headers=gm_headers,
                              json=ch_obj, timeout=10)
        assert rp.status_code in (200, 201), f"bump failed: {rp.status_code} {rp.text[:300]}"
        r2 = requests.get(f"{API}/characters/{ch_id}/validations",
                          headers=gm_headers, timeout=10).json()
        new_attr_w = next((w for w in r2["warnings"]
                           if w["kind"] == "over_benchmark_attr"
                           and "massive" in w["target_name"].lower()), None)
        assert new_attr_w, "bumped Massive Damage L10 should re-fire as a fresh warning"
        assert new_attr_w["signature"] != sig_old

    def test_campaign_dashboard_gm(self, gm_headers, besm_campaign):
        cid = besm_campaign["id"]
        r = requests.get(f"{API}/campaigns/{cid}/validations",
                         headers=gm_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "characters" in body and "total_warnings" in body
        assert body["total_warnings"] >= 1
        char_ids = [c["character_id"] for c in body["characters"]]
        assert TestValidators.dirty_cid in char_ids

    def test_campaign_dashboard_non_gm_403(self, player_headers, besm_campaign):
        r = requests.get(f"{API}/campaigns/{besm_campaign['id']}/validations",
                         headers=player_headers, timeout=10)
        # Player persona is a different user_id; should get 403 or 404
        assert r.status_code in (403, 404), f"expected 403/404 got {r.status_code}"

    def test_zzz_cleanup(self, gm_headers):
        for cid in (TestValidators.clean_cid, TestValidators.dirty_cid):
            if cid:
                requests.delete(f"{API}/characters/{cid}", headers=gm_headers, timeout=10)
