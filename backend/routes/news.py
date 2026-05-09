"""TableGnostic Gazette — V6.25.38.

Old-timey newspaper for every campaign:
  * Front-page editorial articles (LLM-drafted from session events; GM
    curates, edits, approves; "Press the Issue" bundles approved drafts
    into a numbered issue).
  * Box-score leaderboards (kills, XP, sessions attended) — public-facing,
    sports-page styling on the frontend.
  * Public surface at `/discover/{slug}/gazette` for any campaign with
    `discover_published=true`.

Routes (auth):
    POST   /api/campaigns/{cid}/news/articles               — manual create (GM)
    GET    /api/campaigns/{cid}/news/articles               — list (any seated)
    PATCH  /api/campaigns/{cid}/news/articles/{aid}         — edit (GM)
    DELETE /api/campaigns/{cid}/news/articles/{aid}         — delete (GM)
    POST   /api/campaigns/{cid}/news/draft-from-session/{sid} — LLM draft (GM)
    POST   /api/campaigns/{cid}/news/issues                 — Press the Issue (GM)
    GET    /api/campaigns/{cid}/news/issues                 — list issues (any seated)
    POST   /api/campaigns/{cid}/news/log-kill               — record a kill (GM)
    GET    /api/campaigns/{cid}/news/leaderboards           — kills / xp / sessions

Routes (public):
    GET    /api/public/news/{slug}/issues/latest            — latest published issue
    GET    /api/public/news/{slug}/leaderboards             — public leaderboards
"""
import json
import re
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.config import EMERGENT_LLM_KEY
from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["news"])

VALID_COLUMNS = {"front", "world", "marketplace", "obituaries"}
VALID_STATUSES = {"draft", "approved", "published"}


# ── Pydantic models ───────────────────────────────────────────────
class ArticleIn(BaseModel):
    headline: str = Field(min_length=1, max_length=160)
    kicker: Optional[str] = Field(default="", max_length=80)
    byline: Optional[str] = Field(default="", max_length=80)
    body: str = Field(min_length=1, max_length=4000)
    column: str = Field(default="front")


class ArticlePatch(BaseModel):
    headline: Optional[str] = Field(default=None, max_length=160)
    kicker: Optional[str] = Field(default=None, max_length=80)
    byline: Optional[str] = Field(default=None, max_length=80)
    body: Optional[str] = Field(default=None, max_length=4000)
    column: Optional[str] = None
    status: Optional[str] = None


class KillIn(BaseModel):
    character_id: str
    foe_name: str = Field(min_length=1, max_length=120)
    foe_kind: Optional[str] = Field(default="", max_length=60)
    session_id: Optional[str] = ""


class IssueIn(BaseModel):
    masthead: Optional[str] = Field(default="", max_length=80)
    date_label: Optional[str] = Field(default="", max_length=60)


# ── Helpers ───────────────────────────────────────────────────────
async def _campaign_or_404(cid: str) -> dict:
    c = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Campaign not found.")
    return c


def _is_seated(camp: dict, user: dict) -> bool:
    if user.get("role") == "admin":
        return True
    return user["id"] == camp.get("gm_id") or user["id"] in (camp.get("member_ids") or [])


def _is_gm(camp: dict, user: dict) -> bool:
    return user.get("role") == "admin" or user["id"] == camp.get("gm_id")


def _strip_fences(text: str) -> str:
    s = (text or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    return s


# ── Article CRUD ──────────────────────────────────────────────────
@router.post("/campaigns/{cid}/news/articles")
async def create_article(cid: str, body: ArticleIn,
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may file articles.")
    if body.column not in VALID_COLUMNS:
        raise HTTPException(400, f"column must be one of {sorted(VALID_COLUMNS)}")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "headline": body.headline.strip(),
        "kicker": (body.kicker or "").strip(),
        "byline": (body.byline or "").strip() or "By the Gazette",
        "body": body.body.strip(),
        "column": body.column,
        "status": "draft",
        "issue_id": None,
        "source_event_ids": [],
        "generated_by_llm": False,
        "author_id": user["id"],
        "created_at": now_iso(),
        "published_at": None,
    }
    await db.news_articles.insert_one(doc)
    return sanitize(doc)


@router.get("/campaigns/{cid}/news/articles")
async def list_articles(cid: str, user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    rows = await db.news_articles.find(
        {"campaign_id": cid}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return {"articles": rows}


@router.patch("/campaigns/{cid}/news/articles/{aid}")
async def patch_article(cid: str, aid: str, body: ArticlePatch,
                         user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may edit articles.")
    art = await db.news_articles.find_one({"id": aid, "campaign_id": cid}, {"_id": 0})
    if not art:
        raise HTTPException(404, "Article not found.")
    update: dict = {}
    for field in ("headline", "kicker", "byline", "body"):
        v = getattr(body, field)
        if v is not None:
            update[field] = v.strip() if isinstance(v, str) else v
    if body.column is not None:
        if body.column not in VALID_COLUMNS:
            raise HTTPException(400, f"column must be one of {sorted(VALID_COLUMNS)}")
        update["column"] = body.column
    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")
        # Note: 'published' state is reserved for issue press; allow draft/approved here.
        if body.status == "published":
            raise HTTPException(400, "Use POST /news/issues to publish — articles enter 'published' via Press the Issue.")
        update["status"] = body.status
    if not update:
        return sanitize(art)
    await db.news_articles.update_one({"id": aid, "campaign_id": cid}, {"$set": update})
    fresh = await db.news_articles.find_one({"id": aid, "campaign_id": cid}, {"_id": 0})
    return sanitize(fresh)


@router.delete("/campaigns/{cid}/news/articles/{aid}")
async def delete_article(cid: str, aid: str,
                          user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may delete articles.")
    r = await db.news_articles.delete_one({"id": aid, "campaign_id": cid})
    if r.deleted_count == 0:
        raise HTTPException(404, "Article not found.")
    return {"ok": True}


# ── LLM auto-draft ────────────────────────────────────────────────
@router.post("/campaigns/{cid}/news/draft-from-session/{sid}")
async def draft_from_session(cid: str, sid: str,
                              user: dict = Depends(get_current_user)):
    """LLM reads session chat / voice / kills and returns 3-5 article drafts.

    Drafts are inserted as `status="draft"` so the GM can review, edit, and
    approve before pressing the issue. Body length is targeted ~80-150 words
    each in period-appropriate broadsheet voice.
    """
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may draft articles from sessions.")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "LLM key not configured.")

    sess = await db.sessions.find_one({"id": sid, "campaign_id": cid}, {"_id": 0})
    if not sess:
        raise HTTPException(404, "Session not found.")

    chat = await db.chat_logs.find(
        {"session_id": sid}, {"_id": 0, "kind": 1, "text": 1, "actor_name": 1, "created_at": 1}
    ).sort("created_at", 1).to_list(400)
    voice = await db.voice_lines.find(
        {"session_id": sid}, {"_id": 0, "transcript": 1, "character_name": 1, "created_at": 1}
    ).sort("created_at", 1).to_list(200)
    kills = await db.news_kills.find(
        {"campaign_id": cid, "session_id": sid}, {"_id": 0}
    ).to_list(200)

    chat_block = "\n".join(
        f"  [{r.get('kind') or 'note'}] {r.get('actor_name') or '—'}: {(r.get('text') or '')[:300]}"
        for r in chat[:120]
    ) or "  (no chat logs)"
    voice_block = "\n".join(
        f"  {r.get('character_name') or 'unknown'}: {(r.get('transcript') or '')[:300]}"
        for r in voice[:80]
    ) or "  (no voice lines)"
    kills_block = "\n".join(
        f"  {k.get('character_name','?')} felled {k.get('foe_name','?')} ({k.get('foe_kind','foe')})"
        for k in kills
    ) or "  (no kills logged this session)"

    system_prompt = (
        "You are the editor of The TableGnostic Gazette, an old-timey "
        "broadsheet that chronicles a tabletop role-playing campaign in "
        "period-appropriate voice (think 1880s newspaper). You draft "
        "headlines that are punchy, kickers that tease, bylines that name "
        "a fictional reporter, and bodies of 80-150 words written like "
        "front-page editorial. NEVER invent player real names — use the "
        "in-character names from the source materials only. Output strict "
        "JSON only, no commentary, no markdown fences."
    )
    user_prompt = (
        f"CAMPAIGN: {camp.get('name')}  ·  System: {camp.get('system_id')}\n"
        f"GM: {camp.get('gm_name','—')}\n"
        f"Session #{sess.get('session_no', '?')} — {sess.get('title') or 'Untitled'}\n\n"
        f"--- CHAT LOGS ---\n{chat_block}\n\n"
        f"--- VOICE (in-character) ---\n{voice_block}\n\n"
        f"--- KILLS ---\n{kills_block}\n\n"
        "Produce 3-5 article drafts as JSON: "
        "{\"articles\": [{\"headline\":\"\",\"kicker\":\"\",\"byline\":\"\","
        "\"body\":\"\",\"column\":\"front|world|marketplace|obituaries\"}]}. "
        "Pick `column` thoughtfully: front = the marquee plot beat; world = "
        "ambient lore / faction / location notes; marketplace = trade, "
        "treasure, crafted goods; obituaries = deaths, grand defeats, lost "
        "ships. Keep bodies tight, punchy, and tasty — this is a *gazette*, "
        "not a recap log."
    )

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"news-draft-{cid}-{sid}",
            system_message=system_prompt,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        raw = await chat_client.send_message(UserMessage(text=user_prompt))
    except Exception as e:
        print(f"[news_draft:error] cid={cid} sid={sid} -> {e}")
        raise HTTPException(502, "Gazette draft generation failed — try again.")

    text = _strip_fences(raw or "")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise HTTPException(502, "Gazette returned unparseable copy.")
        try:
            payload = json.loads(m.group(0))
        except json.JSONDecodeError:
            raise HTTPException(502, "Gazette returned unparseable copy.")

    arts = payload.get("articles") or []
    if not isinstance(arts, list) or len(arts) == 0:
        raise HTTPException(502, "Gazette returned no articles.")

    drafted = []
    for a in arts[:5]:
        col = (a.get("column") or "front").lower().strip()
        if col not in VALID_COLUMNS:
            col = "front"
        doc = {
            "id": new_id(),
            "campaign_id": cid,
            "headline": (a.get("headline") or "Untitled Dispatch").strip()[:160],
            "kicker": (a.get("kicker") or "").strip()[:80],
            "byline": (a.get("byline") or "By the Gazette").strip()[:80],
            "body": (a.get("body") or "").strip()[:4000],
            "column": col,
            "status": "draft",
            "issue_id": None,
            "source_event_ids": [sid],
            "generated_by_llm": True,
            "author_id": user["id"],
            "created_at": now_iso(),
            "published_at": None,
        }
        await db.news_articles.insert_one(doc)
        drafted.append(sanitize(doc))
    return {"drafted": drafted, "count": len(drafted)}


# ── Press the Issue ───────────────────────────────────────────────
@router.post("/campaigns/{cid}/news/issues")
async def press_the_issue(cid: str, body: IssueIn,
                           user: dict = Depends(get_current_user)):
    """Bundle every `status='approved'` article for this campaign into a
    new numbered issue, mark them `status='published'`, and stamp the
    issue's published_at."""
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may press an issue.")
    approved = await db.news_articles.find(
        {"campaign_id": cid, "status": "approved"}, {"_id": 0, "id": 1}
    ).to_list(500)
    if not approved:
        raise HTTPException(400, "No approved articles to press. Approve drafts first.")
    last = await db.news_issues.find_one(
        {"campaign_id": cid}, {"_id": 0, "issue_number": 1}, sort=[("issue_number", -1)]
    )
    next_no = int((last or {}).get("issue_number", 0)) + 1

    issue_id = new_id()
    pub_iso = now_iso()
    masthead = (body.masthead or "").strip() or f"The {camp.get('name','Campaign')} Gazette"
    date_label = (body.date_label or "").strip() or pub_iso[:10]

    issue = {
        "id": issue_id,
        "campaign_id": cid,
        "issue_number": next_no,
        "masthead": masthead[:80],
        "date_label": date_label[:60],
        "article_ids": [a["id"] for a in approved],
        "published_at": pub_iso,
    }
    await db.news_issues.insert_one(issue)
    await db.news_articles.update_many(
        {"campaign_id": cid, "status": "approved"},
        {"$set": {"status": "published", "issue_id": issue_id, "published_at": pub_iso}},
    )
    return sanitize(issue)


@router.get("/campaigns/{cid}/news/issues")
async def list_issues(cid: str, user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    rows = await db.news_issues.find(
        {"campaign_id": cid}, {"_id": 0}
    ).sort("issue_number", -1).to_list(60)
    return {"issues": rows}


# ── Kills + Leaderboards ──────────────────────────────────────────
@router.post("/campaigns/{cid}/news/log-kill")
async def log_kill(cid: str, body: KillIn,
                   user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_gm(camp, user):
        raise HTTPException(403, "Only the GM may log kills.")
    ch = await db.characters.find_one(
        {"id": body.character_id, "campaign_id": cid}, {"_id": 0, "name": 1, "owner_id": 1}
    )
    if not ch:
        raise HTTPException(404, "Character not found in this campaign.")
    doc = {
        "id": new_id(),
        "campaign_id": cid,
        "character_id": body.character_id,
        "character_name": ch.get("name", "Unknown"),
        "owner_id": ch.get("owner_id"),
        "foe_name": body.foe_name.strip(),
        "foe_kind": (body.foe_kind or "").strip(),
        "session_id": body.session_id or "",
        "recorded_at": now_iso(),
        "recorded_by": user["id"],
    }
    await db.news_kills.insert_one(doc)
    return sanitize(doc)


async def _build_leaderboards(cid: str) -> dict:
    """Aggregate kills + XP + sessions seated. Returns ranked tables."""
    # Per-character kill totals
    kill_pipeline = [
        {"$match": {"campaign_id": cid}},
        {"$group": {
            "_id": "$character_id",
            "character_name": {"$first": "$character_name"},
            "kills": {"$sum": 1},
            "last_kill_at": {"$max": "$recorded_at"},
        }},
        {"$sort": {"kills": -1, "last_kill_at": -1}},
        {"$limit": 50},
    ]
    kill_rows = []
    async for r in db.news_kills.aggregate(kill_pipeline):
        kill_rows.append({
            "character_id": r["_id"],
            "character_name": r.get("character_name", "Unknown"),
            "kills": r["kills"],
            "last_kill_at": r.get("last_kill_at"),
        })

    # Per-character XP totals (from character.xp_total). Newest = highest = topline.
    chars = await db.characters.find(
        {"campaign_id": cid},
        {"_id": 0, "id": 1, "name": 1, "xp_total": 1, "owner_id": 1, "owner_name": 1},
    ).to_list(500)
    xp_rows = sorted(
        [
            {
                "character_id": c["id"],
                "character_name": c.get("name", "Unknown"),
                "xp_total": float(c.get("xp_total", 0) or 0),
                "owner_id": c.get("owner_id"),
                "owner_name": c.get("owner_name"),
            }
            for c in chars
        ],
        key=lambda x: x["xp_total"],
        reverse=True,
    )[:50]

    # Per-character session count (distinct session_id in chat_logs by actor=character)
    # Lighter: count how many sessions a character "appears" in via voice_lines.
    sess_pipeline = [
        {"$match": {"campaign_id": cid}},
        {"$group": {
            "_id": "$character_id",
            "character_name": {"$first": "$character_name"},
            "sessions": {"$addToSet": "$session_id"},
        }},
        {"$project": {
            "character_name": 1,
            "session_count": {"$size": "$sessions"},
        }},
        {"$sort": {"session_count": -1}},
        {"$limit": 50},
    ]
    sess_rows = []
    async for r in db.voice_lines.aggregate(sess_pipeline):
        sess_rows.append({
            "character_id": r["_id"],
            "character_name": r.get("character_name", "Unknown"),
            "session_count": r["session_count"],
        })

    # Player-level rollup (sum of their characters)
    by_player: dict = {}
    for c in chars:
        oid = c.get("owner_id") or "unknown"
        oname = c.get("owner_name") or "Unknown Player"
        by_player.setdefault(oid, {
            "owner_id": oid, "owner_name": oname,
            "character_count": 0, "total_xp": 0.0,
        })
        by_player[oid]["character_count"] += 1
        by_player[oid]["total_xp"] += float(c.get("xp_total", 0) or 0)
    player_rows = sorted(by_player.values(), key=lambda x: x["total_xp"], reverse=True)[:50]

    return {
        "kills": kill_rows,
        "xp": xp_rows,
        "sessions": sess_rows,
        "players": player_rows,
    }


@router.get("/campaigns/{cid}/news/leaderboards")
async def get_leaderboards(cid: str, user: dict = Depends(get_current_user)):
    camp = await _campaign_or_404(cid)
    if not _is_seated(camp, user):
        raise HTTPException(403, "Not seated at this table.")
    return await _build_leaderboards(cid)


# ── Public surfaces (no auth) ─────────────────────────────────────
async def _public_camp_or_404(slug: str) -> dict:
    c = await db.campaigns.find_one(
        {"discover_slug": slug, "discover_published": True}, {"_id": 0}
    )
    if not c:
        raise HTTPException(404, "Showcase not found.")
    return c


@router.get("/public/news/{slug}/issues/latest")
async def public_latest_issue(slug: str):
    camp = await _public_camp_or_404(slug)
    issue = await db.news_issues.find_one(
        {"campaign_id": camp["id"]},
        {"_id": 0},
        sort=[("issue_number", -1)],
    )
    if not issue:
        return {"issue": None, "articles": [], "campaign": {
            "id": camp["id"], "name": camp.get("name"),
            "system_id": camp.get("system_id"), "blurb": camp.get("canon_blurb", ""),
        }}
    arts = await db.news_articles.find(
        {"campaign_id": camp["id"], "issue_id": issue["id"]},
        {"_id": 0},
    ).sort("created_at", 1).to_list(50)
    return {
        "issue": issue,
        "articles": arts,
        "campaign": {
            "id": camp["id"],
            "name": camp.get("name"),
            "system_id": camp.get("system_id"),
            "gm_name": camp.get("gm_name"),
            "blurb": camp.get("canon_blurb", ""),
        },
    }


@router.get("/public/news/{slug}/leaderboards")
async def public_leaderboards(slug: str):
    camp = await _public_camp_or_404(slug)
    return await _build_leaderboards(camp["id"])
