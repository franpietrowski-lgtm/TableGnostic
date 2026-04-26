"""V4.4 Phase E — PDF polish + Profile byline (iter18).

Verifies:
  * PATCH /api/auth/me persists byline_name; clearing returns to None.
  * PDF cover renders byline + Weaved in TableGnostic + Dyskami attribution.
  * Chapter pages use a single 'CHAPTER  I' heading (no duplicate 'Chapter 1').
  * Sessions have multiple paragraphs.
  * Legal page contains 'Publisher's Required Attribution'.
  * Footer shows 'Weaved in TableGnostic · by Fran Pietrowski'.
  * Regression on PDF endpoint (player 403, no-sessions 400).
"""
import io
import os
import re
import pytest
import requests


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


# ─────────── Fixtures ───────────

@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    rr = s.post(f"{BASE}/api/admin/reset-to-evereantha?confirm=WIPE", timeout=120)
    assert rr.status_code in (200, 201), rr.text
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
    email = "TEST_iter18_player@example.com"
    s.post(f"{BASE}/api/auth/register",
           json={"email": email, "password": "Pp123456!!", "name": "T18P", "role": "player"},
           timeout=20)
    r = s.post(f"{BASE}/api/auth/login",
               json={"email": email, "password": "Pp123456!!"}, timeout=20)
    assert r.status_code == 200
    tok = r.json().get("access_token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


# ─────────── Profile byline ───────────

class TestProfileByline:
    def test_patch_sets_byline(self, admin_session):
        r = admin_session.patch(f"{BASE}/api/auth/me",
                                json={"byline_name": "Fran Pietrowski"}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("byline_name") == "Fran Pietrowski"
        # Persisted via GET /me
        rg = admin_session.get(f"{BASE}/api/auth/me", timeout=20)
        assert rg.status_code == 200
        assert rg.json().get("byline_name") == "Fran Pietrowski"

    def test_patch_empty_clears(self, admin_session):
        r = admin_session.patch(f"{BASE}/api/auth/me",
                                json={"byline_name": ""}, timeout=20)
        assert r.status_code == 200
        # Empty string should clear to None per route logic.
        assert r.json().get("byline_name") in (None, "")
        # Verify
        rg = admin_session.get(f"{BASE}/api/auth/me", timeout=20)
        assert rg.json().get("byline_name") in (None, "")

    def test_patch_empty_body_noop(self, admin_session):
        # First set a known value
        admin_session.patch(f"{BASE}/api/auth/me",
                            json={"byline_name": "Sentinel Name"}, timeout=20)
        # Empty body — should not change anything
        r = admin_session.patch(f"{BASE}/api/auth/me", json={}, timeout=20)
        assert r.status_code == 200
        assert r.json().get("byline_name") == "Sentinel Name"

    def test_set_back_to_fran(self, admin_session):
        """Leave the byline as 'Fran Pietrowski' for downstream PDF tests + UI."""
        r = admin_session.patch(f"{BASE}/api/auth/me",
                                json={"byline_name": "Fran Pietrowski"}, timeout=20)
        assert r.status_code == 200
        assert r.json().get("byline_name") == "Fran Pietrowski"


# ─────────── PDF export — content & polish ───────────

@pytest.fixture(scope="module")
def pdf_bytes(admin_session, evereantha_id):
    # Ensure byline is set BEFORE export.
    admin_session.patch(f"{BASE}/api/auth/me",
                        json={"byline_name": "Fran Pietrowski"}, timeout=20)
    r = admin_session.get(f"{BASE}/api/campaigns/{evereantha_id}/export.pdf", timeout=120)
    assert r.status_code == 200, r.text[:300]
    assert r.headers.get("content-type", "").startswith("application/pdf")
    body = r.content
    assert body[:4] == b"%PDF"
    with open("/tmp/iter18_export.pdf", "wb") as f:
        f.write(body)
    return body


class TestPdfPolish:
    def test_pdf_basics(self, pdf_bytes):
        from pypdf import PdfReader
        rdr = PdfReader(io.BytesIO(pdf_bytes))
        assert len(rdr.pages) >= 10, f"expected ≥10 pages, got {len(rdr.pages)}"
        assert len(pdf_bytes) > 50_000

    def test_cover_byline_and_weaved_and_dyskami(self, pdf_bytes):
        from pypdf import PdfReader
        rdr = PdfReader(io.BytesIO(pdf_bytes))
        cover_text = rdr.pages[0].extract_text() or ""
        assert "Fran Pietrowski" in cover_text, f"cover missing GM byline: {cover_text!r}"
        # 'by Fran Pietrowski'
        assert re.search(r"by\s+Fran Pietrowski", cover_text), \
            "cover should say 'by Fran Pietrowski'"
        assert "Weaved in TableGnostic" in cover_text, \
            "cover missing 'Weaved in TableGnostic' line"
        # Dyskami required attribution on cover bottom
        assert "Dyskami" in cover_text, "cover missing Dyskami attribution"
        # © year
        assert ("©" in cover_text) or ("(C)" in cover_text) or ("2026" in cover_text), \
            "cover missing copyright stamp"

    def test_chapter_pages_use_single_heading(self, pdf_bytes):
        """No duplicate 'Chapter 1\\nChapter 1'. Should see 'CHAPTER  I' label."""
        from pypdf import PdfReader
        rdr = PdfReader(io.BytesIO(pdf_bytes))
        full = "\n".join((p.extract_text() or "") for p in rdr.pages)
        # Check at least one CHAPTER  <ROMAN> appearance
        assert re.search(r"CHAPTER\s+I\b", full), \
            f"expected 'CHAPTER  I' in PDF; first 1k: {full[:1000]!r}"
        # Check Roman numerals used in TOC (Chapter I/II/...).
        assert re.search(r"Chapter\s+I\b", full), \
            "TOC should list Chapter I (Roman numeral)"
        # No duplicated 'Chapter 1\nChapter 1' on the same chapter page.
        # A duplicate would show both heading variants verbatim back-to-back.
        for page in rdr.pages:
            t = page.extract_text() or ""
            # Detect duplicate Arabic-numeral chapter heading printed twice.
            arabic_dupes = re.findall(r"Chapter\s+(\d+)[^\n]*\n[^\n]*Chapter\s+\1\b", t)
            assert not arabic_dupes, f"duplicate Chapter heading on page: {arabic_dupes}"

    def test_sessions_have_multiple_paragraphs(self, pdf_bytes):
        """Each speaker turn should be its own paragraph; verify body pages
        contain multiple line groups, not a single wall."""
        from pypdf import PdfReader
        rdr = PdfReader(io.BytesIO(pdf_bytes))
        # Body pages 3..N-1 (skip cover, TOC, and trailing legal).
        body_pages = rdr.pages[2:-1]
        # Heuristic: at least one body page should contain ≥ 8 line breaks
        # — paragraph-broken prose produces many short lines.
        any_paragraph_rich = False
        for p in body_pages:
            t = p.extract_text() or ""
            if t.count("\n") >= 8:
                any_paragraph_rich = True
                break
        assert any_paragraph_rich, "no paragraph-rich body page found"

    def test_legal_page_has_required_attribution(self, pdf_bytes):
        from pypdf import PdfReader
        rdr = PdfReader(io.BytesIO(pdf_bytes))
        last_text = rdr.pages[-1].extract_text() or ""
        # Legal block at end of doc.
        joined = "\n".join((p.extract_text() or "") for p in rdr.pages[-2:])
        assert "Publisher's Required Attribution" in joined or \
               "Publisher\u2019s Required Attribution" in joined, \
            f"missing 'Publisher's Required Attribution' callout in: {joined[:500]!r}"
        assert "DriveThruRPG" in joined
        assert "Compliance Summary" in joined
        # Markdown markers should be stripped on the legal page.
        assert "**" not in last_text, "raw markdown ** still present on legal page"

    def test_footer_byline(self, pdf_bytes):
        from pypdf import PdfReader
        rdr = PdfReader(io.BytesIO(pdf_bytes))
        # Body page 3 (TOC or chapter) should have the footer 'by Fran Pietrowski'.
        # pypdf may collapse footer text; check across all post-cover pages.
        body_text = "\n".join((p.extract_text() or "") for p in rdr.pages[1:])
        assert "Weaved in TableGnostic" in body_text
        assert "Fran Pietrowski" in body_text


# ─────────── PDF endpoint regressions ───────────

class TestPdfRegression:
    def test_player_forbidden(self, player_session, evereantha_id):
        r = player_session.get(f"{BASE}/api/campaigns/{evereantha_id}/export.pdf", timeout=20)
        assert r.status_code == 403

    def test_no_sessions_400(self, admin_session):
        rc = admin_session.post(f"{BASE}/api/campaigns",
                                json={"name": "TEST_empty_iter18", "system_id": "besm-4e"},
                                timeout=20)
        assert rc.status_code in (200, 201), rc.text
        cid = rc.json()["id"]
        try:
            r = admin_session.get(f"{BASE}/api/campaigns/{cid}/export.pdf", timeout=30)
            assert r.status_code == 400
        finally:
            admin_session.delete(f"{BASE}/api/campaigns/{cid}", timeout=20)


# ─────────── Final: leave byline as Fran Pietrowski ───────────

class TestLeaveByline:
    def test_final_state(self, admin_session):
        admin_session.patch(f"{BASE}/api/auth/me",
                            json={"byline_name": "Fran Pietrowski"}, timeout=20)
        r = admin_session.get(f"{BASE}/api/auth/me", timeout=20)
        assert r.json().get("byline_name") == "Fran Pietrowski"
