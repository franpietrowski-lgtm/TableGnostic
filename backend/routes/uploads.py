"""File uploads — battlemap backgrounds (and any future GM media).

POST /api/uploads/map     multipart/form-data → { url, width, height, bytes }

Files are written to /app/backend/uploads/maps/<id>.<ext> and served via
the StaticFiles mount at /api/uploads in server.py. This lets GMs drop in
maps from Inkarnate / DungeonCraft / Talespire / RPGEngine renders without
having to host them publicly first — a major friction point in
free-to-play tabletop apps.

Constraints:
  • image/png · image/jpeg · image/webp only.
  • 12 MB hard cap (battlemap renders rarely exceed 8 MB even at 4K).
  • GM-or-admin only; players never write to the filesystem.

Width/height are read with Pillow when available so the frontend can
auto-scale the grid to the image's pixel dimensions on first paint.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.db import new_id
from core.security import get_current_user

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# --- on-disk storage ---
UPLOAD_ROOT = Path(os.environ.get("UPLOAD_DIR", "/app/backend/uploads")).resolve()
MAP_DIR = UPLOAD_ROOT / "maps"
MAP_DIR.mkdir(parents=True, exist_ok=True)
AVATAR_DIR = UPLOAD_ROOT / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
PORTRAIT_DIR = UPLOAD_ROOT / "portraits"
PORTRAIT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}
MAX_BYTES = 32 * 1024 * 1024  # 32 MB — fits proper 2K (and most 4K) battlemap renders


def _sniff_dims(path: Path) -> tuple[Optional[int], Optional[int]]:
    """Best-effort image dimension read. Returns (None, None) if Pillow
    isn't installed — frontend will fall back to natural <img> dimensions."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size  # (w, h)
    except Exception:
        return None, None


@router.post("/map")
async def upload_map_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """GM-or-admin only. Accept a single PNG / JPEG / WEBP and return its
    served URL. The frontend uses the URL directly as the battlemap
    background and the (width,height) to recommend a grid scale."""
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "Only GMs and admins may upload battlemap images.")

    ctype = (file.content_type or "").lower()
    ext = ALLOWED_IMAGE_TYPES.get(ctype)
    if not ext:
        raise HTTPException(400, f"Unsupported image type '{ctype}'. "
                                  "Use PNG, JPEG, or WEBP.")

    fid = new_id()
    out = MAP_DIR / f"{fid}{ext}"

    # Stream-read with a hard cap so we never exhaust memory on a runaway upload.
    written = 0
    with out.open("wb") as fh:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > MAX_BYTES:
                fh.close()
                try:
                    out.unlink()
                except OSError:
                    pass
                raise HTTPException(413, f"Image exceeds {MAX_BYTES // (1024*1024)} MB cap.")
            fh.write(chunk)

    width, height = _sniff_dims(out)
    return {
        "url": f"/api/uploads/maps/{fid}{ext}",
        "width": width,
        "height": height,
        "bytes": written,
        "content_type": ctype,
    }



@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Any authenticated user — upload a personal avatar / token-fallback
    image. Used as the AV-tile placeholder when the user's camera is off
    AND on PDF character-sheet exports. 4 MB cap (avatars don't need to
    be 4K). Replaces any prior avatar by overwriting filename = user id."""
    ctype = (file.content_type or "").lower()
    ext = ALLOWED_IMAGE_TYPES.get(ctype)
    if not ext:
        raise HTTPException(400, f"Unsupported image type '{ctype}'. Use PNG, JPEG, or WEBP.")
    AVATAR_MAX = 4 * 1024 * 1024
    out = AVATAR_DIR / f"{user['id']}{ext}"
    written = 0
    with out.open("wb") as fh:
        while True:
            chunk = await file.read(512 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > AVATAR_MAX:
                fh.close()
                try:
                    out.unlink()
                except OSError:
                    pass
                raise HTTPException(413, f"Avatar exceeds {AVATAR_MAX // (1024 * 1024)} MB cap.")
            fh.write(chunk)
    # Clear any prior avatar with a different extension so we never serve stale.
    for sib in AVATAR_DIR.glob(f"{user['id']}.*"):
        if sib.name != out.name:
            try:
                sib.unlink()
            except OSError:
                pass
    url = f"/api/uploads/avatars/{user['id']}{ext}"
    # Persist on the user record so /api/auth/me returns it directly.
    from core.db import db as _db
    await _db.users.update_one({"id": user["id"]}, {"$set": {"avatar_url": url}})
    return {"url": url, "bytes": written, "content_type": ctype}


@router.post("/character-portrait/{character_id}")
async def upload_character_portrait(
    character_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """V6.11 — character portrait / character art upload. Owner of the
    character or the campaign GM may set the portrait. Stored at
    /api/uploads/portraits/{character_id}.{ext}, persisted on the
    character document as `portrait_url`. 4 MB cap.
    """
    from core.db import db as _db
    ch = await _db.characters.find_one({"id": character_id}, {"_id": 0})
    if not ch:
        raise HTTPException(404, "Character not found")
    camp = await _db.campaigns.find_one({"id": ch["campaign_id"]}, {"_id": 0})
    is_owner = ch.get("owner_id") == user["id"]
    is_gm = camp and (camp["gm_id"] == user["id"] or user.get("role") == "admin")
    if not (is_owner or is_gm):
        raise HTTPException(403, "Only the character's owner or the GM may set portrait")
    ctype = (file.content_type or "").lower()
    ext = ALLOWED_IMAGE_TYPES.get(ctype)
    if not ext:
        raise HTTPException(400, f"Unsupported image type '{ctype}'. Use PNG, JPEG, or WEBP.")
    PORTRAIT_MAX = 4 * 1024 * 1024
    out = PORTRAIT_DIR / f"{character_id}{ext}"
    written = 0
    with out.open("wb") as fh:
        while True:
            chunk = await file.read(512 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > PORTRAIT_MAX:
                fh.close()
                try:
                    out.unlink()
                except OSError:
                    pass
                raise HTTPException(413, f"Portrait exceeds {PORTRAIT_MAX // (1024 * 1024)} MB cap.")
            fh.write(chunk)
    # Clear prior with different extension.
    for sib in PORTRAIT_DIR.glob(f"{character_id}.*"):
        if sib.name != out.name:
            try:
                sib.unlink()
            except OSError:
                pass
    url = f"/api/uploads/portraits/{character_id}{ext}"
    await _db.characters.update_one(
        {"id": character_id}, {"$set": {"portrait_url": url}},
    )
    return {"url": url, "bytes": written, "content_type": ctype}
