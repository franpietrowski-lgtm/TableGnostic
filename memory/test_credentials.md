# Test credentials — V6.25.8 (current)

**GMFran (admin/GM)**: franpietrowski@gmail.com / PieGod08!!
**Aurora (player)**: albanaszak@ymail.com / AuroraTest123!

Both seeded on backend startup.

## V6.25.8 verification targets

### BESM Enhancement / Limiter ranks (P0 — user-flagged)
- Builder: `/app/characters/new?campaignId=<besm-cid>` → Attributes → "Customise" → toggle an enhancement → confirm a `× rank` numeric input appears below with rank 1-12 selector.
- Save → reload sheet → confirm the chip shows e.g. `+Range×4` and effective level reflects the rank-summed delta.
- Backend test: `tests/test_v6258_mod_rank.py` covers POST/GET round-trip for both new dict shape AND legacy strings.

### Color-coded reference chips
- GM: `/app/campaigns/<cid>` → Custom Rules tab → create a feat/feature with a non-default color (e.g. `#ff5577`).
- Player: open a character on that campaign → ReferencePicker with `kinds=["feat","feature"]` should now show:
  - the dropdown row with a left color stripe + dot,
  - the chip (after picking) with a colored left-border + dot.

### Floating mobile burger + footer
- Resize viewport to < 768px (or load on mobile). The previous bottom-tab nav is replaced by a single floating circular burger pinned to bottom-right.
- Tap → drawer opens with the full nav.
- Footer now centers the TableGnostic sigil + "FRANCIS T. PIETROWSKI" creator credit + 3-paragraph legal block.

### Genesis Archive UI
- GM: `/app/campaigns/<cid>` → Atelier tab → Genesis subtab → scroll past the "Open Genesis (7 phases) →" card.
- Should see "Genesis Archive" panel listing past saves (newest first) with expand → JSON dump → Restore / Delete buttons.

## Existing endpoints (regression)
- `GET /api/anime5e/races` — 29 races.
- `GET /api/characters/{cid}/anime5e/budget-breakdown` — RAW DP math.
- `POST /api/campaigns/{cid}/macros` — V6.25.7 macro CRUD.
- `POST /api/channels/{chid}/messages` — `/cast`, `/use`, `/spend xp`, `/macro`, `/undo` resolvers.
