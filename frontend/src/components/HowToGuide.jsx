import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen, Compass, ChevronRight, Wand2, Layers, Sparkles,
  ScrollText, Users, Network, Skull, Calendar, FileDown, Check, Play,
  Boxes, Coins, Map, X, Image as ImageIcon, Sword,
} from "lucide-react";
import { api } from "../lib/api";
import { useTour } from "./TourProvider";
import { TOURS } from "./tours";

/**
 * HowToGuide — V6.15 interactive walkthrough.
 *
 * 8 recipe cards + a "Launch guided tour" button on each one that
 * spotlights real DOM elements and narrates the workflow with a
 * moving tooltip. Recipes that need a campaign context prompt the
 * user to pick one from their library before the tour begins.
 *
 * Lives under /app/help so the authenticated shell wraps it.
 */
const RECIPES = [
  {
    id: "campaign-from-scratch",
    tourId: "campaign-from-scratch",
    icon: Wand2,
    title: "Author a campaign from scratch",
    blurb: "From empty page to your first session — Genesis flow + Atelier toolkit.",
    steps: [
      ["Pick a system", "Open /app/campaigns/new and choose BESM 4E, Anime 5E, D&D 5E, or Cypher. Each one branches the rest of the flow."],
      ["Run the 7-Phase Genesis", "Click Genesis on the campaign page → walk through Sentence · Theme · Nemesis · Master Plot · Adventure Outlines · Supporting Cast · Beginning & Ending."],
      ["Seed the Knowledge Web", "On Phase 6 (Supporting Cast) click 'Seed Knowledge Web' to materialise NPCs, locations, factions as Codex nodes."],
      ["Tighten the spine in Atelier", "Open Atelier → Workshop. Drop Session 0 contract, draft Arcs in 3-session sweeps."],
      ["Schedule Session 1", "Sessions tab → New Session. Pin a plot phase tag — feeds the Director's Console pulse."],
    ],
  },
  {
    id: "build-character",
    tourId: "build-character",
    icon: Users,
    title: "Build a player character",
    blurb: "System-aware Character Forge for all 4 supported rulebooks.",
    steps: [
      ["Open the Forge", "Campaign → Characters tab → New Character. The form auto-shapes to the campaign's system."],
      ["Set Identity", "Name, concept, optional portrait. Portrait uploads stick to the character across sessions and PDFs."],
      ["Buy mechanics", "BESM/Anime5e: spend CP on Stats, Attributes, Skills. D&D 5E: Class · Level · Race · Background · Spell slots auto-populate. Cypher: Sentence (Descriptor + Type + Focus)."],
      ["Sheet-side tweaks", "Open the sheet — hover any attribute, skill, or defect Level value to edit it inline. Cost recomputes on save."],
      ["Submit for GM approval", "BESM rules-compliance validator runs automatically; the GM signs off via the Approval Panel."],
    ],
  },
  {
    id: "run-encounter",
    tourId: "director-console",
    icon: Skull,
    title: "Run an encounter with the Director's Console",
    blurb: "Pick a session, build encounters from your codex, watch the CR engine balance them live.",
    steps: [
      ["Open the Director", "Campaign → Director button. Aggregates Genesis NPCs, Epic villains, and Codex creatures."],
      ["Pick the active session", "Top-right 'Active session' selector. Sessions appear in their GM-defined timeline order — supports prologues + backstory."],
      ["Drag NPCs / Creatures into the encounter", "Left rail shows Codex People + Codex Creatures + Genesis seeds + Epic villains. Click to add."],
      ["Watch the CR Panel", "Right rail evaluates difficulty against the seated party live. Suggestions adjust environment, count, and tactics — never just the numbers."],
      ["Save + push to a session", "Save the encounter draft. Open a Live Session, drop the same NPCs onto the battlemap, and start the round timer."],
    ],
  },
  {
    id: "knowledge-web",
    tourId: "knowledge-web",
    icon: Network,
    title: "Map your world with the Knowledge Web",
    blurb: "Codex nodes, the org-tree, and the Biome Pyramid.",
    steps: [
      ["Add codex nodes", "Knowledge Web tab → New Node. Pick a type: NPC, Location, Faction, Creature, Lore, Spell, etc. Tag pillar (Population/Geography/History)."],
      ["Detail location climate", "On Location nodes set fields.temperature (hot/warm/cool/cold) and fields.humidity (wet/balanced/dry). The Biome Pyramid auto-positions them."],
      ["See it as a chart", "Knowledge Web → Chart view. World Creation Tree fans out from Creation root. Biome Pyramid maps locations by climate."],
      ["Pin to Timeline", "While viewing the Chart, click any node — it drops a marker on the Timeline at the active session. Useful for tracking when a place / NPC entered the story."],
    ],
  },
  {
    id: "live-session",
    tourId: "live-session",
    icon: Sparkles,
    title: "Run a live session",
    blurb: "Battlemap · WebRTC video · live dice altar · auto-status rings.",
    steps: [
      ["Click Start session", "From the campaign header. Players join via the invite link or by sitting in their character seat."],
      ["Open the battlemap", "Left side panel. GMs paint fog, walls, ruler. Players drag their own tokens. Shift+right-click on a token cycles its grid size (1×1 → 4×4)."],
      ["Apply effects", "Right-click a token → Apply effect. Status rings broadcast to every viewer including the absent character sheet (auto-mirror)."],
      ["Roll & recap", "Roll dice via the altar; finalise the session to auto-generate a Loremaster recap (Claude-powered) that pins as the next session's opener."],
    ],
  },
  {
    id: "timeline",
    tourId: null,
    icon: Calendar,
    title: "Build the campaign Timeline",
    blurb: "GM-defined narrative spine, supporting prologues + backstory + time-shenanigans.",
    steps: [
      ["Open the Timeline", "Atelier tab → Timeline."],
      ["Reorder sessions", "Sessions appear in their GM-defined position (sequence_index). Use the reorder API or session edit UI to drop prologue / flashback sessions wherever they belong on the spine — independent of play date."],
      ["Decorate with markers", "Open Codex Chart → click any node to pin it on the Timeline at the active session. Markers appear below the spine, colour-coded by node."],
      ["Export as chronicle", "Atelier → Export PDF. Timeline appendix joins character journals + chat transcripts in the bundle."],
    ],
  },
  {
    id: "delta-drop",
    tourId: null,
    icon: Layers,
    title: "Sync changes via Delta Drop",
    blurb: "When you've cloned a campaign, push or pull author edits without losing in-progress play.",
    steps: [
      ["Make changes upstream", "GM of the source campaign edits Genesis, House Rules, Codex, or Reference Library."],
      ["Open the Delta Drop tab", "On the cloned campaign. See exactly which fields differ — additions, removals, value changes."],
      ["Approve selectively", "Tick the changes you want to merge. GM-only — the player roster + character data are never touched."],
    ],
  },
  {
    id: "export-pdf",
    tourId: null,
    icon: FileDown,
    title: "Export a chronicle PDF",
    blurb: "DriveThruRPG-ready, system-branded, with character sheets + journals + chat transcripts + timeline.",
    steps: [
      ["Open Atelier → Export PDF", "Choose Campaign (branded) or Narrative (pure prose) mode."],
      ["Set your byline", "Save your name once; every export uses it on the cover + page footer."],
      ["Download", "Bundle includes: cover · table of contents · per-session narrative · character appendix (sheets + folio.journal entries) · Custom Reference appendix · Timeline pin appendix · Chat transcript appendix · legal footer."],
    ],
  },
  // ──────────────────────────────────────────────────────────────
  // V6.25.30 — workflow recipes the user explicitly requested.
  // System-aware where applicable; cross-system by topic everywhere
  // else. Every recipe references the seeded MVP fixture data
  // (Maiden Voyage / Eli / Lyra / Vex) so screenshots are reproducible.
  // ──────────────────────────────────────────────────────────────
  {
    id: "build-character-by-system",
    tourId: null,
    icon: Users,
    title: "Build a character — system by system",
    blurb: "Each rulebook gets a different forge. Pick the system, follow the recipe.",
    bySystem: true,
    systems: {
      "besm-4e": [
        ["Open the Forge", "Campaigns → Maiden Voyage → Characters → New Character. Form auto-shapes to BESM 4E."],
        ["Set total points", "Pick Power Level (Plucky / Heroic / Mighty …) — auto-suggests a CP cap. Editing an existing char no longer overwrites your saved cap (V6.25.27)."],
        ["Spend on Stats / Attributes / Skills", "Body, Mind, Soul cost 1 CP per level. Attributes are catalogued in the Reference panel — click a row to attach. Item / Weapon / Companion containers apply the p.135 half-cost (ceil)."],
        ["Pick Defects to refund CP", "Defects feed back into the bank with floor-0 stacking. Stacks visible in Rules Audit."],
        ["Submit + GM approves", "Once approved, the XP ledger feeds Total: Total = primer + xp_total. CP Bank widget mirrors the Rules Audit on every refresh."],
      ],
      "anime-5e": [
        ["Open the Forge", "Campaigns → … → New Character (Anime 5E system)."],
        ["Pick Tier + Race + Class", "Tier scales DP. Anime 5E full-cost weapon multipliers are enforced in budget-breakdown."],
        ["Buy Abilities, point-buy Stats", "Ability score cost + race cost + point_buy_total drives total_spent."],
        ["Watch the budget audit", "/anime5e/budget-breakdown — lists canonical_raw_dp, total_spent, suspicious_budget, level. Drift surfaces in the CP Bank as a 'drift' chip."],
        ["GM reviews + approves", "Same approval semantics as BESM."],
      ],
      "cypher": [
        ["Write the Sentence", "Descriptor + Type + Focus = your character. Open Vex Ashenhart on the Maiden Cypher campaign for a worked example (Strong Glaive who Wields Power with Precision)."],
        ["Set Tier, Pools, Edge", "folio.cypher_state.pools.{might/speed/intellect} = {max, current, edge}. Pool rings on the sheet read both nested + flat shapes (V6.25.29)."],
        ["List Abilities + Cyphers carried", "Cyphers Carried card shows N / MAX. Pick a Cypher Limit on character creation; over-cap triggers wide-eyed instability."],
        ["XP economy panel", "Cypher XP ledger handles GM intrusion refusals + peer transfers. Spend 4 XP for a Tier advance, etc."],
      ],
      "dnd-5e": [
        ["Pick Class, Race, Background", "Open Lyra Stormblade on the D&D campaign for a worked Half-Elf Paladin lv 3."],
        ["Roll abilities", "Sheet shows STR/DEX/CON/INT/WIS/CHA + auto-modifier."],
        ["Add subclass + features at level milestones", "CLASS_FEATURES + SUBCLASSES on the Reference page list every milestone for all 12 classes."],
        ["Spell slots — RAW or override", "RAW slot table fills automatically; folio.dnd_state.spell_slots overrides win when present (V6.25.29)."],
        ["Equip armor + weapons", "weapon_equipped / armor_equipped strings drive the AC / attack panel; magic_items array surfaces on Inventory tab."],
      ],
    },
  },
  {
    id: "codex-development",
    tourId: "knowledge-web",
    icon: BookOpen,
    title: "Codex development — web your world",
    blurb: "Genesis seeds → Codex nodes → Knowledge Web chart → Timeline pins.",
    steps: [
      ["Run the 7-Phase Genesis", "Phase 6 'Seed Knowledge Web' materialises NPCs, Factions, Locations, and Lore from the Master Plot you set up. They land as Codex nodes."],
      ["Add manual nodes", "Knowledge Web → New Node. Pick node_kind (npc / location / faction / lore / spell / etc.), set fields.temperature + fields.humidity for Locations to auto-position on the Biome Pyramid."],
      ["Link nodes via the chart", "Knowledge Web → Chart view. Click a node, draw an edge to another. Edges store relationship_kind so the graph stays meaningful."],
      ["Pin to Timeline", "While viewing the Chart, click any node — it pins on the Timeline at the active session. Tracks WHEN a thing entered the story."],
      ["Vigilize on death", "When a GM marks an encounter Complete and ticks an NPC casualty, the codex node receives fields.deceased + a death_log entry (V6.25.29)."],
    ],
  },
  {
    id: "reference-and-houserules",
    tourId: null,
    icon: ScrollText,
    title: "Reference table entries & house rules",
    blurb: "Per-campaign Reference Editor. Author Attributes, Defects, Power Packs/Bundles, Subclasses, Magic Items …",
    steps: [
      ["Open Reference Editor", "Director's Console → Reference Editor (Atelier tab)."],
      ["Pick the kind", "BESM 4E gets attribute / defect / enhancement / limiter / power_pack / power_bundle / weapon / armor / item / companion. D&D 5E adds subclass / magic_item / monster / language / tool (V6.25.28). Cypher gets type / focus / descriptor / artifact."],
      ["Author with the right shape", "Each kind has its own Pydantic schema on the backend — name, summary, page reference, plus kind-specific fields (cost_per_level for attributes, prereq for feats, rarity + attune for magic_items …)."],
      ["Enable on character sheet", "Character builder pulls custom rows from /reference/library. Players can attach them to their sheet just like canonical entries."],
      ["Mark as house-rule", "Tag the row 'house-rule' to surface it in the dashboard Reference page under a separate band so players know it diverges from RAW."],
    ],
  },
  {
    id: "adventures-bbeg-genesis",
    tourId: "campaign-from-scratch",
    icon: Skull,
    title: "Adventures, master plot, BBEG / OGAS",
    blurb: "Genesis the world, then Atelier-shape the spine, then drop the BBEG with Azazel-style stats.",
    steps: [
      ["Genesis the campaign", "Phases 1-7 walk Sentence → Theme → Nemesis → Master Plot → Adventure Outlines → Supporting Cast → Beginning & Ending. The Nemesis answer feeds the BBEG dossier."],
      ["Author the BBEG codex node", "Codex → New NPC. Drop the rich fields: subtitle, quote, resources[POWER/NETWORKS/KNOWLEDGE/TOOLS], weakness {description, why, player_can}, cost {body, consequences}, who_knows[]."],
      ["The PDF exporter renders Azazel-style", "V6.25.30 — any entity codex node with structured fields prints as a sectioned dossier (centred title, hero panel + Resources panel, Weakness band, Cost band, Who-Else-Knows footer). See Maiden Voyage's seeded Azazel for a worked example."],
      ["Link to Adventure Outlines", "Atelier Workshop → Arcs. Drop the BBEG into the right Arc; the spine pulses turn red as the BBEG approaches reveal."],
      ["OGAS — One Goal, Always Suffering", "Use fields.cost.consequences to enumerate the permanent campaign-defining sacrifices reaching the BBEG demands."],
    ],
  },
  {
    id: "encounter-loop",
    tourId: null,
    icon: Sword,
    title: "Encounter design + run loop",
    blurb: "Bestiary → Encounters Library → Run → Resolve. NPCs vigilize; monster kills tally per character.",
    steps: [
      ["Open Encounters Library", "Director's Console → Encounters tab. GMs bulk-author here, players never see the library."],
      ["Drop foes from the bestiary", "Editor → Bestiary picker. Pulls system-specific monsters (D&D 5E's 62 SRD monsters, Cypher's bestiary, etc.). Click to attach + adjust count."],
      ["CR / DP balance", "Right rail evaluates difficulty against the current party live (V4.1 BESM CR engine; SRD CR for D&D)."],
      ["Mark Run", "Status flips to running. Run can happen in-session (linked) or out-of-band (Director Console)."],
      ["Resolve & propagate", "Click Complete → modal shows: notes, NPC casualty checkboxes (death reason + witnesses + killing-blow character), per-monster kill counts. Submit → codex vigilizes deceased NPCs, kill_logs aggregate per character (V6.25.29)."],
      ["See the leaderboard", "GET /api/campaigns/{cid}/kill-tally exposes grand_total + by_monster + by_character. Future news / mer-der-hoh-bohs feed will read this."],
    ],
  },
  {
    id: "inventory-workflow",
    tourId: null,
    icon: Boxes,
    title: "Inventory — equip, attune, ready, charge",
    blurb: "Tabbed sections, 6 equipment slots, attunement list, readied items with charges.",
    steps: [
      ["Open the Inventory tab", "On any sheet (BESM / Anime / Cypher / D&D), click the Inventory sub-tab."],
      ["Browse by category", "Tabs: All · Weapons · Shields · Armor · Items · Readied · Materials · Mundane · Magic · Accessory."],
      ["Auto-derived rows", "BESM Item / Weapon / Shield / Armor / Healing / Wealth attributes auto-render as inventory rows. Power Packs and Power Bundles do too."],
      ["Equip → Attune → Ready", "Per-row toggles. Equipping fills L-Hand / R-Hand / Head / Torso / Legs / Feet slots. Two-handed weapons claim both hands. Attuned-but-slotless items (e.g. Eli's Apothecary Bandolier) ride alongside. Readied (potions, scrolls) get a charges counter ±."],
      ["Equipped strip on Mechanics tab", "Mirror of the equip slots so players can see what's in each hand at a glance during combat."],
    ],
  },
  {
    id: "xp-cp-operations",
    tourId: null,
    icon: Coins,
    title: "XP / CP / DP — bank, spend, advance",
    blurb: "How the ledger feeds the bank on each system.",
    steps: [
      ["CP Bank lives in the builder edit window", "V6.25.27 — moved out of the read-only sheet so it stops competing with the Rules Audit."],
      ["Pre-approval Total = primer", "Whatever the player primer set as total_points stays the cap until the GM approves the sheet."],
      ["Post-approval Total = primer + xp_total", "Once GM approves, the XP ledger feeds the Total. Players submit XP spends via the AdvancementWizard."],
      ["Cypher XP economy", "Cypher uses GM intrusion / refusal mechanics. CypherXPPanel tracks ledger, refusals, peer transfers. 4 XP buys a Tier advance."],
      ["Anime 5E DP", "Same shape as BESM CP, but DP = 80 + (level − 1) per RAW. Drift between stored budget and RAW formula raises a warning chip."],
    ],
  },
  {
    id: "exporter-tour",
    tourId: null,
    icon: FileDown,
    title: "Exporter — chronicle PDF + Azazel codex PDF",
    blurb: "Two PDFs, two purposes. Chronicle = full session bundle. Codex = printable entity dossier book.",
    steps: [
      ["Atelier → Export Chronicle PDF", "Cover page (BESM 4E-style) · Foreword · About TableGnostic · per-session narrative · character appendix · custom-reference appendix · timeline · chat transcripts · legal footer."],
      ["Codex Export PDF (V6.25.30)", "Director's Console → Codex Export. Inverted black-on-white print-friendly theme. Entity nodes (npc / character / creature / monster / faction / location) with structured fields render Azazel-style sectioned pages."],
      ["Author your byline once", "Settings → Byline. Used as 'Written by' on every cover."],
      ["Genesis / Epic / World-Tree links", "Phase 6 Knowledge Web seeds become first-class codex nodes — they appear in both PDFs without re-export."],
    ],
  },
  {
    id: "macro-creation",
    tourId: null,
    icon: Wand2,
    title: "Macro creation",
    blurb: "Roll macros · status macros · auto-applies on the battlemap.",
    steps: [
      ["Open Macro Builder", "Director's Console → Macros tab."],
      ["Pick a target", "Player character / NPC / encounter / spell. Macros bind to one target so the system can auto-resolve damage / saves / status."],
      ["Author the dice expression", "Standard d20 grammar — `2d6+CON` / `1d20+PB+DEX adv vs. AC`. Variables resolve from the sheet at roll-time."],
      ["Bind to a status / readied item", "A readied potion macro can decrement charges + apply an effect ring + log to the journal in one action."],
      ["Test against the dice altar", "Macros run through the same altar UI live — every roll is auditable."],
    ],
  },
  {
    id: "session-and-journal",
    tourId: null,
    icon: Calendar,
    title: "Sessions, journals & threads",
    blurb: "Session summary + character journal entries → Loremaster recap pinned for next session.",
    steps: [
      ["Start the session", "Campaign → Sessions → New. Players join. Battlemap, dice altar, video all wire up."],
      ["Players write journal entries", "On any character sheet → History tab → Journal pane. Append entries during play."],
      ["GM writes session notes", "Sessions → current session → Summary. Combine with character journals for a layered recap."],
      ["Finalise → Loremaster recap", "Claude-powered recap injects every journal entry, GM summary, and chat transcript and outputs a tight prose recap pinned to the next session's opener."],
    ],
  },
];

export default function HowToGuide() {
  const [openId, setOpenId] = useState("");
  const { launch } = useTour();
  const [pickerFor, setPickerFor] = useState(null);  // recipe awaiting a campaign choice
  const [campaigns, setCampaigns] = useState([]);
  const [loadingCamps, setLoadingCamps] = useState(false);
  // V6.25.30 — per-system tab inside system-aware recipes (default to BESM
  // because Maiden Voyage is BESM 4E and that's the seeded fixture).
  const [systemTab, setSystemTab] = useState("besm-4e");
  // V6.25.30 — screenshot lightbox.
  const [lightbox, setLightbox] = useState(null);

  // Lazy-load campaigns the first time the user launches a campaign-scoped tour.
  const ensureCampaigns = async () => {
    if (campaigns.length > 0) return campaigns;
    setLoadingCamps(true);
    try {
      const { data } = await api.get("/campaigns");
      setCampaigns(data || []);
      return data || [];
    } catch {
      return [];
    } finally {
      setLoadingCamps(false);
    }
  };

  const launchTour = async (recipe) => {
    if (!recipe.tourId) return;
    const tour = TOURS[recipe.tourId];
    if (!tour) return;
    if (tour.needsCampaign) {
      const cs = await ensureCampaigns();
      if (cs.length === 0) {
        alert("No campaigns yet — create one from the Campaigns page first, then come back here.");
        return;
      }
      if (cs.length === 1) {
        launch(recipe.tourId, { cid: cs[0].id });
        return;
      }
      setPickerFor({ recipe, tour });
      return;
    }
    launch(recipe.tourId, {});
  };

  const pickCampaignAndStart = (cid) => {
    if (!pickerFor) return;
    launch(pickerFor.recipe.tourId, { cid });
    setPickerFor(null);
  };

  return (
    <div className="px-8 md:px-12 py-10 max-w-5xl" data-testid="howto-guide">
      <div className="flex items-baseline gap-3 mb-2">
        <Compass className="w-8 h-8 text-gold-bright"/>
        <h1 className="font-display text-4xl text-parchment">How to TableGnostic</h1>
      </div>
      <div className="text-mist font-body italic mb-6 max-w-2xl">
        Recipes for the table — from conjuring a campaign to chroniclising it.
        Click any card to expand step-by-step instructions, switch system tabs
        for system-aware guidance, peek at example screenshots, or launch an
        <b className="text-gold-bright"> interactive tour</b> that spotlights
        the real UI as it narrates each step.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {RECIPES.map((r) => {
          const Icon = r.icon;
          const open = openId === r.id;
          const hasTour = !!r.tourId && !!TOURS[r.tourId];
          return (
            <div key={r.id}
                 className={`card-mystic p-5 transition-all border-l-4 ${
                   open ? "border-l-gold" : "border-l-gold/20 hover:border-l-gold/60"
                 }`}
                 data-testid={`howto-card-${r.id}`}>
              <div className="flex items-baseline gap-3 cursor-pointer"
                   onClick={() => setOpenId(open ? "" : r.id)}>
                <Icon className="w-5 h-5 text-gold-bright flex-shrink-0"/>
                <div className="flex-1 min-w-0">
                  <div className="font-display text-lg text-parchment">{r.title}</div>
                  <div className="text-[12px] text-mist italic mt-0.5">{r.blurb}</div>
                </div>
                <ChevronRight className={`w-4 h-4 text-mist transition-transform ${open ? "rotate-90" : ""}`}/>
              </div>
              {open && (
                <>
                  {/* V6.25.30 — per-system tab strip for system-aware recipes. */}
                  {r.bySystem && (
                    <div className="mt-3 flex flex-wrap gap-1"
                         data-testid={`howto-system-tabs-${r.id}`}>
                      {Object.keys(r.systems || {}).map((sid) => (
                        <button key={sid}
                                onClick={(e) => { e.stopPropagation(); setSystemTab(sid); }}
                                className={`px-2 py-0.5 text-[10px] uppercase tracking-widest rounded-sm border font-ui ${
                                  systemTab === sid
                                    ? "bg-gold/15 text-gold-bright border-gold"
                                    : "border-gold/20 text-mist hover:bg-gold/5"
                                }`}
                                data-testid={`howto-system-tab-${r.id}-${sid}`}>
                          {sid.replace("-", " ")}
                        </button>
                      ))}
                    </div>
                  )}
                  <ol className="mt-4 space-y-3 pl-2"
                      data-testid={`howto-steps-${r.id}`}>
                    {(r.bySystem
                      ? (r.systems[systemTab] || r.systems[Object.keys(r.systems)[0]] || [])
                      : r.steps).map(([head, body], i) => (
                      <li key={i} className="flex gap-3 text-[12px]">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full border border-gold/40 flex items-center justify-center text-[10px] font-display text-gold-bright">
                          {i + 1}
                        </div>
                        <div className="flex-1 leading-snug">
                          <div className="text-sm font-ui text-parchment">{head}</div>
                          <div className="text-mist mt-0.5">{body}</div>
                        </div>
                      </li>
                    ))}
                  </ol>
                  {/* V6.25.30 — screenshot strip; clicking opens the lightbox. */}
                  {Array.isArray(r.screenshots) && r.screenshots.length > 0 && (
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2"
                         data-testid={`howto-shots-${r.id}`}>
                      {r.screenshots.map((shot, idx) => (
                        <button key={idx}
                                onClick={(e) => { e.stopPropagation(); setLightbox(shot); }}
                                className="relative border border-gold/15 rounded-sm overflow-hidden hover:border-gold/60 transition-colors group">
                          <img src={shot.src} alt={shot.caption}
                               className="w-full h-20 object-cover opacity-90 group-hover:opacity-100"/>
                          <div className="absolute inset-x-0 bottom-0 bg-void/85 text-[9px] text-parchment p-1 text-left">
                            {shot.caption}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                  {hasTour && (
                    <div className="mt-4 pt-3 border-t border-gold/10 flex items-center justify-between gap-3 flex-wrap">
                      <div className="text-[11px] text-mist italic flex-1 min-w-0">
                        <Sparkles className="w-3 h-3 inline -mt-0.5 mr-1 text-gold-bright"/>
                        Prefer to follow along in the UI? Launch the guided tour —
                        we'll spotlight each control as we go.
                      </div>
                      <button onClick={() => launchTour(r)}
                              className="btn btn-primary text-[11px] shrink-0"
                              disabled={loadingCamps}
                              data-testid={`howto-launch-tour-${r.id}`}>
                        <Play className="w-3 h-3"/> {loadingCamps ? "Loading…" : "Launch tour"}
                      </button>
                    </div>
                  )}
                  {!hasTour && (
                    <div className="mt-4 pt-3 border-t border-gold/10 text-[10px] text-mist/60 italic"
                         data-testid={`howto-no-tour-${r.id}`}>
                      Interactive tour for this recipe is on the roadmap — use the
                      steps above as a checklist.
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-8 card-mystic p-5 border-l-4 border-l-arcane">
        <div className="flex items-baseline gap-3">
          <BookOpen className="w-4 h-4 text-arcane-light"/>
          <div className="flex-1">
            <div className="font-display text-lg text-arcane-light">Need the rulebook references?</div>
            <div className="text-[12px] text-mist italic mt-1">
              Each system carries an in-app SRD-aware reference library. From a campaign,
              open Atelier → References to browse system-specific Attributes, Skills,
              Defects, and Power Bundle templates. The Spell Conversion Atlas (D&D → BESM)
              is one click away from there.
            </div>
            <Link to="/app/reference" className="inline-flex items-center gap-1 text-[11px] text-arcane mt-2 underline"
                  data-testid="howto-open-reference">
              Open the global Reference page <ChevronRight className="w-3 h-3"/>
            </Link>
          </div>
        </div>
      </div>

      <div className="mt-6 text-[11px] text-mist italic" data-testid="howto-footer">
        <Check className="w-3 h-3 inline -mt-0.5 mr-1"/> Got a workflow that needs a recipe?
        Tell your GM or admin — recipes here are versioned with the platform.
      </div>

      {/* Orientation tour CTA — for first-time users. */}
      <div className="mt-6 flex justify-end">
        <button onClick={() => launchTour({ tourId: "welcome" })}
                className="btn btn-ghost text-[11px]"
                data-testid="howto-launch-welcome">
          <Compass className="w-3 h-3"/> Take the orientation tour
        </button>
      </div>

      {/* Campaign picker modal — for tours that need a campaign context. */}
      {pickerFor && (
        <div className="fixed inset-0 z-[8500] bg-void/80 backdrop-blur-sm flex items-center justify-center p-4"
             data-testid="tour-campaign-picker" onClick={() => setPickerFor(null)}>
          <div className="card-mystic p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-baseline justify-between mb-3">
              <div>
                <div className="text-[10px] tracking-widest uppercase text-gold-bright">Tour · {pickerFor.tour.title}</div>
                <div className="font-display text-xl text-parchment mt-1">Pick a campaign to tour inside</div>
              </div>
              <button onClick={() => setPickerFor(null)}
                      className="text-mist hover:text-ember"
                      data-testid="tour-picker-close">Close</button>
            </div>
            <div className="text-[12px] text-mist italic mb-4">
              This tour walks the real UI — pick which of your campaigns to use as the stage.
            </div>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {campaigns.map((c) => (
                <button key={c.id} onClick={() => pickCampaignAndStart(c.id)}
                        className="w-full text-left p-3 rounded-sm border border-gold/20 hover:border-gold/60 hover:bg-gold/5 flex items-center justify-between gap-3"
                        data-testid={`tour-pick-campaign-${c.id}`}>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-parchment font-ui truncate">{c.name}</div>
                    <div className="text-[10px] text-mist tracking-widest uppercase">{c.system_id}</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-mist"/>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* V6.25.30 — Screenshot lightbox. */}
      {lightbox && (
        <div className="fixed inset-0 z-[8800] bg-void/90 backdrop-blur-md flex items-center justify-center p-6"
             data-testid="howto-lightbox" onClick={() => setLightbox(null)}>
          <button className="absolute top-4 right-4 text-mist hover:text-parchment"
                  onClick={() => setLightbox(null)} aria-label="Close lightbox">
            <X className="w-6 h-6"/>
          </button>
          <div className="max-w-5xl w-full" onClick={(e) => e.stopPropagation()}>
            <img src={lightbox.src} alt={lightbox.caption}
                 className="w-full max-h-[78vh] object-contain border border-gold/40"
                 data-testid="howto-lightbox-img"/>
            <div className="text-parchment text-sm mt-3 font-body">
              <ImageIcon className="w-3 h-3 inline -mt-0.5 mr-1"/>{lightbox.caption}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
