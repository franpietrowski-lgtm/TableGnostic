# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A BESM 4E-aware tabletop platform unifying worldbuilding, session play, character automation, and knowledge graphs.

## 1. Original Problem Statement

ForgeWeave → rebranded to **Table-Gnostic** at user's request. Build a system-aware tabletop platform that unifies:
- **World Anvil** — guided campaign creation & publishing
- **Roll20** — session execution (initiative, dice, chat)
- **D&D Beyond** — structured, automated character sheets
- **Obsidian** — graph-based knowledge + discovery webs

…on a **rules execution engine** that supports BESM 4E mechanics but **does not distribute copyrighted text** — only source references (book + page).

## 2. Architecture

- **Backend:** FastAPI + MongoDB (motor async) + JWT auth + WebSockets for live session bus
- **Frontend:** React 18 + Tailwind + Radix + Framer Motion + lucide-react, dark cosmic/gold aesthetic (Cinzel/Fraunces/Manrope typography)
- **Auth:** JWT (bcrypt + PyJWT) with httpOnly cookies AND Bearer fallback, brute-force lockout
- **Routes:** `/api/*` for backend; `/`, `/auth`, `/app/*` for frontend
- **Data:** all collections use UUID `id` fields (never expose Mongo ObjectId)

## 3. User Personas

- **Game Master (GM)** — authors campaigns, custom rules, knowledge nodes (GM-only by default), runs sessions, reveals info
- **Player** — seats at campaigns, builds BESM characters, rolls dice in sessions, sees only revealed knowledge
- **Admin** — platform operator

## 4. Core Requirements (static)

- Legal compliance: reference BESM 4E by **name + cost + page only**, never reproduce text
- Role-based visibility on every knowledge node (gm_only / shared / revealed)
- System-aware character sheet with auto-computed derived values
- Live multiplayer session with WebSocket broadcast (chat, dice, initiative, effects, rounds)

## 5. What Has Been Implemented (V1 — shipped 2026-04-23)

### Backend (`/app/backend/server.py`, 1000 lines)
- **Auth:** `/api/auth/{register,login,logout,me,refresh,forgot-password,reset-password}` with bcrypt, JWT cookies + Bearer, brute-force protection
- **Seeded Users:** admin / demo GM / demo Player (see `/app/memory/test_credentials.md`)
- **BESM Reference:** `/api/besm/reference` returns 86 attributes, 36 defects, 5 enhancements, 23 limiters, 7 skill groups, 5 power levels, 7 target numbers — every entry carries `{book: "BESM 4E", page: N}`
- **Campaigns:** CRUD, public/private discovery, join/leave, member caps, GM-only delete
- **Characters:** BESM sheet model with Body/Mind/Soul + attributes (with enhancements/limiters) + defects + skills; server computes `derived` (CV, Attack, Defence, HP, EP, DM) and `spent` point totals on every save
- **Knowledge Nodes:** 8 node types (npc, location, item, event, quest, lore, faction, creature), visibility gm_only / shared / revealed, `/nodes/{id}/reveal` GM-only
- **Edges:** directional links between nodes for the graph
- **Sessions:** GM-created; `/sessions/{id}/round/advance` ticks effect durations
- **Chat:** `/api/chat` (kinds: chat / ooc / action / system); damage applications post system messages
- **Dice:** `/api/dice` with free-form notation (e.g. `2d6+body-3`), resolves stat refs from linked character
- **Initiative / Effects / Damage**
- **WebSockets:** `/api/ws/session/{sid}` broadcasts type=chat|dice|initiative|effect|round on every mutation
- **Custom GM Rules:** per-campaign custom Attributes / Defects / Skills that appear in the character builder picker

### Frontend (`/app/frontend/src/components/`)
- **Landing** (`Landing.jsx`) — dark cosmic hero with Sigil mark, four pillar cards, table-gnostic creed
- **Auth** (`Auth.jsx`) — login/register with Demo GM and Demo Player prefill buttons
- **Shell** (`Shell.jsx`) — sidebar layout with brand mark, nav (Dashboard / Campaigns / BESM Reference), user pill, Leave Table
- **Dashboard** — hearth-style stat tiles + list of user's campaigns
- **Campaigns** (`Campaigns.jsx`) — list with public/private filters + "Forge a campaign" modal (all CampaignIn fields)
- **CampaignDetail** (`CampaignDetail.jsx`) — tabbed: Characters | Knowledge Web | Sessions | Custom Rules (GM). Node reveal, custom rule authoring.
- **CharacterBuilder** (`CharacterBuilder.jsx`) — full BESM forge: identity, stats, power-level, attributes picker (with per-attribute enhancements/limiters and live point cost), defects picker, skill groups picker, custom GM rules automatically fed into pickers, derived value readout, live points remaining
- **CharacterSheet** (`CharacterSheet.jsx`) — read-only sheet with quick-roll buttons (Body / Mind / Soul / Attack / Defence / Initiative) wired to an active session
- **SessionView** (`SessionView.jsx`) — three-column live session: Initiative + Effects + Damage | Chat | Dice Altar; WebSocket live updates; GM round advance
- **Reference** (`Reference.jsx`) — searchable tome over all BESM 4E reference data with tab switching

### Testing
- **Backend:** 40/40 pytest (100%) — `/app/test_reports/iteration_1.json`, `/app/backend/tests/backend_test.py`
- **Frontend E2E:** ~85% verified via Playwright — all major flows green (iteration_2.json). Missing data-testids on two inline forms were patched post-test.

## 6. Prioritised Backlog

### P0 (polish — for user review)
- Add pagination / infinite scroll to campaigns list once N>50
- Secure WebSocket with token query-param (noted in review)
- Wrap `AttributeRow`/`DefectRow`/`SkillRow` in `React.forwardRef` to silence a non-blocking console warning

### P1 (V2 per original PRD)
- **Knowledge Graph UI** — node-link canvas (currently list view); drag/drop, auto-layout
- **Player Discovery Web** — per-player revealed-subgraph visualiser
- **GM Workflow Wizard** — guided 6-phase campaign genesis (Ideation → Structure → Content → Linking → Session Prep → Run)
- **Professional Output templates** (session recap / NPC cards / handouts export)
- **Split server.py** into modules (auth, campaigns, characters, sessions, dice, ws)

### P2 (V3 per original PRD)
- Battlemap + token system
- Advanced automation (chained effects, condition triggers)
- **Device camera/mic Discord-like seamless digital play** (as requested by user) — voice/video seats at the table
- Table matchmaking search & invitations

## 7. Next Tasks

1. User validates MVP flow end-to-end (Register → Create campaign → Forge character → Start session → Roll)
2. Choose next feature focus: Knowledge Graph UI vs GM Workflow Wizard vs Discord-like AV seats
3. If going to production: (a) lock down WebSocket auth, (b) set explicit CORS origins + enable credentials, (c) configure email service for password reset
