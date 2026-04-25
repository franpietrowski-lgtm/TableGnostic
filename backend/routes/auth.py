"""Auth — register / login / logout / me / refresh / forgot / reset.

Brute-force lock: 5 failed attempts per (ip, email) → HTTP 423 lock for 15 min.
Cookies + Bearer header both accepted; token type is checked.
"""
from datetime import datetime, timedelta, timezone
import secrets

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config import JWT_SECRET, JWT_ALGORITHM, FRONTEND_PUBLIC_URL
from core.db import db, new_id, now_iso, sanitize
from core.email import send_password_reset_email
from core.models import ForgotIn, LoginIn, RegisterIn, ResetIn
from core.security import (
    create_access_token, create_refresh_token, get_current_user,
    hash_password, set_auth_cookies, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
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


@router.post("/login")
async def login(body: LoginIn, request: Request, response: Response):
    email = body.email.lower()
    ip = request.client.host if request.client else "?"
    key = f"{ip}:{email}"
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


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return sanitize(user)


@router.post("/refresh")
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
                            max_age=8 * 3600, path="/")
        return {"access_token": access}
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token")


@router.post("/forgot-password")
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
                print(f"[email:error] {e}")
        except Exception as e:
            print(f"[forgot-password:error] {e}")
    # Always 200 — never leak whether the address exists.
    return {"ok": True}


@router.post("/reset-password")
async def reset_password(body: ResetIn):
    rec = await db.password_reset_tokens.find_one({"token": body.token, "used": False})
    if not rec or rec["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(400, "Invalid or expired token")
    await db.users.update_one({"id": rec["user_id"]},
                              {"$set": {"password_hash": hash_password(body.password)}})
    await db.password_reset_tokens.update_one({"token": body.token}, {"$set": {"used": True}})
    return {"ok": True}
