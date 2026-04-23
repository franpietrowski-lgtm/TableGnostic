# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A BESM 4E-aware tabletop platform unifying worldbuilding, session play, character automation, and knowledge graphs.

## 1. Original Problem Statement

Rebranded from ForgeWeave → **Table-Gnostic**. Build a system-aware tabletop platform unifying World Anvil + Roll20 + D&D Beyond + Obsidian on a rules execution engine that supports BESM 4E mechanics **without reproducing copyrighted text** — only source references (book + page).

## 2. Architecture

- **Backend:** FastAPI + MongoDB (motor async) + JWT auth + token-authenticated WebSockets
- **Frontend:** React 18 + Tailwind + Radix + lucide-react, dark cosmic/gold aesthetic (Cinzel/Fraunces/Manrope)
- **Auth:** Bearer token primary (localStorage) with httpOnly cookie backup, bcrypt + PyJWT, brute-force lockout
- **CORS:** locked by regex to `*.preview.emergentagent.com` and `localhost:*` with credentials enabled
- **Data:** all collections use UUID `id` fields (never Mongo ObjectId in responses)

## 3. User Personas

- **Game Master (GM)** — authors campaigns via Atelier, custom rules, knowledge nodes, runs sessions
- **Player** — discovers tables in the Seekers' Hall, builds BESM characters, rolls dice live
- **Admin** — platform operator

## 4. Implemented — V1.1 (as of 2026-04-23)

### V1 Core (shipped earlier)
- JWT auth (admin / demo GM / demo Player seeded)
- BESM 4E reference: 86 attributes, 36 defects, 5 enhancements, 23 limiters, 7 skill groups — all source-cited
- Campaign CRUD + public/private + join/leave + member caps
- Full BESM character forge with enhancement/limiter picker + live derived values (CV/ATK/DEF/HP/EP/DM)
- Per-campaign GM custom Attributes/Defects/Skills
- Live session (WebSocket): 3-column Initiative / Chat / Dice Altar; stat-aware notation `2d6+body`
- Knowledge nodes with 3-tier visibility (gm_only / shared / revealed) + reveal system + edges
- Searchable BESM Reference tome

### V1.1 Enhancements (this iteration)
- **Auth fix** — switched frontend to Bearer-token primary; robust across browsers that block third-party cookies (Safari, Brave, incognito)
- **Campaign Atelier (`/app/campaigns/:id/genesis`)** — 7-phase GM workflow wizard based on Guy Sclanders' *The Complete Guide to Creating Epic Campaigns* (How to be a Great GM, 2018). Phases: The Sentence · Theme & Tone · Nemesis Design · Master Plot Acts · Adventure Outlines · Supporting Cast · Beginning & Ending. Credits the author in the footer with link to `greatgamemaster.com`.
- **Genesis → Nodes materialisation** — one-click turns Nemesis + NPCs + Adventures into gm_only knowledge nodes
- **Tables Seeking Players (`/app/discover`)** — discovery hall filtering public campaigns with open seats, by keyword + experience level; one-click "Take a seat"
- **WebSocket token auth** — `/api/ws/session/{sid}?token=<jwt>`; 4401 unauth / 4403 forbidden / 4404 not-found
- **CORS locked** to `*.preview.emergentagent.com` + `localhost:*` regex with credentials enabled; unknown origins are blocked
- **Campaign create → Atelier redirect** — GMs land directly in the wizard after forging a campaign

### Testing
- **Backend:** 54/55 pytest (98.2%) — `iteration_3.json`. Added 9 Genesis tests, 5 WebSocket auth tests, 2 CORS tests. All iteration-1 tests still green.
- **Frontend E2E:** ~85%+ verified previously; new CampaignGenesis + Discover components to be added to test matrix next iteration.

## 5. Prioritised Backlog

### P0 — pending user validation
- User walks through: register → Atelier (7 phases) → seed knowledge nodes → character forge → start session → roll
- Add email delivery for password reset (deferred — needs SendGrid or Resend integration + user-provided API key)

### P1 — V2 per original PRD
- Knowledge Graph UI canvas (list view → drag/drop node-link diagram)
- Player Discovery Web (per-player revealed subgraph)
- Professional output templates (session recap / NPC cards / handouts export)
- Split server.py into modules (auth, campaigns, characters, sessions, dice, ws, genesis)
- Forward ref wrappers for CharacterBuilder row components (silence console warning)

### P2 — V3
- Battlemap + token system
- **Device camera/mic Discord-like AV seats** (user-requested)
- Advanced automation (chained effects, condition triggers)
- Table invitation links + matchmaking notifications

## 6. Credits

- **BESM 4E rules** — Mark MacKinnon (Dyskami Publishing, 2020). Platform references names, costs, and page numbers only; consult the official rulebook for text.
- **Campaign Atelier framework** — Guy Sclanders, *The Complete Guide to Creating Epic Campaigns* (How to be a Great GM, 2018). Phase structure and prompts reference his approach; all GM-authored content belongs to the user.
- **Table-Gnostic brand** — user-provided logo and positioning.

## 7. Next Tasks

1. User validates login + end-to-end flow through the Atelier
2. Pick next: Knowledge Graph canvas vs Discord-like AV seats vs password-reset email integration
3. Before production: configure SendGrid/Resend for password reset, set canonical `FRONTEND_URL`, rotate JWT_SECRET
