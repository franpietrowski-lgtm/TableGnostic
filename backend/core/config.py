"""Configuration & shared constants — read once at startup."""
import os

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
FRONTEND_PUBLIC_URL = os.environ.get("FRONTEND_PUBLIC_URL", "").strip()
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "").strip()

# CORS — empty allow_origins falls back to the regex below.
# V6.25.32 — Production deployments (tablegnostic.com, *.emergent.host) were
# being rejected by CORS because the regex only matched preview/localhost,
# manifesting as "Network Error" on login after redeploy. We now also allow
# the canonical custom domain and Emergent's deployment hosts.
_extra = os.environ.get("FRONTEND_URL", "").strip()
ALLOW_ORIGINS = [_extra] if _extra and _extra != "*" else []
ALLOW_ORIGIN_REGEX = (
    r"https://.*\.preview\.emergentagent\.com|"
    r"https://.*\.emergentagent\.com|"
    r"https://.*\.emergent\.host|"
    r"https://(www\.)?tablegnostic\.com|"
    r"http://localhost:\d+|http://127\.0\.0\.1:\d+"
)
