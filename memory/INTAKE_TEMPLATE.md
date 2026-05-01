# TableGnostic Atelier Intake Template

> **Purpose:** A markdown structure that the Knowledge Web ingestor (Claude Sonnet 4.5) can parse cleanly, section by section, regardless of file size. Following this template lets the ingestion engine produce sharper, more complete suggestion sets and avoid the "one big blob" truncation that plagues freeform PDFs.

---

## How to use

1. Copy this template into your favourite editor (Obsidian, Notion export, plain Markdown).
2. Fill in the sections you have content for. **Skip sections you don't have** — empty sections are fine.
3. Save as `.md`, `.txt`, or `.docx`.
4. Open your campaign → **Atelier → Knowledge Web → Ingest**.
5. The ingestor walks each `## SECTION` block independently, so a 5 MB intake file is processed as ~30 small focused Claude calls instead of one truncated giant read.

**File size ceiling:** 64 MB (raised from 24 MB in V6.16). Combined Evereantha + Artisan Tale × 1.5 fits comfortably.

---

## CAMPAIGN OVERVIEW

> One paragraph elevator pitch. Genre, tone, where the table will spend most of its play time, what's at stake. The ingestor uses this to bias every other section's suggestions toward the right narrative voice.

Example:
> A 52-session arc of techgnostic mystery across Continenta Aurea. Players are apprentice artisans of the Evereantha order; the Andrewsarchus rises in the deep north, and the Order of the Darkening Star believes void energy is the only force that will outlast the gods.

---

## SYSTEM RULES NOTES

> Optional. House rules, custom point budgets, errata, banned mechanics, encouraged mechanics. The ingestor turns these into Reference Library `house_rules` entries.

- **Power level:** Heroic (150 CP for BESM, Tier 2 for Cypher, Level 5 for D&D 5E)
- **House rule example:** "Companions cap at 1 per PC unless approved by table vote."

---

## CHARACTERS / NPCs

> One subsection per character. Use `### Name` for each. The ingestor turns each subsection into a `kind: npc` Codex node with stat hints.

### Eli (Apocophae apprentice)
- **Concept:** alchemist of Eagles Nest, haunted by the Stranger
- **Affiliation:** Apocophae order, Evereantha workshop
- **Role:** PC (player: GMFran)
- **Goals:** Earn the barter certificate. Prove the Stranger does not own her.
- **Notable mechanics:** Healing 3 (Range, Consumable), Item 6 (apothecary bandolier), Heightened Senses 2 (smell), Cognition 2, Sixth Sense 1, Wealth 2.
- **Defects:** Phobia (tall hooded strangers), Recurring Nightmares, Marked (herb-pigment stains).

### (next character…)

---

## LOCATIONS

> One subsection per location. Use `### Place Name`. The ingestor maps each to a `kind: location` Codex node and seeds `fields.temperature` / `fields.humidity` if you provide them — these power the Biome Pyramid.

### Eagles Nest (BESM home village)
- **Pillar:** Geography
- **Climate:** cool / wet (taiga edge)
- **Population:** ~600
- **Notable people:** Master Vael (lead artisan), the Three Tinctures (rival apothecaries)
- **One-line hook:** "Where the road into the Caldera ends and the climbing begins."

### (next location…)

---

## FACTIONS

> One subsection per faction. Use `### Faction Name`. Becomes `kind: faction` (under `population` pillar) with motive + intent fields the Director's Console can pulse.

### Order of the Darkening Star
- **Pillar:** Population
- **Goal:** Channel void energy as the only post-divine power.
- **Methods:** Public scholarship, secret rites, recruitment of orphaned artisans.
- **Threat level:** rising (turn 0 → primary nemesis by Phase 5)

---

## CREATURES

> One subsection per creature/monster. Use `### Creature Name`. Becomes `kind: creature` with cr / level / total_points hints depending on the campaign system.

### Andrewsarchus
- **Type:** apex predator, mythic
- **Body / Mind / Soul (BESM):** 9 / 4 / 6
- **CR (D&D 5E):** 11
- **Level (Cypher):** 7
- **Total CP (BESM/Anime 5E):** 240
- **Signature:** silent stalking, single-bite kill on a wounded target.

---

## LORE / HISTORY

> Free-form lore beats. Each `### Heading` becomes a `kind: lore` node, tagged to the History pillar. Keep entries short and mechanic-aware where possible (e.g. "the Sundering halved magic-skill pools campaign-wide").

### The Sundering (year ~ -800)
- A continent-spanning fracture between artificial and natural creation.
- **Mechanical effect:** all magic skills cost +1 CP/level (BESM) or +1 difficulty step (Cypher) within the Caldera.

---

## QUESTS / ARC HOOKS

> One subsection per arc or quest. Becomes `kind: quest` with `target_arc` set when the document names an arc explicitly.

### Arc 1 — The Apothecary's Test (Sessions 1-3)
- **Beat 1:** Eli is dispatched to harvest moon-rue beyond the Caldera.
- **Beat 2:** The Stranger appears on the third night.
- **Beat 3:** Returning home, the wares are stolen by Darkening Star recruiters.
- **Resolution conditions:** Recover wares OR negotiate trade OR expose the recruiters.

---

## CUSTOM REFERENCE (system-specific)

> Mechanic content you've authored: custom Attributes, Skills, Foci, Spells, Feats, Power Bundles. The ingestor maps these to `custom_attributes` (BESM/Anime) or system-specific Reference entries (D&D 5E spells, Cypher foci).

### Attribute · Apocophae Discipline (BESM Skill Group)
- **Cost:** 2 pts/level (Lesser Group)
- **Components:** Foraging, Brewing, Diagnosis, Reagent Lore
- **Page hint:** Tri-Stat Skill Groups, p.120

### Focus · "Brews Tinctures of Many Hues" (Cypher)
- **Tier 1:** Trained in identifying alchemical reagents.
- **Tier 2:** Brew a one-shot Cypher per session (level = tier).
- **Tier 3:** Add a step lower to all dosing rolls.

---

## TIMELINE BEATS

> One bullet per dated event. Becomes Timeline markers tagged to a session if the document associates them.

- **Year 1, Day 14:** Eli's Apothecary's Test begins (Session 1).
- **Year 1, Day 17:** Recurring Nightmare returns (Session 2 narrative beat).
- **Year 1, Day 23:** Caldera-rim ambush (Session 3 climax).

---

## SESSION BRIEFS

> Optional — pre-written session outlines. Becomes `kind: quest` + Atelier Workshop arc entries with `atelier_phase: 5` (Session prep).

### Session 1 — "First Tincture"
- **Opening beat:** Master Vael's commission letter.
- **Three escalating challenges:** wolves on the road, a spoiled reagent, the Stranger glimpse.
- **Climax:** the third night camp.
- **Pin candidate:** Eagles Nest → Pin "Master Vael" on Codex, drop on Timeline at Session 1.

---

## INDEX

> Optional — flat list of cross-references the ingestor can use to dedupe. Each line: `KIND :: NAME :: ALIAS, ALIAS`.

- npc :: Eli :: Eli of Eagles Nest, the Apocophae apprentice
- location :: Eagles Nest :: Hawk's Eyrie, the Nest
- faction :: Order of the Darkening Star :: Darkening Star, ODS

---

## Compliance reminder

The ingestor will **not** reproduce uploaded prose verbatim. It summarises mechanic-only and stores only the structured suggestion JSON. The original markdown is parsed in-memory and discarded. This is a Tri-Stat Emporium / Cypher System Creator licence requirement and applies to **every** uploaded document.
