"""Characters — CRUD + Journal entry.

The character sheet is the single artefact that survives between sessions —
its `folio.journal` array is the player-facing diary that feeds the recap LLM.
"""
from fastapi import APIRouter, Depends, HTTPException

from core.bus import broadcast
from routes.ecosystem import _pulse_tick
from core.cost_engine import calc_derived, calc_spent_points, effective_level
from core.db import db, new_id, now_iso, sanitize
from core.models import CharacterIn, JournalEntryIn
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["characters"])


def _decorate(ch: dict) -> dict:
    """Stamp `effective_level` (BESM 4E: level + #lim − #enh, ≥1) on each
    Attribute. Pure decoration — never persisted, so legacy data still loads.
    """
    for a in ch.get("attributes", []) or []:
        a["effective_level"] = effective_level(a)
    return ch


@router.post("/characters")
async def create_character(body: CharacterIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": body.campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user["id"] not in camp.get("member_ids", []):
        raise HTTPException(403, "Join the campaign first")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["owner_id"] = user["id"]
    doc["owner_name"] = user["name"]
    doc["created_at"] = now_iso()
    doc["derived"] = calc_derived(doc, camp)
    doc["spent"] = calc_spent_points(doc)
    await db.characters.insert_one(doc)
    return sanitize(_decorate(doc))


@router.get("/campaigns/{cid}/characters")
async def list_characters(cid: str, user: dict = Depends(get_current_user)):
    rows = await db.characters.find({"campaign_id": cid}, {"_id": 0}).to_list(200)
    return [_decorate(r) for r in rows]


@router.get("/characters")
async def my_characters(mine: bool = False,
                         user: dict = Depends(get_current_user)):
    """Cross-campaign character list — used by the Dashboard 'Your
    characters' strip. `mine=true` filters to characters the caller
    owns. Without the flag we return nothing to avoid leaking the full
    character table.
    """
    if not mine:
        return []
    rows = await db.characters.find(
        {"owner_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return [_decorate(r) for r in rows]


@router.get("/characters/{ch_id}")
async def get_character(ch_id: str, user: dict = Depends(get_current_user)):
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    return _decorate(ch)


@router.put("/characters/{ch_id}")
async def update_character(ch_id: str, body: CharacterIn,
                           user: dict = Depends(get_current_user)):
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if user["id"] != ch["owner_id"] and user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Not permitted")
    update = body.model_dump()
    update["id"] = ch_id
    update["owner_id"] = ch["owner_id"]
    update["owner_name"] = ch["owner_name"]
    update["created_at"] = ch["created_at"]
    update["derived"] = calc_derived(update, camp)
    update["spent"] = calc_spent_points(update)
    update["updated_at"] = now_iso()
    await db.characters.replace_one({"id": ch_id}, update)
    return sanitize(_decorate(update))


@router.delete("/characters/{ch_id}")
async def delete_character(ch_id: str, user: dict = Depends(get_current_user)):
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if user["id"] != ch["owner_id"] and user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Not permitted")
    await db.characters.delete_one({"id": ch_id})
    return {"ok": True}


@router.post("/characters/{ch_id}/transfer")
async def transfer_character(ch_id: str, new_owner_id: str,
                             user: dict = Depends(get_current_user)):
    """Reassign a character to a different player. GM/admin only.

    Use case: cloning a campaign carries published PCs as the cloner-GM's
    characters; transfer hands them off to the actual players. Body is just
    a query-param `new_owner_id` to keep the call simple.
    """
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM/admin may transfer characters")
    new_owner = await db.users.find_one({"id": new_owner_id}, {"_id": 0})
    if not new_owner:
        raise HTTPException(404, "New owner not found")
    # Auto-add transferred-to player as a campaign member if they aren't one
    if (new_owner_id != camp["gm_id"]
            and new_owner_id not in camp.get("member_ids", [])):
        await db.campaigns.update_one({"id": ch["campaign_id"]},
                                      {"$addToSet": {"member_ids": new_owner_id}})
    await db.characters.update_one(
        {"id": ch_id},
        {"$set": {"owner_id": new_owner_id,
                  "owner_name": new_owner.get("name") or new_owner.get("email", "?"),
                  "updated_at": now_iso()}},
    )
    fresh = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    return _decorate(fresh)


@router.post("/characters/{ch_id}/companions")
async def assign_companion_owner(ch_id: str, player_id: str,
                                 user: dict = Depends(get_current_user)):
    """Add `player_id` to this character's `companion_owners` list. The
    player gains move-token rights on the battlemap and read-only view of
    the sheet, without losing any rights for the actual owner. GM/admin only.
    """
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM/admin may assign companion owners")
    player = await db.users.find_one({"id": player_id}, {"_id": 0})
    if not player:
        raise HTTPException(404, "Player not found")
    if player_id == ch.get("owner_id"):
        raise HTTPException(400, "That player already owns this character")
    await db.characters.update_one(
        {"id": ch_id},
        {"$addToSet": {"companion_owners": player_id},
         "$set": {"updated_at": now_iso()}},
    )
    fresh = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    return _decorate(fresh)


@router.delete("/characters/{ch_id}/companions/{player_id}")
async def revoke_companion_owner(ch_id: str, player_id: str,
                                 user: dict = Depends(get_current_user)):
    """Remove `player_id` from this character's companion list. GM/admin only."""
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM/admin may revoke companion owners")
    await db.characters.update_one(
        {"id": ch_id},
        {"$pull": {"companion_owners": player_id},
         "$set": {"updated_at": now_iso()}},
    )
    fresh = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    return _decorate(fresh)


@router.post("/characters/{cid}/journal")
async def add_journal_entry(cid: str, body: JournalEntryIn,
                            user: dict = Depends(get_current_user)):
    """Append a journal entry to a character's Folio. The entry is timestamped,
    optionally echoed as a journal-tagged chat line into the session, AND
    auto-uploaded to the campaign's World Codex as a `player_journal` node
    (visibility=gm_only) so the GM can collect every player's perspective for
    end-of-session weaving. The player retains their folio copy.
    Only the character's owner OR the campaign GM may journal as that PC.
    """
    ch = await db.characters.find_one({"id": cid}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Character's campaign no longer exists.")
    is_owner = ch["owner_id"] == user["id"]
    is_gm = camp["gm_id"] == user["id"]
    if not (is_owner or is_gm):
        raise HTTPException(403, "Only the character's owner or the campaign GM can journal.")

    folio = ch.get("folio") or {}
    journal = folio.get("journal")
    # Defensive: legacy seeds stored journal as a string. Keep arrays only.
    if not isinstance(journal, list):
        journal = []
    entry_id = new_id()
    entry = {
        "id": entry_id,
        "text": body.text.strip(),
        "by_uid": user["id"],
        "by_name": user["name"],
        "created_at": now_iso(),
        # V5.4 — ecosystem nervous system. Echo the optional plot_phase
        # + session_id back onto the entry so the Pulse aggregator can
        # filter by phase without re-walking the chat log.
        "session_id": body.session_id,
        "plot_phase": (body.plot_phase or "").strip(),
    }
    journal.append(entry)
    folio["journal"] = journal
    await db.characters.update_one({"id": cid}, {"$set": {"folio": folio}})

    # Echo into the session's chat log so the recap pipeline picks it up.
    if body.session_id:
        sess = await db.sessions.find_one({"id": body.session_id}, {"_id": 0})
        if sess and sess.get("campaign_id") == ch["campaign_id"]:
            log_doc = {
                "id": new_id(), "session_id": body.session_id,
                "message": f"[journal] {ch.get('name','?')}: {body.text.strip()}",
                "kind": "journal", "user_id": user["id"], "user_name": user["name"],
                "character_id": cid,
                "created_at": now_iso(),
            }
            await db.chat_logs.insert_one(log_doc)
            await broadcast(body.session_id, {"type": "chat", "data": sanitize(log_doc)})

    # Auto-upload to the campaign's World Codex as a `player_journal` node —
    # GM-only, so players can't read each other's perspectives. The end-of-
    # session weaver pulls these in to compose the final chronicle.
    journal_node_id = new_id()
    await db.nodes.insert_one({
        "id": journal_node_id,
        "campaign_id": ch["campaign_id"],
        "type": "player_journal",
        "title": f"{ch.get('name','?')} — {entry['created_at'][:10]}",
        "content": body.text.strip(),
        "tags": ["journal", ch.get("name", "").lower()],
        "visibility": "gm_only",
        "revealed_to": [],
        "links": [],
        "fields": {
            "character_id": cid,
            "character_name": ch.get("name", ""),
            "session_id": body.session_id or "",
            "by_uid": user["id"],
            "by_name": user["name"],
            "folio_entry_id": entry_id,
        },
        "author_id": user["id"],
        "author_name": user["name"],
        "created_at": now_iso(),
    })

    # Ecosystem Pulse — new journal entry is a first-class signal. The
    # Director Console's live panel will refetch on this tick.
    await _pulse_tick(ch["campaign_id"], "journal", {
        "character_id": cid,
        "character_name": ch.get("name", ""),
        "plot_phase": entry.get("plot_phase") or "",
    })

    return {"ok": True, "entry": entry, "count": len(journal),
            "codex_node_id": journal_node_id}