"""V5.2 iteration 23 backend tests.

Covers:
- D&D 5E reference: backgrounds[], spell_slots_full/half/warlock (20 rows each),
  cantrips_known.Wizard[0] == 3
- Anime 5E reference: backgrounds[], defects[], items[], class_casting map
- Cypher reference: descriptors/foci are objects with genres[],
  setting_genres (>=8), pool_baseline == 7
- Campaign V5.2 fields: setting_genre, primer_level_min, primer_tier_suggest,
  primer_xp_cap, house_rules — PUT + GET roundtrip
- Character journal: POST /api/characters/{cid}/journal appends entry with
  timestamp; persists on subsequent GET
"""
from __future__ import annotations

import os
import time

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL required"

ADMIN_EMAIL = "franpietrowski@gmail.com"
ADMIN_PASSWORD = "PieGod08!!"
CYPHER_CAMPAIGN_ID = "22ee28aaf79541c395255e144b5aab42"
CYPHER_CHARACTER_ID = "a129db2a8eb44e3b849de6fff876e9f5"


@pytest.fixture(scope="module")
def auth_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
               timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code} {r.text}")
    token = r.json().get("access_token")
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ---------- D&D 5E reference ----------

class TestDnd5eReference:
    def test_reference_shape(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/systems/dnd-5e/reference", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()

        # backgrounds
        bgs = data.get("backgrounds") or []
        assert isinstance(bgs, list) and len(bgs) >= 8, f"expected >=8 backgrounds, got {len(bgs)}"
        names = [b.get("name") if isinstance(b, dict) else b for b in bgs]
        assert any("Acolyte" in (str(n) or "") for n in names), f"Acolyte missing: {names}"

        # spell_slots tables — 20 rows each
        full = data.get("spell_slots_full") or []
        half = data.get("spell_slots_half") or []
        warl = data.get("spell_slots_warlock") or []
        assert len(full) == 20, f"spell_slots_full: {len(full)}"
        assert len(half) == 20, f"spell_slots_half: {len(half)}"
        assert len(warl) == 20, f"spell_slots_warlock: {len(warl)}"

        # cantrips_known.Wizard[0] == 3 (level 1 → 3 cantrips)
        ck = data.get("cantrips_known") or {}
        wiz = ck.get("Wizard") or []
        assert len(wiz) > 0, f"cantrips_known.Wizard missing: {ck}"
        assert wiz[0] == 3, f"cantrips_known.Wizard[0] expected 3, got {wiz[0]}"


# ---------- Anime 5E reference ----------

class TestAnime5eReference:
    def test_reference_shape(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/systems/anime-5e/reference", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()

        bgs = data.get("backgrounds") or []
        defects = data.get("defects") or []
        items = data.get("items") or []
        assert len(bgs) >= 8, f"backgrounds: {len(bgs)}"
        assert len(defects) >= 8, f"defects: {len(defects)}"
        assert len(items) >= 10, f"items: {len(items)}"

        cc = data.get("class_casting") or {}
        assert cc.get("Adept") == "full", f"class_casting.Adept: {cc}"
        assert cc.get("Champion") == "none", f"class_casting.Champion: {cc}"


# ---------- Cypher reference ----------

class TestCypherReferenceV52:
    def test_descriptors_foci_are_objects_with_genres(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/systems/cypher/reference", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()

        assert data.get("pool_baseline") == 7, f"pool_baseline: {data.get('pool_baseline')}"

        sg = data.get("setting_genres") or []
        assert len(sg) >= 8, f"setting_genres: {len(sg)}"

        descs = data.get("descriptors") or []
        assert descs, "descriptors missing"
        for d in descs:
            assert isinstance(d, dict), f"descriptor not dict: {d!r}"
            assert d.get("name"), f"descriptor missing name: {d}"
            assert isinstance(d.get("genres"), list) and d.get("genres"), \
                f"descriptor missing genres[]: {d}"

        foci = data.get("foci") or []
        assert foci, "foci missing"
        for f in foci:
            assert isinstance(f, dict), f"focus not dict: {f!r}"
            assert isinstance(f.get("genres"), list) and f.get("genres"), \
                f"focus missing genres[]: {f}"


# ---------- Campaign V5.2 fields ----------

class TestCampaignV52Fields:
    def test_put_and_get_roundtrip(self, auth_session):
        # GET current campaign first
        g = auth_session.get(f"{BASE_URL}/api/campaigns/{CYPHER_CAMPAIGN_ID}", timeout=15)
        assert g.status_code == 200, g.text
        original = g.json()

        payload = dict(original)
        # Strip server-assigned fields that PUT should not accept
        for k in ("id", "gm_id", "created_at", "updated_at", "member_ids",
                  "_id", "gm_name"):
            payload.pop(k, None)

        payload.update({
            "setting_genre": "fantasy",
            "primer_level_min": 3,
            "primer_tier_suggest": 2,
            "primer_xp_cap": 42,
            "house_rules": "TEST_V52 house rules line.",
        })

        p = auth_session.put(f"{BASE_URL}/api/campaigns/{CYPHER_CAMPAIGN_ID}",
                             json=payload, timeout=20)
        assert p.status_code == 200, p.text

        # GET round-trip
        g2 = auth_session.get(f"{BASE_URL}/api/campaigns/{CYPHER_CAMPAIGN_ID}", timeout=15)
        assert g2.status_code == 200, g2.text
        data = g2.json()
        assert data.get("setting_genre") == "fantasy", f"setting_genre: {data.get('setting_genre')}"
        assert data.get("primer_level_min") == 3, f"primer_level_min: {data.get('primer_level_min')}"
        assert data.get("primer_tier_suggest") == 2, f"primer_tier_suggest: {data.get('primer_tier_suggest')}"
        assert data.get("primer_xp_cap") == 42, f"primer_xp_cap: {data.get('primer_xp_cap')}"
        assert data.get("house_rules") == "TEST_V52 house rules line.", \
            f"house_rules: {data.get('house_rules')}"

        # Restore previous values (best-effort)
        restore = dict(original)
        for k in ("id", "gm_id", "created_at", "updated_at", "member_ids",
                  "_id", "gm_name"):
            restore.pop(k, None)
        auth_session.put(f"{BASE_URL}/api/campaigns/{CYPHER_CAMPAIGN_ID}",
                         json=restore, timeout=20)


# ---------- Character journal ----------

class TestCharacterJournal:
    def test_append_and_persist(self, auth_session):
        text = f"TEST_V52 journal entry {int(time.time())}"
        r = auth_session.post(
            f"{BASE_URL}/api/characters/{CYPHER_CHARACTER_ID}/journal",
            json={"text": text},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        entry = body.get("entry") or {}
        assert entry.get("text") == text, f"entry text: {entry}"
        assert entry.get("created_at"), f"entry missing created_at: {entry}"

        # GET character to verify persistence
        g = auth_session.get(f"{BASE_URL}/api/characters/{CYPHER_CHARACTER_ID}", timeout=15)
        assert g.status_code == 200, g.text
        ch = g.json()
        folio = ch.get("folio") or {}
        journal = folio.get("journal") or []
        assert isinstance(journal, list) and len(journal) > 0, f"journal empty: {journal}"
        assert any(e.get("text") == text for e in journal), \
            f"appended entry not persisted: {[e.get('text') for e in journal[-3:]]}"
