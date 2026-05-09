/**
 * Marketplace — V6.25.5
 *
 * Cross-table browse + clone of homebrew Custom Rules entries.
 *
 * Three states:
 *   • Browse (default) — paginated grid with kind / system / search /
 *     access filters. Each card shows kind, name, summary, source
 *     system, and a "Clone into…" affordance.
 *   • Detail (modal) — full snapshot view with effects breakdown.
 *   • Clone — pick a target campaign you GM, click Clone. The listing
 *     downloads count increments server-side.
 *
 * Mobile-aware (V6.25.5 sweep): cards collapse to single column on
 * <640 px; filter row stacks; touch targets ≥ 44 px.
 */
import React, { useEffect, useState, useMemo } from "react";
import { api } from "../lib/api";
import { Search, Download, Sparkles, X, Filter, Globe, Lock, DollarSign, Bell, BellPlus, ShieldAlert, Undo2 } from "lucide-react";

const SYSTEM_LABELS = {
  "besm-4e": "BESM 4E",
  "anime-5e": "Anime 5E",
  "dnd-5e": "D&D 5E",
  "cypher": "Cypher",
};

const KIND_LABELS = {
  race: "Race", class: "Class", size: "Size", stat: "Stat",
  attribute: "Attribute", skill: "Skill", defect: "Defect",
  feat: "Feat", trait: "Trait", feature: "Feature",
  descriptor: "Descriptor", focus: "Focus", ability: "Type/Ability",
  cypher: "Cypher", artifact: "Artifact", house: "House Rule",
  weapon: "Weapon", armor: "Armor", item: "Item", spell: "Spell",
  power_pack: "Power Pack", power_bundle: "Power Bundle",
};

const ACCESS_BADGE = {
  public:   { label: "Public", icon: Globe,      tone: "text-arcane-light border-arcane/40" },
  paywall:  { label: "Paywall (V2)", icon: DollarSign, tone: "text-gold-bright border-gold/40" },
  private:  { label: "Private", icon: Lock,      tone: "text-mist border-mist/30" },
};

export default function Marketplace() {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(true);
  const [err, setErr] = useState("");
  const [filter, setFilter] = useState({ kind: "", system: "", q: "", access: "" });
  const [skip, setSkip] = useState(0);
  const [detail, setDetail] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  // V6.25.6 — subscription digest. Polled lazily on mount; the bell
  // shows total_new count and opens an inline drawer.
  const [digest, setDigest] = useState({ buckets: [], total_new: 0 });
  const [showDigest, setShowDigest] = useState(false);
  const [subs, setSubs] = useState([]);
  // V6.25.31 — admin takedown UI.
  const [me, setMe] = useState(null);
  const [showRemoved, setShowRemoved] = useState(false);
  const [takedownFor, setTakedownFor] = useState(null);
  useEffect(() => {
    api.get("/auth/me").then((r) => setMe(r.data)).catch(() => setMe(null));
  }, []);
  const isAdmin = me?.role === "admin";

  const fetchRows = async () => {
    setBusy(true); setErr("");
    try {
      const params = new URLSearchParams();
      if (filter.kind) params.set("kind", filter.kind);
      if (filter.system) params.set("system", filter.system);
      if (filter.q) params.set("q", filter.q);
      if (filter.access) params.set("access", filter.access);
      if (isAdmin && showRemoved) params.set("show_removed", "true");
      params.set("skip", skip);
      const { data } = await api.get(`/marketplace?${params.toString()}`);
      setRows(data.rows || []);
      setTotal(data.total || 0);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  };

  useEffect(() => { fetchRows(); /* eslint-disable-line */ },
                  [filter.kind, filter.system, filter.access, skip,
                    showRemoved, isAdmin]);
  useEffect(() => {
    api.get("/campaigns").then((r) => setCampaigns(
      (r.data || []).filter((c) => c.is_gm))).catch(() => setCampaigns([]));
  }, []);

  // V6.25.6 — load subscriptions + digest on mount.
  const refreshDigest = async () => {
    try {
      const [d, s] = await Promise.all([
        api.get("/marketplace-digest"),
        api.get("/marketplace-subscriptions"),
      ]);
      setDigest(d.data || { buckets: [], total_new: 0 });
      setSubs(s.data || []);
    } catch { /* optional */ }
  };
  useEffect(() => { refreshDigest(); }, []);

  const subscribeFromFilter = async () => {
    if (!filter.kind && !filter.system) return;
    await api.post("/marketplace-subscriptions",
      { kind: filter.kind || null, system: filter.system || null });
    await refreshDigest();
  };
  const removeSub = async (sid) => {
    await api.delete(`/marketplace-subscriptions/${sid}`);
    await refreshDigest();
  };
  const markDigestSeen = async () => {
    await api.get("/marketplace-digest?mark_seen=true").catch(() => {});
    await refreshDigest();
    setShowDigest(false);
  };

  // Manual debounce on q so we don't hammer the search endpoint.
  useEffect(() => {
    const t = setTimeout(() => fetchRows(), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [filter.q]);

  const kindOptions = useMemo(() => Object.entries(KIND_LABELS), []);

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6" data-testid="marketplace-page">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-6">
        <div>
          <div className="label-ref">The Marketplace · cross-table sharing</div>
          <h1 className="font-display text-3xl sm:text-4xl text-parchment tracking-wide mt-1">
            Homebrew Library
          </h1>
          <p className="text-mist text-sm font-body mt-2 max-w-2xl">
            Borrow races, classes, power bundles, feats, and more from other GMs.
            Clone into one of your campaigns; future edits to the original
            never mutate your copy.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowDigest(true)}
                  className="relative text-mist hover:text-gold-bright p-2"
                  title="What's new in your watch list"
                  data-testid="marketplace-bell-btn"
                  aria-label="Watch list digest">
            <Bell className="w-5 h-5"/>
            {digest.total_new > 0 && (
              <span className="absolute -top-0.5 -right-0.5 bg-arcane text-parchment text-[9px]
                                rounded-full min-w-[18px] h-[18px] px-1 flex items-center justify-center font-ui"
                    data-testid="marketplace-bell-badge">
                {digest.total_new > 99 ? "99+" : digest.total_new}
              </span>
            )}
          </button>
          <div className="text-[11px] text-mist/70 font-ui uppercase tracking-widest">
            {busy ? "Browsing…" : `${total} listing${total === 1 ? "" : "s"}`}
          </div>
        </div>
      </div>

      {/* Filter bar — stacks on mobile. */}
      <div className="card-mystic p-3 sm:p-4 mb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3"
           data-testid="marketplace-filter-bar">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-mist pointer-events-none"/>
          <input className="input pl-8 w-full" placeholder="Search…"
                 value={filter.q} onChange={(e) => { setFilter({ ...filter, q: e.target.value }); setSkip(0); }}
                 data-testid="marketplace-search"/>
        </div>
        <select className="select w-full" value={filter.kind}
                onChange={(e) => { setFilter({ ...filter, kind: e.target.value }); setSkip(0); }}
                data-testid="marketplace-kind-filter">
          <option value="">All kinds</option>
          {kindOptions.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select className="select w-full" value={filter.system}
                onChange={(e) => { setFilter({ ...filter, system: e.target.value }); setSkip(0); }}
                data-testid="marketplace-system-filter">
          <option value="">All systems</option>
          {Object.entries(SYSTEM_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select className="select w-full" value={filter.access}
                onChange={(e) => { setFilter({ ...filter, access: e.target.value }); setSkip(0); }}
                data-testid="marketplace-access-filter">
          <option value="">All access</option>
          <option value="public">Public</option>
          <option value="paywall">Paywall (V2)</option>
          <option value="private">My private</option>
        </select>
      </div>

      {/* Watch-this-filter quick action */}
      {(filter.kind || filter.system) && (
        <div className="mb-3 flex items-center justify-end">
          <button onClick={subscribeFromFilter} className="btn btn-ghost text-xs"
                  data-testid="marketplace-watch-btn"
                  title="Subscribe so you get a digest when new listings match this filter.">
            <BellPlus className="w-3 h-3"/> Watch
            {filter.kind ? ` ${KIND_LABELS[filter.kind] || filter.kind}` : ""}
            {filter.system ? ` · ${SYSTEM_LABELS[filter.system] || filter.system}` : ""}
          </button>
        </div>
      )}

      {/* V6.25.31 — Admin takedown review queue toggle. */}
      {isAdmin && (
        <div className="mb-3 flex items-center justify-end gap-2 text-xs"
             data-testid="marketplace-admin-row">
          <ShieldAlert className="w-3 h-3 text-ember"/>
          <span className="text-ember tracking-widest uppercase font-ui">Admin</span>
          <button onClick={() => { setShowRemoved(false); setSkip(0); }}
                  className={`px-2 py-1 rounded-sm border ${!showRemoved
                    ? "bg-gold/15 text-gold-bright border-gold"
                    : "border-gold/20 text-mist hover:bg-gold/5"}`}
                  data-testid="admin-tab-live">Live</button>
          <button onClick={() => { setShowRemoved(true); setSkip(0); }}
                  className={`px-2 py-1 rounded-sm border ${showRemoved
                    ? "bg-ember/15 text-ember border-ember"
                    : "border-ember/30 text-mist hover:bg-ember/5"}`}
                  data-testid="admin-tab-removed">Removed</button>
          <a href="/legal/takedowns" target="_blank" rel="noreferrer"
             className="text-mist/70 underline hover:text-gold-bright"
             data-testid="admin-tab-audit">
            Audit log →
          </a>
        </div>
      )}

      {err && <div className="card-mystic p-3 mb-3 border-ember/40 text-ember text-sm" data-testid="marketplace-error">{err}</div>}
      {!busy && rows.length === 0 && (
        <div className="card-mystic p-8 text-center" data-testid="marketplace-empty">
          <Sparkles className="w-8 h-8 mx-auto text-mist/40 mb-2"/>
          <div className="text-mist font-body italic">Nothing matches yet.</div>
          <div className="text-[11px] text-mist/60 mt-1">
            Try clearing filters — or be the first to publish! Open any campaign's
            Custom Rules tab and use the share icon next to a homebrew entry.
          </div>
        </div>
      )}

      {/* Cards grid — 1 col mobile, 2 col tablet, 3 col desktop. */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4"
           data-testid="marketplace-grid">
        {rows.map((r) => <ListingCard key={r.id} row={r}
                                       onOpen={() => setDetail(r)}
                                       onAfter={fetchRows}
                                       campaigns={campaigns}
                                       isAdmin={isAdmin}
                                       onTakedown={() => setTakedownFor(r)}
                                       onRestore={async () => {
                                         await api.post(`/marketplace/${r.id}/restore`);
                                         fetchRows();
                                       }}/>)}
      </div>

      {total > rows.length + skip && (
        <div className="text-center mt-6">
          <button className="btn btn-ghost" onClick={() => setSkip(skip + 40)}
                  data-testid="marketplace-load-more">
            Load more…
          </button>
        </div>
      )}

      {detail && (
        <ListingDetailModal listing={detail} campaigns={campaigns}
                              onClose={() => setDetail(null)}
                              onAfter={fetchRows}/>
      )}

      {takedownFor && (
        <TakedownModal listing={takedownFor}
                          onClose={() => setTakedownFor(null)}
                          onDone={async () => {
                            setTakedownFor(null);
                            await fetchRows();
                          }}/>
      )}

      {showDigest && (
        <div className="fixed inset-0 z-50 bg-void/80 flex items-start justify-end p-3 sm:p-6"
             onClick={() => setShowDigest(false)}
             data-testid="marketplace-digest-drawer">
          <div className="card-mystic p-5 w-full sm:w-96 max-h-[88vh] overflow-y-auto"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="label-ref">Watch list</div>
                <div className="font-display text-xl text-parchment mt-1">
                  {digest.total_new > 0 ? `${digest.total_new} new` : "All caught up"}
                </div>
              </div>
              <button onClick={() => setShowDigest(false)} className="text-mist hover:text-gold-bright p-1"
                      aria-label="Close" data-testid="marketplace-digest-close">
                <X className="w-4 h-4"/>
              </button>
            </div>
            {subs.length === 0 && (
              <div className="text-[11px] text-mist italic" data-testid="marketplace-digest-empty">
                You aren't watching any filters yet. Pick a kind or system above
                and tap <BellPlus className="w-3 h-3 inline"/> Watch.
              </div>
            )}
            {digest.buckets.map((b) => (
              <div key={b.subscription_id} className="border-t border-gold/10 pt-2 mt-2"
                   data-testid={`marketplace-digest-bucket-${b.subscription_id}`}>
                <div className="flex items-center justify-between">
                  <div className="text-[11px] font-ui uppercase tracking-widest text-gold/60">
                    {b.label || `${b.kind || "any"} · ${b.system || "any"}`}
                  </div>
                  <button onClick={() => removeSub(b.subscription_id)}
                          className="text-mist/40 hover:text-ember p-0.5"
                          title="Stop watching"
                          data-testid={`marketplace-digest-unsub-${b.subscription_id}`}>
                    <X className="w-3 h-3"/>
                  </button>
                </div>
                {b.new_count === 0 ? (
                  <div className="text-[10px] text-mist/60 italic mt-1">No new listings.</div>
                ) : (
                  <ul className="mt-1.5 space-y-1">
                    {b.preview.map((row) => (
                      <li key={row.id}>
                        <button onClick={() => { setDetail(row); setShowDigest(false); }}
                                className="text-left w-full py-1 px-1.5 rounded-sm hover:bg-gold/5 transition-colors"
                                data-testid={`marketplace-digest-item-${row.id}`}>
                          <div className="text-parchment text-sm leading-snug">{row.name}</div>
                          <div className="text-[10px] text-mist/70 font-ui uppercase tracking-widest">
                            {KIND_LABELS[row.kind] || row.kind} · {SYSTEM_LABELS[row.source_system_id] || row.source_system_id}
                          </div>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
            <div className="mt-4 flex justify-end gap-2">
              <button onClick={markDigestSeen} className="btn btn-primary text-xs"
                      data-testid="marketplace-digest-mark-seen">
                Mark all seen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


function ListingCard({ row, onOpen, onAfter, campaigns,
                         isAdmin, onTakedown, onRestore }) {
  const a = ACCESS_BADGE[row.access] || ACCESS_BADGE.public;
  const Icon = a.icon;
  const removed = !!row.removed;
  return (
    <div className={`card-mystic p-4 flex flex-col gap-2 min-h-[180px] ${
                        removed ? "opacity-60 border-ember/40" : ""}`}
         data-testid={`marketplace-listing-${row.id}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="tag flex-shrink-0">{KIND_LABELS[row.kind] || row.kind}</span>
        <span className={`tag border ${a.tone} flex items-center gap-1 flex-shrink-0`}>
          <Icon className="w-3 h-3"/> {a.label}
        </span>
      </div>
      {removed && (
        <div className="border border-ember/40 rounded-sm p-1.5 bg-ember/5"
             data-testid={`marketplace-listing-removed-${row.id}`}>
          <div className="text-[10px] uppercase tracking-widest text-ember font-ui flex items-center gap-1">
            <ShieldAlert className="w-3 h-3"/> Removed by admin
            {row.takedown_policy && (
              <span className="text-mist normal-case tracking-normal">
                · {row.takedown_policy}
              </span>
            )}
          </div>
          {row.takedown_reason && (
            <div className="text-[10px] text-mist italic line-clamp-2 mt-0.5">
              {row.takedown_reason}
            </div>
          )}
        </div>
      )}
      <button onClick={onOpen}
              className="text-left font-display text-lg text-parchment hover:text-gold-bright transition-colors leading-tight"
              data-testid={`marketplace-listing-name-${row.id}`}>
        {row.name}
      </button>
      <div className="text-[11px] text-mist line-clamp-3 font-body flex-1">
        {row.summary || <span className="italic">No summary.</span>}
      </div>
      <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-mist/60 font-ui">
        <span>{SYSTEM_LABELS[row.source_system_id] || row.source_system_id || "—"}</span>
        <span className="flex items-center gap-1">
          <Download className="w-3 h-3"/> {row.downloads}
        </span>
      </div>
      <div className="flex justify-end gap-2 flex-wrap">
        {isAdmin && !removed && (
          <button onClick={onTakedown}
                  className="btn btn-ghost text-[10px] text-ember"
                  data-testid={`marketplace-takedown-${row.id}`}
                  title="Admin: remove this listing for policy / IP violation.">
            <ShieldAlert className="w-3 h-3"/> Takedown
          </button>
        )}
        {isAdmin && removed && (
          <button onClick={onRestore}
                  className="btn btn-ghost text-[10px] text-gold-bright"
                  data-testid={`marketplace-restore-${row.id}`}
                  title="Admin: restore this listing.">
            <Undo2 className="w-3 h-3"/> Restore
          </button>
        )}
        {!removed && (
          <CloneButton listing={row} campaigns={campaigns} onAfter={onAfter}/>
        )}
      </div>
    </div>
  );
}


function CloneButton({ listing, campaigns, onAfter, label = "Clone" }) {
  const [picking, setPicking] = useState(false);
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  const submit = async () => {
    if (!target) return;
    setBusy(true); setErr("");
    try {
      await api.post(`/marketplace/${listing.id}/clone`,
        { into_campaign_id: target });
      setDone(true);
      if (onAfter) await onAfter();
      setTimeout(() => { setPicking(false); setDone(false); setTarget(""); }, 1600);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  };

  if (done) return (
    <span className="text-arcane-light text-[11px] font-ui uppercase tracking-widest"
          data-testid={`marketplace-clone-success-${listing.id}`}>
      ✓ Cloned
    </span>
  );

  if (!picking) return (
    <button onClick={() => setPicking(true)}
            className="btn btn-ghost text-xs flex items-center gap-1"
            data-testid={`marketplace-clone-btn-${listing.id}`}>
      <Download className="w-3 h-3"/> {label}
    </button>
  );

  return (
    <div className="flex flex-col sm:flex-row gap-1.5 items-end w-full"
         data-testid={`marketplace-clone-row-${listing.id}`}>
      <select className="select select-sm flex-1 min-w-0" value={target}
              onChange={(e) => setTarget(e.target.value)}
              data-testid={`marketplace-clone-target-${listing.id}`}>
        <option value="">— pick your campaign —</option>
        {campaigns.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name} · {SYSTEM_LABELS[c.system_id] || c.system_id}
          </option>
        ))}
      </select>
      <div className="flex gap-1">
        <button onClick={() => { setPicking(false); setTarget(""); setErr(""); }}
                className="btn btn-ghost text-xs"
                data-testid={`marketplace-clone-cancel-${listing.id}`}>
          <X className="w-3 h-3"/>
        </button>
        <button onClick={submit} disabled={!target || busy}
                className="btn btn-primary text-xs"
                data-testid={`marketplace-clone-submit-${listing.id}`}>
          {busy ? "…" : "Go"}
        </button>
      </div>
      {err && <span className="text-ember text-[10px] basis-full">{err}</span>}
    </div>
  );
}


function ListingDetailModal({ listing, campaigns, onClose, onAfter }) {
  const a = ACCESS_BADGE[listing.access] || ACCESS_BADGE.public;
  const Icon = a.icon;
  const eff = listing.snapshot?.effects || {};
  const fields = listing.snapshot?.fields || {};
  return (
    <div className="fixed inset-0 z-50 bg-void/85 flex items-start justify-center p-3 sm:p-6 overflow-y-auto"
         onClick={onClose}
         data-testid="marketplace-detail-modal">
      <div className="card-mystic p-5 sm:p-7 max-w-2xl w-full my-6"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-3 mb-2">
          <div>
            <span className="tag mr-2">{KIND_LABELS[listing.kind] || listing.kind}</span>
            <span className={`tag border ${a.tone} inline-flex items-center gap-1`}>
              <Icon className="w-3 h-3"/> {a.label}
            </span>
          </div>
          <button onClick={onClose} className="text-mist hover:text-gold-bright p-1"
                  data-testid="marketplace-detail-close" aria-label="Close">
            <X className="w-4 h-4"/>
          </button>
        </div>
        <h2 className="font-display text-2xl sm:text-3xl text-parchment leading-tight">
          {listing.name}
        </h2>
        <div className="text-[11px] text-mist/70 uppercase tracking-widest font-ui mt-1">
          {SYSTEM_LABELS[listing.source_system_id] || listing.source_system_id} ·
          by {listing.source_owner_name || "anon GM"} ·
          <Download className="w-3 h-3 inline mx-1"/> {listing.downloads}
        </div>
        {listing.summary && (
          <p className="text-mist text-sm font-body mt-3 whitespace-pre-wrap">
            {listing.summary}
          </p>
        )}
        {listing.snapshot?.description_note && (
          <div className="mt-4 border-l-2 border-gold/30 pl-3 text-[12px] text-parchment/85 whitespace-pre-wrap">
            {listing.snapshot.description_note}
          </div>
        )}
        {/* Effects breakdown — BESM-style and DnD-style. */}
        {Object.keys(eff).length > 0 && (
          <div className="mt-4 border-t border-gold/15 pt-3 text-[12px]">
            <div className="label-ref mb-2">Mechanics</div>
            {eff.stat_adjustments && (
              <div>Stat adj.:
                {" "}{["body","mind","soul"]
                  .filter((k) => (eff.stat_adjustments[k] ?? 0) !== 0)
                  .map((k) => `${k[0].toUpperCase()+k.slice(1)} ${eff.stat_adjustments[k] > 0 ? "+" : ""}${eff.stat_adjustments[k]}`)
                  .join(" / ") || "—"}
              </div>
            )}
            {eff.asi && Object.keys(eff.asi).length > 0 && (
              <div>ASI: {Object.entries(eff.asi).map(([k,v]) => `${k} ${v>0?"+":""}${v}`).join(" / ")}</div>
            )}
            {eff.size && <div>Size: {eff.size}</div>}
            {eff.speed && <div>Speed: {eff.speed} ft</div>}
            {eff.traits?.length > 0 && <div>Traits: {eff.traits.join(", ")}</div>}
            {eff.components?.length > 0 && (
              <div className="mt-2">
                <span className="text-gold/60 uppercase tracking-widest text-[9px]">Components ({eff.components.length})</span>
                <ul className="list-disc list-inside mt-1 space-y-0.5">
                  {eff.components.slice(0, 12).map((c, i) => (
                    <li key={i} className="text-parchment/85">
                      <span className="text-mist/60">{c.kind}:</span> {c.name}
                      {c.level != null && ` · L${c.level}`}
                      {c.rank != null && ` · R${c.rank}`}
                    </li>
                  ))}
                  {eff.components.length > 12 && (
                    <li className="text-mist/60 italic">… and {eff.components.length - 12} more</li>
                  )}
                </ul>
              </div>
            )}
            {typeof eff.total_cp === "number" && (
              <div className="mt-2 text-gold-bright">Total: {eff.total_cp} CP</div>
            )}
          </div>
        )}
        {Object.keys(fields).length > 0 && (
          <div className="mt-4 border-t border-gold/15 pt-3 text-[12px]">
            <div className="label-ref mb-2">Reference fields</div>
            <pre className="text-[11px] text-mist/80 whitespace-pre-wrap font-mono">
              {JSON.stringify(fields, null, 2)}
            </pre>
          </div>
        )}
        {listing.license_text && (
          <div className="mt-4 text-[10px] text-mist/60 italic border-t border-gold/10 pt-2">
            License: {listing.license_text}
          </div>
        )}
        <div className="mt-5 flex justify-end">
          <CloneButton listing={listing} campaigns={campaigns} onAfter={onAfter}
                        label="Clone into campaign…"/>
        </div>
      </div>
    </div>
  );
}




// ────────────────────────────────────────────────────────────────────
// V6.25.31 — Admin Takedown modal.
// Captures the policy bucket + plain-English reason so the public
// audit log at /api/legal/takedowns can render it for transparency.
// ────────────────────────────────────────────────────────────────────
const TAKEDOWN_POLICIES = [
  { id: "piracy",                  label: "Piracy / unauthorised reproduction" },
  { id: "lore-export",             label: "System lore export beyond CC/SRD" },
  { id: "artwork",                 label: "Artwork copyright violation" },
  { id: "system-creator-rules",    label: "System creator's licensing rules" },
  { id: "community-rules",         label: "Community / app TOS violation" },
  { id: "other",                   label: "Other (specify in reason)" },
];

function TakedownModal({ listing, onClose, onDone }) {
  const [policy, setPolicy] = useState("piracy");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async () => {
    if (reason.trim().length < 4) {
      setErr("A short reason is required (visible in the public audit log).");
      return;
    }
    setBusy(true); setErr("");
    try {
      await api.post(`/marketplace/${listing.id}/takedown`,
                       { policy, reason: reason.trim() });
      if (onDone) await onDone();
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-50 bg-void/85 flex items-center justify-center p-4"
         onClick={onClose}
         data-testid="marketplace-takedown-modal">
      <div className="card-mystic p-5 w-full max-w-md space-y-3"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <div>
            <div className="label-ref text-ember flex items-center gap-1">
              <ShieldAlert className="w-3 h-3"/> Admin takedown
            </div>
            <div className="font-display text-lg text-parchment mt-1">
              {listing.name}
            </div>
          </div>
          <button onClick={onClose} className="touch-target text-mist hover:text-parchment">
            <X className="w-4 h-4"/>
          </button>
        </div>
        <div>
          <div className="label-ref">Policy bucket</div>
          <select className="select w-full mt-1" value={policy}
                  onChange={(e) => setPolicy(e.target.value)}
                  data-testid="takedown-policy">
            {TAKEDOWN_POLICIES.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </div>
        <div>
          <div className="label-ref">Reason</div>
          <textarea className="input w-full text-sm mt-1" rows={4}
                     value={reason} onChange={(e) => setReason(e.target.value)}
                     placeholder="Plain-English statement of the violation. Visible to the listing owner and on the public audit log at /legal/takedowns."
                     data-testid="takedown-reason"/>
        </div>
        {err && <div className="text-ember text-xs"
                       data-testid="takedown-error">{err}</div>}
        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
          <button onClick={submit} disabled={busy}
                  className="btn btn-primary text-xs"
                  data-testid="takedown-submit">
            {busy ? "Removing…" : "Remove listing"}
          </button>
        </div>
      </div>
    </div>
  );
}
