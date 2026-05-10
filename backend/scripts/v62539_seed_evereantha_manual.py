"""V6.25.39 — DETERMINISTIC seed of Evereantha bible content.

Pure structural parse — no LLM, zero key cost. Walks the HTML headings
and creates one Knowledge Web codex node per section. Sections are
typed by name-pattern (NPCs / locations / lore / factions / quests /
artifacts) and tagged so the GM admin can curate later.

Run:
    cd /app/backend && set -a && source .env && set +a && \
        PYTHONPATH=/app/backend python scripts/v62539_seed_evereantha_manual.py
"""
import asyncio
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

from core.db import db, new_id, now_iso


MAIDEN_CID = "af461ae004364002932f93c5b71cd483"
ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"
BIBLE_PATH = Path("/tmp/evereantha_bible.html")


# Heading-name → codex node type. Matches case-insensitive substring.
TYPE_RULES = [
    # Quests (acts of the campaign)
    (re.compile(r"^act\s+[ivx]+\b", re.I), "quest"),
    (re.compile(r"^digestible module beats", re.I), "quest"),
    (re.compile(r"^module training notes", re.I), "quest"),
    (re.compile(r"^adventure template", re.I), "quest"),
    (re.compile(r"^(act|five-act|master plot|public plot|true plot|hidden engine)", re.I), "quest"),
    # NPCs / characters
    (re.compile(r"(npc|deacon|deacons|roster|noble house|noble houses|order of|villains|antagonist|the maiden|the stranger|cabal|bbeg|ogas)", re.I), "npc"),
    # Locations / world geography
    (re.compile(r"(world map|aurea|vitae|singularity|continents?|temple|tor|nest|arena|locations? and travel|node expectation)", re.I), "location"),
    # Items / artifacts / loot
    (re.compile(r"(artifact|loot|reward|sheets?|sheet|printable)", re.I), "item"),
    # Factions  (sometimes overlaps with NPCs — try first)
    (re.compile(r"(faction|house|order|cabal|conclave|guild|alliance)", re.I), "faction"),
    # Magic / mechanics → lore
    (re.compile(r"(aurae|mortiscura|magic|face rank|connection|prohibited|time mechanic|timeline tracker|besm|implementation)", re.I), "lore"),
]


def _classify(heading: str, parent_h1: str) -> str:
    """Return the codex node type for a section."""
    # Faction-only sections need both heading AND parent-h1 to disambiguate.
    text = f"{parent_h1} :: {heading}"
    for pat, kind in TYPE_RULES:
        if pat.search(text):
            return kind
    return "lore"  # safe default


def _section_body(start, end) -> str:
    """Walk siblings from `start` until `end`, joining text content."""
    parts: list = []
    cur = start.next_sibling
    while cur is not None and cur is not end:
        if isinstance(cur, NavigableString):
            txt = str(cur).strip()
            if txt:
                parts.append(txt)
        else:
            txt = cur.get_text(" ", strip=True)
            if txt:
                parts.append(txt)
        cur = cur.next_sibling
    body = "\n\n".join(parts)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


async def main() -> None:
    camp = await db.campaigns.find_one({"id": MAIDEN_CID}, {"_id": 0})
    if not camp:
        print(f"FATAL: campaign '{MAIDEN_CID}' not found.")
        return
    admin = await db.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "id": 1, "name": 1})
    if not admin:
        print(f"FATAL: admin '{ADMIN_EMAIL}' not seeded.")
        return
    if camp.get("gm_id") != admin["id"]:
        print("WARN: campaign not yet owned by admin — run transfer script first.")

    if not BIBLE_PATH.exists():
        print(f"FATAL: bible not cached at {BIBLE_PATH} — re-fetch it first.")
        return
    raw = BIBLE_PATH.read_bytes()
    print(f"Bible cached: {len(raw):,} bytes")

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    # Idempotency: wipe previously-seeded bible nodes so re-running is clean.
    deleted = await db.nodes.delete_many({
        "campaign_id": MAIDEN_CID,
        "tags": {"$in": ["evereantha-bible-seed"]},
    })
    print(f"Wiped {deleted.deleted_count} previously seeded bible nodes.")

    # Walk h1/h2/h3 in document order; each becomes a section.
    headings = [h for h in soup.find_all(["h1", "h2", "h3"])
                  if h.get_text(strip=True)]
    print(f"Sections found: {len(headings)}")

    nodes_created: list = []
    skipped_short: int = 0
    skipped_frontmatter: int = 0

    current_h1 = ""
    for idx, h in enumerate(headings):
        title = h.get_text(" ", strip=True)
        if h.name == "h1":
            current_h1 = title

        # Skip pure structural headings.
        SKIP = {"front matter", "how to use this book", "table of contents",
                "design intent", "safety and table contract",
                "document version notes", "appendix - printable sheets"}
        if title.lower() in SKIP:
            skipped_frontmatter += 1
            continue

        # Find the body region = everything between this heading and the
        # next heading in document order.
        next_h = headings[idx + 1] if idx + 1 < len(headings) else None

        body = _section_body(h, next_h)
        if len(body) < 50:
            skipped_short += 1
            continue

        node_type = _classify(title, current_h1)
        # Cap body at 8000 chars per node (avoids ingesting a 60-paragraph
        # quest into a single record — keeps the codex grokable).
        body = body[:8000]

        # Bible-canonical h1 tags + section-level tags for filtering.
        tags = [
            "evereantha-bible-seed",
            f"part-{current_h1.lower().replace(' ', '-')}" if current_h1 else "part-untagged",
            f"type-{node_type}",
        ]
        # Detect act tag if heading mentions Act I-V.
        m = re.search(r"act\s+([ivx]+)", title, re.I)
        if m:
            tags.append(f"act-{m.group(1).lower()}")

        node = {
            "id": new_id(),
            "campaign_id": MAIDEN_CID,
            "type": node_type,
            "title": title[:160],
            "content": body,
            "tags": tags,
            "visibility": "gm_only",
            "revealed_to": [],
            "links": [],
            "fields": {
                "parent_part": current_h1,
                "source": "Evereantha — The Rites Of All — Campaign Bible (EXPANDED)",
                "source_kind": "campaign-bible",
                "seeded_at": now_iso(),
                "seeded_by_script": "v62539_seed_evereantha_manual.py",
            },
            "created_at": now_iso(),
        }
        await db.nodes.insert_one(node)
        nodes_created.append((node_type, title))

    # Summary.
    by_kind: dict = {}
    for k, _t in nodes_created:
        by_kind[k] = by_kind.get(k, 0) + 1

    print()
    print("=== SEED COMPLETE ===")
    print(f"Total nodes created: {len(nodes_created)}")
    print(f"Sections skipped (front-matter):  {skipped_frontmatter}")
    print(f"Sections skipped (body too short): {skipped_short}")
    print()
    for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"  {k:<10} {n}")
    print()
    print("Sample (first 12):")
    for k, t in nodes_created[:12]:
        print(f"  [{k:<10}] {t}")


if __name__ == "__main__":
    asyncio.run(main())
