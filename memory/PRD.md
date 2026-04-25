# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E + Anime 5E native (Tri-Stat Emporium), Cypher community-content compatible, scaffolded for 8 more systems.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling + Permissions-Policy
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC; iframe-aware AV; portaled BesmTerm popovers; **AV Spotlight surface** (initiative ordering + active-actor ring + per-character voice-presence pulse + Loremaster's hush)
- **Roles:** `player` / `gm` / `admin`. Legacy `user` accounts auto-migrate to `gm`.
- **Game Systems:** **12** — BESM 4E + Anime 5E fully supported; Cypher legally welcomed; 9 others scaffolded.

## 2. Implemented (cumulative)

### V1.0–V3.6
Auth · BESM 4E reference (full data) · Campaigns · Character Forge · Live Sessions · Knowledge Web · Atelier · Player Primer + caps + benchmarks · Resend · World Codex · Knowledge Graph · Character Folio · Session Recap · Auto-pinned recaps · Mobile/desktop · BESM term click-to-reference (portaled) · Mesh WebRTC AV seats · Role separation · Tri-Stat Emporium logo + Dyskami legal text · 3 Evereantha sample PCs · Setting-flavor primary descriptions · Skill components · Power Pack section · Cost-engine clamp + per-Attribute mod whitelists · Defects on Items/Weapons · 7-template Size system · Anime 5E + Cypher entries.

### V3.7 — AV Spotlight visual layer (this iteration — 2026-04-25)

**Token Color Picker — character signature colours**
- New `CharacterIn.token_color: str = ""` (stored as `#RRGGBB`).
- New `<TokenColorPicker>` component in CharacterBuilder with 8 curated jewel-tone presets (Gold / Apothecary / Forge ember / Slate / Amaranth / Tide / Garnet / Iris) + native `<input type="color">` for custom hex + clear-to-default button. Selection feedback: parchment border, +10% scale, glow shadow at picked colour.
- Picker testids: `token-color-picker`, `token-color-{hex}`, `token-color-custom`, `token-color-clear`.
- Sheet display: token-color appears as a glowing chip beside the character name (`data-testid="sheet-token-color"`).
- Seeded Evereantha PCs assigned thematic colours (Cyma `#5fa37a`, Tarsis `#c47a3d`, Vela `#6b7a99`).

**Initiative-driven AV tile reordering + active-player spotlight**
- `<AVSeats>` now accepts `characters` and `initiative` props (passed from `<SessionView>` which already tracks both).
- Builds a `{uid → character}` map (preferring published characters), then ranks tiles by initiative descending; ties fall back to alphabetical.
- Top-of-init player gets the spotlight: `av-tile--active` class adds 2px gold ring + 28px gold halo + 2px translateY lift; small pulsing gold dot in the top-right corner (`data-testid="av-tile-active-mark"`).
- Tile name now shows the character's name instead of the player's name (player name shown as a small grey suffix when both are known).

**Voice-presence pulse in token color**
- When a peer is in-call AND mic-on AND has a token_color, the tile renders an inline `box-shadow: 0 0 0 2px {color}88, 0 0 18px {color}66` ring.
- CSS `av-speaking-pulse` keyframe (1.6s ease-in-out infinite) modulates brightness + saturation by ±8% so the tile breathes while speaking — subtle, doesn't compete with the active-actor gold ring.
- The mic icon in the tile footer also tints to the token color while live.

**Loremaster's hush**
- `<AVSeats>` exposes `data-gm-speaking="true"|"false"` on the root and adds `av-stage--hush` class when any GM peer (or self if GM) is mic-active.
- CSS dims every non-GM tile to opacity 0.55 + saturation 0.7; the GM tile is left undimmed and gets the gold spotlight ring; an `av-tile__hush-sigil` overlay rotates a layered conic-gradient gold sigil across the tile borders (`av-hush-rotate` 6s linear infinite).
- Effect is gentle by design — players can still see who's at the table; the focus comes from contrast + the rotating sigil.

**Backend support**
- Seed flow updated to include `token_color` and `size`.
- `CharacterAttribute.size: str = ""` already in place from V3.6 (per-Item override) — no schema change needed for V3.7.

### V3.7 — Verified
- Visual Playwright run: Token picker shows 8 preset swatches + custom + clear; selecting Amaranth highlights it with parchment ring + scale + glow. Sheet header chip renders Cyma's apothecary-green dot beside her name. AV strip shows `data-gm-speaking="false"` initially. Re-seed confirms all 3 Evereantha PCs persist `token_color` + `size` correctly.

## 3. Backlog (in user's stated order)

### P1 — Roll-options popup + Journal↔Sheet bond (next batch)
- **Roll-options popup** — system-aware roll-options auto-built from the campaign's mechanics + GM Primer (everything-not-explicitly-prohibited). On the active player's surface during their turn. BESM 4E layer first (2d6 vs TN with stat/attribute/skill modifiers); Anime 5E + Cypher when their content lands.
- **Journal ↔ Sheet bond** — the Character Folio journal becomes the source-of-truth for per-turn entries on the active-player surface. Entries feed session / campaign-to-date / end-campaign summaries via the existing recap LLM pipeline.

### P1 — Other major builds
- **Primer change-request alerts** + GM live-edit mid-campaign.
- **Backend refactor** — `server.py` (~1715 lines) → `/app/backend/routes/{auth,campaigns,characters,sessions,ws,besm,systems,seed}.py`.
- **Discord-style channels + threads PBP** + **Battlemap + tokens** (V3 majors).
- **System theming layer** — CSS variables + `data-system="..."` (Dyskami palette on BESM/Anime 5E; D&D house style on D&D; Cypher voice on Cypher).
- **Anime 5E full content** — Reference + Character Builder using the 5 uploaded PDFs.
- **Cypher full content** — using the 2 uploaded PDFs (Cypher System Rulebook Revised + Expanded Worlds), with the Cypher System Creator legal posture (cite rules, never reproduce prose).
- **Knowledge Web file ingestion** — GM uploads → Claude Sonnet 4.5 → suggests / creates nodes via diff-review.

### P2
- Display Effective Level alongside Purchased Level on Attribute rows.
- Per-character + per-Item Size picker UI in Character Builder (data is wired backend-side; UI is pending).
- AV hardening — rate-limit, payload validation, reconnect/backoff, TURN.
- Animate the active-player ring transition when initiative advances (hand-off feel).
- Cross-fade the Loremaster's hush sigil so toggling GM mic on/off doesn't snap.
- `prefers-reduced-motion` media query: disable the speaking pulse and hush rotation for accessibility.
- `/api/besm/reference` `lru_cache`.
- Recap export to PDF.
- Verify a Resend domain.
- React context for `/api/systems`.
- `<optgroup>` in CreateModal system selector.
- CORS empty-FRONTEND_URL fix.
- LLM 429 cooldown.

### Later VIP
- DriveThruRPG-ready PDF export pipeline with system-appropriate trade dress (Tri-Stat Emporium combined-logo cover for BESM/Anime 5E products; Cypher System Creator logo for Cypher; D&D 5E Compatible logo for D&D).
- 8-session Evereantha demo with auto-summarised sessions, per-player engagement tooltips, character-relationship summaries.

## 4. Credits

- BESM 4E — Mark MacKinnon, Dyskami Publishing, 2020 (referenced, not reproduced)
- Anime 5E — Mark MacKinnon, Dyskami Publishing, OGL-distributed
- Cypher System — Monte Cook Games, LLC; integrated via the Cypher System Creator programme (Cypher System Rulebook Revised + Expanded Worlds PDFs received from user, queued for content build)
- All 9 scaffolded systems credited to their respective publishers
- Evereantha setting (user-provided)

## 5. Next Tasks

1. **Roll-options popup + Journal↔Sheet bond** (paired build — both surface on the active player's tile during their turn)
2. **Primer change-request alerts** + GM live-edit
3. **Backend refactor** → routers
4. **Discord PBP** · **Battlemap**
5. **System theming layer**
6. **Anime 5E full content** (Reference + Character Builder)
7. **Cypher full content** (Reference + Character Builder)
8. **Knowledge Web file ingestion**
9. **Later VIP**: DriveThruRPG export + 8-session Evereantha demo
