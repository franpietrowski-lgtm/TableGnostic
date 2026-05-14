"""V6.25.54 — Phase C tests: Campaign export/import round-trip."""
from __future__ import annotations
import io
import json
import os

import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read()
        .split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"


def _login(email, password):
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _create_campaign(token, name="Phase C Test"):
    r = requests.post(f"{API}/campaigns", headers=_h(token),
                      json={"name": name, "system_id": "besm-4e",
                            "blurb": "phase c export test", "visibility": "private"},
                      timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def _seed_some_content(token, cid):
    # Add a knowledge node so the export has something to round-trip.
    r = requests.post(f"{API}/nodes", headers=_h(token),
                      json={"campaign_id": cid, "title": "Phase C Lorebit",
                            "type": "lore", "content": "phase c smoke"},
                      timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def test_export_returns_self_contained_json_bundle():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    camp = _create_campaign(admin, "PhC-export-shape")
    node = _seed_some_content(admin, camp["id"])

    r = requests.get(f"{API}/campaigns/{camp['id']}/export",
                     headers=_h(admin), timeout=15)
    assert r.status_code == 200, r.text
    assert r.headers.get("content-disposition", "").startswith("attachment;")
    assert "tgcampaign.json" in r.headers.get("content-disposition", "")
    assert r.headers.get("x-tg-bundle-schema") == "1"
    bundle = r.json()

    # Required envelope fields
    for k in ("schema_version", "exported_at", "exported_by",
              "source", "campaign", "collections", "stats"):
        assert k in bundle, f"missing {k} in bundle"
    assert bundle["schema_version"] == 1
    assert bundle["source"]["campaign_id"] == camp["id"]
    assert bundle["campaign"]["id"] == camp["id"]
    assert bundle["campaign"]["name"] == "PhC-export-shape"

    # The seeded node must be inside the nodes collection.
    nodes = bundle["collections"].get("nodes", [])
    assert any(n.get("id") == node["id"] for n in nodes), "seeded node missing"


def test_export_forbidden_for_non_owner():
    """Player accounts (or other GMs) cannot export someone else's campaign."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    # Register a brand-new GM, then try to export an admin-owned campaign.
    gm_email = f"phc-gm-{os.urandom(4).hex()}@tablegnostic-test.com"
    r = requests.post(f"{API}/auth/register",
                      json={"email": gm_email, "password": "PhaseC!Test123",
                            "name": "PhC GM", "role": "gm"}, timeout=10)
    assert r.status_code == 200, r.text
    gm_token = r.json()["access_token"]

    camp = _create_campaign(admin, "PhC-export-forbidden")
    r = requests.get(f"{API}/campaigns/{camp['id']}/export",
                     headers=_h(gm_token), timeout=10)
    assert r.status_code == 403, r.text


def test_export_404_for_unknown_campaign():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    r = requests.get(f"{API}/campaigns/does-not-exist/export",
                     headers=_h(admin), timeout=10)
    assert r.status_code == 404


def test_import_round_trip_creates_new_campaign_with_fresh_ids():
    """Export → upload → fresh campaign owned by importer with remapped ids."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    camp = _create_campaign(admin, "PhC-roundtrip-source")
    node = _seed_some_content(admin, camp["id"])

    bundle = requests.get(f"{API}/campaigns/{camp['id']}/export",
                          headers=_h(admin), timeout=15).json()
    body = json.dumps(bundle).encode("utf-8")

    files = {"file": ("test.tgcampaign.json", io.BytesIO(body), "application/json")}
    r = requests.post(f"{API}/campaigns/import",
                      headers=_h(admin), files=files, timeout=30)
    assert r.status_code == 200, r.text
    out = r.json()
    new_cid = out["campaign"]["id"]
    assert new_cid != camp["id"], "import must produce a fresh campaign id"
    assert out["campaign"]["name"].endswith("(imported)")
    assert out["campaign"]["imported_from"] == camp["id"]
    assert out["counts"].get("nodes", 0) >= 1
    assert out["remapped_ids"] >= 1

    # New campaign must show up in admin's list and the seeded node must
    # be reachable under the new campaign with a fresh id.
    nodes_r = requests.get(f"{API}/campaigns/{new_cid}/nodes",
                           headers=_h(admin), timeout=10)
    assert nodes_r.status_code == 200, nodes_r.text
    new_nodes = nodes_r.json()
    # The lorebit was preserved (same title) but with a brand-new id.
    matches = [n for n in new_nodes if n.get("title") == "Phase C Lorebit"]
    assert matches, "Phase C Lorebit did not round-trip into the new campaign"
    assert matches[0]["id"] != node["id"], "node id must be remapped on import"


def test_import_rejects_bad_schema_version():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    body = json.dumps({
        "schema_version": 99,
        "campaign": {"id": "x", "name": "Bad"},
        "source": {"campaign_id": "x"},
    }).encode()
    files = {"file": ("bad.tgcampaign.json", io.BytesIO(body), "application/json")}
    r = requests.post(f"{API}/campaigns/import",
                      headers=_h(admin), files=files, timeout=10)
    assert r.status_code == 400
    assert "schema_version" in r.text


def test_import_rejects_non_json():
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    files = {"file": ("bad.tgcampaign.json",
                      io.BytesIO(b"<<not json>>"), "application/json")}
    r = requests.post(f"{API}/campaigns/import",
                      headers=_h(admin), files=files, timeout=10)
    assert r.status_code == 400


def test_import_resets_public_surface_flags():
    """A campaign that was discover_published in the source must NOT
    leak that publication status into the imported copy — fresh imports
    are private until the new owner explicitly re-publishes."""
    admin = _login(ADMIN_EMAIL, ADMIN_PASS)
    camp = _create_campaign(admin, "PhC-public-reset-source")

    # Flag it as discover_published in the bundle, simulating an export
    # of a publicly-visible campaign.
    bundle = requests.get(f"{API}/campaigns/{camp['id']}/export",
                          headers=_h(admin), timeout=10).json()
    bundle["campaign"]["discover_published"] = True
    bundle["campaign"]["featured"] = True
    bundle["campaign"]["featured_at"] = "2026-01-01T00:00:00Z"
    bundle["campaign"]["canon_published"] = True

    body = json.dumps(bundle).encode("utf-8")
    files = {"file": ("test.tgcampaign.json", io.BytesIO(body), "application/json")}
    r = requests.post(f"{API}/campaigns/import",
                      headers=_h(admin), files=files, timeout=15)
    assert r.status_code == 200, r.text
    imported = r.json()["campaign"]
    assert imported.get("discover_published") is not True
    assert imported.get("featured") is not True
    assert imported.get("canon_published") is not True
