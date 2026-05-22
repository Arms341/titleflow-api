// JARVIS App — Auth Context  v2.0.0
// Locked template — JARVIS frontend auth.
// Provides useAuth() hook with user, login, logout, register, isAdmin helpers.
// Token stored in localStorage; /auth/me fetched on mount to rehydrate state.
//
// v2.0.0: DEBT #22 fix — isAuthenticated uses user.is_active (boolean)
//         not user.status === 'active'.
import React, {
  createContext, useContext, useState, useEffect, useCallback,
  type ReactNode,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { apiLogin, apiRegister, apiGetMe, TOKEN_STORAGE_KEY } from '@/lib/api';
import type { User } from '@/types';

// ── Context shape ─────────────────────────────────────────────────────────────

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
  login: (username: string, password: string) => Promise<User>;
  register: (data: Record<string, unknown>) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const qc = useQueryClient();

  // Rehydrate on mount if token exists
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) { setIsLoading(false); return; }
    apiGetMe()
      .then(setUser)
      .catch(() => localStorage.removeItem(TOKEN_STORAGE_KEY))
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<User> => {
    const { access_token } = await apiLogin(username, password);
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
    const me = await apiGetMe();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (data: Record<string, unknown>): Promise<void> => {
    await apiRegister(data);
    // Registration requires admin approval — do NOT auto-login
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setUser(null);
    qc.clear(); // Clear all cached query data on logout
    window.location.href = '/login';
  }, [qc]);

  const refreshUser = useCallback(async () => {
    const me = await apiGetMe();
    setUser(me);
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user && user.is_active !== false,
      isLoading,
      isAdmin: user?.role === 'admin',
      login,
      register,
      logout,
      refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default AuthProvider;
