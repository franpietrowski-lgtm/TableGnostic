import React, { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/api";
import {
  Scroll, LayoutGrid, BookOpen, LogOut, UserCircle2, Compass, Menu, X,
  User, HelpCircle, Sparkles, Store, Wand2, Shield,
} from "lucide-react";
import CmdKPalette from "./CmdKPalette";
import ReferenceAutoLink from "./ReferenceAutoLink";
import { TourProvider } from "./TourProvider";

/**
 * Sigil — TableGnostic platform mark.
 *
 * Star-of-eyes + ringed circle. Used everywhere we need brand presence
 * (sidebar, mobile topbar, app footer). Keeps a fixed aspect ratio so
 * the SVG scales clean from 28px to 96px without losing weight.
 */
const Sigil = ({ size = 32 }) => (
  <svg viewBox="0 0 120 120" style={{ width: size, height: size }}
       className="logo-mark shrink-0" xmlns="http://www.w3.org/2000/svg"
       data-testid="tablegnostic-sigil">
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
  { to: "/app/concept-forge", icon: Wand2, label: "Concept Forge", testid: "nav-concept-forge" },
  { to: "/app/canon", icon: Sparkles, label: "Canon", testid: "nav-canon" },
  { to: "/app/marketplace", icon: Store, label: "Market", testid: "nav-marketplace" },
  { to: "/app/help", icon: HelpCircle, label: "How To", testid: "nav-help" },
  { to: "/app/account", icon: User, label: "Account", testid: "nav-account" },
];

// V6.25.39 — Surfaced only when `user.role === "admin"`.
const ADMIN_NAV = [
  { to: "/app/admin", icon: Shield, label: "Admin", testid: "nav-admin" },
];

export default function Shell() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [drawer, setDrawer] = useState(false);
  const onLogout = async () => { await logout(); nav("/"); };

  const sideLink = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-sm font-ui text-sm tracking-wide transition
     ${isActive ? "bg-gold/10 text-gold-bright border-l-2 border-gold" : "text-mist hover:text-parchment hover:bg-gold/5 border-l-2 border-transparent"}`;

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
          {user?.role === "admin" && (
            <>
              <div className="my-2 border-t border-gold/15"/>
              {ADMIN_NAV.map(({ to, icon: Icon, label, testid }) => (
                <NavLink key={to} to={to} className={sideLink} data-testid={testid}>
                  <Icon className="w-4 h-4" /> {label}
                </NavLink>
              ))}
            </>
          )}
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

      {/* MOBILE COMPACT TOPBAR
          V6.25.8 — Page titles previously crunched against the inline
          burger button on narrow viewports. Topbar is now ONLY the
          wordmark + sigil; navigation lives in the floating action
          burger pinned to the lower-right edge of the screen, so the
          header stays unblocked while the burger floats with scroll. */}
      <header className="md:hidden flex items-center justify-center px-4 py-3 border-b border-gold/10 bg-void/80 backdrop-blur sticky top-0 z-30">
        <NavLink to="/app" className="flex items-center gap-2"
                 data-testid="mobile-home-link">
          <Sigil size={26}/>
          <span className="font-display tracking-[0.25em] text-xs text-parchment">TABLE-GNOSTIC</span>
        </NavLink>
      </header>

      {/* FLOATING MOBILE BURGER (V6.25.8)
          Fixed to the lower-right with a sigil-coloured backdrop glow.
          Sits above content via z-40 and stays in reach while the user
          scrolls long sheets / chat logs. The previous bottom tab bar
          is removed so the footer (logo + legal + creator credit) gets
          breathing room on small screens. */}
      <button
        className="md:hidden fixed right-4 bottom-4 z-40 w-14 h-14 rounded-full
                    bg-void/95 border border-gold/40 shadow-2xl
                    flex items-center justify-center text-gold-bright
                    hover:bg-gold/20 hover:border-gold-bright transition-colors"
        style={{ boxShadow: "0 6px 20px rgba(229,195,112,0.25), 0 0 0 1px rgba(229,195,112,0.15)" }}
        onClick={() => setDrawer(true)}
        aria-label="Open navigation"
        data-testid="mobile-fab-menu">
        <Menu className="w-6 h-6"/>
      </button>

      {/* MOBILE DRAWER */}
      {drawer && (
        <div className="md:hidden fixed inset-0 z-50 bg-void/85 backdrop-blur-sm"
             onClick={() => setDrawer(false)}
             data-testid="mobile-drawer">
          <div className="absolute right-0 top-0 bottom-0 w-72 bg-ink border-l border-gold/20 p-5 flex flex-col"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Sigil size={26}/>
                <span className="font-display tracking-[0.25em] text-xs text-parchment">MENU</span>
              </div>
              <button onClick={() => setDrawer(false)} className="text-mist"
                      data-testid="mobile-drawer-close"
                      aria-label="Close navigation"><X className="w-5 h-5"/></button>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto">
              {NAV.map(({ to, end, icon: Icon, label, testid }) => (
                <NavLink key={to} to={to} end={end} className={sideLink}
                         onClick={() => setDrawer(false)} data-testid={`drawer-${testid}`}>
                  <Icon className="w-4 h-4" /> {label}
                </NavLink>
              ))}
              {user?.role === "admin" && (
                <>
                  <div className="my-2 border-t border-gold/15"/>
                  {ADMIN_NAV.map(({ to, icon: Icon, label, testid }) => (
                    <NavLink key={to} to={to} className={sideLink}
                             onClick={() => setDrawer(false)} data-testid={`drawer-${testid}`}>
                      <Icon className="w-4 h-4" /> {label}
                    </NavLink>
                  ))}
                </>
              )}
            </nav>
            <div className="border-t border-gold/10 pt-4">
              <div className="flex items-center gap-2 mb-3 text-sm text-parchment font-ui">
                <UserCircle2 className="w-5 h-5 text-gold/70"/> {user?.name}
              </div>
              <button onClick={() => { setDrawer(false); onLogout(); }} className="btn btn-ghost w-full text-xs"
                      data-testid="mobile-drawer-logout">
                <LogOut className="w-4 h-4"/> Leave Table
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONTENT */}
      <main className="min-h-screen page overflow-x-hidden flex flex-col"
            data-testid="shell-main">
        <div className="flex-1">
          <Outlet />
        </div>
        <AppFooter/>
      </main>

      {/* V6.13 — Cmd-K / Ctrl-K global search palette */}
      <CmdKPalette/>

      {/* V6.21 — Reference auto-link modal. Listens app-wide for
          `tg:open-reference` events fired by inventory chips, spell
          chips, class-feature timeline items, etc. */}
      <ReferenceAutoLink/>
    </div>
    </TourProvider>
  );
}

/**
 * App-level footer.
 *
 * V6.25.8 — Rebuilt.
 *
 * The previous mobile bottom-tab nav crowded the footer to the point
 * where the page titles + nav glyphs overlapped on narrow viewports.
 * Now mobile uses a floating burger; the footer is reclaimed for the
 * **TableGnostic original logo + legal posture**.
 *
 * Creator: Francis T Pietrowski (sole owner). Per-system trademark
 * notices remain inside each campaign's surfaces — they're applied
 * conditionally by `[data-system]` so the right rights-holder gets
 * credit on the right page.
 */
function AppFooter() {
  return (
    <footer className="border-t border-gold/15 bg-gradient-to-b from-void/40 to-void/80
                          px-6 md:px-12 py-10 mt-10 mb-20 md:mb-0"
            data-testid="app-footer">
      <div className="max-w-5xl mx-auto flex flex-col items-center text-center gap-5">
        {/* Centered original logo. */}
        <NavLink to="/app" className="inline-flex flex-col items-center gap-2 group"
                 data-testid="footer-logo">
          <Sigil size={72}/>
          <div>
            <div className="font-display tracking-[0.3em] text-base text-parchment group-hover:text-gold-bright transition-colors">
              TABLE-GNOSTIC
            </div>
            <div className="text-[10px] font-ui tracking-widest uppercase text-gold/60 mt-0.5">
              not the system. the table.
            </div>
          </div>
        </NavLink>

        {/* Creator credit. */}
        <div className="text-[11px] text-parchment/85 font-ui tracking-wide"
             data-testid="footer-creator">
          Created &amp; solely owned by{" "}
          <span className="text-gold-bright font-display tracking-widest">FRANCIS&nbsp;T.&nbsp;PIETROWSKI</span>
        </div>

        {/* Legal posture. Concise, plain-English liability + IP statement. */}
        <div className="text-[10px] md:text-[11px] text-mist/80 leading-relaxed font-ui max-w-3xl"
             data-testid="app-footer-legal">
          <p>
            Table-Gnostic is an independent, system-aware tabletop platform.
            All <strong>original platform code, UI, branding, mark, and
            creator-authored content</strong> are © {new Date().getFullYear()} Francis T. Pietrowski,
            all rights reserved. The Table-Gnostic mark and the &ldquo;Not the
            system. The table.&rdquo; tagline are proprietary.
          </p>
          <p className="mt-2">
            Game systems referenced inside campaigns &mdash; including BESM 4E,
            Anime 5E, the Cypher System, Numenera, Dungeons &amp; Dragons,
            Pathfinder, Fate, Mothership, Blades in the Dark, Call of Cthulhu,
            Savage Worlds, Cyberpunk RED, Vampire: the Masquerade, and
            Shadowrun &mdash; are the property of their respective rights-holders.
            The platform displays only mechanical names, page references, and
            numerics. <strong>No rulebook prose, lore, art, or proprietary
            setting material is reproduced</strong>; per-system attribution and
            required licence text appear on each campaign page and exported PDF.
          </p>
          <p className="mt-2">
            Use of Table-Gnostic is provided <strong>&ldquo;as-is&rdquo;</strong> without warranty
            of any kind. The creator and platform are not liable for any
            game-table outcomes, lost data, or damages arising from use. Users
            are solely responsible for the homebrew content they author and
            for ensuring they have the rights to share or sell any material
            published through the marketplace.
          </p>
        </div>

        <div className="text-[10px] text-mist/60 font-ui tracking-wide pt-2 border-t border-gold/10 w-full max-w-3xl">
          © {new Date().getFullYear()} Francis T. Pietrowski · Table-Gnostic Platform · All rights reserved.
        </div>
      </div>
    </footer>
  );
}
