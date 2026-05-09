import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, ArrowRight, Search, Loader2 } from "lucide-react";
import Sigil from "./landing/Sigil";
import LandingFooter from "./landing/LandingFooter";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SYSTEM_FILTERS = [
  { id: "", label: "All systems" },
  { id: "besm-4e", label: "BESM 4E" },
  { id: "anime-5e", label: "Anime 5E" },
  { id: "cypher", label: "Cypher" },
  { id: "dnd-5e", label: "D&D 5E" },
];

/**
 * DiscoverBrowse — public gallery listing every campaign whose GM has
 * toggled discover_published. No auth required. Each card links to
 * /discover/{slug} where the full showcase lives.
 */
export default function DiscoverBrowse() {
  const [items, setItems] = useState(null);
  const [system, setSystem] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = "Public Tables — TableGnostics Discover";
  }, []);

  useEffect(() => {
    let cancel = false;
    setLoading(true);
    const params = new URLSearchParams();
    if (system) params.set("system", system);
    if (q.trim()) params.set("q", q.trim());
    axios
      .get(`${API}/public/discover?${params.toString()}`)
      .then((r) => !cancel && setItems(r.data.items || []))
      .catch(() => !cancel && setItems([]))
      .finally(() => !cancel && setLoading(false));
    return () => {
      cancel = true;
    };
  }, [system, q]);

  return (
    <div className="page min-h-screen relative" data-testid="browse-root">
      <header className="px-5 md:px-10 py-5 border-b border-gold/10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/discover" className="flex items-center gap-3 group" data-testid="browse-brand">
            <Sigil size={32} />
            <div>
              <div className="font-display tracking-[0.3em] text-sm text-parchment group-hover:text-gold-bright transition-colors">
                TABLE<span className="text-gold">·</span>GNOSTIC
              </div>
              <div className="text-[9px] font-ui tracking-[0.3em] uppercase text-gold/55">
                public tables
              </div>
            </div>
          </Link>
          <Link
            to="/auth?mode=register"
            className="btn btn-primary text-xs"
            data-testid="browse-topbar-cta"
          >
            Begin the Rite <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-5 md:px-10 py-12 md:py-20">
        <Link
          to="/discover"
          className="inline-flex items-center gap-2 text-[11px] font-ui tracking-[0.22em] uppercase text-mist/65 hover:text-gold transition-colors mb-6"
          data-testid="browse-back-landing"
        >
          <ArrowLeft className="w-3 h-3" /> Back to landing
        </Link>

        <div className="label-ref mb-3">Public tables · live showcase</div>
        <h1 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
          Every world a <span className="text-gold italic font-body normal-case">door.</span>
        </h1>
        <p className="mt-6 max-w-2xl text-mist text-base md:text-lg font-body leading-relaxed">
          GMs can publish their campaign as a public TableGnostics showcase —
          codex graph, marketplace listings, and canon registry, all visible
          without an account. Clone any of them into your own table.
        </p>

        {/* Filters */}
        <div className="mt-10 flex flex-col md:flex-row gap-3 md:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gold/65 pointer-events-none" />
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search by name, blurb, tag…"
              className="input pl-9"
              data-testid="browse-search"
            />
          </div>
          <select
            value={system}
            onChange={(e) => setSystem(e.target.value)}
            className="select md:w-56"
            data-testid="browse-filter-system"
          >
            {SYSTEM_FILTERS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Grid */}
        <div className="mt-10">
          {loading && (
            <div className="text-center py-16" data-testid="browse-loading">
              <Loader2 className="w-7 h-7 text-gold animate-spin mx-auto" />
              <div className="mt-4 text-[11px] font-ui tracking-[0.3em] uppercase text-gold/60">
                Gathering tables…
              </div>
            </div>
          )}

          {!loading && items?.length === 0 && (
            <div className="card-mystic p-10 text-center" data-testid="browse-empty">
              <div className="font-display text-lg text-parchment uppercase tracking-widest">
                No tables yet.
              </div>
              <p className="mt-3 text-sm text-mist font-body max-w-md mx-auto">
                Be the first GM to publish a public showcase. Toggle{" "}
                <code className="text-gold-bright font-mono">discover_published</code> on
                your campaign and your world is here.
              </p>
              <Link
                to="/auth?mode=register"
                className="mt-7 btn btn-primary px-5 py-2.5 text-sm"
                data-testid="browse-empty-cta"
              >
                Begin the Rite <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}

          {!loading && items && items.length > 0 && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="browse-grid">
              {items.map((c) => (
                <ShowcaseCard key={c.slug} c={c} />
              ))}
            </div>
          )}
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}

function ShowcaseCard({ c }) {
  return (
    <Link
      to={`/discover/${c.slug}`}
      className="card-mystic p-5 transition-all duration-500 hover:-translate-y-1 group block"
      data-testid={`browse-card-${c.slug}`}
    >
      <div className="text-[10px] font-ui tracking-widest uppercase text-gold/70">
        {c.system || c.system_id}
        {c.canon_published && <span className="ml-2 text-arcane">canon</span>}
      </div>
      <div className="mt-2 font-display text-lg text-parchment leading-tight uppercase tracking-tight group-hover:text-gold-bright transition-colors">
        {c.name}
      </div>
      {c.blurb && (
        <p className="mt-3 text-sm text-mist font-body leading-relaxed line-clamp-4">
          {c.blurb}
        </p>
      )}
      <div className="mt-5 flex flex-wrap gap-1.5">
        {(c.tags || []).slice(0, 4).map((t) => (
          <span
            key={t}
            className="text-[9px] font-ui tracking-widest uppercase text-mist/65 border border-gold/15 rounded-sm px-1.5 py-0.5"
          >
            {t}
          </span>
        ))}
      </div>
      <div className="mt-5 pt-4 border-t border-gold/10 flex items-center justify-between text-[10px] font-mono">
        <span className="text-mist/70">GM · {c.gm_name}</span>
        <span className="text-gold-bright">
          {c.marketplace_count} {c.marketplace_count === 1 ? "listing" : "listings"}
        </span>
      </div>
    </Link>
  );
}
