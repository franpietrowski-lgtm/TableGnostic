import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, X, AlertTriangle, CheckCircle2, Save, Layers, ListTree, ScrollText, FileDown } from "lucide-react";
import IngestPanel from "./IngestPanel";
import XPApprovalQueue from "./XPApprovalQueue";
import MaterialsApprovalQueue from "./MaterialsApprovalQueue";
import EpicCampaignPanel from "./EpicCampaignPanel";
import ReferenceEditor from "./ReferenceEditor";
import TimelinePanel from "./TimelinePanel";
import AtelierWorkshop from "./AtelierWorkshop";
import WorldCreationTree from "./WorldCreationTree";
import GenesisArchivePanel from "./GenesisArchivePanel";

/**
 * AtelierTab — V4.4 dynamic-scaling tiers.
 *
 * Three tiers stacked from concrete → abstract:
 *   1. Session 0 questionnaire (table contract, lines/veils, safety)
 *   2. Arcs (~3-session spans, beats: hook → rising → turn → echo)
 *   3. Master Plot (read-only mirror of genesis.master_acts) + continuity check
 *
 * GM-only. Player visibility is enforced server-side: a /api/atelier/{cid}
 * GET as a non-GM returns only the safety tools + table contract slice.
 */
export default function AtelierTab({ campId, camp }) {
  const [state, setState] = useState(null);
  const [genesis, setGenesis] = useState(null);
  const [findings, setFindings] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  // V6.8 — sub-tab nav. Genesis | Epic | Timeline | References live as
  // discrete sub-surfaces; Workshop is the original Session-0 / Arcs /
  // continuity-check toolset.
  const [subtab, setSubtab] = useState(() => {
    try {
      const u = new URL(window.location.href);
      return u.searchParams.get("atelier") || "workshop";
    } catch { return "workshop"; }
  });

  useEffect(() => {
    (async () => {
      try {
        const [a, g] = await Promise.all([
          api.get(`/atelier/${campId}`).then((r) => r.data),
          api.get(`/campaigns/${campId}/genesis`).then((r) => r.data).catch(() => null),
        ]);
        setState(a);
        setGenesis(g);
        setFindings(a.continuity_findings || []);
      } catch (e) {
        setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
      }
    })();
  }, [campId]);

  const saveAll = async () => {
    setBusy(true); setErr("");
    try {
      const { data } = await api.put(`/atelier/${campId}`, {
        session_zero: state.session_zero,
        arcs: state.arcs || [],
      });
      setState(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  const runContinuity = async () => {
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/atelier/${campId}/continuity`);
      setFindings(data.findings);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  const setSZ = (patch) => setState((s) => ({ ...s, session_zero: { ...s.session_zero, ...patch } }));

  const addArc = () => {
    const next = [...(state.arcs || []), {
      title: `Arc ${(state.arcs || []).length + 1}`,
      sequence: (state.arcs || []).length + 1,
      summary: "",
      expected_sessions: 3,
      status: "draft",
      beats: [],
      referenced_npcs: [],
      referenced_locations: [],
    }];
    setState((s) => ({ ...s, arcs: next }));
  };
  const updateArc = (i, patch) => {
    const arcs = [...state.arcs];
    arcs[i] = { ...arcs[i], ...patch };
    setState((s) => ({ ...s, arcs }));
  };
  const removeArc = (i) => {
    if (!window.confirm(`Remove ${state.arcs[i]?.title}?`)) return;
    const arcs = [...state.arcs];
    arcs.splice(i, 1);
    setState((s) => ({ ...s, arcs }));
  };
  const addBeat = (i) => {
    const arcs = [...state.arcs];
    arcs[i] = { ...arcs[i], beats: [...(arcs[i].beats || []), { title: "", kind: "rising", note: "", completed: false }] };
    setState((s) => ({ ...s, arcs }));
  };
  const updateBeat = (i, j, patch) => {
    const arcs = [...state.arcs];
    const beats = [...arcs[i].beats];
    beats[j] = { ...beats[j], ...patch };
    arcs[i] = { ...arcs[i], beats };
    setState((s) => ({ ...s, arcs }));
  };
  const removeBeat = (i, j) => {
    const arcs = [...state.arcs];
    const beats = [...arcs[i].beats];
    beats.splice(j, 1);
    arcs[i] = { ...arcs[i], beats };
    setState((s) => ({ ...s, arcs }));
  };

  if (err) return <div className="text-ember">{err}</div>;
  if (!state) return <div className="text-mist italic">Summoning the Atelier…</div>;

  return (
    <div className="space-y-6" data-testid="atelier-tab">
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div>
          <div className="label-ref">Atelier · Dynamic Scaling Tiers</div>
          <h2 className="font-display text-2xl text-parchment mt-1">Session 0 → Arcs → Master Plot</h2>
          <div className="text-[11px] font-ui text-mist/70 italic mt-1">
            Build the table contract first, plan arcs in 3-session sweeps, then check
            continuity against the campaign spine. Sclanders / Crawford framework + BESM 4E p.232.
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={runContinuity} disabled={busy}
                  className="btn btn-ghost text-xs" data-testid="atelier-continuity-btn">
            <AlertTriangle className="w-3 h-3"/> Continuity check
          </button>
          <ExportPdfBtn campId={campId}/>
          <button onClick={saveAll} disabled={busy}
                  className="btn btn-primary text-xs" data-testid="atelier-save-btn">
            <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {/* V6.8 — Sub-tab strip. Genesis / Epic / Timeline / References /
          Workshop are now distinct authoring surfaces. */}
      <div className="flex flex-wrap gap-1 border-b border-gold/15 pb-2"
           data-testid="atelier-subtabs">
        {[
          ["workshop",   "Workshop"],
          ["table-tools","Table Tools"],
          ["worldbuild", "World Tree"],
          ["genesis",    "Genesis (7 Phases)"],
          ["epic",       "Epic Campaign"],
          ["timeline",   "Timeline"],
          ["references", "References"],
        ].map(([k, label]) => (
          <button key={k} onClick={() => setSubtab(k)}
                  className={`text-[11px] px-3 py-1.5 rounded-sm font-ui uppercase tracking-widest transition-colors ${subtab === k ? "bg-gold/15 text-gold-bright border border-gold/30" : "text-mist hover:bg-gold/5"}`}
                  data-testid={`atelier-subtab-${k}`}>
            {label}
          </button>
        ))}
      </div>

      {subtab === "genesis" && (
        <div data-testid="atelier-genesis-pane">
          <div className="card-mystic p-5">
            <div className="label-ref">7-Phase Master Plot · independently navigable</div>
            <div className="text-[11px] text-mist italic mt-1 mb-3">
              The full 7-phase plot designer lives on its own deep-link page so each phase has a stable URL. Open it in a new tab if you want to author plot beats while keeping this Atelier surface in view.
            </div>
            <Link to={`/app/campaigns/${campId}/genesis`} className="btn btn-primary text-xs"
                  data-testid="atelier-open-genesis">
              Open Genesis (7 phases) →
            </Link>
          </div>
          {/* V6.25.8 — Archive of past Genesis snapshots, GM-only. */}
          <GenesisArchivePanel campId={campId} isGm={!!camp?.is_gm}/>
        </div>
      )}

      {subtab === "epic" && (
        <div data-testid="atelier-epic-pane">
          <EpicCampaignPanel campId={campId}/>
        </div>
      )}

      {subtab === "timeline" && (
        <div data-testid="atelier-timeline-pane">
          <TimelinePanel campId={campId} systemId={camp?.system_id} isGm={camp?.is_gm}/>
        </div>
      )}

      {subtab === "references" && (
        <div data-testid="atelier-references-pane">
          <ReferenceEditor campaignId={campId} systemId={camp?.system_id}
                            isGm={camp?.is_gm}/>
        </div>
      )}

      {subtab === "table-tools" && (
        <div data-testid="atelier-table-tools-pane">
          <AtelierWorkshop campId={campId}/>
        </div>
      )}

      {subtab === "worldbuild" && (
        <div data-testid="atelier-worldbuild-pane">
          <WorldCreationTree campId={campId} isGm={!!camp?.is_gm}/>
        </div>
      )}

      {subtab === "workshop" && (<>
      {/* ---------- Knowledge Web ingestion ---------- */}
      <IngestPanel campId={campId}/>

      {/* ---------- XP Approval Queue (GM-side) ---------- */}
      <XPApprovalQueue campaignId={campId} isGm/>

      {/* ---------- Materials / Byproduct / Craft Output Approval (GM-side) ---------- */}
      <MaterialsApprovalQueue campaignId={campId} isGm={!!camp?.is_gm}/>

      <div className="text-[11px] text-mist/60 italic px-1" data-testid="atelier-ref-moved-note">
        Looking for the campaign Reference tables and the GM Quickstart instructions?
        Switch to the <button onClick={() => setSubtab("references")} className="text-gold-bright underline">References</button> sub-tab above, or open <Link to={`/app/campaigns/${campId}/genesis`} className="text-gold-bright underline">Genesis</Link> for the full 7-phase plot designer.
      </div>

      {/* ---------- Session 0 ---------- */}
      <SessionZeroPanel sz={state.session_zero || {}} setSZ={setSZ}/>

      {/* ---------- Arcs ---------- */}
      <div className="card-mystic p-5" data-testid="atelier-arcs">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="label-ref flex items-center gap-2"><Layers className="w-3 h-3"/> Arcs</div>
            <div className="text-[10px] text-mist/70 italic">Each arc ~3 sessions: HOOK · RISING · TURN · ECHO.</div>
          </div>
          <button onClick={addArc} className="btn btn-ghost text-xs" data-testid="atelier-add-arc">
            <Plus className="w-3 h-3"/> Arc
          </button>
        </div>
        {(state.arcs || []).length === 0 && <div className="text-mist italic font-body text-xs">No arcs drafted yet.</div>}
        <div className="space-y-3">
          {(state.arcs || []).map((arc, i) => (
            <ArcRow key={i} arc={arc} idx={i}
                    onUpdate={(p) => updateArc(i, p)}
                    onRemove={() => removeArc(i)}
                    onAddBeat={() => addBeat(i)}
                    onUpdateBeat={(j, p) => updateBeat(i, j, p)}
                    onRemoveBeat={(j) => removeBeat(i, j)}/>
          ))}
        </div>
      </div>

      {/* ---------- Master Plot mirror ---------- */}
      <div className="card-mystic p-5" data-testid="atelier-master-plot">
        <div className="flex items-baseline justify-between mb-3">
          <div>
            <div className="label-ref flex items-center gap-2"><ScrollText className="w-3 h-3"/> Master Plot</div>
            <div className="text-[10px] text-mist/70 italic">
              Read-only mirror of the Genesis master_acts. Edit on the Sessions tab → Atelier/Genesis pre-fill.
            </div>
          </div>
          {genesis && genesis.master_acts && (
            <div className="text-[10px] text-gold/70 font-ui">{(genesis.master_acts || []).length} acts</div>
          )}
        </div>
        {(!genesis || !genesis.master_acts || genesis.master_acts.length === 0) && (
          <div className="text-mist italic font-body text-xs">No master acts in Genesis yet.</div>
        )}
        <div className="space-y-2">
          {(genesis?.master_acts || []).map((a, i) => (
            <div key={i} className="border border-gold/15 rounded-sm p-3" data-testid={`atelier-act-${i}`}>
              <div className="text-sm font-ui text-parchment">{a.title}</div>
              {a.beat && (
                <div className="text-[12px] text-parchment/85 italic mt-1 font-body leading-snug">{a.beat}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ---------- Continuity findings ---------- */}
      {findings.length > 0 && (
        <div className="card-mystic p-5" data-testid="atelier-findings">
          <div className="label-ref flex items-center gap-2 mb-3"><AlertTriangle className="w-3 h-3"/> Continuity findings · {findings.length}</div>
          <ul className="space-y-2">
            {findings.map((f) => (
              <li key={f.id}
                  className={`border rounded-sm p-3 ${f.severity === "warning" ? "border-ember/40" : "border-arcane/40"}`}
                  data-testid={`atelier-finding-${f.id}`}>
                <div className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
                  {f.kind} · {f.severity}
                </div>
                <div className="text-sm text-parchment mt-1">{f.message}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
      {findings.length === 0 && state.continuity_checked_at && (
        <div className="text-[11px] text-arcane-light font-ui italic" data-testid="atelier-no-findings">
          <CheckCircle2 className="w-3 h-3 inline -mt-0.5"/> No continuity issues found.
        </div>
      )}
      </>)}
    </div>
  );
}

function SessionZeroPanel({ sz, setSZ }) {
  const sl = (k) => Array.isArray(sz[k]) ? sz[k] : [];
  const setList = (k, v) => setSZ({ [k]: v });
  return (
    <div className="card-mystic p-5" data-testid="atelier-session-zero">
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <div className="label-ref flex items-center gap-2"><ListTree className="w-3 h-3"/> Session 0 · Table Contract</div>
          <div className="text-[10px] text-mist/70 italic">
            What the table agrees to before play. Lines = hard "no". Veils = off-screen.
          </div>
        </div>
        <label className="flex items-center gap-2 text-[10px] font-ui uppercase tracking-widest text-gold/70">
          <input type="checkbox" checked={!!sz.completed}
                 onChange={(e) => setSZ({ completed: e.target.checked })}
                 data-testid="atelier-sz-completed"/>
          Session 0 complete
        </label>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <div>
          <label className="label-ref block mb-1">Table contract</label>
          <textarea className="input min-h-[80px]" value={sz.table_contract || ""}
                    onChange={(e) => setSZ({ table_contract: e.target.value })}
                    placeholder="The agreement we play under — show up, communicate, no surprises."
                    data-testid="atelier-sz-contract"/>
        </div>
        <div>
          <label className="label-ref block mb-1">Schedule</label>
          <input className="input" value={sz.schedule || ""}
                 onChange={(e) => setSZ({ schedule: e.target.value })}
                 placeholder="Wednesdays 7-10pm CST"
                 data-testid="atelier-sz-schedule"/>
          <label className="label-ref block mb-1 mt-3">Expectations · tone & lethality</label>
          <textarea className="input min-h-[60px]" value={sz.expectations || ""}
                    onChange={(e) => setSZ({ expectations: e.target.value })}
                    placeholder="Tone: heroic with consequences. PCs can die at climactic moments only."
                    data-testid="atelier-sz-expectations"/>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-3 mt-3">
        <ChipList label="Lines · hard 'no'" items={sl("lines")} setItems={(v) => setList("lines", v)}
                  placeholder="topic we will not play with" testid="atelier-sz-lines"/>
        <ChipList label="Veils · off-screen" items={sl("veils")} setItems={(v) => setList("veils", v)}
                  placeholder="topic we play around, not through" testid="atelier-sz-veils"/>
      </div>
      <div className="grid md:grid-cols-2 gap-3 mt-3">
        <ChipList label="Safety tools" items={sl("safety_tools")} setItems={(v) => setList("safety_tools", v)}
                  placeholder="X-card, open door, lines & veils, script change" testid="atelier-sz-safety"/>
        <ChipList label="Recurring themes" items={sl("recurring_themes")} setItems={(v) => setList("recurring_themes", v)}
                  placeholder="grief · craft · belonging" testid="atelier-sz-themes"/>
      </div>
      <div className="mt-3">
        <label className="label-ref block mb-1">Character integration</label>
        <textarea className="input min-h-[60px]" value={sz.character_integration || ""}
                  onChange={(e) => setSZ({ character_integration: e.target.value })}
                  placeholder="How the PCs already know each other. Why they leave together."
                  data-testid="atelier-sz-integration"/>
      </div>
    </div>
  );
}

function ArcRow({ arc, idx, onUpdate, onRemove, onAddBeat, onUpdateBeat, onRemoveBeat }) {
  const beats = arc.beats || [];
  return (
    <div className="border border-gold/15 rounded-sm p-3" data-testid={`atelier-arc-${idx}`}>
      <div className="grid md:grid-cols-[1fr_140px_140px_auto] gap-2 items-center">
        <input className="input" value={arc.title || ""}
               onChange={(e) => onUpdate({ title: e.target.value })}
               placeholder="Arc title" data-testid={`atelier-arc-${idx}-title`}/>
        <select className="select" value={arc.status || "draft"}
                onChange={(e) => onUpdate({ status: e.target.value })}
                data-testid={`atelier-arc-${idx}-status`}>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="complete">Complete</option>
          <option value="shelved">Shelved</option>
        </select>
        <input type="number" min={1} max={10} className="input text-center"
               value={arc.expected_sessions || 3}
               onChange={(e) => onUpdate({ expected_sessions: +e.target.value })}
               title="Expected sessions"
               data-testid={`atelier-arc-${idx}-sessions`}/>
        <button onClick={onRemove} className="text-ember/70 hover:text-ember"
                data-testid={`atelier-arc-${idx}-remove`}><X className="w-4 h-4"/></button>
      </div>
      <textarea className="input mt-2" value={arc.summary || ""}
                onChange={(e) => onUpdate({ summary: e.target.value })}
                placeholder="One paragraph: what this arc puts the table through."
                data-testid={`atelier-arc-${idx}-summary`}/>

      <div className="grid md:grid-cols-2 gap-2 mt-2">
        <ChipList label="Referenced NPCs" items={arc.referenced_npcs || []}
                  setItems={(v) => onUpdate({ referenced_npcs: v })}
                  placeholder="Codex node title" testid={`atelier-arc-${idx}-npcs`} compact/>
        <ChipList label="Referenced locations" items={arc.referenced_locations || []}
                  setItems={(v) => onUpdate({ referenced_locations: v })}
                  placeholder="Codex node title" testid={`atelier-arc-${idx}-locs`} compact/>
      </div>

      <div className="mt-3 border-t border-gold/10 pt-2">
        <div className="flex items-center justify-between mb-1.5">
          <div className="label-ref">Beats · {beats.length}</div>
          <button onClick={onAddBeat} className="btn btn-ghost text-[10px]"
                  data-testid={`atelier-arc-${idx}-add-beat`}>
            <Plus className="w-3 h-3"/> Beat
          </button>
        </div>
        {beats.map((b, j) => (
          <div key={j} className="grid md:grid-cols-[110px_1fr_2fr_auto] gap-2 items-center mb-1.5"
               data-testid={`atelier-arc-${idx}-beat-${j}`}>
            <select className="select select-sm" value={b.kind || "rising"}
                    onChange={(e) => onUpdateBeat(j, { kind: e.target.value })}>
              <option value="hook">Hook</option>
              <option value="rising">Rising</option>
              <option value="turn">Turn</option>
              <option value="echo">Echo</option>
              <option value="denouement">Denouement</option>
            </select>
            <input className="input" value={b.title || ""}
                   onChange={(e) => onUpdateBeat(j, { title: e.target.value })}
                   placeholder="Beat title"/>
            <input className="input" value={b.note || ""}
                   onChange={(e) => onUpdateBeat(j, { note: e.target.value })}
                   placeholder="One line. What changes for the table?"/>
            <button onClick={() => onRemoveBeat(j)} className="text-ember/70"><X className="w-3 h-3"/></button>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChipList({ label, items, setItems, placeholder, testid, compact }) {
  const [v, setV] = useState("");
  const add = () => { const t = v.trim(); if (!t) return; setItems([...(items || []), t]); setV(""); };
  return (
    <div>
      <div className="label-ref mb-1">{label}</div>
      <div className="flex flex-wrap gap-1 mb-1.5">
        {(items || []).map((it, i) => (
          <span key={i} className="tag">
            {it}
            <button className="ml-1" onClick={() => setItems(items.filter((_, j) => j !== i))}>
              <X className="w-3 h-3 inline"/>
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input className={`input ${compact ? "text-xs" : ""}`} placeholder={placeholder} value={v}
               onChange={(e) => setV(e.target.value)}
               onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
               data-testid={testid}/>
        <button onClick={add} type="button" className="btn btn-ghost"><Plus className="w-3 h-3"/></button>
      </div>
    </div>
  );
}

/** ExportPdfBtn — downloads a system-branded PDF chronicle.
 *  Uses fetch with the bearer token because <a download> can't carry headers.
 *  Inline byline editor — the cover page credits the GM by name, so we make
 *  setting the byline a one-click affordance right where the export lives. */
function ExportPdfBtn({ campId }) {
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const [byline, setByline] = useState("");
  const [me, setMe] = useState(null);
  const [savedTick, setSavedTick] = useState(false);
  const [mode, setMode] = useState("campaign");  // "campaign" | "narrative"

  React.useEffect(() => {
    if (!open) return;
    api.get("/auth/me").then(({ data }) => {
      setMe(data);
      setByline(data.byline_name || data.name || "");
    }).catch(() => {});
  }, [open]);

  const saveByline = async () => {
    try {
      const { data } = await api.patch("/auth/me", { byline_name: byline });
      setMe(data);
      setSavedTick(true);
      setTimeout(() => setSavedTick(false), 1500);
    } catch (e) {
      window.alert("Could not save byline: " + (e.response?.data?.detail || e.message));
    }
  };

  const [gateMsg, setGateMsg] = useState("");

  const download = async () => {
    setBusy(true); setGateMsg("");
    try {
      const token = localStorage.getItem("tg_token");
      const apiBase = process.env.REACT_APP_BACKEND_URL || "";
      const r = await fetch(`${apiBase}/api/campaigns/${campId}/export.pdf?mode=${encodeURIComponent(mode)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) {
        let detail = "";
        try {
          const j = await r.json();
          detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
        } catch {
          detail = await r.text();
        }
        if (r.status === 451) {
          setGateMsg(detail);
          setBusy(false);
          return;
        }
        throw new Error(detail || `HTTP ${r.status}`);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = mode === "narrative" ? "narrative-chronicle.pdf" : "chronicle.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setOpen(false);
    } catch (e) {
      window.alert("PDF export failed: " + e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} disabled={busy}
              className="btn btn-ghost text-xs" data-testid="atelier-export-pdf-btn"
              title="Download a DriveThruRPG-ready, system-branded PDF chronicle.">
        <FileDown className="w-3 h-3"/> {busy ? "Rendering…" : "Export PDF"}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 z-30 card-mystic p-4 w-[320px] shadow-xl"
             data-testid="atelier-export-pdf-popover">
          <div className="label-ref mb-2">PDF cover byline</div>
          <div className="text-[10px] text-mist/70 italic mb-2">
            Your full name will appear on the cover and page footers as
            "by ___ · Weaved in TableGnostic". Stored on your profile so
            every export uses the same byline.
          </div>
          <input className="input text-sm mb-2"
                 value={byline}
                 onChange={(e) => setByline(e.target.value)}
                 placeholder="First Last"
                 data-testid="atelier-export-byline-input"/>
          <div className="flex items-center justify-between gap-2 mb-3">
            <button onClick={saveByline} className="btn btn-ghost text-xs"
                    data-testid="atelier-export-byline-save">
              {savedTick ? "Saved ✓" : "Save byline"}
            </button>
            <span className="text-[10px] text-mist/60 font-ui">{me?.email || ""}</span>
          </div>
          <button onClick={download} disabled={busy}
                  className="btn btn-primary text-xs w-full"
                  data-testid="atelier-export-pdf-download">
            <FileDown className="w-3 h-3"/> {busy ? "Rendering…" : "Download chronicle"}
          </button>

          {/* Mode toggle — branded vs narrative-only. Narrative bypasses the
              forbidden-setting gate because it's not a sellable supplement;
              just a story export. */}
          <div className="border-t border-gold/10 mt-3 pt-3" data-testid="export-mode-toggle">
            <div className="label-ref mb-1.5">Output mode</div>
            <div className="flex gap-1">
              <button onClick={() => setMode("campaign")}
                      className={`flex-1 px-2 py-1 text-[10px] font-ui uppercase tracking-widest border ${
                        mode === "campaign" ? "border-gold text-gold-bright bg-gold/10" : "border-gold/20 text-mist hover:border-gold/40"
                      }`}
                      data-testid="export-mode-campaign">
                Campaign · branded
              </button>
              <button onClick={() => setMode("narrative")}
                      className={`flex-1 px-2 py-1 text-[10px] font-ui uppercase tracking-widest border ${
                        mode === "narrative" ? "border-gold text-gold-bright bg-gold/10" : "border-gold/20 text-mist hover:border-gold/40"
                      }`}
                      data-testid="export-mode-narrative">
                Narrative · story
              </button>
            </div>
            <div className="text-[10px] text-mist/70 italic mt-1.5 leading-snug">
              {mode === "narrative"
                ? "Pure-prose chronicle — no system trade dress. Bypasses Cypher / OGL setting gates because it's not a sellable supplement."
                : "Branded supplement-style — system trade dress + style profile applied. Subject to per-licence setting gates."}
            </div>
          </div>
          {gateMsg && (
            <div className="mt-3 border border-ember/40 bg-ember/10 rounded-sm p-3 text-[11px] text-ember whitespace-pre-wrap font-body leading-snug"
                 data-testid="atelier-export-licence-gate">
              {gateMsg}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
