import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import Sigil from "./Sigil";

export default function LandingNav({ user }) {
  const nav = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const link = "text-[11px] font-ui uppercase tracking-[0.22em] text-mist hover:text-gold-bright transition-colors";

  return (
    <nav
      className={`fixed top-0 inset-x-0 z-40 transition-all duration-500 ${
        scrolled
          ? "bg-void/80 backdrop-blur-md border-b border-gold/10 py-3"
          : "bg-transparent py-5"
      }`}
      data-testid="landing-nav"
    >
      <div className="max-w-7xl mx-auto px-5 md:px-10 flex items-center justify-between gap-4">
        <a href="#hero" className="flex items-center gap-3 group" data-testid="landing-nav-brand">
          <Sigil size={36} />
          <div className="hidden sm:block">
            <div className="font-display tracking-[0.32em] text-sm text-parchment group-hover:text-gold-bright transition-colors">
              TABLE<span className="text-gold">·</span>GNOSTIC
            </div>
            <div className="text-[9px] font-ui tracking-[0.32em] uppercase text-gold/55 -mt-0.5">
              not the system. the table.
            </div>
          </div>
        </a>

        <div className="hidden lg:flex items-center gap-7">
          <a href="#what" className={link} data-testid="nav-link-what">What it does</a>
          <a href="#roles" className={link} data-testid="nav-link-roles">For your table</a>
          <a href="#features" className={link} data-testid="nav-link-features">Features</a>
          <a href="#marketplace" className={link} data-testid="nav-link-marketplace">Homebrew</a>
          <a href="#roadmap" className={link} data-testid="nav-link-roadmap">Roadmap</a>
          <a href="#contact" className={link} data-testid="nav-link-contact">Contact</a>
        </div>

        <div className="flex items-center gap-2">
          {user ? (
            <button
              onClick={() => nav("/app")}
              className="btn btn-primary text-xs"
              data-testid="nav-enter-app-btn"
            >
              Enter the Table <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <>
              <Link
                to="/auth?mode=login"
                className="btn btn-ghost text-xs hidden sm:inline-flex"
                data-testid="nav-login-btn"
              >
                Sign In
              </Link>
              <Link
                to="/auth?mode=register"
                className="btn btn-primary text-xs"
                data-testid="nav-take-a-seat-btn"
              >
                Take a Seat <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
