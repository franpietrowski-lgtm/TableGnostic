"""Delta-Drop — author-initiated update broadcasts for cloned campaigns.

The origin author of a campaign (e.g. a setting curator for Evereantha)
publishes a delta: a titled summary plus a bundle of codex additions
and motive/epic updates that they've made since the last drop. Clones
of that campaign show a pending-update badge; the cloner decides
whether to APPLY the drop (merges nodes / motives / epic / genesis
updates into their copy) or DEFER (dismiss until next drop arrives).

This lets a setting author maintain a canonical source that downstream
tables can opt-in to receive — without forcing updates on campaigns
that have already diverged.

Schema (collection: campaign_deltas):
  {
    id, origin_campaign_id, origin_author_id, origin_author_name,
    title, summary, version (int, monotonic per-origin),
    published_at, bundle: {
      nodes: [...],          # full codex snapshot at publish-time
      motives: [...],        # all motives at publish-time
      epic: {...},           # epic doc
      genesis: {...},        # genesis doc
    },
    applied_by: [{clone_campaign_id, at}],
    deferred_by: [{clone_campaign_id, at}],
  }

Clone tracking: a cloned campaign's `cloned_from` field (already set by
routes/campaigns.py clone_campaign) is our link back to the origin.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user
from core.bus import broadcast

router = APIRouter(prefix="/api", tags=["deltas"])


class DeltaPublishIn(BaseModel):
    title: str
    summary: str = ""


# ─── author-side: publish a delta drop ───
@router.post("/campaigns/{cid}/deltas")
async def publish_delta(cid: str, body: DeltaPublishIn,
                         user: dict = Depends(get_current_user)):
    """Origin author snapshots current codex + motives + epic + genesis
    into a delta drop that clones can opt-in to receive.

    Only the campaign's GM (and admin) may publish — and only for
    ORIGIN campaigns (not clones themselves). A campaign that is itself
    a clone cannot publish drops: upstream updates must flow from the
    canonical root.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the campaign author may publish a delta.")
    if camp.get("cloned_from"):
        raise HTTPException(400, "This campaign is a clone; publish drops from the origin instead.")

    # Monotonic version number per origin.
    prior = await db.campaign_deltas.count_documents({"origin_campaign_id": cid})
    nodes = await db.nodes.find({"campaign_id": cid}, {"_id": 0}).to_list(2000)
    motives = await db.node_motives.find({"campaign_id": cid}, {"_id": 0}).to_list(2000)
    epic = await db.epic.find_one({"campaign_id": cid}, {"_id": 0}) or {}
    genesis = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0}) or {}

    doc = {
        "id": new_id(),
        "origin_campaign_id": cid,
        "origin_author_id": user["id"],
        "origin_author_name": user["name"],
        "title": body.title.strip() or f"Delta {prior + 1}",
        "summary": body.summary.strip(),
        "version": prior + 1,
        "published_at": now_iso(),
        "bundle": {
            "nodes": nodes,
            "motives": motives,
            "epic": epic,
            "genesis": genesis,
        },
        "applied_by": [],
        "deferred_by": [],
    }
    await db.campaign_deltas.insert_one(doc)
    # Let every clone subscribed to the WS campaign room know; frontend
    # can badge a pending-drop indicator on the clone campaign card.
    clone_ids = [c["id"] async for c in db.campaigns.find({"cloned_from": cid}, {"id": 1})]
    for clone_id in clone_ids:
        await broadcast(f"campaign:{clone_id}", {
            "type": "delta:new",
            "data": {"origin": cid, "delta_id": doc["id"],
                     "title": doc["title"], "version": doc["version"]},
        })
    return sanitize(doc)


@router.get("/campaigns/{cid}/deltas")
async def list_deltas_for_campaign(cid: str, user: dict = Depends(get_current_user)):
    """List relevant deltas. Behaviour depends on whether the caller is
    viewing the ORIGIN or a CLONE:

    - If cid IS the origin: return all deltas that campaign has published.
    - If cid IS a clone: return deltas published by the origin, with
      per-delta `pending` / `applied` / `deferred` status for THIS clone.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    # Permission — GM of this campaign or admin.
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the campaign GM may see deltas.")

    parent = camp.get("cloned_from")
    origin_id = parent or cid
    rows = await db.campaign_deltas.find(
        {"origin_campaign_id": origin_id}, {"_id": 0, "bundle": 0}
    ).sort("version", -1).to_list(100)

    if parent:
        # Stamp per-clone status so the UI can show pending/applied/deferred.
        for d in rows:
            applied_ids = {x["clone_campaign_id"] for x in (d.get("applied_by") or [])}
            deferred_ids = {x["clone_campaign_id"] for x in (d.get("deferred_by") or [])}
            if cid in applied_ids:
                d["status"] = "applied"
            elif cid in deferred_ids:
                d["status"] = "deferred"
            else:
                d["status"] = "pending"
        rows = sorted(rows, key=lambda x: (x["status"] != "pending", -x.get("version", 0)))
    else:
        for d in rows:
            d["status"] = "published"
    return rows


@router.get("/campaigns/{cid}/deltas/{did}")
async def get_delta(cid: str, did: str, user: dict = Depends(get_current_user)):
    """Return the full delta including its bundle (for diff preview)."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the campaign GM may preview a delta.")
    d = await db.campaign_deltas.find_one({"id": did}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Delta not found")
    return sanitize(d)


@router.post("/campaigns/{cid}/deltas/{did}/apply")
async def apply_delta(cid: str, did: str, user: dict = Depends(get_current_user)):
    """Merge the delta's bundle into THIS (clone) campaign.

    Merge rules (conservative, non-destructive):
      - nodes: add any node whose title is NOT already present in the
        clone; DO NOT overwrite existing nodes the cloner may have
        customised.
      - motives: add any motive whose (node-title, motive-text) pair is
        NOT already present.
      - epic / genesis: only write if the clone's copy is empty or has
        no `refined` sentence yet (brand-new campaigns).

    Returns counts of what was added so the cloner gets a clean summary.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the clone's GM may apply a delta.")
    if not camp.get("cloned_from"):
        raise HTTPException(400, "This campaign is not a clone; nothing to apply.")
    d = await db.campaign_deltas.find_one({"id": did}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Delta not found")
    if d["origin_campaign_id"] != camp["cloned_from"]:
        raise HTTPException(400, "Delta origin does not match this clone's origin.")

    bundle = d["bundle"]
    existing_node_titles = set()
    async for n in db.nodes.find({"campaign_id": cid}, {"title": 1}):
        existing_node_titles.add(n["title"])

    added_nodes = 0
    title_to_new_id: Dict[str, str] = {}
    for node in (bundle.get("nodes") or []):
        if node["title"] in existing_node_titles:
            continue
        # Re-id and re-bind to the clone campaign. We keep the title
        # stable so downstream motive lookup works.
        new_nid = new_id()
        title_to_new_id[node["title"]] = new_nid
        await db.nodes.insert_one({
            **{k: v for k, v in node.items() if k not in ("id", "campaign_id", "_id")},
            "id": new_nid,
            "campaign_id": cid,
            "author_id": user["id"],
            "author_name": user["name"],
            "created_at": now_iso(),
        })
        added_nodes += 1

    # Resolve motive source-node titles. For motives attached to nodes
    # that already existed in the clone, look up that clone-side node id.
    clone_title_to_id: Dict[str, str] = {}
    async for n in db.nodes.find({"campaign_id": cid}, {"title": 1, "id": 1}):
        clone_title_to_id[n["title"]] = n["id"]

    existing_motive_keys = set()
    async for m in db.node_motives.find({"campaign_id": cid},
                                         {"node_id": 1, "motive": 1}):
        existing_motive_keys.add((m["node_id"], m["motive"]))

    # To map motives → clone-node-id, we need the origin's (node_id → title)
    # map embedded in bundle.nodes.
    origin_id_to_title = {n["id"]: n["title"] for n in (bundle.get("nodes") or [])}

    added_motives = 0
    for m in (bundle.get("motives") or []):
        title = origin_id_to_title.get(m.get("node_id"))
        if not title:
            continue
        target_nid = clone_title_to_id.get(title) or title_to_new_id.get(title)
        if not target_nid:
            continue
        key = (target_nid, m["motive"])
        if key in existing_motive_keys:
            continue
        await db.node_motives.insert_one({
            **{k: v for k, v in m.items() if k not in ("id", "_id", "node_id", "campaign_id")},
            "id": new_id(),
            "node_id": target_nid,
            "campaign_id": cid,
            "created_at": now_iso(),
        })
        added_motives += 1

    # Epic / Genesis — soft-apply (only if clone's is empty or un-refined)
    epic_applied = False
    clone_epic = await db.epic.find_one({"campaign_id": cid}, {"_id": 0})
    if (bundle.get("epic") or {}) and (
        not clone_epic or not (clone_epic.get("sentence") or {}).get("refined")
    ):
        epic_doc = {**(bundle["epic"]),
                    "campaign_id": cid,
                    "updated_at": now_iso()}
        epic_doc.pop("_id", None)
        epic_doc.pop("id", None)
        await db.epic.replace_one({"campaign_id": cid}, epic_doc, upsert=True)
        epic_applied = True

    genesis_applied = False
    clone_gen = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if (bundle.get("genesis") or {}) and (
        not clone_gen or not clone_gen.get("sentence_what")
    ):
        g = {**(bundle["genesis"]),
             "campaign_id": cid,
             "updated_at": now_iso()}
        g.pop("_id", None)
        g.pop("id", None)
        await db.genesis.replace_one({"campaign_id": cid}, g, upsert=True)
        genesis_applied = True

    # Stamp applied_by on the delta itself.
    await db.campaign_deltas.update_one(
        {"id": did},
        {"$pull": {"deferred_by": {"clone_campaign_id": cid}}}
    )
    await db.campaign_deltas.update_one(
        {"id": did},
        {"$push": {"applied_by": {
            "clone_campaign_id": cid, "at": now_iso(),
            "by_user_id": user["id"], "by_user_name": user["name"],
        }}}
    )

    return {
        "applied": True,
        "delta_id": did,
        "added_nodes": added_nodes,
        "added_motives": added_motives,
        "epic_applied": epic_applied,
        "genesis_applied": genesis_applied,
    }


@router.post("/campaigns/{cid}/deltas/{did}/defer")
async def defer_delta(cid: str, did: str, user: dict = Depends(get_current_user)):
    """Dismiss the delta for THIS clone. Removes the pending badge;
    leaves the delta visible in the clone's history for later apply."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the clone's GM may defer a delta.")
    if not camp.get("cloned_from"):
        raise HTTPException(400, "This campaign is not a clone.")
    await db.campaign_deltas.update_one(
        {"id": did},
        {"$pull": {"applied_by": {"clone_campaign_id": cid}},
         "$push": {"deferred_by": {
             "clone_campaign_id": cid, "at": now_iso(),
             "by_user_id": user["id"], "by_user_name": user["name"],
         }}}
    )
    return {"deferred": True, "delta_id": did}
