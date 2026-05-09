/**
 * ConceptForge V2 — V6.25.34
 *
 * Multi-field BESM-quiz-inspired character brief that respects the
 * campaign's Player Primer (CP cap, max attribute rank, allow/prohibit
 * lists). Optional Codex entity import for additional context.
 *
 * Output candidates now include: appearance, origin, goals, dreams,
 * personality knots, history, race, class, stats, attributes, skills,
 * defects, power_packs, items, weapons (weapon-items), estimated_cp.
 *
 * Drafts → GM approval queue → Player commits → CharacterBuilder
 * pre-fills identity / mechanics / inventory / folio.
 */
import React, { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, Loader2, Check, X, Send, Trash2, ChevronRight,
         ScrollText, Library, ChevronDown } from "lucide-react";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";

const SUPPORTED = new Set(["besm-4e", "anime-5e"]);

// Multi-field brief shape mirrors the backend's ConceptForgeIn schema.
const BLANK_BRIEF = {
  concept_text:      "",
  appearance:        "",
  origin:            "",
  role:              "",
  signature_traits:  "",
  carried_gear:      "",
  goals:             "",
  dreams:            "",
  personality_knots: "",
  history:           "",
};

// Five questions the BESM 4E character quiz asks plus narrative anchors.
const FIELD_DEFS = [
  { k: "role",              l: "Role at the table",          ph: "Tank? Healer? Skill-monkey infiltrator? Pure caster? Social face?", rows: 2, important: true },
  { k: "signature_traits",  l: "Signature traits / abilities", ph: "What 2-3 abilities make this character iconic? (e.g. flame magic, mecha pilot, healing hands, perfect aim).", rows: 2, important: true },
  { k: "appearance",        l: "Appearance",                  ph: "Physical description, age, distinctive markings or accoutrements.", rows: 2 },
  { k: "origin",            l: "Origin / homeland / heritage",ph: "Where they're from, what culture, family standing, defining childhood.", rows: 2 },
  { k: "carried_gear",      l: "Carried gear / weapons",      ph: "What's in their kit by default? (e.g. ‘a phoenix-themed staff and a pouch of healing tinctures’). The Forge will translate this into proper Items / Weapons / Weapon-Items.", rows: 2 },
  { k: "goals",             l: "Goals (short-term + long)",   ph: "Active drives at and beyond the table.", rows: 2 },
  { k: "dreams",             l: "Dreams (aspirational)",      ph: "What would they do if no one was watching? Their truest hope.", rows: 2 },
  { k: "personality_knots", l: "Personality knots / flaws / vows", ph: "What slows them down narratively? Codes they cannot break.", rows: 2 },
  { k: "history",           l: "History / formative events",  ph: "Notable beats already lived. Wounds, lessons, betrayals.", rows: 2 },
  { k: "concept_text",      l: "Free-form additional notes",  ph: "Anything that didn't fit the boxes above. Pitch it like a paragraph.", rows: 3 },
];


export default function ConceptForge() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [campaigns, setCampaigns] = useState([]);
  const [campId, setCampId] = useState("");
  const [camp, setCamp] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [brief, setBrief] = useState(BLANK_BRIEF);
  const [codexNodes, setCodexNodes] = useState([]);
  const [importedNodeIds, setImportedNodeIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [activeTab, setActiveTab] = useState("forge");

  useEffect(() => {
    api.get("/campaigns").then((r) => {
      const list = (r.data || []).filter((c) => SUPPORTED.has(c.system_id));
      setCampaigns(list);
      if (list.length > 0 && !campId) setCampId(list[0].id);
    }).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const reload = useCallback(async () => {
    if (!campId) return;
    const [c, d, n] = await Promise.all([
      api.get(`/campaigns/${campId}`).then((r) => r.data).catch(() => null),
      api.get(`/campaigns/${campId}/concept-drafts`).then((r) => r.data).catch(() => ({ drafts: [] })),
      api.get(`/campaigns/${campId}/nodes`).then((r) => r.data).catch(() => []),
    ]);
    setCamp(c);
    setDrafts(d.drafts || []);
    // Filter to entity-flavoured node kinds the player would want as canon material.
    const ENTITY_KINDS = new Set(["npc", "character", "creature", "monster",
      "person", "faction", "location", "item", "deity", "patron", "organisation"]);
    setCodexNodes((n || []).filter((x) => ENTITY_KINDS.has((x.node_kind || x.type || "").toLowerCase())));
  }, [campId]);

  useEffect(() => { reload(); }, [reload]);

  const submit = async () => {
    setErr("");
    const payload = { ...brief, imported_codex_node_ids: importedNodeIds };
    const totalLen = Object.values(brief).map((v) => (v || "").trim()).join("").length;
    if (totalLen < 20) {
      setErr("Brief is too short — fill in at least one or two of the structured fields.");
      return;
    }
    setLoading(true);
    try {
      await api.post(`/campaigns/${campId}/concept-drafts`, payload);
      setBrief(BLANK_BRIEF);
      setImportedNodeIds([]);
      setActiveTab("drafts");
      await reload();
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail, e));
    } finally {
      setLoading(false);
    }
  };

  const isGm = !!camp?.is_gm;

  return (
    <div className="px-6 md:px-12 py-10 max-w-6xl" data-testid="concept-forge-page">
      <div className="flex items-baseline justify-between flex-wrap gap-3 mb-6">
        <div>
          <h1 className="font-display tracking-[0.18em] text-3xl text-parchment">Concept Forge</h1>
          <div className="text-mist text-sm mt-1 max-w-xl">
            BESM-quiz inspired multi-field brief. Honors the campaign's Player
            Primer (CP cap, benchmarks, allow/prohibit lists). Two builds
            returned per concept; GM approves; Player commits;
            CharacterBuilder pre-fills identity, mechanics, inventory, and folio.
          </div>
        </div>
        <select className="select" value={campId}
                onChange={(e) => setCampId(e.target.value)}
                data-testid="forge-campaign-select">
          {campaigns.length === 0 && <option value="">— no eligible campaigns —</option>}
          {campaigns.map((c) => (
            <option key={c.id} value={c.id}>{c.name} · {c.system_id}</option>
          ))}
        </select>
      </div>

      {campaigns.length === 0 && (
        <div className="card-mystic p-6 text-center">
          <ScrollText className="w-8 h-8 mx-auto text-gold/60 mb-2"/>
          <div className="text-parchment text-sm mb-2">
            No BESM 4E or Anime 5E campaigns found.
          </div>
          <Link to="/app/campaigns" className="btn btn-primary text-xs">
            Forge a Campaign First <ChevronRight className="w-3 h-3"/>
          </Link>
        </div>
      )}

      {campId && camp && (
        <>
          <PrimerBanner camp={camp}/>

          <div className="flex gap-2 border-b border-gold/10 mb-4">
            {[["forge", "Forge"], ["drafts", `Drafts${drafts.length ? ` · ${drafts.length}` : ""}`]].map(([k, l]) => (
              <button key={k} type="button" onClick={() => setActiveTab(k)}
                      className={`px-4 py-2 text-xs font-ui tracking-widest uppercase ${activeTab === k ? "text-gold-bright border-b border-gold" : "text-mist hover:text-parchment"}`}
                      data-testid={`forge-tab-${k}`}>
                {l}
              </button>
            ))}
          </div>

          {activeTab === "forge" && (
            <ForgeBriefForm brief={brief} setBrief={setBrief}
                            codexNodes={codexNodes}
                            importedNodeIds={importedNodeIds}
                            setImportedNodeIds={setImportedNodeIds}
                            submit={submit} loading={loading} err={err}/>
          )}
          {activeTab === "drafts" && (
            <DraftsTab drafts={drafts} isGm={isGm} userId={user?.id}
                       campId={campId} reload={reload} nav={nav}/>
          )}
        </>
      )}
    </div>
  );
}


/**
 * Surface the campaign's primer constraints so the player sees what
 * the Forge is being told to respect.
 */
function PrimerBanner({ camp }) {
  const cpCap = camp.character_point_max || 0;
  const attrCap = camp.max_per_attribute_rank || 0;
  const tags = [];
  if (cpCap > 0)   tags.push(`CP cap · ${cpCap}`);
  if (attrCap > 0) tags.push(`Max attr rank · ${attrCap}`);
  if (camp.power_level)   tags.push(`Power · ${camp.power_level}`);
  if (camp.genre)         tags.push(`Genre · ${camp.genre}`);
  if (camp.time_period)   tags.push(`Era · ${camp.time_period}`);
  if ((camp.allowed_attributes || []).length)   tags.push(`Allowed attrs · ${camp.allowed_attributes.length}`);
  if ((camp.prohibited_attributes || []).length)tags.push(`Prohibited · ${camp.prohibited_attributes.length}`);
  return (
    <div className="card-mystic p-3 mb-4 flex flex-wrap items-center gap-2"
         data-testid="forge-primer-banner">
      <span className="text-gold/70 text-[10px] uppercase tracking-widest">Primer constraints</span>
      {tags.map((t, i) => (
        <span key={i} className="tag bg-gold/10 text-gold-bright text-[10px]">{t}</span>
      ))}
      {tags.length === 0 && (
        <span className="text-mist/70 text-[11px] italic">
          No primer caps set — Forge uses Power Level defaults.
        </span>
      )}
      {camp.player_primer && (
        <details className="w-full mt-2">
          <summary className="cursor-pointer text-[11px] text-mist hover:text-parchment">
            Read primer note
          </summary>
          <div className="text-[11px] text-parchment whitespace-pre-wrap mt-1 italic">
            {camp.player_primer}
          </div>
        </details>
      )}
    </div>
  );
}


function ForgeBriefForm({ brief, setBrief, codexNodes, importedNodeIds,
                          setImportedNodeIds, submit, loading, err }) {
  const update = (k, v) => setBrief((b) => ({ ...b, [k]: v }));
  return (
    <div className="card-mystic p-5" data-testid="forge-input-panel">
      <div className="grid md:grid-cols-2 gap-4">
        {FIELD_DEFS.map((f) => (
          <div key={f.k} className={f.k === "concept_text" || f.k === "history" ? "md:col-span-2" : ""}>
            <label className="label-ref block mb-1">
              {f.l} {f.important && <span className="text-gold-bright">*</span>}
            </label>
            <textarea className="input font-body leading-relaxed"
                      style={{ minHeight: `${(f.rows || 2) * 28}px` }}
                      value={brief[f.k]}
                      onChange={(e) => update(f.k, e.target.value)}
                      placeholder={f.ph}
                      data-testid={`forge-field-${f.k}`}/>
          </div>
        ))}
      </div>

      {codexNodes.length > 0 && (
        <CodexImportPicker nodes={codexNodes}
                           selected={importedNodeIds}
                           onChange={setImportedNodeIds}/>
      )}

      {err && (
        <div className="mt-3 text-sm text-ember" data-testid="forge-error">
          {err}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={submit} disabled={loading}
                className="btn btn-primary"
                data-testid="forge-submit-btn">
          {loading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Sparkles className="w-4 h-4"/>}
          {loading ? "Forging…" : "Forge Two Builds"}
        </button>
        <div className="text-[11px] text-mist/70 self-center italic">
          Drafts go to your GM for approval before the Builder seeds.
        </div>
      </div>
    </div>
  );
}


function CodexImportPicker({ nodes, selected, onChange }) {
  const [open, setOpen] = useState(false);
  const toggle = (id) => onChange(selected.includes(id)
    ? selected.filter((x) => x !== id)
    : [...selected, id]);
  return (
    <div className="mt-4 border-t border-gold/10 pt-3"
         data-testid="forge-codex-picker">
      <button type="button" onClick={() => setOpen(!open)}
              className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-gold-bright hover:text-parchment"
              data-testid="forge-codex-toggle">
        <Library className="w-3 h-3"/>
        Import Codex Entities ({selected.length} selected)
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`}/>
      </button>
      {open && (
        <div className="mt-2 max-h-64 overflow-y-auto border border-gold/10 rounded-sm p-2 grid grid-cols-1 sm:grid-cols-2 gap-1">
          {nodes.map((n) => (
            <label key={n.id} className="flex items-start gap-2 text-[11px] cursor-pointer p-1 rounded-sm hover:bg-gold/5"
                   data-testid={`forge-codex-row-${n.id}`}>
              <input type="checkbox" checked={selected.includes(n.id)}
                     onChange={() => toggle(n.id)}
                     className="mt-0.5"/>
              <div className="min-w-0">
                <div className="text-parchment truncate">
                  <span className="text-gold/70 uppercase tracking-widest text-[9px] mr-1">
                    {n.node_kind || n.type}
                  </span>
                  {n.title}
                </div>
                {n.summary && (
                  <div className="text-mist/70 text-[10px] truncate italic">
                    {n.summary}
                  </div>
                )}
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}


function DraftsTab({ drafts, isGm, userId, campId, reload, nav }) {
  if (drafts.length === 0) {
    return (
      <div className="card-mystic p-6 text-center text-mist">
        No drafts yet. Forge one in the <span className="text-gold">Forge</span> tab.
      </div>
    );
  }
  return (
    <div className="space-y-3" data-testid="forge-drafts-list">
      {drafts.map((d) => (
        <DraftRow key={d.id} draft={d} isGm={isGm} userId={userId}
                  campId={campId} reload={reload} nav={nav}/>
      ))}
    </div>
  );
}


function DraftRow({ draft, isGm, userId, campId, reload, nav }) {
  const [open, setOpen] = useState(draft.status === "approved");
  const [notes, setNotes] = useState(draft.gm_notes || "");
  const isOwner = draft.requester_id === userId;
  const canCommit = draft.status === "approved" && isOwner;

  const review = async (status) => {
    try {
      await api.patch(`/campaigns/${campId}/concept-drafts/${draft.id}`,
                       { status, gm_notes: notes });
      await reload();
    } catch (_e) { /* ignore */ }
  };

  const commit = async (idx) => {
    try {
      const r = await api.post(`/campaigns/${campId}/concept-drafts/${draft.id}/commit`,
                                 { picked_index: idx });
      const picked = encodeURIComponent(JSON.stringify(r.data.picked || {}));
      nav(`/app/campaigns/${campId}/characters/new?from_draft=${draft.id}&seed=${picked}`);
    } catch (_e) { /* swallow */ }
  };

  const remove = async () => {
    if (!window.confirm("Delete this draft permanently?")) return;
    try {
      await api.delete(`/campaigns/${campId}/concept-drafts/${draft.id}`);
      await reload();
    } catch (_e) { /* swallow */ }
  };

  const statusColor = {
    pending:   "bg-arcane/20 text-arcane",
    approved:  "bg-gold/20 text-gold-bright",
    rejected:  "bg-ember/20 text-ember",
    committed: "bg-mist/20 text-parchment",
  }[draft.status] || "bg-mist/20 text-parchment";

  return (
    <div className="card-mystic p-4" data-testid={`forge-draft-${draft.id}`}>
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`tag ${statusColor} uppercase tracking-widest text-[9px]`}>
              {draft.status}
            </span>
            <span className="font-display text-parchment text-base">
              {draft.requester_name}
            </span>
            <span className="text-mist/60 text-[10px]">
              {draft.system_id} · {new Date(draft.created_at).toLocaleString()}
            </span>
          </div>
          <div className="text-sm text-parchment/80 mt-1 italic line-clamp-2">
            {(draft.brief?.role || draft.brief?.signature_traits || draft.concept_text || "(brief)").slice(0, 240)}
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <button type="button" onClick={() => setOpen(!open)} className="btn btn-ghost text-xs"
                  data-testid={`forge-draft-toggle-${draft.id}`}>
            {open ? "Hide" : "Show"} Builds
          </button>
          {(isOwner || isGm) && (
            <button type="button" onClick={remove}
                    className="btn btn-ghost text-xs text-ember"
                    data-testid={`forge-draft-delete-${draft.id}`}>
              <Trash2 className="w-3 h-3"/>
            </button>
          )}
        </div>
      </div>

      {open && (
        <>
          <div className="grid md:grid-cols-2 gap-3 mt-4">
            {(draft.candidates || []).map((c, idx) => (
              <CandidateCard key={idx} c={c} idx={idx}
                             canCommit={canCommit}
                             onCommit={() => commit(idx)}/>
            ))}
          </div>

          {(draft.gm_notes || isGm) && (
            <div className="mt-4 border-t border-gold/10 pt-3">
              <div className="label-ref mb-1">GM notes</div>
              {isGm && draft.status === "pending" ? (
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                          placeholder="Notes to the player…"
                          className="input min-h-[60px] text-sm"
                          data-testid={`forge-draft-notes-${draft.id}`}/>
              ) : (
                <div className="text-sm text-mist italic">
                  {draft.gm_notes || "(no notes)"}
                </div>
              )}
              {isGm && draft.status === "pending" && (
                <div className="mt-2 flex gap-2">
                  <button type="button" onClick={() => review("approved")}
                          className="btn btn-primary text-xs"
                          data-testid={`forge-draft-approve-${draft.id}`}>
                    <Check className="w-3 h-3"/> Approve
                  </button>
                  <button type="button" onClick={() => review("rejected")}
                          className="btn btn-ghost text-xs text-ember"
                          data-testid={`forge-draft-reject-${draft.id}`}>
                    <X className="w-3 h-3"/> Reject
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}


function CandidateCard({ c, idx, canCommit, onCommit }) {
  return (
    <div className="border border-gold/15 rounded-sm p-3 bg-void/40"
         data-testid={`forge-candidate-${idx}`}>
      <div className="flex items-baseline justify-between gap-2 flex-wrap">
        <div className="font-display text-gold-bright text-sm">
          Build {idx + 1} · {c.title || "(untitled)"}
        </div>
        {typeof c.estimated_cp === "number" && (
          <span className="text-[10px] font-ui text-gold/70 tracking-widest uppercase">
            ~{c.estimated_cp} CP
          </span>
        )}
      </div>
      {c.summary && <div className="text-[12px] text-parchment/80 mt-1">{c.summary}</div>}

      <div className="text-[11px] mt-2 space-y-1">
        {(c.race || c.class) && (
          <div className="text-parchment">
            {c.race && <><span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Race</span>{c.race}</>}
            {c.race && c.class && <span className="mx-1.5 text-mist/40">·</span>}
            {c.class && <><span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Class</span>{c.class}</>}
            {c.subclass && <span className="text-mist/70"> ({c.subclass})</span>}
          </div>
        )}
        {c.background && (
          <div className="text-parchment">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Background</span>{c.background}
          </div>
        )}
        {c.appearance && (
          <div className="text-parchment text-[11px]">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Appearance</span>{c.appearance}
          </div>
        )}
        {c.origin && (
          <div className="text-parchment text-[11px]">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Origin</span>{c.origin}
          </div>
        )}
        {c.stats && (
          <div className="text-parchment">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Stats</span>
            Body {c.stats.body} · Mind {c.stats.mind} · Soul {c.stats.soul}
          </div>
        )}
        {c.abilities && (
          <div className="text-parchment">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Abilities</span>
            {Object.entries(c.abilities).map(([k, v]) => `${k} ${v}`).join(" · ")}
          </div>
        )}
        <Section title="Attributes" rows={c.attributes} render={(a) => (
          <>— {a.name} <span className="text-mist/70">L{a.level}</span>
            {a.resistance_kind && a.resistance_kind !== "none" &&
              <span className="text-arcane/80"> · resist:{a.resistance_kind}</span>}
            {a.range_kind && a.range_kind !== "none" &&
              <span className="text-arcane/80"> · range:{a.range_kind}</span>}
            {a.note && <span className="text-mist/60"> · {a.note}</span>}
          </>
        )}/>
        <Section title="Power Packs" rows={c.power_packs} render={(p) => (
          <>— <span className="text-gold-bright">{p.name}</span>
            {p.total_cp ? <span className="text-mist/70"> · {p.total_cp} CP</span> : null}
            {(p.effects || []).length > 0 && <div className="ml-4 text-mist/80">{p.effects.join(" · ")}</div>}
            {p.defect && <div className="ml-4 text-ember/80">↳ defect: {p.defect}</div>}
            {p.narrative && <div className="ml-4 italic text-mist/70">{p.narrative}</div>}
          </>
        )}/>
        <Section title="Skills" rows={c.skills} render={(s) => (
          <>— {s.name} <span className="text-mist/70">L{s.level}</span></>
        )}/>
        <Section title="Defects" rows={c.defects} render={(d) => (
          <>— {d.name} <span className="text-mist/70">R{d.rank}</span>{d.note && <span className="text-mist/60"> · {d.note}</span>}</>
        )}/>
        <Section title="Items" rows={c.items} render={(it) => (
          <>— {it.name}{it.category && <span className="text-mist/70"> · {it.category}</span>}{it.note && <span className="text-mist/60"> · {it.note}</span>}</>
        )}/>
        <Section title="Weapons / Weapon-Items" rows={c.weapons} render={(w) => (
          <>— {w.name} <span className="text-mist/70">{w.class}</span>
            {typeof w.rank === "number" && <span className="text-mist/70"> · R{w.rank}</span>}
            {w.is_weapon_item && <span className="text-arcane/80"> · weapon-item (½ cost)</span>}
            {w.range_m && <span className="text-mist/70"> · {w.range_m}m</span>}
          </>
        )}/>
        {(c.feats || []).length > 0 && (
          <div className="text-parchment">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Feats</span>
            {c.feats.join(", ")}
          </div>
        )}
        {(c.goals || []).length > 0 && (
          <div className="text-parchment">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Goals</span>
            {c.goals.join(" · ")}
          </div>
        )}
        {(c.dreams || []).length > 0 && (
          <div className="text-parchment">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Dreams</span>
            {c.dreams.join(" · ")}
          </div>
        )}
        {c.personality_knots && (
          <div className="text-parchment text-[11px]">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Knots</span>{c.personality_knots}
          </div>
        )}
        {c.rationale && (
          <div className="text-mist italic mt-1.5 text-[11px]">{c.rationale}</div>
        )}
      </div>

      {canCommit && (
        <button type="button" onClick={onCommit}
                className="btn btn-primary text-xs mt-3 w-full"
                data-testid={`forge-candidate-commit-${idx}`}>
          <Send className="w-3 h-3"/> Pick This & Open Builder
        </button>
      )}
    </div>
  );
}


function Section({ title, rows, render }) {
  if (!rows || rows.length === 0) return null;
  return (
    <details className="mt-1">
      <summary className="cursor-pointer text-gold/60 uppercase tracking-widest text-[9px]">
        {title} ({rows.length})
      </summary>
      <ul className="mt-1 space-y-0.5">
        {rows.map((r, i) => (
          <li key={i} className="text-parchment leading-snug">
            {render(r)}
          </li>
        ))}
      </ul>
    </details>
  );
}
