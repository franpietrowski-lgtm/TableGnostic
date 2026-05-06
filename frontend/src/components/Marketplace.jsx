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
import { Search, Download, Sparkles, X, Filter, Globe, Lock, DollarSign } from "lucide-react";

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

  const fetchRows = async () => {
    setBusy(true); setErr("");
    try {
      const params = new URLSearchParams();
      if (filter.kind) params.set("kind", filter.kind);
      if (filter.system) params.set("system", filter.system);
      if (filter.q) params.set("q", filter.q);
      if (filter.access) params.set("access", filter.access);
      params.set("skip", skip);
      const { data } = await api.get(`/marketplace?${params.toString()}`);
      setRows(data.rows || []);
      setTotal(data.total || 0);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  };

  useEffect(() => { fetchRows(); /* eslint-disable-line */ }, [filter.kind, filter.system, filter.access, skip]);
  useEffect(() => {
    api.get("/campaigns").then((r) => setCampaigns(
      (r.data || []).filter((c) => c.is_gm))).catch(() => setCampaigns([]));
  }, []);

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
        <div className="text-[11px] text-mist/70 font-ui uppercase tracking-widest">
          {busy ? "Browsing…" : `${total} listing${total === 1 ? "" : "s"}`}
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
                                       campaigns={campaigns}/>)}
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
    </div>
  );
}


function ListingCard({ row, onOpen, onAfter, campaigns }) {
  const a = ACCESS_BADGE[row.access] || ACCESS_BADGE.public;
  const Icon = a.icon;
  return (
    <div className="card-mystic p-4 flex flex-col gap-2 min-h-[180px]"
         data-testid={`marketplace-listing-${row.id}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="tag flex-shrink-0">{KIND_LABELS[row.kind] || row.kind}</span>
        <span className={`tag border ${a.tone} flex items-center gap-1 flex-shrink-0`}>
          <Icon className="w-3 h-3"/> {a.label}
        </span>
      </div>
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
      <div className="flex justify-end gap-2">
        <CloneButton listing={row} campaigns={campaigns} onAfter={onAfter}/>
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
