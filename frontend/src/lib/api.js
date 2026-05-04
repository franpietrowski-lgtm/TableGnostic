import axios from "axios";
import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from "react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND}/api`;

// Bearer-token based auth (more portable than cookies across browsers/incognito).
// Cookies are still set by backend and will silently work if present; we don't depend on them.
export const api = axios.create({ baseURL: API, withCredentials: false });

// Attach bearer token fallback (cookie is primary)
api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("tg_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

function formatApiErrorDetail(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}
export { formatApiErrorDetail };

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null=checking, false=anon, {..}=user
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      // Skip /me call if we have no token at all — avoids noisy 401 in console.
      const t = localStorage.getItem("tg_token");
      if (!t) { setUser(false); setLoading(false); return; }
      try {
        const { data } = await api.get("/auth/me");
        setUser(data);
      } catch {
        localStorage.removeItem("tg_token");
        setUser(false);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    if (data.access_token) localStorage.setItem("tg_token", data.access_token);
    setUser(data);
    return data;
  }, []);
  const register = useCallback(async (email, password, name, role = "player") => {
    const { data } = await api.post("/auth/register", { email, password, name, role });
    if (data.access_token) localStorage.setItem("tg_token", data.access_token);
    setUser(data);
    return data;
  }, []);
  const logout = useCallback(async () => {
    try { await api.post("/auth/logout"); } catch (_) { /* swallow */ }
    localStorage.removeItem("tg_token");
    setUser(false);
  }, []);
  const updateProfile = useCallback(async (patch) => {
    const { data } = await api.patch("/auth/me", patch);
    setUser(data);
    return data;
  }, []);
  // V6.24 — memoize the context value. The previous inline object
  // literal created a fresh identity on every AuthProvider render
  // and rippled remounts through deeply-wrapped consumers (e.g.,
  // dynamic form fields), contributing to input focus loss when any
  // API call failed (deployment edge-case). Stable identity fixes it.
  const ctxValue = useMemo(
    () => ({ user, login, register, logout, loading, updateProfile }),
    [user, loading, login, register, logout, updateProfile],
  );
  return (
    <AuthCtx.Provider value={ctxValue}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
