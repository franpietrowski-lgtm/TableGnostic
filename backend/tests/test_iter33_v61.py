"""V6.1 backend regression — idempotent seeding, Evereantha rewrite, Anime 5E.

Coverage:
  1. /admin/seed-evereantha-suite idempotency (4 new → 4 skipped)
  2. /admin/seed-demo idempotency via _seed_one
  3. Evereantha BESM campaign nodes (≥43, new canon names)
  4. Evereantha motives authors (Vaelin/Morrigan/Lyra/Luminar)
  5. /api/systems/anime-5e/reference — abilities = 5E six + rule_note
  6. Non-GM/player role → 403 on /admin/seed-evereantha-suite
"""
import os
import pytest
import requests

def _base_url():
    val = os.environ.get("REACT_APP_BACKEND_URL")
    if not val:
        # read from frontend/.env
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        return line.split("=", 1)[1].strip().rstrip("/")
        except FileNotFoundError:
            pass
    return (val or "").rstrip("/")


BASE_URL = _base_url()
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


@pytest.fixture(scope="module")
def gm_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": GM_EMAIL, "password": GM_PASS},
                      timeout=20)
    if r.status_code != 200:
        pytest.skip(f"GMFran login failed: {r.status_code} {r.text[:120]}")
    return r.json().get("access_token")


@pytest.fixture(scope="module")
def gm_client(gm_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {gm_token}"})
    return s


# ─────────── 1 & 7 — Evereantha suite idempotency + role guard ───────────
class TestSeedEvereanthaSuite:
    def test_player_forbidden(self):
        # Register ephemeral player
        import uuid
        email = f"test_player_{uuid.uuid4().hex[:8]}@example.com"
        reg = requests.post(f"{BASE_URL}/api/auth/register",
                            json={"email": email, "password": "Pla1yer!x",
                                  "name": "Test Player", "role": "player"},
                            timeout=15)
        assert reg.status_code in (200, 201), f"register: {reg.status_code} {reg.text[:120]}"
        login = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": "Pla1yer!x"},
                              timeout=15)
        assert login.status_code == 200
        tok = login.json().get("access_token")
        r = requests.post(f"{BASE_URL}/api/admin/seed-evereantha-suite",
                          headers={"Authorization": f"Bearer {tok}"},
                          timeout=20)
        assert r.status_code == 403, f"expected 403, got {r.status_code}"

    def test_suite_idempotency_first_then_second(self, gm_client):
        # First call deploys 4 campaigns (may have been deployed by earlier
        # smoke test -- in that case skipped_existing:true on all 4).
        r1 = gm_client.post(f"{BASE_URL}/api/admin/seed-evereantha-suite", timeout=60)
        assert r1.status_code == 200, f"first call: {r1.status_code} {r1.text[:200]}"
        j1 = r1.json()
        assert "deployed" in j1
        deployed1 = j1["deployed"]
        assert len(deployed1) == 4, f"expected 4, got {len(deployed1)}"
        ids1 = [d["id"] for d in deployed1]

        # Second call MUST return the SAME ids with skipped_existing:true.
        r2 = gm_client.post(f"{BASE_URL}/api/admin/seed-evereantha-suite", timeout=60)
        assert r2.status_code == 200
        j2 = r2.json()
        deployed2 = j2["deployed"]
        ids2 = [d["id"] for d in deployed2]
        assert ids2 == ids1, f"IDs changed on repeat: {ids1} vs {ids2}"
        for d in deployed2:
            assert d.get("skipped_existing") is True, \
                f"not skipped: {d.get('name')} skipped={d.get('skipped_existing')}"

        # expose besm-4e cid for downstream tests
        besm = next((d for d in deployed2
                     if d.get("system_id") == "besm-4e"), None)
        assert besm is not None, "no besm-4e campaign in deployed list"
        pytest.besm_cid = besm["id"]


# ─────────── 2 — /seed-demo idempotency ───────────
class TestSeedDemoIdempotency:
    def test_seed_demo_skips_existing(self, gm_client):
        r1 = gm_client.post(f"{BASE_URL}/api/admin/seed-demo", timeout=60)
        assert r1.status_code == 200
        d1 = r1.json().get("deployed", [])
        assert len(d1) == 2
        ids1 = [d["id"] for d in d1]
        r2 = gm_client.post(f"{BASE_URL}/api/admin/seed-demo", timeout=60)
        assert r2.status_code == 200
        d2 = r2.json().get("deployed", [])
        ids2 = [d["id"] for d in d2]
        assert ids2 == ids1
        for d in d2:
            assert d.get("skipped_existing") is True


# ─────────── 3 — Evereantha nodes (≥43 + canon names) ───────────
REQUIRED_NODES = [
    "Eagle's Nest",
    "Gildenwood",
    "Taurid Tor",
    "Aevum & the Colosseum",
    "Technopolis Lumina · Capital of the Singularity",
    "Order of the Darkening Star",
    "Eclipse Syndicate",
    "Sylas Stonefist — Archdeacon, master smith",
    "Vaelin the Quiet — Deacon of Shadows",
    "Morrigan Nightshade — Deaconess of the Dead",
    "Lyra Earthheart — Deaconess of the Elements / EarthMancer",
    "Luminar — Deacon of Light / Light Weaver",
    "Azazel — Deacon of the Void / The Unmaker",
    "Samael — born of Azazel's machine",
    "The Kin — Azazel's Broken Nervous System",
    "Aurae Magic — the Two Faces",
    "Butterfly Effect Gauge (BEG)",
]
OLD_DEPRECATED = [
    "Forge-Glass Hammer", "Eclipse Saint",
    "Mayor Mishtee", "Sister Quench", "Brother Crack",
    # NOTE: "Aurea" alone was a deprecated NPC, but is also the canonical
    # continent name (Continenta Aurea). Skip the substring match here.
]


class TestEvereanthaNodes:
    def test_nodes_count_and_canon_names(self, gm_client):
        cid = getattr(pytest, "besm_cid", None)
        assert cid, "besm_cid fixture not set — suite test must run first"
        r = gm_client.get(f"{BASE_URL}/api/campaigns/{cid}/nodes", timeout=20)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        nodes = r.json()
        assert isinstance(nodes, list)
        assert len(nodes) >= 43, f"expected ≥43 nodes, got {len(nodes)}"
        # nodes use `title` (not `name`)
        titles = [n.get("title", "") for n in nodes]
        missing = [n for n in REQUIRED_NODES if n not in titles]
        assert not missing, f"missing canonical nodes: {missing}"
        # OLD Caldera Choir names must NOT be in the NEW campaign
        leaks = [t for t in titles if any(old in t for old in OLD_DEPRECATED)]
        assert not leaks, f"deprecated names leaked in new seed: {leaks}"


# ─────────── 4 — Evereantha motives ───────────
REQUIRED_MOTIVE_NPCS = [
    "Vaelin the Quiet",
    "Morrigan Nightshade",
]
# NOTE: Lyra and Luminar motives are silently dropped by the seed
# because the motive tuple uses a TRUNCATED npc_name ("Lyra Earthheart
# — EarthMancer") that does NOT match the node title ("Lyra Earthheart
# — Deaconess of the Elements / EarthMancer"). We separately assert
# this fails so the bug is captured in CI.
EXPECTED_MISSING_MOTIVE_NPCS = ["Lyra Earthheart", "Luminar"]


class TestEvereanthaMotives:
    def test_ecosystem_pulse_motives_have_new_authors(self, gm_client):
        cid = getattr(pytest, "besm_cid", None)
        assert cid
        r = gm_client.get(
            f"{BASE_URL}/api/campaigns/{cid}/ecosystem/pulse"
            f"?plot_phase=epic-9-adventures",
            timeout=20)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        data = r.json()
        motives = data.get("active_motives") or []
        # The motive's NPC identity is in `node_label` (e.g.
        # "npc: Vaelin the Quiet — Deacon of Shadows"). `author_name`
        # is the user who created it (GMFran).
        labels = " | ".join(m.get("node_label", "") for m in motives)
        for npc in REQUIRED_MOTIVE_NPCS:
            assert npc in labels, (
                f"NPC '{npc}' not found in active_motives node_labels. "
                f"Got: {labels}"
            )

    def test_lyra_luminar_motives_now_present_v61_fix(self, gm_client):
        """V6.1 fix verified: prefix-tolerant resolver in demo_seed.py
        now matches truncated motive npc_names ('Lyra Earthheart —
        EarthMancer') against full node titles. Both Lyra and Luminar
        motives must now appear in the pulse.
        """
        cid = getattr(pytest, "besm_cid", None)
        assert cid
        r = gm_client.get(
            f"{BASE_URL}/api/campaigns/{cid}/ecosystem/pulse"
            f"?plot_phase=epic-9-adventures",
            timeout=20)
        labels = " | ".join(m.get("node_label", "") for m in r.json().get("active_motives") or [])
        for npc in EXPECTED_MISSING_MOTIVE_NPCS:
            assert npc in labels, (
                f"V6.1 prefix-tolerant resolver regression: "
                f"'{npc}' missing from pulse. labels={labels}"
            )


# ─────────── 5 — Anime 5E reference ───────────
class TestAnime5eReference:
    def test_reference_abilities_and_rule_note(self, gm_client):
        r = gm_client.get(f"{BASE_URL}/api/systems/anime-5e/reference", timeout=15)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        data = r.json()
        abilities = data.get("abilities") or []
        abbrs = [a.get("abbr") for a in abilities]
        assert abbrs == ["STR", "DEX", "CON", "INT", "WIS", "CHA"], \
            f"abilities not 5E-six: {abbrs}"
        rule_note = data.get("rule_note") or ""
        assert rule_note.startswith(
            "Anime 5E is D&D 5E + an OPTIONAL BESM-style point-buy LAYER"
        ), f"rule_note start: {rule_note[:120]}"

    def test_classes_use_5e_abilities(self, gm_client):
        r = gm_client.get(f"{BASE_URL}/api/systems/anime-5e/reference", timeout=15)
        assert r.status_code == 200
        classes = r.json().get("classes") or []
        # 5 anime originals + 12 D&D SRD = 17
        assert len(classes) == 17, f"expected 17 classes, got {len(classes)}"
        expected = {
            "Adept": "Wisdom",
            "Champion": "Strength",
            "Idol": "Charisma",
            "Pilot": "Intelligence",
            "Tinker": "Intelligence",
        }
        by_name = {c["name"]: c for c in classes}
        forbidden = {"Body", "Mind", "Soul", "BOD", "MND", "SOL"}
        for n, prim in expected.items():
            assert n in by_name, f"missing anime class {n}"
            assert by_name[n].get("primary") == prim, \
                f"{n}.primary={by_name[n].get('primary')} expected {prim}"
            assert by_name[n].get("primary") not in forbidden
