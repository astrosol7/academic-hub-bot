import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

// ─── Types ───
export type UserRole = "admin" | "super_admin" | "operator" | "student" | "guest";

export interface AuthUser {
  username: string;
  role: UserRole;
  studentId?: string;
  telegramId?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isStudent: boolean;
  login: (accessToken: string, refreshToken: string, username: string) => void;
  logout: () => void;
  loading: boolean;
}

// ─── Constants ───
const ACCESS_TOKEN_KEY = "orbit_access_token";
const REFRESH_TOKEN_KEY = "orbit_refresh_token";
const USERNAME_KEY = "orbit_admin_username";

// ─── JWT Decode ───
function decodeJwtPayload(token: string | null): Record<string, unknown> | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    const bytes = Uint8Array.from(window.atob(padded), (c) => c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    return null;
  }
}

function resolveRole(payload: Record<string, unknown> | null): UserRole {
  const role = String(payload?.role || payload?.scope || "guest");
  if (["admin", "super_admin", "operator"].includes(role)) return role as UserRole;
  if (role === "student") return "student";
  return "guest";
}

// ─── Context ───
const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

// ─── Provider ───
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);
    if (token) {
      const payload = decodeJwtPayload(token);
      const role = resolveRole(payload);
      const username = window.localStorage.getItem(USERNAME_KEY) || "";
      setUser({ username, role });
    }
    setLoading(false);
  }, []);

  const login = useCallback((accessToken: string, refreshToken: string, username: string) => {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    window.localStorage.setItem(USERNAME_KEY, username);
    const payload = decodeJwtPayload(accessToken);
    const role = resolveRole(payload);
    setUser({ username, role });
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    window.localStorage.removeItem(USERNAME_KEY);
    setUser(null);
  }, []);

  // Listen for auth expiry events from api.ts
  useEffect(() => {
    const handler = () => logout();
    window.addEventListener("orbit:auth-expired", handler);
    return () => window.removeEventListener("orbit:auth-expired", handler);
  }, [logout]);

  const isAuthenticated = user !== null;
  const isAdmin = isAuthenticated && ["admin", "super_admin", "operator"].includes(user!.role);
  const isStudent = isAuthenticated && user!.role === "student";

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isAdmin, isStudent, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
