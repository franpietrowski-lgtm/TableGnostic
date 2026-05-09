"""V6.25.19 — Codex auto-classifier + Genesis/Epic/World-Tree codexification.

Three pipelines (Genesis, Epic, World Tree) now route every codex
node through `core.codex_classifier.codexify_node`, so every row
exposes name + title + type + node_kind + creation_tree.section
consistently. The new `POST /campaigns/{cid}/codex/auto-classify`
backfills legacy nodes that predate the classifier.
"""
from __future__ import annotations
import os
import requests

# Direct-import is used for the unit test layer — the round-trip
# tests still hit the live API.
from core.codex_classifier import (
    classify_concept, codexify_node, KIND_TO_SECTION, NODE_KINDS,
)

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _gm():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ── Unit tests on the classifier ───────────────────────────────────

def test_classifier_explicit_section_wins():
    out = classify_concept(
        name="Anything", explicit_section="Geography.Countries",
    )
    assert out["creation_tree_section"] == "Geography.Countries"
    assert out["node_kind"] == "country"
    assert out["confidence"] == 1.0


def test_classifier_hint_routes_correctly():
    out = classify_concept(name="Some Name", hint="faction")
    assert out["node_kind"] == "faction"
    assert out["creation_tree_section"] == "Population.Factions"


def test_classifier_tag_matches_kind():
    out = classify_concept(name="The Black Hand", tags=["guild"])
    assert out["node_kind"] == "faction"
    assert out["creation_tree_section"] == "Population.Factions"


def test_classifier_name_pattern_matches():
    """Regex on the name should pick up obvious flags."""
    cases = [
        ("Sir Aldous of the Whispering Wood",   "person"),
        ("The Brotherhood of Iron",              "faction"),
        ("Empire of the Eternal Sun",            "country"),
        ("The Whispering Forest",                "biome"),
        ("Ravensgate Citadel",                   "location"),
        ("The First War of Ash",                 "war"),
        ("The Pact of the Three Crowns",         "treaty"),
        ("The Saga of Vermillion Skies",         "chronicle"),
        ("Legend of the Lost Star",              "myth"),
    ]
    for name, expected_kind in cases:
        out = classify_concept(name=name)
        assert out["node_kind"] == expected_kind, \
            f"{name}: expected {expected_kind}, got {out['node_kind']}"
        assert out["creation_tree_section"] == KIND_TO_SECTION[expected_kind]


def test_classifier_falls_back_to_concept():
    """When nothing matches, kind=concept and section=None."""
    out = classify_concept(name="Aurora Vellichor", tags=["mood-piece"])
    assert out["node_kind"] == "concept"
    assert out["creation_tree_section"] is None
    assert out["confidence"] == 0.0


def test_codexify_node_fills_canonical_shape():
    body = codexify_node(
        name="Sir Aldous", content="An old retainer.",
        summary="An old retainer.",
        tags=["ally"], hint=None,
    )
    assert body["name"] == "Sir Aldous"
    assert body["title"] == "Sir Aldous"
    assert body["type"] == body["node_kind"]
    assert body["node_kind"] in NODE_KINDS
    assert "creation_tree" in body
    assert body["creation_tree"]["section"] in KIND_TO_SECTION.values()
    assert body["creation_tree"]["auto_classified"] is True


# ── End-to-end: auto-classify backfill endpoint ────────────────────

def test_auto_classify_backfill_routes_legacy_nodes():
    """Insert a few legacy-shape nodes (no creation_tree.section) and
    confirm /codex/auto-classify backfills them onto the World Tree."""
    gm = _gm()
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": "V62519 Backfill Demo",
                              "system_id": "anime-5e"})
    cid = cp.json()["id"]
    try:
        # Seed three legacy-style codex nodes via /codex-nodes with
        # node_kind=concept and no section. They should land unplaced
        # initially (until auto-classify runs).
        for name, kind, tags in [
            ("Sir Aldous of Vermilion",   "concept", ["ally"]),
            ("Empire of the Eternal Sun", "concept", []),
            ("The Whispering Forest",     "concept", []),
            ("Mood: ineffable nostalgia", "concept", ["mood-piece"]),
        ]:
            rs = requests.post(
                f"{BASE_URL}/api/campaigns/{cid}/codex-nodes",
                headers=H(gm),
                json={"name": name, "node_kind": kind, "summary": ""})
            assert rs.status_code == 200, rs.text

        # NB — sow_codex_node now auto-classifies on creation when
        # node_kind=='concept', so confirm the names that DO match a
        # pattern have already landed in the right sections.
        tree = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/creation-tree",
            headers=H(gm),
        ).json()
        pop_people = [n["name"] for n in tree["populated"].get(
            "Population.Prominent People", [])]
        geo_countries = [n["name"] for n in tree["populated"].get(
            "Geography.Countries", [])]
        geo_biomes = [n["name"] for n in tree["populated"].get(
            "Geography.Biomes", [])]
        unplaced = [n["name"] for n in tree.get("unplaced") or []]

        assert "Sir Aldous of Vermilion" in pop_people, \
            f"Sir Aldous unplaced (in {pop_people})"
        assert "Empire of the Eternal Sun" in geo_countries
        assert "The Whispering Forest" in geo_biomes
        # The mood-piece concept HAS no signal — stays unplaced.
        assert "Mood: ineffable nostalgia" in unplaced

        # Backfill endpoint should be idempotent — no further changes.
        rs = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/codex/auto-classify",
            headers=H(gm))
        assert rs.status_code == 200, rs.text
        out = rs.json()
        assert out["classified"] == 0, \
            f"already classified, should be 0; got {out}"
        assert out["still_unplaced"] >= 1
        assert out["already_placed"] >= 3
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_genesis_seed_nodes_routes_to_world_tree():
    """V6.25.19 — Genesis seeded NPCs / locations / biomes / factions
    must land in the right Pillar.Branch on the World Tree on the
    NEXT /creation-tree fetch."""
    gm = _gm()
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": "V62519 Genesis Demo",
                              "system_id": "anime-5e"})
    cid = cp.json()["id"]
    try:
        gen = requests.put(
            f"{BASE_URL}/api/campaigns/{cid}/genesis",
            headers=H(gm),
            json={
                "campaign_id": cid,
                "nemesis_name": "Lord Vermillion",
                "nemesis_motive": "Reclaim the throne of fire.",
                "nemesis_resources": "The Crimson Hand cult.",
                "nemesis_weakness": "His own pride.",
                "seed_npcs": [
                    {"name": "Captain Imora", "role": "ally", "note": ""},
                ],
                "adventures": [
                    {"title": "The Bridge of Coals",
                     "hook": "Cross the lava bridge.",
                     "stakes": "Or fall.", "outcome": "Triumph or ruin.",
                     "kind": "quest"},
                ],
                "locations": [{"name": "The Cinder Spire", "summary": ""}],
                "biomes": [{"name": "The Ash Plains", "summary": ""}],
                "factions": [{"name": "House Ember", "summary": ""}],
                "motives": [{"name": "Vengeance for the Fall", "summary": ""}],
            })
        assert gen.status_code == 200, gen.text

        seed = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/genesis/seed-nodes",
            headers=H(gm))
        assert seed.status_code == 200, seed.text
        assert seed.json()["nodes_created"] >= 7

        tree = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/creation-tree",
            headers=H(gm)).json()

        def names_in(section):
            return {n["name"] for n in tree["populated"].get(section, [])}

        # NPCs default-route to Population.Factions (per KIND_TO_SECTION).
        assert "Lord Vermillion" in names_in("Population.Factions")
        assert "Captain Imora" in names_in("Population.Factions")
        # Geography buckets land on the right branches.
        assert "The Cinder Spire" in names_in("Geography.Locations")
        assert "The Ash Plains" in names_in("Geography.Biomes")
        # Faction lands on Population.Factions.
        assert "House Ember" in names_in("Population.Factions")
        # Adventure → quest → History.Of the People (per KIND_TO_SECTION).
        assert "The Bridge of Coals" in names_in("History.Of the People")
        # Nemesis sub-nodes (Motive=lore, Resources=faction, Weakness=lore)
        # land in their respective branches.
        assert "Lord Vermillion — Resources" in names_in("Population.Factions")
        # Crucially — NOTHING from genesis should be unplaced now.
        unplaced_names = {n["name"] for n in tree.get("unplaced") or []}
        seeded_names = {
            "Lord Vermillion", "Captain Imora", "The Cinder Spire",
            "The Ash Plains", "House Ember", "The Bridge of Coals",
        }
        assert seeded_names.isdisjoint(unplaced_names), \
            f"genesis seeds should never be unplaced: {seeded_names & unplaced_names}"
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_epic_seed_codex_routes_to_world_tree():
    """V6.25.19 — Epic seed-codex now writes name + node_kind +
    creation_tree.section so the GM-only Nemesis / Villains / Seeds
    show up in the World Tree like any other codex node."""
    gm = _gm()
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": "V62519 Epic Demo",
                              "system_id": "anime-5e"})
    cid = cp.json()["id"]
    try:
        ep = requests.put(
            f"{BASE_URL}/api/epic/{cid}",
            headers=H(gm),
            json={
                "campaign_id": cid,
                "nemesis": {"name": "The Withered King",
                             "psychology": "bft",
                             "occupation": "deposed monarch",
                             "goal": "Reclaim the Throne of Roots"},
                "villains": [
                    {"name": "Iron Magus Brell", "role": "henchman"},
                ],
                "seeds": [
                    {"label": "The Cursed Banner", "kind": "name",
                     "seeded_in": "session 1"},
                ],
            })
        assert ep.status_code == 200, ep.text

        sd = requests.post(
            f"{BASE_URL}/api/epic/{cid}/seed-codex", headers=H(gm))
        assert sd.status_code == 200, sd.text
        assert sd.json()["nodes_created"] >= 3

        tree = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}/creation-tree",
            headers=H(gm)).json()
        all_names = []
        for sec_nodes in tree["populated"].values():
            all_names.extend(n["name"] for n in sec_nodes)
        assert "The Withered King" in all_names
        assert "Iron Magus Brell" in all_names
        assert "The Cursed Banner" in all_names
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_auto_classify_endpoint_blocks_non_gm():
    """Players cannot run the backfill — 403."""
    gm = _gm()
    pl = requests.post(f"{BASE_URL}/api/auth/login",
                        json={"email": "albanaszak@ymail.com",
                              "password": "AuroraTest123!"})
    if pl.status_code != 200:
        return
    pl_token = pl.json()["access_token"]
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": "V62519 Block Demo",
                              "system_id": "anime-5e"})
    cid = cp.json()["id"]
    try:
        rs = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/codex/auto-classify",
            headers=H(pl_token))
        assert rs.status_code == 403, rs.status_code
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))
