"""V6.25.45 — Catalogue gaps + writer-role registration tests.

Covers:
  * BESM /api/besm/reference now exposes 4 new equipment-mod pools
    (weapon_enhancements, weapon_limiters, item_enhancements,
    item_limiters) + class_templates has 18 entries (was 12 — added
    Demon Hunter, Idol, Pet Trainer, Aurae Acolyte, Mortiscure
    Initiate, Wandering Monk).
  * Auth /api/auth/register accepts the two new writer roles
    (worldbuilder, storyteller) and rejects unknown roles.
"""
from __future__ import annotations
import os
import time

import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read()
        .split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"


def test_besm_reference_exposes_new_catalogue_surfaces():
    r = requests.get(f"{API}/besm/reference", timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()

    # Class templates — at least 18 entries with the new ones present.
    classes = d.get("class_templates") or []
    assert len(classes) >= 18, f"expected ≥18 class templates, got {len(classes)}"
    names = {c["name"] for c in classes}
    must_have = {"Demon Hunter", "Idol (Stage Caster)",
                 "Pet Trainer (Bonded Multitude)",
                 "Aurae Acolyte", "Mortiscure Initiate", "Wandering Monk"}
    missing = must_have - names
    assert not missing, f"missing class templates: {missing}"

    # Equipment-mod pools — all four must surface.
    for k in ("weapon_enhancements", "weapon_limiters",
              "item_enhancements", "item_limiters"):
        rows = d.get(k)
        assert isinstance(rows, list) and len(rows) > 0, \
            f"{k} missing or empty in /api/besm/reference"
        # Every row must carry cost_modifier so the lineFor formatter
        # in Reference.jsx renders cleanly.
        for row in rows:
            assert "cost_modifier" in row, f"{k} row missing cost_modifier: {row}"
            assert "name" in row


def test_register_accepts_writer_roles():
    ts = int(time.time() * 1000)
    for role in ("worldbuilder", "storyteller"):
        email = f"v62545-{role}-{ts}@gmail.com"
        r = requests.post(
            f"{API}/auth/register",
            json={"email": email, "password": "TestPass123!",
                  "name": f"V62545 {role}", "role": role},
            timeout=10,
        )
        assert r.status_code in (200, 201), r.text
        d = r.json()
        assert d.get("role") == role


def test_register_rejects_unknown_role():
    ts = int(time.time() * 1000)
    email = f"v62545-bad-{ts}@gmail.com"
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "password": "TestPass123!",
              "name": "Bad", "role": "hacker"},
        timeout=10,
    )
    assert r.status_code in (422, 400), r.text
    body = r.json()
    assert "role" in str(body).lower()
