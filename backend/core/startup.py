"""Startup-time DB seeding & migrations.

Runs on every backend boot:
- ensures all collection indexes exist
- backfills legacy 'user' role accounts → 'gm'
- seeds the GMFran admin account (the only authoritative app account)
- removes any stale generic-demo users from earlier seeds
- backfills invite tokens on legacy campaigns

Kept here (not in routes/) because nothing here is HTTP-facing; everything
runs in `app.on_event("startup")`.
"""
import secrets

from .db import db, new_id, now_iso
from .security import hash_password, verify_password


# Stale demo accounts that earlier startups seeded. We REMOVE them on every
# boot so the only remaining authoritative account is GMFran. Listed by email
# so a manual /register collision is also tidied up automatically.
_RETIRED_DEMO_EMAILS = (
    "admin@tablegnostic.com",
    "gm@tablegnostic.com",
    "player@tablegnostic.com",
)


async def ensure_indexes():
    # V6.25.30 — email is no longer unique; multiple personas may share an
    # inbox (e.g. one user owning a GM identity and a separate player
    # identity). Drop any pre-existing unique index, then create the
    # non-unique replacement so lookups stay fast.
    try:
        existing = await db.users.index_information()
        if "email_1" in existing and existing["email_1"].get("unique"):
            await db.users.drop_index("email_1")
    except Exception:  # noqa: BLE001 — best-effort migration on cold-start
        pass
    await db.users.create_index("email")
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
    # Retire the old generic-demo accounts: drop their users + any leftover
    # login_attempts / password_reset rows. Anything those accounts authored
    # (campaigns, characters, nodes…) stays intact so GMFran can claim it.
    for email in _RETIRED_DEMO_EMAILS:
        await db.users.delete_one({"email": email})
        await db.login_attempts.delete_many({"key": {"$regex": f":{email}$"}})
        await db.password_reset_tokens.delete_many({"email": email})
    # GMFran — sole authoritative account (admin/GM testing identity).
    await seed_user("franpietrowski@gmail.com", "PieGod08!!", "GMFran", "admin")
    # Backfill invite tokens for legacy campaigns.
    async for c in db.campaigns.find({"invite_token": {"$exists": False}}, {"_id": 0, "id": 1}):
        await db.campaigns.update_one(
            {"id": c["id"]},
            {"$set": {"invite_token": secrets.token_urlsafe(16)}},
        )
