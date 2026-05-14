/**
 * V6.25.54 — Phase C: Campaign export / import UI surfaces.
 *
 * Two components:
 *   - <CampaignExportCard camp/>    drop-in panel for CampaignDetail's
 *                                   "Invite & Share" tab. Owner / admin
 *                                   only — downloads a .tgcampaign.json.
 *   - <CampaignImportButton />      drop-in for the Hall of Tables list
 *                                   page. GM / admin only — uploads a
 *                                   .tgcampaign.json file and navigates
 *                                   to the new campaign on success.
 *
 * Both surfaces avoid LLM dependencies — the underlying endpoints
 * (`GET /api/campaigns/{cid}/export`, `POST /api/campaigns/import`) do
 * pure data round-trips.
 */
import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Download, Loader2 } from "lucide-react";
import { api, useAuth, formatApiErrorDetail } from "../lib/api";

// ────────────────── Export panel (per-campaign) ──────────────────

export function CampaignExportCard({ camp }) {
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const canExport = !!camp && (user?.role === "admin" || user?.id === camp.gm_id);
  if (!canExport) return null;

  const fileSlug = (camp.name || "campaign")
    .toLowerCase().replace(/[^a-z0-9-]+/g, "-").replace(/^-+|-+$/g, "") || "campaign";

  const download = async () => {
    setBusy(true);
    setError("");
    try {
      const res = await api.get(`/campaigns/${camp.id}/export`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileSlug}-${camp.id.slice(0, 8)}.tgcampaign.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(formatApiErrorDetail(e) || "Export failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card-mystic p-4 mt-4" data-testid="campaign-export-card">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="label-ref text-amber-300">Export campaign</div>
          <div className="font-display text-base text-parchment mt-0.5">
            Download `.tgcampaign.json`
          </div>
          <div className="text-[11px] text-mist/80 mt-1 max-w-md">
            A portable, self-contained bundle of the codex, characters,
            writer-tool entries, sessions, channels, encounters, atlas
            pins, and roll tables — re-uploadable on any TableGnostic pod.
            Audio &amp; flagged-content moderation rows are deliberately
            excluded.
          </div>
        </div>
        <button onClick={download} disabled={busy}
                className="btn btn-primary text-xs"
                data-testid="campaign-export-btn">
          {busy
            ? <><Loader2 className="w-3 h-3 animate-spin"/> Bundling…</>
            : <><Download className="w-3 h-3"/> Download bundle</>}
        </button>
      </div>
      {error && (
        <div className="mt-3 text-rose-300 text-[11px]"
             data-testid="campaign-export-error">{error}</div>
      )}
    </div>
  );
}

// ────────────────── Import button (Hall of Tables) ──────────────────

export function CampaignImportButton({ onImported }) {
  const { user } = useAuth();
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const canImport = user && (user.role === "gm" || user.role === "admin");
  if (!canImport) return null;

  const pick = () => {
    setError("");
    inputRef.current?.click();
  };

  const upload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-picking the same file
    if (!file) return;
    if (!/\.tgcampaign\.json$|\.json$/i.test(file.name)) {
      setError("Please pick a .tgcampaign.json file.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file, file.name);
      const { data } = await api.post("/campaigns/import", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onImported?.(data);
      const cid = data?.campaign?.id;
      if (cid) navigate(`/app/campaigns/${cid}`);
    } catch (err) {
      setError(formatApiErrorDetail(err) || "Import failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button onClick={pick} disabled={busy}
              className="btn btn-ghost text-xs"
              data-testid="campaign-import-btn"
              title="Upload a .tgcampaign.json bundle">
        {busy
          ? <><Loader2 className="w-3 h-3 animate-spin"/> Importing…</>
          : <><Upload className="w-3 h-3"/> Import bundle</>}
      </button>
      <input ref={inputRef} type="file"
             accept=".tgcampaign.json,application/json,.json"
             onChange={upload}
             className="hidden"
             data-testid="campaign-import-file-input"/>
      {error && (
        <div className="text-rose-300 text-[10px] mt-1 font-ui"
             data-testid="campaign-import-error">{error}</div>
      )}
    </>
  );
}
