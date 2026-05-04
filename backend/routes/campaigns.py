"""Campaigns — CRUD, membership, invite tokens, custom rules, genesis (Atelier)."""
import secrets
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from core.cost_engine import resolve_system_id
from core.db import db, new_id, now_iso, sanitize
from core.models import CampaignIn, CustomAttributeIn, GenesisIn, JoinIn
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["campaigns"])


@router.post("/campaigns")
async def create_campaign(body: CampaignIn, user: dict = Depends(get_current_user)):
    """Player-role accounts are seat-only — gm + admin may host campaigns."""
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "Player accounts cannot create campaigns. "
                                 "Update your role to Game Master in your profile to host a table.")
    doc = body.model_dump()
    resolve_system_id(doc)
    doc["id"] = new_id()
    doc["gm_id"] = user["id"]
    doc["gm_name"] = user["name"]
    doc["member_ids"] = []
    doc["invite_token"] = secrets.token_urlsafe(16)
    doc["created_at"] = now_iso()
    await db.campaigns.insert_one(doc)
    return sanitize(doc)


@router.post("/campaigns/{cid}/clone")
async def clone_campaign(cid: str, user: dict = Depends(get_current_user)):
    """Fork any campaign you can see (your own, public, or one you've joined)
    into a brand-new campaign you GM. Carries World Codex, edges, Genesis,
    custom rules, and *published* characters (re-owned by the cloning GM).
    Excludes: sessions, chat, dice, recaps, battlemaps, channel history.
    GM/admin role required (Player accounts cannot host).
    """
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "Only GM/admin accounts can clone campaigns.")

    src = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not src:
        raise HTTPException(404, "Source campaign not found")
    visible = (src.get("visibility") == "public"
               or src.get("gm_id") == user["id"]
               or user["id"] in src.get("member_ids", [])
               or user.get("role") == "admin")
    if not visible:
        raise HTTPException(403, "You can only clone campaigns you can see.")

    new_cid = new_id()
    forged = {
        **{k: v for k, v in src.items()
           if k not in ("id", "gm_id", "gm_name", "member_ids", "invite_token", "created_at")},
        "id": new_cid,
        "name": f"{src.get('name', 'Campaign')} (copy)",
        "gm_id": user["id"],
        "gm_name": user["name"],
        "member_ids": [],
        "invite_token": secrets.token_urlsafe(16),
        "created_at": now_iso(),
        "cloned_from": cid,
    }
    await db.campaigns.insert_one(forged)

    # ---- Knowledge Web nodes ----
    node_id_map: Dict[str, str] = {}
    src_nodes = await db.nodes.find({"campaign_id": cid}, {"_id": 0}).to_list(2000)
    for n in src_nodes:
        new_nid = new_id()
        node_id_map[n["id"]] = new_nid
        copy_n = {**n,
                  "id": new_nid, "campaign_id": new_cid,
                  "author_id": user["id"], "author_name": user["name"],
                  "revealed_to": [],  # private to the new GM until re-revealed
                  "created_at": now_iso()}
        await db.nodes.insert_one(copy_n)

    # ---- Edges (remap node ids) ----
    src_edges = await db.edges.find({"campaign_id": cid}, {"_id": 0}).to_list(2000)
    for e in src_edges:
        from_n = node_id_map.get(e.get("from_node"))
        to_n = node_id_map.get(e.get("to_node"))
        if not (from_n and to_n):
            continue
        await db.edges.insert_one({
            **e, "id": new_id(), "campaign_id": new_cid,
            "from_node": from_n, "to_node": to_n, "created_at": now_iso(),
        })

    # ---- Genesis (Atelier pre-fill) ----
    src_gen = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if src_gen:
        copy_g = {**src_gen,
                  "id": new_id(), "campaign_id": new_cid,
                  "created_at": now_iso()}
        await db.genesis.insert_one(copy_g)

    # ---- Custom attributes / rules ----
    src_custom = await db.custom_attributes.find({"campaign_id": cid}, {"_id": 0}).to_list(500)
    for c in src_custom:
        await db.custom_attributes.insert_one({
            **c, "id": new_id(), "campaign_id": new_cid,
            "created_at": now_iso(),
        })

    # ---- Characters (only published; re-owned by the cloning GM until they
    # reassign to the players) ----
    src_chars = await db.characters.find(
        {"campaign_id": cid, "published": True}, {"_id": 0},
    ).to_list(500)
    chars_copied = 0
    for ch in src_chars:
        await db.characters.insert_one({
            **{k: v for k, v in ch.items()
               if k not in ("id", "campaign_id", "owner_id", "owner_name",
                            "created_at", "updated_at")},
            "id": new_id(), "campaign_id": new_cid,
            "owner_id": user["id"], "owner_name": user["name"],
            "created_at": now_iso(),
        })
        chars_copied += 1

    return {
        "ok": True,
        "campaign": sanitize(forged),
        "nodes_cloned": len(src_nodes),
        "edges_cloned": len(src_edges),
        "characters_cloned": chars_copied,
        "genesis_cloned": bool(src_gen),
    }


@router.get("/campaigns")
async def list_campaigns(mine: bool = False, user: dict = Depends(get_current_user)):
    q: Dict[str, Any] = {}
    if mine:
        q = {"$or": [{"gm_id": user["id"]}, {"member_ids": user["id"]}]}
    else:
        q = {"$or": [
            {"visibility": "public"},
            {"gm_id": user["id"]},
            {"member_ids": user["id"]},
        ]}
    rows = await db.campaigns.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    # Hydrate per-row relationship flags the UI relies on (Dashboard
    # card badges, Discover filter, Account "Campaigns GM'd" stat).
    # Detail GET /{cid} already does this at line ~265; the list must
    # mirror it or list-consumers silently mislabel every row.
    uid = user["id"]
    for r in rows:
        r["is_gm"] = r.get("gm_id") == uid
        r["is_member"] = uid in (r.get("member_ids") or [])
    return rows


@router.put("/campaigns/{cid}")
async def update_campaign(cid: str, body: CampaignIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM may edit")
    data = body.model_dump()
    resolve_system_id(data)
    data["id"] = cid
    data["gm_id"] = camp["gm_id"]
    data["gm_name"] = camp["gm_name"]
    data["member_ids"] = camp.get("member_ids", [])
    data["invite_token"] = camp.get("invite_token") or secrets.token_urlsafe(16)
    data["created_at"] = camp.get("created_at", now_iso())
    data["updated_at"] = now_iso()
    await db.campaigns.replace_one({"id": cid}, data)
    return sanitize(data)


@router.post("/campaigns/{cid}/regenerate-invite")
async def regenerate_invite(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp or camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM")
    new_token = secrets.token_urlsafe(16)
    await db.campaigns.update_one({"id": cid}, {"$set": {"invite_token": new_token}})
    return {"invite_token": new_token}


@router.get("/campaigns/{cid}/members")
async def list_campaign_members(cid: str, user: dict = Depends(get_current_user)):
    """Member list for the @mention autocomplete picker. Returns id, name, and
    a kebab-handle (lowercased name with spaces → underscores; falls back to
    the email's local part). Anyone seated at the table can read this."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if (camp["gm_id"] != user["id"]
            and user["id"] not in camp.get("member_ids", [])
            and user.get("role") != "admin"):
        raise HTTPException(403, "Not seated at this table")
    member_ids = list({camp["gm_id"], *camp.get("member_ids", [])})
    rows = await db.users.find(
        {"id": {"$in": member_ids}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "role": 1},
    ).to_list(50)
    out = []
    for u in rows:
        nm = (u.get("name") or "").lower().replace(" ", "_")
        if not nm:
            nm = (u.get("email") or "").split("@")[0].lower()
        out.append({
            "id": u["id"],
            "name": u.get("name") or u.get("email", ""),
            "handle": nm,
            "is_gm": u["id"] == camp["gm_id"],
            "role": u.get("role", "player"),
        })
    return out


@router.get("/invites/{token}")
async def get_invite(token: str):
    """Public invite lookup (no auth) — minimal summary for onboarding."""
    camp = await db.campaigns.find_one({"invite_token": token}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Invite not found or revoked")
    return {
        "campaign_id": camp["id"], "name": camp["name"],
        "description": camp.get("description", ""),
        "system": camp.get("system", "BESM 4E"),
        "power_level": camp.get("power_level", "Heroic"),
        "gm_name": camp.get("gm_name", ""),
        "tags": camp.get("tags", []),
        "tone": camp.get("tone"), "genre": camp.get("genre"),
        "schedule": camp.get("schedule"),
        "experience_level": camp.get("experience_level"),
        "seated": len(camp.get("member_ids", [])),
        "max_players": camp.get("max_players", 6),
        "full": len(camp.get("member_ids", [])) >= camp.get("max_players", 6),
    }


@router.post("/invites/{token}/accept")
async def accept_invite(token: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"invite_token": token}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Invite not found or revoked")
    cid = camp["id"]
    if user["id"] == camp["gm_id"]:
        return {"ok": True, "campaign_id": cid, "already": "gm"}
    if user["id"] in camp.get("member_ids", []):
        return {"ok": True, "campaign_id": cid, "already": True}
    if len(camp.get("member_ids", [])) >= camp.get("max_players", 6):
        raise HTTPException(400, "Table full")
    await db.campaigns.update_one({"id": cid}, {"$addToSet": {"member_ids": user["id"]}})
    return {"ok": True, "campaign_id": cid}


@router.get("/campaigns/{cid}")
async def get_campaign(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp.get("visibility", "private") != "public" and camp["gm_id"] != user["id"] and user["id"] not in camp.get("member_ids", []):
        raise HTTPException(403, "Not permitted")
    members = await db.users.find(
        {"id": {"$in": camp.get("member_ids", [])}},
        {"_id": 0, "password_hash": 0},
    ).to_list(100)
    camp["members"] = members
    camp["is_gm"] = (camp["gm_id"] == user["id"])
    # Parity with list endpoint — Dashboard / Discover / Account all
    # consume is_member; keep detail in sync so any single-campaign
    # view never silently mislabels the caller's relationship.
    camp["is_member"] = user["id"] in (camp.get("member_ids") or [])
    return camp


@router.post("/campaigns/{cid}/join")
async def join_campaign(cid: str, body: JoinIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if user["id"] == camp["gm_id"]:
        raise HTTPException(400, "You are the GM")
    if user["id"] in camp.get("member_ids", []):
        return {"ok": True, "already": True}
    if len(camp.get("member_ids", [])) >= camp.get("max_players", 6):
        raise HTTPException(400, "Table full")
    await db.campaigns.update_one({"id": cid}, {"$addToSet": {"member_ids": user["id"]}})
    return {"ok": True}


@router.post("/campaigns/{cid}/leave")
async def leave_campaign(cid: str, user: dict = Depends(get_current_user)):
    await db.campaigns.update_one({"id": cid}, {"$pull": {"member_ids": user["id"]}})
    return {"ok": True}


@router.delete("/campaigns/{cid}")
async def delete_campaign(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM may delete")
    await db.campaigns.delete_one({"id": cid})
    await db.characters.delete_many({"campaign_id": cid})
    await db.nodes.delete_many({"campaign_id": cid})
    await db.edges.delete_many({"campaign_id": cid})
    await db.sessions.delete_many({"campaign_id": cid})
    await db.custom_attributes.delete_many({"campaign_id": cid})
    return {"ok": True}


# -------- Custom GM rules (custom Attributes / Defects / Skills) --------

@router.post("/campaigns/{campaign_id}/custom")
async def create_custom(campaign_id: str, body: CustomAttributeIn,
                        user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM can add custom entries")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["campaign_id"] = campaign_id
    doc["created_by"] = user["id"]
    doc["created_at"] = now_iso()
    await db.custom_attributes.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{campaign_id}/custom")
async def list_custom(campaign_id: str, user: dict = Depends(get_current_user)):
    rows = await db.custom_attributes.find({"campaign_id": campaign_id}, {"_id": 0}).to_list(500)
    return rows


@router.delete("/campaigns/{campaign_id}/custom/{cid}")
async def delete_custom(campaign_id: str, cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user.get("role") != "admin"):
        raise HTTPException(403, "Only GM can remove")
    await db.custom_attributes.delete_one({"id": cid, "campaign_id": campaign_id})
    return {"ok": True}


# -------- Genesis (Sclanders Atelier) --------

@router.get("/campaigns/{cid}/genesis")
async def get_genesis(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can view genesis")
    doc = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if not doc:
        doc = GenesisIn(campaign_id=cid).model_dump()
        doc["id"] = new_id()
        doc["created_at"] = now_iso()
        await db.genesis.insert_one(dict(doc))
        doc.pop("_id", None)
    return doc


@router.put("/campaigns/{cid}/genesis")
async def update_genesis(cid: str, body: GenesisIn,
                         user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can edit genesis")
    data = body.model_dump()
    data["campaign_id"] = cid
    data["updated_at"] = now_iso()
    existing = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if existing:
        data["id"] = existing["id"]
        data["created_at"] = existing.get("created_at", now_iso())
        await db.genesis.replace_one({"campaign_id": cid}, data)
    else:
        data["id"] = new_id()
        data["created_at"] = now_iso()
        await db.genesis.insert_one(dict(data))
    data.pop("_id", None)
    return data


@router.post("/campaigns/{cid}/genesis/seed-nodes")
async def seed_nodes_from_genesis(cid: str, user: dict = Depends(get_current_user)):
    """Convert genesis seed_npcs / nemesis / adventures / locations /
    biomes / factions / motives into gm_only knowledge nodes.

    V6.25 — Nemesis sub-fields (motive / resources / weakness) now seed
    as distinct linked lore / faction / lore nodes instead of being glued
    into a single monolithic content blob. Discrete seed buckets
    (locations, biomes, factions, motives) each fan out to one codex
    node per entry. The World Tree auto-classifier picks them up by
    `type` on its next fetch.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp or camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can seed")
    g = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if not g:
        raise HTTPException(404, "No genesis")
    created = 0
    now = now_iso()
    author = {"author_id": user["id"], "author_name": user["name"]}

    async def _insert(node: dict) -> str:
        node.setdefault("id", new_id())
        node.setdefault("campaign_id", cid)
        node.setdefault("visibility", "gm_only")
        node.setdefault("revealed_to", [])
        node.setdefault("links", [])
        node.setdefault("tags", [])
        node.setdefault("created_at", now)
        node.update(author)
        await db.nodes.insert_one(node)
        return node["id"]

    # Nemesis → one NPC node + discrete lore/faction sub-nodes for the
    # motive / resources / weakness so the World Tree's Population &
    # History pillars each get a distinct entry.
    nem_id = None
    if g.get("nemesis_name"):
        nem_id = await _insert({
            "type": "npc",
            "title": g["nemesis_name"],
            "content": f"Nemesis · {g.get('nemesis_type','')}".strip(" ·"),
            "tags": ["nemesis"],
        })
        created += 1
        if g.get("nemesis_motive"):
            await _insert({
                "type": "lore",
                "title": f"{g['nemesis_name']} — Motive",
                "content": g["nemesis_motive"],
                "tags": ["nemesis", "motive"],
                "links": [{"target_id": nem_id, "relationship_type": "drives"}],
            })
            created += 1
        if g.get("nemesis_resources"):
            await _insert({
                "type": "faction",
                "title": f"{g['nemesis_name']} — Resources",
                "content": g["nemesis_resources"],
                "tags": ["nemesis", "resources"],
                "links": [{"target_id": nem_id, "relationship_type": "commands"}],
            })
            created += 1
        if g.get("nemesis_weakness"):
            await _insert({
                "type": "lore",
                "title": f"{g['nemesis_name']} — Weakness",
                "content": g["nemesis_weakness"],
                "tags": ["nemesis", "weakness"],
                "links": [{"target_id": nem_id, "relationship_type": "vulnerable-to"}],
            })
            created += 1

    # Supporting cast — one npc node per seed entry.
    for npc in g.get("seed_npcs", []) or []:
        if not npc.get("name"):
            continue
        await _insert({
            "type": "npc",
            "title": npc["name"],
            "content": f"{npc.get('role','')}\n\n{npc.get('note','')}".strip(),
            "tags": [npc.get("role", "").lower()] if npc.get("role") else [],
        })
        created += 1

    # Adventures — one quest node per entry.
    for adv in g.get("adventures", []) or []:
        if not adv.get("title"):
            continue
        await _insert({
            "type": "quest",
            "title": adv["title"],
            "content": (f"Hook: {adv.get('hook','')}\n"
                         f"Stakes: {adv.get('stakes','')}\n"
                         f"Outcome: {adv.get('outcome','')}"),
            "tags": [adv.get("kind", "").lower()] if adv.get("kind") else [],
        })
        created += 1

    # V6.25 — Discrete Genesis buckets → one codex node apiece.
    for bucket, node_type, tag in (
        ("locations", "location", "location"),
        ("biomes", "location", "biome"),
        ("factions", "faction", "faction"),
        ("motives", "lore", "motive"),
    ):
        for entry in g.get(bucket, []) or []:
            title = (entry.get("name") or entry.get("title") or "").strip()
            if not title:
                continue
            await _insert({
                "type": node_type,
                "title": title,
                "content": entry.get("summary") or entry.get("note") or "",
                "tags": [tag] + [t for t in (entry.get("tags") or []) if t],
            })
            created += 1

    return {"ok": True, "nodes_created": created}
