import axios from "axios";
import React, { createContext, useContext, useEffect, useState } from "react";

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

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    if (data.access_token) localStorage.setItem("tg_token", data.access_token);
    setUser(data);
    return data;
  };
  const register = async (email, password, name, role = "player") => {
    const { data } = await api.post("/auth/register", { email, password, name, role });
    if (data.access_token) localStorage.setItem("tg_token", data.access_token);
    setUser(data);
    return data;
  };
  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    localStorage.removeItem("tg_token");
    setUser(false);
  };
  return (
    <AuthCtx.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
