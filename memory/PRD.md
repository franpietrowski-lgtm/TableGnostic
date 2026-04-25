# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A BESM 4E-aware tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT auth + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling over the existing session WS + Permissions-Policy header for camera/mic
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC (RTCPeerConnection); dark cosmic/gold aesthetic; iframe-aware AV
- **Roles:** `player` (seat-only), `gm` (can host campaigns), `admin` (everything). Legacy `user` accounts auto-migrate to `gm` on startup. Role chosen at registration.
- **Responsive:** mobile-first breakpoints (<768px) with bottom-nav + drawer pattern; desktop ≥768px keeps sidebar + multi-column

## 2. Implemented (cumulative)

### V1.0–V3.0
Auth · BESM 4E reference (86 attrs / 36 defects / 23 limiters / 21 Extras) · Campaigns · Character Forge · Live Sessions (WebSocket) · Knowledge Web · Atelier wizard · Player Primer + allow/prohibit lists · Invite links · Resend email · World Codex (8 article types) · Knowledge Graph canvas (force-directed SVG) · Character Folio · Session Recap generator · Auto-pinned recaps · Mobile/desktop responsive UI · BESM term click-to-reference popovers · **Mesh WebRTC AV seats (audio + video, mobile-first, presence-aware tiles)**.

### V3.1 — P0 unblock batch (this iteration — 2026-04-25)

**Role separation (player vs gm vs admin)**
- Registration UI surfaces a role picker (Take a seat / Run the table); default = player
- Players cannot create campaigns (HTTP 403 with helpful upgrade message); the "Forge a campaign" CTA on /app/campaigns is rendered disabled with "GMs only" label for player-role users
- `seed_user` is now authoritative on each boot — keeps demo gm@/player@/admin@ roles in sync
- Role-gate is allowlist-based: `if user.role not in ('gm','admin'): 403` (defense-in-depth)

**Start Session (no more browser prompt)**
- Replaced `window.prompt()` with a styled `<StartSessionModal>` (Escape-to-close, default title `Session N+1`, helper hint about seat-prereq)
- Both top-bar and Sessions tab use the same modal

**AV permission UX**
- `Permissions-Policy: camera=(self), microphone=(self), display-capture=(self)` middleware on every response
- Frontend detects iframe embedding (`window.self !== window.top`) and shows an "Open in new tab" banner above the AV strip when the user is inside the preview frame
- `getUserMedia` errors now distinguish iframe-block vs OS-deny vs no-device vs in-use

**Per-node visibility (role-based)**
- Backend already supported `gm_only / shared / revealed (+ revealed_to: List[user_id])` and the GET `/campaigns/{cid}/nodes` filter — surfaced as a 3-option selector in the GM `<NodeEditor>` with a member-toggle picker for the `revealed` case
- Player-side Knowledge Web only shows nodes they're authorised on

**GM Primer caps**
- New campaign fields: `character_point_min`, `character_point_max`, `max_per_attribute_rank` (each 0 = inherit Power Level default)
- Character Builder shows live "Spent X / Y (GM cap, Heroic)" with a `gm-cap-note` indicator when the override is active, "Below GM floor — spend N more" when under min, and per-Attribute over-cap warnings
- `save()` clamps any over-cap Attribute Level to the GM cap on submit

**Reference cards: legal mechanic-only blurbs**
- Wrote ORIGINAL mechanic-only blurbs (no rulebook prose / lore / examples) for: 21 named Attributes, all 3 Defect categories (Lesser/Greater/Serious), generic Enhancement & Limiter explanations, 10 Extras Rules, all 5 Power Levels, plus a `generic_blurbs` set ("How costing works", "Items vs Mundane", "Weapon vs Gear vs Item")
- Reference page renders the blurb under each card; CharacterBuilder picker also shows the blurb on hover/expand
- All cards keep the page-ref + book-source citation per Tri-Stat compliance

**Tri-Stat Emporium credit**
- Footer credit on every BESM-system campaign with the © Mark MacKinnon / Dyskami line + the standing "references rules — does not reproduce them" disclaimer

### V3.1 — Tested
- Backend: 106/108 pytest stable (98.1%); 21/21 new tests pass across 5 new classes (TestIter7Roles · PrimerCaps · BesmBlurbs · NodeVisibility · PermissionsPolicy)
- Frontend Playwright: every named testid found and exercised (auth-role-picker, new-campaign-btn disabled, tri-stat-credit, start-session-modal, primer-caps, node-visibility 3-way + reveal-picker, ref-blurb cards + ref-generic-blurbs)
- 2 carry-over failures (CORS empty-FRONTEND_URL, LLM 429) pre-date V3.1; documented in iters 3-7

## 3. Backlog

### P1 — Next major builds
- **Game-system selector** + 10 popular systems as data scaffold (D&D 5E, Pathfinder 2e, Call of Cthulhu, Savage Worlds, FATE Core, Cyberpunk RED, Vampire 5e, Blades in the Dark, Mothership, Shadowrun 6e). UI flow stays system-agnostic; mechanics stay BESM-only until system-specific data is added.
- **Discord-style channels & threads (PBP)** per campaign — #general / #ic / #ooc / custom; threading; live unread; mentions; via existing WS bus. **DEFERRED — needs its own dedicated session.**
- **Initiative-driven AV layout + spotlight** — GM grid orders tiles by initiative; chat slides under the active player's tile; the active player's view swaps from grid to a character-sheet+roll-options popup
- **Auto-generated roll-options list** from BESM mechanics + GM Primer (everything-not-explicitly-prohibited)
- **Player → GM live "Primer change request"** popup alerts; GM Primer live-edit mid-campaign

### P1 — V3 candidates
- **Battlemap + tokens** (canvas with grid, fog-of-war, drag tokens, line-of-sight)
- **Backend refactor** — `server.py` (now ~1545 lines) → `/app/backend/routes/{auth,campaigns,characters,sessions,ws,besm}.py`

### P2 — AV hardening
- Per-connection rate limit on the WS relay loop (50 msgs/sec)
- Pydantic validation for `presence:av-state` + `webrtc:*` payloads
- WS reconnect with exponential backoff + presence:room re-sync on kube-ingress idle drops
- TURN credentials for symmetric-NAT users

### P2 — Polish
- Cache `/api/besm/reference` (functools.lru_cache) — fully static payload
- Per-attribute level `<input max>` reflecting `max_per_attribute_rank` for immediate browser-level enforcement
- Extend `<BesmTerm>` to Skills, Enhancements, Limiters, and the Atelier
- Map view with location pins; timeline auto-renderer for `event` nodes; family-tree graph layouts
- Recap export to PDF / handout
- Verify a Resend domain so password-reset emails can go to arbitrary recipients
- WS presence test stabiliser (raise `_drain_until` budget to 8s + 1-shot retry decorator)

### P2 — Carry-overs (pre-V3.1)
- CORS preflight wildcard fix when FRONTEND_URL is empty (pass `allow_origins=[]` so regex applies)
- 502 sanitisation in generate_recap; per-(session,user) cooldown so LLM 429 stops bubbling

## 4. Credits

- BESM 4E (Mark MacKinnon, Dyskami Publishing, 2020) — referenced, not reproduced
- BESM Extras / Character Folio (Dyskami)
- Campaign Atelier framework (Guy Sclanders, *How to be a Great GM*, 2018)
- World Codex inspiration (World Anvil article-typed worldbuilding pattern)

## 5. Next Tasks

1. **Game-system selector + 10 systems scaffold** OR **Discord-style channels & threads** — user's pick for next batch
2. **Initiative-driven AV layout + spotlight** + auto-generated roll-options list (large UX build)
3. **Battlemap + tokens** (V3 major) — recommend after the backend split
4. **Backend refactor** — split `server.py` into routers
