/**
 * ConceptForge — V6.25.33
 *
 * Free-form concept → 2 mechanically-distinct build candidates via Claude.
 * Drafts go to GM approval queue. Once approved, the Player picks a
 * candidate and is taken to the Character Builder pre-filled from the
 * picked draft.
 *
 * Supports BESM 4E and Anime 5E only at launch (point-buy systems).
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, Loader2, Check, X, Send, Trash2, ChevronRight, ScrollText } from "lucide-react";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";

const SUPPORTED = new Set(["besm-4e", "anime-5e"]);

export default function ConceptForge() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [campaigns, setCampaigns] = useState([]);
  const [campId, setCampId] = useState("");
  const [camp, setCamp] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [concept, setConcept] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [activeTab, setActiveTab] = useState("forge"); // forge | drafts

  // Load campaigns the user is in / runs
  useEffect(() => {
    api.get("/campaigns").then((r) => {
      const list = (r.data || []).filter((c) => SUPPORTED.has(c.system_id));
      setCampaigns(list);
      if (list.length > 0 && !campId) setCampId(list[0].id);
    }).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const reload = useCallback(async () => {
    if (!campId) return;
    const [c, d] = await Promise.all([
      api.get(`/campaigns/${campId}`).then((r) => r.data).catch(() => null),
      api.get(`/campaigns/${campId}/concept-drafts`).then((r) => r.data).catch(() => ({ drafts: [] })),
    ]);
    setCamp(c);
    setDrafts(d.drafts || []);
  }, [campId]);

  useEffect(() => { reload(); }, [reload]);

  const submit = async () => {
    setErr("");
    if (concept.trim().length < 10) {
      setErr("Concept must be at least 10 characters — describe role, tone, signature traits.");
      return;
    }
    setLoading(true);
    try {
      await api.post(`/campaigns/${campId}/concept-drafts`, { concept_text: concept });
      setConcept("");
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
            Type a concept. The Loremaster returns two mechanically-distinct
            build candidates. The GM reviews, the Player picks, the Builder
            seeds. Supported on BESM 4E + Anime 5E.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select className="select" value={campId}
                  onChange={(e) => setCampId(e.target.value)}
                  data-testid="forge-campaign-select">
            {campaigns.length === 0 && <option value="">— no eligible campaigns —</option>}
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} · {c.system_id}
              </option>
            ))}
          </select>
        </div>
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

      {campId && (
        <>
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
            <ForgeTab camp={camp} concept={concept} setConcept={setConcept}
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


function ForgeTab({ camp, concept, setConcept, submit, loading, err }) {
  if (!camp) return <div className="text-mist">Loading campaign…</div>;
  return (
    <div className="card-mystic p-5" data-testid="forge-input-panel">
      <div className="label-ref mb-2">
        Campaign · <span className="text-parchment">{camp.name}</span> ·
        <span className="ml-1 text-gold/70">{camp.system_id}</span> · power level
        <span className="ml-1 text-gold/70">{camp.power_level}</span>
      </div>
      <label className="label-ref block mb-1">Character Concept</label>
      <textarea className="input min-h-[180px] font-body leading-relaxed"
                value={concept}
                placeholder="Describe the character. Role at the table, signature abilities, background, personality knots, any custom flavour. The more detail you supply, the more interesting the builds."
                onChange={(e) => setConcept(e.target.value)}
                data-testid="forge-concept-textarea"/>
      <div className="text-[10px] text-mist/70 mt-1">
        {concept.length} chars · min 10
      </div>

      {err && (
        <div className="mt-3 text-sm text-ember" data-testid="forge-error">
          {err}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={submit} disabled={loading || concept.trim().length < 10}
                className="btn btn-primary"
                data-testid="forge-submit-btn">
          {loading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Sparkles className="w-4 h-4"/>}
          {loading ? "Forging…" : "Forge Two Builds"}
        </button>
        <div className="text-[11px] text-mist/70 self-center italic">
          Drafts are saved to your Drafts queue. Your GM reviews before
          you commit to building.
        </div>
      </div>
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
    } catch (_e) { /* surfaced via toast in future */ }
  };

  const commit = async (idx) => {
    try {
      const r = await api.post(`/campaigns/${campId}/concept-drafts/${draft.id}/commit`,
                                 { picked_index: idx });
      // Pre-fill builder via query param.
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
            "{draft.concept_text}"
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
                    data-testid={`forge-draft-delete-${draft.id}`}
                    title="Delete this draft">
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
                          placeholder="Notes to the player (visible regardless of approve/reject)…"
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
        {(c.attributes || []).length > 0 && (
          <details className="mt-1">
            <summary className="cursor-pointer text-gold/60 uppercase tracking-widest text-[9px]">
              Attributes ({c.attributes.length})
            </summary>
            <ul className="mt-1 space-y-0.5">
              {c.attributes.map((a, i) => (
                <li key={i} className="text-parchment leading-snug">
                  — {a.name} <span className="text-mist/70">L{a.level}</span>
                  {a.note && <span className="text-mist/60"> · {a.note}</span>}
                </li>
              ))}
            </ul>
          </details>
        )}
        {(c.point_buy_attributes || []).length > 0 && (
          <details className="mt-1">
            <summary className="cursor-pointer text-gold/60 uppercase tracking-widest text-[9px]">
              Point-buy ({c.point_buy_attributes.length})
            </summary>
            <ul className="mt-1 space-y-0.5">
              {c.point_buy_attributes.map((a, i) => (
                <li key={i} className="text-parchment leading-snug">
                  — {a.name} <span className="text-mist/70">L{a.level}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
        {(c.skills || []).length > 0 && (
          <details className="mt-1">
            <summary className="cursor-pointer text-gold/60 uppercase tracking-widest text-[9px]">
              Skills ({c.skills.length})
            </summary>
            <ul className="mt-1 space-y-0.5">
              {c.skills.map((s, i) => (
                <li key={i} className="text-parchment leading-snug">
                  — {s.name} <span className="text-mist/70">L{s.level}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
        {(c.defects || []).length > 0 && (
          <details className="mt-1">
            <summary className="cursor-pointer text-gold/60 uppercase tracking-widest text-[9px]">
              Defects ({c.defects.length})
            </summary>
            <ul className="mt-1 space-y-0.5">
              {c.defects.map((d, i) => (
                <li key={i} className="text-parchment leading-snug">
                  — {d.name} <span className="text-mist/70">R{d.rank}</span>
                  {d.note && <span className="text-mist/60"> · {d.note}</span>}
                </li>
              ))}
            </ul>
          </details>
        )}
        {(c.feats || []).length > 0 && (
          <div className="text-parchment">
            <span className="text-gold/60 uppercase tracking-widest text-[9px] mr-1">Feats</span>
            {c.feats.join(", ")}
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
