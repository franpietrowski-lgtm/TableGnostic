"""V6.25.42 — LLM-driven re-ingest of the Evereantha bible + supplement.

Chunks each PDF into ~6k-char windows and fires one focused
`_call_claude_section` per chunk so we never blow the LiteLLM proxy
ceiling. Idempotent — wipes prior `evereantha-bible-llm-seed` nodes
before re-running.
"""
import asyncio
from pathlib import Path

import httpx

from core.db import db, new_id, now_iso
from routes.ingest import _parse_to_text, _call_claude_section


MAIDEN_CID = "af461ae004364002932f93c5b71cd483"
ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"

SOURCES = [
    ("bible-v2",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/wec1ch08_Evereantha_The_Rites_Of_All_Campaign_Bible.pdf",
     "/tmp/bible_v2.pdf"),
    ("supplement-v2",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/322lzd5s_Evereantha_Rites_to_Suppliment_v2.pdf",
     "/tmp/suppl_v2.pdf"),
]

NODE_KINDS = {"lore", "npc", "location", "quest", "faction", "creature"}
CUSTOM_KINDS = {"attribute", "power_pack", "power_bundle",
                "item", "weapon", "skill", "house_rule"}
SEED_TAG = "evereantha-bible-llm-seed"

# V6.25.42b — smaller chunks + exponential-backoff retries to dodge
# transient LiteLLM 502/BadGateway errors that plagued the prior run.
CHUNK_SIZE_CHARS = 4200
CHUNK_OVERLAP_CHARS = 350
MAX_RETRIES = 4
BASE_BACKOFF_S = 6.0          # 6, 12, 24, 48 seconds
INTER_CHUNK_DELAY_S = 2.5     # gentle cool-down between successful chunks


async def _call_claude_section_retry(filename: str, system_id: str,
                                     heading: str, body: str,
                                     bias_kind: str) -> list:
    """Wrap `_call_claude_section` with exponential-backoff retries.

    Retries any exception (covers LiteLLM 502 BadGateway / BadRequest /
    transient proxy hiccups) up to MAX_RETRIES times. Last failure is
    re-raised so the caller can record a `FAIL` against that chunk.
    """
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await _call_claude_section(
                filename, system_id, heading, body, bias_kind,
            )
        except Exception as e:  # noqa: BLE001 — broad on purpose
            last_err = e
            if attempt == MAX_RETRIES:
                break
            sleep_s = BASE_BACKOFF_S * (2 ** (attempt - 1))
            print(f"\n      retry {attempt}/{MAX_RETRIES - 1} in "
                  f"{sleep_s:.0f}s ({str(e)[:80]})", end="", flush=True)
            await asyncio.sleep(sleep_s)
    assert last_err is not None
    raise last_err


def _chunk_text(text: str) -> list:
    if len(text) <= CHUNK_SIZE_CHARS:
        return [(1, text)]
    chunks: list = []
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


async def _persist_suggestion(sugg: dict, ingest_id: str, source_tag: str) -> dict:
    kind = sugg["kind"]
    if kind in NODE_KINDS:
        node = {
            "id": new_id(),
            "campaign_id": MAIDEN_CID,
            "type": kind,
            "title": (sugg.get("title") or "Untitled")[:160],
            "content": (sugg.get("summary") or "")[:8000],
            "tags": [SEED_TAG, source_tag, f"phase-{sugg.get('atelier_phase', 4)}"],
            "visibility": "gm_only",
            "revealed_to": [],
            "links": [],
            "fields": {
                **(sugg.get("fields") or {}),
                "ingest_id": ingest_id,
                "source_ref": sugg.get("source_ref"),
                "atelier_phase": sugg.get("atelier_phase"),
                "llm_extracted": True,
            },
            "created_at": now_iso(),
        }
        await db.nodes.insert_one(node)
        return {"kind": kind, "node_id": node["id"], "title": node["title"]}
    elif kind in CUSTOM_KINDS:
        custom = {
            "id": new_id(),
            "campaign_id": MAIDEN_CID,
            "kind": kind,
            "title": (sugg.get("title") or "Untitled")[:160],
            "summary": (sugg.get("summary") or "")[:4000],
            "fields": sugg.get("fields") or {},
            "ingest_id": ingest_id,
            "source_ref": sugg.get("source_ref"),
            "tags": [SEED_TAG, source_tag, "llm-extracted"],
            "created_at": now_iso(),
        }
        await db.custom_attributes.insert_one(custom)
        return {"kind": kind, "custom_id": custom["id"], "title": custom["title"]}
    return {"kind": kind, "skipped": True, "title": sugg.get("title")}


async def main() -> None:
    admin = await db.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "id": 1, "name": 1})
    if not admin:
        print(f"FATAL: admin '{ADMIN_EMAIL}' not seeded.")
        return

    deleted_n = (await db.nodes.delete_many({
        "campaign_id": MAIDEN_CID, "tags": SEED_TAG,
    })).deleted_count
    deleted_c = (await db.custom_attributes.delete_many({
        "campaign_id": MAIDEN_CID, "tags": SEED_TAG,
    })).deleted_count
    print(f"Wiped {deleted_n} prior LLM-seed nodes + {deleted_c} custom rows.")

    total_persisted = 0
    by_kind: dict = {}

    for source_tag, url, cache in SOURCES:
        p = Path(cache)
        if not p.exists() or p.stat().st_size < 1024:
            print(f"  Downloading {source_tag} → {cache} …")
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.get(url)
                r.raise_for_status()
                p.write_bytes(r.content)
        raw = p.read_bytes()
        text = _parse_to_text(p.name, "application/pdf", raw)
        chunks = _chunk_text(text)
        print(f"\n=== Source: {source_tag} — {len(raw):,} bytes "
              f"→ {len(text):,} chars → {len(chunks)} chunk(s) ===")

        ingest_id = new_id()
        all_sugs: list = []

        for chunk_no, chunk_body in chunks:
            heading = f"chunk-{chunk_no:02d}-of-{len(chunks):02d}"
            print(f"  • {heading} ({len(chunk_body):,} chars) … ", end="", flush=True)
            try:
                sugs = await _call_claude_section_retry(
                    p.name, "besm-4e", heading, chunk_body, "lore",
                )
                print(f"{len(sugs)} suggestions")
                all_sugs.extend(sugs)
            except Exception as e:
                print(f"FAIL after retries: {str(e)[:100]}")
                continue
            # Cool-down between chunks so we don't trigger LiteLLM proxy rate limits.
            await asyncio.sleep(INTER_CHUNK_DELAY_S)

        await db.ingestions.insert_one({
            "id": ingest_id,
            "campaign_id": MAIDEN_CID,
            "filename": p.name,
            "content_type": "application/pdf",
            "byte_size": len(raw),
            "extracted_chars": len(text),
            "summary": f"Chunked LLM re-ingest of {source_tag} ({len(chunks)} chunks).",
            "suggestions": all_sugs,
            "status": "accepted",
            "created_at": now_iso(),
            "created_by": admin["id"],
            "auto_accepted_by_seed_script": True,
            "source_tag": source_tag,
            "chunk_count": len(chunks),
        })

        for s in all_sugs:
            try:
                r = await _persist_suggestion(s, ingest_id, source_tag)
                k = r.get("kind", "?")
                by_kind[k] = by_kind.get(k, 0) + 1
                total_persisted += 1
            except Exception as e:
                print(f"    ! skip suggestion ({s.get('kind')}): {e}")

    print("\n=== RE-INGEST COMPLETE ===")
    print(f"Total persisted: {total_persisted}")
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"  {k:<12} {n}")


if __name__ == "__main__":
    asyncio.run(main())
