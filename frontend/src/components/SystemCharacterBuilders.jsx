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
import { Save, Plus, X, BookOpen, Sparkles } from "lucide-react";

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

export function Dnd5eBuilder({ campaign, ref_, charId }) {
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

  if (!ch || !ref_) return <div className="p-10 text-mist">Summoning…</div>;
  const c = ch.folio.cypher_state;
  const setC = (patch) => setCh({ ...ch,
    folio: { ...ch.folio, cypher_state: { ...c, ...patch } } });
  const setPool = (k, v) => setC({ pools: { ...c.pools, [k]: Math.max(0, +v) } });
  const setEdge = (k, v) => setC({ edge: { ...c.edge, [k]: Math.max(0, +v) } });
  const toggleSkill = (sk) => setC({ skill_trains:
    c.skill_trains.includes(sk) ? c.skill_trains.filter((x) => x !== sk) : [...c.skill_trains, sk] });

  const sentence = useMemo(() => {
    const article = /^[aeiouAEIOU]/.test(c.descriptor) ? "an" : "a";
    return `I am ${article} ${c.descriptor} ${c.type} who ${c.focus.toLowerCase()}.`;
  }, [c.descriptor, c.type, c.focus]);

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
              {ref_.descriptors.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label className="label-ref">Type</label>
            <select className="select" value={c.type} onChange={(e) => setC({ type: e.target.value })}
                    data-testid="cypher-type">
              {ref_.types.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label-ref">Focus</label>
            <select className="select" value={c.focus} onChange={(e) => setC({ focus: e.target.value })}
                    data-testid="cypher-focus">
              {ref_.foci.map((f) => <option key={f.name} value={f.name}>{f.name}</option>)}
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
  const campaignIdFromUrl = params.id;
  const charId = params.id && window.location.pathname.includes("/characters/") ? params.id : null;
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
  return <div className="p-10 text-mist">Unsupported system.</div>;
}
