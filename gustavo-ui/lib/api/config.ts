import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";
import type { PlatformConfig } from "@/lib/types/platform";

export const getConfig = () =>
  apiClient.get<ApiResponse<PlatformConfig>>("/config").then((r) => r.data);

export const updateConfig = (partial: Partial<PlatformConfig>) =>
  apiClient.post<ApiResponse<PlatformConfig>>("/config", partial).then((r) => r.data);

export const uploadConfig = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return apiClient.post<ApiResponse>("/config/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

export const downloadConfig = () =>
  apiClient.get("/config/download", { responseType: "text" }).then((r) => r.data as string);

// Scoped to the caller's own Nebula identity — safe for any authenticated
// user, admin or not (see gustavo/api/routers/config.py).
export const downloadWorkerConfig = () =>
  apiClient.get("/config/worker-download", { responseType: "text" }).then((r) => r.data as string);
