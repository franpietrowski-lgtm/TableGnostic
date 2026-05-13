/**
 * V6.25.47 — Storyteller Themes & Motifs tool.
 *
 * Two-kind ledger (theme | motif) with intent / counter-statement /
 * cadence. Drives revision-pass coherence checks.
 */
import React from "react";
import { Target } from "lucide-react";
import { CrudListTool, WRITER_THEME } from "./CrudListTool";

const KINDS = [
  ["theme", "Themes (spine)"],
  ["motif", "Motifs (recurring imagery)"],
];

const FIELDS = [
  { key: "name",               label: "Name",
    placeholder: "e.g. Mercy outlives memory" },
  { key: "intent",             label: "Intent", multiline: true,
    placeholder: "What this theme/motif is FOR in the work.",
    maxLength: 2000 },
  { key: "counter_statement",  label: "Counter-statement", multiline: true,
    placeholder: "The opposing view the story tests against.",
    maxLength: 2000 },
  { key: "cadence",            label: "Cadence",
    placeholder: "linear · climactic · accelerating · …",
    maxLength: 80 },
];

export default function StThemesTool({ campId }) {
  return (
    <CrudListTool
      campId={campId}
      basePath="/writer/themes"
      collectionKey="items"
      theme={WRITER_THEME.rose}
      icon={Target}
      pageTitle="Themes & Motifs"
      pageBlurb="Themes are the spine; motifs are the recurring metaphors. Tracking keeps revision coherent."
      fields={FIELDS}
      kinds={KINDS}
      kindLabel="Kind"
      testidPrefix="st-themes"
    />
  );
}
