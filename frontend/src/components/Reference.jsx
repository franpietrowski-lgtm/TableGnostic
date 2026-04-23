import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { BookOpen, Search } from "lucide-react";

export default function Reference() {
  const [ref, setRef] = useState(null);
  const [q, setQ] = useState("");
  const [tab, setTab] = useState("attributes");

  useEffect(() => { api.get("/besm/reference").then((r) => setRef(r.data)); }, []);
  const ql = q.toLowerCase();
  const lists = useMemo(() => {
    if (!ref) return {};
    const f = (arr) => arr.filter((a) => (a.name || a.difficulty || "").toLowerCase().includes(ql));
    return {
      attributes: f(ref.attributes),
      defects: f(ref.defects),
      skill_groups: f(ref.skill_groups),
      enhancements: f(ref.enhancements),
      limiters: f(ref.limiters),
      power_levels: f(ref.power_levels),
      target_numbers: f(ref.target_numbers || []),
      extras_rules: f(ref.extras_rules || []),
    };
  }, [ref, ql]);

  if (!ref) return <div className="p-10 text-mist">Opening the tome…</div>;

  const tabs = [
    ["attributes", "Attributes"], ["defects", "Defects"], ["skill_groups", "Skill Groups"],
    ["enhancements", "Enhancements"], ["limiters", "Limiters"],
    ["power_levels", "Power Levels"], ["target_numbers", "Target Numbers"],
    ["extras_rules", "BESM Extras"],
  ];

  return (
    <div className="px-8 md:px-12 py-10 max-w-5xl">
      <div className="label-ref mb-2">Sacred Tome</div>
      <h1 className="font-display text-4xl tracking-wide text-parchment">BESM 4E Reference</h1>
      <p className="text-mist mt-2 font-body">
        This application references the BESM 4E rulebook. Look up names, costs, and page numbers here
        — consult the official rulebook for the full text and rules.
      </p>

      <div className="mt-6 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 border border-gold/20 rounded-sm px-3 bg-void/60 w-80">
          <Search className="w-4 h-4 text-gold/60"/>
          <input className="bg-transparent outline-none py-2 text-sm text-parchment flex-1"
                 placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} data-testid="reference-search"/>
        </div>
        <div className="flex flex-wrap gap-1">
          {tabs.map(([v, l]) => (
            <button key={v} onClick={() => setTab(v)}
                    className={`btn btn-ghost text-xs ${tab === v ? "border-gold/60 text-gold-bright" : ""}`}
                    data-testid={`ref-tab-${v}`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="divider-sigil my-5"/>

      <div className="grid md:grid-cols-2 gap-3">
        {(lists[tab] || []).map((item, i) => (
          <div key={i} className="card-mystic p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-parchment font-ui">{item.name || item.difficulty}</div>
              <div className="text-[10px] font-ui uppercase tracking-widest text-gold/70 flex items-center gap-1">
                <BookOpen className="w-3 h-3"/> p.{item.page} {item.source?.book || (tab === "extras_rules" ? "BESM Extras" : "BESM 4E")}
              </div>
            </div>
            <div className="text-[11px] text-mist mt-1 font-ui">
              {tab === "attributes" && `${item.cost_per_level} pts/level${item.human_ok ? " · human" : ""}${item.note ? ` · ${item.note}` : ""}`}
              {tab === "defects" && `${item.points_per_rank} pts/rank · ${item.category}${item.note ? ` · ${item.note}` : ""}`}
              {tab === "skill_groups" && `${item.cost_per_level} pts/level`}
              {tab === "enhancements" && `+${item.cost_modifier} to effective level`}
              {tab === "limiters" && `${item.cost_modifier} to effective level`}
              {tab === "power_levels" && `${item.points} Character Points`}
              {tab === "target_numbers" && `TN ${item.tn}`}
              {tab === "extras_rules" && `${item.category}${item.summary ? ` — ${item.summary}` : ""}`}
            </div>
            {tab === "extras_rules" && (
              <div className="text-[10px] text-gold/60 mt-1 font-ui uppercase tracking-widest">BESM Extras</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
