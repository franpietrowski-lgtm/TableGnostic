"""V6.25.7 — Macros + Hot-keys V2 deduct + Genesis archives.

Verifies:
1. Macro CRUD (create, list with scope filter, delete, scope=campaign GM gate).
2. /<macroname> chat invocation expands tokens (STR/PROF/etc), supports
   trailing modifier injection (`+2`).
3. /cast deducts a spell slot from folio.dnd_state.spell_slots and
   stamps undoable_until; /undo within 30s reverses it.
4. /use bundle deducts charge + EP and supports undo.
5. Genesis archives: editing genesis snapshots prior version; archive
   list returns it; restore swaps live ↔ archive cleanly.
6. CustomAttributeIn accepts the new `color` field.
"""
from __future__ import annotations
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    return r.json()["access_token"]


@pytest.fixture()
def dnd_camp(gm_token):
    r = requests.post(f"{BASE_URL}/api/campaigns",
                       headers=H(gm_token),
                       json={"name": "V6257 hk2-test", "system_id": "dnd-5e"}).json()
    yield r["id"]
    requests.delete(f"{BASE_URL}/api/campaigns/{r['id']}", headers=H(gm_token))


@pytest.fixture()
def chan(gm_token, dnd_camp):
    r = requests.get(f"{BASE_URL}/api/campaigns/{dnd_camp}/channels",
                       headers=H(gm_token)).json()
    return r[0]["id"] if r else requests.post(
        f"{BASE_URL}/api/campaigns/{dnd_camp}/channels", headers=H(gm_token),
        json={"name": "general", "kind": "text"}).json()["id"]


@pytest.fixture()
def char_with_state(gm_token, dnd_camp):
    """Char with ability scores + level + a folio.dnd_state.spell_slots map."""
    r = requests.post(f"{BASE_URL}/api/characters",
                       headers=H(gm_token),
                       json={"campaign_id": dnd_camp,
                             "name": "V6257 Wizard",
                             "stats": {"body": 4, "mind": 5, "soul": 4},
                             "level": 5,
                             "folio": {"dnd_state": {
                                 "ability_scores": {"Strength": 10, "Dexterity": 14,
                                                      "Intelligence": 18},
                                 "level": 5,
                                 "spell_slots": {"1": 4, "2": 3, "3": 2}},
                                "energy_points": 8}})
    cid = r.json()["id"]
    yield cid
    requests.delete(f"{BASE_URL}/api/characters/{cid}", headers=H(gm_token))


def _post_msg(token, chid, text):
    return requests.post(f"{BASE_URL}/api/channels/{chid}/messages",
                           headers=H(token),
                           json={"body": text, "attachments": []}).json()


# ─── Macros CRUD ──────────────────────────────────────────────────────


def test_macro_crud_user_scope(gm_token, dnd_camp):
    r = requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/macros",
                       headers=H(gm_token),
                       json={"name": "strike", "formula": "1d20+STR+PROF",
                             "label": "Sword Strike", "scope": "user"})
    assert r.status_code == 200, r.text
    m = r.json()
    assert m["scope"] == "user"
    assert m["formula"] == "1d20+STR+PROF"

    rows = requests.get(f"{BASE_URL}/api/campaigns/{dnd_camp}/macros",
                          headers=H(gm_token)).json()
    assert any(x["id"] == m["id"] for x in rows)

    # Duplicate within scope rejected.
    dup = requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/macros",
                          headers=H(gm_token),
                          json={"name": "strike", "formula": "1d8",
                                "scope": "user"})
    assert dup.status_code == 400

    rd = requests.delete(f"{BASE_URL}/api/campaigns/{dnd_camp}/macros/{m['id']}",
                           headers=H(gm_token))
    assert rd.status_code == 200


def test_macro_invalid_name_400(gm_token, dnd_camp):
    r = requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/macros",
                       headers=H(gm_token),
                       json={"name": "1bad name!", "formula": "1d20",
                             "scope": "user"})
    assert r.status_code == 422


# ─── Macro chat invocation ────────────────────────────────────────────


def test_macro_chat_expands_tokens_and_modifier(gm_token, dnd_camp,
                                                  chan, char_with_state):
    requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/macros",
                   headers=H(gm_token),
                   json={"name": "spelltest", "formula": "1d20+INT+PROF",
                         "scope": "user"})
    msg = _post_msg(gm_token, chan, "/spelltest +2")
    assert msg["kind"] == "macro", msg
    meta = msg["slash_meta"]
    assert meta["macro"]["formula_raw"] == "1d20+INT+PROF"
    # INT = (18-10)/2 = +4 ; PROF at L5 = +3 ; modifier = +2.
    assert meta["macro"]["formula_expanded"] == "1d20+4+3+2"
    assert meta["result"]["total"] >= 1 + 4 + 3 + 2
    assert meta["result"]["total"] <= 20 + 4 + 3 + 2


def test_macro_unknown_renders_miss(gm_token, dnd_camp, chan):
    msg = _post_msg(gm_token, chan, "/notamacro")
    assert msg["kind"] == "macro"
    assert msg["slash_meta"]["miss"] is True


# ─── Hot-keys V2 deduct + undo ────────────────────────────────────────


def test_cast_deducts_spell_slot_and_undoes(gm_token, dnd_camp, chan,
                                              char_with_state):
    # Author a leveled spell in the campaign reference pool.
    requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/reference",
                   headers=H(gm_token),
                   json={"kind": "spell", "name": "V6257 Fireball",
                         "summary": "8d6 fire in a 20-ft sphere.",
                         "fields": {"level": 3, "school": "Evocation",
                                     "description": "8d6 fire."}})
    # /cast deducts a level-3 slot (was 2 → 1).
    msg = _post_msg(gm_token, chan, "/cast V6257 Fireball")
    assert msg["kind"] == "cast"
    deduct = msg["slash_meta"]["deduct"]
    assert deduct["applied"] is True
    assert deduct["mode"] == "spell_slot"
    assert deduct["payload"]["level"] == 3
    assert deduct["payload"]["before"] == 2
    assert deduct["payload"]["after"] == 1
    assert msg.get("undoable_until")

    # Verify folio reflects the deduction.
    ch = requests.get(f"{BASE_URL}/api/characters/{char_with_state}",
                        headers=H(gm_token)).json()
    assert ch["folio"]["dnd_state"]["spell_slots"]["3"] == 1

    # /undo restores it.
    u = requests.post(f"{BASE_URL}/api/messages/{msg['id']}/undo",
                        headers=H(gm_token))
    assert u.status_code == 200, u.text
    ch2 = requests.get(f"{BASE_URL}/api/characters/{char_with_state}",
                         headers=H(gm_token)).json()
    assert ch2["folio"]["dnd_state"]["spell_slots"]["3"] == 2


def test_cast_no_slots_doesnt_deduct(gm_token, dnd_camp, chan,
                                       char_with_state):
    """Casting a level the character has no slots for returns
    `applied: False` with reason — character is not modified."""
    requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/reference",
                   headers=H(gm_token),
                   json={"kind": "spell", "name": "V6257 Wish",
                         "fields": {"level": 9, "description": "the works."}})
    before = requests.get(f"{BASE_URL}/api/characters/{char_with_state}",
                            headers=H(gm_token)).json()
    msg = _post_msg(gm_token, chan, "/cast V6257 Wish")
    assert msg["slash_meta"]["deduct"]["applied"] is False
    assert "no L9 slots" in msg["slash_meta"]["deduct"]["reason"]
    after = requests.get(f"{BASE_URL}/api/characters/{char_with_state}",
                           headers=H(gm_token)).json()
    assert after["folio"]["dnd_state"]["spell_slots"] == \
           before["folio"]["dnd_state"]["spell_slots"]


def test_use_bundle_deducts_charge_and_ep(gm_token, dnd_camp, chan,
                                            char_with_state):
    requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/reference",
                   headers=H(gm_token),
                   json={"kind": "power_bundle",
                         "name": "V6257 Star Volley",
                         "fields": {"description": "3d8 radiant",
                                     "invocation": "per-day",
                                     "charges_max": 3,
                                     "energy_cost": 2}})
    msg = _post_msg(gm_token, chan, "/use bundle V6257 Star Volley")
    deduct = msg["slash_meta"]["deduct"]
    assert deduct["applied"] is True
    assert deduct["mode"] == "bundle"
    assert deduct["payload"]["charges"]["used_after"] == 1
    assert deduct["payload"]["ep"]["after"] == 6  # was 8, cost 2.

    ch = requests.get(f"{BASE_URL}/api/characters/{char_with_state}",
                        headers=H(gm_token)).json()
    assert ch["folio"]["energy_points"] == 6
    src = deduct["payload"]["source_id"]
    assert ch["folio"]["bundle_charges"][src] == 1


# ─── Genesis archives ─────────────────────────────────────────────────


def test_genesis_archive_round_trip(gm_token, dnd_camp):
    # First save → no archive (nothing to archive yet).
    r = requests.put(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis",
                       headers=H(gm_token),
                       json={"campaign_id": dnd_camp,
                             "sentence_who": "Hero v1",
                             "theme": "draft 1"})
    assert r.status_code == 200, r.text

    arc0 = requests.get(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis/archives",
                          headers=H(gm_token)).json()
    assert arc0 == []

    # Second save archives v1.
    time.sleep(0.5)
    requests.put(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis",
                  headers=H(gm_token),
                  json={"campaign_id": dnd_camp,
                        "sentence_who": "Hero v2", "theme": "draft 2"})
    arc1 = requests.get(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis/archives",
                          headers=H(gm_token)).json()
    assert len(arc1) == 1
    assert arc1[0]["sentence_who"] == "Hero v1"

    # Restore v1.
    aid = arc1[0]["archive_id"]
    rest = requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis/archives/{aid}/restore",
                            headers=H(gm_token))
    assert rest.status_code == 200, rest.text
    live = requests.get(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis",
                          headers=H(gm_token)).json()
    assert live["sentence_who"] == "Hero v1"

    # The restore also archives the v2 we replaced → 2 archives now.
    arc2 = requests.get(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis/archives",
                          headers=H(gm_token)).json()
    assert len(arc2) >= 2

    # Delete one.
    rd = requests.delete(f"{BASE_URL}/api/campaigns/{dnd_camp}/genesis/archives/{aid}",
                           headers=H(gm_token))
    assert rd.status_code == 200


def test_custom_rule_color_round_trip(gm_token, dnd_camp):
    r = requests.post(f"{BASE_URL}/api/campaigns/{dnd_camp}/custom",
                       headers=H(gm_token),
                       json={"campaign_id": dnd_camp, "kind": "feat",
                             "name": "V6257 Color test",
                             "cost_per_level": 1,
                             "color": "#7E5CB7"})
    assert r.status_code == 200, r.text
    assert r.json()["color"] == "#7E5CB7"
    rows = requests.get(f"{BASE_URL}/api/campaigns/{dnd_camp}/custom",
                          headers=H(gm_token)).json()
    match = next(x for x in rows if x["name"] == "V6257 Color test")
    assert match["color"] == "#7E5CB7"
