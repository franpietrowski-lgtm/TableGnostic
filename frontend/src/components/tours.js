/**
 * Tour registry — V6.15 interactive UI-guided walkthroughs.
 *
 * Each tour is an array of steps. A step shape:
 *   {
 *     selector: '[data-testid="…"]' | string,  // CSS selector of DOM target
 *     title:    "Short headline",
 *     body:     "One-paragraph explanation rendered in the tooltip.",
 *     route?:   "/app/campaigns",              // navigate before running
 *     placement?: "bottom" | "top" | "right" | "left" | "auto",
 *     optional?: true,                          // skip if selector missing
 *   }
 *
 * The tour engine (GuidedTour.jsx) waits up to 4s for `selector` to appear
 * on-screen after route changes before auto-skipping. Optional steps skip
 * silently if the target isn't mounted (e.g. role-gated buttons).
 *
 * Tours that need a campaign context use `{cid}` placeholders — the engine
 * substitutes `tour.cid` at runtime, supplied by the launcher. If the
 * launcher has no cid, a pre-step lets the user pick one from /app/campaigns.
 */
export const TOURS = {
  // ─────────────────────────────────────────────────────────────────────
  "welcome": {
    title: "Welcome to TableGnostic",
    needsCampaign: false,
    steps: [
      {
        route: "/app",
        selector: '[data-testid="shell-sidebar"]',
        title: "Your table's left rail",
        body: "Every feature branches from here — Campaigns, Discover, Reference, Canon Registry, and this How-To page itself.",
        placement: "right",
      },
      {
        selector: '[data-testid="nav-campaigns"]',
        title: "Campaigns — your workshop",
        body: "Where you forge new campaigns and revisit existing ones. Each campaign is a universe of its own: Genesis, sessions, Codex, battlemaps.",
        placement: "right",
      },
      {
        selector: '[data-testid="nav-reference"]',
        title: "Reference — system-aware rulebook",
        body: "A living SRD-aware library per system (BESM 4E, Anime 5E, D&D 5E, Cypher). House rules you publish here flow back into every campaign.",
        placement: "right",
      },
      {
        selector: '[data-testid="nav-canon"]',
        title: "Canon — the public table",
        body: "Public Delta Drops from other GMs. Clone, fork, or draw inspiration — credit stays attached to the source.",
        placement: "right",
      },
      {
        selector: '[data-testid="nav-help"]',
        title: "That's the map",
        body: "You're standing on it. Ready to build?",
        placement: "right",
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────
  "campaign-from-scratch": {
    title: "Author a campaign from scratch",
    needsCampaign: false,
    steps: [
      {
        route: "/app/campaigns",
        selector: '[data-testid="new-campaign-btn"]',
        title: "Forge a campaign",
        body: "Click here to open the Forge. You'll pick one of four systems — BESM 4E, Anime 5E, D&D 5E, or Cypher — and the rest of the flow auto-shapes to your choice.",
        placement: "bottom",
      },
      {
        selector: '[data-testid="campaign-list"], [data-testid="new-campaign-btn"]',
        title: "After creation",
        body: "Your new campaign opens with an empty Genesis tab and an Atelier workbench. The next three steps happen on the campaign page — come back to this tour from the How-To menu once you're inside your campaign.",
        placement: "bottom",
        optional: true,
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────
  "director-console": {
    title: "Run an encounter with the Director's Console",
    needsCampaign: true,
    steps: [
      {
        route: "/app/campaigns/{cid}/director",
        selector: '[data-testid="director-console"]',
        title: "Director's Console",
        body: "The tactical brain of your campaign. Aggregates every NPC you've seeded — Genesis cast, Epic villains, Codex creatures — into encounter drafts.",
        placement: "bottom",
      },
      {
        selector: '[data-testid="director-session-picker"]',
        title: "Pick the active session",
        body: "Sessions appear in their GM-defined timeline order (sequence_index), so prologues and backstory scenes land where they belong — not where they were played.",
        placement: "bottom",
      },
      {
        selector: '[data-testid="director-npc-pool"]',
        title: "The NPC & Creature Pool",
        body: "Everything you've seeded across the campaign, grouped by source. Click any entry to drop it into the current encounter.",
        placement: "right",
      },
      {
        selector: '[data-testid="director-encounter-editor"]',
        title: "The encounter editor",
        body: "Name, type (combat/social/puzzle/chase), party seats, NPCs, and environment. Every edit debounce-triggers a live CR re-analysis.",
        placement: "top",
      },
      {
        selector: '[data-testid="cr-panel"]',
        title: "The CR Panel",
        body: "System-aware Challenge Rating with concrete suggestions — add minions, drop AC, add weather, tune to a target band. All rule-based and deterministic.",
        placement: "left",
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────
  "knowledge-web": {
    title: "Map your world with the Knowledge Web",
    needsCampaign: true,
    steps: [
      {
        route: "/app/campaigns/{cid}",
        selector: '[data-testid="campaign-tabs-nodes"], [data-testid="campaign-tab-nodes"], [data-testid="tab-nodes"], [data-testid="campaign-detail"]',
        title: "Open the campaign",
        body: "Find the Knowledge tab among the campaign's sub-tabs. The Web lives there: Codex nodes, Chart view, Biome Pyramid.",
        placement: "bottom",
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────
  "live-session": {
    title: "Run a live session",
    needsCampaign: true,
    steps: [
      {
        route: "/app/campaigns/{cid}",
        selector: '[data-testid="campaign-detail"], [data-testid="director-btn"]',
        title: "From campaign to Live Session",
        body: "Open the campaign and use the Sessions tab to Start a session. Players join via invite link or by claiming a character seat.",
        placement: "bottom",
      },
    ],
  },

  // ─────────────────────────────────────────────────────────────────────
  "build-character": {
    title: "Build a player character",
    needsCampaign: true,
    steps: [
      {
        route: "/app/campaigns/{cid}",
        selector: '[data-testid="campaign-detail"]',
        title: "Characters tab",
        body: "Every campaign carries a Characters tab. The Forge auto-shapes to the campaign's system — BESM CP buy, D&D class/level, Cypher sentence, or Anime 5E hybrid.",
        placement: "bottom",
      },
    ],
  },
};

/** Reify step route/selector tokens against a context object (e.g. cid). */
export function reifyTour(tour, ctx = {}) {
  if (!tour) return null;
  return {
    ...tour,
    steps: tour.steps.map((step) => ({
      ...step,
      route: step.route ? step.route.replace(/\{(\w+)\}/g, (_, k) => ctx[k] ?? "") : null,
    })),
  };
}
