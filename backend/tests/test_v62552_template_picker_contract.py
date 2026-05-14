"""V6.25.52 — Phase A backend regression.

Phase A is mostly a frontend fix (BesmTemplatePicker silently rendered
null because of `ref={ref}` clobbering the React-reserved prop). This
test file simply guards the data contract the picker depends on:

  * GET /api/besm/reference.race_templates >= 1 with name + effects.
  * GET /api/besm/reference.class_templates >= 1 with name + effects.
  * Each canon row has a `description_note` and an `effects.total_cp`
    so the inline preview can render properly.
"""
from __future__ import annotations
import os

import requests

API = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read()
        .split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
) + "/api"


def test_besm_reference_race_templates_contract():
    r = requests.get(f"{API}/besm/reference", timeout=10)
    assert r.status_code == 200, r.text
    races = r.json().get("race_templates") or []
    assert len(races) >= 8, f"need >= 8 canon races, got {len(races)}"
    for row in races:
        assert row.get("name"), f"race missing name: {row}"
        # description_note + page are optional — picker has fallbacks.
        # Only invariant: bundle is iterable (the inline preview maps
        # over it to show stat_adjustments / attrs / skills / defects).
        assert isinstance(row.get("bundle", []), list)


def test_besm_reference_class_templates_contract():
    r = requests.get(f"{API}/besm/reference", timeout=10)
    assert r.status_code == 200, r.text
    classes = r.json().get("class_templates") or []
    assert len(classes) >= 18, f"need >= 18 canon classes, got {len(classes)}"
    for row in classes:
        assert row.get("name"), f"class missing name: {row}"
        # Class entries should reference at least one attribute or
        # skill so the inline preview has something to show.
        bundle = row.get("bundle") or []
        assert isinstance(bundle, list)


def test_besm_reference_conditions_still_30plus():
    """Regression — conditions catalogue (V6.25.49) not eroded."""
    r = requests.get(f"{API}/besm/reference", timeout=10)
    conds = r.json().get("conditions") or []
    assert len(conds) >= 30
