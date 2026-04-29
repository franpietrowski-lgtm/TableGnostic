"""Table-Gnostic backend — BESM 4E aware TTRPG platform.

This file is intentionally thin: it just composes the FastAPI app from the
modular routers under `routes/` and the shared infrastructure under `core/`.

Layout:
    core/        config, db, security, models, cost_engine, bus, email, startup
    routes/      auth · besm · campaigns · characters · nodes · sessions
                 · seed · recap

The session-room layer (sessions + chat + dice + WebRTC mesh signalling) is
all in `routes/sessions.py`. A future LiveKit / Daily / Agora migration will
swap the relay parts of `core/bus.py` + the `webrtc:*` handler in that router
without touching any of the table-state routes.
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import ALLOW_ORIGINS, ALLOW_ORIGIN_REGEX
from core.startup import run_startup
from routes import auth, besm, campaigns, characters, nodes, recap, seed, sessions
from routes import admin as admin_routes
from routes import battlemap as battlemap_routes
from routes import channels as channels_routes
from routes import uploads as uploads_routes
from routes import xp as xp_routes
from routes import atelier as atelier_routes
from routes import ingest as ingest_routes
from routes import pdf_export as pdf_export_routes
from routes import xp_approval as xp_approval_routes
from routes import reference_editor as reference_editor_routes
from routes import cards as cards_routes
from routes import director as director_routes
from routes import epic_campaign as epic_campaign_routes

app = FastAPI(title="Table-Gnostic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_origin_regex=ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def permissions_policy_header(request: Request, call_next):
    """Permissions-Policy: explicitly allow camera + microphone for AV Seats.
    Without these headers, modern browsers reject getUserMedia() inside
    embedded iframes (preview / kiosks). The frontend additionally detects
    iframe embedding and surfaces an "Open in new tab" banner when needed.
    """
    response = await call_next(request)
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), display-capture=(self)"
    response.headers["Feature-Policy"] = "camera 'self'; microphone 'self'"
    return response


@app.on_event("startup")
async def on_startup():
    await run_startup()


# Mount domain routers (each declares its own /api prefix + OpenAPI tag).
app.include_router(auth.router)
app.include_router(besm.router)
app.include_router(campaigns.router)
app.include_router(characters.router)
app.include_router(nodes.router)
app.include_router(seed.router)
app.include_router(sessions.router)
app.include_router(sessions.ws_router)  # WebSocket — no prefix, declares its own path
app.include_router(recap.router)
app.include_router(admin_routes.router)
app.include_router(battlemap_routes.router)
app.include_router(channels_routes.router)
app.include_router(uploads_routes.router)
app.include_router(xp_routes.router)
app.include_router(atelier_routes.router)
app.include_router(ingest_routes.router)
app.include_router(pdf_export_routes.router)
app.include_router(xp_approval_routes.router)
app.include_router(reference_editor_routes.router)
app.include_router(cards_routes.router)
app.include_router(director_routes.router)
app.include_router(epic_campaign_routes.router)

# Static-file mount: serve uploaded battlemap images from disk so GMs can
# drop in renders from Inkarnate / DungeonCraft / Talespire / RPGEngine
# without hosting them publicly first. The /api/uploads prefix is required
# so Kubernetes ingress routes correctly to this backend.
import os as _os
from pathlib import Path as _Path
_UPLOAD_ROOT = _Path(_os.environ.get("UPLOAD_DIR", "/app/backend/uploads")).resolve()
(_UPLOAD_ROOT / "maps").mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(_UPLOAD_ROOT)), name="uploads")
