import React, { createContext, useContext, useState, useCallback } from "react";
import GuidedTour from "./GuidedTour";
import { TOURS, reifyTour } from "./tours";

/**
 * TourProvider — app-wide mount point for the GuidedTour overlay.
 *
 * The tour must persist across route changes (each step often navigates
 * to a different page), so the overlay can't live inside any single route
 * component. This provider sits just inside `Shell`, above `<Outlet/>`,
 * and renders the live tour into a portal. Any descendant component
 * can call `useTour().launch(tourId, ctx)` to fire one off.
 *
 *   const { launch, stop, active } = useTour();
 *   launch("director-console", { cid: "abc123" });
 */
const TourContext = createContext(null);

export function TourProvider({ children }) {
  const [tour, setTour] = useState(null);

  const launch = useCallback((tourId, ctx = {}) => {
    const def = TOURS[tourId];
    if (!def) {
      console.warn(`[TourProvider] Unknown tourId: ${tourId}`);
      return;
    }
    setTour(reifyTour(def, ctx));
  }, []);

  const stop = useCallback(() => setTour(null), []);

  return (
    <TourContext.Provider value={{ launch, stop, active: !!tour, title: tour?.title || "" }}>
      {children}
      {tour && <GuidedTour tour={tour} onClose={stop} />}
    </TourContext.Provider>
  );
}

export function useTour() {
  const ctx = useContext(TourContext);
  if (!ctx) {
    // Safe no-op fallback so unmounted/isolated components don't crash.
    return { launch: () => {}, stop: () => {}, active: false, title: "" };
  }
  return ctx;
}
