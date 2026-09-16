"use client";
import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { login as loginRequest, signInFirebase } from "@/lib/api/auth";
import { getMyGroups } from "@/lib/api/users";

interface AuthContextValue {
  token: string | null;
  username: string | null;
  isAdmin: boolean;
  isAuthenticated: boolean;
  firebaseEnabled: boolean;
  // The caller's own Nebula group memberships, fetched fresh per session
  // (not a login-time snapshot) since grants can change mid-session. Combine
  // with ConfigContext's EXTERNAL_USER_GROUPS to determine external status -
  // kept as raw groups here rather than a derived isExternal boolean, since
  // AuthContext has no access to platform config.
  groups: string[];
  login: (credential: string) => Promise<{ error: boolean; message?: string }>;
  loginFirebase: (userId: string, userToken: string) => Promise<{ error: boolean; message?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const COOKIE_NAME = "gustavo_token";
// Matches the backend's default GUSTAVO_SESSION_TTL (12h) — keep in sync so
// the cookie middleware relies on doesn't expire before the session itself.
const COOKIE_MAX_AGE = 12 * 3600;

function setAuthCookie(token: string) {
  document.cookie = `${COOKIE_NAME}=${token}; path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`;
}

function clearAuthCookie() {
  document.cookie = `${COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax`;
}

function persistSession(token: string, username: string, isAdmin: boolean) {
  localStorage.setItem("gustavo_token", token);
  localStorage.setItem("gustavo_username", username);
  localStorage.setItem("gustavo_is_admin", isAdmin ? "1" : "0");
  setAuthCookie(token);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  // null = not yet fetched from server
  const [authEnabled, setAuthEnabled] = useState<boolean | null>(null);
  const [firebaseEnabled, setFirebaseEnabled] = useState(false);
  const [groups, setGroups] = useState<string[]>([]);

  // Fetch runtime auth status from the API so it can be toggled via env var
  // without a rebuild (NEXT_PUBLIC_AUTH_ENABLED is baked and ignored here).
  useEffect(() => {
    fetch("/api/auth/status")
      .then((r) => r.json())
      .then((data) => {
        setAuthEnabled(data.auth_enabled === true);
        setFirebaseEnabled(data.firebase_enabled === true);
      })
      .catch(() => setAuthEnabled(true)); // fail-safe: assume auth required
  }, []);

  // Hydrate session from localStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedToken = localStorage.getItem("gustavo_token");
    const storedUsername = localStorage.getItem("gustavo_username");
    const storedIsAdmin = localStorage.getItem("gustavo_is_admin");
    if (storedToken) {
      setToken(storedToken);
      setAuthCookie(storedToken);
    }
    if (storedUsername) setUsername(storedUsername);
    setIsAdmin(storedIsAdmin === "1");
  }, []);

  // Fetch fresh (not cached at login) whenever the session becomes usable,
  // so a mid-session grant change is picked up on the next mount/reload.
  useEffect(() => {
    if (authEnabled === false || token) {
      getMyGroups()
        .then((res) => setGroups(!res.error ? res.response.groups : []))
        .catch(() => setGroups([]));
    } else {
      setGroups([]);
    }
  }, [authEnabled, token]);

  const login = async (credential: string) => {
    try {
      const res = await loginRequest(credential);
      if (res.error) {
        return { error: true, message: String(res.response) };
      }
      const { token: newToken, username: newUsername, is_admin } = res.response;
      persistSession(newToken, newUsername, is_admin);
      setToken(newToken);
      setUsername(newUsername);
      setIsAdmin(is_admin);
      return { error: false };
    } catch (exc) {
      return { error: true, message: String(exc) };
    }
  };

  const loginFirebase = async (userId: string, userToken: string) => {
    try {
      const res = await signInFirebase(userId, userToken);
      if (res.error) {
        return { error: true, message: String(res.response) };
      }
      const { token: newToken, username: newUsername, is_admin } = res.response;
      persistSession(newToken, newUsername, is_admin);
      setToken(newToken);
      setUsername(newUsername);
      setIsAdmin(is_admin);
      return { error: false };
    } catch (exc) {
      return { error: true, message: String(exc) };
    }
  };

  const logout = () => {
    localStorage.removeItem("gustavo_token");
    localStorage.removeItem("gustavo_username");
    localStorage.removeItem("gustavo_is_admin");
    clearAuthCookie();
    setToken(null);
    setUsername(null);
    setIsAdmin(false);
    setGroups([]);
    if (authEnabled) {
      window.location.href = "/login";
    }
  };

  // While auth status is loading (null), treat as not authenticated.
  // Once loaded: if auth is disabled, everyone is authenticated; otherwise require a token.
  const isAuthenticated = authEnabled === false || (authEnabled === true && !!token);

  // When auth is disabled, isAuthenticated short-circuits to true without ever
  // calling /login - so the `isAdmin` state (only ever set from a login
  // response) never gets populated and stays stuck at its useState(false)
  // default, hiding every admin-gated control even though the backend
  // (verify_firebase_token's AUTH_ENABLED=false branch) treats every request
  // as admin. Mirror that here instead of trusting the un-derived state.
  const effectiveIsAdmin = authEnabled === false ? true : isAdmin;

  return (
    <AuthContext.Provider
      value={{ token, username, isAdmin: effectiveIsAdmin, isAuthenticated, firebaseEnabled, groups, login, loginFirebase, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
