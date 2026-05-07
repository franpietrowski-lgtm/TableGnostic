/**
 * MaterialsIntakePanel — V6.25.12
 *
 * Player-facing intake for material / byproduct / craft-output
 * entries. The panel sits inside the Character Journal (or any
 * journal-shaped surface) and is read/write for the character's
 * owner; GMs see a richer mirror of the same surface in the GM
 * Approval Queue (see GM Approval Queue UI).
 *
 * Permission model (V6.25.11):
 *   • Players cannot directly add to codex/genesis/epic.
 *   • Submitting here creates a PENDING ticket. The GM's queue UI
 *     decides — approve seeds a codex node with the right `node_kind`,
 *     reject preserves the journal entry but flags it 'rejected'.
 *
 * Use:
 *   <MaterialsIntakePanel campaignId={cid}/>
 */
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Loader2, Send, AlertCircle, CheckCircle2, Clock, X } from "lucide-react";

const KINDS = [
  { id: "material",     label: "Material",       hint: "Raw substance harvested or refined." },
  { id: "byproduct",    label: "Byproduct",      hint: "Waste / leftover / mundane reside." },
  { id: "craft_output", label: "Craft Output",   hint: "Finished recipe result." },
];

const RARITY = ["common", "uncommon", "rare", "very rare", "legendary"];

export default function MaterialsIntakePanel({ campaignId }) {
  const [tickets, setTickets] = useState([]);
  const [name, setName] = useState("");
  const [kind, setKind] = useState("material");
  const [summary, setSummary] = useState("");
  const [tags, setTags] = useState("");
  const [rarity, setRarity] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState(false);

  const refresh = async () => {
    try {
      const { data } = await api.get(`/campaigns/${campaignId}/materials-queue`);
      setTickets(data || []);
    } catch (e) {
      // Silent — the panel still works for submission.
    }
  };

  useEffect(() => { if (campaignId) refresh(); }, [campaignId]);

  const submit = async (e) => {
    e?.preventDefault?.();
    setBusy(true); setErr(""); setOk(false);
    try {
      await api.post(`/campaigns/${campaignId}/materials-queue`, {
        name, node_kind: kind,
        summary,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        rarity: rarity || null,
      });
      setName(""); setSummary(""); setTags(""); setRarity(""); setKind("material");
      setOk(true);
      await refresh();
    } catch (e2) {
      setErr(e2.response?.data?.detail || e2.message);
    } finally { setBusy(false); }
  };

  const statusIcon = (s) => {
    if (s === "approved") return <CheckCircle2 className="w-3 h-3 text-arcane"/>;
    if (s === "rejected") return <X className="w-3 h-3 text-ember"/>;
    return <Clock className="w-3 h-3 text-mist"/>;
  };

  return (
    <div className="card-mystic p-4 space-y-3" data-testid="materials-intake-panel">
      <div>
        <div className="label-ref">Materials, Byproducts &amp; Craft Outputs</div>
        <div className="text-[11px] text-mist italic">
          Record what you harvested, refined, or crafted. Submissions go to the
          GM&apos;s approval queue — approved entries seed the campaign codex with
          full provenance back to your character.
        </div>
      </div>

      <form onSubmit={submit} className="space-y-2 border-t border-gold/10 pt-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <input className="input" required value={name}
                 placeholder="e.g. Spider Silk (rough)"
                 onChange={(e) => setName(e.target.value)}
                 data-testid="materials-name"/>
          <select className="select" value={kind}
                   onChange={(e) => setKind(e.target.value)}
                   data-testid="materials-kind">
            {KINDS.map((k) =>
              <option key={k.id} value={k.id}>{k.label} — {k.hint}</option>)}
          </select>
        </div>
        <textarea className="input" rows={2} value={summary}
                   placeholder="Summary — where it came from, what it does, who might want it."
                   onChange={(e) => setSummary(e.target.value)}
                   data-testid="materials-summary"/>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <input className="input" value={tags}
                 placeholder="tags (comma-separated): fibre, alchemy, rare"
                 onChange={(e) => setTags(e.target.value)}
                 data-testid="materials-tags"/>
          <select className="select" value={rarity}
                   onChange={(e) => setRarity(e.target.value)}
                   data-testid="materials-rarity">
            <option value="">Rarity (optional)</option>
            {RARITY.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        {err && (
          <div className="text-ember text-[11px] flex items-center gap-1"
               data-testid="materials-error">
            <AlertCircle className="w-3 h-3"/> {err}
          </div>
        )}
        {ok && (
          <div className="text-arcane text-[11px]"
               data-testid="materials-success">
            Submitted to GM. They&apos;ll review and approve / reject from the queue.
          </div>
        )}
        <button type="submit" disabled={busy || !name}
                className="btn btn-primary text-xs"
                data-testid="materials-submit">
          {busy ? <Loader2 className="w-3 h-3 animate-spin"/> : <Send className="w-3 h-3"/>}
          {busy ? "Submitting…" : "Submit to GM"}
        </button>
      </form>

      {tickets.length > 0 && (
        <div className="border-t border-gold/10 pt-3 space-y-1">
          <div className="label-ref">Your submissions</div>
          {tickets.map((t) => (
            <div key={t.id}
                 className="flex items-start gap-2 border border-gold/10 rounded-sm p-2 text-xs"
                 data-testid={`materials-ticket-${t.id}`}>
              {statusIcon(t.status)}
              <div className="flex-1 min-w-0">
                <div className="text-parchment font-display truncate">
                  {t.name}
                  <span className="ml-2 text-[10px] text-mist/70 font-ui uppercase tracking-widest">
                    {t.node_kind}
                  </span>
                  {t.rarity && (
                    <span className="ml-2 text-[10px] text-arcane">{t.rarity}</span>
                  )}
                </div>
                <div className="text-[10px] text-mist truncate">
                  {t.status} · submitted {new Date(t.submitted_at).toLocaleDateString()}
                  {t.codex_node_id && (
                    <span className="ml-2 text-arcane">→ codex seeded</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
