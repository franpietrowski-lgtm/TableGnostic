// CypherSheetView — extracted in V6.10 refactor.
// Cypher pools + difficulty tracker + intrusion ledger + skill trains.
import React, { useState } from "react";
import { Dice6 } from "lucide-react";
import { SimpleListCard, DiceCard } from "./sheetCommon";

export default function CypherSheetView({ state, roll }) {
  const [diff, setDiff] = useState(3);
  const [extraSteps, setExtraSteps] = useState(0);
  const sentence = state.sentence || (() => {
    const article = /^[aeiouAEIOU]/.test(state.descriptor || "") ? "an" : "a";
    return `I am ${article} ${state.descriptor || "?"} ${state.type || "?"} who ${(state.focus || "").toLowerCase() || "?"}.`;
  })();
  const effectiveDiff = Math.max(0, diff - Math.max(0, extraSteps));
  const target = effectiveDiff * 3;
  const tier = Math.max(1, +(state.tier || 1));
  const cypherLimit = state.cypher_limit ?? (state.starting_cypher_limit || 2);
  const armor = state.armor || 0;
  const recoveriesMax = state.recoveries_max || 4;
  const recoveriesUsed = state.recoveries_used || 0;
  const recoveryDie = state.recovery_die
    || `1d6+${Math.min(6, Math.max(1, tier))}`;
  const rollAtDifficulty = () => {
    const label = `Cypher roll · diff ${diff}${extraSteps ? ` (−${extraSteps} steps)` : ""} · TN ${target}`;
    roll("1d20", label);
  };
  const quickRolls = [
    { label: "Cypher Roll (d20)", notation: "1d20",
      hint: "1d20 ≥ 3 × difficulty. Train/Specialise/Effort/Asset each lower difficulty 1 step." },
    { label: `Recovery (${recoveryDie})`, notation: recoveryDie, hint: "Cypher pool recovery roll." },
    { label: "Light Cypher Damage", notation: "1d6", hint: "Single-target light damage die." },
  ];
  return (
    <div data-system="cypher" data-testid="cypher-sheet-view">
      <div className="card-mystic p-6 mt-8">
        <div className="label-ref">Character Sentence</div>
        <div className="text-base text-gold-bright italic mt-2"
             data-testid="cypher-sheet-sentence">"{sentence}"</div>
        <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] text-mist">
          <div><span className="label-ref">Descriptor</span> {state.descriptor || "—"}</div>
          <div><span className="label-ref">Type</span> {state.type || "—"}</div>
          <div><span className="label-ref">Focus</span> {state.focus || "—"}</div>
        </div>
      </div>

      <div className="card-mystic p-6 mt-4" data-testid="cypher-pool-rings">
        <div className="label-ref">Stat Pools (current / max) — damage tracker</div>
        <div className="grid grid-cols-3 gap-3 mt-3">
          {["Might", "Speed", "Intellect"].map((k) => {
            // V6.25.29 — accept BOTH shapes:
            //   1. flat   pools[k] (number) + current_pools[k] + edge[k]
            //   2. nested pools[k.toLowerCase()] = {max, current, edge}
            const lk = k.toLowerCase();
            const nested = state.pools?.[lk];
            const isNested = nested && typeof nested === "object";
            const max = isNested
              ? Number(nested.max ?? 0)
              : Number(state.pools?.[k] ?? 0);
            const cur = isNested
              ? Number(nested.current ?? nested.max ?? 0)
              : Number(state.current_pools?.[k] ?? max);
            const edge = isNested
              ? Number(nested.edge ?? 0)
              : Number(state.edge?.[k] ?? 0);
            const pct = max > 0 ? Math.max(0, Math.min(100, (cur / max) * 100)) : 0;
            const colour = pct > 66 ? "#3FAA62" : pct > 33 ? "#C8A34A" : "#7A1F2E";
            return (
              <div key={k} className="border border-gold/15 rounded-sm p-3 text-center"
                   data-testid={`cypher-pool-ring-${lk}`}>
                <div className="label-ref text-[9px]">{k}</div>
                <div className="font-display text-2xl text-gold">
                  <span style={{ color: colour }}>{cur}</span>
                  <span className="text-mist text-xs"> / {max}</span>
                </div>
                <div className="h-1.5 bg-void/60 rounded-full mt-1 overflow-hidden">
                  <div className="h-full transition-all"
                       style={{ width: `${pct}%`, backgroundColor: colour }}/>
                </div>
                <div className="text-[10px] font-ui text-mist mt-1">
                  Edge <span className="text-gold-bright">{edge}</span>
                </div>
              </div>
            );
          })}
        </div>
        <div className="text-[10px] text-mist/70 italic mt-2">
          Players: spend Pool with the Effort lever above. GMs: edit `current_pools`
          (or `pools.&lt;name&gt;.current`) on the character sheet to mark damage between sessions.
        </div>
      </div>

      <div className="card-mystic p-5 mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center"
           data-testid="cypher-derived-block">
        <div className="border border-gold/15 rounded-sm py-2">
          <div className="label-ref">Armor</div>
          <div className="font-display text-2xl text-gold-bright"
               data-testid="cypher-armor-value">{armor}</div>
          <div className="text-[9px] text-mist">soak / hit</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-2">
          <div className="label-ref">Cypher Limit</div>
          <div className="font-display text-2xl text-gold-bright"
               data-testid="cypher-limit-value">{cypherLimit}</div>
          <div className="text-[9px] text-mist">max carried</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-2"
             data-testid="cypher-recoveries-block">
          <div className="label-ref">Recoveries</div>
          <div className="font-display text-2xl text-gold-bright">
            {Math.max(0, recoveriesMax - recoveriesUsed)}
            <span className="text-mist text-xs"> / {recoveriesMax}</span>
          </div>
          <div className="text-[9px] text-mist">{recoveryDie}/day</div>
        </div>
        <div className="border border-gold/15 rounded-sm py-2">
          <div className="label-ref">Effort</div>
          <div className="font-display text-2xl text-gold-bright">{state.effort || 1}</div>
          <div className="text-[9px] text-mist">max steps</div>
        </div>
      </div>

      <div className="card-mystic p-6 mt-4" data-testid="cypher-difficulty-tracker">
        <div className="label-ref">Difficulty Tracker</div>
        <div className="grid sm:grid-cols-3 gap-3 mt-3 items-end">
          <div>
            <label className="label-ref">Task Difficulty (0-10)</label>
            <input className="input" type="number" min={0} max={10} value={diff}
                   onChange={(e) => setDiff(Math.max(0, Math.min(10, +e.target.value || 0)))}
                   data-testid="cypher-diff-input"/>
          </div>
          <div>
            <label className="label-ref">Steps Lowered (Train/Effort/Asset)</label>
            <input className="input" type="number" min={0} max={10} value={extraSteps}
                   onChange={(e) => setExtraSteps(Math.max(0, Math.min(10, +e.target.value || 0)))}
                   data-testid="cypher-steps-input"/>
          </div>
          <div className="text-center border border-gold/30 rounded-sm py-3 bg-gold/5">
            <div className="label-ref">Target Number</div>
            <div className="font-display text-3xl text-gold-bright" data-testid="cypher-tn">
              {target}
            </div>
            <div className="text-[10px] text-mist">eff. diff {effectiveDiff}</div>
          </div>
        </div>
        <button onClick={rollAtDifficulty} className="btn btn-primary mt-3"
                data-testid="cypher-roll-against-tn">
          <Dice6 className="w-4 h-4"/> Roll 1d20 vs TN {target}
        </button>

        <div className="grid sm:grid-cols-3 gap-2 mt-3 text-[11px] text-mist">
          <div className="border border-gold/15 rounded-sm p-2">
            <div className="label-ref text-[9px]">Effort</div>
            <div className="text-parchment font-ui">Spend (3 + 2× extra) Pool to lower difficulty 1 step / level. Max = Edge + 1.</div>
          </div>
          <div className="border border-gold/15 rounded-sm p-2">
            <div className="label-ref text-[9px]">Edge ({(state.edge?.Might||0)+(state.edge?.Speed||0)+(state.edge?.Intellect||0)} total)</div>
            <div className="text-parchment font-ui">Reduces Pool cost of Effort &amp; abilities by Edge for that pool.</div>
          </div>
          <div className="border border-gold/15 rounded-sm p-2">
            <div className="label-ref text-[9px]">Skill / Asset</div>
            <div className="text-parchment font-ui">Trained −1 step · Specialised −2 · Asset −1 (max 2 assets).</div>
          </div>
        </div>
      </div>

      <div className="card-mystic p-6 mt-4" data-testid="cypher-intrusion-ledger">
        <div className="label-ref flex items-center gap-2">
          GM Intrusion Ledger
          <span className="text-[9px] text-mist normal-case tracking-normal italic">accept = +2 XP self · +2 XP ally · refuse = −1 XP</span>
        </div>
        <div className="flex gap-2 mt-3 flex-wrap">
          <button onClick={() => roll("0+2", "Intrusion accepted · +2 XP")}
                  className="btn btn-ghost text-xs"
                  title="Log accepting a GM intrusion (+2 XP self, +2 XP ally)"
                  data-testid="cypher-intrusion-accept">
            ✓ Accept (+2/+2)
          </button>
          <button onClick={() => roll("0-1", "Intrusion refused · −1 XP")}
                  className="btn btn-ghost text-xs"
                  title="Log refusing a GM intrusion (−1 XP)"
                  data-testid="cypher-intrusion-refuse">
            ✗ Refuse (−1)
          </button>
          <span className="text-[10px] text-mist italic ml-2 self-center">
            Logged as a chat ledger entry — GM can convert to formal XP via the XP Approval Queue.
          </span>
        </div>
      </div>

      {(state.skill_trains?.length || 0) > 0 && (
        <div className="card-mystic p-6 mt-4">
          <div className="label-ref flex items-center gap-2">
            Skills Trained
            <span className="text-[10px] text-mist/70 italic normal-case tracking-normal"
                  title="Trained skills: difficulty of tasks using this skill is lowered by 1 step (Specialised lowers by 2). Inability: raised by 1 step.">
              (hover any tag)
            </span>
          </div>
          <div className="flex flex-wrap gap-1 mt-2">
            {state.skill_trains.map((s) => {
              const [skill, kind] = (typeof s === "string")
                ? [s, /^specialised?:/i.test(s) ? "specialised"
                     : /^inability:/i.test(s) ? "inability" : "trained"]
                : [s.name, s.kind || "trained"];
              const tooltip = kind === "specialised"
                ? `Specialised in ${skill}: difficulty lowered by 2 steps — normally requires two training slots.`
                : kind === "inability"
                ? `Inability with ${skill}: difficulty raised by 1 step. Often taken for roleplay or to free a training slot.`
                : `Trained in ${skill}: difficulty lowered by 1 step on applicable tasks.`;
              const cls = kind === "specialised" ? "border-arcane/50 text-arcane"
                        : kind === "inability" ? "border-ember/40 text-ember"
                        : "border-gold/40 text-gold-bright";
              return <span key={typeof s === "string" ? s : s.name}
                           className={`tag cursor-help ${cls}`}
                           title={tooltip}>{skill}</span>;
            })}
          </div>
        </div>
      )}
      {(state.abilities?.length || 0) > 0 && (
        <SimpleListCard title="Type / Focus Abilities" items={state.abilities}
                         testid="cypher-sheet-abilities"/>
      )}
      {(state.cyphers?.length || 0) > 0 && (
        <SimpleListCard
          title={`Cyphers Carried (${state.cyphers.length} / ${state.cyphers_max ?? cypherLimit})`}
          items={state.cyphers}
          testid="cypher-sheet-cyphers"/>
      )}
      {state.notes && (
        <div className="card-mystic p-6 mt-4">
          <div className="label-ref">Notes / GM Intrusion ledger</div>
          <div className="text-sm text-mist mt-2 whitespace-pre-wrap font-body">{state.notes}</div>
        </div>
      )}

      <DiceCard quickRolls={quickRolls} roll={roll}/>

      <div className="text-[10px] text-mist/60 italic mt-3 text-center">
        Cypher System Creator · Requires the Cypher System Rulebook from Monte Cook Games.
      </div>
    </div>
  );
}
