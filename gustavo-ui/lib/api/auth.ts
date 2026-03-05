import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";

export const signIn = (userId: string, userToken: string) =>
  apiClient
    .post<ApiResponse<{ idToken: string; localId: string }>>("/auth/token", {
      user_id: userId,
      user_token: userToken,
    })
    .then((r) => r.data);
