"""V6.25.36 — Admin migration: port everything to a single admin account.

Steps:
  1. Verify the target admin user (email + password match).
  2. Promote target to role='admin'.
  3. For EVERY collection that holds a user_id / owner_id / gm_id /
     member_ids / requester_id / dismissed_by reference, rewrite all
     references from OLD user ids → ADMIN id.
  4. Delete every other user record.
  5. Print a verification summary the operator can use to log in.

The script is IDEMPOTENT — re-running it after success is a no-op.
"""
import asyncio
import os
import sys
from typing import Set, Dict, Any, List

import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient


TARGET_EMAIL = "franpietrowski@gmail.com"
TARGET_PASSWORD = "PieBan2018!!"


async def main() -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("FATAL: MONGO_URL or DB_NAME not set", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # ── 1. Find the target admin via password match ──────────
    matches = await db.users.find(
        {"email": TARGET_EMAIL.lower()}, {"_id": 0}
    ).to_list(50)
    if not matches:
        # Try un-lowered email as fallback (legacy registrations)
        matches = await db.users.find(
            {"email": TARGET_EMAIL}, {"_id": 0}
        ).to_list(50)
    print(f"Found {len(matches)} accounts at {TARGET_EMAIL}:")
    for m in matches:
        print(f"  · id={m['id']} role={m.get('role','user')} name={m.get('name','-')} created={m.get('created_at','?')}")

    target = None
    for m in matches:
        h = m.get("password_hash") or ""
        try:
            ok = bcrypt.checkpw(TARGET_PASSWORD.encode(), h.encode())
        except Exception:
            ok = False
        if ok:
            target = m
            break
    if not target:
        print(f"FATAL: no account at {TARGET_EMAIL} with the supplied password.", file=sys.stderr)
        return 3
    admin_id = target["id"]
    print(f"\nTARGET ADMIN: id={admin_id}  email={target['email']}  name={target.get('name','-')}\n")

    # ── 2. Build the list of OLD user ids (everyone else) ─────
    all_users = await db.users.find({}, {"_id": 0, "id": 1, "email": 1, "name": 1}).to_list(10000)
    old_ids: Set[str] = {u["id"] for u in all_users if u["id"] != admin_id}
    print(f"Will rewrite references for {len(old_ids)} OLD user ids and then delete them.")
    if not old_ids:
        print("Already migrated — nothing to do.")

    # ── 3. Promote target to admin (idempotent) ───────────────
    await db.users.update_one(
        {"id": admin_id}, {"$set": {"role": "admin"}}
    )
    print("→ target promoted to role='admin'.")

    # ── 4. Rewrite all references ─────────────────────────────
    # Field-level rewrites by collection. Each entry: (collection, [scalar_fields], [array_fields])
    rewrite_map: List[Dict[str, Any]] = [
        {"col": "campaigns",            "scalar": ["gm_id", "owner_id"], "array": ["member_ids"]},
        {"col": "characters",           "scalar": ["user_id", "owner_id"], "array": []},
        {"col": "sessions",             "scalar": ["gm_id", "owner_id"], "array": ["attendees"]},
        {"col": "nodes",                "scalar": ["created_by", "owner_id"], "array": []},
        {"col": "edges",                "scalar": ["created_by"], "array": []},
        {"col": "rolls",                "scalar": ["user_id", "character_id_owner"], "array": []},
        {"col": "messages",             "scalar": ["user_id", "author_id"], "array": []},
        {"col": "encounter_completions","scalar": ["completed_by"], "array": []},
        {"col": "concept_drafts",       "scalar": ["requester_id"], "array": []},
        {"col": "cost_overrides",       "scalar": ["gm_id"], "array": []},
        {"col": "marketplace_listings", "scalar": ["owner_id"], "array": []},
        {"col": "takedowns",            "scalar": ["admin_id"], "array": []},
        {"col": "share_links",          "scalar": ["created_by"], "array": []},
        {"col": "consents",             "scalar": ["user_id"], "array": []},
        {"col": "pending_advancements", "scalar": ["user_id", "approved_by"], "array": []},
        {"col": "macros",               "scalar": ["user_id", "owner_id"], "array": []},
        {"col": "private_access",       "scalar": ["user_id"], "array": []},
        {"col": "session_attendees",    "scalar": ["user_id"], "array": []},
    ]

    rewrites_done: Dict[str, int] = {}
    for plan in rewrite_map:
        col = db[plan["col"]]
        total = 0
        for field in plan["scalar"]:
            res = await col.update_many(
                {field: {"$in": list(old_ids)}},
                [{"$set": {field: admin_id}}],
            )
            total += res.modified_count
        for field in plan["array"]:
            # Replace each old id with admin id inside arrays.
            cursor = col.find({field: {"$in": list(old_ids)}}, {"_id": 0, "id": 1, field: 1})
            async for doc in cursor:
                arr = doc.get(field) or []
                new_arr = [admin_id if x in old_ids else x for x in arr]
                # Dedup preserve-order
                seen, deduped = set(), []
                for x in new_arr:
                    if x in seen:
                        continue
                    seen.add(x)
                    deduped.append(x)
                if deduped != arr:
                    await col.update_one({"id": doc["id"]}, {"$set": {field: deduped}})
                    total += 1
        if total:
            rewrites_done[plan["col"]] = total

    print("\nRewrite counts:")
    for col, n in sorted(rewrites_done.items()):
        print(f"  · {col}: {n} doc(s) updated")
    if not rewrites_done:
        print("  (none — already migrated.)")

    # ── 5. Delete the old user records ─────────────────────────
    if old_ids:
        del_res = await db.users.delete_many({"id": {"$in": list(old_ids)}})
        print(f"\nDeleted {del_res.deleted_count} old user record(s).")

    # ── 6. Verify ──────────────────────────────────────────────
    remaining = await db.users.count_documents({})
    print(f"\nFinal users.count = {remaining}")
    surviving = await db.users.find({}, {"_id": 0}).to_list(10)
    for s in surviving:
        print(f"  · id={s['id']}  email={s['email']}  role={s.get('role','user')}  name={s.get('name','-')}")

    # Spot-check ownership counts under the admin's id.
    counts = {
        "campaigns_gm":    await db.campaigns.count_documents({"gm_id": admin_id}),
        "characters":      await db.characters.count_documents({"user_id": admin_id}),
        "sessions":        await db.sessions.count_documents({"gm_id": admin_id}),
        "nodes":           await db.nodes.count_documents({"created_by": admin_id}),
        "concept_drafts":  await db.concept_drafts.count_documents({"requester_id": admin_id}),
        "macros":          await db.macros.count_documents({"$or": [{"user_id": admin_id}, {"owner_id": admin_id}]}),
        "marketplace":     await db.marketplace_listings.count_documents({"owner_id": admin_id}),
    }
    print("\nAdmin now owns:")
    for k, v in counts.items():
        print(f"  · {k}: {v}")

    client.close()
    print("\nMIGRATION COMPLETE.")
    print(f"  Login email:    {target['email']}")
    print(f"  Login password: {TARGET_PASSWORD}")
    print(f"  Role:           admin")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
