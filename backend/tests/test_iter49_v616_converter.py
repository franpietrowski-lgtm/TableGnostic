"""V6.16 — Cross-system Content Converter regression.

These tests exercise the converter's permission model, validation,
and `_materialise_character` shape-coercion logic without hitting
Claude (which would cost $$ + take ~30s/test).

Live conversion is smoke-tested separately via the seed script
`scripts/port_eli_v616.py` which actually runs Claude.
"""
from __future__ import annotations

import pytest

from routes.conversion import (
    SUPPORTED_SYSTEMS,
    TARGET_SHAPE,
    _coerce_to_dict_list,
    _materialise_character,
    _validate_systems,
)


# ──────────────────────── Validation ────────────────────────
class TestSystemValidation:
    def test_all_four_systems_supported(self):
        for sys_id in ("besm-4e", "anime-5e", "dnd-5e", "cypher"):
            assert sys_id in SUPPORTED_SYSTEMS
            assert sys_id in TARGET_SHAPE

    def test_target_shape_hint_mentions_canonical_fields(self):
        # Each shape hint should mention key target-system primitives
        # so Claude produces the right structure.
        assert "Body/Mind/Soul" in TARGET_SHAPE["besm-4e"]
        assert "Sentence" in TARGET_SHAPE["cypher"] or "Descriptor" in TARGET_SHAPE["cypher"]
        assert "SRD 5.1" in TARGET_SHAPE["dnd-5e"] or "ability_scores" in TARGET_SHAPE["dnd-5e"]
        assert "Tri-Stat" in TARGET_SHAPE["anime-5e"] or "anime5e_state" in TARGET_SHAPE["anime-5e"]

    def test_validate_rejects_unknown_systems(self):
        with pytest.raises(Exception) as exc:
            _validate_systems("besm-4e", "pathfinder-2e")
        assert "Unsupported" in str(exc.value)
        with pytest.raises(Exception):
            _validate_systems("genesys", "cypher")

    def test_validate_accepts_all_supported_pairs(self):
        for src in SUPPORTED_SYSTEMS:
            for tgt in SUPPORTED_SYSTEMS:
                _validate_systems(src, tgt)  # should not raise


# ──────────────────────── Coercion ────────────────────────
class TestCoercion:
    def test_strings_become_dicts(self):
        out = _coerce_to_dict_list(["foraging", "alchemy"],
                                   default_keys={"cost_per_level": 0, "level": 0})
        assert len(out) == 2
        assert out[0] == {"cost_per_level": 0, "level": 0, "name": "foraging"}
        assert out[1]["name"] == "alchemy"

    def test_dicts_pass_through(self):
        src = [{"name": "Healing", "level": 3, "cost_per_level": 4}]
        out = _coerce_to_dict_list(src)
        assert out == src

    def test_mixed_input_is_normalised(self):
        out = _coerce_to_dict_list([{"name": "A", "rank": 1}, "B", None, 42])
        assert len(out) == 2  # dict + string survive; None / int dropped
        assert out[0]["name"] == "A"
        assert out[1]["name"] == "B"

    def test_none_input_returns_empty_list(self):
        assert _coerce_to_dict_list(None) == []
        assert _coerce_to_dict_list([]) == []


# ──────────────────────── Materialiser ────────────────────────
@pytest.mark.asyncio
class TestMaterialiseCharacter:
    """The materialiser is the hot path — it has to gracefully handle
    every shape Claude might return."""

    async def _run(self, target_payload, target_system, source_ch=None):
        source_ch = source_ch or {
            "id": "src-1", "name": "Eli", "concept": "Apothecary apprentice",
            "system_id": "besm-4e", "total_points": 80,
            "stats": {"body": 4, "mind": 7, "soul": 6},
            "folio": {"physical_description": "small, herb-stained"},
        }
        target_camp = {"id": "tgt-1", "system_id": target_system, "house_rules": ""}
        return await _materialise_character(
            target_payload, target_system, target_camp, source_ch,
            owner_id="player-1", owner_name="Aurora",
            keep_folio=True, name_override=None,
        )

    async def test_cypher_state_extracted_from_top_level(self):
        # Claude often returns Cypher fields directly in target_payload.
        payload = {
            "name": "Eli",
            "tier": 2, "descriptor": "Learned", "type": "Explorer",
            "focus": "Concocts Powerful Elixirs",
            "pools": {"might": 8, "speed": 11, "intellect": 17},
            "edge": {"might": 0, "speed": 1, "intellect": 1},
            "abilities": ["Practiced With Light Weapons"],
        }
        ch = await self._run(payload, "cypher")
        st = ch["folio"]["cypher_state"]
        assert st["tier"] == 2
        assert st["descriptor"] == "Learned"
        assert st["type"] == "Explorer"
        assert st["focus"] == "Concocts Powerful Elixirs"
        assert st["pools"]["intellect"] == 17

    async def test_cypher_state_extracted_from_wrapped(self):
        # Some prompts also produce a wrapped object.
        payload = {"name": "Eli",
                   "cypher_state": {"tier": 3, "type": "Adept", "focus": "Bears a Halo of Fire"}}
        ch = await self._run(payload, "cypher")
        assert ch["folio"]["cypher_state"]["tier"] == 3
        assert ch["folio"]["cypher_state"]["type"] == "Adept"

    async def test_dnd_state_extracted_from_top_level(self):
        payload = {
            "name": "Eli", "class": "Artificer", "level": 5,
            "race": "Halfling", "background": "Guild Artisan",
            "ability_scores": {"strength": 10, "intelligence": 16, "wisdom": 14},
            "spells": [{"name": "Cure Wounds", "level": 1}],
            "features": [{"name": "Alchemical Savant"}],
        }
        ch = await self._run(payload, "dnd-5e")
        st = ch["folio"]["dnd_state"]
        assert st["class"] == "Artificer"
        assert st["level"] == 5
        assert st["ability_scores"]["intelligence"] == 16
        assert len(st["spells"]) == 1

    async def test_anime5e_keeps_tristat_shape(self):
        payload = {
            "name": "Eli", "total_points": 80,
            "stats": {"body": 4, "mind": 7, "soul": 6},
            "attributes": [{"name": "Healing", "level": 3, "cost_per_level": 4}],
            "skills": [{"name": "Alchemy", "level": 3, "cost_per_level": 1}],
            "defects": [{"name": "Phobia", "rank": 2, "points_per_rank": 1}],
            "points": {"total": 80, "spent": 80},
        }
        ch = await self._run(payload, "anime-5e")
        assert ch["total_points"] == 80
        assert ch["stats"]["mind"] == 7
        assert len(ch["attributes"]) == 1
        assert ch["folio"]["anime5e_state"]["points"]["total"] == 80

    async def test_string_skills_dont_crash_cost_engine(self):
        # Regression — Claude sometimes returns skills as ["forage", "brew"];
        # the BESM cost engine used to AttributeError on them.
        payload = {
            "name": "Eli",
            "skills": ["forage", "brew"],   # plain strings
            "attributes": [{"name": "Healing", "level": 3, "cost_per_level": 4}],
            "tier": 2, "type": "Adept",
        }
        ch = await self._run(payload, "cypher")
        # Must not raise. spent.total_spent comes back as 0 for non-Tri-Stat.
        assert ch["spent"]["total_spent"] == 0
        # Skills should be coerced into dicts for downstream consumers.
        assert all(isinstance(s, dict) for s in ch["skills"])
        assert ch["skills"][0]["name"] == "forage"

    async def test_folio_journal_is_carried_when_keep_folio(self):
        source = {
            "id": "src-2", "name": "Eli", "system_id": "besm-4e",
            "stats": {"body": 4, "mind": 7, "soul": 6},
            "total_points": 80,
            "folio": {
                "physical_description": "small, herb-stained",
                "personality_traits": "shy, reverent",
                "journal": [{"date": "2026-01-01", "entry": "Met the Stranger"}],
            },
        }
        ch = await self._run({"name": "Eli"}, "dnd-5e", source_ch=source)
        # Source folio carries over verbatim.
        assert ch["folio"]["physical_description"] == "small, herb-stained"
        assert ch["folio"]["personality_traits"] == "shy, reverent"
        assert ch["folio"]["journal"][0]["entry"] == "Met the Stranger"
        # Plus the dnd_state slot is added (empty here, but present).
        assert "dnd_state" in ch["folio"]

    async def test_converted_from_breadcrumb(self):
        ch = await self._run({"name": "Eli"}, "cypher")
        assert ch["converted_from"]["source_character_id"] == "src-1"
        assert ch["converted_from"]["source_system"] == "besm-4e"
        assert "converted_at" in ch["converted_from"]

    async def test_owner_passthrough(self):
        ch = await self._run({"name": "Eli"}, "anime-5e")
        assert ch["owner_id"] == "player-1"
        assert ch["owner_name"] == "Aurora"
