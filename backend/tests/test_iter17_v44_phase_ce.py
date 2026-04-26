"""V4.4 Phase C+E — Knowledge Web ingest (Claude) + DriveThruRPG PDF export.

Destructive: calls reset-to-evereantha at module start.
LLM-cost-aware: only ONE real Claude ingest call; reuse ingest_id downstream.
"""
import io
import os
import pytest
import requests

def _read_backend_url():
    if os.environ.get("REACT_APP_BACKEND_URL"):
        return os.environ["REACT_APP_BACKEND_URL"]
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

BASE = _read_backend_url().rstrip("/")
ADMIN = {"email": "franpietrowski@gmail.com", "password": "PieGod08!!"}


# ─────────── Fixtures ───────────

@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    # Reset to a clean Evereantha demo (also wipes ingestions per Phase C).
    rr = s.post(f"{BASE}/api/admin/reset-to-evereantha?confirm=WIPE", timeout=60)
    assert rr.status_code in (200, 201), rr.text
    return s


@pytest.fixture(scope="module")
def evereantha_id(admin_session):
    r = admin_session.get(f"{BASE}/api/campaigns", timeout=20)
    assert r.status_code == 200
    camps = r.json()
    ev = next((c for c in camps if "evereantha" in (c.get("name") or "").lower()), None)
    assert ev, f"Evereantha campaign not found in {[(c.get('name')) for c in camps]}"
    return ev["id"]


@pytest.fixture(scope="module")
def player_session():
    s = requests.Session()
    email = "TEST_iter17_player@example.com"
    s.post(f"{BASE}/api/auth/register",
           json={"email": email, "password": "Pp123456!!", "name": "T17P", "role": "player"},
           timeout=20)
    r = s.post(f"{BASE}/api/auth/login",
               json={"email": email, "password": "Pp123456!!"}, timeout=20)
    assert r.status_code == 200
    tok = r.json().get("access_token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


SAMPLE_MD = (
    "# Eagles Nest — A Hamlet's Heart\n\n"
    "The mayor **Maelren Sorenson** governs forty households.\n\n"
    "## Mechanics — Mayoral Authority\n\n"
    "- BESM 4E p.142 'Authority' attribute, Cost 2 pts/level, Rank 3.\n\n"
    "## Power Pack — Manor's Echo\n\n"
    "Sense + Heightened Senses (p.180), Levels 2-4.\n\n"
    "## Location — The Manor\n\n"
    "Central manor ringed by irrigation ponds.\n"
)


# ─────────── PHASE C — INGEST ───────────

class TestIngestErrors:
    def test_unsupported_type_400(self, admin_session, evereantha_id):
        files = {"file": ("evil.exe", b"MZ\x90\x00binarydata", "application/octet-stream")}
        r = admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/ingest",
                                files=files, timeout=30)
        assert r.status_code == 400, r.text

    def test_empty_file_400(self, admin_session, evereantha_id):
        files = {"file": ("empty.md", b"", "text/markdown")}
        r = admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/ingest",
                                files=files, timeout=30)
        assert r.status_code == 400, r.text

    def test_oversize_file_413(self, admin_session, evereantha_id):
        big = b"x" * (25 * 1024 * 1024)
        files = {"file": ("big.md", big, "text/markdown")}
        r = admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/ingest",
                                files=files, timeout=60)
        assert r.status_code == 413, f"expected 413 got {r.status_code}: {r.text[:200]}"

    def test_player_403(self, player_session, evereantha_id):
        files = {"file": ("note.md", b"Hi there", "text/markdown")}
        r = player_session.post(f"{BASE}/api/campaigns/{evereantha_id}/ingest",
                                 files=files, timeout=30)
        assert r.status_code == 403, r.text


# Module-cached ingest result (single Claude call).
_INGEST_CACHE = {}


@pytest.fixture(scope="module")
def ingest_doc(admin_session, evereantha_id):
    if "doc" in _INGEST_CACHE:
        return _INGEST_CACHE["doc"]
    files = {"file": ("sample_lore.md", SAMPLE_MD.encode("utf-8"), "text/markdown")}
    r = admin_session.post(f"{BASE}/api/campaigns/{evereantha_id}/ingest",
                            files=files, timeout=180)
    assert r.status_code == 200, r.text
    doc = r.json()
    _INGEST_CACHE["doc"] = doc
    return doc


class TestIngestHappy:
    def test_ingest_shape(self, ingest_doc):
        assert "id" in ingest_doc
        assert ingest_doc["status"] == "pending"
        assert isinstance(ingest_doc.get("detected_kind_counts"), dict)
        sugs = ingest_doc.get("suggestions") or []
        assert len(sugs) >= 1
        valid_kinds = {"attribute", "power_pack", "power_bundle", "item", "weapon",
                       "skill", "npc", "location", "lore", "quest"}
        for s in sugs:
            assert s["kind"] in valid_kinds
            assert "title" in s and "summary" in s
            assert "atelier_phase" in s and 1 <= int(s["atelier_phase"]) <= 7
            assert "source_ref" in s
            assert s.get("accepted") is False

    def test_list_ingestions(self, admin_session, evereantha_id, ingest_doc):
        r = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/ingestions", timeout=20)
        assert r.status_code == 200
        ids = [d["id"] for d in r.json()]
        assert ingest_doc["id"] in ids

    def test_get_single_ingestion(self, admin_session, ingest_doc):
        r = admin_session.get(f"{BASE}/api/ingestions/{ingest_doc['id']}", timeout=20)
        assert r.status_code == 200
        assert r.json()["id"] == ingest_doc["id"]

    def test_accept_persists_nodes_and_custom_attrs(self, admin_session, ingest_doc, evereantha_id):
        sugs = ingest_doc["suggestions"]
        # Accept first 3 (or all if fewer).
        idxs = list(range(min(3, len(sugs))))
        r = admin_session.post(
            f"{BASE}/api/ingestions/{ingest_doc['id']}/accept",
            json={"accepted_indices": idxs}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert len(body["accepted"]) == len(idxs)
        # Status transitions.
        rg = admin_session.get(f"{BASE}/api/ingestions/{ingest_doc['id']}", timeout=20)
        d = rg.json()
        assert d["status"] in ("partial", "accepted")
        for i in idxs:
            assert d["suggestions"][i]["accepted"] is True
            assert "created_id" in d["suggestions"][i]
            assert d["suggestions"][i]["created_kind"] in ("node", "custom_attribute")
        # Verify GET nodes endpoint reflects new node entries (if any node-kind accepted).
        rn = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/nodes", timeout=20)
        assert rn.status_code == 200

    def test_delete_ingestion_keeps_children(self, admin_session, evereantha_id):
        # Re-fetch to get the id (don't burn another LLM call).
        rl = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/ingestions", timeout=20)
        rows = rl.json()
        assert rows
        target = rows[0]
        # Count nodes/custom_attrs before delete.
        nodes_before = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/nodes", timeout=20).json()
        rd = admin_session.delete(f"{BASE}/api/ingestions/{target['id']}", timeout=20)
        assert rd.status_code == 200
        # Ingestion gone.
        rg = admin_session.get(f"{BASE}/api/ingestions/{target['id']}", timeout=20)
        assert rg.status_code == 404
        # Children (nodes) preserved.
        nodes_after = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/nodes", timeout=20).json()
        assert len(nodes_after) >= len(nodes_before)


# ─────────── PHASE E — PDF EXPORT ───────────

class TestPdfExport:
    def test_pdf_admin_returns_pdf(self, admin_session, evereantha_id):
        r = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/export.pdf", timeout=60)
        assert r.status_code == 200, r.text[:300]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        body = r.content
        assert body[:4] == b"%PDF", f"missing magic: {body[:8]!r}"
        assert len(body) > 50_000, f"PDF too small: {len(body)} bytes"
        # Header latin-1 safe (campaign name has em-dash).
        cd = r.headers.get("content-disposition", "")
        assert cd
        cd.encode("latin-1")  # would raise if not safe
        # Save for chapter inspection.
        path = "/tmp/iter17_export.pdf"
        with open(path, "wb") as f:
            f.write(body)
        # Inspect with pypdf.
        from pypdf import PdfReader
        rdr = PdfReader(io.BytesIO(body))
        full_text = "\n".join((p.extract_text() or "") for p in rdr.pages)
        # Should mention BESM 4E (system header).
        assert "BESM 4E" in full_text, "expected 'BESM 4E' header text in PDF"
        # ToC: 4 chapters expected (S0+S1+S2 / S3+S4 / S5+S6 / S7+S8).
        chapter_count = sum(1 for line in full_text.splitlines()
                            if line.strip().startswith("Chapter ") and any(c.isdigit() for c in line))
        # Be lenient: at least 4 chapter lines (ToC + chapter pages add up to ≥4).
        assert chapter_count >= 4, f"expected ≥4 'Chapter N' refs, found {chapter_count}"
        # Chapter 1 should reference Session 0/1/2.
        assert "Session 0" in full_text or "Session 1" in full_text, \
            "expected Session 0 or 1 mention"

    def test_pdf_player_403(self, player_session, evereantha_id):
        r = player_session.get(f"{BASE}/api/campaigns/{evereantha_id}/export.pdf", timeout=20)
        assert r.status_code == 403

    def test_pdf_no_sessions_400(self, admin_session):
        # Create a fresh campaign with zero sessions.
        rc = admin_session.post(f"{BASE}/api/campaigns",
                                 json={"name": "TEST_empty_iter17", "system_id": "besm-4e"},
                                 timeout=20)
        assert rc.status_code in (200, 201), rc.text
        cid = rc.json()["id"]
        try:
            r = admin_session.get(f"{BASE}/api/campaigns/{cid}/export.pdf", timeout=30)
            assert r.status_code == 400, f"expected 400 got {r.status_code}"
        finally:
            admin_session.delete(f"{BASE}/api/campaigns/{cid}", timeout=20)


# ─────────── PHASE C+E — Reset wipes ingestions ───────────

class TestResetWipesIngestions:
    def test_reset_clears_ingestions(self, admin_session, evereantha_id):
        # Pre-condition: at least no exception before.
        admin_session.post(f"{BASE}/api/admin/reset-to-evereantha?confirm=WIPE", timeout=60)
        # New campaign id may differ; fetch fresh.
        camps = admin_session.get(f"{BASE}/api/campaigns", timeout=20).json()
        ev = next((c for c in camps if "evereantha" in (c.get("name") or "").lower()), None)
        assert ev
        rl = admin_session.get(f"{BASE}/api/campaigns/{ev['id']}/ingestions", timeout=20)
        assert rl.status_code == 200
        assert rl.json() == []
