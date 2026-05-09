"""V6.25.37 — Mark all existing campaigns as public.

User asked, post super-admin wipe, that every existing campaign in the
preview pod be flipped to `visibility="public"` so the test catalogue
remains discoverable from `/app/discover` (open-seat) and so any of
them can later be cherry-picked for `discover_published=true` when
the GM wants the SEO showcase at `/discover/{slug}`.

This is intentionally NOT idempotent in the sense of pruning anything
— it ONLY flips visibility="public" if it isn't already, leaving
audit metadata in place.
"""
import asyncio

from core.db import db


async def main() -> None:
    cur = db.campaigns.find(
        {"visibility": {"$ne": "public"}},
        {"_id": 0, "id": 1, "name": 1, "visibility": 1},
    )
    flipped = 0
    async for c in cur:
        await db.campaigns.update_one(
            {"id": c["id"]},
            {"$set": {"visibility": "public"}},
        )
        flipped += 1
        print(f"  • flipped {c.get('name')!r} ({c['id']}) → public")

    total = await db.campaigns.count_documents({})
    public = await db.campaigns.count_documents({"visibility": "public"})
    print(f"\nDone. Flipped {flipped}. Total campaigns: {total}. Public: {public}.")


if __name__ == "__main__":
    asyncio.run(main())
