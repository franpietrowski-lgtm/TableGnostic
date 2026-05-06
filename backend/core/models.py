"""All Pydantic request/response models for Table-Gnostic."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# -------- Auth --------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=80)
    role: Literal["player", "gm"] = "player"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=6)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    byline_name: Optional[str] = None  # full name as it should appear on PDF exports


class ProfilePatchIn(BaseModel):
    """Self-edit via PATCH /api/auth/me — byline + avatar + bio."""
    byline_name: Optional[str] = Field(default=None, max_length=120)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = Field(default=None, max_length=2000)


class PasswordChangeIn(BaseModel):
    """In-app password change — requires the current password."""
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=200)


# -------- Campaign --------

class CampaignIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    system: str = "BESM 4E"
    # Game-system selector. Non-BESM systems show a 'content coming soon'
    # placeholder in BESM-specific surfaces while still letting the GM run
    # worldbuilding, sessions, and AV seats normally.
    system_id: str = "besm-4e"
    tone: Optional[str] = None
    tags: List[str] = []
    experience_level: Optional[str] = "Any"
    schedule: Optional[str] = None
    max_players: int = 6
    visibility: Literal["public", "private"] = "public"
    power_level: str = "Heroic"
    # Player primer + allow/prohibit lists (empty = all allowed)
    player_primer: str = ""
    allowed_attributes: List[str] = []
    prohibited_attributes: List[str] = []
    allowed_defects: List[str] = []
    prohibited_defects: List[str] = []
    allowed_skill_groups: List[str] = []
    prohibited_skill_groups: List[str] = []
    # GM Primer caps — override the Power Level point budget for this table.
    # 0 means "no override" and the Power Level's default point budget applies.
    character_point_min: int = 0
    character_point_max: int = 0
    # Hard cap on the Level of any single Attribute (0 = no cap)
    max_per_attribute_rank: int = 0
    # V6.25.6 — Cut B chat hot-key toggles. Defaults to ON so the
    # /cast, /use bundle, /spend xp commands work out of the box.
    # GM can flip this off if their table prefers a strict no-meta
    # PBP feel.
    xp_marketplace: bool = True
    # ---------- V3.5 — Campaign Benchmarks ----------
    genre: str = ""           # "High Fantasy", "Cyberpunk", etc.
    time_period: str = ""     # "Modern", "Medieval", etc.
    default_character_size: str = "Medium"  # BESM 4E size template
    damage_rating_baseline: int = 5         # DM formula base
    # ---------- V4.6 — Per-licence setting tagging ----------
    # Free-text setting name (e.g. "Aurea", "Godforsaken", "The Heartwood",
    # "Eberron-inspired"). Used by the PDF export pipeline to gate exports
    # against forbidden-settings lists for licence-restricted systems.
    setting_name: str = ""
    # ---------- V5.2 — Cypher genre-gating ----------
    # When the system is `cypher`, the genre key from `SETTING_GENRES` filters
    # the Descriptors / Foci picker so the table sees only setting-appropriate
    # entries. Empty / "any" = no filter.
    setting_genre: str = ""
    # ---------- V5.2 — System-aware Player Primer caps ----------
    # D&D / Anime 5E: minimum starting level a player may forge.
    primer_level_min: int = 1
    # Cypher: suggested starting Tier (1..6).
    primer_tier_suggest: int = 1
    # System-agnostic: hard cap on XP a freshly-forged character may carry.
    primer_xp_cap: int = 0
    # Free-text house rules — surfaced in the primer card.
    house_rules: str = ""
    # V6.4 / V6.21 — Anime 5E DP→character-point formula.
    # RAW default per Anime 5E core p.20: 80 + (level − 1).
    # GM overrides:
    #   * "raw"    — 80 + (level − 1). The core rulebook default.
    #   * "flat"   — Flat 80 DP at every level (no per-level bonus).
    #   * "curve"  — Heroic: 80 + 2 × (level − 1). Extra DP per level
    #                for a more powerful party.
    #   * "tier"   — Legacy V6.19 tier brackets (10/20/40/60/80).
    #                Preserved for back-compat with pre-V6.21 campaigns.
    anime5e_xp_formula: Literal["raw", "flat", "curve", "tier"] = "raw"
    # V6.13 — Canon Registry. GMs may publish their campaign to the public
    # Canon Registry so fellow GMs can discover its Delta Drops and
    # subscribe. Does NOT expose player seats — that's `visibility=public`.
    canon_published: bool = False
    canon_blurb: str = ""   # short pitch shown on the registry card
    # V6.21 — GM/Player consent flow. When true, members must tick the
    # primer acknowledgement (via `POST /api/campaigns/{cid}/consent`)
    # before their character sheet becomes editable.
    consent_required: bool = False


class CampaignOut(CampaignIn):
    id: str
    gm_id: str
    gm_name: str
    member_ids: List[str] = []
    created_at: str


class JoinIn(BaseModel):
    message: Optional[str] = ""


# -------- Character --------

class CharacterStats(BaseModel):
    body: int = 4
    mind: int = 4
    soul: int = 4


class CharacterDefect(BaseModel):
    name: str
    rank: int = 1
    points_per_rank: int
    category: str
    page: Optional[int] = None
    note: Optional[str] = ""
    display_name: Optional[str] = ""
    # V6.4 — structured value (BESM Extras ch.3 allows defects to be
    # rated beyond the canonical 1/2-pt scale for Absolute Power /
    # Silver-Age Sentinels-style campaigns). Default 0 = inherit
    # points_per_rank × rank; a non-zero `value` overrides and stamps the
    # explicit CP refund.
    value: int = 0
    # V6.25.3 — when a row originates from an applied BESM race / class
    # template, this carries the template's custom_attribute id so the
    # sheet can group / revert cleanly.
    from_template_id: Optional[str] = None


class ModifierRow(BaseModel):
    """BESM 4E V4.1 / Extras ch.3 — an Enhancement or Limiter applied to
    an Attribute. Each row is exactly ONE application; stack by listing
    multiple rows.

    * `value` is the effective-level delta this modifier imposes.
      Canonical scale is −12 to +12 (BESM Extras ch.3); Absolute Power
      supplements can push beyond. We WARN beyond ±12 but do not block.
    * Sign convention: positive value = the modifier INCREASES effective
      level (Limiter-like — narrower scope, more potent per CP).
      Negative = DECREASES (Enhancement-like — broader scope, more CP/lvl).
      This matches the character validator's CP path.
    """
    name: str
    value: int = 0
    note: str = ""


class CharacterAttribute(BaseModel):
    name: str
    level: int = 1
    cost_per_level: float
    # V6.4 — Enhancements / Limiters can now be strings (legacy) OR
    # ModifierRow objects ({name, value, note}). The validator treats
    # a bare string as {name: s, value: +1 for limiter, -1 for enhancement}.
    enhancements: List[Any] = []
    limiters: List[Any] = []
    custom_attribute_id: Optional[str] = None
    page: Optional[int] = None
    note: Optional[str] = ""
    display_name: Optional[str] = ""
    # Item / Weapon-class Attributes may carry their own Defects.
    defects: List[CharacterDefect] = []
    # Optional Size template — "" means inherit the character's size.
    size: str = ""
    # V6.4 — effective-level tracking. `effective_level` is the final
    # functional level after all enhancement/limiter value deltas are
    # applied; `cost_modifier` is the per-level cost multiplier after
    # the same deltas (Flight Lvl 1 (4) → cost_modifier 4). If both are
    # left at 0/None the validator computes them on the fly.
    effective_level: Optional[int] = None
    cost_modifier: Optional[int] = None
    # V6.25.3 — applied BESM race / class template provenance.
    from_template_id: Optional[str] = None


class CharacterSkillComponent(BaseModel):
    name: str
    level: int = 1
    note: str = ""


class CharacterSkill(BaseModel):
    group: str
    level: int = 1
    cost_per_level: int
    page: Optional[int] = None
    note: str = ""
    display_name: Optional[str] = ""
    components: List[CharacterSkillComponent] = []
    # V6.25.3 — applied BESM race / class template provenance.
    from_template_id: Optional[str] = None


class CharacterPowerPack(BaseModel):
    """**Power Pack** (BESM Extras ch.5) — a narrative source-of-power
    cluster of Attributes/Skills/Defects bought once and ALWAYS ACTIVE.
    Think "Enchanted Armor Set" or "Cybernetic Implant Rig" — the CP cost
    is paid once, the effects are baseline-on-forever until the source is
    removed narratively (armor sundered, implant disabled).

    For SPELL-LIKE / ACTIVATABLE effects (Fireball, Cure Wounds), use
    `CharacterPowerBundle` instead — those have invocation costs.
    """
    name: str
    description: str = ""
    references: List[str] = []
    cost: int = 0
    # V6.4 — explicit kind marker for clarity in the sheet UI.
    kind: Literal["power_pack"] = "power_pack"


class CharacterPowerBundle(BaseModel):
    """**Power Bundle** (BESM Extras ch.5) — a spell-like / activatable
    packet of Attribute effects that the character invokes in play.

    Unlike a Power Pack (always-on), a Bundle:
    * Is dormant until invoked (GM narration or action economy).
    * Consumes a resource — energy points, a charge, a round of casting,
      or a to-hit/to-invoke roll — declared via `invocation`.
    * Can have per-scene / per-day / per-encounter limits via `charges`.

    Typical uses: D&D spells adapted via Anime 5E Spell Conversions (see
    `/app/memory/references/Anime_5E_Spell_Conversions.pdf`).
    """
    name: str
    description: str = ""
    references: List[str] = []
    cost: int = 0
    kind: Literal["power_bundle"] = "power_bundle"
    # Invocation — how the bundle is activated in play.
    # * always-on        — baseline active (use Power Pack instead).
    # * per-scene        — once per scene / encounter.
    # * per-charge       — consumes a charge from a finite pool.
    # * per-day          — once per in-game day (recharges on long rest).
    # * roll-to-invoke   — requires a skill check or casting roll.
    # * energy-cost      — spends N Energy Points / Mana per invocation.
    invocation: Literal["always-on", "per-scene", "per-charge", "per-day",
                         "roll-to-invoke", "energy-cost"] = "per-scene"
    charges_max: int = 0   # 0 = no charge cap
    charges_current: int = 0
    energy_cost: int = 0   # energy/EP/mana spent per invocation
    cooldown: str = ""     # free-text ("1 round", "5 minutes", "long rest")
    # For D&D-spell-mimic bundles seeded from the conversion PDF.
    source_spell_name: str = ""
    source_spell_level: Optional[int] = None  # 0 (cantrip) .. 9


class CharacterIn(BaseModel):
    campaign_id: str
    name: str
    concept: str = ""
    power_level: str = "Heroic"
    total_points: int = 120
    size: str = "Medium"
    token_color: str = ""
    stats: CharacterStats = CharacterStats()
    attributes: List[CharacterAttribute] = []
    defects: List[CharacterDefect] = []
    skills: List[CharacterSkill] = []
    power_packs: List[CharacterPowerPack] = []
    power_bundles: List[CharacterPowerBundle] = []
    notes: str = ""
    published: bool = False
    folio: Dict[str, Any] = Field(default_factory=dict)
    # V6.9 — Companion / sidekick assignment. Players whose user_id is in this
    # list are allowed to MOVE this character's token on the battlemap and
    # view its sheet read-only. The owner (`owner_id`) always retains full
    # control regardless. GM-only field; players cannot self-assign.
    companion_owners: List[str] = Field(default_factory=list)


class JournalEntryIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
    # V5.4 — ecosystem nervous system. Optional plot phase ref so the Pulse
    # panel and Director's Console can correlate journal entries to the
    # campaign's current plot beat. Free-form key (e.g. "epic-7-milestones",
    # "genesis-3-nemesis") to keep it loose for the GM's convenience.
    plot_phase: Optional[str] = None


# V5.4 — NPC motives evolve over the plot timeline.
# Each entry is an append-only diary of what a Codex NPC wants RIGHT NOW
# at a given plot phase — driven by GM intent, journal entries that
# touch the NPC, and Director events. Players never see GM-only motives.
class NodeMotiveIn(BaseModel):
    motive: str = Field(min_length=1, max_length=600)
    plot_phase: Optional[str] = None
    state: Literal["dormant", "active", "thwarted", "achieved", "evolving"] = "active"
    triggered_by: Optional[str] = None  # session_id / journal_entry_id / encounter_id
    visibility: Literal["gm_only", "shared"] = "gm_only"


# -------- Knowledge Web --------

class NodeIn(BaseModel):
    campaign_id: str
    type: str
    title: str
    content: str = ""
    tags: List[str] = []
    visibility: Literal["gm_only", "shared", "revealed"] = "gm_only"
    revealed_to: List[str] = []
    links: List[str] = []
    fields: Dict[str, Any] = Field(default_factory=dict)


class EdgeIn(BaseModel):
    campaign_id: str
    from_node: str
    to_node: str
    label: str = "related"


class NodeRevealIn(BaseModel):
    user_ids: List[str]


# -------- Session room layer --------

class SessionIn(BaseModel):
    campaign_id: str
    title: str
    scheduled_at: Optional[str] = None
    # V5.4 — ecosystem nervous system. Tags this session with the plot
    # phase the table is playing through, so Pulse / Director / Codex
    # views can correlate cross-system activity.
    plot_phase: Optional[str] = None
    location: Optional[str] = None  # free-text in-fiction location
    # V6.11 — explicit timeline position (drag-reorder on the Timeline
    # panel). Lets prologues / backstory / time-shenanigans sessions sit
    # at any position in the narrative spine, regardless of play date.
    sequence_index: Optional[int] = None


class ChatIn(BaseModel):
    session_id: str
    message: str
    kind: Literal["chat", "ooc", "action", "system"] = "chat"


class DiceIn(BaseModel):
    session_id: str
    notation: str  # "2d6+Body", "1d20", "3d6"
    label: str = ""
    target: Optional[int] = None
    character_id: Optional[str] = None
    private: bool = False


class InitiativeEntryIn(BaseModel):
    session_id: str
    name: str
    character_id: Optional[str] = None
    roll: int = 0
    side: Literal["pc", "npc", "neutral"] = "pc"


class EffectIn(BaseModel):
    session_id: str
    target_name: str
    target_character_id: Optional[str] = None  # Battlemap binding (V4.2)
    name: str
    duration_rounds: int = 1
    note: str = ""


class DamageIn(BaseModel):
    session_id: str
    target_name: str
    amount: int
    kind: Literal["hp", "ep"] = "hp"


class RecapIn(BaseModel):
    style: Literal["narrative", "bullet", "in-character"] = "narrative"


class FinalizeIn(BaseModel):
    recap_node_id: str
    journal_node_ids: List[str] = Field(default_factory=list)
    tone: Literal["lyrical", "terse", "in-character"] = "lyrical"


# -------- Custom rules + Genesis --------

class CustomAttributeIn(BaseModel):
    campaign_id: str
    # V6.25 — Universal homebrew kinds. The frontend CampaignDetail
    # "Custom Rules" tab surfaces system-aware option sets; backend
    # accepts any of them so submissions don't silently 422.
    kind: Literal[
        # BESM / Anime 5E core
        "attribute", "defect", "skill",
        # D&D 5E / Anime 5E
        "feature", "trait", "feat", "house",
        # Cypher
        "descriptor", "focus", "ability", "cypher", "artifact",
        # V6.25 — homebrew structural kinds (BESM Extras style)
        "race", "class", "size", "stat",
    ]
    name: str
    cost_per_level: float = 1
    category: Optional[str] = None
    page_ref: Optional[str] = None
    description_note: str = ""
    # V6.25.2 — numeric impacts the GM declares so homebrew Race /
    # Class entries can influence sheet math. Shape is system-aware
    # and free-form on the backend (frontend owns the schema):
    #   BESM Race/Class:
    #     { "stat_adjustments": {"body": 2, "mind": 1, "soul": 0},
    #       "components": [ {kind, name, level|rank, cost_per_level|points_per_rank, ...} ],
    #       "total_cp": 35 }
    #   D&D/Anime 5E Race:
    #     { "asi": {"Strength": 2, "Dexterity": 1},
    #       "size": "Medium", "speed": 30, "traits": ["Darkvision"] }
    #   D&D/Anime 5E Class:
    #     { "hit_die": 8, "save_profs": ["Strength","Constitution"],
    #       "armor_profs": [...], "weapon_profs": [...] }
    effects: Dict[str, Any] = Field(default_factory=dict)


class GenesisIn(BaseModel):
    """Campaign genesis (Guy Sclanders' Great GM framework — credited)."""
    campaign_id: str
    sentence_who: str = ""
    sentence_wants: str = ""
    sentence_badly_when: str = ""
    sentence_using: str = ""
    sentence_reasons: str = ""
    theme: str = ""
    tone_words: List[str] = []
    nemesis_name: str = ""
    nemesis_type: str = ""
    nemesis_motive: str = ""
    nemesis_resources: str = ""
    nemesis_weakness: str = ""
    master_acts: List[Dict[str, str]] = []
    adventures: List[Dict[str, str]] = []
    seed_npcs: List[Dict[str, str]] = []
    # V6.25 — optional discrete seed buckets so the Genesis materializer
    # can split Locations / Biomes / Factions / Motives into separate
    # codex nodes. Structure: {name, summary, tags?}.
    locations: List[Dict[str, str]] = []
    biomes: List[Dict[str, str]] = []
    factions: List[Dict[str, str]] = []
    motives: List[Dict[str, str]] = []
    beginning: str = ""
    ending: str = ""
    phase_completed: int = 0
