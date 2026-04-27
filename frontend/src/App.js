import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/api";
import Landing from "./components/Landing";
import Auth from "./components/Auth";
import Shell from "./components/Shell";
import Dashboard from "./components/Dashboard";
import Campaigns from "./components/Campaigns";
import CampaignDetail from "./components/CampaignDetail";
import CharacterBuilder from "./components/CharacterBuilder";
import CharacterSheet from "./components/CharacterSheet";
import SessionView from "./components/SessionView";
import Reference from "./components/Reference";
import CampaignGenesis from "./components/CampaignGenesis";
import Discover from "./components/Discover";
import Invite from "./components/Invite";
import Reset from "./components/Reset";
import Account from "./components/Account";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading || user === null) return <LoadingScreen />;
  if (!user) return <Navigate to="/auth" replace />;
  return children;
}

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-gold font-display tracking-[0.4em] text-sm animate-flicker">
        SUMMONING
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
          <Route path="/reset" element={<Reset />} />
          <Route element={<Protected><Shell /></Protected>}>
            <Route path="/app" element={<Dashboard />} />
            <Route path="/app/campaigns" element={<Campaigns />} />
            <Route path="/app/discover" element={<Discover />} />
            <Route path="/app/campaigns/:id" element={<CampaignDetail />} />
            <Route path="/app/campaigns/:id/genesis" element={<CampaignGenesis />} />
            <Route path="/app/campaigns/:id/characters/new" element={<CharacterBuilder />} />
            <Route path="/app/characters/:id" element={<CharacterSheet />} />
            <Route path="/app/characters/:id/edit" element={<CharacterBuilder />} />
            <Route path="/app/sessions/:id" element={<SessionView />} />
            <Route path="/app/reference" element={<Reference />} />
            <Route path="/app/account" element={<Account />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
