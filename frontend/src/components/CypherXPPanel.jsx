/**
 * CypherXPPanel — V6.25.24 (Cycle B-4)
 *
 * Surfaces Cypher's living XP economy on a character sheet:
 *   • Award log (reverse-chrono ledger)
 *   • Quick-spend buttons: Re-roll, Refuse Intrusion, Player Intrusion,
 *     Short/Med/Long-term Benefit, Advancement Step
 *   • Peer XP Transfer modal (pick a peer character + justification)
 *   • Narrative Pool authoring (multi-contributor authoring)
 *   • GM-only: Award Intrusion (auto-pairs with peer share rule)
 *
 * All actions hit POST /api/campaigns/{cid}/cypher/xp-events; the ledger
 * lives on the same endpoint with GET. Atomically debits xp_unspent so
 * the floating CP / XP widget on the sheet auto-refreshes.
 */
import React, { useEffect, useState, useMemo } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import {
  Sparkles, Coins, Users, ScrollText, Loader2, Plus, X, Award,
  RotateCcw, ShieldOff, Wand2,
} from "lucide-react";

const SPEND_BUTTONS = [
  { kind: "reroll",                cost: 1, label: "Re-roll",            Icon: RotateCcw,
    hint: "Re-roll any die you just rolled (1 XP)." },
  { kind: "refuse-intrusion",      cost: 1, label: "Refuse Intrusion",   Icon: ShieldOff,
    hint: "Decline the GM's intrusion (1 XP). Cannot refuse with 0 XP." },
  { kind: "player-intrusion",      cost: 1, label: "Player Intrusion",   Icon: Wand2,
    hint: "Introduce a beneficial twist on your turn (1 XP — GM ratifies)." },
  { kind: "short-term-benefit",    cost: 2, label: "Short-term Benefit", Icon: Coins,
    hint: "Recover from a minor setback (2 XP)." },
  { kind: "medium-term-benefit",   cost: 3, label: "Med-term Benefit",   Icon: Coins,
    hint: "Gain a session-long contact / asset (3 XP)." },
  { kind: "long-term-benefit",     cost: 4, label: "Long-term Benefit",  Icon: Coins,
    hint: "Establish a permanent contact / claim (4 XP)." },
];

const ADVANCEMENT_STEPS = [
  { key: "increasing-capabilities", name: "Increasing Capabilities" },
  { key: "moving-toward-perfection", name: "Moving Toward Perfection" },
  { key: "extra-effort",             name: "Extra Effort" },
  { key: "skill-training",           name: "Skill Training" },
];


export default function CypherXPPanel({ campId, character, isGm, onChange }) {
  const [events, setEvents] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [transferOpen, setTransferOpen] = useState(false);
  const [poolOpen, setPoolOpen] = useState(false);
  const [grantOpen, setGrantOpen] = useState(false);
  const [advOpen, setAdvOpen] = useState(false);
  const [peers, setPeers] = useState([]);
  const xp = Number(character?.xp_unspent || 0);

  // Reload ledger.
  const refreshLedger = async () => {
    try {
      const r = await api.get(
        `/campaigns/${campId}/cypher/xp-events?character_id=${character.id}&limit=20`);
      setEvents(r.data?.rows || []);
    } catch (e) {
      // Soft-fail: empty ledger.
      setEvents([]);
    }
  };

  // Reload peers (other party characters in the same campaign).
  useEffect(() => {
    if (!campId || !character?.id) return;
    api.get(`/campaigns/${campId}/characters`).then((r) => {
      const all = r.data?.characters || r.data || [];
      setPeers(all.filter((c) => c.id !== character.id));
    }).catch(() => setPeers([]));
    refreshLedger();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campId, character?.id]);

  const post = async (body) => {
    setErr(""); setBusy(true);
    try {
      const r = await api.post(
        `/campaigns/${campId}/cypher/xp-events`, body);
      onChange && onChange(r.data?.xp_unspent);
      window.dispatchEvent(new Event("tg:character-mutated"));
      await refreshLedger();
      return r.data;
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const handleSpend = async (kind) => {
    if (kind === "refuse-intrusion" && xp < 1) {
      setErr("Cannot refuse a GM intrusion with 0 XP.");
      return;
    }
    await post({ kind, character_id: character.id });
  };

  return (
    <div className="card-mystic p-4 space-y-3"
         data-testid="cypher-xp-panel">
      <div className="flex items-baseline justify-between flex-wrap gap-2 border-b border-gold/10 pb-2">
        <div>
          <div className="h-arcane text-sm flex items-center gap-2">
            <Sparkles className="w-3 h-3"/> Cypher XP Economy
          </div>
          <div className="text-[10px] text-mist italic">
            Intrusion / Refusal / Peer Transfer / Narrative Pool
          </div>
        </div>
        <div className="text-xs"
             data-testid="cypher-xp-balance">
          <span className="text-mist">unspent </span>
          <span className="text-gold-bright font-display text-base tabular-nums">{xp}</span>
          <span className="text-mist"> XP</span>
        </div>
      </div>

      {/* Quick spends */}
      <div>
        <div className="label-ref">Quick spends</div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
          {SPEND_BUTTONS.map((s) => {
            const I = s.Icon;
            const disabled = busy || xp < s.cost;
            return (
              <button key={s.kind}
                      disabled={disabled}
                      onClick={() => handleSpend(s.kind)}
                      title={s.hint}
                      className="btn btn-ghost text-xs justify-start"
                      data-testid={`cypher-spend-${s.kind}`}>
                <I className="w-3 h-3"/>
                <span className="truncate">{s.label}</span>
                <span className="text-[10px] text-arcane-light ml-auto">−{s.cost}</span>
              </button>
            );
          })}
          <button onClick={() => setAdvOpen(true)}
                  disabled={busy || xp < 4}
                  className="btn btn-ghost text-xs justify-start"
                  title="Buy one of the four canonical advancement steps (4 XP each). Complete all four to advance a tier."
                  data-testid="cypher-spend-advancement-step">
            <Award className="w-3 h-3"/>
            <span className="truncate">Advancement Step</span>
            <span className="text-[10px] text-arcane-light ml-auto">−4</span>
          </button>
          <button onClick={() => setTransferOpen(true)}
                  disabled={busy || xp < 1 || peers.length === 0}
                  className="btn btn-ghost text-xs justify-start"
                  title="Hand 1 XP to another character with a brief narrative justification."
                  data-testid="cypher-peer-transfer-btn">
            <Users className="w-3 h-3"/>
            <span className="truncate">Peer Transfer</span>
            <span className="text-[10px] text-arcane-light ml-auto">−1</span>
          </button>
          <button onClick={() => setPoolOpen(true)}
                  disabled={busy}
                  className="btn btn-ghost text-xs justify-start"
                  title="Multi-player co-funded setting-shaping spend (typically 4-12 XP)."
                  data-testid="cypher-narrative-pool-btn">
            <ScrollText className="w-3 h-3"/>
            <span className="truncate">Narrative Pool</span>
            <span className="text-[10px] text-arcane-light ml-auto">var</span>
          </button>
        </div>
      </div>

      {/* GM-only awards */}
      {isGm && (
        <div>
          <div className="label-ref">GM awards</div>
          <button onClick={() => setGrantOpen(true)}
                  disabled={busy}
                  className="btn btn-primary text-xs"
                  title="Inject a complication. Acceptor gets 2 XP and immediately hands 1 to a peer."
                  data-testid="cypher-grant-intrusion-btn">
            <Plus className="w-3 h-3"/> Award GM Intrusion (+2 / +1 peer)
          </button>
        </div>
      )}

      {err && (
        <div className="text-ember text-xs" data-testid="cypher-xp-error">{err}</div>
      )}

      {/* Ledger */}
      <div>
        <div className="label-ref">Ledger</div>
        {events.length === 0 && (
          <div className="text-mist italic text-[11px]"
               data-testid="cypher-xp-ledger-empty">
            No XP events yet. Awards and spends appear here in reverse-chronological order.
          </div>
        )}
        {events.length > 0 && (
          <ul className="text-[11px] divide-y divide-gold/5"
              data-testid="cypher-xp-ledger">
            {events.map((e) => (
              <li key={e.id} className="py-1.5 flex justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="text-parchment">
                    <span className={e.delta >= 0 ? "text-gold-bright" : "text-ember"}>
                      {e.delta >= 0 ? "+" : ""}{e.delta} XP
                    </span>
                    <span className="text-mist"> · </span>
                    <span>{e.kind}</span>
                    {e.peer_character_name && (
                      <span className="text-mist"> ↔ {e.peer_character_name}</span>
                    )}
                  </div>
                  {e.justification && (
                    <div className="text-mist italic text-[10px] truncate"
                         title={e.justification}>"{e.justification}"</div>
                  )}
                </div>
                <div className="text-mist text-[9px] tabular-nums whitespace-nowrap">
                  {e.created_at?.slice(0, 16).replace("T", " ")}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Modals */}
      {transferOpen && (
        <PeerTransferModal
          peers={peers}
          onClose={() => setTransferOpen(false)}
          onSubmit={async ({ peerId, justification }) => {
            await post({ kind: "peer-transfer", character_id: character.id,
              peer_character_id: peerId, justification });
            setTransferOpen(false);
          }}/>
      )}
      {poolOpen && (
        <NarrativePoolModal
          peers={[character, ...peers]}
          onClose={() => setPoolOpen(false)}
          onSubmit={async ({ contributors, justification }) => {
            await post({
              kind: "narrative-pool",
              character_id: character.id,
              narrative_pool_contributors: contributors,
              justification,
            });
            setPoolOpen(false);
          }}/>
      )}
      {grantOpen && isGm && (
        <GrantIntrusionModal
          character={character}
          peers={peers}
          onClose={() => setGrantOpen(false)}
          onSubmit={async ({ peerId, justification }) => {
            await post({
              kind: "intrusion-grant",
              character_id: character.id,
              peer_character_id: peerId || null,
              justification,
            });
            setGrantOpen(false);
          }}/>
      )}
      {advOpen && (
        <AdvancementStepModal
          onClose={() => setAdvOpen(false)}
          onSubmit={async ({ stepKey, justification }) => {
            await post({
              kind: "advancement-step",
              character_id: character.id,
              advancement_step_key: stepKey,
              justification,
            });
            setAdvOpen(false);
          }}/>
      )}
    </div>
  );
}


function ModalShell({ title, onClose, children, testid }) {
  return (
    <div className="fixed inset-0 z-[200] bg-void/80 flex items-center justify-center p-4"
         onClick={onClose} data-testid={testid}>
      <div className="card-mystic p-5 max-w-md w-full max-h-[90vh] overflow-y-auto
                      relative space-y-3"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose}
                className="absolute top-2 right-2 text-mist hover:text-parchment">
          <X className="w-4 h-4"/>
        </button>
        <div className="h-arcane text-sm">{title}</div>
        {children}
      </div>
    </div>
  );
}


function PeerTransferModal({ peers, onClose, onSubmit }) {
  const [peerId, setPeerId] = useState(peers[0]?.id || "");
  const [just, setJust] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <ModalShell title="Peer XP Transfer (1 XP)"
                onClose={onClose}
                testid="cypher-peer-transfer-modal">
      <div className="text-[11px] text-mist italic">
        Hand 1 XP to a peer with a brief narrative justification. Per the
        Cypher XP rule, this also fires automatically when you accept a GM
        intrusion (2 XP earned, 1 immediately to a peer).
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-widest text-mist">Recipient</div>
        <select className="select" value={peerId}
                onChange={(e) => setPeerId(e.target.value)}
                data-testid="cypher-peer-transfer-recipient">
          {peers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-widest text-mist">Why?</div>
        <textarea className="input text-xs w-full" rows={2}
                  value={just} onChange={(e) => setJust(e.target.value)}
                  placeholder="Roll knowledge to your specialty…"
                  data-testid="cypher-peer-transfer-just"/>
      </div>
      <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
        <button onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
        <button onClick={async () => { setBusy(true); await onSubmit({ peerId, justification: just }); }}
                disabled={!peerId || busy}
                className="btn btn-primary text-xs"
                data-testid="cypher-peer-transfer-submit">
          {busy && <Loader2 className="w-3 h-3 animate-spin"/>} Transfer 1 XP
        </button>
      </div>
    </ModalShell>
  );
}


function NarrativePoolModal({ peers, onClose, onSubmit }) {
  const [rows, setRows] = useState(
    peers.slice(0, 4).map((p) => ({ character_id: p.id, name: p.name, amount: 0 })));
  const [just, setJust] = useState("");
  const [busy, setBusy] = useState(false);
  const total = useMemo(() =>
    rows.reduce((s, r) => s + (Number(r.amount) || 0), 0), [rows]);
  return (
    <ModalShell title="Narrative-Pool Spend"
                onClose={onClose}
                testid="cypher-narrative-pool-modal">
      <div className="text-[11px] text-mist italic">
        Several players co-fund a setting-shaping change. Typical scale 4-12 XP;
        GM ratifies the consequence. Each contributor must have enough unspent XP.
      </div>
      <div className="space-y-1">
        {rows.map((r, i) => (
          <div key={r.character_id}
               className="flex items-center gap-2 text-[11px]">
            <span className="text-parchment flex-1 truncate">{r.name}</span>
            <input type="number" min={0} max={20} value={r.amount}
                   onChange={(e) => setRows(rows.map((x, j) =>
                     j === i ? { ...x, amount: +e.target.value } : x))}
                   className="input w-20 text-center"
                   data-testid={`cypher-pool-amount-${i}`}/>
            <span className="text-mist text-[10px]">XP</span>
          </div>
        ))}
      </div>
      <div className="text-[10px] text-arcane-light text-right">
        pool total: {total} XP
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-widest text-mist">Authoring intent</div>
        <textarea className="input text-xs w-full" rows={3}
                  value={just} onChange={(e) => setJust(e.target.value)}
                  placeholder="Together we declare the dragon has always feared cold iron…"
                  data-testid="cypher-pool-just"/>
      </div>
      <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
        <button onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
        <button onClick={async () => {
                  setBusy(true);
                  await onSubmit({
                    contributors: rows
                      .filter((r) => Number(r.amount) > 0)
                      .map((r) => ({ character_id: r.character_id, amount: Number(r.amount) })),
                    justification: just,
                  });
                }}
                disabled={total <= 0 || busy}
                className="btn btn-primary text-xs"
                data-testid="cypher-pool-submit">
          {busy && <Loader2 className="w-3 h-3 animate-spin"/>} Spend {total} XP
        </button>
      </div>
    </ModalShell>
  );
}


function GrantIntrusionModal({ character, peers, onClose, onSubmit }) {
  const [peerId, setPeerId] = useState(peers[0]?.id || "");
  const [just, setJust] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <ModalShell title={`Award GM Intrusion to ${character.name}`}
                onClose={onClose}
                testid="cypher-grant-intrusion-modal">
      <div className="text-[11px] text-mist italic">
        Acceptor gains 2 XP. Per the canonical rule, 1 of those XP is
        immediately handed to a peer. Pick the peer; both deltas log
        atomically (acceptor net +1, peer +1).
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-widest text-mist">Auto-pair to peer</div>
        <select className="select" value={peerId}
                onChange={(e) => setPeerId(e.target.value)}
                data-testid="cypher-grant-peer">
          <option value="">— skip auto-pair —</option>
          {peers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-widest text-mist">Intrusion description</div>
        <textarea className="input text-xs w-full" rows={3}
                  value={just} onChange={(e) => setJust(e.target.value)}
                  placeholder="The bridge cracks under the weight…"
                  data-testid="cypher-grant-just"/>
      </div>
      <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
        <button onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
        <button onClick={async () => { setBusy(true); await onSubmit({ peerId, justification: just }); }}
                disabled={busy}
                className="btn btn-primary text-xs"
                data-testid="cypher-grant-submit">
          {busy && <Loader2 className="w-3 h-3 animate-spin"/>} Award Intrusion
        </button>
      </div>
    </ModalShell>
  );
}


function AdvancementStepModal({ onClose, onSubmit }) {
  const [stepKey, setStepKey] = useState(ADVANCEMENT_STEPS[0].key);
  const [just, setJust] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <ModalShell title="Buy Advancement Step (4 XP)"
                onClose={onClose}
                testid="cypher-advancement-modal">
      <div className="text-[11px] text-mist italic">
        Buying all four steps (4 × 4 = 16 XP) advances the character to
        the next tier. Steps may be bought in any order.
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-widest text-mist">Step</div>
        <select className="select" value={stepKey}
                onChange={(e) => setStepKey(e.target.value)}
                data-testid="cypher-advancement-step-pick">
          {ADVANCEMENT_STEPS.map((s) => (
            <option key={s.key} value={s.key}>{s.name}</option>
          ))}
        </select>
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-widest text-mist">Note</div>
        <input className="input text-xs w-full" value={just}
               onChange={(e) => setJust(e.target.value)}
               placeholder="What did this step represent in the fiction?"
               data-testid="cypher-advancement-just"/>
      </div>
      <div className="flex justify-end gap-2 border-t border-gold/10 pt-3">
        <button onClick={onClose} className="btn btn-ghost text-xs">Cancel</button>
        <button onClick={async () => { setBusy(true); await onSubmit({ stepKey, justification: just }); }}
                disabled={busy}
                className="btn btn-primary text-xs"
                data-testid="cypher-advancement-submit">
          {busy && <Loader2 className="w-3 h-3 animate-spin"/>} Spend 4 XP
        </button>
      </div>
    </ModalShell>
  );
}
