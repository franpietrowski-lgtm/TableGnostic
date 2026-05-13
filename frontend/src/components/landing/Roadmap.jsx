/**
 * Roadmap — V6.25.40
 *
 * Live-wired to `GET /api/public/roadmap`. Admin curates items via
 * `/app/admin` → Roadmap tab. Falls back to a hardcoded "we're cooking"
 * sentinel if the API returns nothing (the section never goes blank).
 *
 * Markdown supported in `body_md` so admin can author rich changelog-style
 * entries with bold, lists, inline code, links.
 */
import React, { useEffect, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { CheckCircle2 as CircleCheckBig, Hammer, Telescope, Sparkles } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const COLUMNS = [
  { k: "now",     label: "Live now",         Icon: CircleCheckBig, tone: "text-gold-bright" },
  { k: "next",    label: "Next 90 days",     Icon: Hammer,         tone: "text-arcane" },
  { k: "later",   label: "Horizon",          Icon: Telescope,      tone: "text-mist" },
  { k: "shipped", label: "Recently shipped", Icon: Sparkles,       tone: "text-ember" },
];


export default function Roadmap() {
  const [items, setItems] = useState(null);

  useEffect(() => {
    let cancel = false;
    axios.get(`${API}/public/roadmap`)
      .then((r) => !cancel && setItems(r.data.items || []))
      .catch(() => !cancel && setItems([]));
    return () => { cancel = true; };
  }, []);

  if (items === null) {
    return null; // initial load — no flash of empty
  }

  const byStatus = (k) => items.filter((i) => i.status === k);

  return (
    <section
      id="roadmap"
      className="relative z-10 px-5 md:px-10 py-24 md:py-32 border-y border-gold/10 bg-void/30"
      data-testid="roadmap-section"
    >
      <div className="max-w-6xl mx-auto">
        <div className="mb-12 max-w-2xl">
          <div className="label-ref mb-4">Roadmap · live</div>
          <h2 className="font-display text-3xl md:text-5xl leading-tight text-parchment uppercase tracking-tight">
            What's <span className="text-gold italic font-body normal-case">on the table.</span>
          </h2>
          <p className="mt-6 text-mist text-base md:text-lg font-body leading-relaxed">
            Updated whenever the desk presses a new build. Admin-curated;
            community votes follow soon.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {COLUMNS.map(({ k, label, Icon, tone }) => {
            const col = byStatus(k);
            return (
              <div key={k} className="card-mystic p-5 flex flex-col"
                   data-testid={`roadmap-col-${k}`}>
                <div className="flex items-center gap-2 mb-3">
                  <Icon className={`w-4 h-4 ${tone}`}/>
                  <div className={`text-[10px] uppercase tracking-widest ${tone}`}>{label}</div>
                </div>
                {col.length === 0 ? (
                  <div className="text-mist/60 text-xs italic">No items yet.</div>
                ) : (
                  <ul className="space-y-3">
                    {col.map((it) => (
                      <li key={it.id}
                          className="border-l-2 border-gold/20 pl-3"
                          data-testid={`roadmap-item-${it.id}`}>
                        <div className="text-parchment text-sm font-display tracking-wide">
                          {it.title}
                          {it.eta && (
                            <span className="ml-2 text-[9px] uppercase tracking-widest text-gold/60 font-ui">
                              {it.eta}
                            </span>
                          )}
                        </div>
                        {it.body_md && (
                          <div className="text-mist/85 text-[12px] mt-1 leading-relaxed font-body roadmap-md">
                            <ReactMarkdown
                              components={{
                                p: ({ children }) => <p className="mb-1.5">{children}</p>,
                                code: ({ children }) => (
                                  <code className="font-mono text-[11px] text-gold-bright bg-gold/10 px-1 rounded-sm">{children}</code>
                                ),
                                a: ({ href, children }) => (
                                  <a href={href} className="text-gold-bright underline">{children}</a>
                                ),
                                strong: ({ children }) => (
                                  <strong className="text-parchment">{children}</strong>
                                ),
                                ul: ({ children }) => <ul className="list-disc ml-4">{children}</ul>,
                                li: ({ children }) => <li className="mb-0.5">{children}</li>,
                              }}>
                              {it.body_md}
                            </ReactMarkdown>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
