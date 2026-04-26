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

## V4.4 — Bug-fix Sweep + Map Upload + Demo Chronicle (2026-04-26)

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

## V4.4 Phase C+E — Knowledge Web Ingestion + DriveThruRPG PDF Export (2026-04-26)

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


