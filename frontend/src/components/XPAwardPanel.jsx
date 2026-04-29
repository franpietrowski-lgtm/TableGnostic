import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { X, Sparkles, BookOpen, Check, Info } from "lucide-react";

/**
 * XPAwardPanel — GM session-end XP scorecard (BESM 4E p.232 Advancement).
 *
 * Suggest-only: backend tallies engagement quanta (IC chat, OOC chat,
 * dice macros, journal entries, GM-flagged spotlight) and proposes a
 * per-PC base + bonus. The GM edits values inline and clicks Commit;
 * nothing writes until then.
 *
 * Per user choice (V4.4 ask_human #2 = a): suggest only, never auto-award.
 * IC chat is weighted higher than OOC (V4.4 ask_human #3 = c) — handled
 * server-side in routes/xp.WEIGHTS.
 */
export default function XPAwardPanel({ sessionId, campaign, onClose, onCommitted }) {
  const [card, setCard] = useState(null);
  const [edits, setEdits] = useState({});  // { character_id: { base, bonus, spotlight, note } }
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [committed, setCommitted] = useState(null);
  // Which row's bonus-breakdown popover is open (character_id or null).
  const [openBreakdown, setOpenBreakdown] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get(`/sessions/${sessionId}/xp/suggest`).then(({ data }) => {
      if (!mounted) return;
      setCard(data);
      const seed = {};
      for (const r of data.rows) {
        seed[r.character_id] = {
          base: r.suggested_base,
          bonus: r.bonus,
          spotlight: 0,
          note: "",
        };
      }
      setEdits(seed);
    }).catch((e) => setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message));
    return () => { mounted = false; };
  }, [sessionId]);

  if (err) return <Shell onClose={onClose}><div className="text-ember">{err}</div></Shell>;
  if (!card) return <Shell onClose={onClose}><div className="text-mist italic">Tallying engagement…</div></Shell>;

  const update = (cid, patch) => setEdits((p) => ({ ...p, [cid]: { ...p[cid], ...patch } }));

  // Spotlight is a fractional bonus the GM toggles on a PC who carried a
  // scene. It stacks on top of the auto-bonus, then both are capped at the
  // server-reported bonus_cap before commit.
  const effectiveBonus = (cid) => {
    const e = edits[cid] || {};
    const sp = +(e.spotlight || 0);
    return Math.min(card.bonus_cap, +(e.bonus || 0) + sp);
  };

  const commit = async () => {
    setBusy(true); setErr("");
    try {
      const awards = card.rows.map((r) => ({
        character_id: r.character_id,
        base: +(edits[r.character_id]?.base ?? r.suggested_base),
        bonus: effectiveBonus(r.character_id),
        note: (edits[r.character_id]?.note || "").trim() || `${card.session_id ? "Session" : "Award"} XP`,
      }));
      const { data } = await api.post(`/sessions/${sessionId}/xp/commit`, { awards });
      setCommitted(data.committed);
      onCommitted && onCommitted();
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Shell onClose={onClose}>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <div className="label-ref flex items-center gap-2"><Sparkles className="w-3 h-3"/> Session XP · Scorecard</div>
          <div className="text-[11px] text-mist/70 italic mt-1 flex items-center gap-1">
            <BookOpen className="w-3 h-3"/> {card.guidance}
          </div>
        </div>
        <button onClick={onClose} className="btn btn-ghost p-2"><X className="w-4 h-4"/></button>
      </div>

      <table className="w-full text-sm" data-testid="xp-scorecard-table">
        <thead className="text-[10px] font-ui uppercase tracking-widest text-gold/60">
          <tr className="border-b border-gold/15">
            <th className="text-left py-2">Character</th>
            <th className="text-right py-2">IC</th>
            <th className="text-right py-2">OOC</th>
            <th className="text-right py-2">Dice</th>
            <th className="text-right py-2">Journal</th>
            <th className="text-center py-2">Spotlight</th>
            <th className="text-right py-2">Base</th>
            <th className="text-right py-2">Bonus</th>
            <th className="text-right py-2">Total</th>
            <th className="text-left py-2 pl-2">Note</th>
          </tr>
        </thead>
        <tbody>
          {card.rows.length === 0 && (
            <tr>
              <td colSpan={10} className="py-6 text-center text-mist italic text-xs" data-testid="xp-scorecard-empty">
                No characters seated in this session yet. Seat a character
                from the session toolbar (Seating → assign a player to a
                character) then reopen this panel.
              </td>
            </tr>
          )}
          {card.rows.map((r) => {
            const e = edits[r.character_id] || {};
            const total = (+e.base || 0) + effectiveBonus(r.character_id);
            return (
              <tr key={r.character_id}
                  className="border-b border-gold/5"
                  data-testid={`xp-row-${r.character_id}`}>
                <td className="py-2">
                  <div className="flex items-center gap-2">
                    {r.token_color && (
                      <span className="inline-block w-3 h-3 rounded-full"
                            style={{ backgroundColor: r.token_color }}/>
                    )}
                    <span className="font-display text-parchment">{r.character_name}</span>
                  </div>
                  <div className="text-[10px] text-mist font-ui">{r.owner_name}</div>
                </td>
                <td className="text-right text-mist tabular-nums">{r.counts.chat_ic}</td>
                <td className="text-right text-mist tabular-nums">{r.counts.chat_ooc}</td>
                <td className="text-right text-mist tabular-nums">{r.counts.dice_macro}</td>
                <td className="text-right text-mist tabular-nums">{r.counts.journal}</td>
                <td className="text-center">
                  <input type="checkbox"
                         checked={!!e.spotlight}
                         onChange={(ev) => update(r.character_id, {
                           spotlight: ev.target.checked ? card.weights.spotlight : 0,
                         })}
                         data-testid={`xp-spotlight-${r.character_id}`}
                         title={`+${card.weights.spotlight} XP — GM flag for "carried this scene"`}/>
                </td>
                <td className="text-right">
                  <input type="number" step="0.5" min={0} max={5}
                         className="input w-16 text-right text-xs py-1"
                         value={e.base ?? r.suggested_base}
                         onChange={(ev) => update(r.character_id, { base: ev.target.value })}
                         data-testid={`xp-base-${r.character_id}`}/>
                </td>
                <td className="text-right">
                  <div className="inline-flex items-center gap-1 relative">
                    <input type="number" step="0.05" min={0} max={card.bonus_cap}
                           className="input w-20 text-right text-xs py-1"
                           value={e.bonus ?? r.bonus}
                           onChange={(ev) => update(r.character_id, { bonus: ev.target.value })}
                           title={`Auto-suggested ${r.bonus} from breakdown`}
                           data-testid={`xp-bonus-${r.character_id}`}/>
                    <button type="button"
                            onClick={() => setOpenBreakdown(
                              openBreakdown === r.character_id ? null : r.character_id)}
                            className="text-mist/60 hover:text-gold-bright"
                            title="Per-quantum bonus breakdown"
                            data-testid={`xp-breakdown-btn-${r.character_id}`}>
                      <Info className="w-3 h-3"/>
                    </button>
                    {openBreakdown === r.character_id && (
                      <div className="absolute right-0 top-7 z-40 w-64 card-mystic p-3 text-left shadow-xl"
                           data-testid={`xp-breakdown-popover-${r.character_id}`}>
                        <div className="label-ref mb-2">Bonus breakdown</div>
                        <table className="w-full text-[11px]">
                          <tbody>
                            {Object.entries(r.bonus_breakdown || {}).map(([k, v]) => (
                              <tr key={k} className="border-b border-gold/5">
                                <td className="py-1 text-parchment/80 capitalize">
                                  {k.replace(/_/g, " ")}
                                </td>
                                <td className="py-1 text-right text-mist tabular-nums">
                                  {r.counts[k] || 0} × {card.weights[k]}
                                </td>
                                <td className="py-1 text-right font-display text-gold tabular-nums">
                                  {Number(v).toFixed(2)}
                                </td>
                              </tr>
                            ))}
                            {Object.keys(r.bonus_breakdown || {}).length === 0 && (
                              <tr><td className="text-mist italic py-2" colSpan={3}>
                                No engagement quanta in this session window.
                              </td></tr>
                            )}
                          </tbody>
                          <tfoot>
                            <tr className="border-t border-gold/20">
                              <td className="pt-1 text-[10px] text-mist uppercase tracking-widest">Subtotal</td>
                              <td></td>
                              <td className="pt-1 text-right font-display text-gold-bright">{r.bonus.toFixed(2)}</td>
                            </tr>
                            {!!edits[r.character_id]?.spotlight && (
                              <tr>
                                <td className="text-[10px] text-arcane-light uppercase tracking-widest">+ Spotlight</td>
                                <td></td>
                                <td className="text-right text-arcane-light tabular-nums">
                                  +{Number(edits[r.character_id].spotlight).toFixed(2)}
                                </td>
                              </tr>
                            )}
                            <tr>
                              <td className="text-[10px] text-mist uppercase tracking-widest">Capped at</td>
                              <td></td>
                              <td className="text-right text-mist tabular-nums">+{card.bonus_cap.toFixed(2)}</td>
                            </tr>
                          </tfoot>
                        </table>
                        <button type="button" onClick={() => setOpenBreakdown(null)}
                                className="btn btn-ghost text-[10px] mt-2 w-full"
                                data-testid={`xp-breakdown-close-${r.character_id}`}>
                          close
                        </button>
                      </div>
                    )}
                  </div>
                </td>
                <td className="text-right font-display text-gold tabular-nums" data-testid={`xp-total-${r.character_id}`}>
                  {total.toFixed(2)}
                </td>
                <td className="pl-2">
                  <input className="input text-xs py-1"
                         value={e.note || ""}
                         onChange={(ev) => update(r.character_id, { note: ev.target.value })}
                         placeholder="Why this award? (optional)"
                         data-testid={`xp-note-${r.character_id}`}/>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {committed && (
        <div className="mt-3 text-arcane-light text-xs flex items-center gap-1" data-testid="xp-committed-banner">
          <Check className="w-3 h-3"/> Committed {committed.length} awards.
        </div>
      )}

      <div className="mt-4 flex items-center justify-between gap-3 flex-wrap">
        <div className="text-[10px] text-mist/70 italic">
          Bonus cap +{card.bonus_cap} · weights: IC {card.weights.chat_ic} / OOC {card.weights.chat_ooc} /
          dice {card.weights.dice_macro} / journal {card.weights.journal} / spotlight {card.weights.spotlight}.
        </div>
        <div className="flex gap-2">
          <button onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
          <button onClick={commit} disabled={busy}
                  className="btn btn-primary text-xs" data-testid="xp-commit-btn">
            {busy ? "Committing…" : "Commit awards"}
          </button>
        </div>
      </div>
    </Shell>
  );
}

function Shell({ children, onClose }) {
  return (
    <div className="fixed inset-0 z-40 bg-void/90 backdrop-blur-sm flex items-start justify-center p-3 md:p-6 overflow-auto"
         data-testid="xp-panel-overlay"
         onClick={(e) => { if (e.target === e.currentTarget) onClose && onClose(); }}>
      <div className="w-full max-w-5xl card-mystic p-5 mt-10">
        {children}
      </div>
    </div>
  );
}
