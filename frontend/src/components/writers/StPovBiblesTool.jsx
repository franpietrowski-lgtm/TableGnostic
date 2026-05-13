/**
 * V6.25.47 — Storyteller POV Bibles tool.
 *
 * Literary character sheets (not statted — voiced). Want / Need /
 * Wound triangle + voice quirks + revelation timeline.
 */
import React from "react";
import { Feather } from "lucide-react";
import { CrudListTool, WRITER_THEME } from "./CrudListTool";

const FIELDS = [
  { key: "name",                 label: "Name",
    placeholder: "e.g. Calenwë the Quiet" },
  { key: "voice_quirks",         label: "Voice quirks", multiline: true,
    placeholder: "Speech patterns, rhythms, signature gestures…",
    maxLength: 4000 },
  { key: "vocab_fingerprint",    label: "Vocab fingerprint", multiline: true,
    placeholder: "Favourite words, words they'd never say…",
    maxLength: 2000 },
  { key: "gait",                 label: "Gait & posture", multiline: true,
    placeholder: "How they enter rooms, how they hold pain…",
    maxLength: 1000 },
  { key: "want",                 label: "Want (surface goal)", multiline: true,
    placeholder: "What the character is actively pursuing.",
    maxLength: 2000 },
  { key: "need",                 label: "Need (deeper truth)", multiline: true,
    placeholder: "What they actually need to grow / heal.",
    maxLength: 2000 },
  { key: "wound",                label: "Wound (origin scar)", multiline: true,
    placeholder: "The lie they believe; the moment that made them.",
    maxLength: 2000 },
  { key: "revelations_timeline", label: "Revelations timeline", multiline: true,
    placeholder: "What does the reader know about them, and when?",
    maxLength: 4000 },
];

export default function StPovBiblesTool({ campId }) {
  return (
    <CrudListTool
      campId={campId}
      basePath="/writer/pov-bibles"
      collectionKey="bibles"
      theme={WRITER_THEME.rose}
      icon={Feather}
      pageTitle="POV Character Bibles"
      pageBlurb="Literary sheets. Not statted — voiced. Goals, wounds, lies they believe, how they sound on the page."
      fields={FIELDS}
      testidPrefix="st-pov-bibles"
    />
  );
}
