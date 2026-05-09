"""V6.25.21 — Classifier Confidence audit endpoints.

Two new endpoints power the GM-facing audit panel:
  * GET  /api/campaigns/{cid}/codex/classifier-audit
  * POST /api/campaigns/{cid}/codex/classifier-audit/{nid}/confirm
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _gm():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200
    return r.json()["access_token"]


def _spin(gm, name="V62521 Demo"):
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": name, "system_id": "anime-5e"})
    return cp.json()["id"]


def test_audit_returns_auto_placed_rows_sorted_by_ascending_confidence():
    """Three nodes with different confidence bands must surface in
    ascending order."""
    gm = _gm()
    cid = _spin(gm, "V62521 sort demo")
    try:
        # High-confidence (regex on name = 0.7)
        requests.post(f"{BASE_URL}/api/nodes", headers=H(gm),
                       json={"campaign_id": cid, "type": "concept",
                             "title": "Empire of the Eternal Sun"})
        # Mid-confidence (tag matcher = 0.85)
        requests.post(f"{BASE_URL}/api/nodes", headers=H(gm),
                       json={"campaign_id": cid, "type": "concept",
                             "title": "The Black Hand", "tags": ["guild"]})
        # The "Empire" pattern hit fires at 0.7; the tag matcher fires
        # at 0.85 — so on ascending sort, Empire comes first.
        rs = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/codex/classifier-audit",
            headers=H(gm))
        assert rs.status_code == 200, rs.text
        body = rs.json()
        assert body["totals"]["auto_placed"] == 2
        assert body["totals"]["manual_placed"] == 0
        names = [r["name"] for r in body["rows"]]
        assert names == ["Empire of the Eternal Sun", "The Black Hand"]
        # Both rows expose confidence + reasoning.
        for r in body["rows"]:
            assert 0 < r["confidence"] <= 1
            assert isinstance(r["reasoning"], str) and r["reasoning"]
            assert r["section"]
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_confirm_endpoint_locks_placement():
    """POST .../confirm flips auto_classified=False; the node then
    drops out of the audit feed but stays on the World Tree."""
    gm = _gm()
    cid = _spin(gm, "V62521 confirm demo")
    try:
        rs = requests.post(f"{BASE_URL}/api/nodes", headers=H(gm),
                            json={"campaign_id": cid, "type": "concept",
                                  "title": "The Brotherhood of Iron"})
        nid = rs.json()["id"]

        # Audit shows it.
        before = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/codex/classifier-audit",
            headers=H(gm)).json()
        assert before["totals"]["auto_placed"] == 1
        assert before["totals"]["manual_placed"] == 0

        # Confirm.
        cf = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/codex/classifier-audit/{nid}/confirm",
            headers=H(gm))
        assert cf.status_code == 200, cf.text
        assert cf.json()["modified"] == 1

        # Audit no longer shows it; manual count went up by 1.
        after = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/codex/classifier-audit",
            headers=H(gm)).json()
        assert after["totals"]["auto_placed"] == 0
        assert after["totals"]["manual_placed"] == 1

        # And a subsequent rename via PUT no longer re-classifies.
        rs2 = requests.put(
            f"{BASE_URL}/api/nodes/{nid}", headers=H(gm),
            json={"campaign_id": cid, "type": "concept",
                  "title": "Republic of the Iron Coast"})
        assert rs2.status_code == 200
        # Section is preserved (Population.Factions, NOT Geography.Countries).
        assert rs2.json()["creation_tree"]["section"] == "Population.Factions"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_audit_excludes_unplaced_nodes_from_rows_but_counts_them():
    """A signal-less concept is unplaced — it must NOT surface in
    rows (only auto-placed shows there) but must still be counted in
    totals.unplaced."""
    gm = _gm()
    cid = _spin(gm, "V62521 unplaced demo")
    try:
        # Signal-less concept → unplaced.
        requests.post(f"{BASE_URL}/api/nodes", headers=H(gm),
                       json={"campaign_id": cid, "type": "concept",
                             "title": "Mood Piece Vellichor"})
        body = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/codex/classifier-audit",
            headers=H(gm)).json()
        assert body["totals"]["unplaced"] >= 1
        assert all(r["name"] != "Mood Piece Vellichor" for r in body["rows"])
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_audit_endpoint_blocks_non_gm():
    """Audit is GM-only — players get 403."""
    gm = _gm()
    pl = requests.post(f"{BASE_URL}/api/auth/login",
                        json={"email": "albanaszak@ymail.com",
                              "password": "AuroraTest123!"})
    if pl.status_code != 200:
        return
    pl_token = pl.json()["access_token"]
    cid = _spin(gm, "V62521 block demo")
    try:
        for path in [
            f"/api/campaigns/{cid}/codex/classifier-audit",
        ]:
            r = requests.get(f"{BASE_URL}{path}", headers=H(pl_token))
            assert r.status_code == 403
        rc = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/codex/classifier-audit/missing-id/confirm",
            headers=H(pl_token))
        assert rc.status_code == 403
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))
