import React, { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/api";
import { Scroll, LayoutGrid, BookOpen, LogOut, UserCircle2, Compass, Menu, X, User, HelpCircle, Sparkles } from "lucide-react";
import CmdKPalette from "./CmdKPalette";
import { TourProvider } from "./TourProvider";

const Sigil = ({ size = 32 }) => (
  <svg viewBox="0 0 120 120" style={{ width: size, height: size }}
       className="logo-mark shrink-0" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="sh" x1="0" x2="1">
        <stop offset="0" stopColor="#e5c370" />
        <stop offset="1" stopColor="#8a6b20" />
      </linearGradient>
    </defs>
    <circle cx="60" cy="60" r="52" fill="none" stroke="url(#sh)" strokeWidth="1" />
    <polygon points="60,18 72,38 96,40 78,56 82,80 60,68 38,80 42,56 24,40 48,38"
             fill="none" stroke="url(#sh)" strokeWidth="1.2" />
  </svg>
);

const NAV = [
  { to: "/app", end: true, icon: LayoutGrid, label: "Dashboard", testid: "nav-dashboard" },
  { to: "/app/campaigns", icon: Scroll, label: "Campaigns", testid: "nav-campaigns" },
  { to: "/app/discover", icon: Compass, label: "Discover", testid: "nav-discover" },
  { to: "/app/reference", icon: BookOpen, label: "Reference", testid: "nav-reference" },
  { to: "/app/canon", icon: Sparkles, label: "Canon", testid: "nav-canon" },
  { to: "/app/help", icon: HelpCircle, label: "How To", testid: "nav-help" },
  { to: "/app/account", icon: User, label: "Account", testid: "nav-account" },
];

export default function Shell() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [drawer, setDrawer] = useState(false);
  const onLogout = async () => { await logout(); nav("/"); };

  const sideLink = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-sm font-ui text-sm tracking-wide transition
     ${isActive ? "bg-gold/10 text-gold-bright border-l-2 border-gold" : "text-mist hover:text-parchment hover:bg-gold/5 border-l-2 border-transparent"}`;
  const tabLink = ({ isActive }) =>
    `flex flex-col items-center justify-center gap-0.5 flex-1 py-2.5 transition
     ${isActive ? "text-gold-bright" : "text-mist/70 hover:text-parchment"}`;

  return (
    <TourProvider>
    <div className="relative z-10 min-h-screen md:grid md:grid-cols-[240px_1fr]">
      {/* DESKTOP SIDEBAR */}
      <aside className="hidden md:flex border-r border-gold/10 bg-void/60 backdrop-blur-sm min-h-screen flex-col"
             data-testid="shell-sidebar">
        <div className="px-6 py-6 border-b border-gold/10">
          <NavLink to="/app" className="flex items-center gap-3">
            <Sigil />
            <div>
              <div className="font-display tracking-[0.25em] text-sm text-parchment">TABLE-GNOSTIC</div>
              <div className="text-[10px] font-ui tracking-widest uppercase text-gold/60">not the system. the table.</div>
            </div>
          </NavLink>
        </div>
        <nav className="flex-1 py-4 space-y-1 px-3">
          {NAV.map(({ to, end, icon: Icon, label, testid }) => (
            <NavLink key={to} to={to} end={end} className={sideLink} data-testid={testid}>
              <Icon className="w-4 h-4" /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gold/10">
          <div className="flex items-center gap-3 mb-3">
            <UserCircle2 className="w-6 h-6 text-gold/70" />
            <div className="min-w-0">
              <div className="text-sm text-parchment font-ui truncate" data-testid="user-name">{user?.name}</div>
              <div className="text-[10px] text-mist font-ui tracking-widest uppercase">{user?.role}</div>
            </div>
          </div>
          <button onClick={onLogout} className="btn btn-ghost w-full text-xs" data-testid="logout-btn">
            <LogOut className="w-4 h-4" /> Leave Table
          </button>
        </div>
      </aside>

      {/* MOBILE TOPBAR */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 border-b border-gold/10 bg-void/80 backdrop-blur sticky top-0 z-30">
        <NavLink to="/app" className="flex items-center gap-2">
          <Sigil size={28}/>
          <span className="font-display tracking-[0.25em] text-xs text-parchment">TABLE-GNOSTIC</span>
        </NavLink>
        <button onClick={() => setDrawer(true)} className="p-2 text-gold/80" data-testid="mobile-menu-btn">
          <Menu className="w-5 h-5"/>
        </button>
      </header>

      {/* MOBILE DRAWER */}
      {drawer && (
        <div className="md:hidden fixed inset-0 z-40 bg-void/85 backdrop-blur-sm" onClick={() => setDrawer(false)}>
          <div className="absolute right-0 top-0 bottom-0 w-72 bg-ink border-l border-gold/20 p-5 flex flex-col"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <span className="font-display tracking-[0.25em] text-xs text-parchment">MENU</span>
              <button onClick={() => setDrawer(false)} className="text-mist"><X className="w-5 h-5"/></button>
            </div>
            <nav className="flex-1 space-y-1">
              {NAV.map(({ to, end, icon: Icon, label, testid }) => (
                <NavLink key={to} to={to} end={end} className={sideLink}
                         onClick={() => setDrawer(false)} data-testid={`drawer-${testid}`}>
                  <Icon className="w-4 h-4" /> {label}
                </NavLink>
              ))}
            </nav>
            <div className="border-t border-gold/10 pt-4">
              <div className="flex items-center gap-2 mb-3 text-sm text-parchment font-ui">
                <UserCircle2 className="w-5 h-5 text-gold/70"/> {user?.name}
              </div>
              <button onClick={() => { setDrawer(false); onLogout(); }} className="btn btn-ghost w-full text-xs">
                <LogOut className="w-4 h-4"/> Leave Table
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONTENT */}
      <main className="min-h-screen page overflow-x-hidden pb-20 md:pb-0 flex flex-col">
        <div className="flex-1">
          <Outlet />
        </div>
        <AppFooter/>
      </main>

      {/* V6.13 — Cmd-K / Ctrl-K global search palette */}
      <CmdKPalette/>

      {/* MOBILE BOTTOM NAV */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 flex border-t border-gold/15 bg-void/90 backdrop-blur">
        {NAV.map(({ to, end, icon: Icon, label, testid }) => (
          <NavLink key={to} to={to} end={end} className={tabLink} data-testid={`bottom-${testid}`}>
            <Icon className="w-4 h-4"/>
            <span className="text-[9px] uppercase tracking-widest font-ui">{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
    </TourProvider>
  );
}

/**
 * App-level footer.
 *
 * Carries the **TableGnostic** legal posture (platform-wide). Per-system
 * marks (Tri-Stat Emporium · Dyskami · Cypher System Creator · etc.) live
 * inside each campaign's surfaces — they're applied conditionally by
 * `[data-system]` so the right rights-holder gets credit on the right page.
 */
function AppFooter() {
  return (
    <footer className="border-t border-gold/10 bg-void/60 px-6 md:px-12 py-6 mt-10"
            data-testid="app-footer">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Sigil size={28}/>
          <div>
            <div className="font-display tracking-[0.25em] text-xs text-parchment">TABLE-GNOSTIC</div>
            <div className="text-[10px] text-mist/70 italic">Not the system. The table.</div>
          </div>
        </div>
        <div className="text-[10px] text-mist/70 leading-relaxed font-ui max-w-2xl"
             data-testid="app-footer-legal">
          <p>
            Table-Gnostic is an unofficial, system-aware tabletop platform.
            Trademarks and copyrighted material referenced inside campaigns
            (BESM, Anime 5E, Cypher System, Numenera, D&amp;D, Pathfinder, Fate, Mothership,
            Blades in the Dark, Call of Cthulhu, Savage Worlds, Cyberpunk RED,
            Vampire: the Masquerade, Shadowrun) belong to their respective
            rights-holders. We display only mechanic names, page references,
            and numerics — never reproduced rulebook prose, lore, or art.
            Per-system attribution &amp; required licence text appear on each
            campaign and exported PDF.
          </p>
          <p className="mt-1">
            © {new Date().getFullYear()} Table-Gnostic · All original platform
            content licensed under its respective creator's terms.
          </p>
        </div>
      </div>
    </footer>
  );
}
