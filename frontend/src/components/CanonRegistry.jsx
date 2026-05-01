import React, { useEffect, useState } from "react";
import { useAuth, api, formatApiErrorDetail } from "../lib/api";
import { Link } from "react-router-dom";
import {
  Library, Bookmark, BookmarkCheck, Users, Layers, Globe2, ArrowRight, Flame,
} from "lucide-react";

/**
 * CanonRegistry — V6.13 public-ish author-side discovery of campaigns
 * whose GM has opted into the Canon Registry. Distinct from Discover
 * (which surfaces open PLAYER seats). Here the audience is fellow GMs
 * who want to track a campaign's Delta Drops as inspiration or inherited
 * substrate.
 *
 * Auth required for the subscribe action (200 when signed in, login
 * prompt otherwise). The registry list itself is public — you can
 * browse without an account.
 */
export default function CanonRegistry() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [mine, setMine] = useState([]);   // my subscriptions
  const [err, setErr] = useState("");
  const [busyId, setBusyId] = useState("");

  const load = async () => {
    try {
      const [all, subs] = await Promise.all([
        api.get("/canon-registry").then((r) => r.data || []),
        user
          ? api.get("/canon-registry/subscriptions").then((r) => r.data || []).catch(() => [])
          : Promise.resolve([]),
      ]);
      setRows(all);
      setMine(subs);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [user?.id]);

  const subscribedIds = new Set(mine.map((m) => m.id));

  const toggle = async (c) => {
    if (!user) { alert("Sign in to subscribe to a canon."); return; }
    setBusyId(c.id);
    try {
      if (subscribedIds.has(c.id)) {
        await api.delete(`/canon-registry/${c.id}/subscribe`);
      } else {
        await api.post(`/canon-registry/${c.id}/subscribe`);
      }
      await load();
    } catch (e) {
      alert(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusyId(""); }
  };

  return (
    <div className="px-8 md:px-12 py-10" data-testid="canon-registry">
      <div className="label-ref flex items-center gap-2 mb-2">
        <Library className="w-3 h-3"/> Author's Hall
      </div>
      <h1 className="font-display text-4xl tracking-wide text-parchment">Public Canon Registry</h1>
      <p className="text-mist mt-2 font-body max-w-2xl">
        Fellow GMs' campaigns they've published for cross-table borrowing — subscribe to watch
        their Delta Drops land, adapt what fits, leave the rest. Distinct from the Seekers' Hall
        (which surfaces open <em>player</em> seats).
      </p>

      {user && mine.length > 0 && (
        <div className="mt-6" data-testid="canon-subscriptions">
          <div className="label-ref mb-2 flex items-center gap-2">
            <BookmarkCheck className="w-3 h-3"/> You follow {mine.length} canon{mine.length === 1 ? "" : "s"}
          </div>
          <div className="flex flex-wrap gap-2">
            {mine.map((m) => (
              <Link key={m.id} to={`/app/campaigns/${m.id}`}
                    className="tag border-gold/40 text-gold-bright hover:bg-gold/10 transition-colors"
                    data-testid={`canon-subscribed-${m.id}`}>
                {m.name} · {m.system}
              </Link>
            ))}
          </div>
        </div>
      )}

      <div className="divider-sigil my-6"/>
      {err && <div className="text-ember text-sm mb-4" data-testid="canon-error">{err}</div>}

      {rows.length === 0 ? (
        <div className="card-mystic p-10 text-center" data-testid="canon-empty">
          <Flame className="w-6 h-6 text-gold/60 mx-auto mb-3"/>
          <div className="font-display text-xl text-parchment">The Hall is quiet.</div>
          <div className="text-sm text-mist mt-2 font-body">
            No GMs have published a canon yet. Be the first — open your campaign's settings and
            toggle "Publish to Canon Registry."
          </div>
          {user && (
            <Link to="/app/campaigns" className="btn btn-primary mt-4 inline-flex"
                  data-testid="canon-author-cta">
              Your campaigns <ArrowRight className="w-4 h-4"/>
            </Link>
          )}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="canon-grid">
          {rows.map((c) => {
            const subscribed = subscribedIds.has(c.id);
            return (
              <div key={c.id} className="card-mystic p-5 flex flex-col"
                   data-testid={`canon-card-${c.id}`}>
                <div className="flex items-center justify-between">
                  <span className="label-ref">{c.system}</span>
                  <span className="tag">
                    <Globe2 className="w-3 h-3"/> Canon
                  </span>
                </div>
                <div className="font-display text-xl text-parchment mt-2">{c.name}</div>
                {(c.setting_name || c.genre) && (
                  <div className="text-[11px] text-gold/70 font-ui uppercase tracking-widest mt-1">
                    {[c.setting_name, c.genre].filter(Boolean).join(" · ")}
                  </div>
                )}
                <div className="text-sm text-mist mt-2 line-clamp-3 font-body">
                  {c.canon_blurb || "—"}
                </div>
                <div className="mt-3 space-y-1 text-xs font-ui">
                  <div className="flex items-center gap-2 text-mist/80">
                    <Users className="w-3 h-3 text-gold/70"/> GM {c.gm_name} · {c.member_count} seated
                  </div>
                  <div className="flex items-center gap-2 text-mist/80">
                    <Layers className="w-3 h-3 text-gold/70"/>
                    {c.delta_drops || 0} delta drop{c.delta_drops === 1 ? "" : "s"} ·
                    {" "}{c.subscribers || 0} subscriber{c.subscribers === 1 ? "" : "s"}
                  </div>
                </div>
                {(c.tags?.length || c.tone) && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {c.tone && <span className="tag">{c.tone}</span>}
                    {(c.tags || []).slice(0, 3).map((t, i) => (
                      <span key={i} className="tag">{t}</span>
                    ))}
                  </div>
                )}
                <div className="mt-auto pt-4 flex gap-2">
                  <Link to={`/app/campaigns/${c.id}`} className="btn btn-ghost text-xs flex-1"
                        data-testid={`canon-inspect-${c.id}`}>
                    Inspect
                  </Link>
                  <button onClick={() => toggle(c)}
                          disabled={busyId === c.id}
                          className={`btn text-xs flex-1 ${subscribed ? "btn-primary" : "btn-ghost"}`}
                          data-testid={`canon-toggle-${c.id}`}>
                    {subscribed ? (
                      <><BookmarkCheck className="w-3 h-3"/> Following</>
                    ) : (
                      <><Bookmark className="w-3 h-3"/> Follow</>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
