/**
 * V6.25.47 — Worldbuilder Cultures tool.
 *
 * People-groups, languages, ritual quirks. A flat list (no kinds-
 * facet) of CultureIn records, edited via the shared CrudListTool.
 */
import React from "react";
import { Library } from "lucide-react";
import { CrudListTool, WRITER_THEME } from "./CrudListTool";

const FIELDS = [
  { key: "name",                label: "Name",                placeholder: "e.g. Aurelian Confederation" },
  { key: "summary",             label: "Summary",             multiline: true,
    placeholder: "One-paragraph sketch: vibe, geography, key tensions.", maxLength: 4000 },
  { key: "naming_conventions",  label: "Naming conventions",  multiline: true,
    placeholder: "Phonemes, patronymics, role names…", maxLength: 2000 },
  { key: "etiquette_quirks",    label: "Etiquette & quirks",  multiline: true,
    placeholder: "Greetings, taboos, table manners…",   maxLength: 2000 },
  { key: "language_seed",       label: "Language seed",       multiline: true,
    placeholder: "Phonology hints, a dozen common phrases…", maxLength: 2000 },
  { key: "holidays",            label: "Holidays & rituals",  multiline: true,
    placeholder: "Calendar anchors, ritual cadences…", maxLength: 2000 },
  { key: "diaspora_notes",      label: "Diaspora / migration",multiline: true,
    placeholder: "Where they've spread, how they're received…", maxLength: 2000 },
];

export default function WbCulturesTool({ campId }) {
  return (
    <CrudListTool
      campId={campId}
      basePath="/writer/cultures"
      collectionKey="cultures"
      theme={WRITER_THEME.emerald}
      icon={Library}
      pageTitle="Cultures & Languages"
      pageBlurb="People-groups, their tongues, their rituals, their kitchen smells."
      fields={FIELDS}
      testidPrefix="wb-cultures"
    />
  );
}
