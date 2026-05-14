"""V6.25.57 — Phase F: GM Bestiary endpoint tests."""
from __future__ import annotations
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


def _camp(token, system="dnd-5e", name="PhF"):
    r = requests.post(f"{API}/campaigns", headers=_h(token),
                      json={"name": name, "system_id": system, "blurb": "phf", "visibility": "private"},
                      timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def test_bestiary_dnd5e_returns_srd_monsters():
    admin = _login()
    c = _camp(admin, "dnd-5e", "PhF-dnd")
    r = requests.get(f"{API}/campaigns/{c['id']}/bestiary",
                     headers=_h(admin), timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["system_id"] == "dnd-5e"
    assert d["total"] > 0
    # Goblin or Beholder must be in the SRD list.
    names = [r["name"].lower() for r in d["rows"]]
    assert any("goblin" in n or "beholder" in n or "kobold" in n for n in names)
    # Required fields per row.
    row = d["rows"][0]
    for k in ("id", "name", "tooltip", "color"):
        assert row.get(k) is not None, f"row missing {k}: {row}"


def test_bestiary_cypher_returns_creatures():
    admin = _login()
    c = _camp(admin, "cypher", "PhF-cyph")
    r = requests.get(f"{API}/campaigns/{c['id']}/bestiary",
                     headers=_h(admin), timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] > 0
    assert all(r["source"] in ("srd", "custom") for r in d["rows"])


def test_bestiary_besm_returns_only_custom():
    """BESM has no canon monster list — base output is empty, custom
    entity-typed nodes are the only source."""
    admin = _login()
    c = _camp(admin, "besm-4e", "PhF-besm")
    r = requests.get(f"{API}/campaigns/{c['id']}/bestiary",
                     headers=_h(admin), timeout=10).json()
    assert r["total"] == 0
    # Seed a custom monster — has to round-trip into the bestiary.
    requests.post(f"{API}/nodes", headers=_h(admin),
                  json={"campaign_id": c["id"], "type": "monster",
                        "title": "Crystal Wyrm",
                        "content": "Custom homebrew",
                        "fields": {"hp": 88, "ac": 17, "cr": 6, "atks": "Crystal Bite 2d10+5"}},
                  timeout=10)
    r2 = requests.get(f"{API}/campaigns/{c['id']}/bestiary",
                      headers=_h(admin), timeout=10).json()
    assert r2["total"] >= 1
    names = [row["name"] for row in r2["rows"]]
    assert "Crystal Wyrm" in names


def test_bestiary_filter_q():
    admin = _login()
    c = _camp(admin, "dnd-5e", "PhF-q")
    r = requests.get(f"{API}/campaigns/{c['id']}/bestiary?q=dragon",
                     headers=_h(admin), timeout=10).json()
    # All returned rows should be dragon-ish.
    for row in r["rows"]:
        hay = (row.get("name", "") + " " + (row.get("type") or "")).lower()
        assert "dragon" in hay, f"row {row['name']} doesn't match dragon filter"


def test_bestiary_403_for_non_gm():
    admin = _login()
    c = _camp(admin, "dnd-5e", "PhF-403")
    # Fresh GM not seated on admin's table.
    em = f"phf-gm-{os.urandom(4).hex()}@tablegnostic-test.com"
    r = requests.post(f"{API}/auth/register",
                      json={"email": em, "password": "PhF!Test123",
                            "name": "PhF Other", "role": "gm"}, timeout=10)
    other_token = r.json()["access_token"]
    r2 = requests.get(f"{API}/campaigns/{c['id']}/bestiary",
                      headers=_h(other_token), timeout=10)
    assert r2.status_code == 403


def test_bestiary_404_unknown():
    admin = _login()
    r = requests.get(f"{API}/campaigns/does-not-exist/bestiary",
                     headers=_h(admin), timeout=10)
    assert r.status_code == 404
