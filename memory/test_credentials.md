# Test credentials — V6.25.9 (current)

**GMFran (admin/GM)**: franpietrowski@gmail.com / PieGod08!!
**Aurora (player)**: albanaszak@ymail.com / AuroraTest123!

Both seeded on backend startup.

## V6.25.9 verification targets

### Character-aware Macro Builder (P0 — user-flagged)
- Open any character sheet → Mechanics tab → click an empty slot in the Quick-Roll Bar → "New macro" in the Slot Picker.
- Confirm the new builder pops with `character.name` in the title and shows tabs for: Stats, Attributes (with `eff ×N` hints), Skills, Defects, Derived (HP/EP/CV/ATK/DFN/...).
- Click any chip → token appears in the formula bar (e.g. `{attr:Weapon}`).
- "Live →" preview line should show the substituted formula in real time (e.g. `2d6+5+5`).
- Save → Slot picks it up → fire it from the slot → chat message shows the resolved roll.

### Backend token grammar (5/5 tests in `tests/test_v6259_macro_grammar.py`)
- `{attr:Name}` → effective level (level + Σlimiter.rank − Σenhancement.rank)
- `{skill:Name}` → assigned level
- `{def:Name}` → defect rank
- `{stat:body|mind|soul|str|...}` → stat / ability score
- `{derived:cv|atk|dfn|hp|ep|dm|ac|init}` → BESM / D&D derived value
- `{hp}`, `{ep}`, `{sanity}` → current resource pool
- Legacy `BODY/MIND/SOUL/STR/DEX/.../PROF/LVL` still resolve.

### Z-index portal fix
- The Macro Builder popup should sit ABOVE the next scroll section. Test by opening the builder on a long character sheet and scrolling — the modal MUST stay fixed and not bleed through.
- Same for the Slot Picker modal.

### Existing V6.25.8 (regression)
- BESM enhancement / limiter rank inputs (1-12) on `Customise` panel.
- Color-coded reference chips when GM sets a custom-rule color.
- Floating mobile burger menu replaces bottom-tab nav.
- Footer with `FRANCIS T. PIETROWSKI` creator credit + 3-paragraph legal block.
- Genesis Archive panel under Atelier ▸ Genesis subtab.

