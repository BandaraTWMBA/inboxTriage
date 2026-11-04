import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, USE_MOCK } from "../api/index.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setUser(await api.getMe());
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener("it:unauthorized", onUnauthorized);
    return () => window.removeEventListener("it:unauthorized", onUnauthorized);
  }, []);

  const login = useCallback(async () => {
    if (USE_MOCK) {
      await api.mockLogin();
      await refresh();
    } else {
      // Full-page redirect: the backend starts the Google OAuth flow and sets the session cookie.
      window.location.href = api.loginUrl();
    }
  }, [refresh]);

  const logout = useCallback(async () => {
    try { await api.logout(); } finally { setUser(null); }
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
