# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A BESM 4E-aware tabletop platform unifying worldbuilding, session play, character automation, and knowledge graphs.

## 1. Original Problem Statement

Rebranded from ForgeWeave → **Table-Gnostic**. System-aware tabletop platform unifying World Anvil + Roll20 + D&D Beyond + Obsidian on a rules execution engine that supports BESM 4E without reproducing copyrighted text — references source names + page numbers only.

## 2. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT auth + token-authenticated WebSockets + Resend email
- **Frontend:** React 18 + Tailwind + Radix + lucide-react, dark cosmic/gold aesthetic (Cinzel/Fraunces/Manrope)
- **Auth:** Bearer-token primary (localStorage), httpOnly cookie backup
- **CORS:** locked by regex to `*.preview.emergentagent.com` + `localhost:*` with credentials enabled
- **Data:** UUID `id` fields (never Mongo ObjectId in responses)

## 3. User Personas

- **Game Master (GM)** — Atelier planner, custom rules author, knowledge weaver, session runner, primer writer
- **Player** — Seekers' Hall explorer, character forger, dice-roller at live sessions
- **Admin** — platform operator

## 4. Implemented

### V1 (2026-04-23)
- JWT auth with seeded admin/GM/Player
- BESM 4E reference (86 attrs / 36 defects / 5 enh / 23 lim / 7 skill groups)
- Campaign CRUD + public/private + join/leave
- Full BESM character forge with live derived values
- Per-campaign GM custom Attributes/Defects/Skills
- Live session with WebSocket 3-column UI (Initiative / Chat / Dice Altar)
- Knowledge nodes with 3-tier visibility + reveal + edges
- Searchable BESM Reference tome

### V1.1 (2026-04-23)
- Frontend switched to Bearer-token primary
- **Campaign Atelier** — 7-phase wizard based on Guy Sclanders' *Complete Guide to Creating Epic Campaigns* (credited)
- Genesis → Nodes materialisation
- **Tables Seeking Players** discovery page
- WebSocket token auth (4401/4403/4404)
- CORS locked to preview + localhost with credentials

### V1.2 (2026-04-23 — current)
- **Atelier tooltips** — every field has a hover `Tip` component with GM-coaching guidance; rotating prompt chips under each textarea (inspired by World Anvil's prompt-based writing)
- **Player Primer** — GM-written briefing stored on the campaign, visible to all seated players; displayed as a "Campaign Briefing" card at the top of the Character Forge
- **Allow / Prohibit Lists** — GM can restrict character-forge pickers by listing allowed or prohibited Attributes/Defects/Skill Groups. Prohibited items are hidden from the player's selector; empty allowed = all permitted
- **Invite Links** — every campaign auto-generates an `invite_token`; GM can copy `/invite/{token}` URL, regenerate (revokes old), or share directly. Public `/api/invites/{token}` endpoint returns campaign summary without auth so non-users see what they're signing up for. Accepting while signed-in joins the table in one click; while signed-out routes to register/login then back
- **Character Forge preloads** campaign power-level + points (no more manual selection of a level that's off-spec)
- **BESM Extras reference** — 21 rule expansions added (Shock Value p.14, Sanity Points p.15, Skill Ranks p.19, Individual Skills p.26, Power Packs p.73, Mass Combat p.52, Critical Failures p.57, etc.), cited as `BESM Extras` (Dyskami, v1.1.2). New "BESM Extras" tab in the Reference tome.
- **Node `fields` dict** — NodeIn now accepts a structured `fields` object for per-type article data (Character Folio-style). Wired into the data model; UI integration to follow in V1.3
- **Resend email integration** for password reset — `RESEND_API_KEY` + `SENDER_EMAIL` in `.env`. Falls back to console logging if no key; resilient (try/except wrapped) so auth flow never errors. Reset link uses `FRONTEND_PUBLIC_URL`

### Testing
- **Backend:** 71/72 pytest (98.6%) — iteration_4.json. 17 new tests added: BESM Extras, Campaign Primer, Invite Flow (8 tests including table-full, idempotent join, invite regen + revoke), Forgot Password (2). Pre-existing iteration-3 tests all still green.
- Residual CORS test issue has been resolved (FRONTEND_URL now `""` → regex-only mode → preflight echoes specific origin + credentials:true, verified by curl).

## 5. Backlog

### P0 — pending user action
- User walks the full flow: register → Atelier → primer → invite link → player joins → forge filtered character → start session
- User provides **Resend API key** (and optionally verifies a sender domain) to activate live password-reset emails — right now emails log to stdout only

### P1 — V2 per original PRD
- **World Codex** — per-type structured article editors (World/Locations/Organizations/Species/Items/Lore/Events/History) backed by the new `fields` dict on nodes (Character Folio + World Anvil structure captured in design notes)
- **Knowledge Graph UI canvas** — drag/drop node-link diagram (currently list view)
- **Character Folio fields** — Edges & Obstacles, Goals, Family, History of Events, Personality Profile, Group Dynamics, Advancement tracking, Journal sections (from `dys_besm_character_folio_v1.01.pdf`)
- **Relationship maps** — family trees, diplomatic webs, NPC relationship graphs
- **Timelines** — auto-placed event scroller
- **Maps with pins** linking to location nodes
- **Professional output templates** (session recap / NPC cards / handouts export)
- **Split server.py** (now 1,300+ lines) into auth/campaigns/invites/characters/sessions/ws/genesis modules
- **PATCH semantics** for campaign edit (current PUT risks resetting missing fields)

### P2 — V3
- Battlemap + token system
- **Camera/mic Discord-like AV seats** (user-requested)
- Advanced automation (chained effects, condition triggers)
- Mobile-first responsive pass

## 6. Credits

- **BESM 4E rules** — Mark MacKinnon, Dyskami Publishing, 2020
- **BESM Extras** — Dyskami Publishing, v1.1.2
- **BESM Character Folio** — Dyskami Publishing, v1.01
- **Campaign Atelier framework** — Guy Sclanders, *How to be a Great GM* (2018) — credited in the wizard footer with link to greatgamemaster.com
- **Table-Gnostic brand** — user-provided logo and positioning

## 7. Next Tasks

1. User provides Resend API key (or confirms console-log is fine for now) and tests password-reset flow
2. Pick next build focus:
   - **World Codex** (structured article editors using the new `fields` dict) — highest user-visible impact given the World Anvil brief
   - **Knowledge Graph canvas** — the V2 visual PRD goal
   - **Character Folio fields** — deeper character depth using the uploaded Folio PDF
