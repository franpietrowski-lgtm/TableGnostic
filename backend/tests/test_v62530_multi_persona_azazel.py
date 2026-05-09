"""V6.25.30 — Multi-persona email + Azazel-style codex layout tests."""
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"


def _hdr(t):
    return {"Authorization": f"Bearer {t}"}


def test_multi_persona_login_disambiguates_by_password():
    """V6.25.30 — same email + different passwords ⇒ different identities."""
    # GM persona.
    r = requests.post(f"{API}/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!"})
    assert r.status_code == 200, r.text
    gm = r.json()
    assert gm["role"] in {"admin", "gm", "user"}
    # Player persona (created by the main agent V6.25.30).
    r = requests.post(f"{API}/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieBan18!!"})
    assert r.status_code == 200, r.text
    player = r.json()
    assert player["role"] == "player"
    # Different ids → different identities.
    assert gm["id"] != player["id"]
    assert gm["email"] == player["email"]
    # Wrong password under either email locks rate-limiting in.
    r = requests.post(f"{API}/auth/login",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "definitely-wrong-XX"})
    assert r.status_code in (401, 423)


def test_register_blocks_same_email_same_password_combo():
    """Soft guard — re-registering with email + password that already
    matches an existing account returns 400 (otherwise login would be
    ambiguous between two identical credentials)."""
    r = requests.post(f"{API}/auth/register",
                       json={"email": "franpietrowski@gmail.com",
                             "password": "PieGod08!!",
                             "name": "x", "role": "player"})
    assert r.status_code == 400, r.text
    assert "already exists" in (r.json().get("detail") or "").lower()


def test_codex_pdf_renders_azazel_when_fields_present():
    """V6.25.30 — codex PDF must include the seeded Azazel rich entity
    and still produce a valid PDF (>= 10 KB given the layout)."""
    token = requests.post(f"{API}/auth/login",
                           json={"email": "franpietrowski@gmail.com",
                                 "password": "PieGod08!!"}
                           ).json()["access_token"]
    cid = "af461ae004364002932f93c5b71cd483"  # Maiden Voyage
    r = requests.get(f"{API}/campaigns/{cid}/codex-export.pdf",
                      headers=_hdr(token), timeout=30)
    assert r.status_code == 200, r.text
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 10000, "Azazel layout should add bulk"


def test_azazel_layout_handles_node_without_structured_fields():
    """A plain codex node without azazel fields still renders via the
    legacy path — no regression on existing campaigns."""
    token = requests.post(f"{API}/auth/login",
                           json={"email": "franpietrowski@gmail.com",
                                 "password": "PieGod08!!"}
                           ).json()["access_token"]
    cid = "01a74ce4d3064b83a94ac897e1689e62"  # Fracture campaign — no azazel
    r = requests.get(f"{API}/campaigns/{cid}/codex-export.pdf",
                      headers=_hdr(token), timeout=30)
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
