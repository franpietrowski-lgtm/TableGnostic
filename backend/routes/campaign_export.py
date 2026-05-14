"""V6.25.54 — Phase C: Campaign export / import (.tgcampaign.json round-trip).

Pure data round-trip — NO LLM dependency. Bundles a campaign plus every
campaign-bound child collection (codex / characters / writer tools /
sessions / channels / encounters / etc.) into a single portable JSON
file. Re-uploading creates a brand-new campaign owned by the importer,
with every internal id remapped to fresh ids so the new copy is
independent of the source.

The bundle deliberately omits:
- Moderation rows (`flags`, `flag_messages`, `admin_actions`) — those
  belong to the platform, not the campaign.
- `voice_lines` — audio binaries don't round-trip cleanly through JSON;
  re-recording is straightforward.
- `discover_published` / `canon_published` / `featured*` flags are reset
  on import so a fresh copy never inherits a public surface.

Endpoints:
  GET  /api/campaigns/{cid}/export       — owner/admin only; .tgcampaign.json download.
  POST /api/campaigns/import             — GM/admin only; multipart file upload.
"""
from __future__ import annotations
import io
import json
import re
import secrets
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["campaign-export"])

EXPORT_SCHEMA_VERSION = 1
MAX_UPLOAD_BYTES = 32 * 1024 * 1024  # 32 MB — generous for big campaigns

# Collections keyed directly by `campaign_id`.
CAMPAIGN_BOUND: List[str] = [
    "characters", "nodes", "edges", "codex_nodes", "codex_edges",
    "sessions", "scenes",
    "campaign_channels", "channel_msgs", "threads",
    "cultures", "cosmology_entries", "manuscript_sections",
    "pov_bibles", "themes_motifs", "magic_systems",
    "encounters_library", "roll_tables", "macros", "custom_attributes",
    "materials", "material_intake_queue", "creation_myths",
    "atelier", "genesis", "epic_campaigns", "directors",
    "campaign_scene_breaks", "campaign_surprise_bag", "campaign_share_links",
    "cypher_xp_events", "kill_logs", "node_motives", "concept_drafts",
    "xp_pending",
    "news_articles", "news_issues", "news_kills",
    "campaign_reference",
]

# Collections keyed by `session_id` — collected by walking the campaign's sessions.
PER_SESSION: List[str] = [
    "battlemaps", "effects", "initiative", "dice_rolls", "chat_logs", "recaps",
]

# Never export / never import — platform-scoped.
SKIP_ALWAYS = {"flags", "flag_messages", "admin_actions", "voice_lines",
               "leads", "login_attempts", "password_reset_tokens",
               "marketplace_listings", "marketplace_subscriptions",
               "campaign_deltas",  # cross-campaign deltas; not portable
               "change_requests",  # moderation queue, regenerates fresh
               }

# Fields whose values are id-strings referencing other docs we are
# remapping. We try each on every doc; missing keys are ignored.
SINGLE_ID_REF_FIELDS = (
    "parent_id", "character_id", "session_id", "node_id", "source_id",
    "target_id", "from_node", "to_node", "encounter_id", "monster_ref_id",
    "linked_character_id", "linked_node_id", "atlas_node_id",
    "first_occurrence_section_id", "target_character_id", "peer_character_id",
    "triggered_by", "parent_node_id", "issue_id", "channel_id", "thread_id",
)
LIST_ID_REF_FIELDS = (
    "revealed_to", "article_ids", "related_section_ids",
    "ingredient_ids", "pillar_seeds",
)


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", (name or "").strip().lower()).strip("-")
    return s or "campaign"


def _remap(doc: dict, id_map: Dict[str, str]) -> dict:
    """Return a shallow-cloned doc with every id-bearing field swapped through id_map.
    Unknown ids pass through untouched (e.g. user_id of a player that doesn't
    exist on the destination pod)."""
    out = dict(doc)
    for k in SINGLE_ID_REF_FIELDS:
        v = out.get(k)
        if isinstance(v, str) and v in id_map:
            out[k] = id_map[v]
    for k in LIST_ID_REF_FIELDS:
        v = out.get(k)
        if isinstance(v, list):
            out[k] = [id_map.get(x, x) if isinstance(x, str) else x for x in v]
    return out


# ─────────────────────────── EXPORT ───────────────────────────

@router.get("/campaigns/{cid}/export")
async def export_campaign(cid: str, user: dict = Depends(get_current_user)):
    """Download a single self-contained `.tgcampaign.json` bundle of the
    entire campaign — codex, characters, writer tools, sessions, channels,
    encounters, atlas pins, etc. Owner / admin only.
    """
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user.get("role") != "admin" and user.get("id") != camp.get("gm_id"):
        raise HTTPException(403, "Only the campaign's GM or an admin may export it.")

    bundle: Dict[str, Any] = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": now_iso(),
        "exported_by": {"id": user["id"], "name": user.get("name", "")},
        "source": {
            "campaign_id": cid,
            "name": camp.get("name", ""),
            "system_id": camp.get("system_id"),
        },
        "campaign": sanitize(camp),
        "collections": {},
        "per_session": {},
        "stats": {},
    }

    session_ids: List[str] = []
    for col in CAMPAIGN_BOUND:
        try:
            docs = await db[col].find({"campaign_id": cid}, {"_id": 0}).to_list(50000)
        except Exception:
            docs = []
        if docs:
            bundle["collections"][col] = docs
            bundle["stats"][col] = len(docs)
            if col == "sessions":
                session_ids = [d["id"] for d in docs if isinstance(d.get("id"), str)]

    if session_ids:
        for col in PER_SESSION:
            try:
                docs = await db[col].find(
                    {"session_id": {"$in": session_ids}}, {"_id": 0},
                ).to_list(200000)
            except Exception:
                docs = []
            if docs:
                bundle["per_session"][col] = docs
                bundle["stats"][f"per_session.{col}"] = len(docs)

    body = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fname = f"{_slugify(camp.get('name', 'campaign'))}-{cid[:8]}.tgcampaign.json"
    return StreamingResponse(
        io.BytesIO(body),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{fname}"',
            "X-TG-Bundle-Schema": str(EXPORT_SCHEMA_VERSION),
            "X-TG-Bundle-Bytes": str(len(body)),
        },
    )


# ─────────────────────────── IMPORT ───────────────────────────

@router.post("/campaigns/import")
async def import_campaign(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a `.tgcampaign.json` produced by `/api/campaigns/{cid}/export`
    (or a compatible export from another TableGnostic pod). Creates a NEW
    campaign owned by the importing user with every internal id remapped
    to fresh ids — the new copy is independent of the source.

    Player accounts are seat-only; GM/admin role required.
    """
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "Player accounts cannot import campaigns. "
                                 "Switch to a Game Master account first.")

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty upload.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Bundle exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit.")
    try:
        bundle = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise HTTPException(400, f"Bundle is not valid JSON: {e}")

    if not isinstance(bundle, dict):
        raise HTTPException(400, "Bundle must be a JSON object.")
    if bundle.get("schema_version") != EXPORT_SCHEMA_VERSION:
        raise HTTPException(400,
            f"Unsupported bundle schema_version "
            f"{bundle.get('schema_version')!r} (this pod expects "
            f"{EXPORT_SCHEMA_VERSION}). Re-export from a compatible TableGnostic.")
    if not isinstance(bundle.get("campaign"), dict):
        raise HTTPException(400, "Bundle missing required `campaign` object.")

    src_camp = bundle["campaign"]
    src_cid = (bundle.get("source") or {}).get("campaign_id") or src_camp.get("id")
    if not src_cid:
        raise HTTPException(400, "Bundle is missing source campaign id.")

    collections = bundle.get("collections") or {}
    per_session = bundle.get("per_session") or {}
    if not isinstance(collections, dict) or not isinstance(per_session, dict):
        raise HTTPException(400, "Bundle `collections` / `per_session` must be objects.")

    # 1. Pre-allocate fresh ids for every doc that carries an `id` field.
    new_cid = new_id()
    id_map: Dict[str, str] = {src_cid: new_cid}
    for col, docs in collections.items():
        if col in SKIP_ALWAYS or not isinstance(docs, list):
            continue
        for d in docs:
            if isinstance(d, dict) and isinstance(d.get("id"), str):
                # don't overwrite if duplicate id (paranoia: first wins)
                id_map.setdefault(d["id"], new_id())
    # per-session: ids inside session rows are not used as fk targets often,
    # but generate to be safe
    for col, docs in per_session.items():
        if col in SKIP_ALWAYS or not isinstance(docs, list):
            continue
        for d in docs:
            if isinstance(d, dict) and isinstance(d.get("id"), str):
                id_map.setdefault(d["id"], new_id())

    # 2. New campaign doc — importer becomes owner, members reset, all
    #    public-surface flags reset.
    forged_camp = {
        **{k: v for k, v in src_camp.items()
           if k not in ("_id", "id", "gm_id", "gm_name", "member_ids",
                        "invite_token", "created_at", "discover_published",
                        "discover_slug", "canon_published", "featured",
                        "featured_at", "featured_requested",
                        "featured_request_note", "featured_requested_at")},
        "id": new_cid,
        "name": (src_camp.get("name") or "Campaign") + " (imported)",
        "gm_id": user["id"],
        "gm_name": user.get("name", ""),
        "member_ids": [],
        "invite_token": secrets.token_urlsafe(16),
        "created_at": now_iso(),
        "imported_from": src_cid,
        "imported_at": now_iso(),
    }
    await db.campaigns.insert_one(forged_camp)

    # 3. Walk every collection — remap ids + campaign_id, then bulk-insert.
    counts: Dict[str, int] = {}
    for col, docs in collections.items():
        if col in SKIP_ALWAYS or not isinstance(docs, list) or not docs:
            continue
        out: List[dict] = []
        for d in docs:
            if not isinstance(d, dict):
                continue
            new_d = _remap(d, id_map)
            new_d["campaign_id"] = new_cid
            if "id" in new_d and isinstance(new_d["id"], str):
                new_d["id"] = id_map.get(d["id"], new_id())
            # Characters: importer claims ownership; player accounts that
            # owned them on the source pod likely don't exist here.
            if col == "characters":
                new_d["owner_id"] = user["id"]
                new_d["owner_name"] = user.get("name", "")
            # Nodes/edges/etc.: reset author to importer where the source
            # author won't resolve. Cheap and consistent with clone_campaign.
            if col in ("nodes", "edges"):
                new_d["author_id"] = user["id"]
                new_d["author_name"] = user.get("name", "")
                if col == "nodes":
                    new_d["revealed_to"] = []  # private to importer until re-revealed
            new_d.pop("_id", None)
            out.append(new_d)
        if out:
            try:
                await db[col].insert_many(out)
                counts[col] = len(out)
            except Exception as e:
                # one collection failing must not orphan the rest of the
                # import — keep going, record the failure in counts.
                counts[col] = f"error: {type(e).__name__}"

    # 4. Per-session collections — remap session_id + character ids.
    for col, docs in per_session.items():
        if col in SKIP_ALWAYS or not isinstance(docs, list) or not docs:
            continue
        out2: List[dict] = []
        for d in docs:
            if not isinstance(d, dict):
                continue
            new_d = _remap(d, id_map)
            if isinstance(new_d.get("session_id"), str):
                new_d["session_id"] = id_map.get(d.get("session_id"), d.get("session_id"))
            if "id" in new_d and isinstance(new_d["id"], str):
                new_d["id"] = id_map.get(d["id"], new_id())
            new_d.pop("_id", None)
            out2.append(new_d)
        if out2:
            try:
                await db[col].insert_many(out2)
                counts[f"per_session.{col}"] = len(out2)
            except Exception as e:
                counts[f"per_session.{col}"] = f"error: {type(e).__name__}"

    return {
        "ok": True,
        "campaign": sanitize(forged_camp),
        "counts": counts,
        "remapped_ids": len(id_map) - 1,  # exclude the campaign-id seed entry
        "source": bundle.get("source"),
    }
