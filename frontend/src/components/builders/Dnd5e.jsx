/**
 * D&D 5E character builder. Uses the SRD 5.1 (CC-BY) reference shape.
 * Persists into `folio.dnd_state` so the same /api/characters route
 * carries the system data alongside the BESM-shape `stats` defaults.
 *
 * When called by the Anime 5E hybrid loader, `hybridSupplement` is the
 * Anime 5E reference object — that turns on the Tri-Stat point-buy
 * supplement card at the bottom of the sheet.
 */
import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, formatApiErrorDetail } from "../../lib/api";
import { Save } from "lucide-react";
import {
  ABILITIES_5E, ABBR_5E, modOf, profByLevel,
  Stat,
} from "./shared";
import ReferencePicker from "./ReferencePicker";
import { Anime5eHybridSupplement } from "./Anime5eHybridSupplement";

export const empty5e = (cid) => ({
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
  const [refRows, setRefRows] = useState([]);
  // V6.25 — pull campaign custom_attributes so homebrew Race / Class /
  // Size entries surface in their respective dropdowns.
  const [customs, setCustoms] = useState([]);

  useEffect(() => {
    if (charId) {
      api.get(`/characters/${charId}`).then((r) => {
        const existing = r.data;
        // V6.20 — merge any missing dnd_state array fields so the editor
        // can call .includes()/.map() without crashing on
        // converter-created characters that skipped these initially.
        const baseDnd = empty5e(campaign?.id).folio.dnd_state;
        const cur = existing.folio?.dnd_state || {};
        existing.folio = {
          ...(existing.folio || {}),
          dnd_state: {
            ...baseDnd,
            ...cur,
            ability_scores: { ...baseDnd.ability_scores,
                                ...(cur.ability_scores || {}) },
            saving_throw_profs: cur.saving_throw_profs || baseDnd.saving_throw_profs,
            skill_profs: cur.skill_profs || baseDnd.skill_profs,
            inventory: cur.inventory || baseDnd.inventory,
            spells_known: cur.spells_known || baseDnd.spells_known,
          },
        };
        setCh(existing);
      });
    } else {
      setCh(empty5e(campaign?.id));
    }
  }, [charId, campaign?.id]);

  // Load campaign-reference rows so the Background dropdown can include
  // GM-authored entries alongside the SRD set.
  useEffect(() => {
    if (!campaign?.id) return;
    api.get(`/campaigns/${campaign.id}/reference?kind=defect`)
      .then((r) => setRefRows(Array.isArray(r.data) ? r.data : []))
      .catch(() => {});
    // V6.25 — homebrew race / class / size / stat (BESM Extras-style).
    api.get(`/campaigns/${campaign.id}/custom`)
      .then((r) => setCustoms(Array.isArray(r.data) ? r.data : []))
      .catch(() => setCustoms([]));
  }, [campaign?.id]);

  const homebrewRaces = customs.filter((c) => c.kind === "race");
  const homebrewClasses = customs.filter((c) => c.kind === "class");

  if (!ch || !ref_) return <div className="p-10 text-mist">Summoning the forge…</div>;
  const s = ch.folio.dnd_state;
  const setS = (patch) => setCh({ ...ch,
    folio: { ...ch.folio, dnd_state: { ...s, ...patch } } });
  const setScore = (a, v) => setS({ ability_scores: { ...s.ability_scores, [a]: Math.max(1, +v) } });
  const toggle = (k, v) => {
    const list = Array.isArray(s[k]) ? s[k] : [];
    setS({ [k]: list.includes(v) ? list.filter((x) => x !== v) : [...list, v] });
  };
  // V6.20 — defensive accessors so .includes()/.map() can never crash on
  // a sparse / migrated dnd_state.
  const savingProfs = Array.isArray(s.saving_throw_profs) ? s.saving_throw_profs : [];
  const skillProfs = Array.isArray(s.skill_profs) ? s.skill_profs : [];

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
      // V6.23 — DP overspend gate (Anime 5E hybrid only). The
      // canonical RAW budget is 80 + (level − 1); the spend bucket is
      // ability scores + race + BESM point-buys. If the player is over
      // budget AND the GM hasn't toggled an override, block the save.
      // Race + ability cost lookup is done locally; the BESM layer
      // already lives on `folio.anime5e_state.point_buys`.
      if (hybridSupplement) {
        const aState = ch.folio?.anime5e_state || {};
        const lvl = Math.max(1, +s.level || 1);
        const budget = +(aState.point_budget || 0) || (80 + (lvl - 1));
        const abilityCost = Object.values(s.ability_scores || {})
          .reduce((sum, v) => sum + (+v || 10), 0);
        const raceObj = (hybridSupplement.heritages
                         || hybridSupplement.races
                         || ref_.races || []).find((r) =>
          (r.name || r.key || "").toLowerCase() === (s.race || "").toLowerCase());
        const raceCost = +(raceObj?.dp_cost || 0) || 0;
        const buyTotal = (aState.point_buys || []).reduce(
          (sum, b) => sum + (+b.cost_per_level || 0) * (+b.level || 1), 0);
        const totalSpent = abilityCost + raceCost + buyTotal;
        const overBy = totalSpent - budget;
        const gmOverride = !!aState.gm_dp_override;
        if (overBy > 0 && !gmOverride) {
          setErr(
            `Over Anime 5E DP budget by ${overBy} — abilities ${abilityCost}` +
            ` + race ${raceCost} + point-buys ${buyTotal} = ${totalSpent}` +
            ` (budget ${budget}). Lower a stat / drop a point-buy / pick` +
            ` a cheaper race, or have the GM tick the override checkbox` +
            ` on the BESM Point-Buy Layer card below.`,
          );
          return;
        }
      }
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
            <optgroup label="SRD 5.1 (CC-BY)">
              {ref_.classes.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
            </optgroup>
            {homebrewClasses.length > 0 && (
              <optgroup label="Campaign Homebrew">
                {homebrewClasses.map((c) => (
                  <option key={c.id} value={c.name} data-testid={`dnd-class-homebrew-${c.id}`}>
                    {c.name}
                  </option>
                ))}
              </optgroup>
            )}
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
            <optgroup label="SRD 5.1 (CC-BY)">
              {ref_.races.map((r) => <option key={r.name} value={r.name}>{r.name}</option>)}
            </optgroup>
            {homebrewRaces.length > 0 && (
              <optgroup label="Campaign Homebrew">
                {homebrewRaces.map((r) => (
                  <option key={r.id} value={r.name} data-testid={`dnd-race-homebrew-${r.id}`}>
                    {r.name}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>
        <div>
          <label className="label-ref">Background</label>
          <select className="select" value={s.background}
                  onChange={(e) => setS({ background: e.target.value })}
                  data-testid="dnd-background">
            <option value="">— pick a background —</option>
            <optgroup label="SRD 5.1 (CC-BY)">
              {(ref_.backgrounds || []).map((b) => (
                <option key={b.name} value={b.name}>{b.name}</option>
              ))}
            </optgroup>
            {refRows.filter((r) => r.kind === "defect").length > 0 && (
              <optgroup label="Campaign Reference">
                {refRows.filter((r) => r.kind === "defect").map((r) => (
                  <option key={r.id} value={r.name}>{r.name}</option>
                ))}
              </optgroup>
            )}
          </select>
        </div>
      </div>

      {/* Background detail card — proficiencies + feature blurb */}
      {s.background && (() => {
        const bg = (ref_.backgrounds || []).find((x) => x.name === s.background);
        if (!bg) return null;
        return (
          <div className="card-mystic p-4 mt-2 text-[12px] text-parchment/85 leading-snug"
               data-testid="dnd-background-card">
            <div className="label-ref mb-1">Background · {bg.name}</div>
            Skills: {bg.skills.join(", ")}
            {bg.tools?.length ? ` · Tools: ${bg.tools.join(", ")}` : ""}
            {bg.languages && bg.languages !== "—" ? ` · Languages: ${bg.languages}` : ""}
            <div className="mt-1 italic text-mist/80">Feature: {bg.feature}</div>
          </div>
        );
      })()}

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
      {!race && homebrewRaces.find((r) => r.name === s.race) && (() => {
        const hb = homebrewRaces.find((r) => r.name === s.race);
        return (
          <div className="card-mystic p-4 mt-2 text-[12px] text-parchment/85 leading-snug"
               data-testid="dnd-race-homebrew-card">
            <div className="label-ref mb-1 flex items-center gap-1.5">
              <span className="text-gold-bright">Homebrew Race</span>
              <span className="text-mist/60 normal-case tracking-normal">· {hb.category || "custom"}</span>
            </div>
            {hb.description_note || <span className="italic text-mist">No description provided by GM.</span>}
          </div>
        );
      })()}
      {!cls && homebrewClasses.find((c) => c.name === s.class) && (() => {
        const hb = homebrewClasses.find((c) => c.name === s.class);
        return (
          <div className="card-mystic p-4 mt-2 text-[12px] text-parchment/85 leading-snug"
               data-testid="dnd-class-homebrew-card">
            <div className="label-ref mb-1 flex items-center gap-1.5">
              <span className="text-gold-bright">Homebrew Class</span>
              <span className="text-mist/60 normal-case tracking-normal">· {hb.category || "custom"}</span>
            </div>
            {hb.description_note || <span className="italic text-mist">No description provided by GM.</span>}
          </div>
        );
      })()}

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
                  Save: {ABBR_5E[a]} {m >= 0 ? "+" : ""}{m}{savingProfs.includes(a) ? ` +${prof} prof` : ""}
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
                    className={`tag ${savingProfs.includes(a) ? "border-gold text-gold-bright bg-gold/15" : ""}`}
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
                    className={`tag ${skillProfs.includes(sk.name) ? "border-gold text-gold-bright bg-gold/15" : ""}`}
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

      {/* V6.21 — Reference-backed dropdown selectors replace free-text
          FreeList. Inventory pulls from SRD 5.1 weapons + armor + items
          catalog; spells filter by max slot level the character can cast. */}
      <ReferencePicker title="Inventory / Equipment"
                       placeholder="Longsword, Chain Mail, Healer's Kit…"
                       values={s.inventory} onChange={(v) => setS({ inventory: v })}
                       testidPrefix="dnd-inv"
                       systemId={hybridSupplement ? "anime-5e" : "dnd-5e"}
                       kinds={["weapons", "armor", "items"]}
                       campaignId={ch.campaign_id}/>
      {cls?.casting !== "none" && (
        <ReferencePicker title="Spells Known / Prepared"
                         placeholder="Fire Bolt, Magic Missile, Cure Wounds…"
                         values={s.spells_known} onChange={(v) => setS({ spells_known: v })}
                         testidPrefix="dnd-spell"
                         systemId={hybridSupplement ? "anime-5e" : "dnd-5e"}
                         kinds={["spells"]}
                         campaignId={ch.campaign_id}
                         maxSpellLevel={Math.min(9, Math.ceil((s.level || 1) / 2))}/>
      )}

      {/* Anime 5E hybrid — Tri-Stat point-buy supplement on top of d20 sheet */}
      {hybridSupplement && (
        <Anime5eHybridSupplement ch={ch} setCh={setCh}
                                  ref_={hybridSupplement}
                                  isGm={!!campaign?.is_gm}/>
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
