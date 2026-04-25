# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E + Anime 5E native (Tri-Stat Emporium), Cypher community-content compatible, scaffolded for 8 more systems.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling + Permissions-Policy
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC; iframe-aware AV; portaled BesmTerm + ActorPopover surfaces; **AV Spotlight** (initiative ordering + active-actor ring + voice-presence pulse + Loremaster's hush)
- **Roles:** `player` / `gm` / `admin`. Legacy `user` accounts auto-migrate to `gm`.
- **Game Systems:** **12** — BESM 4E + Anime 5E fully supported; Cypher legally welcomed (PDFs received, queued for content); 9 others scaffolded.

## 2. Implemented (cumulative)

### V1.0–V3.7
Auth · BESM 4E reference (full data) · Campaigns · Character Forge · Live Sessions · Knowledge Web · Atelier · Player Primer + caps + benchmarks · Resend · World Codex · Knowledge Graph · Character Folio · Session Recap · Auto-pinned recaps · Mobile/desktop · BESM term click-to-reference (portaled) · Mesh WebRTC AV seats · Role separation · Tri-Stat Emporium logo + Dyskami legal text · 3 Evereantha sample PCs · Setting-flavor primary descriptions · Skill components · Power Pack section · Cost-engine clamp + per-Attribute mod whitelists · Defects on Items/Weapons · 7-template Size system · Anime 5E + Cypher entries · Token color picker · AV initiative-driven spotlight · Voice-presence pulse · Loremaster's hush.

### V3.8 — Roll-options popup + Journal↔Sheet bond (this iteration — 2026-04-25)

**Backend — Journal endpoint**
- `JournalEntryIn` Pydantic model with `text: str(min=1, max=2000)` + optional `session_id`.
- `POST /api/characters/{cid}/journal` — appends a stamped entry (id, text, by_uid, by_name, created_at) to `folio.journal`. **Defensive coercion** for legacy data: if `folio.journal` is a string (or anything non-list), it gets reset to a fresh list starting with the new entry.
- **Access**: only the character's owner OR the campaign GM can journal as them — players who haven't seated in the campaign get 403.
- **Recap-pipeline echo**: when `session_id` belongs to the same campaign, a `[journal]`-tagged chat row (kind=`"journal"`, character_id set) is inserted into `chat_logs` AND broadcast over the session WS so the recap LLM picks it up alongside dialogue and dice.
- 404 hardening: orphan character (campaign deleted) returns 404 instead of falling through to the GM-or-owner check.

**Frontend — `<ActorPopover>` (new component, portaled)**
- Anchored to the active player's tile via `getBoundingClientRect()`; reflows on resize / scroll; clamps to viewport with 12-px margin; auto-flips above the tile if bottom-room is tight.
- Outside-click + Escape close. Manually dismissed popovers re-open automatically when initiative rotates to a new active actor (`popoverOpen` resets on `activeUid` change).
- Three stacked panes:
  1. **Derived stats row** (`actor-popover-derived`) — ATK / DEF / HP / EP / DM at a glance.
  2. **Roll Options** (`roll-options`) — system-aware suggestion list:
     - 3 Stat checks (Body / Mind / Soul · 2d6+Stat · TN 7)
     - One row per Attribute the character owns (2d6 + dominant Stat + Attribute Level · TN tuned by Attribute family — combat 7, perception 9, hard 11)
     - One row per Skill Group (2d6 + Mind + Group Level · TN 9)
     - 2 raw fallbacks (Plain 2d6 + cross-system d20)
     - **Filtered through Primer** — anything in `campaign.prohibited_attributes` / `prohibited_skill_groups` is hidden.
     - Each row testid: `roll-opt-{kind}-{i}`. Click → POST `/api/dice` with the suggested notation, label, target, and the active character's id; the existing dice WS broadcast renders the result in the session log.
  3. **Journal this turn** (`journal-this-turn`) — textarea (`journal-input`) + submit (`journal-submit`). On save: clears + flashes `Saved ✓` for 1.8s; persists to character's `folio.journal`; broadcasts the `[journal]`-tagged chat row.
- Render gate: `(isActiveSelf && popoverOpen && myCharacter && sessionId)` — only opens when *I* am the top-of-init player AND I own a character in this campaign AND the session is loaded. The GM (who doesn't own a character) sees the spotlight ring on whoever IS active but no popover for themselves — verified.

**Frontend — wiring**
- `<AVSeats>` accepts `sessionId` + `campaign` props; renders `<ActorPopover>` below the tile strip; wraps the self `<Tile>` in `selfTileRef` so the popover anchors correctly.
- `<SessionView>.loadAll()` now also fetches the campaign so it can pass through to AVSeats (powers the prohibited-list filtering).
- New `[data-testid="session-roll-log"]` wrapper on the dice-log container in `<SessionView>` — addresses iter_10 spec-alignment hint.

### V3.8 — Tested (iter_10)
- Backend: 10/10 new tests pass (`test_iter10_v38.py`): TestJournalOwnerHappyPath 3/3, TestJournalAccessControl 2/2, TestJournalValidation 4/4, TestJournalLegacyCoercion 1/1.
- Frontend: GM-negative case verified live (`actor-popover` correctly absent for GM viewing a session). All 8 ActorPopover testids present + correctly wired. Journal entries end-to-end visible — backend test entries rendered as **GAME MASTER · JOURNAL** chat rows in the session log, proving the recap-pipeline echo works.
- Active-self render path verified by source review per the iter_10 fallback note (would need a 2nd browser session + AV join + initiative manipulation for full Playwright e2e).
- Post-test cleanup: re-seeded Evereantha PCs (3 fresh) so Cyma's folio.journal is back to clean state.

## 3. Backlog (in user's stated order)

### P1 — Architecture
- **Backend refactor** — `server.py` (~1771 lines, exceeds the 700-line guideline) → `/app/backend/routes/{auth,campaigns,characters,sessions,ws,besm,systems,seed,recap,journal}.py`. Iter_10 critical-comments flagged this again.

### P1 — V3 majors
- **Discord-style channels + threads PBP** per campaign.
- **Battlemap + tokens** (canvas grid, fog-of-war, drag tokens, line-of-sight). The token color picker from V3.7 directly powers the map tokens here.

### P1 — System-aware content & theming
- **System theming layer** — Dyskami palette on BESM/Anime 5E; D&D house style on D&D; Cypher voice on Cypher. CSS variables + `data-system="..."` on the page wrapper.
- **Anime 5E full content** — Reference + Character Builder using the 5 uploaded PDFs.
- **Cypher full content** — Reference + Character Builder using the 2 uploaded PDFs (Cypher System Rulebook Revised + Expanded Worlds), Cypher System Creator legal posture (cite rules, never reproduce prose).
- **Knowledge Web file ingestion** — GM uploads → Claude Sonnet 4.5 → suggests / creates nodes via diff-review.

### P1 — Other
- **Primer change-request alerts** + GM live-edit mid-campaign.

### P2 — V3.8 polish (from iter_10)
- ActorPopover positive-render path: end-to-end Playwright harness (register fresh player → seat → create char → put on init top → second browser session → AV join). Currently verified by source review only.
- Unit-mount harness for `buildBesmRollOptions` (pure function — easy to isolate in a test route).
- Anime 5E + Cypher roll-builders to mirror BESM's `buildBesmRollOptions` pattern (each system gets its own builder; the popover dispatches by `campaign.system_id`).
- "What This Roll Means" tooltip above each suggestion (deferred friendly-enhancement idea — teaching surface for new players).

### P2 — Carry-overs
- Display Effective Level alongside Purchased Level on Attribute rows.
- Per-character + per-Item Size picker UI (data wired backend-side; UI pending).
- AV hardening — rate-limit, payload validation, reconnect/backoff, TURN.
- `prefers-reduced-motion` for AV pulse + hush rotation.
- `/api/besm/reference` `lru_cache`.
- Recap export to PDF.
- Verify a Resend domain.
- React context for `/api/systems`.
- `<optgroup>` in CreateModal system selector.
- CORS empty-FRONTEND_URL fix.
- LLM 429 cooldown.

### Later VIP
- DriveThruRPG-ready PDF export with system-appropriate trade dress per publisher.
- 8-session Evereantha demo with auto-summarised sessions, per-player engagement tooltips, character-relationship summaries.

## 4. Credits

- BESM 4E — Mark MacKinnon, Dyskami Publishing, 2020
- Anime 5E — Mark MacKinnon, Dyskami Publishing, OGL-distributed
- Cypher System — Monte Cook Games, LLC; integrated via the Cypher System Creator programme
- All 9 scaffolded systems credited to their respective publishers
- Evereantha setting (user-provided)

## 5. Next Tasks

1. **Backend refactor** → `/app/backend/routes/`
2. **Discord PBP** + **Battlemap + tokens** (V3 majors)
3. **System theming layer** (Dyskami / D&D / Cypher palettes)
4. **Anime 5E full content**
5. **Cypher full content**
6. **Knowledge Web file ingestion**
7. **Primer change-request alerts** + GM live-edit
8. **Later VIP**: DriveThruRPG export + 8-session Evereantha demo
