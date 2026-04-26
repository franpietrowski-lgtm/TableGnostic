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

ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}
MAX_BYTES = 12 * 1024 * 1024  # 12 MB


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
