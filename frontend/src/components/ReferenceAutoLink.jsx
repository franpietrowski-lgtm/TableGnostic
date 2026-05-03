/**
 * ReferenceAutoLink — V6.21 P2
 *
 * App-wide modal that listens for `tg:open-reference` events and opens
 * a focused reference browser for the requested entry.
 *
 * Triggered by:
 *   - ReferencePicker chip clicks (inventory / spells / armor)
 *   - DndDerivedAndEquipment class-feature timeline clicks
 *   - AdvancementWizard subclass/feat picker blurbs
 *
 * The payload: `{ system_id, kind, name }`. The modal fetches
 * `/systems/{sid}/reference` + the campaign's custom references, finds
 * the match (case-insensitive substring), and renders the entry's full
 * mechanic block with a Close button.
 */
import React, { useEffect, useState } from "react";
import { X, BookOpen, Sparkles } from "lucide-react";
import { api } from "../lib/api";

export default function ReferenceAutoLink() {
  const [entry, setEntry] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    const handler = async (ev) => {
      const { system_id, kind, name, campaign_id } = ev.detail || {};
      if (!system_id || !name) return;
      setLoading(true); setErr(""); setEntry({ name, kind, loading: true });
      try {
        const [sysRef, camp] = await Promise.all([
          api.get(`/systems/${system_id}/reference`).catch(() => ({ data: {} })),
          campaign_id
            ? api.get(`/campaigns/${campaign_id}/references`).catch(() => ({ data: { entries: [] } }))
            : Promise.resolve({ data: { entries: [] } }),
        ]);
        const lc = (s) => (s || "").toLowerCase().trim();
        const haystack = [];
        const buckets = ["spells", "weapons", "armor", "items", "skills",
                          "classes", "races", "feats", "backgrounds",
                          "conditions", "actions", "power_levels",
                          // V6.23 Cypher buckets
                          "cyphers", "artifacts", "types", "foci",
                          "descriptors"];
        buckets.forEach((b) => (sysRef.data?.[b] || []).forEach(
          (e) => haystack.push({ ...e, __bucket: b })));
        (camp.data?.entries || camp.data || []).forEach(
          (e) => haystack.push({ ...e, __bucket: e.kind, __custom: true }));
        const qName = lc(name);
        const match = haystack.find(
          (e) => lc(e.name || e.title) === qName
        ) || haystack.find(
          (e) => lc(e.name || e.title).includes(qName)
        );
        if (!match) {
          setErr(`No reference entry found for "${name}". The GM can add `
                  + `a homebrew entry via Atelier · References.`);
          setEntry({ name, kind });
        } else {
          setEntry({ ...match, original_name: name });
        }
      } catch (e) {
        setErr(e.message || "Reference lookup failed.");
      } finally { setLoading(false); }
    };
    window.addEventListener("tg:open-reference", handler);
    return () => window.removeEventListener("tg:open-reference", handler);
  }, []);

  if (!entry) return null;

  const close = () => setEntry(null);

  const fields = entry ? Object.entries(entry).filter(
    ([k]) => !["name", "__bucket", "__custom", "__kind", "original_name",
                "loading"].includes(k) && !k.startsWith("_")
  ) : [];

  return (
    <div className="fixed inset-0 z-50 bg-void/90 backdrop-blur-md flex items-center justify-center p-4"
         onClick={close} data-testid="reference-autolink-modal">
      <div className="card-mystic max-w-2xl w-full p-6 relative"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={close}
                className="absolute top-3 right-3 btn btn-ghost"
                data-testid="reference-autolink-close">
          <X className="w-4 h-4"/>
        </button>
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="w-4 h-4 text-gold-bright"/>
          <span className="label-ref">Reference</span>
          {entry.__custom && (
            <span className="inline-flex items-center gap-1 text-[10px] text-gold-bright">
              <Sparkles className="w-3 h-3"/> Homebrew
            </span>
          )}
        </div>
        <h2 className="font-display text-2xl text-gold-bright">
          {entry.name || entry.original_name}
        </h2>
        {entry.__bucket && (
          <div className="text-[11px] text-mist uppercase tracking-widest">
            {entry.__bucket}
          </div>
        )}
        {loading && <div className="text-mist text-xs mt-3">Loading reference…</div>}
        {err && (
          <div className="border-l-2 border-ember bg-ember/10 p-2 text-[11px] text-ember mt-3"
               data-testid="reference-autolink-error">
            {err}
          </div>
        )}
        {!loading && !err && (
          <div className="mt-4 space-y-2 text-sm">
            {fields.map(([k, v]) => (
              <div key={k} className="grid grid-cols-3 gap-2 border-b border-gold/10 pb-1">
                <div className="col-span-1 text-[11px] text-mist uppercase tracking-widest">
                  {k.replace(/_/g, " ")}
                </div>
                <div className="col-span-2 text-parchment">
                  {Array.isArray(v)
                    ? v.join(", ")
                    : typeof v === "object" && v !== null
                      ? JSON.stringify(v)
                      : String(v)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
