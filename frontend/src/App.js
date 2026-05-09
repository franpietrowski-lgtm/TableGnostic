import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/api";
import { useMinDelay } from "./lib/useMinDelay";
import Landing from "./components/Landing";
import Auth from "./components/Auth";
import Shell from "./components/Shell";
import Dashboard from "./components/Dashboard";
import Invite from "./components/Invite";
import ShareLink from "./components/ShareLink";
import Reset from "./components/Reset";
import TakedownsLog from "./components/TakedownsLog";

// Lazy-load the heavy route components so initial bundle stays lean and
// the Dashboard paints sooner. Each chunk is ~50–200KB minified.
const Campaigns       = lazy(() => import("./components/Campaigns"));
const CampaignDetail  = lazy(() => import("./components/CampaignDetail"));
const CharacterBuilder= lazy(() => import("./components/CharacterBuilder"));
const CharacterSheet  = lazy(() => import("./components/CharacterSheet"));
const SessionView     = lazy(() => import("./components/SessionView"));
const Reference       = lazy(() => import("./components/Reference"));
const CampaignGenesis = lazy(() => import("./components/CampaignGenesis"));
const Discover        = lazy(() => import("./components/Discover"));
const Account         = lazy(() => import("./components/Account"));
const DirectorConsole = lazy(() => import("./components/DirectorConsole"));
const HowToGuide      = lazy(() => import("./components/HowToGuide"));
const CanonRegistry   = lazy(() => import("./components/CanonRegistry"));
const Marketplace     = lazy(() => import("./components/Marketplace"));

function Protected({ children }) {
  const { user, loading } = useAuth();
  // Hold the SUMMONING screen for a beat so the flicker actually reads
  // as a ritual instead of a flash. ~5 s minimum.
  const stillSummoning = useMinDelay(loading || user === null, 5000);
  if (stillSummoning) return <LoadingScreen />;
  if (!user) return <Navigate to="/auth" replace />;
  return children;
}

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center" data-testid="app-loading-screen">
      <div className="flex flex-col items-center gap-4">
        <div className="text-gold font-display tracking-[0.4em] text-sm animate-flicker">
          SUMMONING
        </div>
        <div className="text-mist/50 text-[10px] font-ui uppercase tracking-[0.3em]">
          The Loremaster gathers your table…
        </div>
      </div>
    </div>
  );
}

// Quick fallback for lazily-loaded route chunks. Shorter than the full
// SUMMONING screen — these chunks are typically <200ms.
function RouteFallback() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center" data-testid="route-loading">
      <div className="text-gold/70 font-display tracking-[0.3em] text-xs animate-flicker">
        UNFOLDING…
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/invite/:token" element={<Invite />} />
          <Route path="/share/:token" element={<ShareLink />} />
          <Route path="/reset" element={<Reset />} />
          <Route path="/legal/takedowns" element={<TakedownsLog />} />
          <Route element={<Protected><Shell /></Protected>}>
            <Route path="/app" element={<Dashboard />} />
            <Route path="/app/campaigns" element={<Suspense fallback={<RouteFallback/>}><Campaigns /></Suspense>} />
            <Route path="/app/discover" element={<Suspense fallback={<RouteFallback/>}><Discover /></Suspense>} />
            <Route path="/app/campaigns/:id" element={<Suspense fallback={<RouteFallback/>}><CampaignDetail /></Suspense>} />
            <Route path="/app/campaigns/:id/genesis" element={<Suspense fallback={<RouteFallback/>}><CampaignGenesis /></Suspense>} />
            <Route path="/app/campaigns/:id/characters/new" element={<Suspense fallback={<RouteFallback/>}><CharacterBuilder /></Suspense>} />
            <Route path="/app/characters/:id" element={<Suspense fallback={<RouteFallback/>}><CharacterSheet /></Suspense>} />
            <Route path="/app/characters/:id/edit" element={<Suspense fallback={<RouteFallback/>}><CharacterBuilder /></Suspense>} />
            <Route path="/app/sessions/:id" element={<Suspense fallback={<RouteFallback/>}><SessionView /></Suspense>} />
            <Route path="/app/reference" element={<Suspense fallback={<RouteFallback/>}><Reference /></Suspense>} />
            <Route path="/app/account" element={<Suspense fallback={<RouteFallback/>}><Account /></Suspense>} />
            <Route path="/app/campaigns/:id/director" element={<Suspense fallback={<RouteFallback/>}><DirectorConsole /></Suspense>} />
            <Route path="/app/help" element={<Suspense fallback={<RouteFallback/>}><HowToGuide /></Suspense>} />
            <Route path="/app/canon" element={<Suspense fallback={<RouteFallback/>}><CanonRegistry /></Suspense>} />
            <Route path="/app/marketplace" element={<Suspense fallback={<RouteFallback/>}><Marketplace /></Suspense>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
