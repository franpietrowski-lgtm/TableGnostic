import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Spade, RefreshCw, Eye, EyeOff, Plus, Trash2, Sparkles } from "lucide-react";

/**
 * CardDeckPanel — system-aware card drawing.
 *
 * Three deck shapes covered:
 *   - D&D 5E Deck of Many Things (22 trump cards · GM-only by default)
 *   - Cypher Draw (random cypher from the active SRD list)
 *   - Anime 5E Genre Shift Deck (narrative cards)
 *   - TableGnostic Mood Deck (universal · ceremonial Session 0 tone-set)
 *
 * BESM 4E doesn't natively use cards but TableGnostic Mood Deck is offered
 * to any system that opts in — the user's "even though BESM doesn't use
 * them, card options should be available" requirement.
 */
export default function CardDeckPanel({ campaignId, systemId, sessionId, isGm }) {
  const [catalogue, setCatalogue] = useState([]);
  const [instances, setInstances] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [draws, setDraws] = useState({});
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const reloadInstances = async () => {
    try {
      const { data } = await api.get(`/cards/instances?campaign_id=${campaignId}`);
      setInstances(data);
      if (!activeId && data.length) setActiveId(data[0].id);
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/cards/decks/${systemId || "besm-4e"}`);
        setCatalogue(data.decks || []);
      } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
      await reloadInstances();
    })();
    // eslint-disable-next-line
  }, [campaignId, systemId]);

  const createInstance = async (deckId) => {
    setBusy(true); setErr("");
    try {
      await api.post("/cards/instances", {
        campaign_id: campaignId, session_id: sessionId || null, deck_id: deckId,
      });
      await reloadInstances();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const drawCard = async () => {
    if (!activeId) return;
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/cards/instances/${activeId}/draw`, { count: 1 });
      setDraws((prev) => ({ ...prev, [activeId]: [data.cards[0], ...(prev[activeId] || [])] }));
      await reloadInstances();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const shuffle = async () => {
    if (!activeId) return;
    setBusy(true);
    try {
      await api.post(`/cards/instances/${activeId}/shuffle`);
      setDraws((prev) => ({ ...prev, [activeId]: [] }));
      await reloadInstances();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const flipMode = async () => {
    if (!activeId) return;
    const cur = instances.find((i) => i.id === activeId);
    if (!cur) return;
    const nextMode = cur.mode === "open" ? "gm-only" : "open";
    try {
      await api.post(`/cards/instances/${activeId}/mode?mode=${nextMode}`);
      await reloadInstances();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  const deleteInstance = async () => {
    if (!activeId || !window.confirm("Delete this deck instance?")) return;
    try {
      await api.delete(`/cards/instances/${activeId}`);
      setActiveId(null);
      await reloadInstances();
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };

  const active = instances.find((i) => i.id === activeId);
  const recentDraws = activeId ? (draws[activeId] || []) : [];
  const remaining = active ? Math.max(0, (catalogue.find((c) => c.id === active.deck_id)?.size || 0) - (active.drawn_card_ids?.length || 0)) : 0;

  return (
    <div className="card-mystic p-4" data-testid="card-deck-panel">
      <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
        <div>
          <div className="label-ref flex items-center gap-2">
            <Spade className="w-3 h-3"/> Card Decks
          </div>
          <div className="text-[10px] text-mist/70 italic">
            System-aware ceremonial &amp; mechanic decks · drawn cards are logged.
          </div>
        </div>
      </div>
      {err && <div className="text-ember text-xs mb-2" data-testid="card-deck-err">{err}</div>}

      {/* Catalogue — GM-only spawn buttons */}
      {isGm && (
        <div className="mb-4 border-b border-gold/10 pb-3">
          <div className="text-[10px] font-ui uppercase tracking-widest text-mist mb-1.5">Available decks</div>
          <div className="flex flex-wrap gap-1.5">
            {catalogue.map((d) => (
              <button key={d.id} onClick={() => createInstance(d.id)} disabled={busy}
                      className="btn btn-ghost text-[10px]"
                      data-testid={`card-deck-spawn-${d.id}`}
                      title={d.compliance}>
                <Plus className="w-3 h-3"/> {d.name} ({d.size})
              </button>
            ))}
            {catalogue.length === 0 && (
              <span className="text-[11px] text-mist italic">No decks available for this system.</span>
            )}
          </div>
        </div>
      )}

      {/* Active instance picker */}
      {instances.length > 0 ? (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1">
            {instances.map((i) => {
              const meta = catalogue.find((c) => c.id === i.deck_id);
              return (
                <button key={i.id} onClick={() => setActiveId(i.id)}
                        className={`text-[10px] px-2 py-1 rounded-sm font-ui uppercase tracking-widest transition-colors ${activeId === i.id ? "bg-gold/15 text-gold-bright border border-gold/30" : "text-mist hover:bg-gold/5"}`}
                        data-testid={`card-instance-${i.id}`}>
                  {meta?.name || i.deck_id} · {i.drawn_card_ids?.length || 0}/{meta?.size || "?"}
                </button>
              );
            })}
          </div>

          {active && (
            <>
              <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-mist">Mode:</span>
                  <span className={`tag ${active.mode === "open" ? "border-gold/60 text-gold-bright" : "border-ember/40 text-ember"}`}
                        data-testid={`card-mode-${active.id}`}>
                    {active.mode}
                  </span>
                  <span className="text-mist/60">{remaining} of {catalogue.find((c) => c.id === active.deck_id)?.size || "?"} left</span>
                </div>
                <div className="flex gap-1.5">
                  {(isGm || active.mode === "open") && (
                    <button onClick={drawCard} disabled={busy || remaining === 0}
                            className="btn btn-primary text-xs"
                            data-testid="card-draw-btn">
                      <Sparkles className="w-3 h-3"/> Draw
                    </button>
                  )}
                  {isGm && (
                    <>
                      <button onClick={shuffle} disabled={busy}
                              className="btn btn-ghost text-xs"
                              data-testid="card-shuffle-btn">
                        <RefreshCw className="w-3 h-3"/> Shuffle
                      </button>
                      <button onClick={flipMode} className="btn btn-ghost text-xs"
                              data-testid="card-mode-toggle">
                        {active.mode === "open"
                          ? <><EyeOff className="w-3 h-3"/> Close to GM</>
                          : <><Eye className="w-3 h-3"/> Open to table</>}
                      </button>
                      <button onClick={deleteInstance} className="btn btn-ghost text-xs text-ember/70"
                              data-testid="card-delete-btn">
                        <Trash2 className="w-3 h-3"/>
                      </button>
                    </>
                  )}
                </div>
              </div>

              {recentDraws.length > 0 ? (
                <div className="space-y-2 max-h-72 overflow-auto" data-testid="card-recent-draws">
                  {recentDraws.map((c, i) => (
                    <div key={`${c.id}-${i}`}
                         className="border border-gold/30 rounded-sm p-3 bg-gold/5"
                         data-testid={`card-draw-${c.id}`}>
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="font-display text-base text-gold-bright">{c.name}</div>
                        {c.suit && <span className="text-[10px] text-mist uppercase tracking-widest">{c.suit}</span>}
                        {c.rank && <span className="text-[10px] text-mist">{c.rank}</span>}
                      </div>
                      <div className="text-[12px] text-parchment/90 leading-snug">{c.effect}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-mist italic text-xs">Tap Draw to pull a card.</div>
              )}

              {/* Draw history footer */}
              {(active.log || []).length > 0 && (
                <details className="text-[10px] text-mist/70 mt-2"
                         data-testid="card-draw-log">
                  <summary className="cursor-pointer hover:text-parchment">
                    History · {(active.log || []).length} draws
                  </summary>
                  <ul className="mt-1 space-y-0.5 ml-2">
                    {(active.log || []).slice(-20).reverse().map((l, i) => (
                      <li key={i}>· <b>{l.by_name}</b> drew <i>{l.card_name}</i></li>
                    ))}
                  </ul>
                </details>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="text-mist italic text-xs">
          {isGm ? "No decks created yet — pick one from the catalogue above." : "The GM hasn't put any decks on the table yet."}
        </div>
      )}
    </div>
  );
}
