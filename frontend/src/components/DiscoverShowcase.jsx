import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ArrowRight, ArrowLeft, Globe2, Network, Store, BookOpen,
  Crown, Tag, Sparkles, Loader2, AlertCircle, Copy,
} from "lucide-react";
import Sigil from "./landing/Sigil";
import LandingFooter from "./landing/LandingFooter";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const NODE_ICONS = {
  npc: Crown,
  faction: Network,
  location: Globe2,
  lore: BookOpen,
  quest: Sparkles,
};

/**
 * DiscoverShowcase — public showcase for a single published campaign at
 * /discover/:slug. Renders without auth so search engines & cold visitors
 * can browse a GM's world before committing.
 *
 * Tabs: World (shared codex nodes + simple list view) | Marketplace
 * (listings sourced from this campaign) | Canon (registry summary).
 *
 * Primary CTA: "Begin the Rite to clone or join" → /auth?mode=register.
 */
export default function DiscoverShowcase() {
  const { slug } = useParams();
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("world");

  useEffect(() => {
    let cancel = false;
    setData(null);
    setError("");
    axios
      .get(`${API}/public/discover/${slug}`)
      .then((r) => {
        if (!cancel) setData(r.data);
      })
      .catch((err) => {
        if (cancel) return;
        if (err?.response?.status === 404) {
          setError("This showcase isn't published, or the link is wrong.");
        } else {
          setError("Couldn't load this showcase. Try again in a moment.");
        }
      });
    return () => {
      cancel = true;
    };
  }, [slug]);

  // Document title + meta for SEO when data lands.
  useEffect(() => {
    const prev = document.title;
    if (data?.campaign?.name) {
      document.title = `${data.campaign.name} — TableGnostics Showcase`;
      const setMeta = (name, content, kind = "name") => {
        let el = document.querySelector(`meta[${kind}="${name}"]`);
        if (!el) {
          el = document.createElement("meta");
          el.setAttribute(kind, name);
          document.head.appendChild(el);
        }
        el.setAttribute("content", content);
      };
      const desc = (data.campaign.blurb
        || `${data.campaign.name} — a public TableGnostics campaign showcase.`).slice(0, 220);
      const ogImage = `${process.env.REACT_APP_BACKEND_URL}/api/seo/og/${slug}.svg`;
      const ogUrl = `https://tablegnostic.com/discover/${slug}`;
      setMeta("description", desc);
      // V6.25.41 — Open Graph tags so Discord/FB/Twitter/LinkedIn unfurl
      // every showcase with a proper sigil card.
      setMeta("og:title", `${data.campaign.name} — TableGnostics`, "property");
      setMeta("og:description", desc, "property");
      setMeta("og:image", ogImage, "property");
      setMeta("og:url", ogUrl, "property");
      setMeta("og:type", "website", "property");
      setMeta("twitter:card", "summary_large_image");
      setMeta("twitter:title", `${data.campaign.name} — TableGnostics`);
      setMeta("twitter:description", desc);
      setMeta("twitter:image", ogImage);
    }
    return () => {
      document.title = prev;
    };
  }, [data, slug]);

  if (error) {
    return (
      <ShowcaseShell>
        <div className="max-w-2xl mx-auto card-mystic p-8 text-center" data-testid="showcase-error">
          <AlertCircle className="w-10 h-10 text-ember mx-auto mb-4" />
          <h1 className="font-display text-2xl text-parchment uppercase tracking-widest">
            Showcase not found
          </h1>
          <p className="mt-3 text-sm text-mist font-body leading-relaxed">{error}</p>
          <div className="mt-7 flex gap-3 justify-center">
            <Link to="/discover" className="btn px-5 py-2.5 text-sm" data-testid="showcase-back-landing">
              <ArrowLeft className="w-4 h-4" /> Back to Discover
            </Link>
            <Link to="/discover/browse" className="btn btn-primary px-5 py-2.5 text-sm" data-testid="showcase-back-browse">
              Browse public tables <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </ShowcaseShell>
    );
  }

  if (!data) {
    return (
      <ShowcaseShell>
        <div className="text-center py-20" data-testid="showcase-loading">
          <Loader2 className="w-7 h-7 text-gold animate-spin mx-auto" />
          <div className="mt-4 text-[11px] font-ui tracking-[0.3em] uppercase text-gold/60">
            Unfolding the table…
          </div>
        </div>
      </ShowcaseShell>
    );
  }

  const c = data.campaign;
  const tabs = [
    { id: "world", label: "World", count: data.stats.node_count, icon: Globe2 },
    { id: "marketplace", label: "Marketplace", count: data.stats.marketplace_count, icon: Store },
    { id: "canon", label: "Canon", count: data.canon.published ? "✓" : "—", icon: BookOpen },
  ];

  return (
    <ShowcaseShell>
      {/* HERO */}
      <header className="max-w-6xl mx-auto px-5 md:px-10 pt-8 pb-12 md:pb-16" data-testid="showcase-hero">
        <Link
          to="/discover/browse"
          className="inline-flex items-center gap-2 text-[11px] font-ui tracking-[0.22em] uppercase text-mist/65 hover:text-gold transition-colors"
          data-testid="showcase-breadcrumb"
        >
          <ArrowLeft className="w-3 h-3" /> All public tables
        </Link>

        <div className="mt-6 grid lg:grid-cols-[1fr_auto] gap-8 items-end">
          <div>
            <div className="label-ref mb-3" data-testid="showcase-system">
              {c.system || c.system_id} {c.power_level && `· ${c.power_level}`}
              {c.setting_name && ` · ${c.setting_name}`}
            </div>
            <h1
              className="font-display text-[clamp(2.4rem,5vw,4.5rem)] leading-[1] uppercase tracking-tight text-parchment"
              data-testid="showcase-name"
            >
              {c.name}
            </h1>
            {c.blurb && (
              <p className="mt-6 max-w-2xl text-lg font-body leading-relaxed text-mist" data-testid="showcase-blurb">
                {c.blurb}
              </p>
            )}
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <div className="text-[11px] font-ui tracking-[0.22em] uppercase text-gold/70" data-testid="showcase-gm">
                GM · <span className="text-gold-bright">{c.gm_name || "Unknown"}</span>
              </div>
              {c.tone && <Pill>{c.tone}</Pill>}
              {c.genre && <Pill>{c.genre}</Pill>}
              {c.canon_published && <Pill accent="arcane">Canon Registry</Pill>}
            </div>
            {c.tags?.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1.5" data-testid="showcase-tags">
                {c.tags.slice(0, 8).map((t) => (
                  <span
                    key={t}
                    className="text-[10px] font-ui tracking-[0.18em] uppercase text-mist/70 border border-gold/15 rounded-sm px-2 py-0.5 bg-ink/40"
                  >
                    <Tag className="inline w-2.5 h-2.5 mr-1" />
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-col items-start lg:items-end gap-3">
            <button
              onClick={() => nav("/auth?mode=register")}
              className="btn btn-primary px-6 py-3.5 text-sm"
              data-testid="showcase-cta-clone"
            >
              <Copy className="w-4 h-4" /> Begin the Rite to clone
            </button>
            <Link
              to="/auth?mode=login"
              className="btn btn-ghost px-5 py-2.5 text-xs"
              data-testid="showcase-cta-login"
            >
              I already have a seat <ArrowRight className="w-3 h-3" />
            </Link>
            <Link
              to={`/discover/${slug}/gazette`}
              className="btn btn-ghost px-5 py-2.5 text-xs"
              data-testid="showcase-cta-gazette"
            >
              Read the Gazette <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </header>

      {/* TABS */}
      <nav className="sticky top-0 z-30 bg-void/85 backdrop-blur border-y border-gold/10" data-testid="showcase-tabs">
        <div className="max-w-6xl mx-auto px-5 md:px-10 flex gap-1 overflow-x-auto scroll-stylish">
          {tabs.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`whitespace-nowrap inline-flex items-center gap-2 px-5 py-3.5 text-[11px] font-ui tracking-[0.22em] uppercase border-b-2 transition-colors ${
                  active
                    ? "border-gold text-gold-bright"
                    : "border-transparent text-mist hover:text-parchment"
                }`}
                data-testid={`showcase-tab-${t.id}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {t.label}
                <span
                  className={`ml-1 text-[10px] font-mono ${
                    active ? "text-gold-bright" : "text-mist/55"
                  }`}
                >
                  {t.count}
                </span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* CONTENT */}
      <main className="max-w-6xl mx-auto px-5 md:px-10 py-12 md:py-16">
        {tab === "world" && <WorldTab nodes={data.nodes} edges={data.edges} />}
        {tab === "marketplace" && <MarketplaceTab listings={data.marketplace} />}
        {tab === "canon" && <CanonTab canon={data.canon} gmName={c.gm_name} />}
      </main>
    </ShowcaseShell>
  );
}

function ShowcaseShell({ children }) {
  return (
    <div className="page min-h-screen relative" data-testid="showcase-root">
      <ShowcaseTopBar />
      {children}
      <LandingFooter />
    </div>
  );
}

function ShowcaseTopBar() {
  return (
    <header className="px-5 md:px-10 py-5 border-b border-gold/10">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <Link to="/discover" className="flex items-center gap-3 group" data-testid="showcase-brand">
          <Sigil size={32} />
          <div>
            <div className="font-display tracking-[0.3em] text-sm text-parchment group-hover:text-gold-bright transition-colors">
              TABLE<span className="text-gold">·</span>GNOSTIC
            </div>
            <div className="text-[9px] font-ui tracking-[0.3em] uppercase text-gold/55">
              public showcase
            </div>
          </div>
        </Link>
        <Link
          to="/auth?mode=register"
          className="btn btn-primary text-xs"
          data-testid="showcase-topbar-cta"
        >
          Begin the Rite <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </header>
  );
}

function Pill({ children, accent = "gold" }) {
  const cls = {
    gold: "border-gold/30 text-gold-bright bg-gold/5",
    arcane: "border-arcane/40 text-arcane bg-arcane/5",
  }[accent];
  return (
    <span
      className={`text-[10px] font-ui tracking-[0.22em] uppercase border rounded-sm px-2.5 py-1 ${cls}`}
    >
      {children}
    </span>
  );
}

function WorldTab({ nodes, edges }) {
  if (!nodes || nodes.length === 0) {
    return <Empty hint="The GM hasn't surfaced any public codex nodes yet." />;
  }
  // group by type
  const byType = nodes.reduce((acc, n) => {
    const t = (n.type || "lore").toLowerCase();
    (acc[t] = acc[t] || []).push(n);
    return acc;
  }, {});
  const order = ["npc", "faction", "location", "quest", "lore"];
  const types = [
    ...order.filter((t) => byType[t]),
    ...Object.keys(byType).filter((t) => !order.includes(t)),
  ];

  return (
    <div data-testid="showcase-world-tab">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="label-ref mb-2">World Codex</div>
          <h2 className="font-display text-2xl md:text-3xl text-parchment uppercase tracking-tight">
            {nodes.length} public {nodes.length === 1 ? "node" : "nodes"}
            <span className="text-mist/60 font-body italic normal-case text-base ml-3">
              · {edges.length} connection{edges.length === 1 ? "" : "s"}
            </span>
          </h2>
        </div>
      </div>

      <div className="space-y-12">
        {types.map((t) => {
          const Icon = NODE_ICONS[t] || BookOpen;
          return (
            <section key={t} data-testid={`showcase-node-group-${t}`}>
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 rounded-sm border border-gold/30 text-gold flex items-center justify-center bg-void/50">
                  <Icon className="w-4 h-4" />
                </div>
                <h3 className="font-display text-base text-parchment uppercase tracking-[0.2em]">
                  {t}
                </h3>
                <span className="text-[10px] font-mono text-mist/55">
                  {byType[t].length}
                </span>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {byType[t].map((n) => (
                  <article
                    key={n.id}
                    className="card-mystic p-5"
                    data-testid={`showcase-node-${n.id}`}
                  >
                    <div className="font-display text-base text-parchment leading-tight">
                      {n.title}
                    </div>
                    {n.content && (
                      <p className="mt-3 text-sm text-mist font-body leading-relaxed line-clamp-6 whitespace-pre-line">
                        {n.content}
                      </p>
                    )}
                    {n.tags?.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-1">
                        {n.tags.slice(0, 5).map((tg) => (
                          <span
                            key={tg}
                            className="text-[9px] font-ui tracking-widest uppercase text-mist/65 border border-gold/15 rounded-sm px-1.5 py-0.5"
                          >
                            {tg}
                          </span>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

function MarketplaceTab({ listings }) {
  if (!listings || listings.length === 0) {
    return <Empty hint="No marketplace listings have been published from this campaign yet." />;
  }
  return (
    <div data-testid="showcase-marketplace-tab">
      <div className="label-ref mb-2">From this campaign</div>
      <h2 className="font-display text-2xl md:text-3xl text-parchment uppercase tracking-tight mb-8">
        {listings.length} marketplace {listings.length === 1 ? "listing" : "listings"}
      </h2>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {listings.map((l) => (
          <article
            key={l.id}
            className="card-mystic p-5"
            data-testid={`showcase-listing-${l.id}`}
          >
            <div className="text-[10px] font-ui tracking-widest uppercase text-arcane mb-1">
              {l.kind}
              {l.access === "paywall" && (
                <span className="ml-2 text-ember">paywall</span>
              )}
            </div>
            <div className="font-display text-base text-parchment leading-tight">
              {l.name}
            </div>
            {l.summary && (
              <p className="mt-3 text-sm text-mist font-body leading-relaxed line-clamp-4">
                {l.summary}
              </p>
            )}
            <div className="mt-4 flex items-center justify-between text-[10px] font-mono">
              <span className="text-gold-bright">
                {l.source_system_id || "system"}
              </span>
              <span className="text-mist/65">
                {l.downloads ?? 0} clones
              </span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function CanonTab({ canon, gmName }) {
  if (!canon.published) {
    return (
      <Empty hint={`${gmName || "The GM"} hasn't enrolled this campaign in the Canon Registry yet — but you can still clone the public world above.`} />
    );
  }
  return (
    <div data-testid="showcase-canon-tab" className="max-w-3xl">
      <div className="label-ref mb-3">Canon Registry</div>
      <h2 className="font-display text-2xl md:text-3xl text-parchment uppercase tracking-tight">
        Enrolled in the public canon.
      </h2>
      {canon.blurb && (
        <p className="mt-6 text-mist font-body text-base leading-relaxed">
          {canon.blurb}
        </p>
      )}
      <div className="mt-8 grid sm:grid-cols-2 gap-3">
        <div className="card-mystic p-5" data-testid="showcase-canon-deltas">
          <div className="label-ref mb-1">Delta drops</div>
          <div className="font-display text-3xl text-gold-bright">
            {canon.deltas_count}
          </div>
          <div className="mt-1 text-xs text-mist/65 font-body">
            Campaign updates that other GMs can fork into their tables.
          </div>
        </div>
        <div className="card-mystic p-5">
          <div className="label-ref mb-1">Subscribe</div>
          <p className="text-xs text-mist/85 font-body leading-relaxed">
            Subscribers receive a digest when this canon publishes new
            delta drops. Subscription requires a TableGnostics seat.
          </p>
          <Link
            to="/auth?mode=register"
            className="mt-4 inline-flex items-center gap-2 text-[11px] font-ui uppercase tracking-widest text-gold-bright hover:text-gold underline-offset-4 hover:underline"
            data-testid="showcase-canon-subscribe-cta"
          >
            Begin the Rite to subscribe <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>
    </div>
  );
}

function Empty({ hint }) {
  return (
    <div className="card-mystic p-8 text-center text-mist/80 font-body" data-testid="showcase-empty">
      {hint}
    </div>
  );
}
