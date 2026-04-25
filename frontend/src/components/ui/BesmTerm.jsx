import React, { useState, useEffect, useRef } from "react";
import { BookOpen, X } from "lucide-react";

/**
 * Click-to-reference popover for BESM terms (Attributes, Defects, Skills, etc.)
 * Shows the official name, cost, source page, and any GM note.
 *
 * Props:
 *   name          : term name shown in the link
 *   cost          : "{n} pts/level" or "{n}/rank" string for tooltip
 *   page          : page number (BESM 4E or extras)
 *   book          : "BESM 4E" | "BESM Extras" | "Custom"
 *   note          : optional GM note (custom rules)
 *   category      : optional category tag (e.g. "Greater" for defects)
 *   children      : if provided, used as the trigger; otherwise the name is shown
 *
 * Click reveals an inline panel; Esc / X / outside-click dismiss.
 */
export default function BesmTerm({ name, cost, page, book = "BESM 4E", note, category, children }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  }, [open]);

  const ref_label = page ? `p.${page} ${book}` : (book || "Custom");

  return (
    <span className="relative inline-flex" ref={ref}>
      <button type="button" onClick={() => setOpen((o) => !o)}
              className="text-parchment hover:text-gold-bright underline decoration-gold/30 decoration-dotted underline-offset-4 transition-colors text-left"
              data-besm-term={name}>
        {children || name}
      </button>
      {open && (
        <div role="dialog"
             className="absolute z-50 left-0 top-[calc(100%+6px)] w-72 p-4 rounded-sm border border-gold/40 bg-void
                        shadow-[0_18px_60px_-30px_rgba(212,175,55,0.6)] animate-fade-in"
             onClick={(e) => e.stopPropagation()}>
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <div className="font-display tracking-wide text-parchment text-base">{name}</div>
              <div className="text-[10px] font-ui uppercase tracking-widest text-gold/70 flex items-center gap-1 mt-0.5">
                <BookOpen className="w-3 h-3"/> {ref_label}
                {category && <span className="ml-2">· {category}</span>}
              </div>
            </div>
            <button onClick={() => setOpen(false)} className="text-mist hover:text-parchment"><X className="w-3 h-3"/></button>
          </div>
          {cost && <div className="text-xs text-gold-bright font-ui">{cost}</div>}
          {note && <div className="text-xs text-mist italic mt-2 font-body">{note}</div>}
          <div className="mt-3 text-[10px] font-ui italic text-mist/70 leading-relaxed">
            For the full rules, consult the {book} rulebook
            {page ? `, page ${page}` : ""}. Table-Gnostic references rules — it does not reproduce them.
          </div>
        </div>
      )}
    </span>
  );
}
