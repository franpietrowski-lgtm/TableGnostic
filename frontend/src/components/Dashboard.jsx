import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Scroll, Plus, ArrowRight, Flame } from "lucide-react";

export default function Dashboard() {
  const [mine, setMine] = useState([]);
  const [all, setAll] = useState([]);

  useEffect(() => {
    (async () => {
      const [m, a] = await Promise.all([
        api.get("/campaigns", { params: { mine: true } }).then((r) => r.data).catch(() => []),
        api.get("/campaigns").then((r) => r.data).catch(() => []),
      ]);
      setMine(m); setAll(a);
    })();
  }, []);

  return (
    <div className="px-8 md:px-12 py-10 max-w-6xl">
      <div className="label-ref mb-3">Hearth</div>
      <h1 className="font-display text-4xl tracking-wide text-parchment mb-2">Welcome back to the table.</h1>
      <p className="text-mist font-body">Resume an unfolding story, or take a seat at a new one.</p>

      <div className="mt-10 grid md:grid-cols-3 gap-4">
        <Link to="/app/campaigns" className="card-mystic p-5 transition hover:-translate-y-0.5" data-testid="dash-my-campaigns">
          <div className="flex items-center gap-2 label-ref"><Scroll className="w-3 h-3"/> My campaigns</div>
          <div className="mt-3 font-display text-3xl text-gold">{mine.length}</div>
          <div className="text-xs text-mist mt-2">Campaigns you run or are seated at</div>
        </Link>
        <Link to="/app/campaigns?create=1" className="card-mystic p-5 transition hover:-translate-y-0.5" data-testid="dash-create-campaign">
          <div className="flex items-center gap-2 label-ref"><Plus className="w-3 h-3"/> Begin a new rite</div>
          <div className="mt-3 font-display text-xl text-parchment">Forge a campaign</div>
          <div className="text-xs text-mist mt-2">Host a new BESM 4E table</div>
        </Link>
        <Link to="/app/campaigns" className="card-mystic p-5 transition hover:-translate-y-0.5" data-testid="dash-discover">
          <div className="flex items-center gap-2 label-ref"><Flame className="w-3 h-3"/> Discover tables</div>
          <div className="mt-3 font-display text-3xl text-gold">{all.filter(c => c.visibility === "public").length}</div>
          <div className="text-xs text-mist mt-2">Public tables seeking players</div>
        </Link>
      </div>

      <div className="mt-12">
        <div className="flex items-center justify-between">
          <h2 className="h-arcane text-lg">Your campaigns</h2>
          <Link to="/app/campaigns" className="text-xs text-gold/80 hover:text-gold-bright uppercase tracking-widest font-ui">Browse all <ArrowRight className="inline w-3 h-3"/></Link>
        </div>
        <div className="divider-sigil my-3" />
        {mine.length === 0 ? (
          <div className="text-mist text-sm font-body italic">No threads held yet. Start your first campaign.</div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mine.map(c => (
              <Link key={c.id} to={`/app/campaigns/${c.id}`} className="card-mystic p-5" data-testid={`campaign-card-${c.id}`}>
                <div className="label-ref">{c.system} · {c.power_level}</div>
                <div className="font-display text-lg text-parchment mt-1 truncate">{c.name}</div>
                <div className="text-xs text-mist mt-1 line-clamp-2">{c.description || "—"}</div>
                <div className="flex items-center justify-between mt-4">
                  <span className="tag">{c.visibility}</span>
                  <span className="text-[11px] text-gold/70 font-ui">{c.member_ids?.length || 0}/{c.max_players} seated</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
