"""V6.25.25 — Cypher Flavor + BESM converter + Reference library aggregator + Codex PDF."""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _login_gm():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ── Flavors ──────────────────────────────────────────────────────────


def test_flavors_full_listing():
    r = requests.get(f"{BASE_URL}/api/cypher/flavors")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 6
    keys = {f["key"] for f in body["rows"]}
    assert {"magic", "combat", "stealth", "technology", "skills-knowledge",
            "horror-occult"}.issubset(keys)


def test_flavors_genre_filter():
    r = requests.get(f"{BASE_URL}/api/cypher/flavors?genre=horror")
    assert r.status_code == 200
    rows = r.json()["rows"]
    for row in rows:
        assert ("horror" in row["genres"]) or ("any" in row["genres"])
    # Magic + Stealth + Skills + Horror-Occult = at least 4 for horror.
    assert len(rows) >= 3


def test_flavors_substitutions_present():
    r = requests.get(f"{BASE_URL}/api/cypher/flavors?genre=fantasy")
    rows = r.json()["rows"]
    magic = next((x for x in rows if x["key"] == "magic"), None)
    assert magic and magic["substitutions"].get("Onslaught") == "Eldritch Bolt"


def test_reference_includes_flavors():
    r = requests.get(f"{BASE_URL}/api/systems/cypher/reference")
    body = r.json()
    assert "flavors" in body
    assert len(body["flavors"]) >= 6


# ── Cypher → BESM converter ──────────────────────────────────────────


def test_converter_warrior_default():
    r = requests.get(f"{BASE_URL}/api/cypher/besm-conversion",
                       params={"type": "warrior", "tier": 1})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type_block"]["primary_stat"] == "BODY"
    assert body["estimated_cp_cost"] > 0
    # Cost notes always present.
    assert any("Item" in n for n in body["balancing_notes"])


def test_converter_adept_tier3_with_focus():
    r = requests.get(f"{BASE_URL}/api/cypher/besm-conversion",
                       params={"type": "adept", "descriptor": "mystical",
                               "focus": "bears a halo of fire", "tier": 3})
    body = r.json()
    assert body["type_block"]["primary_stat"] == "MIND"
    # Mystical descriptor adds Sixth Sense (Magic).
    assert body["descriptor_tweak"]["add_attribute"]["name"] == "Sixth Sense (Magic)"
    assert body["focus_block"]["power_pack"] == "Pyromantic Aura"
    # Adept tier 3 → primary stat (mind) bumped by (3-1)//2 = 1.
    assert body["stats_recommended"]["mind"] >= 6


def test_converter_unknown_falls_back_to_warrior():
    r = requests.get(f"{BASE_URL}/api/cypher/besm-conversion",
                       params={"type": "warlock"})
    body = r.json()
    assert body["type_block"]["primary_stat"] == "BODY"


# ── Reference library aggregator ─────────────────────────────────────


def test_reference_library_requires_system_id():
    token = _login_gm()
    r = requests.get(f"{BASE_URL}/api/reference/library",
                       headers=H(token))
    assert r.status_code == 422, r.text


def test_reference_library_aggregates_for_system():
    """Create a campaign + a custom reference row, then verify the
    library aggregator surfaces the row tagged with the campaign name."""
    token = _login_gm()
    # Create campaign.
    r = requests.post(f"{BASE_URL}/api/campaigns", headers=H(token),
                       json={"name": "V62525 ref-lib", "system_id": "cypher"})
    cid = r.json()["id"]
    try:
        # Author a custom reference row.
        rr = requests.post(f"{BASE_URL}/api/campaigns/{cid}/reference",
                            headers=H(token),
                            json={"kind": "descriptor",
                                  "name": "Ashen-Souled",
                                  "summary": "Descriptor born of cinder."})
        assert rr.status_code == 200, rr.text

        # Library should surface it.
        lib = requests.get(f"{BASE_URL}/api/reference/library?system_id=cypher",
                            headers=H(token))
        assert lib.status_code == 200, lib.text
        body = lib.json()
        assert body["system_id"] == "cypher"
        names = [r["name"] for r in body["rows"]]
        assert "Ashen-Souled" in names
        ash = next(r for r in body["rows"] if r["name"] == "Ashen-Souled")
        assert ash["campaign_name"] == "V62525 ref-lib"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(token))


# ── Codex PDF inverted theme ─────────────────────────────────────────


def test_codex_pdf_export_requires_shared_nodes():
    """Empty campaign → 400."""
    token = _login_gm()
    r = requests.post(f"{BASE_URL}/api/campaigns", headers=H(token),
                       json={"name": "V62525 codex-empty", "system_id": "besm-4e"})
    cid = r.json()["id"]
    try:
        rr = requests.get(f"{BASE_URL}/api/campaigns/{cid}/codex-export.pdf",
                           headers=H(token))
        assert rr.status_code == 400, rr.text
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(token))


def test_codex_pdf_export_emits_pdf():
    """Seed one shared node → endpoint returns a non-empty PDF stream."""
    token = _login_gm()
    r = requests.post(f"{BASE_URL}/api/campaigns", headers=H(token),
                       json={"name": "V62525 codex-pdf", "system_id": "besm-4e"})
    cid = r.json()["id"]
    try:
        nr = requests.post(f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                            headers=H(token),
                            json={"name": "Iron Coast Republic",
                                  "title": "Iron Coast Republic",
                                  "type": "country",
                                  "node_kind": "country",
                                  "summary": "Coastal trade league.",
                                  "visibility": "shared"})
        assert nr.status_code == 200, nr.text

        pr = requests.get(f"{BASE_URL}/api/campaigns/{cid}/codex-export.pdf",
                           headers=H(token))
        assert pr.status_code == 200, pr.text[:200]
        assert pr.content[:4] == b"%PDF", pr.content[:20]
        assert pr.headers["content-type"].startswith("application/pdf")
        assert "codex.pdf" in pr.headers.get("content-disposition", "")
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(token))
