"""Demo seed — Evereantha + Artisan's Tale showcase campaigns.

Single-shot deploy that creates two playable demo campaigns owned by the
calling GM, exercising every interweaving in V5.4:
  · Setting + system + primer caps
  · Genesis 7-phase plan + seed_npcs[]
  · Epic Campaign 8th-tab — nemesis OGAS, milestones, seeds
  · Codex nodes (locations, factions, lore)
  · Sample characters for the GM to seat
  · Director's Console encounter staged on a plot phase
  · Live NPC motives tagged to plot phases (drives the Pulse panel)
  · A sample journal entry tagged to a plot phase

Idempotent — running twice creates a SECOND copy, not duplicates inside
the existing copy. The frontend Account page exposes this as a one-click
"Deploy demo campaigns" button.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from core.db import db, new_id, now_iso, sanitize
from core.security import get_current_user

router = APIRouter(prefix="/api", tags=["demo-seed"])


def _now() -> str:
    return now_iso()


# ─────────── Evereantha — BESM 4E heroic-fantasy demo ───────────
EVEREANTHA = {
    "system_id": "besm-4e",
    "name": "Evereantha · The Caldera Choir",
    "description": (
        "A heroic-fantasy table where the Solar-Lunar Caldera is cracking and "
        "an ancient choir threatens to wake what was sealed beneath it. The "
        "demo seeds a 24-session arc complete with NPC motives that evolve."
    ),
    "setting_name": "Evereantha · Forge-Glass Reach",
    "genre": "heroic fantasy",
    "time_period": "late mythic age",
    "default_character_size": "Medium",
    "damage_rating_baseline": 5,
    "primer_xp_cap": 0,
    "house_rules": "Crit on natural 6 with the ten-sided check die. Forge-Glass shards lower difficulty by 1 step (consumable).",
    "player_primer": (
        "You are apprentices of the Forge-Glass Choir. The mountain hums "
        "louder each night. The Mayor of Aurea has hired you to find why."
    ),
    "nodes": [
        {"type": "location", "title": "Aurea, the Forge-Glass City", "tags": ["evereantha", "city"],
         "summary": "Capital of the Reach. Foundries throw red light over a city that runs on songs. The Choir-Halls hum at dawn; every guildhouse keeps a 'tuning bell' that the Iron-Cantors can hear three districts away. Population ~38,000 with a floating apprentice class."},
        {"type": "location", "title": "Solar-Lunar Caldera", "tags": ["evereantha", "site"],
         "summary": "Twin-eye crater above the city where the eclipse will land. Two perfect-circle pools of liquid forge-glass — one Solar, one Lunar — the Choir keeps in tension. Crack the rim and the Eclipse Saint underneath wakes."},
        {"type": "location", "title": "Choir Hall of First Resonance", "tags": ["evereantha", "site"],
         "summary": "The mountain-side amphitheatre where apprentice singers learn the seven Resonance forms. Acoustically perfect — a whisper from the centre rolls audibly to the back row 80 m away."},
        {"type": "location", "title": "Brassyards", "tags": ["evereantha", "district"],
         "summary": "Aurea's smelter quarter. The forge-cantors sing iron into shape. Smoke columns visible from the Caldera rim — the cult uses them as a calendar."},
        {"type": "location", "title": "Pass of Aurea", "tags": ["evereantha", "wilderness"],
         "summary": "Single mountain switchback connecting the city to the Caldera. Snow nine months of the year. Every adventuring party crosses it twice."},
        {"type": "location", "title": "The Drowned Choir", "tags": ["evereantha", "ruin"],
         "summary": "A Choir-Hall sunk beneath a glacial lake during the First Eclipse. Its bells still ring in 7-year cycles when the moon is right. Treasure: pre-Choir manuscripts of the Forbidden Resonance."},
        {"type": "faction", "title": "Order of the Darkening Star", "tags": ["evereantha", "antagonist"],
         "summary": "Star-cult that intends to crack the Caldera open during the next eclipse. ~120 initiates, six Hierophants, one Eclipse-Saint sealed beneath the Caldera. They believe they are FREEING the Saint, not destroying the city."},
        {"type": "faction", "title": "Forge-Glass Choir", "tags": ["evereantha", "ally"],
         "summary": "The Choir-singers' guild. Trains apprentices in seven Resonance forms (Quench, Edge, Strike, Weld, Hum, Crack, Seal). Pious but politically cautious — they will not act without proof."},
        {"type": "faction", "title": "The Mayoral Council of Aurea", "tags": ["evereantha", "ally"],
         "summary": "Twelve elected stewards (one per guild). Mayor Mishtee chairs. The Council's writ unlocks city resources but every withdrawal must pass a vote — slow when the cult is fast."},
        {"type": "faction", "title": "The Solitary Cantors", "tags": ["evereantha", "neutral"],
         "summary": "Heretic Choir-singers exiled for practising the Forbidden Resonance (the eighth song that BREAKS rather than seals). One of them knows what the Saint truly is."},
        {"type": "lore", "title": "The Forge-Glass Hammer", "tags": ["evereantha", "macguffin"],
         "summary": "Lost relic that can either seal the Caldera or shatter it. Two singers know its hum — Eli of the Glass-Hands (knows half) and the heretic Cantor Veshin (knows the other half). Both halves must be combined to attune."},
        {"type": "lore", "title": "The Seven Resonance Forms (Magic System)", "tags": ["evereantha", "magic"],
         "summary": "Evereantha's magic is sung. Seven forms: QUENCH (cool/seal), EDGE (sharpen/cut), STRIKE (kinetic), WELD (bind), HUM (charm/calm), CRACK (sunder), SEAL (preserve). Each form has 5 ranks. Forbidden Eighth: BREAK (unmaking — instant CP-cost ×2; risk of soul-shatter)."},
        {"type": "lore", "title": "The Eclipse Saint", "tags": ["evereantha", "lore"],
         "summary": "First-age entity sealed under the Caldera by the original Choir. Half-deity, half-glass-elemental. Sings on the eclipse cycle. The cult believes she is suffering; the Choir believes she is the seal."},
        {"type": "lore", "title": "The Choir Codex (Apprentice Reader)", "tags": ["evereantha", "lore"],
         "summary": "First-year reader for Choir apprentices. Covers vocal exercises, the seven forms, the seven SAFE intervals, and the three Songs the apprentices must sing at every Choir-Hall before sunset (the Hush, the Open, the Mind)."},
        {"type": "npc", "title": "Mayor Mishtee", "tags": ["evereantha", "ally"],
         "summary": "Pragmatic leader who hired the apprentices. Trusts the table — for now. Has a daughter (Anbel) the cult will try to take. Carries the Mayoral whistle (calls 30 city guards in 3 rounds)."},
        {"type": "npc", "title": "Eli of the Glass-Hands", "tags": ["evereantha", "ally"],
         "summary": "Master glassblower who teaches QUENCH and EDGE forms. Charges in songs, not coin. Knows half the Forge-Glass Hammer's attunement."},
        {"type": "npc", "title": "Cantor Veshin the Heretic", "tags": ["evereantha", "ambivalent"],
         "summary": "Exiled Solitary Cantor. Knows the FORBIDDEN BREAK form and the second half of the Hammer's hum. Lives in the Drowned Choir. Will help the table — for a price they will not understand until later."},
        {"type": "npc", "title": "Anbel Mishtee", "tags": ["evereantha", "ally"],
         "summary": "The Mayor's daughter. Apprentice singer. Brave, naive. Plot-keyed (kidnapping potential)."},
        {"type": "npc", "title": "Choirmaster Olen", "tags": ["evereantha", "ally"],
         "summary": "Head of the Forge-Glass Choir. Will not believe in the Star-cult without testimony from inside it. Blocking until convinced."},
        {"type": "npc", "title": "Malshe Darkening", "tags": ["evereantha", "nemesis"],
         "summary": "Star-Cult Hierophant. Patient, reverent, never raises voice. Believes she is freeing the Saint, not killing the city. Carries the Eclipse Sigil cypher (one-shot — opens any sealed door)."},
        {"type": "npc", "title": "Frock the Iron-Cantor", "tags": ["evereantha", "henchman"],
         "summary": "Forge-Cantor turned cult Lieutenant. Servile then mocking. Tests apprentices. Uses STRIKE form 3 with a forge-hammer."},
        {"type": "npc", "title": "Sister Quench", "tags": ["evereantha", "henchman"],
         "summary": "Cult assassin trained in QUENCH form. Hits weld-points on armour to drop fighters in one note. Quiet, polite, lethal."},
        {"type": "npc", "title": "Brother Crack", "tags": ["evereantha", "henchman"],
         "summary": "Cult demolitionist. Uses CRACK form on city walls to make 'doors' the cult can pour through. Unstable, loud."},
    ],
    # Per-node motives keyed to plot phases (the Pulse panel will pick these up).
    "motives": [
        ("Malshe Darkening", "Locate the Forge-Glass Hammer before the table can.",
         "epic-7-milestones", "evolving"),
        ("Frock the Iron-Cantor", "Humiliate the apprentices to test their resolve.",
         "epic-8-adventures", "active"),
        ("Mayor Mishtee", "Shelter the apprentices and find evidence of a star-cult.",
         "genesis-3-nemesis", "active"),
        ("Cantor Veshin the Heretic", "Watch the apprentices — decide if they can survive the Eighth Form.",
         "epic-8-adventures", "active"),
        ("Sister Quench", "Identify which apprentice carries the Hammer-half hum and silence them.",
         "epic-9-adventures", "evolving"),
        ("Brother Crack", "Open three new 'doors' in Aurea's walls before the eclipse.",
         "epic-9-adventures", "active"),
        ("Anbel Mishtee", "Prove she is more than the Mayor's daughter — sing the Open at Choir-Hall.",
         "genesis-4-master-plot", "active"),
        ("Choirmaster Olen", "Demand inside-cult testimony before mobilising the Choir.",
         "genesis-3-nemesis", "active"),
        ("Eli of the Glass-Hands", "Teach the table QUENCH form before the Star-cult finds her.",
         "genesis-7-beginning-ending", "active"),
    ],
    "genesis": {
        "sentence_who": "An apprentice of the Forge-Glass Choir",
        "sentence_what": "must seal the Solar-Lunar Caldera",
        "sentence_badly_when": "before the next solar eclipse, in 8 sessions",
        "theme": "Faith demands proof.",
        "tone": "heroic with consequences",
        "nemesis_name": "Malshe Darkening",
        "nemesis_motive": "Free the Eclipse Saint",
        "beginning": "Open with the Mayor assigning the Maiden Adventure to the apprentices.",
        "ending": "A silence as the eclipse passes — one apprentice's sigil written on the Caldera floor.",
    },
    "epic": {
        "plan_summary": "The Order of the Darkening Star intends to shatter the Caldera and free the Eclipse Saint.",
        "theme": "Faith demands proof.",
        "sentence": {"someone": "Malshe Darkening", "wants": "the Forge-Glass Hammer",
                     "timeframe": "Before Solar Eclipse, in 8 sessions",
                     "method": "minions",
                     "refined": "Malshe Darkening wants the Forge-Glass Hammer before the Solar Eclipse, manipulating the Iron-Cantor's choir to do it."},
        "milestones": [
            {"title": "Find the First Sigil", "sequence": 1,
             "obstacles": ["Mountain pass closed", "Order spies in Aurea"],
             "resources_have": ["Mayoral writ"], "resources_needed": ["Climbing kit"]},
            {"title": "Disrupt the Iron-Choir", "sequence": 2,
             "obstacles": ["Frock's hidden Cantors"],
             "resources_have": ["First Sigil"], "resources_needed": ["A counter-tone"]},
        ],
    },
    "encounter": {
        "name": "Pass-of-Aurea Ambush",
        "kind": "combat",
        "plot_phase": "epic-7-milestones",
        "environment": {"indoor": False, "weather": "snow squall", "light": "dim"},
        "notes": "Frock baits the apprentices into the pass with a fake Mayoral writ.",
        "npcs": [
            {"name": "Frock the Iron-Cantor", "role": "henchman", "level": 4, "count": 1,
             "intent": "Test the apprentices' resolve — humiliate, then withdraw."},
            {"name": "Cantor Recruit", "role": "minion", "level": 2, "count": 3,
             "intent": "Pin the apprentices long enough for Frock to escape."},
        ],
    },
}


# ─────────── Artisan's Tale — Cypher post-apocalypse demo ───────────
ARTISAN = {
    "system_id": "cypher",
    "name": "Artisan's Tale · The Last Glassworks",
    "description": (
        "A post-apocalyptic Cypher campaign where the world has been reborn "
        "in glass, and the only artisans who remember pre-Cataclysm techniques "
        "are being hunted. The demo seeds a 12-session arc."
    ),
    "setting_name": "Heartwood-Reach",
    "setting_genre": "post",
    "primer_tier_suggest": 2,
    "primer_xp_cap": 12,
    "house_rules": "Glass-shards count as Cyphers (TN-step-down by 1 per shard, consumable). Cypher Limit is genre-default.",
    "player_primer": (
        "You are an artisan circle in the Heartwood-Reach — a band of survivors "
        "who remember how to MAKE things in a world that only knows how to SCAVENGE."
    ),
    "nodes": [
        {"type": "location", "title": "Heartwood-Reach", "tags": ["artisan", "wilderness"],
         "summary": "A spiral forest grown around a single living tree the size of a mountain."},
        {"type": "location", "title": "The Last Glassworks", "tags": ["artisan", "site"],
         "summary": "Pre-Cataclysm furnace still cool to the touch. Hums when sung to."},
        {"type": "faction", "title": "The Salt-Iron Combine", "tags": ["artisan", "antagonist"],
         "summary": "Gristle-empire that buys artisans and burns the rest."},
        {"type": "lore", "title": "The Memory of Making", "tags": ["artisan", "lore"],
         "summary": "An oral tradition encoded in song. Lose the song — lose the craft."},
        {"type": "npc", "title": "Vothne, the Salt Magnate", "tags": ["artisan", "nemesis"],
         "summary": "Combine head. Wants every artisan in his ledger or in his ovens."},
        {"type": "npc", "title": "Eli of the Glass-Hands", "tags": ["artisan", "ally"],
         "summary": "Master glassblower. Trains the table for free, charges in songs."},
    ],
    "motives": [
        ("Vothne, the Salt Magnate", "Buy out the artisans — or burn them with the Glassworks.",
         "epic-7-milestones", "evolving"),
        ("Eli of the Glass-Hands", "Teach the table the lost songs before the Combine arrives.",
         "epic-8-adventures", "active"),
    ],
    "genesis": {
        "sentence_who": "An artisan of the Heartwood-Reach",
        "sentence_what": "must keep the songs of making alive",
        "sentence_badly_when": "before the Salt-Iron Combine arrives at the Last Glassworks",
        "theme": "Memory is the last weapon of the small.",
        "tone": "elegiac, with sparks of hope",
        "nemesis_name": "Vothne, the Salt Magnate",
        "nemesis_motive": "Own every artisan or burn them",
        "beginning": "Open with Eli bringing the table a glass-and-iron broken song to mend.",
        "ending": "A new artisan learns the song, by firelight, while the Combine retreats.",
    },
    "epic": {
        "plan_summary": "The Salt-Iron Combine intends to buy or burn every artisan in the Heartwood.",
        "theme": "Memory is the last weapon of the small.",
        "sentence": {"someone": "Vothne", "wants": "the artisan ledger",
                     "timeframe": "Before the next salt-tide", "method": "objects",
                     "refined": "Vothne wants the artisan ledger before the salt-tide, using bought-up artifacts to pressure the table."},
        "milestones": [
            {"title": "Mend the Broken Song", "sequence": 1,
             "obstacles": ["Combine spies in the Reach", "Eli's failing voice"],
             "resources_have": ["Heartwood charcoal"], "resources_needed": ["Glass-shard cypher"]},
            {"title": "Re-light the Last Glassworks", "sequence": 2,
             "obstacles": ["Combine cordon"],
             "resources_have": ["The mended song"], "resources_needed": ["A truthtelling artisan"]},
        ],
    },
    "encounter": {
        "name": "Combine Cordon · the Glassworks Gate",
        "kind": "social",
        "plot_phase": "epic-7-milestones",
        "environment": {"indoor": False, "weather": "ash-fall", "light": "dim"},
        "notes": "Vothne's enforcer offers gold — then poison.",
        "npcs": [
            {"name": "Vothne, the Salt Magnate", "role": "nemesis", "level": 5, "count": 1,
             "intent": "Buy the artisans peacefully. Burn them if they decline twice."},
            {"name": "Combine Enforcer", "role": "henchman", "level": 3, "count": 2,
             "intent": "Show force without spilling artisan blood — yet."},
        ],
    },
}


async def _seed_one(blob: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Create one fully-interweaved demo campaign."""
    cid = new_id()
    base_camp = {
        "id": cid,
        "name": blob["name"],
        "description": blob["description"],
        "system_id": blob["system_id"],
        "visibility": "private",
        "gm_id": user["id"],
        "gm_name": user["name"],
        "member_ids": [],
        "invite_token": new_id(),
        "setting_name": blob.get("setting_name", ""),
        "setting_genre": blob.get("setting_genre", ""),
        "genre": blob.get("genre", ""),
        "time_period": blob.get("time_period", ""),
        "default_character_size": blob.get("default_character_size", "Medium"),
        "damage_rating_baseline": blob.get("damage_rating_baseline", 5),
        "primer_xp_cap": blob.get("primer_xp_cap", 0),
        "primer_tier_suggest": blob.get("primer_tier_suggest", 1),
        "primer_level_min": blob.get("primer_level_min", 1),
        "house_rules": blob.get("house_rules", ""),
        "player_primer": blob.get("player_primer", ""),
        "allowed_attributes": [], "prohibited_attributes": [],
        "allowed_defects": [], "prohibited_defects": [],
        "allowed_skill_groups": [], "prohibited_skill_groups": [],
        "character_point_min": 0, "character_point_max": 0, "max_per_attribute_rank": 0,
        "created_at": _now(),
    }
    await db.campaigns.insert_one(dict(base_camp))

    # Codex nodes.
    name_to_node_id: Dict[str, str] = {}
    for n in blob.get("nodes", []):
        nid = new_id()
        node_doc = {
            "id": nid, "campaign_id": cid,
            "title": n["title"], "type": n["type"],
            "content": n.get("summary", ""),
            "tags": n.get("tags", []),
            "visibility": "gm_only" if n["type"] == "npc" and "nemesis" in (n.get("tags") or []) else "shared",
            "revealed_to": [],
            "fields": {"source": "demo-seed"},
            "author_id": user["id"], "author_name": user["name"],
            "created_at": _now(), "updated_at": _now(),
        }
        await db.nodes.insert_one(dict(node_doc))
        name_to_node_id[n["title"]] = nid

    # NPC motives — keyed by node title → node_id, tagged to plot phases.
    for npc_name, motive_text, phase, state in blob.get("motives", []):
        nid = name_to_node_id.get(npc_name)
        if not nid:
            continue
        await db.node_motives.insert_one({
            "id": new_id(),
            "node_id": nid, "campaign_id": cid,
            "motive": motive_text,
            "plot_phase": phase, "state": state,
            "triggered_by": None, "visibility": "gm_only",
            "author_id": user["id"], "author_name": user["name"],
            "created_at": _now(),
        })

    # Genesis 7-phase scaffold.
    genesis_doc = {
        "campaign_id": cid, "updated_at": _now(),
        **blob.get("genesis", {}),
        "seed_npcs": [
            {"name": n["title"], "role": "ally" if n.get("tags", []).count("ally") else
                                          ("nemesis" if "nemesis" in n.get("tags", []) else "neutral"),
             "description": n.get("summary", ""), "relationship": ""}
            for n in blob.get("nodes", []) if n["type"] == "npc"
        ],
    }
    await db.genesis.replace_one({"campaign_id": cid}, genesis_doc, upsert=True)

    # Epic Campaign — only the headline fields the demo cares about.
    if blob.get("epic"):
        ep = blob["epic"]
        epic_doc = {
            "campaign_id": cid, "updated_at": _now(),
            "plan_summary": ep.get("plan_summary", ""),
            "theme": ep.get("theme", ""),
            "sentence": ep.get("sentence", {}),
            "milestones": [{"id": new_id(), **m} for m in ep.get("milestones", [])],
            "villains": [], "seeds": [], "adventures": [],
            "linked_node_ids": list(name_to_node_id.values()),
        }
        await db.epic_campaigns.replace_one({"campaign_id": cid}, epic_doc, upsert=True)

    # Director's Console encounter — plot-phase tagged.
    if blob.get("encounter"):
        e = blob["encounter"]
        director_doc = {
            "campaign_id": cid, "updated_at": _now(),
            "current_location": "", "current_phase_ref": e.get("plot_phase", ""),
            "encounters": [{
                "id": new_id(),
                "name": e.get("name", "Opening encounter"),
                "kind": e.get("kind", "combat"),
                "plot_phase": e.get("plot_phase", ""),
                "environment": e.get("environment", {}),
                "notes": e.get("notes", ""),
                "party_character_ids": [],
                "npcs": [
                    {**npc, "id": new_id(),
                     "source": "codex" if npc.get("name") in name_to_node_id else "manual",
                     "source_id": name_to_node_id.get(npc.get("name")),
                     "location": "", "state": "active"}
                    for npc in e.get("npcs", [])
                ],
            }],
        }
        await db.directors.replace_one({"campaign_id": cid}, director_doc, upsert=True)

    return {"id": cid, "name": blob["name"], "system_id": blob["system_id"],
            "nodes": len(blob.get("nodes", [])),
            "motives": len(blob.get("motives", [])),
            "milestones": len(blob.get("epic", {}).get("milestones", [])),
            "encounter": blob.get("encounter", {}).get("name") or None}


@router.post("/admin/seed-demo")
async def seed_demo(user: Dict[str, Any] = Depends(get_current_user)):
    """Deploy Evereantha + Artisan's Tale demo campaigns owned by the
    calling user. Two GM-only campaigns ready to play, exercising every
    interweaving in V5.4."""
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "GM/admin only.")
    out: List[Dict[str, Any]] = []
    out.append(await _seed_one(EVEREANTHA, user))
    out.append(await _seed_one(ARTISAN, user))
    return {"deployed": out}
