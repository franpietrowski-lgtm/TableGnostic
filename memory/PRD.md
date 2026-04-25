# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A BESM 4E-aware tabletop platform unifying worldbuilding, session play, character automation, and knowledge graphs.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT auth + token-authed WebSockets + Resend email + Claude Sonnet 4.5 (via emergentintegrations) for AI recaps
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph; dark cosmic/gold aesthetic
- **CORS:** regex-locked to `*.preview.emergentagent.com` + `localhost:*` with credentials enabled

## 2. Implemented (cumulative)

### V1.0–1.2 (prior summaries — see git history)
Auth, BESM 4E reference, campaigns, character forge, live sessions, knowledge nodes, BESM Reference tome, Atelier wizard with tooltips, Player Primer + allow/prohibit lists, invite links, BESM Extras, structured node `fields`, Resend email scaffolding.

### V2.0 (this iteration — 2026-04-25)

**World Codex (the big World Anvil ask)**
- 8 article types (NPC, Location, Organization, Event, Species, Item, Lore, Quest), each with its own structured field template inspired by World Anvil's pre-scaffolded articles
- Type-specific prompts under each field ("What does the air feel like here?", "What event still echoes in its walls?")
- Type filter chips with live counts in the Knowledge Web
- New `NodeEditor` modal with one-click type selection + structured fields
- All article data persists in `node.fields` dict (server-side `Dict[str, Any]`) — backwards compatible with the original simple `content` text

**Knowledge Graph canvas**
- Pure-SVG force-directed graph (custom physics simulation, no external deps)
- Toggle between List view ↔ Graph view
- Drag nodes to reposition; click to inspect; node colour by type; edges as constellation lines with optional labels
- Quick "Link" button to connect any two nodes by title substring + relation label

**Character Folio (from BESM Folio v1.01 PDF)**
- Full Folio panel below skills: Aliases · Gender/Species/Age · Occupation · Group dynamics · Physical description · Personality · Motivations · Fears · **Edges** (situational +1) · **Obstacles** (recurring −1) · **Goals** (short / long / secret) · **Family & Bonds** · **History of Events** · **Journal**
- Stored in `character.folio` dict; round-trips through the API

**Session Recap (the potential improvement)**
- One-click recap button in the Session view; modal pops with the result
- Three styles: **Narrative** (third-person past, ~200 words), **Bulleted** (groups), **In-character** (first-person journal entry)
- Uses Claude Sonnet 4.5 via emergentintegrations + EMERGENT_LLM_KEY
- Honours the campaign's tone + genre + character names (Loremaster system prompt)
- 30-second per-(user, session) cooldown to prevent cost spikes
- Recaps persisted in `db.recaps`; `GET /sessions/{sid}/recaps` returns the history

**Resend email — live**
- `RESEND_API_KEY` set; password-reset emails are now sent on `forgot-password`
- New `/reset?token=…` page lands users from the email; gracefully validates and confirms
- "Forgot?" link added on the sign-in form
- ⚠️ **Resend account is currently in test mode** — the API can only deliver to the verified account email (`franpietrowski@gmail.com`). To send to other recipients, verify a domain at resend.com/domains and update `SENDER_EMAIL` in `/app/backend/.env` to use that domain (e.g. `noreply@yourdomain.com`). The integration itself is fully working.

**CORS hardening complete**
- Empty `FRONTEND_URL` → regex-only mode → preflight echoes specific origin + `credentials: true`
- Verified: `https://abc.preview.emergentagent.com` → echoed; `https://evil.com` → blocked

### Testing
- Backend: 80/81 pytest (98.8%) → /app/test_reports/iteration_5.json. Includes 5 new Folio tests + 5 new Session Recap tests with real Claude calls.
- The single residual failure was the same CORS test, which is now resolved (verified by curl post-fix).

## 3. Backlog

### P0 — pending user
- User verifies a Resend domain to enable arbitrary recipient emails (or stays on test mode)
- Walk through the V2 flow: Codex → drop a few articles → switch to Graph → run a session → generate a recap

### P1 — V2 polish
- Map view with pinnable locations
- Timeline auto-renderer for `event` nodes
- Family-tree / diplomatic-web specialised graph layouts
- "What happened last time" auto-prepended to next session's chat
- Recap export to PDF / handout

### P2 — V3
- Battlemap + token system
- **Camera/mic Discord-like AV seats** (your original ask)
- Mobile-first responsive pass

## 4. Credits

- BESM 4E — Mark MacKinnon, Dyskami Publishing (2020)
- BESM Extras (Rule Expansions & Character Options) — Dyskami v1.1.2
- BESM Character Folio — Dyskami v1.01
- Campaign Atelier framework — Guy Sclanders, *How to be a Great GM* (2018)
- World Codex inspiration — World Anvil's article-typed worldbuilding pattern

## 5. Next Tasks

1. User verifies Resend domain (or stays in test mode)
2. Pick V3 direction: AV seats · Battlemap · Mobile pass
3. Optional polish: PATCH-style campaign edit; PDF export of recaps and handouts; seasonal/multi-arc Atelier
