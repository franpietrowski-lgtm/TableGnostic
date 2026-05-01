"""V6.15 — Multi-system encounter auto-balancer parity tests.

Validates that D&D 5E, Cypher, BESM 4E, and Anime 5E all surface the same
tier of enrichment in their suggestion lists — environmental levers, role-mix
nudges, party-spread warnings, and concrete "tune to target" deltas — not
just the baseline rating-branch advice.

These tests exercise the pure engine module (no network, no DB).
"""
from __future__ import annotations

from core.cr_engine import (
    analyse,
    analyse_besm,
    analyse_cypher,
    analyse_dnd,
)


# ──────────────────────── Env lever parity ────────────────────────
class TestEnvironmentalLeversParity:
    """Indoor / weather / light / hazard flags should enrich every system."""

    def _env(self):
        return {
            "indoor": True,
            "weather": "dense fog",
            "light": "dim gloom",
            "hazard": "collapsing scaffolding",
        }

    def test_dnd_env_levers(self):
        out = analyse_dnd(
            party=[{"level": 5}, {"level": 5}],
            npcs=[{"name": "boss", "cr": "5", "count": 1, "role": "villain"}],
            env=self._env(),
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "indoor" in labels
        assert "fog" in labels
        assert "dim" in labels or "gloom" in labels
        assert "scaffolding" in labels or "hazard" in labels

    def test_cypher_env_levers(self):
        out = analyse_cypher(
            party=[{"cypher_state": {"tier": 2}}],
            npcs=[{"name": "foe", "level": 4, "count": 1, "role": "villain"}],
            env=self._env(),
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "indoor" in labels
        assert "fog" in labels
        assert "dim" in labels or "gloom" in labels
        assert "scaffolding" in labels or "hazard" in labels

    def test_besm_env_levers(self):
        out = analyse_besm(
            party=[{"total_points": 150}, {"total_points": 150}],
            npcs=[{"name": "foe", "total_points": 180, "count": 1, "role": "villain"}],
            env=self._env(),
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "indoor" in labels
        assert "fog" in labels
        assert "dim" in labels or "gloom" in labels
        assert "scaffolding" in labels or "hazard" in labels


# ──────────────────────── Role-mix parity ────────────────────────
class TestRoleMixParity:
    """Minion-only / leader-only / solo-boss compositions should nudge the GM."""

    def test_dnd_all_minions_no_leader_nudges(self):
        # CR-2 ×6 = 2700 raw ×2.5 group-mult = 6750 adj. XP vs party medium
        # 1800 / hard 2700 / deadly 4050 for 3× L5 → Deadly. Minion role-mix
        # nudge fires for any non-Pushover rating.
        out = analyse_dnd(
            party=[{"level": 5}, {"level": 5}, {"level": 5}],
            npcs=[{"name": "Bandit", "cr": "2", "count": 6, "role": "minion"}],
            env={},
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "promote" in labels or "henchman" in labels or "leader" in labels

    def test_cypher_solo_boss_action_economy(self):
        out = analyse_cypher(
            party=[{"cypher_state": {"tier": 2}}, {"cypher_state": {"tier": 2}}],
            npcs=[{"name": "BBEG", "level": 6, "count": 1, "role": "nemesis"}],
            env={},
        )
        # Effective level 6 - (2*1.5=3) = 3 → Hard. Solo boss rule fires.
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "solo" in labels or "legendary" in labels or "phase" in labels

    def test_besm_leaders_only_missing_minions(self):
        out = analyse_besm(
            party=[{"total_points": 200}, {"total_points": 200}],
            npcs=[
                {"name": "Villain A", "total_points": 180, "count": 1, "role": "villain"},
                {"name": "Villain B", "total_points": 180, "count": 1, "role": "nemesis"},
            ],
            env={},
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "minion" in labels or "rank-and-file" in labels


# ──────────────────────── Party-spread parity ────────────────────────
class TestPartySpreadParity:
    def test_dnd_party_level_spread(self):
        out = analyse_dnd(
            party=[{"level": 2}, {"level": 6}],
            npcs=[{"cr": "2", "count": 2, "role": "minion"}],
            env={},
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "spread" in labels or "lower-level" in labels or "parallel" in labels

    def test_cypher_tier_spread(self):
        out = analyse_cypher(
            party=[{"cypher_state": {"tier": 1}}, {"cypher_state": {"tier": 3}}],
            npcs=[{"level": 3, "count": 2, "role": "villain"}],
            env={},
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "tier spread" in labels or "lower-tier" in labels or "borrowed" in labels

    def test_besm_cp_spread(self):
        out = analyse_besm(
            party=[{"total_points": 100}, {"total_points": 200}],
            npcs=[{"total_points": 150, "count": 1, "role": "villain"}],
            env={},
        )
        labels = " ".join(s["label"] for s in out["suggestions"]).lower()
        assert "cp spread" in labels or "lower-cp" in labels


# ──────────────────────── Tune-to-target parity ────────────────────────
class TestTuneToTargetParity:
    """Every system should produce concrete 'add/remove X to land in rating Y' deltas."""

    def test_dnd_deadly_produces_tune_delta(self):
        out = analyse_dnd(
            party=[{"level": 3}],
            npcs=[{"cr": "10", "count": 1, "role": "nemesis"}],
            env={},
        )
        assert out["rating"] == "Deadly"
        kinds = {s.get("kind") for s in out["suggestions"]}
        assert "tune" in kinds, f"Expected 'tune' suggestion kind, got {kinds}"

    def test_dnd_pushover_produces_tune_delta(self):
        out = analyse_dnd(
            party=[{"level": 10}, {"level": 10}],
            npcs=[{"cr": "1/8", "count": 1, "role": "minion"}],
            env={},
        )
        assert out["rating"] == "Pushover"
        kinds = {s.get("kind") for s in out["suggestions"]}
        assert "tune" in kinds

    def test_cypher_punishing_produces_tune_delta(self):
        out = analyse_cypher(
            party=[{"cypher_state": {"tier": 1}}],
            npcs=[{"level": 8, "count": 2, "role": "nemesis"}],
            env={},
        )
        assert out["rating"] == "Punishing"
        kinds = {s.get("kind") for s in out["suggestions"]}
        assert "tune" in kinds

    def test_besm_punishing_produces_tune_delta(self):
        out = analyse_besm(
            party=[{"total_points": 100}],
            npcs=[{"total_points": 300, "count": 1, "role": "nemesis"}],
            env={},
        )
        assert out["rating"] == "Punishing"
        kinds = {s.get("kind") for s in out["suggestions"]}
        assert "tune" in kinds


# ──────────────────────── Backward-compat ────────────────────────
class TestBackwardCompat:
    """V5.3 tests still pass shape-wise — no regressions."""

    def test_cypher_empty_npcs_still_pushover(self):
        out = analyse_cypher(
            party=[{"cypher_state": {"tier": 2}}],
            npcs=[],
            env={},
        )
        assert out["rating"] == "Pushover"

    def test_cypher_empty_party_still_unknown(self):
        out = analyse_cypher(
            party=[],
            npcs=[{"level": 3, "count": 1}],
            env={},
        )
        assert out["rating"] == "Unknown"
        # No seat → no suggestions.
        assert out["suggestions"] == []

    def test_dnd_empty_party_still_unknown(self):
        out = analyse_dnd(
            party=[],
            npcs=[{"cr": "1", "count": 1}],
            env={},
        )
        assert out["rating"] == "Unknown"

    def test_besm_zero_party_still_unknown(self):
        # BESM's Unknown branch fires when party_total sums to 0 — which only
        # happens with an empty party (each missing-field PC defaults to 100).
        out = analyse_besm(
            party=[],
            npcs=[{"total_points": 100, "count": 1}],
            env={},
        )
        assert out["rating"] == "Unknown"

    def test_anime5e_dispatch_routes_to_dnd_when_cr_set(self):
        out = analyse(
            party=[{"level": 5, "total_points": 150}],
            npcs=[{"cr": "3", "count": 1, "role": "villain"}],
            system_id="anime-5e",
            env={},
        )
        assert out["system_id"] == "dnd-5e"

    def test_anime5e_dispatch_routes_to_besm_when_no_cr(self):
        out = analyse(
            party=[{"total_points": 150}],
            npcs=[{"total_points": 130, "count": 1, "role": "villain"}],
            system_id="anime-5e",
            env={},
        )
        assert out["system_id"] == "besm-4e"


# ──────────────────────── Suggestion count parity ────────────────────────
class TestSuggestionCountParity:
    """A seeded encounter with env + role-mix should yield comparable depth
    (~3-7 suggestions) across every system — this is the heart of parity."""

    MIN_SUGGESTIONS = 3
    MAX_REASONABLE = 9

    def _env_seed(self):
        return {"indoor": True, "weather": "fog", "light": "dim"}

    def test_dnd_parity_count(self):
        out = analyse_dnd(
            party=[{"level": 5}, {"level": 5}, {"level": 5}],
            npcs=[{"cr": "3", "count": 2, "role": "villain"},
                  {"cr": "1", "count": 3, "role": "minion"}],
            env=self._env_seed(),
        )
        n = len(out["suggestions"])
        assert self.MIN_SUGGESTIONS <= n <= self.MAX_REASONABLE, \
            f"D&D parity: expected {self.MIN_SUGGESTIONS}-{self.MAX_REASONABLE}, got {n}"

    def test_cypher_parity_count(self):
        out = analyse_cypher(
            party=[{"cypher_state": {"tier": 2}}, {"cypher_state": {"tier": 2}}],
            npcs=[{"level": 4, "count": 1, "role": "villain"},
                  {"level": 2, "count": 3, "role": "minion"}],
            env=self._env_seed(),
        )
        n = len(out["suggestions"])
        assert self.MIN_SUGGESTIONS <= n <= self.MAX_REASONABLE, \
            f"Cypher parity: expected {self.MIN_SUGGESTIONS}-{self.MAX_REASONABLE}, got {n}"

    def test_besm_parity_count(self):
        out = analyse_besm(
            party=[{"total_points": 150}, {"total_points": 150}],
            npcs=[{"total_points": 160, "count": 1, "role": "villain"},
                  {"total_points": 40,  "count": 3, "role": "minion"}],
            env=self._env_seed(),
        )
        n = len(out["suggestions"])
        assert self.MIN_SUGGESTIONS <= n <= self.MAX_REASONABLE, \
            f"BESM parity: expected {self.MIN_SUGGESTIONS}-{self.MAX_REASONABLE}, got {n}"
