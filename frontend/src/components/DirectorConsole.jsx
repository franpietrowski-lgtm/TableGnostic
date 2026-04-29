import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  ArrowLeft, Users, Skull, Plus, X, Save, Wand2, Shield, Swords,
  Mountain, Compass, Flame, Scroll, Sparkles, ChevronRight, MapPin,
  AlertTriangle, CheckCircle2, Crown,
} from "lucide-react";

/**
 * GM Director's Console — the tactical brain of the campaign.
 *
 * Aggregates Atelier Genesis (7-phase) + Epic Campaign (8th tab) + Codex NPCs
 * + the seated character roster, and runs a SYSTEM-AWARE Challenge Rating
 * pass on every encounter draft. Suggestions are rule-based ("add a minion",
 * "drop NPC armor", "add an environmental clock") so latency is constant —
 * no LLM round-trip in the encounter loop.
 *
 * Surfaces:
 *   1. Header — campaign / system badge + party current location
 *   2. NPC Pool (left) — drag-style list of every NPC the campaign has
 *      seeded, grouped by source (Genesis · Epic · Codex)
 *   3. Encounter Editor (centre) — current encounter draft + party seats +
 *      rolling CR badge
 *   4. Suggestions panel (right) — actionable nudges with icons
 *
 * GM/admin only — players hitting this route get a 403 from the backend.
 */
export default function DirectorConsole() {
  const { id: cid } = useParams();
  const [doc, setDoc] = useState(null);
  const [characters, setCharacters] = useState([]);
  const [campaign, setCampaign] = useState(null);
  const [activeIdx, setActiveIdx] = useState(0);
  const [analysis, setAnalysis] = useState(null);
  const [busy, setBusy] = useState(false);
  const [savedTick, setSavedTick] = useState(false);
  const [err, setErr] = useState("");

  const load = async () => {
    setErr("");
    try {
      const [d, ch, c] = await Promise.all([
        api.get(`/director/${cid}`).then((r) => r.data),
        api.get(`/campaigns/${cid}/characters`).then((r) => r.data || []),
        api.get(`/campaigns/${cid}`).then((r) => r.data),
      ]);
      // Lazily ensure at least one encounter exists.
      if (!d.encounters || d.encounters.length === 0) {
        d.encounters = [{ id: "draft", name: "Untitled Encounter",
                          party_character_ids: [], npcs: [],
                          environment: { indoor: false }, notes: "" }];
      }
      setDoc(d);
      setCharacters(ch);
      setCampaign(c);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  useEffect(() => { load(); }, [cid]);

  const active = doc?.encounters?.[activeIdx] || null;

  // Re-analyse whenever the active encounter changes.
  useEffect(() => {
    if (!doc || !active) { setAnalysis(null); return; }
    const t = setTimeout(async () => {
      try {
        const { data } = await api.post(`/director/${cid}/cr-analyse`, {
          name: active.name,
          party_character_ids: active.party_character_ids || [],
          npcs: active.npcs || [],
          environment: active.environment || {},
          notes: active.notes || "",
        });
        setAnalysis(data);
      } catch (e) {
        setAnalysis({ rating: "Error", score: 0, reason: "Analysis failed",
                      party_label: "—", npc_label: "—", suggestions: [] });
      }
    }, 250);  // debounce
    return () => clearTimeout(t);
  }, [doc, activeIdx, cid, active?.party_character_ids?.length,
      active?.npcs?.length, JSON.stringify(active?.npcs || [])]);

  const setActive = (patch) => setDoc((d) => {
    const next = { ...d, encounters: [...d.encounters] };
    next.encounters[activeIdx] = { ...next.encounters[activeIdx], ...patch };
    return next;
  });

  const togglePartyMember = (charId) => {
    const ids = active.party_character_ids || [];
    setActive({ party_character_ids: ids.includes(charId)
      ? ids.filter((x) => x !== charId)
      : [...ids, charId] });
  };

  const addNpcFromPool = (pooled) => {
    const npcs = [...(active.npcs || [])];
    npcs.push({
      id: null, name: pooled.name, role: pooled.role || "villain",
      source: pooled.source, source_id: pooled.source_id || null,
      location: doc.current_location || "",
      state: "active", intent: pooled.intent || "",
      level: 3, count: 1, total_points: 0, notes: pooled.notes || "",
    });
    setActive({ npcs });
  };

  const addBlankNpc = () => {
    setActive({ npcs: [...(active.npcs || []), {
      id: null, name: "New NPC", role: "minion",
      source: "manual", source_id: null,
      location: doc.current_location || "", state: "active",
      intent: "", level: 2, count: 1, total_points: 0, notes: "",
    }] });
  };

  const updateNpc = (i, patch) => {
    const npcs = [...(active.npcs || [])];
    npcs[i] = { ...npcs[i], ...patch };
    setActive({ npcs });
  };

  const removeNpc = (i) => {
    const npcs = [...(active.npcs || [])];
    npcs.splice(i, 1);
    setActive({ npcs });
  };

  const newEncounter = () => {
    setDoc((d) => ({
      ...d,
      encounters: [...d.encounters, {
        id: null, name: `Encounter ${d.encounters.length + 1}`,
        party_character_ids: [], npcs: [],
        environment: { indoor: false }, notes: "",
      }],
    }));
    setActiveIdx(doc.encounters.length);
  };

  const save = async () => {
    setBusy(true); setErr("");
    try {
      const payload = {
        encounters: doc.encounters.map((e) => ({ ...e, id: e.id === "draft" ? null : e.id })),
        current_location: doc.current_location || "",
        current_phase_ref: doc.current_phase_ref || "",
      };
      const { data } = await api.put(`/director/${cid}`, payload);
      setDoc({ ...data, npc_pool: doc.npc_pool, system_id: doc.system_id });
      setSavedTick(true);
      setTimeout(() => setSavedTick(false), 1700);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  if (err) return <div className="px-8 py-10 text-ember">{err}</div>;
  if (!doc || !campaign) return <div className="px-8 py-10 text-mist italic">Summoning the Director's Console…</div>;

  const sysId = doc.system_id || campaign?.system_id || "besm-4e";

  return (
    <div className="px-6 sm:px-10 py-8" data-testid="director-console">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
        <div>
          <Link to={`/app/campaigns/${cid}`} className="text-[11px] text-mist hover:text-parchment flex items-center gap-1 mb-1">
            <ArrowLeft className="w-3 h-3"/> Back to campaign
          </Link>
          <div className="label-ref">{campaign.name} · GM Director</div>
          <h1 className="font-display text-3xl sm:text-4xl text-parchment mt-1 flex items-center gap-2">
            <Wand2 className="w-7 h-7 text-gold"/>
            Director's Console
          </h1>
          <p className="text-[11px] text-mist/70 italic mt-1 max-w-2xl">
            Pull NPCs from your Atelier — Genesis seeds, Epic Campaign nemesis &amp; villains, Codex entries — into encounters.
            We'll judge the Challenge Rating against your seated party in <b>{labelForSystem(sysId)}</b>'s native math, and suggest
            additions, environmental levers, and tactical adjustments to make every fight engaging — not easier.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {savedTick && <span className="text-arcane-light text-[10px]">Saved ✓</span>}
          <button onClick={save} disabled={busy} className="btn btn-primary text-xs"
                  data-testid="director-save-btn">
            <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {/* Live location strip */}
      <div className="card-mystic p-4 mb-6 flex items-center gap-3 flex-wrap" data-testid="director-location-strip">
        <MapPin className="w-4 h-4 text-arcane-light"/>
        <div className="flex-1 min-w-0">
          <div className="label-ref mb-1">Party current location</div>
          <input className="input" placeholder="e.g. The Caldera-rim Choir Hall, mid-eclipse"
                 value={doc.current_location || ""}
                 onChange={(e) => setDoc({ ...doc, current_location: e.target.value })}
                 data-testid="director-current-location"/>
        </div>
        <div className="flex-1 min-w-0">
          <div className="label-ref mb-1">Live Atelier phase</div>
          <select className="select" value={doc.current_phase_ref || ""}
                  onChange={(e) => setDoc({ ...doc, current_phase_ref: e.target.value })}
                  data-testid="director-phase-ref">
            <option value="">— pick —</option>
            <option value="genesis-1-sentence">Genesis · 1 — The Sentence</option>
            <option value="genesis-3-nemesis">Genesis · 3 — Nemesis Design</option>
            <option value="genesis-4-plot">Genesis · 4 — Master Plot</option>
            <option value="genesis-5-adventures">Genesis · 5 — Adventure Outlines</option>
            <option value="genesis-6-bookends">Genesis · 6 — Beginning &amp; Ending</option>
            <option value="epic-2-theme">Epic · Theme & Sentence</option>
            <option value="epic-7-milestones">Epic · 7 — Milestones</option>
            <option value="epic-8-adventures">Epic · 8 — Adventures (mode + type)</option>
            <option value="epic-11-climax">Epic · 11 — Climax & Ending</option>
          </select>
        </div>
      </div>

      <div className="grid lg:grid-cols-[260px_1fr_300px] gap-5">
        {/* NPC pool */}
        <NpcPool pool={doc.npc_pool || []} onPick={addNpcFromPool}/>

        {/* Encounter editor */}
        <div data-testid="director-encounter-editor">
          {/* Encounter tabs */}
          <div className="flex items-center gap-1 mb-3 overflow-x-auto" data-testid="director-encounter-tabs">
            {doc.encounters.map((e, i) => (
              <button key={e.id || i} onClick={() => setActiveIdx(i)}
                      className={`px-3 py-1.5 text-[11px] font-ui whitespace-nowrap border-b ${
                        i === activeIdx ? "text-gold-bright border-gold" : "text-mist border-transparent hover:text-parchment"
                      }`}
                      data-testid={`director-encounter-tab-${i}`}>
                {e.name || `Encounter ${i + 1}`}
              </button>
            ))}
            <button onClick={newEncounter} className="text-mist hover:text-gold ml-2 px-2"
                    data-testid="director-add-encounter">
              <Plus className="w-3 h-3 inline"/> add
            </button>
          </div>

          {/* Encounter body */}
          {active && (
            <div className="card-mystic p-5 space-y-4">
              <input className="input font-display text-lg"
                     value={active.name}
                     onChange={(e) => setActive({ name: e.target.value })}
                     placeholder="Encounter name"
                     data-testid="director-encounter-name"/>

              {/* Party seats */}
              <div>
                <div className="label-ref mb-2 flex items-center gap-2">
                  <Users className="w-3 h-3"/> Party seats · {(active.party_character_ids || []).length} of {characters.length}
                </div>
                <div className="grid sm:grid-cols-2 gap-2">
                  {characters.map((c) => {
                    const seated = (active.party_character_ids || []).includes(c.id);
                    return (
                      <button key={c.id} onClick={() => togglePartyMember(c.id)}
                              className={`text-left p-2 rounded-sm border ${
                                seated ? "border-gold bg-gold/10" : "border-gold/15 hover:border-gold/40"
                              }`}
                              data-testid={`director-party-${c.id}`}>
                        <div className="text-sm text-parchment font-ui truncate">{c.name}</div>
                        <div className="text-[10px] text-mist tracking-widest uppercase">
                          {pcBlurb(c, sysId)}
                        </div>
                      </button>
                    );
                  })}
                  {characters.length === 0 && (
                    <div className="text-mist italic text-xs">No characters in this campaign yet.</div>
                  )}
                </div>
              </div>

              {/* NPCs in encounter */}
              <div>
                <div className="label-ref mb-2 flex items-center gap-2 justify-between">
                  <span><Skull className="w-3 h-3 inline mr-1"/> Encounter NPCs · {(active.npcs || []).length}</span>
                  <button onClick={addBlankNpc} className="btn btn-ghost text-xs"
                          data-testid="director-add-blank-npc">
                    <Plus className="w-3 h-3"/> Blank NPC
                  </button>
                </div>
                <div className="space-y-2">
                  {(active.npcs || []).map((n, i) => (
                    <NpcRow key={n.id || i} n={n} idx={i} systemId={sysId}
                            onPatch={(p) => updateNpc(i, p)}
                            onRemove={() => removeNpc(i)}/>
                  ))}
                  {(active.npcs || []).length === 0 && (
                    <div className="text-mist italic text-xs">No NPCs yet — pick one from the Pool on the left or add a Blank.</div>
                  )}
                </div>
              </div>

              {/* Environment */}
              <div>
                <div className="label-ref mb-2 flex items-center gap-2">
                  <Mountain className="w-3 h-3"/> Environment
                </div>
                <div className="grid sm:grid-cols-3 gap-2 text-[11px]">
                  <label className="flex items-center gap-2 border border-gold/15 rounded-sm p-2">
                    <input type="checkbox" checked={!!active.environment?.indoor}
                           onChange={(e) => setActive({ environment: { ...(active.environment || {}), indoor: e.target.checked } })}
                           data-testid="director-env-indoor"/>
                    <span>Indoor / line-of-sight breaks</span>
                  </label>
                  <input className="input" placeholder="Weather (storm, fog…)"
                         value={active.environment?.weather || ""}
                         onChange={(e) => setActive({ environment: { ...(active.environment || {}), weather: e.target.value } })}
                         data-testid="director-env-weather"/>
                  <input className="input" placeholder="Light (dim, dark, magical…)"
                         value={active.environment?.light || ""}
                         onChange={(e) => setActive({ environment: { ...(active.environment || {}), light: e.target.value } })}
                         data-testid="director-env-light"/>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* CR + suggestions */}
        <CrPanel analysis={analysis} systemId={sysId}/>
      </div>
    </div>
  );
}


// ────────────────────── sub-components ──────────────────────

function NpcPool({ pool, onPick }) {
  const grouped = useMemo(() => {
    const out = { genesis: [], epic: [], codex: [] };
    (pool || []).forEach((p) => { (out[p.source] || (out[p.source] = [])).push(p); });
    return out;
  }, [pool]);
  return (
    <div className="card-mystic p-4 self-start sticky top-4" data-testid="director-npc-pool">
      <div className="label-ref mb-2">NPC Pool</div>
      <div className="text-[10px] text-mist/70 italic mb-3">
        Drag-pick from your Atelier. Click adds to the active encounter.
      </div>
      {Object.entries({ genesis: "Genesis seeds", epic: "Epic Campaign", codex: "Codex" }).map(([k, label]) => {
        const items = grouped[k] || [];
        if (items.length === 0) return null;
        return (
          <div key={k} className="mb-3" data-testid={`pool-group-${k}`}>
            <div className="text-[10px] tracking-widest uppercase text-arcane-light mb-1">{label}</div>
            <div className="space-y-1">
              {items.map((p, i) => (
                <button key={p.source_id || `${k}-${i}`} onClick={() => onPick(p)}
                        className="w-full text-left p-2 rounded-sm border border-gold/15 hover:border-gold/40 hover:bg-gold/5"
                        data-testid={`pool-pick-${k}-${i}`}>
                  <div className="text-xs text-parchment font-ui flex items-center justify-between">
                    <span className="truncate">{p.name}</span>
                    <ChevronRight className="w-3 h-3 text-mist"/>
                  </div>
                  {p.intent && <div className="text-[10px] text-mist line-clamp-2 italic">{p.intent}</div>}
                </button>
              ))}
            </div>
          </div>
        );
      })}
      {(pool || []).length === 0 && (
        <div className="text-[11px] text-mist italic">
          No NPCs seeded yet. Forge some in the Atelier — Genesis Phase 5 (Supporting Cast)
          or the Epic Campaign tab — and they'll appear here.
        </div>
      )}
    </div>
  );
}

function NpcRow({ n, idx, systemId, onPatch, onRemove }) {
  return (
    <div className="border border-gold/15 rounded-sm p-3" data-testid={`director-npc-${idx}`}>
      <div className="grid sm:grid-cols-[1fr_120px_90px_24px] gap-2 items-center">
        <input className="input" value={n.name}
               onChange={(e) => onPatch({ name: e.target.value })}
               placeholder="NPC name"
               data-testid={`director-npc-${idx}-name`}/>
        <select className="select" value={n.role || "minion"}
                onChange={(e) => onPatch({ role: e.target.value })}
                data-testid={`director-npc-${idx}-role`}>
          <option value="minion">Minion</option>
          <option value="henchman">Henchman</option>
          <option value="villain">Villain</option>
          <option value="nemesis">Nemesis</option>
          <option value="ally">Ally</option>
        </select>
        <select className="select text-xs" value={n.state || "active"}
                onChange={(e) => onPatch({ state: e.target.value })}
                data-testid={`director-npc-${idx}-state`}>
          <option value="active">Active</option>
          <option value="wounded">Wounded</option>
          <option value="bloodied">Bloodied</option>
          <option value="fled">Fled</option>
          <option value="down">Down</option>
        </select>
        <button onClick={onRemove} className="text-ember/60 hover:text-ember"
                data-testid={`director-npc-${idx}-remove`}>
          <X className="w-4 h-4"/>
        </button>
      </div>
      <div className="grid sm:grid-cols-[1fr_120px_80px] gap-2 mt-2">
        <input className="input" placeholder="Location"
               value={n.location || ""}
               onChange={(e) => onPatch({ location: e.target.value })}
               data-testid={`director-npc-${idx}-location`}/>
        <input className="input" placeholder="Current intent"
               value={n.intent || ""}
               onChange={(e) => onPatch({ intent: e.target.value })}
               data-testid={`director-npc-${idx}-intent`}/>
        <input className="input text-center" type="number" min={1}
               value={n.count || 1}
               onChange={(e) => onPatch({ count: Math.max(1, +e.target.value || 1) })}
               title="Count"
               data-testid={`director-npc-${idx}-count`}/>
      </div>
      {/* System-specific stat-block hint */}
      <div className="grid sm:grid-cols-3 gap-2 mt-2">
        {systemId === "dnd-5e" && (
          <input className="input" placeholder="CR (e.g. 1, 1/4, 5)"
                 value={n.cr || ""}
                 onChange={(e) => onPatch({ cr: e.target.value })}
                 data-testid={`director-npc-${idx}-cr`}/>
        )}
        {(systemId === "cypher" || systemId === "anime-5e") && (
          <input className="input" type="number" min={1} max={10}
                 placeholder="Level (1-10)"
                 value={n.level || ""}
                 onChange={(e) => onPatch({ level: +e.target.value || 0 })}
                 data-testid={`director-npc-${idx}-level`}/>
        )}
        {(systemId === "besm-4e" || systemId === "anime-5e") && (
          <input className="input" type="number" min={0}
                 placeholder="CP (point total)"
                 value={n.total_points || ""}
                 onChange={(e) => onPatch({ total_points: +e.target.value || 0 })}
                 data-testid={`director-npc-${idx}-cp`}/>
        )}
      </div>
    </div>
  );
}

function CrPanel({ analysis, systemId }) {
  if (!analysis) return (
    <div className="card-mystic p-5 self-start sticky top-4" data-testid="cr-panel">
      <div className="text-mist italic text-xs">Calculating…</div>
    </div>
  );
  const colour = ratingColour(analysis.rating);
  return (
    <div className="card-mystic p-5 self-start sticky top-4 space-y-4" data-testid="cr-panel">
      <div>
        <div className="label-ref">Challenge Rating · {labelForSystem(systemId)}</div>
        <div className="mt-2 flex items-center gap-3">
          <div className="font-display text-3xl" style={{ color: colour }}
               data-testid="cr-rating">{analysis.rating}</div>
          <div className="flex-1">
            <div className="text-[10px] text-mist tracking-widest uppercase">difficulty</div>
            <div className="h-2 bg-void/60 rounded-sm overflow-hidden mt-1">
              <div className="h-full transition-all" style={{
                width: `${Math.round((analysis.score || 0) * 100)}%`,
                backgroundColor: colour,
              }} data-testid="cr-score-bar"/>
            </div>
          </div>
        </div>
        <div className="text-[11px] text-mist/80 italic mt-2 leading-snug">{analysis.reason}</div>
      </div>
      <div className="text-[11px] text-parchment/85 space-y-1">
        <div><b>Party:</b> {analysis.party_label}</div>
        <div><b>NPCs:</b> {analysis.npc_label}</div>
      </div>
      {(analysis.suggestions || []).length > 0 && (
        <div data-testid="cr-suggestions">
          <div className="label-ref mb-2 flex items-center gap-2">
            <Sparkles className="w-3 h-3"/> Suggestions
          </div>
          <div className="space-y-2">
            {analysis.suggestions.map((sg, i) => (
              <div key={i} className="border border-gold/15 rounded-sm p-2 flex items-start gap-2"
                   data-testid={`cr-suggestion-${i}`}>
                <span className="text-arcane-light shrink-0">{iconFor(sg.icon)}</span>
                <div className="text-[11px] text-parchment/85 leading-snug flex-1">
                  {sg.label}
                </div>
                {typeof sg.delta === "number" && sg.delta !== 0 && (
                  <span className={`text-[10px] tracking-widest uppercase shrink-0 ${
                    sg.delta > 0 ? "text-gold" : "text-ember"
                  }`}>
                    {sg.delta > 0 ? "+" : ""}{sg.delta}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


// ────────────────────── helpers ──────────────────────

function labelForSystem(sysId) {
  return ({
    "dnd-5e":   "D&D 5E (DMG p.82)",
    "cypher":   "Cypher (Difficulty × 3)",
    "besm-4e":  "BESM 4E (CP ratio ±15%)",
    "anime-5e": "Anime 5E (hybrid)",
  })[sysId] || sysId;
}

function ratingColour(rating) {
  return ({
    Pushover:   "#7BBD8C",   // green
    Easy:       "#9EC4DA",   // pale blue
    Fair:       "#D8C285",   // gold
    Medium:     "#D8C285",
    Hard:       "#E69A4C",   // amber
    Deadly:     "#D14545",   // red
    Punishing:  "#D14545",
    Unknown:    "#7C8298",
    Error:      "#D14545",
  })[rating] || "#D8C285";
}

function iconFor(name) {
  const cls = "w-3.5 h-3.5";
  return ({
    swords:    <Swords className={cls}/>,
    shield:    <Shield className={cls}/>,
    mountain:  <Mountain className={cls}/>,
    compass:   <Compass className={cls}/>,
    flame:     <Flame className={cls}/>,
    scroll:    <Scroll className={cls}/>,
    sparkles:  <Sparkles className={cls}/>,
    x:         <X className={cls}/>,
    door:      <ChevronRight className={cls}/>,
    crown:     <Crown className={cls}/>,
    skull:     <Skull className={cls}/>,
  })[name] || <AlertTriangle className={cls}/>;
}

function pcBlurb(c, sysId) {
  const dnd = c.folio?.dnd_state;
  const cyph = c.folio?.cypher_state;
  if (cyph) return `T${cyph.tier || 1} · ${cyph.descriptor || "?"} ${cyph.type || "?"}`;
  if (dnd)  return `${dnd.class || "?"} ${dnd.level || 1} · AC ${10 + Math.floor(((dnd.ability_scores?.Dexterity || 10) - 10) / 2)}`;
  return `BESM · ${c.total_points || 0} CP`;
}
