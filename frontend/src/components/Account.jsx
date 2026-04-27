import React, { useEffect, useRef, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Save, Lock, Camera, User as UserIcon, Award, Scroll } from "lucide-react";

/**
 * Account — self-service profile editor.
 *
 * Surfaces:
 *   1. Identity strip (email · role · joined · byline)
 *   2. Avatar upload (used as AV-tile fallback when camera off + on PDF
 *      character-sheet exports). 4 MB cap; PNG/JPEG/WEBP only.
 *   3. Profile patch (byline name + bio)
 *   4. Password change (in-app, requires current password)
 *   5. Game stats — campaigns owned · characters owned · XP earned across
 *      all your characters. Lightweight aggregate, no extra round-trips.
 */
export default function Account() {
  const [me, setMe] = useState(null);
  const [byline, setByline] = useState("");
  const [bio, setBio] = useState("");
  const [pwCur, setPwCur] = useState("");
  const [pwNew, setPwNew] = useState("");
  const [pwConfirm, setPwConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [tick, setTick] = useState("");
  const [stats, setStats] = useState(null);
  const fileRef = useRef(null);

  const apiBase = process.env.REACT_APP_BACKEND_URL || "";

  const loadMe = async () => {
    try {
      const { data } = await api.get("/auth/me");
      setMe(data);
      setByline(data.byline_name || "");
      setBio(data.bio || "");
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    }
  };

  const loadStats = async () => {
    try {
      const camps = await api.get("/campaigns").then((r) => r.data || []);
      // Aggregate: campaigns I GM, characters across campaigns I'm in.
      const ownedCamps = camps.filter((c) => c.is_gm);
      const memberCamps = camps.filter((c) => !c.is_gm);
      const charLists = await Promise.all(
        camps.slice(0, 12).map((c) => api.get(`/campaigns/${c.id}/characters`)
          .then((r) => r.data || []).catch(() => []))
      );
      const myChars = [];
      charLists.forEach((list) => {
        list.forEach((ch) => { if (ch.owner_id === me?.id) myChars.push(ch); });
      });
      const xpTotal = myChars.reduce((s, ch) => s + (Number(ch.xp_total) || 0), 0);
      const xpUnspent = myChars.reduce((s, ch) => s + (Number(ch.xp_unspent) || 0), 0);
      setStats({
        campaigns_owned: ownedCamps.length,
        campaigns_seated: memberCamps.length,
        characters: myChars.length,
        xp_total: xpTotal,
        xp_unspent: xpUnspent,
      });
    } catch {/* non-blocking */}
  };

  useEffect(() => { loadMe(); }, []);
  useEffect(() => { if (me?.id) loadStats(); }, [me?.id]);

  const saveProfile = async () => {
    setBusy(true); setErr(""); setTick("");
    try {
      const { data } = await api.patch("/auth/me", { byline_name: byline, bio });
      setMe(data); setTick("profile-saved");
      setTimeout(() => setTick(""), 1800);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const changePassword = async () => {
    setErr(""); setTick("");
    if (pwNew.length < 8) { setErr("New password must be at least 8 characters."); return; }
    if (pwNew !== pwConfirm) { setErr("Passwords do not match."); return; }
    setBusy(true);
    try {
      await api.post("/auth/change-password",
        { current_password: pwCur, new_password: pwNew });
      setPwCur(""); setPwNew(""); setPwConfirm("");
      setTick("password-changed");
      setTimeout(() => setTick(""), 2200);
    } catch (e) {
      setErr(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally { setBusy(false); }
  };

  const onAvatarPicked = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true); setErr(""); setTick("");
    try {
      const fd = new FormData();
      fd.append("file", f);
      const token = localStorage.getItem("tg_token");
      const r = await fetch(`${apiBase}/api/uploads/avatar`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.detail || `Upload failed (HTTP ${r.status})`);
      }
      await loadMe();
      setTick("avatar-saved");
      setTimeout(() => setTick(""), 1800);
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  if (!me) return <div className="px-8 py-10 text-mist">Summoning your account…</div>;
  const avatarFullUrl = me.avatar_url ? `${apiBase}${me.avatar_url}` : "";

  return (
    <div className="px-6 sm:px-10 py-10 max-w-4xl" data-testid="account-page">
      <div className="label-ref flex items-center gap-2"><UserIcon className="w-3.5 h-3.5"/> Account</div>
      <h1 className="font-display text-3xl sm:text-4xl text-parchment mt-1">Your profile</h1>
      <p className="text-[12px] text-mist/80 italic mt-2 max-w-2xl">
        Identity, avatar, password, and game stats. Your avatar fills in for the
        AV tile when the camera's off, and rides along on PDF character sheet exports.
      </p>

      {err && <div className="text-ember text-sm mt-3" data-testid="account-error">{err}</div>}

      {/* Identity + Avatar */}
      <div className="card-mystic p-6 mt-6 grid sm:grid-cols-[160px_1fr] gap-6 items-start"
           data-testid="account-identity">
        <div className="flex flex-col items-center gap-2">
          <div className="w-28 h-28 rounded-full border border-gold/30 overflow-hidden bg-void/60 flex items-center justify-center"
               data-testid="account-avatar">
            {avatarFullUrl
              ? <img src={avatarFullUrl} alt="avatar" className="w-full h-full object-cover"/>
              : <UserIcon className="w-12 h-12 text-mist/50"/>}
          </div>
          <input type="file" ref={fileRef} accept="image/png,image/jpeg,image/webp"
                 onChange={onAvatarPicked} className="hidden"
                 data-testid="account-avatar-input"/>
          <button onClick={() => fileRef.current?.click()} disabled={busy}
                  className="btn btn-ghost text-xs"
                  data-testid="account-avatar-upload-btn">
            <Camera className="w-3 h-3"/> {avatarFullUrl ? "Change" : "Upload"}
          </button>
          {tick === "avatar-saved" && <span className="text-[10px] text-arcane-light">Saved ✓</span>}
        </div>
        <div className="space-y-2">
          <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
            <Row label="Email" v={me.email}/>
            <Row label="Role" v={me.role}/>
            <Row label="Display name" v={me.name || "—"}/>
            <Row label="User ID" v={me.id?.slice(0, 8) + "…"} mono/>
          </div>
        </div>
      </div>

      {/* Game stats */}
      {stats && (
        <div className="card-mystic p-6 mt-4" data-testid="account-stats">
          <div className="label-ref flex items-center gap-2"><Award className="w-3 h-3"/> Game Stats</div>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
            <Stat label="Campaigns GM'd" v={stats.campaigns_owned} testid="stat-campaigns-owned"/>
            <Stat label="Campaigns Seated" v={stats.campaigns_seated} testid="stat-campaigns-seated"/>
            <Stat label="Characters" v={stats.characters} testid="stat-characters"/>
            <Stat label="XP Earned" v={stats.xp_total.toFixed(1)} testid="stat-xp-total"/>
            <Stat label="XP Unspent" v={stats.xp_unspent.toFixed(1)} testid="stat-xp-unspent"/>
          </div>
        </div>
      )}

      {/* Profile patch */}
      <div className="card-mystic p-6 mt-4" data-testid="account-profile-patch">
        <div className="label-ref flex items-center gap-2"><Scroll className="w-3 h-3"/> Profile</div>
        <div className="grid sm:grid-cols-2 gap-3 mt-3">
          <div>
            <label className="label-ref">Byline name</label>
            <input className="input" value={byline} onChange={(e) => setByline(e.target.value)}
                   placeholder="First Last (printed on PDF covers)"
                   data-testid="account-byline-input"/>
            <div className="text-[10px] text-mist/70 italic mt-1">Used on PDF chronicle covers + page footers.</div>
          </div>
        </div>
        <div className="mt-3">
          <label className="label-ref">Bio</label>
          <textarea className="input min-h-[70px]" value={bio} onChange={(e) => setBio(e.target.value)}
                    placeholder="A line or two players see in your profile card. Optional."
                    data-testid="account-bio-input"/>
        </div>
        <div className="flex justify-end gap-2 mt-3">
          {tick === "profile-saved" && <span className="text-[10px] text-arcane-light self-center">Saved ✓</span>}
          <button onClick={saveProfile} disabled={busy} className="btn btn-primary text-xs"
                  data-testid="account-profile-save">
            <Save className="w-3 h-3"/> {busy ? "Saving…" : "Save profile"}
          </button>
        </div>
      </div>

      {/* Password change */}
      <div className="card-mystic p-6 mt-4" data-testid="account-password-card">
        <div className="label-ref flex items-center gap-2"><Lock className="w-3 h-3"/> Password</div>
        <div className="grid sm:grid-cols-3 gap-3 mt-3">
          <div>
            <label className="label-ref">Current</label>
            <input type="password" className="input" value={pwCur} onChange={(e) => setPwCur(e.target.value)}
                   data-testid="account-pw-current"/>
          </div>
          <div>
            <label className="label-ref">New</label>
            <input type="password" className="input" value={pwNew} onChange={(e) => setPwNew(e.target.value)}
                   data-testid="account-pw-new"/>
          </div>
          <div>
            <label className="label-ref">Confirm</label>
            <input type="password" className="input" value={pwConfirm} onChange={(e) => setPwConfirm(e.target.value)}
                   data-testid="account-pw-confirm"/>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-3">
          {tick === "password-changed" && <span className="text-[10px] text-arcane-light self-center">Password changed ✓</span>}
          <button onClick={changePassword}
                  disabled={busy || !pwCur || !pwNew || !pwConfirm}
                  className="btn btn-primary text-xs"
                  data-testid="account-pw-save">
            <Lock className="w-3 h-3"/> Change password
          </button>
        </div>
      </div>
    </div>
  );
}

function Row({ label, v, mono }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="label-ref shrink-0 w-32">{label}</span>
      <span className={`text-parchment ${mono ? "font-mono text-xs" : ""}`}>{v}</span>
    </div>
  );
}

function Stat({ label, v, testid }) {
  return (
    <div className="border border-gold/15 rounded-sm py-2" data-testid={testid}>
      <div className="label-ref">{label}</div>
      <div className="font-display text-2xl text-gold-bright">{v}</div>
    </div>
  );
}
