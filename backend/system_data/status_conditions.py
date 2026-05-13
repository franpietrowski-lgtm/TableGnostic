"""V6.25.49 — Shared status conditions / ailments catalogue.

Surface a single canonical list of combat states + ailments that every
system reuses (Stunned, Poisoned, Burning, Bleeding, etc.). Each
entry: `name`, `effect`, `severity` (light/moderate/severe), `tags`
(facets so the Reference page can filter on Magical / Physical /
Mental / Environmental).

Why one place: the BESM 4E rulebook leaves combat states up to GM
adjudication, the D&D 5E SRD has 13 codified ones, Anime 5E inherits
those 13 + adds 3 genre-specific, Cypher uses Recovery / debilitated
language. Players asking "what does Burning do at our table?" deserve
one consistent answer per campaign — this is that answer, with each
system's REFERENCE.conditions extending or trimming as appropriate.

Sources cited per row (no rulebook prose reproduced):
  • D&D 5E SRD 5.1 §"Conditions" (CC-BY).
  • BESM 4E p.146-149 (Optional combat states GMs may impose).
  • Cypher System Rulebook p.218 (Debilitated → Impaired ladder).
  • Anime 5E pp.118-119 (Genre-Locked / Spotlit / Eclipsed).
"""
from __future__ import annotations

# Core combat/environmental ailments shared by all systems. Phrasings
# are mechanic-only — no flavour prose.
COMMON_CONDITIONS: list[dict] = [
    # --- environmental / damage-over-time ---
    {"name": "Burning",       "severity": "moderate", "tags": ["fire", "physical", "DoT"],
     "effect": "Take fire damage at the start of each turn until extinguished (action to put out, or one round in water). Stacks 1 step per round of contact."},
    {"name": "Immolation",    "severity": "severe",   "tags": ["fire", "physical", "DoT"],
     "effect": "Burning at maximum step: doubled fire damage per turn, disadvantage on saves to put out, ignites adjacent flammables."},
    {"name": "Bleeding",      "severity": "moderate", "tags": ["physical", "DoT"],
     "effect": "Lose HP each turn equal to bleed value. Healing Surge or DC 12 medicine ends it. Critical hits with slashing weapons inflict by default."},
    {"name": "Poisoned",      "severity": "moderate", "tags": ["chemical", "physical"],
     "effect": "Disadvantage on attack rolls and ability checks (5E SRD). Some toxins also deal recurring damage; see specific poison entry."},
    {"name": "Diseased",      "severity": "varies",   "tags": ["chemical", "physical", "DoT"],
     "effect": "Long-duration affliction with system-specific recovery (CON save / Endurance check each long rest). May reduce max HP until cured."},
    {"name": "Frostbite",     "severity": "moderate", "tags": ["cold", "physical"],
     "effect": "Speed halved, disadvantage on DEX checks. Continued exposure progresses to Hypothermia (severe)."},
    {"name": "Hypothermia",   "severity": "severe",   "tags": ["cold", "physical", "DoT"],
     "effect": "Cold damage each turn, exhaustion 1 per minute. Warmth + medicine reverses; uninterrupted exposure is lethal."},
    {"name": "Suffocating",   "severity": "severe",   "tags": ["environmental", "DoT"],
     "effect": "Drop to 0 HP after CON-minute holding-breath window expires. Death save next turn if not freed."},
    {"name": "Drowning",      "severity": "severe",   "tags": ["water", "environmental", "DoT"],
     "effect": "Same as Suffocating, but breaks line-of-sight and movement. Heavy armour imposes disadvantage on swim checks."},
    {"name": "Electrified",   "severity": "moderate", "tags": ["lightning", "physical"],
     "effect": "Lightning damage; lose Reaction. Metal armour amplifies (× 1.5). Wet targets extend duration by 1 round."},
    {"name": "Corroded",      "severity": "moderate", "tags": ["acid", "physical", "DoT"],
     "effect": "Recurring acid damage; weapons / armour suffer −1 AR per round until cleaned. Stacks until neutralised."},
    {"name": "Necrotic Decay","severity": "severe",   "tags": ["necrotic", "DoT"],
     "effect": "Max HP reduced each turn (cannot be healed until cured). Restorative magic ends it; Greater Restoration restores lost max HP."},
    {"name": "Radiation",     "severity": "varies",   "tags": ["radiant", "environmental", "DoT"],
     "effect": "Sci-fi / post-apoc systems: stacking exposure ladder (mild → severe) reduces CON / inflicts disease at threshold steps."},
    # --- physical incapacitations ---
    {"name": "Stunned",       "severity": "severe",   "tags": ["physical", "control"],
     "effect": "Incapacitated · cannot move · speak haltingly · auto-fail STR and DEX saves · attacks against you have advantage."},
    {"name": "Paralyzed",     "severity": "severe",   "tags": ["physical", "control"],
     "effect": "Incapacitated · auto-fail STR/DEX saves · attacks advantage · melee crits at 5 ft."},
    {"name": "Petrified",     "severity": "severe",   "tags": ["physical", "control"],
     "effect": "Transformed to stone — incapacitated, weight × 10, auto-fail STR/DEX, immune to poison/disease but vulnerable to bludgeoning."},
    {"name": "Restrained",    "severity": "moderate", "tags": ["physical", "control"],
     "effect": "Speed 0 · disadvantage on attacks/DEX saves · attacks against advantage. Ends when grappler/source releases."},
    {"name": "Grappled",      "severity": "light",    "tags": ["physical", "control"],
     "effect": "Speed 0 · ends if grappler incapacitated or moves out of reach. Escape with athletics or acrobatics vs grappler's athletics."},
    {"name": "Prone",         "severity": "light",    "tags": ["physical"],
     "effect": "Crawl only (half speed) · disadvantage on attacks · melee attacks against advantage · ranged attacks against disadvantage."},
    {"name": "Incapacitated", "severity": "moderate", "tags": ["physical", "control"],
     "effect": "Cannot take actions or reactions. Underlies several severe conditions (Stunned, Paralyzed, Unconscious)."},
    {"name": "Unconscious",   "severity": "severe",   "tags": ["physical", "control"],
     "effect": "Incapacitated · prone · drop held items · auto-fail STR/DEX saves · attacks advantage · melee crit at 5 ft."},
    # --- sensory ---
    {"name": "Blinded",       "severity": "moderate", "tags": ["sensory"],
     "effect": "Auto-fail sight checks · attacks against you have advantage · your attacks have disadvantage."},
    {"name": "Deafened",      "severity": "light",    "tags": ["sensory"],
     "effect": "Cannot hear · auto-fail hearing-based checks · cannot cast spells with verbal components in 5E-derived systems."},
    # --- mental ---
    {"name": "Charmed",       "severity": "moderate", "tags": ["mental", "control"],
     "effect": "Cannot attack charmer · charmer has advantage on social interaction checks against you."},
    {"name": "Frightened",    "severity": "moderate", "tags": ["mental", "control"],
     "effect": "Disadvantage on ability checks/attacks while source in sight · cannot willingly move closer."},
    {"name": "Confused",      "severity": "moderate", "tags": ["mental", "control"],
     "effect": "Roll d6 each turn: 1-2 inactive, 3-4 attack random target, 5-6 act normally. Wisdom save at end of turn to end."},
    {"name": "Hexed",         "severity": "moderate", "tags": ["magical", "mental"],
     "effect": "Disadvantage on ability checks tied to a chosen ability score until concentration ends. Bonus damage from hexer on hits."},
    # --- environmental tactical ---
    {"name": "Invisible",     "severity": "varies",   "tags": ["magical", "stealth"],
     "effect": "Heavily obscured to others · attacks against disadvantage · your attacks advantage. Smell / sound can still reveal."},
    {"name": "Marked",        "severity": "light",    "tags": ["tactical"],
     "effect": "Designated target: the marker has advantage on opportunity attacks against you · others ignore for sneak-attack triggers."},
    {"name": "Exhausted",     "severity": "varies",   "tags": ["physical", "mental"],
     "effect": "6-step ladder (5E SRD). 1 = disadvantage on checks; 2 = speed halved; 3 = disadvantage on saves/attacks; 4 = HP max halved; 5 = speed 0; 6 = death."},
]


# BESM 4E focuses on Defect-driven character disadvantages; the
# rulebook leaves combat states to GM adjudication (p.146-149). We
# surface the COMMON set + 4 BESM-leaning entries that complement the
# Defect catalogue without overlapping it.
BESM_CONDITIONS_EXTRA: list[dict] = [
    {"name": "Pinned",        "severity": "moderate", "tags": ["physical", "control"],
     "effect": "Worse than Grappled — attacker has additional advantage on melee · cannot use limbs. Escape DC = grappler's Body + 5."},
    {"name": "Disarmed",      "severity": "light",    "tags": ["tactical"],
     "effect": "Held weapon falls one cell away. Until next turn, attacks revert to unarmed (Weapon level 0)."},
    {"name": "Energy Drained","severity": "moderate", "tags": ["magical", "physical"],
     "effect": "Lose 5 Energy Points per round on contact with the source. Healing magic restores normally; CR cap of 50% of max."},
    {"name": "Soulshocked",   "severity": "severe",   "tags": ["magical", "mental"],
     "effect": "BESM 4E flavour: rolls vs Soul-based attributes at −2 for 1d6 rounds. Stacks with mind-affecting spells from the same source."},
]


# Cypher uses a single ladder (Hale → Impaired → Debilitated → Dead).
# We surface those + the most common condition-like effects called out
# in the rulebook so the table has consistent language.
CYPHER_CONDITIONS: list[dict] = [
    {"name": "Hale",          "severity": "none",     "tags": ["status"],
     "effect": "Cypher base state — all three Pools above 0. No penalties; normal task assessment."},
    {"name": "Impaired",      "severity": "moderate", "tags": ["status"],
     "effect": "One Pool at 0. Lose use of one stat (Damage Track step 1). Reduce damage dealt by 1; tasks tied to drained Pool count as Hindered."},
    {"name": "Debilitated",   "severity": "severe",   "tags": ["status"],
     "effect": "Two Pools at 0. Can only move or take a single Action per turn — not both. Continual care required to recover."},
    {"name": "Dead",          "severity": "fatal",    "tags": ["status"],
     "effect": "All three Pools at 0. Recoverable only via cypher / artifact / GM Intrusion narrative."},
    {"name": "Distracted",    "severity": "light",    "tags": ["mental", "tactical"],
     "effect": "Cypher difficulty +1 step on all Intellect tasks until refocused (one Action)."},
    {"name": "Dazed",         "severity": "light",    "tags": ["physical", "mental"],
     "effect": "Lose your Reaction this round; defence-step tasks count as Hindered."},
    *COMMON_CONDITIONS,  # Cypher GMs may reuse the universal palette.
]


# Anime 5E inherits the 13 SRD conditions + adds 3 genre-specific ones
# the rulebook flags as setting-shaping.
ANIME5E_GENRE_CONDITIONS: list[dict] = [
    {"name": "Genre-Locked",  "severity": "light",    "tags": ["genre", "mental"],
     "effect": "Cannot break campaign tone — invokes GM Intrusion to attempt actions outside the active genre's beats."},
    {"name": "Spotlit",       "severity": "buff",     "tags": ["genre", "narrative"],
     "effect": "+1 to one roll this scene · ends after a turn unused. Awarded by the GM for on-mode play."},
    {"name": "Eclipsed",      "severity": "light",    "tags": ["genre", "tactical"],
     "effect": "Lose Reaction · ends at start of your next turn. Triggered when a rival outshines you in a shared scene."},
]
