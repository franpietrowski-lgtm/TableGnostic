"""V6.25.46 — Evereantha lore re-seed (chunk-incremental + resumable).

Successor to v62543_evereantha_reseed.py. Two structural changes:

  1. **Chunk-incremental persistence.** Each chunk's suggestions are
     written to MongoDB the instant Claude returns them, not buffered
     until the whole source completes. A `db.reseed_checkpoints`
     document is upserted with `{source_tag, chunk_no, status}` so a
     killed-and-restarted script can skip already-completed chunks.

  2. **Durable logging.** Writes to `/var/log/tablegnostic/reseed.log`
     instead of `/tmp/`. The container's tmp wipe will no longer eat
     the progress log mid-run.

Run modes
---------
    # Resume from wherever the script last stopped (default):
    PYTHONPATH=/app/backend python scripts/v62546_evereantha_reseed_incremental.py

    # Wipe v3 data and start over (only when you explicitly want a reset):
    PYTHONPATH=/app/backend python scripts/v62546_evereantha_reseed_incremental.py --fresh

Idempotency
-----------
  * Every persisted row carries `script_run_id` AND `(source_tag, chunk_no)`
    so re-running with the same source set does NOT create duplicates.
    The checkpoint table is the source of truth for "has this chunk
    been ingested already".
  * `--fresh` wipes every v3-tagged row and resets the checkpoint table.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

import httpx

from core.db import db, new_id, now_iso
from routes.ingest import _parse_to_text


MAIDEN_CID = "af461ae004364002932f93c5b71cd483"
ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
SEED_TAG = "evereantha-bible-llm-seed-v3"
LEGACY_SEED_TAGS = ["evereantha-bible-llm-seed", "evereantha-bible-llm-seed-v2"]
CHECKPOINT_COL = "reseed_checkpoints"  # {source_tag, chunk_no, status}

SOURCES = [
    ("bible-v3",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/hggzg3mj_Evereantha_The_Rites_Of_All_Campaign_Bible.pdf",
     "/var/cache/tablegnostic/eve_bible_v3.pdf"),
    ("supplement-v3",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/5m3s2m3t_Evereantha_Rites_to_Suppliment_v2.pdf",
     "/var/cache/tablegnostic/eve_suppl_v3.pdf"),
    ("evereantha-extras",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/k6nfo3sm_Evereantha%20e4f31179bbcf47369d26a715cfcf542e.pdf",
     "/var/cache/tablegnostic/eve_extras_v3.pdf"),
    ("artisans-tale",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/8b508ktb_artisans%20tale.pdf",
     "/var/cache/tablegnostic/artisans_tale.pdf"),
]

NODE_KINDS = {"lore", "npc", "location", "quest", "faction", "creature"}
CUSTOM_KINDS = {"attribute", "power_pack", "power_bundle",
                "item", "weapon", "skill", "house_rule"}

CHUNK_SIZE_CHARS = 4200
CHUNK_OVERLAP_CHARS = 350
MAX_RETRIES = 4
BASE_BACKOFF_S = 6.0
INTER_CHUNK_DELAY_S = 2.5

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
SCRIPT_RUN_ID = new_id()

LOG_DIR = Path("/var/log/tablegnostic")
LOG_PATH = LOG_DIR / "reseed.log"


# ---- Bespoke Claude prompt (identical to v62543 — proven good) -------
SYSTEM_PROMPT = (
    "You are an extraction engine for the TableGnostic RPG platform. "
    "Given a CHUNK of the Evereantha campaign bible, you return JSON "
    "describing every distinct world-element you can identify. "
    "ABSOLUTE RULES:\n"
    "1. Output ONLY a single JSON object. No prose, no preamble.\n"
    "2. Shape: {\"suggestions\": [ {...}, {...} ]}.\n"
    "3. Each suggestion MUST have: kind, title, summary, fields.\n"
    "4. `kind` is one of: lore, npc, location, quest, faction, creature, item, weapon.\n"
    "5. `summary` is 1-3 paragraphs drawn directly from the chunk.\n"
    "6. `fields` is a JSON object with kind-specific structured data:\n"
    "   npc.fields: {is_major: bool, role: string, species_or_kin: string,"
    "   faction: string|null, magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\","
    "   home_location: string|null, notable_items: [string], aliases: [string]}\n"
    "   location.fields: {location_type: \"city\"|\"town\"|\"village\"|\"tavern\"|\"keep\"|"
    "   \"ruin\"|\"forest\"|\"road\"|\"chamber\"|\"mountain\"|\"waterway\"|\"shrine\"|"
    "   \"battlefield\"|\"other\", map_region: string|null, description: string,"
    "   parent_location: string|null, notable_npcs: [string],"
    "   magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\"}\n"
    "   lore.fields: {category: \"magic-source\"|\"history\"|\"cosmology\"|\"culture\"|"
    "   \"prophecy\"|\"language\"|\"other\", magic_source_kind: \"face_of_aurae\"|"
    "   \"face_of_mortiscure\"|null, magical_alignment: \"aurae\"|\"mortiscure\"|"
    "   \"both\"|\"none\", associated_effects: [string]}\n"
    "   faction.fields: {allegiance: string, seat_of_power: string|null,"
    "   notable_members: [string], magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\"}\n"
    "   quest.fields: {hook: string, objectives: [string], rewards: [string],"
    "   related_npcs: [string], related_locations: [string]}\n"
    "   creature.fields: {challenge_band: \"trivial\"|\"low\"|\"mid\"|\"high\"|\"apex\","
    "   abilities: [string], habitat: string, magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\"}\n"
    "   item|weapon.fields: {rarity: \"common\"|\"uncommon\"|\"rare\"|\"legendary\"|\"artifact\","
    "   bearer: string|null, magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\","
    "   effect: string}\n\n"
    "HEURISTICS: Mark NPCs `is_major: true` only when pivotal. Use the explicit "
    "phrases 'Face of Aurae' / 'Face of Mortiscure' to populate magic_source_kind. "
    "Never invent stats. If chunk doesn't say it, leave field empty (null / [] / \"\")."
)


def _log(msg: str, end: str = "\n", flush: bool = True) -> None:
    """Dual-write to stdout (so `tail -f` works) AND to /var/log/tablegnostic/reseed.log."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(msg + end)
    except Exception:
        pass
    print(msg, end=end, flush=flush)


async def _call_claude(filename: str, heading: str, body: str) -> list:
    if not EMERGENT_LLM_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY not set in env")
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    user_msg = (
        f"# Source: {filename}\n# Chunk: {heading}\n\n"
        f"--- CHUNK BODY START ---\n{body}\n--- CHUNK BODY END ---\n\n"
        f"Return ONLY the JSON object per the system prompt rules."
    )
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"eve-reseed-v46-{filename[:14]}-{heading[:12]}",
        system_message=SYSTEM_PROMPT,
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    raw = await chat.send_message(UserMessage(text=user_msg))
    cleaned = (raw or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        obj = json.loads(cleaned)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            return []
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return []
    sugs = obj.get("suggestions", []) if isinstance(obj, dict) else []
    return [s for s in sugs if isinstance(s, dict)
            and s.get("kind") in NODE_KINDS | CUSTOM_KINDS]


async def _call_claude_retry(filename: str, heading: str, body: str) -> list:
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await _call_claude(filename, heading, body)
        except Exception as e:
            last_err = e
            if attempt == MAX_RETRIES:
                break
            sleep_s = BASE_BACKOFF_S * (2 ** (attempt - 1))
            _log(f"\n      retry {attempt}/{MAX_RETRIES - 1} in "
                 f"{sleep_s:.0f}s ({str(e)[:80]})", end="")
            await asyncio.sleep(sleep_s)
    assert last_err is not None
    raise last_err


def _chunk_text(text: str) -> list:
    if len(text) <= CHUNK_SIZE_CHARS:
        return [(1, text)]
    chunks = []
    cursor = 0
    idx = 1
    while cursor < len(text):
        end = min(cursor + CHUNK_SIZE_CHARS, len(text))
        if end < len(text):
            for marker in ("\n--- PAGE ", "\n\n", "\n"):
                hit = text.rfind(marker, cursor + CHUNK_SIZE_CHARS - 1500, end)
                if hit > 0:
                    end = hit
                    break
        chunk = text[cursor:end].strip()
        if chunk:
            chunks.append((idx, chunk))
            idx += 1
        cursor = end - CHUNK_OVERLAP_CHARS if end < len(text) else end
    return chunks


# -------- Persistence --------

async def _persist_one(s: dict, source_tag: str, chunk_no: int,
                       admin: dict) -> dict:
    """Insert a single suggestion immediately. Returns metadata for stub creation."""
    kind = s["kind"]
    fields = dict(s.get("fields") or {})
    fields.update({
        "source_ref": s.get("source_ref"),
        "llm_extracted": True,
        "script_run_id": SCRIPT_RUN_ID,
        "source_tag": source_tag,
        "chunk_no": chunk_no,
    })
    title = (s.get("title") or "Untitled")[:160]
    tags = [SEED_TAG, source_tag, f"kind-{kind}",
            f"chunk-{chunk_no:02d}"]
    if kind == "npc" and fields.get("is_major"):
        tags.append("major-npc")
    if kind == "lore" and fields.get("magic_source_kind"):
        tags.append(fields["magic_source_kind"])
        tags.append("magic-source")
    if kind == "location" and fields.get("location_type"):
        tags.append(f"loc-{fields['location_type']}")

    if kind in NODE_KINDS:
        node = {
            "id": new_id(),
            "campaign_id": MAIDEN_CID,
            "type": kind,
            "title": title,
            "content": (s.get("summary") or "")[:8000],
            "tags": tags,
            "visibility": "gm_only",
            "revealed_to": [],
            "links": [],
            "fields": fields,
            "created_at": now_iso(),
        }
        await db.nodes.insert_one(node)
        return {"kind": kind, "node_id": node["id"], "title": title,
                "is_major": bool(fields.get("is_major")),
                "fields": fields}
    if kind in CUSTOM_KINDS:
        custom = {
            "id": new_id(),
            "campaign_id": MAIDEN_CID,
            "kind": kind,
            "title": title,
            "summary": (s.get("summary") or "")[:4000],
            "fields": fields,
            "tags": tags + ["llm-extracted"],
            "created_at": now_iso(),
        }
        await db.custom_attributes.insert_one(custom)
        return {"kind": kind, "custom_id": custom["id"], "title": title}
    return {"kind": kind, "skipped": True}


async def _create_besm_stub_for_major_npc(node_id: str, npc: dict,
                                          admin: dict) -> str | None:
    title = npc["title"]
    fields = npc.get("fields") or {}
    existing = await db.characters.find_one(
        {"campaign_id": MAIDEN_CID, "name": title,
         "tags": "evereantha-major-npc-stub-v3"},
        {"_id": 0, "id": 1},
    )
    if existing:
        return existing["id"]
    ch_id = new_id()
    align = (fields.get("magical_alignment") or "none").lower()
    role = fields.get("role") or "neutral"
    species = fields.get("species_or_kin") or "human"
    home = fields.get("home_location") or ""
    faction = fields.get("faction") or ""
    concept = (
        f"{title} — {species} {role} ({align} alignment). "
        f"From {home or 'unknown origin'}{', allied with ' + faction if faction else ''}. "
        "Stub sheet auto-generated from the Evereantha bible re-ingest."
    )
    base = {"body": 6, "mind": 6, "soul": 6}
    if "villain" in role.lower() or fields.get("is_major"):
        base = {"body": 8, "mind": 7, "soul": 8}
    if align in {"mortiscure", "both"}:
        base["soul"] = max(base["soul"], 8)
    char = {
        "id": ch_id, "campaign_id": MAIDEN_CID,
        "owner_id": admin["id"], "owner_name": admin.get("name") or "Loremaster",
        "name": title, "concept": concept,
        "stats": base, "attributes": [], "skills": [], "defects": [],
        "derived": {
            "acv": base["body"] + base["mind"] + base["soul"],
            "dcv": base["body"] + base["mind"] + base["soul"] - 2,
            "hp": base["body"] * 5 + base["soul"] * 5,
            "ep": base["mind"] * 5 + base["soul"] * 5,
            "dmgmult": max(1, base["body"] // 4),
        },
        "power_packs": [], "power_bundles": [], "companion_owners": [],
        "size": "medium", "power_level": 1, "total_points": 200,
        "spent": {"total_spent": sum(base.values()) * 2, "by_kind": {}},
        "folio": {"inventory_state": {
            "items": [], "equipped": {}, "attuned_ids": [], "readied_ids": [],
        }},
        "notes": (f"## Source\n\nAuto-generated stub for the Evereantha bible "
                  f"major NPC **{title}**.\n\n## Magical alignment\n\n`{align}`\n\n"
                  f"## Linked codex node\n\n`{node_id}`"),
        "token_color": "#8b6f4e",
        "tags": ["evereantha-major-npc-stub-v3", f"align-{align}",
                 f"role-{role.lower().replace(' ', '-')}",
                 f"script-run-{SCRIPT_RUN_ID[:8]}"],
        "published": False, "linked_node_id": node_id,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.characters.insert_one(char)
    await db.nodes.update_one(
        {"id": node_id},
        {"$set": {"fields.linked_character_id": ch_id}},
    )
    return ch_id


async def _checkpoint(source_tag: str, chunk_no: int, status: str,
                      meta: dict | None = None) -> None:
    """Upsert chunk progress. status ∈ {ok, fail, in_progress}."""
    await db[CHECKPOINT_COL].update_one(
        {"source_tag": source_tag, "chunk_no": chunk_no},
        {"$set": {
            "status": status, "updated_at": now_iso(),
            "script_run_id": SCRIPT_RUN_ID,
            **(meta or {}),
        }, "$setOnInsert": {"created_at": now_iso()}},
        upsert=True,
    )


async def _completed_chunks(source_tag: str) -> set:
    rows = await db[CHECKPOINT_COL].find(
        {"source_tag": source_tag, "status": "ok"},
        {"_id": 0, "chunk_no": 1},
    ).to_list(2000)
    return {r["chunk_no"] for r in rows}


# -------- Main --------

async def main(fresh: bool) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    Path("/var/cache/tablegnostic").mkdir(parents=True, exist_ok=True)

    admin = await db.users.find_one({"email": ADMIN_EMAIL},
                                    {"_id": 0, "id": 1, "name": 1})
    if not admin:
        _log(f"FATAL: admin '{ADMIN_EMAIL}' not seeded.")
        return

    if fresh:
        _log("--fresh flag set: wiping prior v3 rows + checkpoints.")
        n = 0
        c = 0
        for tag in [SEED_TAG, *LEGACY_SEED_TAGS]:
            n += (await db.nodes.delete_many(
                {"campaign_id": MAIDEN_CID, "tags": tag})).deleted_count
            c += (await db.custom_attributes.delete_many(
                {"campaign_id": MAIDEN_CID, "tags": tag})).deleted_count
        stubs = (await db.characters.delete_many({
            "campaign_id": MAIDEN_CID,
            "tags": "evereantha-major-npc-stub-v3",
        })).deleted_count
        cp = (await db[CHECKPOINT_COL].delete_many({})).deleted_count
        _log(f"  wiped {n} nodes + {c} customs + {stubs} stubs + {cp} checkpoints.")

    _log(f"\n[run-id {SCRIPT_RUN_ID}] starting at {now_iso()}")

    total_new = 0
    by_kind: dict = {}
    major_npc_results: list = []

    for source_tag, url, cache in SOURCES:
        p = Path(cache)
        if not p.exists() or p.stat().st_size < 1024:
            _log(f"\n  Downloading {source_tag} → {cache} …")
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.get(url)
                r.raise_for_status()
                p.write_bytes(r.content)
        raw = p.read_bytes()
        try:
            text = _parse_to_text(p.name, "application/pdf", raw)
        except Exception as e:
            _log(f"  ! parse failed for {source_tag}: {e}")
            continue
        chunks = _chunk_text(text)
        completed = await _completed_chunks(source_tag)
        _log(f"\n=== Source: {source_tag} — {len(text):,} chars → "
             f"{len(chunks)} chunk(s) — {len(completed)} already done ===")

        for chunk_no, chunk_body in chunks:
            heading = f"chunk-{chunk_no:02d}-of-{len(chunks):02d}"
            if chunk_no in completed:
                _log(f"  ✓ {heading} (resume — already persisted)")
                continue
            _log(f"  • {heading} ({len(chunk_body):,} chars) … ", end="")
            await _checkpoint(source_tag, chunk_no, "in_progress")
            try:
                sugs = await _call_claude_retry(p.name, heading, chunk_body)
                _log(f"{len(sugs)} suggestions")
            except Exception as e:
                _log(f"FAIL after retries: {str(e)[:120]}")
                await _checkpoint(source_tag, chunk_no, "fail",
                                  {"last_error": str(e)[:300]})
                continue
            persisted_here = 0
            for s in sugs:
                try:
                    r = await _persist_one(s, source_tag, chunk_no, admin)
                    k = r.get("kind", "?")
                    by_kind[k] = by_kind.get(k, 0) + 1
                    total_new += 1
                    persisted_here += 1
                    if k == "npc" and r.get("is_major") and r.get("node_id"):
                        cid = await _create_besm_stub_for_major_npc(
                            r["node_id"],
                            {"title": r["title"], "fields": r.get("fields") or {}},
                            admin,
                        )
                        if cid:
                            major_npc_results.append((r["title"], cid))
                except Exception as e:
                    _log(f"    ! skip suggestion ({s.get('kind')}): {e}")
            await _checkpoint(source_tag, chunk_no, "ok",
                              {"persisted_count": persisted_here,
                               "raw_suggestion_count": len(sugs)})
            await asyncio.sleep(INTER_CHUNK_DELAY_S)

    _log("\n=== RE-INGEST COMPLETE ===")
    _log(f"  This run persisted: {total_new} new rows")
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        _log(f"    {k:<12} {n}")
    _log(f"  Major NPCs with auto-stub sheets: {len(major_npc_results)}")
    for nm, cid in major_npc_results[:25]:
        _log(f"    - {nm} → {cid}")
    if len(major_npc_results) > 25:
        _log(f"    … and {len(major_npc_results) - 25} more")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true",
                    help="Wipe all v3 rows + checkpoints before starting.")
    args = ap.parse_args()
    asyncio.run(main(fresh=args.fresh))
