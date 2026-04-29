"""Ecosystem nervous system — V5.4.

The user's vision: TableGnostic should run as an ecosystem where every
authored layer talks to every other. The plot timeline is the spine.

Routes:
  POST /api/nodes/{nid}/motive  — append a motive evolution to a Codex node
  GET  /api/nodes/{nid}/motives — list all motive entries for a node

  GET  /api/campaigns/{cid}/ecosystem/pulse?plot_phase=X
       — single aggregated read returning everything that is live RIGHT NOW
       at the given plot phase: sessions, journal entries (gm + player),
       NPC motives that are 'active' or 'evolving', Director encounters,
       Codex nodes touched in those journal entries.

The Pulse endpoint is what powers the Director Console's "Live Ecosystem"
panel and gives the GM a single-pane-of-glass view without manual
bookkeeping. Idempotent reads. GM-only.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from core.db import db, new_id, now_iso, sanitize
from core.models import NodeMotiveIn
from core.security import get_current_user
from core.bus import broadcast

router = APIRouter(prefix="/api", tags=["ecosystem"])


async def _pulse_tick(cid: str, kind: str, meta: Dict[str, Any] | None = None):
    """Notify the campaign room that the Pulse has something new.

    Any subscribed Director Console will refetch `/ecosystem/pulse` on
    receipt — we deliberately DON'T send the new motive inline because
    the Pulse aggregator applies plot-phase / visibility filtering that
    belongs on the server.
    """
    await broadcast(f"campaign:{cid}", {
        "type": "pulse:tick",
        "data": {"kind": kind, **(meta or {}), "at": now_iso()},
    })


# ───────────────────── helpers ─────────────────────
async def _campaign_or_404(cid: str) -> Dict[str, Any]:
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp


def _is_gm(user: Dict[str, Any], camp: Dict[str, Any]) -> bool:
    return user["id"] == camp["gm_id"] or user.get("role") == "admin"


# ───────────────────── NPC / Codex node motives ─────────────────────
@router.post("/nodes/{nid}/motive")
async def post_motive(nid: str, body: NodeMotiveIn,
                      user: Dict[str, Any] = Depends(get_current_user)):
    """Append-only motive entry on a Codex node. Existing campaign-edit
    permissions apply (only the GM/admin or the node author can post)."""
    node = await db.nodes.find_one({"id": nid}, {"_id": 0})
    if not node:
        raise HTTPException(404, "Node not found")
    camp = await _campaign_or_404(node["campaign_id"])
    # GM or admin or the node's original author may post a motive.
    if not _is_gm(user, camp) and node.get("author_id") != user["id"]:
        raise HTTPException(403, "Not authorised for this node.")
    entry = {
        "id": new_id(),
        "node_id": nid,
        "campaign_id": node["campaign_id"],
        "motive": body.motive,
        "plot_phase": body.plot_phase or "",
        "state": body.state,
        "triggered_by": body.triggered_by,
        "visibility": body.visibility,
        "author_id": user["id"],
        "author_name": user.get("name") or user.get("email"),
        "created_at": now_iso(),
    }
    await db.node_motives.insert_one(dict(entry))
    # Ecosystem nerve-fire — let any Director Console on this campaign
    # refresh its Pulse panel live.
    await _pulse_tick(node["campaign_id"], "motive",
                      {"node_id": nid, "plot_phase": entry["plot_phase"]})
    return sanitize(entry)


@router.get("/nodes/{nid}/motives")
async def get_motives(nid: str, user: Dict[str, Any] = Depends(get_current_user)):
    """List motive history for a single node. Filters out gm_only entries
    for non-GM viewers — players see only what's been declared `shared`."""
    node = await db.nodes.find_one({"id": nid}, {"_id": 0})
    if not node:
        raise HTTPException(404, "Node not found")
    camp = await _campaign_or_404(node["campaign_id"])
    is_gm = _is_gm(user, camp)
    cursor = db.node_motives.find({"node_id": nid}, {"_id": 0}).sort("created_at", 1)
    out = []
    async for m in cursor:
        if not is_gm and m.get("visibility") == "gm_only":
            continue
        out.append(m)
    return out


# ───────────────────── Ecosystem Pulse ─────────────────────
@router.get("/campaigns/{cid}/ecosystem/pulse")
async def pulse(cid: str, plot_phase: Optional[str] = None,
                user: Dict[str, Any] = Depends(get_current_user)):
    """Single-pane-of-glass aggregator for "what's live right now."

    Returns:
      - **plot_phase** echo (or empty)
      - **sessions[]** matching the phase (most recent first)
      - **journal_entries[]** flattened from all characters' folio.journal,
        filtered to gm-readable ones only
      - **active_motives[]** for every Codex node, latest entry per node
        whose state is active|evolving and matches the phase (or any phase
        if no filter)
      - **encounters[]** from the Director doc matching the phase
      - **touched_node_ids[]** referenced by any of the above
    GM/admin only — the Pulse view leaks too much narrative metadata for
    a player surface; players use the regular Codex/Session listings.
    """
    camp = await _campaign_or_404(cid)
    if not _is_gm(user, camp):
        raise HTTPException(403, "GM/admin only.")

    # Sessions for the campaign. We want the most-recent N matching the
    # phase, plus any session marked 'live' or in-progress.
    sess_q: Dict[str, Any] = {"campaign_id": cid}
    if plot_phase:
        sess_q["plot_phase"] = plot_phase
    sessions = []
    async for s in db.sessions.find(sess_q, {"_id": 0}).sort("created_at", -1).limit(20):
        sessions.append({
            "id": s["id"], "title": s.get("title"),
            "plot_phase": s.get("plot_phase") or "",
            "scheduled_at": s.get("scheduled_at"),
            "location": s.get("location") or "",
            "status": s.get("status") or "draft",
            "round": s.get("round", 0),
        })

    # Character folios — pull every character to walk folio.journal.
    journal_entries: List[Dict[str, Any]] = []
    async for c in db.characters.find({"campaign_id": cid}, {"_id": 0}):
        for je in (c.get("folio") or {}).get("journal", []) or []:
            if plot_phase and (je.get("plot_phase") or "") != plot_phase:
                continue
            journal_entries.append({
                "character_id": c["id"],
                "character_name": c.get("name"),
                "owner_name": c.get("owner_name"),
                "text": je.get("text"),
                "created_at": je.get("created_at"),
                "session_id": je.get("session_id"),
                "plot_phase": je.get("plot_phase") or "",
            })
    journal_entries.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    journal_entries = journal_entries[:25]

    # NPC motives — latest per node, only active/evolving entries.
    motive_q: Dict[str, Any] = {"campaign_id": cid,
                                "state": {"$in": ["active", "evolving"]}}
    if plot_phase:
        motive_q["plot_phase"] = plot_phase
    latest_per_node: Dict[str, Dict[str, Any]] = {}
    async for m in db.node_motives.find(motive_q, {"_id": 0}).sort("created_at", -1):
        nid = m["node_id"]
        if nid in latest_per_node:
            continue
        latest_per_node[nid] = m
    # Hydrate node titles into each motive.
    motive_node_ids = list(latest_per_node.keys())
    node_titles: Dict[str, str] = {}
    if motive_node_ids:
        async for n in db.nodes.find({"id": {"$in": motive_node_ids}},
                                     {"_id": 0, "id": 1, "title": 1, "type": 1}):
            node_titles[n["id"]] = f"{n.get('type', 'lore')}: {n.get('title', '?')}"
    active_motives = []
    for nid, m in latest_per_node.items():
        active_motives.append({**m, "node_label": node_titles.get(nid, nid)})

    # Director encounters at this phase.
    director = await db.directors.find_one({"campaign_id": cid}, {"_id": 0})
    encounters: List[Dict[str, Any]] = []
    if director:
        for e in director.get("encounters", []) or []:
            if plot_phase and (e.get("plot_phase") or "") != plot_phase:
                continue
            encounters.append({
                "id": e.get("id"),
                "name": e.get("name") or "Untitled",
                "kind": e.get("kind") or "combat",
                "plot_phase": e.get("plot_phase") or "",
                "npc_count": len(e.get("npcs") or []),
                "party_count": len(e.get("party_character_ids") or []),
                "environment": e.get("environment") or {},
            })

    # Compute the touched node id set for cross-linking.
    touched: set[str] = set(motive_node_ids)
    for je in journal_entries:
        if je.get("session_id"):
            touched.add(je["session_id"])  # not a node, but useful
    return {
        "campaign_id": cid,
        "plot_phase": plot_phase or "",
        "sessions": sessions,
        "journal_entries": journal_entries,
        "active_motives": active_motives,
        "encounters": encounters,
        "touched_node_ids": list(touched),
    }
