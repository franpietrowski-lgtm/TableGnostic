/**
 * V6.25.46 — Storyteller Outline & Beats.
 *
 * Reuses the manuscript_sections backend collection but presents it
 * as a flat outline view focused on beats: each scene's beats are
 * listed inline with a tension-rating slider (0..5) and a status
 * chip. This makes pacing visible — the user can scan the whole
 * arc's tension curve at a glance.
 */
import React, { useEffect, useMemo, useState } from "react";
import { ListTree, Plus } from "lucide-react";
import { api } from "../../lib/api";

const TENSION_BAR_COLOR = ["bg-emerald-700", "bg-emerald-500", "bg-amber-500",
                           "bg-orange-500", "bg-rose-500", "bg-rose-700"];
const STATUS_OPTIONS = ["planned", "drafted", "revised", "cut"];

export default function StOutlineTool({ campId }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      const r = await api.get(`/writer/manuscript/${campId}`);
      setData(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Load failed.");
    }
  };
  useEffect(() => { if (campId) refresh(); }, [campId]);

  // Build chapter → scenes → beats structure.
  const tree = useMemo(() => {
    const rows = (data?.sections || []).slice().sort(
      (a, b) => (a.order || 0) - (b.order || 0),
    );
    const byParent = {};
    rows.forEach((r) => {
      const k = r.parent_id || "_root";
      (byParent[k] = byParent[k] || []).push(r);
    });
    const out = [];
    for (const ch of byParent["_root"] || []) {
      const scenes = [];
      for (const sc of byParent[ch.id] || []) {
        const beats = byParent[sc.id] || [];
        scenes.push({ scene: sc, beats });
      }
      out.push({ chapter: ch, scenes });
    }
    return out;
  }, [data]);

  const patch = async (sid, patchObj) => {
    setBusy(true); setErr("");
    try {
      const cur = (data?.sections || []).find((r) => r.id === sid);
      await api.patch(`/writer/manuscript/${campId}/${sid}`, {
        kind: cur.kind, title: cur.title, ...patchObj,
      });
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Save failed.");
    } finally { setBusy(false); }
  };

  const addBeat = async (sceneId) => {
    setBusy(true); setErr("");
    try {
      await api.post(`/writer/manuscript/${campId}`, {
        kind: "beat", parent_id: sceneId, title: "New beat",
        status: "planned", tension: 2,
      });
      await refresh();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Create failed.");
    } finally { setBusy(false); }
  };

  if (!data) {
    return <div className="p-6 text-mist italic" data-testid="st-outline-loading">Drafting outline…</div>;
  }

  return (
    <div className="p-4 space-y-3" data-testid="st-outline-page">
      <div className="card-mystic p-3 border-rose-700/30 flex items-center gap-3">
        <ListTree className="w-5 h-5 text-rose-300"/>
        <div className="flex-1">
          <div className="label-ref text-rose-300">Outline & Beats</div>
          <div className="text-[11px] text-mist/70 italic">
            Pacing graph at a glance. Edit chapters/scenes in <b>Manuscript</b>;
            here you tune the tension of each beat and watch the arc breathe.
          </div>
        </div>
      </div>

      {tree.length === 0 ? (
        <div className="text-[12px] text-mist/60 italic text-center py-6"
             data-testid="st-outline-empty">
          No chapters yet. Create one in the Manuscript tab and the beats land here.
        </div>
      ) : tree.map(({ chapter, scenes }) => (
        <div key={chapter.id} className="card-mystic p-3 border-rose-700/30"
             data-testid={`st-outline-chapter-${chapter.id}`}>
          <div className="font-display text-lg text-parchment mb-2">
            {chapter.title}
          </div>
          {scenes.length === 0 && (
            <div className="text-[11px] text-mist/60 italic">No scenes in this chapter.</div>
          )}
          {scenes.map(({ scene, beats }) => (
            <div key={scene.id} className="mb-3 pl-3 border-l border-rose-900/30"
                 data-testid={`st-outline-scene-${scene.id}`}>
              <div className="flex items-center gap-2 mb-1">
                <div className="text-sm text-rose-200">{scene.title}</div>
                <div className="text-[10px] text-mist/50">
                  {beats.length} beat{beats.length === 1 ? "" : "s"}
                </div>
                {data.writable && (
                  <button type="button" onClick={() => addBeat(scene.id)}
                          disabled={busy}
                          className="btn btn-ghost text-[10px] text-rose-300"
                          data-testid={`st-outline-add-beat-${scene.id}`}>
                    <Plus className="w-2.5 h-2.5"/> Beat
                  </button>
                )}
              </div>
              {beats.length > 0 && (
                <div className="space-y-1">
                  {beats.map((b) => (
                    <div key={b.id}
                         className="grid grid-cols-[1fr_120px_90px_8px] gap-2 items-center text-[11px]"
                         data-testid={`st-outline-beat-${b.id}`}>
                      <input type="text" value={b.title}
                             onChange={(e) => patch(b.id, { title: e.target.value })}
                             disabled={!data.writable}
                             className="bg-transparent border-b border-rose-900/30 px-1 py-0.5 outline-none focus:border-rose-500"
                             data-testid={`st-outline-beat-title-${b.id}`}/>
                      <select value={b.status || "planned"}
                              onChange={(e) => patch(b.id, { status: e.target.value })}
                              disabled={!data.writable}
                              className="input text-[10px] py-0"
                              data-testid={`st-outline-beat-status-${b.id}`}>
                        {STATUS_OPTIONS.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                      <input type="range" min={0} max={5} step={1}
                             value={b.tension ?? 2}
                             onChange={(e) => patch(b.id, { tension: parseInt(e.target.value, 10) })}
                             disabled={!data.writable}
                             className="w-full accent-rose-500"
                             data-testid={`st-outline-beat-tension-${b.id}`}/>
                      <div className={`w-2 h-5 rounded-sm ${TENSION_BAR_COLOR[b.tension ?? 2]}`}
                           title={`tension ${b.tension ?? 2}/5`}/>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}

      {err && (
        <div className="text-[11px] text-rose-300 italic"
             data-testid="st-outline-error">{err}</div>
      )}
    </div>
  );
}
