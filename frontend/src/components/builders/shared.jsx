/**
 * builders/shared — small UI atoms + math helpers shared by the
 * D&D 5E and Cypher (and Anime 5E hybrid) character builders.
 */
import React, { useState } from "react";
import { Plus, X } from "lucide-react";

export const ABILITIES_5E = ["Strength", "Dexterity", "Constitution",
                              "Intelligence", "Wisdom", "Charisma"];
export const ABBR_5E = { Strength: "STR", Dexterity: "DEX", Constitution: "CON",
                          Intelligence: "INT", Wisdom: "WIS", Charisma: "CHA" };

export function modOf(score) { return Math.floor(((score | 0) - 10) / 2); }
export function profByLevel(lvl) { return Math.max(2, 2 + Math.floor((Math.max(1, lvl) - 1) / 4)); }

export function Stat({ label, v }) {
  return (
    <div>
      <div className="text-[10px] font-ui uppercase tracking-widest text-mist">{label}</div>
      <div className="font-display text-xl text-gold-bright">{v}</div>
    </div>
  );
}

export function FreeList({ title, placeholder, values, onChange, testidPrefix }) {
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
