"""Table-Gnostic backend — BESM 4E aware TTRPG platform."""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import random
import re
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Literal, Dict, Any

import bcrypt
import jwt
import resend
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Depends, Request, Response, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

from besm_data import (
    BOOK, BOOK_EXTRAS, CORE_STATS, DERIVED_VALUES, ATTRIBUTES, DEFECTS,
    ENHANCEMENTS, LIMITERS, SKILL_GROUPS, POWER_LEVELS,
    NODE_TYPES, TARGET_NUMBERS, EXTRAS_RULES, with_source,
    attribute_blurb, defect_blurb, enhancement_blurb, limiter_blurb,
    extras_blurb, power_level_blurb, attribute_whitelist,
    ENHANCEMENT_BLURB, LIMITER_BLURB,
    GENERIC_BLURBS, GAME_SYSTEMS, GAME_SYSTEM_IDS, GAME_SYSTEMS_BY_ID,
    DEFAULT_SYSTEM_ID,
    SIZE_TEMPLATES, SIZE_BY_NAME, DEFAULT_SIZE,
)


def _resolve_system_id(data: dict) -> tuple:
    """Validate `data['system_id']` and sync `data['system']` with the canonical name.
    Returns (system_id, system_name). Raises HTTPException(400) on unknown id.
    """
    sid = data.get("system_id") or DEFAULT_SYSTEM_ID
    if sid not in GAME_SYSTEMS_BY_ID:
        raise HTTPException(400, f"Unknown game system '{sid}'.")
    meta = GAME_SYSTEMS_BY_ID[sid]
    data["system_id"] = sid
    data["system"] = meta["name"]
    return sid, meta["name"]

# -------- Config --------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Resend email client (optional — falls back to console logging)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
FRONTEND_PUBLIC_URL = os.environ.get("FRONTEND_PUBLIC_URL", "").strip()
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

async def send_password_reset_email(to_email: str, reset_link: str, user_name: str):
    subject = "Table-Gnostic — Reset your password"
    html = f"""
    <div style="font-family: Georgia, serif; background:#07060a; color:#e9e3d2; padding:32px; max-width:560px; margin:0 auto;">
      <div style="font-family: 'Cinzel', serif; letter-spacing:0.3em; color:#c8a34a; font-size:14px;">TABLE·GNOSTIC</div>
      <h1 style="color:#e9e3d2; font-size:22px; margin:14px 0 6px;">Reset your password</h1>
      <p style="color:#a9a3b8; line-height:1.55;">Hello {user_name or 'table-gnostic'},</p>
      <p style="color:#a9a3b8; line-height:1.55;">A password reset was requested for your Table-Gnostic account. If this was you, follow the link below within the next hour.</p>
      <p style="margin:24px 0;">
        <a href="{reset_link}" style="background:#c8a34a; color:#07060a; text-decoration:none; padding:12px 20px; letter-spacing:0.12em; font-weight:600; font-family: sans-serif; font-size:13px;">RESET PASSWORD</a>
      </p>
      <p style="color:#777; font-size:12px; line-height:1.55;">If you didn't request this, you can ignore this message — your password will stay unchanged.</p>
      <hr style="border:none; border-top:1px solid #33302a; margin:24px 0;" />
      <p style="color:#555; font-size:11px; letter-spacing:0.2em; text-transform:uppercase;">Not the system. The table.</p>
    </div>"""
    text = (f"Table-Gnostic password reset\n\nHello {user_name or 'table-gnostic'},\n\n"
            f"Reset your password within 1 hour:\n{reset_link}\n\nIf you didn't request this, ignore this email.\n")
    if not RESEND_API_KEY:
        print(f"[email:dev] password reset -> {to_email} | {reset_link}")
        return {"delivered": False, "reason": "RESEND_API_KEY not configured"}
    try:
        result = await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL, "to": [to_email],
            "subject": subject, "html": html, "text": text,
        })
        return {"delivered": True, "id": result.get("id")}
    except Exception as e:
        print(f"[email:error] {e}")
        return {"delivered": False, "reason": str(e)}

import asyncio  # required for send_password_reset_email

app = FastAPI(title="Table-Gnostic API")
api = APIRouter(prefix="/api")

# Lock CORS: always restrict by regex (preview.emergentagent.com + localhost).
# FRONTEND_URL can explicitly add one more origin if desired.
_extra_origin = os.environ.get("FRONTEND_URL", "").strip()
_allow_origins = [_extra_origin] if _extra_origin and _extra_origin != "*" else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_origin_regex=r"https://.*\.preview\.emergentagent\.com|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Permissions-Policy: explicitly allow camera + microphone for the AV Seats
# feature. Without this header, modern browsers reject getUserMedia() inside
# embedded iframes (preview / kiosks). The frontend additionally detects iframe
# embedding and surfaces an "Open in new tab" banner when needed.
@app.middleware("http")
async def permissions_policy_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), display-capture=(self)"
    response.headers["Feature-Policy"] = "camera 'self'; microphone 'self'"
    return response

# -------- Auth helpers --------

def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(p: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(p.encode("utf-8"), h.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email,
               "exp": datetime.now(timezone.utc) + timedelta(hours=8),
               "type": "access"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id,
               "exp": datetime.now(timezone.utc) + timedelta(days=30),
               "type": "refresh"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def set_auth_cookies(resp: Response, access: str, refresh: str):
    resp.set_cookie("access_token", access, httponly=True, samesite="lax",
                    max_age=8*3600, path="/")
    resp.set_cookie("refresh_token", refresh, httponly=True, samesite="lax",
                    max_age=30*86400, path="/")

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(401, "User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# -------- Models --------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=80)
    role: Literal["player", "gm"] = "player"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ForgotIn(BaseModel):
    email: EmailStr

class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=6)

class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str

class CampaignIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    system: str = "BESM 4E"
    # Game-system selector — references entries in GAME_SYSTEMS (besm-4e, dnd-5e, etc.).
    # When system_id != 'besm-4e', BESM-specific UIs (Reference, Character Forge)
    # surface a 'content coming soon' placeholder while still letting the GM run
    # worldbuilding, sessions, and AV seats normally.
    system_id: str = "besm-4e"
    tone: Optional[str] = None
    genre: Optional[str] = None
    tags: List[str] = []
    experience_level: Optional[str] = "Any"
    schedule: Optional[str] = None
    max_players: int = 6
    visibility: Literal["public", "private"] = "public"
    power_level: str = "Heroic"
    # Player primer + allow/prohibit lists (empty = all allowed)
    player_primer: str = ""
    allowed_attributes: List[str] = []
    prohibited_attributes: List[str] = []
    allowed_defects: List[str] = []
    prohibited_defects: List[str] = []
    allowed_skill_groups: List[str] = []
    prohibited_skill_groups: List[str] = []
    # GM Primer caps — override the Power Level point budget for this table.
    # 0 means "no override" and the Power Level's default point budget applies.
    character_point_min: int = 0
    character_point_max: int = 0
    # Hard cap on the Level of any single Attribute (0 = no cap)
    max_per_attribute_rank: int = 0
    # ---------- V3.5 — Campaign Benchmarks ----------
    # Free-form genre flavour ("High Fantasy", "Cyberpunk", "Cosmic Horror", etc.).
    # Surfaced on the Character Builder + Reference views as a context badge.
    genre: str = ""
    # Time-period anchors weapons / gear / item availability.
    time_period: str = ""
    # Default Size template applied to brand-new characters in this campaign.
    # Size in BESM 4E is a per-entity TEMPLATE (Diminutive ↔ Massive), NOT a
    # campaign-wide world-scale enum. A GM can pin "Medium" (humans) or shift
    # to e.g. "Small" for a halfling-only table.
    default_character_size: str = "Medium"
    # Damage Rating baseline — replaces the engine's hard-coded 5 in the
    # damage_multiplier formula. Higher = grittier / more lethal table.
    damage_rating_baseline: int = 5

class CampaignOut(CampaignIn):
    id: str
    gm_id: str
    gm_name: str
    member_ids: List[str] = []
    created_at: str

class JoinIn(BaseModel):
    message: Optional[str] = ""

class CharacterStats(BaseModel):
    body: int = 4
    mind: int = 4
    soul: int = 4

class CharacterDefect(BaseModel):
    name: str
    rank: int = 1
    points_per_rank: int
    category: str
    page: Optional[int] = None
    note: Optional[str] = ""

class CharacterAttribute(BaseModel):
    name: str
    level: int = 1
    cost_per_level: float
    enhancements: List[str] = []
    limiters: List[str] = []
    custom_attribute_id: Optional[str] = None  # GM custom
    page: Optional[int] = None
    note: Optional[str] = ""
    # Item / Weapon-class Attributes may carry their own Defects (e.g. a sword
    # that breaks easily). Refunds reduce the parent Attribute's net cost.
    defects: List[CharacterDefect] = []
    # Optional Size template applied to this Item/Weapon/Companion (BESM 4E
    # Size templates: Diminutive / Small / Medium / Large / Huge / Gargantuan
    # / Massive). "" = inherit the character's size; non-empty overrides.
    size: str = ""

class CharacterSkillComponent(BaseModel):
    name: str
    level: int = 1
    note: str = ""

class CharacterSkill(BaseModel):
    group: str
    level: int = 1
    cost_per_level: int
    page: Optional[int] = None
    note: str = ""
    components: List[CharacterSkillComponent] = []

class CharacterPowerPack(BaseModel):
    """A narrative grouping of a character's powers / materials / training
    tied to one in-setting source (e.g., 'Cryptosha · Serenitas Tincture Kit').
    Defaults to free; GM Primer can authorise a fixed cost via the campaign's
    `power_pack_cost_template` map (P2). References are display-only labels
    pointing at Attribute / Defect / Skill names already on the sheet.
    """
    name: str
    description: str = ""
    references: List[str] = []
    cost: int = 0  # 0 = narrative / free; positive = GM-set cost

class CharacterIn(BaseModel):
    campaign_id: str
    name: str
    concept: str = ""
    power_level: str = "Heroic"
    total_points: int = 120
    # BESM 4E Size template applied to the character (Diminutive ↔ Massive).
    # Modifies damage output, defence, movement, weight. Default Medium.
    size: str = "Medium"
    # Player-chosen signature colour for AV tile pulse + future map tokens.
    # Empty = AVSeats falls back to gold. Stored as #RRGGBB.
    token_color: str = ""
    stats: CharacterStats = CharacterStats()
    attributes: List[CharacterAttribute] = []
    defects: List[CharacterDefect] = []
    skills: List[CharacterSkill] = []
    power_packs: List[CharacterPowerPack] = []
    notes: str = ""
    published: bool = False
    # Character Folio (Dyskami v1.01) — narrative depth
    folio: Dict[str, Any] = Field(default_factory=dict)
    # Expected keys (all optional, free-form):
    # - aliases, gender_species_age, occupation, physical_description, personality_traits
    # - motivations, fears_weaknesses, edges (list[str]), obstacles (list[str])
    # - goals (list[{title, kind: short|long|secret, note}])
    # - family (list[{name, relation, note}])
    # - rivals (list[{name, note}])
    # - history_events (list[{date, title, note}])
    # - group_dynamics, advancement_log (list[{date, change, points}])
    # - journal (list[{session_id, date, entry}])

class NodeIn(BaseModel):
    campaign_id: str
    type: str
    title: str
    content: str = ""
    tags: List[str] = []
    visibility: Literal["gm_only", "shared", "revealed"] = "gm_only"
    revealed_to: List[str] = []  # user ids
    links: List[str] = []  # node ids
    fields: Dict[str, Any] = Field(default_factory=dict)  # structured article data per node type

class EdgeIn(BaseModel):
    campaign_id: str
    from_node: str
    to_node: str
    label: str = "related"

class SessionIn(BaseModel):
    campaign_id: str
    title: str
    scheduled_at: Optional[str] = None

class ChatIn(BaseModel):
    session_id: str
    message: str
    kind: Literal["chat", "ooc", "action", "system"] = "chat"

class DiceIn(BaseModel):
    session_id: str
    notation: str  # e.g. "2d6+Body", "1d20", "3d6"
    label: str = ""
    target: Optional[int] = None
    character_id: Optional[str] = None
    private: bool = False

class InitiativeEntryIn(BaseModel):
    session_id: str
    name: str
    character_id: Optional[str] = None
    roll: int = 0
    side: Literal["pc", "npc", "neutral"] = "pc"

class EffectIn(BaseModel):
    session_id: str
    target_name: str
    name: str
    duration_rounds: int = 1
    note: str = ""

class DamageIn(BaseModel):
    session_id: str
    target_name: str
    amount: int
    kind: Literal["hp", "ep"] = "hp"

class CustomAttributeIn(BaseModel):
    campaign_id: str
    kind: Literal["attribute", "defect", "skill"]
    name: str
    cost_per_level: float = 1
    category: Optional[str] = None
    page_ref: Optional[str] = None
    description_note: str = ""  # GM-authored (original content)

class NodeRevealIn(BaseModel):
    user_ids: List[str]

class GenesisIn(BaseModel):
    """Campaign genesis using Guy Sclanders' Great GM framework.

    Credit: This structure is inspired by "The Complete Guide to Creating Epic
    Campaigns" by Guy Sclanders (How to be a Great GM, 2018). Only the phase
    naming and prompts are borrowed — all authored content belongs to the user.
    """
    campaign_id: str
    # Phase 1: The Sentence — Someone wants something badly by when, having
    # difficulty using something because of reasons.
    sentence_who: str = ""
    sentence_wants: str = ""
    sentence_badly_when: str = ""
    sentence_using: str = ""
    sentence_reasons: str = ""
    # Phase 2: Theme
    theme: str = ""
    tone_words: List[str] = []
    # Phase 3: Nemesis
    nemesis_name: str = ""
    nemesis_type: str = ""  # villain / henchman / force-of-nature / rival / system
    nemesis_motive: str = ""
    nemesis_resources: str = ""
    nemesis_weakness: str = ""
    # Phase 4: Plotting — the Master Plot arc
    master_acts: List[Dict[str, str]] = []  # [{title, beat}]
    # Phase 5: Adventure outlines (Follow Plotters + Make Plotters + Fly)
    adventures: List[Dict[str, str]] = []   # [{title, kind, hook, stakes, outcome}]
    # Phase 6: NPCs to seed
    seed_npcs: List[Dict[str, str]] = []    # [{name, role, note}]
    # Phase 7: Beginning + Ending ideas
    beginning: str = ""
    ending: str = ""
    # Progress
    phase_completed: int = 0  # 0..7

# -------- Helpers --------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_id() -> str:
    return str(uuid.uuid4())

def sanitize(doc: dict) -> dict:
    if not doc:
        return doc
    doc = {k: v for k, v in doc.items() if k != "_id" and k != "password_hash"}
    return doc

# -------- Startup --------

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.campaigns.create_index("id", unique=True)
    await db.characters.create_index("id", unique=True)
    await db.characters.create_index("campaign_id")
    await db.nodes.create_index("id", unique=True)
    await db.nodes.create_index("campaign_id")
    await db.edges.create_index("campaign_id")
    await db.sessions.create_index("id", unique=True)
    await db.sessions.create_index("campaign_id")
    await db.chat_logs.create_index("session_id")
    await db.dice_rolls.create_index("session_id")
    await db.initiative.create_index("session_id")
    await db.effects.create_index("session_id")
    await db.custom_attributes.create_index("campaign_id")
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)

    # Backfill: legacy "user" role accounts get promoted to "gm" so existing
    # campaigns and creators keep working seamlessly. Runs BEFORE seed_user so
    # that the seed step can authoritatively pin specific demo roles afterward.
    await db.users.update_many({"role": "user"}, {"$set": {"role": "gm"}})
    # Seed admin + demo users — gm@ is a Game Master, player@ is a Player
    await seed_user("admin@tablegnostic.com", "admin123", "Admin", "admin")
    await seed_user("gm@tablegnostic.com", "gm123456", "Game Master", "gm")
    await seed_user("player@tablegnostic.com", "player12345", "Player", "player")
    # Backfill invite tokens for legacy campaigns
    async for c in db.campaigns.find({"invite_token": {"$exists": False}}, {"_id": 0, "id": 1}):
        await db.campaigns.update_one({"id": c["id"]},
                                      {"$set": {"invite_token": secrets.token_urlsafe(16)}})

async def seed_user(email: str, password: str, name: str, role: str):
    existing = await db.users.find_one({"email": email})
    if existing is None:
        await db.users.insert_one({
            "id": new_id(), "email": email, "password_hash": hash_password(password),
            "name": name, "role": role, "created_at": now_iso(),
        })
        return
    # Make seed accounts authoritative — keep password and role in sync each boot.
    update = {"role": role, "name": name}
    if not verify_password(password, existing.get("password_hash", "")):
        update["password_hash"] = hash_password(password)
    await db.users.update_one({"email": email}, {"$set": update})

# -------- Auth Routes --------

@api.post("/auth/register")
async def register(body: RegisterIn, response: Response):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    user_id = new_id()
    user = {
        "id": user_id, "email": email, "password_hash": hash_password(body.password),
        "name": body.name, "role": body.role, "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    return {"id": user_id, "email": email, "name": body.name, "role": body.role,
            "access_token": access}

@api.post("/auth/login")
async def login(body: LoginIn, request: Request, response: Response):
    email = body.email.lower()
    ip = request.client.host if request.client else "?"
    key = f"{ip}:{email}"
    # brute force
    attempt = await db.login_attempts.find_one({"key": key})
    if attempt and attempt.get("count", 0) >= 5:
        locked_until = attempt.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
            raise HTTPException(423, "Too many attempts — locked for 15 minutes")
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        await db.login_attempts.update_one(
            {"key": key},
            {"$inc": {"count": 1},
             "$set": {"locked_until": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()}},
            upsert=True,
        )
        raise HTTPException(401, "Invalid credentials")
    await db.login_attempts.delete_one({"key": key})
    access = create_access_token(user["id"], email)
    refresh = create_refresh_token(user["id"])
    set_auth_cookies(response, access, refresh)
    return {"id": user["id"], "email": user["email"], "name": user["name"],
            "role": user.get("role", "user"), "access_token": access}

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}

@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return sanitize(user)

@api.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(401, "No refresh token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(401, "User not found")
        access = create_access_token(user["id"], user["email"])
        response.set_cookie("access_token", access, httponly=True, samesite="lax",
                            max_age=8*3600, path="/")
        return {"access_token": access}
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token")

@api.post("/auth/forgot-password")
async def forgot_password(body: ForgotIn):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if user:
        try:
            token = secrets.token_urlsafe(32)
            await db.password_reset_tokens.insert_one({
                "token": token, "user_id": user["id"],
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                "used": False,
            })
            base = FRONTEND_PUBLIC_URL or ""
            reset_link = f"{base}/reset?token={token}" if base else f"/reset?token={token}"
            print(f"[Password reset] {email} -> {reset_link}")
            try:
                await send_password_reset_email(email, reset_link, user.get("name", ""))
            except Exception as e:
                print(f"[email:error] {e}")  # never leak delivery status
        except Exception as e:
            print(f"[forgot-password:error] {e}")
    # Always return ok (don't leak whether email exists or whether delivery succeeded)
    return {"ok": True}

@api.post("/auth/reset-password")
async def reset_password(body: ResetIn):
    rec = await db.password_reset_tokens.find_one({"token": body.token, "used": False})
    if not rec or rec["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(400, "Invalid or expired token")
    await db.users.update_one({"id": rec["user_id"]},
                              {"$set": {"password_hash": hash_password(body.password)}})
    await db.password_reset_tokens.update_one({"token": body.token}, {"$set": {"used": True}})
    return {"ok": True}

# -------- BESM Reference --------

@api.get("/besm/reference")
async def besm_reference():
    def enrich_attr(a):
        wl = attribute_whitelist(a["name"])
        return {**a, "blurb": attribute_blurb(a["name"]),
                "allowed_enhancements": wl["enhancements"],
                "allowed_limiters": wl["limiters"],
                "open_mods": wl["open"]}
    def enrich_def(d):
        return {**d, "blurb": defect_blurb(d.get("category", ""), d.get("name", ""))}
    def enrich_pl(p):
        return {**p, "blurb": power_level_blurb(p["name"])}
    return {
        "book": BOOK,
        "core_stats": with_source(CORE_STATS),
        "derived_values": with_source(DERIVED_VALUES),
        "attributes": [enrich_attr(a) for a in with_source(ATTRIBUTES)],
        "defects": [enrich_def(d) for d in with_source(DEFECTS)],
        "enhancements": [{**e, "blurb": enhancement_blurb(e["name"])} for e in with_source(ENHANCEMENTS)],
        "limiters": [{**lim, "blurb": limiter_blurb(lim["name"])} for lim in with_source(LIMITERS)],
        "skill_groups": with_source(SKILL_GROUPS),
        "power_levels": [enrich_pl(p) for p in with_source(POWER_LEVELS)],
        "node_types": NODE_TYPES,
        "target_numbers": with_source(TARGET_NUMBERS),
        # BESM Extras (Rule Expansions & Character Options)
        "extras_book": BOOK_EXTRAS,
        "extras_rules": [{**r, "blurb": extras_blurb(r["name"]),
                          "source": {"book": BOOK_EXTRAS, "page": r.get("page")}}
                         for r in EXTRAS_RULES],
        # Generic mechanic primers (about the costing equation, items vs gear, etc.)
        "generic_blurbs": [{"name": k, "blurb": v} for k, v in GENERIC_BLURBS.items()],
        # Size templates (BESM 4E p.181 — applied per-character / per-item).
        "size_templates": SIZE_TEMPLATES,
    }


@api.get("/systems")
async def list_game_systems(response: Response):
    """Public list of game systems advertised by Table-Gnostic.
    BESM 4E is fully supported (mechanics, reference cards, builder).
    Other systems are scaffolded — the campaign UI can pick them, but their
    Reference / Character Forge / Roll Options surfaces show a 'content
    coming soon' placeholder until that system's data is loaded.
    """
    # Payload is fully static; cache aggressively on the client / CDN.
    response.headers["Cache-Control"] = "public, max-age=300"
    return {"default": DEFAULT_SYSTEM_ID, "systems": GAME_SYSTEMS}

# -------- Campaign Genesis (Great GM framework) --------
# Credit: Framework inspired by Guy Sclanders, "The Complete Guide to Creating
# Epic Campaigns" (How to be a Great GM, 2018). Only section structure and
# prompts are referenced; all authored content belongs to the user.

@api.get("/campaigns/{cid}/genesis")
async def get_genesis(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can view genesis")
    doc = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if not doc:
        doc = GenesisIn(campaign_id=cid).model_dump()
        doc["id"] = new_id()
        doc["created_at"] = now_iso()
        await db.genesis.insert_one(dict(doc))
        doc.pop("_id", None)
    return doc

@api.put("/campaigns/{cid}/genesis")
async def update_genesis(cid: str, body: GenesisIn,
                         user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can edit genesis")
    data = body.model_dump()
    data["campaign_id"] = cid
    data["updated_at"] = now_iso()
    existing = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if existing:
        data["id"] = existing["id"]
        data["created_at"] = existing.get("created_at", now_iso())
        await db.genesis.replace_one({"campaign_id": cid}, data)
    else:
        data["id"] = new_id()
        data["created_at"] = now_iso()
        await db.genesis.insert_one(dict(data))
    data.pop("_id", None)
    return data

@api.post("/campaigns/{cid}/genesis/seed-nodes")
async def seed_nodes_from_genesis(cid: str, user: dict = Depends(get_current_user)):
    """Convert genesis seed_npcs into gm_only knowledge nodes."""
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp or camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can seed")
    g = await db.genesis.find_one({"campaign_id": cid}, {"_id": 0})
    if not g:
        raise HTTPException(404, "No genesis")
    created = 0
    # Seed nemesis as NPC
    if g.get("nemesis_name"):
        await db.nodes.insert_one({
            "id": new_id(), "campaign_id": cid, "type": "npc",
            "title": g["nemesis_name"],
            "content": f"Nemesis · {g.get('nemesis_type','')}\nMotive: {g.get('nemesis_motive','')}\nResources: {g.get('nemesis_resources','')}\nWeakness: {g.get('nemesis_weakness','')}",
            "tags": ["nemesis"], "visibility": "gm_only", "revealed_to": [],
            "links": [], "author_id": user["id"], "author_name": user["name"],
            "created_at": now_iso(),
        })
        created += 1
    for npc in g.get("seed_npcs", []) or []:
        if not npc.get("name"): continue
        await db.nodes.insert_one({
            "id": new_id(), "campaign_id": cid, "type": "npc",
            "title": npc["name"],
            "content": f"{npc.get('role','')}\n\n{npc.get('note','')}",
            "tags": [npc.get("role","").lower()] if npc.get("role") else [],
            "visibility": "gm_only", "revealed_to": [], "links": [],
            "author_id": user["id"], "author_name": user["name"],
            "created_at": now_iso(),
        })
        created += 1
    for adv in g.get("adventures", []) or []:
        if not adv.get("title"): continue
        await db.nodes.insert_one({
            "id": new_id(), "campaign_id": cid, "type": "quest",
            "title": adv["title"],
            "content": f"Hook: {adv.get('hook','')}\nStakes: {adv.get('stakes','')}\nOutcome: {adv.get('outcome','')}",
            "tags": [adv.get("kind","").lower()] if adv.get("kind") else [],
            "visibility": "gm_only", "revealed_to": [], "links": [],
            "author_id": user["id"], "author_name": user["name"],
            "created_at": now_iso(),
        })
        created += 1
    return {"ok": True, "nodes_created": created}

# -------- Custom GM Attributes / Defects / Skills --------

@api.post("/campaigns/{campaign_id}/custom")
async def create_custom(campaign_id: str, body: CustomAttributeIn,
                        user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM can add custom entries")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["campaign_id"] = campaign_id
    doc["created_by"] = user["id"]
    doc["created_at"] = now_iso()
    await db.custom_attributes.insert_one(doc)
    return sanitize(doc)

@api.get("/campaigns/{campaign_id}/custom")
async def list_custom(campaign_id: str, user: dict = Depends(get_current_user)):
    rows = await db.custom_attributes.find({"campaign_id": campaign_id}, {"_id": 0}).to_list(500)
    return rows

@api.delete("/campaigns/{campaign_id}/custom/{cid}")
async def delete_custom(campaign_id: str, cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user.get("role") != "admin"):
        raise HTTPException(403, "Only GM can remove")
    await db.custom_attributes.delete_one({"id": cid, "campaign_id": campaign_id})
    return {"ok": True}

# -------- Campaigns --------

@api.post("/campaigns")
async def create_campaign(body: CampaignIn, user: dict = Depends(get_current_user)):
    # Player-role accounts are seat-only — they take seats at tables, they
    # don't run them. Allowlist (gm, admin) so any future role added later
    # has to be explicitly granted campaign-create.
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "Player accounts cannot create campaigns. "
                                 "Update your role to Game Master in your profile to host a table.")
    doc = body.model_dump()
    # Validate game-system selection and sync the display label.
    _resolve_system_id(doc)
    doc["id"] = new_id()
    doc["gm_id"] = user["id"]
    doc["gm_name"] = user["name"]
    doc["member_ids"] = []
    doc["invite_token"] = secrets.token_urlsafe(16)
    doc["created_at"] = now_iso()
    await db.campaigns.insert_one(doc)
    return sanitize(doc)

@api.get("/campaigns")
async def list_campaigns(mine: bool = False, user: dict = Depends(get_current_user)):
    q: Dict[str, Any] = {}
    if mine:
        q = {"$or": [{"gm_id": user["id"]}, {"member_ids": user["id"]}]}
    else:
        q = {"$or": [
            {"visibility": "public"},
            {"gm_id": user["id"]},
            {"member_ids": user["id"]},
        ]}
    rows = await db.campaigns.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return rows

@api.put("/campaigns/{cid}")
async def update_campaign(cid: str, body: CampaignIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM may edit")
    data = body.model_dump()
    _resolve_system_id(data)
    data["id"] = cid
    data["gm_id"] = camp["gm_id"]
    data["gm_name"] = camp["gm_name"]
    data["member_ids"] = camp.get("member_ids", [])
    data["invite_token"] = camp.get("invite_token") or secrets.token_urlsafe(16)
    data["created_at"] = camp.get("created_at", now_iso())
    data["updated_at"] = now_iso()
    await db.campaigns.replace_one({"id": cid}, data)
    return sanitize(data)

@api.post("/campaigns/{cid}/regenerate-invite")
async def regenerate_invite(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp or camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM")
    new_token = secrets.token_urlsafe(16)
    await db.campaigns.update_one({"id": cid}, {"$set": {"invite_token": new_token}})
    return {"invite_token": new_token}

# Public invite lookup (no auth) — shows a minimal summary for onboarding
@api.get("/invites/{token}")
async def get_invite(token: str):
    camp = await db.campaigns.find_one({"invite_token": token}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Invite not found or revoked")
    return {
        "campaign_id": camp["id"],
        "name": camp["name"],
        "description": camp.get("description", ""),
        "system": camp.get("system", "BESM 4E"),
        "power_level": camp.get("power_level", "Heroic"),
        "gm_name": camp.get("gm_name", ""),
        "tags": camp.get("tags", []),
        "tone": camp.get("tone"),
        "genre": camp.get("genre"),
        "schedule": camp.get("schedule"),
        "experience_level": camp.get("experience_level"),
        "seated": len(camp.get("member_ids", [])),
        "max_players": camp.get("max_players", 6),
        "full": len(camp.get("member_ids", [])) >= camp.get("max_players", 6),
    }

@api.post("/invites/{token}/accept")
async def accept_invite(token: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"invite_token": token}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Invite not found or revoked")
    cid = camp["id"]
    if user["id"] == camp["gm_id"]:
        return {"ok": True, "campaign_id": cid, "already": "gm"}
    if user["id"] in camp.get("member_ids", []):
        return {"ok": True, "campaign_id": cid, "already": True}
    if len(camp.get("member_ids", [])) >= camp.get("max_players", 6):
        raise HTTPException(400, "Table full")
    await db.campaigns.update_one({"id": cid}, {"$addToSet": {"member_ids": user["id"]}})
    return {"ok": True, "campaign_id": cid}

@api.get("/campaigns/{cid}")
async def get_campaign(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp["visibility"] != "public" and camp["gm_id"] != user["id"] and user["id"] not in camp.get("member_ids", []):
        raise HTTPException(403, "Not permitted")
    members = await db.users.find(
        {"id": {"$in": camp.get("member_ids", [])}},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    camp["members"] = members
    camp["is_gm"] = (camp["gm_id"] == user["id"])
    return camp

@api.post("/campaigns/{cid}/join")
async def join_campaign(cid: str, body: JoinIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if user["id"] == camp["gm_id"]:
        raise HTTPException(400, "You are the GM")
    if user["id"] in camp.get("member_ids", []):
        return {"ok": True, "already": True}
    if len(camp.get("member_ids", [])) >= camp.get("max_players", 6):
        raise HTTPException(400, "Table full")
    await db.campaigns.update_one({"id": cid}, {"$addToSet": {"member_ids": user["id"]}})
    return {"ok": True}

@api.post("/campaigns/{cid}/leave")
async def leave_campaign(cid: str, user: dict = Depends(get_current_user)):
    await db.campaigns.update_one({"id": cid}, {"$pull": {"member_ids": user["id"]}})
    return {"ok": True}

@api.delete("/campaigns/{cid}")
async def delete_campaign(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp["gm_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only GM may delete")
    await db.campaigns.delete_one({"id": cid})
    await db.characters.delete_many({"campaign_id": cid})
    await db.nodes.delete_many({"campaign_id": cid})
    await db.edges.delete_many({"campaign_id": cid})
    await db.sessions.delete_many({"campaign_id": cid})
    await db.custom_attributes.delete_many({"campaign_id": cid})
    return {"ok": True}

# -------- Characters --------

def attribute_cost(a) -> float:
    """Compute the BESM 4E net cost of an Attribute entry.

    Per-Level cost equation (BESM 4E):
        per_level = max(1, cost_per_level + (#Enhancements - #Limiters))
    Subtotal = per_level × Level.

    The `max(1, …)` clamp enforces the BESM 4E rule that an Attribute's
    net cost-per-Level cannot fall below 1, no matter how many Limiters
    are stacked on top.

    Item / Weapon-class Attributes may carry their own nested Defects
    (e.g. a sword that breaks easily). Those refunds reduce the parent
    Attribute's cost; the result is floored at 0 (an Attribute never
    refunds more than it costs).
    """
    if hasattr(a, "model_dump"):
        a = a.model_dump()
    level = max(1, int(a.get("level", 1)))
    base_per_level = float(a.get("cost_per_level", 0))
    mod_count = len(a.get("enhancements", [])) - len(a.get("limiters", []))
    per_level = max(1.0, base_per_level + mod_count)
    subtotal = per_level * level

    # Nested Defects on Items / Weapons refund into the parent Attribute.
    nested_defect_refund = 0
    for d in a.get("defects", []) or []:
        if hasattr(d, "model_dump"):
            d = d.model_dump()
        nested_defect_refund += int(d.get("points_per_rank", 0)) * int(d.get("rank", 0))

    return max(0.0, subtotal - nested_defect_refund)

def calc_derived(ch: dict, campaign: Optional[dict] = None) -> dict:
    s = ch.get("stats", {})
    body, mind, soul = s.get("body", 0), s.get("mind", 0), s.get("soul", 0)
    attr_map = {a["name"]: a for a in ch.get("attributes", [])}

    attack_mastery = attr_map.get("Attack Mastery", {}).get("level", 0)
    defence_mastery = attr_map.get("Defence Mastery", {}).get("level", 0)
    tough = attr_map.get("Tough", {}).get("level", 0)
    energised = attr_map.get("Energised", {}).get("level", 0)
    massive_damage = attr_map.get("Massive Damage", {}).get("level", 0)

    # Damage Rating baseline can be overridden per campaign (V3.5 benchmark).
    dm_base = 5
    if campaign and isinstance(campaign.get("damage_rating_baseline"), int) and campaign["damage_rating_baseline"] > 0:
        dm_base = campaign["damage_rating_baseline"]

    cv = (body + mind + soul) // 3
    atk = cv + attack_mastery
    dfn = cv - 2 + defence_mastery
    hp = (body + soul) * 5 + tough * 5
    ep = (mind + soul) * 5 + energised * 5
    dm = dm_base + massive_damage * 5
    return {
        "combat_value": cv, "attack_value": atk, "defence_value": dfn,
        "health_points": hp, "energy_points": ep, "damage_multiplier": dm,
        "damage_rating_baseline": dm_base,
    }

def calc_spent_points(ch: dict) -> Dict[str, float]:
    s = ch.get("stats", {})
    stat_cost = s.get("body", 0) + s.get("mind", 0) + s.get("soul", 0)
    # Use attribute_cost() so the BESM ≥1/Level clamp + nested Item/Weapon
    # Defects are reflected in totals (single source of truth).
    attr_cost = sum(attribute_cost(a) for a in ch.get("attributes", []))
    skill_cost = sum(int(sk.get("cost_per_level", 0)) * int(sk.get("level", 0))
                     for sk in ch.get("skills", []))
    defect_points = sum(int(d.get("points_per_rank", 0)) * int(d.get("rank", 0))
                        for d in ch.get("defects", []))
    # Defect refunds are SUBTRACTED from total (returned to player).
    total = stat_cost + attr_cost + skill_cost - defect_points
    return {
        "stat_cost": stat_cost,
        "attribute_cost": attr_cost,
        "skill_cost": skill_cost,
        "defect_points": defect_points,  # always positive: total points refunded
        "total_spent": total,
    }

@api.post("/characters")
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
    return sanitize(doc)


@api.post("/campaigns/{cid}/seed/evereantha")
async def seed_evereantha_pcs(cid: str, user: dict = Depends(get_current_user)):
    """GM-only: insert three Adventurous-tier sample PCs from the public
    Evereantha setting. They become NPCs / pre-built sheets the GM can hand
    to players who want to drop in fast. Idempotent — re-running adds new
    copies, so the GM should clean up duplicates manually if reseeding.
    Only allowed on BESM 4E system campaigns; samples use core BESM mechanics.
    """
    from seed_evereantha import EVEREANTHA_PCS
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Campaign not found")
    if user["id"] != camp["gm_id"] and user.get("role") != "admin":
        raise HTTPException(403, "Only the GM may seed sample characters")
    if camp.get("system_id", "besm-4e") != "besm-4e":
        raise HTTPException(400, "Evereantha sample PCs are BESM 4E builds. "
                                  "Switch the campaign system to BESM 4E first.")
    created = []
    for pc in EVEREANTHA_PCS:
        doc = {
            "id": new_id(),
            "campaign_id": cid,
            "owner_id": user["id"],
            "owner_name": user["name"],
            "created_at": now_iso(),
            "name": pc["name"],
            "concept": pc["concept"],
            "power_level": pc["power_level"],
            "total_points": pc["total_points"],
            "token_color": pc.get("token_color", ""),
            "size": pc.get("size", "Medium"),
            "stats": pc["stats"],
            "attributes": pc["attributes"],
            "defects": pc["defects"],
            "skills": pc.get("skills", []),
            "power_packs": pc.get("power_packs", []),
            "notes": "Evereantha sample PC — Adventurous tier (~80 pts).",
            "published": True,
            "folio": pc.get("folio", {}),
        }
        doc["derived"] = calc_derived(doc, camp)
        doc["spent"] = calc_spent_points(doc)
        await db.characters.insert_one(doc)
        created.append(sanitize(doc))
    return {"created": len(created), "characters": created}

@api.get("/campaigns/{cid}/characters")
async def list_characters(cid: str, user: dict = Depends(get_current_user)):
    rows = await db.characters.find({"campaign_id": cid}, {"_id": 0}).to_list(200)
    return rows

@api.get("/characters/{ch_id}")
async def get_character(ch_id: str, user: dict = Depends(get_current_user)):
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    return ch

@api.put("/characters/{ch_id}")
async def update_character(ch_id: str, body: CharacterIn, user: dict = Depends(get_current_user)):
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
    return sanitize(update)

@api.delete("/characters/{ch_id}")
async def delete_character(ch_id: str, user: dict = Depends(get_current_user)):
    ch = await db.characters.find_one({"id": ch_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    if user["id"] != ch["owner_id"] and user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Not permitted")
    await db.characters.delete_one({"id": ch_id})
    return {"ok": True}

# -------- Nodes (Knowledge) --------

def visible_to(node: dict, user_id: str, camp: dict) -> bool:
    if camp["gm_id"] == user_id:
        return True
    v = node.get("visibility", "gm_only")
    if v == "shared":
        return True
    if v == "revealed" and user_id in node.get("revealed_to", []):
        return True
    return False

@api.post("/nodes")
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
    # Players can only create shared nodes by default
    if camp["gm_id"] != user["id"]:
        doc["visibility"] = "shared"
    await db.nodes.insert_one(doc)
    return sanitize(doc)

@api.get("/campaigns/{cid}/nodes")
async def list_nodes(cid: str, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": cid}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    rows = await db.nodes.find({"campaign_id": cid}, {"_id": 0}).to_list(500)
    return [n for n in rows if visible_to(n, user["id"], camp)]

@api.put("/nodes/{nid}")
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

@api.post("/nodes/{nid}/reveal")
async def reveal_node(nid: str, body: NodeRevealIn, user: dict = Depends(get_current_user)):
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

@api.delete("/nodes/{nid}")
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

@api.post("/edges")
async def create_edge(body: EdgeIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": body.campaign_id}, {"_id": 0})
    if not camp or (camp["gm_id"] != user["id"] and user["id"] not in camp.get("member_ids", [])):
        raise HTTPException(403, "Not permitted")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    await db.edges.insert_one(doc)
    return sanitize(doc)

@api.get("/campaigns/{cid}/edges")
async def list_edges(cid: str, user: dict = Depends(get_current_user)):
    rows = await db.edges.find({"campaign_id": cid}, {"_id": 0}).to_list(500)
    return rows

# -------- Sessions --------

@api.post("/sessions")
async def create_session(body: SessionIn, user: dict = Depends(get_current_user)):
    camp = await db.campaigns.find_one({"id": body.campaign_id}, {"_id": 0})
    if not camp:
        raise HTTPException(404, "Not found")
    if camp["gm_id"] != user["id"]:
        raise HTTPException(403, "Only GM can create sessions")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    doc["status"] = "open"
    doc["round"] = 0
    await db.sessions.insert_one(doc)
    # Auto-pin: post the most recent recap from any previous session of this
    # campaign as a system chat message — "What happened last time…"
    try:
        prev_recap = await db.recaps.find_one(
            {"campaign_id": body.campaign_id},
            {"_id": 0}, sort=[("created_at", -1)],
        )
        if prev_recap and prev_recap.get("text"):
            pinned = {
                "id": new_id(), "session_id": doc["id"],
                "message": f"📜 What happened last time…\n\n{prev_recap['text']}",
                "kind": "system", "user_id": "system",
                "user_name": "LOREMASTER",
                "pinned": True,
                "created_at": now_iso(),
            }
            await db.chat_logs.insert_one(pinned)
    except Exception as e:
        print(f"[auto-pin recap] {e}")
    return sanitize(doc)

@api.get("/campaigns/{cid}/sessions")
async def list_sessions(cid: str, user: dict = Depends(get_current_user)):
    rows = await db.sessions.find({"campaign_id": cid}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return rows

@api.get("/sessions/{sid}")
async def get_session(sid: str, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Not found")
    return s

# -------- Chat --------

@api.post("/chat")
async def post_chat(body: ChatIn, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": body.session_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "No session")
    doc = {
        "id": new_id(), "session_id": body.session_id, "message": body.message,
        "kind": body.kind, "user_id": user["id"], "user_name": user["name"],
        "created_at": now_iso(),
    }
    await db.chat_logs.insert_one(doc)
    await broadcast(body.session_id, {"type": "chat", "data": sanitize(doc)})
    return sanitize(doc)

@api.get("/sessions/{sid}/chat")
async def list_chat(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.chat_logs.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return rows

# -------- Dice --------

DICE_TOKEN = re.compile(r"^\s*(\d+)d(\d+)\s*$")

def roll_dice(notation: str, stat_values: Dict[str, int] = None) -> Dict[str, Any]:
    stat_values = stat_values or {}
    # Tokenise: e.g. "2d6+3+Body"
    notation = notation.strip()
    # Split on + / -
    parts = re.split(r"([+\-])", notation)
    sign = 1
    rolls: List[Dict[str, Any]] = []
    flat = 0
    total = 0
    for idx, p in enumerate(parts):
        p = p.strip()
        if not p:
            continue
        if p == "+":
            sign = 1; continue
        if p == "-":
            sign = -1; continue
        m = DICE_TOKEN.match(p)
        if m:
            n, d = int(m.group(1)), int(m.group(2))
            if n <= 0 or d <= 0 or n > 30 or d > 1000:
                raise HTTPException(400, "Invalid dice")
            these = [random.randint(1, d) for _ in range(n)]
            rolls.append({"notation": p, "sides": d, "results": these, "sign": sign})
            total += sign * sum(these)
        else:
            # try int
            try:
                v = int(p)
                flat += sign * v
                total += sign * v
            except ValueError:
                # stat reference (case insensitive)
                key = p.lower()
                v = int(stat_values.get(key, 0))
                flat += sign * v
                total += sign * v
                rolls.append({"notation": p, "ref": p, "value": v, "sign": sign})
    return {"rolls": rolls, "flat": flat, "total": total}

@api.post("/dice")
async def post_dice(body: DiceIn, user: dict = Depends(get_current_user)):
    stats = {}
    if body.character_id:
        ch = await db.characters.find_one({"id": body.character_id}, {"_id": 0})
        if ch:
            s = ch.get("stats", {})
            d = ch.get("derived", {})
            stats = {
                "body": s.get("body", 0), "mind": s.get("mind", 0), "soul": s.get("soul", 0),
                "cv": d.get("combat_value", 0), "atk": d.get("attack_value", 0),
                "def": d.get("defence_value", 0),
                "combat_value": d.get("combat_value", 0),
                "attack_value": d.get("attack_value", 0),
                "defence_value": d.get("defence_value", 0),
            }
    result = roll_dice(body.notation, stats)
    doc = {
        "id": new_id(), "session_id": body.session_id, "user_id": user["id"],
        "user_name": user["name"], "notation": body.notation, "label": body.label,
        "result": result, "target": body.target, "character_id": body.character_id,
        "private": body.private, "created_at": now_iso(),
    }
    success = None
    if body.target is not None:
        success = result["total"] <= body.target  # BESM: roll 2d6+mods, want result UNDER target number (low)
        # Actually BESM uses roll-under for Stat/Skill 2d6 vs Target Number after modifiers.
        # We simply expose both sides; GM can interpret.
    doc["success"] = success
    await db.dice_rolls.insert_one(doc)
    await broadcast(body.session_id, {"type": "dice", "data": sanitize(doc)})
    return sanitize(doc)

@api.get("/sessions/{sid}/dice")
async def list_dice(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.dice_rolls.find({"session_id": sid}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return rows

# -------- Initiative --------

@api.post("/initiative")
async def add_initiative(body: InitiativeEntryIn, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": body.session_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "No session")
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    doc["active"] = True
    await db.initiative.insert_one(doc)
    await broadcast(body.session_id, {"type": "initiative", "data": sanitize(doc)})
    return sanitize(doc)

@api.get("/sessions/{sid}/initiative")
async def list_initiative(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.initiative.find({"session_id": sid}, {"_id": 0}).sort("roll", -1).to_list(100)
    return rows

@api.delete("/initiative/{iid}")
async def remove_initiative(iid: str, user: dict = Depends(get_current_user)):
    row = await db.initiative.find_one({"id": iid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Not found")
    await db.initiative.delete_one({"id": iid})
    await broadcast(row["session_id"], {"type": "initiative_remove", "data": {"id": iid}})
    return {"ok": True}

@api.post("/sessions/{sid}/round/advance")
async def advance_round(sid: str, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Not found")
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    if user["id"] != camp["gm_id"]:
        raise HTTPException(403, "Only GM")
    new_round = s.get("round", 0) + 1
    await db.sessions.update_one({"id": sid}, {"$set": {"round": new_round}})
    # Tick effects
    await db.effects.update_many({"session_id": sid, "active": True},
                                 {"$inc": {"duration_rounds": -1}})
    expired = await db.effects.find({"session_id": sid, "duration_rounds": {"$lte": 0}, "active": True},
                                    {"_id": 0}).to_list(200)
    for e in expired:
        await db.effects.update_one({"id": e["id"]}, {"$set": {"active": False}})
    await broadcast(sid, {"type": "round", "data": {"round": new_round, "expired": expired}})
    return {"round": new_round, "expired": expired}

# -------- Effects / Damage --------

@api.post("/effects")
async def add_effect(body: EffectIn, user: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc["id"] = new_id()
    doc["created_at"] = now_iso()
    doc["active"] = True
    doc["applied_by"] = user["name"]
    await db.effects.insert_one(doc)
    await broadcast(body.session_id, {"type": "effect", "data": sanitize(doc)})
    return sanitize(doc)

@api.get("/sessions/{sid}/effects")
async def list_effects(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.effects.find({"session_id": sid, "active": True}, {"_id": 0}).to_list(200)
    return rows

@api.delete("/effects/{eid}")
async def remove_effect(eid: str, user: dict = Depends(get_current_user)):
    row = await db.effects.find_one({"id": eid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Not found")
    await db.effects.update_one({"id": eid}, {"$set": {"active": False}})
    await broadcast(row["session_id"], {"type": "effect_remove", "data": {"id": eid}})
    return {"ok": True}

@api.post("/damage")
async def apply_damage(body: DamageIn, user: dict = Depends(get_current_user)):
    s = await db.sessions.find_one({"id": body.session_id}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Not found")
    msg = f"{body.target_name} took {body.amount} {body.kind.upper()} damage"
    doc = {
        "id": new_id(), "session_id": body.session_id, "message": msg,
        "kind": "system", "user_id": user["id"], "user_name": "SYSTEM",
        "created_at": now_iso(),
    }
    await db.chat_logs.insert_one(doc)
    await broadcast(body.session_id, {"type": "chat", "data": sanitize(doc)})
    return sanitize(doc)

# -------- Session Recap (LLM-powered) --------
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "").strip()
_recap_cooldown: Dict[str, datetime] = {}  # in-memory cooldown tracker

class RecapIn(BaseModel):
    style: Literal["narrative", "bullet", "in-character"] = "narrative"

@api.post("/sessions/{sid}/recap")
async def generate_recap(sid: str, body: RecapIn, user: dict = Depends(get_current_user)):
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
    # Rate-limit: 30s per (user, session)
    cooldown_key = f"{user['id']}:{sid}"
    last = _recap_cooldown.get(cooldown_key)
    if last and (datetime.now(timezone.utc) - last).total_seconds() < 30:
        raise HTTPException(429, "Recap cooldown — try again in a few seconds.")

    chat = await db.chat_logs.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    dice = await db.dice_rolls.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(300)
    chars = await db.characters.find({"campaign_id": s["campaign_id"]}, {"_id": 0, "name": 1, "concept": 1}).to_list(50)

    if not chat:
        raise HTTPException(400, "No chat history yet to recap")

    transcript_lines = []
    for m in chat[-200:]:
        kind = m.get("kind", "chat")
        prefix = "[SYSTEM]" if kind == "system" else f"[{kind.upper()}]"
        transcript_lines.append(f"{prefix} {m.get('user_name','?')}: {m.get('message','')}")
    dice_summary = []
    for d in dice[-60:]:
        r = d.get("result", {})
        label = d.get("label") or d.get("notation", "")
        dice_summary.append(f"  • {d.get('user_name','?')} rolled {d.get('notation','?')} = {r.get('total','?')} ({label})")

    char_lines = "\n".join(f"  • {c['name']} — {c.get('concept','')}" for c in chars[:20]) or "  (none)"
    transcript = "\n".join(transcript_lines[-180:])
    dice_block = "\n".join(dice_summary[-40:]) or "  (none)"

    style_instruction = {
        "narrative": "Write a flowing narrative recap (~180–240 words) in third-person past tense. Capture the emotional beats, the pivotal rolls, and any unanswered questions. Skip dice mechanics that didn't matter.",
        "bullet": "Write a tight bulleted recap. Group by: What happened · Who acted · What changed · Open threads. Keep each bullet to one line.",
        "in-character": "Write the recap as a journal entry from one of the player characters' perspective (pick whoever was most active). First-person, evocative, ~200 words.",
    }[body.style]

    system_prompt = (
        f"You are the Loremaster of a tabletop campaign called \"{camp['name']}\" "
        f"({camp.get('system','BESM 4E')}, {camp.get('power_level','Heroic')} tier). "
        f"Tone: {camp.get('tone') or 'unspecified'}. Genre: {camp.get('genre') or 'unspecified'}. "
        f"Your job: turn raw session logs into a recap the table will love rereading. "
        f"Never invent details that aren't in the transcript. Honour the players. {style_instruction}"
    )
    user_prompt = (
        f"Session: \"{s.get('title','Untitled session')}\" (round {s.get('round',0)}).\n\n"
        f"Characters at the table:\n{char_lines}\n\n"
        f"Transcript:\n{transcript}\n\n"
        f"Notable dice:\n{dice_block}\n\n"
        f"Now write the recap."
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

    # Update cooldown after successful generation
    _recap_cooldown[f"{user['id']}:{sid}"] = datetime.now(timezone.utc)

    doc = {
        "id": new_id(), "session_id": sid, "campaign_id": s["campaign_id"],
        "style": body.style, "text": recap_text, "by_user_id": user["id"],
        "by_user_name": user["name"], "created_at": now_iso(),
    }
    await db.recaps.insert_one(doc)
    return sanitize(doc)

@api.get("/sessions/{sid}/recaps")
async def list_recaps(sid: str, user: dict = Depends(get_current_user)):
    rows = await db.recaps.find({"session_id": sid}, {"_id": 0}).sort("created_at", -1).to_list(20)
    return rows

# -------- WebSocket session bus (chat + WebRTC signaling) --------
import json as _json

class Peer:
    __slots__ = ("ws", "uid", "name", "conn_id")
    def __init__(self, ws, uid, name, conn_id):
        self.ws = ws; self.uid = uid; self.name = name; self.conn_id = conn_id

class Bus:
    def __init__(self):
        self.rooms: Dict[str, List[Peer]] = {}

    async def join(self, sid: str, ws: WebSocket, uid: str, name: str) -> Peer:
        await ws.accept()
        peer = Peer(ws=ws, uid=uid, name=name, conn_id=secrets.token_urlsafe(8))
        self.rooms.setdefault(sid, []).append(peer)
        return peer

    def leave(self, sid: str, ws: WebSocket) -> Optional[Peer]:
        if sid not in self.rooms:
            return None
        gone = None
        kept = []
        for p in self.rooms[sid]:
            if p.ws is ws and gone is None:
                gone = p
            else:
                kept.append(p)
        self.rooms[sid] = kept
        return gone

    def peers(self, sid: str) -> List[Peer]:
        return list(self.rooms.get(sid, []))

    async def _safe_send(self, peer: Peer, payload: dict):
        try:
            await peer.ws.send_text(_json.dumps(payload, default=str))
            return True
        except Exception:
            return False

    async def send(self, sid: str, payload: dict, exclude_ws: Optional[WebSocket] = None):
        dead = []
        for p in list(self.rooms.get(sid, [])):
            if exclude_ws is not None and p.ws is exclude_ws:
                continue
            ok = await self._safe_send(p, payload)
            if not ok:
                dead.append(p)
        for p in dead:
            self.leave(sid, p.ws)

    async def send_to(self, sid: str, conn_id: str, payload: dict):
        for p in list(self.rooms.get(sid, [])):
            if p.conn_id == conn_id:
                ok = await self._safe_send(p, payload)
                if not ok:
                    self.leave(sid, p.ws)
                return

bus = Bus()

async def broadcast(sid: str, payload: dict):
    await bus.send(sid, payload)

@app.websocket("/api/ws/session/{sid}")
async def ws_session(ws: WebSocket, sid: str, token: str = None):
    # Token auth: accept bearer token as query parameter
    if not token:
        await ws.close(code=4401)
        return
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            await ws.close(code=4401); return
    except jwt.PyJWTError:
        await ws.close(code=4401); return
    # Verify session exists
    s = await db.sessions.find_one({"id": sid}, {"_id": 0})
    if not s:
        await ws.close(code=4404); return
    # Verify user has access to the campaign
    camp = await db.campaigns.find_one({"id": s["campaign_id"]}, {"_id": 0})
    uid = payload.get("sub")
    if not camp or (camp["gm_id"] != uid and uid not in camp.get("member_ids", []) and camp.get("visibility") != "public"):
        await ws.close(code=4403); return

    user = await db.users.find_one({"id": uid}, {"_id": 0}) or {}
    name = user.get("name") or user.get("email") or "Adventurer"
    is_gm = (camp.get("gm_id") == uid)

    me = await bus.join(sid, ws, uid, name)

    # 1. Tell the joiner who's already in the room
    others = [
        {"conn_id": p.conn_id, "uid": p.uid, "name": p.name}
        for p in bus.peers(sid) if p.conn_id != me.conn_id
    ]
    await bus._safe_send(me, {
        "type": "presence:room",
        "data": {
            "you": {"conn_id": me.conn_id, "uid": me.uid, "name": me.name, "is_gm": is_gm},
            "peers": others,
        },
    })
    # 2. Tell everyone else a new peer arrived
    await bus.send(sid, {
        "type": "presence:join",
        "data": {"conn_id": me.conn_id, "uid": me.uid, "name": me.name, "is_gm": is_gm},
    }, exclude_ws=ws)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = _json.loads(raw)
            except Exception:
                continue
            t = msg.get("type")
            if t in ("webrtc:offer", "webrtc:answer", "webrtc:ice"):
                target = msg.get("to")
                data = msg.get("data") or {}
                if not target:
                    continue
                await bus.send_to(sid, target, {
                    "type": t,
                    "data": {**data, "from": me.conn_id, "from_name": me.name},
                })
            elif t == "presence:av-state":
                data = msg.get("data") or {}
                await bus.send(sid, {
                    "type": "presence:av-state",
                    "data": {"conn_id": me.conn_id, **data},
                }, exclude_ws=ws)
            # any other inbound types are ignored — REST endpoints handle chat/dice/init
    except WebSocketDisconnect:
        gone = bus.leave(sid, ws)
        if gone:
            await bus.send(sid, {
                "type": "presence:leave",
                "data": {"conn_id": gone.conn_id, "uid": gone.uid, "name": gone.name},
            })

# -------- Health --------

@api.get("/health")
async def health():
    return {"ok": True, "service": "table-gnostic", "time": now_iso()}

app.include_router(api)
