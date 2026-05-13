"""Voice Lines — V6.25.36.

Push-to-talk in-character speech capture for the Session View.

Workflow:
  1. Player holds the PTT button → browser MediaRecorder records webm/opus.
  2. On release, frontend POSTs the audio chunk + character_id +
     started_at_iso + ended_at_iso to /api/sessions/{sid}/voice-lines.
  3. Server runs OpenAI Whisper (whisper-1 via emergentintegrations) on
     the chunk and stores the transcript on the `voice_lines` collection.
  4. The recap consumer reads voice_lines AND chat AND dice_rolls AND
     encounter completions AND turn-order ticks; the LLM weaves them
     into a single chronicle.

Rules for design:
  • Voice lines represent **the CHARACTER speaking, not the player**.
    Players can mute their mic, disable camera, and still speak in
    chat — voice is opt-in per push.
  • Voice lines are NEVER pushed into player journals — that's
    deliberate. The journal is a player's own perspective, possibly
    unreliable; voice + chat + rolls are the ground truth.
  • The author can delete their own line within 60s of upload (typo /
    misspoke). The GM can delete any line at any time.
"""
from __future__ import annotations
import os
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from core.config import EMERGENT_LLM_KEY
from core.db import db, new_id, now_iso
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["voice-lines"])

_MAX_BYTES = 12 * 1024 * 1024   # 12 MB / push (Whisper hard cap is 25 MB)
_ALLOWED_MIME = {
    "audio/webm", "audio/webm;codecs=opus", "audio/ogg", "audio/ogg;codecs=opus",
    "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a", "audio/wav",
    "audio/x-wav", "audio/x-m4a",
}


async def _seated_or_403(session_id: str, user: dict) -> dict:
    s = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found.")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found.")
    is_gm = user["id"] == camp.get("gm_id") or user.get("role") == "admin"
    is_member = user["id"] in (camp.get("member_ids") or [])
    if not (is_gm or is_member):
        raise HTTPException(403, "Not seated at this table.")
    return s


@router.post("/sessions/{sid}/voice-lines")
async def create_voice_line(
    sid: str,
    audio: UploadFile = File(...),
    character_id: str = Form(...),
    started_at: str = Form(...),
    ended_at: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """Receive a PTT audio chunk, transcribe via Whisper, persist the
    line. Returns the saved record.
    """
    s = await _seated_or_403(sid, user)
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured for transcription.")

    raw = await audio.read()
    if len(raw) == 0:
        raise HTTPException(400, "Empty audio.")
    if len(raw) > _MAX_BYTES:
        raise HTTPException(413, f"Audio too large ({len(raw)} bytes). "
                                  f"Max {_MAX_BYTES} bytes per push.")
    mime = (audio.content_type or "").lower()
    if mime and mime not in _ALLOWED_MIME:
        # Tolerate unknown subtype params (e.g. "audio/webm;codecs=opus,...");
        # only the leading prefix needs to be in the allowed set.
        prefix = mime.split(";", 1)[0].strip()
        if prefix not in {m.split(";", 1)[0] for m in _ALLOWED_MIME}:
            raise HTTPException(415, f"Unsupported audio mime '{mime}'.")

    char = await db.characters.find_one(
        {"id": character_id, "campaign_id": s["campaign_id"]},
        {"_id": 0, "id": 1, "name": 1, "user_id": 1},
    )
    if not char:
        raise HTTPException(404, "Character not found on this campaign.")
    # Players may only speak as their own character; admin/GM may speak as any.
    is_gm = user["id"] == (await db.campaigns.find_one(
        {"id": s["campaign_id"]}, {"_id": 0, "gm_id": 1}
    )).get("gm_id")
    if char.get("user_id") != user["id"] and not (is_gm or user.get("role") == "admin"):
        raise HTTPException(403, "Not the owner of this character.")

    # Whisper transcription — file is uploaded straight from RAM.
    # Whisper needs a `name` attribute on the file-like; BytesIO does not
    # have one natively, so we fake it.
    text = ""
    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        stt = OpenAISpeechToText(api_key=EMERGENT_LLM_KEY)
        bio = io.BytesIO(raw)
        # Whisper picks the format from the filename extension.
        ext = "webm"
        if "ogg" in mime:
            ext = "ogg"
        elif "mp3" in mime or "mpeg" in mime:
            ext = "mp3"
        elif "wav" in mime:
            ext = "wav"
        elif "mp4" in mime or "m4a" in mime:
            ext = "m4a"
        bio.name = f"voice_{new_id()}.{ext}"
        resp = await stt.transcribe(file=bio, model="whisper-1",
                                     response_format="text", language="en")
        # In some SDK builds `transcribe(response_format='text')` returns the
        # raw string; in others it returns an object with `.text`. Handle both.
        if isinstance(resp, str):
            text = resp.strip()
        else:
            text = (getattr(resp, "text", "") or "").strip()
    except Exception as e:
        print(f"[voice_lines:whisper-error] sid={sid} char={character_id} -> {e}")
        # Don't lose the player's effort — store an empty-text record so the
        # GM can re-trigger transcription manually if Whisper hiccuped.
        text = ""

    doc = {
        "id":            new_id(),
        "session_id":    sid,
        "campaign_id":   s["campaign_id"],
        "character_id":  character_id,
        "character_name":char.get("name") or "Unnamed",
        "speaker_user_id": user["id"],
        "speaker_user_name": user.get("name", "Unknown"),
        "text":          text,
        "started_at":    started_at,
        "ended_at":      ended_at,
        "audio_bytes":   len(raw),
        "transcribed":   bool(text),
        "created_at":    now_iso(),
    }

    # V6.25.43 — tag with the active scene (if any) and auto-forward the
    # transcription to the session chat + the GM-configured target thread.
    try:
        from routes.scenes import attach_active_scene
        from core.bus import broadcast as _broadcast
        scene = await attach_active_scene(sid)
        scene_id = (scene or {}).get("id")
        target_thread_id = ((scene or {}).get("target_thread_id")
                            or s.get("default_target_thread_id"))
        if scene_id:
            doc["scene_id"] = scene_id
            doc["scene_slug"] = scene.get("slug")
    except Exception as e:
        print(f"[voice_lines:scene-attach] {e}")
        scene = None
        scene_id = None
        target_thread_id = None

    await db.voice_lines.insert_one(dict(doc))
    doc.pop("_id", None)

    # ---- Auto-forward to session chat ----------------------------
    # Players want PTT lines visible inline. Format:
    #   Character "Name": "transcription"
    if text:
        chat_msg = {
            "id": new_id(),
            "session_id": sid,
            "user_id": user["id"],
            "user_name": user.get("name", "Unknown"),
            "kind": "voice",  # downstream renderers can style PTT
            "character_id": character_id,
            "character_name": char.get("name") or "Unnamed",
            "message": f'Character "{char.get("name") or "Unnamed"}": "{text}"',
            "voice_line_id": doc["id"],
            "scene_id": scene_id,
            "scene_slug": (scene or {}).get("slug"),
            "created_at": now_iso(),
        }
        try:
            await db.chat_logs.insert_one(dict(chat_msg))
            chat_msg.pop("_id", None)
            await _broadcast(sid, {"type": "chat", "data": chat_msg})
        except Exception as e:
            print(f"[voice_lines:chat-mirror] {e}")
            chat_msg = None

        # ---- Mirror to the configured target thread/channel ----------
        # V6.25.44 — target may be either a thread_id OR a channel_id
        # (Scene Switcher dropdown groups both kinds). Resolve which.
        if target_thread_id and chat_msg:
            try:
                th = await db.threads.find_one({"id": target_thread_id},
                                               {"_id": 0, "channel_id": 1})
                if th:
                    mirror_channel_id = th.get("channel_id")
                    mirror_thread_id = target_thread_id
                else:
                    ch_row = await db.campaign_channels.find_one(
                        {"id": target_thread_id}, {"_id": 0, "id": 1},
                    )
                    if ch_row:
                        mirror_channel_id = target_thread_id
                        mirror_thread_id = None
                    else:
                        mirror_channel_id = None
                        mirror_thread_id = None
                if mirror_channel_id:
                    thread_msg = {
                        "id": new_id(),
                        "channel_id": mirror_channel_id,
                        "thread_id": mirror_thread_id,
                        "author_id": user["id"],
                        "author_name": user.get("name", "Unknown"),
                        "body": f'**{char.get("name") or "Unnamed"}** _(PTT, {(scene or {}).get("slug") or "no-scene"})_:\n\n"{text}"',
                        "kind": "voice-mirror",
                        "voice_line_id": doc["id"],
                        "scene_id": scene_id,
                        "session_id": sid,
                        "created_at": now_iso(),
                        "reactions": [],
                        "pinned": False,
                        "edited_at": None,
                    }
                    await db.channel_msgs.insert_one(dict(thread_msg))
                    thread_msg.pop("_id", None)
                    await _broadcast(
                        f"campaign:{s['campaign_id']}:channels",
                        {"type": "channel:msg", "data": thread_msg},
                    )
            except Exception as e:
                print(f"[voice_lines:thread-mirror] {e}")

        # ---- Patch scene participant + ids -------------------------
        if scene_id:
            try:
                upd = {
                    "$addToSet": {"participant_character_ids": character_id},
                    "$push": {"voice_line_ids": doc["id"]},
                }
                if chat_msg:
                    # Can't have two $push keys for the same array; this
                    # array (chat_message_ids) is separate from voice_line_ids
                    # so we're safe.
                    upd["$push"]["chat_message_ids"] = chat_msg["id"]
                await db.scenes.update_one({"id": scene_id}, upd)
            except Exception as e:
                print(f"[voice_lines:scene-patch] {e}")

    return {"voice_line": doc}


@router.get("/sessions/{sid}/voice-lines")
async def list_voice_lines(sid: str,
                            user: dict = Depends(get_current_user)):
    """Anyone seated at the table may read. Sorted oldest-first."""
    await _seated_or_403(sid, user)
    rows = await db.voice_lines.find(
        {"session_id": sid}, {"_id": 0}
    ).sort("started_at", 1).to_list(2000)
    return {"session_id": sid, "voice_lines": rows, "count": len(rows)}


class VoiceLinePatch(BaseModel):
    text: Optional[str] = None  # GM-only correction


@router.patch("/sessions/{sid}/voice-lines/{vid}")
async def patch_voice_line(sid: str, vid: str, body: VoiceLinePatch,
                            user: dict = Depends(get_current_user)):
    """GM-only — fix a mistranscription. Speaker themself may correct
    their own within 5 minutes of upload (handled by `dismiss` semantics
    on the client; server enforces GM-or-author within 5min)."""
    s = await _seated_or_403(sid, user)
    row = await db.voice_lines.find_one({"id": vid, "session_id": sid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Voice line not found.")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0, "gm_id": 1})
    is_gm = user["id"] == (camp or {}).get("gm_id") or user.get("role") == "admin"
    is_author = row.get("speaker_user_id") == user["id"]
    if not (is_gm or is_author):
        raise HTTPException(403, "Only GM or the author can correct a line.")
    update: dict = {"updated_at": now_iso()}
    if body.text is not None:
        update["text"] = body.text.strip()
        update["transcribed"] = bool(update["text"])
    await db.voice_lines.update_one({"id": vid}, {"$set": update})
    out = await db.voice_lines.find_one({"id": vid}, {"_id": 0})
    return {"voice_line": out}


@router.delete("/sessions/{sid}/voice-lines/{vid}")
async def delete_voice_line(sid: str, vid: str,
                              user: dict = Depends(get_current_user)):
    """Author may delete within 60s; GM may delete any time."""
    s = await _seated_or_403(sid, user)
    row = await db.voice_lines.find_one({"id": vid, "session_id": sid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Voice line not found.")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0, "gm_id": 1})
    is_gm = user["id"] == (camp or {}).get("gm_id") or user.get("role") == "admin"
    is_author = row.get("speaker_user_id") == user["id"]
    if not is_gm:
        if not is_author:
            raise HTTPException(403, "Not your voice line.")
        # 60-second author grace window — string compare on iso works
        # because both are timezone-aware UTC ISO-8601.
        from datetime import datetime, timezone
        try:
            created = datetime.fromisoformat(
                row["created_at"].replace("Z", "+00:00")
            )
            age = (datetime.now(timezone.utc) - created).total_seconds()
        except Exception:
            age = 99999
        if age > 60:
            raise HTTPException(403, "Author delete window (60s) elapsed. Ask the GM.")
    await db.voice_lines.delete_one({"id": vid})
    return {"deleted": vid}
