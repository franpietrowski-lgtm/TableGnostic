"""V6.25.14 — World Tree lattice schema + bridge-sow endpoint.

The lattice UI (`WorldTreeLattice.jsx`) consumes the new schema shape
+ bridge_prompts map; the bridge-sow endpoint creates twin codex nodes
on each side of a cross-pillar bridge with a relationship-tagged edge.
"""
from __future__ import annotations
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _spin_camp(gm, name="V62514 Lattice Demo", system="anime-5e"):
    cp = requests.post(f"{BASE_URL}/api/campaigns", headers=H(gm),
                        json={"name": name, "system_id": system})
    assert cp.status_code == 200, cp.text
    return cp.json()["id"]


def test_creation_tree_returns_v62514_schema_with_lenses_and_prompts():
    gm = _gm_token()
    cid = _spin_camp(gm)
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/creation-tree",
                          headers=H(gm))
        assert r.status_code == 200, r.text
        body = r.json()
        sch = body["schema"]
        # Three pillars unchanged.
        assert set(sch["pillars"].keys()) == {"Population", "Geography", "History"}
        # New: history_lenses bottom-strip exposed.
        assert sch["history_lenses"] == [
            "Political", "Cultural", "Social", "Economic", "Diplomatic",
        ]
        # Cross-pillar links contains the canonical infographic bridges.
        bridges = {(s, t) for s, t, *_ in sch["cross_pillar_links"]}
        for required in [
            ("Population.Laws", "Geography.Countries"),
            ("Population.Beliefs", "History.Truth"),
            ("Population.Beliefs", "History.Lies"),
            ("Population.Wars", "Geography.Continents"),
            ("Population.Conflicts", "Geography.Man-made Borders"),
            ("Population.Factions", "Geography.Locations"),
            ("Population.Races", "Geography.Biomes"),
            ("Geography.Magic", "Geography.Natural Laws"),
            ("History.Truth", "History.Lies"),
            ("History.Written", "History.Oral"),
        ]:
            assert required in bridges, f"missing canonical bridge {required}"

        # New: bridge_prompts surfaced as a top-level keyed map.
        prompts = body["bridge_prompts"]
        assert isinstance(prompts, dict)
        assert "Population.Laws|Geography.Countries" in prompts
        assert "moral fibre" in prompts["Population.Laws|Geography.Countries"]

        # New branches added to Population (Wars / Conflicts surface
        # both in branches and bridges now).
        assert "Wars" in sch["pillars"]["Population"]["branches"]
        assert "Conflicts" in sch["pillars"]["Population"]["branches"]
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_bridge_sow_creates_twin_nodes_and_edge():
    """End-to-end: GM clicks a bridge, types both sides, hits Sow.
    Backend creates two codex nodes (one per section) with the right
    creation_tree.section + a `via_bridge` provenance flag, plus a
    codex_edges row connecting them with `relationship_type` set."""
    gm = _gm_token()
    cid = _spin_camp(gm)
    try:
        body = {
            "src_section": "Population.Laws",
            "tgt_section": "Geography.Countries",
            "relationship": "governs",
            "src_name": "V62514 Edict of Cinders",
            "src_summary": "Crime: arson. Punishment: exile.",
            "tgt_name": "V62514 Republic of Ash",
            "tgt_summary": "Built on a burned forest, governed by the Edict.",
        }
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/world-tree/bridge-sow",
            headers=H(gm), json=body)
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["src_node"]["creation_tree"]["section"] == "Population.Laws"
        assert out["src_node"]["creation_tree"]["via_bridge"] == "Geography.Countries"
        assert out["tgt_node"]["creation_tree"]["section"] == "Geography.Countries"
        assert out["edge"]["relationship_type"] == "governs"
        assert out["edge"]["source_id"] == out["src_node"]["id"]
        assert out["edge"]["target_id"] == out["tgt_node"]["id"]

        # Both nodes appear under their right pillar.branch in the tree.
        tr = requests.get(f"{BASE_URL}/api/campaigns/{cid}/creation-tree",
                           headers=H(gm)).json()
        pop_laws = tr["populated"].get("Population.Laws") or []
        geo_countries = tr["populated"].get("Geography.Countries") or []
        assert any(n["id"] == out["src_node"]["id"] for n in pop_laws)
        assert any(n["id"] == out["tgt_node"]["id"] for n in geo_countries)

        # Codex links endpoint shows the new edge.
        edges = requests.get(f"{BASE_URL}/api/campaigns/{cid}/codex-links",
                              headers=H(gm)).json()
        assert any(e["id"] == out["edge"]["id"] for e in edges["edges"])
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_bridge_sow_rejects_unknown_section():
    """Defensive: invalid Pillar.Branch returns 422 with helpful detail."""
    gm = _gm_token()
    cid = _spin_camp(gm)
    try:
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/world-tree/bridge-sow",
            headers=H(gm), json={
                "src_section": "Population.NotARealBranch",
                "tgt_section": "Geography.Countries",
                "relationship": "governs",
                "src_name": "X", "tgt_name": "Y",
            })
        assert r.status_code == 422
        assert "Unknown section" in r.json().get("detail", "")
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))


def test_bridge_sow_player_blocked():
    """Players are not GMs — bridge-sow is GM-only."""
    gm = _gm_token()
    pl = requests.post(f"{BASE_URL}/api/auth/login",
                        json={"email": "albanaszak@ymail.com",
                              "password": "AuroraTest123!"})
    if pl.status_code != 200:
        return  # Aurora not seeded; skip silently.
    aurora = pl.json()["access_token"]
    cid = _spin_camp(gm)
    try:
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/world-tree/bridge-sow",
            headers=H(aurora), json={
                "src_section": "Population.Laws",
                "tgt_section": "Geography.Countries",
                "relationship": "governs",
                "src_name": "X", "tgt_name": "Y",
            })
        assert r.status_code == 403
    finally:
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=H(gm))
