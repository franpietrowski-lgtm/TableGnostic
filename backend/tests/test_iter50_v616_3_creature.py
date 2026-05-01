"""V6.16.3 — Cross-system Creature Converter regression.

Tests the new /api/convert/creature endpoint's materialiser. Avoids
hitting Claude — exercises only the deterministic post-LLM shape
mapping for stat blocks across all 4 supported systems.
"""
from __future__ import annotations

import pytest

from core.conversion_engine import (
    materialise_creature,
)


@pytest.mark.asyncio
class TestMaterialiseCreature:
    """Each port produces a `nodes`-shaped doc ready for db.nodes insert."""

    async def _run(self, target_payload, target_system, source_node=None):
        source_node = source_node or {
            "id": "node-andrewsarchus",
            "campaign_id": "src-camp",
            "title": "Andrewsarchus",
            "fields": {
                "kind": "creature",
                "system_id": "besm-4e",
                "summary": "Apex predator of the deep north taiga.",
                "stats": {"body": 9, "mind": 4, "soul": 6},
                "total_points": 240,
            },
            "motive": "creature",
            "type": "creature",
        }
        target_camp = {"id": "tgt-camp", "system_id": target_system}
        return await materialise_creature(
            target_payload, target_system, target_camp, source_node, None,
        )

    # ── D&D 5E ──
    async def test_dnd_creature_stat_block(self):
        payload = {
            "name": "Andrewsarchus",
            "summary": "Apex predator. Silent stalker.",
            "challenge_rating": "11",
            "hit_points": 161,
            "armor_class": 16,
            "ability_scores": {"Strength": 22, "Dexterity": 14},
            "actions": [
                {"name": "Crushing Bite", "description": "Reach 5ft, +10 to hit, 28 (4d10+6) piercing."},
            ],
        }
        node = await self._run(payload, "dnd-5e")
        assert node["motive"] == "creature"
        assert node["title"] == "Andrewsarchus"
        f = node["fields"]
        assert f["kind"] == "creature"
        assert f["system_id"] == "dnd-5e"
        assert f["cr"] == "11"
        assert f["hp"] == 161
        assert f["ac"] == 16
        # Per-system block carries the stats for the Director's Console.
        assert f["dnd_state"]["challenge_rating"] == "11"
        assert f["dnd_state"]["actions"][0]["name"] == "Crushing Bite"

    async def test_dnd_creature_cr_fallback(self):
        # Missing CR → defaults to "1" (sane low-floor for the encounter math).
        node = await self._run({"name": "Lesser Beast"}, "dnd-5e")
        assert node["fields"]["cr"] == "1"

    # ── Cypher ──
    async def test_cypher_creature_stat_block(self):
        payload = {
            "name": "Andrewsarchus",
            "level": 7,
            "health": 30,
            "modifications": ["stalking eases by 2 steps"],
            "special_abilities": [
                {"name": "Crushing Bite", "description": "Inflicts 7 damage; ignores 3 armor."},
            ],
        }
        node = await self._run(payload, "cypher")
        f = node["fields"]
        assert f["system_id"] == "cypher"
        assert f["level"] == 7
        # target_difficulty defaults to level × 3 when not provided.
        assert f["target_difficulty"] == 21
        assert f["cypher_state"]["level"] == 7
        assert f["cypher_state"]["special_abilities"][0]["name"] == "Crushing Bite"

    async def test_cypher_creature_health_fallback(self):
        # Missing health → defaults to level × 3 (Cypher monster rule of thumb).
        node = await self._run({"level": 4}, "cypher")
        assert node["fields"]["health"] == 12

    # ── Anime 5E ──
    async def test_anime5e_creature_stat_block(self):
        # Anime 5E uses 5E stat block + anime_traits for genre flair.
        payload = {
            "name": "Andrewsarchus",
            "challenge_rating": "11",
            "hit_points": 161,
            "armor_class": 16,
            "anime_traits": [
                {"name": "Tragic Pact", "description": "Once per encounter, transform into a humanoid form to negotiate."},
            ],
            "actions": [{"name": "Crushing Bite"}],
        }
        node = await self._run(payload, "anime-5e")
        f = node["fields"]
        assert f["system_id"] == "anime-5e"
        assert f["cr"] == "11"
        assert len(f["anime_traits"]) == 1
        assert f["anime_traits"][0]["name"] == "Tragic Pact"
        # 5E chassis still lives in dnd_state.
        assert f["dnd_state"]["hit_points"] == 161

    # ── BESM ──
    async def test_besm_creature_stat_block(self):
        payload = {
            "name": "Andrewsarchus",
            "stats": {"body": 9, "mind": 4, "soul": 6},
            "total_points": 240,
            "attributes": [
                {"name": "Special Movement (Sneaking)", "level": 4, "cost_per_level": 1},
                {"name": "Massive Damage", "level": 3, "cost_per_level": 4},
            ],
            "defects": [
                {"name": "Recurring Nightmares (PCs')", "rank": 1, "points_per_rank": 0},
            ],
        }
        node = await self._run(payload, "besm-4e")
        f = node["fields"]
        assert f["system_id"] == "besm-4e"
        assert f["total_points"] == 240
        assert f["stats"]["body"] == 9
        assert len(f["attributes"]) == 2
        # Tri-Stat normaliser kicked in.
        assert f["attributes"][0]["cost_per_level"] == 1

    # ── Common shape contract ──
    async def test_node_shape_includes_breadcrumb(self):
        node = await self._run({"name": "Test"}, "dnd-5e")
        assert node["fields"]["converted_from_node"] == "node-andrewsarchus"
        assert node["fields"]["source_system"] == "besm-4e"
        # ID, campaign_id, motive all set.
        assert node["motive"] == "creature"
        assert node["campaign_id"] == "tgt-camp"
        assert "id" in node
        assert "created_at" in node


# ──────────────────────── Endpoint shape ────────────────────────
class TestEndpointSchema:
    def test_convert_creature_in_schema(self):
        from routes.conversion import ConvertCreatureIn
        body = ConvertCreatureIn(
            source_node_id="abc123",
            target_campaign_id="def456",
            name_override="Andrewsarchus (Cypher)",
        )
        assert body.source_node_id == "abc123"
        assert body.target_campaign_id == "def456"
        assert body.name_override == "Andrewsarchus (Cypher)"

    def test_convert_creature_in_optional_name(self):
        from routes.conversion import ConvertCreatureIn
        body = ConvertCreatureIn(
            source_node_id="abc",
            target_campaign_id="def",
        )
        assert body.name_override is None
