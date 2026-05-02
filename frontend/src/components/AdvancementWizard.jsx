/**
 * AdvancementWizard — V6.17
 *
 * Detect-and-guide UI for per-system advancement choices:
 *   - D&D 5E / Anime 5E: ASI / feat / fighting style / subclass
 *   - Cypher: tier benefit checklist
 *   - Anime 5E: BESM-style point-buy unspent advisory
 *   - BESM 4E: unspent XP advisory (links to XP queue)
 *
 * Renders:
 *   <AdvancementBadge> — pill-shaped "N pending" button
 *   <AdvancementWizard> — modal with guided picker
 */
import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Sparkles, X, ArrowRight, Check } from "lucide-react";

const SIX_ABILITIES = [
  "Strength", "Dexterity", "Constitution",
  "Intelligence", "Wisdom", "Charisma",
];

export function AdvancementBadge({ characterId, isOwnerOrGm, onClick }) {
  const [data, setData] = useState(null);
  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/characters/${characterId}/advancement`);
      setData(data);
    } catch { /* ignore */ }
  }, [characterId]);
  useEffect(() => { refresh(); }, [refresh]);

  // Listen for the wizard's apply event so the badge auto-refreshes.
  useEffect(() => {
    const onApplied = () => refresh();
    window.addEventListener("tg:advancement-applied", onApplied);
    return () => window.removeEventListener("tg:advancement-applied", onApplied);
  }, [refresh]);

  if (!data) return null;
  const n = data.pending_count || 0;
  if (n === 0) {
    return (
      <button onClick={onClick}
              className="text-[10px] font-ui uppercase tracking-widest text-mist/60 hover:text-gold transition-colors px-2 py-1 border border-gold/15 rounded-full"
              data-testid="advancement-badge-clean"
              title="No pending choices owed by this character.">
        <Check className="w-3 h-3 inline-block mr-1"/> Up to date
      </button>
    );
  }
  return (
    <button onClick={onClick}
            className="text-[11px] font-ui uppercase tracking-widest text-gold-bright hover:bg-gold/15 transition-colors px-2.5 py-1 border border-gold/40 rounded-full inline-flex items-center gap-1 animate-pulse"
            data-testid="advancement-badge-pending"
            title={`${n} pending advancement choice${n === 1 ? "" : "s"} — click to resolve`}>
      <Sparkles className="w-3.5 h-3.5"/> {n} pending choice{n === 1 ? "" : "s"}
    </button>
  );
}

export default function AdvancementWizard({ characterId, isOwnerOrGm, onClose, onApplied }) {
  const [data, setData] = useState(null);
  const [activeIdx, setActiveIdx] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // Per-step picks; shape varies per advancement kind.
  const [pick, setPick] = useState({ key: "", detail: {}, note: "" });

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/characters/${characterId}/advancement`);
      setData(data);
      // Reset pick state for the next step.
      setPick({ key: "", detail: {}, note: "" });
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  }, [characterId]);

  useEffect(() => { refresh(); }, [refresh]);

  if (!data) return null;
  const pending = data.pending || [];
  if (pending.length === 0) {
    return (
      <Modal onClose={onClose}>
        <div className="text-center py-8" data-testid="advancement-wizard-empty">
          <div className="font-display text-2xl text-gold mb-2">Up to date</div>
          <div className="text-mist text-sm italic">
            No pending advancement choices for this character.
          </div>
          <button onClick={onClose} className="btn btn-ghost text-xs mt-4"
                  data-testid="advancement-wizard-close">Close</button>
        </div>
      </Modal>
    );
  }

  const idx = Math.min(activeIdx, pending.length - 1);
  const step = pending[idx];

  const apply = async () => {
    if (!isOwnerOrGm) {
      setError("Only the character's owner or the GM may apply advancement choices.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.post(`/characters/${characterId}/advancement/apply`, {
        advancement_id: step.id,
        choice_key: pick.key || "",
        detail: pick.detail || {},
        note: pick.note || "",
      });
      window.dispatchEvent(new CustomEvent("tg:advancement-applied"));
      onApplied && onApplied();
      // Refresh and stay open — the user might have multiple pending choices.
      await refresh();
      setActiveIdx(0);
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose} testid="advancement-wizard">
      <div className="flex items-baseline justify-between gap-2 mb-3">
        <div>
          <div className="text-[10px] font-ui uppercase tracking-widest text-mist">
            Advancement · Step {idx + 1} of {pending.length}
          </div>
          <h2 className="font-display text-2xl text-gold-bright mt-0.5"
              data-testid="advancement-step-title">
            {step.title}
          </h2>
        </div>
        <button onClick={onClose} className="text-mist hover:text-gold"
                data-testid="advancement-wizard-x">
          <X className="w-5 h-5"/>
        </button>
      </div>
      <div className="text-sm text-parchment/85 italic mb-3" data-testid="advancement-step-blurb">
        {step.blurb}
      </div>

      {/* Renderer per kind */}
      {(step.kind === "asi_or_feat") && (
        <AsiOrFeatPicker pick={pick} setPick={setPick}/>
      )}
      {(step.kind === "fighting_style" || step.kind === "subclass") && (
        <OptionListPicker step={step} pick={pick} setPick={setPick}/>
      )}
      {(step.kind === "cypher_tier_benefits") && (
        <CypherBenefitPicker step={step} pick={pick} setPick={setPick}/>
      )}
      {(step.kind === "anime5e_point_buy") && (
        <AdvisoryPanel
          icon="✦"
          message={`The Anime 5E BESM-style point-buy supplement on this sheet has ${step.extra?.unspent ?? "?"} unspent points (budget ${step.extra?.budget ?? "?"}). Open Edit and add another point-buy attribute on the supplement card to spend them. Closing this step records that the player acknowledged the advisory.`}
        />
      )}
      {(step.kind === "besm_xp") && (
        <AdvisoryPanel
          icon="✦"
          message={`This BESM 4E character has ${step.extra?.xp_unspent ?? "?"} XP unspent. Submit an XP-spend proposal via the XP Approval Queue (visible on the Identity tab). Closing this step records that the player acknowledged the advisory.`}
        />
      )}

      {/* Note + actions */}
      <div className="mt-3">
        <label className="label-ref">Optional note (visible to GM)</label>
        <textarea className="input mt-1 w-full" rows={2}
                  value={pick.note || ""}
                  onChange={(e) => setPick({ ...pick, note: e.target.value })}
                  data-testid="advancement-note"
                  placeholder="e.g. picked Tough because of the Lakemen ambush — narrative reason"/>
      </div>

      {error && (
        <div className="text-ember text-xs mt-2" data-testid="advancement-error">{error}</div>
      )}

      <div className="flex items-center justify-between mt-4 gap-2 flex-wrap">
        <div className="flex items-center gap-1">
          <button onClick={() => setActiveIdx(Math.max(0, idx - 1))}
                  disabled={idx === 0} className="btn btn-ghost text-xs"
                  data-testid="advancement-prev">‹ Prev</button>
          <button onClick={() => setActiveIdx(Math.min(pending.length - 1, idx + 1))}
                  disabled={idx === pending.length - 1} className="btn btn-ghost text-xs"
                  data-testid="advancement-next">Next ›</button>
        </div>
        <button onClick={apply}
                disabled={busy || !isOwnerOrGm}
                className="btn btn-primary text-xs flex items-center gap-1"
                data-testid="advancement-apply-btn">
          {busy ? "Saving…" : (
            <>Apply &amp; record <ArrowRight className="w-3.5 h-3.5"/></>
          )}
        </button>
      </div>
    </Modal>
  );
}

// ─── Sub-pickers ─────────────────────────────────────────────────────────

function AsiOrFeatPicker({ pick, setPick }) {
  const [mode, setMode] = useState(pick.key || "asi_2");
  useEffect(() => { setPick({ ...pick, key: mode }); /* eslint-disable-next-line */ }, [mode]);
  return (
    <div className="space-y-3" data-testid="asi-or-feat-picker">
      <div className="flex flex-wrap gap-2">
        {[
          { k: "asi_2",   l: "+2 to one ability score" },
          { k: "asi_1_1", l: "+1 to two ability scores" },
          { k: "feat",    l: "Pick a feat (free text)" },
        ].map((opt) => (
          <button key={opt.k}
                  onClick={() => setMode(opt.k)}
                  className={`btn text-xs ${mode === opt.k ? "btn-primary" : "btn-ghost"}`}
                  data-testid={`asi-mode-${opt.k}`}>
            {opt.l}
          </button>
        ))}
      </div>
      {mode === "asi_2" && (
        <div>
          <label className="label-ref">Ability to raise by 2</label>
          <select className="select mt-1 w-full"
                  value={pick.detail?.ability || "Strength"}
                  onChange={(e) => setPick({ ...pick, detail: { ability: e.target.value } })}
                  data-testid="asi-ability-2">
            {SIX_ABILITIES.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      )}
      {mode === "asi_1_1" && (
        <div className="grid grid-cols-2 gap-2">
          {[0, 1].map((slot) => (
            <div key={slot}>
              <label className="label-ref">Ability {slot + 1}</label>
              <select className="select mt-1 w-full"
                      value={pick.detail?.abilities?.[slot] || SIX_ABILITIES[slot]}
                      onChange={(e) => {
                        const arr = [...(pick.detail?.abilities || [])];
                        arr[slot] = e.target.value;
                        setPick({ ...pick, detail: { ...pick.detail, abilities: arr } });
                      }}
                      data-testid={`asi-ability-1-1-${slot}`}>
                {SIX_ABILITIES.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
          ))}
        </div>
      )}
      {mode === "feat" && (
        <div>
          <label className="label-ref">Feat name (campaign-allowed)</label>
          <input type="text" className="input mt-1 w-full"
                 value={pick.detail?.feat || ""}
                 onChange={(e) => setPick({ ...pick, detail: { feat: e.target.value } })}
                 placeholder="e.g. Determined Underdog"
                 data-testid="asi-feat-name"/>
          <div className="text-[10px] text-mist italic mt-1">
            Tip: Anime 5E SRD-safe feats live in this campaign's reference library —
            check the Atelier · References tab for the full curated list.
          </div>
        </div>
      )}
    </div>
  );
}

function OptionListPicker({ step, pick, setPick }) {
  const opts = step.options || [];
  return (
    <div className="space-y-2" data-testid={`option-picker-${step.kind}`}>
      {opts.length === 0 ? (
        <div>
          <label className="label-ref">Free-text choice</label>
          <input type="text" className="input mt-1 w-full"
                 value={pick.key || ""}
                 onChange={(e) => setPick({ ...pick, key: e.target.value })}
                 placeholder="e.g. School of Evocation"
                 data-testid="option-free-text"/>
        </div>
      ) : opts.map((o) => (
        <label key={o.key}
               className={`block border ${pick.key === o.key ? "border-gold bg-gold/10" : "border-gold/15"} rounded-sm p-2.5 cursor-pointer hover:border-gold/40 transition-colors`}
               data-testid={`option-${o.key}`}>
          <input type="radio" name="opt" className="mr-2"
                 checked={pick.key === o.key}
                 onChange={() => setPick({ ...pick, key: o.key })}/>
          <span className="text-sm text-parchment font-ui">{o.label}</span>
        </label>
      ))}
    </div>
  );
}

function CypherBenefitPicker({ step, pick, setPick }) {
  const opts = step.options || [];
  return (
    <div className="space-y-2" data-testid="cypher-benefit-picker">
      <div className="text-[10px] font-ui uppercase tracking-widest text-mist">
        Tier {step.extra?.tier} · {step.extra?.owed} pick{step.extra?.owed === 1 ? "" : "s"} remaining ({step.extra?.chosen?.length || 0}/4 done)
      </div>
      {opts.map((o) => (
        <label key={o.key}
               className={`block border ${pick.key === o.key ? "border-gold bg-gold/10" : "border-gold/15"} rounded-sm p-2.5 cursor-pointer hover:border-gold/40 transition-colors`}
               data-testid={`cypher-benefit-${o.key}`}>
          <input type="radio" name="cy-benefit" className="mr-2"
                 checked={pick.key === o.key}
                 onChange={() => setPick({ ...pick, key: o.key })}/>
          <div className="inline-block align-middle">
            <div className="text-sm text-parchment font-ui">{o.label}</div>
            <div className="text-[10px] text-mist italic">{o.blurb}</div>
          </div>
        </label>
      ))}
    </div>
  );
}

function AdvisoryPanel({ icon, message }) {
  return (
    <div className="border-l-2 border-arcane/50 bg-arcane/5 p-3 text-sm text-parchment/90"
         data-testid="advisory-panel">
      <span className="text-arcane-light font-display text-lg mr-2">{icon}</span>
      {message}
    </div>
  );
}

function Modal({ children, onClose, testid }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 bg-void/90 backdrop-blur-md z-50 flex items-start justify-center pt-12 sm:pt-20 p-4"
         data-testid={testid || "advancement-modal"}
         onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="card-mystic max-w-lg w-full p-6 shadow-2xl">
        {children}
      </div>
    </div>
  );
}
