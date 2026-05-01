# Table-Gnostic — Product Requirements Document

> **Tagline:** "Not the system. The table."
> A multi-system tabletop platform unifying worldbuilding, session play, character automation, knowledge graphs, and live voice/video — BESM 4E + Anime 5E + Cypher + D&D 5E content-aware, 9 more systems scaffolded.

> **Note:** This PRD is the cumulative spine. Detailed iteration changelogs prior to V5.1 live in `git log` and the `/app/test_reports/iteration_*.json` artefacts.

## 1. Architecture

- **Backend:** FastAPI + MongoDB (motor) + JWT + token-authed WebSockets + Resend email + Claude Sonnet 4.5 via emergentintegrations + WebRTC mesh signaling + Permissions-Policy
- **Frontend:** React 18 + Tailwind + Radix + lucide-react + custom SVG force-graph + native WebRTC; iframe-aware AV; portaled BesmTerm + ActorPopover surfaces
- **Roles:** `player` / `gm` / `admin`. Legacy `user` accounts auto-migrate to `gm`.
- **Game Systems:** **13** — BESM 4E + Anime 5E + Cypher + D&D 5E content-aware; 9 others scaffolded.

## 2. Implemented (cumulative, condensed)

### V6.11 — User-feedback batch: modal vignette + Director session picker + worldbuilding chart V2 + character portrait + how-to guide (2026-05-01)

**Batch 1 — UX hygiene & architecture cleanup**
- **Modal vignette/blur fix** — DeltaDropPanel, SpellConversionAtlas, PowerBundleTemplatePicker, ChannelsPanel thread-drawer all migrated from `bg-black/80` (no blur) → `bg-void/90 backdrop-blur-md` for proper page isolation. Fixes content bleed-through reported by user.
- **Director's Console: phase → session picker** — Replaced "Live Atelier phase" hardcoded enum dropdown with `director-session-picker` listing sessions in their GM-defined timeline order. Added `Session.sequence_index` field + `PUT /api/campaigns/{cid}/sessions/reorder` to support backstory / prologue / time-shenanigans sessions whose timeline position diverges from play date.
- **Atelier ↔ Genesis redundancy** — Removed top-bar "Atelier" button from CampaignDetail header (was duplicate of Atelier tab + Genesis sub-tab). Genesis flow truncated from 9 phases → 7 phases (Phase 8 Epic + Phase 9 Reference Library now live ONLY as their dedicated Atelier sub-tabs).
- **Encounter Builder field labels** — every input in `NpcRow` now carries an explicit visible `label-ref` (NPC name · Role · State · Location in scene · Current intent · Count · Challenge Rating · Level (1-10) · Total CP).
- **Creatures bucket** — `_gather_npc_pool` in `routes/director.py` now separates `type=creature` codex nodes into `source="creatures"`. NpcPool UI groups them under "Codex · Creatures & Beasts" alongside the existing People bucket.

**Batch 2 — Content & feature work**
- **BESM 4E in-sheet inline level editors** — Owners and GMs can edit attribute Level, skill Level, and defect Rank directly on the character sheet via tiny inline numeric inputs. Updates PUT to `/api/characters/{id}`. Cost auto-recomputes server-side. Testing-agent caught + auto-fixed a bug where the PUT body was missing required `campaign_id`/`name`; fix spreads full character body.
- **Character portrait uploader** — New `CharacterPortrait.jsx` component on every sheet header. POST `/api/uploads/character-portrait/{cid}` (multipart, 4 MB cap, PNG/JPEG/WEBP). Persists `portrait_url` on the character document. Falls back to a stylised silhouette placeholder when no portrait set.
- **Worldbuilding Chart V2** — `CodexChartView.jsx` rewritten:
  - **World Creation Tree** — organisational chart rooted on "Creation · Beginning", branching into Population · Geography · History pillars, fanning out into declared sub-branches (`fields.pillar` + `fields.pillar_branch`). Auto-infers from node type when not explicitly set.
  - **Biome Pyramid** — content-aware 4×3 grid (Hot/Warm/Cool/Cold × Wet/Balanced/Dry) reading `fields.temperature` & `fields.humidity` on location nodes. Auto-falls-back to 11 sample biomes when no GM data exists so the chart never feels empty.
- **How-To interactive guide** — New `/app/help` route. 8 recipe cards (Author campaign · Build PC · Run encounter · Map world · Run live session · Build Timeline · Delta Drop · Export PDF), each expanding into numbered step-by-step. Sidebar nav-help link added.

**Testing — `/app/test_reports/iteration_44.json`**
- Backend: **6/6 V6.11 + 41/41 V6.6-V6.10 regression** (1 historical skip retained, 1 V6.11 skip when test character has no attributes — both seed-dependent).
- Frontend: 9/9 critical surfaces live-verified post-Evereantha-reset. Testing agent caught + auto-fixed inline-edit 422 bug.
- 1 false-negative finding (NPC field labels not detected) — labels render correctly inside `NpcRow`, but only once an NPC is added; agent scanned empty encounter.
- Stale CARRY note re `tg_user_id` localStorage gate — `grep -r "tg_user_id" /app/frontend/src/` returns ZERO matches, V6.7 fix permanently in place. PRD-removed.

**Deferred to future sprints**
- Click-and-drag session reorder UI on the Timeline panel (backend `PUT .../sessions/reorder` endpoint exists; UI handle pending).
- Character portrait in PDF export bundle (currently text-only sheet appendix).
- Public Canon Registry, Cmd-K global search, Reference Editor visual grouping (P2).


### V6.10 — Refactor Sprint + Auto-status rings + Expanded PDF export + Bulk NPC seed (2026-05-01)

**P0 — Refactor sprint (file-size hygiene, zero behavioural change)**
- `CharacterSheet.jsx` 1411 → **634 lines**. Extracted to:
  - `sheets/sheetCommon.jsx` — Stat, SimpleListCard, DiceCard, CharacterJournal, Anime5eSupplementView.
  - `sheets/DndSheetView.jsx` — D&D 5E + Anime 5E hybrid d20 view (chassis + spell slots + class features).
  - `sheets/CypherSheetView.jsx` — Cypher pools, difficulty tracker, intrusion ledger, skill trains.
- `CampaignDetail.jsx` 1670 → **804 lines**. Extracted to:
  - `campaignDetail/KnowledgeTab.jsx` — list/graph/chart views + NodeCard/Detail/Editor.
  - `campaignDetail/PrimerTab.jsx` — Primer + system-aware Forge Caps + House Rules + ListField.
- `ReferenceEditor.jsx` 971 → **607 lines**. Extracted to:
  - `referenceEditor/PowerBundleTemplatePicker.jsx` — D&D-mimic template grid.
  - `referenceEditor/SpellConversionAtlas.jsx` — read-only conversion library modal.
  - `referenceEditor/PowerBundleEditor.jsx` — bundle component composer with live CP estimator.
- All `data-testid` attributes preserved verbatim. ESLint clean across all touched files.

**P1 — Auto-status rings on character sheet**
- New `GET /api/characters/{cid}/effects` — returns active effects targeting the character (member/owner/GM/admin only).
- `CharacterStatusRings.jsx` mounted on the sheet under XP queue. Conditionally renders only when ≥1 effect active. 30s polling + manual refresh button. Mirrors the live battlemap status rings.

**P1 — Campaign export bundle expansion**
- Character appendices now render `folio.journal[]` entries inline (timestamp + author + text), per-PC.
- New "Appendix · Campaign Timeline" — V6.9 timeline markers grouped by anchoring session.
- New "Appendix · Chat Transcripts" — verbatim per-session chat logs (capped at 200 lines/session).
- Hydrated via `db.timeline_markers` + `db.chat_logs` queries in the `/api/campaigns/{cid}/export.pdf` endpoint.

**P1 — Artisan / Evereantha auto-NPC seeding**
- New `POST /api/campaigns/{cid}/npcs/auto-generate-all?threat_tier=&overwrite=` — bulk-stamps system-appropriate stat_block on every NPC/creature codex node. Idempotent (skips populated nodes unless `overwrite=true`).
- Shared `_build_stat_block()` helper extracted in `cypher_suggest_anime_cr.py` so the bulk and single-node generators stay in lockstep.
- `POST /api/admin/seed-evereantha-suite` now AUTO-RUNS the bulk generator on each freshly-seeded campaign (skipped on `skipped_existing` clones). Returns new field: `auto_generated_npc_sheets: List[{campaign_id, system_id, auto_npc_sheets: int}]`.

**Testing — `/app/test_reports/iteration_43.json`**
- Backend: **6/6 V6.10 + 38/38 regression V6.6→V6.9** (single historical skip retained). New tests at `/app/backend/tests/test_iter43_v610.py`.
- Frontend: 10/10 campaign tab-* testids driven live; 11/11 refactor-preserved sheet/reference testids verified in their new sub-module locations.
- All previously-deferred refactor items now CLOSED. CARRY note about `tg_user_id` localStorage gate is a stale historical reference — `grep -r "tg_user_id" /app/frontend/src/` returns ZERO matches; V6.7 fix to `useAuth()` is confirmed in place.

**Deferred to next sprint**
- Public Canon Registry (landing page) — let GMs publish Delta Drops for discovery.
- Cmd-K global search across campaigns / codex / characters.
- Reference Editor visual grouping (5 categories per DESIGN_AUDIT).


### V6.9 — Timeline ↔ Codex bridge + Companion seats + Token size cycler (2026-05-01)

**Timeline ↔ Codex Chart bridge (P0 #1)**
- New `routes/timeline_markers.py` — `db.timeline_markers` collection. CRUD endpoints:
  - `GET /api/campaigns/{cid}/timeline-markers` — members can read.
  - `POST /api/campaigns/{cid}/timeline-markers` — GM-only. Validates `session_id` and optional `codex_node_id` belong to the campaign (400 on mismatch). Stores `{label, kind, color, codex_node_id, session_id}`.
  - `DELETE /api/campaigns/{cid}/timeline-markers/{mid}` — GM-only.
- `CodexChartView.jsx` — Each chart-node row is now click-target on GM-owned campaigns. New `codex-chart-pin-bar` strip at the top with an active-session selector (`codex-chart-active-session`). Clicking a node POSTs a marker, fires a `tg:timeline-marker-added` window event, and shows `codex-chart-pin-feedback` toast.
- `TimelinePanel.jsx` — Loads markers alongside sessions. Each session column renders a stack of `timeline-marker-{mid}` badges below the spine; GMs see an `X` to remove. Listens for `tg:timeline-marker-added` events to refresh live without a page reload.

**Companion seats + token-move parity (P0 #2)**
- `CharacterIn.companion_owners: List[str]` — new model field.
- `routes/characters.py`:
  - `POST /api/characters/{ch_id}/companions?player_id=X` — GM/admin assigns.
  - `DELETE /api/characters/{ch_id}/companions/{player_id}` — GM/admin revokes.
- `routes/battlemap.py` — `upsert_token` now accepts ANY `companion_owners[]` user as a valid mover, in addition to the actual `owner_id`. GM still moves all tokens.
- `CompanionAssignPanel.jsx` (new GM-only widget) mounted on the character sheet under the Approval Panel. Lists campaign members, lets GM `Plus`/`X` to assign or revoke companion seats. Excludes the actual owner from the picker.

**Battlemap token-size cycler**
- Tokens already scaled with `grid.size_px`. Added a single keystroke discovery: GM can **Shift+right-click** any token to cycle its grid size (1 → 2 → 3 → 4 → 1). Helper-text strip below the canvas updated. Plain right-click still removes (V5.5 behaviour preserved).

**Testing — `/app/test_reports/iteration_42.json`**
- Backend: **7/7 V6.9 + 31/31 regression** (V6.6/6.7/6.8 still green). `/app/backend/tests/test_iter42_v69.py` + extended `test_iter42_v69_extra.py` (testing-agent-authored: real-second-user companion assign/revoke + battlemap can-move-after-assign / 403-after-revoke).
- Frontend: TimelinePanel live render verified. CodexChartView + CompanionAssignPanel testids verified by source grep + smoke screenshot.

**Deferred to next session (per user, scope)**
- Refactor sprint (4052 lines across 3 files): `CharacterSheet.jsx` (1411), `CampaignDetail.jsx` (1670), `ReferenceEditor.jsx` (971). Documented as critical hygiene — too large to attempt mid-feature-batch safely. Recommended dedicated sprint with full testing-agent regression after each split.
- Auto-status rings on character sheet driven by check outcomes (already wired live on map tokens via `/api/effects`; needs sheet-side mirror).
- Character-sheet PDF in overall campaign export bundle.
- Artisan / Evereantha auto-NPC seeding across all 4 systems.
- Public Canon Registry.


### Core (V1.0 → V4.6)
- Auth · BESM 4E full reference data · Campaign Atelier (7-phase Sclanders Master Plot Genesis) · multi-system Character Forges · Live Sessions with WebRTC mesh AV · Knowledge Web with role-gated reveal · Atelier Session-0 + Arcs + continuity · Player Primer with allow/prohibit lists · Resend email · World Codex + Genesis seed → nodes · Session Recap (Claude) + auto-pin + finalize-into-chronicle · Battlemap V2 (LoS raycast + measure ruler + token effects) · Discord-style PBP Channels V2 (real-time WS + @mention autocomplete + image attachments) · System theming layer · Card Decks (Deck of Many Things, Cypher Draw, Genre Shift, Mood) · DriveThruRPG-ready PDF chronicles with system-specific style profiles · system-aware ingestion (Claude branch per system) · XP scorecard with GM approval queue · Customisable Attribute/Skill/Defect display names · System-aware Reference Editor (Atelier) · System-aware Character Sheets · D&D 5E + Cypher dedicated builders · Anime 5E hybrid (Tri-Stat point-buy + 5E class+slot) builder · HP/Pool status rings on Character Sheet · 404-fix on `/campaigns/:id/characters/new` for non-BESM systems

### V4.3 Compliance
- Cypher System Creator licence — cover-line + trade-dress + forbidden-setting (Numenera/Strange/NTYE) PDF-export gate (HTTP 451) + verbatim required-text strings served via `/api/systems/cypher/reference`.

### V5.1 — Atelier "Epic Campaign" 8th-phase tab (2026-04-27)
**Trigger:** GMFran uploaded Guy Sclanders' follow-up book *Epic Campaigns: Digital Edition* (146 pp) and asked for a new tab inside the **"Forge the Master Plot"** Atelier page. The two planes (the existing 7-phase Genesis and the new Epic Campaign) are intentionally INDEPENDENT — usable in tandem, separately, or one-or-the-other; pure GM brainstorming kit. Implemented as `phase === 7` panel inside `CampaignGenesis.jsx`, alongside the existing seven phases. Backend: new `db.epic_campaigns` collection + `routes/epic_campaign.py` (GET/PUT/seed-codex). Frontend: new `EpicCampaignPanel.jsx` (11 sections — Plan/Constraints, Theme, Sentence, OGAS Nemesis, Villains, Expanding Goal, Milestones, Adventures, Seeds, Beginning, Climax — plus Tie-ins picker). The "Sync to Codex" action pushes the Nemesis + each Villain + each Seed into the World Codex as gm-only knowledge nodes; idempotent on re-run.

### V6.8 — Genesis/Epic Atelier split + Timeline + Cypher fuzzy + NPC save + Codex chart view (2026-04-30)

**Atelier sub-tab navigation**
- `AtelierTab.jsx` now exposes 5 sub-tabs: **Workshop** (legacy: ingestion + XP queue + Session 0 + Arcs + Continuity), **Genesis (7 Phases)** (deep-link to the standalone `/genesis` page), **Epic Campaign** (mounts `EpicCampaignPanel` directly), **Timeline** (new), **References** (mounts `ReferenceEditor`).
- Default sub-tab is `workshop` so legacy users land on the original surface.
- URL query param `?atelier={key}` deep-links to a chosen sub-tab.

**TimelinePanel — graphical session/encounter tracker**
- New `TimelinePanel.jsx` — horizontal spine with sessions ordered by `scheduled_at`/`played_at`/`created_at` as glyph nodes. Encounters (codex nodes with type `encounter`/`set-piece` + `session_id` link) cluster above their parent session.
- System-themed: BESM gold lozenge `◆`, Anime 5E magenta `●`, D&D fleur `❦`, Cypher teal `▣`. Soft glow on hover.
- Empty-state copy + GM tip line. Drag-to-reorder noted as next-sprint follow-on.

**Cypher Suggest fuzzy + free-text keywords**
- `_score_entry()` now does case-insensitive substring matching on entry name+summary, returning `matched_hints` (codex-derived) AND `matched_keywords` (user-typed).
- Endpoint accepts new `keywords` query (comma-separated) — score boost +2 per match. Response echoes `free_keywords` for UI debugging.

**NPC save-onto-node**
- `POST /api/campaigns/{cid}/npcs/{nid}/generate-sheet?save=true` now persists `stat_block` + `stat_block_threat_tier` + bumps `updated_at` on the codex node. Default `save=false` keeps the V6.7 non-mutating draft behaviour. GM-only.

**Codex Chart View (per user reference image)**
- New `CodexChartView.jsx` — two stacked surfaces:
  1. **Geography & Biome Flow**: locations grouped by `fields.biome`/`fields.climate` into vertical lanes with population callouts.
  2. **Worldbuilding Pillars**: 5-pillar grid (Population & Culture · Geography & Biome · Magic & Mystery · Technology & Crafts · History & Mythology). Auto-infers from node type if `fields.pillar` not set.
- Codex tab gained 3 view-mode buttons (List / Graph / Chart).
- Read-only; no schema changes (uses `fields[]` already supported).

**Testing — `/app/test_reports/iteration_41.json`**
- Backend: 19/19 (8 V6.8 + 11 V6.7) + 80/80 broader regression. **Zero defects.**
- Frontend: 24/24 testid + behavioural assertions pass — all 5 atelier sub-tabs, all 3 codex view modes, timeline + chart populate end-to-end.
- Two micro-fixes applied post-test: `node.updated_at` bumped on save-block; `CharacterSheet.jsx` ownership gate confirmed already on `useAuth()` (V6.7 fix re-verified).

**Deferred to next session (Sprint after — already on roadmap)**
- Token-placement system (GM-can-move-all + player-only-own + companions; auto status rings; map-scale-aware sizing).
- Refactor sprint: CharacterSheet (1411) / CampaignDetail (1656) / ReferenceEditor (971) → split-by-tab files.
- Artisan / Evereantha system-protected seed across all 4 systems (NPCs auto-sheets; name-clash protection for cross-system terms).
- Character-sheet PDF in campaign export bundle (currently character-only download).
- Public canon registry on landing page (discover + subscribe to Delta Drops).


### V6.7 — Soft party cap + BESM CR kit + NPC sheet generator + Power Bundle on sheet + Design Audit (2026-04-30)

**Soft party cap of 6 (warn, allow)**
- `/api/anime5e/encounter-budget` now returns `warnings: [...]` array; soft-cap message emits when `party_size > 6`. Existing math unchanged.
- Frontend EncounterDesigner shows ⚠ on Party label and renders `encounter-designer-warnings` block.

**BESM 4E CR / Encounter Threat-Tier kit**
- Researched and implemented from BESM 4E p.119+: PowerLevel-CP-based threat tiers — Underling (0.5×PC-CP), Equal (1.0), Boss (1.5), Demigod (2.5).
- `GET /api/besm/encounter-budget?campaign_id&party_size&difficulty` — returns `pc_cp`, `party_total_cp`, `encounter_budget`, `threat_slots[]` with `max_count` per tier, plus the same soft-cap warning behaviour. Difficulty multipliers: easy 0.7 / medium 0.85 / equal 1.0 / hard 1.25 / deadly 1.5.
- EncounterDesigner BESM mode: hides level input, shows CP budget + per-tier threat-slot rows (`besm-threat-{tier}`), 'equal' difficulty option added.
- Mounted on BESM-4E sessions in addition to Anime 5E / D&D 5E.

**NPC / Creature character-sheet auto-generator**
- `POST /api/campaigns/{cid}/npcs/{nid}/generate-sheet?threat_tier=…` — system-aware draft stat block:
  - **BESM 4E**: stats (Body/Mind/Soul above baseline 4), 2 attribute starters (Combat Mastery + Tough), 1 skill starter, total CP = pc_cp × tier_ratio.
  - **Anime 5E / D&D 5E**: AC, HP, six abilities, 2 actions; CR mapping {1/4, 2, 5, 12} for the four tiers.
  - **Cypher**: level, target_number = 3×level, health, damage, armor (+1 at level≥4).
- Returns `{node_id, stat_block, saved:false}` so the GM reviews before persisting; non-mutating.
- GM-only (HTTP 403 for non-GM/non-admin).

**Power Bundle visibility on BESM 4E + Anime 5E character sheet**
- New `character-power-bundles` section renders activatable bundles with cost / invocation / charges / EP / cooldown / source-spell-mimic line.
- New `character-forge-power-bundles` card (owner-only) with two link buttons: **+ Power Pack** and **+ Power Bundle**, deep-linked to the Atelier reference editor.
- Bug fix from V6.7 testing-agent: ownership gate previously read non-existent `localStorage.getItem('tg_user_id')` — switched to `useAuth()` context (`user.id === ch.owner_id`). Forge buttons now actually render for the owner.

**Design Audit document (`/app/memory/DESIGN_AUDIT.md`)**
- 8-section read-only analysis: top-level "two modes" re-grouping (Atelier ↔ Table) + 15 ranked QoL suggestions + dedicated-page route table + UX paper-cuts + system-personality consistency + things to kill + things to never touch.
- Highlights for executive review: Genesis ↔ Epic split, Encounter Lab as first-class Atelier section, NPC sheets auto-generation (now shipping in V6.7), per-role landing surfaces, Reference Editor visual grouping, Cmd-K global search.
- No code changes; pick-and-execute in subsequent sessions.

**Testing — `/app/test_reports/iteration_40.json`**
- Backend: **72/73 pytest pass** (11 V6.7 new + 61 regression). Single skip is a benign no-D&D-campaign scenario. All 3 new endpoints ✓.
- Frontend testing-agent caught the dead localStorage key bug — fixed in-place.
- Minor design notes from agent: BESM demigod tier silently dropped at very small party sizes (n < 1 guard). Document-only; not regressing.

**Deferred to next session (per user direction)**
- Genesis ↔ Epic split into two Atelier tabs.
- Timeline view (graphical encounter/session tracker, click-drag nodes, system-themed particles).
- Cypher Suggest substring/fuzzy hint matching.


### V6.6 — Cypher codex-aware suggest + Anime 5E CR kit + Mobile character PDF + Spell→Bundle converter (2026-04-30)

**Cypher codex-aware suggestions**
- `routes/cypher_suggest_anime_cr.py` — new module, registered on `server.py`.
- `GET /api/cypher/{cid}/suggest?kind=<axis>&limit=N` — inspects the campaign's `setting_genre` + the latest 5 motives + session `plot_phase`, weighs tone-hint keywords against Descriptor/Focus/Type candidates, returns the top N per axis with a `why` line per row. Tone hints cover Doomed/Tragic/Sacrifice, Rising/Ascending, Mystery/Investigation, Heist/Infiltration, Revolution/Uprising, War/Conflict — each boosts curated descriptor+focus sets.
- Frontend `builders/Cypher.jsx` — new **Suggest from codex** button (testid `cypher-suggest-btn`) next to the identity sentence. One click populates descriptor/type/focus from the top suggestion per axis. Genre-gated campaigns supported.

**Anime 5E / D&D 5E CR + Encounter design kit**
- Same router: `GET /api/anime5e/encounter-budget?party_level=N&party_size=N&difficulty=easy|medium|hard|deadly`.
- Returns `xp_per_pc`, `total_xp_budget`, slot-by-CR suggestions (1/2/4/6/8 monster clusters with DMG p.82 multipliers), `environmental_hazard_budget` (half medium).
- Frontend `EncounterDesigner.jsx` — new component, mounted in `SessionView.jsx` for GMs on Anime 5E / D&D 5E sessions. Controls for party level/size/difficulty, live recompute button, budget chip, slot rows, hazard chip.

**Mobile character-sheet PDF**
- `routes/character_pdf.py` — new module, registered on `server.py`.
- `GET /api/characters/{cid}/export.pdf?mode=mobile` — renders an A6 phone-portrait 1-column character sheet styled per system (BESM stats+attrs+defects; Anime 5E D&D chassis + BESM point-buy layer; D&D 5E abilities+combat+spell slots; Cypher pools+edge+cyphers). Uses the same per-system `STYLE_PROFILES` palette and font map as the campaign-level chronicle export.
- Frontend `CharacterSheet.jsx` — **Mobile PDF** button in the sheet header (testid `export-mobile-sheet-btn`) downloads the PDF via authenticated fetch → blob → `download` anchor pattern (mirrors AtelierTab's export flow).

**Spell → Power Bundle converter (bonus)**
- `GET /api/reference/spell-conversions/{slug}/as-power-bundle` — converts a read-only Spell Conversion Atlas row into a Power Bundle draft shape (name, description, invocation heuristic from spell level, charges, cost, components with enhancement/limiter rows).
- Frontend `ReferenceEditor.jsx` — Spell Conversion Atlas rows gained a **→ Power Bundle** button (GM-only, testid `spell-convert-{slug}`). Clicking auto-switches the tab to `power_bundle`, pre-populates the editor draft, and closes the atlas modal.

**Testing — `/app/test_reports/iteration_39.json`**
- Backend: **61/61 pass** (12 V6.6 new + 19 V6.4 + 15 V6.2 + 5 V6.1 + 10 V6.5).
- Frontend surfaces source-verified (all testids present). Playwright headless auth-propagation quirk noted but verified a live browser renders the landing page cleanly; login flow uses `/signin`.

**Deferred to next sprint**
- `SystemCharacterBuilders` + `CampaignDetail.jsx` split-by-tab refactor (still 1656 lines) + `ReferenceEditor.jsx` split (971 lines → 4 files).
- Artisan / Evereantha full seed across all 4 core systems (classes, skill profs, weapons, NPCs, magic items, artifacts).
- Public canon registry (discover + subscribe to campaigns publishing Delta Drops).


### V6.5 — Spell Conversion Atlas + Live Spend Preview + Per-system PDF ornaments (2026-04-30)

**Spell Conversion Atlas (62 entries, read-only reference)**
- `/app/backend/system_data/spell_conversion_library.py` — hand-authored 62-entry library mapping D&D 5E spells & class features to BESM Attribute bundles with enhancement/limiter numeric values and SRD citations. Covers:
  - 10 cantrips (every school: Evocation, Conjuration, Illusion, Transmutation, Enchantment, Necromancy-equivalents).
  - 10 1st-level spells, 8 2nd-level, 8 3rd-level, 6 4th-level, and 10 spells spanning 5th→9th.
  - 10 class features (Rage, Action Surge, Flurry of Blows, Lay On Hands, Favoured Enemy, Sneak Attack, Eldritch Blast, Wild Shape, Metamagic, Turn Undead).
- `GET /api/reference/spell-conversions?max_level=N&school=X` — filterable endpoint; returns `{entries, total, returned, schools}`.
- Frontend `SpellConversionAtlas` modal (opened via `reference-open-atlas-btn`) — school + level + text filters; each row shows the canonical spell, its BESM attribute conversion, every enhancement/limiter with numeric value tag, net CP, and source reference.

**Live Spend Preview on Power Bundle template cards**
- New `POST /api/characters/{cid}/simulate-import` — returns `{current_spent, current_cap, projected_spent, fits, headroom, summary}` for a hypothetical cost addition. Access-gated (owner/GM/member/admin).
- Frontend `PowerBundleTemplatePicker` now has a **character picker** at the top (`bundle-preview-character-select`). Selecting a PC and hovering a template card triggers `/simulate-import` with the template's cost; card shows a green "OK (N spare)" or ember "OVER by N" tag live.

**Per-system PDF ornaments**
- `pdf_export.py` `chrome()` now draws a system-keyed glyph midway along the top+bottom rule of every body page: **diamond** (BESM 4E), **petal** (Anime 5E), **fleur** (D&D 5E), **circuit** (Cypher), **rule** (default). Pure-vector (ReportLab primitives), no image assets required. Style profiles `chapter_decoration` finally drive rendering.

**Testing — `/app/test_reports/iteration_38.json`**
- Backend pytest: **49/49 pass** (10 V6.5 + 19 V6.4 + 15 V6.2 + 5 V6.1). 789KB BESM PDF renders cleanly with new ornaments.
- Frontend compile blocker (misplaced brace scoping SpellConversionAtlas inside PowerBundleTemplatePicker) caught by testing-agent and fixed in-place — all three component fns (PowerBundleTemplatePicker, SpellConversionAtlas, Row) now module-level siblings. Webpack compiles with warnings-only.

**Nits flagged for next session**
- `ReferenceEditor.jsx` now 933 lines — split SpellConversionAtlas + PowerBundleTemplatePicker + PowerBundleEditor into own files in the next SystemCharacterBuilders refactor sprint.
- PDF export endpoint is `GET /campaigns/{cid}/export.pdf` (not POST /export-pdf) — doc note.
- 2 unfixed exhaustive-deps warnings on refresh/template-load flows; low priority.


### V6.4 — Rules correctness + Power Pack/Bundle distinction + Anime 5E XP→CP + D&D-spell-mimic templates (2026-04-30)

**Models (BESM Extras ch.3 compliance)**
- `CharacterAttribute` gained `effective_level: Optional[int]` + `cost_modifier: Optional[int]`. Syntax `Flight Level 1 (4)` now round-trips cleanly.
- Enhancements / Limiters may now be `{name, value, note}` rows OR bare strings (legacy). Value range warned beyond ±12 (Absolute Power supplement allowed — user's "Silver Age Sentinels" use case).
- `CharacterDefect` gained a `value: int = 0` override for explicit CP refund (Absolute Power beyond canonical 1/2-pt scale).
- `CharacterPowerPack` marked `kind: "power_pack"` — always-on narrative source-of-power bundle.
- New `CharacterPowerBundle` — activatable spell-like packet: `invocation` ∈ {always-on / per-scene / per-charge / per-day / roll-to-invoke / energy-cost}; `charges_max`/`charges_current`; `energy_cost`; `cooldown`; `source_spell_name`/`source_spell_level` for D&D-spell mimicry.
- `Character.power_bundles: List[CharacterPowerBundle]` — separate from `power_packs` (as the BESM Extras book distinguishes).
- `Campaign.anime5e_xp_formula: Literal["flat","curve"]` — GM-picked conversion formula for the optional BESM point-buy layer on Anime 5E.

**Validator upgrades (`/app/backend/routes/character_validation.py`)**
- BESM breakdown now sums Enhancement/Limiter VALUE deltas (not just count). `effective_level = level + net_delta` with floor 1; `gross = max(1, cpl×level + net_delta×level)` so stacked limiters raise paid CP proportionally, stacked enhancements lower it.
- Modifier-value out-of-range (|v| > 12) emits a warning line but does NOT fail the audit.
- Power Bundle lines render with their invocation + charge metadata in the breakdown (`"activatable · per-charge · 3 charges"`).
- `breakdown` now exposes `power_bundle_total` alongside `power_pack_total`, and `modifier_warnings` list.

**New endpoints**
- `GET /api/campaigns/{cid}/anime5e-xp-curve` — returns `{formula, cp_budget_at_level, curve[1..20]}`.
- `GET /api/reference/power-bundle-templates?max_level=N` — returns the seeded starter library filtered by spell level.

**Power Bundle starter library (`/app/backend/system_data/power_bundle_templates.py`)**
- 10 templates seeded from the user-supplied `Anime_5E_Spell_Conversions.pdf`:
  Dancing Lights (0), Cure Wounds (1), Enlarge/Reduce (2), Dispel Magic (3), Greater Invisibility (4), Insect Plague (5), Move Earth (6), Plane Shift (7), Control Weather (8), Meteor Swarm (9) — every spell school and every spell tier covered.
- Each carries its canonical invocation mode, CP cost, component Attributes with enhancement/limiter value rows, and page-cited references.

**Frontend**
- Campaign Primer form: Anime 5E campaigns show an `Anime 5E XP → CP formula` radio (flat/curve) with tooltips. Persists on save.
- Reference Editor: for `power_bundle` / `power_pack` tabs, GMs see an `Import from templates` button that opens a `PowerBundleTemplatePicker` modal with the 10 seeded cards (name · school · invocation · CP · charges/EP). Clicking a card drops a pre-populated Row into the draft editor for further customisation. Template testids now slugified (safe for selectors).

**Rules-correctness pytest sweep — `/app/backend/tests/test_iter37_v64_rules.py`**
- 19 new tests covering modifier-value math, out-of-range warning, power-pack vs bundle distinction, Anime 5E XP formula arithmetic at 9 level/formula combinations, curve endpoint, template filter, D&D level bound, Cypher tier bound, bundle-estimator vs validator cross-consistency, house-rules bypass, legacy string-tag compat.
- 20 regression tests (V6.1 + V6.2) still pass. **Total: 39/39.**
- Added `load_dotenv` to `tests/conftest.py` so direct-import helpers resolve MONGO_URL cleanly.

**Testing agent verification — `/app/test_reports/iteration_37.json`**
- Backend: 100% (39/39). Frontend smoke: toggle persists on Anime campaigns, hidden on others; template picker opens with all 10 seeded entries; filter input present.

**Stashed**
- `/app/memory/references/Anime_5E_Spell_Conversions.pdf` retained for future template expansion.


### V6.3 — Epic panel crash fix + System-label correctness + Cypher dynamics + Custom Reference expansion (2026-04-30)

**Bugs fixed**
- 🔴 `EpicCampaignPanel.jsx` crashed `Cannot read properties of undefined (reading 'kind')` on Phase 7 of Genesis. Root cause: epic docs seeded before newer fields existed arrived missing `beginning` / `seeds[*].kind` / `sentence` shapes. Fix: defensive normalisation in the load effect — every optional sub-doc (sentence, nemesis, beginning, ending_coolness) defaults to an empty-shape object, and list-items (seeds, villains, milestones, adventures) are spread with safe defaults so every section renders even on legacy docs.
- 🔴 Character sheet `sheet-system-label` showed "D&D 5E" / "5E hybrid" on Anime 5E campaigns. Root cause: label read from `folio.dnd_state` / `folio.anime5e_state` — player only populated the chassis, so Anime never registered. Fix: label now keyed off `campaign.system_id` (authoritative truth). An Anime 5E campaign always reads "Anime 5E"; a D&D 5E campaign "D&D 5E"; Cypher "Cypher · Tier N …"; BESM 4E "BESM 4E · PowerLevel · N pts".

**Cypher dynamic accounting**
- `builders/Cypher.jsx` — `setTier(newTier)` now also refreshes the Recovery die (defaults to 1d6+tier unless the player customised it). When the Type changes, `pools_type_baseline` is stored alongside `pools` so the discretionary-points chip can tell the "given by Type" bucket apart from the player-spent bucket.
- New **`cypher-pool-budget-chip`** in the Pools header: "Discretionary X / 6 [over]". X is the pool-points spent above the Type's baseline; the chip goes ember when > 6 (CSR p.16 creation rule).
- Character-sheet Cypher skill-train tags now have **per-kind hover tooltips**: Trained (−1 step), Specialised (−2 steps), Inability (+1 step). Colour-coded + cursor-help.

**BESM tooltip sweep**
- Enhancement tags: "Enhancement: {name}. Lowers the Attribute's effective Level by 1 — the power is more potent per CP paid. Stacks if listed multiple times."
- Limiter tags: "Limiter: {name}. Raises the Attribute's effective Level by 1 — the power is narrower, so each CP buys more functional range."
- Both rendered with `cursor-help`.

**Custom Reference Editor expansion**
- `REFERENCE_KINDS` grew from 8 → 23. New kinds (backend `Literal` + runtime allow-list kept in sync): `enhancement`, `limiter`, `power_pack`, `power_bundle` (BESM); `spell`, `feat`, `background`, `race_trait`, `class_feature` (D&D / Anime 5E); `cypher_ability`, `cypher_item`, `artifact`, `descriptor`, `focus`, `type` (Cypher).
- `SYSTEM_KIND_ORDER` — per-system tab ordering in the Reference Editor so BESM GMs don't scroll past 15 Cypher-only kinds to find Attributes.
- New **`PowerBundleEditor`** composer: GMs add Attribute/Skill/Defect/Enhancement/Limiter components, see a live CP estimate (via new `POST /api/reference/estimate-bundle-cost`) — same math path as the character validator so there's no drift between the two surfaces.

**Backend**
- `routes/reference_editor.py`:
  - `REFERENCE_KINDS` expanded.
  - `ReferenceItemIn.kind: Literal[...]` widened.
  - New `BundleComponentIn` + `BundleEstimateIn` + `POST /api/reference/estimate-bundle-cost` returning `{total_cost, component_count, lines[]}`.

**Verification — `/app/test_reports/iteration_36.json`**
- Backend: 28/28 (13 V6.3 + 15 V6.2 regression). Bundle estimator math verified (attribute 4×3−2=10, skill 2×2=4, defect −2 → 12). New kinds accepted via POST. Unknown kind still 400.
- Frontend: EpicCampaignPanel mounts without pageerrors on all four systems. Sheet-system-label correct across besm-4e / anime-5e / dnd-5e / cypher. Cypher builder shows `cypher-pool-budget-chip` 0/6 for a default Warrior. BESM Enhancement/Limiter/Defect tags carry hover tooltips verified live.

**Stashed for next session**
- `/app/memory/references/Anime_5E_Spell_Conversions.pdf` — user-uploaded conversion kit for the upcoming D&D-spell-mimic Power Bundle builder.

**Deferred to next session:**
- 🟠 BESM Power Bundle templates mimicking D&D spell effects (using the stashed conversion PDF as blueprint).
- 🟠 Public canon registry (discover + subscribe to campaigns that publish Delta Drops).
- 🟠 Per-system PDF theming; mobile PDF sheets; "How to" interactive guide.


### V6.2 — Delta-Drop + Character Rules-Compliance + Dual Approval (2026-04-30)

Session continuation after previous agent ran out of context. Completed three inter-linked P0 items:

**1. Delta-Drop — author-initiated cross-campaign updates**
- `routes/deltas.py` (now registered in `server.py`) exposes full CRUD over `db.campaign_deltas`:
  - `POST /api/campaigns/{cid}/deltas` — origin-only publish: snapshots current nodes / motives / epic / genesis, auto-increments version, broadcasts `delta:new` over WS to every clone room.
  - `GET /api/campaigns/{cid}/deltas` — returns per-row status (`published` on origin, `pending`/`applied`/`deferred` on clones). Pending drops first on the clone side.
  - `GET /api/campaigns/{cid}/deltas/{did}` — full bundle for preview.
  - `POST /api/campaigns/{cid}/deltas/{did}/apply` — conservative non-destructive merge: nodes deduped by title, motives by `(node-title, motive-text)`, epic/genesis soft-applied only if the clone's copy is empty/un-refined. Returns counts (`added_nodes`, `added_motives`, `epic_applied`, `genesis_applied`).
  - `POST /api/campaigns/{cid}/deltas/{did}/defer` — dismiss badge, keep drop in history.
- Frontend `DeltaDropPanel.jsx` mounted in a new GM-only `Delta Drop` tab on `CampaignDetail.jsx`. Auto-detects origin vs clone; origin shows a publish form, clone shows pending/applied/deferred rows with Preview / Apply / Defer buttons and a preview modal showing counts + node & motive lists.

**2. Character rules-compliance validator + dual approval**
- `routes/character_validation.py` — new module. System-aware `_validate_character()` computes:
  - **BESM 4E**: stats × 2 CP above baseline (4), attributes × cost_per_level − item-defect refunds, skills × cost_per_level, power-pack explicit costs, character defects refunded to pool. Flags over-budget (spent > campaign's `total_points`) and yellow-warns if ≥5 CP under-spent.
  - **Anime 5E**: D&D chassis sanity (level 1-20) + BESM-style point-buy layer sum vs `folio.anime5e_state.point_budget`.
  - **D&D 5E**: level 1-20 bound + class-set warning.
  - **Cypher**: tier 1-6 bound + descriptor/type/focus set.
- Endpoints:
  - `GET /api/characters/{cid}/validate` — read-only audit (owner, GM, or member).
  - `POST /api/characters/{cid}/app-validate` — stamps `approval.app_validated` on the character. Sheet-change invalidation: if the sheet has changed since the GM ratified, `gm_approved` resets to false with `gm_approval_stale_reason` set.
  - `POST /api/characters/{cid}/approve-for-play` (GM-only) — ratifies. **Hard guard**: if `passes_rules=False` AND campaign has no `house_rules` declared, HTTP 400 — GM cannot accidentally approve an over-budget PC without a house-rule exception recorded.
- **Session seat-take gate** (`routes/sessions.py`): seat-character now returns 409 if the PC isn't `approved_for_play`. `force=true` lets the GM override.
- Frontend `CharacterApprovalPanel.jsx` mounted under the XP Approval Queue on the character sheet. Status badge, rules audit card with per-system breakdown, issues/advisories lists, app-internal + GM-ratification status row, Re-run Validator / GM Approve (+ note) / Revoke buttons, and a house-rules override notice card.

**3. Anime5eSupplementView relabel**
- `CharacterSheet.jsx` `Anime5eSupplementView` header copy rewritten per the V6.1 rename: "Tri-Stat Supplement · Anime 5E hybrid" → "BESM Point-Buy Layer · Anime 5E hybrid"; subhead now notes the one-way port from 5E. Closes the last V6.1 inconsistency surfaced by iter34.

**Verification — `/app/test_reports/iteration_35.json`**
- Backend: 15/15 pytest pass in `test_iter35_v62.py`. Delta-Drop CRUD + permissions + clone-only apply + idempotent dedup; validator BESM/Anime/D&D/Cypher; GM approval 400-guard when no house-rules; house-rules bypass; seat-character 409 gate + GM force override; V6.1 regression retained (seed-evereantha-suite 9 motives, pulse resolver).
- Frontend: source-verified — all required testids present on DeltaDropPanel + CharacterApprovalPanel.

**Deferred (session completed P0; P1 queue unchanged):**
- Per-system PDF theming across all export paths.
- Mobile sweep for PDF character sheets styled like core rulebooks.
- "How to" interactive guide page with feature-interconnection map.
- "Canon delta" panel to visualise divergence vs canonical BESM 4E.


### V6.1 — Evereantha canon rewrite + Idempotent seeding + Anime 5E rules clarification (2026-04-30)

User-driven correction pass after V6.0.

**1. Idempotent seeding**
- `routes/demo_seed.py` `_seed_one()` now does a lookup by `(gm_id, name, system_id)` BEFORE creating anything. If found, returns `skipped_existing: true` with the existing campaign id + live counts. End to "click Deploy → 5 copies in account".

**2. Evereantha canon rewrite — "The Fracture of the Unmaker"**
- Replaced the placeholder Caldera Choir setting with the canonical 52-session arc per the user's source PDF.
- 43 codex nodes spanning: Continenta Aurea + Aetheris cosmology, Eagle's Nest / Gildenwood / Taurid Tor / Aevum Colosseum / Technopolis Lumina / 13th Temple, Order of the Darkening Star / Eclipse Syndicate / Singularity / Five Noble Houses, all 11 Deacons by name (Sylas Stonefist, Vaelin the Quiet, Morrigan Nightshade, Lyra Earthheart, Luminar, Rowena Wildwood, Augustus Blackpaw, Marcus Aurelius, Zephyr Windrider, Ignatius the Inferno, Azura Starlight), the cosmic principals Azazel/Samael/the Kin, Aurae & Mortiscura magic + Butterfly Effect Gauge.
- 9 plot-phase-tagged motives. 6-act epic milestone arc.
- System adaptations updated for D&D 5E / Cypher / Anime 5E (encounter NPCs are now Sleeping Kin + Cult Scout instead of the deprecated Sister Quench, properly setting up Sylas's Act-I storyline).

**3. Motive resolver hardening (bug fix)**
- The motive lookup table was matching by exact title only; the new long titles (`'Lyra Earthheart — Deaconess of the Elements / EarthMancer'`) silently dropped 3 of 9 motives. Lookup is now prefix-tolerant: matches by the segment before ` — `, falls back to startswith. Drop-events log a warning so the next divergence can't slip past.

**4. Anime 5E rules clarification — Tri-Stat REMOVED**
- Per the user's correction: Anime 5E is **D&D 5E with an OPTIONAL BESM-style point-buy LAYER on top**. It does NOT use Tri-Stat ability scores.
- `system_data/anime5e_data.py` — module docstring rewritten; `ABILITIES` is now the standard 5E six (STR/DEX/CON/INT/WIS/CHA); `TRI_STAT_LEGACY_ABILITIES` retained for migration only; the 5 Anime-original classes (Adept/Champion/Idol/Pilot/Tinker) now use 5E ability names for primary/saves; `rule_note` rewritten.
- `frontend/src/components/builders/Anime5eHybridSupplement.jsx` — UI strings: "Tri-Stat Supplement" → "BESM Point-Buy Layer", "+ Add Tri-Stat Attribute…" → "+ Add BESM-style Attribute…", footer disclaimer adds the one-way port note (5E content imports here; Anime 5E content does NOT port back to a strict-5E table).

**Verification — `/app/test_reports/iteration_33.json`**
- iter_33 found 1 backend issue (motive truncation at 6/9) + 2 frontend nits (3 leftover Tri-Stat strings). All fixed in this turn.
- Curl smoke verify: deleted-and-reseeded canonical besm now reports 9/9 motives. 4-system suite all systems show 9 motives. Second-call idempotency: `skipped_existing: true` with same IDs.

**Deferred to dedicated session(s):**
- 🟠 Per-system PDF theming across all export paths (BESM ornate/serif, Anime 5E vivid, Cypher brutalist, D&D 5E parchment)
- 🟡 Mobile sweep for CharacterSheet + PDF character sheets styled like core rulebooks
- 🟡 "How to" interactive guide page with feature-interconnection map



**Real-time Pulse nervous system**
- `routes/ecosystem.py` — new `_pulse_tick(cid, kind, meta)` helper broadcasts `{type:'pulse:tick'}` to `campaign:{cid}` room.
- Motive POST, Director PUT (encounter), and journal POST all fire a pulse tick. `DirectorConsole.jsx` subscribes via `/ws/campaign/{cid}`, debounces 350ms, refetches `/ecosystem/pulse`. New `[data-testid='pulse-live-badge']` flashes on each tick.

**Ingestion preview (clarity-check before LLM spend)**
- `POST /api/campaigns/{cid}/ingest-preview` — parse-only endpoint, zero LLM cost, returns head/tail excerpts + byte/char/paragraph meta.
- `IngestPanel.jsx` — two-step Upload & Preview → commit to Claude. New `[data-testid='ingest-preview-overlay']` with head/tail pre blocks + Cancel / Commit buttons.

**Anime 5E — D&D SRD class / race imports + chassis summary card**
- `system_data/anime5e_data.py` — CLASSES expanded from 5 to 17 (5 Anime-5E originals + 12 D&D SRD: Barbarian through Wizard), each tagged `origin` ('anime-5e' / 'dnd-5e-srd') with hit_die, primary ability, saves, casting. HERITAGES expanded from 8 to 16 (+Dwarf, Elf, Halfling, Dragonborn, Gnome, Half-Elf, Half-Orc, Tiefling) with ASI/size/speed/traits.
- `CharacterSheet.jsx` — new `[data-testid='dnd-chassis-summary']` 3-column card below the Class/Race/Background header showing hit die · casting · saves · speed · skills · tools · feature. Same mechanics power Anime 5E hybrid sheets (they share the dnd_state folio). `[data-testid='sheet-system-label']` now correctly reads "Anime 5E hybrid" when the folio has anime5e_state.

**Evereantha cross-system suite**
- `POST /api/admin/seed-evereantha-suite` deploys Evereantha as 4 parallel campaigns — besm-4e (canonical), dnd-5e, cypher, anime-5e — sharing the 23-node Codex + 9 motives but with per-system encounter stat shapes (CR / level / CR+Tri-Stat) and system-flavoured player primers. `Account.jsx` exposes `[data-testid='account-evereantha-suite-btn']`.

**Dashboard one-page redesign**
- Full rewrite of `components/Dashboard.jsx`. Hero strip + quick-action rail (Forge / Campaigns / Discover / Reference) + "Continue at the table" (3 recent sessions) + rich system-badged campaign grid + "Your characters" strip + "Tables seeking players" strip. 4 StatChips (campaigns / GM of / seats / public) aligned right. Fully responsive (1→2→3 col at base/sm/lg).
- Supporting backend: `GET /api/characters?mine=true` (user's owned characters, cross-campaign).

**Regression fix**
- `routes/campaigns.py` — list_campaigns now hydrates `is_gm` and `is_member` per row (previously only the detail handler did). Detail handler also gained `is_member` for parity. Dashboard GM badges, Account "Campaigns GM'd" stat, and Discover filter all rely on these.

**Verification — `/app/test_reports/iteration_{31,32}.json`**
- Backend: 9/9 iter31 regression, 3/4 iter32 (the 1 "fail" was a parity suggestion for detail endpoint — applied in this turn).
- Frontend: Dashboard all GM badges correct, DirectorConsole pulse-live-badge mounts + pulse data hydrates, Ingest preview modal open→cancel works (LLM budget preserved), chassis-summary + sheet-system-label testids verified in source.



Two P1 features shipped + significant hardening from the V5.5 work.

**Feature 1 — System-native MacroBar (Session Dice Altar)**
- `components/MacroBar.jsx` (new) renders per-system character-aware quick-roll macros in the dice panel. Each button populates the notation + label fields; click Roll to fire.
  - BESM 4E / Anime 5E (Tri-Stat): `macro-body`, `-mind`, `-soul`, `-acv`, `-dcv`, `-init`.
  - D&D 5E: `macro-str/dex/con/int/wis/cha`, `-adv` (2d20kh1), `-dis` (2d20kl1).
  - Cypher: `macro-d20`, `-d20-1` (asset), `-d20-3` (impaired), `-gm-intr` (GM Intrusion 1d6).
  - Anime 5E hybrid appends `2d6+B/M/S` on top of the D&D set.
- `components/SessionView.jsx` wires `<MacroBar>` below the Roll button; auto-selects the first character on load (player's own if present) so macros show without a dropdown click.

**Feature 2 — XP scorecard polish**
- *Per-quantum bonus breakdown popover*: Info icon next to each bonus input in `XPAwardPanel.jsx` opens a `[data-testid='xp-breakdown-popover-{cid}']` card showing counts × weights rows + subtotal + spotlight + cap.
- *Campaign-level XP Ledger*: new endpoint `GET /api/campaigns/{cid}/xp/ledger` (GM-only) aggregates every character's `xp_log[]` into a reverse-chrono feed with per-character totals + campaign totals. Mounted via `components/XPLedgerPanel.jsx` (GM-only modal, filter chips per character, source-label column, converted→CP indicator) triggered from a new `xp-ledger-btn` in the `CampaignDetail` header.
- *Empty-state safety*: XP scorecard now renders `[data-testid='xp-scorecard-empty']` when no characters are seated in a session instead of showing a confusing empty table.

**Hardening**
- `SessionView.jsx` `loadAll()` wrapped in try/catch; on failure `setLoadErr(detail)` and `useMinDelay(!session && !loadErr, 5000)` bypasses the ritual; renders `[data-testid='session-load-error']` with a "Back to campaigns" link. Fixes the "Opening the table…" infinite hang on 404 sessions that the testing agent previously hit.
- Cleaned up two file-tail duplication artefacts (`SessionView.jsx`, `CampaignDetail.jsx`) left over from earlier iterations.

**Verification — `/app/test_reports/iteration_{28,29,30}.json`**
- Backend: 5/5 pytest pass (`test_iter28_v552.py` — ledger access/shape/award/convert).
- Frontend iter_30: 4/4 PASS — session-load-error on 404, MacroBar auto-visible for Cypher (macro-d20/d20-1/d20-3/gm-intr), xp-scorecard-empty renders helpful copy, XP Ledger regression still clean.



Pure refactor — zero behavioural change. The 853-line monolith
`/app/frontend/src/components/SystemCharacterBuilders.jsx` was split
into a `builders/` package:

- `builders/shared.jsx` — `Stat`, `FreeList`, `ABILITIES_5E`, `ABBR_5E`, `modOf`, `profByLevel`.
- `builders/Dnd5e.jsx` — `Dnd5eBuilder` + `empty5e` (D&D 5E character forge).
- `builders/Cypher.jsx` — `CypherBuilder` + `emptyCypher` (Cypher System).
- `builders/Anime5e.jsx` — `Anime5eBuilder` (thin adapter that reshapes the Anime 5E ref into a 5E-shape ref and delegates to `Dnd5eBuilder` with the hybrid prop).
- `builders/Anime5eHybridSupplement.jsx` — Tri-Stat point-buy card (its own file so `Dnd5e.jsx` and `Anime5e.jsx` can both import it without a circular ESM cycle).
- `SystemCharacterBuilders.jsx` — reduced to a ~60-line `SystemBuilderLoader` that resolves URL params + fetches the campaign & system reference, then dispatches to the matching builder. Re-exports the named builders so any legacy import `from "./SystemCharacterBuilders"` keeps working.

**Verification — `/app/test_reports/iteration_27.json`**
- 100 % frontend pass: D&D / Cypher / Anime 5E builders all render with every testid intact and save end-to-end (`POST /api/characters` → navigate to `/app/characters/{id}`).
- Module compiled with only pre-existing eslint warnings (unrelated). No "Element type is invalid" runtime errors.
- ESM cycle removed by extracting `Anime5eHybridSupplement` to its own file (suggested by testing agent — applied immediately).

### V5.5 — Living Ecosystem fixed + Map upgrades + Loading ritual + Speed (2026-04-29)

Continuation pass after the V5.4 testing-agent-found CRITICAL bug.

**Backend fixes**
- `routes/demo_seed.py` — base_camp now writes `visibility: "private"` (was missing → caused GET /api/campaigns/{cid} to 500).
- `routes/campaigns.py:257` — defence-in-depth: `camp.get("visibility", "private")` instead of subscript.
- `routes/uploads.py` — MAX_BYTES bumped 12 MB → **32 MB** to support proper 2K (and most 4K) battlemap renders.

**Backend content — Evereantha demo expansion**
- `routes/demo_seed.py` EVEREANTHA blob now seeds **23 codex nodes** (was 7) and **9 NPC motives** (was 3) covering: 6 locations · 4 factions · 4 lore entries (incl. full magic system) · 9 NPCs.
- New magic system documented: **Seven Resonance Forms** (Quench / Edge / Strike / Weld / Hum / Crack / Seal) + Forbidden Eighth (Break). Each form has 5 ranks; Break costs ×2 CP and risks soul-shatter.
- New NPCs: Choirmaster Olen, Eli of the Glass-Hands, Cantor Veshin the Heretic, Anbel Mishtee, Sister Quench, Brother Crack — each carries a plot-phase-tagged motive that the Pulse Panel surfaces.

**Frontend — Mobile-friendly Battlemap + Fullscreen Edit + Min-delay loading**
- `lib/useMinDelay.js` (new) — holds a "still-loading" flag true for ≥ N ms after upstream resolves, so the thematic SUMMONING / OPENING / UNROLLING text gets a beat to read.
- `App.js` — `Protected` uses `useMinDelay(loading || user===null, 5000)`; `LoadingScreen` styled with new `data-testid="app-loading-screen"`.
- `components/SessionView.jsx` — replaced flash "Opening the table…" with full ritual: `data-testid="session-loading"` showing **OPENING THE TABLE** / "Tuning the candles" for ≥5s.
- `components/Battlemap.jsx`:
  - Replaced flash "Unrolling the map…" with **UNROLLING THE MAP** / "Pinning the corners · invoking the grid" for ≥5s.
  - **Mobile detector** (`window.innerWidth < 768` + resize listener). On mobile: GM tools hidden (`map-gm-tools`, `map-mode-fog`, `map-mode-wall`, `map-fullscreen-toggle` all gated `!isMobile`); mode auto-resets to `select`; new `data-testid="map-mobile-viewonly-banner"` reads "Map is view-only on mobile. GMs prep walls / fog / tokens on desktop."
  - **Fullscreen edit (desktop GM only)** — auto-engages when GM picks `fog` or `wall` mode. Renders `data-testid="battlemap-fullscreen"` (fixed inset-0, z-60, bg-black) so the rest of the app blacks out behind. ESC exits; manual toggle button `data-testid="map-fullscreen-toggle"` also works.
  - **Fit-to-screen on initial paint** — canvas wrapper now uses `maxHeight: 75vh` (default) / `calc(100vh - 90px)` (fullscreen) / `calc(100vh - 220px)` (mobile) and the bg `<img>` defaults to `objectFit: contain` so the whole map shows without scroll.
  - Upload tooltip + cap raised to **32 MB**.

**Frontend — Speed health-check**
- `App.js` lazy-loads heavy route components via `React.lazy` + `Suspense`: `Campaigns`, `CampaignDetail`, `CharacterBuilder`, `CharacterSheet`, `SessionView`, `Reference`, `CampaignGenesis`, `Discover`, `Account`, `DirectorConsole`. Each chunk is its own request, so the initial Dashboard paints faster. `RouteFallback` shows "UNFOLDING…" while a chunk loads (typically <200 ms).

**Verification — `/app/test_reports/iteration_25.json` + `iteration_26.json`**
- iteration_25: V5.4 surfaces 7/7 backend pytest PASS; **CRITICAL bug** found — demo-seeded campaigns 500'd on detail GET.
- iteration_26 (after fix): **16/16 backend pytest PASS** across `test_iter25_v54.py` + new `test_iter26_v55.py` (9 new tests). Frontend Playwright: SUMMONING / battlemap fullscreen / mobile view-only banner / Director Pulse Panel all visible. Only LOW issue: mobile leak on `map-mode-fog` / `map-mode-wall` buttons — fixed in this turn (now also gated `!isMobile`).
- Curl verified post-fix: GET /api/campaigns/{seeded_cid} → 200; pulse `?plot_phase=epic-9-adventures` returns Brother Crack + Sister Quench motives.

**Remaining (deferred):**
- Refactor `SystemCharacterBuilders.jsx` (853 lines) into `builders/{Dnd5e,Cypher,Anime5e}.jsx` — risky in the current context, deferred to a dedicated cleanup sprint.
- System-native macro library expansion (Session view per-system quick-rolls).
- XP scorecard polish — per-quantum bonus popover + campaign-level ledger.
- Ingestion preview — show parsed text excerpt before Claude commits.



**Two flagship features — the marquee item the user asked for + the deferred improvement idea, shipped in one batch.**

**Feature 1 — GM Director's Console (`/app/campaigns/:id/director`)** (V5.3 — Director's Console + One-Shot Scaffold)
The tactical brain of the campaign, GM/admin-only.

*Backend*
- New `core/cr_engine.py` — system-aware Challenge Rating with rule-based suggestions:
  - **D&D 5E**: DMG p.82 XP-threshold table per PC level, encounter-multiplier by NPC count, CR→XP map (DMG p.275). Returns Pushover/Easy/Medium/Hard/Deadly with reason.
  - **Cypher**: avg NPC level + crowd overflow vs party tier-weighted step-down (tier × 1.5). Pushover/Easy/Fair/Hard/Punishing.
  - **BESM 4E**: NPC CP total ÷ party CP total, ±15% bands. Pushover/Easy/Fair/Hard/Punishing.
  - **Anime 5E hybrid**: routes to D&D engine if any NPC has `cr` set, BESM engine otherwise.
- New `routes/director.py` — `GET /api/director/{cid}` aggregates `npc_pool` from Genesis seed_npcs[], Epic Campaign nemesis+villains, and Codex `npc` nodes (de-duplicated by source:name); `PUT /api/director/{cid}` round-trips encounters with id-stamping; `POST /api/director/{cid}/cr-analyse` runs the engine without persisting (debounced UI calls).
- New collection `db.directors`, one doc per campaign.

*Frontend — `DirectorConsole.jsx` (~700 lines)*
- 3-column layout: NPC Pool (left, sticky) · Encounter Editor (centre) · CR Panel (right, sticky).
- NPC Pool grouped by source (Genesis · Epic · Codex), one-click adds the NPC to the active encounter with intent + role pre-filled.
- Encounter Editor: party seat toggles, NPC rows with location/intent/state/role/count/system-shaped stat hint (CR for D&D, level for Cypher, CP for BESM/Anime), environment toggles (indoor/weather/light).
- CR Panel: rating with colour-coded difficulty bar (green→red), party_label, npc_label, reason, and rule-based suggestions list with Lucide icons (swords/shield/mountain/compass/flame/scroll/sparkles/x). Suggestions are designed to make encounters MORE engaging, not easier — explicit nudges like "GM Intrusion at the climax", "Plant a moral lever", "Add a ticking environmental clock".
- Multi-encounter tabs at the top so a GM can pre-build a session arc.
- Live "Atelier phase" picker that ties the current scene back to the 7-phase Genesis or 8-phase Epic Campaign.
- Director button on the campaign header (GM-only).

**Feature 2 — One-Shot Scaffold (`POST /api/campaigns/{cid}/scaffold-oneshot`)**
The "60-second campaign deploy" improvement.

*Backend — `routes/ingest.py` (extended)*
- New SCAFFOLD_SYSTEM_PROMPT — strict-JSON Claude Sonnet 4.5 contract: title_suggestion, premise, session_beats[], codex_nodes[] (≤30, type/title/summary/tags), npcs[] (≤12, name/role/intent/stat_hint), opening_encounter (name/environment/npc_indices/notes). Hard rules: no rulebook prose verbatim, mechanic-only, valid JSON.
- `commit=false` returns the parsed preview; `commit=true` writes Codex nodes (each codex_node + each NPC as a `npc`-typed gm-only node), tags them `one-shot-scaffold`, and stages the opening_encounter on the Director's doc with the picked NPC indices linked back to the codex node ids.
- Integrates with existing `_parse_to_text()` (PDF/MD/TXT/RTF/DOCX) + `_truncate_for_llm()` so the upload pipeline is identical to the existing Knowledge Web ingestion.

*Frontend — `IngestPanel.jsx` (extended)*
- New `scaffold-panel` card above the History block.
- Two-stage flow: Preview button → reviews title/premise/session-beats/codex-nodes/npcs in a 3-column preview block → Commit button writes everything to the campaign + Director.
- File input requires re-attach for Commit (browsers don't keep file handles between calls — documented in the helper text).

**Verification — `/app/test_reports/iteration_24.json`**
- 9/9 backend pytest cases PASS in `/app/backend/tests/test_iter24_v53.py` — including a LIVE Claude Sonnet scaffold-preview call (EMERGENT_LLM_KEY is set in this env).
- Director GET returns system_id=cypher + npc_pool aggregating Genesis/Epic/Codex; players get 403; PUT round-trips with id-stamping. CR-analyse on Cypher tier-1 PC vs L4 villain + 3×L2 minions returned `Punishing` with `remove_npc + feat` suggestions; empty-NPC = `Pushover`; empty-party = `Unknown`.
- Frontend Playwright sweep confirmed: director-console + director-npc-pool + director-encounter-editor + cr-panel render; pool-pick-* adds an NPC; director-party-{charId} seats the PC and the cr-panel updates to "Fair · Effective level 1.5 (encounter 3.0 + overflow 0.0 − party step-down 1.5)" with the suggestions list populated. Scaffold-panel + scaffold-preview-btn + file input present on the Atelier tab.

**Remaining backlog (deferred — judged lower-impact for this batch):**
- Move Reference Editor + Quickstart Instructions onto the Genesis page (UI re-org, low risk but no functional gain — existing locations still work).
- Custom-rules tab fields system+mechanic specific (small UI tweak — most fields already work for all systems).
- Editable card fields polish in CustomCardEditor (already wired at API + UI level — additional polish only).
- Evereantha + Artisan's Tale demo seeding across all systems (now SOLVABLE in 60 seconds via the One-Shot Scaffold for any pasted setting brief).
- Code refactor — split `SystemCharacterBuilders.jsx` into `builders/{Dnd5e,Cypher,Anime5e}.jsx` (no user-visible change, deferred to a dedicated cleanup sprint).

### V5.2 — Content expansion + system-aware UI sweep (2026-04-27)

**Big push.** Tackled most of the user's V5.1.2 backlog list in one pass.

**Backend content expansion**
- `dnd5e_data.py` — 8 SRD CC-BY backgrounds (Acolyte / Criminal / Folk Hero / Noble / Sage / Soldier / Sailor / Charlatan), full `SPELL_SLOTS_FULL`, `SPELL_SLOTS_HALF`, `SPELL_SLOTS_WARLOCK` tables (level 1-20), `CANTRIPS_KNOWN` per class.
- `anime5e_data.py` — 8 genre backgrounds (Honor Student / Idol Trainee / Mech Pilot Cadet / Wandering Swordsman / Magical Trainee / Cyberpunk Runner / Spirit Medium / Otherworlder), 8 Defects (Awkward, Bane, Conditional Power…), 10 anime-themed items, `CLASS_CASTING` map (Adept full, Pilot/Tinker half, Champion/Idol none).
- `cypher_data.py` — Descriptors and Foci now ship as objects with `genres[]` tags (8 genres: fantasy/modern/post/scifi/horror/superhero/historical/any) for genre-gating; new top-level `SETTING_GENRES`.
- `core/models.py` — Campaign V5.2 fields: `setting_genre` (Cypher gate), `primer_level_min` (D&D/Anime min), `primer_tier_suggest` (Cypher), `primer_xp_cap`, `house_rules`.

**Frontend system-aware UI**
- `CharacterSheet.jsx` — new universal **CharacterJournal** block (POST /characters/{id}/journal, reverse-chrono entries with timestamp + session id pill); new D&D **dnd-spell-slots** card derived from class+level using SRD tables (full/half/warlock variants + cantrips count).
- `SystemCharacterBuilders.jsx` — D&D Builder Background field is now a **dropdown** populated from SRD; selecting one surfaces a `dnd-background-card` showing skills/tools/languages/feature blurb. Cypher Builder Descriptor and Focus dropdowns now **filter by `campaign.setting_genre`** (entries tagged 'any' always show; legacy string descriptors normalised inline).
- `CampaignDetail.jsx` PrimerTab — new system-aware **Forge Caps** block: D&D / Anime show `primer-level-min`, Cypher shows `primer-tier-suggest` + `primer-cypher-genre`, all systems show `primer-xp-cap`. Universal `house-rules` textarea. Read-only player-side primer view surfaces setting / genre / level-min / tier / XP cap / prohibited-list / house-rules in cards.
- `ReferenceEditor.jsx` — **system-aware row fields**: `cost-per-level` / `points-per-rank` / defect-category hidden for non-BESM systems; non-BESM systems get description + (Cypher) genre tag inputs. The legacy BESM mechanic shape is preserved on `besm-4e`.
- `CharacterBuilder.jsx` — BESM **points-loading-bar** under the points-pool card; turns ember when over-spent.

**Verification — `/app/test_reports/iteration_23.json`**
- 5/5 backend pytest cases PASS in `/app/backend/tests/test_iter23_v52.py` (D&D ref, Anime 5E ref, Cypher ref, Campaign primer roundtrip, Character Journal).
- Frontend Playwright sweep: `primer-system-caps` + all 5 `primer-*` testids + save roundtrip (Cypher); `dnd-background` dropdown + `dnd-background-card` (D&D); `points-pool-card` + `points-loading-bar` (BESM); `character-journal` end-to-end (Cypher). `dnd-spell-slots` UI not visually exercised (no D&D chars yet); component code verified.

**Remaining from the V5.2 backlog (deferred — next iteration):**
- Anime 5E Challenge Rating / Encounter design tools.
- Move Reference Editor + Quickstart onto the Genesis page.
- Custom-rules tab fields system+mechanic specific.
- Editable card fields + deck composition by GM/players (CRUD wired; UI polish in CustomCardEditor pending).
- Evereantha + Artisan's Tale demo seeding across all systems.
- Code refactor — split `SystemCharacterBuilders.jsx` into `builders/{Dnd5e,Cypher,Anime5e}.jsx`.

### V5.1.2 — Cypher derived stats + system-aware Characters list + Account page + Seat-character + Narrative PDF (2026-04-27)

**Big batch in one pass.** Highest-leverage items from the user's list shipped, with the rest logged as P1 backlog.

**Backend**
- `system_data/cypher_data.py` — every `TYPES` entry now ships `pool_offsets`, `starting_edge`, `starting_cypher_limit`. New top-level `POOL_BASELINE = 7` and `TIER_DERIVED` (`recoveries_per_day` / `recovery_die`) — referenced both by the React builder for auto-fill and by the sheet for derived display.
- `routes/auth.py` — new `POST /api/auth/change-password` (verifies current password against fresh DB hash, rotates to new). `PATCH /api/auth/me` extended with `avatar_url` and `bio`.
- `routes/uploads.py` — new `POST /api/uploads/avatar` for any authenticated user. 4 MB cap. Persists `avatar_url` on the user record. Sibling-extension cleanup on re-upload (no stale PNG/JPEG/WEBP stacking).
- `routes/sessions.py` — new `POST /api/sessions/{sid}/seat-character?character_id=X` (player seats own char, GM/admin can seat any) + `POST /api/sessions/{sid}/assign-character` (GM override) + WS broadcast `seating:update`.
- `routes/pdf_export.py` — new `?mode=narrative` query param. Bypasses the per-licence forbidden-setting 451 gate (Cypher Numenera/Strange/NTYE etc.) since narrative output is, by definition, not a sellable supplement. Switches to a new `_narrative_profile()` (no system trade dress, neutral parchment, narrative-only banner). `mode=campaign` (default) keeps every existing licence guarantee.

**Frontend**
- `Account.jsx` (new, ~250 lines) — avatar upload with file picker, profile patch (byline + bio), in-app password change, game stats aggregate (campaigns GM'd / seated, character count, XP earned / unspent across all owned characters). Wired into `App.js` `/app/account` route + `Shell.jsx` sidebar `nav-account`.
- `CharacterSheet.jsx` — `CypherSheetView` now renders a 4-up derived block (Armor / Cypher Limit / Recoveries-remaining / Effort cap) directly under the pool rings. Recovery die computes from tier (1d6+tier). New `Anime5eSupplementView` renders the Tri-Stat point-buy supplement read-only on the d20 chassis when `folio.anime5e_state.point_buys[]` exists.
- `SystemCharacterBuilders.jsx` (Cypher) — `setType()` auto-fills pools (`baseline + pool_offsets`), starting edge, and cypher limit from the chosen Type. New editable Armor / Cypher Limit / Recoveries-max / Recovery-die row.
- `CampaignDetail.jsx` — replaced the BESM-shape Body/Mind/Soul card strip with `CharacterCardPreview` (system-aware): D&D shows class+level / AC / HP / Prof; Cypher shows Tier/Descriptor/Type + Pools + Armor + Cypher×limit; Anime 5E hybrid shows D&D + tri-stat ×N badge; BESM unchanged.
- `SessionView.jsx` — new `take-seat-section` listing the user's own characters with seat/release toggle (calls `/sessions/{sid}/seat-character`). Seated state highlights gold; other players' seats show in a `seating-summary` strip. WS `seating:update` patches the in-page state. Compact `systemBlurb()` helper used by both the seat picker and the existing "Add to Initiative" list — no more BESM Body/Mind leak for D&D / Cypher characters.
- `AtelierTab.jsx` — `ExportPdfBtn` popover gains a Mode toggle (Campaign · branded vs Narrative · story). Narrative mode is recommended in the helper text for forbidden-setting campaigns.

**Verification**
- `iteration_22.json`: 13/13 backend pytest cases PASS in `/app/backend/tests/test_iter22_v512.py`. Frontend Playwright sweep confirmed Account page renders + avatar upload round-trip + system-aware Characters list testid `card-system-{id}` present. The narrative-PDF empty-state response (400 "No sessions to export.") on the Forbidden-Test campaign is documented as correct, not a bug.
- One cosmetic finding fixed in this turn (Account identity-card column overlap on 1920w viewports — widened gap and added truncation).

**Remaining from the user's V5.1.2 wishlist (P1 backlog — next iteration):**
- Anime 5E full content extraction — races / classes / backgrounds / ancestries / items / spell slots / cantrips list with toggleable pickers.
- D&D backgrounds + ancestries content seeding (CC-BY SRD).
- Cypher genre-gating — filter Descriptors/Foci/Types/Equipment by campaign setting; deepen Effort/Edge/Intrusions in flow.
- Anime 5E Challenge Rating / Encounter design tools.
- Character sheets in all systems: Journal section, Backgrounds (D&D + Anime 5E), Ancestries, Spell Slots / Cantrips picker.
- XP point pool counter visible during creation; XP loading-bar animation when earning.
- Custom-rules tab fields system-and-mechanic specific.
- Reference Editor: hide BESM "cost/level" labels for non-BESM kinds; show appropriate Cypher Tier requirement / D&D level requirement.
- Move Reference Editor + Quickstart Instructions onto the Genesis page (new phase tab); leave only what remains in the in-campaign Atelier card.
- Player Primer system-specific (level min / XP cap / suggested tier / prohibited lists / house rules / setting / description).
- Editable card fields + deck composition (GM, sometimes player).
- Anime 5E Reference content — ensure non-BESM systems don't show Body/Mind/Soul as the literal "stats" strip on system reference pages.
- Evereantha + Artisan's Tale demo seeding across all systems (campaigns, codex, atelier, sessions, references, custom rules).
- Robust content injection for D&D / Cypher / Anime 5E (cyphers, relics, items/equipment, foci, descriptors, types, flavors, races, classes, backgrounds).
- Code refactor pass — split `SystemCharacterBuilders.jsx` into `builders/{Dnd5e,Cypher,Anime5e}.jsx`.
- PDF export options expansion — per-system theme variants surfaced in the popover.
- One-page-design philosophy assessment on the main dashboard.
- Mobile-friendly review (especially session running page — responsive video tiles, chat overflow, dice roller, character sheet quick-references).
**Trigger:** GMFran uploaded Guy Sclanders' follow-up book *Epic Campaigns: Digital Edition* (146 pp) and asked for a new tab inside the **"Forge the Master Plot"** Atelier page. The two planes (the existing 7-phase Genesis and the new Epic Campaign) are intentionally INDEPENDENT — usable in tandem, separately, or one-or-the-other; pure GM brainstorming kit.

**Initial mis-placement (corrected):** First pass put the new framework as a sub-tab inside `AtelierTab` (the in-tab Session-0/Arcs/Master-Plot stack). Per user clarification, the user actually meant the standalone `/app/campaigns/:id/genesis` route ("Forge the Master Plot" — 7-phase guided form) reached via the **Atelier** button on the Campaign header. AtelierTab reverted to original; Epic framework moved to a new `phase === 7` panel inside `CampaignGenesis.jsx`, alongside the existing Sentence / Theme & Tone / Nemesis Design / Master Plot / Adventure Outlines / Supporting Cast / Beginning & Ending. The progress bar now reads `0/8 phases`.

**Backend — `/app/backend/routes/epic_campaign.py` (new module)**
- New collection `db.epic_campaigns`, one doc per campaign (`campaign_id` keyed). GM-only.
- Pydantic models mirror the book's structure 1-to-1:
  - `OGASNpcIn` — Occupation · Attitude · Goal · Stake (ch.3) + driving desire (ch.4) + nemesis psychology (BFT / Never-Present / Mentor — ch.8) + weakness pattern (ch.11)
  - `SentenceIn` — Someone wants something in a timeframe by a method (ch.7)
  - `MilestoneIn` — Plan → milestones → obstacles → resources-have/needed → POE design (ch.9)
  - `AdventureIn` — mode (Advancing-Campaign / Advancing-PCs / Enhancing-Game) + 8 types (Nemesis-On-Track / Nemesis-Revenge / Ah-Ha / Backstory / PC-Goal / Emergent / Chaos / Pacing) (ch.10)
  - `SeedIn` — name/place/object/person/dream/portent/omen with payoff + paid_off flag (ch.12)
  - `BeginningIn` — 9 POE adventure-design templates for Session 0/1 (ch.13)
  - `CoolnessIn` — Location · Abilities · NPCs · Situation · Pressure (ch.14.1)
  - Plus `theme` / `theme_evolution` (ch.5), `expanding_goal[]` (ch.8.3), and 4 climax C's (ch.14)
- 3 endpoints:
  - `GET  /api/epic/{cid}` — auto-creates an empty plan on first read; GM-only (403 for non-GM).
  - `PUT  /api/epic/{cid}` — full-doc replace; stamps stable ids on every list-item.
  - `POST /api/epic/{cid}/seed-codex` — pushes the Nemesis + each Villain + each Seed into the World Codex as `gm_only` knowledge nodes; idempotent (re-run = 0 new nodes until the entity changes); writes the resulting `linked_node_id` back into the Epic doc so subsequent runs UPDATE the existing node instead of duplicating.

**Frontend — `/app/frontend/src/components/EpicCampaignPanel.jsx` (new component, ~700 lines)**
- 11 collapsible sections matching the book's chapter order (sections 1–11).
- `OGASNpcEditor` reused for the Nemesis + each Villain row (locked role for the Nemesis).
- `MilestoneEditor` carries chiplists for obstacles/resources + a 3-column POE block.
- `AdventureEditor` shows Mode + Type dropdowns; surfaces a Linked-PCs picker only when mode is `advancing-pcs` or type is `backstory`/`pc-goal`.
- `SeedRow` — 7-kind dropdown + label + payoff + seeded-in + paid-off checkbox.
- Climax — Coolness Factor 5-input grid + Chaos&Calm + Contingency + Catastrophic-Consequences + Climax beats.
- Tie-ins section — `PickList` connectors that link any Codex node id and any Character id into the Epic doc (pure pointers, no destructive coupling).
- `Sync to Codex` button — invokes the seed-codex endpoint and shows a toast with the count of new nodes created. The `linked_node_id` shows as a confirmation chip on each NPC row once synced.
- Every interactive element has a `data-testid` (e.g. `epic-section-nemesis-toggle`, `epic-sentence-someone-input`, `epic-milestone-0-poe-prob-input`, `epic-adv-0-mode`, `epic-seed-0-payoff`, etc.)

**Frontend — `AtelierTab.jsx` wiring**
- Added a sub-tab strip below the Atelier header: `Master Plot · 7 Phases` (existing) ↔ `Epic Campaign` (new), persisted in `planeTab` state. The Master-Plot stack only renders when its sub-tab is active; the `Save` and `Continuity check` header buttons hide on the Epic tab (the Epic panel has its own Save / Sync-to-Codex). The PDF-export button stays on both planes.
- Pre-fetches `/api/campaigns/{cid}/characters` and `/api/campaigns/{cid}/nodes` so the Epic panel's tie-in pickers are populated without extra round-trips.

**Verification (curl + Playwright smoke)**
- GET on a fresh campaign returns the empty-shape doc; PUT round-trips Plan summary / theme / Sentence / Nemesis OGAS / Villains / Milestones / Seeds intact.
- POST seed-codex created 3 gm-only nodes (Nemesis Malshe Darkening + Henchman Frock + Seed "Brass concussive horn") on the user's Forbidden-Test Cypher campaign; second invocation returned `nodes_created: 0` (idempotent).
- Playwright login → Forbidden-Test campaign → Atelier tab → Epic sub-tab — panel renders, fundamentals/sentence/nemesis sections expanded by default, Plan-summary textarea shows the previously-saved data, Save + Sync-to-Codex buttons visible.
- All ESLint + Ruff lints clean.

**Acknowledged but deferred (per user instruction):**
- Cypher character derived-stats (HP / Shield) not computed on builder save, and the in-campaign Character list still renders the BESM stat strip for Cypher PCs (numbers come from the Cypher state but the labels/derived calc are BESM-shape). User explicitly asked to not spend cycles on this in the current request — logged here so the next iteration can pick it up.

## 3. Backlog (Prioritized)

### P0 — Pending validation
- Validate the 404 fix on `/campaigns/:id/characters/new` for Anime 5E + Cypher live (testing-agent confirmed the underlying routing fix in iter_21; manual UX check still pending).

### P1 — Cypher polish (the issue user flagged but deferred this turn)
- Compute Cypher-shaped derived stats (Pool totals, Recovery rolls, Effort cap remaining) at character-save time and surface them on the Character Sheet.
- Replace the BESM stat strip on the campaign Characters list with a system-aware preview: Cypher = "Adept · T1 · M7/S11/I13", D&D = "Wizard 3 · AC 12 · HP 18", Anime 5E = system's combo, BESM unchanged.

### P1 — Content & Mechanics
- Anime 5E full content extraction — toggleable race/class lists with hit-dice, modifiers, Tri-Stat attributes (pg 91), defects (pg 132), enhancements/limiters, items (pg 190+), alignment.
- Cypher genre-gating — filter Descriptors / Foci / Types / Equipment by campaign's chosen Cypher setting (Godforsaken / Heartwood / Predation / etc.), surfaced in the Cypher builder.
- Anime 5E Challenge Rating + Encounter design tools (battlemap-side companion).
- System-native macro library expansion (per-system quick-rolls in session view).
- XP scorecard polish — per-quantum bonus popover + campaign-level ledger.
- Ingestion preview — show parsed text excerpt before Claude commits.
- Seed Evereantha + Artisan Tale demo campaigns across all four content systems.

### P2 — Refactor
- Split `SystemCharacterBuilders.jsx` into `builders/{Dnd5e,Cypher,Anime5e}Builder.jsx`.
- Migrate `routes/sessions.py.roll_dice` into `core/dice.py` so `routes/channels.py` doesn't import inside the handler.
- Add `?confirm=WIPE` flag also to `POST /api/admin/reset-to-evereantha` (already done for the destructive reset endpoint per V4.2 — verify no other destructive routes are unguarded).

## 4. Credits
- BESM 4E — Mark MacKinnon, Dyskami Publishing, 2020
- Anime 5E — Mark MacKinnon, Dyskami Publishing, OGL-distributed
- Cypher System — Monte Cook Games, LLC; integrated via the Cypher System Creator programme
- D&D 5E content — CC-BY SRD 5.1 (Wizards of the Coast)
- "How To Be A Great GM" / "Epic Campaigns" frameworks — Guy Sclanders (used by permission of the author/buyer; both Sclanders frameworks now power the Atelier Master-Plot and Epic-Campaign sub-tabs respectively)
- Evereantha setting — user-provided ("Artisan's Tale")

## 5. Test Credentials

See `/app/memory/test_credentials.md`. GMFran (`franpietrowski@gmail.com` / `PieGod08!!`) is the sole authoritative seeded admin.
