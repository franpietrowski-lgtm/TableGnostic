/**
 * V6.25.58 — Featured Starter Campaigns landing-page gallery.
 *
 * A discoverability flywheel: new GMs land on TableGnostic, see a row
 * of curated `.tgcampaign.json` starters they can one-click download,
 * and then upload through the Phase C import flow to instantly stand
 * up a populated campaign. No LLM dependency — pure data round-trip.
 *
 * Renders nothing if the admin hasn't curated any starters yet — the
 * landing page stays clean instead of showing an empty rail.
 */
import React, { useEffect, useState } from "react";
import { Download, Scroll, Loader2, Sparkles, Crown } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SYSTEM_LABEL = {
  "besm-4e":  "BESM 4E",
  "dnd-5e":   "D&D 5E",
  "cypher":   "Cypher",
  "anime-5e": "Anime 5E",
};

const SYSTEM_TINT = {
  "besm-4e":  "border-amber-500/40 text-amber-300",
  "dnd-5e":   "border-rose-600/40 text-rose-300",
  "cypher":   "border-indigo-400/40 text-indigo-300",
  "anime-5e": "border-pink-500/40 text-pink-300",
};

export default function StarterCampaigns() {
  const [rows, setRows] = useState(null);
  const [busy, setBusy] = useState({});  // slug -> bool

  useEffect(() => {
    let cancel = false;
    fetch(`${API}/public/starters`)
      .then((r) => r.json())
      .then((d) => { if (!cancel) setRows((d && d.rows) || []); })
      .catch(() => { if (!cancel) setRows([]); });
    return () => { cancel = true; };
  }, []);

  const onDownload = (slug, title) => {
    setBusy((b) => ({ ...b, [slug]: true }));
    // Anchor-tag click triggers the file download natively; the
    // backend sets Content-Disposition so the browser saves directly.
    const a = document.createElement("a");
    a.href = `${API}/public/starters/${slug}/download`;
    a.download = `${slug}.tgcampaign.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    // Bump local download count optimistically; the real counter
    // increments on the server side.
    setRows((prev) => (prev || []).map((r) =>
      r.slug === slug ? { ...r, downloads: (r.downloads || 0) + 1 } : r
    ));
    setTimeout(() => setBusy((b) => ({ ...b, [slug]: false })), 800);
  };

  // No starters curated → hide the entire section so the landing
  // page never shows an empty rail.
  if (rows && rows.length === 0) return null;

  return (
    <section
      id="starter-campaigns"
      className="relative z-10 px-5 md:px-10 py-24 md:py-32 border-y border-gold/10"
      data-testid="landing-starter-campaigns"
    >
      <div className="max-w-6xl mx-auto">
        <div className="flex items-end justify-between flex-wrap gap-4 mb-10">
          <div>
            <div className="label-ref mb-3">
              <Sparkles className="inline w-3 h-3 mr-1 -mt-0.5 text-gold"/>
              Starter Campaigns
            </div>
            <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
              One click, <span className="text-gold italic font-body normal-case">a full table.</span>
            </h2>
            <p className="mt-4 text-mist text-base md:text-lg font-body leading-relaxed max-w-2xl">
              Download a hand-curated `.tgcampaign.json` bundle — codex,
              characters, scenes, encounters, atlas pins, the works.
              Re-upload through your dashboard and the campaign stands up
              instantly, owned by you.
            </p>
          </div>
          <div className="text-[10px] text-mist/60 uppercase tracking-widest font-ui">
            No LLM · No keys · Portable
          </div>
        </div>

        {/* Loading state */}
        {rows === null && (
          <div className="flex items-center gap-2 text-mist/70 text-sm"
               data-testid="starter-loading">
            <Loader2 className="w-4 h-4 animate-spin"/> Loading the starters'
            shelf…
          </div>
        )}

        {/* Cards grid */}
        {rows && rows.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4"
               data-testid="starter-grid">
            {rows.map((r) => (
              <article key={r.slug}
                       data-testid={`starter-card-${r.slug}`}
                       className={`card-mystic p-5 flex flex-col transition hover:-translate-y-0.5 hover:border-gold/60
                                  ${r.featured ? "ring-1 ring-gold/50" : ""}`}>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className={`text-[10px] uppercase tracking-widest font-ui px-2 py-0.5 rounded-sm border
                                  ${SYSTEM_TINT[r.system_id] || "border-mist/30 text-mist/70"}`}
                        data-testid={`starter-system-${r.slug}`}>
                    {SYSTEM_LABEL[r.system_id] || r.system_id}
                  </span>
                  {r.featured && (
                    <span className="text-[10px] uppercase tracking-widest text-gold-bright flex items-center gap-1"
                          data-testid={`starter-featured-${r.slug}`}>
                      <Crown className="w-3 h-3"/> Featured
                    </span>
                  )}
                </div>
                <h3 className="font-display text-xl text-parchment leading-snug mb-1">
                  {r.title}
                </h3>
                {r.blurb && (
                  <p className="text-[12px] text-mist mb-3 leading-relaxed">{r.blurb}</p>
                )}
                {r.blurb_long && (
                  <p className="text-[11px] text-mist/70 italic mb-3 leading-relaxed line-clamp-3">
                    {r.blurb_long}
                  </p>
                )}
                <div className="mt-auto flex items-center justify-between gap-2 pt-3 border-t border-mist/10">
                  <div className="text-[10px] text-mist/50 font-ui flex items-center gap-3">
                    <span title="Total downloads">
                      <Scroll className="inline w-3 h-3 mr-0.5"/>{r.downloads || 0}
                    </span>
                    <span title="Bundle size">
                      {r.bytes ? formatBytes(r.bytes) : ""}
                    </span>
                  </div>
                  <button onClick={() => onDownload(r.slug, r.title)}
                          disabled={!!busy[r.slug]}
                          className="btn btn-primary text-xs"
                          data-testid={`starter-download-${r.slug}`}>
                    {busy[r.slug]
                      ? <><Loader2 className="w-3 h-3 animate-spin"/> Downloading…</>
                      : <><Download className="w-3 h-3"/> Download</>}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}

        <div className="mt-8 text-[11px] text-mist/60 font-ui">
          New here? Create an account, head to <b className="text-gold-bright">Hall of Tables → Import bundle</b>,
          and drop the file you just downloaded. Your new campaign appears the second the upload completes.
        </div>
      </div>
    </section>
  );
}

function formatBytes(n) {
  if (!n) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 102.4) / 10} KB`;
  return `${Math.round(n / 104857.6) / 10} MB`;
}
