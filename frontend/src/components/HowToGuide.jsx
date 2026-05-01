import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen, Compass, ChevronRight, Wand2, Layers, Sparkles,
  ScrollText, Users, Network, Skull, Calendar, FileDown, Check, Play,
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
];

export default function HowToGuide() {
  const [openId, setOpenId] = useState("");
  const { launch } = useTour();
  const [pickerFor, setPickerFor] = useState(null);  // recipe awaiting a campaign choice
  const [campaigns, setCampaigns] = useState([]);
  const [loadingCamps, setLoadingCamps] = useState(false);

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
        Eight recipes for the table — from conjuring a campaign to chroniclising it.
        Click any card to expand step-by-step instructions, or launch an
        <b className="text-gold-bright"> interactive tour</b> that spotlights the real UI
        as it narrates each step.
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
    </div>
  );
}
