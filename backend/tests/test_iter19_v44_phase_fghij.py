"""V4.4 Phases F+G+H+I+J — saleable-chronicle batch (iter19).

Coverage:
  Phase F  — Bi-directional KB↔character sync + Nyaulis 4th PC + location scale.
  Phase G  — PDF cover BESM4 layout + World Codex/Per-PC/Reference appendices.
  Phase H  — XP-spend GM approval queue (propose / approve / reject / 403 / 400).
  Phase I  — Reference editor CRUD + page-validation + 403 for non-GM.
  Phase J  — GM Session Journal pinned node auto-created on reset.

Destructive: runs reset-to-evereantha?confirm=WIPE at module start.
"""
import io
import os
import re
import time
import uuid
import pytest
import requests

try:
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None


def _read_backend_url():
    if os.environ.get("REACT_APP_BACKEND_URL"):
        return os.environ["REACT_APP_BACKEND_URL"]
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE = _read_backend_url().rstrip("/")
ADMIN = {"email": "franpietrowski@gmail.com", "password": "PieGod08!!"}


# ─────────── Module-scoped fixtures ───────────

@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    rr = s.post(f"{BASE}/api/admin/reset-to-evereantha?confirm=WIPE", timeout=180)
    assert rr.status_code in (200, 201), rr.text
    # Set byline for PDF cover assertions
    s.patch(f"{BASE}/api/auth/me", json={"byline_name": "Fran Pietrowski"}, timeout=15)
    return s


@pytest.fixture(scope="module")
def evereantha_id(admin_session):
    r = admin_session.get(f"{BASE}/api/campaigns", timeout=20)
    assert r.status_code == 200
    ev = next((c for c in r.json() if "evereantha" in (c.get("name") or "").lower()), None)
    assert ev, "Evereantha demo not found"
    return ev["id"]


@pytest.fixture(scope="module")
def player_session():
    s = requests.Session()
    email = f"TEST_iter19_player_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "Pp123456!!"
    s.post(f"{BASE}/api/auth/register", json={
        "email": email, "password": pwd, "name": "TEST iter19 player", "role": "player"
    }, timeout=20)
    r = s.post(f"{BASE}/api/auth/login", json={"email": email, "password": pwd}, timeout=20)
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


@pytest.fixture(scope="module")
def chars(admin_session, evereantha_id):
    r = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/characters", timeout=20)
    assert r.status_code == 200, r.text
    rows = r.json()
    by_name = {c["name"]: c for c in rows}
    return rows, by_name


@pytest.fixture(scope="module")
def nodes(admin_session, evereantha_id):
    r = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/nodes", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


# ───────────────────────── PHASE F ─────────────────────────

class TestPhaseF_BidirectionalSync:

    def test_4_pcs_present(self, chars):
        rows, by_name = chars
        for n in ("Eli", "Laryk", "Roney", "Nyaulis"):
            assert n in by_name, f"PC {n} missing from /characters list. Got {list(by_name)}"

    def test_pc_linked_node_id_set(self, chars):
        _, by_name = chars
        for n in ("Eli", "Laryk", "Roney", "Nyaulis"):
            assert by_name[n].get("linked_node_id"), f"{n}.linked_node_id is missing"

    def test_pc_npc_nodes_link_back(self, chars, nodes):
        _, by_name = chars
        npc_by_title = {x["title"]: x for x in nodes if x.get("type") == "npc"}
        for n in ("Eli", "Laryk", "Roney", "Nyaulis"):
            assert n in npc_by_title, f"NPC node titled {n!r} missing"
            node = npc_by_title[n]
            assert node.get("visibility") == "shared", f"{n} node visibility should be 'shared'"
            tags = node.get("tags") or []
            assert "pc" in tags, f"{n} node tags should contain 'pc'. Got {tags}"
            cid_in_node = (node.get("fields") or {}).get("character_id")
            assert cid_in_node == by_name[n]["id"], (
                f"{n} npc.fields.character_id mismatch: node says {cid_in_node}, char is {by_name[n]['id']}"
            )
            # Symmetry: character.linked_node_id == this node's id
            assert by_name[n]["linked_node_id"] == node["id"], (
                f"{n}.linked_node_id ({by_name[n]['linked_node_id']}) != node.id ({node['id']})"
            )

    def test_locations_scale_and_parent(self, nodes):
        loc_by_title = {x["title"]: x for x in nodes if x.get("type") == "location"}
        # Match by substring — seed uses "Golden Forests of Aurea" and
        # "The Solar / Lunar Caldera"; the spec key is the substring.
        expected = {
            "Eagles Nest": "hamlet",
            "Aurea": "country",
            "Golden Forests": "biome",
            "Montes Inexpugnabilis": "mountain-range",
            "Caldera": "landmark",
        }
        for needle, want_scale in expected.items():
            match_title = next(
                (t for t in loc_by_title
                 if t == needle or needle.lower() in t.lower()),
                None,
            )
            assert match_title, f"location matching {needle!r} missing. Got: {list(loc_by_title)}"
            f = loc_by_title[match_title].get("fields") or {}
            assert f.get("scale") == want_scale, (
                f"{match_title}.fields.scale expected {want_scale!r}, got {f.get('scale')!r}"
            )
            assert "parent_location" in f, f"{match_title}.fields.parent_location missing"
        # spot-check hierarchy: Eagles Nest is inside Aurea
        assert (loc_by_title["Eagles Nest"].get("fields") or {}).get("parent_location") == "Aurea"
        assert (loc_by_title["Aurea"].get("fields") or {}).get("parent_location") in (None, "")


class TestPhaseF_NyaulisAsPC:

    def test_nyaulis_concept_and_points(self, chars):
        _, by_name = chars
        ny = by_name.get("Nyaulis")
        assert ny, "Nyaulis missing from PC roster"
        assert "Faunamimic hermit" in (ny.get("concept") or ""), ny.get("concept")
        assert ny.get("power_level") == "Adventurous"
        assert int(ny.get("total_points") or 0) == 90

    def test_nyaulis_attributes(self, chars):
        _, by_name = chars
        names = [a.get("name") for a in (by_name["Nyaulis"].get("attributes") or [])]
        assert any("Alternate Form" in n and "firelight" in n for n in names), names
        assert any("Heightened Senses" in n for n in names), names
        assert any("Weapon" in n and "iron stake" in n for n in names), names

    def test_nyaulis_defects_marked(self, chars):
        _, by_name = chars
        defs_ = [d.get("name") for d in (by_name["Nyaulis"].get("defects") or [])]
        assert any("Marked" in (n or "") for n in defs_), defs_


# ───────────────────────── PHASE J ─────────────────────────

class TestPhaseJ_GMSessionJournal:

    def test_gm_journal_node_present(self, nodes):
        cands = [n for n in nodes if n.get("title") == "GM Session Journal"]
        assert cands, "GM Session Journal node not auto-created"
        n = cands[0]
        assert n.get("type") == "lore"
        assert n.get("visibility") == "gm_only"
        tags = n.get("tags") or []
        for t in ("gm-only", "session-journal", "pinned"):
            assert t in tags, f"GM Journal missing tag {t!r}"
        f = n.get("fields") or {}
        assert f.get("is_pinned") is True
        assert f.get("is_gm_journal") is True
        assert f.get("entries") == []


# ───────────────────────── PHASE H ─────────────────────────

class TestPhaseH_XPApproval:

    @pytest.fixture(scope="class")
    def laryk_id(self, chars):
        _, by_name = chars
        return by_name["Laryk"]["id"]

    def test_award_xp_to_laryk(self, admin_session, laryk_id):
        r = admin_session.post(f"{BASE}/api/characters/{laryk_id}/xp",
                                json={"amount": 2, "reason": "iter19 test award"},
                                timeout=20)
        assert r.status_code in (200, 201), r.text

    def _baseline(self, admin_session, laryk_id):
        r = admin_session.get(f"{BASE}/api/characters/{laryk_id}", timeout=15)
        assert r.status_code == 200
        ch = r.json()
        tough = next((a for a in ch.get("attributes", []) if a.get("name") == "Tough"), None)
        return ch.get("xp_unspent", 0), (tough.get("level") if tough else None)

    def test_propose_then_reject_unchanged(self, admin_session, laryk_id):
        unspent_before, tough_before = self._baseline(admin_session, laryk_id)
        # If Tough doesn't exist, the test must skip—but Laryk per BESM4 baseline
        # should have it; we'll fall back to a stat patch if not.
        if tough_before is None:
            pytest.skip("Laryk has no 'Tough' attribute — skipping reject path")
        r = admin_session.post(f"{BASE}/api/characters/{laryk_id}/xp-spend", json={
            "cost": 1,
            "reason": "iter19 reject test",
            "summary": "+1 Tough (will be rejected)",
            "change": {"attribute_level": {"name": "Tough", "delta": 1}},
        }, timeout=20)
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        # GM list contains it
        rl = admin_session.get(f"{BASE}/api/campaigns/{r.json()['campaign_id']}/xp-pending", timeout=15)
        assert rl.status_code == 200
        assert any(p["id"] == pid for p in rl.json())
        # Reject
        rj = admin_session.post(f"{BASE}/api/xp-pending/{pid}/reject",
                                 json={"reason": "too soon"}, timeout=15)
        assert rj.status_code == 200, rj.text
        unspent_after, tough_after = self._baseline(admin_session, laryk_id)
        assert tough_after == tough_before, "Tough level changed despite rejection"
        assert unspent_after == unspent_before, "xp_unspent changed despite rejection"

    def test_propose_then_approve_applies(self, admin_session, laryk_id):
        unspent_before, tough_before = self._baseline(admin_session, laryk_id)
        if tough_before is None:
            pytest.skip("Laryk has no 'Tough' attribute — skipping approve path")
        r = admin_session.post(f"{BASE}/api/characters/{laryk_id}/xp-spend", json={
            "cost": 1,
            "reason": "iter19 approve test",
            "summary": "+1 Tough (approve)",
            "change": {"attribute_level": {"name": "Tough", "delta": 1}},
        }, timeout=20)
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        ap = admin_session.post(f"{BASE}/api/xp-pending/{pid}/approve", timeout=15)
        assert ap.status_code == 200, ap.text
        unspent_after, tough_after = self._baseline(admin_session, laryk_id)
        assert tough_after == tough_before + 1, (
            f"Tough should go from {tough_before} → {tough_before+1}, got {tough_after}"
        )
        assert round(unspent_before - unspent_after, 2) == 1.0, (
            f"xp_unspent should drop by 1, went {unspent_before} → {unspent_after}"
        )

    def test_insufficient_xp_400(self, admin_session, laryk_id):
        # Schema bounds the cost (gt=0, lt=200), so use 150 — well over Laryk's
        # remaining unspent (we awarded 2, spent 1, so ≤1 remains).
        r = admin_session.post(f"{BASE}/api/characters/{laryk_id}/xp-spend", json={
            "cost": 150,
            "reason": "iter19 broke",
            "change": {"attribute_level": {"name": "Tough", "delta": 1}},
        }, timeout=15)
        assert r.status_code == 400, r.text

    def test_non_gm_cannot_list_pending(self, player_session, evereantha_id):
        r = player_session.get(f"{BASE}/api/campaigns/{evereantha_id}/xp-pending", timeout=15)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"

    def test_non_owner_cannot_propose(self, player_session, laryk_id):
        r = player_session.post(f"{BASE}/api/characters/{laryk_id}/xp-spend", json={
            "cost": 1,
            "reason": "iter19 not allowed",
            "change": {"attribute_level": {"name": "Tough", "delta": 1}},
        }, timeout=15)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"


# ───────────────────────── PHASE I ─────────────────────────

class TestPhaseI_ReferenceEditor:

    @pytest.fixture(scope="class")
    def created(self, admin_session, evereantha_id):
        r = admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/reference", json={
            "kind": "weapon", "name": "Spike-hammer", "page": 196, "book": "besm-4e",
            "summary": "iter19 valid weapon",
        }, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["page_validation"]["valid"] is True
        return body

    def test_create_valid_page(self, created):
        assert created["name"] == "Spike-hammer"
        assert created["page"] == 196

    def test_create_invalid_page(self, admin_session, evereantha_id):
        r = admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/reference", json={
            "kind": "weapon", "name": "TEST_BadPage", "page": 999, "book": "besm-4e",
        }, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["page_validation"]["valid"] is False
        reason = body["page_validation"].get("reason", "")
        assert "BESM Fourth Edition" in reason or "besm" in reason.lower(), reason

    def test_list_filtered_by_kind(self, admin_session, evereantha_id, created):
        r = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/reference?kind=weapon",
                               timeout=15)
        assert r.status_code == 200
        rows = r.json()
        assert any(x["id"] == created["id"] for x in rows)

    def test_patch_row(self, admin_session, evereantha_id, created):
        r = admin_session.patch(
            f"{BASE}/api/campaigns/{evereantha_id}/reference/{created['id']}",
            json={"summary": "patched-iter19"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["summary"] == "patched-iter19"

    def test_validate_page_endpoint(self, admin_session):
        r = admin_session.post(f"{BASE}/api/reference/validate-page",
                                json={"page": 50, "book": "anime-5e"},
                                timeout=15)
        assert r.status_code == 200
        assert r.json().get("valid") is True

    def test_non_gm_cannot_create(self, player_session, evereantha_id):
        r = player_session.post(f"{BASE}/api/campaigns/{evereantha_id}/reference", json={
            "kind": "weapon", "name": "TEST_NoAuth", "page": 100, "book": "besm-4e",
        }, timeout=15)
        assert r.status_code == 403, r.text

    def test_delete_row(self, admin_session, evereantha_id):
        c = admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/reference", json={
            "kind": "item", "name": "TEST_DeleteMe", "page": 50, "book": "besm-4e",
        }, timeout=15).json()
        d = admin_session.delete(
            f"{BASE}/api/campaigns/{evereantha_id}/reference/{c['id']}",
            timeout=15,
        )
        assert d.status_code == 200
        assert d.json().get("deleted") == 1


# ───────────────────────── PHASE G ─────────────────────────

class TestPhaseG_PDFExport:

    @pytest.fixture(scope="class")
    def pdf_bytes(self, admin_session, evereantha_id):
        # Ensure Spike-hammer reference exists (TestPhaseI fixture is class-scoped
        # to its own class, so insert here too — idempotent enough for the suite).
        admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/reference", json={
            "kind": "weapon", "name": "Spike-hammer", "page": 196, "book": "besm-4e",
            "summary": "for pdf appendix",
        }, timeout=15)
        r = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/export.pdf",
                               timeout=240)
        assert r.status_code == 200, f"PDF export failed: {r.status_code} {r.text[:300]}"
        assert r.content[:4] == b"%PDF", "Not a PDF (missing %PDF magic)"
        assert len(r.content) > 100_000, f"PDF too small ({len(r.content)} bytes)"
        return r.content

    @pytest.fixture(scope="class")
    def pdf_text(self, pdf_bytes):
        if pypdf is None:
            pytest.skip("pypdf not installed")
        rdr = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        per_page = [(p.extract_text() or "") for p in rdr.pages]
        return per_page, "\n".join(per_page)

    def test_cover_credits(self, pdf_text):
        per_page, _ = pdf_text
        assert per_page, "PDF has zero pages"
        cover = per_page[0]
        for needle in ("WRITTEN BY:", "ADDITIONAL WRITING BY:", "SPECIAL THANKS TO:",
                       "Mark MacKinnon",
                       "Dyskami Publishing Company with Japanime Games",
                       "Fran Pietrowski",
                       "© 2026"):
            assert needle in cover, f"Cover missing {needle!r}.\n--- COVER ---\n{cover[:1500]}"

    def test_cover_trademark_bar(self, pdf_text):
        _, full = pdf_text
        # Tri-Stat trademark line + URL — may render across canvas drawString boundaries
        assert "Tri-Stat System and BESM" in full and "Paradox Interactive Group" in full
        assert "BESM4.life" in full

    def test_cover_no_artwork_or_graphic_rows(self, pdf_text):
        per_page, _ = pdf_text
        cover = per_page[0]
        assert "Artwork by" not in cover, "Cover should NOT have 'Artwork by' row"
        assert "Graphic Production by" not in cover, "Cover should NOT have 'Graphic Production by' row"

    def test_world_codex_appendix(self, pdf_text):
        _, full = pdf_text
        assert "World Codex" in full or "WORLD CODEX" in full.upper()
        for loc in ("Aurea", "Eagles Nest", "Golden Forests", "Montes Inexpugnabilis"):
            assert loc in full, f"World Codex missing {loc!r}"
        assert "[scale:" in full, "Locations should be tagged with [scale: ...]"

    def test_per_pc_appendices(self, pdf_text):
        _, full = pdf_text
        # APPENDIX A/B/C/D — non-breaking spaces collapse on extraction; tolerate any whitespace
        for letter in ("A", "B", "C", "D"):
            assert re.search(rf"APPENDIX\s+{letter}\b", full), (
                f"Missing APPENDIX {letter} per-PC sheet"
            )
        for stat in ("Body", "Mind", "Soul", "ACV", "DCV"):
            assert stat in full, f"Per-PC sheet missing stat label {stat!r}"

    def test_reference_appendix(self, pdf_text):
        _, full = pdf_text
        assert "Spike-hammer" in full, "Reference appendix missing Spike-hammer entry"
        assert "p. 196" in full or "p.196" in full or "196" in full
