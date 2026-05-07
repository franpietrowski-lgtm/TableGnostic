# Table-Gnostic — Landing Page Ideation

> **Author:** Francis T. Pietrowski (creator & sole owner)
> **Status:** strategic blueprint — not implementation. This document captures the marketing pitch, page architecture, design vibe, asset inventory, and content-by-section plan for a public landing page that converts visiting GMs and players into seated tables.
> **Last revised:** 2026-02 · V6.25.9

---

## 1. Pitch (the elevator)

**One-liner**
> *Not the system. The table.*

**Tagline-paragraph** (homepage hero — for the eight-second skim)
> Table-Gnostic is the worldbuilding-first, play-by-post-second, voice-and-video-third tabletop platform built by a player who got tired of wiring four tools together. BESM 4E, Anime 5E, Cypher, and D&D 5E are first-class citizens — your homebrew is, too. Bring your own canon. Sit down. Roll.

**Value propositions (each one is a section anchor)**
1. **System-aware, not system-locked.** The same campaign can host BESM heroes, D&D 5E rangers, and Cypher Glaives without a converter spreadsheet. The math respects each ruleset's intent.
2. **Worldbuilding that survives the campaign.** Genesis (7-phase plot designer), Codex Knowledge Graph, World Creation Tree, and a per-campaign Reference Editor mean the lore your table builds is browsable, linkable, and exportable — not buried in Discord scrollback.
3. **Character creation that's actually fun.** Race / class / size templates, BESM Power Bundles, ASI auto-apply, and a Quick-Roll Bar that programs custom macros from your own attributes — including limiter and enhancement ranks. Build a level-1 character in five minutes; back-fill provenance on a legacy one in two clicks.
4. **Play-by-post that feels alive.** Slash commands resolve server-side (`/cast`, `/use bundle`, `/spend xp`, plus user-defined macros), undoable actions, and a chat layer that shows mechanical state — not just chat bubbles.
5. **Marketplace for homebrew.** Publish a polished feat / class / power bundle once. Other GMs clone it into their tables in one click. (V1 free; V2 monetized.)
6. **Yours, end-to-end.** Markdown PDF exports, Save-to-GitHub for the GM who wants version control, Atelier-published canon registry for the GM who wants to make their world a public reference, and zero rulebook prose reproduction so you stay clean of the IP holders' lawyers.

**What we are NOT**
- Not a VTT replacement (yet — Battlemap is here for tactical sketching, not full grid combat).
- Not a digital rulebook — we display mechanic NAMES and PAGE REFS. Bring your own books.
- Not an account-warehouse — we export everything, all the time, in plain JSON / Markdown / PDF. Take it with you.

---

## 2. Vision (the long horizon)

We are building the **shared brain a GM and their players co-author a campaign with**. The platform should:

- Be **system-aware enough** to do the boring math (CP budgets, DP curves, attunement caps, slot tracking).
- Be **system-agnostic enough** that an Anime 5E GM and a Cypher GM both feel like the platform was built specifically for them.
- Treat **homebrew as the default state**, not as a fallback. Every catalog is editable; every editable thing publishes to a marketplace.
- Make the **player's character sheet the central UX surface** — anything they need at the table (rolls, macros, advancement, spells, conditions, party initiative) flows through it.
- Make the **GM's world the proof-of-work** — Genesis, Codex, Atelier, and the Director's Console reward the GM who actually does the prep.
- **Never ship audio-without-consent**, **never ship LLM prose into players' lore without a GM safety pass**, **never reproduce a single line of someone else's rulebook**.

**Three-year horizon (informational, not commitment):**
- Mobile-first companion app (Pro / GM features gated to desktop).
- Stripe-Connect monetised marketplace with author payouts and 10% platform cut.
- Cross-table canon sharing (your campaign's Half-Dragon race becomes citable in someone else's campaign with a one-click attribution clone).
- LLM-assisted session recap that sounds like the table, not like Wikipedia.
- A public canon registry where worlds — not campaigns, *worlds* — are first-class published entities other tables can play in.

---

## 3. Page architecture (above-the-fold → footer)

### 3.1 Hero
**Layout** asymmetric: left-aligned 60% column for copy, right 40% for an animated sigil-overlay device that morphs between the four flagship system glyphs (BESM die, Anime 5E speed-line burst, Cypher hex, D&D 20).

**Copy**
> # Not the system. The table.
> A worldbuilding-first tabletop platform that respects every ruleset your table loves.
> [ Take a seat ] [ Watch the table tour (60s) ]

**Below-the-fold-edge sliver:** four-system glyph row with hover labels (BESM 4E · Anime 5E · Cypher · D&D 5E + 9 more scaffolded). Reinforces breadth in a single eyeline.

### 3.2 "What it does" — three scene-cards

Three rotating scene-cards that live-render real screenshots (role-gated below).

**Card A — World-First**
- Screenshot: Genesis 7-phase plot tree with the World Creation Tree subtab open and 28 codex nodes auto-classified into Population / Geography / History pillars.
- Copy: *"Build the world before you build the heroes. Auto-classify your codex. Author your nemesis as four linked nodes (motive · resources · weakness · the NPC themselves) so your players never wiki-trip their own villain."*

**Card B — Character-Smart**
- Screenshot: BESM 4E character sheet with a Weapon attribute showing `+Range×4 / −Backlash×2`, the Quick-Roll Bar with six bound macros, and an Anime 5E DP audit panel.
- Copy: *"The math obeys the rules. Limiter and enhancement RANKS — not just toggles — feed effective level. Custom macros pull from your sheet, not a generic SRD. Save the macro once. Roll it forever."*

**Card C — Table-Aware**
- Screenshot: SessionView with PBP chat showing a `/cast Fireball` resolution card next to the live battlemap and an XP marketplace tile.
- Copy: *"Slash-commands resolve server-side, so a refresh doesn't lose state. Pin macros to your sheet. Bid XP at the table economy. Roll dice that the GM can audit."*

### 3.3 "For whom" — role-gated function tour

A vertical accordion that asks the visitor *"Are you a GM, a Player, or a Worldbuilder?"* and reveals different screenshots and copy per choice.

**GM ribbon** (default open)
- Atelier · Genesis · Director's Console · Approval Queue · CR Engine · Genesis Archive · Marketplace publish
- Quote slot: *"My session prep used to live in five tabs. Now it lives in one Codex graph and exports to a PDF my players actually read."*

**Player ribbon**
- Character Builder · Quick-Roll Bar (with custom macros) · Spell Tracker · Folio (notes / journal / inventory) · Consent Checkbox
- Quote slot: *"I built a BESM Half-Dragon Werewolf in 4 minutes and the system told me my point budget was off by 3."*

**Worldbuilder ribbon**
- Codex Knowledge Graph · Reference Editor · Power Bundles · Canon Registry · Marketplace · World Tree
- Quote slot: *"My worldbook is now a living graph that publishes to other tables when I'm ready."*

### 3.4 Milestones & "what's next" (the trust device)

A horizontal milestone strip — `V6.21 → V6.22 → V6.25 → V6.25.8 → ROADMAP` — clickable to the changelog. Plus a "what we shipped this month" mini-feed pulled from `/app/memory/PRD.md` (auto-generated, no manual upkeep). Builds credibility — visitors see we ship.

### 3.5 Wizards & helpers (matching the design vibe)

- **"What system fits my table?" wizard** — 5 questions, recommends BESM / Anime 5E / Cypher / D&D 5E with a one-line *why this matches you*.
- **"From spreadsheet to Table-Gnostic" wizard** — paste a CSV row of your existing character; the wizard produces a starter sheet you can edit and import.
- **"Pitch your homebrew to the marketplace" wizard** — 3-step submission with attestation, license picker, and access-tier explainer.

These wizards live as `lucide-react`-iconed cards in a glass-morphism row. Each one is a 12-24px backdrop-blur tile over the obsidian gradient. Hover states reveal the question count + estimated time.

### 3.6 About + Contact

**About**
- Founder section — a paragraph + portrait of Francis T. Pietrowski with the *why* (built it as a GM tired of wiring tools together).
- "What we DON'T do" repeated as a trust-builder list.
- Open-source posture statement (frontend portion is inspectable; backend is a managed service).

**Contact**
- A tasteful contact form (Resend integration for delivery — already wired into the platform).
- Three direct channels: support@tablegnostic, gm-feedback@tablegnostic, marketplace@tablegnostic.
- Discord invite tile (icon + member count if/when wired).
- Bug-report deep-link that pre-fills a form with the visitor's browser + viewport context.

### 3.7 Footer

Already implemented as the in-app footer (V6.25.8 — see `Shell.jsx`):
- Centered original sigil + uppercase "TABLE-GNOSTIC" wordmark + "not the system. the table." tagline.
- Creator credit: **FRANCIS T. PIETROWSKI** in display caps.
- Three-paragraph legal block (original IP · third-party trademark notice · as-is liability).
- © {year} line.

The landing page footer should be visually identical so the brand is consistent across marketing and product.

---

## 4. Theme · scheme · blueprints

### 4.1 Aesthetic

**One-line:** *"Obsidian altar lit by gold candlelight, with arcane and ember accents."*

This is NOT the AI-slop default (purple gradient on white). It's:
- Solid obsidian backgrounds (`#08060e` / `#0c0a16`) — gradients on dark muddy them, so we use solid + overlays.
- Gold (`#e5c370` → `#8a6b20`) as the primary accent. Used for borders, headings, mark elements.
- Ember (`#c25646`) reserved for danger / cost / defect / overspend signals.
- Arcane-light (`#a999d6`) reserved for math / effective-level callouts.
- Mist (`#8b8aa3`) — body / labels / tertiary text.
- Parchment (`#e3dccb`) — primary readable text.

### 4.2 Typography

- **Display** — a serifed broken-faced face (currently Cinzel-aligned) for headings, sigils, role labels.
- **UI** — uppercase tracking-widest sans for labels, badges, chip text. AVOID: Inter, Roboto, Arial.
- **Body** — readable serif for paragraphs (avoiding the "AI slop" sans-on-card look).
- **Mono** — for formula previews, codex JSON, dice expressions only.

### 4.3 Layout & spacing

- **Asymmetric / left-aligned** — not centered. The hero is 60/40, the section heads sit left-tabbed with subtitles below.
- **2-3× the spacing you think you need** — generous breathing room between cards.
- **Glass-morphism** — 12-24px backdrop-blur tiles for the wizards row only. The rest is solid obsidian + gold border.
- **Grain / noise overlays** — subtle texture on the body background (already in the in-app `body::before` rule). Reuse on the landing.

### 4.4 Motion

- **Hero sigil** — slow morph between BESM die / Anime burst / Cypher hex / D&D 20. 8s loop. CSS-only (no GSAP needed).
- **Scene-card stack** — staggered reveal on scroll with `animation-delay` (CSS) — first card 0ms, second 120ms, third 240ms.
- **Hover micro-anims** — every interactive element has a transition on `transform` / `opacity` / `border-color` (NOT `transition: all` — it breaks transforms).
- **Cursor** — custom obsidian crosshair on the hero only.

### 4.5 Sound (deferred)

A **subtle dice-clack on Take a Seat hover** is on the wishlist. Out of scope for V1. The UX should NOT autoplay anything.

---

## 5. Asset inventory (what we need to ship)

### 5.1 Existing assets we already control
- TableGnostic original sigil SVG (`Shell.jsx::Sigil`).
- All four system glyphs (need to commission: BESM, Anime 5E, Cypher, D&D 5E corner-marks).
- Real-app screenshots (per role) — we can capture from the live app:
  - GM/Atelier ▸ Genesis 7-phase tree
  - GM/Atelier ▸ World Creation Tree (Pillars + Graph view)
  - Player ▸ BESM character sheet with Quick-Roll Bar
  - Player ▸ DnD sheet with Spell Tracker + Equipment slots
  - Worldbuilder ▸ Reference Editor with a power_bundle being authored
  - Marketplace browse grid
  - Session view with PBP + battlemap

### 5.2 To commission
- Hero sigil-morph animation (8s loop, alpha-channel WEBM).
- Wizard tile illustrations (3 tiles — line-art on obsidian).
- Founder portrait (creator headshot in the brand palette).
- Optional: a 60-second "table tour" video. Voiceover by the creator.

---

## 6. Data we should include (the proof points)

- **Systems supported**: 4 first-class (BESM 4E, Anime 5E, Cypher, D&D 5E) + 9 scaffolded (Pathfinder, Fate, Mothership, Blades in the Dark, Call of Cthulhu, Savage Worlds, Cyberpunk RED, Vampire: the Masquerade, Shadowrun, Numenera).
- **Tests**: cumulative pytest pass count from latest PRD entry (currently 20+ in V6.25.8 — display as a "this many tests pass on every deploy" trust badge).
- **Marketplace**: number of public listings (will grow over time; show live count when ≥ 12).
- **Versions**: most recent shipped version + a "next milestone" teaser pulled from ROADMAP.
- **Up-time**: backend health-check uptime % over rolling 30 days (when we wire telemetry).

---

## 7. Selling current + planned features

### 7.1 What ships today (concrete, demo-able)

| Feature | Pitch line |
|---|---|
| Genesis (7-phase plot designer) | *"The plot scaffolding the rest of your table builds on."* |
| World Creation Tree + Codex Graph | *"Your lore is a graph, not a Word doc."* |
| BESM Power Bundles | *"Buy a power once, apply it to every character that needs it."* |
| BESM enhancement / limiter ranks | *"Four levels of Range is different from one. The math now knows that."* |
| Custom Rules tab + Marketplace v1 | *"Author it once. Share it everywhere."* |
| Quick-Roll Bar with character-aware macros | *"`/strike` rolls 2d6 + your Weapon's effective level + your Combat skill — no SRD substitution."* |
| Slash commands (`/cast`, `/use bundle`, `/spend xp`, `/undo`) | *"The chat layer is the rules layer."* |
| Genesis Archive (snapshot history) | *"Roll back a Genesis edit you regret. Your worldbuilding has version control."* |
| ASI / Size auto-apply for D&D / Anime 5E | *"Pick a homebrew race; the math updates."* |
| PDF export per character + per campaign | *"Take everything with you. JSON. Markdown. PDF."* |
| Mobile floating burger nav | *"The burger floats with the scroll. The page title finally has room to breathe."* |

### 7.2 Next 90 days (forward-looking, but honest)

- **Mobile Sweep V3** — touch-target audit + sticky-header collapse on Character Sheet.
- **Strict Permission Gating** — players submit codex/genesis to GM approval queue (V1 read-only, V2 collaborative).
- **Anime 5E + D&D class library to level 20** with cross-system auto-conversion.

### 7.3 Aspirational (12-24 months)

- Marketplace V2 with Stripe-Connect payouts.
- Public canon registry (campaign → published-world publishing flow).
- LLM-assisted session recap with player-voice isolation.
- Companion mobile app (Google Play first; Pro features stay desktop).
- Private campaign access via password / pre-authored share links.

---

## 8. Awareness / outreach (how we get visitors)

- **GM-targeted**: r/rpg, r/AnimeRPG, r/Cypher_System; tabletop discord servers; post a release-note blog every minor version.
- **Player-targeted**: short-form video on TikTok / YouTube Shorts demonstrating "build a BESM character in 4 minutes" and "/cast Fireball that actually works".
- **Worldbuilder-targeted**: r/worldbuilding, r/DnDBehindTheScreen; partnership with worldbuilding-first podcasts.
- **Press kit page** (separate from main landing) with downloadable assets + creator bio + screenshots in 4K.

---

## 9. The blueprint, in one diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ HERO  · sigil-morph + headline + dual CTA + system-glyph row        │
├─────────────────────────────────────────────────────────────────────┤
│ SCENE-CARDS  · World-First · Character-Smart · Table-Aware          │
├─────────────────────────────────────────────────────────────────────┤
│ ROLE-GATED TOUR  · GM | Player | Worldbuilder accordion             │
├─────────────────────────────────────────────────────────────────────┤
│ MILESTONES  · ship-strip + "what's next" feed from PRD.md           │
├─────────────────────────────────────────────────────────────────────┤
│ WIZARDS  · 3 glass tiles · system-fit | spreadsheet-import | publish│
├─────────────────────────────────────────────────────────────────────┤
│ ABOUT + CONTACT · founder · don't-do-list · contact form · Discord  │
├─────────────────────────────────────────────────────────────────────┤
│ FOOTER  · sigil · creator credit · legal triple-paragraph · ©       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation notes (for whoever builds this next)

- **Re-use the Shell footer** verbatim (it's the in-app one and matches the brand).
- **Pull screenshots from the LIVE app** at build-time so they stay in sync with the product. Add a `/scripts/capture_marketing_screens.py` Playwright job to refresh them on every release.
- **Wire the milestone strip to PRD.md** so it self-updates. Parse the V-number headings; use the first paragraph as the blurb.
- **Marketplace listings count** — `GET /api/marketplace/stats` (will need to add this endpoint when listing count crosses 12).
- **Copy must avoid AI-slop tropes** — no "revolutionary", "AI-powered", "next-gen". Read like a human GM wrote it (because one did).
- **Performance budget** — landing page < 250kb compressed, hero LCP < 1.2s. Lazy-load every screenshot below the fold.
- **Accessibility** — WCAG AA. The obsidian background plus parchment text already passes 4.5:1.
- **i18n** — defer to V2; English-only on launch.

---

## 11. Definition of done

The landing page is "shipped" when:
- [ ] All 7 sections render at desktop + tablet + mobile breakpoints.
- [ ] Three role accordions populate from real screenshots.
- [ ] Milestone strip auto-pulls from PRD.md.
- [ ] All wizards link to a working flow (even if the flow is a "join the waitlist" stub for V1).
- [ ] Contact form delivers via Resend.
- [ ] Lighthouse mobile score ≥ 92 (perf + a11y + SEO).
- [ ] The creator (Francis T. Pietrowski) has reviewed and signed off on the copy and asset list.

---

*This file is intentionally non-implementation. It exists so the next agent — or the creator — can hand the work to a designer with a clear contract about what we're selling and to whom.*
