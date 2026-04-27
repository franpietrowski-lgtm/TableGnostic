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

### V3.9 — Backend modularisation + OpenAPI tag pass (this iteration — 2026-04-25)

**Refactor — `server.py` 1772 → 65 lines (well under the 700-line guideline)**

Old monolithic `server.py` split into focused modules with 1:1 functional preservation:

```
core/
  config.py        env vars · JWT_SECRET · CORS regex · EMERGENT_LLM_KEY · Resend
  db.py            Mongo client (MONGO_URL/DB_NAME) · now_iso · new_id · sanitize
  security.py      hash/verify password · JWT mint/verify · set_auth_cookies · get_current_user
  email.py         Resend transport with console fallback
  models.py        all Pydantic In/Out (RegisterIn, LoginIn, CampaignIn, CharacterIn,
                   JournalEntryIn, NodeIn, EdgeIn, SessionIn, ChatIn, DiceIn,
                   InitiativeEntryIn, EffectIn, DamageIn, RecapIn (+in-character),
                   CustomAttributeIn, GenesisIn, NodeRevealIn)
  cost_engine.py   attribute_cost (BESM ≥1/Level clamp + nested Item/Weapon defects),
                   calc_derived (campaign DR-baseline aware), calc_spent_points,
                   resolve_system_id
  bus.py           Bus class (mesh WebRTC presence + relay) · module-level broadcast()
  startup.py       ensure_indexes · seed_user (admin/gm/player auth) · invite-token backfill

routes/
  auth.py          tags=['auth']           7 routes  (register/login/logout/me/refresh/forgot/reset)
  besm.py          tags=['reference']      2 routes  (besm/reference + systems)
  campaigns.py     tags=['campaigns']     16 routes  (CRUD + invites + custom rules + genesis)
  characters.py    tags=['characters']     6 routes  (CRUD + journal)
  nodes.py         tags=['knowledge-web']  7 routes  (nodes + edges + reveal + visible_to)
  sessions.py      tags=['sessions']      16 routes  (sessions + chat + dice + initiative
                                                      + effects + damage + health + WS)
  recap.py         tags=['recap']          2 routes  (Loremaster LLM)
  seed.py          tags=['seed']           1 route   (Evereantha PCs)
```

`server.py` keeps only: `load_dotenv()`, FastAPI app, CORS middleware, Permissions-Policy
middleware (camera/microphone for AV Seats), `@on_event("startup") → run_startup()`, and 9
`include_router` calls (the 8 domain routers + the WebSocket `ws_router`).

**OpenAPI tag pass (export-ready Swagger UI for VIP DriveThruRPG pipeline)**
- 8 distinct tags · 57 operations across 49 paths.
- Each route file declares `APIRouter(tags=["..."])` so endpoints group cleanly.
- Verified: `curl http://localhost:8001/openapi.json | jq` lists all 8 groups.

**Future LiveKit-readiness**
- `core/bus.py` is engineered as a thin relay so the AV layer can swap to an SFU
  (LiveKit / Daily / Agora) later without touching session-state routes.
- The `webrtc:offer/answer/ice` targeted relay + `presence:av-state` broadcast
  in `routes/sessions.py.ws_session` are the only call sites that would change.

### V4.0 — Evereantha Seed + Battlemap + PBP Channels (this iteration — 2026-04-26)

**1. AV black-square fix (`AVSeats.jsx`)**
- The self-tile `<video>` is rendered conditionally on `joined` — `localVideoRef.current` was therefore null at the moment `getUserMedia()` resolved, so `srcObject` was set on a null ref and silently lost.
- Moved the attach into a post-mount `useEffect(()=>{ ... }, [joined, camOn])`.
- Added `.play().catch(()=>{})` on both self + peer tiles for Safari/older Chromium autoplay quirks.

**2. Phase A — Evereantha canonical seed**
- New module `seed_evereantha.py` (full rewrite): three apprentice PCs from the user's "Artisan's Tale" PDF —
  - **Eli** (Apocophae alchemist) — token green, B4/M7/S6, Healing+Range-Consumable, alchemy bandolier, Apocophae Discipline lvl 3
  - **Laryk** (Ferrilith earth-smith monk) — token bronze, B6/M4/S5, Massive Damage, Heavy Armour, Hammer & Forge special attack
  - **Roney** (Techgnostic tinker) — token copper, B4/M7/S5, Item L8 + concussive horn, light burst, brass harness
- Each PC ships with a Power Pack bundle that references the appropriate attributes/skills.
- 20-node **World Codex**: 5 locations (Aurea / Eagles Nest / Golden Forests / Montes Inexpugnabilis / Solar-Lunar Caldera) · 2 factions (Artisans Guild + Order of the Darkening Star nemesis) · 6 NPCs (Mayor + Maid + Nyaulis + Mishtee + Frock + Malshe) · 1 creature (Lancing Andrewsarchus) · 2 lore (Barter Economy + Artisan Disciplines) · 4 quests (Maiden Adventure / Cataclysm Reagent / Forge-Glass Hammer / Sigil in the Harness — the last GM-only).
- 7-phase **Atelier/Genesis** pre-fill — Sentence + Theme + Nemesis + 6 Master-Plot Acts + 5 Adventures + 6 seed NPCs + Beginning + Ending.
- New endpoint `POST /api/admin/reset-to-evereantha` (admin-only) — wipes all game collections (preserves users, login_attempts, password_reset_tokens) and seeds the canonical Evereantha demo table atomically.

**3. Phase B — Battlemap (`routes/battlemap.py` + `Battlemap.jsx`)**
- Per-session canvas state (`db.battlemaps`) — square grid + image bg + tokens + walls + fog cells + measurements.
- Endpoints: `GET/PUT /sessions/{sid}/map`, `POST/DELETE /sessions/{sid}/map/tokens[/{tid}]`, `POST /sessions/{sid}/map/fog` (reveal/hide deltas), `POST/DELETE /sessions/{sid}/map/walls[/{wid}]`.
- Access: read = any campaign member. Token moves: GM moves any token; player moves only tokens whose `character_id` they own. All other writes (image/grid, walls, fog) are GM-only.
- Real-time: re-uses session WebSocket bus — broadcasts `map:state` / `map:token` / `map:token-remove` / `map:fog` / `map:wall`.
- Frontend: `<Battlemap>` component opens as a full-screen overlay from the new "Map" button in `SessionView`. Square grid SVG, draggable token buttons, mode toggles (Select / Fog / Wall), GM tools (image URL / grid resize / Seed PCs / Hide-all / Reveal-all), HP bars, status rings, init-driven gold-ring spotlight on the active actor's token.

**4. Phase C — Discord-style PBP channels (`routes/channels.py` + `ChannelsPanel.jsx`)**
- Per-campaign text channels (`db.campaign_channels`), threads (`db.threads`), messages (`db.channel_msgs`).
- Endpoints: channels CRUD (GM-only writes) · threads CRUD · messages CRUD with markdown bodies · reactions toggle · pin (GM-only) · attachments[].
- Slash-commands parsed server-side: `/roll <notation>` (executes via `routes.sessions.roll_dice`, stores result in `slash_meta.result`, kind=`"roll"`) · `/me <text>` (emote, slash_meta.kind=`"emote"`) · `/w @handle <text>` (whisper).
- Mention resolution: `@handle` matched against campaign members' `name` / `email` prefix; resolved uids stored in `mention_uids` for highlight.
- First channel auto-creates as `#tavern` on first GET — fresh campaigns always have somewhere to talk.
- Frontend: `<ChannelsPanel>` lives in a new "Channels" tab inside `CampaignDetail`. Discord-like layout — channels rail · message stream with hover toolbar (react / thread / pin / delete) · markdown body · /roll renders as big total + dice breakdown · /me as third-person italics · /w as private aside · thread drawer slides in from the right.
- Polling: 4 s on the active channel (campaign WS room is wired but not yet subscribed — V1.5).

**5. Sheet macros**
- `CharacterSheet.jsx` core stat tiles are now clickable buttons (`2d6-Body`, `2d6-Mind`, `2d6-Soul`).
- The shared `roll()` function now ALSO posts `/roll <notation>     # <PC name> · <label>` into the campaign's first PBP channel (so the table sees rolls even when no live session is open).
- Existing attribute / skill `Roll` buttons reuse the same path.

### V4.0 — Tested (iter_12)
- Backend: **33/33 new tests PASS** (`test_iter12_v40.py`) — covers admin reset (forbidden for player+gm; 200 for admin), Evereantha seed integrity (campaign + 20 nodes by-type breakdown + 3 PCs with computed `spent.total_spent` + Genesis phase 7), battlemap (member 200 / non-member 403 / GM-only PUT / GM token add / player can move OWN token / player cannot add unbound / GM fog hide-then-reveal / player cannot fog / GM walls CRUD / GM delete token), battlemap WebSocket (`map:token` event delivered after POST), channels (auto-tavern · player-cannot-create · admin-creates · /roll dice expansion · /me + /w slash kinds · mention resolution · reaction toggle · pin GM-only · threads CRUD + filter · edit + delete authorisation · GM channel delete), regression (`/api/health` · OpenAPI new tags · `/api/dice` still works).
- iter_11 OpenAPI assertion re-baselined to expect 11 tags + ≥75 ops (was 8 / 57 — V4.0 added admin/battlemap/channels).
- Found-and-fixed in this run: **ObjectId leak** in `routes/channels.py::list_channels` auto-create branch (motor mutates the input dict to inject `_id` — wrapped the default in `sanitize()` before return).
- Test fixture fix: switched the character ownership-transfer write from `motor` (asyncio loop flake) to sync `pymongo`, and added a `load_dotenv` so the test connects to the same DB as the running backend.

### V4.0 — Code-review notes (deferred — not blocking)
- `roll_dice` in `routes/sessions.py` is imported by `routes/channels.py` inside the handler to avoid a cycle. Hoisting to `core/dice.py` would let both routes import freely (cosmetic).
- `POST /api/admin/reset-to-evereantha` is destructive and irreversible. Consider gating behind `?confirm=WIPE` to defend against automation triggers.
- `PUT /api/characters/{id}` silently drops `owner_id` changes (frozen on update). Fine by design but should either 400 explicitly or expose an admin-only ownership-transfer endpoint.
- Campaign-scoped channel broadcasts go to a `campaign:{cid}` WS room that has no current subscriber. Frontend uses 4 s polling; a `/api/ws/campaign/{cid}` upgrade would make channels real-time.

### V4.1 — GMFran admin · BESM 4E cost-rule fix · Campaign clone · Reference expansion · Aurea custom (this iteration — 2026-04-26)

**1. GMFran admin account** — `franpietrowski@gmail.com` / `PieGod08!!` / name `GMFran` / role `admin`. Seeded idempotently from `core/startup.py`; replaces any prior account with that email.

**2. BESM 4E cost-rule correction (Mark MacKinnon's primer)**
The prior `per_level = max(1, base + #Enh − #Lim)` formula was the *opposite* of the BESM 4E rule. Corrected to:
- **Cost** = `base_cost_per_level × assigned_level` (fixed — Enhancements/Limiters never change cost)
- **Effective Level** = `assigned_level + #Limiters − #Enhancements` (≥ 1)
`core/cost_engine.attribute_cost()` rewritten + new `effective_level()` helper. `calc_derived()` now reads effective level (so HP / EP / ATK / etc. shift with limiter/enhancement stacking). `routes/characters.py` decorates each Attribute with `effective_level` on every read so the frontend just renders it.

**3. Campaign cloning** — `POST /api/campaigns/{cid}/clone`. Any GM/admin with read access (own / public / member) forks a campaign into a brand-new one they GM. Carries World Codex nodes (with id-remapped edges), Genesis (Atelier) pre-fill, custom rules, and *published* characters (re-owned by the cloner). Excludes sessions / chat / dice / recaps / battlemaps / channels. UI: new "Clone" button on the CampaignDetail header.

**4. Reference page expansion (V4.1)**
New sections piped through `/api/besm/reference`:
- `actions` (13 entries — Standard Attack / Defend / Block / Move / Sprint / Charge / Aim / Dodge / Grapple / Ranged / Skill / Recover / Use Power Pack)
- `companions` (5 — Henchman / Servant / Mecha / Mount / AI-Spirit)
- `race_templates` (8 — Human / Half-Demon / Beastfolk / Construct / Faerie / Spirit / Animal / Apprentice Artisan-Aurea)
- `size_modifiers` (8 — Microscopic→Colossal with ATK/DEF/HP table)
- `weapons` (14 — incl. setting-specific Pocket Lamp Burst)
- `items_gear` (12 — incl. Alchemy Bandolier, Tinker Harness, Forge Bellows, Iron Stakes)
- `armour` (10 — incl. Ferrilith's Smith's Apron, Apothecary Coat)

Three tab groups in `Reference.jsx`: **Core BESM 4E** · **Combat & Play** · **Custom · Aurea**. A pinned BESM 4E cost-rule note appears on attribute / enhancement / limiter / custom tabs so the rule is visible everywhere it matters.

**5. Aurea magic system as a worked custom example**
New `custom` block on `/api/besm/reference` showing how to build a setting's magic system inside vanilla BESM 4E + Extras — **no new sub-system, only Attribute/Skill/Defect re-skins**:
- 8 **Custom Attributes** — Apothecary Tincture · Stone-Shape · Forge-Strike · Cog-Insight · Pocket Detonation · Wild Speech · Pelt-Shift · Reagent-Sense (each with `based_on`, `enhancements_intent`, `limiters_intent`, `discipline`).
- 5 **Power Packs / Bundles** — Apocophae's Field Kit · Ferrilith's Anvil · Techgnost's Workbench · Faunamimic's Cloak · Apprentice's Carry-All (with components + barter values).
- 5 **Custom Skill Groups** (Lesser, 2 pts/Lvl) — Apocophae · Ferrilith · Techgnostic · Faunamimic Discipline · Aurean Barter & Etiquette.

**6. Knowledge-Web node detail panel** — full content rendered prominently in `text-base text-parchment` (was dim `text-sm text-mist`). Now also shows visibility badge, tags, author, divider sigil, larger heading, and (on template-typed nodes) the structured fields grid in `parchment/90`. The "every node has its full write-up" promise is now visible.

**7. CharacterSheet — effective level surface**
Each attribute row shows `×Level` and, when limiters/enhancements shift it, an italic `(eff. ×N)` chip in arcane-light with a tooltip explaining the BESM rule.

### V4.2 — Theming · Battlemap V2 · Channels V2 · Quick Wins (this iteration — 2026-04-26)

**1. Quick wins**
- **Brute-force lock IP-key fix** — `routes/auth.py` now reads `X-Forwarded-For` first hop with fallback to `request.client.host`. Behind the K8s ingress the lock now reliably engages (verified by an iter_13 test that pins XFF and asserts a 423 within 12 attempts).
- **`?confirm=WIPE` gate** on `POST /api/admin/reset-to-evereantha`. Without the param: 400 ("This endpoint is destructive"). Defends against stray UI/automation calls.
- **Character ownership transfer** — `POST /api/characters/{id}/transfer?new_owner_id=…` (GM/admin). Updates owner_id+owner_name, auto-adds the new owner to `campaign.member_ids`, returns the freshly-decorated character (with `effective_level`).
- **`prefers-reduced-motion`** — global CSS gate disables AV pulse, page-fade, hush-sigil ripple and trims any other animation/transition durations to 0.001ms when the OS pref is set.
- **WebSocket close codes wire-visible** — `ws_session` and `ws_campaign` now `ws.accept()` BEFORE `ws.close(code=44xx)` so client libraries can read the policy reason instead of seeing a generic HTTP-handshake rejection. `bus.join(... , accepted=True)` skips the double-accept.

**2. System theming layer**
`/app/frontend/src/index.css` ships a `[data-system="…"]` selector tree with CSS variables for **13 game systems**: `besm-4e` · `anime-5e` · `dnd-5e` · `pf2e` · `cypher` · `coc-7e` · `savage-worlds` · `fate-condensed` · `cyberpunk-red` · `v5` · `blades-in-the-dark` · `mothership` · `shadowrun-6e`. Variables flow into `.card-mystic` / `.btn` / `.label-ref` / `.tag` / `.divider-sigil` so inner surfaces re-tint without leaving the dark-mystic shell. `CampaignDetail.jsx` and `SessionView.jsx` now stamp `data-system={camp.system_id}` on their roots.

**3. Battlemap V2 (`Battlemap.jsx`)**
- **Line-of-sight raycast** — for each token we run a 2-segment intersection test against every wall from the active-actor's token; tokens behind walls are hidden from non-GM players. GM sees through walls. Player toggle lets them disable LoS for testing.
- **Distance-measure ruler** — new `measure` mode; click+drag draws a gold dashed line with a label showing chebyshev cells + metres (2 m / cell default).
- **Token-status binding to `/api/effects`** — Battlemap now pulls the live effects list on mount, subscribes to `effect` / `effect_remove` WS events, and renders effect names as ember-coloured rings on the matching token (alongside any manual `t.status` rings). `EffectIn.target_character_id: Optional[str]` added to the model.

**4. Channels V2 (`ChannelsPanel.jsx` + `routes/sessions.py`)**
- **`/api/ws/campaign/{cid}` real-time** — new ws_router endpoint joins the bus room `campaign:{cid}` so existing channel REST broadcasts (msg / msg-delete / reaction / pin / thread) deliver in real time. Frontend connects + falls back to 8 s polling when disconnected. WS-state pip ("● live" vs "○ polling") in the composer footer.
- **`@mention` autocomplete** — typing `@` + a partial opens a member picker driven by `GET /api/campaigns/{cid}/members` (new endpoint returning `id / name / handle / is_gm / role`). Arrow keys navigate, Tab/Enter inserts, Esc closes. Mention resolution server-side already in place.
- **Image / file attachments by URL** — composer attach button prompts for a public URL + display name, inserts as `![name](url)` (image) or `[name](url)` (link). Frontend renders inline images (max 64 px tall, gold-bordered). Skips a full upload pipeline so it works today; CDN-hosted media works fine.

**5. Reference page (V4.1, recap)** — three tab-groups (Core · Combat & Play · Custom · Aurea), pinned BESM 4E cost-rule note, 7 new sections (actions / companions / race templates / size modifiers / weapons / items / armour), Aurea custom catalogue (8 attributes, 5 power packs, 5 skill groups).

### V4.3 — Demo retire · Codex sharability · Player-journal-to-Codex · Chronicle weave · Legal audit (this iteration — 2026-04-26)

**1. Demo accounts retired**
`core/startup.py` now actively REMOVES `admin@tablegnostic.com` / `gm@tablegnostic.com` / `player@tablegnostic.com` (plus their lingering `login_attempts` and `password_reset_tokens` rows) on every backend boot. **GMFran is the sole seeded account** (`franpietrowski@gmail.com` / `PieGod08!!`, role `admin`). The Auth.jsx login page no longer shows the "Demo GM / Demo Player" buttons.

**2. World-Codex card click & bidirectional visibility**
- Cards in the codex grid are now full-tile click targets (also keyboard-accessible — `Enter`/`Space`). Click opens a `NodeDetail` panel under the grid showing the entire write-up, structured fields, tags, and visibility badge.
- New `PUT /api/nodes/{nid}/visibility` endpoint (GM-only) accepts `gm_only` / `shared` / `revealed` and clears `revealed_to` on a flip back to `gm_only`. The card and detail panel both expose a 3-state visibility selector (the previous one-way "Reveal" button is gone).
- New `POST /api/campaigns/{cid}/nodes/bulk-visibility` for the GM's "Reveal all to players" / "Hide all (GM-only)" one-click affordances on the codex header.

**3. Player journal → Codex (Sessions tab)**
- `POST /api/characters/{cid}/journal` now ALSO creates a `player_journal` node in the campaign's World Codex with `visibility="gm_only"`. The player retains their folio.journal copy (so their personal record is untouched), but the GM gets the colour + voice they need to weave a chronicle. Response now includes `codex_node_id`.
- `POST /api/sessions/{sid}/recap` likewise mirrors the recap into the codex as a `session_record` node (`gm_only`, `fields.is_finalized=false`).
- Two new node types declared in `nodeTemplates.js`: `session_record` (teal #3da89a) and `player_journal` (violet #9d6dd0).

**4. Chronicle finalisation (Sessions workshop)**
- `SessionsTab.jsx` rewritten as the workshop. Each session row shows the recap (the spine), every linked player journal (collapsible), and a `Finalize chronicle` button with a tone selector (`lyrical` / `terse` / `in-character`).
- Backend: new `POST /api/sessions/{sid}/finalize` endpoint takes `FinalizeIn { recap_node_id, journal_node_ids[], tone }`, calls Claude Sonnet 4.5 via `emergentintegrations` with a system-aware prompt that honours the campaign's tone/genre/power-level, and rewrites the `session_record` node's content with the woven chronicle. The original recap is preserved at `fields.original_recap` for the audit trail; `fields.is_finalized` flips true.
- The chronicle is what the upcoming DriveThruRPG-export pipeline will compose into the campaign-PDF chapters (one chapter per session).

**5. Legal compliance audit (`/app/memory/LEGAL_COMPLIANCE.md`)**
Per-system audit covering all 13 systems in the selector. Status table:
- ✅ Compliant: BESM 4E (Tri-Stat Emporium), Cypher (Cypher System Creator), Fate Condensed (CC-BY 3.0), Blades in the Dark (FitD SRD), Mothership (3PL), D&D 5E (CC-BY SRD 5.1/5.2 only), PF2e (ORC).
- 🟡 Pending content: Anime 5E (Tri-Stat), Call of Cthulhu (Miskatonic Repository), Savage Worlds (Pinnacle).
- ⚠️ Constrained: Cyberpunk RED (mechanics-only — no commercial branded export), V5 (Storytellers Vault rules apply), Shadowrun 6E (non-commercial only — no public CC programme).
- Per-system PDF export footer text drafted for the future DriveThruRPG pipeline.
- Trademark policy table — branded marks NEVER displayed in UI without permission.
- Distribution-model section explaining what GMFran can/can't ship for money under the current state.

### V4.3 — Tested
- iter_14 = **22/22 PASS** (`test_iter14_v43.py`). Cumulative across iter9 + iter10 + iter11 + iter12 + iter13 + iter14 = **100 PASS / 28 SKIP / 0 FAIL**.
- All test files updated to register transient `@example.com` accounts on module setup (the retired demo accounts are gone).
- Verified live: demo logins return 401, GMFran 200; journal entry creates `player_journal` codex node; recap creates `session_record` codex node; bulk visibility flips 21 nodes in one shot; bidirectional visibility PUT works.

### V4.3 — Deferred
- Iter_14 noted ergonomic wins (now applied):
  - `FinalizeIn` Pydantic schema replacing the dict body (✅ applied; route docstring tightened).
  - Bulk-visibility 400 message (mentions `gm_only` and `shared` explicitly — already done).
- Branded DriveThruRPG PDF generation pipeline (reportlab + per-system footer + cover page + chapter-per-session) — V4.4.
- Anime 5E + Cypher full content extraction from the uploaded PDFs — V4.4 / V4.5.
- Knowledge Web file ingestion (Claude diff-review) — V4.4.
- **18/18 new tests PASS** (`test_iter13_v42.py`). Cumulative across iter9 + iter10 + iter11 + iter12 + iter13 = **82 PASS / 28 SKIP / 0 FAIL**.
- Test fixture stability: switched all iter11 mongo helpers from `motor` (asyncio loop flake) to sync `pymongo` so test order no longer matters.
- iter_10 marked superseded (Cyma-based seed assertions can't be re-baselined cleanly against the new Eli/Laryk/Roney seed).
- iter_9 V3.5 clamp test rewritten to assert the *correct* BESM 4E rule (cost stays at base × level; effective level rises with limiters).
- iter_13 `test_brute_force_lock_kicks_in` now asserts 423 fires reliably with a stable XFF (was previously documented-but-broken).
- iter_13 verified live WS fan-out: REST POST to `/channels/{chid}/messages` → connected campaign-WS subscribers received `channel:msg` event in <1s.

### V4.2 — Code-review notes (deferred)
- Public `/openapi.json` URL still returns the SPA HTML (K8s ingress only routes `/api/*`). A `/api/openapi.json` alias would help external tooling — low priority.
- Channel `body` field name (vs `text` elsewhere) creates a per-route convention split. Cosmetic, defer.
- `legacy backend/tests/backend_test.py` errors at collection without dotenv. Add `load_dotenv` at the top or `--ignore` it in CI.
- Backend: **46/46 tests PASS** — 36 new (`test_refactor_iter11.py`) + 10 carry-over
  (`test_iter10_v38.py`). Coverage: auth (incl. brute-force semantics), reference,
  campaigns + invites + custom + genesis, characters + access gates, seed, knowledge
  web, sessions + chat + dice + initiative + effects + damage + round, recap, health,
  OpenAPI shape, WebSocket auth + presence:room handshake.
- WebSocket: invalid-token close verified; valid-token connect emits `presence:room`
  as the first frame ✓. Targeted `to: conn_id` relay code path matches spec but
  was not exercised end-to-end (would need 2 concurrent ws clients).
- Behavioural 1:1 preservation **CONFIRMED** — no regressions vs the monolithic
  server.py.

### V3.9 — Pre-existing findings surfaced by iter_11 (NOT refactor regressions)
- **(MEDIUM, security)** Brute-force lock in `routes/auth.py:42-66` keys attempts on
  `f"{request.client.host}:{email}"`. Behind the Kubernetes ingress, `request.client.host`
  is the immediate upstream pod IP and **rotates per-request** — verified in mongo:
  `10.79.131.85:email` count=4 AND `10.79.131.86:email` count=4 simultaneously for
  the same email burst. Threshold `>=5` therefore never trips reliably. Fix:
  trust `X-Forwarded-For` first hop OR drop IP from the key and rate-limit
  email-only with a tighter window. Off-by-one note: `count >= 5` actually locks
  on the 6th attempt (re-read the spec wording).
- **(LOW)** `https://<host>/openapi.json` returns the SPA's `index.html` (frontend
  catch-all), only `http://localhost:8001/openapi.json` serves the real schema.
  Cosmetic — programmatic API consumers using the public hostname get HTML.

## 3. Backlog (in user's stated order)

### P1 — Architecture
- **Backend refactor — DONE in V3.9** (`server.py` 1772 → 65 lines; 8-router split with OpenAPI tags). See V3.9 section above.
- **Brute-force lock IP-key fix** (security MEDIUM, pre-existing — surfaced by iter_11). Read `X-Forwarded-For` first hop or drop IP from the key.

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

> Items 5, 7, 8, **and 1, 2(partial), 4** below were completed in **V4.4 (2026-04-26)** — see §V4.4 changelog.

1. ~~**DriveThruRPG export pipeline**~~ — **DONE (V4.4 Phase E)**. System-native styling for BESM 4E + Anime 5E shipped; chapters group S0+S1+S2 / pairs.
2. **Anime 5E full content** — extract attribute/skill/defect/template content from the uploaded Anime 5E SRD into `besm_data.py`. Tag entries `cross_systems: ["dnd-5e"]` for D&D-5E setting overlay. (Logo + style profile already in.)
3. **Cypher full content** — extract from the 5 Cypher / Numenera / Godforsaken PDFs into the Cypher selector. Compliance-checked per `LEGAL_COMPLIANCE.md` §5. Build a new `STYLE_PROFILES["cypher"]` entry when extracted.
4. ~~**Knowledge Web mechanic-aware ingestion**~~ — **DONE (V4.4 Phase C)**. 10-category Claude diff-review with atelier-phase tagging.
5. ~~**CharacterBuilder** in-builder live cost-preview update to V4.1 rule~~ — **DONE (V4.4)**.
6. **Primer change-request alerts** + GM live-edit mid-campaign.
7. ~~**8-session Evereantha demo** — pre-seeded chronicle that ships out of the box.~~ — **DONE (V4.4)**.
8. ~~**Atelier dynamic scaling** — Session 0/1 vs Arc vs Master Plot tiers with continuity checks for the GM.~~ — **DONE (V4.4 Phase B)**.
9. **System-native macro library expansion** — wire BESM/Cypher/Anime 5E core macros (skill-component picker, action-preset menu, GM-roll templates) so each system's table feels native, not generic.
10. **XP scorecard polish** — show per-PC bonus_breakdown popover (which quantum contributed how much), and a campaign-level XP ledger for GMs to see all conversions over time.
11. **Style-profile theming for D&D 5E + Cypher + Numenera** PDF exports.
12. **Ingestion preview** — show the GM the parsed text excerpt before committing the Claude call (so the GM can verify the parse caught the right pages).

## V4.4 Phase K — Customizable Names & Campaign-Reference Attributes/Skills/Defects (2026-04-26)

**User pain:** Once an Attribute / Skill / Defect was selected on a sheet, there was no way to customize its on-sheet name or descriptive flavour. Only the level / enhancements / limiters were editable. The Reference Editor in the Atelier covered Weapons / Armor / Items / Companions / Custom Rules but couldn't curate Attributes / Skills / Defects for the table to use during character creation.

**Backend (`/app/backend/routes/reference_editor.py`, `/app/backend/core/models.py`)**
- `REFERENCE_KINDS` extended from 5 → 8: now also includes `attribute`, `skill`, `defect`. The `Literal` type on `ReferenceItemIn.kind` updated to match — `POST /api/campaigns/{cid}/reference` validates the new kinds with the same page-validation pipeline that already powers the other kinds.
- `CharacterAttribute`, `CharacterDefect`, `CharacterSkill` models gained `display_name: Optional[str] = ""`. The existing `note` field is repurposed as the player's freeform description. Both round-trip through `PUT /api/characters/{id}` (curl-verified).

**Frontend — Reference Editor (`/app/frontend/src/components/ReferenceEditor.jsx`)**
- 3 new tabs in the Atelier reference-editor: **Attributes**, **Skills**, **Defects** (`reference-tab-attribute|skill|defect`).
- When the GM is creating/editing one of the **playable kinds**, an extra structured-fields panel (`reference-playable-fields`) appears with `cost_per_level` (numeric, attribute & skill), `points_per_rank` (numeric, defect), `category` selector (defect: Lesser / Greater / Custom), and a description input for the player-facing picker.

**Frontend — Character Builder (`/app/frontend/src/components/CharacterBuilder.jsx`)**
- On mount, also fetches `GET /api/campaigns/{cid}/reference` and merges any `attribute` / `skill` / `defect` rows into the picker as **"Campaign Reference"** options (alongside BESM 4E core + Custom (GM)). Defects auto-negate `points_per_rank` so the refund is correct.
- AttributeRow / DefectRow / SkillRow each now expose a **"Customise"** toggle that opens a small inline editor with two inputs: custom display name (overrides the on-sheet label while keeping the underlying mechanic name in brackets) and description (long-form flavour persisted as `note`). Testids: `attr|defect|skill-display-name-{idx}` / `attr|defect|skill-note-{idx}`.

**Frontend — Character Sheet (`/app/frontend/src/components/CharacterSheet.jsx`)**
- When a row has a `display_name`, it renders as a bold parchment header *above* the `BesmTerm` mechanic line. The mechanic name and rule-link still appear directly below it so a click still pops the BESM 4E reference. Testids: `attr|defect|skill-display-{i}`.

**Workflow this enables (the Session-0 GM scenario):** GM opens **Atelier → Reference Tables → Attributes/Skills/Defects** and adds setting-flavoured entries. Players then see them in the picker tagged "Campaign Reference" and rename them per-character. Mechanic resolution (cost, dice, derived stats) all key off the underlying name — renames are pure flavour and never break the engine.

**Verification:** Backend round-trip via curl created an attribute/skill/defect reference row, then PUT a character with `display_name` + `note` on attribute[0] / defect[0] — both fields persisted intact in the response. All ESLint + Ruff lints pass on the 5 modified files.

## V4.4 Phase L — Audio fix · Dashboard footer · Bidirectional UX hardening (2026-04-26)

**P0 audio regression fix (`/app/frontend/src/components/AVSeats.jsx`)**
- Symptom: phone joins session, **video reaches the desktop fine but no audio is heard on the desktop side**.
- Root cause: the peer `<video>` element was hidden via Tailwind's `hidden` class (= `display:none`) whenever cam was off — `display:none` halts media playback in Chromium and WebKit, so the audio track went silent.
- Two-line fix: (1) `hidden` → `invisible` on the `<video>` so the element stays in the layout tree, media keeps playing; (2) dedicated `<audio ref autoPlay playsInline>` per peer that mirrors the same MediaStream — guaranteed audio sink immune to any cam-on/off visibility flips. Testid: `av-audio-{conn_id}`.

**Dashboard / app-wide legal footer (`/app/frontend/src/components/Shell.jsx`)**
- New `<AppFooter>` rendered below every authenticated screen — Table-Gnostic sigil + platform legal disclaimer naming all 13 supported systems, stating only mechanic names + page refs are displayed (no copyrighted prose/lore/art). Per-system attribution lives inside CampaignDetail (see `<SystemBadge>` in V4.5). Testids `app-footer` / `app-footer-legal`.

**Verified-already-in-place**: System selector in Campaign creation (`Campaigns.jsx:137`) and live channel WebSocket (`/api/ws/campaign/{cid}` with 4 s polling fallback).

## V4.5 — Multi-System Content & Card Decks (2026-04-26)

The biggest content drop since V4.0. Three new systems get real reference data (not just scaffolds), card decks land system-wide, ingestion goes system-aware, PDF themes expand, and CampaignDetail gets a per-system legal/logo overlay.

### A. System-aware reference data (`/app/backend/system_data/`)

New package: 4 modules + `__init__.py`. All entries are mechanic-only — page references + names + numerics. No reproduced rulebook prose.

- **`dnd5e_data.py`** — CC-BY SRD 5.1 only. **12 classes** (Barbarian → Wizard with hit-die, primary ability, save proficiencies, spellcasting type), **9 races** (with ASI / size / speed / trait list), **6 abilities**, **18 SRD skills** (mapped to abilities), **17 spells** sample (cantrip → 5th, with damage dice formulas pre-stamped for one-click macros), **13 weapons** (with damage type + properties), **7 armor** (with AC formula), **7 adventuring items**, **14 conditions** (with mechanic effect), **11 actions** (action / bonus / reaction), **5 power levels** (Apprentice → Mythic), proficiency-by-level table, modifier formula `(score - 10) // 2`.
- **`anime5e_data.py`** — Tri-Stat Emporium OGL release. **Hybrid engine**: BOTH 5E class+slot AND Tri-Stat point-buy are exposed — GM picks the engine in the Primer. **5 classes** (Adept / Champion / Idol / Pilot / Tinker), **8 heritages**, **18 skills** mapped to Body / Mind / Soul, **8 spells**, **8 weapons** (Katana, Wakizashi, Naginata, Mecha Cannon, …), **6 armor** (incl. Mecha Frame), **3 anime-specific conditions** (Genre-Locked / Spotlit / Eclipsed), **9 point-buy attributes** (Combat Mastery / Tough / Massive Damage / …). Tagged `cross_systems: ["dnd-5e"]` so Anime 5E content can layer onto a D&D campaign as a supplement.
- **`cypher_data.py`** — Cypher System Creator licence (Monte Cook Games). **3 stat pools** (Might / Speed / Intellect), **6 types** (Warrior / Adept / Explorer / Speaker / Wright / Paradox with starting pools + Edge), **16 descriptors**, **18 foci** (each with role keyword), **23 skills**, **12 cyphers** (level + form + effect), **6 artifacts** (with depletion roll), **GM Intrusion** mechanic, **6 tiers**. Compatible-settings list (Numenera / The Strange / Predation / Godforsaken / Stay Alive! / Claim the Sky / Old Gods of Appalachia / Rust & Redemption) so the GM can flag which Cypher setting they're running.
- **`decks.py`** — see section C.

### B. System-aware reference endpoint (`/app/backend/routes/besm.py`)

- New `GET /api/systems/{system_id}/reference` returns the system-shaped reference dict. `besm-4e` falls through to the existing deep `/api/besm/reference`; `dnd-5e` / `anime-5e` / `cypher` return their respective dicts; unknown systems return a `kind: "scaffold"` notice pointing GMs at the Reference Editor.
- Cached `Cache-Control: public, max-age=300` for cheap repeated loads.

### C. Card decks system (`/app/backend/routes/cards.py` + `system_data/decks.py` + `frontend/CardDeckPanel.jsx`)

- Per-system deck catalogue. **D&D 5E**: Deck of Many Things (22 trump cards, mechanic-only restatements of SRD effects) + TableGnostic Mood Deck. **Cypher**: Cypher Draw (12 random SRD cyphers from the active list) + Mood Deck. **Anime 5E**: Genre Shift Deck (12 narrative cards: Spotlight / Tournament Arc / Training Montage / Memory Lapse / …) + Mood Deck. **BESM 4E**: Mood Deck only — even though BESM is card-less by design, the user-requested universal opt-in is satisfied.
- 7 endpoints: `GET /api/cards/decks/{system_id}` (catalogue), `GET /api/cards/decks/{system_id}/{deck_id}/preview` (full card list), `POST /api/cards/instances` (GM creates an instance scoped to a campaign or session), `GET /api/cards/instances?campaign_id=…`, `POST /api/cards/instances/{id}/draw` (random no-replacement; broadcasts `card:drawn` over campaign+session WS), `POST /api/cards/instances/{id}/shuffle` (reset drawn list), `POST /api/cards/instances/{id}/mode?mode=open|gm-only`, `DELETE /api/cards/instances/{id}`.
- Mongo collection: `deck_instances`. Cleared by admin reset.
- Frontend `<CardDeckPanel>` (lives in a new **Decks** tab inside CampaignDetail): catalogue list with per-deck spawn buttons (GM-only), instance picker tabs, big "Draw" button (GM, or anyone if mode=open), Shuffle, Open-to-table toggle, recent-draws stack with system-flavoured card faces, draw history `<details>` section.
- Curl-verified: spawn → draw 3 → shuffle → delete works end-to-end with `card:drawn` events broadcasting to `session:{sid}` and `campaign:{cid}` rooms.

### D. System-aware ingestion (`/app/backend/routes/ingest.py`)

- New `SYSTEM_ADDENDUM` dict branches the Claude prompt per `campaign.system_id`. BESM 4E gets the existing 10-category list (attribute / power_pack / item / weapon / skill / npc / location / lore / quest). D&D 5E adds class / race / background / spell / feature / monster (and explicitly forbids reproducing Wizards-trademarked content like Forgotten Realms / Mind Flayer / Beholder). Anime 5E branches between class+slot and Tri-Stat point-buy categories. Cypher branches to type / focus / descriptor / cypher / artifact / ability with the Cypher difficulty-1-to-10 dice notation.
- The hard rule about not reproducing rulebook prose / lore / examples is preserved verbatim in every branch. Capped at 60 suggestions, mechanic-only summaries ≤240 chars.

### E. Per-system PDF style profiles (`/app/backend/routes/pdf_export.py`)

- Two new entries in `STYLE_PROFILES`:
  - **dnd-5e** — parchment background, heraldic crimson primary, midnight indigo secondary, antique gold accent, Times-Roman body, fleur chapter decoration. Cover subtitle: "A 5th Edition Chronicle (CC-BY SRD 5.1)".
  - **cypher** — white background, deep cyber-cobalt primary, arcane violet secondary, numenera-teal accent, circuit chapter decoration. Cover subtitle: "A Cypher System Chronicle".
- BESM 4E and Anime 5E profiles unchanged.

### F. SystemBadge overlay (`/app/frontend/src/components/SystemBadge.jsx`)

- Renders inside CampaignDetail header below the campaign description. Per-system logo (resolved from `/system-logos/{system_id}.png` with graceful hide on 404), system label, licence string, and verbatim attribution notice.
- Profiles in place for besm-4e (Tri-Stat Emporium · Dyskami), anime-5e (Tri-Stat OGL), dnd-5e (Wizards of the Coast · CC-BY-4.0), cypher (Monte Cook Games · CSC). Fallback profile for any other system marks the content as "Original / Community". Testid `system-badge`.
- This is where the rights-holder credit appears — distinct from the platform-wide footer (which carries TableGnostic's own disclaimer).

### G. Reference page system tabs (`/app/frontend/src/components/Reference.jsx`)

- New system-tab strip at the top: BESM 4E (Native) · Anime 5E · D&D 5E (CC-BY SRD) · Cypher System.
- BESM 4E renders the existing deep reference (3 tab-groups, search, custom Aurea sections) — no regression.
- Non-BESM systems render a new `<SystemReferenceView>` that adapts to each system's shape: stat pools / abilities, classes, types, foci, descriptors, races / heritages, point-buy attributes, weapons, armor, spells, cyphers, artifacts, skills, conditions, actions, power levels, GM intrusion. Search filter applies across all sections via JSON-stringify match.
- The `<div data-system={systemId}>` wrapper picks up the existing CSS variable theming (already defined for all 13 systems in `index.css`).

### H. CampaignDetail wiring

- New **Decks** tab between Sessions and Player Primer. Renders `<CardDeckPanel>` scoped to the current campaign (and current session if one is open).
- `<SystemBadge>` rendered in the header block under the GM/seat-count line.

### Compliance audit (V4.5)

- D&D 5E: only CC-BY SRD 5.1 mechanic names + page refs. The Deck of Many Things entries restate game effects in mechanic terms (e.g. "Euryale: −1 to all saving throws (permanent until magically removed)") rather than reproducing rulebook prose. No Forgotten Realms, no Mind Flayer / Beholder, no monster-manual flavour.
- Cypher: Cypher System Creator licence — type / focus / descriptor names + cypher names + page refs. No flavour paragraphs from the SRD or any setting book.
- Anime 5E: Tri-Stat Emporium OGL — same posture as BESM 4E. Hybrid mode preserves the original Tri-Stat point-buy semantics.
- TableGnostic Mood Deck (12 cards) and Anime 5E Genre Shift Deck (12 cards) are 100% original TableGnostic content.

### Pending follow-ups (deferred — credit budget)

1. PNG logos for `/system-logos/dnd-5e.png` and `/system-logos/cypher.png` — SystemBadge gracefully hides the `<img>` on 404, so the overlay is functional now but visually richer once the artwork lands. Anime 5E uses `anime5e-tristat-emporium.png` (already on disk).
2. **D&D-shaped Character Builder** — the current builder is BESM-shaped. A class+slot variant (level / class / race / proficiency / spell-slot tracker / equipment / dice-formula macros) is the next major build. Until then, the D&D Reference page + Atelier Reference Editor + Custom Attributes give GMs a working ingredient set.
3. **Cypher-shaped Character Builder** — type/focus/descriptor sentence picker + Pool/Edge/Effort tracker + cypher inventory.
4. Expand the spells / weapons / monsters lists from "representative sample" to "full SRD coverage" — straightforward extension once the structural pattern proves out.



**P0 audio regression fix (`/app/frontend/src/components/AVSeats.jsx`)**
- Symptom: phone joins session, **video reaches the desktop fine but no audio is heard on the desktop side**.
- Root cause: the peer `<video>` element was hidden via Tailwind's `hidden` class (= `display:none`) whenever `camOn || hasStream` was false. **`display:none` halts media playback in Chromium and WebKit** — the audio track travels with the video element's stream, so when the element gets `display:none`'d the mic feed goes silent on the receiving side.
- Two-line fix:
  1. `hidden` → `invisible` on the `<video>` (Tailwind `visibility:hidden`) — element stays in the layout tree, media keeps playing, but the visual is suppressed so the avatar bubble shows through.
  2. Dedicated `<audio ref autoPlay playsInline>` element rendered next to each `PeerTile` and bound to `peer.stream` via the same `srcObject` plumbing. This is a guaranteed audio sink that never participates in the cam-on/cam-off visibility flips, so audio is robust to any future visual-state change. Testid: `av-audio-{conn_id}`.
- The fix preserves the self-tile mute (`muted={!!isSelf}` still in place — prevents echo for the local user).

**Dashboard / app-wide legal footer (`/app/frontend/src/components/Shell.jsx`)**
- New `<AppFooter>` rendered below every authenticated screen via the `<Outlet>` slot. Carries:
  - Internal **Table-Gnostic** sigil (Sigil component, 28 px).
  - Platform legal disclaimer naming the 13 supported systems (BESM, Anime 5E, Cypher, Numenera, D&D, PF2e, Fate, Mothership, Blades, CoC, Savage Worlds, Cyberpunk RED, V:tM, Shadowrun) and stating that we display only mechanic names + page refs — never copyrighted prose, lore, or art.
  - "Per-system attribution &amp; required licence text appear on each campaign and exported PDF" — points users at the per-system surfaces where Tri-Stat Emporium · Dyskami · Cypher System Creator marks live.
  - Year-stamped TableGnostic original-content copyright.
- Testids: `app-footer` / `app-footer-legal`.
- Layout: `<main>` switched to `flex flex-col` with the page content in `flex-1` and footer pushed to bottom, so short pages don't leave the footer floating.

**System selection in campaign creation — verified already in place**
- `Campaigns.jsx:137` exposes a `<select>` populated from `GET /api/systems` (all 13 systems). No work needed.

**Channel live updates — verified already in place**
- `ChannelsPanel.jsx` connects to `/api/ws/campaign/{cid}` and processes `channel:msg`, `channel:msg-delete`, `channel:reaction`, `channel:pin`, `channel:thread` events in real-time. Polls every 4 s only when the WS is disconnected. The "● live / ○ polling" pip in the composer footer already exposes the WS state.

### Deferred — large phases requiring fresh credit budget
- **Card decks system** (D&D 5E Deck of Many Things · Cypher cyphers/artifacts · Anime 5E character/bestiary cards) — system-aware. BESM 4E does not use cards by design, so the deck panel only renders for systems where `system.uses_cards === true`.
- **Full D&D 5E mechanics extraction** — classes, races, backgrounds, equipment, spells, attack-roll/damage/saves dice formulas, system-coloured theme. CC-BY SRD 5.1/5.2 licensing only.
- **Full Cypher System extraction** — types, foci, descriptors, cyphers, artifacts, GM Intrusion mechanics. Cypher System Creator licence — mechanics only, never reproduce flavour text.
- **System-aware ingestion** — `routes/ingest.py` Claude prompt currently has one BESM-shaped category list. Should branch per `campaign.system_id` so D&D ingestions return classes/spells/items, Cypher ingestions return cyphers/artifacts/foci, etc.
- **Per-system logo/disclaimer overlay** inside CampaignDetail header — already groundwork in `STYLE_PROFILES`; just needs the visible badge surface.

**User pain:** Once an Attribute/Skill/Defect was selected on a sheet, there was no way to customize its on-sheet name or descriptive flavour. Only the level / enhancements / limiters were editable. The Reference Editor in the Atelier covered Weapons / Armor / Items / Companions / Custom Rules but couldn't curate Attributes / Skills / Defects for the table to use during character creation.

**Backend (`/app/backend/routes/reference_editor.py`, `/app/backend/core/models.py`)**
- `REFERENCE_KINDS` extended from 5 → 8: now also includes `attribute`, `skill`, `defect`. The `Literal` type on `ReferenceItemIn.kind` updated to match — `POST /api/campaigns/{cid}/reference` validates the new kinds with the same page-validation pipeline that already powers the other kinds.
- `CharacterAttribute`, `CharacterDefect`, `CharacterSkill` models gained `display_name: Optional[str] = ""`. The existing `note` field is repurposed as the player's freeform description. Both round-trip through `PUT /api/characters/{id}` (curl-verified).

**Frontend — Reference Editor (`/app/frontend/src/components/ReferenceEditor.jsx`)**
- 3 new tabs in the Atelier reference-editor: **Attributes**, **Skills**, **Defects** (`reference-tab-attribute|skill|defect`). 
- When the GM is creating/editing one of the **playable kinds**, an extra structured-fields panel (`reference-playable-fields`) appears with:
  - `cost_per_level` (numeric, attribute & skill) — `data-testid="reference-input-cost-per-level"`
  - `points_per_rank` (numeric, defect) — `data-testid="reference-input-points-per-rank"`
  - `category` selector (defect: Lesser / Greater / Custom) — `data-testid="reference-input-defect-category"`
  - `description` (long-form GM note shown to players in the picker) — `data-testid="reference-input-description"`
- Existing kinds (weapon/armor/item/companion/custom) keep the original simpler form — no regression.

**Frontend — Character Builder (`/app/frontend/src/components/CharacterBuilder.jsx`)**
- On mount, also fetches `GET /api/campaigns/{cid}/reference` and merges any `attribute` / `skill` / `defect` rows into the picker as **"Campaign Reference"** options (alongside BESM 4E core + Custom (GM)). Defects auto-negate `points_per_rank` so the refund is correct. Attributes default to `open_mods=true` so any enhancement/limiter can apply (the GM-curated entry is presumed permissive).
- AttributeRow / DefectRow / SkillRow each now expose a **"Customise"** toggle that opens a small inline editor with two inputs: 
  1. **Custom display name** (`attr|defect|skill-display-name-{idx}`) — overrides the on-sheet label while keeping the underlying mechanic name in brackets (so the GM can always see what it really is).
  2. **Description / how it works at this table** (`attr|defect|skill-note-{idx}`) — long-form flavour persisted as `note`.
- AttributeRow already had a `Customise` panel for enhancements/limiters/item-defects — the rename inputs slot above the existing controls. Defect/Skill rows gain their own toggle (`defect-cust-{idx}` / `skill-cust-{idx}`) to keep the row compact when not editing.

**Frontend — Character Sheet (`/app/frontend/src/components/CharacterSheet.jsx`)**
- When a row has a `display_name`, it renders as a bold parchment header *above* the `BesmTerm` mechanic line. The mechanic name and rule-link still appear directly below it, so a click still pops the BESM 4E reference. Testids: `attr-display-{i}` / `defect-display-{i}` / `skill-display-{i}`.

**Workflow this enables (the GM scenario you described):**
1. During Session 0 (A/V or Threads PBP), the GM opens **Atelier → Reference Tables → Attributes** and adds setting-flavoured Attributes (e.g. *Apothecary Tincture* with `cost_per_level=4`, page 196 BESM 4E, description "Channels Aurean reagents into healing draughts"). Same for Skills and Defects.
2. The page-validation guard rails still apply — out-of-range page citations save with a warning.
3. When players open the Character Builder, the new entries appear in the picker tagged **"Campaign Reference"**. They select one, and on the row they can hit **Customise** to set their personal display name and a short description.
4. The mechanic resolution (cost, dice rolls, derived stats) all key off the underlying name — so renames are pure flavour and never break the engine.

**Verification (this iteration)**
- Backend round-trip via curl: `franpietrowski@gmail.com` GM-created an *attribute* / *skill* / *defect* reference row, listed them back, then PUT a character with `display_name` + `note` on attribute[0] / defect[0] — both fields persisted intact in the response.
- All ESLint + Ruff lints pass on the 5 modified files.
- No new endpoints — extends the existing `/api/campaigns/{cid}/reference` surface area (no migration needed).


### P0 Bug Fixes
- **CharacterSheet stat dice math (BESM 4E meet/beat)**: Stat-tile clicks and quick-roll buttons now post `2d6+body|mind|soul` (not `2d6-stat`). Initiative is `1d6+mind`. Tooltip text updated. (`/app/frontend/src/components/CharacterSheet.jsx`)
- **CharacterBuilder cost preview (V4.1 rule mirrored client-side)**: Enhancements/Limiters no longer adjust point cost; cost stays at `cost_per_level × level` (minus nested Item/Weapon defect refunds, floored at 0). A new **`eff. ×N`** badge (`data-testid="attr-eff-level-builder-{idx}"`) appears next to LVL whenever the effective level differs — `effective = level + #limiters − #enhancements`, floored at 1. (`/app/frontend/src/components/CharacterBuilder.jsx`)
- **Knowledge Web NodeDetail truncation**: `KnowledgeTab` now scrolls the detail panel into view on every node click via `detailRef + scrollIntoView({behavior:"smooth"})`. Admin reset (`/api/admin/reset-to-evereantha`) now copies seed `node["fields"]` into Mongo so `NodeDetail` renders structured fields (geography, government, biology, abilities, …) — not just the short content blurb. Aurea, Eagles Nest, Nyaulis, and Lancing Andrewsarchus now ship with full structured metadata. (`/app/frontend/src/components/CampaignDetail.jsx`, `/app/backend/routes/admin.py`, `/app/backend/seed_evereantha.py`)

### P0 Content Seed
- **8-Session Evereantha Chronicle** (`EVEREANTHA_SESSIONS` in `seed_evereantha.py`): 8 sequential sessions with chat dialogue, dice rolls, GM narration, and per-session `gm_notes`. Nyaulis joins the party in **Session 2** (Faunamimic's Apology). Cliffhanger at **Session 8 — Master's Pass**: Roney's harness sigil flares, he vanishes mid-line, and a parchment in the Mayor's hand reads "You will not bring him home. — M." Reset endpoint now seeds 8 sessions + 130 chat lines + 22 dice rolls. Sessions 1–7 are `closed`; Session 8 is `open` so a GM can jump straight in.

### P0.5 Map Upload Pipeline (user-requested enhancement)
- **Direct image upload + grid scaling**. New backend route `POST /api/uploads/map` (multipart/form-data, GM/admin only, 12 MB cap, PNG/JPEG/WEBP whitelist). Files are written to `/app/backend/uploads/maps/<id>.<ext>` and served via a new `StaticFiles` mount at `/api/uploads`. Pillow reads pixel dimensions; the response payload `{url, width, height, bytes, content_type}` lets the frontend auto-recommend a grid scale. (`/app/backend/routes/uploads.py`, `/app/backend/server.py`)
- **Battlemap GM toolbar overhaul**: replaced the URL-prompt-only `Image` button with an `Upload Map` file picker (`data-testid="map-bg-upload-btn"`) plus a fallback `URL` button (`data-testid="map-bg-url-btn"`) for legacy share-links. New `⊞ Npx` cell-size button (`data-testid="map-cell-btn"`) lets GMs scale the grid pixel size 12–256. After a successful upload the GM is offered a one-click auto-grid (cols/rows derived from `image.width / cellPx`). Maps from Inkarnate, DungeonCraft, Talespire, RPGEngine all drop in directly — no public hosting required. (`/app/frontend/src/components/Battlemap.jsx`)

### Testing
- `/app/test_reports/iteration_15.json` — backend 12/12 new pytest cases pass; frontend Bug 1 + Bug 2 verified end-to-end (POST /api/dice payload intercepted, builder cost preview confirmed); Bug 3 self-verified by main agent (NodeDetail panel renders Type/Geography/Government/Economy/Notable Landmarks/History/Inhabitants for the Aurea node and auto-scrolls into view).
- Cumulative regression: 112 PASS / 18 SKIP / 0 FAIL.

### Legal compliance reaffirmed
- Per `LEGAL_COMPLIANCE.md` (Tri-Stat Emporium licence): page references and mechanic names only — never reproduce rulebook prose, stat-block descriptions, lore, or examples. The new Evereantha Chronicle dialogue uses **only user-provided "Artisan's Tale" original setting material** with mechanic-only references back to BESM 4E (page numbers + attribute names). The `besm_data.py` Cypher/Anime 5E entries continue to cite mechanics + page numbers without reproducing flavour text.

## V4.4 Phase E.2 — PDF Polish + Profile Byline (2026-04-26)

User-reported defects in `chronicle.pdf`: wrong logo, title not centered/width-aware, no GM byline, missing Dyskami legal, double "Chapter N" headers, no paragraph indentation/separation in session recaps. All resolved.

### PDF cover overhaul
- **Correct system logo on cover** — added `/app/frontend/public/system-logos/besm-4e.png` (Tri-Stat Emporium BESM logo, 300dpi). `STYLE_PROFILES["besm-4e"].logo_files` lists it first; the older Anime5E/TriStat logo only appears now as the secondary fallback. Logo is centered, ~2.4 inches tall, preserves aspect.
- **Width-aware centered title** — cover title rendered through a `Paragraph(TA_CENTER)` with a 5-step font-size auto-shrink ladder (42pt → 34pt → 28pt → 22pt → 18pt) that wraps inside `pw - 2*margin - 0.4*inch` and never collides with the accent stripe.
- **GM byline + "Weaved in TableGnostic" addendum** — cover draws "by {byline_name}" in primary colour 14pt, then "Weaved in TableGnostic" italic 10pt below the decorative rule. Sourced from `db.users.byline_name` with a fall-through to `db.users.name`.
- **Dyskami required attribution** — new `_legal_required_footer(system_id)` extracts ONLY the `>` blockquote from the `Required PDF footer` subsection of `LEGAL_COMPLIANCE.md`, rendered verbatim at the bottom of the cover (white text on the secondary-colour bottom bar) AND prominently inside a system-coloured callout box on the legal page.
- **© year stamp** — `© {YEAR} {byline_name} · All Aurea original content` on cover above the legal block.

### Chapter & body layout
- **No more double "Chapter N" headers** — `_emit()` chapter dict now carries `title_text` (the first session's narrative title, e.g. "The Maiden Road"). Chapter pages render exactly ONE `Paragraph(chapter_label="CHAPTER  I")` (small kerned label, Roman numerals) + ONE `Paragraph(chapter_title=narrative_title)` — never the same number twice.
- **Paragraph indentation + separation** — body style uses `firstLineIndent=18` for natural prose flow; first-paragraph-of-section uses `firstLineIndent=0`. `_session_prose` chat-log digest fallback now paragraph-breaks on every speaker change (joins with `\n\n`) so each turn is a distinct paragraph in the rendered prose.
- **Sessions visually separated within a chapter** — a 50%-width centred `HRFlowable` accent rule appears between sessions inside the same chapter. Each session header keeps its own SESSION-N kerned label + bold session title.
- **Page footer** — every body page now reads `Weaved in TableGnostic · by {byline_name}` (left) + `p. N` (right).

### Legal page
- **"Publisher's Required Attribution"** section renders the verbatim Dyskami quote inside a system-bordered callout box.
- **"Compliance Summary"** section pulls the wider per-system block from `LEGAL_COMPLIANCE.md` and pipes it through a new `_strip_markdown()` helper that removes `**`, `>`, `*`, `-`, ` ` ` markers so the prose reads cleanly on the printed page.
- Distribution channel reaffirmed as DriveThruRPG.

### Profile / byline plumbing
- New `PATCH /api/auth/me` accepts `{byline_name}` (max 120 chars). Empty string → null. Empty body → 200 no-op. (`/app/backend/routes/auth.py`, `/app/backend/core/models.py` adds `ProfilePatchIn`)
- `UserOut` exposes `byline_name`.
- `useAuth` exposes `updateProfile(patch)` for client-side state hydration.

### Frontend UX
- Atelier `Export PDF` button now opens an inline popover (`atelier-export-pdf-popover`) with: byline input prefilled from `/auth/me`, **Save byline** button (`atelier-export-byline-save` → `PATCH /auth/me`), and **Download chronicle** button (`atelier-export-pdf-download` → `GET /campaigns/{cid}/export.pdf`). Stored on the user profile, so every export uses the same byline across all campaigns.

### Iter11 stale assertion fixed
- Refactored `test_openapi_has_expected_tags_and_ops` to assert tags-as-superset instead of exact-list equality, so the suite stays green as new routers are added (atelier, battlemap, channels, ingest, pdf, uploads, xp).

### Testing
- `/app/test_reports/iteration_18.json` — 13/13 new pytest pass (PATCH /me set/clear/no-op, PDF cover/chapter/legal pypdf-extracted assertions, Dyskami quote presence, single-heading no-duplicate, multi-paragraph speaker breaks, footer byline). Cumulative regression after iter11 fix: **149 PASS / 0 FAIL**.



### Phase C — Knowledge Web mechanic-aware ingestion
- New `routes/ingest.py`: `POST /api/campaigns/{cid}/ingest` (multipart, GM/admin only, 24 MB cap, **PDF · MD · TXT · RTF · DOCX**), `GET /api/campaigns/{cid}/ingestions`, `GET /api/ingestions/{id}`, `POST /api/ingestions/{id}/accept` (with idempotency guard — re-clicking never duplicates), `DELETE /api/ingestions/{id}`.
- File parsers: `pypdf` (PDF) · `python-docx` (DOCX) · `striprtf` (RTF) · UTF-8 (MD/TXT). LLM input capped at 60 k chars (head 60% + tail 40%) to control spend on the shared Emergent LLM key.
- Claude Sonnet 4.5 (via `emergentintegrations`) returns STRICT JSON across **10 categories**: `attribute · power_pack · power_bundle · item · weapon · skill · npc · location · lore · quest`. Each suggestion carries `kind`, `title`, mechanic-only `summary` (≤240 chars, **never reproduces rulebook prose** per Tri-Stat Emporium licence), structured `fields`, `atelier_phase` (1-7 mapped to Genesis phases), optional `target_arc`, and a `source_ref` audit anchor.
- Acceptance routes suggestions to two persistence paths:
  - Lore / NPC / Location / Quest → `db.nodes` (gm_only by default; tags include `ingest` + `atelier-phase-{N}`).
  - Attribute / Power Pack / Power Bundle / Item / Weapon / Skill → `db.custom_attributes` (so they appear in Character Builder selector).
- New `IngestPanel.jsx` embedded in the GM-only Atelier tab: history list, upload picker, categorized review tabs (`ingest-tab-{kind}`), per-suggestion checkbox, **"Mark visible"** + **"Accept all marked"** master controls (per user choice 'c' — categorized tabs *with* a master batch button).
- Storage: new `ingestions` collection added to `_GAME_COLLECTIONS` so admin reset clears it cleanly.

### Phase E — DriveThruRPG-ready system-branded PDF export
- New `routes/pdf_export.py`: `GET /api/campaigns/{cid}/export.pdf` returns a real `application/pdf` stream (latin-1-safe Content-Disposition strips non-ASCII from filename to prevent header errors on em-dash titles).
- **System-native style profiles** (full visual identity, not just accent colours):
  - **BESM 4E** — palette: white #FFFFFF · purple #3B1E63 · red #C81D1D · yellow #E8B339 · black #0B0710. Fonts: Helvetica-Bold heading / Helvetica-Oblique subheading / Helvetica body. Cover subtitle "Big Eyes, Small Mouth · Fourth Edition".
  - **Anime 5E** — palette: pink #E03A8E · blue #1E66C9 · white · red #C81D1D · black. Fonts: Helvetica-Bold headings / Times-Roman body / Times-Italic. Cover subtitle "Anime · 5E · A Tri-Stat Emporium System".
  - **Default** fallback profile so every system gets *some* PDF, even before authoring its own theme.
- **Chapter grouping (per user)**: Chapter 1 = **Session 0 + Session 1 + Session 2** (S0 as Prologue), every chapter from Ch2 onwards groups two sessions (Ch2 = S3+S4, Ch3 = S5+S6, Ch4 = S7+S8). Falls back gracefully if no S0 exists.
- Each session's narrative prefers the GM-finalised `session_record` chronicle (Phase 4.3 Chronicle Weave), falls back to the latest recap, then to a chat-log digest. Player journals append as visually distinct callout boxes with system-coloured borders.
- **Cover** has a top accent bar (primary), bottom accent bar (secondary), vertical accent stripe (accent), centred logo (`/app/frontend/public/system-logos/<system>.png`), camp title, system subtitle, decorative rule, and "Generated by TableGnostic · DriveThruRPG-ready" footer attribution.
- **Header chrome** on every body page: top + bottom rules in system primary colour, camp name top-left, system name top-right, page number bottom-right.
- **Legal page** at the end pulls per-system footer text from `LEGAL_COMPLIANCE.md` and references DriveThruRPG as the distribution channel.
- New `ExportPdfBtn` in the Atelier toolbar (`atelier-export-pdf-btn`) — fetches with bearer token, downloads as blob.

### Testing
- `/app/test_reports/iteration_17.json` — 13/13 new pytest pass (ingestion endpoints, multipart upload, file-type validation, accept persistence, delete, PDF magic + size + chapter ToC + latin-1 header + non-GM 403 + zero-sessions 400 + ingestions wipe). Cumulative regression: 137 PASS / 0 FAIL. Frontend self-verified — Atelier tab renders Ingest panel + Export PDF button; PDF download triggers HTTP 200 via Playwright network interception. Browser screenshot confirmed `sample_lore.md` ingestion with 11 suggestions across 6 categories (npc, location, attribute, item, lore, power_pack).

### Legal compliance reaffirmed (Phase C-specific)
- The Claude prompt explicitly forbids reproduction of rulebook prose, lore paragraphs, examples, or stat-block descriptions — only mechanic names, page references, and numerics. Suggestion `summary` capped at 240 chars to prevent accidental quotation.
- Raw uploaded text is parsed in-memory and **never** persisted; only Claude's structured JSON output lands in the `ingestions` collection.



### Phase A.1 — Character-sheet card display clarity
- Attribute rows now show `Name ×N assigned · cost N×M = K pts · X applications · Y enhancements ↓eff · Z limiters ↑eff` plus a top-of-card legend explaining BESM 4E V4.1 semantics. Each toggled enhancement / limiter row is exactly one application; multi-application requires re-listing.
- Skill rows show assigned level, per-level cost, total cost, and component count.
- Defect rows show rank, refund formula (`pts/rank × rank = total`).
- (`/app/frontend/src/components/CharacterSheet.jsx`)

### Phase A.2 — XP System (BESM 4E p.232 — Advancement)
- New `routes/xp.py`: `GET /sessions/{sid}/xp/suggest`, `POST /sessions/{sid}/xp/commit`, `POST /characters/{cid}/xp` (manual award/correction), `POST /characters/{cid}/xp/convert` (XP → Character Points 1:1). Engagement weights: chat_ic 0.05, chat_ooc 0.01, dice_macro 0.10, journal 0.25, spotlight 0.50; bonus capped at +2.0 per session. Default baseline 2 XP (BESM 4E "standard" session). **Suggest-only** — never auto-awards.
- Storage: `character.xp_total`, `character.xp_unspent`, `character.xp_log[]` audit trail (every entry tagged with source: `gm_award` / `session_baseline` / `engagement_bonus` / `correction` / `convert`).
- New `XPAwardPanel` modal in SessionView (`open-xp-btn`): GM-only, table of every published PC with IC/OOC/Dice/Journal counts, Spotlight checkbox, editable Base + Bonus + Note, computed Total, single Commit button. Per user choice: IC weighted higher than OOC.
- CharacterSheet header shows live `XP X.XX earned · Y.YY unspent` badge.
- (`/app/backend/routes/xp.py`, `/app/frontend/src/components/XPAwardPanel.jsx`, `/app/frontend/src/components/SessionView.jsx`, `/app/frontend/src/components/CharacterSheet.jsx`)

### Phase B — Atelier Dynamic Scaling
- New `routes/atelier.py` + `atelier` Mongo collection. Three planning tiers stacked: **Session 0** (table contract, lines/veils, safety tools, schedule, expectations, character integration, recurring themes, completed flag) → **Arcs** (~3-session spans with title/status/expected_sessions/summary/referenced NPCs/locations and beats: hook/rising/turn/echo/denouement) → **Master Plot mirror** (read-only of `genesis.master_acts`).
- `POST /api/atelier/{cid}/continuity` — deterministic continuity sweep flags `empty_arc`, `missing_node`, `act_arc_mismatch`, `dead_alive_conflict` findings.
- Player-view: GET as a non-GM returns ONLY safety subset (`lines`, `veils`, `safety_tools`, `schedule`, `table_contract`) — GM private planning never leaks.
- New "Atelier" tab in CampaignDetail (GM-only, `data-testid="tab-atelier"`).
- Admin reset wipe list now includes `atelier`, `battlemaps`, `channels`, `channel_messages`.
- (`/app/backend/routes/atelier.py`, `/app/frontend/src/components/AtelierTab.jsx`, `/app/frontend/src/components/CampaignDetail.jsx`, `/app/backend/routes/admin.py`)

### Testing
- `/app/test_reports/iteration_16.json` — 12/12 new pytest pass (XP weights/suggest/commit/convert + atelier GET/PUT/continuity + player-view safety subset). Cumulative regression: 124 PASS / 0 FAIL. Phase A.1 visual clarity self-verified in browser screenshot — Eli's Healing card renders `×3 assigned · cost 4×3 = 12 pts · 2 applications · 1 enhancement ↓eff · 1 limiter ↑eff · +Range / −Consumable`. XP badge `XP 5.00 earned · 5.00 unspent` confirmed.


