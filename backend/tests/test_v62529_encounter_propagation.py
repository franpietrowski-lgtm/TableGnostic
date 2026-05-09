"""V6.25.29 — Encounter completion → codex propagation tests.

Validates:
  • GET /campaigns/{cid}/entities returns codex nodes (NPC/character/etc.)
  • Bestiary picker source (already covered: /systems/dnd-5e/reference)
  • Encounter completion with body propagates:
      - casualties → codex node fields.deceased + death_log entry
      - kills → kill_logs collection rows
  • GET /campaigns/{cid}/kill-tally returns aggregated totals
  • Legacy completion query-string call (no body) still works
"""
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"


def _login():
    r = requests.post(f"{API}/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    r.raise_for_status()
    return r.json()["access_token"]


def _hdr(t):
    return {"Authorization": f"Bearer {t}"}


def _get_or_make_dnd_campaign(token):
    r = requests.get(f"{API}/campaigns", headers=_hdr(token))
    r.raise_for_status()
    camps = r.json()
    dnd = next((c for c in camps if c.get("system_id") == "dnd-5e"), None)
    if dnd:
        return dnd["id"]
    r = requests.post(f"{API}/campaigns", headers=_hdr(token),
                       json={"name": "V62529 dnd test",
                             "system_id": "dnd-5e",
                             "power_level": "Heroic"})
    r.raise_for_status()
    return r.json()["id"]


def test_entities_endpoint_returns_npc_nodes():
    token = _login()
    cid = _get_or_make_dnd_campaign(token)
    # Seed an NPC node so the endpoint has something to return.
    r = requests.post(f"{API}/nodes", headers=_hdr(token),
                       json={"campaign_id": cid, "type": "npc",
                             "title": "V62529 Test NPC",
                             "content": "Trial witness."})
    r.raise_for_status()
    nid = r.json()["id"]
    try:
        r = requests.get(f"{API}/campaigns/{cid}/entities", headers=_hdr(token))
        r.raise_for_status()
        d = r.json()
        assert d["total"] >= 1
        assert any(row["id"] == nid for row in d["rows"])
        # Filter by kind.
        r = requests.get(f"{API}/campaigns/{cid}/entities?kind=npc", headers=_hdr(token))
        r.raise_for_status()
        d2 = r.json()
        assert any(row["id"] == nid for row in d2["rows"])
    finally:
        requests.delete(f"{API}/nodes/{nid}", headers=_hdr(token))


def test_complete_encounter_vigilizes_npc_and_tallies_kills():
    token = _login()
    cid = _get_or_make_dnd_campaign(token)
    # Seed an NPC + a witness.
    n1 = requests.post(f"{API}/nodes", headers=_hdr(token),
                        json={"campaign_id": cid, "type": "npc",
                              "title": "V62529 Casualty",
                              "content": ""}).json()["id"]
    w1 = requests.post(f"{API}/nodes", headers=_hdr(token),
                        json={"campaign_id": cid, "type": "npc",
                              "title": "V62529 Witness",
                              "content": ""}).json()["id"]
    # Create an encounter.
    enc = requests.post(f"{API}/campaigns/{cid}/encounters-library",
                        headers=_hdr(token),
                        json={"name": "V62529 ambush",
                              "summary": "test",
                              "encounter_type": "combat",
                              "monsters": [{"name": "Goblin", "count": 4, "cr": 0.25}],
                              "status": "running"}).json()
    eid = enc["id"]
    try:
        # Resolve with body — vigilize n1, tally 4 goblins.
        r = requests.post(
            f"{API}/campaigns/{cid}/encounters-library/{eid}/complete",
            headers=_hdr(token),
            json={"completion_notes": "PCs prevailed.",
                  "casualties": [{"node_id": n1,
                                    "death_reason": "Slain by warlord.",
                                    "witnesses": [w1]}],
                  "kills": [{"monster_name": "Goblin",
                              "count": 4,
                              "cr": 0.25}]})
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["status"] == "completed"
        assert out["completion_notes"] == "PCs prevailed."
        assert len(out["propagated_casualties"]) == 1
        assert out["propagated_casualties"][0]["node_id"] == n1
        assert len(out["propagated_kills"]) == 1
        # Verify codex node was vigilized (no GET /nodes/{nid} endpoint;
        # fetch the campaign nodes list and pluck ours).
        nodes = requests.get(f"{API}/campaigns/{cid}/nodes",
                              headers=_hdr(token)).json()
        rows = nodes if isinstance(nodes, list) else nodes.get("nodes", [])
        node = next((n for n in rows if n["id"] == n1), None)
        assert node is not None, "casualty node missing from campaign listing"
        assert node["fields"]["deceased"] is True
        assert len(node["fields"]["death_log"]) == 1
        log = node["fields"]["death_log"][0]
        assert log["death_reason"] == "Slain by warlord."
        assert w1 in log["witnesses"]
        # Verify kill tally aggregation.
        tally = requests.get(f"{API}/campaigns/{cid}/kill-tally",
                              headers=_hdr(token)).json()
        assert tally["grand_total"] >= 4
        gob = next((r for r in tally["by_monster"] if r["monster_name"] == "Goblin"), None)
        assert gob is not None
        assert gob["kills"] >= 4
    finally:
        requests.delete(f"{API}/campaigns/{cid}/encounters-library/{eid}",
                         headers=_hdr(token))
        requests.delete(f"{API}/nodes/{n1}", headers=_hdr(token))
        requests.delete(f"{API}/nodes/{w1}", headers=_hdr(token))


def test_complete_encounter_legacy_query_param_still_works():
    """The simple /complete?completion_notes=... call (no body) must still
    succeed for any UI that hasn't migrated to the rich payload yet."""
    token = _login()
    cid = _get_or_make_dnd_campaign(token)
    enc = requests.post(f"{API}/campaigns/{cid}/encounters-library",
                        headers=_hdr(token),
                        json={"name": "V62529 legacy",
                              "encounter_type": "social",
                              "status": "running"}).json()
    eid = enc["id"]
    try:
        r = requests.post(
            f"{API}/campaigns/{cid}/encounters-library/{eid}/complete?completion_notes=legacy",
            headers=_hdr(token))
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["completion_notes"] == "legacy"
        assert out["status"] == "completed"
    finally:
        requests.delete(f"{API}/campaigns/{cid}/encounters-library/{eid}",
                         headers=_hdr(token))


def test_kill_tally_resolves_character_names():
    """When a kill log records killed_by_character_id, the tally
    response must look up the character name via the characters
    collection."""
    token = _login()
    cid = _get_or_make_dnd_campaign(token)
    # Make a character to attribute kills to.
    ch = requests.post(f"{API}/characters", headers=_hdr(token),
                        json={"campaign_id": cid,
                              "name": "V62529 Hunter",
                              "concept": "test", "power_level": "Heroic",
                              "total_points": 80,
                              "stats": {"body": 4, "mind": 4, "soul": 4},
                              "attributes": [], "defects": [], "skills": [],
                              "size": "Medium"}).json()
    ch_id = ch["id"]
    enc = requests.post(f"{API}/campaigns/{cid}/encounters-library",
                        headers=_hdr(token),
                        json={"name": "V62529 named kill",
                              "encounter_type": "combat",
                              "monsters": [{"name": "Skeleton", "count": 2}],
                              "status": "running"}).json()
    eid = enc["id"]
    try:
        requests.post(
            f"{API}/campaigns/{cid}/encounters-library/{eid}/complete",
            headers=_hdr(token),
            json={"completion_notes": "",
                  "kills": [{"monster_name": "Skeleton", "count": 2,
                              "killed_by_character_id": ch_id}]}).raise_for_status()
        tally = requests.get(f"{API}/campaigns/{cid}/kill-tally",
                              headers=_hdr(token)).json()
        bc = next((r for r in tally["by_character"]
                    if r["character_id"] == ch_id), None)
        assert bc is not None
        assert bc["character_name"] == "V62529 Hunter"
        assert bc["kills"] >= 2
    finally:
        requests.delete(f"{API}/campaigns/{cid}/encounters-library/{eid}",
                         headers=_hdr(token))
        requests.delete(f"{API}/characters/{ch_id}", headers=_hdr(token))


def test_entities_includes_deceased_filter():
    """include_deceased=false must filter out vigilized entities."""
    token = _login()
    cid = _get_or_make_dnd_campaign(token)
    # Create a ghost NPC and mark it deceased.
    n = requests.post(f"{API}/nodes", headers=_hdr(token),
                       json={"campaign_id": cid, "type": "npc",
                             "title": "V62529 Ghost",
                             "content": "",
                             "fields": {"deceased": True,
                                          "death_log": [{"reason": "ago"}]}}).json()
    nid = n["id"]
    try:
        r = requests.get(f"{API}/campaigns/{cid}/entities?include_deceased=false",
                          headers=_hdr(token))
        r.raise_for_status()
        rows = r.json()["rows"]
        assert not any(row["id"] == nid for row in rows)
        # Without the filter, the ghost shows up.
        r2 = requests.get(f"{API}/campaigns/{cid}/entities",
                           headers=_hdr(token))
        rows2 = r2.json()["rows"]
        assert any(row["id"] == nid for row in rows2)
    finally:
        requests.delete(f"{API}/nodes/{nid}", headers=_hdr(token))
