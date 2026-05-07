/**
 * ClassifierConfidencePanel — V6.25.21
 *
 * GM-only audit surface for codex nodes that the V6.25.19 classifier
 * auto-placed onto a Pillar.Branch. Renders a sortable list (lowest
 * confidence first) with three actions per row:
 *   1. Confirm → locks the placement (auto_classified=false).
 *   2. Re-pin  → moves the row to a different Pillar.Branch via the
 *                existing PATCH /codex-nodes/{nid}/place endpoint
 *                (which also clears auto_classified).
 *   3. Open    → fires the existing tg:open-codex-node CustomEvent.
 *
 * A one-glance "world is converging" meter at the top shows the
 * ratio of manual vs auto vs unplaced rows.
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Sparkles, RefreshCw, Check, MapPin, ExternalLink, Loader2,
  ChevronDown, ChevronRight,
} from "lucide-react";

const CONF_BAND = (c) => {
  // Visual band for the confidence pill.
  if (c >= 0.9) return { label: "high",   tone: "text-gold-bright" };
  if (c >= 0.65) return { label: "good",  tone: "text-arcane-light" };
  if (c >= 0.4) return { label: "fair",   tone: "text-mist" };
  return { label: "low", tone: "text-ember" };
};


export default function ClassifierConfidencePanel({ campId, schema, isGm, onChanged }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [pinning, setPinning] = useState({});  // {id: section}
  const [rowBusy, setRowBusy] = useState({});

  const refresh = useCallback(async () => {
    if (!campId || !isGm) return;
    setBusy(true); setErr("");
    try {
      const { data } = await api.get(
        `/campaigns/${campId}/codex/classifier-audit`);
      setData(data);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  }, [campId, isGm]);

  useEffect(() => { if (open) refresh(); }, [open, refresh]);

  if (!isGm) return null;

  const allSections = (() => {
    const out = [];
    Object.entries(schema?.pillars || {}).forEach(([pillar, meta]) => {
      (meta.branches || []).forEach((branch) => out.push(`${pillar}.${branch}`));
    });
    return out;
  })();

  const confirm = async (nid) => {
    setRowBusy({ ...rowBusy, [nid]: true });
    try {
      await api.post(
        `/campaigns/${campId}/codex/classifier-audit/${nid}/confirm`);
      await refresh();
      onChanged && onChanged();
    } catch (e) {
      window.alert("Confirm failed: "
        + (formatApiErrorDetail(e.response?.data?.detail) || e.message));
    } finally { setRowBusy({ ...rowBusy, [nid]: false }); }
  };

  const repin = async (nid) => {
    const section = pinning[nid];
    if (!section) return;
    setRowBusy({ ...rowBusy, [nid]: true });
    try {
      await api.patch(
        `/campaigns/${campId}/codex-nodes/${nid}/place`, { section });
      await refresh();
      onChanged && onChanged();
    } catch (e) {
      window.alert("Re-pin failed: "
        + (formatApiErrorDetail(e.response?.data?.detail) || e.message));
    } finally { setRowBusy({ ...rowBusy, [nid]: false }); }
  };

  const totals = data?.totals || { auto_placed: 0, manual_placed: 0, unplaced: 0, total: 0 };
  const rows = data?.rows || [];

  // Convergence meter: manual ÷ (manual + auto + unplaced).
  const denom = totals.manual_placed + totals.auto_placed + totals.unplaced || 1;
  const convergence = Math.round((totals.manual_placed / denom) * 100);

  return (
    <div className="card-mystic p-3"
         data-testid="classifier-confidence-panel">
      <button onClick={() => setOpen(!open)}
              className="w-full flex items-center justify-between"
              data-testid="classifier-confidence-toggle">
        <div className="flex items-center gap-2">
          {open ? <ChevronDown className="w-3 h-3"/> : <ChevronRight className="w-3 h-3"/>}
          <Sparkles className="w-3 h-3 text-arcane"/>
          <span className="text-parchment font-display text-sm">
            Classifier Confidence Audit
          </span>
        </div>
        {data && (
          <span className="text-[10px] text-mist tabular-nums"
                data-testid="classifier-convergence">
            {convergence}% converged · {totals.auto_placed} auto · {totals.unplaced} unplaced
          </span>
        )}
      </button>

      {open && (
        <div className="mt-3 space-y-2">
          <div className="text-[10px] text-mist/80 italic">
            Auto-placed codex entries sorted by ascending confidence.
            Confirm a placement to lock it, or re-pin to a different
            Pillar.Branch. Manual placements never appear here.
          </div>

          {/* Convergence meter */}
          <div className="flex h-2 rounded-sm overflow-hidden bg-void/60 border border-gold/10"
               data-testid="convergence-meter">
            <div className="bg-gold-bright"
                 style={{ width: `${(totals.manual_placed / denom) * 100}%` }}
                 title={`${totals.manual_placed} manually pinned`}/>
            <div className="bg-arcane/60"
                 style={{ width: `${(totals.auto_placed / denom) * 100}%` }}
                 title={`${totals.auto_placed} auto-classified`}/>
            <div className="bg-mist/30"
                 style={{ width: `${(totals.unplaced / denom) * 100}%` }}
                 title={`${totals.unplaced} unplaced`}/>
          </div>

          <div className="flex justify-between items-center">
            <div className="text-[10px] text-mist">
              <span className="text-gold-bright">manual {totals.manual_placed}</span>
              {" · "}
              <span className="text-arcane-light">auto {totals.auto_placed}</span>
              {" · "}
              <span className="text-mist">unplaced {totals.unplaced}</span>
              {" / "}
              <span>total {totals.total}</span>
            </div>
            <button onClick={refresh}
                    disabled={busy}
                    className="btn btn-ghost text-[10px]"
                    data-testid="classifier-confidence-refresh">
              {busy ? <Loader2 className="w-3 h-3 animate-spin"/>
                    : <RefreshCw className="w-3 h-3"/>}
              Refresh
            </button>
          </div>

          {err && (
            <div className="text-ember text-xs"
                 data-testid="classifier-confidence-error">{err}</div>
          )}

          {rows.length === 0 && !busy && (
            <div className="text-mist italic text-[11px]">
              No auto-placed nodes — every codex entry has either been
              manually pinned or is intentionally floating.
            </div>
          )}

          <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
            {rows.map((r) => {
              const band = CONF_BAND(r.confidence);
              const conf = Math.round(r.confidence * 100);
              return (
                <div key={r.id}
                     className="border border-gold/10 rounded-sm p-2 space-y-1.5"
                     data-testid={`classifier-row-${r.id}`}>
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-parchment text-sm truncate">
                        {r.name}
                        <span className="text-[10px] text-mist/70 ml-1.5 uppercase tracking-widest">
                          {r.node_kind}
                        </span>
                      </div>
                      <div className="text-[10px] text-mist">
                        <span className="text-arcane-light">{r.section}</span>
                        {r.source && (
                          <> · from <span className="text-parchment">{r.source}</span></>
                        )}
                      </div>
                    </div>
                    <span className={`tag text-[10px] ${band.tone}`}
                          data-testid={`classifier-confidence-${r.id}`}
                          title={r.reasoning}>
                      {conf}% · {band.label}
                    </span>
                  </div>

                  {r.reasoning && (
                    <div className="text-[10px] text-mist/70 italic border-l-2 border-arcane/20 pl-2">
                      {r.reasoning}
                    </div>
                  )}

                  <div className="flex flex-wrap gap-1.5 items-center pt-1">
                    <button onClick={() => confirm(r.id)}
                            disabled={rowBusy[r.id]}
                            className="btn btn-ghost text-[10px]"
                            title="Lock this placement so future edits don't re-classify"
                            data-testid={`classifier-confirm-${r.id}`}>
                      {rowBusy[r.id]
                        ? <Loader2 className="w-3 h-3 animate-spin"/>
                        : <Check className="w-3 h-3 text-gold-bright"/>}
                      Confirm
                    </button>
                    <select className="select select-sm text-[10px]"
                            value={pinning[r.id] || ""}
                            onChange={(e) => setPinning({ ...pinning, [r.id]: e.target.value })}
                            data-testid={`classifier-repin-select-${r.id}`}>
                      <option value="">— move to —</option>
                      {allSections.filter((s) => s !== r.section).map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                    <button onClick={() => repin(r.id)}
                            disabled={rowBusy[r.id] || !pinning[r.id]}
                            className="btn btn-ghost text-[10px]"
                            data-testid={`classifier-repin-${r.id}`}>
                      <MapPin className="w-3 h-3"/> Re-pin
                    </button>
                    <button onClick={() => window.dispatchEvent(new CustomEvent(
                              "tg:open-codex-node",
                              { detail: { node_id: r.id, campaign_id: campId } }))}
                            className="btn btn-ghost text-[10px]"
                            data-testid={`classifier-open-${r.id}`}>
                      <ExternalLink className="w-3 h-3"/> Open
                    </button>
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
