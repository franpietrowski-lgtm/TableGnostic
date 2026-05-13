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
         CheckCircle2, XCircle, ExternalLink, Flag, Star, MessagesSquare,
         X, Send } from "lucide-react";
import { api, useAuth } from "../lib/api";

const TABS = [
  { k: "campaigns",   l: "All Campaigns" },
  { k: "showcases",   l: "Public Showcases" },
  { k: "featured",    l: "Featured Requests" },
  { k: "roadmap",     l: "Roadmap" },
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
  const [roadmap, setRoadmap] = useState([]);
  const [featuredReqs, setFeaturedReqs] = useState([]);
  const [threadFlag, setThreadFlag] = useState(null);
  const [err, setErr] = useState("");

  const reload = useCallback(async () => {
    setErr("");
    try {
      const [c, s, m, f, a, r, fr] = await Promise.all([
        api.get("/admin/campaigns").then((x) => x.data.items).catch(() => []),
        api.get("/admin/showcases").then((x) => x.data.items).catch(() => []),
        api.get("/admin/marketplace").then((x) => x.data.items).catch(() => []),
        api.get(`/admin/flags?status=${flagStatus}`).then((x) => x.data.items).catch(() => []),
        api.get("/admin/audit").then((x) => x.data.items).catch(() => []),
        api.get("/admin/roadmap").then((x) => x.data.items).catch(() => []),
        api.get("/admin/featured-requests").then((x) => x.data.items).catch(() => []),
      ]);
      setCampaigns(c); setShowcases(s); setMarketplace(m); setFlags(f);
      setAudit(a); setRoadmap(r); setFeaturedReqs(fr);
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
  const approveFeature = async (cid) => {
    await api.post(`/admin/campaigns/${cid}/feature`);
    await reload();
  };
  const unfeature = async (cid) => {
    await api.delete(`/admin/campaigns/${cid}/feature`);
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
                        <button onClick={() => setThreadFlag(r)}
                                className="btn btn-ghost text-[10px]"
                                data-testid={`admin-flag-thread-${r.id}`}>
                          <MessagesSquare className="w-3 h-3"/> Open
                        </button>
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
                      <>
                        <button onClick={() => setThreadFlag(r)}
                                className="btn btn-ghost text-[10px]"
                                data-testid={`admin-flag-thread-${r.id}`}>
                          <MessagesSquare className="w-3 h-3"/> Thread
                        </button>
                        <span className="text-[10px] text-mist italic">{r.review_notes || "—"}</span>
                      </>
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

      {tab === "featured" && (
        <Table rows={featuredReqs}
                cols={[
                  { l: "Campaign", k: "name" },
                  { l: "System", k: "system_id" },
                  { l: "GM", k: "gm_name" },
                  { l: "Slug", render: (r) => <code className="text-[10px] text-gold-bright">{r.discover_slug}</code> },
                  { l: "Requested", render: (r) => (r.featured_requested_at || "").slice(0, 16).replace("T", " ") },
                  { l: "Note", render: (r) => <span className="text-xs italic">{r.featured_request_note || "—"}</span> },
                ]}
                actions={(r) => (
                  <>
                    <a href={`/discover/${r.discover_slug}`} target="_blank" rel="noopener noreferrer"
                       className="btn btn-ghost text-[10px]" data-testid={`feat-preview-${r.id}`}>
                      <ExternalLink className="w-3 h-3"/>
                    </a>
                    <button onClick={() => approveFeature(r.id)}
                            className="btn btn-primary text-[10px]"
                            data-testid={`feat-approve-${r.id}`}>
                      <Star className="w-3 h-3"/> Feature
                    </button>
                  </>
                )}
                testid="admin-table-featured"/>
      )}

      {tab === "roadmap" && (
        <RoadmapEditor rows={roadmap} onReload={reload}/>
      )}

      {threadFlag && (
        <FlagThreadDrawer flag={threadFlag}
                          onClose={() => setThreadFlag(null)}
                          onAction={async (status) => {
                            await reviewFlag(threadFlag.id, status);
                            setThreadFlag(null);
                          }}/>
      )}
    </div>
  );
}


// ── Roadmap Editor ────────────────────────────────────────────────
function RoadmapEditor({ rows, onReload }) {
  const [editing, setEditing] = useState(null); // item id or "new"
  const [draft, setDraft] = useState({
    title: "", body_md: "", status: "next", eta: "", order: 0, public: true,
  });
  const startNew = () => {
    setDraft({ title: "", body_md: "", status: "next", eta: "", order: 0, public: true });
    setEditing("new");
  };
  const startEdit = (item) => {
    setDraft({
      title: item.title, body_md: item.body_md || "", status: item.status,
      eta: item.eta || "", order: item.order || 0, public: item.public !== false,
    });
    setEditing(item.id);
  };
  const save = async () => {
    if (editing === "new") {
      await api.post("/admin/roadmap", draft);
    } else {
      await api.patch(`/admin/roadmap/${editing}`, draft);
    }
    setEditing(null);
    onReload();
  };
  const remove = async (rid) => {
    if (!window.confirm("Delete this roadmap item?")) return;
    await api.delete(`/admin/roadmap/${rid}`);
    onReload();
  };
  return (
    <div className="space-y-4" data-testid="admin-roadmap-editor">
      <div className="flex items-center justify-between">
        <div className="text-mist text-sm">
          Public landing reads from <code>/api/public/roadmap</code>. Items
          flagged <code>public=true</code> appear there. Markdown supported in body.
        </div>
        <button onClick={startNew} className="btn btn-primary text-xs"
                data-testid="roadmap-new-btn">+ New item</button>
      </div>

      {editing && (
        <div className="card-mystic p-4 space-y-2" data-testid="roadmap-form">
          <input className="input text-sm" value={draft.title}
                 onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                 placeholder="Title" data-testid="roadmap-title"/>
          <div className="grid grid-cols-3 gap-2">
            <select className="select text-xs" value={draft.status}
                    onChange={(e) => setDraft({ ...draft, status: e.target.value })}>
              <option value="now">now</option>
              <option value="next">next</option>
              <option value="later">later</option>
              <option value="shipped">shipped</option>
            </select>
            <input className="input text-xs" value={draft.eta}
                   onChange={(e) => setDraft({ ...draft, eta: e.target.value })}
                   placeholder="ETA (Q1, Live, —)"/>
            <input type="number" className="input text-xs" value={draft.order}
                   onChange={(e) => setDraft({ ...draft, order: Number(e.target.value) })}
                   placeholder="order"/>
          </div>
          <textarea className="input text-sm min-h-[120px] font-mono"
                    value={draft.body_md}
                    onChange={(e) => setDraft({ ...draft, body_md: e.target.value })}
                    placeholder="Markdown body — **bold**, lists, `code`, [links](#)"
                    data-testid="roadmap-body"/>
          <label className="flex items-center gap-2 text-xs text-mist">
            <input type="checkbox" checked={draft.public}
                   onChange={(e) => setDraft({ ...draft, public: e.target.checked })}/>
            Public on landing
          </label>
          <div className="flex gap-2">
            <button onClick={save} className="btn btn-primary text-xs"
                    data-testid="roadmap-save">Save</button>
            <button onClick={() => setEditing(null)} className="btn text-xs">Cancel</button>
          </div>
        </div>
      )}

      <Table rows={rows}
              cols={[
                { l: "Title", k: "title" },
                { l: "Status", render: (r) => <code className="text-[10px]">{r.status}</code> },
                { l: "ETA", k: "eta" },
                { l: "Public?", render: (r) => r.public ? "✓" : "—" },
                { l: "Order", k: "order" },
              ]}
              actions={(r) => (
                <>
                  <button onClick={() => startEdit(r)} className="btn btn-ghost text-[10px]"
                          data-testid={`roadmap-edit-${r.id}`}>Edit</button>
                  <button onClick={() => remove(r.id)} className="btn btn-danger text-[10px]"
                          data-testid={`roadmap-delete-${r.id}`}>
                    <Trash2 className="w-3 h-3"/>
                  </button>
                </>
              )}
              testid="admin-table-roadmap"/>
    </div>
  );
}


// ── Flag Thread Drawer ────────────────────────────────────────────
function FlagThreadDrawer({ flag, onClose, onAction }) {
  const [thread, setThread] = useState(null);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    try {
      const r = await api.get(`/flags/${flag.id}`);
      setThread(r.data);
    } catch { /* ignore */ }
  }, [flag.id]);
  useEffect(() => { reload(); }, [reload]);

  const send = async () => {
    if (!body.trim()) return;
    setBusy(true);
    try {
      await api.post(`/flags/${flag.id}/messages`, { body });
      setBody("");
      await reload();
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-stretch justify-end" onClick={onClose}
         data-testid="flag-thread-drawer">
      <div className="absolute inset-0 bg-void/70"/>
      <div className="relative bg-ink border-l border-gold/20 w-full max-w-lg flex flex-col"
           onClick={(e) => e.stopPropagation()}>
        <div className="px-5 py-4 border-b border-gold/10 flex items-start justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-gold/70">
              Flag thread · {flag.status}
            </div>
            <div className="text-parchment font-display tracking-wide text-sm">
              {flag.target_kind} · <code className="text-gold-bright text-[10px]">{flag.target_id.slice(0, 16)}…</code>
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost text-xs"
                  data-testid="flag-thread-close">
            <X className="w-3 h-3"/>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3"
             data-testid="flag-thread-messages">
          <div className="border-l-2 border-ember pl-3">
            <div className="text-[10px] uppercase tracking-widest text-ember">
              Original report · {flag.filed_by_name}
              <span className="text-mist/60 ml-2 normal-case">
                {(flag.filed_at || "").slice(0, 16).replace("T", " ")}
              </span>
            </div>
            <p className="text-sm text-parchment mt-1 whitespace-pre-wrap">{flag.reason}</p>
          </div>
          {thread?.messages?.map((m) => (
            <div key={m.id}
                 className={`border-l-2 pl-3 ${m.author_role === "admin" ? "border-gold" : "border-arcane"}`}
                 data-testid={`flag-message-${m.id}`}>
              <div className={`text-[10px] uppercase tracking-widest ${m.author_role === "admin" ? "text-gold-bright" : "text-arcane"}`}>
                {m.author_role === "admin" ? "Admin" : "User"} · {m.author_name}
                <span className="text-mist/60 ml-2 normal-case">
                  {(m.created_at || "").slice(0, 16).replace("T", " ")}
                </span>
              </div>
              <p className="text-sm text-parchment mt-1 whitespace-pre-wrap">{m.body}</p>
            </div>
          ))}
        </div>

        <div className="px-4 py-3 border-t border-gold/10 space-y-2">
          <textarea className="input text-sm min-h-[70px]" value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder="Reply (visible to filer and admins). Be specific — this is audit-traceable."
                    data-testid="flag-thread-reply"/>
          <div className="flex gap-2">
            <button onClick={send} disabled={busy || !body.trim()}
                    className="btn btn-primary text-xs"
                    data-testid="flag-thread-send">
              <Send className="w-3 h-3"/> {busy ? "Sending…" : "Send reply"}
            </button>
            {flag.status === "open" && (
              <>
                <button onClick={() => onAction("actioned")}
                        className="btn text-xs"
                        data-testid="flag-thread-action">
                  <CheckCircle2 className="w-3 h-3"/> Mark Actioned
                </button>
                <button onClick={() => onAction("dismissed")}
                        className="btn btn-ghost text-xs"
                        data-testid="flag-thread-dismiss">
                  <XCircle className="w-3 h-3"/> Dismiss
                </button>
              </>
            )}
          </div>
        </div>
      </div>
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
