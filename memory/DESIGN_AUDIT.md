# TableGnostic — Design Audit & Re-Grouping Recommendations

**Date:** 2026-04-30 · V6.7 baseline
**Author:** E1 (assistant) — candid analysis, not a directive
**Status:** **Read-only document.** No code changed. Pick the suggestions you like; we'll execute in subsequent sessions.

---

## 1 · The single biggest UX problem today

**Cognitive overload at the campaign root.**
A `CampaignDetail.jsx` page is 1656 lines and surfaces ~12 tabs (Primer, Sessions, Codex, Atelier, Delta Drop, Custom Rules, Invite, Roster, Sheets, NPCs, Sessions, Maps…). New GMs see this and freeze.

**Root cause:** the app collapses *Authoring* (Atelier-style world-building, planning, references) and *Running* (live session, dice, tokens, recaps) onto the same page. These are entirely different user modes.

**Symptom in the wild:** GM is mid-session, needs to look up a Power Bundle they wrote three weeks ago — they're 3 tab-clicks deep on the same page that's trying to render the dashboard, the codex, and the live Pulse feed.

---

## 2 · Proposed Top-Level Re-Grouping (the "two modes" model)

Split the campaign experience into **two stable halves**, with a persistent switch in the top bar:

### MODE A · Atelier (authoring / planning / references)
*Everything you do BETWEEN sessions.* No live data, no dice, no WS noise.

  - **Genesis** — 7-phase master plot panel (each phase separately accessible & updateable, populates codex).
  - **Epic Campaign** — campaign-arc tracker (separate from Genesis, distinct mental model).
  - **Codex** — the world atlas (read-mostly here; live PCs writing motives is rare).
  - **Reference Tables** — Power Packs, Power Bundles, Custom Enhancements / Limiters / Skills, House Rules.
  - **Spell Conversion Atlas** (already built in V6.5; lift it to a top-level Atelier item — currently buried under the Reference Editor).
  - **Encounter & Threat Lab** — Encounter Designer, NPC sheet auto-generation (V6.7), CR/CP threat-tiers.
  - **Timeline** (NEW, planned next session) — visual tracker for sessions + encounters as nodes.

### MODE B · Table (live play / running)
*Everything you do DURING a session.* High-performance, real-time, minimal chrome.

  - **Session View** (the existing one — keep mostly as-is).
  - **Maps + Tokens** (will be elevated next sprint).
  - **Pulse / Director Console** — only here, only live.
  - **Macro Bar / XP Award / Approval queues** — already strong; promote.
  - **Player Sheet pop-out** — quick-glance character window for the table.

> **A persistent toggle** in the top bar (e.g. `< Atelier · Table >`) lets a GM switch contexts without re-loading the whole campaign.

---

## 3 · Specific suggestions, ranked by impact

### 🔴 P0 — Highest impact, low cost

1. **Genesis ↔ Epic split** (already on roadmap). Currently `EpicCampaignPanel.jsx` carries BOTH the campaign arc AND the 7-phase plot fundamentals. They serve different mental models — split into two Atelier tabs as planned.

2. **Encounter / Threat Lab as a first-class Atelier section.** Currently only renders inside Session View. GMs plan encounters BETWEEN sessions; the kit should live in the Atelier and link to sessions, not the other way round.

3. **NPC sheets generated automatically.** Once V6.7 ships `POST /campaigns/{id}/npcs/{nid}/generate-sheet`, every codex `npc` node should grow a "Generate sheet" button and a stat-block panel. Reduces encounter-prep friction by 70%+.

4. **The "Add character" path is too generic.** Today: pick system → blank builder. Better: pick system → choose `From scratch`, `From archetype` (templates), `From conversion` (e.g. import a D&D character via Anime 5E XP→CP), `Generate NPC` (GM-only).

5. **Reference Editor tab cluster is a wall.** 23 kinds in one strip is overwhelming. Group them visually:
   - **Mechanics** (Attributes, Skills, Defects, Enhancements, Limiters)
   - **Bundles & Packs** (Power Pack, Power Bundle)
   - **Content** (Spells, Feats, Backgrounds, Class Features, Race Traits)
   - **Cypher** (Type, Descriptor, Focus, Cypher, Artifact)
   - **Items & Rules** (Weapons, Armor, Items, Companions, Custom Rules)

### 🟠 P1 — Medium impact

6. **Player vs GM landing surface.** When a player logs in, they see the Atelier-heavy campaign-detail page. They mostly want: their character sheet, the next session, and the codex they have access to. Suggest a per-role dashboard widget that prioritizes the role's typical first-action.

7. **The character sheet is monolithic.** 1349 lines, vertical scroll. Split into stable sub-tabs: **Identity / Stats** | **Mechanics** (attributes, defects, bundles) | **Inventory & Items** | **History** (XP ledger, awards, approval). Players already scroll — sub-tabs cut to one screen.

8. **Approval workflow is a footnote.** `CharacterApprovalPanel` is buried below the XP Approval Queue. For tables that lean on rules-compliance, this is a primary GM action — surface it on the campaign roster page as a column next to each PC's name.

9. **Power Pack vs Power Bundle confusion** (mostly fixed in V6.4 but still…). On the BESM character builder flow, the picker conflates them. Show two separate "+" buttons with hover copy: "Power Pack — always-on source of power" vs "Power Bundle — activatable spell-like effect."

10. **Session-list scannability.** The session list is a flat dump. Add visual tags: 🟢 in-progress, ✓ resolved, 📜 narrative-only, ⚔ combat, ☆ milestone. GMs scan their season at a glance.

11. **Codex node detail page is text-heavy.** Add a "Connections" mini-graph (already have force-directed lib?) showing which other nodes link in/out — players retain context faster than reading prose.

### 🟡 P2 — Polish

12. **Empty-state design** is bare. First-time GM creates a campaign and sees empty Sessions / empty Codex / empty Atelier. Add tasteful inline hints: "No motives yet — try a Genesis Phase 1 sentence-starter." Each empty state suggests the next reasonable action.

13. **Toasts / notifications** sometimes vanish before users read them (login flow, save-success flicks). Persist last 5 in a corner-tray that can be dismissed.

14. **Mobile sweep** — most pages have decent reflow but the Atelier tab strip overflows horizontally on phones; the dice panel is finger-hostile. (Mobile PDF character sheet shipped in V6.6 — that's the precedent for direction.)

15. **Onboarding tour.** The "How to" guide is in the backlog. When delivered, surface it from the dashboard's empty state and the campaign creation success screen, not just a link in the footer.

---

## 4 · Specific dedicated-page suggestions

These would justify being lifted out of `CampaignDetail.jsx` into their own routes:

| Today's location | Suggested own page | Why |
|---|---|---|
| Atelier → Reference Editor (23 tabs) | `/app/campaigns/{id}/atelier/reference` | Reference authoring is a deep-focus task; deserves its own URL. |
| Atelier → Genesis | `/app/campaigns/{id}/atelier/genesis` | Each phase deserves its own deep-link (URL fragment per phase). |
| Atelier → Epic | `/app/campaigns/{id}/atelier/epic` | Same. Epic is a long-form planning surface. |
| Atelier → Encounter Lab | `/app/campaigns/{id}/atelier/encounters` | Connects to NPCs + threat-tier kit. |
| Atelier → Timeline (new) | `/app/campaigns/{id}/atelier/timeline` | Visual tracker — wants the page width. |
| Codex node detail | `/app/campaigns/{id}/codex/{nid}` | Already routed? Verify — this is reference; deserves a stable URL for sharing. |
| Director Console | `/app/sessions/{id}/director` | Only meaningful in live play; stop bleeding into campaign root. |

---

## 5 · UX paper-cuts I'd fix on day 1

- **Tab strip overflow on phones** — add `overflow-x-auto` + scroll snapping; keep current tabs but stop hiding them.
- **The campaign tile on `/app/campaigns`** — show `system_id` chip + last-session timestamp; currently just a name + concept, hard to scan a list of 30 campaigns.
- **Search.** No global search across campaigns / codex / characters. A single `Cmd-K` palette would 10x productivity for active GMs.
- **Breadcrumbs.** A user 5 levels deep (campaign → atelier → reference → power_bundle → editing one) has no breadcrumb to walk back.
- **"Approved for Play" badge** should visually echo on the character tile in `Roster`, not only inside the sheet. Three states: 🟢 approved · 🟡 pending GM · 🔴 fails rules.
- **Save-and-stay vs Save-and-back.** Lots of forms force a navigation on save. Default should be "save and stay" — content creators can iterate without context loss.

---

## 6 · System-personality consistency

Each system has a *vibe*. Right now BESM 4E gets the most love (gold/parchment). Suggest: each system page should subtly shift the entire palette so a player who runs three campaigns at three different tables can tell at a glance which world they just entered.

  - **BESM 4E** — current: gold + ember + parchment. Keep. Iconic.
  - **Anime 5E** — vivid (magenta/cyan accents already started in V6.1). Push harder: speed-line decorations, manga panel borders.
  - **D&D 5E** — parchment + drop-cap headings + serif body. Currently styled too close to BESM.
  - **Cypher** — Numenera teal + Eno-style ambient. Currently pure teal; add the "circuit-bracket" motif (already drawn on PDFs in V6.5) into the *web* UI, not just exports.

---

## 7 · Things I'd KILL (controversial but honest)

- **Custom Rules tab.** The Reference Editor `kind=custom` already covers it. Custom Rules is a redundant tab people don't use.
- **Invite & Share.** Tiny one-screen utility wrapped in a tab. Could collapse into a modal triggered from the Roster.
- **The "How to" placeholder route.** Ship the real guide or remove the link until you do — current state is a dead end.

---

## 8 · Things I'd NEVER kill

- The **Pulse** WebSocket layer. Critical, working, and rare. Don't touch.
- The **Approval workflow.** Quietly the highest-trust feature in the app — keep it pristine.
- **Cited references.** The legal-compliance posture (cite, never reproduce) is your moat. Every new feature must continue to cite, not reproduce.

---

## Closing

The product has *more* features than it has *organisation* for them. The "two modes" split (Atelier ↔ Table) plus three or four de-tabbed sub-pages is the highest-leverage change to make the current surface area feel cohesive. The Genesis/Epic split + the Timeline view planned next session are good next steps in that direction.

— E1 · 2026-04-30
