import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen, Compass, ChevronRight, Wand2, Layers, Sparkles, Map as MapIcon,
  ScrollText, Users, Network, Skull, Calendar, FileDown, Check,
} from "lucide-react";

/**
 * HowToGuide — V6.11 interactive walkthrough.
 *
 * 8 cards, each a discrete "I want to…" recipe. Each opens to step-by-step
 * instructions with deep links into the relevant TableGnostic surface so
 * GMs can perform the workflow as they read. Lives under /app/help so the
 * authenticated shell wraps it (sidebar nav still visible).
 */
const RECIPES = [
  {
    id: "campaign-from-scratch",
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
    icon: FileDown,
    title: "Export a chronicle PDF",
    blurb: "DriveThruRPG-ready, system-branded, with character sheets + journals + chat transcripts + timeline.",
    steps: [
      ["Open Atelier → Export PDF", "Choose Campaign (branded) or Narrative (pure prose) mode."],
      ["Set your byline", "Save your name once; every export uses it on the cover + page footer."],
      ["Download", "Bundle includes: cover · table of contents · per-session narrative · character appendix (sheets + folio.journal entries) · Custom Reference appendix · Timeline pin appendix · Chat transcript appendix · legal footer."],
    ],
  },
];

export default function HowToGuide() {
  const [openId, setOpenId] = useState("");

  return (
    <div className="px-8 md:px-12 py-10 max-w-5xl" data-testid="howto-guide">
      <div className="flex items-baseline gap-3 mb-2">
        <Compass className="w-8 h-8 text-gold-bright"/>
        <h1 className="font-display text-4xl text-parchment">How to TableGnostic</h1>
      </div>
      <div className="text-mist font-body italic mb-6 max-w-2xl">
        Eight recipes for the table — from conjuring a campaign to chroniclising it.
        Click any card to expand step-by-step instructions; deep links open the
        live surface so you can do as you read.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {RECIPES.map((r) => {
          const Icon = r.icon;
          const open = openId === r.id;
          return (
            <div key={r.id}
                 className={`card-mystic p-5 cursor-pointer transition-all border-l-4 ${
                   open ? "border-l-gold" : "border-l-gold/20 hover:border-l-gold/60"
                 }`}
                 onClick={() => setOpenId(open ? "" : r.id)}
                 data-testid={`howto-card-${r.id}`}>
              <div className="flex items-baseline gap-3">
                <Icon className="w-5 h-5 text-gold-bright flex-shrink-0"/>
                <div className="flex-1 min-w-0">
                  <div className="font-display text-lg text-parchment">{r.title}</div>
                  <div className="text-[12px] text-mist italic mt-0.5">{r.blurb}</div>
                </div>
                <ChevronRight className={`w-4 h-4 text-mist transition-transform ${open ? "rotate-90" : ""}`}/>
              </div>
              {open && (
                <ol className="mt-4 space-y-3 pl-2"
                    data-testid={`howto-steps-${r.id}`}>
                  {r.steps.map(([head, body], i) => (
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
    </div>
  );
}
