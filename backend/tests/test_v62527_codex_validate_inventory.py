"""V6.25.27 backend tests:
  1) Codex PDF unicode (em-dash) Content-Disposition fix
  2) /characters/{cid}/validate audit shape (CP Bank parity)
  3) folio.inventory_state PATCH round-trip (new tabbed inventory persistence)
"""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

# --- Test fixtures ---------------------------------------------------------
GMFRAN_EMAIL = "franpietrowski@gmail.com"
GMFRAN_PASS = "PieGod08!!"

DASH_CAMPAIGN_ID = "af461ae004364002932f93c5b71cd483"  # 'Evereantha — The Maiden Adventure'
ASCII_CAMPAIGN_ID = "01a74ce4d3064b83a94ac897e1689e62"  # 'Evereantha · The Fracture of the Unmaker'
ELI_CHAR_ID = "35b9746b30a24d2bafac5f117d673bd1"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    # try login (cookie-based)
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": GMFRAN_EMAIL, "password": GMFRAN_PASS},
               timeout=20)
    if r.status_code != 200:
        pytest.skip(f"GMFran auth failed: {r.status_code} {r.text[:200]}")
    # If a token is returned, attach as Bearer too (defensive)
    try:
        body = r.json()
        tok = body.get("token") or body.get("access_token")
        if tok:
            s.headers.update({"Authorization": f"Bearer {tok}"})
    except Exception:
        pass
    return s


# --- 1) Codex PDF em-dash regression --------------------------------------
class TestCodexPdfUnicode:
    def test_codex_pdf_ascii_campaign_returns_200(self, session):
        """ASCII-only campaign must still stream a real PDF."""
        r = session.get(
            f"{BASE_URL}/api/campaigns/{ASCII_CAMPAIGN_ID}/codex-export.pdf",
            timeout=60)
        # campaign with codex nodes -> 200; without nodes -> 400
        assert r.status_code in (200, 400), f"unexpected {r.status_code}: {r.text[:300]}"
        if r.status_code == 200:
            assert r.headers.get("content-type", "").startswith("application/pdf")
            assert r.content[:4] == b"%PDF"

    def test_codex_pdf_dash_campaign_no_unicode_crash(self, session):
        """Campaign whose name contains an em-dash must NOT crash with
        UnicodeEncodeError on Content-Disposition. Auto-seed a node if
        the campaign has none, so the endpoint can reach the header path."""
        url = f"{BASE_URL}/api/campaigns/{DASH_CAMPAIGN_ID}/codex-export.pdf"
        r = session.get(url, timeout=60)

        # If the campaign has no codex nodes, seed one so we exercise the
        # fixed Content-Disposition latin-1 path.
        if r.status_code == 400:
            seed = session.post(
                f"{BASE_URL}/api/campaigns/{DASH_CAMPAIGN_ID}/nodes",
                json={
                    "title": "TEST_v62527_unicode_node",
                    "summary": "regression seed for em-dash header",
                    "kind": "lore",
                    "shared_with_players": True,
                    "tags": ["TEST_v62527"],
                },
                timeout=30,
            )
            assert seed.status_code in (200, 201), \
                f"seed node failed: {seed.status_code} {seed.text[:200]}"
            r = session.get(url, timeout=60)

        assert r.status_code == 200, \
            f"em-dash campaign codex pdf failed: {r.status_code} {r.text[:300]}"
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF"

        # Header must be latin-1 encodable (this is the actual fix under test).
        cd = r.headers.get("content-disposition", "")
        assert cd, "missing Content-Disposition"
        cd.encode("latin-1")  # raises if regression returns


# --- 2) /validate breakdown shape (CP Bank parity) ------------------------
class TestCharacterValidateBreakdown:
    def test_eli_validate_returns_audit(self, session):
        # First fetch the canonical primer total off the character record
        # itself — Eli's saved total_points has shifted between cycles
        # (84 → 65) as the seed evolved; the test must stay anchored to
        # whatever the current primer says, not a hard-coded constant.
        ch_r = session.get(f"{BASE_URL}/api/characters/{ELI_CHAR_ID}",
                            timeout=20)
        assert ch_r.status_code == 200
        primer_total = ch_r.json().get("total_points")
        assert primer_total is not None and primer_total > 0, \
            "Eli must have a positive primer total_points"

        r = session.get(f"{BASE_URL}/api/characters/{ELI_CHAR_ID}/validate",
                        timeout=20)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        body = r.json()

        # /validate.total_points must equal the primer stored on the
        # character record; that's the contract the CP Bank widget
        # depends on.
        assert body.get("total_points") == primer_total, \
            f"total_points expected {primer_total}, got {body.get('total_points')}"

        bd = body.get("breakdown") or {}
        assert "total_spent" in bd, f"breakdown.total_spent missing: {bd}"
        assert isinstance(bd["total_spent"], (int, float)), \
            "breakdown.total_spent must be numeric"
        assert bd["total_spent"] >= 0

        # Approval flags must be booleans (not None / missing)
        for key in ("approved_for_play", "app_validated", "gm_approved"):
            assert key in body, f"missing {key} in /validate response"
            assert isinstance(body[key], bool), \
                f"{key} should be bool, got {type(body[key]).__name__}"

        # Per spec note: Eli is NOT GM-approved yet
        assert body["gm_approved"] is False, \
            "spec: Eli should currently be gm_approved=False"


# --- 3) folio.inventory_state PATCH round-trip ----------------------------
class TestInventoryStatePersistence:
    def test_patch_inventory_state_round_trip(self, session):
        payload = {
            "bucket": "inventory_state",
            "patch": {
                "items": [{
                    "id": "test-1",
                    "name": "Test Potion",
                    "category": "consumable",
                    "qty": 1,
                    "ready_required": True,
                    "charges_max": 3,
                    "charges_current": 3,
                }],
                "equipped": {},
                "attuned_ids": [],
                "readied_ids": ["test-1"],
            },
        }
        r = session.patch(
            f"{BASE_URL}/api/characters/{ELI_CHAR_ID}/folio",
            json=payload,
            timeout=20,
        )
        assert r.status_code == 200, \
            f"PATCH folio failed: {r.status_code} {r.text[:300]}"

        # GET the character and verify persistence
        g = session.get(f"{BASE_URL}/api/characters/{ELI_CHAR_ID}", timeout=20)
        assert g.status_code == 200, f"{g.status_code}: {g.text[:200]}"
        body = g.json()
        folio = body.get("folio") or {}
        inv = folio.get("inventory_state") or {}

        items = inv.get("items") or []
        assert items, f"folio.inventory_state.items empty: {inv}"
        names = [i.get("name") for i in items]
        assert "Test Potion" in names, f"Test Potion missing from {names}"

        readied = inv.get("readied_ids") or []
        assert "test-1" in readied, f"test-1 not in readied_ids={readied}"

        # Charges round-trip
        target = next(i for i in items if i.get("id") == "test-1")
        assert target.get("charges_max") == 3
        assert target.get("charges_current") == 3
        assert target.get("ready_required") is True
