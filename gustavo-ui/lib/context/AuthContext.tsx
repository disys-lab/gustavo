"use client";
import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { signIn } from "@/lib/api/auth";

interface AuthContextValue {
  token: string | null;
  userId: string | null;
  isAuthenticated: boolean;
  login: (userId: string, userToken: string) => Promise<{ error: boolean; message?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const COOKIE_NAME = "gustavo_token";
const COOKIE_MAX_AGE = 3600;

function setAuthCookie(token: string) {
  document.cookie = `${COOKIE_NAME}=${token}; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`;
}

function clearAuthCookie() {
  document.cookie = `${COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax`;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  // null = not yet fetched from server
  const [authEnabled, setAuthEnabled] = useState<boolean | null>(null);

  // Fetch runtime auth status from the API so AUTH_ENABLED can be toggled
  // via env var without a rebuild (NEXT_PUBLIC_AUTH_ENABLED is baked and ignored here).
  useEffect(() => {
    fetch("/api/auth/status")
      .then((r) => r.json())
      .then((data) => setAuthEnabled(data.auth_enabled === true))
      .catch(() => setAuthEnabled(true)); // fail-safe: assume auth required
  }, []);

  // Hydrate token from localStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedToken = localStorage.getItem("gustavo_token");
    const storedUid = localStorage.getItem("gustavo_uid");
    if (storedToken) {
      setToken(storedToken);
      setAuthCookie(storedToken);
    }
    if (storedUid) setUserId(storedUid);
  }, []);

  const login = async (userId: string, userToken: string) => {
    try {
      const res = await signIn(userId, userToken);
      if (res.error) {
        return { error: true, message: String(res.response) };
      }
      const { idToken, localId } = res.response as { idToken: string; localId: string };
      localStorage.setItem("gustavo_token", idToken);
      localStorage.setItem("gustavo_uid", localId ?? "");
      setAuthCookie(idToken);
      setToken(idToken);
      setUserId(localId ?? null);
      return { error: false };
    } catch (exc) {
      return { error: true, message: String(exc) };
    }
  };

  const logout = () => {
    localStorage.removeItem("gustavo_token");
    localStorage.removeItem("gustavo_uid");
    clearAuthCookie();
    setToken(null);
    setUserId(null);
    if (authEnabled) {
      window.location.href = "/login";
    }
  };

  // While auth status is loading (null), treat as not authenticated.
  // Once loaded: if auth is disabled, everyone is authenticated; otherwise require a token.
  const isAuthenticated = authEnabled === false || (authEnabled === true && !!token);

  return (
    <AuthContext.Provider value={{ token, userId, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
