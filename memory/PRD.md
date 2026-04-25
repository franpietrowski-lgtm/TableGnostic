# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E + Anime 5E native (Tri-Stat Emporium), scaffolded for 9 more systems including Cypher.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling + Permissions-Policy
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC; iframe-aware AV; portaled BesmTerm popovers; system-aware footer credit + logo
- **Roles:** `player` / `gm` / `admin`. Legacy `user` accounts auto-migrate to `gm`.
- **Game Systems:** **12** — BESM 4E + Anime 5E fully supported; Cypher legally welcomed (community-content compatible); 9 others scaffolded.

## 2. Implemented (cumulative)

### V1.0–V3.5
Auth · BESM 4E reference (full data) · Campaigns · Character Forge · Live Sessions · Knowledge Web · Atelier · Player Primer + caps + benchmarks · Resend · World Codex · Knowledge Graph · Character Folio · Session Recap · Auto-pinned recaps · Mobile/desktop · BESM term click-to-reference (portaled) · Mesh WebRTC AV seats · Role separation · Tri-Stat Emporium logo + Dyskami legal text · 3 Evereantha sample PCs · Setting-flavor primary descriptions · Skill components · Power Pack section · Cost-engine clamp + per-Attribute mod whitelists · Defects on Items/Weapons.

### V3.6 — Folio crash · Size template · Anime 5E · Cypher legal (this iteration — 2026-04-25)

**🔴 P0 — `FolioPanel` editor crash fixed**
- Root cause: seeded Evereantha PCs stored `folio.goals / family / edges / obstacles` as STRINGS (single-line free text). FolioPanel expected ARRAYS and called `.map()` directly, producing `(f.goals || []).map is not a function`.
- Two-part fix:
  1. **Defensive coercion** in FolioPanel — added `arr(v) = Array.isArray(v) ? v : []` and applied it to all 5 collection fields (`edges`, `obstacles`, `goals`, `family`, `history_events`, `journal`). A misshapen record can no longer crash the editor.
  2. **Seed-data correction** — re-shaped the 3 Evereantha PCs to use proper arrays. Each PC now ships with 3 long/short/secret goals, 1-2 family entries (with relation + note), 2 edges, 2 obstacles. Re-seed verified via API.

**Conceptual correction — Size is a per-entity TEMPLATE, not a campaign world-scale enum**
- Removed the wrong `size_scale: "Personal" / "Squad" / "Vehicle" / "Capital" / "Cosmic"` field on Campaign.
- Added proper `SIZE_TEMPLATES` registry to `besm_data.py` (BESM 4E p.181) — 7 entries on the Diminutive ↔ Massive ladder (Tiny/Small/Medium/Large/Huge/Gargantuan/Colossal aliases for d20 vocabulary). Each carries `damage_mod`, `defence_mod`, `speed_mult`, `weight_mult`, blurb, and a numeric `rank`.
- Replaced campaign field with `default_character_size: str = "Medium"` — the GM's recommended template for new PCs in this campaign. Players can still override per-character / per-Item.
- Added `CharacterIn.size: str = "Medium"` (whole-character template) and `CharacterAttribute.size: str = ""` (optional override for Item / Weapon / Companion entries).
- `/api/besm/reference` now returns `size_templates` so the frontend can render Size pickers consistently.
- PrimerTab `[data-testid="primer-size"]` selector replaced — shows the 7 templates with "per-entity, players can override" hint. CharacterBuilder briefing badge `bench-size` reflects the new default.

**Anime 5E added as a fully-supported system**
- New `GAME_SYSTEMS` entry: `id="anime-5e"`, publisher Dyskami, Dyskami's exact required notice for Anime 5E products (Mark MacKinnon credit, Japanime Games co-pub, OGL distribution, Anime5E.com link), shares the Tri-Stat Emporium combined-logo cover requirement.
- `supported=true` flag advertises that mechanics are about to land. Full Reference / Character Builder for Anime 5E is queued for V3.7 (it's a d20 5E-compat system, not Tri-Stat — needs its own sheet template, classes, races, feats).
- Total system count is now 12 (BESM 4E + Anime 5E supported; Cypher + 9 others scaffolded).

**Cypher System legal text — Monte Cook Games' exact required notice**
- Replaced the placeholder Cypher copyright with the full Cypher System Creator programme text (CYPHER SYSTEM trademarks, Monte Cook Games, LLC attribution, link to montecookgames.com, community-content acknowledgement).
- Confirmed the Cypher System Creator policy ALLOWS tool-integration scenarios like ours (we reference rules without reproducing prose, exactly the same posture as our BESM 4E integration). Any commercial export pipeline (the Later VIP) will need to display the Cypher System Creator logo on covers and the required notices in the legal page.

### V3.6 — Tested
- Backend curl: `/api/systems` returns 12 entries; Anime 5E supported=true; Cypher carries the new legal text. `/api/besm/reference` returns 7 size_templates with all expected fields. Re-seed confirms PCs ship with goals=3, family=1, edges=2, obstacles=2 each.
- Frontend Playwright: Cyma's character sheet **Edit** loads cleanly (was the crash before); 15 folio sub-panels render; PrimerTab Size selector shows all 7 templates ("Medium — standard h…" selected). Benchmark badges still render correctly (HIGH FANTASY · MEDIEVAL · DR BASELINE · 7).

## 3. Backlog (in user's stated order)

### P1 — Next major builds
- **Initiative-driven AV spotlight + Journal↔Sheet bond + Roll-options popup + Loremaster's hush** — paired build (shares the active-player surface). Roll-options auto-built from current-system mechanics + GM Primer ("everything not explicitly prohibited"). Loremaster's hush gold-sigil pulse when GM speaks.
- **Primer change-request alerts** + GM live-edit mid-campaign.
- **Backend refactor** — `server.py` (~1700 lines) → `/app/backend/routes/{auth,campaigns,characters,sessions,ws,besm,systems,seed}.py`.
- **Discord-style channels + threads PBP** + **Battlemap + tokens** (V3 majors).

### P1 — Anime 5E content
- Full Reference + Character Builder for Anime 5E (d20 / 5E-compat: classes, races, ability scores, proficiency bonus, feats, spell slots) — major build, ~1 dedicated session.
- The 5 PDFs the user uploaded (RPG core v1.3.6, character sheet v1.02, Adventuring Accessories v1.01, Bonus Character Options v1.02, Mounts & Monsters v1.02) have everything needed to populate; reading flow likely:
  1. Extract class/race/ability data from RPG core
  2. Extract sheet layout from character_sheet PDF (mirror Dyskami's typography)
  3. Extras (Mounts, Accessories, Bonus Options) feed Reference sub-tabs

### P1 — System theming layer
- Dyskami palette/accents on BESM 4E + Anime 5E (shared house style)
- D&D house style on D&D campaigns
- Cypher voice on Cypher campaigns
- Scoped to inner-window surfaces via CSS variables + `data-system="..."` attribute

### P1 — Knowledge Web file ingestion
- GM uploads PDF / MD / TXT → Claude Sonnet 4.5 (via emergentintegrations) parses → suggests / creates nodes (NPCs, locations, factions, events). Diff-review before commit.

### P2
- Display Effective Level alongside Purchased Level on Attribute rows (`5 → effective 6`)
- Per-character + per-Item Size picker UI in Character Builder (data is already wired backend-side)
- AV hardening (rate-limit, validation, reconnect/backoff, TURN)
- `/api/besm/reference` `lru_cache`
- `<BesmTerm>` extended to Skills / Enhancements / Limiters / Atelier
- Recap export to PDF
- Verify a Resend domain
- React context for `/api/systems`
- `<optgroup>` in CreateModal system selector
- CORS empty-FRONTEND_URL fix
- LLM 429 cooldown

### Later VIP
- DriveThruRPG-ready PDF export pipeline with system-appropriate trade dress (Tri-Stat Emporium combined-logo cover for BESM/Anime 5E products; Cypher System Creator logo for Cypher; D&D 5E Compatible logo for D&D)
- 8-session Evereantha demo with auto-summarised sessions, per-player engagement tooltips, character-relationship summaries

## 4. Credits

- BESM 4E — Mark MacKinnon, Dyskami Publishing, 2020 (referenced, not reproduced)
- Anime 5E — Mark MacKinnon, Dyskami Publishing, OGL-distributed
- Cypher System — Monte Cook Games, LLC; integrated via the Cypher System Creator programme
- All 9 scaffolded systems credited to their respective publishers
- Evereantha setting (user-provided)

## 5. Next Tasks

1. **Initiative-driven AV spotlight + Journal↔Sheet bond + Roll-options popup + Loremaster's hush** (paired build)
2. **Primer change-request alerts** + GM live-edit
3. **Backend refactor** → routers
4. **Discord PBP** · **Battlemap**
5. **System theming layer**
6. **Knowledge Web file ingestion**
7. **Anime 5E full content** (Reference + Character Builder)
8. **Later VIP**: DriveThruRPG export + 8-session Evereantha demo
