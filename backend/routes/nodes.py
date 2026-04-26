"""Knowledge-Web nodes + edges (the World Codex / Knowledge Graph layer).

`visible_to(...)` is the access-control check that drives the entire
World Codex view — gm_only / shared / revealed-to-specific-players.
"""
from fastapi import APIRouter, Depends, HTTPException

from core.db import db, new_id, now_iso, sanitize
from core.models import EdgeIn, NodeIn, NodeRevealIn
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["knowledge-web"])


def visible_to(node: dict, user_id: str, camp: dict) -> bool:
    if camp["gm_id"] == user_id:
        return True
    v = node.get("visibility", "gm_only")
    if v == "shared":
        return True
    if v == "revealed" and user_id in node.get("revealed_to", []):
        return True
    return False


@router.post("/nodes")
async def create_node(body: NodeIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": body.campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user["id"] not in camp.get("member_ids", []):
        raise HTTPException(403, "Not permitted")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["author_id"] = user["id"]
    doc["author_name"] = user["name"]
    doc["created_at"] = now_iso()
    # Players can only create shared nodes by default.
    if camp["gm_id"] != user["id"]:
        doc["visibility"] = "shared"
    await db.nodes.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{cid}/nodes")
async def list_nodes(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    rows = await db.nodes.find({"campaign_id": cid}, {"_id": 0}).to_list(500)
    return [n for n in rows if visible_to(n, user["id"], camp)]


@router.put("/nodes/{nid}")
async def update_node(nid: str, body: NodeIn, user: dict = Depends(get_current_user)):
    n = await db.nodes.find_one({"id": nid}, {"_id": 0})
    if not n:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": n["campaign_id"]}, {"_id": 0})
    if user["id"] != n["author_id"] and user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Not permitted")
    upd = body.model_dump()
    upd["id"] = nid
    upd["author_id"] = n["author_id"]
    upd["author_name"] = n["author_name"]
    upd["created_at"] = n["created_at"]
    upd["updated_at"] = now_iso()
    await db.nodes.replace_one({"id": nid}, upd)
    return sanitize(upd)


@router.post("/nodes/{nid}/reveal")
async def reveal_node(nid: str, body: NodeRevealIn,
                      user: dict = Depends(get_current_user)):
    n = await db.nodes.find_one({"id": nid}, {"_id": 0})
    if not n:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": n["campaign_id"]}, {"_id": 0})
    if user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Only GM can reveal")
    await db.nodes.update_one(
        {"id": nid},
        {"$set": {"visibility": "revealed"},
         "$addToSet": {"revealed_to": {"$each": body.user_ids}}},
    )
    return {"ok": True}


@router.put("/nodes/{nid}/visibility")
async def set_node_visibility(nid: str, body: dict,
                              user: dict = Depends(get_current_user)):
    """Bidirectional visibility flip. Body: {"visibility": "gm_only" | "shared" | "revealed"}.
    GM only. Switching back to gm_only also clears the revealed_to list so a
    node reset to private is fully private again."""
    visibility = body.get("visibility") if isinstance(body, dict) else None
    if visibility not in ("gm_only", "shared", "revealed"):
        raise HTTPException(400, "visibility must be one of: gm_only / shared / revealed")
    n = await db.nodes.find_one({"id": nid}, {"_id": 0})
    if not n:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": n["campaign_id"]}, {"_id": 0})
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM can change visibility")
    update = {"visibility": visibility, "updated_at": now_iso()}
    if visibility == "gm_only":
        update["revealed_to"] = []
    await db.nodes.update_one({"id": nid}, {"$set": update})
    return {"ok": True, "visibility": visibility}


@router.post("/campaigns/{cid}/nodes/bulk-visibility")
async def bulk_set_visibility(cid: str, body: dict,
                              user: dict = Depends(get_current_user)):
    """Bulk toggle every node in the campaign. Body: {"visibility": "shared"
    or "gm_only"}. GM only. The "Reveal-all-to-players" / "Reset-all-to-GM"
    one-click affordance the GM Codex panel exposes."""
    visibility = body.get("visibility") if isinstance(body, dict) else None
    if visibility not in ("gm_only", "shared"):
        raise HTTPException(400, "Bulk visibility supports gm_only or shared only")
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user.get("role") != "admin"):
        raise HTTPException(403, "Only GM can bulk-set visibility")
    update = {"visibility": visibility, "updated_at": now_iso()}
    if visibility == "gm_only":
        update["revealed_to"] = []
    res = await db.nodes.update_many({"campaign_id": cid}, {"$set": update})
    return {"ok": True, "updated": res.modified_count, "visibility": visibility}


@router.delete("/nodes/{nid}")
async def delete_node(nid: str, user: dict = Depends(get_current_user)):
    n = await db.nodes.find_one({"id": nid}, {"_id": 0})
    if not n:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": n["campaign_id"]}, {"_id": 0})
    if user["id"] != n["author_id"] and user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Not permitted")
    await db.nodes.delete_one({"id": nid})
    await db.edges.delete_many({"$or": [{"from_node": nid}, {"to_node": nid}]})
    return {"ok": True}


@router.post("/edges")
async def create_edge(body: EdgeIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": body.campaign_id}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user["id"] not in camp.get("member_ids", [])):
        raise HTTPException(403, "Not permitted")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    await db.edges.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{cid}/edges")
async def list_edges(cid: str, user: dict = Depends(get_current_user)):
    rows = await db.edges.find({"campaign_id": cid}, {"_id": 0}).to_list(500)
    return rows
