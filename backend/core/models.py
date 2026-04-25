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
    # ---------- V3.5 — Campaign Benchmarks ----------
    genre: str = ""           # "High Fantasy", "Cyberpunk", etc.
    time_period: str = ""     # "Medieval", "Modern", etc.
    default_character_size: str = "Medium"  # BESM 4E size template
    damage_rating_baseline: int = 5         # DM formula base


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


class CharacterAttribute(BaseModel):
    name: str
    level: int = 1
    cost_per_level: float
    enhancements: List[str] = []
    limiters: List[str] = []
    custom_attribute_id: Optional[str] = None
    page: Optional[int] = None
    note: Optional[str] = ""
    # Item / Weapon-class Attributes may carry their own Defects.
    defects: List[CharacterDefect] = []
    # Optional Size template — "" means inherit the character's size.
    size: str = ""


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
    components: List[CharacterSkillComponent] = []


class CharacterPowerPack(BaseModel):
    """Narrative grouping of a character's powers / materials / training tied
    to a single in-setting source. Defaults to free; GM may set a cost."""
    name: str
    description: str = ""
    references: List[str] = []
    cost: int = 0


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
    notes: str = ""
    published: bool = False
    folio: Dict[str, Any] = Field(default_factory=dict)


class JournalEntryIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None


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


# -------- Custom rules + Genesis --------

class CustomAttributeIn(BaseModel):
    campaign_id: str
    kind: Literal["attribute", "defect", "skill"]
    name: str
    cost_per_level: float = 1
    category: Optional[str] = None
    page_ref: Optional[str] = None
    description_note: str = ""


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
    beginning: str = ""
    ending: str = ""
    phase_completed: int = 0
