/**
 * TakedownsLog — V6.25.31 — public IP-rights transparency log.
 *
 * Mirrors what the admin takedown modal writes to db.takedown_audit.
 * Lives at /legal/takedowns (no auth). Mounted in App.jsx routing.
 */
import React, { useEffect, useState } from "react";
import axios from "axios";
import { ShieldAlert, Undo2, Compass } from "lucide-react";

const POLICY_LABELS = {
  "piracy":                "Piracy / unauthorised reproduction",
  "lore-export":           "System lore export beyond CC/SRD",
  "artwork":               "Artwork copyright violation",
  "system-creator-rules":  "System creator's licensing rules",
  "community-rules":       "Community / app TOS violation",
  "other":                 "Other",
};

export default function TakedownsLog() {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    const apiBase = process.env.REACT_APP_BACKEND_URL || "";
    axios.get(`${apiBase}/api/legal/takedowns?limit=200`)
         .then((r) => { setRows(r.data.rows || []); setTotal(r.data.total || 0); })
         .catch(() => {})
         .finally(() => setBusy(false));
  }, []);

  return (
    <div className="min-h-screen bg-void text-parchment py-12 px-6">
      <div className="max-w-4xl mx-auto">
        <a href="/" className="text-mist text-xs hover:text-gold-bright flex items-center gap-1 mb-4"
           data-testid="takedown-log-home">
          <Compass className="w-3 h-3"/> back to TableGnostic
        </a>
        <h1 className="font-display text-4xl text-parchment mb-2"
            data-testid="takedown-log-title">
          Takedowns Log
        </h1>
        <p className="text-mist max-w-2xl mb-6 font-body">
          A transparent record of every marketplace listing TableGnostic
          administrators have removed. We publish this so creators, players,
          and rights-holders can see what's been actioned and why. Submitted
          counter-notices that result in restoration also appear here.
        </p>
        <div className="text-[10px] text-mist/60 tracking-widest uppercase mb-3">
          {busy ? "loading…" : `${total} entries`}
        </div>
        {rows.length === 0 && !busy && (
          <div className="card-mystic p-6 text-mist italic"
               data-testid="takedown-log-empty">
            No takedowns recorded — the marketplace remains untouched.
          </div>
        )}
        <ul className="space-y-2" data-testid="takedown-log-rows">
          {rows.map((r) => (
            <li key={r.id} className="card-mystic p-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  {r.action === "restore"
                    ? <Undo2 className="w-3 h-3 text-gold-bright"/>
                    : <ShieldAlert className="w-3 h-3 text-ember"/>}
                  <span className="font-display text-base text-parchment">
                    {r.target_name || r.target_id}
                  </span>
                  {r.policy && (
                    <span className="tag">{POLICY_LABELS[r.policy] || r.policy}</span>
                  )}
                </div>
                <div className="text-[10px] text-mist tabular-nums">{r.at}</div>
              </div>
              <div className="text-sm text-mist mt-1 font-body italic">
                {r.action === "restore"
                  ? "Listing restored."
                  : (r.reason || "—")}
              </div>
              <div className="text-[10px] text-mist/60 mt-1">
                actioned by {r.by_name || "admin"}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
