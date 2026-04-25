# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E native, scaffolded for 10 more systems.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling + Permissions-Policy header
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC; iframe-aware AV; **portaled BesmTerm popovers**; system-aware footer credit + logo
- **Roles:** `player` / `gm` / `admin`. Legacy `user` accounts auto-migrate to `gm`.
- **Game Systems:** 11 — BESM 4E fully supported; 10 scaffolded.

## 2. Implemented (cumulative)

### V1.0–V3.3
Auth · BESM 4E reference (full mechanic data) · Campaigns · Character Forge · Live Sessions · Knowledge Web · Atelier · Player Primer + caps · Invite links · Resend · World Codex · Knowledge Graph · Character Folio · Session Recap · Auto-pinned recaps · Mobile/desktop responsive · BESM term click-to-reference · Mesh WebRTC AV seats · Role separation · Game-system selector + 10-system scaffold · Tri-Stat Emporium logo + Dyskami legal text · 3 Evereantha sample PCs.

### V3.4 — Tooltip portal + Sheet flavor + Skill components + Power Packs (this iteration — 2026-04-25)

**Tooltip z-index bug fixed (P0)**
- Root cause: BesmTerm used `position: absolute` inside cards with their own stacking context (`z-index`, `transform`, `overflow:hidden`), causing the popover to be clipped or rendered behind sibling cards.
- Fix: rewrote `<BesmTerm>` to render its popover via `createPortal(document.body)` with `position: fixed` viewport-relative coordinates calculated from `getBoundingClientRect()`. Reflows on scroll/resize. Auto-flips above the trigger when bottom-room is tight. `data-testid="besm-term-popover"` for testing.

**Setting-flavor as primary description on character sheet**
- Surfaces each Attribute / Defect / Skill's `note` field (the in-setting flavor) as an italic primary description directly under the term name on the Character Sheet — e.g. **"Cryptosha · Serenitas calmative tincture, distilled in glass and warmed before pour"** under Healing, instead of the generic mechanic blurb.
- Generic blurbs remain available behind the click-to-reveal BesmTerm popover for players who want the rules-side reminder.

**Skill Groups properly populated (and moved off Attributes)**
- Removed the misplaced `Skill Group` Attribute entries from all 3 Evereantha PCs. They now live in the dedicated `skills` array with `components` breakdowns, so a player sees exactly what the group does at the table.
- Added `CharacterSkillComponent` Pydantic model (`name`, `level`, `note`) and `components: List[CharacterSkillComponent]` on `CharacterSkill`.
- Character Sheet now renders the component list as a 2-column responsive grid under the Skill Group header, each component with its own setting-flavored note.
- Example — Cyma's **Apocophea Kit (Lesser, ×2)**:
  - Survivalist ×1 — Foraging, weather-reading, camp-craft.
  - Apocophea Training ×1 — Autobag handling, staff-and-vial discipline.
  - Flora Library ×1 — Recall and identify a region's flora and toxins.
  - Encumbrance ×1 — GM-approved · carry the bandolier full without penalty.

**Power Pack / Source-of-Power section**
- New `CharacterPowerPack` Pydantic model with `name`, `description`, `references[]` (label-list pointing at Attributes / Defects / Skills already on the sheet), `cost` (defaults to 0 = free narrative grouping; GM may set positive).
- New `power_packs: List[CharacterPowerPack]` on `CharacterIn`.
- Character Sheet renders a dedicated Power Pack card per entry — each with name, optional cost or "Narrative · no cost" tag, italic description, reference tag-chips, and the BESM Extras citation.
- All 3 Evereantha PCs now ship with one Power Pack each:
  - Cyma — **Cryptosha · Serenitas** (refs: Healing, Cognition, Vial Bandolier)
  - Tarsis — **The Ferralith Circle** (refs: Resonant war-hammer, Combat Discipline, Connected)
  - Vela — **Aurae · Confluo · Vallum** (refs: Control Environment, Armour, Tunnelling)

### V3.4 — Verified
- Visual Playwright run confirms: `attr-note-0` carries the setting flavor; `skill-components-0` lists 4 named sub-skills with notes; `power-packs` + `power-pack-0` testids present; `besm-term-popover` opens at fixed coordinates (686, 316) — z-index 1000 — on top of every sibling card, no clipping.
- Adventurous-tier point spend per PC after restructure: Cyma 50/80 (attrs 25 + skills 4 + stats 17 − defects 4 = 42 net spending headroom), Tarsis 56/80, Vela 41/80. Headroom intentional — leaves room for advancement.

## 3. Backlog (in user's stated order)

### P1 — Cost engine + benchmarks (next batch)
- **Cost engine clamp** — net cost-per-Level must be ≥ 1 (BESM 4E rule); current engine allows 0 / negative when Limiters > Enhancements + 1. Affects Vela's Tunnelling and any heavily-limited build.
- **Per-Attribute Enhancement / Limiter whitelists** — BESM core lists which mods may apply to which Attributes; enforce in builder picker.
- **Defects on Items / Weapons** — extend the model to allow Item / Weapon entries to carry their own Defect lists with refunds applied to the parent Attribute's cost.
- **Genre / Time-Period / Size / Damage-Rating benchmarks** at campaign level → flow into Character Builder caps + Map tokens + Reference filtering. Stored on Campaign Primer.
- **System theming** — Dyskami palette/accents only on BESM 4E (and Anime 5E when added per OGL); D&D house style on D&D campaigns; Cypher voice on Cypher campaigns; etc. Applied to inner-window surfaces only.

### P1 — Knowledge Web file ingestion
- GM uploads PDF / MD / TXT → Claude Sonnet 4.5 (via emergentintegrations) parses → suggests / creates nodes (NPCs, locations, factions, events). Diff-review before commit. P0 path: parse → propose; P1: auto-link nodes.

### P1 — Initiative-driven AV spotlight + Journal↔Sheet bond + Roll-options popup
- Active player tile enlarges; chat slides under it; the active player's surface swaps to char-sheet + auto-generated roll-options popup; roll-options built from current-system mechanics + GM Primer ("everything not explicitly prohibited"). Loremaster's hush gold-sigil pulse when GM speaks. Character Journal lives on the sheet; journal entries feed session/campaign/end-campaign summaries.

### P1 — Other
- Player → GM live "Primer change request" popup alerts; GM Primer live-edit mid-campaign.
- Backend refactor — `server.py` (~1635 lines) → `/app/backend/routes/`.

### P2
- Discord-style channels + threads PBP per campaign.
- Battlemap + tokens (canvas grid, fog-of-war, drag tokens, line-of-sight).
- AV hardening (rate-limit, payload validation, reconnect/backoff, TURN).
- `/api/besm/reference` `lru_cache`.
- Per-attribute `<input max>` bound to `max_per_attribute_rank`.
- React context for `/api/systems` so SystemCredit doesn't refetch.
- `<optgroup>` in CreateModal system selector.

### Later VIP
- DriveThruRPG-ready PDF export pipeline (digital-release-ready, properly flowed; system-appropriate trade dress per publisher).
- 8-session Evereantha demo with auto-summarised sessions, per-player engagement tooltips (mic/cam/chat/roll time), character-relationship summaries.

## 4. Credits

- BESM 4E (Mark MacKinnon, Dyskami Publishing, 2020) — referenced, not reproduced; Tri-Stat Emporium attribution + logo on every BESM campaign
- Campaign Atelier framework (Guy Sclanders, *How to be a Great GM*, 2018)
- World Codex inspiration (World Anvil)
- All 10 scaffolded systems credited to their respective publishers in `GAME_SYSTEMS`
- Evereantha setting (user-provided)

## 5. Next Tasks

1. **Cost-engine corrections + benchmarks** (Genre / Time-Period / Size / Damage-Rating + clamp ≥1 + per-Attribute mod whitelists + Defects-on-Items)
2. **Knowledge Web file-ingestion** (GM uploads → LLM-suggested nodes)
3. **Initiative-driven AV spotlight + Journal↔Sheet bond + Roll-options popup + Loremaster's hush** (paired build)
4. **System theming** layer (palette/typography accent per system, scoped to inner surfaces)
5. **Primer change-request alerts** + GM live-edit
6. **Backend refactor** → routers
7. **Discord PBP channels** · **Battlemap**
