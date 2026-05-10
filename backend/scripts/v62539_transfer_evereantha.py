"""V6.25.39 — Transfer Evereantha → super-admin ownership.

User asked, post super-admin establishment, that "Evereantha — The Maiden
Adventure" (the canonical seeded BESM campaign) move to the
super-admin account so the admin can continue seeding + designing it
while testing functionality.

This script:
  1. Locates the `tablegnostic-admin@tablegnostic.com` user.
  2. Rebinds the Maiden Adventure campaign's `gm_id` + `gm_name` to that
     admin. Original GMFran (the previous owner) is added to
     `member_ids` so they retain seated access.
  3. Idempotent — re-running has no effect once ownership is set.

Run with: `cd /app/backend && set -a && source .env && set +a && PYTHONPATH=/app/backend python scripts/v62539_transfer_evereantha.py`
"""
import asyncio

from core.db import db


MAIDEN_CID = "af461ae004364002932f93c5b71cd483"
ADMIN_EMAIL = "tablegnostic-admin@tablegnostic.com"


async def main() -> None:
    admin = await db.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "id": 1, "name": 1})
    if not admin:
        print(f"FATAL: admin user '{ADMIN_EMAIL}' not found — boot first.")
        return

    camp = await db.campaigns.find_one({"id": MAIDEN_CID}, {"_id": 0})
    if not camp:
        print(f"FATAL: campaign '{MAIDEN_CID}' not found.")
        return

    if camp.get("gm_id") == admin["id"]:
        print(f"OK: '{camp.get('name')}' already owned by '{admin['name']}'.")
        return

    prev_gm_id = camp.get("gm_id")
    prev_gm_name = camp.get("gm_name")
    members = set(camp.get("member_ids") or [])
    if prev_gm_id and prev_gm_id != admin["id"]:
        members.add(prev_gm_id)
    # The admin must also be a member of their own campaign.
    members.add(admin["id"])

    await db.campaigns.update_one(
        {"id": MAIDEN_CID},
        {"$set": {
            "gm_id": admin["id"],
            "gm_name": admin["name"],
            "member_ids": list(members),
            # Keep the OG GM credited in the campaign description trail.
            "prior_gm_id": prev_gm_id,
            "prior_gm_name": prev_gm_name,
        }},
    )
    print(
        f"OK: '{camp.get('name')}' transferred {prev_gm_name!r} → {admin['name']!r}. "
        f"Previous GM kept as member. Total seated: {len(members)}."
    )


if __name__ == "__main__":
    asyncio.run(main())
