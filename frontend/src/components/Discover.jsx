import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";
import { Compass, Users, Clock3, Globe2, Search, ArrowRight, Flame, Filter, UserPlus2 } from "lucide-react";

export default function Discover() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [exp, setExp] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/campaigns").then((r) => setRows(r.data)).catch((e) => setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message));
  }, []);

  const filtered = useMemo(() => {
    const ql = q.toLowerCase();
    return rows.filter((c) => {
      if (c.visibility !== "public") return false;
      if ((c.member_ids?.length || 0) >= c.max_players) return false;
      if (c.gm_id === user?.id) return false;
      if (exp && c.experience_level !== exp) return false;
      if (!ql) return true;
      const blob = `${c.name} ${c.description || ""} ${(c.tags || []).join(" ")} ${c.tone || ""} ${c.genre || ""} ${c.gm_name}`.toLowerCase();
      return blob.includes(ql);
    });
  }, [rows, q, exp, user]);

  const join = async (c) => {
    try { await api.post(`/campaigns/${c.id}/join`, { message: "" });
      alert(`Seat claimed at "${c.name}".`);
      const { data } = await api.get("/campaigns");
      setRows(data);
    } catch (e) { alert(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };

  return (
    <div className="px-8 md:px-12 py-10">
      <div className="label-ref flex items-center gap-2 mb-2"><Compass className="w-3 h-3"/> The Seekers' Hall</div>
      <h1 className="font-display text-4xl tracking-wide text-parchment">Tables Seeking Players</h1>
      <p className="text-mist mt-2 font-body max-w-2xl">
        Public tables with an open seat. Find a campaign whose genre, tone, and tempo speak to you — then claim the seat.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 border border-gold/20 rounded-sm px-3 bg-void/60 w-80">
          <Search className="w-4 h-4 text-gold/60"/>
          <input className="bg-transparent outline-none py-2 text-sm text-parchment flex-1"
                 placeholder="Search by genre, tag, GM, keyword…"
                 value={q} onChange={(e) => setQ(e.target.value)} data-testid="discover-search"/>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gold/60"/>
          <select className="select" value={exp} onChange={(e) => setExp(e.target.value)} data-testid="discover-experience">
            <option value="">Any experience level</option>
            <option>Newcomer</option><option>Intermediate</option><option>Veteran</option><option>Any</option>
          </select>
        </div>
        <div className="text-xs font-ui uppercase tracking-widest text-mist/70 ml-auto">
          {filtered.length} {filtered.length === 1 ? "table" : "tables"} open
        </div>
      </div>

      <div className="divider-sigil my-6"/>

      {err && <div className="text-ember text-sm">{err}</div>}
      {filtered.length === 0 ? (
        <div className="card-mystic p-10 text-center">
          <Flame className="w-6 h-6 text-gold/60 mx-auto mb-3"/>
          <div className="font-display text-xl text-parchment">No tables seeking players — yet.</div>
          <div className="text-sm text-mist mt-2 font-body">Try widening your filters, or host your own table.</div>
          <Link to="/app/campaigns?create=1" className="btn btn-primary mt-4 inline-flex">
            Forge a campaign <ArrowRight className="w-4 h-4"/>
          </Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((c) => (
            <div key={c.id} className="card-mystic p-5 flex flex-col" data-testid={`discover-${c.id}`}>
              <div className="flex items-center justify-between">
                <span className="label-ref">{c.system} · {c.power_level}</span>
                <span className="tag"><Globe2 className="w-3 h-3"/> Public</span>
              </div>
              <div className="font-display text-xl text-parchment mt-2">{c.name}</div>
              <div className="text-sm text-mist mt-1 line-clamp-3 font-body">{c.description || "—"}</div>
              <div className="mt-3 space-y-1 text-xs font-ui">
                <div className="flex items-center gap-2 text-mist/80"><Users className="w-3 h-3 text-gold/70"/> {c.member_ids?.length || 0}/{c.max_players} seated · GM {c.gm_name}</div>
                {c.schedule && <div className="flex items-center gap-2 text-mist/80"><Clock3 className="w-3 h-3 text-gold/70"/> {c.schedule}</div>}
                {c.experience_level && <div className="text-[10px] uppercase tracking-widest text-gold/60">{c.experience_level}</div>}
              </div>
              {(c.tags?.length || c.tone || c.genre) && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {c.tone && <span className="tag">{c.tone}</span>}
                  {c.genre && <span className="tag">{c.genre}</span>}
                  {(c.tags || []).slice(0, 4).map((t, i) => <span key={i} className="tag">{t}</span>)}
                </div>
              )}
              <div className="mt-auto pt-4 flex gap-2">
                <Link to={`/app/campaigns/${c.id}`} className="btn btn-ghost text-xs flex-1">Inspect</Link>
                <button onClick={() => join(c)} className="btn btn-primary text-xs flex-1" data-testid={`join-${c.id}`}>
                  <UserPlus2 className="w-3 h-3"/> Take a seat
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
