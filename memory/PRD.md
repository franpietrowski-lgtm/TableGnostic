# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A BESM 4E-aware tabletop platform unifying worldbuilding, session play, character automation, and knowledge graphs.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT auth + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph; dark cosmic/gold aesthetic
- **Responsive:** mobile-first breakpoints (<768px) with bottom-nav + drawer pattern; desktop ≥768px keeps sidebar + multi-column

## 2. Implemented (cumulative)

### V1.0–V2.0
Auth · BESM 4E reference (86 attrs / 36 defects / 23 limiters / 21 Extras) · Campaigns · Character Forge · Live Sessions (WebSocket) · Knowledge Web · Atelier wizard (Sclanders framework, credited) · Player Primer + allow/prohibit lists · Invite links · Resend email · World Codex (8 article types) · Knowledge Graph canvas (force-directed SVG) · Character Folio (Edges/Obstacles/Goals/Family/Journal) · Session Recap generator (Claude Sonnet 4.5).

### V2.1 (this iteration — 2026-04-25)

**"What happened last time…" auto-pin**
- When a GM creates a new session in a campaign that already has a recap on file, the most recent recap is auto-posted as the first chat message and rendered with a sticky, gold-bordered "Pinned · Last time at the table" treatment that floats at the top of the chat pane

**Mobile/desktop responsive UI (separate designs)**
- **Shell**: sidebar persists on desktop; on mobile it collapses to a sticky topbar (logo + hamburger drawer) plus a fixed bottom-nav with icon+label tabs (Dashboard / Campaigns / Discover / Reference)
- **SessionView**: 3-column desktop layout (Initiative · Chat · Dice) → 3-tab mobile layout with a sticky pane switcher; each pane gets full screen on phone
- All forms, cards, and grids already used responsive Tailwind classes; verified at 390×844 (iPhone 14) and 1600×900 (desktop)

**BESM term click-to-reference (smooth physical→digital handoff)**
- New `<BesmTerm>` popover component on the Character Sheet — click any Attribute or Defect name to see its cost, category, page, and source book; explicitly says "Table-Gnostic references rules — it does not reproduce them" so the player knows where to flip in their physical book
- Wired into Attributes and Defects on the Character Sheet; trivial to extend to Skills, Enhancements, Limiters

**System rules adherence**
- Source citations everywhere ("p.94 BESM 4E", "p.14 BESM Extras") on every Attribute/Defect/Skill row in the builder, sheet, picker, and Reference tome
- Custom GM-authored rules (Atelier custom_attributes / custom_defects) carry their own page_ref string and surface alongside official rules with a "Custom (GM)" group label
- BESM Extras (Shock Value, Sanity Points, Power Packs, Mass Combat, etc.) integrated as a separate tab in the Reference tome with `BESM Extras` source label
- Player Primer + allow/prohibit lists ensure each table only sees what their GM has approved

### Testing
- Backend: 80/81 (98.8%); CORS issue resolved post-fix.
- Mobile + desktop screenshots verified end-to-end.

## 3. Backlog

### P1 — V3 candidates (next major iterations, large)
- **Camera/mic Discord-like AV seats** (WebRTC) — voice/video tiles around the live session
- **Battlemap + tokens** (canvas with grid, fog-of-war, drag tokens, line-of-sight)

### P2 — Polish
- Extend `<BesmTerm>` to Skills, Enhancements, Limiters, and the Atelier
- Map view with location pins
- Timeline auto-renderer for `event` nodes
- Family-tree / diplomatic-web specialised graph layouts
- Recap export to PDF / handout
- Mobile pass on Atelier (already responsive via Tailwind, but specific test on phone needed)
- Verify Resend domain to enable arbitrary recipient emails

## 4. Credits

- BESM 4E (Mark MacKinnon, Dyskami Publishing, 2020)
- BESM Extras / Character Folio (Dyskami)
- Campaign Atelier framework (Guy Sclanders, *How to be a Great GM*, 2018)
- World Codex inspiration (World Anvil article-typed worldbuilding pattern)

## 5. Next Tasks

1. User decides between **AV seats** vs **Battlemap** as the next V3 build (each is a major project)
2. Verify a Resend domain (or stay test-mode)
3. Optional polish: extend `<BesmTerm>` everywhere; add map/timeline/family-tree views
