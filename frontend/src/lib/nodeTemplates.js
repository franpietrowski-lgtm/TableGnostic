// World Codex — per-type article templates inspired by World Anvil's structured fields.
// Each template is a list of field descriptors used to render type-specific node editors.

export const NODE_TYPES = [
  { key: "npc",       label: "Character / NPC", color: "#c8a34a" },
  { key: "location",  label: "Location",        color: "#6d4a9e" },
  { key: "faction",   label: "Organization",    color: "#b5542b" },
  { key: "event",     label: "Event",           color: "#7a8a6e" },
  { key: "creature",  label: "Species / Creature", color: "#8a6b20" },
  { key: "item",      label: "Item / Artifact", color: "#d4af37" },
  { key: "lore",      label: "Lore / Concept",  color: "#a9a3b8" },
  { key: "quest",     label: "Quest / Hook",    color: "#e5c370" },
];

const f = (key, label, opts = {}) => ({ key, label, ...opts });

// Each template = { intro, fields[] } where fields can have:
//   { key, label, placeholder, textarea, prompt }
export const NODE_TEMPLATES = {
  npc: {
    intro: "Build a person the table will remember by their voice, want, and weakness.",
    fields: [
      f("aliases", "Aliases / Honorifics", { placeholder: "what others call them" }),
      f("gender_species_age", "Gender · Species · Age"),
      f("occupation", "Occupation / Role"),
      f("physical_description", "Physical description", { textarea: true, prompt: "What does the table notice first?" }),
      f("personality", "Personality traits", { textarea: true, prompt: "What single mannerism stays with the players?" }),
      f("motivations", "Motivations / Goals", { textarea: true, prompt: "What do they want before the year is out?" }),
      f("fears", "Fears / Weaknesses", { textarea: true, prompt: "What would unmask them?" }),
      f("affiliations", "Affiliations", { placeholder: "factions, allegiances (comma-separated)" }),
      f("inventory", "Inventory / Gear", { textarea: true }),
      f("backstory", "Backstory beats", { textarea: true, prompt: "Three moments that shaped them." }),
    ],
  },
  location: {
    intro: "A place the players will return to — give it senses and a heartbeat.",
    fields: [
      f("loc_type", "Type", { placeholder: "city · ruin · planet · shrine · dungeon" }),
      f("geography", "Geography / Climate", { textarea: true, prompt: "What does the air feel like here?" }),
      f("population", "Population"),
      f("government", "Government"),
      f("economy", "Economy"),
      f("landmarks", "Notable landmarks", { textarea: true, prompt: "What can be seen from anywhere in the place?" }),
      f("history", "History of the place", { textarea: true, prompt: "What event still echoes in its walls?" }),
      f("inhabitants", "Who lives here", { placeholder: "linked NPCs / factions" }),
      f("connections", "Connected locations", { placeholder: "what borders or links it" }),
    ],
  },
  faction: {
    intro: "Why the world is a chessboard — every faction has a shape it wants the world to take.",
    fields: [
      f("faction_type", "Type", { placeholder: "guild · government · cult · cartel" }),
      f("leadership", "Leadership", { placeholder: "who speaks for it" }),
      f("members", "Members", { placeholder: "core members (linked NPCs)" }),
      f("ideology", "Goals / Ideology", { textarea: true, prompt: "What world do they want?" }),
      f("resources", "Resources", { textarea: true }),
      f("enemies_allies", "Enemies / Allies", { textarea: true, prompt: "Who do they need? Who do they fear?" }),
      f("territory", "Territory", { placeholder: "linked locations" }),
    ],
  },
  event: {
    intro: "Time has texture. Mark the moments that bend the campaign's spine.",
    fields: [
      f("date", "Date / Era", { placeholder: "in-world calendar or 'before the second war'" }),
      f("location", "Location", { placeholder: "where it happened" }),
      f("participants", "Participants", { placeholder: "who was there" }),
      f("causes", "Causes", { textarea: true, prompt: "What set the stage?" }),
      f("outcomes", "Outcomes", { textarea: true, prompt: "What changed in the world?" }),
      f("consequences", "Long-term consequences", { textarea: true }),
      f("related", "Related events", { placeholder: "earlier or later events" }),
    ],
  },
  creature: {
    intro: "Not a stat block — a life-form with logic.",
    fields: [
      f("biology", "Biology / Anatomy", { textarea: true, prompt: "How does it eat, breathe, hunt?" }),
      f("lifespan", "Lifespan"),
      f("culture", "Culture", { textarea: true }),
      f("abilities", "Abilities", { textarea: true }),
      f("weaknesses", "Weaknesses", { textarea: true }),
      f("relations", "Relations with other species", { textarea: true }),
      f("origin", "Origin / Evolution", { textarea: true }),
    ],
  },
  item: {
    intro: "Objects of consequence. Every great item asks for something in return.",
    fields: [
      f("item_type", "Type", { placeholder: "weapon · relic · tech · vestment" }),
      f("function", "Function", { textarea: true, prompt: "What does it do? At what cost?" }),
      f("origin", "Origin", { textarea: true }),
      f("owners", "Owner(s)", { placeholder: "current and former" }),
      f("abilities", "Abilities / Effects", { textarea: true }),
      f("limitations", "Limitations / Cost", { textarea: true, prompt: "What does it demand?" }),
      f("history", "History of ownership", { textarea: true }),
    ],
  },
  lore: {
    intro: "Magic systems, religions, languages, scientific rules, cultural practices.",
    fields: [
      f("kind", "Kind", { placeholder: "magic · religion · language · science · custom" }),
      f("description", "Description", { textarea: true, prompt: "What does an outsider see first?" }),
      f("rules", "Rules / Mechanics", { textarea: true, prompt: "How does it actually work? What does it cost?" }),
      f("origin", "Origin", { textarea: true }),
      f("limitations", "Limitations", { textarea: true }),
      f("known_users", "Known users / groups", { placeholder: "who practises it" }),
    ],
  },
  quest: {
    intro: "A thread the players might pull — write it loose enough to surprise you.",
    fields: [
      f("hook", "Hook", { textarea: true, prompt: "How does the table first hear about it?" }),
      f("stakes", "Stakes", { textarea: true, prompt: "What shifts in the world if they fail?" }),
      f("twist", "Possible twist", { textarea: true }),
      f("rewards", "Rewards", { textarea: true }),
      f("npcs_involved", "NPCs involved", { placeholder: "linked NPCs" }),
      f("locations_involved", "Locations involved", { placeholder: "linked locations" }),
    ],
  },
};

export const colorForType = (t) => (NODE_TYPES.find((x) => x.key === t) || {}).color || "#c8a34a";
export const labelForType = (t) => (NODE_TYPES.find((x) => x.key === t) || {}).label || t;
