import React, { useState, useEffect, useRef, useLayoutEffect } from "react";
import { createPortal } from "react-dom";
import { BookOpen, X } from "lucide-react";

/**
 * Click-to-reference popover for BESM terms (Attributes, Defects, Skills, etc.)
 *
 * Why a portal? When the trigger lives inside a card with its own stacking
 * context (z-index, transform, overflow:hidden), an `absolute` popover gets
 * clipped or rendered behind sibling cards. Rendering into <body> via
 * createPortal puts the popover at the document root with its own
 * viewport-relative coordinates so it is never occluded.
 */
export default function BesmTerm({ name, cost, page, book = "BESM 4E", note, category, children }) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0, placement: "below" });
  const triggerRef = useRef(null);
  const popoverRef = useRef(null);

  // Position the popover near the trigger, flipping above when room is tight.
  useLayoutEffect(() => {
    if (!open || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const W = 288;          // matches w-72
    const H = 180;          // estimated; flipping handles overflow
    const margin = 8;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let left = rect.left;
    if (left + W > vw - margin) left = Math.max(margin, vw - W - margin);
    let top = rect.bottom + 6;
    let placement = "below";
    if (top + H > vh - margin) {
      top = Math.max(margin, rect.top - H - 6);
      placement = "above";
    }
    setPos({ top, left, placement });
  }, [open]);

  // Outside-click + Escape dismiss
  useEffect(() => {
    if (!open) return;
    const onDoc = (e) => {
      if (popoverRef.current && popoverRef.current.contains(e.target)) return;
      if (triggerRef.current && triggerRef.current.contains(e.target)) return;
      setOpen(false);
    };
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    // Reposition on scroll/resize so the popover follows its anchor.
    const reflow = () => {
      if (!triggerRef.current) return;
      const r = triggerRef.current.getBoundingClientRect();
      setPos((p) => ({ ...p, top: r.bottom + 6, left: r.left }));
    };
    window.addEventListener("scroll", reflow, true);
    window.addEventListener("resize", reflow);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", reflow, true);
      window.removeEventListener("resize", reflow);
    };
  }, [open]);

  const ref_label = page ? `p.${page} ${book}` : (book || "Custom");

  const popover = open ? (
    <div ref={popoverRef}
         role="dialog"
         data-testid="besm-term-popover"
         style={{ position: "fixed", top: pos.top, left: pos.left, zIndex: 1000, width: 288 }}
         className="p-4 rounded-sm border border-gold/40 bg-void
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
  ) : null;

  return (
    <>
      <button type="button" ref={triggerRef} onClick={() => setOpen((o) => !o)}
              className="text-parchment hover:text-gold-bright underline decoration-gold/30 decoration-dotted underline-offset-4 transition-colors text-left"
              data-besm-term={name}>
        {children || name}
      </button>
      {typeof document !== "undefined" && popover && createPortal(popover, document.body)}
    </>
  );
}
