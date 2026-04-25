# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A BESM 4E-aware tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and now live voice/video.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT auth + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling over the existing session WS
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC (RTCPeerConnection); dark cosmic/gold aesthetic
- **Responsive:** mobile-first breakpoints (<768px) with bottom-nav + drawer pattern; desktop ≥768px keeps sidebar + multi-column

## 2. Implemented (cumulative)

### V1.0–V2.1
Auth · BESM 4E reference (86 attrs / 36 defects / 23 limiters / 21 Extras) · Campaigns · Character Forge · Live Sessions (WebSocket) · Knowledge Web · Atelier wizard (Sclanders framework, credited) · Player Primer + allow/prohibit lists · Invite links · Resend email · World Codex (8 article types) · Knowledge Graph canvas (force-directed SVG) · Character Folio (Edges/Obstacles/Goals/Family/Journal) · Session Recap generator (Claude Sonnet 4.5) · Auto-pinned recaps · Mobile/desktop responsive UI · BESM term click-to-reference popovers.

### V3.0 — AV Seats (this iteration — 2026-04-25)

**Camera/Mic Discord-like seats around the live session**
- Backend `Bus` rewritten from `List[WebSocket]` → `List[Peer]` (uid + name + opaque conn_id) — see `server.py` lines ~1350-1495
- WebSocket relay extended with `presence:room` (initial seed for joiner), `presence:join`, `presence:leave`, `presence:av-state` (mic/cam toggles), and targeted `webrtc:offer` / `webrtc:answer` / `webrtc:ice` (forwarded to a single peer via `to:` field, never broadcast)
- Mesh peer-to-peer architecture: every participant maintains an RTCPeerConnection per other participant, via Google STUN servers; no SFU, no TURN
- Glare avoidance: deterministic offerer rule (lexicographically smaller `conn_id` initiates the offer)
- Frontend `<AVSeats>` component (`/app/frontend/src/components/AVSeats.jsx`):
  - Sticky strip above the 3-col session grid on desktop, full-width on mobile
  - Tile per participant (self + remotes) with avatar fallback, GM crown, mic/cam status
  - Mic toggle, camera toggle, leave-call controls
  - Tap-to-enlarge tile (mobile-friendly)
  - Empty state when alone at the table
- Signaling channel: shares the existing session WebSocket via a (subscribe / send) bridge in `SessionView.jsx`, so no second connection needed
- Mobile-first: horizontal scroll strip on phones, wrap-grid on desktop
- Audio + video both supported from launch (per user spec)

### V3.0 — Tested
- Backend: 85/87 pytest (97.7%); 6/6 new TestWebSocketPresence cases pass; 5/5 prior WS regression tests still green after Bus rewrite. Two carry-over failures (CORS preflight wildcard, LLM 429) pre-date this iteration
- Frontend Playwright: AV strip renders, empty state visible, join button visible, mobile (390×844) pane tabs still switch, two-context test (GM + Player) confirms peer tile upsert on `presence:join` and removal on `presence:leave`
- Regressions verified green: chat send, dice roll, advance round, recap

## 3. Backlog

### P1 — V3+ candidates
- **Battlemap + tokens** (canvas with grid, fog-of-war, drag tokens, line-of-sight)
- **Backend refactor** of `server.py` (now 1500 lines) into modular routers (`/app/backend/routes/{auth,campaigns,characters,sessions,ws}.py`)

### P2 — AV Seats hardening
- Per-connection rate limit on the WS relay loop (50 msgs/sec) to prevent signaling-channel flooding
- Pydantic validation for `presence:av-state` and `webrtc:*` payloads (currently pass-through)
- Frontend WS reconnect with exponential backoff + presence:room re-sync (kube ingress idle drops)
- Split `AVSeats.jsx` into `useMeshWebRTC()` hook + `<AVTile>` presentational component
- TURN credentials for symmetric-NAT participants (today STUN-only)

### P2 — Polish
- Extend `<BesmTerm>` to Skills, Enhancements, Limiters, and the Atelier
- Map view with location pins
- Timeline auto-renderer for `event` nodes
- Family-tree / diplomatic-web specialised graph layouts
- Recap export to PDF / handout
- Verify Resend domain to enable arbitrary recipient emails

## 4. Credits

- BESM 4E (Mark MacKinnon, Dyskami Publishing, 2020)
- BESM Extras / Character Folio (Dyskami)
- Campaign Atelier framework (Guy Sclanders, *How to be a Great GM*, 2018)
- World Codex inspiration (World Anvil article-typed worldbuilding pattern)

## 5. Next Tasks

1. **Battlemap + tokens** (next major V3 build) OR backend refactor first
2. AV seats hardening (rate-limit, validation, reconnect)
3. Verify a Resend domain (or stay test-mode)
