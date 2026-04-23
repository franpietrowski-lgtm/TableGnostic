import React from "react";
import { Info } from "lucide-react";

/**
 * Tiny hover tooltip. Uses native title as a11y fallback + a styled popover on hover/focus.
 * Usage: <Tip text="..."> <label>X</label> </Tip>
 * Or just:  <TipDot text="..."/>  next to a label.
 */
export function Tip({ text, children, className = "" }) {
  return (
    <span className={`relative inline-flex items-center group ${className}`} title={text}>
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute z-40 left-1/2 -translate-x-1/2 top-[calc(100%+6px)]
                   w-72 p-3 rounded-sm border border-gold/40 bg-void text-[12px] text-mist font-body leading-relaxed
                   opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-200
                   shadow-[0_8px_32px_-12px_rgba(212,175,55,0.25)]"
      >
        <span className="block text-gold-bright font-ui uppercase tracking-widest text-[9px] mb-1">Guidance</span>
        {text}
      </span>
    </span>
  );
}

export function TipDot({ text, className = "" }) {
  return (
    <Tip text={text} className={className}>
      <Info className="w-3 h-3 text-gold/50 hover:text-gold-bright cursor-help" tabIndex={0} />
    </Tip>
  );
}

export default Tip;
