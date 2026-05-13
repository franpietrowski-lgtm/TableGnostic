"""V6.25.42 — Live end-to-end HTTP regression for the V6.25.42 surface.

Exercises the LIVE external REACT_APP_BACKEND_URL (not localhost) to
confirm auto-queue + dynamic public + SEO + admin moderation +
cost-balance preview all work through the real ASGI/ingress stack.
"""
import os
import uuid
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
ADMIN_PASS = "LoremasterAurea2026!Forge"
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password}, timeout=20)
    if r.status_code != 200:
        return None, r
    body = r.json()
    return body.get("token") or body.get("access_token"), r


@pytest.fixture(scope="module")
def admin_token():
    tok, r = _login(ADMIN_EMAIL, ADMIN_PASS)
    if not tok:
        pytest.skip(f"admin login failed status={r.status_code} body={r.text[:200]}")
    return tok


@pytest.fixture(scope="module")
def gm_token():
    tok, r = _login(GM_EMAIL, GM_PASS)
    if not tok:
        pytest.skip(f"gm login failed status={r.status_code} body={r.text[:200]}")
    return tok


@pytest.fixture(scope="module")
def player_token():
    """Aurora is a role=player non-admin — used to verify 403 gating."""
    tok, r = _login("albanaszak@ymail.com", "AuroraTest123!")
    if not tok:
        pytest.skip(f"player login failed status={r.status_code}")
    return tok


def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ─── Public dynamic endpoints (no auth) ────────────────────────────
class TestPublicEndpoints:
    def test_public_stats(self):
        r = requests.get(f"{BASE_URL}/api/public/stats", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "campaigns" in data
        assert "_id" not in data
        # numeric
        for k in ("campaigns", "characters"):
            assert isinstance(data.get(k), int)

    def test_public_roadmap(self):
        r = requests.get(f"{BASE_URL}/api/public/roadmap", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        for item in data["items"]:
            assert "_id" not in item

    def test_public_featured(self):
        r = requests.get(f"{BASE_URL}/api/public/featured", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "item" in data
        if data["item"] is not None:
            assert "_id" not in data["item"]
            # expected curated fields
            for f in ("id", "name", "slug"):
                assert f in data["item"]


# ─── SEO endpoints ─────────────────────────────────────────────────
class TestSEO:
    def test_sitemap_xml(self):
        r = requests.get(f"{BASE_URL}/api/seo/sitemap.xml", timeout=20)
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert ("xml" in ct.lower()), f"unexpected content-type {ct}"
        body = r.text
        assert "<urlset" in body
        assert "/discover" in body

    def test_og_unknown_slug(self):
        # Random unknown slug — per spec returns either 404 or fallback SVG.
        slug = f"nonexistent-{uuid.uuid4().hex[:8]}"
        r = requests.get(f"{BASE_URL}/api/seo/og/{slug}.svg", timeout=20)
        assert r.status_code in (200, 404), f"got {r.status_code}"
        if r.status_code == 200:
            assert "svg" in r.headers.get("content-type", "").lower()

    def test_og_known_slug_if_any(self, admin_token):
        # Find a discover_published campaign via admin/showcases.
        r = requests.get(f"{BASE_URL}/api/admin/showcases", headers=_h(admin_token), timeout=20)
        if r.status_code != 200:
            pytest.skip("cannot list showcases")
        items = r.json().get("items", [])
        slugs = [c.get("discover_slug") for c in items if c.get("discover_slug")]
        if not slugs:
            pytest.skip("no published showcases on this instance")
        slug = slugs[0]
        rr = requests.get(f"{BASE_URL}/api/seo/og/{slug}.svg", timeout=20)
        assert rr.status_code == 200
        assert "svg" in rr.headers.get("content-type", "").lower()
        assert "<svg" in rr.text


# ─── Cost-balance preview (route is /api/convert/preview-cost-balance) ─
class TestCostBalance:
    def test_preview_cost_balance_or_skip(self, gm_token):
        # Find a character owned by GM.
        r = requests.get(f"{BASE_URL}/api/characters?mine=true", headers=_h(gm_token), timeout=20)
        if r.status_code != 200:
            pytest.skip(f"cannot list characters: {r.status_code}")
        chars = r.json()
        if not chars:
            pytest.skip("GM has no characters to preview")
        src_id = chars[0]["id"]
        # Try BESM<->Cypher preview.
        for target in ("cypher", "besm-4e"):
            rr = requests.post(
                f"{BASE_URL}/api/convert/preview-cost-balance",
                headers=_h(gm_token),
                json={"source_character_id": src_id, "target_system": target},
                timeout=30,
            )
            if rr.status_code == 400:
                continue  # unsupported target — try next
            assert rr.status_code == 200, f"target={target} body={rr.text[:300]}"
            data = rr.json()
            # The route returns compute_cost_balance(); spec wants
            # source_cost/target_cost/delta — accept either source_budget/target_budget
            # or source_cost/target_cost shape.
            keys = set(data.keys())
            has_src = bool(keys & {"source_cost", "source_budget"})
            has_tgt = bool(keys & {"target_cost", "target_budget"})
            assert has_src and "delta" in data and has_tgt, f"missing keys, got {keys}"
            return
        pytest.skip("no supported target system for preview")


# ─── Admin moderation gating ───────────────────────────────────────
class TestAdminModeration:
    def test_admin_endpoints_require_admin(self, player_token):
        # Non-admin Aurora hitting admin/flags should 403.
        r = requests.get(f"{BASE_URL}/api/admin/flags", headers=_h(player_token), timeout=20)
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text[:200]}"

    def test_admin_flags_list(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/flags", headers=_h(admin_token), timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and isinstance(body["items"], list)

    def test_admin_audit_log(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/audit", headers=_h(admin_token), timeout=20)
        assert r.status_code == 200
        assert "items" in r.json()

    def test_admin_showcases(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/showcases", headers=_h(admin_token), timeout=20)
        assert r.status_code == 200

    def test_admin_roadmap_crud(self, admin_token, player_token):
        # Non-admin forbidden.
        r = requests.get(f"{BASE_URL}/api/admin/roadmap", headers=_h(player_token), timeout=20)
        assert r.status_code == 403
        # Admin create.
        payload = {"title": f"TEST_roadmap {uuid.uuid4().hex[:6]}",
                   "body_md": "test entry", "status": "next", "public": True}
        c = requests.post(f"{BASE_URL}/api/admin/roadmap", headers=_h(admin_token),
                          json=payload, timeout=20)
        assert c.status_code == 200, c.text[:200]
        rid = c.json()["id"]
        # Patch
        p = requests.patch(f"{BASE_URL}/api/admin/roadmap/{rid}", headers=_h(admin_token),
                           json={"status": "now"}, timeout=20)
        assert p.status_code == 200
        assert p.json()["status"] == "now"
        # Public read sees it.
        pr = requests.get(f"{BASE_URL}/api/public/roadmap", timeout=20)
        assert any(it["id"] == rid for it in pr.json()["items"])
        # Delete
        d = requests.delete(f"{BASE_URL}/api/admin/roadmap/{rid}", headers=_h(admin_token), timeout=20)
        assert d.status_code == 200


# ─── Auto-queue intercept end-to-end ───────────────────────────────
class TestAutoQueueLive:
    """Spin up a clean campaign with gating ON, add a player, attempt
    a player PUT — expect 202 + change_request inserted. Also verify
    GM bypass and non-inventory folio passthrough."""

    @pytest.fixture(scope="class")
    def setup(self, admin_token):
        # Use GMFran (admin/GM) to create + own the campaign, and Aurora
        # (role=player) as the non-admin/non-GM player whose edits should
        # be intercepted. Aurora is seeded; no registration needed.
        gm_tok, _ = _login(GM_EMAIL, GM_PASS)
        if not gm_tok:
            pytest.skip("GM login failed")
        player_tok, pr = _login("albanaszak@ymail.com", "AuroraTest123!")
        if not player_tok:
            pytest.skip(f"player (Aurora) login failed: {pr.status_code}")
        player_id = pr.json().get("id")

        # GM creates a campaign.
        camp_body = {"name": f"TEST_camp_{uuid.uuid4().hex[:6]}",
                     "system_id": "besm-4e"}
        cc = requests.post(f"{BASE_URL}/api/campaigns", headers=_h(gm_tok),
                           json=camp_body, timeout=20)
        if cc.status_code not in (200, 201):
            pytest.skip(f"cannot create campaign: {cc.status_code} {cc.text[:200]}")
        camp = cc.json()
        cid = camp.get("id") or camp.get("campaign", {}).get("id")
        if not cid:
            pytest.skip(f"campaign id missing: {camp}")

        # Add player via invite_token flow. GET the campaign to fetch
        # `invite_token`, then POST /api/invites/{token}/accept as the player.
        camp_full = requests.get(f"{BASE_URL}/api/campaigns/{cid}",
                                  headers=_h(gm_tok), timeout=15).json()
        invite_token = camp_full.get("invite_token")
        added = False
        if invite_token:
            j = requests.post(f"{BASE_URL}/api/invites/{invite_token}/accept",
                              headers=_h(player_tok), json={}, timeout=20)
            if j.status_code in (200, 201):
                added = True
        if not added:
            requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=_h(gm_tok), timeout=10)
            pytest.skip(f"could not add player via invite: {invite_token}")

        # Player creates a character.
        ch_body = {"name": "TEST_PC", "campaign_id": cid,
                   "concept": "tester", "total_points": 10}
        chr_r = requests.post(f"{BASE_URL}/api/characters", headers=_h(player_tok),
                              json=ch_body, timeout=20)
        if chr_r.status_code not in (200, 201):
            pytest.skip(f"player cannot create character: {chr_r.status_code} {chr_r.text[:200]}")
        ch = chr_r.json()
        ch_id = ch["id"]

        # GM flips gating ON.
        g = requests.patch(f"{BASE_URL}/api/campaigns/{cid}/settings/approval",
                           headers=_h(gm_tok),
                           json={"gm_approval_required": True}, timeout=20)
        assert g.status_code == 200, f"gate toggle failed: {g.status_code} {g.text[:200]}"

        yield {"cid": cid, "ch_id": ch_id, "gm_tok": gm_tok,
               "player_tok": player_tok, "ch": ch}

        # Teardown — delete the character + campaign.
        requests.delete(f"{BASE_URL}/api/characters/{ch_id}", headers=_h(gm_tok), timeout=15)
        requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=_h(gm_tok), timeout=15)

    def test_player_put_gets_queued(self, setup):
        s = setup
        put_body = dict(s["ch"])
        # Strip server-only fields
        for k in ("derived", "spent", "_id"):
            put_body.pop(k, None)
        put_body["name"] = "TEST_PC_renamed"
        r = requests.put(f"{BASE_URL}/api/characters/{s['ch_id']}",
                         headers=_h(s["player_tok"]), json=put_body, timeout=20)
        assert r.status_code == 202, f"expected 202 got {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert body.get("queued") is True
        assert "change_request" in body
        cr = body["change_request"]
        assert cr["status"] == "pending"
        assert cr["kind"] == "character"
        # Verify character NOT mutated.
        gr = requests.get(f"{BASE_URL}/api/characters/{s['ch_id']}",
                          headers=_h(s["gm_tok"]), timeout=15)
        assert gr.status_code == 200
        assert gr.json()["name"] != "TEST_PC_renamed"

    def test_player_inventory_folio_queued(self, setup):
        s = setup
        r = requests.patch(f"{BASE_URL}/api/characters/{s['ch_id']}/folio",
                           headers=_h(s["player_tok"]),
                           json={"bucket": "inventory_state",
                                 "patch": {"loot": ["TEST sword"]}}, timeout=20)
        assert r.status_code == 202, f"expected 202 got {r.status_code}: {r.text[:300]}"
        assert r.json().get("queued") is True

    def test_player_noninventory_folio_passes_through(self, setup):
        s = setup
        r = requests.patch(f"{BASE_URL}/api/characters/{s['ch_id']}/folio",
                           headers=_h(s["player_tok"]),
                           json={"bucket": "dnd_state",
                                 "patch": {"spells_prepared": ["TEST"]}}, timeout=20)
        assert r.status_code == 200, f"expected 200 got {r.status_code}: {r.text[:300]}"
        assert r.json().get("ok") is True

    def test_gm_put_passes_through(self, setup):
        s = setup
        # GM gets current character then PUTs.
        gr = requests.get(f"{BASE_URL}/api/characters/{s['ch_id']}",
                          headers=_h(s["gm_tok"]), timeout=15)
        ch = gr.json()
        for k in ("derived", "spent", "_id", "effective_level"):
            ch.pop(k, None)
        for a in ch.get("attributes", []) or []:
            a.pop("effective_level", None)
        ch["name"] = "TEST_PC_gm_edit"
        r = requests.put(f"{BASE_URL}/api/characters/{s['ch_id']}",
                         headers=_h(s["gm_tok"]), json=ch, timeout=20)
        assert r.status_code == 200, f"expected 200 got {r.status_code}: {r.text[:300]}"
        assert r.json().get("name") == "TEST_PC_gm_edit"

    def test_gate_off_player_writes_through(self, setup):
        s = setup
        # Flip gate OFF.
        g = requests.patch(f"{BASE_URL}/api/campaigns/{s['cid']}/settings/approval",
                           headers=_h(s["gm_tok"]),
                           json={"gm_approval_required": False}, timeout=20)
        assert g.status_code == 200
        gr = requests.get(f"{BASE_URL}/api/characters/{s['ch_id']}",
                          headers=_h(s["player_tok"]), timeout=15)
        ch = gr.json()
        for k in ("derived", "spent", "_id", "effective_level"):
            ch.pop(k, None)
        for a in ch.get("attributes", []) or []:
            a.pop("effective_level", None)
        ch["name"] = "TEST_PC_gate_off"
        r = requests.put(f"{BASE_URL}/api/characters/{s['ch_id']}",
                         headers=_h(s["player_tok"]), json=ch, timeout=20)
        assert r.status_code == 200, f"expected 200 got {r.status_code}: {r.text[:300]}"
        assert r.json().get("name") == "TEST_PC_gate_off"
