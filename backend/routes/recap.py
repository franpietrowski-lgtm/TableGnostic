"""Session recap — Loremaster LLM (Claude Sonnet 4.5 via emergentintegrations).

Recap rules:
- 30s per (user, session) cooldown to avoid spamming the LLM key.
- Honours campaign tone / genre / power level when crafting the prompt.
- Never invents details that aren't in the transcript (hard system instruction).
- Stores recaps in `db.recaps` so the next session's auto-pin picks the latest.
"""
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from core.config import EMERGENT_LLM_KEY
from core.db import db, new_id, now_iso, sanitize
from core.models import FinalizeIn, RecapIn
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["recap"])

_recap_cooldown: Dict[str, datetime] = {}


@router.post("/sessions/{sid}/recap")
async def generate_recap(sid: str, body: RecapIn,
                         user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user["id"] not in camp.get("member_ids", []):
        raise HTTPException(403, "Not seated at this table")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured")
    cooldown_key = f"{user['id']}:{sid}"
    last = _recap_cooldown.get(cooldown_key)
    if last and (datetime.now(timezone.utc) - last).total_seconds() < 30:
        raise HTTPException(429, "Recap cooldown — try again in a few seconds.")

    chat = await db.chat_logs.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    dice = await db.dice_rolls.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(300)
    # V6.25.36 — Voice push-to-talk lines are IN-CHARACTER speech (the
    # character is talking, not the player). Fold them into the chronicle
    # alongside chat / rolls / encounter ticks. We deliberately do NOT
    # surface them on player journals — the journal stays a player's own
    # perspective so we can still detect lies / sub-plot drift.
    voice = await db.voice_lines.find(
        {"session_id": sid, "transcribed": True}, {"_id": 0}
    ).sort("started_at", 1).to_list(400)
    # V6.25.43 — pull scenes so the recap engine can segment by scene.
    scenes = await db.scenes.find(
        {"session_id": sid}, {"_id": 0},
    ).sort("scene_no", 1).to_list(200)
    chars = await db.characters.find(
        {"campaign_id": s["campaign_id"]},
        {"_id": 0, "name": 1, "concept": 1},
    ).to_list(50)

    if not chat:
        raise HTTPException(400, "No chat history yet to recap")

    # ----- Per-scene segmentation -----------------------------------
    # Build a map scene_id -> {meta, chat[], voice[], dice[]}. Anything
    # without a scene_id falls under the synthetic "pre-scene" bucket.
    buckets: dict = {None: {"meta": None, "chat": [], "voice": [], "dice": []}}
    for sc in scenes:
        buckets[sc["id"]] = {"meta": sc, "chat": [], "voice": [], "dice": []}
    for m in chat:
        b = buckets.get(m.get("scene_id")) or buckets[None]
        b["chat"].append(m)
    for v in voice:
        b = buckets.get(v.get("scene_id")) or buckets[None]
        b["voice"].append(v)
    for d in dice:
        b = buckets.get(d.get("scene_id")) or buckets[None]
        b["dice"].append(d)

    def _bucket_block(label: str, b: dict) -> str:
        lines = [f"\n### {label}"]
        meta = b.get("meta") or {}
        if meta.get("location_label"):
            lines.append(f"_Location: {meta['location_label']}"
                         + (f" — {meta.get('location_description','')[:300]}"
                            if meta.get('location_description') else "")
                         + "_")
        if meta.get("participant_character_ids"):
            lines.append(f"_Participants: {len(meta['participant_character_ids'])} character(s)_")
        if meta.get("gm_narration"):
            for n in meta["gm_narration"][:20]:
                lines.append(f"  ◆ GM narration: {n.get('text','')}")
        for m in b["chat"][-120:]:
            kind = m.get("kind", "chat")
            prefix = "[SYSTEM]" if kind == "system" else f"[{kind.upper()}]"
            lines.append(f"{prefix} {m.get('user_name','?')}: {m.get('message','')}")
        for v in b["voice"][-60:]:
            t = (v.get("text") or "").strip()
            if t:
                lines.append(f"  • {v.get('character_name','?')} (in-character): \"{t}\"")
        for d in b["dice"][-30:]:
            r = d.get("result", {})
            lbl = d.get("label") or d.get("notation", "")
            lines.append(f"  • {d.get('user_name','?')} rolled "
                         f"{d.get('notation','?')} = {r.get('total','?')} ({lbl})")
        return "\n".join(lines)

    segmented_blocks = []
    # Render pre-scene first only if it has anything.
    pre = buckets[None]
    if pre["chat"] or pre["voice"] or pre["dice"]:
        segmented_blocks.append(_bucket_block("Pre-scene / Unscoped", pre))
    for sc in scenes:
        b = buckets[sc["id"]]
        segmented_blocks.append(_bucket_block(
            f"{sc.get('name')} (`{sc.get('slug')}`)", b,
        ))
    segmented_text = "\n".join(segmented_blocks) or "(no transcript)"

    char_lines = "\n".join(f"  • {c['name']} — {c.get('concept','')}" for c in chars[:20]) or "  (none)"

    style_instruction = {
        "narrative": "Write a flowing narrative recap (~180–240 words per scene) in third-person past tense. PRESERVE the scene structure — open each scene with its slug header, then the prose. Capture emotional beats, pivotal rolls, and any unanswered questions. Skip dice mechanics that didn't matter.",
        "bullet": "Write a tight bulleted recap, grouped per scene. For each scene emit a header line with its slug, then bullets: What happened · Who acted · What changed · Open threads.",
        "in-character": "Write the recap as a journal entry from one of the player characters' perspective (pick whoever was most active). First-person, evocative, ~150 words per scene. Use the scene slug as a date-stamp.",
    }[body.style]

    system_prompt = (
        f"You are the Loremaster of a tabletop campaign called \"{camp['name']}\" "
        f"({camp.get('system','BESM 4E')}, {camp.get('power_level','Heroic')} tier). "
        f"Tone: {camp.get('tone') or 'unspecified'}. Genre: {camp.get('genre') or 'unspecified'}. "
        f"Your job: turn raw session logs into a recap the table will love rereading. "
        f"The session is segmented into SCENES — preserve that segmentation in your output. "
        f"Never invent details that aren't in the transcript. Honour the players. {style_instruction}"
    )
    user_prompt = (
        f"Session: \"{s.get('title','Untitled session')}\" (round {s.get('round',0)}).\n\n"
        f"Characters at the table:\n{char_lines}\n\n"
        f"Scene-segmented transcript (the # SCENE headers below MUST be preserved as section dividers in your recap):\n{segmented_text}\n\n"
        f"Now write the recap, scene by scene."
    )

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"recap-{sid}",
            system_message=system_prompt,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        recap_text = await chat_client.send_message(UserMessage(text=user_prompt))
    except Exception as e:
        print(f"[recap:error] session={sid} -> {e}")
        raise HTTPException(502, "Recap generation failed — try again in a moment.")

    _recap_cooldown[f"{user['id']}:{sid}"] = datetime.now(timezone.utc)

    doc = {
        "id": new_id(), "session_id": sid, "campaign_id": s["campaign_id"],
        "style": body.style, "text": recap_text, "by_user_id": user["id"],
        "by_user_name": user["name"], "created_at": now_iso(),
    }
    await db.recaps.insert_one(doc)

    # Mirror the recap into the World Codex as a `session_record` node so it
    # collects alongside player journals on the Codex Sessions tab. GM-only
    # by default; the GM can flip to "shared" when the woven chronicle is
    # ready for the table.
    record_node_id = new_id()
    await db.nodes.insert_one({
        "id": record_node_id,
        "campaign_id": s["campaign_id"],
        "type": "session_record",
        "title": f"Recap — {s.get('title','Session')} ({doc['created_at'][:10]})",
        "content": recap_text,
        "tags": ["session", "recap", body.style],
        "visibility": "gm_only",
        "revealed_to": [],
        "links": [],
        "fields": {
            "session_id": sid,
            "session_title": s.get("title", ""),
            "round": s.get("round", 0),
            "style": body.style,
            "recap_id": doc["id"],
            "is_finalized": False,
        },
        "author_id": user["id"],
        "author_name": user["name"],
        "created_at": now_iso(),
    })
    return sanitize({**doc, "codex_node_id": record_node_id})


@router.post("/sessions/{sid}/finalize")
async def finalize_session_chronicle(sid: str, body: FinalizeIn,
                                     user: dict = Depends(get_current_user)):
    """Weave a final session chronicle: GM provides a list of player-journal
    node ids + a base recap, Claude composes a unified third-person narrative
    that incorporates each character's voice/perception. The result is
    persisted as a finalised `session_record` node and (when the entire
    campaign is finalised) becomes a chapter of the campaign chronicle PDF.

    GM/admin only.
    """
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM/admin can finalize a session chronicle.")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured")

    journal_ids = body.journal_node_ids
    recap_node_id = body.recap_node_id
    tone = body.tone

    recap_node = await db.nodes.find_one(
        {"id": recap_node_id, "campaign_id": s["campaign_id"]}, {"_id": 0})
    if not recap_node or recap_node.get("type") != "session_record":
        raise HTTPException(404, "Recap node not found in this campaign")

    journals = []
    for jid in journal_ids:
        jn = await db.nodes.find_one(
            {"id": jid, "campaign_id": s["campaign_id"], "type": "player_journal"},
            {"_id": 0})
        if jn:
            journals.append(jn)

    journal_block = "\n\n".join(
        f"### {j.get('fields', {}).get('character_name','?')} — {j.get('created_at','')[:16]}\n"
        f"{j.get('content','').strip()}"
        for j in journals
    ) or "  (no player journals yet)"

    style_instruction = {
        "lyrical": "Write a lyrical, third-person narrative chronicle (~250–350 words). "
                   "Weave each character's perspective into the broader event flow. "
                   "Honour the GM's recap as the spine; treat journals as colour and inner voice.",
        "terse": "Write a tight, present-tense chronicle. Group beats by what happened, "
                 "who acted, what changed, what's left open. Use journal lines as direct "
                 "quotations only when they add fact (not feeling).",
        "in-character": "Write the chronicle as a many-voiced campfire retelling — each "
                        "character speaks one paragraph in their own voice, the GM's recap "
                        "frames the cold-open and outro. Roughly 400 words.",
    }[tone]

    system_prompt = (
        f"You are the Loremaster of \"{camp['name']}\" "
        f"({camp.get('system','BESM 4E')}, {camp.get('power_level','Heroic')} tier). "
        f"Your task: weave the GM's recap and the players' journal entries into the "
        f"definitive chronicle of this session. Honour every voice. Never invent "
        f"details that aren't in either source. Tone: {camp.get('tone') or 'unspecified'}. "
        f"Genre: {camp.get('genre') or 'unspecified'}. {style_instruction}"
    )
    user_prompt = (
        f"# Session: {s.get('title','Untitled')} (round {s.get('round',0)})\n\n"
        f"## GM Recap (the spine)\n{recap_node.get('content','').strip()}\n\n"
        f"## Player Journals (colour + voice)\n{journal_block}\n\n"
        f"Now compose the chronicle."
    )

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"chronicle-{sid}",
            system_message=system_prompt,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        chronicle_text = await chat_client.send_message(UserMessage(text=user_prompt))
    except Exception as e:
        print(f"[finalize:error] session={sid} -> {e}")
        raise HTTPException(502, "Chronicle weaving failed — try again in a moment.")

    # Update the session_record node with the woven chronicle.
    fields = {**(recap_node.get("fields") or {}),
              "is_finalized": True,
              "tone": tone,
              "journal_ids": journal_ids,
              "finalized_at": now_iso(),
              "finalized_by": user["name"],
              "original_recap": recap_node.get("content", "")}
    await db.nodes.update_one(
        {"id": recap_node_id},
        {"$set": {
            "content": chronicle_text,
            "title": f"Chronicle — {s.get('title','Session')} ({now_iso()[:10]})",
            "tags": list(set([*(recap_node.get("tags") or []), "chronicle", "finalized", tone])),
            "fields": fields,
            "updated_at": now_iso(),
        }})
    fresh = await db.nodes.find_one({"id": recap_node_id}, {"_id": 0})
    return sanitize(fresh)


@router.get("/sessions/{sid}/recaps")
async def list_recaps(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.recaps.find({"session_id": sid}, {"_id": 0}).sort("created_at", -1).to_list(20)
    return rows
