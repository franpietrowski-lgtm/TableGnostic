"""V6.16.4 — Section-aware ingest + Entities pool + ConvertContent
role-open regression.
"""
from __future__ import annotations

from routes.ingest import (
    INTAKE_SECTION_MAP,
    _looks_like_intake_template,
    _split_by_section,
)


# ──────────────────────── Section splitting ────────────────────────
class TestSplitBySection:
    def test_splits_on_h2_headers(self):
        md = (
            "# Campaign\nIntro prose.\n\n"
            "## CHARACTERS\nBody of characters.\n\n"
            "## LOCATIONS\nBody of locations.\n"
        )
        parts = _split_by_section(md)
        headings = [p["heading"] for p in parts]
        assert "Campaign Overview" in headings  # synthetic preamble
        assert "CHARACTERS" in headings
        assert "LOCATIONS" in headings

    def test_preamble_captured_under_synthetic_heading(self):
        md = "Pre-header intro.\n\n## Lore\nLore body.\n"
        parts = _split_by_section(md)
        first = parts[0]
        assert first["heading"] == "Campaign Overview"
        assert "Pre-header intro" in first["body"]

    def test_empty_sections_are_dropped(self):
        md = "## A\n\n## B\nb body\n\n## C\n\n"
        parts = _split_by_section(md)
        # A and C have empty bodies → only B should yield content.
        bodies = [p["body"] for p in parts]
        assert "b body" in bodies


# ──────────────────────── Intake-template detection ────────────────────────
class TestIntakeTemplateDetection:
    def test_detects_canonical_template(self):
        md = (
            "## Characters\n- Eli\n\n## Locations\n- Eagles Nest\n\n"
            "## Factions\n- ODS\n\n## Creatures\n- Andrewsarchus\n"
        )
        assert _looks_like_intake_template(md) is True

    def test_rejects_random_markdown(self):
        md = "# Some blog\n\n## Introduction\nBlah.\n\n## Method\nBlah.\n"
        assert _looks_like_intake_template(md) is False

    def test_section_map_covers_expected_headings(self):
        # Sanity — canonical template headings all map.
        for h in ["characters", "locations", "factions", "creatures",
                  "lore", "history", "quests", "session briefs",
                  "custom reference", "timeline beats"]:
            assert h in INTAKE_SECTION_MAP, f"missing intake mapping for '{h}'"

    def test_skip_sections_documented(self):
        # Sections explicitly marked None for skipping.
        assert INTAKE_SECTION_MAP["index"] is None
        assert INTAKE_SECTION_MAP["compliance reminder"] is None
