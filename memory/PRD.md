# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E native, scaffolded for 10 more systems.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT auth + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling over the existing session WS + Permissions-Policy header for camera/mic
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC (RTCPeerConnection); dark cosmic/gold aesthetic; iframe-aware AV
- **Roles:** `player` (seat-only), `gm` (can host campaigns), `admin` (everything). Legacy `user` accounts auto-migrate to `gm`. Role chosen at registration.
- **Game Systems:** 11 advertised — BESM 4E fully supported; D&D 5E / Pathfinder 2E / Call of Cthulhu 7E / Savage Worlds / FATE Core / Cyberpunk RED / Vampire 5E / Blades in the Dark / Mothership / Shadowrun 6E scaffolded (campaign-create + worldbuilding + sessions + AV work today; system-specific Reference + Character Forge content coming with each system's data fill-in).
- **Responsive:** mobile-first <768px (bottom-nav + drawer); desktop ≥768px (sidebar + multi-column)

## 2. Implemented (cumulative)

### V1.0–V3.1
Auth · BESM 4E reference (full mechanic data) · Campaigns · Character Forge · Live Sessions (WebSocket) · Knowledge Web · Atelier wizard · Player Primer + allow/prohibit lists · Invite links · Resend email · World Codex · Knowledge Graph canvas · Character Folio · Session Recap generator · Auto-pinned recaps · Mobile/desktop responsive UI · BESM term click-to-reference popovers · Mesh WebRTC AV seats · Role separation · Tri-Stat Emporium credit · GM Primer caps.

### V3.2 — BESM data fill + Game-system selector (this iteration — 2026-04-25)

**Comprehensive BESM 4E reference data**
- Original mechanic-only blurbs on **every** entry of the Reference: 86/86 Attributes, 36/36 Defects (per-name with category fallback), 23/23 Limiters (per-name), 5/5 Enhancements (per-name: Area / Duration / Range / Targets / Potent), 21/21 Extras Rules
- Blurbs describe HOW each entry slots into the cost equation `cost × Level × (1 + ΣEnh − ΣLim)` and the trigger / refund shape for Defects — 100% original wording, no rulebook prose / lore / examples
- CharacterBuilder picker now surfaces these blurbs inline so players see what each pick *does* before committing points

**Game-system selector + 10-system scaffold**
- Backend `GAME_SYSTEMS` registry with id / name / publisher / edition / year / copyright / supported / blurb for 11 systems
- New public endpoint `GET /api/systems` (cache-friendly)
- `CampaignIn.system_id` validated on POST + PUT via shared `_resolve_system_id()` helper; bad ids return 400; valid ids auto-sync the human-readable `system` label
- Campaign create modal: live system dropdown with ✓ supported / ○ scaffolded indicators + per-system blurb + "scaffolded — content coming soon" disclaimer for non-BESM
- `<SystemCredit>` subcomponent in CampaignDetail — renders the appropriate publisher footer per campaign system (BESM = Tri-Stat Emporium / Dyskami; D&D = Wizards of the Coast; etc.)
- Reference page `ref-system-note` paragraph naming all 10 scaffolded systems

### V3.2 — Tested
- Backend: 123/125 stable (98.4%); 17/17 new V3.2 tests pass across 4 new classes (TestIter8GameSystems, BesmBlurbCoverage, CampaignSystemId, PermissionsPolicyHeader); 2 carry-over failures (CORS empty-FRONTEND_URL, LLM 429) pre-date V3.2
- Frontend Playwright: 11-option `create-system` selector with ✓/○ prefixes; D&D blurb + scaffold disclaimer live-update; D&D campaign creation succeeds with publisher='Wizards of the Coast' credit; BESM keeps Dyskami credit; Defects tab = 36 unique blurbs; Limiters tab = 23 unique blurbs; Enhancements tab = 5 distinct blurbs; player CTA still 'GMs only' (V3.1 regression intact)
- One small post-test fix: extracted `_resolve_system_id()` helper + `GAME_SYSTEMS_BY_ID` O(1) lookup dict (addressed iter_8 code-review hints)

## 3. Backlog

### P1 — Next major builds (in user's order)
- **Initiative-driven AV layout + spotlight** — GM grid orders tiles by initiative; chat slides under the active player's tile; the active player swaps from grid to character-sheet + auto-generated roll-options popup. Includes "Loremaster's hush" CSS pulse when GM speaks.
- **Roll-options generator** — built from BESM mechanics + GM Primer ("everything not explicitly prohibited")
- **Player → GM live "Primer change request"** popup alerts; GM Primer live-edit mid-campaign
- **Backend refactor** — `server.py` (~1577 lines) → `/app/backend/routes/{auth,campaigns,characters,sessions,ws,besm,systems}.py`
- **Battlemap + tokens** (V3 major)
- **Discord-style channels + threads PBP** per campaign (deferred — its own focused build)

### P1 — System content fill (driven by demand)
- D&D 5E mechanics from SRD (OGL/CC content only)
- PF2e mechanics from ORC-licensed content
- FATE Core (already CC-BY)
- Other systems require licensing or stay scaffold-only

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
- `<optgroup>` in CreateModal system selector (replace ✓/○ prefixes with semantic groups for macOS/iOS native styling)

### P2 — Carry-overs (pre-V3.2)
- CORS preflight wildcard fix when FRONTEND_URL is empty
- 502 sanitisation in generate_recap; per-(session,user) cooldown so LLM 429 stops bubbling

## 4. Credits

- BESM 4E (Mark MacKinnon, Dyskami Publishing, 2020) — referenced, not reproduced
- BESM Extras / Character Folio (Dyskami)
- Campaign Atelier framework (Guy Sclanders, *How to be a Great GM*, 2018)
- World Codex inspiration (World Anvil article-typed worldbuilding pattern)
- All 10 scaffolded systems credited to their respective publishers in `GAME_SYSTEMS`

## 5. Next Tasks

1. **Initiative-driven AV layout + spotlight** + **roll-options generator** + **Player→GM Primer-change request alerts** (large UX build — next dedicated session)
2. **Backend refactor** of `server.py` → modular routers (recommended before Battlemap)
3. **Battlemap + tokens** (V3 major)
4. **Discord-style channels + threads PBP**
