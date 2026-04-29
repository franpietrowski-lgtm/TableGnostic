// useMinDelay — hold a "still loading" gate true for at least `ms` after
// it first turns true, so the user can savour the thematic loading text
// (SUMMONING, Opening the table, Unrolling the map) instead of it
// flashing for 80 ms.
//
// Pattern:
//   const showLoading = useMinDelay(!ready, 5000);
//   if (showLoading) return <Loading />;
//
// On mount with `loading=true`, we set t0=now and keep the gate open
// until ms have elapsed AND the upstream loading flag flipped to false.
import { useEffect, useState } from "react";

export function useMinDelay(loading, ms = 5000) {
  const [stillShowing, setStillShowing] = useState(loading);
  const [startedAt, setStartedAt] = useState(loading ? Date.now() : null);

  useEffect(() => {
    if (loading) {
      if (startedAt === null) setStartedAt(Date.now());
      setStillShowing(true);
      return;
    }
    // Upstream says done — but enforce min display duration.
    const elapsed = startedAt == null ? ms : Date.now() - startedAt;
    const remaining = Math.max(0, ms - elapsed);
    const t = setTimeout(() => {
      setStillShowing(false);
      setStartedAt(null);
    }, remaining);
    return () => clearTimeout(t);
  }, [loading, ms, startedAt]);

  return stillShowing;
}

export default useMinDelay;
