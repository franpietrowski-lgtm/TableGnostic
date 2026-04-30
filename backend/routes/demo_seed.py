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


# ─────────── Evereantha — "The Fracture of the Unmaker" ───────────
# Canonical setting drawn from the Evereantha core reference:
#   • Continenta Aurea / Vitae / Nivalis / Arida / Umbrosa
#   • Order of the Darkening Star + Eclipse Syndicate + Singularity
#   • Azazel/Samael paradox + the Kin (broken nervous system)
#   • Aurae / Mortiscura magic + Butterfly Effect Gauge
EVEREANTHA = {
    "system_id": "besm-4e",
    "name": "Evereantha · The Fracture of the Unmaker",
    "description": (
        "A 52-session arc across Continenta Aurea. The Order of the "
        "Darkening Star believes void energy is the only force that can "
        "stop a coming cosmic extinction. They are right — and they are "
        "wrong. Azazel is not their prophet; he IS the Unmaker. His "
        "splintered counterpart Samael waits in Technopolis Lumina. "
        "Between them: the Kin — fragments of a broken god that hear "
        "each other across timelines. Every relic the players 'secure' "
        "is another organ in the body they're unknowingly assembling."
    ),
    "setting_name": "Evereantha · Continenta Aurea",
    "genre": "dark heroic fantasy with cosmic horror",
    "time_period": "the Age of the Singularity",
    "default_character_size": "Medium",
    "damage_rating_baseline": 5,
    "primer_xp_cap": 0,
    "house_rules": (
        "Crit on natural 6 with the ten-sided check die. Aurae magic "
        "uses Threading; Mortiscura uses Chaining (see Codex). The GM "
        "tracks a Butterfly Effect Gauge per session — past-changing "
        "actions accumulate Time Displacement Factor that warps "
        "future scenes."
    ),
    "player_primer": (
        "You begin in Eagle's Nest, where animals are born with black "
        "glass eyes and children draw the same star in ash. Beneath a "
        "dying tree, a relic sleeps that is not a relic at all. You "
        "do not yet know it, but every cult deacon you fell, every "
        "ritual you break, brings the Unmaker one breath closer to "
        "remembering who he is."
    ),
    "nodes": [
        # ─── Cosmic geography ───
        {"type": "lore", "title": "The Aetheris (Serene Abyss)",
         "tags": ["evereantha", "cosmology", "ocean"],
         "summary": "Vast saltwater expanse cradling the continent of Continenta Aurea. Shimmers blue-green; holds memory in its depths. As the campaign progresses the Aetheris itself begins ERASING history — wars forgotten, borders gone, names falling out of language."},
        {"type": "location", "title": "Continenta Aurea — the Golden Continent",
         "tags": ["evereantha", "continent"],
         "summary": "Primary landmass of the campaign. Divided into four quarters: Septentrionalis (north), Meridionalis (south), Orientalis (east), Occidentalis (west). Most of the campaign happens here; the four other continents (Vitae, Nivalis, Arida, Umbrosa) supply NPCs, allies and threats from beyond."},
        {"type": "location", "title": "Eagle's Nest",
         "tags": ["evereantha", "starting-village"],
         "summary": "Quiet hamlet near the Montes Inexpugnabilis and the western Aetheris. Old artisan bloodlines have faded into superstition. The campaign opens here. Beneath a dying tree's roots, the first of the Kin sleeps."},
        {"type": "location", "title": "Gildenwood",
         "tags": ["evereantha", "wilderness"],
         "summary": "Sprawling forest with gilded foliage; natural bastion encasing parts of Taurid Tor and the road to Eagle's Nest. A vibrant, dangerous labyrinth of beasts and lost shrines."},
        {"type": "location", "title": "Taurid Tor",
         "tags": ["evereantha", "region"],
         "summary": "Southwestern rocky plains scattered with resilient villages, including the new Tech-Forged Hamlets uplifted by Singularity tech. Guardian Outposts watch the passes; Verdant Nexus Farms feed the city beyond."},
        {"type": "location", "title": "Aevum & the Colosseum",
         "tags": ["evereantha", "city"],
         "summary": "Walled city famed for its Colosseum where slaves and herculi fight. Sylas Stonefist runs the resident forge, fitting the gladiators with weapons and armour he reveres as instruments of carnage."},
        {"type": "location", "title": "Technopolis Lumina · Capital of the Singularity",
         "tags": ["evereantha", "city"],
         "summary": "Where magic and machine have become indistinguishable. Districts: Nexus Ward (administrative core, Eclipse Syndicate stronghold, houses Samael's machine), Aether Heights (floating apartments of the wealthy), Mechanist's Enclave (artificers' industrial heart), Shadowthorn Sector (espionage), Circuit Market (trade)."},
        {"type": "location", "title": "The Nexus",
         "tags": ["evereantha", "site"],
         "summary": "Spiraling tower at the heart of Technopolis Lumina. Pulses with the energy that powers the entire Singularity. The artifact Samael was born from sits at its base."},
        {"type": "location", "title": "Quad Quay (the Mine-Labyrinth)",
         "tags": ["evereantha", "underground"],
         "summary": "Underground mine network so vast it is a city in its own right. Center of mining, technological experiment, and industry; honeycombed with tunnels older than the Singularity."},
        {"type": "location", "title": "13th Temple — Temple of the Void",
         "tags": ["evereantha", "site", "endgame"],
         "summary": "A temple located WITHIN the void itself. Holds an artifact capable of manipulating reality. Goal of the Order's deepest rituals; final-act destination."},
        {"type": "location", "title": "Sun and Moon Temple",
         "tags": ["evereantha", "site"],
         "summary": "Twin-shrine where Morrigan Nightshade has been performing the death-art rites. A confrontation site flagged by the hermit's note."},
        {"type": "location", "title": "Montes Inexpugnabilis",
         "tags": ["evereantha", "geography"],
         "summary": "The Impenetrable Mountains, dividing Continenta Aurea and Continenta Vitae. Rumored to hide secret tunnels and sealed-age secrets — including paths the Order has reopened."},

        # ─── Cosmic principals ───
        {"type": "npc", "title": "Azazel — Deacon of the Void / The Unmaker",
         "tags": ["evereantha", "principal", "antagonist"],
         "summary": "The hidden master of the Order of the Darkening Star. Believes void energy is the only force that can halt the coming Unmaker. He is wrong: he IS the Unmaker. He may not yet remember. Appears not as a monster but as someone tired beyond history."},
        {"type": "npc", "title": "Samael — born of Azazel's machine",
         "tags": ["evereantha", "principal", "ambivalent"],
         "summary": "Manifested from a machine artifact in Technopolis Lumina. Claims he is the discarded branch — Azazel's failed escape from the same doom under a different name. Offers the players maps, weapons, partial truths. He does not want Azazel free; he wants to BECOME the final Unmaker himself."},
        {"type": "lore", "title": "The Kin — Azazel's Broken Nervous System",
         "tags": ["evereantha", "cosmology", "principal"],
         "summary": "Fragments of Azazel scattered across history — human-shaped artifacts, relics with faces, statues that dream, weapons that remember being alive, lookalikes wearing different names in different ages. When one awakens, the others hear. When one dies, the others remember. The Kin do not serve the Order — they ARE the Unmaker's broken nervous system."},

        # ─── Factions ───
        {"type": "faction", "title": "Order of the Darkening Star",
         "tags": ["evereantha", "antagonist", "cult"],
         "summary": "Apocalyptic order of priests, deacons, killers, scholars, artisan-lords. Hunts the scattered relics of the Void, convinced void energy is the only force potent enough to confront the Unmaker. They believe atrocity is preparation. Led (in form) by Archdeacons under the hidden hand of Azazel."},
        {"type": "faction", "title": "Eclipse Syndicate",
         "tags": ["evereantha", "antagonist", "syndicate"],
         "summary": "Power bloc inside Technopolis Lumina. Controls the Nexus Ward and Aether Heights. Magic + technocracy fused into a shadow government. Currently sheltering / harnessing Samael."},
        {"type": "faction", "title": "The Singularity",
         "tags": ["evereantha", "neutral", "civilization"],
         "summary": "Transhuman magitech civilization centered on Technopolis Lumina. Five Noble Houses run its internals: House Novar (factories/research), House Lumicore (energy/magic), House Aetherforge (airships), House CyBerrun (cybernetic defense), House Etherion (biotech / harmonized ecosystems)."},
        {"type": "faction", "title": "The Five Noble Houses",
         "tags": ["evereantha", "civilization"],
         "summary": "Novar (Domina) — factories & R&D. Lumicore (Illumina) — energy production / magical research. Aetherforge (Skrelm) — airship yards & aeronautical academies. CyBerrun (Pathsgeon) — tech-defense hub, cybernetic + rune barriers. Etherion (Synthgard) — biotech gardens, synthetic ecosystems."},

        # ─── Deacons (Order's archcraftspeople) ───
        {"type": "npc", "title": "Sylas Stonefist — Archdeacon, master smith",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Resident smith of Aevum's Colosseum. Forges weapons and armour for the gladiators, reveling in the carnage. His devotion to the Order has clouded his morality. When he falls (Act I), the artifact he protects 'stabilizes' — the players believe they have stopped something. They have completed the first lock."},
        {"type": "npc", "title": "Vaelin the Quiet — Deacon of Shadows",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Hides in plain sight as a maid in a noble house. Grief-tattooed shadow-script beneath her skin. Driven by the loss of her lover, she works dark magic to bring him back. Her calligraphy and tattoo work harness shadow itself. Strained — possibly antagonistic — relationship with Morrigan Nightshade."},
        {"type": "npc", "title": "Morrigan Nightshade — Deaconess of the Dead",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Practices death as an art. Binds souls into vessels that whisper prophecies they should not know. Cruel and sadistic, but respected for her mastery of necromancy and the afterlife. Her shadow returns post-mortem as Shadow Morrigan, serving Samael."},
        {"type": "npc", "title": "Lyra Earthheart — Deaconess of the Elements / EarthMancer",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Sculptor-geomancer who bends stone, root, and buried bone into ritual geometry. A love of nature warped into a need for control."},
        {"type": "npc", "title": "Luminar — Deacon of Light / Light Weaver",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Obsessed with light as a tool of manipulation and control. Messianic complex — believes he will bring enlightenment through total mastery. Even radiance can enslave."},
        {"type": "npc", "title": "Rowena Wildwood — High Deaconess / Woodweaver",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Staffmaker, lumberjack, self-styled protector of ancient groves. Believes preserving the cult's knowledge restores 'balance' against forces of good."},
        {"type": "npc", "title": "Augustus Blackpaw — Deacon of the Hunt / Bait Master",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Hunter-fisherman who supplies the Order's larder. Believes provisioning sustains the apocalypse-prep."},
        {"type": "npc", "title": "Marcus Aurelius — Deacon of Alchemy / Matter Tinkerer",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Transmutation obsessive — willing to sacrifice others to chase the universe's mechanical secrets."},
        {"type": "npc", "title": "Zephyr Windrider — Deacon of the Wilds / Apocophea",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Eco-fanatic who would destroy civilization to 'protect' the wilds. Extreme, unethical means."},
        {"type": "npc", "title": "Ignatius the Inferno — Deacon of Flames / Ore Talker-Smith",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Charismatic, impulsive. Uses fire to intimidate and rule. Believes the Order alone can wield true flame."},
        {"type": "npc", "title": "Azura Starlight — Deaconess of the Oceans / Bait Master",
         "tags": ["evereantha", "deacon", "antagonist"],
         "summary": "Spiritual oceanic devotee. 'Protects' marine life through ruthless cult enforcement."},

        # ─── Eclipse Syndicate operatives ───
        {"type": "npc", "title": "Shadow Morrigan",
         "tags": ["evereantha", "syndicate", "antagonist"],
         "summary": "Reformed from the lingering miasma of the original Morrigan; now Samael's enforcer. Necromantic, shadow-creature creation, death-energy manipulation."},
        {"type": "npc", "title": "Zephyr (Vitae Origin)",
         "tags": ["evereantha", "syndicate"],
         "summary": "Former gladiator from Continenta Vitae. Combines Mortiscura magic with Vitae gladiatorial techniques."},
        {"type": "npc", "title": "Shade Nix (Umbrosa)",
         "tags": ["evereantha", "syndicate"],
         "summary": "From the shadow continent. Stealth and assassination specialist; the syndicate's scout."},
        {"type": "npc", "title": "ArVex (Aurea)",
         "tags": ["evereantha", "syndicate"],
         "summary": "Master of Aurea's Faces; ruthless strategic adviser inside the syndicate."},
        {"type": "npc", "title": "Malak (Singularity)",
         "tags": ["evereantha", "syndicate"],
         "summary": "Magic-tech integration prodigy. Builds the syndicate's advanced weapons and machinery."},
        {"type": "npc", "title": "Strategist Kael (Singularity, rogue)",
         "tags": ["evereantha", "syndicate"],
         "summary": "Former Singularity general turned. Plans the syndicate's military operations."},

        # ─── Singularity technocrats ───
        {"type": "npc", "title": "Dr. Caelum Innovus — Science Technocrat",
         "tags": ["evereantha", "singularity", "neutral"],
         "summary": "Bioengineering and mechanotechnology lead pushing Singularity's scientific frontier."},
        {"type": "npc", "title": "Magus Noctis Aeterna — Magic Technocrat",
         "tags": ["evereantha", "singularity", "ambivalent"],
         "summary": "Master of Mortiscura magic. Aims to integrate dark magical forces with Singularity's tech."},
        {"type": "npc", "title": "Senator Vox Populi — People's Technocrat",
         "tags": ["evereantha", "singularity", "ally"],
         "summary": "Elected mediator between technocrat and military sectors. Voice of public interest."},
        {"type": "npc", "title": "General 'Jea' Stratos — Air Force",
         "tags": ["evereantha", "singularity"],
         "summary": "Aerial warfare strategist commanding Singularity airships."},
        {"type": "npc", "title": "General 'Kun' Firma — Ground Forces",
         "tags": ["evereantha", "singularity"],
         "summary": "Mechanized & magic-enhanced ground commander."},

        # ─── Magic system ───
        {"type": "lore", "title": "Aurae Magic — the Two Faces",
         "tags": ["evereantha", "magic"],
         "summary": "Evereantha's magic is split into two Faces: Face of Aurae (creation, nurturing, expansion) and Face of Mortiscura (hiding, deception, halting). Aurae mastery progresses Single Face → Threading → Multi-Face Threading → Tri-Threading. Mortiscura: Single Face → Chaining → Multi-Face Chaining → Chain Binding → Recursive Chaining."},
        {"type": "lore", "title": "Butterfly Effect Gauge (BEG)",
         "tags": ["evereantha", "magic", "mechanic"],
         "summary": "Custom mechanic: tracks how player decisions in past timelines warp the present. Combines Time Displacement Factor (TDF — how far back the act reaches) and Decision Impact Factor (DIF — magnitude of the change). The GM uses BEG to introduce timeline ripples in Acts III-V."},
    ],
    "motives": [
        ("Azazel — Deacon of the Void / The Unmaker",
         "Remember that he already IS the Unmaker. Each broken seal returns a sliver of memory.",
         "epic-7-milestones", "evolving"),
        ("Samael — born of Azazel's machine",
         "Become the final Unmaker. Use the players to weaken Azazel without freeing him.",
         "genesis-3-nemesis", "evolving"),
        ("The Kin — Azazel's Broken Nervous System",
         "Become whole again. Independently jealous, afraid, ambitious — but the instinct binds them all.",
         "epic-9-adventures", "evolving"),
        ("Sylas Stonefist — Archdeacon, master smith",
         "Forge weapons fit for the apocalypse-prep — and bait the players into the first 'wrong victory'.",
         "epic-8-adventures", "active"),
        ("Vaelin the Quiet — Deacon of Shadows",
         "Bring her dead lover back through Mortiscura — even if it requires a player as the soul-vessel.",
         "epic-9-adventures", "active"),
        ("Morrigan Nightshade — Deaconess of the Dead",
         "Bind a player's soul to a vessel before they realise what the 'rescue' actually was.",
         "epic-9-adventures", "active"),
        ("Lyra Earthheart — EarthMancer",
         "Inscribe the third stone-circle of the Order's geometry before the spring melt.",
         "epic-9-adventures", "active"),
        ("Luminar — Deacon of Light",
         "Capture a Kin alive and 'enlighten' it into obedience.",
         "epic-9-adventures", "active"),
        ("Senator Vox Populi",
         "Identify which Singularity technocrat is feeding the Eclipse Syndicate.",
         "genesis-3-nemesis", "active"),
    ],
    "genesis": {
        "sentence_who": "A circle of ordinary people from Eagle's Nest",
        "sentence_what": "must oppose the Order of the Darkening Star",
        "sentence_badly_when": "before realising every victory is another organ in the Unmaker's body",
        "theme": "The terror of being useful to the thing you oppose.",
        "tone": "dark heroic with creeping cosmic horror",
        "nemesis_name": "Azazel — Deacon of the Void / The Unmaker",
        "nemesis_motive": "Remember that he already IS the Unmaker.",
        "beginning": (
            "Open in Eagle's Nest with the small wrongnesses — black-glass-eyed "
            "lambs, humming tools, ash-stars in children's drawings. A relic "
            "is found beneath the dying tree's roots. It appears to be an "
            "artifact. It is not. It is one of the Kin, sleeping."
        ),
        "ending": (
            "All timelines overlap; the players face Azazel, Samael, and "
            "alternate versions of themselves at once, deciding which truth "
            "the world is bound to."
        ),
    },
    "epic": {
        "plan_summary": (
            "Six-act / 52-session arc — The Fracture of the Unmaker. Act I: "
            "First Wrong Victory (Sylas falls). Act II: Deacons open the "
            "world. Act III: Samael Branch — alternating timelines begin. "
            "Act IV: Kin awaken — hive-mind fragments hunt the players. "
            "Act V: Unmaker remembers — Azazel as the inevitable conclusion. "
            "Act VI: Final shape of reality — Unmaking / Ascension / Binding "
            "/ Samael Crown / Kin Rebellion endings."
        ),
        "theme": "The terror of being useful to the thing you oppose.",
        "sentence": {
            "someone": "Azazel & Samael (both)",
            "wants": "to become the final Unmaker",
            "timeframe": "across 52 sessions of overlapping timelines",
            "method": "the Order builds the structure; the Kin are the body; the players unknowingly assemble both",
            "refined": "Azazel wants to remember he is the Unmaker; Samael wants to take that role; the players must decide what kind of monster gets to hold reality together.",
        },
        "milestones": [
            {"title": "Act I — The First Wrong Victory", "sequence": 1,
             "obstacles": ["Black-glass omens in Eagle's Nest", "Sylas Stonefist of Aevum"],
             "resources_have": ["Trust between the apprentices"],
             "resources_needed": ["A relic that is secretly Kin"]},
            {"title": "Act II — Deacons Open the World", "sequence": 2,
             "obstacles": ["Vaelin's grief", "Morrigan's death-art", "Lyra's geometry", "Luminar's obedience-light"],
             "resources_have": ["The locked artifact"],
             "resources_needed": ["Inside-cult testimony"]},
            {"title": "Act III — The Samael Branch", "sequence": 3,
             "obstacles": ["Time stutters", "Alternate timelines diverge", "Eclipse Syndicate"],
             "resources_have": ["A working enemy network"],
             "resources_needed": ["Forbidden calculations from Samael"]},
            {"title": "Act IV — The Kin Awaken", "sequence": 4,
             "obstacles": ["The Kin develop preferences", "Aetheris erases history"],
             "resources_have": ["Most of the Order broken"],
             "resources_needed": ["A reason for the Kin to choose the players"]},
            {"title": "Act V — The Unmaker Remembers", "sequence": 5,
             "obstacles": ["Samael's betrayal", "Kin factional war"],
             "resources_have": ["Sympathetic Kin"],
             "resources_needed": ["A truth Azazel does not yet hold"]},
            {"title": "Act VI — The Final Shape of Reality", "sequence": 6,
             "obstacles": ["All timelines overlap", "Alternate selves arrive"],
             "resources_have": ["The accumulated cost of every choice"],
             "resources_needed": ["A decision the table can live with"]},
        ],
    },
    "encounter": {
        "name": "Eagle's Nest · The Sleeping Kin",
        "kind": "social-then-combat",
        "plot_phase": "epic-7-milestones",
        "environment": {"indoor": False, "weather": "still", "light": "dawn"},
        "notes": (
            "The dying tree's roots peel back to reveal what looks like a "
            "porcelain woman. She is breathing — barely. The first cult "
            "scout watches from the treeline. The party's first decision "
            "cascades into Sylas Stonefist's storyline."
        ),
        "npcs": [
            {"name": "Sleeping Kin (lookalike)", "role": "ambivalent", "level": 5, "count": 1,
             "intent": "Wake. Listen for the others. Decide whether the players are kin or kindling."},
            {"name": "Cult Scout", "role": "henchman", "level": 2, "count": 1,
             "intent": "Witness, then run for Sylas."},
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
    """Create one fully-interweaved demo campaign — IDEMPOTENT.

    If this user already owns a campaign with the same name AND
    system_id, return the existing one instead of duplicating. Avoids
    the 'click Deploy demo five times → 5 copies in your account'
    failure mode the user previously hit.
    """
    existing = await db.campaigns.find_one(
        {"gm_id": user["id"],
         "name": blob["name"],
         "system_id": blob["system_id"]},
        {"_id": 0},
    )
    if existing:
        node_count = await db.nodes.count_documents({"campaign_id": existing["id"]})
        motive_count = await db.node_motives.count_documents({"campaign_id": existing["id"]})
        return {
            "id": existing["id"],
            "name": existing["name"],
            "system_id": existing["system_id"],
            "nodes": node_count,
            "motives": motive_count,
            "milestones": len(blob.get("genesis", {}).get("milestones") or []),
            "skipped_existing": True,
        }
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


def _evereantha_adapted(system_id: str) -> Dict[str, Any]:
    """Port the Evereantha setting onto a non-BESM system.

    The Codex nodes (locations, factions, NPCs, lore) are shared across
    systems — they're narrative, not mechanical. We DO reshape:
      - campaign name  ← system-flavoured subtitle
      - encounter NPCs ← system-specific stat_hint (cr / level / pool)
      - player_primer  ← nod to the local magic system analogue
    so each adaptation reads like a real conversion rather than a copy.
    """
    base = dict(EVEREANTHA)
    # Shared Codex nodes — same world, different math.
    base["nodes"] = list(EVEREANTHA["nodes"])
    base["motives"] = list(EVEREANTHA["motives"])
    base["genesis"] = dict(EVEREANTHA.get("genesis", {}))
    base["epic"] = dict(EVEREANTHA.get("epic", {}))
    base["system_id"] = system_id

    if system_id == "dnd-5e":
        base["name"] = "Evereantha · The Fracture of the Unmaker (D&D 5E adaptation)"
        base["genre"] = "dark heroic fantasy with cosmic horror"
        base["player_primer"] = (
            "You are villagers of Eagle's Nest at the threshold of a "
            "52-session arc. The Order of the Darkening Star believes "
            "the void can stop the Unmaker. They are wrong. Expect "
            "Bardic warnings, Cleric-domain crises, Wizard-tier "
            "calculations of which timeline is real."
        )
        base["damage_rating_baseline"] = 8
        # D&D-flavoured encounter: CR-scale NPCs matching the demo's tier.
        base["encounter"] = {
            "name": "Eagle's Nest · The Sleeping Kin (SRD CR)",
            "kind": "social-then-combat",
            "plot_phase": "epic-7-milestones",
            "environment": {"indoor": False, "weather": "still", "light": "dawn"},
            "notes": "The dying tree's roots peel back to reveal a porcelain woman, breathing barely. A cult scout watches from the treeline. Party is level 3.",
            "npcs": [
                {"name": "Sleeping Kin (lookalike)", "role": "ambivalent", "cr": "5", "count": 1,
                 "intent": "Wake. Decide if the players are kin or kindling."},
                {"name": "Cult Scout (Order of the Darkening Star)", "role": "henchman", "cr": "1/2", "count": 1,
                 "intent": "Witness, then run for Sylas Stonefist."},
            ],
        }
    elif system_id == "cypher":
        base["name"] = "Evereantha · The Fracture of the Unmaker (Cypher adaptation)"
        base["setting_genre"] = "fantasy"
        base["genre"] = "dark fantasy with cosmic horror"
        base["player_primer"] = (
            "You are villagers of Eagle's Nest. Aurae magic is "
            "Threading; Mortiscura is Chaining. The Butterfly Effect "
            "Gauge governs how your past-changing acts ripple into the "
            "present. Cypher level 5 = base difficulty for cosmic-horror "
            "saves."
        )
        base["encounter"] = {
            "name": "Eagle's Nest · The Sleeping Kin (Cypher levels)",
            "kind": "social-then-combat",
            "plot_phase": "epic-7-milestones",
            "environment": {"indoor": False, "weather": "still", "light": "dawn"},
            "notes": "Cypher difficulty 5 for the perception roll; the Sleeping Kin is level 5.",
            "npcs": [
                {"name": "Sleeping Kin (lookalike)", "role": "ambivalent", "level": 5, "count": 1,
                 "intent": "Wake. Listen for the others. Decide whether the players are kin."},
                {"name": "Cult Scout (Order of the Darkening Star)", "role": "henchman", "level": 2, "count": 1,
                 "intent": "Witness without engaging. Run for Sylas at the first sign of force."},
            ],
        }
    elif system_id == "anime-5e":
        base["name"] = "Evereantha · The Fracture of the Unmaker (Anime 5E hybrid)"
        base["genre"] = "shōnen-tinged dark fantasy with cosmic horror"
        # Anime 5E is D&D 5E + BESM-style point-buy LAYER for genre
        # powers — NOT Tri-Stat ability scores. Flavour the primer
        # accordingly so the player picks the right mental model.
        base["player_primer"] = (
            "You are villagers of Eagle's Nest. The d20 chassis runs "
            "your class, level, hit dice, AC, and saves exactly as in "
            "5E. The BESM-style point-buy layer sits on TOP of the "
            "sheet — you can spend a point budget on signature genre "
            "powers (e.g. Combat Mastery, Heightened Senses, Personal "
            "Gear, Custom Technique) for shōnen flavour. Anime 5E does "
            "NOT use Tri-Stat ability scores — Body / Mind / Soul are "
            "absent here. The D&D SRD races, classes, feats and "
            "backgrounds port directly into Anime 5E (one-way port — "
            "Anime 5E content does NOT port back to a strict-5E table)."
        )
        base["primer_tier_suggest"] = 1
        base["encounter"] = {
            "name": "Eagle's Nest · The Sleeping Kin (Anime 5E hybrid)",
            "kind": "social-then-combat",
            "plot_phase": "epic-7-milestones",
            "environment": {"indoor": False, "weather": "still", "light": "dawn"},
            "notes": "d20 SRD CR + a small BESM point-buy budget for the Kin's signature techniques.",
            "npcs": [
                {"name": "Sleeping Kin (lookalike)", "role": "ambivalent", "cr": "5", "count": 1,
                 "intent": "Wake. Decide whether the players are kin or kindling."},
                {"name": "Cult Scout (Order of the Darkening Star)", "role": "henchman", "cr": "1/2", "count": 1,
                 "intent": "Witness, then run for Sylas."},
            ],
        }
    return base


@router.post("/admin/seed-evereantha-suite")
async def seed_evereantha_suite(user: Dict[str, Any] = Depends(get_current_user)):
    """Deploy the FULL Evereantha suite — one campaign per supported
    system (besm-4e, dnd-5e, cypher, anime-5e). Gives the GM/admin a
    parallel-world testbed for cross-system compatibility + adaptation
    review. Four GM-only campaigns in one call.
    """
    if user.get("role") not in ("gm", "admin"):
        raise HTTPException(403, "GM/admin only.")
    out: List[Dict[str, Any]] = []
    out.append(await _seed_one(EVEREANTHA, user))  # besm-4e canonical
    for sid in ("dnd-5e", "cypher", "anime-5e"):
        out.append(await _seed_one(_evereantha_adapted(sid), user))
    return {"deployed": out, "suite": "evereantha-cross-system"}
