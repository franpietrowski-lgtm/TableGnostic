"""V6.25.53 — Evereantha cosmology hard-seed.

Faces of Aurae × Faces of Mortiscura — the two-faced magic system at
the spine of every Evereantha campaign. Surfaced as a public
quick-reference in the Magic Architect AND as an
edge/obstacle/advantage adjudication table for the encounter chat
roller (`Cosmological Tension`).

Why hard-seed here instead of as DB nodes: this is *canon system data*
that ships as part of TableGnostics' inter-system agnostic campaign
core (the long-term plan is to port every game system we adapt back
through this same lore spine). Keeping it in code means:

  • Single source-of-truth — no risk of partial DB seed drift.
  • Inter-system reuse — same JSON returned regardless of
    `campaign.system_id`. BESM 4E sheets, D&D 5E spells, Anime 5E
    powers, and Cypher cyphers can all reference the same Face
    palette for their flavour text without per-system seeding.
  • The opposition matrix is GM-tunable later by overriding via
    `/api/cosmology/evereantha/opposition` (campaign-scoped) without
    breaking the canon table.

Canon source: Evereantha bible v3 — "Aurae and Mortiscura Duality"
(chunk-09) + per-node failure & forbidden-pair entries scattered
across chunks 05-21.
"""
from __future__ import annotations

# ─────────────────────────── Faces of Aurae ───────────────────────────
# The creative / expansive face of magic. Four Faces, each with three
# Nodes. Each Face carries a thematic axis the GM can lean into for
# fiction prompts and macro flavour.

FACES_AUREA = [
    {
        "id": "luxantia",
        "name": "Luxantia",
        "axis": "Light & Life",
        "core_uses": "light · life · energy · strength",
        "summary": ("The life-giving and energetic aspect of Aurae. "
                    "Healers, hearth-keepers, lantern-walkers, and the "
                    "sun-blessed strike-warriors all draw from Luxantia."),
        "nodes": [
            {"name": "Splendora", "domain": "radiance, illuminate",
             "rank_1": "Reveal, brighten, or signal across a room.",
             "rank_3": "Selective beacons or blinding fields.",
             "failure": "Wild glare · attracts unwanted attention.",
             "tags": ["light", "vision"]},
            {"name": "Vitara", "domain": "quicken, heal",
             "rank_1": "Heal and encourage growth.",
             "rank_3": "Rapid regeneration or fertility of land.",
             "failure": "Overgrowth · uncontrolled vitality bleeds into rot at the edges.",
             "tags": ["healing", "growth"]},
            {"name": "Dynamis", "domain": "strength, energy",
             "rank_1": "Charge body or object with force.",
             "rank_3": "Explosive force or group surge effects.",
             "failure": "Burnout · overload · structural failure of conduits.",
             "tags": ["force", "kinetic"]},
        ],
    },
    {
        "id": "cryptosha",
        "name": "Cryptosha",
        "axis": "Secret & Keep",
        "core_uses": "secrecy · preservation · calm",
        "summary": ("The protective, preserving aspect of Aurae. "
                    "Archivists, peace-wardens, sanctuary keepers, "
                    "and the cult of unseen mercy."),
        "nodes": [
            {"name": "Veila", "domain": "conceal, shroud",
             "rank_1": "Hide messages or persons from sight.",
             "rank_3": "Invisible action or secret-only beacons.",
             "failure": "Inversion · the hider becomes the most visible thing in the room.",
             "tags": ["stealth", "perception"]},
            {"name": "Duravita", "domain": "preserve, endure",
             "rank_1": "Prevent decay and wear on a person or item.",
             "rank_3": "Preserve person, object, or time-trace.",
             "failure": "Stagnation · refusal to age that cracks under any change.",
             "tags": ["time", "endurance"]},
            {"name": "Serenitas", "domain": "soothe, calm",
             "rank_1": "Quiet an area or reduce panic.",
             "rank_3": "Suppress chaos and stabilise rituals.",
             "failure": "Emotional numbness · loss of warning instincts.",
             "tags": ["emotion", "calm"]},
        ],
    },
    {
        "id": "confluo",
        "name": "Confluo",
        "axis": "Gather & Guard",
        "core_uses": "reduction · storage · barriers",
        "summary": ("The gathering and guarding aspect of Aurae. "
                    "Engineers of ward-batteries, vault-makers, and "
                    "shield-line tacticians draw from Confluo."),
        "nodes": [
            {"name": "Reducta", "domain": "condense, draw",
             "rank_1": "Dampen effects · pull energy inward.",
             "rank_3": "Draw from field into focus.",
             "failure": "Drain spreads to allies or the place itself.",
             "tags": ["counter", "drain"]},
            {"name": "Cumulus", "domain": "gather, store",
             "rank_1": "Hold a charge for later release.",
             "rank_3": "Large reservoir or delayed-release mechanism.",
             "failure": "Becomes a Void-magnet · attracts erasure.",
             "tags": ["storage", "battery"]},
            {"name": "Vallum", "domain": "shield, barrier",
             "rank_1": "Wards and personal shields.",
             "rank_3": "Multi-person shields or temple locks.",
             "failure": "Entrapment · the wall guards both sides.",
             "tags": ["barrier", "protection"]},
        ],
    },
    {
        "id": "expanzis",
        "name": "Expanzis",
        "axis": "Spread & Move",
        "core_uses": "expansion · broadcast · movement",
        "summary": ("The mobile, communicative aspect of Aurae. "
                    "Couriers, broadcast-mages, fleet-blessers, "
                    "and rapid-response orders draw from Expanzis."),
        "nodes": [
            {"name": "Kineto", "domain": "shift, move",
             "rank_1": "Speed and shift — kinetic nudge.",
             "rank_3": "Transform trajectory or state.",
             "failure": "Unstable change · shattering on impact.",
             "tags": ["movement", "speed"]},
            {"name": "Diffundere", "domain": "spread, expand",
             "rank_1": "Expand effect to nearby cells.",
             "rank_3": "Area amplification with linked sources.",
             "failure": "Uncontrolled spread · contagion-class incidents.",
             "tags": ["aoe", "spread"]},
            {"name": "Broadcastis", "domain": "amplify, transmit",
             "rank_1": "Transmit messages or shared effects.",
             "rank_3": "Mass transmission across regions.",
             "failure": "Propaganda · the broadcast carries the broadcaster's bias.",
             "tags": ["communication", "broadcast"]},
        ],
    },
]


# ────────────────────────── Faces of Mortiscura ──────────────────────────
# The shadowed / negating face of magic. Four Faces, each with three
# Nodes. Same shape as Aurae but inverted intent — concealment,
# distortion, negation, stasis.

FACES_MORTISCURA = [
    {
        "id": "obscuritia",
        "name": "Obscuritia",
        "axis": "Shadow & Conceal",
        "core_uses": "dimming · deep shadow · total absorption",
        "summary": ("The shadow and anxiety-inducing aspect of Mortiscura. "
                    "Cultists of the Veil, fear-priests, and Morrigan-haunted "
                    "operatives draw from Obscuritia."),
        "nodes": [
            {"name": "Penumbra", "domain": "dim, soften light",
             "rank_1": "Conceal edges · zones of uncertainty.",
             "rank_3": "Extensive penumbra fields that swallow detail.",
             "failure": "Paranoia · onlookers cannot trust what they see.",
             "tags": ["shadow", "perception"]},
            {"name": "Umbros", "domain": "deep shadow",
             "rank_1": "Localised darkness fields.",
             "rank_3": "Shadow passage · fear auras.",
             "failure": "Morrigan resonance — the shadow looks back.",
             "tags": ["shadow", "fear"]},
            {"name": "Voidalis", "domain": "total absorption",
             "rank_1": "Small void pocket — eats light.",
             "rank_3": "Persistent void wells that drink magic.",
             "failure": "Azazel resonance · Azazel-aware artifacts orient toward the caster.",
             "tags": ["void", "absorption", "azazel-risk"]},
        ],
    },
    {
        "id": "spectros",
        "name": "Spectros",
        "axis": "Distort & Mimic",
        "core_uses": "false image · false sense · mimicry",
        "summary": ("The distorting and fear-inducing aspect of Mortiscura. "
                    "Spies, doppelgangers, sense-thieves, and Wraith-handlers "
                    "draw from Spectros."),
        "nodes": [
            {"name": "Illusio", "domain": "false image",
             "rank_1": "Decoys or visual masks.",
             "rank_3": "Scene-scale deception.",
             "failure": "Self-doubt · the caster can't trust their own senses.",
             "tags": ["illusion", "sight"]},
            {"name": "Miragea", "domain": "false senses",
             "rank_1": "Sensory misreading — taste / smell / touch.",
             "rank_3": "Memory-sense distortion of bystanders.",
             "failure": "Identity confusion · 'where am I' moments.",
             "tags": ["illusion", "memory"]},
            {"name": "Dopplis", "domain": "mimic, copy",
             "rank_1": "Copy sound or form briefly.",
             "rank_3": "Identity echoes that act independently.",
             "failure": "Replacement paranoia · the echo refuses to dismiss.",
             "tags": ["illusion", "identity"]},
        ],
    },
    {
        "id": "exutus",
        "name": "Exutus",
        "axis": "Purge & Negate",
        "core_uses": "purge · negate · eradicate",
        "summary": ("The negating and eradicating aspect of Mortiscura. "
                    "Magic-breakers, dead-zone tacticians, anti-paladins "
                    "of the Unmaker draw from Exutus."),
        "nodes": [
            {"name": "Expurgate", "domain": "purge energy",
             "rank_1": "Remove taint from a small area.",
             "rank_3": "Strip magic from places or people.",
             "failure": "Overpurge · removes friendly enchantments too.",
             "tags": ["counter", "purge"]},
            {"name": "Nullifi", "domain": "negate, cancel",
             "rank_1": "Briefly shut down artifacts.",
             "rank_3": "Persistent dead zones — radius nullification.",
             "failure": "Spreading null — caster's own gear stops working.",
             "tags": ["counter", "null"]},
            {"name": "Vanis", "domain": "eradicate, make absent",
             "rank_1": "Erase a single trace cleanly.",
             "rank_3": "Erase persons, memories, or events from local record.",
             "failure": "Permanent loss · cannot be reversed by anything but Azazel.",
             "tags": ["counter", "erase", "azazel-risk"]},
        ],
    },
    {
        "id": "stasis",
        "name": "Stasis",
        "axis": "Halt & Bind",
        "core_uses": "slow · rigid · halt",
        "summary": ("The slowing and halting aspect of Mortiscura. "
                    "Jail-mages, time-binders, and ward-locks that "
                    "outlast empires draw from Stasis."),
        "nodes": [
            {"name": "Inerto", "domain": "slow",
             "rank_1": "Reduce motion · area drag.",
             "rank_3": "Stagnant body or mind states.",
             "failure": "Stagnation creep · caster slows along with the target.",
             "tags": ["debuff", "slow"]},
            {"name": "Rigis", "domain": "immobilize, rigid",
             "rank_1": "Hold a target or object briefly.",
             "rank_3": "Brittle stillness — anything pushed back shatters.",
             "failure": "Shatter under force · explosive release of stored bind.",
             "tags": ["control", "hold"]},
            {"name": "Lockis", "domain": "freeze, halt change",
             "rank_1": "Pause a small process.",
             "rank_3": "Temporal locks · ritual time-out states.",
             "failure": "Chain Lock — the freeze becomes persistent and locks the caster too.",
             "tags": ["time", "control"]},
        ],
    },
]


# ──────────────────────── Cosmological Opposition ────────────────────────
# Natural-opposition table for the encounter chat roller. Each row is
# directional: the FIRST listed Face is the *attacker / acting party*,
# the SECOND is the *defender / resisting party*. Magnitude is one of:
#
#   "edge"      → attacker gets +d4 on their action roll (small advantage)
#   "advantage" → attacker rolls 2d20 take higher (D&D-style adv)
#   "obstacle"  → attacker's difficulty +1 step (Cypher-style hinder)
#   "neutral"   → no built-in modifier
#
# When the roller surfaces a tension, the GM still adjudicates fiction
# (a Luxantia healer DOES get edge against a Stasis warden, but if the
# warden has stacked Vallum barriers in advance, the GM can downgrade).
#
# Reflexive principle (lifted from the bible chunk-09 lore): each Aurae
# Face has a "complementary opposite" Mortiscura Face — the pair that
# directly negates the other's core verb. Cross-pair tensions exist
# but degrade by one magnitude step.

OPPOSITION = [
    # ── Direct opposites (the four cardinal axes) ──
    # Luxantia (Light & Life) ↔ Obscuritia (Shadow & Conceal)
    {"attacker": "luxantia",  "defender": "obscuritia", "magnitude": "advantage",
     "note": "Light scatters shadow — direct cosmological clash. Aurae caster has clear edge."},
    {"attacker": "obscuritia","defender": "luxantia",   "magnitude": "advantage",
     "note": "Shadow swallows light at its source — Mortiscura answers with corruption of vision."},

    # Cryptosha (Secret & Keep) ↔ Spectros (Distort & Mimic)
    {"attacker": "cryptosha", "defender": "spectros",  "magnitude": "advantage",
     "note": "Preservation reveals lies — illusions crack under Cryptosha's steady gaze."},
    {"attacker": "spectros",  "defender": "cryptosha", "magnitude": "advantage",
     "note": "Distortion fractures the kept secret — Spectros rewrites what Cryptosha protects."},

    # Confluo (Gather & Guard) ↔ Exutus (Purge & Negate)
    {"attacker": "confluo",   "defender": "exutus",    "magnitude": "advantage",
     "note": "Gathered force overwhelms negation — barriers stand against the Unmaker's purge."},
    {"attacker": "exutus",    "defender": "confluo",   "magnitude": "advantage",
     "note": "Negation strips the barrier — Exutus exists to undo what Confluo builds."},

    # Expanzis (Spread & Move) ↔ Stasis (Halt & Bind)
    {"attacker": "expanzis",  "defender": "stasis",    "magnitude": "advantage",
     "note": "Motion shatters stillness — Expanzis sweeps past stasis-bound foes."},
    {"attacker": "stasis",    "defender": "expanzis",  "magnitude": "advantage",
     "note": "Stillness halts spread — Stasis nails motion to the floor."},

    # ── Cross-pair edges (one magnitude step down) ──
    # Luxantia vs other Mortiscura Faces
    {"attacker": "luxantia", "defender": "spectros",   "magnitude": "edge",
     "note": "Vitara's growth burns through false sense; Splendora reveals illusion."},
    {"attacker": "luxantia", "defender": "exutus",     "magnitude": "neutral",
     "note": "Life and negation cancel each other — fiction decides the outcome."},
    {"attacker": "luxantia", "defender": "stasis",     "magnitude": "edge",
     "note": "Dynamis breaks rigis-locks; Vitara thaws frozen targets."},

    # Cryptosha vs other Mortiscura Faces
    {"attacker": "cryptosha","defender": "obscuritia", "magnitude": "neutral",
     "note": "Both rely on concealment — meeting in the dark, fiction-led."},
    {"attacker": "cryptosha","defender": "exutus",     "magnitude": "edge",
     "note": "Duravita's preservation resists Vanis's erasure — slow contest."},
    {"attacker": "cryptosha","defender": "stasis",     "magnitude": "obstacle",
     "note": "Serenitas calms but does not move — Stasis matches it stillness-for-stillness."},

    # Confluo vs other Mortiscura Faces
    {"attacker": "confluo",  "defender": "obscuritia", "magnitude": "edge",
     "note": "Vallum's wards block Umbros's shadow passage."},
    {"attacker": "confluo",  "defender": "spectros",   "magnitude": "edge",
     "note": "Cumulus stores true memory — illusions cannot displace it."},
    {"attacker": "confluo",  "defender": "stasis",     "magnitude": "neutral",
     "note": "Both fortify — meeting is siege-pace, fiction-led."},

    # Expanzis vs other Mortiscura Faces
    {"attacker": "expanzis", "defender": "obscuritia", "magnitude": "edge",
     "note": "Broadcastis amplifies signal past Penumbra's dimming."},
    {"attacker": "expanzis", "defender": "spectros",   "magnitude": "obstacle",
     "note": "Diffundere spreads the illusion further when it touches Spectros — backfire risk."},
    {"attacker": "expanzis", "defender": "exutus",     "magnitude": "edge",
     "note": "Kineto outruns Nullifi's null radius before it locks."},

    # ── Forbidden / strained pairings (from per-node bible chunks) ──
    # These trigger when BOTH the attacker AND defender are casting the
    # listed face's specific nodes. The roller flags these even when
    # the face-level table would say "neutral".
]


# Lookup helpers — the route layer calls these.

def _by_id(faces, fid):
    for f in faces:
        if f["id"] == fid:
            return f
    return None


def get_face(fid: str):
    """Return the Face dict (Aurae or Mortiscura) by id, or None."""
    return _by_id(FACES_AUREA, fid) or _by_id(FACES_MORTISCURA, fid)


def get_opposition(attacker_id: str, defender_id: str) -> dict:
    """Lookup the cosmological-tension row for an attacker/defender
    Face pair. Returns the row dict (with `note` for GM display) or
    a synthetic `neutral` row when no entry exists.
    """
    for row in OPPOSITION:
        if row["attacker"] == attacker_id and row["defender"] == defender_id:
            return row
    return {
        "attacker": attacker_id,
        "defender": defender_id,
        "magnitude": "neutral",
        "note": "No canon tension. Fiction-led adjudication.",
    }


def get_cosmology_payload() -> dict:
    """Single bundle for /api/cosmology/evereantha — consumed by both
    the Magic Architect quick-ref and the encounter chat roller."""
    return {
        "version": "v1",
        "source": "Evereantha bible v3 — chunk-09 + per-node chunks 05-21",
        "aurae": FACES_AUREA,
        "mortiscura": FACES_MORTISCURA,
        "opposition": OPPOSITION,
        "magnitude_legend": {
            "advantage": "+1 step / 2d20 take-higher · direct cosmological clash",
            "edge":      "+d4 to the action roll · partial tension",
            "neutral":   "no built-in modifier · fiction decides",
            "obstacle":  "+1 difficulty step · backfire-risk pairing",
        },
    }
