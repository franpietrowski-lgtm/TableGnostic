# Test credentials — V6.25.24 (current)

**GMFran (admin/GM)**: franpietrowski@gmail.com / PieGod08!!
**Aurora (player)**: albanaszak@ymail.com / AuroraTest123!

Both seeded on backend startup.

## V6.25.24 verification targets (Cypher Cycles B-2..B-6)

### Cypher Reference Panel UI (B-2)
- Open a cypher campaign in Atelier ▸ References subtab. The `CypherReferencePanel` (testid `cypher-reference-panel`) renders ABOVE the existing Reference Editor.
- 8 genre tabs (testids `cypher-ref-genre-fantasy` etc.) and 6 sub-tabs (`cypher-ref-tab-types|descriptors|foci|cyphers|artifacts|bestiary`).

### Cypher Tier-Progression Sidebar (B-3)
- In the Cypher Builder, change Type or Tier — the testid `cypher-tier-progression` panel re-fetches `/api/cypher/tier-helper`.
- Click an ability chip (testid `cypher-ability-bash`) to toggle pick state; persists into `folio.cypher_state.abilities`.

### Cypher XP Economy panel (B-4)
- On every cypher character sheet: `cypher-xp-panel` mounts under the sheet view.
- Quick spends: `cypher-spend-reroll`, `cypher-spend-refuse-intrusion`, etc. Refuse with 0 XP returns 400.
- Modals: `cypher-peer-transfer-modal`, `cypher-narrative-pool-modal`, `cypher-grant-intrusion-modal`, `cypher-advancement-modal`.

### Cyphers / Artifacts random-roll (B-5)
- Cyphers / Artifacts sub-tabs show `cypher-ref-roll-cypher` / `cypher-ref-roll-artifact` button. Click → result card `cypher-ref-roll-result-cypher` with name + level + form + effect + depletion (artifacts).

### Bestiary (B-6)
- `cypher-ref-bestiary` tab loads 12 creatures with level filters `cypher-bestiary-level-min/max`. Each row testid `cypher-bestiary-{id}` (e.g. `cypher-bestiary-fantasy-dragon-juvenile`).

### V6.25.24 backend tests (15/15 NEW pass)
- `tests/test_v62524_cypher_xp.py` (7/7) — reroll, refuse@0xp 400, peer-transfer ±1, intrusion-grant +2 / auto-pair, narrative-pool multi-debit, advancement-step −4, unknown 422.
- `tests/test_v62524_cypher_tables_bestiary.py` (8/8) — random cypher full payload, random artifact w/ depletion, 422 on bad kind, level modifier, ≥12 bestiary listing, genre filter, level band, /reference includes bestiary.

### V6.25.23 regression
- 16/16 V6.25.23 tests still GREEN.

## Earlier verification targets (V6.25.10)

### Per-row "Add to macro" sprinkles (P0)
- On Eli's sheet: each BESM stat tile, Derived tile, Attribute / Skill / Defect row should have a small wand icon (data-testid `add-to-macro-{token-with-dashes}`).
- Click → MacroBuilder opens pre-seeded with `2d6+{token}` and the live-preview line shows substituted values.

### BESM Extras item / weapon mods
- `GET /api/besm/reference` should include `weapon_enhancements` (10), `weapon_limiters` (8), `item_enhancements` (7), `item_limiters` (8) with source = "BESM Extras" and blurbs.
- In the BESM CharacterBuilder: edit a `Weapon` Attribute → Customise → both standard mods AND a "Weapon · BESM Extras" group should appear. Same for `Item` Attributes — should also show "Item · BESM Extras" group.

### Mobile Sweep V3
- Resize to 414px wide. Open Eli's sheet. Scroll the sheet — the tab strip pins to the top with `bg-void/95 backdrop-blur-sm`. Tab pills are 40px+ tall with no wrapping (horizontal scroll on overflow).

### V6.25.10 backend tests (3/3 pass)
- `tests/test_v62510_apocophea_bag.py` — exposes pools, builds bag, fires macro on Eli, seeds 4 codex materials.

## Existing endpoints (regression — all 26 pytest pass)
- BESM enhancement / limiter ranks (V6.25.8)
- Character-aware macro grammar (V6.25.9)
- Custom rule color round-trip (V6.25.7)
- Genesis archive endpoints (V6.25.7)
- `/cast`, `/use bundle`, `/spend xp`, `/macro`, `/undo` resolvers (V6.25.6 + .7)


