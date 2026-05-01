import React, { useRef, useState } from "react";
import { ImagePlus, RefreshCw, User } from "lucide-react";

/**
 * CharacterPortrait — V6.11 character art slot for the sheet header.
 *
 * Owners (and the GM) can upload a portrait; everyone sees it. Falls back to
 * a stylised silhouette when no portrait is set so the slot still anchors
 * the header layout. Multipart upload to /api/uploads/character-portrait/{cid}.
 */
export default function CharacterPortrait({ character, canEdit, onUploaded }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const url = character.portrait_url
    ? `${process.env.REACT_APP_BACKEND_URL || ""}${character.portrait_url}`
    : null;

  const onFile = async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    setBusy(true); setErr("");
    try {
      const fd = new FormData();
      fd.append("file", f);
      const token = localStorage.getItem("tg_token");
      const r = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/uploads/character-portrait/${character.id}`,
        { method: "POST", body: fd, headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.detail || `HTTP ${r.status}`);
      }
      onUploaded && onUploaded();
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className="flex-shrink-0" data-testid="character-portrait">
      <div
        className="relative w-28 h-36 sm:w-32 sm:h-44 rounded-sm overflow-hidden border-2 border-gold/40 bg-void/50 cursor-pointer group"
        onClick={() => canEdit && inputRef.current?.click()}
        title={canEdit ? "Click to upload character art" : character.name}
        data-testid="character-portrait-slot"
        style={{ boxShadow: "inset 0 0 30px rgba(0,0,0,0.65)" }}
      >
        {url ? (
          <img src={url} alt={`${character.name} portrait`}
               className="w-full h-full object-cover"
               data-testid="character-portrait-image"/>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-mist/60">
            <User className="w-10 h-10"/>
            <div className="text-[9px] uppercase tracking-widest mt-1">no portrait</div>
            {canEdit && (
              <div className="text-[8px] text-gold-bright mt-1 italic">click to upload</div>
            )}
          </div>
        )}
        {canEdit && url && (
          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <span className="text-[10px] text-gold-bright uppercase tracking-widest font-ui flex items-center gap-1">
              <ImagePlus className="w-3 h-3"/> Replace
            </span>
          </div>
        )}
        {busy && (
          <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
            <RefreshCw className="w-5 h-5 text-gold animate-spin"/>
          </div>
        )}
      </div>
      <input ref={inputRef} type="file" accept="image/png,image/jpeg,image/webp"
             className="hidden" onChange={onFile}
             data-testid="character-portrait-file-input"/>
      {err && (
        <div className="text-[10px] text-ember mt-1 max-w-[140px]"
             data-testid="character-portrait-error">{err}</div>
      )}
    </div>
  );
}
