/**
 * NewsRoom — V6.25.38
 *
 * In-app editorial newsroom for the campaign Gazette. GM-curated.
 *
 * Workflow:
 *   1. GM (or LLM) drafts articles. Status goes draft → approved → published.
 *   2. GM clicks "Press the Issue" — every approved article becomes published
 *      under a new numbered issue. Public readers see the latest issue at
 *      /discover/{slug}/gazette (only if discover_published=true).
 *   3. Kill log feeds the box-score leaderboard (kills · XP · sessions).
 */
import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { Newspaper, Sparkles, Send, Trash2, Edit3, Skull,
         Check, ArrowLeft, Loader2 } from "lucide-react";
import { api, formatApiErrorDetail, useAuth } from "../lib/api";

const COLUMNS = [
  { k: "front",        l: "Front Page" },
  { k: "world",        l: "World Wire" },
  { k: "marketplace",  l: "Marketplace" },
  { k: "obituaries",   l: "Obituaries" },
];

export default function NewsRoom() {
  const { id: cid } = useParams();
  const { user } = useAuth();
  const [camp, setCamp] = useState(null);
  const [articles, setArticles] = useState([]);
  const [issues, setIssues] = useState([]);
  const [boards, setBoards] = useState(null);
  const [chars, setChars] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [tab, setTab] = useState("desk");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const reload = useCallback(async () => {
    if (!cid) return;
    const [c, a, i, b, ch, ss] = await Promise.all([
      api.get(`/campaigns/${cid}`).then((r) => r.data).catch(() => null),
      api.get(`/campaigns/${cid}/news/articles`).then((r) => r.data.articles || []).catch(() => []),
      api.get(`/campaigns/${cid}/news/issues`).then((r) => r.data.issues || []).catch(() => []),
      api.get(`/campaigns/${cid}/news/leaderboards`).then((r) => r.data).catch(() => null),
      api.get(`/campaigns/${cid}/characters`).then((r) => r.data || []).catch(() => []),
      api.get(`/campaigns/${cid}/sessions`).then((r) => r.data || []).catch(() => []),
    ]);
    setCamp(c); setArticles(a); setIssues(i); setBoards(b); setChars(ch); setSessions(ss);
  }, [cid]);

  useEffect(() => { reload(); }, [reload]);

  if (!camp) {
    return (
      <div className="px-6 md:px-12 py-10 text-mist text-sm">Loading the desk…</div>
    );
  }
  const isGm = !!camp.is_gm || user?.role === "admin";

  const draftFromSession = async (sid) => {
    setErr(""); setBusy(true);
    try {
      const r = await api.post(`/campaigns/${cid}/news/draft-from-session/${sid}`);
      setBusy(false);
      await reload();
      return r.data;
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail, e));
      setBusy(false);
    }
  };

  const pressIssue = async () => {
    if (!window.confirm("Press the issue? Every approved article will publish to the gazette and lock from further edits.")) return;
    setErr(""); setBusy(true);
    try {
      await api.post(`/campaigns/${cid}/news/issues`, {});
      await reload();
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail, e));
    } finally { setBusy(false); }
  };

  const approvedCount = articles.filter((a) => a.status === "approved").length;
  const draftCount    = articles.filter((a) => a.status === "draft").length;
  const publishedCount = articles.filter((a) => a.status === "published").length;

  return (
    <div className="px-6 md:px-12 py-10 max-w-6xl" data-testid="news-room">
      <div className="mb-6">
        <Link to={`/app/campaigns/${cid}`} className="text-mist hover:text-gold-bright text-xs flex items-center gap-1">
          <ArrowLeft className="w-3 h-3"/> Back to campaign
        </Link>
        <h1 className="font-display tracking-[0.18em] text-3xl text-parchment mt-2 flex items-center gap-3">
          <Newspaper className="w-6 h-6 text-gold-bright"/> The {camp.name} Gazette
        </h1>
        <div className="text-mist text-sm mt-1 max-w-2xl">
          Old-timey newsroom for the campaign. GM curates articles (LLM-drafted
          or hand-typed), approves them, and presses the issue. Public readers
          land at <code className="text-gold-bright">/discover/{camp.discover_slug || "{slug}"}/gazette</code>
          {camp.discover_published ? "" : " — currently NOT publicly visible (toggle Public Showcase on the campaign page)"}.
        </div>
      </div>

      {!isGm && (
        <div className="card-mystic p-4 text-mist text-sm" data-testid="news-readonly">
          You're seated at this table — the newsroom is read-only for players.
          Browse the latest published gazette below.
        </div>
      )}

      <div className="flex gap-2 border-b border-gold/10 mb-4 overflow-x-auto">
        {[
          ["desk",    `Editorial Desk · ${draftCount + approvedCount}`],
          ["press",   `Issues · ${issues.length}`],
          ["scores",  `Leaderboards`],
          ["kills",   `Kill Log`],
        ].map(([k, l]) => (
          <button key={k} type="button" onClick={() => setTab(k)}
                  className={`px-4 py-2 text-xs font-ui tracking-widest uppercase whitespace-nowrap ${tab === k ? "text-gold-bright border-b border-gold" : "text-mist hover:text-parchment"}`}
                  data-testid={`news-tab-${k}`}>
            {l}
          </button>
        ))}
      </div>

      {err && (
        <div className="text-ember text-sm mb-3" data-testid="news-error">{err}</div>
      )}

      {tab === "desk" && (
        <DeskTab cid={cid} isGm={isGm} articles={articles} sessions={sessions}
                 onReload={reload} onDraftFromSession={draftFromSession}
                 busy={busy} approvedCount={approvedCount}
                 publishedCount={publishedCount} onPressIssue={pressIssue}/>
      )}
      {tab === "press" && <IssuesTab issues={issues} articles={articles}/>}
      {tab === "scores" && <ScoresTab boards={boards}/>}
      {tab === "kills" && <KillsTab cid={cid} isGm={isGm} chars={chars}
                                    sessions={sessions} onReload={reload}/>}
    </div>
  );
}


function DeskTab({ cid, isGm, articles, sessions, onReload, onDraftFromSession,
                   busy, approvedCount, publishedCount, onPressIssue }) {
  const [pickedSession, setPickedSession] = useState("");
  const [showCompose, setShowCompose] = useState(false);

  const drafts    = articles.filter((a) => a.status === "draft");
  const approved  = articles.filter((a) => a.status === "approved");
  const published = articles.filter((a) => a.status === "published");

  return (
    <div className="space-y-5">
      {isGm && (
        <div className="card-mystic p-4 flex flex-wrap items-center gap-3"
             data-testid="news-toolbar">
          <select className="select text-xs" value={pickedSession}
                  onChange={(e) => setPickedSession(e.target.value)}
                  data-testid="news-session-select">
            <option value="">— pick a session to draft from —</option>
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                #{s.session_no || "?"} · {s.title || "Untitled"}
              </option>
            ))}
          </select>
          <button type="button" disabled={!pickedSession || busy}
                  onClick={() => onDraftFromSession(pickedSession)}
                  className="btn btn-primary text-xs"
                  data-testid="news-llm-draft-btn">
            {busy ? <Loader2 className="w-3 h-3 animate-spin"/> : <Sparkles className="w-3 h-3"/>}
            {busy ? "Drafting…" : "LLM Draft from Session"}
          </button>
          <button type="button" onClick={() => setShowCompose(!showCompose)}
                  className="btn text-xs" data-testid="news-compose-toggle">
            <Edit3 className="w-3 h-3"/> {showCompose ? "Close composer" : "Compose by hand"}
          </button>
          <div className="flex-1"/>
          <button type="button" disabled={busy || approvedCount === 0}
                  onClick={onPressIssue}
                  className="btn btn-primary text-xs"
                  data-testid="news-press-issue-btn">
            <Send className="w-3 h-3"/> Press the Issue ({approvedCount})
          </button>
        </div>
      )}

      {showCompose && isGm && (
        <Composer cid={cid} onSaved={() => { setShowCompose(false); onReload(); }}/>
      )}

      <ArticleColumn label={`Drafts · ${drafts.length}`} testid="news-col-drafts"
                      articles={drafts} cid={cid} isGm={isGm} onReload={onReload}/>
      <ArticleColumn label={`Approved (queued for next issue) · ${approved.length}`}
                      testid="news-col-approved"
                      articles={approved} cid={cid} isGm={isGm} onReload={onReload}/>
      <ArticleColumn label={`Published archive · ${published.length}`}
                      testid="news-col-published"
                      articles={published} cid={cid} isGm={isGm} onReload={onReload}
                      readOnly/>
    </div>
  );
}


function ArticleColumn({ label, testid, articles, cid, isGm, onReload, readOnly }) {
  if (articles.length === 0) {
    return (
      <div className="card-mystic p-4" data-testid={testid}>
        <div className="label-ref mb-1">{label}</div>
        <div className="text-mist text-xs italic">No articles in this column.</div>
      </div>
    );
  }
  return (
    <div className="card-mystic p-4" data-testid={testid}>
      <div className="label-ref mb-3">{label}</div>
      <div className="space-y-3">
        {articles.map((a) => (
          <ArticleCard key={a.id} a={a} cid={cid} isGm={isGm}
                        onReload={onReload} readOnly={readOnly}/>
        ))}
      </div>
    </div>
  );
}


function ArticleCard({ a, cid, isGm, onReload, readOnly }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({
    headline: a.headline, kicker: a.kicker || "",
    byline: a.byline || "", body: a.body, column: a.column,
  });
  const setStatus = async (status) => {
    try {
      await api.patch(`/campaigns/${cid}/news/articles/${a.id}`, { status });
      await onReload();
    } catch { /* ignore */ }
  };
  const remove = async () => {
    if (!window.confirm("Delete this article? This cannot be undone.")) return;
    try {
      await api.delete(`/campaigns/${cid}/news/articles/${a.id}`);
      await onReload();
    } catch { /* ignore */ }
  };
  const save = async () => {
    try {
      await api.patch(`/campaigns/${cid}/news/articles/${a.id}`, draft);
      setEditing(false);
      await onReload();
    } catch { /* ignore */ }
  };
  return (
    <div className="border border-gold/10 rounded-sm p-3 bg-void/40"
         data-testid={`news-article-${a.id}`}>
      {!editing ? (
        <>
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="min-w-0">
              <div className="text-[9px] uppercase tracking-widest text-gold/70">
                {a.column} · {a.kicker || "—"} {a.generated_by_llm && <span className="text-arcane">· LLM draft</span>}
              </div>
              <div className="text-parchment font-display tracking-wide text-base">
                {a.headline}
              </div>
              <div className="text-[10px] text-mist/70 italic">{a.byline}</div>
            </div>
            <span className={`tag uppercase tracking-widest text-[9px] ${
              a.status === "published" ? "bg-mist/20 text-parchment"
              : a.status === "approved" ? "bg-gold/20 text-gold-bright"
              : "bg-arcane/20 text-arcane"
            }`}>{a.status}</span>
          </div>
          <p className="text-parchment text-sm mt-2 whitespace-pre-wrap leading-relaxed">
            {a.body}
          </p>
          {!readOnly && isGm && (
            <div className="mt-3 flex gap-2 flex-wrap">
              {a.status === "draft" && (
                <button type="button" onClick={() => setStatus("approved")}
                        className="btn btn-primary text-xs"
                        data-testid={`news-approve-${a.id}`}>
                  <Check className="w-3 h-3"/> Approve
                </button>
              )}
              {a.status === "approved" && (
                <button type="button" onClick={() => setStatus("draft")}
                        className="btn text-xs"
                        data-testid={`news-unapprove-${a.id}`}>
                  Send back to drafts
                </button>
              )}
              <button type="button" onClick={() => setEditing(true)}
                      className="btn text-xs"
                      data-testid={`news-edit-${a.id}`}>
                <Edit3 className="w-3 h-3"/> Edit
              </button>
              <button type="button" onClick={remove}
                      className="btn btn-danger text-xs"
                      data-testid={`news-delete-${a.id}`}>
                <Trash2 className="w-3 h-3"/>
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="space-y-2">
          <input className="input text-sm" value={draft.headline}
                 onChange={(e) => setDraft({ ...draft, headline: e.target.value })}
                 placeholder="Headline" data-testid={`news-edit-headline-${a.id}`}/>
          <div className="grid grid-cols-2 gap-2">
            <input className="input text-xs" value={draft.kicker}
                   onChange={(e) => setDraft({ ...draft, kicker: e.target.value })}
                   placeholder="Kicker"/>
            <input className="input text-xs" value={draft.byline}
                   onChange={(e) => setDraft({ ...draft, byline: e.target.value })}
                   placeholder="Byline"/>
          </div>
          <select className="select text-xs" value={draft.column}
                  onChange={(e) => setDraft({ ...draft, column: e.target.value })}>
            {COLUMNS.map((c) => <option key={c.k} value={c.k}>{c.l}</option>)}
          </select>
          <textarea className="input text-sm min-h-[100px]" value={draft.body}
                    onChange={(e) => setDraft({ ...draft, body: e.target.value })}
                    placeholder="Body" data-testid={`news-edit-body-${a.id}`}/>
          <div className="flex gap-2">
            <button type="button" onClick={save} className="btn btn-primary text-xs"
                    data-testid={`news-save-${a.id}`}>Save</button>
            <button type="button" onClick={() => setEditing(false)} className="btn text-xs">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}


function Composer({ cid, onSaved }) {
  const [d, setD] = useState({ headline: "", kicker: "", byline: "", body: "", column: "front" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async () => {
    setErr(""); setBusy(true);
    try {
      await api.post(`/campaigns/${cid}/news/articles`, d);
      onSaved();
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail, e));
    } finally { setBusy(false); }
  };
  return (
    <div className="card-mystic p-4 space-y-2" data-testid="news-composer">
      <div className="label-ref">Compose new article</div>
      <input className="input text-sm" value={d.headline}
             onChange={(e) => setD({ ...d, headline: e.target.value })}
             placeholder="Headline" data-testid="compose-headline"/>
      <div className="grid grid-cols-2 gap-2">
        <input className="input text-xs" value={d.kicker}
               onChange={(e) => setD({ ...d, kicker: e.target.value })}
               placeholder="Kicker (subtitle)"/>
        <input className="input text-xs" value={d.byline}
               onChange={(e) => setD({ ...d, byline: e.target.value })}
               placeholder="Byline (e.g. By Edward Lucent)"/>
      </div>
      <select className="select text-xs" value={d.column}
              onChange={(e) => setD({ ...d, column: e.target.value })}>
        {COLUMNS.map((c) => <option key={c.k} value={c.k}>{c.l}</option>)}
      </select>
      <textarea className="input text-sm min-h-[120px]" value={d.body}
                onChange={(e) => setD({ ...d, body: e.target.value })}
                placeholder="80-150 words. Period-appropriate broadsheet voice."
                data-testid="compose-body"/>
      <div className="flex gap-2 items-center">
        <button type="button" onClick={submit} disabled={busy}
                className="btn btn-primary text-xs"
                data-testid="compose-submit">
          {busy ? "Filing…" : "File draft"}
        </button>
        {err && <span className="text-ember text-[11px]">{err}</span>}
      </div>
    </div>
  );
}


function IssuesTab({ issues, articles }) {
  if (issues.length === 0) {
    return (
      <div className="card-mystic p-6 text-mist text-sm text-center">
        No issues pressed yet. Approve drafts on the Editorial Desk and click
        <span className="text-gold-bright"> Press the Issue</span>.
      </div>
    );
  }
  return (
    <div className="space-y-4" data-testid="news-issues-list">
      {issues.map((i) => {
        const arts = articles.filter((a) => a.issue_id === i.id);
        return (
          <div key={i.id} className="card-mystic p-4"
               data-testid={`news-issue-${i.id}`}>
            <div className="font-display tracking-[0.18em] text-xl text-parchment">
              {i.masthead}
            </div>
            <div className="text-[10px] text-gold/70 uppercase tracking-widest mt-1">
              Issue No. {i.issue_number} · {i.date_label} · {arts.length} articles
            </div>
            <div className="mt-3 space-y-2">
              {arts.map((a) => (
                <div key={a.id} className="border-l-2 border-gold/30 pl-3">
                  <div className="text-[9px] uppercase tracking-widest text-gold/60">
                    {a.column}
                  </div>
                  <div className="text-parchment text-sm">{a.headline}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}


function ScoresTab({ boards }) {
  if (!boards) {
    return <div className="card-mystic p-6 text-mist text-sm">Loading scores…</div>;
  }
  return (
    <div className="space-y-4" data-testid="news-scores-tab">
      <BoxScore label="Kill Count · the mer der hoh bohs"
                rows={boards.kills}
                cols={[
                  { k: "character_name", l: "Character" },
                  { k: "kills", l: "Kills", num: true },
                  { k: "last_kill_at", l: "Last Felled" },
                ]}
                testid="boxscore-kills"/>
      <BoxScore label="XP Standings"
                rows={boards.xp}
                cols={[
                  { k: "character_name", l: "Character" },
                  { k: "owner_name", l: "Player" },
                  { k: "xp_total", l: "XP", num: true },
                ]}
                testid="boxscore-xp"/>
      <BoxScore label="Sessions Logged (voice presence)"
                rows={boards.sessions}
                cols={[
                  { k: "character_name", l: "Character" },
                  { k: "session_count", l: "Sessions", num: true },
                ]}
                testid="boxscore-sessions"/>
      <BoxScore label="Player Roster · Total XP across characters"
                rows={boards.players}
                cols={[
                  { k: "owner_name", l: "Player" },
                  { k: "character_count", l: "Heroes", num: true },
                  { k: "total_xp", l: "Combined XP", num: true },
                ]}
                testid="boxscore-players"/>
    </div>
  );
}


function BoxScore({ label, rows, cols, testid }) {
  return (
    <div className="card-mystic p-4" data-testid={testid}>
      <div className="label-ref mb-2">{label}</div>
      {(!rows || rows.length === 0) ? (
        <div className="text-mist text-xs italic">No standings yet.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gold/20">
                <th className="text-left py-1.5 pr-2 text-gold/70 uppercase tracking-widest text-[10px]">#</th>
                {cols.map((c) => (
                  <th key={c.k} className={`py-1.5 px-2 text-gold/70 uppercase tracking-widest text-[10px] ${c.num ? "text-right" : "text-left"}`}>
                    {c.l}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-gold/5 hover:bg-gold/5">
                  <td className="py-1.5 pr-2 text-gold-bright tabular-nums">{i + 1}</td>
                  {cols.map((c) => (
                    <td key={c.k} className={`py-1.5 px-2 ${c.num ? "text-right tabular-nums text-parchment" : "text-parchment"}`}>
                      {c.num ? Math.round((r[c.k] || 0) * 10) / 10 : (r[c.k] || "—")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


function KillsTab({ cid, isGm, chars, sessions, onReload }) {
  const [k, setK] = useState({ character_id: "", foe_name: "", foe_kind: "", session_id: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async () => {
    setErr(""); setBusy(true);
    try {
      await api.post(`/campaigns/${cid}/news/log-kill`, k);
      setK({ character_id: "", foe_name: "", foe_kind: "", session_id: "" });
      onReload();
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail, e));
    } finally { setBusy(false); }
  };
  if (!isGm) {
    return (
      <div className="card-mystic p-4 text-mist text-sm">
        Only the GM may log kills. Browse the leaderboard tab for current standings.
      </div>
    );
  }
  return (
    <div className="card-mystic p-4 space-y-2" data-testid="news-kills-form">
      <div className="label-ref flex items-center gap-2">
        <Skull className="w-4 h-4 text-ember"/> Log a kill
      </div>
      <div className="grid md:grid-cols-2 gap-2">
        <select className="select text-xs" value={k.character_id}
                onChange={(e) => setK({ ...k, character_id: e.target.value })}
                data-testid="kill-character-select">
          <option value="">— picker the felling hero —</option>
          {chars.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className="select text-xs" value={k.session_id}
                onChange={(e) => setK({ ...k, session_id: e.target.value })}>
          <option value="">— session (optional) —</option>
          {sessions.map((s) => <option key={s.id} value={s.id}>#{s.session_no} {s.title}</option>)}
        </select>
        <input className="input text-xs" value={k.foe_name}
               onChange={(e) => setK({ ...k, foe_name: e.target.value })}
               placeholder="Foe name"
               data-testid="kill-foe-name"/>
        <input className="input text-xs" value={k.foe_kind}
               onChange={(e) => setK({ ...k, foe_kind: e.target.value })}
               placeholder="Foe kind (dragon, bandit, lich…)"/>
      </div>
      <div className="flex gap-2 items-center">
        <button type="button" onClick={submit}
                disabled={busy || !k.character_id || !k.foe_name}
                className="btn btn-primary text-xs"
                data-testid="kill-submit">
          {busy ? "Logging…" : "Log kill"}
        </button>
        {err && <span className="text-ember text-[11px]">{err}</span>}
      </div>
    </div>
  );
}
