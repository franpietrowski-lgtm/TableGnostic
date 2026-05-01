# Table-Gnostic — Test Credentials

All three accounts are auto-seeded on backend startup (see `seed_user` in `server.py`).
The seed step is **authoritative** — on every boot the three role assignments are
re-asserted (so manual DB edits to these accounts will be overwritten).

| Role   | Email                          | Password      | What they can do                                        |
|--------|--------------------------------|---------------|---------------------------------------------------------|
| Admin  | admin@tablegnostic.com         | admin123      | Everything (GM rights + admin overrides)                |
| GM     | gm@tablegnostic.com            | gm123456      | Host campaigns, run sessions, full Knowledge Web rights |
| Player | player@tablegnostic.com        | player12345   | Take seats only — cannot create campaigns (HTTP 403)    |

**Roles model:**
- `player` — seat-only. The "Forge a campaign" CTA is disabled (`GMs only` label).
- `gm` — can create campaigns, run sessions, edit Primer, weave nodes.
- `admin` — every GM right plus admin-only routes.
- Legacy `user` accounts auto-migrate to `gm` on startup.

Auth endpoints (all prefixed with `/api`):
- POST `/api/auth/register` — body `{ email, password, name, role: 'player'|'gm' }` (default `player`)
- POST `/api/auth/login` — body `{ email, password }` (sets httpOnly cookies AND returns access_token + role in JSON)
- POST `/api/auth/logout`
- GET  `/api/auth/me` (returns user with `role`)
- POST `/api/auth/refresh`
- POST `/api/auth/forgot-password`
- POST `/api/auth/reset-password`

Session cookies (httpOnly, samesite=lax):
- `access_token` — 8 hours
- `refresh_token` — 30 days

Bearer fallback: frontend also stores `access_token` in localStorage and sends
`Authorization: Bearer <token>` — either cookies or header work.

Brute-force protection: 5 failed login attempts per (ip, email) = HTTP 423 lock for 15 minutes.

# Test credentials

> Updated 2026-04-26 (V4.3) — generic demo accounts retired. Only GMFran remains.

## Demo accounts

| Email                          | Password           | Role     | Notes                                    |
|--------------------------------|--------------------|----------|------------------------------------------|
| **franpietrowski@gmail.com**   | **PieGod08!!**     | admin    | **GMFran** — sole authoritative account  |
| **albanaszak@ymail.com**       | **AuroraTest123!** | player   | **Aurora** — owns Eli across all 4 systems for cross-account UX testing (V6.16) |

The previous generic-demo accounts (admin@tablegnostic.com / gm@tablegnostic.com / player@tablegnostic.com) have been **retired in V4.3**. `core/startup.py` actively removes them from the DB on every backend boot.

If a new player needs access during testing, register them via `POST /api/auth/register` (player or gm role), then GMFran can transfer characters to them via `POST /api/characters/{id}/transfer?new_owner_id=...`.

## Test campaigns

| Field            | Value                                          |
|------------------|------------------------------------------------|
| Evereantha demo  | Run `POST /api/admin/reset-to-evereantha` to (re)create. Owner = caller of the reset. |
| World Codex      | 20 nodes — 5 locations, 2 factions, 6 NPCs, 1 creature, 2 lore, 4 quests |
| PCs (3)          | Eli (Apocophae), Laryk (Ferrilith), Roney (Techgnostic) |
| Atelier/Genesis  | All 7 phases pre-filled. Nemesis: Order of the Darkening Star |

Re-seed at any time: `POST /api/admin/reset-to-evereantha` (admin role only).
This wipes campaigns/characters/sessions/chat/dice/initiative/effects/nodes/edges/recaps/custom_attributes/genesis (preserves users) and recreates the canonical Evereantha demo table.

Any GM/admin can also `POST /api/campaigns/{cid}/clone` to fork any visible campaign into their own copy (carries nodes, edges, Genesis, custom rules, published characters).
