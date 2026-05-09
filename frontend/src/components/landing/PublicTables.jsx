import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { ArrowRight, Globe2 } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Public Tables strip — fetches the first 6 publicly-published showcases
 * and surfaces them inline on the Landing page so visitors can dive in
 * without signing up. Hides itself entirely if no campaigns are published
 * (so the section never displays a depressing "0 tables" placeholder).
 */
export default function PublicTables() {
  const [items, setItems] = useState(null);

  useEffect(() => {
    let cancel = false;
    axios
      .get(`${API}/public/discover?limit=6`)
      .then((r) => !cancel && setItems(r.data.items || []))
      .catch(() => !cancel && setItems([]));
    return () => {
      cancel = true;
    };
  }, []);

  if (!items || items.length === 0) {
    // Hide the entire section when there's nothing public yet — no
    // placeholder copy, no awkward zero-state on the marketing page.
    return null;
  }

  return (
    <section
      id="public-tables"
      className="relative z-10 px-5 md:px-10 py-24 md:py-32"
      data-testid="public-tables-section"
    >
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-12">
          <div className="max-w-2xl">
            <div className="label-ref mb-4">Public tables · live</div>
            <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
              Walk into a <span className="text-gold italic font-body normal-case">stranger's world.</span>
            </h2>
            <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
              Real campaigns published by real GMs. Browse the codex, peek at
              the marketplace listings, fork a copy into your own table.
            </p>
          </div>
          <Link
            to="/discover/browse"
            className="btn px-5 py-3 text-sm self-start md:self-end"
            data-testid="public-tables-browse-all"
          >
            Browse all tables <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="public-tables-grid">
          {items.slice(0, 6).map((c) => (
            <Link
              key={c.slug}
              to={`/discover/${c.slug}`}
              className="card-mystic p-5 transition-all duration-500 hover:-translate-y-1 group block"
              data-testid={`public-tables-card-${c.slug}`}
            >
              <div className="flex items-center gap-2 text-[10px] font-ui tracking-widest uppercase text-gold/70">
                <Globe2 className="w-3 h-3" />
                {c.system || c.system_id}
                {c.canon_published && <span className="ml-1 text-arcane">canon</span>}
              </div>
              <div className="mt-2 font-display text-lg text-parchment leading-tight uppercase tracking-tight group-hover:text-gold-bright transition-colors">
                {c.name}
              </div>
              {c.blurb && (
                <p className="mt-3 text-sm text-mist font-body leading-relaxed line-clamp-3">
                  {c.blurb}
                </p>
              )}
              <div className="mt-5 pt-4 border-t border-gold/10 flex items-center justify-between text-[10px] font-mono">
                <span className="text-mist/70 truncate pr-2">GM · {c.gm_name}</span>
                <span className="text-gold-bright shrink-0">
                  {c.marketplace_count} {c.marketplace_count === 1 ? "listing" : "listings"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
