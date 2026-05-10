/**
 * AdminConsole — V6.25.39
 *
 * Admin-only moderation surface at `/app/admin`. Tabs:
 *   • Campaigns       — list ALL campaigns; force-unpublish, force-delete.
 *   • Public Showcases — list `discover_published=true`; one-click unpublish.
 *   • Marketplace      — list listings; take-down / reinstate.
 *   • Flags            — moderation queue; dismiss or action.
 *   • Audit Log        — read-only history of every admin action.
 *
 * Flags do NOT auto-hide content. Content stays visible until the admin
 * explicitly acts. Every action is audited.
 */
import React, { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield, AlertTriangle, EyeOff, Trash2, RefreshCw, ScrollText,
         CheckCircle2, XCircle, ExternalLink, Flag } from "lucide-react";
import { api, useAuth } from "../lib/api";

const TABS = [
  { k: "campaigns",   l: "All Campaigns" },
  { k: "showcases",   l: "Public Showcases" },
  { k: "marketplace", l: "Marketplace" },
  { k: "flags",       l: "Flag Queue" },
  { k: "audit",       l: "Audit Log" },
];

export default function AdminConsole() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [tab, setTab] = useState("campaigns");
  const [campaigns, setCampaigns] = useState([]);
  const [showcases, setShowcases] = useState([]);
  const [marketplace, setMarketplace] = useState([]);
  const [flags, setFlags] = useState([]);
  const [flagStatus, setFlagStatus] = useState("open");
  const [audit, setAudit] = useState([]);
  const [err, setErr] = useState("");

  const reload = useCallback(async () => {
    setErr("");
    try {
      const [c, s, m, f, a] = await Promise.all([
        api.get("/admin/campaigns").then((r) => r.data.items).catch(() => []),
        api.get("/admin/showcases").then((r) => r.data.items).catch(() => []),
        api.get("/admin/marketplace").then((r) => r.data.items).catch(() => []),
        api.get(`/admin/flags?status=${flagStatus}`).then((r) => r.data.items).catch(() => []),
        api.get("/admin/audit").then((r) => r.data.items).catch(() => []),
      ]);
      setCampaigns(c); setShowcases(s); setMarketplace(m); setFlags(f); setAudit(a);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load admin data.");
    }
  }, [flagStatus]);

  useEffect(() => { reload(); }, [reload]);

  if (user && user.role !== "admin") {
    return (
      <div className="px-6 md:px-12 py-10 text-mist">
        <div className="text-ember">Admin role required.</div>
      </div>
    );
  }

  const forceUnpublish = async (cid, reason = "") => {
    if (!window.confirm(`Force-unpublish this showcase from /discover?\n\n(Audited.)`)) return;
    await api.post(`/admin/campaigns/${cid}/force-unpublish`, { reason });
    await reload();
  };
  const forceDelete = async (cid) => {
    const reason = window.prompt("Reason for deletion (audited):");
    if (reason === null) return;
    if (!window.confirm(`PERMANENTLY DELETE campaign and ALL its data (codex, characters, sessions, gazette)? Cannot be undone.`)) return;
    await api.delete(`/admin/campaigns/${cid}?reason=${encodeURIComponent(reason)}`);
    await reload();
  };
  const takeDown = async (lid) => {
    const reason = window.prompt("Reason for take-down (audited):");
    if (reason === null) return;
    await api.post(`/admin/marketplace/${lid}/take-down`, { reason });
    await reload();
  };
  const reinstate = async (lid) => {
    await api.post(`/admin/marketplace/${lid}/reinstate`, { reason: "Reinstated by admin" });
    await reload();
  };
  const reviewFlag = async (fid, status) => {
    const notes = window.prompt(`Notes (audited) for ${status}:`, "");
    if (notes === null) return;
    await api.patch(`/admin/flags/${fid}`, { status, notes });
    await reload();
  };

  return (
    <div className="px-6 md:px-12 py-10 max-w-6xl" data-testid="admin-console">
      <div className="mb-6">
        <h1 className="font-display tracking-[0.18em] text-3xl text-parchment flex items-center gap-3">
          <Shield className="w-6 h-6 text-gold-bright"/>
          Admin Moderation Console
        </h1>
        <div className="text-mist text-sm mt-1 max-w-2xl">
          App-wide moderation. Every action is audited. Flags stay visible
          until you review them.
        </div>
      </div>

      {err && <div className="text-ember text-sm mb-3" data-testid="admin-error">{err}</div>}

      <div className="flex gap-2 border-b border-gold/10 mb-4 overflow-x-auto">
        {TABS.map((t) => (
          <button key={t.k} type="button" onClick={() => setTab(t.k)}
                  className={`px-4 py-2 text-xs font-ui tracking-widest uppercase whitespace-nowrap ${tab === t.k ? "text-gold-bright border-b border-gold" : "text-mist hover:text-parchment"}`}
                  data-testid={`admin-tab-${t.k}`}>
            {t.l}
            {t.k === "flags" && flags.length > 0 && (
              <span className="ml-2 px-1.5 rounded-full bg-ember/40 text-parchment text-[9px] tabular-nums">{flags.length}</span>
            )}
          </button>
        ))}
        <div className="flex-1"/>
        <button type="button" onClick={reload} className="btn btn-ghost text-xs">
          <RefreshCw className="w-3 h-3"/>
        </button>
      </div>

      {tab === "campaigns" && (
        <Table rows={campaigns}
                cols={[
                  { l: "Name", k: "name" },
                  { l: "System", k: "system_id" },
                  { l: "GM", k: "gm_name" },
                  { l: "Visibility", render: (r) => r.visibility || "private" },
                  { l: "Discover?", render: (r) => r.discover_published
                      ? <span className="tag bg-gold/20 text-gold-bright text-[9px] uppercase">public</span>
                      : <span className="text-mist/60 text-xs">—</span> },
                  { l: "Members", render: (r) => (r.member_ids || []).length },
                ]}
                actions={(r) => (
                  <>
                    <Link to={`/app/campaigns/${r.id}`} className="btn btn-ghost text-[10px]"
                          data-testid={`admin-open-campaign-${r.id}`}>
                      <ExternalLink className="w-3 h-3"/>
                    </Link>
                    {r.discover_published && (
                      <button onClick={() => forceUnpublish(r.id)}
                              className="btn btn-ghost text-[10px]"
                              data-testid={`admin-unpub-${r.id}`}
                              title="Force unpublish from /discover">
                        <EyeOff className="w-3 h-3"/>
                      </button>
                    )}
                    <button onClick={() => forceDelete(r.id)}
                            className="btn btn-danger text-[10px]"
                            data-testid={`admin-del-${r.id}`}
                            title="Force-delete (cascades to all campaign data)">
                      <Trash2 className="w-3 h-3"/>
                    </button>
                  </>
                )}
                testid="admin-table-campaigns"/>
      )}

      {tab === "showcases" && (
        <Table rows={showcases}
                cols={[
                  { l: "Name", k: "name" },
                  { l: "System", k: "system_id" },
                  { l: "Slug", render: (r) => <code className="text-gold-bright text-[10px]">{r.discover_slug}</code> },
                  { l: "GM", k: "gm_name" },
                ]}
                actions={(r) => (
                  <>
                    <a href={`/discover/${r.discover_slug}`} target="_blank" rel="noopener noreferrer"
                       className="btn btn-ghost text-[10px]"
                       data-testid={`admin-showcase-open-${r.id}`}>
                      <ExternalLink className="w-3 h-3"/>
                    </a>
                    <button onClick={() => forceUnpublish(r.id, "Force unpublished from admin console")}
                            className="btn btn-danger text-[10px]"
                            data-testid={`admin-showcase-unpub-${r.id}`}>
                      <EyeOff className="w-3 h-3"/> Unpublish
                    </button>
                  </>
                )}
                testid="admin-table-showcases"/>
      )}

      {tab === "marketplace" && (
        <Table rows={marketplace}
                cols={[
                  { l: "Title", k: "title" },
                  { l: "Kind", k: "kind" },
                  { l: "Price", render: (r) => `${r.price ?? 0} ${r.currency || ""}` },
                  { l: "Status", render: (r) => r.taken_down
                      ? <span className="tag bg-ember/30 text-parchment text-[9px] uppercase">taken down</span>
                      : <span className="tag bg-gold/15 text-gold-bright text-[9px] uppercase">live</span> },
                ]}
                actions={(r) => (
                  r.taken_down
                    ? <button onClick={() => reinstate(r.id)} className="btn btn-ghost text-[10px]"
                              data-testid={`admin-reinstate-${r.id}`}>
                        <RefreshCw className="w-3 h-3"/> Reinstate
                      </button>
                    : <button onClick={() => takeDown(r.id)} className="btn btn-danger text-[10px]"
                              data-testid={`admin-takedown-${r.id}`}>
                        <EyeOff className="w-3 h-3"/> Take down
                      </button>
                )}
                testid="admin-table-marketplace"/>
      )}

      {tab === "flags" && (
        <>
          <div className="flex gap-2 mb-2 text-[10px] uppercase tracking-widest">
            {["open", "actioned", "dismissed", "all"].map((s) => (
              <button key={s} onClick={() => setFlagStatus(s)}
                      className={`px-2 py-1 rounded-sm border ${flagStatus === s ? "border-gold text-gold-bright" : "border-gold/15 text-mist"}`}
                      data-testid={`admin-flag-filter-${s}`}>
                {s}
              </button>
            ))}
          </div>
          <Table rows={flags}
                  cols={[
                    { l: "Target", render: (r) => <code className="text-[10px]">{r.target_kind}/{r.target_id.slice(0, 12)}…</code> },
                    { l: "Reason", render: (r) => <span className="text-xs italic">{(r.reason || "").slice(0, 120)}</span> },
                    { l: "Filed by", k: "filed_by_name" },
                    { l: "When", render: (r) => (r.filed_at || "").slice(0, 16).replace("T", " ") },
                    { l: "Status", k: "status" },
                  ]}
                  actions={(r) => (
                    r.status === "open" ? (
                      <>
                        <button onClick={() => reviewFlag(r.id, "actioned")}
                                className="btn btn-primary text-[10px]"
                                data-testid={`admin-flag-action-${r.id}`}>
                          <CheckCircle2 className="w-3 h-3"/> Action
                        </button>
                        <button onClick={() => reviewFlag(r.id, "dismissed")}
                                className="btn btn-ghost text-[10px]"
                                data-testid={`admin-flag-dismiss-${r.id}`}>
                          <XCircle className="w-3 h-3"/> Dismiss
                        </button>
                      </>
                    ) : (
                      <span className="text-[10px] text-mist italic">{r.review_notes || "—"}</span>
                    )
                  )}
                  testid="admin-table-flags"/>
        </>
      )}

      {tab === "audit" && (
        <Table rows={audit}
                cols={[
                  { l: "When", render: (r) => (r.at || "").slice(0, 16).replace("T", " ") },
                  { l: "Actor", render: (r) => r.actor_email || r.actor_id?.slice(0, 8) },
                  { l: "Action", render: (r) => <code className="text-[10px]">{r.action}</code> },
                  { l: "Target", render: (r) => <span className="text-[10px]">{r.target_kind}/{(r.target_id || "").slice(0, 12)}…</span> },
                  { l: "Reason", render: (r) => <span className="text-xs italic">{(r.reason || "").slice(0, 90)}</span> },
                ]}
                testid="admin-table-audit"/>
      )}
    </div>
  );
}


function Table({ rows, cols, actions, testid }) {
  if (!rows || rows.length === 0) {
    return <div className="card-mystic p-4 text-mist text-sm italic" data-testid={`${testid}-empty`}>No rows.</div>;
  }
  return (
    <div className="card-mystic p-3 overflow-x-auto" data-testid={testid}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gold/20">
            {cols.map((c, i) => (
              <th key={i} className="text-left py-1.5 px-2 text-gold/70 uppercase tracking-widest text-[10px]">
                {c.l}
              </th>
            ))}
            {actions && <th className="text-right py-1.5 px-2 text-gold/70 uppercase tracking-widest text-[10px]">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, idx) => (
            <tr key={r.id || idx} className="border-b border-gold/5 hover:bg-gold/5">
              {cols.map((c, ci) => (
                <td key={ci} className="py-1.5 px-2 text-parchment">
                  {c.render ? c.render(r) : (r[c.k] ?? "—")}
                </td>
              ))}
              {actions && <td className="py-1.5 px-2 text-right">
                <div className="inline-flex gap-1 justify-end flex-wrap">{actions(r)}</div>
              </td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
