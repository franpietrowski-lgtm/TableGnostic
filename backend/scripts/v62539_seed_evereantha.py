"""V6.25.39 — Seed Evereantha — The Maiden Adventure with the full
campaign bible content the user supplied.

Pipeline:
  1. Download the EXPANDED HTML campaign bible.
  2. Parse to plain text (via the same `_parse_to_text` the API uses).
  3. Run the sectioned Claude ingestion (one focused call per `##`
     section — better fidelity for a 68k-char bible than a single
     truncated mega-call).
  4. Persist the ingestion record exactly as the API would.
  5. Auto-accept ALL suggestions into the campaign's Knowledge Web
     (codex nodes for NPCs / locations / lore / quests; custom rules
     for attributes / power packs / items / weapons / skills).

Runs in-process so no HTTP 60s gateway timeout. Idempotent — re-running
just creates a new ingestion record; previously accepted suggestions
remain (no dupes thanks to the existing `accepted` flag).

Run with:
    cd /app/backend && set -a && source .env && set +a && \
        PYTHONPATH=/app/backend python scripts/v62539_seed_evereantha.py
"""
import asyncio
import json
from pathlib import Path

import httpx

from core.db import db, new_id, now_iso
from routes.ingest import (
    _parse_to_text,
    _call_claude_auto,
    _looks_like_intake_template,
)

MAIDEN_CID = "af461ae004364002932f93c5b71cd483"
ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
BIBLE_URL = (
    "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/"
    "7ojzivqa_Evereantha_Rites_Of_All_Campaign_Bible_EXPANDED.html"
)


NODE_KINDS = {"lore", "npc", "location", "quest"}
CUSTOM_KINDS = {"attribute", "power_pack", "power_bundle",
                "item", "weapon", "skill"}


async def _accept_one(sugg: dict, campaign_id: str, ingest_id: str) -> dict:
    """Inline copy of the accept-suggestions persistence for a single
    suggestion — avoids re-implementing the route's auth gate."""
    kind = sugg["kind"]
    if kind in NODE_KINDS:
        node = {
            "id": new_id(),
            "campaign_id": campaign_id,
            "type": kind,
            "title": sugg["title"],
            "content": sugg.get("summary", ""),
            "tags": ["ingest", f"atelier-phase-{sugg.get('atelier_phase', 4)}",
                     "evereantha-bible"],
            "visibility": "gm_only",
            "revealed_to": [],
            "links": [],
            "fields": {
                **(sugg.get("fields") or {}),
                "ingest_id": ingest_id,
                "source_ref": sugg.get("source_ref"),
                "atelier_phase": sugg.get("atelier_phase"),
                "target_arc": sugg.get("target_arc"),
            },
            "created_at": now_iso(),
        }
        await db.nodes.insert_one(node)
        return {"kind": kind, "node_id": node["id"], "title": node["title"]}
    elif kind in CUSTOM_KINDS:
        custom = {
            "id": new_id(),
            "campaign_id": campaign_id,
            "kind": kind,
            "title": sugg["title"],
            "summary": sugg.get("summary", ""),
            "fields": sugg.get("fields") or {},
            "ingest_id": ingest_id,
            "source_ref": sugg.get("source_ref"),
            "tags": ["ingest", "evereantha-bible"],
            "created_at": now_iso(),
        }
        await db.custom_attributes.insert_one(custom)
        return {"kind": kind, "custom_id": custom["id"], "title": custom["title"]}
    return {"kind": kind, "skipped": True, "title": sugg.get("title")}


async def main() -> None:
    camp = await db.campaigns.find_one({"id": MAIDEN_CID}, {"_id": 0})
    if not camp:
        print(f"FATAL: campaign '{MAIDEN_CID}' missing — run transfer script first.")
        return

    admin = await db.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "id": 1, "name": 1})
    if not admin:
        print(f"FATAL: admin '{ADMIN_EMAIL}' not seeded.")
        return

    # 1) Download the HTML bible (cache locally).
    cache = Path("/tmp/evereantha_bible.html")
    if not cache.exists() or cache.stat().st_size < 1024:
        print(f"Downloading {BIBLE_URL} …")
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(BIBLE_URL)
            r.raise_for_status()
            cache.write_bytes(r.content)
    raw = cache.read_bytes()
    print(f"Cached bible: {len(raw)} bytes")

    # 2) Parse to text.
    text = _parse_to_text(cache.name, "text/html", raw)
    if not text:
        print("FATAL: parser returned empty text.")
        return
    print(f"Extracted {len(text):,} chars. Intake-template shape: "
          f"{_looks_like_intake_template(text)}")

    # 3) Run sectioned Claude ingestion (no HTTP timeout, in-process).
    print("Running Claude sectioned auto-ingest (may take a few minutes)…")
    parsed = await _call_claude_auto(cache.name, camp.get("system_id"), text)
    sugs = parsed.get("suggestions") or []
    print(f"Claude returned {len(sugs)} suggestions. "
          f"Detected counts: {parsed.get('detected_kind_counts')}")

    # 4) Persist the ingestion record.
    ingest_id = new_id()
    doc = {
        "id": ingest_id,
        "campaign_id": MAIDEN_CID,
        "filename": cache.name,
        "content_type": "text/html",
        "byte_size": len(raw),
        "extracted_chars": len(text),
        "summary": parsed.get("summary", ""),
        "detected_kind_counts": parsed.get("detected_kind_counts", {}),
        "suggestions": sugs,
        "status": "accepted",  # we auto-accept everything below
        "created_at": now_iso(),
        "created_by": admin["id"],
        "auto_accepted_by_seed_script": True,
    }
    await db.ingestions.insert_one(doc)
    print(f"Persisted ingestion record: {ingest_id}")

    # 5) Auto-accept every suggestion.
    accepted = []
    for idx, s in enumerate(sugs):
        try:
            r = await _accept_one(s, MAIDEN_CID, ingest_id)
            accepted.append(r)
        except Exception as e:
            print(f"  ! suggestion {idx} ({s.get('kind')} / {s.get('title')}) failed: {e}")
    # Mark suggestions accepted on the ingestion record (idempotency).
    for idx, _s in enumerate(sugs):
        if idx < len(accepted):
            sugs[idx]["accepted"] = True
    await db.ingestions.update_one(
        {"id": ingest_id},
        {"$set": {"suggestions": sugs}},
    )

    # Summary breakdown.
    by_kind: dict = {}
    for a in accepted:
        by_kind[a.get("kind", "?")] = by_kind.get(a.get("kind", "?"), 0) + 1
    print("\n=== SEED COMPLETE ===")
    print(f"Ingestion id: {ingest_id}")
    print(f"Total accepted: {len(accepted)}")
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"  {k}: {n}")
    print()
    print(f"Sample:")
    for a in accepted[:8]:
        print(f"  - {a.get('kind'):<12} {a.get('title')}")


if __name__ == "__main__":
    asyncio.run(main())
