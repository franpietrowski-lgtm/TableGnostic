/**
 * SystemCharacterBuilders — first-pass class+slot (D&D 5E) and
 * type-focus-descriptor (Cypher) character builders.
 *
 * Design constraints:
 *   - Re-use the existing /api/characters POST/PUT route with the
 *     system-specific data tucked into `folio` (a free-form Dict[str,Any]).
 *     This means no backend model change is needed — `folio.dnd_state` and
 *     `folio.cypher_state` carry the system-shaped data.
 *   - `name`, `concept`, `published`, `notes`, and the BESM-shape `stats`
 *     are still required by CharacterIn so we set defaults that don't fight
 *     the engine (stats=4/4/4 for D&D so derived values don't NaN; Cypher
 *     uses its own pools and ignores BESM stats).
 *   - These are first-pass — they capture the essential mechanics so a
 *     player can sit at the table tonight; they are not full character
 *     management UIs. Future phases extend.
 */
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { Save, Plus, X, Sparkles } from "lucide-react";

// ─────────────────────── DnD 5E Builder ───────────────────────

const ABILITIES_5E = ["Strength", "Dexterity", "Constitution",
                       "Intelligence", "Wisdom", "Charisma"];
const ABBR_5E = { Strength: "STR", Dexterity: "DEX", Constitution: "CON",
                  Intelligence: "INT", Wisdom: "WIS", Charisma: "CHA" };

function modOf(score) { return Math.floor(((score | 0) - 10) / 2); }
function profByLevel(lvl) { return Math.max(2, 2 + Math.floor((Math.max(1, lvl) - 1) / 4)); }

const empty5e = (cid) => ({
  campaign_id: cid, name: "", concept: "", power_level: "Heroic", total_points: 0,
  size: "Medium", token_color: "",
  stats: { body: 4, mind: 4, soul: 4 }, // satisfies CharacterIn — unused in 5E mode
  attributes: [], defects: [], skills: [], power_packs: [], notes: "", published: false,
  folio: {
    dnd_state: {
      class: "Fighter", level: 1, race: "Human", background: "",
      ability_scores: { Strength: 10, Dexterity: 10, Constitution: 10,
                         Intelligence: 10, Wisdom: 10, Charisma: 10 },
      saving_throw_profs: ["Strength", "Constitution"],
      skill_profs: [], inventory: [], spells_known: [], notes: "",
    },
  },
});

export function Dnd5eBuilder({ campaign, ref_, charId, hybridSupplement }) {
  const nav = useNavigate();
  const [ch, setCh] = useState(empty5e(campaign?.id));
  const [err, setErr] = useState("");

  useEffect(() => {
    if (charId) {
      api.get(`/characters/${charId}`).then((r) => {
        const existing = r.data;
        if (!existing.folio?.dnd_state) {
          existing.folio = { ...(existing.folio || {}),
                              dnd_state: empty5e(campaign?.id).folio.dnd_state };
        }
        setCh(existing);
      });
    } else {
      setCh(empty5e(campaign?.id));
    }
  }, [charId, campaign?.id]);

  if (!ch || !ref_) return <div className="p-10 text-mist">Summoning the forge…</div>;
  const s = ch.folio.dnd_state;
  const setS = (patch) => setCh({ ...ch,
    folio: { ...ch.folio, dnd_state: { ...s, ...patch } } });
  const setScore = (a, v) => setS({ ability_scores: { ...s.ability_scores, [a]: Math.max(1, +v) } });
  const toggle = (k, v) => setS({ [k]: s[k].includes(v) ? s[k].filter((x) => x !== v) : [...s[k], v] });

  const cls = ref_.classes.find((c) => c.name === s.class);
  const race = ref_.races.find((r) => r.name === s.race);
  const hp = (cls?.hit_die || 8) + modOf(s.ability_scores.Constitution) +
             ((cls?.hit_die || 8) / 2 + 1) * (s.level - 1);
  const ac = 10 + modOf(s.ability_scores.Dexterity);
  const prof = profByLevel(s.level);

  const save = async () => {
    setErr("");
    try {
      const payload = { ...ch };
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
    <div className="px-8 md:px-12 py-10 max-w-5xl" data-system="dnd-5e" data-testid="dnd5e-builder">
      <Link to={`/app/campaigns/${ch.campaign_id}`} className="text-xs font-ui uppercase tracking-widest text-gold/70">← Campaign</Link>
      <h1 className="font-display text-4xl tracking-wide text-parchment mt-4">D&D 5E Character</h1>
      <div className="text-[11px] text-mist/70 italic mt-1">Mechanics from the System Reference Document 5.1 (CC-BY-4.0). © Wizards of the Coast.</div>

      {/* Header — name / class / level / race */}
      <div className="card-mystic p-5 mt-6 grid sm:grid-cols-2 gap-3">
        <div>
          <label className="label-ref">Name</label>
          <input className="input" value={ch.name}
                 onChange={(e) => setCh({ ...ch, name: e.target.value })}
                 data-testid="dnd-name"/>
        </div>
        <div>
          <label className="label-ref">Concept (one line)</label>
          <input className="input" value={ch.concept}
                 onChange={(e) => setCh({ ...ch, concept: e.target.value })}
                 data-testid="dnd-concept"/>
        </div>
        <div>
          <label className="label-ref">Class</label>
          <select className="select" value={s.class} onChange={(e) => setS({ class: e.target.value })}
                  data-testid="dnd-class">
            {ref_.classes.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label className="label-ref">Level (1-20)</label>
          <input className="input" type="number" min={1} max={20} value={s.level}
                 onChange={(e) => setS({ level: Math.max(1, Math.min(20, +e.target.value)) })}
                 data-testid="dnd-level"/>
        </div>
        <div>
          <label className="label-ref">Race</label>
          <select className="select" value={s.race} onChange={(e) => setS({ race: e.target.value })}
                  data-testid="dnd-race">
            {ref_.races.map((r) => <option key={r.name} value={r.name}>{r.name}</option>)}
          </select>
        </div>
        <div>
          <label className="label-ref">Background</label>
          <input className="input" value={s.background}
                 onChange={(e) => setS({ background: e.target.value })}
                 placeholder="Acolyte / Soldier / Sage / …" data-testid="dnd-background"/>
        </div>
      </div>

      {/* Class summary */}
      {cls && (
        <div className="card-mystic p-4 mt-4 text-[12px] text-parchment/85 leading-snug" data-testid="dnd-class-card">
          <div className="label-ref mb-1">Class summary</div>
          d{cls.hit_die} HD · primary {cls.primary} · saves {cls.saves.join(", ")}
          {cls.casting !== "none" && ` · ${cls.casting} caster`} · SRD p.{cls.page}
        </div>
      )}
      {race && (
        <div className="card-mystic p-4 mt-2 text-[12px] text-parchment/85 leading-snug" data-testid="dnd-race-card">
          <div className="label-ref mb-1">Race</div>
          {race.asi} · {race.size} · {race.speed ? `speed ${race.speed} ft` : "—"}
          {race.traits && ` · traits: ${race.traits.join(", ")}`}
        </div>
      )}

      {/* Ability scores */}
      <div className="card-mystic p-5 mt-4">
        <h3 className="h-arcane text-sm mb-3">Ability Scores</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          {ABILITIES_5E.map((a) => {
            const score = s.ability_scores[a];
            const m = modOf(score);
            return (
              <div key={a} className="border border-gold/15 rounded-sm p-3">
                <label className="label-ref">{a} ({ABBR_5E[a]})</label>
                <div className="flex items-center gap-2">
                  <input className="input w-20 text-center" type="number" min={1} max={30}
                         value={score} onChange={(e) => setScore(a, e.target.value)}
                         data-testid={`dnd-score-${ABBR_5E[a]}`}/>
                  <span className="text-gold font-display">mod {m >= 0 ? "+" : ""}{m}</span>
                </div>
                <div className="text-[10px] text-mist mt-1 font-ui uppercase tracking-widest">
                  Save: {ABBR_5E[a]} {m >= 0 ? "+" : ""}{m}{s.saving_throw_profs.includes(a) ? ` +${prof} prof` : ""}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Save proficiencies */}
      <div className="card-mystic p-5 mt-4">
        <h3 className="h-arcane text-sm mb-2">Saving Throw Proficiencies</h3>
        <div className="flex flex-wrap gap-1.5">
          {ABILITIES_5E.map((a) => (
            <button key={a} type="button" onClick={() => toggle("saving_throw_profs", a)}
                    className={`tag ${s.saving_throw_profs.includes(a) ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                    data-testid={`dnd-save-${ABBR_5E[a]}`}>
              {ABBR_5E[a]}
            </button>
          ))}
        </div>
      </div>

      {/* Skill proficiencies */}
      <div className="card-mystic p-5 mt-4">
        <h3 className="h-arcane text-sm mb-2">Skill Proficiencies</h3>
        <div className="flex flex-wrap gap-1.5">
          {ref_.skills.map((sk) => (
            <button key={sk.name} type="button" onClick={() => toggle("skill_profs", sk.name)}
                    className={`tag ${s.skill_profs.includes(sk.name) ? "border-gold text-gold-bright bg-gold/15" : ""}`}
                    data-testid={`dnd-skill-${sk.name.replace(/\s+/g, "-")}`}>
              {sk.name} <span className="text-mist/60 text-[9px]">({ABBR_5E[sk.ability]})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Derived */}
      <div className="card-mystic p-5 mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center" data-testid="dnd-derived">
        <Stat label="HP (base)" v={Math.floor(hp)}/>
        <Stat label="AC (base)" v={ac}/>
        <Stat label="Proficiency" v={`+${prof}`}/>
        <Stat label="Initiative" v={modOf(s.ability_scores.Dexterity) >= 0 ? `+${modOf(s.ability_scores.Dexterity)}` : modOf(s.ability_scores.Dexterity)}/>
      </div>

      {/* Inventory + spells (free-text JSON-shaped lists) */}
      <FreeList title="Inventory / Equipment" placeholder="Longsword, Chain Mail, Healer's Kit…"
                values={s.inventory} onChange={(v) => setS({ inventory: v })}
                testidPrefix="dnd-inv"/>
      {cls?.casting !== "none" && (
        <FreeList title="Spells Known / Prepared"
                  placeholder="Fire Bolt, Magic Missile, Cure Wounds…"
                  values={s.spells_known} onChange={(v) => setS({ spells_known: v })}
                  testidPrefix="dnd-spell"/>
      )}

      {/* Anime 5E hybrid — Tri-Stat point-buy supplement on top of d20 sheet */}
      {hybridSupplement && (
        <Anime5eHybridSupplement ch={ch} setCh={setCh}
                                  ref_={hybridSupplement}/>
      )}

      <div className="mt-6">
        <textarea className="input min-h-[80px]" placeholder="GM notes / personality / backstory hooks…"
                  value={s.notes} onChange={(e) => setS({ notes: e.target.value })}
                  data-testid="dnd-notes"/>
      </div>

      {err && <div className="text-ember text-sm mt-3">{err}</div>}

      <div className="mt-6 flex gap-2">
        <button onClick={save} className="btn btn-primary" data-testid="dnd-save-btn">
          <Save className="w-4 h-4"/> Save
        </button>
        <Link to={`/app/campaigns/${ch.campaign_id}`} className="btn btn-ghost">Cancel</Link>
      </div>
    </div>
  );
}


// ─────────────────────── Cypher Builder ───────────────────────

const emptyCypher = (cid) => ({
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
    });
  };

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
            <label className="label-ref">Descriptor</label>
            <select className="select" value={c.descriptor} onChange={(e) => setC({ descriptor: e.target.value })}
                    data-testid="cypher-descriptor">
              <optgroup label="Cypher SRD">
                {ref_.descriptors.map((d) => <option key={d} value={d}>{d}</option>)}
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
                {ref_.foci.map((f) => <option key={f.name} value={f.name}>{f.name}</option>)}
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
                 onChange={(e) => setC({ tier: Math.max(1, Math.min(6, +e.target.value)) })}
                 data-testid="cypher-tier"/>
        </div>
      </div>

      {/* Pools & Edge */}
      <div className="card-mystic p-5 mt-4">
        <h3 className="h-arcane text-sm mb-3">Stat Pools &amp; Edge</h3>
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


// ─────────────────────── Shared bits ───────────────────────

function Stat({ label, v }) {
  return (
    <div>
      <div className="text-[10px] font-ui uppercase tracking-widest text-mist">{label}</div>
      <div className="font-display text-xl text-gold-bright">{v}</div>
    </div>
  );
}

function FreeList({ title, placeholder, values, onChange, testidPrefix }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    if (!draft.trim()) return;
    onChange([...(values || []), draft.trim()]);
    setDraft("");
  };
  return (
    <div className="card-mystic p-5 mt-4" data-testid={`${testidPrefix}-list`}>
      <h3 className="h-arcane text-sm mb-2">{title}</h3>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {(values || []).map((v, i) => (
          <span key={i} className="tag">{v}
            <button onClick={() => onChange(values.filter((_, j) => j !== i))} className="ml-1">
              <X className="w-3 h-3 inline"/>
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="input" placeholder={placeholder} value={draft}
               onChange={(e) => setDraft(e.target.value)}
               onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
               data-testid={`${testidPrefix}-input`}/>
        <button onClick={add} type="button" className="btn btn-ghost"
                data-testid={`${testidPrefix}-add`}>
          <Plus className="w-3 h-3"/>
        </button>
      </div>
    </div>
  );
}

// Loader wrapper — fetches /api/systems/{id}/reference and routes.
export default function SystemBuilderLoader({ systemId }) {
  const params = useParams();
  // Two route shapes:
  //   /app/campaigns/:id/characters/new  → params.id is the CAMPAIGN id
  //   /app/characters/:id/edit           → params.id is the CHARACTER id
  // Distinguish by whether the URL path STARTS with /app/characters/ —
  // pathname.includes("/characters/") is also true for the campaign-scoped
  // /new route, which (until this fix) made the loader try
  // GET /characters/{campaign_id} and 404 every Anime/Cypher new-character forge.
  const isEdit = /\/characters\/[^/]+\/edit$/.test(window.location.pathname);
  const charId = isEdit ? params.id : null;
  const campaignIdFromUrl = isEdit ? null : params.id;
  const [ref_, setRef] = useState(null);
  const [campaign, setCampaign] = useState(null);

  useEffect(() => {
    let cid = campaignIdFromUrl;
    (async () => {
      if (charId && window.location.pathname.includes("/edit")) {
        const existing = await api.get(`/characters/${charId}`).then((x) => x.data).catch(() => null);
        if (existing) cid = existing.campaign_id;
      }
      const [r, c] = await Promise.all([
        api.get(`/systems/${systemId}/reference`).then((x) => x.data).catch(() => null),
        api.get(`/campaigns/${cid}`).then((x) => x.data).catch(() => null),
      ]);
      setRef(r); setCampaign(c);
    })();
    // eslint-disable-next-line
  }, [campaignIdFromUrl, charId, systemId]);

  if (!ref_ || !campaign) return <div className="p-10 text-mist">Summoning the {systemId} forge…</div>;

  if (systemId === "dnd-5e") return <Dnd5eBuilder campaign={campaign} ref_={ref_} charId={charId}/>;
  if (systemId === "cypher") return <CypherBuilder campaign={campaign} ref_={ref_} charId={charId}/>;
  if (systemId === "anime-5e") return <Anime5eBuilder campaign={campaign} ref_={ref_} charId={charId}/>;
  return <div className="p-10 text-mist">Unsupported system.</div>;
}


/**
 * Anime 5E — hybrid character builder.
 *
 * Anime 5E is a Tri-Stat OGL release that grafts the BESM point-buy engine
 * onto a 5E d20 chassis. It uses 5E ability scores AND lets you buy
 * Tri-Stat attributes / skills / defects on top with a point budget.
 *
 * Implementation: render the Dnd5eBuilder shape, plus a "Tri-Stat point-buy
 * supplement" card that captures point_buy spend in `folio.anime5e_state`.
 * Persists alongside `dnd_state` so dice macros + sheet view both work.
 */
function Anime5eBuilder({ campaign, ref_, charId }) {
  // Build a 5E-shape ref from the Anime 5E hybrid response. The Anime 5E
  // reference DOES expose `classes`, `heritages`/`races`, `skills`, etc.
  // but its abilities default to Body/Mind/Soul. For the D&D-shape sheet we
  // upgrade abilities to the D&D 6 + map back when point-buy is shown.
  const dndRef = {
    ...ref_,
    classes: ref_.classes || [],
    races: ref_.heritages || ref_.races || [],
    abilities: ref_.abilities || [
      { name: "Strength", abbr: "STR" }, { name: "Dexterity", abbr: "DEX" },
      { name: "Constitution", abbr: "CON" }, { name: "Intelligence", abbr: "INT" },
      { name: "Wisdom", abbr: "WIS" }, { name: "Charisma", abbr: "CHA" },
    ],
    skills: ref_.skills?.length ? ref_.skills : [],
  };
  return (
    <Dnd5eBuilder campaign={campaign} ref_={dndRef} charId={charId}
                  hybridSupplement={ref_}/>
  );
}


/**
 * Anime5eHybridSupplement — Tri-Stat point-buy layer for Anime 5E.
 * The top sheet uses 5E mechanics (class/level/abilities/saves/skills),
 * and this card lets the player spend a separate Tri-Stat point budget
 * on Tri-Stat Attributes (e.g. Combat Mastery, Heightened Senses, Tough,
 * Personal Gear) for genre-flavoured powers that don't fit the 5E class.
 *
 * Persists into `folio.anime5e_state` alongside `folio.dnd_state`.
 */
function Anime5eHybridSupplement({ ch, setCh, ref_ }) {
  const state = ch.folio?.anime5e_state || {
    point_budget: 50, point_buys: [],
  };
  const setState = (patch) => setCh({ ...ch,
    folio: { ...(ch.folio || {}),
              anime5e_state: { ...state, ...patch } } });
  const buys = state.point_buys || [];
  const totalSpent = buys.reduce(
    (sum, b) => sum + ((b.cost_per_level || 0) * (b.level || 1)), 0);
  const remaining = (state.point_budget || 0) - totalSpent;

  const addAttribute = (name) => {
    const opt = (ref_.point_buy_attributes || []).find((a) => a.name === name);
    if (!opt) return;
    setState({ point_buys: [...buys, {
      name: opt.name, cost_per_level: opt.cost_per_level,
      level: 1, blurb_role: opt.blurb_role,
    }] });
  };
  const setBuy = (i, patch) => {
    const next = buys.slice();
    next[i] = { ...next[i], ...patch };
    setState({ point_buys: next });
  };
  const removeBuy = (i) => setState({ point_buys: buys.filter((_, j) => j !== i) });

  return (
    <div className="card-mystic p-5 mt-4 border-pink-400/30"
         style={{ borderLeftWidth: 3, borderLeftColor: "#E03A8E" }}
         data-testid="anime5e-hybrid-supplement">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <h3 className="h-arcane text-sm">
            Tri-Stat Supplement
            <span className="text-[9px] text-mist ml-2 uppercase tracking-widest">Anime 5E hybrid</span>
          </h3>
          <div className="text-[11px] text-mist/80 italic">
            Point-buy attributes layered on top of your d20 sheet — for
            genre powers, custom gear, and signature techniques the 5E
            class doesn't cover.
          </div>
        </div>
        <div className="text-right">
          <div className="label-ref">Point Budget</div>
          <div className="font-display text-2xl text-gold-bright">
            <span className={remaining < 0 ? "text-ember" : ""}>{remaining}</span>
            <span className="text-mist text-sm"> / {state.point_budget}</span>
          </div>
          <div className="text-[10px] text-mist">spent {totalSpent}</div>
        </div>
      </div>

      <div className="mt-3 grid sm:grid-cols-2 gap-2">
        <input className="input" type="number" min={0}
               placeholder="Point budget (50)"
               value={state.point_budget}
               onChange={(e) => setState({ point_budget: Math.max(0, +e.target.value || 0) })}
               data-testid="anime5e-point-budget"/>
        <select className="select"
                onChange={(e) => { if (e.target.value) { addAttribute(e.target.value); e.target.value = ""; } }}
                data-testid="anime5e-add-attribute">
          <option value="">+ Add Tri-Stat Attribute…</option>
          {(ref_.point_buy_attributes || []).map((a) => (
            <option key={a.name} value={a.name}>
              {a.name} ({a.cost_per_level} pts/lvl) — {a.blurb_role}
            </option>
          ))}
        </select>
      </div>

      {buys.length === 0 ? (
        <div className="text-mist italic text-xs mt-3">
          Pick a Tri-Stat Attribute above to add a point-buy power.
        </div>
      ) : (
        <div className="mt-3 space-y-2">
          {buys.map((b, i) => (
            <div key={i}
                 className="border border-gold/15 rounded-sm p-2.5 flex items-center gap-2 flex-wrap"
                 data-testid={`anime5e-buy-${i}`}>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-parchment font-ui">
                  <b>{b.name}</b>
                  <span className="text-[10px] text-mist ml-2">{b.cost_per_level} pts/lvl</span>
                </div>
                <div className="text-[10px] text-mist/70 italic">{b.blurb_role}</div>
              </div>
              <label className="label-ref">LVL</label>
              <input type="number" min={1} max={6} className="input w-16 text-center"
                     value={b.level}
                     onChange={(e) => setBuy(i, { level: Math.max(1, +e.target.value || 1) })}
                     data-testid={`anime5e-buy-level-${i}`}/>
              <span className="font-display text-gold">
                {b.cost_per_level * b.level} pts
              </span>
              <button onClick={() => removeBuy(i)} className="text-ember/70 hover:text-ember"
                      data-testid={`anime5e-buy-remove-${i}`}>
                <X className="w-4 h-4"/>
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="text-[10px] text-mist/60 italic mt-3">
        Anime 5E hybrid mode — the 5E class/level/slot mechanics drive your
        d20 rolls; Tri-Stat point-buy adds genre-flavoured powers.
      </div>
    </div>
  );
}
