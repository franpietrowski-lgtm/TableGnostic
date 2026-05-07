# Test credentials — V6.25.10 (current)

**GMFran (admin/GM)**: franpietrowski@gmail.com / PieGod08!!
**Aurora (player)**: albanaszak@ymail.com / AuroraTest123!

Both seeded on backend startup.

## V6.25.10 demo characters

- **Eli (Apocophea)** — `/app/characters/07a6f21a14be4ea9ada50e6db8727ad3`
  - BESM 4E, Heroic, 120 pts.
  - **Apocophea AutoMakers Bag** (Item ×4, eff ×5) — Auto-Refining ×2, Compact, Unwarned Eject, No Selection, Tied to Owner.
  - **Lacrosse Staff** (Weapon ×3, eff ×2) — Throwable, Reach ×2, Two-Handed.
  - Skills: Artisan ×4, Athletics ×3.
  - Defects: Phobia ×1.

## V6.25.10 verification targets

### Per-row "Add to macro" sprinkles (P0)
- On Eli's sheet: each BESM stat tile (BODY/MIND/SOUL), each Derived tile (CV/ATK/DFN/HP/EP/DM), each Attribute roll cell, each Skill roll cell, each Defect row should have a small wand icon (data-testid `add-to-macro-{token-with-dashes}`).
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


