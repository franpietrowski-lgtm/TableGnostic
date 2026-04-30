/**
 * Cypher System character builder. Uses the SRD shape from
 * /api/systems/cypher/reference. Persists into `folio.cypher_state`.
 *
 * Cypher uses the iconic "I am a [descriptor] [type] who [focus]"
 * sentence as identity, plus three pools (Might / Speed / Intellect),
 * Edge per pool, Effort cap, and a per-tier recovery mechanic. The
 * dropdowns are genre-gated when `campaign.setting_genre` is set.
 */
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../../lib/api";
import { Save, Sparkles } from "lucide-react";
import { FreeList } from "./shared";

export const emptyCypher = (cid) => ({
  campaign_id: cid, name: "", concept: "", power_level: "Heroic", total_points: 0,
  size: "Medium", token_color: "",
  stats: { body: 4, mind: 4, soul: 4 }, // satisfies CharacterIn — Cypher uses pools
  attributes: [], defects: [], skills: [], power_packs: [], notes: "", published: false,
  folio: {
    cypher_state: {
      type: "Warrior", focus: "Bears a Halo of Fire", descriptor: "Tough",
      tier: 1,
      pools: { Might: 11, Speed: 11, Intellect: 7 },
      edge: { Might: 1, Speed: 0, Intellect: 0 },
      effort: 1,
      cyphers: [],
      abilities: [],
      skill_trains: [],
      sentence: "",
      notes: "",
    },
  },
});

export function CypherBuilder({ campaign, ref_, charId }) {
  const nav = useNavigate();
  const [ch, setCh] = useState(emptyCypher(campaign?.id));
  const [err, setErr] = useState("");
  // GM-curated Cypher reference rows for THIS campaign — Atelier → Reference Tables
  // entries with kind=attribute (Types) / companion (Foci) / defect (Cyphers) / item / custom (Intrusions).
  const [refRows, setRefRows] = useState([]);
  useEffect(() => {
    if (campaign?.id) {
      api.get(`/campaigns/${campaign.id}/reference`)
        .then((r) => setRefRows(r.data || []))
        .catch(() => setRefRows([]));
    }
  }, [campaign?.id]);

  useEffect(() => {
    if (charId) {
      api.get(`/characters/${charId}`).then((r) => {
        const existing = r.data;
        if (!existing.folio?.cypher_state) {
          existing.folio = { ...(existing.folio || {}),
                              cypher_state: emptyCypher(campaign?.id).folio.cypher_state };
        }
        setCh(existing);
      });
    } else {
      setCh(emptyCypher(campaign?.id));
    }
  }, [charId, campaign?.id]);

  // Compute the sentence BEFORE any early return so useMemo is always
  // invoked in the same hook order. Use optional chaining so it produces
  // a stable placeholder when ch hasn't loaded yet.
  const sentence = useMemo(() => {
    const cs = ch?.folio?.cypher_state;
    if (!cs) return "";
    const article = /^[aeiouAEIOU]/.test(cs.descriptor || "") ? "an" : "a";
    return `I am ${article} ${cs.descriptor} ${cs.type} who ${(cs.focus || "").toLowerCase()}.`;
  }, [ch]);

  if (!ch || !ref_) return <div className="p-10 text-mist">Summoning…</div>;
  const c = ch.folio.cypher_state;
  const setC = (patch) => setCh({ ...ch,
    folio: { ...ch.folio, cypher_state: { ...c, ...patch } } });
  const setPool = (k, v) => setC({ pools: { ...c.pools, [k]: Math.max(0, +v) } });
  const setEdge = (k, v) => setC({ edge: { ...c.edge, [k]: Math.max(0, +v) } });
  const toggleSkill = (sk) => setC({ skill_trains:
    c.skill_trains.includes(sk) ? c.skill_trains.filter((x) => x !== sk) : [...c.skill_trains, sk] });

  // Auto-fill pools / edge / cypher-limit when the Type changes — ties to
  // the SRD `pool_offsets` / `starting_edge` / `starting_cypher_limit` we
  // ship in `cypher_data.py`. Players can still override any value.
  const setType = (typeName) => {
    const baseline = ref_?.pool_baseline ?? 7;
    const t = (ref_?.types || []).find((x) => x.name === typeName);
    if (!t) { setC({ type: typeName }); return; }
    const off = t.pool_offsets || { Might: 0, Speed: 0, Intellect: 0 };
    setC({
      type: typeName,
      pools: {
        Might: baseline + (off.Might || 0),
        Speed: baseline + (off.Speed || 0),
        Intellect: baseline + (off.Intellect || 0),
      },
      edge: t.starting_edge || { Might: 0, Speed: 0, Intellect: 0 },
      starting_cypher_limit: t.starting_cypher_limit || 2,
      cypher_limit: t.starting_cypher_limit || 2,
      // Track the baseline + offsets so the discretionary-points validator
      // can tell what was "given by Type" vs what the player added on top.
      pools_type_baseline: {
        Might: baseline + (off.Might || 0),
        Speed: baseline + (off.Speed || 0),
        Intellect: baseline + (off.Intellect || 0),
      },
    });
  };

  // V6.3 — tier-bump recompute. When the tier changes, some derived values
  // should move in lock-step: recovery die defaults to 1d6+tier and the
  // max Effort is (by house convention) tier capped at Edge+1 in play.
  // We leave the explicit Effort value editable but refresh the recovery
  // die unless the player has customised it.
  const setTier = (newTier) => {
    const next = Math.max(1, Math.min(6, +newTier || 1));
    const defaultRecovery = `1d6+${c.tier || 1}`;
    const nextRecovery = (c.recovery_die === defaultRecovery
      || !c.recovery_die) ? `1d6+${next}` : c.recovery_die;
    setC({ tier: next, recovery_die: nextRecovery });
  };

  // Pool-discretionary points tracker. The Cypher character-creation rule
  // (CSR p.16) gives 6 points to distribute across the three stat pools
  // at any ratio (max +X per pool is a soft cap — we warn at > +6 which
  // would exceed the canonical Type+rotation budget). The `pools_type_baseline`
  // captures what the Type + offsets granted; anything above that is a
  // discretionary spend we can audit.
  const POOL_BUDGET = ref_?.pool_discretionary_budget ?? 6;
  const baseline = c.pools_type_baseline || {
    Might: c.pools?.Might, Speed: c.pools?.Speed, Intellect: c.pools?.Intellect };
  const spent = ["Might", "Speed", "Intellect"].reduce((sum, k) =>
    sum + Math.max(0, (c.pools?.[k] || 0) - (baseline?.[k] || 0)), 0);
  const over = spent > POOL_BUDGET;

  const save = async () => {
    setErr("");
    try {
      const payload = { ...ch, folio: { ...ch.folio, cypher_state: { ...c, sentence } } };
      if (charId && window.location.pathname.includes("/edit")) {
        const { data } = await api.put(`/characters/${charId}`, payload);
        nav(`/app/characters/${data.id}`);
      } else {
        const { data } = await api.post("/characters", payload);
        nav(`/app/characters/${data.id}`);
      }
    } catch (e) { setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message); }
  };

  return (
    <div className="px-8 md:px-12 py-10 max-w-5xl" data-system="cypher" data-testid="cypher-builder">
      <Link to={`/app/campaigns/${ch.campaign_id}`} className="text-xs font-ui uppercase tracking-widest text-gold/70">← Campaign</Link>
      <h1 className="font-display text-4xl tracking-wide text-parchment mt-4">Cypher Character</h1>
      <div className="text-[11px] text-mist/70 italic mt-1">
        Cypher System Creator · Requires the Cypher System Rulebook from Monte Cook Games.
      </div>

      {/* Sentence builder — the Cypher's signature mechanic */}
      <div className="card-mystic p-5 mt-6">
        <div className="label-ref mb-2 flex items-center gap-2"><Sparkles className="w-3 h-3"/> Character Sentence</div>
        <div className="text-base text-gold-bright italic mb-3" data-testid="cypher-sentence">"{sentence}"</div>
        <div className="grid sm:grid-cols-3 gap-3">
          <div>
            <label className="label-ref">Descriptor
              {(campaign?.setting_genre || "") && (
                <span className="text-[9px] text-arcane-light ml-1" title="Genre-gated by campaign setting">
                  · {campaign.setting_genre}
                </span>
              )}
            </label>
            <select className="select" value={c.descriptor} onChange={(e) => setC({ descriptor: e.target.value })}
                    data-testid="cypher-descriptor">
              <optgroup label="Cypher SRD">
                {(ref_.descriptors || []).map((d) => {
                  const dn = typeof d === "string" ? d : d.name;
                  const tags = (typeof d === "object" && d.genres) || ["any"];
                  const gate = (campaign?.setting_genre || "").trim();
                  if (gate && !tags.includes(gate) && !tags.includes("any")) return null;
                  return <option key={dn} value={dn}>{dn}</option>;
                })}
              </optgroup>
              {refRows.filter((r) => r.kind === "skill").length > 0 && (
                <optgroup label="Campaign Reference">
                  {refRows.filter((r) => r.kind === "skill").map((r) => (
                    <option key={r.id} value={r.name}>{r.name}</option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
          <div>
            <label className="label-ref">Type</label>
            <select className="select" value={c.type} onChange={(e) => setType(e.target.value)}
                    data-testid="cypher-type">
              <optgroup label="Cypher SRD">
                {ref_.types.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
              </optgroup>
              {refRows.filter((r) => r.kind === "attribute").length > 0 && (
                <optgroup label="Campaign Reference">
                  {refRows.filter((r) => r.kind === "attribute").map((r) => (
                    <option key={r.id} value={r.name}>{r.name}</option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
          <div>
            <label className="label-ref">Focus</label>
            <select className="select" value={c.focus} onChange={(e) => setC({ focus: e.target.value })}
                    data-testid="cypher-focus">
              <optgroup label="Cypher SRD">
                {(ref_.foci || []).map((f) => {
                  const tags = f.genres || ["any"];
                  const gate = (campaign?.setting_genre || "").trim();
                  if (gate && !tags.includes(gate) && !tags.includes("any")) return null;
                  return <option key={f.name} value={f.name}>{f.name}</option>;
                })}
              </optgroup>
              {refRows.filter((r) => r.kind === "companion").length > 0 && (
                <optgroup label="Campaign Reference">
                  {refRows.filter((r) => r.kind === "companion").map((r) => (
                    <option key={r.id} value={r.name}>{r.name}</option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
        </div>
      </div>

      {/* Header — name / tier */}
      <div className="card-mystic p-5 mt-4 grid sm:grid-cols-2 gap-3">
        <div>
          <label className="label-ref">Name</label>
          <input className="input" value={ch.name} onChange={(e) => setCh({ ...ch, name: e.target.value })}
                 data-testid="cypher-name"/>
        </div>
        <div>
          <label className="label-ref">Tier (1-6)</label>
          <input className="input" type="number" min={1} max={6} value={c.tier}
                 onChange={(e) => setTier(e.target.value)}
                 title="Your Cypher tier — every increment advances a derived stat track (an ability, a skill, or a pool). Recovery die defaults to 1d6+tier."
                 data-testid="cypher-tier"/>
        </div>
      </div>

      {/* Pools & Edge */}
      <div className="card-mystic p-5 mt-4">
        <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
          <h3 className="h-arcane text-sm">Stat Pools &amp; Edge</h3>
          <div className="text-[10px] font-ui uppercase tracking-widest"
               data-testid="cypher-pool-budget-chip"
               title={`Cypher character-creation rule: ${POOL_BUDGET} discretionary points to spend across the three Pools above the Type baseline. Exceeding is a flag for the GM.`}>
            <span className="text-mist">Discretionary </span>
            <span className={over ? "text-ember" : "text-gold-bright"}>
              {spent} / {POOL_BUDGET}
            </span>
            {over && <span className="ml-1 text-ember">over</span>}
          </div>
        </div>
        <div className="grid sm:grid-cols-3 gap-3">
          {["Might", "Speed", "Intellect"].map((k) => (
            <div key={k} className="border border-gold/15 rounded-sm p-3">
              <label className="label-ref">{k}</label>
              <div className="flex items-center gap-2">
                <input className="input w-20 text-center" type="number" min={0} value={c.pools[k]}
                       onChange={(e) => setPool(k, e.target.value)}
                       data-testid={`cypher-pool-${k.toLowerCase()}`}/>
                <span className="text-gold/60 text-[10px]">pool</span>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className="label-ref">Edge</span>
                <input className="input w-16 text-center" type="number" min={0} max={6} value={c.edge[k]}
                       onChange={(e) => setEdge(k, e.target.value)}
                       data-testid={`cypher-edge-${k.toLowerCase()}`}/>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center gap-2">
          <span className="label-ref">Effort (max)</span>
          <input className="input w-20 text-center" type="number" min={1} max={6} value={c.effort}
                 onChange={(e) => setC({ effort: Math.max(1, Math.min(6, +e.target.value)) })}
                 data-testid="cypher-effort"/>
          <span className="text-[10px] text-mist italic">spend per Pool to lower difficulty by 1 step / Effort</span>
        </div>
      </div>

      {/* Cypher derived — Armor (damage soak), Cypher Limit (max carried),
          Recoveries (per-day pool restore action). All editable so the GM
          can tune for setting / power-level. */}
      <div className="card-mystic p-5 mt-4">
        <h3 className="h-arcane text-sm mb-3">Derived · Armor / Cypher Limit / Recoveries</h3>
        <div className="grid sm:grid-cols-4 gap-3">
          <div className="border border-gold/15 rounded-sm p-3">
            <label className="label-ref">Armor</label>
            <input className="input text-center" type="number" min={0} max={10}
                   value={c.armor || 0}
                   onChange={(e) => setC({ armor: Math.max(0, +e.target.value || 0) })}
                   data-testid="cypher-armor"/>
            <div className="text-[9px] text-mist italic mt-1">subtracted from each hit (Speed defense -1 step / 1 Armor)</div>
          </div>
          <div className="border border-gold/15 rounded-sm p-3">
            <label className="label-ref">Cypher Limit</label>
            <input className="input text-center" type="number" min={1} max={6}
                   value={c.cypher_limit || c.starting_cypher_limit || 2}
                   onChange={(e) => setC({ cypher_limit: Math.max(1, Math.min(6, +e.target.value || 2)) })}
                   data-testid="cypher-limit"/>
            <div className="text-[9px] text-mist italic mt-1">max cyphers carried</div>
          </div>
          <div className="border border-gold/15 rounded-sm p-3">
            <label className="label-ref">Recoveries / day</label>
            <input className="input text-center" type="number" min={1} max={8}
                   value={c.recoveries_max || 4}
                   onChange={(e) => setC({ recoveries_max: Math.max(1, Math.min(8, +e.target.value || 4)) })}
                   data-testid="cypher-recoveries-max"/>
            <div className="text-[9px] text-mist italic mt-1">action / 10m / 1h / 10h</div>
          </div>
          <div className="border border-gold/15 rounded-sm p-3">
            <label className="label-ref">Recovery die</label>
            <input className="input text-center text-xs"
                   value={c.recovery_die || `1d6+${c.tier || 1}`}
                   onChange={(e) => setC({ recovery_die: e.target.value })}
                   data-testid="cypher-recovery-die"/>
            <div className="text-[9px] text-mist italic mt-1">restored to a Pool</div>
          </div>
        </div>
      </div>

      {/* Skills training */}
      <div className="card-mystic p-5 mt-4">
        <h3 className="h-arcane text-sm mb-2">Skill Training</h3>
        <div className="flex flex-wrap gap-1.5">
          {ref_.skills.map((sk) => (
            <button key={sk} type="button" onClick={() => toggleSkill(sk)}
                    className={`tag ${c.skill_trains.includes(sk) ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                    data-testid={`cypher-skill-${sk.toLowerCase().replace(/\s+/g, "-")}`}>
              {sk}
            </button>
          ))}
        </div>
      </div>

      {/* Cyphers carried */}
      <FreeList title="Cyphers Carried" placeholder="Adhesion Patch, Spatial Warp, …"
                values={c.cyphers} onChange={(v) => setC({ cyphers: v })}
                testidPrefix="cypher-cypher"/>
      <FreeList title="Type/Focus Abilities" placeholder="e.g. 'Trained Without Armor', 'Bonus Recovery'"
                values={c.abilities} onChange={(v) => setC({ abilities: v })}
                testidPrefix="cypher-ability"/>

      <div className="mt-6">
        <textarea className="input min-h-[80px]" placeholder="GM Intrusion notes / connections / quirks…"
                  value={c.notes} onChange={(e) => setC({ notes: e.target.value })}
                  data-testid="cypher-notes"/>
      </div>

      {err && <div className="text-ember text-sm mt-3">{err}</div>}

      <div className="mt-6 flex gap-2">
        <button onClick={save} className="btn btn-primary" data-testid="cypher-save-btn">
          <Save className="w-4 h-4"/> Save
        </button>
        <Link to={`/app/campaigns/${ch.campaign_id}`} className="btn btn-ghost">Cancel</Link>
      </div>
    </div>
  );
}
