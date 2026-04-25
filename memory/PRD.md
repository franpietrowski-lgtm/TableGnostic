# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E native, scaffolded for 10 more systems.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling + Permissions-Policy
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC; iframe-aware AV; portaled BesmTerm popovers; system-aware footer credit + logo
- **Roles:** `player` / `gm` / `admin`. Legacy `user` accounts auto-migrate to `gm`.
- **Game Systems:** 11 — BESM 4E fully supported; 10 scaffolded.

## 2. Implemented (cumulative)

### V1.0–V3.4
Auth · BESM 4E reference · Campaigns · Character Forge · Live Sessions · Knowledge Web · Atelier · Player Primer + caps · Resend · World Codex · Knowledge Graph · Character Folio · Session Recap · Auto-pinned recaps · Mobile/desktop · BESM term click-to-reference (portaled) · Mesh WebRTC AV seats · Role separation · Tri-Stat Emporium logo + Dyskami legal text · 3 Evereantha sample PCs · Setting-flavor as primary description on sheet · Skill components · Power Pack section.

### V3.5 — Cost engine + Campaign Benchmarks (this iteration — 2026-04-25)

**BESM 4E cost-engine clamp**
- `attribute_cost(a)` rewritten: `per_level = max(1, cost_per_level + (#Enh − #Lim))`, `subtotal = per_level × level`, then `max(0, subtotal − nested_defect_refund)`.
- Single source of truth — `calc_spent_points()` calls `attribute_cost()` per Attribute (no more parallel implementation).
- **Defect refund direction fix**: previous `calc_spent_points()` ADDED `defect_points` to `total_spent` (over-counted refunds). Corrected to SUBTRACT — matches BESM 4E p.154 spec. *Heads up*: existing characters' totals may shift after recalc; this is a correctness fix.
- Frontend `<CharacterBuilder>` `spent` useMemo + `derived` calculator both mirror the new clamp + nested-defect math (single calculation pattern across client and server).

**Defects on Items / Weapons (and other objectifiable Attributes)**
- New `CharacterAttribute.defects: List[CharacterDefect] = []` model field.
- New `ITEM_LIKE_ATTRS` set on the frontend (Item, Weapon, Gear, Companion, Minions, Wealth, Connected, Vehicle).
- Customise picker on those Attributes shows a **Defects on this {Attribute}** section with per-defect select + rank input + remove button. Refunds visible in the row's total cost.
- Engine math floors at 0 (an Attribute never refunds more than it costs).

**Per-Attribute Enhancement / Limiter whitelist**
- `besm_data.py`: new `ATTRIBUTE_MOD_WHITELIST` covering 30+ Attributes with rule-side restrictions (Tough → no Enh; Wealth → no Enh; Heightened Senses → only Range; Movement modes → Duration/Range only; Combat Mastery → no Enh, narrow Lim; etc.).
- New `attribute_whitelist(name)` helper; `/api/besm/reference` now returns `allowed_enhancements`, `allowed_limiters`, `open_mods` per Attribute.
- Customise picker dims/disables non-whitelisted chips with explanatory tooltip ("Not typically allowed on {Attribute} — rule advisory"). GM Primer can still override via custom mods.

**Campaign Benchmarks**
- New fields on `CampaignIn`: `genre: str`, `time_period: str`, `size_scale: str` (default "Personal"), `damage_rating_baseline: int` (default 5).
- `calc_derived(ch, campaign)` reads `damage_rating_baseline` and uses it in the Damage Multiplier formula (`dm_base + massive_damage * 5`); 3 call sites updated to pass campaign.
- New PrimerTab section **Campaign Benchmarks** with 4 inputs (Genre — datalist of 16 suggestions; Time Period — 13-option select; Size Scale — 5-option select; Damage Rating — numeric).
- Character Builder's campaign-briefing card surfaces the benchmarks as testable badges (`bench-genre`, `bench-period`, `bench-size`, `bench-dr`).
- `damage_rating_baseline=5` and `size_scale="Personal"` hide their badges (sensible default UX).

### V3.5 — Tested (iter_9)
- Backend: 13/13 new pytest cases pass (`test_iter9_v35.py`): TestWhitelist 6/6, TestCostEngineClamp 5/5, TestCampaignBenchmarks 2/2.
- Frontend Playwright: Primer benchmarks UI all 5 testids present + save→reload persistence; Builder briefing badges correct (HIGH FANTASY · MEDIEVAL · DR baseline · 7); bench-size correctly hidden for default Personal.
- Manual verification: Tough's Enhancement chips (Area/Duration/Range/Targets/Potent) all rendered disabled with cursor-not-allowed; Item's chips all active; Defects-on-Item flow adds → updates → removes correctly.
- Post-test fix: live-derived DM in unsaved builder now reads `campaign.damage_rating_baseline` instead of hard-coded 5 (cosmetic — persisted character was already correct).

## 3. Backlog (in user's stated order)

### P1 — Next major builds
- **System theming layer** — Dyskami palette/accents only on BESM 4E (and Anime 5E when OGL content lands); D&D house style on D&D campaigns; Cypher voice on Cypher; scoped to inner-window surfaces. CSS variables + `data-system="..."` attribute on the page wrapper.
- **Knowledge Web file ingestion** — GM uploads PDF / MD / TXT → Claude Sonnet 4.5 (via emergentintegrations) parses → suggests / creates nodes (NPCs, locations, factions, events). Diff-review before commit.
- **Initiative-driven AV spotlight + Journal↔Sheet bond + Roll-options popup + Loremaster's hush** — paired build (shares the active-player surface). Roll-options auto-built from current-system mechanics + GM Primer ("everything not explicitly prohibited"). Loremaster's hush gold-sigil pulse when GM speaks.
- **Player → GM live "Primer change request"** popup alerts; GM Primer live-edit mid-campaign.

### P1 — Architecture / V3 majors
- **Backend refactor** — `server.py` (~1700 lines) → `/app/backend/routes/{auth,campaigns,characters,sessions,ws,besm,systems,seed}.py`.
- **Discord-style channels + threads PBP** per campaign.
- **Battlemap + tokens** (canvas grid, fog-of-war, drag tokens, line-of-sight).

### P2 — V3.5 polish (from iter_9 hints)
- `/api/besm/reference` cached via `lru_cache` (fully static payload now ~2x larger after whitelist+blurbs).
- Stable `data-testid` on the Picker `+ Add` button (currently `add-${prefix}-btn` is dynamic).
- Per-chip `data-testid` (`attr-${idx}-enh-${name}`) so Playwright can assert disabled state.
- Move `ATTRIBUTE_MOD_WHITELIST` to a JSON file editable by non-engineers.
- Centralise the "Personal" default constant on the size-scale (currently duplicated in both backend default and frontend hide-rule).
- `bench-dr` badge: optional separate `is_overridden` flag rather than the current "≠ 5" heuristic — would let a GM pin DR=5 and still see the badge.
- AV hardening (rate-limit, validation, reconnect/backoff, TURN).

### P2 — Other carry-overs
- CORS preflight wildcard fix when `FRONTEND_URL` is empty.
- 502 sanitisation in generate_recap; per-(session, user) cooldown so LLM 429 stops bubbling.
- Per-attribute `<input max>` bound to `max_per_attribute_rank` for browser-level enforcement.
- Extend `<BesmTerm>` to Skills / Enhancements / Limiters / Atelier surfaces.
- Map view with location pins; timeline auto-renderer for `event` nodes; family-tree graph layouts.
- Recap export to PDF / handout.
- Verify a Resend domain so password-reset emails can go to arbitrary recipients.

### Later VIP
- DriveThruRPG-ready PDF export pipeline (digital-release-ready, properly flowed; system-appropriate trade dress per publisher; Tri-Stat Emporium combined-logo cover on BESM products).
- 8-session Evereantha demo with auto-summarised sessions, per-player engagement tooltips (mic/cam/chat/roll time), character-relationship summaries.

## 4. Credits

- BESM 4E (Mark MacKinnon, Dyskami Publishing, 2020) — referenced, not reproduced; full Tri-Stat Emporium attribution in footer.
- Campaign Atelier framework (Guy Sclanders, *How to be a Great GM*, 2018).
- World Codex inspiration (World Anvil).
- All 10 scaffolded systems credited to their respective publishers in `GAME_SYSTEMS`.
- Evereantha setting (user-provided).

## 5. Next Tasks

1. **System theming layer** (palette + typography accent per system, scoped to inner surfaces).
2. **Knowledge Web file ingestion** (GM uploads → Claude → suggested nodes).
3. **Initiative-driven AV spotlight + Journal↔Sheet bond + Roll-options popup + Loremaster's hush** (paired build).
4. **Primer change-request alerts** + GM live-edit.
5. **Backend refactor** → routers.
6. **Discord PBP** · **Battlemap**.
7. **Later VIP**: DriveThruRPG export + 8-session Evereantha demo.
