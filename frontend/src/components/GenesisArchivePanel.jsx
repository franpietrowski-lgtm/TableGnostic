/**
 * GenesisArchivePanel — V6.25.8
 *
 * GM-only expandable archive of past Genesis sheet versions for a
 * campaign. The backend snapshots a copy of the live Genesis every
 * time it's overwritten and keeps the last 50 — this surface lets
 * the GM:
 *   • expand each archive in-place to inspect the saved JSON,
 *   • restore an archive into the live slot (current live is itself
 *     archived first so nothing is lost),
 *   • delete an archive permanently.
 *
 * Sharing currently piggybacks on the campaign's existing fork /
 * delta-drop pipeline (see DeltaDropPanel) — no per-archive share
 * link yet; that's slated for a follow-up once the marketplace
 * publishing flow grows author payouts.
 */
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { ChevronDown, ChevronRight, RotateCcw, Trash2, Loader2, Archive } from "lucide-react";

export default function GenesisArchivePanel({ campId, isGm }) {
  const [rows, setRows] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null); // archive_id currently mutating
  const [err, setErr] = useState("");

  const refresh = async () => {
    setLoading(true); setErr("");
    try {
      const { data } = await api.get(`/campaigns/${campId}/genesis/archives`);
      setRows(data || []);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  useEffect(() => { if (isGm) refresh(); }, [campId, isGm]);

  if (!isGm) return null;

  const restore = async (aid) => {
    if (!window.confirm("Restore this archived Genesis to be the live sheet? "
                          + "The current live sheet will be archived first.")) return;
    setBusy(aid); setErr("");
    try {
      await api.post(`/campaigns/${campId}/genesis/archives/${aid}/restore`);
      await refresh();
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(null); }
  };
  const remove = async (aid) => {
    if (!window.confirm("Delete this archive permanently? This cannot be undone.")) return;
    setBusy(aid); setErr("");
    try {
      await api.delete(`/campaigns/${campId}/genesis/archives/${aid}`);
      setRows(rows.filter((r) => r.archive_id !== aid));
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(null); }
  };

  return (
    <div className="card-mystic p-5 mt-4" data-testid="genesis-archive-panel">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Archive className="w-4 h-4 text-gold/70"/>
          <div>
            <div className="label-ref">Genesis Archive</div>
            <div className="text-[11px] text-mist italic">
              Last {rows.length} saved snapshot{rows.length === 1 ? "" : "s"}.
              {" "}Click a row to inspect, restore, or delete.
            </div>
          </div>
        </div>
        <button onClick={refresh} className="btn btn-ghost text-[10px]"
                data-testid="genesis-archive-refresh">Refresh</button>
      </div>
      {err && <div className="text-ember text-[11px] mb-2"
                     data-testid="genesis-archive-error">{err}</div>}
      {loading ? (
        <div className="flex items-center gap-2 text-mist text-xs">
          <Loader2 className="w-3 h-3 animate-spin"/> Loading archives…
        </div>
      ) : rows.length === 0 ? (
        <div className="text-mist italic text-[12px]"
             data-testid="genesis-archive-empty">
          No archives yet — archives are created automatically the first
          time you re-save Genesis. Edit the live Genesis once, then
          come back here and you'll see the previous version listed.
        </div>
      ) : (
        <div className="border border-gold/15 rounded-sm divide-y divide-gold/10">
          {rows.map((r) => {
            const aid = r.archive_id;
            const open = openId === aid;
            const summary = _summarize(r);
            return (
              <div key={aid} data-testid={`genesis-archive-row-${aid}`}>
                <button onClick={() => setOpenId(open ? null : aid)}
                        className="w-full flex items-center justify-between p-3 hover:bg-gold/5
                                    text-left"
                        data-testid={`genesis-archive-toggle-${aid}`}>
                  <div className="flex items-center gap-2 min-w-0">
                    {open ? <ChevronDown className="w-3 h-3 text-gold"/>
                          : <ChevronRight className="w-3 h-3 text-gold"/>}
                    <div className="min-w-0">
                      <div className="text-sm text-parchment font-display truncate">
                        {summary.title}
                      </div>
                      <div className="text-[10px] text-mist font-ui">
                        archived {_fmtDate(r.archived_at)} · {summary.bytes} chars
                      </div>
                    </div>
                  </div>
                </button>
                {open && (
                  <div className="px-3 pb-3 space-y-3" data-testid={`genesis-archive-body-${aid}`}>
                    <pre className="text-[10px] text-mist whitespace-pre-wrap font-mono
                                       max-h-72 overflow-y-auto bg-void/50 border border-gold/10
                                       rounded-sm p-2"
                         data-testid={`genesis-archive-json-${aid}`}>
                      {JSON.stringify(_clean(r), null, 2)}
                    </pre>
                    <div className="flex flex-wrap gap-2">
                      <button onClick={() => restore(aid)} disabled={busy === aid}
                              className="btn btn-primary text-xs"
                              data-testid={`genesis-archive-restore-${aid}`}>
                        {busy === aid ? <Loader2 className="w-3 h-3 animate-spin"/>
                                       : <RotateCcw className="w-3 h-3"/>} Restore as live
                      </button>
                      <button onClick={() => remove(aid)} disabled={busy === aid}
                              className="btn btn-ghost text-xs text-ember hover:text-ember-bright"
                              data-testid={`genesis-archive-delete-${aid}`}>
                        <Trash2 className="w-3 h-3"/> Delete
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const _fmtDate = (iso) => {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch { return iso; }
};

const _clean = (r) => {
  const { _id, _id_dropped, archive_id, archived_at, archived_by, archived_from, kind, ...rest } = r;
  return rest;
};

const _summarize = (r) => {
  const cleaned = _clean(r);
  const json = JSON.stringify(cleaned);
  const setting = r.setting_name || r.title || r.campaign_name || "Genesis snapshot";
  const phase = r.current_phase || r.phase || null;
  const title = phase ? `${setting} · phase ${phase}` : setting;
  return { title, bytes: json.length };
};
