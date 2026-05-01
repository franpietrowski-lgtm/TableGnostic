"""V6.16 — Port Eli (BESM Maiden Adventure) into the 3 sister system
campaigns (Cypher / D&D 5E / Anime 5E hybrid) using the new
/api/convert/character endpoint, then transfer each port to Aurora
(player account) so the cross-account UX can be tested.

This is a one-shot seed script — run it, verify the 3 new sheets
appear in Aurora's "My characters" rail, and we're done with Cut 2.

Run from repo root:
    cd /app/backend && python3 scripts/port_eli_v616.py
"""
from __future__ import annotations

import os
import sys
import time

import requests
from dotenv import load_dotenv

# ───────────────────────── config ─────────────────────────
load_dotenv()  # picks up MONGO_URL + DB_NAME for any DB-side audit

API = os.environ.get("REACT_APP_BACKEND_URL_INTERNAL") or "http://localhost:8001"
GM_EMAIL = "franpietrowski@gmail.com"
GM_PASS = "PieGod08!!"

# Source — Eli on the BESM Maiden Adventure (V6.13 seed).
SOURCE_CHAR_ID = "244db025742b4bd9a9662f6240e40729"

# Targets — the 3 Evereantha sister campaigns + the Anime-5E hybrid.
# Re-runs are idempotent at the script level (just generates a new id),
# but to avoid duplicates set ONLY_TARGETS to a system list — empty = all.
ONLY_TARGETS = (os.environ.get("ONLY_TARGETS") or "").split(",") if os.environ.get("ONLY_TARGETS") else []
TARGETS = {
    "cypher":   "7e510c2be80440708622f6a3b2f3dae4",
    "dnd-5e":   "0b22785861b64c70bf1fae181ca38f84",
    "anime-5e": "f68e1b235fbe4f1bab702a05aa7b4467",
}
if ONLY_TARGETS:
    TARGETS = {k: v for k, v in TARGETS.items() if k in ONLY_TARGETS}

# Player owner — Aurora.
AURORA_USER_ID = "3dc6882a9b6847ef91bef6f3640e120c"


def gm_login() -> str:
    r = requests.post(
        f"{API}/api/auth/login",
        json={"email": GM_EMAIL, "password": GM_PASS},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def port_one(token: str, target_system: str, target_cid: str) -> dict:
    print(f"\n===== Porting Eli → {target_system} ({target_cid}) =====")
    body = {
        "source_character_id": SOURCE_CHAR_ID,
        "target_campaign_id": target_cid,
        "new_owner_id": AURORA_USER_ID,
        "keep_folio": True,
        "name_override": f"Eli ({target_system})",
    }
    t0 = time.time()
    r = requests.post(
        f"{API}/api/convert/character",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,  # Claude calls can take 30-60s per port
    )
    dt = time.time() - t0
    if r.status_code != 200:
        print(f"  FAILED · {r.status_code} · {r.text[:600]}")
        return {}
    out = r.json()
    ch = out.get("character", {})
    print(
        f"  OK  ({dt:.1f}s) · id={ch.get('id')} · name={ch.get('name')!r} "
        f"· owner={ch.get('owner_name')!r} · system={ch.get('system_id')}"
    )
    if out.get("caveats"):
        print(f"  caveats: {out['caveats']}")
    return ch


def main() -> int:
    token = gm_login()
    print(f"GM token acquired ({len(token)} chars)")
    results = {}
    for target_system, cid in TARGETS.items():
        ch = port_one(token, target_system, cid)
        results[target_system] = ch
    print("\n===== SUMMARY =====")
    for sys_id, ch in results.items():
        if ch:
            print(f"  {sys_id:<10} · {ch.get('id')} · {ch.get('name')}")
        else:
            print(f"  {sys_id:<10} · FAILED")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
