/**
 * SystemBuilderLoader — system-aware character-builder router.
 *
 * The actual builders live in `./builders/{Dnd5e,Cypher,Anime5e}.jsx`.
 * This file resolves URL params + fetches the system reference + the
 * campaign, then dispatches to the matching builder. Re-exports the
 * named builders so any existing import (`import { Dnd5eBuilder } from
 * "./SystemCharacterBuilders"`) keeps working — no breaking changes.
 *
 * Two route shapes are supported:
 *   /app/campaigns/:id/characters/new   → params.id is the CAMPAIGN id
 *   /app/characters/:id/edit            → params.id is the CHARACTER id
 *
 * The discriminator is `pathname.endsWith("/edit")` — the character
 * route includes "/characters/" too, so a substring check would match
 * BOTH and break the new-character flow.
 */
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";

import { Dnd5eBuilder, empty5e } from "./builders/Dnd5e";
import { CypherBuilder, emptyCypher } from "./builders/Cypher";
import { Anime5eBuilder, Anime5eHybridSupplement } from "./builders/Anime5e";

// Re-export so legacy import paths continue to work.
export { Dnd5eBuilder, empty5e, CypherBuilder, emptyCypher,
         Anime5eBuilder, Anime5eHybridSupplement };

export default function SystemBuilderLoader({ systemId }) {
  const params = useParams();
  const isEdit = /\/characters\/[^/]+\/edit$/.test(window.location.pathname);
  const charId = isEdit ? params.id : null;
  const campaignIdFromUrl = isEdit ? null : params.id;
  const [ref_, setRef] = useState(null);
  const [campaign, setCampaign] = useState(null);

  useEffect(() => {
    let cid = campaignIdFromUrl;
    (async () => {
      if (charId && window.location.pathname.includes("/edit")) {
        const existing = await api.get(`/characters/${charId}`).then((x) => x.data).catch(() => null);
        if (existing) cid = existing.campaign_id;
      }
      const [r, c] = await Promise.all([
        api.get(`/systems/${systemId}/reference`).then((x) => x.data).catch(() => null),
        api.get(`/campaigns/${cid}`).then((x) => x.data).catch(() => null),
      ]);
      setRef(r); setCampaign(c);
    })();
    // eslint-disable-next-line
  }, [campaignIdFromUrl, charId, systemId]);

  if (!ref_ || !campaign) return <div className="p-10 text-mist">Summoning the {systemId} forge…</div>;

  if (systemId === "dnd-5e")  return <Dnd5eBuilder  campaign={campaign} ref_={ref_} charId={charId}/>;
  if (systemId === "cypher")  return <CypherBuilder campaign={campaign} ref_={ref_} charId={charId}/>;
  if (systemId === "anime-5e")return <Anime5eBuilder campaign={campaign} ref_={ref_} charId={charId}/>;
  return <div className="p-10 text-mist">Unsupported system.</div>;
}
