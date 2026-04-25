"""Startup-time DB seeding & migrations.

Runs on every backend boot:
- ensures all collection indexes exist
- backfills legacy 'user' role accounts → 'gm'
- seeds the three demo accounts (admin / gm / player) with authoritative
  password+role pinning every boot, so manual edits don't drift
- backfills invite tokens on legacy campaigns

Kept here (not in routes/) because nothing here is HTTP-facing; everything
runs in `app.on_event("startup")`.
"""
import secrets

from .db import db, new_id, now_iso
from .security import hash_password, verify_password


async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.campaigns.create_index("id", unique=True)
    await db.characters.create_index("id", unique=True)
    await db.characters.create_index("campaign_id")
    await db.nodes.create_index("id", unique=True)
    await db.nodes.create_index("campaign_id")
    await db.edges.create_index("campaign_id")
    await db.sessions.create_index("id", unique=True)
    await db.sessions.create_index("campaign_id")
    await db.chat_logs.create_index("session_id")
    await db.dice_rolls.create_index("session_id")
    await db.initiative.create_index("session_id")
    await db.effects.create_index("session_id")
    await db.custom_attributes.create_index("campaign_id")
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)


async def seed_user(email: str, password: str, name: str, role: str):
    existing = await db.users.find_one({"email": email})
    if existing is None:
        await db.users.insert_one({
            "id": new_id(), "email": email,
            "password_hash": hash_password(password),
            "name": name, "role": role, "created_at": now_iso(),
        })
        return
    # Seed accounts are authoritative — keep password and role in sync each boot.
    update = {"role": role, "name": name}
    if not verify_password(password, existing.get("password_hash", "")):
        update["password_hash"] = hash_password(password)
    await db.users.update_one({"email": email}, {"$set": update})


async def run_startup():
    await ensure_indexes()
    # Legacy "user" role → "gm" so existing creators keep working.
    await db.users.update_many({"role": "user"}, {"$set": {"role": "gm"}})
    await seed_user("admin@tablegnostic.com", "admin123", "Admin", "admin")
    await seed_user("gm@tablegnostic.com", "gm123456", "Game Master", "gm")
    await seed_user("player@tablegnostic.com", "player12345", "Player", "player")
    # Backfill invite tokens for legacy campaigns.
    async for c in db.campaigns.find({"invite_token": {"$exists": False}}, {"_id": 0, "id": 1}):
        await db.campaigns.update_one(
            {"id": c["id"]},
            {"$set": {"invite_token": secrets.token_urlsafe(16)}},
        )
