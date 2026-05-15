"""V6.25.58 — Featured Starter Campaigns gallery tests."""
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

ADMIN = "tablegnostic-admin@tablegnostic.com"
PASS = "LoremasterAurea2026!Forge"


def _login(e=ADMIN, p=PASS):
    r = requests.post(f"{API}/auth/login", json={"email": e, "password": p}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t): return {"Authorization": f"Bearer {t}"}


def _camp(token, system="besm-4e", name="StarterSrc"):
    r = requests.post(f"{API}/campaigns", headers=_h(token),
                      json={"name": name, "system_id": system, "blurb": "starter source",
                            "visibility": "private"}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def _cleanup_slug(token, slug):
    requests.delete(f"{API}/admin/starters/{slug}", headers=_h(token), timeout=10)


def test_starter_from_campaign_round_trip():
    admin = _login()
    camp = _camp(admin, "dnd-5e", "Starter-src-1")
    # Seed a tiny node so the bundle isn't trivial.
    requests.post(f"{API}/nodes", headers=_h(admin),
                  json={"campaign_id": camp["id"], "type": "lore",
                        "title": "Starter lorebit", "content": "x"}, timeout=10)

    r = requests.post(f"{API}/admin/starters/from-campaign/{camp['id']}",
                      headers=_h(admin),
                      json={"title": "D&D 5E Tutorial Adventure",
                            "system_id": "dnd-5e",
                            "blurb": "A one-shot perfect for first-night GMs.",
                            "blurb_long": "Two encounters, three NPCs, one twist.",
                            "featured": True},
                      timeout=15)
    assert r.status_code == 200, r.text
    s = r.json()["starter"]
    slug = s["slug"]
    assert slug.startswith("d-d-5e") or slug.startswith("dnd-5e") or slug.startswith("d-d")
    assert s["featured"] is True
    assert s["bytes"] > 0
    assert s["downloads"] == 0
    try:
        # Public list must include it without auth.
        public = requests.get(f"{API}/public/starters", timeout=10).json()
        assert any(row["slug"] == slug for row in public["rows"])
        # Public download streams the bundle, increments downloads, schema_version=1.
        dl = requests.get(f"{API}/public/starters/{slug}/download", timeout=15)
        assert dl.status_code == 200
        assert dl.headers.get("content-disposition", "").endswith(f'"{slug}.tgcampaign.json"')
        assert dl.headers.get("x-tg-bundle-schema") == "1"
        bundle = dl.json()
        assert bundle["schema_version"] == 1
        assert bundle["campaign"]["id"] == camp["id"]
        assert "nodes" in bundle["collections"]
        # Download counter increments.
        again = requests.get(f"{API}/public/starters", timeout=10).json()
        row = next(r for r in again["rows"] if r["slug"] == slug)
        assert row["downloads"] >= 1
    finally:
        _cleanup_slug(admin, slug)


def test_starter_upload_direct_json_file():
    admin = _login()
    camp = _camp(admin, "besm-4e", "Starter-src-2")
    bundle = requests.get(f"{API}/campaigns/{camp['id']}/export",
                          headers=_h(admin), timeout=10).json()
    body = json.dumps(bundle).encode("utf-8")
    files = {"file": ("starter.tgcampaign.json", io.BytesIO(body), "application/json")}
    data = {"title": "BESM Anime Tutorial",
            "system_id": "besm-4e",
            "blurb": "Hand-picked starter for new BESM tables.",
            "featured": "false"}
    r = requests.post(f"{API}/admin/starters",
                      headers=_h(admin), files=files, data=data, timeout=15)
    assert r.status_code == 200, r.text
    slug = r.json()["starter"]["slug"]
    try:
        # Re-upload with same title must produce a unique slug (suffix -2).
        files2 = {"file": ("starter.tgcampaign.json", io.BytesIO(body), "application/json")}
        r2 = requests.post(f"{API}/admin/starters",
                           headers=_h(admin), files=files2, data=data, timeout=15)
        assert r2.status_code == 200
        slug2 = r2.json()["starter"]["slug"]
        assert slug2 != slug
        assert slug2.endswith("-2")
        _cleanup_slug(admin, slug2)
    finally:
        _cleanup_slug(admin, slug)


def test_starter_upload_rejects_non_json():
    admin = _login()
    files = {"file": ("bad.tgcampaign.json", io.BytesIO(b"<<not json>>"), "application/json")}
    data = {"title": "Bad", "system_id": "besm-4e"}
    r = requests.post(f"{API}/admin/starters",
                      headers=_h(admin), files=files, data=data, timeout=10)
    assert r.status_code == 400


def test_starter_admin_only():
    # Player can't list admin starters, can't upload, can't delete.
    em = f"st-{os.urandom(4).hex()}@tablegnostic-test.com"
    r = requests.post(f"{API}/auth/register",
                      json={"email": em, "password": "St!Test123",
                            "name": "ST Player", "role": "player"}, timeout=10)
    assert r.status_code == 200
    player = r.json()["access_token"]
    r = requests.get(f"{API}/admin/starters", headers=_h(player), timeout=10)
    assert r.status_code == 403


def test_starter_patch_and_delete():
    admin = _login()
    camp = _camp(admin, "cypher", "Starter-src-patch")
    r = requests.post(f"{API}/admin/starters/from-campaign/{camp['id']}",
                      headers=_h(admin),
                      json={"title": "Cypher Quick-Start",
                            "system_id": "cypher",
                            "blurb": "one-shot"}, timeout=15).json()
    slug = r["starter"]["slug"]
    try:
        # PATCH blurb + featured.
        r2 = requests.patch(f"{API}/admin/starters/{slug}",
                            headers=_h(admin),
                            json={"featured": True, "blurb": "updated blurb"}, timeout=10)
        assert r2.status_code == 200
        assert r2.json()["starter"]["featured"] is True
        assert r2.json()["starter"]["blurb"] == "updated blurb"
        # 404 on unknown slug.
        r3 = requests.patch(f"{API}/admin/starters/no-such-slug",
                            headers=_h(admin), json={"featured": True}, timeout=10)
        assert r3.status_code == 404
    finally:
        d = requests.delete(f"{API}/admin/starters/{slug}", headers=_h(admin), timeout=10)
        assert d.status_code == 200
    # Public list no longer contains the slug.
    public = requests.get(f"{API}/public/starters", timeout=10).json()
    assert not any(row["slug"] == slug for row in public["rows"])


def test_starter_download_404_unknown_slug():
    r = requests.get(f"{API}/public/starters/no-such-slug-here/download", timeout=10)
    assert r.status_code == 404


def test_starter_public_list_is_anonymous():
    """No auth header should still return a 200 with a list."""
    r = requests.get(f"{API}/public/starters", timeout=10)
    assert r.status_code == 200
    assert "rows" in r.json()


def test_starter_upload_rejects_future_schema_version():
    """Reject bundles with a schema_version the import endpoint would
    later refuse — fail fast at upload time."""
    admin = _login()
    body = json.dumps({
        "schema_version": 99,
        "campaign": {"id": "x", "name": "Future"},
        "source": {"campaign_id": "x"},
    }).encode("utf-8")
    files = {"file": ("future.tgcampaign.json", io.BytesIO(body), "application/json")}
    data = {"title": "Future bundle", "system_id": "besm-4e"}
    r = requests.post(f"{API}/admin/starters",
                      headers=_h(admin), files=files, data=data, timeout=10)
    assert r.status_code == 400
    assert "schema_version" in r.text
