/**
 * API functions for the /api/apps endpoints.
 *
 * Covers application CRUD, registry image queries, YAML import/export,
 * and server-side default env-var fetching.
 */
import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";
import type { AppConfig } from "@/lib/types/platform";

export const listApps = () =>
  apiClient.get<ApiResponse>("/apps").then((r) => r.data);

export const getApp = (name: string) =>
  apiClient.get<ApiResponse>(`/apps/${name}`).then((r) => r.data);

export const createApp = (name: string, config: AppConfig, device_groups: string[] = [], owner_group?: string) =>
  apiClient.post<ApiResponse>("/apps", { name, config, device_groups, owner_group }).then((r) => r.data);

export const updateApp = (name: string, config: AppConfig) =>
  apiClient.put<ApiResponse>(`/apps/${name}`, { config }).then((r) => r.data);

export const deleteApp = (name: string) =>
  apiClient.delete<ApiResponse>(`/apps/${name}`).then((r) => r.data);

export const getRegistryImages = () =>
  apiClient.get<ApiResponse>("/apps/registry/images").then((r) => r.data);

export const getAppDefaults = () =>
  apiClient.get<ApiResponse>("/apps/defaults").then((r) => r.data);

export const parseYaml = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return apiClient.post<ApiResponse>("/apps/yaml/parse", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

export const exportAppYaml = (name: string) =>
  apiClient.get(`/apps/${name}/yaml`, { responseType: "text" }).then((r) => r.data as string);
