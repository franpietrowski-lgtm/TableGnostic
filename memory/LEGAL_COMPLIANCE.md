# Table-Gnostic — Legal Compliance Audit (V4.3)

> Living document. Updated 2026-04-26. Reviews every game system the app
> exposes, what license / community-content programme governs it, what
> Table-Gnostic stores per-system, and what it must NOT store. Errs on the
> side of mechanics-only references — never reproduces rulebook prose.

## TL;DR

Table-Gnostic is **mechanics-aware, lore-empty**. For every system in the
selector, the app:

* References Attribute / Skill / Defect / etc. **names + cost numbers + page
  refs** (factual mechanic data — not copyrightable).
* Generates **its own original prose** for blurbs, primer text, etc.
* **Never reproduces** rulebook descriptions, setting fiction, or art.
* **User-authored content** (campaign nodes, journals, recaps, custom rules)
  belongs to the authoring user — Table-Gnostic stores and serves it but
  does not republish or commercialise it without consent.

The only original setting Table-Gnostic ships is **Aurea (the Maiden
Adventure)** — original to this project, public-domain-grade prose released
under the same project licence.

If the app is distributed for money in its current form, it operates within
the Tri-Stat Emporium / OGL / ORC / CC-BY licences enumerated below — but
the **shipped Cypher and BESM 4E publishing pipelines (DriveThruRPG export
chapters)** require explicit per-system attribution + disclaimer footers,
which the export pipeline must inject programmatically.

---

## Per-system status

### 1. BESM 4E — Tri-Stat Emporium (Dyskami Publishing)

**Programme:** Tri-Stat Emporium Community Content licence
**Status:** ✅ Compliant
**What we store / serve:**
* Attribute/Defect/Skill names + cost numbers + page references (BOOK,
  BOOK_EXTRAS in `besm_data.py`)
* Original blurbs and educational notes — written by Table-Gnostic
* Aurea custom-content showcase (8 attributes, 5 power packs, 5 skill
  groups) — original re-skins, OUR setting, no Dyskami IP
**What we MUST NOT do:**
* Reproduce rulebook descriptive prose (ruled out by design)
* Reproduce Dyskami-original setting fiction (Aurea is OURS — not Anime
  Companion / Spirit etc. — those are Dyskami)
* Sell PDFs that aren't badged as Tri-Stat Emporium Community Content
  with the required disclaimer
**Required PDF footer (campaign export):**

> Table-Gnostic uses BESM Fourth Edition mechanics by Dyskami Publishing
> Company under the Tri-Stat Emporium Community Content licence. BESM and
> Big Eyes, Small Mouth are trademarks of Dyskami Publishing Company.
> This product is not endorsed by, sponsored by, or affiliated with
> Dyskami Publishing Company. All Aurea original content © Table-Gnostic
> contributors.

### 2. Anime 5E — Dyskami Publishing

**Programme:** Tri-Stat Emporium (same as BESM)
**Status:** 🟡 Pending content extraction (PDFs uploaded; not ingested yet)
**Same constraints as BESM 4E** — names + costs + page refs only.

### 3. D&D 5E — Wizards of the Coast

**Programme:** Creative Commons (CC-BY 4.0) for the SRD 5.1 / 5.2
**Status:** ✅ Compliant for SRD-only references; 🟡 user-authored content
must not include non-SRD WotC IP (Forgotten Realms, etc.)
**What we store / serve:**
* SRD-licensed names (classes, spells, monsters in SRD 5.1)
* Page references to the SRD PDF
* No reproduction of non-SRD content
**What we MUST NOT do:**
* Reproduce non-SRD content (most adventure-module text, Faerûn fiction,
  flavour text from supplements)
* Use the WotC trademarks (Dungeons & Dragons, D&D logo) without
  permission — refer to the rules generically as "5E-compatible"
**Required PDF footer (campaign export):**

> Compatible with the Fifth Edition fantasy roleplaying game. Mechanics
> derived from SRD 5.1 / 5.2 used under CC-BY 4.0. Dungeons & Dragons is
> a registered trademark of Wizards of the Coast LLC; this product is
> not affiliated with, endorsed by, or licensed by Wizards of the Coast.

### 4. Pathfinder 2E — Paizo

**Programme:** ORC (Open RPG Creative License) for the post-2023 Remaster
**Status:** ✅ Compliant for ORC-licensed content
**What we store / serve:**
* Names, ancestries, classes, feats, spells, monsters from the ORC
  licensed Remaster
**What we MUST NOT do:**
* Use Pathfinder Compatibility logo without complying with the ORC
  trademark requirements
* Reproduce setting fiction (Golarion lore is not ORC-released)
**Required PDF footer (campaign export):**

> This product is compatible with the Pathfinder Roleplaying Game,
> Remastered. Mechanics used under the Open RPG Creative License (ORC).
> Pathfinder is a trademark of Paizo Inc.; this product is not endorsed
> by Paizo Inc.

### 5. Cypher System — Monte Cook Games (Cypher System Creator)

**Programme:** Cypher System Creator licence (community content)
**Status:** ✅ Compliant per V4.5 — verbatim cover & legal text embedded in PDF exports

**Settings the Creator licence EXPLICITLY allows full content for:**
Godforsaken · Gods of the Fall · Masters of the Night · Predation · The Heartwood · The Revel · Unmasked

**Settings Creators may CITE for compatibility but NOT duplicate:**
Claim the Sky · First Responders · Stay Alive! · The Origin · The Stars Are Fire · We Are All Mad Here

**Settings the licence FORBIDS use of (NEVER referenced as content sources in TableGnostic):**
Numenera · The Strange · No Thank You, Evil!

**What we store / serve:**
* Type / Focus / Descriptor names; tier costs; cypher / artifact / GM
  Intrusion mechanic references with short stat lines; page numbers
* Compatibility-mode citations for the cite-only setting list above

**What we MUST NOT do:**
* Reproduce Cypher rulebook prose, lore paragraphs, or stat-block descriptions
* Copy art from Monte Cook Games publications (only Cypher System Creator
  art-pack content is permitted, with required artist credit)
* Use the Cypher System Rulebook trade dress, Monte Cook Games logo, or
  the Cypher System logo (only the **Cypher System Creator** logo)
* Generate content for Numenera / The Strange / No Thank You, Evil!

**Required cover-page text (per the Creator licence):**

> Requires the Cypher System Rulebook from Monte Cook Games. Distributed through the Cypher System Creator™ at DriveThruRPG.

**Required PDF footer (campaign export, verbatim copyright text per the Creator licence):**

> This product was created under license. CYPHER SYSTEM and its logo, and CYPHER SYSTEM CREATOR and its logo, are trademarks of Monte Cook Games, LLC in the U.S.A. and other countries. All Monte Cook Games characters and character names, and the distinctive likenesses thereof, are trademarks of Monte Cook Games, LLC. www.montecookgames.com. This work contains material that is copyright Monte Cook Games, LLC and/or other authors. Such material is used with permission under the Community Content Agreement for Cypher System Creator. All other original material in this work is copyright by the GM listed on the cover and published under the Community Content Agreement for Cypher System Creator.

### 6. Call of Cthulhu 7E — Chaosium

**Programme:** Miskatonic Repository (community content programme)
**Status:** 🟡 Pending content extraction
**What we store / serve:**
* Skill names, sanity / luck mechanics references, page numbers
* No reproduction of mythos fiction (which is partly public-domain
  Lovecraft and partly Chaosium IP)
**Required PDF footer (campaign export):**

> Compatible with the Call of Cthulhu roleplaying game by Chaosium Inc.
> Released under the Miskatonic Repository Community Content programme.
> Call of Cthulhu, Chaosium, and the Miskatonic Repository logo are
> trademarks of Chaosium Inc. Used with permission.

### 7. Savage Worlds Adventure Edition — Pinnacle

**Programme:** Savage Worlds Fan Licence (non-commercial) /
"Powered by Savage Worlds" branding licence (commercial)
**Status:** 🟡 Pending content extraction; commercial export needs
explicit Pinnacle agreement
**What we store / serve:**
* Trait / Edge / Hindrance names; page references; mechanics only

### 8. Fate Condensed — Evil Hat

**Programme:** Creative Commons Attribution 3.0 (CC-BY 3.0)
**Status:** ✅ Compliant
**What we store / serve:**
* Aspect / Skill / Stunt frameworks; mechanics only
* Original blurbs + Aurea-style custom showcases

### 9. Cyberpunk RED — R. Talsorian Games

**Programme:** No formal community content programme
**Status:** 🟡 Mechanics-only references permitted (factual data); brand
+ setting are NOT licensed
**What we store / serve:**
* Role names, stat names, page references
**What we MUST NOT do:**
* Reproduce ANY rulebook prose, art, or setting fiction
* Sell a PDF with the Cyberpunk RED logo / wordmark — branding the
  export as "Cyberpunk RED-compatible house rules"

### 10. Vampire: The Masquerade 5E — Renegade Game Studios / Paradox

**Programme:** Storytellers Vault (DriveThruRPG community content)
**Status:** 🟡 Storytellers Vault rules apply for distribution
**What we store / serve:**
* Clan / Discipline / Predator type names; mechanics only

### 11. Blades in the Dark — Evil Hat / John Harper

**Programme:** Creative Commons Attribution 3.0 + Forged in the Dark SRD
**Status:** ✅ Compliant under Forged in the Dark SRD

### 12. Mothership — Tuesday Knight Games

**Programme:** Mothership Third Party License (commercial-friendly)
**Status:** ✅ Compliant if Mothership compatibility logo + footer
included on commercial PDFs

### 13. Shadowrun 6E — Catalyst Game Labs

**Programme:** No public community content programme
**Status:** ⚠️ Mechanics-only; commercial distribution NOT permitted
without direct Catalyst Game Labs licence
**What we store / serve:**
* Attribute / Skill / Edge names; page refs only
**What we MUST NOT do:**
* Sell a Shadowrun-branded PDF — strictly non-commercial only

---

## App-level guarantees

### Content visibility & ownership

* Player journal entries default to `gm_only` visibility on the codex —
  a private GM artefact, not a published asset.
* Session recaps default to `gm_only` until the GM explicitly reveals.
* Campaign cloning carries World Codex but **excludes session history /
  chat / dice rolls / player journals** so a clone never leaks private
  player data into a forked table.
* The bulk reveal/hide buttons are GM-only and audited per node
  (`updated_at` stamped).

### LLM usage (Emergent / Claude Sonnet 4.5)

* Loremaster recap + chronicle finalisation send the GM's own session
  transcript to Claude. We **do not** include any system rulebook prose
  in prompts. The system field passed to Claude is `system_id` (a label,
  not licensed text).
* Generated chronicles are stored per-campaign and never aggregated into
  cross-campaign training/inference signal.

### Distribution model (in flight)

* The DriveThruRPG export pipeline (planned) will inject the per-system
  legal footer above on every chapter cover, plus a campaign-level
  attribution page with:
  * Original setting credit (Table-Gnostic contributors)
  * System compatibility statement + community-content licence reference
  * GM + player credits (opt-in)
  * Disclaimer that the product is unofficial / fan-made

### Trademarks NEVER used in UI without permission

| System              | Trademark                          | Status              |
|---------------------|------------------------------------|---------------------|
| BESM                | Big Eyes, Small Mouth · BESM       | ✅ disclaimer carried |
| D&D                 | Dungeons & Dragons · D&D logo      | ❌ never displayed in UI; refer as "5E-compatible" |
| Pathfinder          | Pathfinder · Goblin logo           | ❌ never displayed in UI; refer as "PF2e-compatible" |
| Cypher              | Cypher System · Numenera logos     | ✅ shown via Cypher Creator licence (already enforced) |
| Call of Cthulhu     | CoC · Miskatonic Repository sigil  | 🟡 will be carried via Miskatonic licence on export |
| Cyberpunk RED       | Cyberpunk RED logo                 | ❌ never displayed |
| Vampire             | World of Darkness · V5 logos       | ❌ never displayed |
| Shadowrun           | Shadowrun · CGL logos              | ❌ never displayed |

### What this means for the user (GMFran)

You can ship the app for money in its CURRENT form provided:
1. **No DriveThruRPG export goes live** until the per-system footer
   injection pipeline is wired — that's the V4.4+ task.
2. **Cypher exports are paid-tier creator-licence eligible** (free to
   start; Monte Cook Games requires a small commercial fee per gross
   threshold — this is on the GM, not on Table-Gnostic the platform).
3. **Shadowrun & Cyberpunk RED exports must be free** — no paid PDFs
   under those brands until a direct licence is in place.
4. **All other systems above** can support paid PDF exports under the
   community-content / Creative Commons programmes named.

The app itself (Table-Gnostic the platform) is a hosting/tooling product
and is not constrained by per-system licences as long as users stay within
the same constraints when they author content on it.

---

## Audit log

| Date       | Author     | Change                                              |
|------------|------------|-----------------------------------------------------|
| 2026-04-26 | GMFran     | Initial draft — V4.3 round, all 13 systems audited |
