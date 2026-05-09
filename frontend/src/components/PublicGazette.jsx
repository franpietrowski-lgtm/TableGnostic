/**
 * PublicGazette — V6.25.38
 *
 * Public newspaper view for a discover_published campaign.
 * Old-timey broadsheet styling: blackletter masthead, dateline, multi-column
 * layout, drop-caps, sepia/parchment paper, ornament dividers.
 *
 * Box-score leaderboards rendered like a sports/stocks page underneath.
 *
 * Mounts at: /discover/{slug}/gazette  (public, no auth)
 */
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, Star } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const COLUMN_LABEL = {
  front: "Front Page",
  world: "World Wire",
  marketplace: "Marketplace",
  obituaries: "Obituaries",
};

export default function PublicGazette() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [boards, setBoards] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    document.title = `The Gazette · TableGnostics`;
    axios.get(`${API}/public/news/${slug}/issues/latest`)
      .then((r) => setData(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Showcase not found."));
    axios.get(`${API}/public/news/${slug}/leaderboards`)
      .then((r) => setBoards(r.data))
      .catch(() => {});
  }, [slug]);

  if (err) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void text-mist p-8">
        <div className="text-center">
          <div className="text-2xl font-display tracking-widest text-parchment mb-2">No such gazette.</div>
          <div className="text-sm">{err}</div>
          <Link to="/discover" className="btn btn-ghost text-xs mt-4 inline-flex">
            <ArrowLeft className="w-3 h-3"/> Back to Discover
          </Link>
        </div>
      </div>
    );
  }
  if (!data) {
    return <div className="min-h-screen flex items-center justify-center text-mist text-sm">Setting type…</div>;
  }

  const { issue, articles, campaign } = data;
  return (
    <div className="public-gazette min-h-screen bg-[#f3e9d2] text-[#1c1208] py-10 px-4 sm:px-8"
         style={{ fontFamily: '"Cormorant Garamond", "Times New Roman", serif' }}
         data-testid="public-gazette-root">
      <div className="max-w-5xl mx-auto">
        <div className="mb-3">
          <Link to={`/discover/${slug}`} className="text-[#7a4d1d] hover:text-[#1c1208] text-xs uppercase tracking-widest">
            ← Back to Showcase
          </Link>
        </div>

        <Masthead campaign={campaign} issue={issue}/>

        {!issue && (
          <div className="border-y-2 border-double border-[#1c1208] py-12 text-center my-8"
               data-testid="public-gazette-empty">
            <div className="font-bold tracking-widest uppercase text-2xl">No Issue Yet</div>
            <div className="text-sm italic mt-2 max-w-md mx-auto">
              The presses are warming. The {campaign.name} Gazette has not pressed
              its first issue. Check back when the GM rolls the cylinders.
            </div>
          </div>
        )}

        {issue && articles && articles.length > 0 && (
          <FrontPage articles={articles}/>
        )}

        <Boxscore boards={boards}/>

        <Colophon/>
      </div>
    </div>
  );
}


function Masthead({ campaign, issue }) {
  const date = issue ? issue.date_label : new Date().toISOString().slice(0, 10);
  const number = issue ? `Issue No. ${issue.issue_number}` : "Pre-Issue";
  return (
    <div className="text-center border-y-4 border-double border-[#1c1208] py-4 mb-2"
         data-testid="gazette-masthead">
      <div className="text-[10px] tracking-[0.5em] uppercase mb-1">
        {campaign.system_id?.toUpperCase()} · GM {campaign.gm_name || "Anonymous"}
      </div>
      <h1 className="text-[44px] sm:text-[64px] leading-none font-black tracking-[0.02em] uppercase"
          style={{ fontFamily: '"UnifrakturCook", "Cinzel", "Cormorant Garamond", serif', fontWeight: 900 }}>
        {issue?.masthead || `The ${campaign.name} Gazette`}
      </h1>
      <div className="flex justify-between items-center mt-3 text-[11px] tracking-widest uppercase">
        <span>{date}</span>
        <span className="hidden sm:block">— Pressed at the Tablegnostic Print-Works —</span>
        <span>{number}</span>
      </div>
      {campaign.blurb && (
        <div className="mt-3 italic text-sm max-w-xl mx-auto">{campaign.blurb}</div>
      )}
    </div>
  );
}


function FrontPage({ articles }) {
  // First front article is the marquee. Rest split by column.
  const front = articles.filter((a) => a.column === "front");
  const world = articles.filter((a) => a.column === "world");
  const market = articles.filter((a) => a.column === "marketplace");
  const obits = articles.filter((a) => a.column === "obituaries");
  const lead = front[0];
  const restFront = front.slice(1);

  return (
    <div data-testid="gazette-frontpage">
      {/* Marquee article — wide, drop-cap */}
      {lead && (
        <article className="border-b-2 border-[#1c1208] py-6"
                 data-testid={`gazette-lead-${lead.id}`}>
          {lead.kicker && (
            <div className="text-[10px] uppercase tracking-[0.3em] text-[#7a4d1d] mb-1">{lead.kicker}</div>
          )}
          <h2 className="text-3xl sm:text-5xl font-bold leading-tight uppercase tracking-tight">
            {lead.headline}
          </h2>
          <div className="text-xs italic mt-1 text-[#5d3a18]">{lead.byline}</div>
          <p className="mt-4 text-base sm:text-lg leading-relaxed first-letter:text-6xl first-letter:font-black first-letter:float-left first-letter:mr-2 first-letter:leading-[0.85]">
            {lead.body}
          </p>
        </article>
      )}

      {/* Two-column secondary front-page articles */}
      {restFront.length > 0 && (
        <div className="grid md:grid-cols-2 gap-x-8 gap-y-6 border-b-2 border-[#1c1208] py-6">
          {restFront.map((a) => <Column article={a} key={a.id}/>)}
        </div>
      )}

      {/* World Wire — three columns of shorts */}
      {world.length > 0 && (
        <Section title="World Wire">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4">
            {world.map((a) => <Column article={a} key={a.id}/>)}
          </div>
        </Section>
      )}

      {/* Marketplace — two columns */}
      {market.length > 0 && (
        <Section title="Marketplace">
          <div className="grid md:grid-cols-2 gap-6">
            {market.map((a) => <Column article={a} key={a.id}/>)}
          </div>
        </Section>
      )}

      {/* Obituaries — single column, italic */}
      {obits.length > 0 && (
        <Section title="Obituaries · They Shall Be Mourned">
          <div className="space-y-4 italic">
            {obits.map((a) => <Column article={a} key={a.id}/>)}
          </div>
        </Section>
      )}
    </div>
  );
}


function Section({ title, children }) {
  return (
    <section className="py-6 border-b-2 border-[#1c1208]">
      <div className="text-center mb-4">
        <div className="inline-block px-4 border-y border-[#1c1208] py-1 uppercase tracking-[0.3em] text-sm font-bold">
          {title}
        </div>
      </div>
      {children}
    </section>
  );
}


function Column({ article }) {
  return (
    <div data-testid={`gazette-article-${article.id}`}>
      {article.kicker && (
        <div className="text-[9px] uppercase tracking-[0.3em] text-[#7a4d1d] mb-0.5">{article.kicker}</div>
      )}
      <h3 className="text-lg font-bold leading-tight uppercase">{article.headline}</h3>
      <div className="text-[11px] italic text-[#5d3a18] mb-1">{article.byline}</div>
      <p className="text-sm leading-relaxed">{article.body}</p>
    </div>
  );
}


function Boxscore({ boards }) {
  if (!boards) return null;
  return (
    <section className="py-8 border-b-2 border-[#1c1208]"
             data-testid="gazette-boxscore-section">
      <div className="flex items-end justify-between flex-wrap mb-4">
        <div>
          <div className="uppercase tracking-[0.3em] text-xs">Sporting Standings</div>
          <h2 className="text-2xl font-bold uppercase">The Mer Der Hoh Bohs</h2>
        </div>
        <Ticker boards={boards}/>
      </div>
      <div className="grid md:grid-cols-2 gap-6">
        <ScoreTable title="Kill Count" rows={boards.kills}
                     cols={[["character_name", "Hero"], ["kills", "K", true]]}
                     testid="gazette-bs-kills"/>
        <ScoreTable title="XP Standings" rows={boards.xp}
                     cols={[["character_name", "Hero"], ["xp_total", "XP", true]]}
                     testid="gazette-bs-xp"/>
        <ScoreTable title="Sessions Sat" rows={boards.sessions}
                     cols={[["character_name", "Hero"], ["session_count", "S", true]]}
                     testid="gazette-bs-sessions"/>
        <ScoreTable title="Player Roster · Total XP" rows={boards.players}
                     cols={[["owner_name", "Player"], ["character_count", "★", true], ["total_xp", "XP", true]]}
                     testid="gazette-bs-players"/>
      </div>
    </section>
  );
}


function Ticker({ boards }) {
  // Sports/stocks "ticker" running header — top kill, top XP.
  const topKill = (boards.kills || [])[0];
  const topXP   = (boards.xp || [])[0];
  const bits = [];
  if (topKill) bits.push(`KILL LDR · ${topKill.character_name} ${topKill.kills}K`);
  if (topXP)   bits.push(`XP LDR · ${topXP.character_name} ${Math.round(topXP.xp_total)}xp`);
  if (bits.length === 0) return null;
  return (
    <div className="text-[10px] tracking-widest uppercase font-mono bg-[#1c1208] text-[#f3e9d2] px-2 py-1 max-w-full overflow-hidden whitespace-nowrap">
      ▲ {bits.join("   ·   ")} ▲
    </div>
  );
}


function ScoreTable({ title, rows, cols, testid }) {
  return (
    <div className="border-2 border-[#1c1208] p-3" data-testid={testid}>
      <div className="text-center font-bold uppercase tracking-widest text-xs border-b border-[#1c1208] pb-1 mb-2">
        {title}
      </div>
      {(!rows || rows.length === 0) ? (
        <div className="text-xs italic text-center py-3">— no standings —</div>
      ) : (
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-[#1c1208]">
              <th className="text-left py-0.5 pr-1 w-6">#</th>
              {cols.map(([k, l, num]) => (
                <th key={k} className={`py-0.5 px-1 ${num ? "text-right" : "text-left"} uppercase tracking-wide`}>
                  {l}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 8).map((r, i) => (
              <tr key={i} className="border-b border-dotted border-[#1c1208]/30">
                <td className="py-0.5 pr-1 tabular-nums">{i + 1}</td>
                {cols.map(([k, , num]) => (
                  <td key={k} className={`py-0.5 px-1 ${num ? "text-right tabular-nums" : ""}`}>
                    {num ? Math.round((r[k] || 0) * 10) / 10 : (r[k] || "—")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}


function Colophon() {
  return (
    <div className="text-center py-6 text-[11px] uppercase tracking-[0.3em]"
         data-testid="gazette-colophon">
      <div className="flex items-center justify-center gap-2">
        <Star className="w-3 h-3"/>
        Tablegnostics Press &nbsp;·&nbsp; Set in moveable type, pressed nightly
        <Star className="w-3 h-3"/>
      </div>
      <Link to="/" className="block mt-2 text-[10px] underline">
        Return to TableGnostics →
      </Link>
    </div>
  );
}
