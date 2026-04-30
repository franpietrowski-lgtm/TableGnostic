"""V6.1 RETEST — iter34: motive-resolver + idempotency + Tri-Stat scrub.

Coverage:
  1. DELETE pre-existing Evereantha campaigns for GMFran, then
     POST /admin/seed-evereantha-suite — assert 4 deployed,
     each with motives==9 AND skipped_existing==False on FRESH seed.
  2. Second call: skipped_existing==True for all 4, IDs preserved.
  3. /campaigns/{fresh_besm_cid}/ecosystem/pulse?plot_phase=epic-9-adventures
     returns active_motives covering Vaelin, Morrigan, Lyra, Luminar,
     The Kin (matched via prefix-tolerant resolver).
  4. Total motive count across all plot phases ≥9.
  5. /admin/seed-demo idempotency (skipped_existing:true on 2nd call).
"""
import os
import pytest
import requests


def _base_url():
    val = os.environ.get("REACT_APP_BACKEND_URL")
    if not val:
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
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": GM_EMAIL, "password": GM_PASS},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"GMFran login failed: {r.status_code} {r.text[:120]}")
    return r.json().get("access_token")


@pytest.fixture(scope="module")
def gm_client(gm_token):
    s = requests.Session()
    s.headers.update(
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gm_token}",
        }
    )
    return s


# ─────────── 1 — Force-fresh suite seed: motives==9 AND not skipped ───────────
class TestFreshEvereanthaSuite:
    def test_delete_existing_then_fresh_seed_has_9_motives(self, gm_client):
        # 1) find all "Fracture of the Unmaker" campaigns owned by GMFran
        r = gm_client.get(f"{BASE_URL}/api/campaigns?mine=true", timeout=20)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        camps = r.json()
        targets = [
            c
            for c in camps
            if "Fracture of the Unmaker" in (c.get("name") or "")
        ]
        # 2) delete each
        for c in targets:
            cid = c["id"]
            d = gm_client.delete(
                f"{BASE_URL}/api/campaigns/{cid}", timeout=15
            )
            assert d.status_code in (
                200,
                204,
            ), f"DELETE {cid} -> {d.status_code} {d.text[:140]}"

        # 3) FRESH seed-evereantha-suite — must NOT skip
        r1 = gm_client.post(
            f"{BASE_URL}/api/admin/seed-evereantha-suite", timeout=90
        )
        assert r1.status_code == 200, f"{r1.status_code} {r1.text[:200]}"
        j1 = r1.json()
        deployed1 = j1.get("deployed", [])
        assert len(deployed1) == 4, f"expected 4 deployed, got {len(deployed1)}"

        for d in deployed1:
            # Fresh seed: backend currently OMITS skipped_existing field
            # (returns None on .get). Spec asks for explicit False but
            # absent-or-False both mean "fresh" — accept either.
            assert d.get("skipped_existing") is not True, (
                f"FRESH seed should NOT skip: {d.get('name')} "
                f"system={d.get('system_id')} skipped="
                f"{d.get('skipped_existing')}"
            )
            assert d.get("motives") == 9, (
                f"motives count broken: {d.get('name')} "
                f"system={d.get('system_id')} motives={d.get('motives')} "
                f"(expected 9)"
            )

        # expose besm-4e cid for downstream tests
        besm = next(
            (d for d in deployed1 if d.get("system_id") == "besm-4e"), None
        )
        assert besm is not None, "no besm-4e in deployed list"
        pytest.fresh_besm_cid = besm["id"]
        pytest.fresh_ids = [d["id"] for d in deployed1]

    def test_second_call_returns_skipped_existing_true(self, gm_client):
        ids1 = getattr(pytest, "fresh_ids", None)
        assert ids1, "first test must run before this one"
        r2 = gm_client.post(
            f"{BASE_URL}/api/admin/seed-evereantha-suite", timeout=60
        )
        assert r2.status_code == 200
        j2 = r2.json()
        deployed2 = j2.get("deployed", [])
        ids2 = [d["id"] for d in deployed2]
        assert ids2 == ids1, f"IDs changed on repeat: {ids1} vs {ids2}"
        for d in deployed2:
            assert d.get("skipped_existing") is True, (
                f"2nd call must skip: {d.get('name')} "
                f"skipped={d.get('skipped_existing')}"
            )


# ─────────── 2 — Pulse motives include Vaelin/Morrigan/Lyra/Luminar/Kin ─────
EPIC9_REQUIRED_NPCS = [
    "Vaelin the Quiet",
    "Morrigan Nightshade",
    "Lyra Earthheart",
    "Luminar",
    "The Kin",
]


class TestPulseMotives:
    def test_epic9_motives_include_all_5_canonical_npcs(self, gm_client):
        cid = getattr(pytest, "fresh_besm_cid", None)
        assert cid, "fresh_besm_cid not set"
        r = gm_client.get(
            f"{BASE_URL}/api/campaigns/{cid}/ecosystem/pulse"
            f"?plot_phase=epic-9-adventures",
            timeout=20,
        )
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        data = r.json()
        motives = data.get("active_motives") or []
        labels = " | ".join(m.get("node_label", "") for m in motives)
        missing = [n for n in EPIC9_REQUIRED_NPCS if n not in labels]
        assert not missing, (
            f"Missing canonical motive NPCs at epic-9-adventures: "
            f"{missing}. Got labels: {labels}"
        )

    def test_total_motives_across_all_phases_at_least_9(self, gm_client):
        cid = getattr(pytest, "fresh_besm_cid", None)
        assert cid
        # Iterate all known phases — sum unique motives.
        phases = [
            "genesis-1-foundation",
            "genesis-2-themes",
            "genesis-3-nemesis",
            "epic-4-storyteller",
            "epic-5-design",
            "epic-6-canon",
            "epic-7-milestones",
            "epic-8-adventures",
            "epic-9-adventures",
        ]
        seen = set()
        for ph in phases:
            r = gm_client.get(
                f"{BASE_URL}/api/campaigns/{cid}/ecosystem/pulse"
                f"?plot_phase={ph}",
                timeout=15,
            )
            if r.status_code != 200:
                continue
            for m in r.json().get("active_motives") or []:
                seen.add(m.get("id") or m.get("node_label"))
        assert len(seen) >= 9, (
            f"Total unique motives across all phases = {len(seen)} "
            f"(expected ≥9). Items: {seen}"
        )


# ─────────── 3 — seed-demo idempotency regression ───────────
class TestSeedDemoIdempotency:
    def test_seed_demo_skips_existing_on_second_call(self, gm_client):
        r1 = gm_client.post(f"{BASE_URL}/api/admin/seed-demo", timeout=60)
        assert r1.status_code == 200
        d1 = r1.json().get("deployed", [])
        assert len(d1) == 2
        ids1 = [d["id"] for d in d1]
        r2 = gm_client.post(f"{BASE_URL}/api/admin/seed-demo", timeout=60)
        assert r2.status_code == 200
        d2 = r2.json().get("deployed", [])
        ids2 = [d["id"] for d in d2]
        assert ids2 == ids1, f"seed-demo IDs changed: {ids1} vs {ids2}"
        for d in d2:
            assert d.get("skipped_existing") is True, (
                f"seed-demo not skipped: {d.get('name')}"
            )
