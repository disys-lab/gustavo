import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";

export interface AuthStatus {
  auth_enabled: boolean;
  nebula_enabled: boolean;
  firebase_enabled: boolean;
}

export interface LoginResponse {
  token: string;
  username: string;
  is_admin: boolean;
}

export const getAuthStatus = () =>
  apiClient.get<AuthStatus>("/auth/status").then((r) => r.data);

// The one unified login: credential is "identifier:secret" — either the
// break-glass admin (NEBULA_USERNAME:NEBULA_PASSWORD) or a regular
// "username:token" issued from the Users page.
export const login = (credential: string) =>
  apiClient
    .post<ApiResponse<LoginResponse>>("/auth/login", { credential })
    .then((r) => r.data);

export const signInFirebase = (userId: string, userToken: string) =>
  apiClient
    .post<ApiResponse<LoginResponse>>("/auth/token", {
      user_id: userId,
      user_token: userToken,
    })
    .then((r) => r.data);
