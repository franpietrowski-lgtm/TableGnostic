import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../lib/api";
import { Plus, X, Save, Trash2, BookOpen } from "lucide-react";

const emptyChar = (campaign_id) => ({
  campaign_id, name: "", concept: "", power_level: "Heroic", total_points: 120,
  stats: { body: 4, mind: 4, soul: 4 },
  attributes: [], defects: [], skills: [], notes: "", published: false,
  folio: {
    aliases: "", gender_species_age: "", occupation: "",
    physical_description: "", personality: "", motivations: "", fears: "",
    edges: [], obstacles: [], goals: [], family: [], rivals: [],
    history_events: [], group_dynamics: "", advancement_log: [], journal: [],
  },
});

export default function CharacterBuilder() {
  const params = useParams();
  const nav = useNavigate();
  const campaignIdFromUrl = params.id; // for /campaigns/:id/characters/new
  const charId = params.id && window.location.pathname.includes("/characters/") ? params.id : null;

  const [ref, setRef] = useState(null);
  const [customs, setCustoms] = useState([]);
  const [ch, setCh] = useState(null);
  const [campaign, setCampaign] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      const r = await api.get("/besm/reference").then((x) => x.data);
      setRef(r);
      let campaignId = campaignIdFromUrl;
      if (charId && window.location.pathname.includes("/edit")) {
        const existing = await api.get(`/characters/${charId}`).then((x) => x.data);
        setCh(existing);
        campaignId = existing.campaign_id;
      } else {
        setCh(emptyChar(campaignIdFromUrl));
      }
      const [cu, camp] = await Promise.all([
        api.get(`/campaigns/${campaignId}/custom`).then((x) => x.data).catch(() => []),
        api.get(`/campaigns/${campaignId}`).then((x) => x.data).catch(() => null),
      ]);
      setCustoms(cu); setCampaign(camp);
      // Pre-set power_level + total_points from campaign if new character
      if (!charId && camp) {
        const pts = (r.power_levels.find(p => p.name === camp.power_level) || {}).points || 120;
        setCh((prev) => prev ? ({ ...prev, power_level: camp.power_level, total_points: pts }) : prev);
      }
    })();
  }, [campaignIdFromUrl, charId]);

  const pointsForPowerLevel = (pl) => (ref?.power_levels.find((p) => p.name === pl)?.points || 120);
  useEffect(() => { if (ch && ref) setCh((c) => ({ ...c, total_points: pointsForPowerLevel(c.power_level) })); // eslint-disable-next-line
  }, [ch?.power_level, ref]);

  const spent = useMemo(() => {
    if (!ch) return { stat_cost: 0, attribute_cost: 0, skill_cost: 0, defect_points: 0, total_spent: 0 };
    const stat_cost = ch.stats.body + ch.stats.mind + ch.stats.soul;
    const attribute_cost = ch.attributes.reduce((s, a) => {
      const base = (a.cost_per_level || 0) * (a.level || 0);
      const mods = (a.enhancements.length - a.limiters.length) * (a.level || 0);
      return s + base + mods;
    }, 0);
    const skill_cost = ch.skills.reduce((s, k) => s + (k.cost_per_level || 0) * (k.level || 0), 0);
    const defect_points = ch.defects.reduce((s, d) => s + (d.points_per_rank || 0) * (d.rank || 0), 0);
    return {
      stat_cost, attribute_cost, skill_cost, defect_points,
      total_spent: stat_cost + attribute_cost + skill_cost + defect_points,
    };
  }, [ch]);

  if (!ch || !ref) return <div className="p-10 text-mist">Summoning the forge…</div>;

  const remaining = ch.total_points - spent.total_spent;

  const derived = (() => {
    const attrMap = Object.fromEntries(ch.attributes.map((a) => [a.name, a]));
    const lv = (n) => attrMap[n]?.level || 0;
    const { body, mind, soul } = ch.stats;
    const cv = Math.floor((body + mind + soul) / 3);
    return {
      cv, atk: cv + lv("Attack Mastery"), dfn: cv - 2 + lv("Defence Mastery"),
      hp: (body + soul) * 5 + lv("Tough") * 5,
      ep: (mind + soul) * 5 + lv("Energised") * 5,
      dm: 5 + lv("Massive Damage") * 5,
    };
  })();

  const addAttribute = (base) => {
    setCh({
      ...ch, attributes: [...ch.attributes, {
        name: base.name, level: 1, cost_per_level: base.cost_per_level || 0,
        enhancements: [], limiters: [], page: base.page, note: base.note || "",
        custom_attribute_id: base.id || null,
      }],
    });
  };
  const addDefect = (base) => {
    setCh({
      ...ch, defects: [...ch.defects, {
        name: base.name, rank: 1, points_per_rank: base.points_per_rank || 0,
        category: base.category || "Custom", page: base.page, note: base.note || "",
      }],
    });
  };
  const addSkill = (base) => {
    setCh({
      ...ch, skills: [...ch.skills, {
        group: base.name, level: 1, cost_per_level: base.cost_per_level || 1, page: base.page,
      }],
    });
  };

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

  const customAttrs = customs.filter((c) => c.kind === "attribute");
  const customDefects = customs.filter((c) => c.kind === "defect");
  const customSkills = customs.filter((c) => c.kind === "skill");

  // Campaign filters
  const allow = (list, name) => !list || list.length === 0 || list.includes(name);
  const prohib = (list, name) => list && list.includes(name);
  const filterBy = (items, allowed, prohibited) =>
    items.filter((it) => allow(allowed, it.name) && !prohib(prohibited, it.name));
  const filteredAttrOpts = [
    ...filterBy(ref.attributes, campaign?.allowed_attributes, campaign?.prohibited_attributes).map((a) => ({ ...a, _group: "BESM 4E" })),
    ...customAttrs.map((c) => ({ ...c, _group: "Custom (GM)" })),
  ];
  const filteredDefectOpts = [
    ...filterBy(ref.defects, campaign?.allowed_defects, campaign?.prohibited_defects).map((d) => ({ ...d, _group: d.category })),
    ...customDefects.map((c) => ({
      ...c, _group: "Custom (GM)",
      points_per_rank: -Math.abs(+c.cost_per_level || 1), category: c.category || "Custom",
    })),
  ];
  const filteredSkillOpts = [
    ...filterBy(ref.skill_groups, campaign?.allowed_skill_groups, campaign?.prohibited_skill_groups),
    ...customSkills.map((c) => ({ ...c, _group: "Custom (GM)" })),
  ];

  return (
    <div className="px-8 md:px-12 py-10 max-w-7xl">
      <Link to={`/app/campaigns/${ch.campaign_id}`} className="text-xs font-ui uppercase tracking-widest text-gold/70">
        ← Campaign
      </Link>

      {campaign && (
        <div className="mt-4 card-mystic p-5" data-testid="campaign-briefing">
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <div className="label-ref">Campaign Briefing · {campaign.name}</div>
              <div className="mt-2 flex flex-wrap gap-3 text-xs font-ui">
                <span className="tag">Power Level · {campaign.power_level}</span>
                <span className="tag">{(ref.power_levels.find(p => p.name === campaign.power_level) || {}).points || 120} Character Points</span>
                <span className="tag">GM · {campaign.gm_name}</span>
                {campaign.genre && <span className="tag">{campaign.genre}</span>}
                {campaign.tone && <span className="tag">{campaign.tone}</span>}
              </div>
            </div>
          </div>
          {campaign.player_primer && (
            <>
              <div className="divider-sigil my-4"/>
              <div className="label-ref mb-2">Player Primer (from the GM)</div>
              <div className="text-sm text-parchment/90 font-body whitespace-pre-wrap leading-relaxed italic border-l-2 border-gold/40 pl-4" data-testid="builder-primer">
                {campaign.player_primer}
              </div>
            </>
          )}
          {((campaign.allowed_attributes?.length || 0) + (campaign.prohibited_attributes?.length || 0) +
            (campaign.allowed_defects?.length || 0) + (campaign.prohibited_defects?.length || 0) +
            (campaign.allowed_skill_groups?.length || 0) + (campaign.prohibited_skill_groups?.length || 0)) > 0 && (
            <div className="mt-4 grid md:grid-cols-2 gap-2 text-xs">
              {campaign.allowed_attributes?.length > 0 && (
                <div><span className="label-ref">Allowed Attributes:</span> <span className="text-gold/80">{campaign.allowed_attributes.join(", ")}</span></div>
              )}
              {campaign.prohibited_attributes?.length > 0 && (
                <div><span className="label-ref">Prohibited:</span> <span className="text-ember/80">{campaign.prohibited_attributes.join(", ")}</span></div>
              )}
              {campaign.allowed_defects?.length > 0 && (
                <div><span className="label-ref">Allowed Defects:</span> <span className="text-gold/80">{campaign.allowed_defects.join(", ")}</span></div>
              )}
              {campaign.prohibited_defects?.length > 0 && (
                <div><span className="label-ref">Prohibited:</span> <span className="text-ember/80">{campaign.prohibited_defects.join(", ")}</span></div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="mt-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="label-ref mb-1">Character Forge · BESM 4E</div>
          <h1 className="font-display text-4xl text-parchment tracking-wide">
            {ch.name || "Unnamed Soul"}
          </h1>
        </div>
        <div className="card-mystic px-5 py-3 text-right">
          <div className="label-ref">Points</div>
          <div className="font-display text-2xl text-gold">{remaining} / {ch.total_points}</div>
          <div className="text-[10px] font-ui tracking-widest uppercase text-mist">
            stats {spent.stat_cost} · attrs {spent.attribute_cost} · skills {spent.skill_cost} · defects {spent.defect_points}
          </div>
        </div>
      </div>

      {err && <div className="mt-3 text-ember text-sm">{err}</div>}

      <div className="mt-8 grid lg:grid-cols-3 gap-6">
        {/* LEFT: core */}
        <div className="card-mystic p-6 space-y-4">
          <div className="label-ref">Identity</div>
          <input className="input" placeholder="Name" value={ch.name}
                 onChange={(e) => setCh({ ...ch, name: e.target.value })} data-testid="char-name"/>
          <textarea className="input" placeholder="Concept / archetype"
                    value={ch.concept} onChange={(e) => setCh({ ...ch, concept: e.target.value })} data-testid="char-concept"/>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-ref block mb-1">Power Level</label>
              <select className="select" value={ch.power_level}
                      onChange={(e) => setCh({ ...ch, power_level: e.target.value })} data-testid="char-power-level">
                {ref.power_levels.map((p) => <option key={p.name}>{p.name}</option>)}
              </select>
              <div className="text-[10px] text-gold/60 mt-1 font-ui uppercase tracking-widest">
                {ref.power_levels.find((p) => p.name === ch.power_level)?.points} pts · p.{ref.power_levels.find((p) => p.name === ch.power_level)?.page} BESM 4E
              </div>
            </div>
            <div>
              <label className="label-ref block mb-1">Total Points</label>
              <input type="number" className="input" value={ch.total_points}
                     onChange={(e) => setCh({ ...ch, total_points: +e.target.value })} data-testid="char-total"/>
            </div>
          </div>

          <div className="divider-sigil" />
          <div className="label-ref">Core Stats · p.71 BESM 4E</div>
          <div className="grid grid-cols-3 gap-3">
            {["body", "mind", "soul"].map((s) => (
              <div key={s}>
                <label className="label-ref block mb-1">{s.toUpperCase()}</label>
                <input type="number" min={1} max={20} className="input text-center font-display text-xl"
                       value={ch.stats[s]}
                       onChange={(e) => setCh({ ...ch, stats: { ...ch.stats, [s]: +e.target.value } })}
                       data-testid={`stat-${s}`}/>
              </div>
            ))}
          </div>

          <div className="divider-sigil" />
          <div className="label-ref">Derived · ch.8 p.168 BESM 4E</div>
          <div className="grid grid-cols-3 gap-2 text-center">
            {[
              ["CV", derived.cv], ["ATK", derived.atk], ["DEF", derived.dfn],
              ["HP", derived.hp], ["EP", derived.ep], ["DM", derived.dm],
            ].map(([l, v]) => (
              <div key={l} className="border border-gold/15 py-2 rounded-sm">
                <div className="label-ref">{l}</div>
                <div className="font-display text-gold text-lg">{v}</div>
              </div>
            ))}
          </div>

          <div className="divider-sigil" />
          <textarea className="input" placeholder="Notes, backstory, moves…"
                    value={ch.notes} onChange={(e) => setCh({ ...ch, notes: e.target.value })} data-testid="char-notes"/>

          <div className="flex justify-end gap-2 pt-2">
            <button onClick={save} className="btn btn-primary" data-testid="save-character-btn">
              <Save className="w-4 h-4"/> Save
            </button>
          </div>
        </div>

        {/* RIGHT: modular lists */}
        <div className="lg:col-span-2 space-y-6">
          <ListSection
            title="Attributes · p.74–132 BESM 4E"
            testIdPrefix="attributes"
            items={ch.attributes}
            options={filteredAttrOpts}
            enhancementOpts={ref.enhancements}
            limiterOpts={ref.limiters}
            onAdd={addAttribute}
            renderRow={(a, idx) => (
              <AttributeRow key={idx} idx={idx} a={a} ref={ref}
                onUpdate={(next) => {
                  const arr = [...ch.attributes]; arr[idx] = next;
                  setCh({ ...ch, attributes: arr });
                }}
                onRemove={() => {
                  const arr = [...ch.attributes]; arr.splice(idx, 1);
                  setCh({ ...ch, attributes: arr });
                }}/>
            )}
            kind="attribute"
          />

          <ListSection
            title="Defects · p.154 BESM 4E"
            testIdPrefix="defects"
            items={ch.defects}
            options={filteredDefectOpts}
            onAdd={addDefect}
            renderRow={(d, idx) => (
              <DefectRow key={idx} idx={idx} d={d}
                onUpdate={(next) => {
                  const arr = [...ch.defects]; arr[idx] = next;
                  setCh({ ...ch, defects: arr });
                }}
                onRemove={() => {
                  const arr = [...ch.defects]; arr.splice(idx, 1);
                  setCh({ ...ch, defects: arr });
                }}/>
            )}
            kind="defect"
          />

          <ListSection
            title="Skill Groups · p.120 BESM 4E"
            testIdPrefix="skills"
            items={ch.skills}
            options={filteredSkillOpts}
            onAdd={addSkill}
            renderRow={(s, idx) => (
              <SkillRow key={idx} idx={idx} s={s}
                onUpdate={(next) => {
                  const arr = [...ch.skills]; arr[idx] = next;
                  setCh({ ...ch, skills: arr });
                }}
                onRemove={() => {
                  const arr = [...ch.skills]; arr.splice(idx, 1);
                  setCh({ ...ch, skills: arr });
                }}/>
            )}
            kind="skill"
          />

          <FolioPanel ch={ch} setCh={setCh}/>
        </div>
      </div>
    </div>
  );
}

function FolioPanel({ ch, setCh }) {
  const f = ch.folio || {};
  const setF = (patch) => setCh({ ...ch, folio: { ...f, ...patch } });
  const addItem = (key, item) => setF({ [key]: [...(f[key] || []), item] });
  const updateItem = (key, idx, patch) => {
    const arr = [...(f[key] || [])]; arr[idx] = { ...arr[idx], ...patch };
    setF({ [key]: arr });
  };
  const removeItem = (key, idx) => {
    const arr = [...(f[key] || [])]; arr.splice(idx, 1);
    setF({ [key]: arr });
  };

  return (
    <div className="card-mystic p-5 space-y-5" data-testid="folio-panel">
      <div className="flex items-center justify-between">
        <div>
          <div className="label-ref">Character Folio · BESM Folio v1.01</div>
          <h3 className="h-arcane text-sm mt-1">Personality, goals, history, journal</h3>
        </div>
        <span className="text-[10px] text-mist/70 italic">expand the parts that matter</span>
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        <FolioInput label="Aliases" value={f.aliases} onChange={(v) => setF({ aliases: v })} testid="folio-aliases"/>
        <FolioInput label="Gender · Species · Age" value={f.gender_species_age}
                    onChange={(v) => setF({ gender_species_age: v })} testid="folio-gsa"/>
        <FolioInput label="Occupation" value={f.occupation} onChange={(v) => setF({ occupation: v })} testid="folio-occupation"/>
        <FolioInput label="Group dynamics" value={f.group_dynamics}
                    onChange={(v) => setF({ group_dynamics: v })} testid="folio-group"/>
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        <FolioTextarea label="Physical description" value={f.physical_description}
                       onChange={(v) => setF({ physical_description: v })} prompt="What does the table notice first?"
                       testid="folio-physical"/>
        <FolioTextarea label="Personality" value={f.personality}
                       onChange={(v) => setF({ personality: v })} prompt="One mannerism, one belief, one wound."
                       testid="folio-personality"/>
        <FolioTextarea label="Motivations / Goals" value={f.motivations}
                       onChange={(v) => setF({ motivations: v })} prompt="What do they want before this campaign ends?"
                       testid="folio-motivations"/>
        <FolioTextarea label="Fears / Weaknesses" value={f.fears}
                       onChange={(v) => setF({ fears: v })} testid="folio-fears"/>
      </div>

      <ChipList label="Edges" hint="Situational +1 bonuses (BESM Folio Edges)"
                items={f.edges || []} setItems={(arr) => setF({ edges: arr })}
                placeholder="e.g. familiar with the docks; knows the priest" testid="folio-edges"/>
      <ChipList label="Obstacles" hint="Recurring −1 burdens"
                items={f.obstacles || []} setItems={(arr) => setF({ obstacles: arr })}
                placeholder="e.g. afraid of fire; owes a favour" testid="folio-obstacles"/>

      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="label-ref">Goals</div>
            <div className="text-[10px] text-mist/70 italic">Short-term, long-term, and secret. Three of each is plenty.</div>
          </div>
          <button onClick={() => addItem("goals", { title: "", kind: "short", note: "" })}
                  className="btn btn-ghost text-xs" data-testid="folio-add-goal"><Plus className="w-3 h-3"/> Goal</button>
        </div>
        {(f.goals || []).map((g, i) => (
          <div key={i} className="border border-gold/15 rounded-sm p-2 mb-2 grid md:grid-cols-[1fr_120px_auto] gap-2 items-center">
            <input className="input" placeholder="Goal" value={g.title || ""}
                   onChange={(e) => updateItem("goals", i, { title: e.target.value })}/>
            <select className="select" value={g.kind || "short"}
                    onChange={(e) => updateItem("goals", i, { kind: e.target.value })}>
              <option value="short">Short-term</option>
              <option value="long">Long-term</option>
              <option value="secret">Secret</option>
            </select>
            <button onClick={() => removeItem("goals", i)} className="text-ember/70"><X className="w-4 h-4"/></button>
            <textarea className="input md:col-span-3" placeholder="Note (why? at what cost?)" value={g.note || ""}
                      onChange={(e) => updateItem("goals", i, { note: e.target.value })}/>
          </div>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="label-ref">Family & Bonds</div>
          <button onClick={() => addItem("family", { name: "", relation: "", note: "" })}
                  className="btn btn-ghost text-xs" data-testid="folio-add-family"><Plus className="w-3 h-3"/> Person</button>
        </div>
        {(f.family || []).map((p, i) => (
          <div key={i} className="border border-gold/15 rounded-sm p-2 mb-2 grid md:grid-cols-[1fr_1fr_auto] gap-2">
            <input className="input" placeholder="Name" value={p.name || ""}
                   onChange={(e) => updateItem("family", i, { name: e.target.value })}/>
            <input className="input" placeholder="Relation" value={p.relation || ""}
                   onChange={(e) => updateItem("family", i, { relation: e.target.value })}/>
            <button onClick={() => removeItem("family", i)} className="text-ember/70"><X className="w-4 h-4"/></button>
            <input className="input md:col-span-3" placeholder="Note (alive? estranged? what do they think of the PC?)"
                   value={p.note || ""} onChange={(e) => updateItem("family", i, { note: e.target.value })}/>
          </div>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="label-ref">History of Events</div>
          <button onClick={() => addItem("history_events", { date: "", title: "", note: "" })}
                  className="btn btn-ghost text-xs" data-testid="folio-add-history"><Plus className="w-3 h-3"/> Event</button>
        </div>
        {(f.history_events || []).map((h, i) => (
          <div key={i} className="border border-gold/15 rounded-sm p-2 mb-2 grid md:grid-cols-[120px_1fr_auto] gap-2">
            <input className="input" placeholder="Date / age" value={h.date || ""}
                   onChange={(e) => updateItem("history_events", i, { date: e.target.value })}/>
            <input className="input" placeholder="What happened" value={h.title || ""}
                   onChange={(e) => updateItem("history_events", i, { title: e.target.value })}/>
            <button onClick={() => removeItem("history_events", i)} className="text-ember/70"><X className="w-4 h-4"/></button>
          </div>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="label-ref">Journal</div>
          <button onClick={() => addItem("journal", { date: new Date().toISOString().slice(0, 10), entry: "" })}
                  className="btn btn-ghost text-xs" data-testid="folio-add-journal"><Plus className="w-3 h-3"/> Entry</button>
        </div>
        {(f.journal || []).map((j, i) => (
          <div key={i} className="border border-gold/15 rounded-sm p-2 mb-2">
            <div className="flex items-center gap-2 mb-1">
              <input className="input w-40" placeholder="Date" value={j.date || ""}
                     onChange={(e) => updateItem("journal", i, { date: e.target.value })}/>
              <button onClick={() => removeItem("journal", i)} className="text-ember/70 ml-auto"><X className="w-4 h-4"/></button>
            </div>
            <textarea className="input" placeholder="Today the table…"
                      value={j.entry || ""} onChange={(e) => updateItem("journal", i, { entry: e.target.value })}/>
          </div>
        ))}
      </div>
    </div>
  );
}

function FolioInput({ label, value, onChange, testid }) {
  return (
    <div>
      <label className="label-ref block mb-1">{label}</label>
      <input className="input" value={value || ""} onChange={(e) => onChange(e.target.value)} data-testid={testid}/>
    </div>
  );
}
function FolioTextarea({ label, value, onChange, prompt, testid }) {
  return (
    <div>
      <label className="label-ref block mb-1">{label}</label>
      <textarea className="input" value={value || ""} onChange={(e) => onChange(e.target.value)} data-testid={testid}/>
      {prompt && <div className="text-[10px] text-mist/70 italic mt-1">{prompt}</div>}
    </div>
  );
}
function ChipList({ label, hint, items, setItems, placeholder, testid }) {
  const [v, setV] = useState("");
  const add = () => { const t = v.trim(); if (!t) return; setItems([...(items || []), t]); setV(""); };
  return (
    <div>
      <div className="label-ref mb-1">{label}</div>
      {hint && <div className="text-[10px] text-mist/70 italic mb-1">{hint}</div>}
      <div className="flex flex-wrap gap-1 mb-2">
        {(items || []).map((it, i) => (
          <span key={i} className="tag">{it}
            <button className="ml-1" onClick={() => setItems(items.filter((_, j) => j !== i))}>
              <X className="w-3 h-3 inline"/>
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="input" placeholder={placeholder} value={v}
               onChange={(e) => setV(e.target.value)}
               onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
               data-testid={testid}/>
        <button onClick={add} type="button" className="btn btn-ghost"><Plus className="w-3 h-3"/></button>
      </div>
    </div>
  );
}

function ListSection({ title, items, options, onAdd, renderRow, kind, testIdPrefix }) {
  const [show, setShow] = useState(false);
  const [q, setQ] = useState("");
  const filtered = options.filter((o) => o.name.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="card-mystic p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="h-arcane text-sm">{title}</h3>
        <button onClick={() => setShow(!show)} className="btn btn-ghost text-xs" data-testid={`add-${testIdPrefix}-btn`}>
          <Plus className="w-3 h-3"/> Add
        </button>
      </div>
      {items.length === 0 && <div className="text-mist italic font-body text-xs">None selected.</div>}
      <div className="space-y-2">{items.map((it, i) => renderRow(it, i))}</div>

      {show && (
        <div className="mt-4 border-t border-gold/10 pt-4">
          <input className="input mb-3" placeholder={`Search ${kind}s…`} value={q} onChange={(e) => setQ(e.target.value)}
                 data-testid={`search-${testIdPrefix}`}/>
          <div className="max-h-72 overflow-auto scroll-stylish grid sm:grid-cols-2 gap-2">
            {filtered.map((o, i) => (
              <button key={i} onClick={() => { onAdd(o); setShow(false); setQ(""); }}
                      className="text-left p-2 border border-gold/10 rounded-sm hover:border-gold/40 hover:bg-gold/5"
                      data-testid={`opt-${testIdPrefix}-${o.name.replace(/\s+/g,'-')}`}>
                <div className="flex items-center justify-between gap-2">
                  <div className="text-sm text-parchment font-ui">{o.name}</div>
                  <span className="text-[10px] text-gold/70 font-ui">
                    {kind === "defect" ? `${o.points_per_rank || -1}/rank` : `${o.cost_per_level ?? 0} pts/lvl`}
                  </span>
                </div>
                <div className="text-[10px] text-mist font-ui flex items-center gap-1 mt-0.5">
                  <BookOpen className="w-3 h-3"/> {o.page ? `p.${o.page} BESM 4E` : (o.page_ref || "—")}
                  {o._group && <span className="ml-2 tag">{o._group}</span>}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AttributeRow({ idx, a, ref, onUpdate, onRemove }) {
  const [openCust, setOpenCust] = useState(false);
  const toggle = (kind, name) => {
    const list = a[kind].includes(name) ? a[kind].filter((x) => x !== name) : [...a[kind], name];
    onUpdate({ ...a, [kind]: list });
  };
  const cost = (a.cost_per_level * a.level) + (a.enhancements.length - a.limiters.length) * a.level;
  return (
    <div className="border border-gold/15 rounded-sm p-3" data-testid={`attr-row-${idx}`}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="text-sm text-parchment font-ui">{a.name}</div>
          <div className="text-[10px] font-ui text-mist uppercase tracking-widest flex items-center gap-1">
            <BookOpen className="w-3 h-3"/> {a.page ? `p.${a.page} BESM 4E` : "Custom"}
            {a.note && <span className="ml-1 text-gold/70">({a.note})</span>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="label-ref">LVL</label>
          <input type="number" min={1} max={10} className="input w-20 text-center"
                 value={a.level} onChange={(e) => onUpdate({ ...a, level: +e.target.value })}
                 data-testid={`attr-level-${idx}`}/>
          <span className="text-gold font-display">{cost} pts</span>
          <button onClick={onRemove} className="text-ember/70 hover:text-ember" data-testid={`attr-remove-${idx}`}><X className="w-4 h-4"/></button>
        </div>
      </div>
      <div className="mt-2 flex gap-2 text-[10px]">
        <button className="btn btn-ghost text-[10px] py-1" onClick={() => setOpenCust(!openCust)}
                data-testid={`attr-cust-${idx}`}>
          {openCust ? "Hide" : "Customise"} ({a.enhancements.length}↑ / {a.limiters.length}↓)
        </button>
      </div>
      {openCust && (
        <div className="mt-2 grid md:grid-cols-2 gap-3">
          <div>
            <div className="label-ref mb-1">Enhancements (+1/lvl each) · p.145</div>
            <div className="flex flex-wrap gap-1">
              {ref.enhancements.map((e) => (
                <button key={e.name} onClick={() => toggle("enhancements", e.name)}
                        className={`tag ${a.enhancements.includes(e.name) ? "border-gold text-gold-bright bg-gold/15" : ""}`}>
                  {e.name}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="label-ref mb-1">Limiters (-1/lvl each) · p.148</div>
            <div className="flex flex-wrap gap-1">
              {ref.limiters.map((l) => (
                <button key={l.name} onClick={() => toggle("limiters", l.name)}
                        className={`tag ${a.limiters.includes(l.name) ? "border-ember text-ember bg-ember/15" : ""}`}>
                  {l.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DefectRow({ idx, d, onUpdate, onRemove }) {
  const pts = d.points_per_rank * d.rank;
  return (
    <div className="border border-gold/15 rounded-sm p-3 flex items-center justify-between gap-2 flex-wrap"
         data-testid={`defect-row-${idx}`}>
      <div>
        <div className="text-sm text-parchment font-ui">{d.name}</div>
        <div className="text-[10px] font-ui text-mist uppercase tracking-widest flex items-center gap-1">
          <BookOpen className="w-3 h-3"/> {d.page ? `p.${d.page} BESM 4E` : "Custom"} · {d.category}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <label className="label-ref">RANK</label>
        <input type="number" min={1} max={3} className="input w-20 text-center"
               value={d.rank} onChange={(e) => onUpdate({ ...d, rank: +e.target.value })}
               data-testid={`defect-rank-${idx}`}/>
        <span className="text-ember font-display">{pts} pts</span>
        <button onClick={onRemove} className="text-ember/70 hover:text-ember"><X className="w-4 h-4"/></button>
      </div>
    </div>
  );
}

function SkillRow({ idx, s, onUpdate, onRemove }) {
  return (
    <div className="border border-gold/15 rounded-sm p-3 flex items-center justify-between gap-2 flex-wrap"
         data-testid={`skill-row-${idx}`}>
      <div>
        <div className="text-sm text-parchment font-ui">{s.group}</div>
        <div className="text-[10px] font-ui text-mist uppercase tracking-widest flex items-center gap-1">
          <BookOpen className="w-3 h-3"/> {s.page ? `p.${s.page} BESM 4E` : "Custom"} · {s.cost_per_level} pts/lvl
        </div>
      </div>
      <div className="flex items-center gap-2">
        <label className="label-ref">LVL</label>
        <input type="number" min={1} max={6} className="input w-20 text-center"
               value={s.level} onChange={(e) => onUpdate({ ...s, level: +e.target.value })}
               data-testid={`skill-level-${idx}`}/>
        <span className="text-gold font-display">{s.cost_per_level * s.level} pts</span>
        <button onClick={onRemove} className="text-ember/70 hover:text-ember"><X className="w-4 h-4"/></button>
      </div>
    </div>
  );
}
