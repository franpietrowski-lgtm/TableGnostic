"""Resend email transport. Falls back to console logging when the key is missing."""
import asyncio

import resend

from .config import RESEND_API_KEY, SENDER_EMAIL

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
