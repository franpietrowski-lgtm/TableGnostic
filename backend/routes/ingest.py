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

MAX_BYTES = 64 * 1024 * 1024  # 64 MB — V6.16 raise (was 24 MB) so a single
# campaign-bible upload can carry old + new Evereantha + Artisan Tale combined.

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


def _truncate_for_llm(text: str, hard_cap_chars: int = 240_000) -> str:
    """Claude Sonnet 4.5 has a 200k-token context (~600k chars). The
    EMERGENT key is shared, so we cap input at 240k chars (≈ 80k tokens)
    per call — comfortably enough for a 1.5×Evereantha+Artisan-Tale doc
    while keeping per-call cost predictable. V6.16 raised from 60k.

    For larger files, prefer the Atelier Intake Template (markdown
    `## SECTION` blocks) — the chunked endpoint splits by section so each
    Claude call gets focused context instead of a single big-truncated read.
    """
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

@router.post("/campaigns/{cid}/ingest-preview")
async def preview_ingestion(cid: str,
                             file: UploadFile = File(...),
                             user: dict = Depends(get_current_user)):
    """PARSE-ONLY preview — no LLM call, no persistence. The GM sees
    exactly what text we extracted and can decide whether to commit
    (which then fires Claude). Returns an excerpt (first ~2 KB) plus
    file meta so the UI can surface clarity checks, OCR failures, and
    weird PDF parse artefacts BEFORE spending LLM budget.

    Response shape:
      { filename, content_type, byte_size, extracted_chars,
        excerpt_head, excerpt_tail, paragraph_count, system_id }
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may preview an ingestion.")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"File exceeds {MAX_BYTES // (1024*1024)} MB cap.")
    if len(raw) == 0:
        raise HTTPException(400, "Empty file.")

    text = _parse_to_text(file.filename, file.content_type or "", raw)
    if not text:
        raise HTTPException(400, "Could not extract text from file.")

    # Keep excerpts small — the point is clarity review, not a full
    # read-back. Head + tail lets the GM spot both "table-of-contents
    # pollution at the start" and "footnote cruft at the end" failures.
    head_limit = 1800
    tail_limit = 900
    clean = text.strip()
    head = clean[:head_limit]
    tail = clean[-tail_limit:] if len(clean) > head_limit + tail_limit else ""
    paragraphs = [p for p in re.split(r"\n\s*\n", clean) if p.strip()]

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "byte_size": len(raw),
        "extracted_chars": len(clean),
        "excerpt_head": head,
        "excerpt_tail": tail,
        "paragraph_count": len(paragraphs),
        "system_id": camp.get("system_id"),
        "preview_only": True,
    }


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


# ─────────────────────── One-Shot Scaffold ───────────────────────
SCAFFOLD_SYSTEM_PROMPT = """You are TableGnostic's One-Shot Scaffolder.

Given a raw text dump from a published one-shot adventure, GM module,
or campaign brief, you produce a STRICT JSON document a GM can deploy
in 60 seconds: opening session beats, a starter NPC roster with stat
hints, an opening encounter draft, and 5-10 Codex nodes (locations,
factions, lore beats).

Hard rules:
  1. NEVER reproduce rulebook prose, room boxed text, or lore paragraphs
     verbatim. Mechanic-only summaries; reword the rest.
  2. Output MUST be valid JSON. No markdown fences.
  3. Stat-block hints are MECHANIC-ONLY — names, page references, CR or
     level, nothing else. The host system field tells you which numbers
     matter (CR for D&D, level for Cypher, point total for BESM).
  4. Every NPC carries: name, role (minion/henchman/villain/nemesis/ally),
     intent (one-line current goal), stat_hint{cr|level|total_points|notes}.
  5. Cap at 30 codex nodes, 12 NPCs, 1 opening encounter.

Top-level shape:
{
  "summary": "≤ 200 chars overview of what this one-shot is.",
  "title_suggestion": "short campaign name to suggest",
  "premise": "≤ 400 chars premise / hook for the opening session",
  "session_beats": ["beat 1", "beat 2", "beat 3", ...],
  "codex_nodes": [
    {"type": "location|npc|faction|lore", "title": "...",
     "summary": "≤ 240 chars mechanic+narrative summary",
     "tags": [...]}
  ],
  "npcs": [
    {"name": "...", "role": "villain", "intent": "...",
     "stat_hint": {"cr": "1/4"} | {"level": 4} | {"total_points": 120}}
  ],
  "opening_encounter": {
    "name": "Opening Strike",
    "environment": {"indoor": true, "weather": "rain"},
    "npc_indices": [0, 1, 2],   // pick the first NPCs above
    "notes": "≤ 240 chars setup / GM notes"
  }
}
"""


async def _call_scaffold(filename: str, system_id: Optional[str], text: str) -> Dict[str, Any]:
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured")
    user_prompt = (
        f"# Source one-shot: {filename}\n"
        f"# Target system: {system_id or 'besm-4e'}\n\n"
        f"{_truncate_for_llm(text)}\n\n"
        "Now scaffold the one-shot per the hard rules above."
    )
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"scaffold-{filename[:32]}",
            system_message=SCAFFOLD_SYSTEM_PROMPT,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        raw = await chat.send_message(UserMessage(text=user_prompt))
    except Exception as e:
        raise HTTPException(502, f"Claude call failed: {e}")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            raise HTTPException(502, "Claude returned non-JSON output; try again.")
        try:
            parsed = json.loads(m.group(0))
        except Exception as e:
            raise HTTPException(502, f"Claude JSON malformed: {e}")
    if not isinstance(parsed, dict):
        raise HTTPException(502, "Scaffold JSON must be an object.")
    parsed.setdefault("summary", "")
    parsed.setdefault("title_suggestion", "")
    parsed.setdefault("premise", "")
    parsed.setdefault("session_beats", [])
    parsed.setdefault("codex_nodes", [])
    parsed.setdefault("npcs", [])
    parsed.setdefault("opening_encounter", {})
    return parsed


@router.post("/campaigns/{cid}/scaffold-oneshot")
async def scaffold_oneshot(cid: str,
                            commit: bool = False,
                            file: UploadFile = File(...),
                            user: dict = Depends(get_current_user)):
    """GM uploads a published one-shot PDF/TXT/DOCX → Claude scaffolds it
    into a deploy-ready blob (codex nodes, NPCs, opening encounter).

    `commit=false` (default) returns the parsed structure as a dry-run
    preview. `commit=true` writes:
       · each `codex_nodes[]` entry as a `db.nodes` document (gm-only)
       · each NPC as a Codex `npc` node (gm-only)
       · the `opening_encounter` as a draft on the campaign's Director doc
    Idempotent — a re-commit creates fresh nodes (not deduped).
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "GM only.")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"File exceeds {MAX_BYTES // (1024*1024)} MB cap.")
    if len(raw) == 0:
        raise HTTPException(400, "Empty file.")
    text = _parse_to_text(file.filename, file.content_type or "", raw)
    if not text:
        raise HTTPException(400, "Could not extract text from file.")
    parsed = await _call_scaffold(file.filename, camp.get("system_id"), text)

    if not commit:
        return {"committed": False, "preview": parsed}

    # Commit path — write nodes + a Director encounter draft.
    nodes_created: List[Dict[str, Any]] = []
    for cn in parsed.get("codex_nodes", []) or []:
        node = {
            "id": new_id(),
            "campaign_id": cid,
            "title": cn.get("title", "Untitled"),
            "type": cn.get("type", "lore"),
            "content": cn.get("summary", ""),
            "tags": (cn.get("tags") or []) + ["one-shot-scaffold"],
            "visibility": "gm_only",
            "revealed_to": [],
            "fields": {"source": "scaffold-oneshot"},
            "author_id": user["id"],
            "author_name": user.get("name") or user.get("email"),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        await db.nodes.insert_one(dict(node))
        nodes_created.append({"id": node["id"], "title": node["title"], "type": node["type"]})

    npc_node_ids: List[str] = []
    for n in parsed.get("npcs", []) or []:
        node = {
            "id": new_id(),
            "campaign_id": cid,
            "title": n.get("name", "Unknown NPC"),
            "type": "npc",
            "content": (n.get("intent") or "")[:500],
            "tags": ["one-shot-scaffold", n.get("role") or "minion"],
            "visibility": "gm_only",
            "revealed_to": [],
            "fields": {"intent": n.get("intent", ""),
                       "role": n.get("role", "minion"),
                       "stat_hint": n.get("stat_hint", {})},
            "author_id": user["id"],
            "author_name": user.get("name") or user.get("email"),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        await db.nodes.insert_one(dict(node))
        npc_node_ids.append(node["id"])

    # Stage the opening encounter on the Director's doc.
    enc = parsed.get("opening_encounter") or {}
    if enc:
        director = await db.directors.find_one({"campaign_id": cid}, {"_id": 0})
        if not director:
            director = {"campaign_id": cid, "encounters": [],
                        "current_location": "", "current_phase_ref": "",
                        "updated_at": now_iso()}
        npc_indices = enc.get("npc_indices") or list(range(min(3, len(parsed.get("npcs", [])))))
        npcs_for_encounter = []
        for i in npc_indices:
            if i < 0 or i >= len(parsed.get("npcs", [])):
                continue
            n = parsed["npcs"][i]
            sh = n.get("stat_hint", {}) or {}
            npcs_for_encounter.append({
                "id": new_id(),
                "name": n.get("name", "NPC"),
                "role": n.get("role", "minion"),
                "source": "codex",
                "source_id": npc_node_ids[i] if i < len(npc_node_ids) else None,
                "location": "",
                "state": "active",
                "intent": n.get("intent", ""),
                "cr": sh.get("cr"),
                "level": sh.get("level"),
                "total_points": sh.get("total_points"),
                "count": 1,
                "notes": sh.get("notes", ""),
            })
        director["encounters"] = list(director.get("encounters") or [])
        director["encounters"].append({
            "id": new_id(),
            "name": enc.get("name") or "Opening Encounter",
            "party_character_ids": [],
            "npcs": npcs_for_encounter,
            "environment": enc.get("environment") or {},
            "notes": enc.get("notes") or "",
        })
        director["updated_at"] = now_iso()
        await db.directors.replace_one({"campaign_id": cid}, director, upsert=True)

    return {
        "committed": True,
        "summary": parsed.get("summary"),
        "title_suggestion": parsed.get("title_suggestion"),
        "premise": parsed.get("premise"),
        "session_beats": parsed.get("session_beats"),
        "nodes_created": len(nodes_created),
        "npcs_created": len(npc_node_ids),
        "encounter_staged": bool(enc),
    }



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
