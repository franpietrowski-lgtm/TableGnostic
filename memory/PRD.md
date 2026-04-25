# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E native, scaffolded for 10 more systems.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT auth + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling over the existing session WS + Permissions-Policy header for camera/mic
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC; iframe-aware AV; system-aware footer credit + logo
- **Roles:** `player` / `gm` / `admin`. Legacy `user` accounts auto-migrate to `gm`. Role chosen at registration.
- **Game Systems:** 11 advertised — BESM 4E fully supported (full mechanic data); 10 scaffolded.

## 2. Implemented (cumulative)

### V1.0–V3.2
Auth · BESM 4E reference (full data) · Campaigns · Character Forge · Live Sessions · Knowledge Web · Atelier wizard · Player Primer + caps · Invite links · Resend email · World Codex · Knowledge Graph · Character Folio · Session Recap generator · Auto-pinned recaps · Mobile/desktop responsive · BESM term click-to-reference · Mesh WebRTC AV seats · Role separation · GM Primer caps · Game-system selector + 10-system scaffold.

### V3.3 — Customise crash fix + Tri-Stat compliance + Evereantha samples (this iteration — 2026-04-25)

**P0 bug fix — `Customise` link runtime crash**
- Root cause: `AttributeRow` received `ref={ref}` from its parent — `ref` is a *reserved* React prop intercepted for `forwardRef`, so inside the component `ref` was `undefined`, and `ref.enhancements.map(...)` threw "Cannot read properties of undefined". Fixed by renaming the prop to `reference={ref}` everywhere.
- Verified: clicking Customise on any Attribute row now reveals all 5 Enhancements + 23 Limiters as togglable chips; toggling AREA correctly raises Attack Mastery from 1 → 2 pts (cost equation `cost × Level × (1 + Enh − Lim)`).

**Tri-Stat Emporium compliance (Dyskami's exact required text + logo)**
- Updated BESM 4E `GAME_SYSTEMS` entry with:
  - The official BESM/Tri-Stat Emporium logo URL (rendered in `SystemCredit` at h-20/h-24, aspect ratio preserved per Dyskami's requirement)
  - Dyskami's exact required notice for BESM 4th Edition products with `{YEAR}` token (filled at render time from `new Date().getFullYear()`)
  - Both required URLs (`http://www.white-wolf.com` and `http://BESM4.life`) rendered as small footer links
- `<SystemCredit>` now centers the logo, headline, full legal text, links, and the Table-Gnostic disclaimer in a vertical stack — every BESM 4E campaign now displays compliant attribution

**Three Adventurous-tier Evereantha sample PCs**
- Created `/app/backend/seed_evereantha.py` with three fully-statted PCs from the public Evereantha setting (provided by the user as "Evereantha old.pdf"):
  - **Cyma Glasswort** — Apocophea (Herbalist–Alchemist) of the Taurid Tor villages — Healing/Cognition/Heightened Senses + Vial Bandolier (Item shell), 50/80 pts
  - **Tarsis Hammergrip** — Ferralith (Metal Whisperer Monk-Smith) of Oriun's Reach — Tough/Attack Mastery/Combat Technique + Resonant war-hammer Weapon, 53/80 pts
  - **Vela Stoneglyph** — Lithomorph (Geomantic Sculptor) of Continenta Aurea — Control Environment/Armour/Tunnelling/Sixth Sense + glyph-armour, 42/80 pts
- All three reference setting-specific Apocophean, Ferralith, Lithomorph artisan classes; defects nod to the Order of the Darkening Star, Mortiscura Curses, and Aetheris Ocean dread
- New endpoint `POST /api/campaigns/{cid}/seed/evereantha` (GM-only, BESM 4E-only) — inserts the three as published characters with full Folio entries
- New GM-only "Seed Evereantha samples" button in the CharactersTab on BESM 4E campaigns (`data-testid="seed-evereantha-btn"`)

## 3. Backlog (in user's stated order)

### P1 — Next major build
- **Initiative-driven AV layout + spotlight + roll-options popup + Loremaster's hush** — active player tile enlarges, chat slides under it, the active player swaps from grid to char-sheet+roll-options popup; roll-options auto-built from current-system mechanics + GM Primer ("everything not explicitly prohibited"); GM-speak triggers gold sigil pulse on player tiles.
- **Character Journal ↔ Sheet bond** — journal lives on the sheet; journal entries feed session summaries + campaign-to-date + end-campaign story summaries. Pairs naturally with the active-player popup (the popup IS the sheet+journal surface during turns).

### P1 — Compliance / UX layering
- **BESM-themed Dyskami layout influence** within BESM 4E campaign context (palette/typography accent that nods to the Tri-Stat house style without copying trade dress). Apply the same pattern (system-themed accent on system-specific surfaces) to D&D / PF2e / Cypher / FATE when their content is loaded.
- **Player → GM live "Primer change request"** popup alerts; GM Primer live-edit mid-campaign

### P1 — Architecture
- **Backend refactor** — `server.py` (~1623 lines) → `/app/backend/routes/{auth,campaigns,characters,sessions,ws,besm,systems,seed}.py` (recommended before Battlemap)

### P2 — V3 majors
- **Discord-style channels + threads PBP** per campaign
- **Battlemap + tokens** (canvas grid, fog-of-war, drag tokens, line-of-sight)

### Later VIP — Distribution
- **DriveThruRPG-ready export** — pre-formatted, properly flowed, page-numbered, accessible PDFs ready for digital release. Layout templates that match Dyskami's Tri-Stat Emporium trade-dress requirements (BESM 4E products use the BESM/Tri-Stat Emporium combined logo on the cover; legal page carries the Dyskami-mandated text).
- **8-session demo campaign on Evereantha (BESM 4E)** with auto-summarised sessions, per-player engagement tooltips (chat / rolls / mic-cam time), full character-relationship summaries, and end-of-campaign story summary. The 3 Cyma/Tarsis/Vela PCs + a 4th-PC slot already exist as the seed.

### P2 — AV hardening
- Per-connection rate limit on the WS relay loop (50 msgs/sec)
- Pydantic validation for `presence:av-state` + `webrtc:*` payloads
- WS reconnect with exponential backoff + presence:room re-sync on kube-ingress idle drops
- TURN credentials for symmetric-NAT users

### P2 — Polish
- Cache `/api/besm/reference` (functools.lru_cache) — fully static payload
- Per-attribute `<input max>` reflecting `max_per_attribute_rank` for browser-level enforcement
- Extend `<BesmTerm>` to Skills / Enhancements / Limiters / Atelier
- Map view with location pins; timeline auto-renderer for `event` nodes; family-tree graph layouts
- Recap export to PDF / handout
- Verify a Resend domain so password-reset emails can go to arbitrary recipients
- WS presence test stabiliser
- `CampaignIn.system_id` should use `Field(default_factory=lambda: DEFAULT_SYSTEM_ID)` for drift-safety
- React context for `/api/systems` so `<SystemCredit>` doesn't refetch on every CampaignDetail mount
- `<optgroup>` in CreateModal system selector
- BESM cost engine: clamp net cost-per-level to `≥ 1` per BESM 4E rule (currently allows 0 or negative when limiters > enhancements + 1) — minor design call, currently makes heavily-limited Attributes effectively free

### P2 — Carry-overs (pre-V3.3)
- CORS preflight wildcard fix when FRONTEND_URL is empty
- 502 sanitisation in generate_recap; per-(session,user) cooldown so LLM 429 stops bubbling

## 4. Credits

- BESM 4E (Mark MacKinnon, Dyskami Publishing, 2020) — referenced, not reproduced; full Tri-Stat Emporium attribution in footer
- BESM Extras / Character Folio (Dyskami)
- Campaign Atelier framework (Guy Sclanders, *How to be a Great GM*, 2018)
- World Codex inspiration (World Anvil)
- All 10 scaffolded systems credited to their respective publishers in `GAME_SYSTEMS`
- Evereantha setting (user-provided, public)

## 5. Next Tasks

1. **Initiative-driven AV layout + spotlight + Character Journal ↔ Sheet bond** (paired build — the active-player popup IS the sheet+journal surface)
2. **Player → GM Primer change-request alerts** + GM live-edit
3. **Discord-style channels + threads PBP**
4. **Backend refactor** → routers
5. **Battlemap + tokens**
6. **Later VIP**: DriveThruRPG export pipeline + 8-session Evereantha demo
