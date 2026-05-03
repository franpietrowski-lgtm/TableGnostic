# V6.21 test credentials
# (unchanged from V6.20)

**GMFran (admin/GM)**: franpietrowski@gmail.com / PieGod08!!
**Aurora (player)**: albanaszak@ymail.com / AuroraTest123!

Both seeded on backend startup.

## V6.21 specific notes for testing

**Anime 5E character for budget audit testing:**
- Campaign: Evereantha Anime 5E
- Eli Anime 5E character (look up via `GET /api/campaigns?system_id=anime-5e` → first campaign → first character)
- Budget breakdown now shows: ability_score_cost, race_cost, point_buy_total, total_spent
- RAW formula: 80 + (level − 1). Level 5 Eli = 84 DP.

**New endpoints to verify (V6.21):**
- `GET /api/anime5e/races` — returns 29 races (14 native + 14 PHB + Raceless). Has `rules_note` with "80".
- `GET /api/characters/{cid}/anime5e/budget-breakdown` — adds `ability_score_breakdown`, `ability_score_cost`, `total_spent`, `canonical_raw_dp`, `formula_note`.
- `POST /api/campaigns/{cid}/anime5e-recompute-budget` — default formula is "raw".
- `GET/POST/DELETE /api/campaigns/{cid}/consent` — player consent record.
- `GET /api/campaigns/{cid}/consent-roll` — GM view of every member's consent status.
- `GET/POST /api/campaigns/{cid}/seat-applications` — player applies, GM lists.
- `POST /api/campaigns/{cid}/seat-applications/{aid}/approve|reject` — GM decision.
- `POST /api/campaigns/{cid}/leave` — player leaves a seat.
