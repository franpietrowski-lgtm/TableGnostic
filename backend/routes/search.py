"""Global search — V6.13 · powers the Cmd-K palette.

Searches across all surfaces the current user can see:
    * Campaigns they GM or sit at
    * Codex nodes inside those campaigns (NPCs / locations / factions / creatures / lore)
    * Characters in those campaigns
    * Sessions in those campaigns

Result shape: a flat list of { type, id, title, subtitle, campaign_id,
campaign_name, url } tuples so the frontend can dispatch directly.

Performance: simple `$regex` with `$options: "i"` across indexed fields.
Capped to 40 results total. Case-insensitive, substring match. Empty
query returns []; <2-char query returns [].
"""
import re
from fastapi import APIRouter, Depends
from core.db import db, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["search"])


def _safe_re(q: str):
    return re.compile(re.escape(q), re.IGNORECASE)


@router.get("/search")
async def global_search(q: str = "", user: dict = Depends(get_current_user)):
    q = (q or "").strip()
    if len(q) < 2:
        return []
    pat = _safe_re(q)
    rx = {"$regex": re.escape(q), "$options": "i"}

    # Campaigns the user can see: GM or member or admin.
    is_admin = user.get("role") == "admin"
    campaign_query = (
        {} if is_admin
        else {"$or": [{"gm_id": user["id"]}, {"member_ids": user["id"]}]}
    )
    campaigns_cursor = db.campaigns.find(
        campaign_query, {"_id": 0, "id": 1, "name": 1, "description": 1,
                          "system_id": 1, "tags": 1},
    )
    visible_campaigns = await campaigns_cursor.to_list(500)
    visible_ids = [c["id"] for c in visible_campaigns]
    camp_by_id = {c["id"]: c for c in visible_campaigns}

    results = []

    # 1. Campaigns — match name / description / tags
    for c in visible_campaigns:
        blob = f"{c.get('name','')} {c.get('description','')} {' '.join(c.get('tags') or [])}"
        if pat.search(blob):
            results.append({
                "type": "campaign",
                "id": c["id"],
                "title": c["name"],
                "subtitle": c.get("description", "")[:100],
                "campaign_id": c["id"],
                "campaign_name": c["name"],
                "system_id": c.get("system_id", ""),
                "url": f"/app/campaigns/{c['id']}",
            })

    if not visible_ids:
        return sanitize(results[:40])

    # 2. Codex nodes
    nodes_cursor = db.nodes.find(
        {"campaign_id": {"$in": visible_ids},
         "$or": [{"title": rx}, {"content": rx}]},
        {"_id": 0, "id": 1, "title": 1, "content": 1, "type": 1, "campaign_id": 1},
    ).limit(30)
    async for n in nodes_cursor:
        c = camp_by_id.get(n["campaign_id"], {})
        results.append({
            "type": "node",
            "id": n["id"],
            "title": n.get("title") or "—",
            "subtitle": f"{n.get('type','node')} · {(n.get('content') or '')[:80]}",
            "campaign_id": n["campaign_id"],
            "campaign_name": c.get("name", ""),
            "system_id": c.get("system_id", ""),
            "url": f"/app/campaigns/{n['campaign_id']}#node-{n['id']}",
        })

    # 3. Characters
    chars_cursor = db.characters.find(
        {"campaign_id": {"$in": visible_ids},
         "$or": [{"name": rx}, {"notes": rx}]},
        {"_id": 0, "id": 1, "name": 1, "notes": 1, "campaign_id": 1},
    ).limit(30)
    async for ch in chars_cursor:
        c = camp_by_id.get(ch["campaign_id"], {})
        results.append({
            "type": "character",
            "id": ch["id"],
            "title": ch.get("name") or "—",
            "subtitle": (ch.get("notes") or "")[:100] or c.get("name", ""),
            "campaign_id": ch["campaign_id"],
            "campaign_name": c.get("name", ""),
            "system_id": c.get("system_id", ""),
            "url": f"/app/campaigns/{ch['campaign_id']}/characters/{ch['id']}",
        })

    # 4. Sessions
    sessions_cursor = db.sessions.find(
        {"campaign_id": {"$in": visible_ids},
         "$or": [{"name": rx}, {"title": rx}, {"location": rx}]},
        {"_id": 0, "id": 1, "name": 1, "title": 1, "location": 1, "campaign_id": 1},
    ).limit(15)
    async for s in sessions_cursor:
        c = camp_by_id.get(s["campaign_id"], {})
        title = s.get("name") or s.get("title") or "Session"
        results.append({
            "type": "session",
            "id": s["id"],
            "title": title,
            "subtitle": s.get("location") or c.get("name", ""),
            "campaign_id": s["campaign_id"],
            "campaign_name": c.get("name", ""),
            "system_id": c.get("system_id", ""),
            "url": f"/app/sessions/{s['id']}",
        })

    return sanitize(results[:40])
