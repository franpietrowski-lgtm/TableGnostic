import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/api";
import { Scroll, LayoutGrid, BookOpen, LogOut, UserCircle2, Compass } from "lucide-react";

const Sigil = () => (
  <svg viewBox="0 0 120 120" className="w-8 h-8 logo-mark" xmlns="http://www.w3.org/2000/svg">
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

export default function Shell() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const onLogout = async () => { await logout(); nav("/"); };

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-sm font-ui text-sm tracking-wide transition
     ${isActive ? "bg-gold/10 text-gold-bright border-l-2 border-gold" : "text-mist hover:text-parchment hover:bg-gold/5 border-l-2 border-transparent"}`;

  return (
    <div className="relative z-10 min-h-screen grid grid-cols-[240px_1fr]">
      <aside className="border-r border-gold/10 bg-void/60 backdrop-blur-sm min-h-screen flex flex-col"
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
          <NavLink to="/app" end className={linkClass} data-testid="nav-dashboard">
            <LayoutGrid className="w-4 h-4" /> Dashboard
          </NavLink>
          <NavLink to="/app/campaigns" className={linkClass} data-testid="nav-campaigns">
            <Scroll className="w-4 h-4" /> Campaigns
          </NavLink>
          <NavLink to="/app/discover" className={linkClass} data-testid="nav-discover">
            <Compass className="w-4 h-4" /> Discover Tables
          </NavLink>
          <NavLink to="/app/reference" className={linkClass} data-testid="nav-reference">
            <BookOpen className="w-4 h-4" /> BESM Reference
          </NavLink>
        </nav>

        <div className="p-4 border-t border-gold/10">
          <div className="flex items-center gap-3 mb-3">
            <UserCircle2 className="w-6 h-6 text-gold/70" />
            <div>
              <div className="text-sm text-parchment font-ui" data-testid="user-name">{user?.name}</div>
              <div className="text-[10px] text-mist font-ui tracking-widest uppercase">{user?.role}</div>
            </div>
          </div>
          <button onClick={onLogout} className="btn btn-ghost w-full text-xs" data-testid="logout-btn">
            <LogOut className="w-4 h-4" /> Leave Table
          </button>
        </div>
      </aside>

      <main className="min-h-screen page overflow-x-hidden">
        <Outlet />
      </main>
    </div>
  );
}
