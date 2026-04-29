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

### Core (V1.0 → V4.6)
- Auth · BESM 4E full reference data · Campaign Atelier (7-phase Sclanders Master Plot Genesis) · multi-system Character Forges · Live Sessions with WebRTC mesh AV · Knowledge Web with role-gated reveal · Atelier Session-0 + Arcs + continuity · Player Primer with allow/prohibit lists · Resend email · World Codex + Genesis seed → nodes · Session Recap (Claude) + auto-pin + finalize-into-chronicle · Battlemap V2 (LoS raycast + measure ruler + token effects) · Discord-style PBP Channels V2 (real-time WS + @mention autocomplete + image attachments) · System theming layer · Card Decks (Deck of Many Things, Cypher Draw, Genre Shift, Mood) · DriveThruRPG-ready PDF chronicles with system-specific style profiles · system-aware ingestion (Claude branch per system) · XP scorecard with GM approval queue · Customisable Attribute/Skill/Defect display names · System-aware Reference Editor (Atelier) · System-aware Character Sheets · D&D 5E + Cypher dedicated builders · Anime 5E hybrid (Tri-Stat point-buy + 5E class+slot) builder · HP/Pool status rings on Character Sheet · 404-fix on `/campaigns/:id/characters/new` for non-BESM systems

### V4.3 Compliance
- Cypher System Creator licence — cover-line + trade-dress + forbidden-setting (Numenera/Strange/NTYE) PDF-export gate (HTTP 451) + verbatim required-text strings served via `/api/systems/cypher/reference`.

### V5.1 — Atelier "Epic Campaign" 8th-phase tab (2026-04-27)
**Trigger:** GMFran uploaded Guy Sclanders' follow-up book *Epic Campaigns: Digital Edition* (146 pp) and asked for a new tab inside the **"Forge the Master Plot"** Atelier page. The two planes (the existing 7-phase Genesis and the new Epic Campaign) are intentionally INDEPENDENT — usable in tandem, separately, or one-or-the-other; pure GM brainstorming kit. Implemented as `phase === 7` panel inside `CampaignGenesis.jsx`, alongside the existing seven phases. Backend: new `db.epic_campaigns` collection + `routes/epic_campaign.py` (GET/PUT/seed-codex). Frontend: new `EpicCampaignPanel.jsx` (11 sections — Plan/Constraints, Theme, Sentence, OGAS Nemesis, Villains, Expanding Goal, Milestones, Adventures, Seeds, Beginning, Climax — plus Tie-ins picker). The "Sync to Codex" action pushes the Nemesis + each Villain + each Seed into the World Codex as gm-only knowledge nodes; idempotent on re-run.

### V5.3 — Director's Console + One-Shot Scaffold (this iteration — 2026-04-29)

**Two flagship features — the marquee item the user asked for + the deferred improvement idea, shipped in one batch.**

**Feature 1 — GM Director's Console (`/app/campaigns/:id/director`)**
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
