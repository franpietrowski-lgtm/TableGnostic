# Auth Testing Playbook — Table-Gnostic

Credentials (seeded from backend/.env):
- Admin: admin@tablegnostic.com / admin123 (role: admin)
- Test GM: gm@tablegnostic.com / gm123456 (role: user)
- Test Player: player@tablegnostic.com / player12345 (role: user)

Auth endpoints (all under /api/auth):
- POST /api/auth/register   { email, password, name }
- POST /api/auth/login      { email, password }
- POST /api/auth/logout
- GET  /api/auth/me
- POST /api/auth/refresh
- POST /api/auth/forgot-password
- POST /api/auth/reset-password

Cookie behaviour:
- access_token (15 min) and refresh_token (7 days) set as httpOnly cookies with samesite=lax.
- All requests must send cookies (axios withCredentials=true or fetch credentials:'include').
- /api/auth/me uses the cookie to return the current user.

Brute-force protection:
- 5 failed attempts per (ip, email) within 15 minutes = 423 locked.

MongoDB verification:
```
mongosh
use tablegnostic
db.users.find({role:"admin"}).pretty()
db.users.getIndexes()
```
Expect: unique index on email, TTL on password_reset_tokens.expires_at.

API sanity:
```
curl -c /tmp/c.txt -X POST $BACKEND/api/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@tablegnostic.com","password":"admin123"}'
curl -b /tmp/c.txt $BACKEND/api/auth/me
```
