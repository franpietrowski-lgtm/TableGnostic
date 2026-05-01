import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Share2, Download, Clock, CheckCircle2, XCircle, Eye } from "lucide-react";

/**
 * DeltaDropPanel — GM-only surface for pushing & receiving canonical
 * campaign updates.
 *
 * Two modes, auto-detected from the campaign's `cloned_from` field:
 *
 *   • **Origin mode** (campaign is the canonical source):
 *     GM can author a new Delta Drop — a titled + summarised snapshot
 *     of the current codex + motives + epic + genesis payload — which
 *     gets broadcast to every clone of this campaign. Useful for
 *     setting curators pushing errata / new lore to derivative tables.
 *
 *   • **Clone mode** (campaign is a clone):
 *     GM sees all deltas the origin has published with pending / applied
 *     / deferred status. They preview a delta's bundle, then APPLY
 *     (merges non-destructively) or DEFER (dismisses the badge).
 */
export default function DeltaDropPanel({ campaign, onApplied }) {
  const [deltas, setDeltas] = useState([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(null);
  const isClone = !!campaign?.cloned_from;

  const load = useCallback(async () => {
    setErr("");
    try {
      const { data } = await api.get(`/campaigns/${campaign.id}/deltas`);
      setDeltas(data || []);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [campaign?.id]);

  useEffect(() => { load(); }, [load]);

  if (!campaign?.is_gm) return null;

  const publish = async (e) => {
    e?.preventDefault?.();
    const title = e.target.elements.title.value.trim();
    const summary = e.target.elements.summary.value.trim();
    if (!title) return;
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${campaign.id}/deltas`, { title, summary });
      e.target.reset();
      await load();
    } catch (ex) {
      setErr(formatApiErrorDetail(ex.response?.data?.detail) || ex.message);
    } finally { setBusy(false); }
  };

  const apply = async (did) => {
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/campaigns/${campaign.id}/deltas/${did}/apply`);
      window.alert(`Applied. ${data.added_nodes} node(s) + ${data.added_motives} motive(s) added` +
                   `${data.epic_applied ? " · epic synced" : ""}` +
                   `${data.genesis_applied ? " · genesis synced" : ""}.`);
      await load();
      onApplied && onApplied();
    } catch (ex) {
      setErr(formatApiErrorDetail(ex.response?.data?.detail) || ex.message);
    } finally { setBusy(false); }
  };

  const defer = async (did) => {
    setBusy(true); setErr("");
    try {
      await api.post(`/campaigns/${campaign.id}/deltas/${did}/defer`);
      await load();
    } catch (ex) {
      setErr(formatApiErrorDetail(ex.response?.data?.detail) || ex.message);
    } finally { setBusy(false); }
  };

  const openPreview = async (did) => {
    try {
      const { data } = await api.get(`/campaigns/${campaign.id}/deltas/${did}`);
      setPreview(data);
    } catch (ex) {
      setErr(formatApiErrorDetail(ex.response?.data?.detail) || ex.message);
    }
  };

  const pending = deltas.filter((d) => d.status === "pending").length;

  return (
    <div className="card-mystic p-5 mt-4" data-testid="delta-drop-panel">
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Share2 className="w-4 h-4"/> Delta Drop
            {isClone ? (
              <span className="tag border-arcane/40 text-arcane">Clone</span>
            ) : (
              <span className="tag border-gold/40 text-gold-bright">Origin</span>
            )}
            {isClone && pending > 0 && (
              <span className="tag border-ember/50 text-ember"
                    data-testid="delta-pending-badge">
                {pending} pending
              </span>
            )}
          </div>
          <div className="text-[11px] text-mist/80 italic mt-1 max-w-xl leading-snug">
            {isClone
              ? "This campaign was cloned — the origin author can push updates here (codex / motives / epic / genesis). Apply merges them non-destructively; defer dismisses until next drop."
              : "Publish a snapshot of this campaign's canonical state. Every campaign cloned from it gets a pending-update badge; their GMs decide whether to merge your changes."}
          </div>
        </div>
      </div>

      {!isClone && (
        <form onSubmit={publish} className="mt-3 grid gap-2 sm:grid-cols-2"
              data-testid="delta-publish-form">
          <input name="title" className="input text-sm sm:col-span-2"
                 placeholder="Drop title — e.g. 'Patch 2 — Sylas backstory, new deacon'"
                 data-testid="delta-publish-title-input"
                 required/>
          <textarea name="summary" className="input text-sm sm:col-span-2 min-h-[60px]"
                    placeholder="What's in this drop? (optional changelog for receivers)"
                    data-testid="delta-publish-summary-input"/>
          <div className="sm:col-span-2 flex items-center gap-2">
            <button type="submit" className="btn btn-primary text-xs"
                    disabled={busy} data-testid="delta-publish-btn">
              <Share2 className="w-3 h-3"/> Publish Drop to all clones
            </button>
            <span className="text-[10px] text-mist italic">
              Snapshots all codex nodes, motives, epic plan, and genesis. Version auto-increments.
            </span>
          </div>
        </form>
      )}

      {err && <div className="text-ember text-xs mt-2" data-testid="delta-error">{err}</div>}

      {/* Drop list ─────────────────────────────────────── */}
      {deltas.length === 0 ? (
        <div className="mt-3 text-[11px] text-mist italic" data-testid="delta-empty">
          {isClone ? "No drops from the origin yet." : "No drops published yet."}
        </div>
      ) : (
        <div className="mt-3 space-y-2" data-testid="delta-list">
          {deltas.map((d) => (
            <div key={d.id}
                 className="border border-gold/15 rounded-sm p-3"
                 data-testid={`delta-row-${d.id}`}>
              <div className="flex items-start justify-between flex-wrap gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-ui text-parchment text-sm">{d.title}</span>
                    <span className="text-[9px] text-mist uppercase tracking-widest">v{d.version}</span>
                    {d.status === "pending" && (
                      <span className="tag border-ember/40 text-ember"><Clock className="w-3 h-3"/> Pending</span>
                    )}
                    {d.status === "applied" && (
                      <span className="tag border-arcane/40 text-arcane"><CheckCircle2 className="w-3 h-3"/> Applied</span>
                    )}
                    {d.status === "deferred" && (
                      <span className="tag border-mist/40 text-mist"><XCircle className="w-3 h-3"/> Deferred</span>
                    )}
                    {d.status === "published" && (
                      <span className="tag border-gold/40 text-gold">Published</span>
                    )}
                  </div>
                  <div className="text-[10px] text-mist mt-0.5">
                    {d.origin_author_name} · {d.published_at ? new Date(d.published_at).toLocaleString() : ""}
                  </div>
                  {d.summary && (
                    <div className="text-[12px] text-parchment/85 italic mt-1 whitespace-pre-wrap">
                      {d.summary}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1 flex-wrap">
                  <button onClick={() => openPreview(d.id)}
                          className="btn btn-ghost text-xs"
                          data-testid={`delta-preview-${d.id}`}
                          title="Inspect the drop's bundle before applying">
                    <Eye className="w-3 h-3"/> Preview
                  </button>
                  {isClone && d.status !== "applied" && (
                    <button onClick={() => apply(d.id)}
                            disabled={busy}
                            className="btn btn-primary text-xs"
                            data-testid={`delta-apply-${d.id}`}>
                      <Download className="w-3 h-3"/> Apply
                    </button>
                  )}
                  {isClone && d.status === "pending" && (
                    <button onClick={() => defer(d.id)}
                            disabled={busy}
                            className="btn btn-ghost text-xs"
                            data-testid={`delta-defer-${d.id}`}>
                      Defer
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {preview && (
        <DeltaPreviewModal delta={preview} onClose={() => setPreview(null)}/>
      )}
    </div>
  );
}

function DeltaPreviewModal({ delta, onClose }) {
  const b = delta.bundle || {};
  const counts = {
    nodes: (b.nodes || []).length,
    motives: (b.motives || []).length,
    epic: b.epic && Object.keys(b.epic).length ? 1 : 0,
    genesis: b.genesis && Object.keys(b.genesis).length ? 1 : 0,
  };
  return (
    <div className="fixed inset-0 bg-void/90 backdrop-blur-md z-50 flex items-center justify-center p-4"
         data-testid="delta-preview-modal"
         onClick={onClose}>
      <div className="card-mystic p-6 max-w-3xl w-full max-h-[85vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between flex-wrap gap-2">
          <div>
            <div className="label-ref">Delta Drop Preview · v{delta.version}</div>
            <h3 className="font-display text-2xl text-gold mt-1">{delta.title}</h3>
            <div className="text-[11px] text-mist">
              {delta.origin_author_name} · {delta.published_at && new Date(delta.published_at).toLocaleString()}
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost text-xs"
                  data-testid="delta-preview-close">Close</button>
        </div>
        {delta.summary && (
          <div className="mt-3 text-sm text-parchment/90 italic whitespace-pre-wrap border-l-2 border-gold/30 pl-3">
            {delta.summary}
          </div>
        )}
        <div className="grid grid-cols-4 gap-2 mt-4 text-center" data-testid="delta-preview-counts">
          <CountChip label="Codex nodes" v={counts.nodes}/>
          <CountChip label="Motives" v={counts.motives}/>
          <CountChip label="Epic plan" v={counts.epic ? "1 doc" : "—"}/>
          <CountChip label="Genesis" v={counts.genesis ? "1 doc" : "—"}/>
        </div>
        {counts.nodes > 0 && (
          <details className="mt-3" data-testid="delta-preview-nodes">
            <summary className="label-ref cursor-pointer">{counts.nodes} codex nodes</summary>
            <ul className="mt-2 space-y-1 text-[12px]">
              {b.nodes.map((n, i) => (
                <li key={i} className="border-b border-gold/10 py-1">
                  <span className="text-gold-bright font-ui">{n.title}</span>
                  <span className="text-[10px] text-mist ml-2 uppercase tracking-widest">{n.type}</span>
                  {n.summary && <div className="text-mist italic">{n.summary}</div>}
                </li>
              ))}
            </ul>
          </details>
        )}
        {counts.motives > 0 && (
          <details className="mt-2" data-testid="delta-preview-motives">
            <summary className="label-ref cursor-pointer">{counts.motives} motives</summary>
            <ul className="mt-2 space-y-1 text-[12px]">
              {b.motives.map((m, i) => (
                <li key={i} className="border-b border-gold/10 py-1">
                  <span className="text-gold font-ui">{m.npc_name || m.node_id}</span>
                  <span className="text-parchment ml-2">{m.motive}</span>
                  {m.plot_phase && <span className="text-[10px] text-mist ml-2 uppercase tracking-widest">{m.plot_phase}</span>}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}

function CountChip({ label, v }) {
  return (
    <div className="border border-gold/20 rounded-sm py-2">
      <div className="label-ref text-[9px]">{label}</div>
      <div className="font-display text-xl text-gold-bright">{v}</div>
    </div>
  );
}
