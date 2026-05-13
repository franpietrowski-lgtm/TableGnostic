"""V6.25.43 — Evereantha lore re-seed (4 new PDFs).

Wipes the prior `evereantha-bible-llm-seed*` rows and re-ingests four
sources with a bespoke Claude prompt that elicits the structured fields
TableGnostic's downstream surfaces actually consume:

  - `is_major: bool`           — major/recurring NPC ⇒ also gets a stub
                                  BESM character sheet auto-created
  - `location_type: str`       — city / town / tavern / ruin / forest /
                                  road / chamber / mountain / waterway /
                                  other — used by the world-map pin layer
  - `map_region: str | null`   — coarse world-map region key
  - `magical_alignment`        — aurae / mortiscure / both / none —
                                  routes lore→magic-system surface
  - `magic_source_kind`        — "face_of_aurae" | "face_of_mortiscure"
                                  for the Primary Source rows themselves
                                  (NOT a pantheon — these are weighted
                                  guideposts that bend effects)

The script keeps the existing seeded characters (Eli, Vex, Lyra, Apo)
UNTOUCHED — it only adds new `evereantha-bible-llm-seed-v3` rows.

Run with the env wrapper script:
    ./tmp/run_reingest_v3.sh   (or)
    set -a; . /app/backend/.env; set +a
    PYTHONPATH=/app/backend python scripts/v62543_evereantha_reseed.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

import httpx

from core.db import db, new_id, now_iso
from routes.ingest import _parse_to_text


MAIDEN_CID = "af461ae004364002932f93c5b71cd483"
ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
SEED_TAG = "evereantha-bible-llm-seed-v3"
LEGACY_SEED_TAGS = ["evereantha-bible-llm-seed", "evereantha-bible-llm-seed-v2"]

# V6.25.43 — four canonical sources for the Evereantha campaign world.
SOURCES = [
    ("bible-v3",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/hggzg3mj_Evereantha_The_Rites_Of_All_Campaign_Bible.pdf",
     "/tmp/eve_bible_v3.pdf"),
    ("supplement-v3",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/5m3s2m3t_Evereantha_Rites_to_Suppliment_v2.pdf",
     "/tmp/eve_suppl_v3.pdf"),
    ("evereantha-extras",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/k6nfo3sm_Evereantha%20e4f31179bbcf47369d26a715cfcf542e.pdf",
     "/tmp/eve_extras_v3.pdf"),
    ("artisans-tale",
     "https://customer-assets.emergentagent.com/job_rules-forge/artifacts/8b508ktb_artisans%20tale.pdf",
     "/tmp/artisans_tale.pdf"),
]

NODE_KINDS = {"lore", "npc", "location", "quest", "faction", "creature"}
CUSTOM_KINDS = {"attribute", "power_pack", "power_bundle",
                "item", "weapon", "skill", "house_rule"}

# Chunking + retry knobs (kept conservative — LiteLLM proxy rejects ~5%
# of chunks deterministically on content-policy when they include large
# tables of names/proper-nouns; that's why retries help but we cap at 4).
CHUNK_SIZE_CHARS = 4200
CHUNK_OVERLAP_CHARS = 350
MAX_RETRIES = 4
BASE_BACKOFF_S = 6.0
INTER_CHUNK_DELAY_S = 2.5

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")


# ----------------------------------------------------------------------
# Bespoke Claude prompt — far more specific than the generic ingest one.
# ----------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an extraction engine for the TableGnostic RPG platform. "
    "Given a CHUNK of the Evereantha campaign bible, you return JSON "
    "describing every distinct world-element you can identify. "
    "ABSOLUTE RULES:\n"
    "1. Output ONLY a single JSON object. No prose, no preamble.\n"
    "2. Shape: {\"suggestions\": [ {...}, {...} ]}.\n"
    "3. Each suggestion MUST have: kind, title, summary, fields.\n"
    "4. `kind` is one of: lore, npc, location, quest, faction, creature, item, weapon.\n"
    "5. `summary` is 1-3 paragraphs of clean prose drawn directly from "
    "the chunk — no invention. Quote-paraphrase, do not editorialise.\n"
    "6. `fields` is a JSON object with kind-specific structured data "
    "(see the per-kind schema below).\n\n"
    "PER-KIND fields schema:\n\n"
    "  npc.fields = {\n"
    "    is_major: bool,            // recurring / pivotal to the plot\n"
    "    role: string,              // \"ally\", \"villain\", \"neutral\", \"mentor\", \"rival\", \"oracle\", \"merchant\", ...\n"
    "    species_or_kin: string,    // \"human\", \"elf\", \"shadowfell-cursed\", ...\n"
    "    faction: string|null,      // which faction they serve (free text)\n"
    "    magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\",\n"
    "    home_location: string|null,// best-known location title\n"
    "    notable_items: [string],   // weapons / artefacts they carry\n"
    "    aliases: [string]\n"
    "  }\n\n"
    "  location.fields = {\n"
    "    location_type: \"city\"|\"town\"|\"village\"|\"tavern\"|\"keep\"|\"ruin\"|\"forest\"|\"road\"|\"chamber\"|\"mountain\"|\"waterway\"|\"shrine\"|\"battlefield\"|\"other\",\n"
    "    map_region: string|null,   // \"north\", \"east-coast\", \"forsaken-marches\", ...\n"
    "    description: string,       // sensory description (sight/sound/smell), >=2 sentences\n"
    "    parent_location: string|null, // title of containing region/city if applicable\n"
    "    notable_npcs: [string],    // titles of NPCs found here\n"
    "    magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\"\n"
    "  }\n\n"
    "  lore.fields = {\n"
    "    category: \"magic-source\"|\"history\"|\"cosmology\"|\"culture\"|\"prophecy\"|\"language\"|\"other\",\n"
    "    magic_source_kind: \"face_of_aurae\"|\"face_of_mortiscure\"|null,\n"
    "      // Faces of Aurae & Faces of Mortiscure are PRIMARY SOURCES of\n"
    "      // magical power and intent in Evereantha — NOT a pantheon.\n"
    "      // They are weighted guide-posts whose effects can be applied\n"
    "      // by characters, items, weapons, or the environment.\n"
    "    magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\",\n"
    "    associated_effects: [string]   // short bullet phrasing of what tilts when this source is invoked\n"
    "  }\n\n"
    "  faction.fields = {\n"
    "    allegiance: string,        // who/what they serve\n"
    "    seat_of_power: string|null,// title of a location\n"
    "    notable_members: [string],\n"
    "    magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\"\n"
    "  }\n\n"
    "  quest.fields = {\n"
    "    hook: string,              // one-line GM hook\n"
    "    objectives: [string],\n"
    "    rewards: [string],\n"
    "    related_npcs: [string],\n"
    "    related_locations: [string]\n"
    "  }\n\n"
    "  creature.fields = {\n"
    "    challenge_band: \"trivial\"|\"low\"|\"mid\"|\"high\"|\"apex\",\n"
    "    abilities: [string],\n"
    "    habitat: string,           // location-type words\n"
    "    magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\"\n"
    "  }\n\n"
    "  item.fields / weapon.fields = {\n"
    "    rarity: \"common\"|\"uncommon\"|\"rare\"|\"legendary\"|\"artifact\",\n"
    "    bearer: string|null,       // current owner if named\n"
    "    magical_alignment: \"aurae\"|\"mortiscure\"|\"both\"|\"none\",\n"
    "    effect: string             // mechanical or narrative effect\n"
    "  }\n\n"
    "EXTRACTION HEURISTICS:\n"
    " - Mark NPCs `is_major: true` only when the chunk strongly implies "
    "they are pivotal (named multiple times, given backstory, drive "
    "plot, or are listed in a primary cast list).\n"
    " - Use the explicit phrases 'Face of Aurae' / 'Faces of Aurae' / "
    "'Face of Mortiscure' / 'Faces of Mortiscure' to populate "
    "magic_source_kind on `lore` entries.\n"
    " - Locations that appear ONLY as a passing reference still get an "
    "entry (low priority) but with sparse fields. Prefer fewer rich "
    "entries over many thin ones if the chunk is descriptive.\n"
    " - Never invent stats. If the chunk doesn't say it, leave the "
    "field empty (null / [] / \"\").\n"
)


async def _call_claude(filename: str, heading: str, body: str) -> list:
    """One Claude call per chunk, with the bespoke Evereantha prompt."""
    if not EMERGENT_LLM_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY not set in env")
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    user_msg = (
        f"# Source: {filename}\n"
        f"# Chunk: {heading}\n\n"
        f"--- CHUNK BODY START ---\n{body}\n--- CHUNK BODY END ---\n\n"
        f"Return ONLY the JSON object per the system prompt rules."
    )
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"eve-reseed-{filename[:18]}-{heading[:12]}",
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
    # Light kind validation.
    out = []
    for s in sugs:
        if not isinstance(s, dict):
            continue
        k = s.get("kind")
        if k not in NODE_KINDS and k not in CUSTOM_KINDS:
            continue
        out.append(s)
    return out


async def _call_claude_retry(filename: str, heading: str, body: str) -> list:
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await _call_claude(filename, heading, body)
        except Exception as e:  # noqa: BLE001
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


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------

async def _persist_node(s: dict, ingest_id: str, source_tag: str,
                        admin: dict) -> dict:
    kind = s["kind"]
    fields = dict(s.get("fields") or {})
    fields.update({
        "ingest_id": ingest_id,
        "source_ref": s.get("source_ref"),
        "llm_extracted": True,
    })
    title = (s.get("title") or "Untitled")[:160]
    tags = [SEED_TAG, source_tag, f"kind-{kind}"]
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
                "magic_source_kind": fields.get("magic_source_kind")}
    elif kind in CUSTOM_KINDS:
        custom = {
            "id": new_id(),
            "campaign_id": MAIDEN_CID,
            "kind": kind,
            "title": title,
            "summary": (s.get("summary") or "")[:4000],
            "fields": fields,
            "ingest_id": ingest_id,
            "source_ref": s.get("source_ref"),
            "tags": tags + ["llm-extracted"],
            "created_at": now_iso(),
        }
        await db.custom_attributes.insert_one(custom)
        return {"kind": kind, "custom_id": custom["id"], "title": title}
    return {"kind": kind, "skipped": True, "title": title}


async def _create_besm_stub_for_major_npc(node_id: str, npc: dict,
                                          admin: dict) -> str | None:
    """Auto-create a minimal BESM 4E character sheet for a major NPC and
    cross-link it to the source codex node so the Encounter Builder and
    Director's Console pick it up. The sheet is admin-owned, unpublished,
    and tagged so a GM can review / delete before play.
    """
    title = npc["title"]
    fields = npc.get("fields") or {}
    # Avoid duplicates if rerun.
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
        "Stub sheet auto-generated from the Evereantha bible re-ingest; "
        "GM should refine stats before play."
    )

    # Minimal BESM scaffolding mirroring Eli's shape (stats/attributes/derived).
    base_stats = {"body": 6, "mind": 6, "soul": 6}
    if "villain" in role.lower() or fields.get("is_major"):
        base_stats = {"body": 8, "mind": 7, "soul": 8}
    if align in {"mortiscure", "both"}:
        base_stats["soul"] = max(base_stats["soul"], 8)

    char = {
        "id": ch_id,
        "campaign_id": MAIDEN_CID,
        "owner_id": admin["id"],
        "owner_name": admin.get("name") or "Loremaster",
        "name": title,
        "concept": concept,
        "stats": base_stats,
        "attributes": [],
        "skills": [],
        "defects": [],
        "derived": {
            "acv": base_stats["body"] + base_stats["mind"] + base_stats["soul"],
            "dcv": base_stats["body"] + base_stats["mind"] + base_stats["soul"] - 2,
            "hp": base_stats["body"] * 5 + base_stats["soul"] * 5,
            "ep": base_stats["mind"] * 5 + base_stats["soul"] * 5,
            "dmgmult": max(1, base_stats["body"] // 4),
        },
        "power_packs": [],
        "power_bundles": [],
        "companion_owners": [],
        "size": "medium",
        "power_level": 1,
        "total_points": 200,
        "spent": {"total_spent": (sum(base_stats.values())) * 2, "by_kind": {}},
        "folio": {"inventory_state": {
            "items": [], "equipped": {}, "attuned_ids": [], "readied_ids": [],
        }},
        "notes": (f"## Source\n\nAuto-generated stub for the Evereantha "
                  f"bible major NPC **{title}**.\n\n## Magical alignment\n\n"
                  f"`{align}` — adjust if the source text reveals nuance.\n\n"
                  f"## Linked codex node\n\n`{node_id}`"),
        "token_color": "#8b6f4e",
        "tags": ["evereantha-major-npc-stub-v3", f"align-{align}",
                 f"role-{role.lower().replace(' ', '-')}"],
        "published": False,
        "linked_node_id": node_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.characters.insert_one(char)
    # Cross-link the node back to the character.
    await db.nodes.update_one(
        {"id": node_id},
        {"$set": {"fields.linked_character_id": ch_id}},
    )
    return ch_id


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

async def main() -> None:
    admin = await db.users.find_one({"email": ADMIN_EMAIL},
                                    {"_id": 0, "id": 1, "name": 1})
    if not admin:
        print(f"FATAL: admin '{ADMIN_EMAIL}' not seeded.")
        return

    # Wipe v3 (idempotent) AND any legacy v1/v2 nodes from earlier runs.
    deleted_n = 0
    deleted_c = 0
    deleted_stubs = 0
    for tag in [SEED_TAG, *LEGACY_SEED_TAGS]:
        deleted_n += (await db.nodes.delete_many({
            "campaign_id": MAIDEN_CID, "tags": tag,
        })).deleted_count
        deleted_c += (await db.custom_attributes.delete_many({
            "campaign_id": MAIDEN_CID, "tags": tag,
        })).deleted_count
    deleted_stubs = (await db.characters.delete_many({
        "campaign_id": MAIDEN_CID,
        "tags": "evereantha-major-npc-stub-v3",
    })).deleted_count
    print(f"Wiped {deleted_n} prior seed nodes + {deleted_c} custom rows "
          f"+ {deleted_stubs} prior major-NPC stub sheets.")

    total_persisted = 0
    by_kind: dict = {}
    major_npc_results: list = []

    for source_tag, url, cache in SOURCES:
        p = Path(cache)
        if not p.exists() or p.stat().st_size < 1024:
            print(f"  Downloading {source_tag} → {cache} …")
            async with httpx.AsyncClient(timeout=90) as c:
                r = await c.get(url)
                r.raise_for_status()
                p.write_bytes(r.content)
        raw = p.read_bytes()
        try:
            text = _parse_to_text(p.name, "application/pdf", raw)
        except Exception as e:
            print(f"  ! parse failed for {source_tag}: {e}")
            continue
        chunks = _chunk_text(text)
        print(f"\n=== Source: {source_tag} — {len(raw):,} bytes "
              f"→ {len(text):,} chars → {len(chunks)} chunk(s) ===")

        ingest_id = new_id()
        all_sugs: list = []
        for chunk_no, chunk_body in chunks:
            heading = f"chunk-{chunk_no:02d}-of-{len(chunks):02d}"
            print(f"  • {heading} ({len(chunk_body):,} chars) … ",
                  end="", flush=True)
            try:
                sugs = await _call_claude_retry(p.name, heading, chunk_body)
                print(f"{len(sugs)} suggestions")
                all_sugs.extend(sugs)
            except Exception as e:
                print(f"FAIL after retries: {str(e)[:120]}")
                continue
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
            "script_version": "v6.25.43",
        })

        for s in all_sugs:
            try:
                r = await _persist_node(s, ingest_id, source_tag, admin)
                k = r.get("kind", "?")
                by_kind[k] = by_kind.get(k, 0) + 1
                total_persisted += 1
                if k == "npc" and r.get("is_major") and r.get("node_id"):
                    full = await db.nodes.find_one({"id": r["node_id"]},
                                                   {"_id": 0})
                    if full:
                        cid = await _create_besm_stub_for_major_npc(
                            r["node_id"], full, admin,
                        )
                        if cid:
                            major_npc_results.append((r["title"], cid))
            except Exception as e:
                print(f"    ! skip suggestion ({s.get('kind')}): {e}")

    print("\n=== RE-INGEST COMPLETE ===")
    print(f"Total persisted: {total_persisted}")
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"  {k:<12} {n}")
    print(f"\nMajor NPCs with auto-stub BESM sheets: {len(major_npc_results)}")
    for nm, cid in major_npc_results[:25]:
        print(f"  - {nm} → {cid}")
    if len(major_npc_results) > 25:
        print(f"  … and {len(major_npc_results) - 25} more")


if __name__ == "__main__":
    asyncio.run(main())
