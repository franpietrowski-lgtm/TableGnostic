"""V6.25.40 — Seed initial public roadmap items.

User asked the landing page Roadmap section to be dynamic and
admin-curated. Seed with the current backlog so it ships non-empty.
Idempotent — wipes existing seeds and re-creates.
"""
import asyncio

from core.db import db, new_id, now_iso


ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"


ITEMS = [
    # NOW
    {"status": "now", "order": 1, "title": "Admin Moderation Console",
     "body_md": "App-wide moderation surface for the super-admin: force-unpublish, "
                "take-down, flag queue, full audit trail. **Shipped V6.25.39.**\n\n"
                "Backed by `db.admin_actions` so every action is recorded with "
                "actor, target, and reason.", "eta": "Live"},
    {"status": "now", "order": 2, "title": "TableGnostic Gazette",
     "body_md": "Old-timey newspaper for every campaign. LLM-drafted articles from "
                "session events, GM curates and presses the issue, public readers "
                "land at `/discover/{slug}/gazette`.\n\n"
                "Includes the **mer der hoh bohs** box-score leaderboard.",
     "eta": "Live"},
    # NEXT
    {"status": "next", "order": 1, "title": "Strict Permission Gating",
     "body_md": "Players submit Codex / Genesis / inventory edits into a "
                "**GM approval queue**. No more silent character changes — the GM "
                "sees every diff before it lands.\n\n"
                "Critical for legal-compliance dispute resolution at long-running "
                "tables.", "eta": "Q1"},
    {"status": "next", "order": 2, "title": "Cypher ↔ BESM auto-converter cost balance",
     "body_md": "Cross-system conversion that **respects each system's point math** "
                "instead of a 1:1 token swap. Lets a player port a BESM character "
                "into a Cypher game with correct Edge / Pool budgets.", "eta": "Q1"},
    {"status": "next", "order": 3, "title": "Concept Forge — BESM 4E quiz polish + Codex import",
     "body_md": "Already live (V6.25.37) — adding the **BESM-quiz suggestion chips** "
                "and **Codex Import** picker so an LLM-generated concept can pull "
                "from the campaign's existing entity graph. Ongoing tightening.",
     "eta": "Live → polish"},
    # LATER
    {"status": "later", "order": 1, "title": "Marketplace V2 — Stripe Connect payouts",
     "body_md": "Homebrew creators get **paid**. Stripe Connect (Standard) routing, "
                "10% platform cut, automatic license-attestation gating on listing "
                "creation.", "eta": "Q2"},
    {"status": "later", "order": 2, "title": "Companion mobile app",
     "body_md": "iOS + Android companion for in-table use: voice push-to-talk, dice "
                "macros, character-aware quick-rolls, codex search.", "eta": "Q3"},
    {"status": "later", "order": 3, "title": "Resend issue digests",
     "body_md": "When the GM presses a gazette issue, every seated player gets an "
                "email with the masthead + link. Drives between-session "
                "engagement.", "eta": "Q2"},
    # SHIPPED (highlight wins to build credibility)
    {"status": "shipped", "order": 1, "title": "Voice push-to-talk v1",
     "body_md": "In-character voice lines transcribed via Whisper STT and fed into "
                "the LLM session-recap pipeline. **V6.25.36.**", "eta": "—"},
    {"status": "shipped", "order": 2, "title": "Public Discover showcase",
     "body_md": "SEO-indexed `/discover/{slug}` pages for any campaign the GM "
                "publishes. **V6.25.37–38.**", "eta": "—"},
]


async def main() -> None:
    admin = await db.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "id": 1})
    if not admin:
        print(f"FATAL: admin '{ADMIN_EMAIL}' not seeded.")
        return
    # Wipe seed-tagged items, then recreate.
    r = await db.roadmap_items.delete_many({"created_by": "v62540_seed"})
    print(f"Wiped {r.deleted_count} previously-seeded items.")
    for item in ITEMS:
        doc = {
            "id": new_id(),
            "title": item["title"],
            "body_md": item["body_md"],
            "status": item["status"],
            "eta": item.get("eta", ""),
            "order": item.get("order", 0),
            "public": True,
            "created_at": now_iso(),
            "created_by": "v62540_seed",
            "updated_at": now_iso(),
        }
        await db.roadmap_items.insert_one(doc)
    print(f"Seeded {len(ITEMS)} roadmap items "
          f"({sum(1 for i in ITEMS if i['status']=='now')} now, "
          f"{sum(1 for i in ITEMS if i['status']=='next')} next, "
          f"{sum(1 for i in ITEMS if i['status']=='later')} later, "
          f"{sum(1 for i in ITEMS if i['status']=='shipped')} shipped).")


if __name__ == "__main__":
    asyncio.run(main())
