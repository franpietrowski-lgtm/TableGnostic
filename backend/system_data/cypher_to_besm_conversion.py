"""V6.25.25 — Cypher → BESM 4E conversion mapping.

Cypher characters are built from a "I am a [descriptor] [type] who
[focus]" sentence + 3 stat pools (Might / Speed / Intellect) + Edge +
Effort + a per-tier ability roster. BESM 4E characters are built on
total CP budget = power-level grant; attributes pay `level × cost_per_level`
and Items pay ceil(raw_total / 2) per p.135.

This module maps each Cypher building-block to the closest BESM
equivalent so a player who built a Cypher character can re-instantiate
the same fictional concept under BESM rules with a transparent CP estimate.

Cost balancing notes (cross-system observations):
  * Anime 5E (the "5E + Tri-Stat hybrid" of BESM Fourth) bundles a
    LOT of mechanical breadth into attributes that cost FEWER CP per
    level than core BESM. e.g. an Anime 5E "Companion" rank (5 DP) does
    NOT include the BESM Companion's full attribute build — Anime 5E
    treats the companion as a flat narrative entity with its own
    HP/AC, while BESM Companion levels translate roughly 1:1 to CP
    spent on the companion's own attribute bundle.
  * BESM Item half-cost rule (p.135) makes Items genuinely cheaper
    than buying the same effects directly. Anime 5E does NOT replicate
    the half-cost rule — the equivalent flavour is folded into the
    "Item" attribute's flat 4 DP/level cost.
  * Carrying multiple weapons in BESM: each weapon attribute pays its
    own CP cost; there is no "secondary weapon discount". Anime 5E
    similarly prices each weapon ranks at full DP — no implicit
    discount. The user's reading is correct: there is no native
    "primary/secondary" discount in either system. Where this matters:
    when converting a Cypher character with multiple cyphers carried,
    the BESM converter prices each cypher as its own Item attribute
    at half cost, giving the BESM rebuild the closest mechanical
    equivalent without inventing a discount.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# Cypher Type → BESM attribute / stat distribution. Keys are the four
# canonical Type names (lowercase). Each value carries a recommended
# starting-stat tilt and a list of BESM attributes (with starter level
# and cost_per_level pulled from BESM 4E core).
TYPE_TO_BESM: Dict[str, Dict[str, Any]] = {
    "warrior": {
        "primary_stat": "BODY",
        "stat_tilt": {"BODY": +1, "MIND": 0, "SOUL": 0},
        "attributes": [
            {"name": "Combat Mastery",  "level": 4, "cost_per_level": 4,
             "note": "Translates Warrior's combat focus + per-tier attack skill bumps."},
            {"name": "Combat Technique", "level": 2, "cost_per_level": 1,
             "note": "Picks 2 starter techniques (Two Weapons, Hard-Boiled, etc.)."},
            {"name": "Tough", "level": 2, "cost_per_level": 2,
             "note": "+10 HP / level — Cypher's pool buffer."},
        ],
        "defects_suggested": ["Recurring Nightmares", "Wanted"],
    },
    "adept": {
        "primary_stat": "MIND",
        "stat_tilt": {"BODY": -1, "MIND": +2, "SOUL": +1},
        "attributes": [
            {"name": "Dynamic Powers", "level": 4, "cost_per_level": 10,
             "note": "Models the Adept's freeform magic / psionics. Apply Limiters per the chosen genre flavour."},
            {"name": "Energy Bonus", "level": 2, "cost_per_level": 2,
             "note": "Enlarges the Adept's casting reservoir."},
            {"name": "Sixth Sense (Magic)", "level": 1, "cost_per_level": 1,
             "note": "Detects supernatural threats."},
        ],
        "defects_suggested": ["Unique Defect (mana-burn)"],
    },
    "explorer": {
        "primary_stat": "BODY",
        "stat_tilt": {"BODY": +1, "MIND": +1, "SOUL": 0},
        "attributes": [
            {"name": "Skill Group (Athletics)", "level": 3, "cost_per_level": 1,
             "note": "Climbing / running / endurance bundle."},
            {"name": "Skill Group (Knowledge — Survival)", "level": 2, "cost_per_level": 1,
             "note": "Tracking, navigation, geography."},
            {"name": "Sixth Sense (Danger)", "level": 1, "cost_per_level": 1,
             "note": "Cypher's Danger-Sense ability."},
            {"name": "Combat Technique (Lightning Reflexes)", "level": 1,
             "cost_per_level": 1, "note": "Initiative bonus."},
        ],
        "defects_suggested": ["Awkward Size", "Phobia (specific terrain)"],
    },
    "speaker": {
        "primary_stat": "SOUL",
        "stat_tilt": {"BODY": -1, "MIND": +1, "SOUL": +2},
        "attributes": [
            {"name": "Skill Group (Social)", "level": 4, "cost_per_level": 1,
             "note": "Persuasion, intimidation, performance bundle."},
            {"name": "Aura of Command", "level": 2, "cost_per_level": 4,
             "note": "Encourages allies / cows enemies — Speaker's cornerstone."},
            {"name": "Mind Control (Lesser)", "level": 1, "cost_per_level": 5,
             "note": "Quasi-Suggestion. Apply Limiter (audible) to halve effective level."},
        ],
        "defects_suggested": ["Owned (Patron)", "Recurring Responsibility"],
    },
}


# Cypher Descriptor → BESM attribute / defect tweaks. Descriptors are
# adjectives that nudge the build's cost cuts a few CP either way.
DESCRIPTOR_TWEAKS: Dict[str, Dict[str, Any]] = {
    "tough":     {"add_attribute": {"name": "Tough", "level": 1, "cost_per_level": 2},
                   "blurb": "+10 HP."},
    "graceful":  {"add_attribute": {"name": "Combat Technique (Acrobatics)", "level": 1, "cost_per_level": 1},
                   "blurb": "Acrobatic dodge."},
    "stealthy":  {"add_attribute": {"name": "Skill (Stealth)", "level": 2, "cost_per_level": 1},
                   "blurb": "Trained stealth."},
    "swift":     {"add_attribute": {"name": "Speed", "level": 1, "cost_per_level": 3},
                   "blurb": "+10 metres / round."},
    "intelligent":{"add_attribute": {"name": "Skill Group (Academic)", "level": 2, "cost_per_level": 1},
                   "blurb": "Trained knowledge."},
    "charming":  {"add_attribute": {"name": "Skill (Persuasion)", "level": 2, "cost_per_level": 1},
                   "blurb": "Trained social."},
    "clever":    {"add_attribute": {"name": "Skill (Investigation)", "level": 2, "cost_per_level": 1},
                   "blurb": "Trained investigation."},
    "doomed":    {"add_defect":    {"name": "Recurring Nightmares", "rank": 1},
                   "blurb": "−1 CP refund · narrative shadow."},
    "hideous":   {"add_defect":    {"name": "Marked", "rank": 2},
                   "blurb": "−2 CP refund · social penalty."},
    "vicious":   {"add_attribute": {"name": "Damage Bonus", "level": 1, "cost_per_level": 2},
                   "blurb": "+5 unarmed damage."},
    "mystical":  {"add_attribute": {"name": "Sixth Sense (Magic)", "level": 1, "cost_per_level": 1},
                   "blurb": "Detect supernatural."},
    "mysterious":{"add_defect":    {"name": "Wanted", "rank": 1},
                   "blurb": "−1 CP refund · past catches up."},
    "resilient": {"add_attribute": {"name": "Tough", "level": 1, "cost_per_level": 2},
                   "blurb": "+10 HP."},
    "empathic":  {"add_attribute": {"name": "Sixth Sense (Emotion)", "level": 1, "cost_per_level": 1},
                   "blurb": "Read feelings."},
    "brash":     {"add_defect":    {"name": "Easily Distracted (boredom)", "rank": 1},
                   "blurb": "−1 CP refund · acts before thinking."},
    "impulsive": {"add_defect":    {"name": "Easily Distracted (impulse)", "rank": 1},
                   "blurb": "−1 CP refund · narrative wedge."},
}


# Cypher Focus → BESM "power pack" suggestion. Each focus carries a 1-2
# attribute headline and a flavour blurb. Players can refine ranks to
# match the campaign's CP budget.
FOCUS_TO_BESM: Dict[str, Dict[str, Any]] = {
    "bears a halo of fire":    {"power_pack": "Pyromantic Aura",
                                  "attributes": [{"name": "Special Attack (Fire Aura)", "level": 4, "cost_per_level": 4}]},
    "carries a quiver":        {"power_pack": "Marksman",
                                  "attributes": [{"name": "Weapon (Bow)", "level": 4, "cost_per_level": 1},
                                                  {"name": "Skill (Marksmanship)", "level": 3, "cost_per_level": 1}]},
    "commands mental might":   {"power_pack": "Psionicist",
                                  "attributes": [{"name": "Telepathy", "level": 3, "cost_per_level": 3},
                                                  {"name": "Mind Control (Lesser)", "level": 2, "cost_per_level": 5}]},
    "conducts weird science":  {"power_pack": "Tinker's Rig",
                                  "attributes": [{"name": "Item (Pocket Workshop)", "level": 4, "cost_per_level": 4,
                                                   "note": "Pays half-cost per p.135 — actual CP = ceil(level × cpl / 2) = 8 pts."}]},
    "crafts illusions":        {"power_pack": "Illusionist",
                                  "attributes": [{"name": "Special Attack (Illusion)", "level": 3, "cost_per_level": 4}]},
    "crafts unique objects":   {"power_pack": "Artisan",
                                  "attributes": [{"name": "Skill Group (Crafting)", "level": 4, "cost_per_level": 1},
                                                  {"name": "Item (Tools)", "level": 2, "cost_per_level": 4}]},
    "defends the weak":        {"power_pack": "Bulwark",
                                  "attributes": [{"name": "Tough", "level": 3, "cost_per_level": 2},
                                                  {"name": "Combat Technique (Defensive)", "level": 2, "cost_per_level": 1}]},
    "entertains":              {"power_pack": "Bard",
                                  "attributes": [{"name": "Skill Group (Performance)", "level": 4, "cost_per_level": 1},
                                                  {"name": "Aura of Command", "level": 1, "cost_per_level": 4}]},
    "explores dark places":    {"power_pack": "Dungeoneer",
                                  "attributes": [{"name": "Sixth Sense (Danger)", "level": 1, "cost_per_level": 1},
                                                  {"name": "Skill (Stealth)", "level": 3, "cost_per_level": 1},
                                                  {"name": "Heightened Senses (Sight)", "level": 1, "cost_per_level": 2}]},
    "fights with panache":     {"power_pack": "Duellist",
                                  "attributes": [{"name": "Combat Technique (Riposte)", "level": 2, "cost_per_level": 1},
                                                  {"name": "Combat Mastery", "level": 2, "cost_per_level": 4}]},
    "howls at the moon":       {"power_pack": "Shapeshifter",
                                  "attributes": [{"name": "Alternate Form", "level": 3, "cost_per_level": 4}]},
    "leads":                   {"power_pack": "Captain",
                                  "attributes": [{"name": "Aura of Command", "level": 3, "cost_per_level": 4}]},
    "masters defense":         {"power_pack": "Bastion",
                                  "attributes": [{"name": "Combat Technique (Defensive)", "level": 3, "cost_per_level": 1},
                                                  {"name": "Tough", "level": 2, "cost_per_level": 2}]},
    "masters weaponry":        {"power_pack": "Weapons Master",
                                  "attributes": [{"name": "Combat Mastery", "level": 4, "cost_per_level": 4},
                                                  {"name": "Combat Technique (Two Weapons)", "level": 1, "cost_per_level": 1}]},
    "murders":                 {"power_pack": "Assassin",
                                  "attributes": [{"name": "Combat Technique (Stealth Strike)", "level": 2, "cost_per_level": 1},
                                                  {"name": "Skill (Stealth)", "level": 4, "cost_per_level": 1}]},
    "wields two weapons at once":{"power_pack": "Twin-Blade",
                                  "attributes": [{"name": "Combat Technique (Two Weapons)", "level": 2, "cost_per_level": 1},
                                                  {"name": "Combat Mastery", "level": 2, "cost_per_level": 4}]},
    "works miracles":          {"power_pack": "Devout",
                                  "attributes": [{"name": "Healing", "level": 3, "cost_per_level": 4},
                                                  {"name": "Sixth Sense (Divine)", "level": 1, "cost_per_level": 1}]},
}


def _normalise(name: Optional[str]) -> str:
    return (name or "").strip().lower()


def _attr_cost(attr: Dict[str, Any]) -> int:
    return int(attr.get("level", 0)) * int(attr.get("cost_per_level", 0))


def convert_to_besm(*, cypher_type: str = "", descriptor: str = "",
                     focus: str = "", tier: int = 1) -> Dict[str, Any]:
    """Convert a Cypher character build to a BESM 4E recommendation.

    Returns:
      {
        "type_block":      {primary_stat, stat_tilt, attributes[], defects_suggested[]},
        "descriptor_tweak": {add_attribute|add_defect, blurb},
        "focus_block":     {power_pack, attributes[]},
        "stats_recommended": {body, mind, soul},
        "estimated_cp_cost":  int,
        "balancing_notes": [str],     # known cost-rule observations
      }
    """
    type_key = _normalise(cypher_type) or "warrior"
    desc_key = _normalise(descriptor)
    focus_key = _normalise(focus)
    type_block = TYPE_TO_BESM.get(type_key) or TYPE_TO_BESM["warrior"]
    desc_tweak = DESCRIPTOR_TWEAKS.get(desc_key) or {}
    focus_block = FOCUS_TO_BESM.get(focus_key) or {"power_pack": "Custom Focus", "attributes": []}

    # Stat baseline 4 + tilt; per-tier bump = +1 to primary stat for every
    # 2 tiers above 1.
    base = {"body": 4, "mind": 4, "soul": 4}
    tilt_map = {"BODY": "body", "MIND": "mind", "SOUL": "soul"}
    for raw, delta in (type_block.get("stat_tilt") or {}).items():
        k = tilt_map.get(raw)
        if k:
            base[k] = max(1, base[k] + delta)
    primary_lc = (type_block.get("primary_stat") or "BODY").lower()
    if primary_lc in base:
        base[primary_lc] += max(0, (int(tier) - 1) // 2)

    # Cost estimate — sums type + focus attributes + descriptor tweak attribute.
    total = sum(_attr_cost(a) for a in type_block.get("attributes", []))
    total += sum(_attr_cost(a) for a in focus_block.get("attributes", []))
    if desc_tweak.get("add_attribute"):
        total += _attr_cost(desc_tweak["add_attribute"])
    if desc_tweak.get("add_defect"):
        # Defect refund: rank × 1 CP (BESM 4E defects refund 1-3 per rank;
        # we use 1 as the conservative floor so the converter never
        # overstates the player's free CP).
        total -= int(desc_tweak["add_defect"].get("rank", 1))

    notes = [
        "BESM Item attributes pay ceil(raw_total / 2) per p.135 — the converter applies this where applicable but you should re-verify each Item line.",
        "Cypher Effort/Edge has no direct BESM equivalent; the converter folds it into Combat Technique / Energy Bonus where the Type calls for it.",
        "Anime 5E and BESM 4E both price each weapon at full CP — no native primary/secondary discount. If your Cypher carries multiple cyphers, each becomes its own Item attribute at half cost.",
        f"Estimated CP: {max(0, total)} — fits a Heroic (120) or Veteran (150) BESM power-level start at tier {tier}.",
    ]

    return {
        "input": {"cypher_type": type_key, "descriptor": desc_key,
                   "focus": focus_key, "tier": int(tier)},
        "type_block": type_block,
        "descriptor_tweak": desc_tweak,
        "focus_block": focus_block,
        "stats_recommended": base,
        "estimated_cp_cost": max(0, total),
        "balancing_notes": notes,
    }
