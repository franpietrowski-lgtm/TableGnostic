/**
 * V6.25.47 — Worldbuilder Cosmology tool.
 *
 * Multi-kind ledger: planar layers, calendar months, cosmic events,
 * omens, celestial bodies. The kinds-facet groups them in the UI;
 * backend enforces the same enumeration.
 */
import React from "react";
import { Compass } from "lucide-react";
import { CrudListTool, WRITER_THEME } from "./CrudListTool";

const KINDS = [
  ["planar_layer",   "Planar layers"],
  ["calendar_month", "Calendar months"],
  ["cosmic_event",   "Cosmic events"],
  ["omen",           "Omens & prophecies"],
  ["celestial_body", "Celestial bodies"],
];

const FIELDS = [
  { key: "name",                 label: "Name",
    placeholder: "e.g. The Veiled Tier" },
  { key: "summary",              label: "Summary", multiline: true,
    placeholder: "Brief description, lore hooks, mortal-facing rumours…",
    maxLength: 4000 },
  { key: "bleed_through_rules",  label: "Bleed-through rules", multiline: true,
    placeholder: "How does this layer/event interact with the prime?",
    maxLength: 2000 },
  { key: "when_date",            label: "When (date / cadence)",
    placeholder: "e.g. 3rd of Aurelin, every 7 years",
    maxLength: 120 },
];

export default function WbCosmologyTool({ campId }) {
  return (
    <CrudListTool
      campId={campId}
      basePath="/writer/cosmology"
      collectionKey="entries"
      theme={WRITER_THEME.emerald}
      icon={Compass}
      pageTitle="Cosmology & Calendar"
      pageBlurb="The shape of time and the layers of reality. The skeleton every culture's calendar pins itself to."
      fields={FIELDS}
      kinds={KINDS}
      kindLabel="Kind"
      testidPrefix="wb-cosmology"
    />
  );
}
