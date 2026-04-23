# Table-Gnostic — Test Credentials

All three accounts are auto-seeded on backend startup (see `seed_user` in `server.py`).

| Role | Email | Password |
|---|---|---|
| Admin | admin@tablegnostic.com | admin123 |
| Test GM | gm@tablegnostic.com | gm123456 |
| Test Player | player@tablegnostic.com | player12345 |

Auth endpoints (all prefixed with `/api`):
- POST `/api/auth/register` — body `{ email, password, name }`
- POST `/api/auth/login` — body `{ email, password }` (sets httpOnly cookies AND returns access_token in JSON)
- POST `/api/auth/logout`
- GET  `/api/auth/me`
- POST `/api/auth/refresh`
- POST `/api/auth/forgot-password`
- POST `/api/auth/reset-password`

Session cookies (httpOnly, samesite=lax):
- `access_token` — 8 hours
- `refresh_token` — 30 days

Bearer fallback: frontend also stores `access_token` in localStorage and sends
`Authorization: Bearer <token>` — either cookies or header work.

Brute-force protection: 5 failed login attempts per (ip, email) = HTTP 423 lock for 15 minutes.
