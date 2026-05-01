import React, { useEffect, useLayoutEffect, useRef, useState, useCallback } from "react";
import { createPortal } from "react-dom";
import { useNavigate, useLocation } from "react-router-dom";
import { ChevronLeft, ChevronRight, X, Compass } from "lucide-react";

/**
 * GuidedTour — V6.15 interactive UI walk-through overlay.
 *
 *   <GuidedTour tour={tourObj} onClose={…} />
 *
 * `tourObj` shape (from tours.js → reifyTour):
 *   {
 *     title: "Human-readable headline",
 *     steps: [
 *       { selector, title, body, route?, placement?, optional? },
 *       ...
 *     ]
 *   }
 *
 * Engine behaviour:
 *   • If `step.route` is set and differs from the current path, navigate
 *     there; wait up to 4s for `step.selector` to appear in the DOM.
 *   • Draw a 4-rect cut-out (top/right/bottom/left) of the viewport to dim
 *     everything EXCEPT the target's bounding box → creates the "spotlight".
 *   • Anchor a tooltip card next to the target (auto-placement with
 *     viewport awareness).
 *   • Prev / Next / Skip controls. ESC closes. Clicking the dim area does
 *     NOT advance (prevents accidental close on scroll).
 *   • On window resize / scroll, reposition in real time via
 *     ResizeObserver + requestAnimationFrame.
 *
 * Optional steps (`optional: true`) are skipped silently after a 1.2s grace
 * period if the selector never resolves — useful for role-gated controls.
 */
export default function GuidedTour({ tour, onClose }) {
  const nav = useNavigate();
  const loc = useLocation();
  const [idx, setIdx] = useState(0);
  const [targetRect, setTargetRect] = useState(null);
  const [waiting, setWaiting] = useState(false);
  const mountedRef = useRef(true);
  const rafRef = useRef(null);

  useEffect(() => () => { mountedRef.current = false; }, []);

  const step = tour?.steps?.[idx] || null;
  const total = tour?.steps?.length || 0;

  // ── Navigate + find target ──
  const findTarget = useCallback(() => {
    if (!step) return null;
    // Support comma-joined fallback selectors ("sel-a, sel-b").
    const sels = step.selector.split(",").map((s) => s.trim()).filter(Boolean);
    for (const sel of sels) {
      const el = document.querySelector(sel);
      if (el) return el;
    }
    return null;
  }, [step]);

  useEffect(() => {
    if (!step) return;
    // Navigate if the step demands it.
    if (step.route && step.route !== loc.pathname + loc.search) {
      nav(step.route);
    }
    setTargetRect(null);
    setWaiting(true);
    // Poll for the target up to ~4s.
    let attempts = 0;
    const maxAttempts = step.optional ? 6 : 20;  // 300ms × N
    const tick = () => {
      if (!mountedRef.current) return;
      const el = findTarget();
      if (el) {
        try { el.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" }); } catch { /* noop */ }
        setTimeout(() => {
          if (!mountedRef.current) return;
          const r = el.getBoundingClientRect();
          setTargetRect({
            top: r.top, left: r.left, width: r.width, height: r.height, el,
          });
          setWaiting(false);
        }, 250);
        return;
      }
      attempts += 1;
      if (attempts >= maxAttempts) {
        setWaiting(false);
        if (step.optional) {
          // Silently skip optional unresolved steps.
          if (idx < total - 1) setIdx(idx + 1); else onClose?.();
        } else {
          // Non-optional: leave rect null → tooltip centres + warns.
          setTargetRect(null);
        }
        return;
      }
      setTimeout(tick, 300);
    };
    tick();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, tour, loc.pathname]);

  // ── Reposition on scroll / resize ──
  useLayoutEffect(() => {
    if (!targetRect?.el) return undefined;
    const update = () => {
      if (!mountedRef.current) return;
      const r = targetRect.el.getBoundingClientRect();
      setTargetRect((prev) => prev && { ...prev, top: r.top, left: r.left, width: r.width, height: r.height });
    };
    const onScroll = () => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(update);
    };
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onScroll);
    let ro;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(onScroll);
      try { ro.observe(targetRect.el); } catch { /* noop */ }
    }
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
      if (ro) ro.disconnect();
    };
  }, [targetRect?.el]);

  // ── ESC to close ──
  useEffect(() => {
    const h = (e) => { if (e.key === "Escape") onClose?.(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  if (!tour || !step) return null;

  const prev = () => { if (idx > 0) setIdx(idx - 1); };
  const next = () => { if (idx < total - 1) setIdx(idx + 1); else onClose?.(); };

  // ── Spotlight geometry ──
  const PAD = 8;
  const sx = targetRect ? Math.max(0, targetRect.left - PAD) : 0;
  const sy = targetRect ? Math.max(0, targetRect.top - PAD) : 0;
  const sw = targetRect ? targetRect.width + PAD * 2 : 0;
  const sh = targetRect ? targetRect.height + PAD * 2 : 0;

  // ── Tooltip positioning ──
  const TIP_W = 340;
  const TIP_H_EST = 180;
  const VW = typeof window !== "undefined" ? window.innerWidth : 1280;
  const VH = typeof window !== "undefined" ? window.innerHeight : 800;
  let tipX = VW / 2 - TIP_W / 2;
  let tipY = VH / 2 - TIP_H_EST / 2;
  if (targetRect) {
    const placement = resolvePlacement(step.placement, targetRect, VW, VH, TIP_W, TIP_H_EST);
    const gap = 16;
    if (placement === "bottom") {
      tipX = Math.min(VW - TIP_W - 16, Math.max(16, targetRect.left + targetRect.width / 2 - TIP_W / 2));
      tipY = Math.min(VH - TIP_H_EST - 16, targetRect.top + targetRect.height + gap);
    } else if (placement === "top") {
      tipX = Math.min(VW - TIP_W - 16, Math.max(16, targetRect.left + targetRect.width / 2 - TIP_W / 2));
      tipY = Math.max(16, targetRect.top - TIP_H_EST - gap);
    } else if (placement === "right") {
      tipX = Math.min(VW - TIP_W - 16, targetRect.left + targetRect.width + gap);
      tipY = Math.min(VH - TIP_H_EST - 16, Math.max(16, targetRect.top + targetRect.height / 2 - TIP_H_EST / 2));
    } else if (placement === "left") {
      tipX = Math.max(16, targetRect.left - TIP_W - gap);
      tipY = Math.min(VH - TIP_H_EST - 16, Math.max(16, targetRect.top + targetRect.height / 2 - TIP_H_EST / 2));
    }
  }

  const overlay = (
    <div className="fixed inset-0 z-[9000] pointer-events-none" data-testid="guided-tour-overlay">
      {/* Dim the 4 rectangles around the target → spotlight effect. */}
      {targetRect ? (
        <>
          <div className="absolute bg-void/75 backdrop-blur-[1px] pointer-events-auto"
               style={{ top: 0, left: 0, right: 0, height: sy }} />
          <div className="absolute bg-void/75 backdrop-blur-[1px] pointer-events-auto"
               style={{ top: sy, left: 0, width: sx, height: sh }} />
          <div className="absolute bg-void/75 backdrop-blur-[1px] pointer-events-auto"
               style={{ top: sy, left: sx + sw, right: 0, height: sh }} />
          <div className="absolute bg-void/75 backdrop-blur-[1px] pointer-events-auto"
               style={{ top: sy + sh, left: 0, right: 0, bottom: 0 }} />
          {/* Gold ring around the target. */}
          <div className="absolute rounded-sm pointer-events-none border-2 border-gold shadow-[0_0_20px_rgba(229,195,112,0.45)] animate-pulse"
               style={{ top: sy, left: sx, width: sw, height: sh, transition: "top 160ms, left 160ms, width 160ms, height 160ms" }}
               data-testid="guided-tour-spotlight" />
        </>
      ) : (
        <div className="absolute inset-0 bg-void/75 backdrop-blur-[1px] pointer-events-auto" />
      )}

      {/* Tooltip card. */}
      <div className="absolute card-mystic p-5 pointer-events-auto"
           style={{ top: tipY, left: tipX, width: TIP_W, zIndex: 9001,
                    boxShadow: "0 18px 48px rgba(0,0,0,.55)" }}
           data-testid="guided-tour-tooltip">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-[10px] tracking-widest uppercase text-gold-bright">
            <Compass className="w-3 h-3" />
            <span>Tour · {tour.title}</span>
          </div>
          <button onClick={onClose} className="text-mist hover:text-ember"
                  data-testid="guided-tour-close" title="Close tour (ESC)">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="font-display text-lg text-parchment leading-tight" data-testid="guided-tour-title">
          {step.title}
        </div>
        <div className="text-[12px] text-mist mt-2 leading-snug" data-testid="guided-tour-body">
          {waiting && !targetRect ? (
            <span className="italic">Finding the spot…</span>
          ) : !targetRect ? (
            <>
              <span className="text-ember/80 italic">
                Couldn't find the target on this page.
              </span>
              <br />
              {step.body}
            </>
          ) : (
            step.body
          )}
        </div>
        <div className="mt-4 flex items-center justify-between">
          <div className="text-[10px] tracking-widest uppercase text-mist"
               data-testid="guided-tour-step-indicator">
            Step {idx + 1} / {total}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={prev} disabled={idx === 0}
                    className="btn btn-ghost text-[11px] disabled:opacity-40"
                    data-testid="guided-tour-prev">
              <ChevronLeft className="w-3 h-3" /> Prev
            </button>
            <button onClick={next} className="btn btn-primary text-[11px]"
                    data-testid="guided-tour-next">
              {idx === total - 1 ? "Finish" : <>Next <ChevronRight className="w-3 h-3" /></>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(overlay, document.body);
}

function resolvePlacement(requested, rect, VW, VH, tipW, tipH) {
  if (requested && requested !== "auto") return requested;
  const spaceBottom = VH - (rect.top + rect.height);
  const spaceTop = rect.top;
  const spaceRight = VW - (rect.left + rect.width);
  const spaceLeft = rect.left;
  // Prefer the side with most room.
  const candidates = [
    ["bottom", spaceBottom, tipH + 32],
    ["top",    spaceTop,    tipH + 32],
    ["right",  spaceRight,  tipW + 32],
    ["left",   spaceLeft,   tipW + 32],
  ].filter(([, space, need]) => space >= need);
  if (candidates.length === 0) return "bottom";
  candidates.sort((a, b) => b[1] - a[1]);
  return candidates[0][0];
}
