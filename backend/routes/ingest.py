"""Knowledge Web mechanic-aware ingestion (V4.4 Phase C).

POST /api/campaigns/{cid}/ingest    multipart/form-data → ingest record id
GET  /api/campaigns/{cid}/ingestions
GET  /api/ingestions/{ingest_id}
POST /api/ingestions/{ingest_id}/accept    {accepted_indices: [...]}
DELETE /api/ingestions/{ingest_id}

Pipeline:
  1. GM uploads PDF / MD / TXT / RTF / DOCX (≤24 MB, GM-or-admin).
  2. Backend parses to plain text:
       PDF → pypdf
       DOCX → python-docx
       RTF → striprtf
       MD/TXT → utf-8 read
  3. Claude Sonnet 4.5 (via emergentintegrations) is asked to produce a
     STRICT JSON document of suggestions across these mechanic types:
         attribute, power_pack, power_bundle, item, weapon, skill,
         npc, location, lore, quest
     Each suggestion is also tagged with an `atelier_phase` hint
     (1-7 of the existing Genesis flow) and an optional `target_arc`
     when one is mentioned by name. Suggestions retain the source
     filename + page/section reference for audit.
  4. The ingest record (the full suggestions list) is stored in the
     `ingestions` Mongo collection so the GM can review at leisure.
  5. On accept, suggestions are persisted as `nodes` (lore/npc/location
     types map directly) or `custom_attributes` (attribute / power_pack /
     power_bundle / item / weapon / skill — these route through the
     existing custom-attribute infrastructure so they show up in the
     Character Builder selector).

Compliance: We DO NOT echo back uploaded text verbatim — Claude is
instructed to summarise mechanic-only and never reproduce rulebook prose.
The ingest record stores only Claude's structured JSON, never the raw file
content (file is parsed in-memory and discarded).
"""
from __future__ import annotations

import io
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.config import EMERGENT_LLM_KEY
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["ingest"])

MAX_BYTES = 24 * 1024 * 1024  # 24 MB

# Map sniffed content-type / extension → parser. Keep extension as fallback
# because some clients don't set the right content-type.
_TEXT_TYPES = {"text/plain", "text/markdown", "text/x-markdown"}
_DOCX_TYPES = {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
_PDF_TYPES = {"application/pdf"}
_RTF_TYPES = {"application/rtf", "text/rtf"}


def _parse_to_text(filename: str, content_type: str, data: bytes) -> str:
    ext = (Path(filename).suffix or "").lower().lstrip(".")
    ct = (content_type or "").lower()
    # PDF
    if ct in _PDF_TYPES or ext == "pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            pages = []
            for i, p in enumerate(reader.pages, start=1):
                t = (p.extract_text() or "").strip()
                if t:
                    pages.append(f"\n\n--- PAGE {i} ---\n{t}")
            return "".join(pages).strip()
        except Exception as e:
            raise HTTPException(400, f"Could not parse PDF: {e}")
    # DOCX
    if ct in _DOCX_TYPES or ext == "docx":
        try:
            from docx import Document
            d = Document(io.BytesIO(data))
            return "\n".join(p.text for p in d.paragraphs if p.text).strip()
        except Exception as e:
            raise HTTPException(400, f"Could not parse DOCX: {e}")
    # RTF
    if ct in _RTF_TYPES or ext == "rtf":
        try:
            from striprtf.striprtf import rtf_to_text
            return rtf_to_text(data.decode("latin-1", errors="ignore")).strip()
        except Exception as e:
            raise HTTPException(400, f"Could not parse RTF: {e}")
    # MD / TXT
    if ct in _TEXT_TYPES or ext in ("md", "txt", "markdown"):
        return data.decode("utf-8", errors="ignore").strip()
    raise HTTPException(400, f"Unsupported file type '{ct}' / .{ext}. Use PDF / MD / TXT / RTF / DOCX.")


def _truncate_for_llm(text: str, hard_cap_chars: int = 60_000) -> str:
    """Claude has plenty of context, but the EMERGENT key is shared. Cap
    the input so a 200-page rulebook doesn't cost hundreds of dollars."""
    if len(text) <= hard_cap_chars:
        return text
    head = text[: int(hard_cap_chars * 0.6)]
    tail = text[-int(hard_cap_chars * 0.4):]
    return head + "\n\n[…truncated for cost…]\n\n" + tail


# ─────────────────────── Pydantic ───────────────────────

class AcceptIn(BaseModel):
    """Indices into `ingest.suggestions` that the GM accepts."""
    accepted_indices: List[int] = Field(default_factory=list)
    overrides: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


# ─── Per-system addendum to the ingest prompt ──────────────────────────
# Branches the category list + page citations + licence reminder so the
# LLM produces system-shaped suggestions.

SYSTEM_ADDENDUM = {
    "besm-4e": (
        "TARGET SYSTEM: BESM 4E (Tri-Stat Emporium licence). Prefer "
        "attribute / skill / defect / power_pack / power_bundle / weapon / "
        "item / location / npc / lore / quest. Page references should cite "
        "BESM 4E (range 1-320). Cost notation: 'N pts/level' for attributes "
        "and skills, '−N pts/rank' for defects."
    ),
    "anime-5e": (
        "TARGET SYSTEM: Anime 5E (Tri-Stat Emporium OGL release). Hybrid "
        "engine — accept BOTH 5E class+slot mechanics AND Tri-Stat point-buy. "
        "Prefer class / heritage / spell / weapon / armor / point_buy_attribute "
        "/ skill / npc / location / lore / quest. Cite Anime 5E SRD pages "
        "(range 1-200). Stats are Body / Mind / Soul, not 5E ability scores."
    ),
    "dnd-5e": (
        "TARGET SYSTEM: D&D 5E (CC-BY SRD 5.1 ONLY). NEVER reproduce "
        "Wizards-trademarked content — no Forgotten Realms, no Mind Flayer, "
        "no Beholder, etc. Prefer class / race / background / spell / "
        "feature / weapon / armor / item / monster / npc / location / quest. "
        "Cite SRD 5.1 page references. Use d20 + ability mod + proficiency "
        "shape for any rolls in the suggestion. Stick to mechanic names, "
        "not lore paragraphs."
    ),
    "cypher": (
        "TARGET SYSTEM: Cypher System (Cypher System Creator licence — Monte "
        "Cook Games). Prefer type / focus / descriptor / cypher / artifact / "
        "ability / npc / location / lore / quest. Cite Cypher SRD/Numenera "
        "page references. Use difficulty (1-10) × 3 = TN format. Stats are "
        "Might / Speed / Intellect with Edge and Effort. NEVER reproduce "
        "flavour prose — names + mechanic terms only."
    ),
}


# ─────────────────────── Claude prompt ───────────────────────

SYSTEM_PROMPT = """You are TableGnostic's Knowledge Web ingestor.

Given a raw text dump from a GM-uploaded document (rulebook excerpt,
campaign notes, player handout, world bible), you produce a STRICT JSON
document of mechanic-aware suggestions for the campaign's Knowledge Web.

Hard rules:
  1. NEVER reproduce rulebook prose, lore paragraphs, examples, or
     stat-block descriptions verbatim. Summarise mechanic-only:
     names, page references, point costs, rank/level numerics.
     This is a Tri-Stat Emporium licence requirement.
  2. Output MUST be valid JSON. No markdown fences. No commentary.
  3. Use ONLY these category strings for `kind`:
       "attribute", "power_pack", "power_bundle", "item", "weapon",
       "skill", "npc", "location", "lore", "quest"
  4. Every suggestion includes:
       kind, title (short),
       summary (≤ 240 chars, mechanic-only — NO copyrighted prose),
       fields (object: cost_per_level | rank | points_per_rank |
               page | category | tags),
       atelier_phase (integer 1-7 — best-fit Genesis phase),
       target_arc (string or null — only if document names an arc),
       source_ref (string — page or section anchor).
  5. atelier_phase mapping:
       1 = Sentence (concept), 2 = Theme & tone, 3 = Cast & setting,
       4 = Master plot acts, 5 = Session prep, 6 = Live play, 7 = Wrap-up.
  6. If the document is a rules excerpt: prefer attribute/power_pack/
     power_bundle/item/weapon/skill. If it's a setting bible: prefer
     npc/location/lore. If it's a quest brief: prefer quest/npc/location.
  7. Cap your response at 60 suggestions. Quality over quantity.

Top-level shape:
{
  "summary": "≤ 200 chars overview of what was ingested.",
  "detected_kind_counts": { "attribute": 4, "skill": 2, ... },
  "suggestions": [
    { "kind": "attribute", "title": "...", "summary": "...",
      "fields": {...}, "atelier_phase": 4, "target_arc": null,
      "source_ref": "p.142" },
    ...
  ]
}
"""


async def _call_claude(filename: str, system_id: Optional[str], text: str) -> Dict[str, Any]:
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured")
    addendum = SYSTEM_ADDENDUM.get(system_id or "besm-4e", SYSTEM_ADDENDUM["besm-4e"])
    user_prompt = (
        f"# Source file: {filename}\n"
        f"# Target system: {system_id or 'besm-4e (default)'}\n"
        f"# System addendum:\n{addendum}\n\n"
        f"{_truncate_for_llm(text)}\n\n"
        f"Now produce the JSON document per the hard rules + the system addendum above."
    )
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ingest-{filename[:32]}",
            system_message=SYSTEM_PROMPT,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        raw = await chat.send_message(UserMessage(text=user_prompt))
    except Exception as e:
        raise HTTPException(502, f"Claude call failed: {e}")

    # Defensive JSON extraction (in case the model wraps despite instructions).
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except Exception:
        # Try to grab the largest {...} block.
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            raise HTTPException(502, "Claude returned non-JSON output; try again.")
        try:
            parsed = json.loads(m.group(0))
        except Exception as e:
            raise HTTPException(502, f"Claude JSON malformed: {e}")
    # Normalise.
    if not isinstance(parsed, dict):
        raise HTTPException(502, "Claude JSON must be an object.")
    parsed.setdefault("summary", "")
    parsed.setdefault("detected_kind_counts", {})
    sugs = parsed.get("suggestions", [])
    if not isinstance(sugs, list):
        sugs = []
    # Cap & lightly validate each suggestion.
    out_sugs: List[Dict[str, Any]] = []
    valid_kinds = {"attribute", "power_pack", "power_bundle", "item", "weapon",
                   "skill", "npc", "location", "lore", "quest"}
    for s in sugs[:60]:
        if not isinstance(s, dict):
            continue
        kind = s.get("kind", "lore")
        if kind not in valid_kinds:
            kind = "lore"
        out_sugs.append({
            "kind": kind,
            "title": (s.get("title") or "Untitled")[:120],
            "summary": (s.get("summary") or "")[:300],
            "fields": s.get("fields") or {},
            "atelier_phase": int(s.get("atelier_phase") or 4),
            "target_arc": s.get("target_arc"),
            "source_ref": s.get("source_ref") or "",
            "accepted": False,
        })
    parsed["suggestions"] = out_sugs
    return parsed


# ─────────────────────── Endpoints ───────────────────────

@router.post("/campaigns/{cid}/ingest")
async def create_ingestion(cid: str,
                            file: UploadFile = File(...),
                            user: dict = Depends(get_current_user)):
    """GM/admin uploads a file → Claude returns categorised mechanic
    suggestions. The ingest record is persisted in `ingestions`."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may ingest documents.")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"File exceeds {MAX_BYTES // (1024*1024)} MB cap.")
    if len(raw) == 0:
        raise HTTPException(400, "Empty file.")

    text = _parse_to_text(file.filename, file.content_type or "", raw)
    if not text:
        raise HTTPException(400, "Could not extract text from file.")
    parsed = await _call_claude(file.filename, camp.get("system_id"), text)

    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "filename": file.filename,
        "content_type": file.content_type,
        "byte_size": len(raw),
        "extracted_chars": len(text),
        "summary": parsed["summary"],
        "detected_kind_counts": parsed["detected_kind_counts"],
        "suggestions": parsed["suggestions"],
        "status": "pending",
        "by_user_id": user["id"],
        "by_user_name": user["name"],
        "created_at": now_iso(),
    }
    await db.ingestions.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{cid}/ingestions")
async def list_ingestions(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM only.")
    rows = await db.ingestions.find({"campaign_id": cid}, {"_id": 0}) \
                                .sort("created_at", -1).to_list(40)
    return rows


@router.get("/ingestions/{ingest_id}")
async def get_ingestion(ingest_id: str, user: dict = Depends(get_current_user)):
    doc = await db.ingestions.find_one({"id": ingest_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Ingestion not found")
    camp = await db.campaigns.find_one({"id": doc["campaign_id"]}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user.get("role") != "admin"):
        raise HTTPException(403, "GM only.")
    return doc


@router.post("/ingestions/{ingest_id}/accept")
async def accept_suggestions(ingest_id: str, body: AcceptIn,
                              user: dict = Depends(get_current_user)):
    """Persist accepted suggestions:
      * lore / npc / location / quest → `nodes` collection.
      * attribute / power_pack / power_bundle / item / weapon / skill →
        `custom_attributes` collection (so they appear in Character Builder).
    """
    doc = await db.ingestions.find_one({"id": ingest_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Ingestion not found")
    camp = await db.campaigns.find_one({"id": doc["campaign_id"]}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user.get("role") != "admin"):
        raise HTTPException(403, "GM only.")

    sugs = doc.get("suggestions", [])
    accepted_results: List[Dict[str, Any]] = []
    NODE_KINDS = {"lore", "npc", "location", "quest"}

    for idx in body.accepted_indices:
        if idx < 0 or idx >= len(sugs):
            continue
        # Idempotency: skip already-accepted indices so re-clicking the
        # accept button never creates duplicate nodes / custom_attributes.
        if sugs[idx].get("accepted"):
            continue
        s = dict(sugs[idx])
        # Apply GM overrides if present.
        ov = body.overrides.get(idx) or body.overrides.get(str(idx)) or {}
        if isinstance(ov, dict):
            for k in ("title", "summary", "kind", "atelier_phase", "target_arc"):
                if k in ov:
                    s[k] = ov[k]
            if isinstance(ov.get("fields"), dict):
                s["fields"] = {**(s.get("fields") or {}), **ov["fields"]}

        kind = s["kind"]
        result: Dict[str, Any] = {"index": idx, "kind": kind, "title": s["title"]}

        if kind in NODE_KINDS:
            node_type = {"lore": "lore", "npc": "npc",
                         "location": "location", "quest": "quest"}[kind]
            node = {
                "id": new_id(),
                "campaign_id": doc["campaign_id"],
                "type": node_type,
                "title": s["title"],
                "content": s.get("summary", ""),
                "tags": ["ingest", f"atelier-phase-{s.get('atelier_phase',4)}"],
                "visibility": "gm_only",
                "revealed_to": [],
                "links": [],
                "fields": {
                    **(s.get("fields") or {}),
                    "ingest_id": ingest_id,
                    "source_ref": s.get("source_ref"),
                    "atelier_phase": s.get("atelier_phase"),
                    "target_arc": s.get("target_arc"),
                },
                "author_id": user["id"],
                "author_name": user["name"],
                "created_at": now_iso(),
            }
            await db.nodes.insert_one(node)
            result["created"] = "node"
            result["id"] = node["id"]
        else:
            # attribute / power_pack / power_bundle / item / weapon / skill
            ca = {
                "id": new_id(),
                "campaign_id": doc["campaign_id"],
                "kind": kind,
                "name": s["title"],
                "category": (s.get("fields") or {}).get("category", kind),
                "cost_per_level": int((s.get("fields") or {}).get("cost_per_level", 1) or 1),
                "page": (s.get("fields") or {}).get("page"),
                "note": s.get("summary", ""),
                "fields": s.get("fields") or {},
                "ingest_id": ingest_id,
                "atelier_phase": s.get("atelier_phase"),
                "target_arc": s.get("target_arc"),
                "source_ref": s.get("source_ref"),
                "created_at": now_iso(),
                "author_id": user["id"],
                "author_name": user["name"],
            }
            await db.custom_attributes.insert_one(ca)
            result["created"] = "custom_attribute"
            result["id"] = ca["id"]

        # Mark the suggestion accepted in the ingest record.
        sugs[idx]["accepted"] = True
        sugs[idx]["created_kind"] = result["created"]
        sugs[idx]["created_id"] = result["id"]
        accepted_results.append(result)

    await db.ingestions.update_one(
        {"id": ingest_id},
        {"$set": {
            "suggestions": sugs,
            "status": "accepted" if all(s.get("accepted") for s in sugs) else "partial",
            "last_accepted_at": now_iso(),
            "last_accepted_by": user["name"],
        }},
    )
    return {"ok": True, "accepted": accepted_results,
            "ingest_id": ingest_id, "remaining": sum(1 for s in sugs if not s.get("accepted"))}


@router.delete("/ingestions/{ingest_id}")
async def delete_ingestion(ingest_id: str,
                            user: dict = Depends(get_current_user)):
    doc = await db.ingestions.find_one({"id": ingest_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Ingestion not found")
    camp = await db.campaigns.find_one({"id": doc["campaign_id"]}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user.get("role") != "admin"):
        raise HTTPException(403, "GM only.")
    await db.ingestions.delete_one({"id": ingest_id})
    return {"ok": True, "deleted_id": ingest_id}
