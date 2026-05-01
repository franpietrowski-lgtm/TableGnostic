// Extracted from CampaignDetail.jsx in V6.10 refactor sprint.
// Player Primer + GM-side Primer editor with system-aware Forge Caps,
// House Rules, Cypher genre gating, etc. ~425 lines.
import React, { useState } from "react";
import { Save, Shield, X } from "lucide-react";
import { api, formatApiErrorDetail } from "../../lib/api";

function PrimerTab({ camp, onRefresh }) {
  const [primer, setPrimer] = useState(camp.player_primer || "");
  const [allowedA, setAllowedA] = useState((camp.allowed_attributes || []).join(", "));
  const [prohibA, setProhibA] = useState((camp.prohibited_attributes || []).join(", "));
  const [allowedD, setAllowedD] = useState((camp.allowed_defects || []).join(", "));
  const [prohibD, setProhibD] = useState((camp.prohibited_defects || []).join(", "));
  const [allowedS, setAllowedS] = useState((camp.allowed_skill_groups || []).join(", "));
  const [prohibS, setProhibS] = useState((camp.prohibited_skill_groups || []).join(", "));
  const [pointMin, setPointMin] = useState(camp.character_point_min || 0);
  const [pointMax, setPointMax] = useState(camp.character_point_max || 0);
  const [maxAttrRank, setMaxAttrRank] = useState(camp.max_per_attribute_rank || 0);
  // V3.5/V3.6 — Campaign Benchmarks
  const [genre, setGenre] = useState(camp.genre || "");
  const [timePeriod, setTimePeriod] = useState(camp.time_period || "");
  const [defaultSize, setDefaultSize] = useState(camp.default_character_size || "Medium");
  const [damageRating, setDamageRating] = useState(camp.damage_rating_baseline || 5);
  // V4.6 — per-licence setting tag (used by PDF export gate for Cypher).
  const [settingName, setSettingName] = useState(camp.setting_name || "");
  // V5.2 — Cypher genre-gate + system-aware primer caps.
  const [settingGenre, setSettingGenre] = useState(camp.setting_genre || "");
  const [primerLevelMin, setPrimerLevelMin] = useState(camp.primer_level_min || 1);
  const [primerTierSuggest, setPrimerTierSuggest] = useState(camp.primer_tier_suggest || 1);
  const [primerXpCap, setPrimerXpCap] = useState(camp.primer_xp_cap || 0);
  const [houseRules, setHouseRules] = useState(camp.house_rules || "");
  const [anime5eXpFormula, setAnime5eXpFormula] = useState(camp.anime5e_xp_formula || "flat");
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState("");
  const parse = (s) => s.split(",").map((x) => x.trim()).filter(Boolean);

  const save = async () => {
    setErr(""); setSaved(false);
    try {
      const payload = { ...camp,
        player_primer: primer,
        allowed_attributes: parse(allowedA),
        prohibited_attributes: parse(prohibA),
        allowed_defects: parse(allowedD),
        prohibited_defects: parse(prohibD),
        allowed_skill_groups: parse(allowedS),
        prohibited_skill_groups: parse(prohibS),
        character_point_min: parseInt(pointMin) || 0,
        character_point_max: parseInt(pointMax) || 0,
        max_per_attribute_rank: parseInt(maxAttrRank) || 0,
        genre, time_period: timePeriod,
        default_character_size: defaultSize,
        damage_rating_baseline: parseInt(damageRating) || 5,
        setting_name: settingName,
        setting_genre: settingGenre,
        primer_level_min: parseInt(primerLevelMin) || 1,
        primer_tier_suggest: parseInt(primerTierSuggest) || 1,
        primer_xp_cap: parseInt(primerXpCap) || 0,
        house_rules: houseRules,
        anime5e_xp_formula: anime5eXpFormula,
      };
      delete payload.is_gm; delete payload.members; delete payload.id;
      delete payload.gm_id; delete payload.gm_name; delete payload.member_ids;
      delete payload.invite_token; delete payload.created_at;
      await api.put(`/campaigns/${camp.id}`, payload);
      setSaved(true); setTimeout(() => setSaved(false), 1800);
      onRefresh();
    } catch (e) { setErr(e.response?.data?.detail || e.message); }
  };

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <div className="label-ref">Player Primer</div>
          <h3 className="h-arcane text-sm mt-1">What players need to know before they forge a character</h3>
        </div>
        {camp.is_gm && (
          <button onClick={save} className="btn btn-primary" data-testid="primer-save-btn">
            <Save className="w-4 h-4"/> {saved ? "Saved" : "Save"}
          </button>
        )}
      </div>
      <p className="text-xs text-mist font-body mt-2 italic">
        Visible to all seated players. Use it to establish the setting, the tone, what's allowed,
        what's off the table, and what the table expects from each character's arc.
      </p>
      <div className="divider-sigil my-4"/>

      {camp.is_gm ? (
        <textarea className="input min-h-[220px] font-body" placeholder="Welcome to the campaign. In this world…"
                  value={primer} onChange={(e) => setPrimer(e.target.value)} data-testid="primer-input"/>
      ) : (
        <>
        <div className="card-mystic p-5 whitespace-pre-wrap text-parchment/90 font-body leading-relaxed" data-testid="primer-readonly">
          {camp.player_primer || <span className="text-mist italic">The Game Master hasn't written a primer yet.</span>}
        </div>
        {/* Player-facing system & house-rule summary — shown to non-GMs only.
            Surfaces forge caps + house rules + setting genre so a player
            can read the table contract before forging a character. */}
        <div className="grid sm:grid-cols-2 gap-3 mt-4" data-testid="primer-readonly-caps">
          {camp.setting_name && (
            <div className="card-mystic p-3 text-xs">
              <div className="label-ref">Setting</div>
              <div className="text-parchment mt-1">{camp.setting_name}</div>
            </div>
          )}
          {camp.system_id === "cypher" && camp.setting_genre && (
            <div className="card-mystic p-3 text-xs">
              <div className="label-ref">Cypher genre gate</div>
              <div className="text-parchment mt-1">{camp.setting_genre}
                <span className="text-mist text-[10px] ml-1">(Descriptors / Foci filtered to this)</span>
              </div>
            </div>
          )}
          {(camp.system_id === "dnd-5e" || camp.system_id === "anime-5e") && (camp.primer_level_min || 0) > 1 && (
            <div className="card-mystic p-3 text-xs">
              <div className="label-ref">Min starting level</div>
              <div className="text-parchment mt-1">Level {camp.primer_level_min}</div>
            </div>
          )}
          {camp.system_id === "cypher" && (camp.primer_tier_suggest || 0) > 0 && (
            <div className="card-mystic p-3 text-xs">
              <div className="label-ref">Suggested Tier</div>
              <div className="text-parchment mt-1">Tier {camp.primer_tier_suggest}</div>
            </div>
          )}
          {(camp.primer_xp_cap || 0) > 0 && (
            <div className="card-mystic p-3 text-xs">
              <div className="label-ref">Starting XP cap</div>
              <div className="text-parchment mt-1">{camp.primer_xp_cap} XP</div>
            </div>
          )}
          {(camp.prohibited_attributes?.length || camp.prohibited_defects?.length) ? (
            <div className="card-mystic p-3 text-xs sm:col-span-2"
                 data-testid="primer-readonly-prohibited">
              <div className="label-ref">Off the table</div>
              <div className="text-mist text-[11px] mt-1">
                {[...(camp.prohibited_attributes || []), ...(camp.prohibited_defects || [])].join(" · ") || "—"}
              </div>
            </div>
          ) : null}
          {camp.house_rules && (
            <div className="card-mystic p-3 text-xs sm:col-span-2"
                 data-testid="primer-readonly-house-rules">
              <div className="label-ref">House rules</div>
              <div className="text-parchment mt-1 whitespace-pre-wrap">{camp.house_rules}</div>
            </div>
          )}
        </div>
        </>
      )}

      {camp.is_gm && (
        <>
          <div className="divider-sigil my-6"/>
          <div className="label-ref mb-2 flex items-center gap-2">Campaign Benchmarks <Shield className="w-3 h-3"/></div>
          <p className="text-xs text-mist font-body mb-4 italic">
            Set the table's tone, era, and scale. These flow into the Character Builder
            (display badges + later: filtering), the Live Session (token sizing),
            and the Damage Rating engine (Damage Multiplier baseline).
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3" data-testid="primer-benchmarks">
            <div className="lg:col-span-2">
              <label className="label-ref block mb-1 flex items-center gap-2">
                Setting Name
                {camp.system_id === "cypher" && (
                  <span className="text-[9px] text-ember/80 font-ui uppercase tracking-widest"
                        title="The Cypher System Creator licence forbids exports for Numenera, The Strange, and No Thank You, Evil!. Naming your setting one of those will block PDF export.">
                    licence-gated
                  </span>
                )}
              </label>
              <input className="input" value={settingName}
                     onChange={(e) => setSettingName(e.target.value)}
                     placeholder={camp.system_id === "cypher"
                       ? "Godforsaken · The Heartwood · The Revel · custom Cypher setting…"
                       : "Aurea · Eberron-inspired · home-brew name…"}
                     data-testid="primer-setting-name"/>
              {camp.system_id === "cypher" && (
                <div className="text-[10px] text-mist/70 italic mt-1 leading-snug">
                  Creator-licensed (full content): Godforsaken, Gods of the Fall, Masters of the Night,
                  Predation, The Heartwood, The Revel, Unmasked. Compatibility-only: Claim the Sky,
                  First Responders, Stay Alive!, The Origin, The Stars Are Fire, We Are All Mad Here.
                  <span className="text-ember/80"> Forbidden (export will be blocked):
                  Numenera, The Strange, No Thank You Evil!.</span>
                </div>
              )}
            </div>
            <div>
              <label className="label-ref block mb-1">Genre</label>
              <input className="input" list="dl-genres" value={genre}
                     onChange={(e) => setGenre(e.target.value)}
                     placeholder="High Fantasy"
                     data-testid="primer-genre"/>
              <datalist id="dl-genres">
                {["High Fantasy","Low Fantasy","Sword & Sorcery","Cosmic Horror","Modern Horror","Cyberpunk","Steampunk","Space Opera","Hard Sci-Fi","Post-Apocalyptic","Mecha","Mythic Fantasy","Pulp Adventure","Noir","Anime","Slice of Life"].map((g) => <option key={g} value={g}/>)}
              </datalist>
            </div>
            <div>
              <label className="label-ref block mb-1">Time Period</label>
              <select className="select" value={timePeriod}
                      onChange={(e) => setTimePeriod(e.target.value)}
                      data-testid="primer-period">
                <option value="">— unset —</option>
                {["Stone Age","Bronze Age","Iron Age","Classical","Medieval","Renaissance","Industrial","Victorian","Modern","Near Future","Far Future","Post-Apocalyptic","Mixed / Anachronistic"].map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            {/* BESM-shaped sizing & damage. The Tri-Stat damage equation
                doesn't exist in D&D 5E (HP+AC) or Cypher (Pools+Effort);
                hide the controls for those systems to reduce confusion. */}
            {(camp.system_id === "besm-4e" || camp.system_id === "anime-5e") && (
              <>
                <div data-testid="primer-besm-size-block">
                  <label className="label-ref block mb-1">Default Character Size</label>
                  <select className="select" value={defaultSize}
                          onChange={(e) => setDefaultSize(e.target.value)}
                          data-testid="primer-size">
                    {[["Diminutive","Diminutive — sprite / fairy / pixie"],
                      ["Small","Small — halfling / goblin / housecat"],
                      ["Medium","Medium — standard humanoid (default)"],
                      ["Large","Large — ogre / horse / war-bear"],
                      ["Huge","Huge — giant / wagon / small mecha"],
                      ["Gargantuan","Gargantuan — dragon / mecha / siege engine"],
                      ["Massive","Massive — kaiju / capital ship / fortress"]].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                  <div className="text-[10px] text-mist/70 italic mt-1">
                    Per-entity Tri-Stat template; players can override on their sheet.
                  </div>
                </div>
                <div data-testid="primer-besm-dr-block">
                  <label className="label-ref block mb-1">Damage Rating (Tri-Stat)</label>
                  <input className="input" type="number" min={1} max={20}
                         value={damageRating}
                         onChange={(e) => setDamageRating(e.target.value)}
                         data-testid="primer-dr"/>
                  <div className="text-[10px] text-mist/70 italic mt-1">
                    Baseline 5 (BESM default) · grittier = lower · cinematic = higher
                  </div>
                </div>
              </>
            )}
          </div>

          {/* System-aware character-forge primer caps. Different fields show
              for different systems so the table sees only what's relevant.
              House rules block is universal. */}
          <div className="divider-sigil my-6"/>
          <div className="label-ref mb-2 flex items-center gap-2">Forge Caps · per-system <Shield className="w-3 h-3"/></div>
          <p className="text-xs text-mist font-body mb-4 italic">
            What the table guarantees about freshly-forged characters.
            Empty / 0 = no cap. <span className="text-mist/70">System-aware: D&D shows level, Cypher shows tier, all show XP cap.</span>
          </p>
          <div className="grid md:grid-cols-3 gap-3" data-testid="primer-system-caps">
            {(camp.system_id === "dnd-5e" || camp.system_id === "anime-5e") && (
              <div data-testid="primer-level-min-block">
                <label className="label-ref block mb-1">Min starting level</label>
                <input className="input" type="number" min={1} max={20} value={primerLevelMin}
                       onChange={(e) => setPrimerLevelMin(e.target.value)}
                       data-testid="primer-level-min"/>
                <div className="text-[10px] text-mist/70 italic mt-1">Gates the character builder's level slider.</div>
              </div>
            )}
            {camp.system_id === "cypher" && (
              <div data-testid="primer-tier-suggest-block">
                <label className="label-ref block mb-1">Suggested Tier</label>
                <input className="input" type="number" min={1} max={6} value={primerTierSuggest}
                       onChange={(e) => setPrimerTierSuggest(e.target.value)}
                       data-testid="primer-tier-suggest"/>
                <div className="text-[10px] text-mist/70 italic mt-1">Cypher Tier (1-6) the table starts at.</div>
              </div>
            )}
            <div data-testid="primer-xp-cap-block">
              <label className="label-ref block mb-1">Starting XP cap</label>
              <input className="input" type="number" min={0} value={primerXpCap}
                     onChange={(e) => setPrimerXpCap(e.target.value)}
                     data-testid="primer-xp-cap"/>
              <div className="text-[10px] text-mist/70 italic mt-1">0 = no cap. Hard ceiling on XP carried at character creation.</div>
            </div>
            {camp.system_id === "cypher" && (
              <div data-testid="primer-genre-gate-block">
                <label className="label-ref block mb-1">Cypher genre gate</label>
                <select className="select" value={settingGenre}
                        onChange={(e) => setSettingGenre(e.target.value)}
                        data-testid="primer-cypher-genre">
                  <option value="">— no gate (all entries) —</option>
                  <option value="any">Genre-agnostic</option>
                  <option value="fantasy">Fantasy</option>
                  <option value="modern">Modern</option>
                  <option value="post">Post-Apocalypse</option>
                  <option value="scifi">Science-Fiction</option>
                  <option value="horror">Horror</option>
                  <option value="superhero">Superhero</option>
                  <option value="historical">Historical</option>
                </select>
                <div className="text-[10px] text-mist/70 italic mt-1">Filters the Cypher Descriptors / Foci picker by genre tag.</div>
              </div>
            )}
          </div>

          <div className="mt-4">
            <label className="label-ref block mb-1">House rules</label>
            <textarea className="input min-h-[70px] font-body" value={houseRules}
                      onChange={(e) => setHouseRules(e.target.value)}
                      placeholder="One-liners only — keep it scan-able. e.g. 'Crit on 19-20 with weapons; nat 1 on saves auto-fail.'"
                      data-testid="primer-house-rules"/>
            <div className="text-[10px] text-mist/70 italic mt-1">Surfaced on the player primer card so the table sees deviations from RAW. Also bypasses the app-internal character-approval rules gate so the GM can ratify house-rule-legal PCs.</div>
          </div>

          {/* V6.4 — Anime 5E XP→CP formula selector. Only relevant when
              players can use the optional BESM point-buy layer. */}
          {camp.system_id === "anime-5e" && (
            <div className="mt-4" data-testid="primer-anime5e-xp-formula">
              <label className="label-ref block mb-1">Anime 5E XP → CP formula</label>
              <div className="flex items-center gap-2 flex-wrap">
                <label className="inline-flex items-center gap-1 text-xs cursor-pointer"
                       title="CP = 50 + 8 × adventure level. Flat linear climb; good for gritty / narrow-power campaigns.">
                  <input type="radio" name="anime5e-xp-formula" value="flat"
                         checked={anime5eXpFormula === "flat"}
                         onChange={() => setAnime5eXpFormula("flat")}
                         data-testid="anime5e-xp-formula-flat"/>
                  <span>Flat <span className="text-mist">(50 + 8 × Lvl)</span></span>
                </label>
                <label className="inline-flex items-center gap-1 text-xs cursor-pointer"
                       title="CP = 40 + Lvl × {10 if Lvl ≤ 5 else 12 if Lvl ≤ 10 else 15}. Sharper mid-tier bump for power-fantasy campaigns.">
                  <input type="radio" name="anime5e-xp-formula" value="curve"
                         checked={anime5eXpFormula === "curve"}
                         onChange={() => setAnime5eXpFormula("curve")}
                         data-testid="anime5e-xp-formula-curve"/>
                  <span>Curve <span className="text-mist">(40 + Lvl × 10/12/15)</span></span>
                </label>
              </div>
              <div className="text-[10px] text-mist/70 italic mt-1">
                Sets the default CP budget the BESM-style point-buy layer gets when a player forges a new PC at the campaign's level floor.
              </div>
            </div>
          )}

          {/* Tri-Stat point-buy caps — irrelevant outside BESM / Anime 5E.
              D&D uses class+level; Cypher uses tier-driven pools. */}
          {(camp.system_id === "besm-4e" || camp.system_id === "anime-5e") && (<>
          <div className="divider-sigil my-6"/>
          <div className="label-ref mb-2 flex items-center gap-2">Character-Point Caps <Shield className="w-3 h-3"/></div>
          <p className="text-xs text-mist font-body mb-4 italic">
            Override the Power Level's default budget for this table. Useful for session-0 starts
            ("Heroic, but begin at 90") or floor enforcement ("nobody under 70"). Set to <b>0</b> to
            inherit the Power Level's default. <span className="text-mist/70">(BESM 4E / Anime 5E point-buy mode only.)</span>
          </p>
          <div className="grid md:grid-cols-3 gap-3" data-testid="primer-caps">
            <div>
              <label className="label-ref block mb-1">Min Character Points</label>
              <input className="input" type="number" min={0} value={pointMin}
                     onChange={(e) => setPointMin(e.target.value)}
                     data-testid="primer-cap-min"/>
              <div className="text-[10px] text-mist/70 italic mt-1">0 = no floor</div>
            </div>
            <div>
              <label className="label-ref block mb-1">Max Character Points</label>
              <input className="input" type="number" min={0} value={pointMax}
                     onChange={(e) => setPointMax(e.target.value)}
                     data-testid="primer-cap-max"/>
              <div className="text-[10px] text-mist/70 italic mt-1">0 = use Power Level default</div>
            </div>
            <div>
              <label className="label-ref block mb-1">Max Level per Attribute</label>
              <input className="input" type="number" min={0} value={maxAttrRank}
                     onChange={(e) => setMaxAttrRank(e.target.value)}
                     data-testid="primer-cap-attr-rank"/>
              <div className="text-[10px] text-mist/70 italic mt-1">0 = no per-Attribute cap</div>
            </div>
          </div>

          <div className="divider-sigil my-6"/>
          <div className="label-ref mb-2 flex items-center gap-2">Allow / Prohibit Lists <Shield className="w-3 h-3"/></div>
          <p className="text-xs text-mist font-body mb-4 italic">
            Leave <b>Allowed</b> empty to permit everything, or list names to restrict the character forge
            to only those entries. <b>Prohibited</b> items are always hidden from the player picker.
            <span className="text-mist/70"> (Tri-Stat Attribute / Defect / Skill Group names — BESM 4E / Anime 5E.)</span>
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <ListField label="Allowed Attributes" value={allowedA} setValue={setAllowedA} testid="allowed-attrs"
                       hint="e.g. Attack Mastery, Combat Technique, Flight, Heightened Senses"/>
            <ListField label="Prohibited Attributes" value={prohibA} setValue={setProhibA} testid="prohibited-attrs"
                       hint="e.g. Mind Control, Dynamic Powers"/>
            <ListField label="Allowed Defects" value={allowedD} setValue={setAllowedD} testid="allowed-defects"
                       hint="Narrow to flaws that fit the setting"/>
            <ListField label="Prohibited Defects" value={prohibD} setValue={setProhibD} testid="prohibited-defects"
                       hint="e.g. Awkward Size, Vulnerability"/>
            <ListField label="Allowed Skill Groups" value={allowedS} setValue={setAllowedS} testid="allowed-skills"/>
            <ListField label="Prohibited Skill Groups" value={prohibS} setValue={setProhibS} testid="prohibited-skills"/>
          </div>
          </>)}
          {(camp.system_id === "dnd-5e") && (
            <div className="card-mystic p-4 mt-6" data-testid="primer-dnd-note">
              <div className="label-ref mb-1">D&amp;D 5E note</div>
              <div className="text-xs text-parchment/85 leading-snug font-body">
                D&amp;D 5E uses class + level + slot mechanics, not point-buy. Use the
                <b> Atelier → Reference Tables</b> tab to authorise / restrict classes,
                races, spells, and items per campaign. The character forge will pull
                Campaign-Reference entries alongside the SRD core.
              </div>
            </div>
          )}
          {(camp.system_id === "cypher") && (
            <div className="card-mystic p-4 mt-6" data-testid="primer-cypher-note">
              <div className="label-ref mb-1">Cypher System note</div>
              <div className="text-xs text-parchment/85 leading-snug font-body">
                Cypher uses Tier (1-6) + Type/Focus/Descriptor + Pools (Might/Speed/
                Intellect) + Edge + Effort. There are no point-buy caps; players
                customise via Edge allocation and Skills trained at each Tier.
                Use the <b>Atelier → Reference Tables</b> tab to seed campaign-specific
                cyphers, artifacts, types, foci, and descriptors.
              </div>
            </div>
          )}
          {err && <div className="mt-3 text-ember text-sm">{err}</div>}
        </>
      )}
    </div>
  );
}

function ListField({ label, value, setValue, testid, hint }) {
  return (
    <div>
      <label className="label-ref block mb-1">{label}</label>
      <input className="input" placeholder="comma-separated names"
             value={value} onChange={(e) => setValue(e.target.value)} data-testid={testid}/>
      {hint && <div className="text-[10px] text-mist/70 italic mt-1">{hint}</div>}
    </div>
  );
}


export default PrimerTab;
