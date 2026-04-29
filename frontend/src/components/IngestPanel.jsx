import React, { useEffect, useRef, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Upload, FileText, Trash2, Check, X, Sparkles, BookOpen, Filter } from "lucide-react";

/**
 * IngestPanel — V4.4 Phase C.
 *
 * Knowledge Web mechanic-aware ingestion. GM uploads PDF/MD/TXT/RTF/DOCX,
 * Claude Sonnet returns categorized suggestions across:
 *   attribute · power_pack · power_bundle · item · weapon · skill ·
 *   npc · location · lore · quest
 * each tagged with an atelier_phase (1-7) and optional target_arc.
 *
 * Review UX (per user choice 'c'): categorized tabs with a master
 * "Accept all reviewed" button. Each suggestion has an inline checkbox
 * — toggling marks it for the next batched accept.
 */
const KIND_LABELS = {
  attribute: "Attributes",
  power_pack: "Power Packs",
  power_bundle: "Power Bundles",
  item: "Items",
  weapon: "Weapons",
  skill: "Skills",
  npc: "NPCs",
  location: "Locations",
  lore: "Lore",
  quest: "Quests",
};
const KIND_ORDER = ["attribute", "power_pack", "power_bundle", "item", "weapon",
                     "skill", "npc", "location", "lore", "quest"];

export default function IngestPanel({ campId }) {
  const [list, setList] = useState([]);
  const [open, setOpen] = useState(null);  // currently-open ingest doc
  const [tab, setTab] = useState("all");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [marked, setMarked] = useState({});  // {idx: true}
  const fileRef = useRef(null);
  const scaffoldFileRef = useRef(null);
  const [scaffoldPreview, setScaffoldPreview] = useState(null);
  const [scaffoldBusy, setScaffoldBusy] = useState(false);

  const refresh = async () => {
    try {
      const { data } = await api.get(`/campaigns/${campId}/ingestions`);
      setList(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  useEffect(() => { refresh(); }, [campId]);

  const upload = async (file) => {
    if (!file) return;
    if (file.size > 24 * 1024 * 1024) {
      setErr("File exceeds 24 MB cap.");
      return;
    }
    setBusy(true); setErr("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post(`/campaigns/${campId}/ingest`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setOpen(data);
      setMarked({});
      setTab("all");
      await refresh();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  // ─── One-Shot Scaffold ───
  // Uploads a published one-shot adventure / module → Claude returns
  // a full deploy-ready blob (codex nodes, NPCs, opening encounter).
  // commit=false returns a preview; commit=true writes nodes + an
  // encounter draft on the campaign's Director's doc.
  const scaffoldOneShot = async (file, commit) => {
    if (!file) return;
    if (file.size > 24 * 1024 * 1024) {
      setErr("File exceeds 24 MB cap.");
      return;
    }
    setScaffoldBusy(true); setErr("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post(
        `/campaigns/${campId}/scaffold-oneshot?commit=${commit ? "true" : "false"}`,
        fd, { headers: { "Content-Type": "multipart/form-data" } }
      );
      setScaffoldPreview({ commit, data, filename: file.name });
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setScaffoldBusy(false);
    }
  };

  const acceptMarked = async () => {
    if (!open) return;
    const indices = Object.keys(marked).filter((k) => marked[k]).map(Number);
    if (indices.length === 0) return;
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/ingestions/${open.id}/accept`, {
        accepted_indices: indices, overrides: {},
      });
      // Re-fetch the ingest doc to refresh accepted flags.
      const refreshed = await api.get(`/ingestions/${open.id}`).then((r) => r.data);
      setOpen(refreshed);
      setMarked({});
      await refresh();
      // Best-effort toast.
      window.alert(`Accepted ${data.accepted.length} suggestions. ${data.remaining} remain.`);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this ingestion record? Already-accepted items remain.")) return;
    await api.delete(`/ingestions/${id}`);
    if (open?.id === id) setOpen(null);
    await refresh();
  };

  const sugs = open?.suggestions || [];
  const filtered = tab === "all" ? sugs : sugs.filter((s) => s.kind === tab);

  return (
    <div className="space-y-4" data-testid="ingest-panel">
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div>
          <div className="label-ref flex items-center gap-2"><Sparkles className="w-3 h-3"/> Knowledge Web · Mechanic Ingestion</div>
          <div className="text-[11px] text-mist/70 italic mt-1">
            Drop a rulebook excerpt / setting bible / quest brief.
            Claude Sonnet returns categorized mechanic-aware suggestions —
            never reproducing rulebook prose. PDF · MD · TXT · RTF · DOCX (≤ 24 MB).
          </div>
        </div>
        <div>
          <input ref={fileRef} type="file" className="hidden"
                 accept=".pdf,.md,.txt,.rtf,.docx,application/pdf,text/markdown,text/plain,application/rtf,text/rtf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                 onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }}
                 data-testid="ingest-file-input"/>
          <button onClick={() => fileRef.current?.click()} disabled={busy}
                  className="btn btn-primary text-xs" data-testid="ingest-upload-btn">
            <Upload className="w-3 h-3"/> {busy ? "Ingesting…" : "Upload & Ingest"}
          </button>
        </div>
      </div>

      {err && <div className="text-ember text-xs" data-testid="ingest-err">{err}</div>}

      {/* One-Shot Scaffold — flagship feature: drop a published one-shot
          adventure / GM module, get a deploy-ready campaign skeleton in
          one Claude pass: codex nodes, NPCs, opening encounter. Two-stage
          flow — Preview, then Commit. */}
      <div className="card-mystic p-4" data-testid="scaffold-panel">
        <div className="flex items-baseline justify-between flex-wrap gap-3">
          <div>
            <div className="label-ref flex items-center gap-2">
              <Sparkles className="w-3 h-3"/> One-Shot Scaffold · 60-second campaign deploy
            </div>
            <div className="text-[11px] text-mist/70 italic mt-1 max-w-2xl">
              Drop a published one-shot adventure or GM module — Claude returns a
              ready-to-run skeleton: opening session beats, 5-30 Codex nodes,
              up to 12 NPCs with stat hints, and a staged opening encounter on the
              Director's Console. Preview first, then Commit. PDF · MD · TXT · RTF · DOCX.
            </div>
          </div>
          <div className="flex gap-2">
            <input ref={scaffoldFileRef} type="file" className="hidden"
                   accept=".pdf,.md,.txt,.rtf,.docx,application/pdf,text/markdown,text/plain,application/rtf,text/rtf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                   onChange={(e) => { scaffoldOneShot(e.target.files?.[0], false); e.target.value = ""; }}
                   data-testid="scaffold-file-input"/>
            <button onClick={() => scaffoldFileRef.current?.click()} disabled={scaffoldBusy}
                    className="btn btn-ghost text-xs" data-testid="scaffold-preview-btn">
              <Upload className="w-3 h-3"/> {scaffoldBusy ? "Scaffolding…" : "Preview a one-shot"}
            </button>
          </div>
        </div>
        {scaffoldPreview && (
          <div className="border border-gold/15 rounded-sm p-3 mt-3 text-[12px]" data-testid="scaffold-preview">
            {scaffoldPreview.commit ? (
              <>
                <div className="text-gold-bright font-display text-base">
                  ✓ Scaffold deployed for "{scaffoldPreview.filename}"
                </div>
                <div className="mt-1.5 text-mist">
                  {scaffoldPreview.data.nodes_created} Codex nodes ·
                  {" "}{scaffoldPreview.data.npcs_created} NPCs ·
                  {scaffoldPreview.data.encounter_staged ? " 1 encounter staged on Director" : " no encounter staged"}
                </div>
                {scaffoldPreview.data.title_suggestion && (
                  <div className="mt-1 text-parchment italic">Suggested title: {scaffoldPreview.data.title_suggestion}</div>
                )}
                <button onClick={() => setScaffoldPreview(null)}
                        className="btn btn-ghost text-[10px] mt-2"
                        data-testid="scaffold-clear-btn">Clear</button>
              </>
            ) : (
              <>
                <div className="text-parchment font-display">{scaffoldPreview.data.preview.title_suggestion || scaffoldPreview.filename}</div>
                <div className="text-mist mt-1 italic">{scaffoldPreview.data.preview.premise}</div>
                <div className="grid sm:grid-cols-3 gap-3 mt-3">
                  <PreviewBlock title={`Codex nodes · ${scaffoldPreview.data.preview.codex_nodes?.length || 0}`}
                                items={(scaffoldPreview.data.preview.codex_nodes || []).slice(0, 8).map((n) => `${n.type} · ${n.title}`)}/>
                  <PreviewBlock title={`NPCs · ${scaffoldPreview.data.preview.npcs?.length || 0}`}
                                items={(scaffoldPreview.data.preview.npcs || []).slice(0, 8).map((n) => `${n.role} · ${n.name}`)}/>
                  <PreviewBlock title={`Session beats · ${scaffoldPreview.data.preview.session_beats?.length || 0}`}
                                items={(scaffoldPreview.data.preview.session_beats || []).slice(0, 6)}/>
                </div>
                {scaffoldPreview.data.preview.opening_encounter?.name && (
                  <div className="text-arcane-light mt-2 text-[11px]">
                    Opening Encounter: <b>{scaffoldPreview.data.preview.opening_encounter.name}</b>
                    {" — will be staged on the Director's Console"}
                  </div>
                )}
                <div className="flex gap-2 mt-3">
                  <button onClick={() => scaffoldOneShot(scaffoldFileRef.current?.files?.[0]
                            || (scaffoldPreview && new File([], scaffoldPreview.filename)), true)}
                          className="btn btn-primary text-xs"
                          disabled={scaffoldBusy}
                          data-testid="scaffold-commit-btn">
                    <Sparkles className="w-3 h-3"/> Commit · deploy to campaign
                  </button>
                  <button onClick={() => setScaffoldPreview(null)}
                          className="btn btn-ghost text-[10px]"
                          data-testid="scaffold-discard-btn">Discard</button>
                </div>
                <div className="text-[10px] text-mist/60 italic mt-2">
                  Re-attaching the file is required for Commit (browsers don't keep file handles between calls).
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* History */}
      <div className="card-mystic p-4">
        <div className="label-ref mb-2">History · {list.length}</div>
        {list.length === 0 && <div className="text-mist italic text-xs">No ingestions yet.</div>}
        <ul className="space-y-1">
          {list.map((row) => (
            <li key={row.id}
                className={`flex items-center justify-between px-2 py-1.5 rounded-sm cursor-pointer ${open?.id === row.id ? "bg-gold/10 border border-gold/30" : "hover:bg-gold/5"}`}
                onClick={() => { setOpen(row); setMarked({}); setTab("all"); }}
                data-testid={`ingest-row-${row.id}`}>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-parchment font-ui flex items-center gap-2">
                  <FileText className="w-3 h-3 text-gold/70"/>
                  <span className="truncate">{row.filename}</span>
                  <span className={`tag text-[9px] ${row.status === "accepted" ? "border-arcane/50 text-arcane-light" : row.status === "partial" ? "border-gold/50 text-gold-bright" : "border-ember/50 text-ember"}`}>
                    {row.status}
                  </span>
                </div>
                <div className="text-[10px] text-mist/70 font-ui">
                  {row.suggestions?.length || 0} suggestions · {(row.byte_size/1024).toFixed(1)} KB · {(row.created_at || "").slice(0, 16)}
                </div>
              </div>
              <button onClick={(e) => { e.stopPropagation(); remove(row.id); }}
                      className="text-ember/70 hover:text-ember p-1"
                      data-testid={`ingest-delete-${row.id}`}>
                <Trash2 className="w-3 h-3"/>
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Detail / review */}
      {open && (
        <div className="card-mystic p-5" data-testid="ingest-detail">
          <div className="flex items-baseline justify-between gap-3 mb-3 flex-wrap">
            <div>
              <div className="label-ref">{open.filename}</div>
              <div className="text-[11px] text-mist/80 italic mt-1">{open.summary}</div>
              <div className="text-[10px] text-gold/60 font-ui mt-1">
                {Object.entries(open.detected_kind_counts || {}).map(([k, v]) => `${KIND_LABELS[k] || k}: ${v}`).join(" · ")}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-mist/70 font-ui">{Object.values(marked).filter(Boolean).length} marked</span>
              <button onClick={acceptMarked} disabled={busy || Object.values(marked).filter(Boolean).length === 0}
                      className="btn btn-primary text-xs" data-testid="ingest-accept-marked">
                <Check className="w-3 h-3"/> Accept all marked
              </button>
              <button onClick={() => {
                const all = {};
                filtered.forEach((s, i) => { if (!s.accepted) all[sugs.indexOf(s)] = true; });
                setMarked({ ...marked, ...all });
              }} className="btn btn-ghost text-xs" data-testid="ingest-mark-all-tab">
                <Filter className="w-3 h-3"/> Mark visible
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex flex-wrap gap-1 mb-3 border-b border-gold/10 pb-2"
               data-testid="ingest-tabs">
            <TabBtn label={`All · ${sugs.length}`} active={tab === "all"} onClick={() => setTab("all")} testid="ingest-tab-all"/>
            {KIND_ORDER.map((k) => {
              const n = (open.detected_kind_counts || {})[k] || 0;
              if (n === 0) return null;
              return (
                <TabBtn key={k} label={`${KIND_LABELS[k]} · ${n}`}
                        active={tab === k} onClick={() => setTab(k)}
                        testid={`ingest-tab-${k}`}/>
              );
            })}
          </div>

          {/* Suggestions */}
          {filtered.length === 0 && <div className="text-mist italic text-xs">Nothing in this category.</div>}
          <div className="space-y-2">
            {filtered.map((s) => {
              const idx = sugs.indexOf(s);
              const isMarked = !!marked[idx];
              return (
                <div key={idx}
                     className={`border rounded-sm p-3 ${s.accepted ? "border-arcane/40 opacity-70" : isMarked ? "border-gold/60 bg-gold/5" : "border-gold/15"}`}
                     data-testid={`ingest-sug-${idx}`}>
                  <div className="flex items-start gap-3">
                    <input type="checkbox"
                           disabled={s.accepted}
                           checked={isMarked || !!s.accepted}
                           onChange={(e) => setMarked({ ...marked, [idx]: e.target.checked })}
                           className="mt-1"
                           data-testid={`ingest-sug-${idx}-mark`}/>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="tag border-gold/50 text-gold-bright text-[10px]" data-testid={`ingest-sug-${idx}-kind`}>{KIND_LABELS[s.kind] || s.kind}</span>
                        <span className="font-display text-parchment">{s.title}</span>
                        {s.accepted && <span className="tag border-arcane/50 text-arcane-light text-[9px]"><Check className="w-3 h-3 inline"/> accepted</span>}
                      </div>
                      <div className="text-[12px] text-parchment/85 italic mt-1 leading-snug font-body">
                        {s.summary}
                      </div>
                      <div className="text-[10px] text-mist/70 font-ui mt-1.5 flex items-center gap-3 flex-wrap">
                        <span><BookOpen className="w-3 h-3 inline -mt-0.5"/> {s.source_ref || "—"}</span>
                        <span>· Atelier phase {s.atelier_phase}</span>
                        {s.target_arc && <span>· Arc: {s.target_arc}</span>}
                        {s.fields && Object.keys(s.fields).length > 0 && (
                          <span className="text-gold/70">
                            {Object.entries(s.fields).slice(0, 3).map(([k, v]) => `${k}: ${v}`).join(" · ")}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function TabBtn({ label, active, onClick, testid }) {
  return (
    <button onClick={onClick}
            className={`text-[10px] px-2 py-1 rounded-sm font-ui uppercase tracking-widest transition-colors ${active ? "bg-gold/15 text-gold-bright border border-gold/30" : "text-mist hover:bg-gold/5"}`}
            data-testid={testid}>
      {label}
    </button>
  );
}

function PreviewBlock({ title, items }) {
  return (
    <div className="border border-gold/10 rounded-sm p-2 bg-gold/5">
      <div className="label-ref mb-1">{title}</div>
      <ul className="space-y-0.5">
        {(items || []).map((it, i) => (
          <li key={i} className="text-[11px] text-parchment/85 truncate">· {it}</li>
        ))}
        {(!items || items.length === 0) && (
          <li className="text-[10px] text-mist italic">—</li>
        )}
      </ul>
    </div>
  );
}
