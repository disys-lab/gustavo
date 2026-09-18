/**
 * API functions for the /api/cron-jobs endpoints.
 *
 * Structural mirror of lib/api/apps.ts. No cron-job-specific YAML parse
 * endpoint - apps.py's /apps/yaml/parse is a generic YAML-to-dict parser
 * with zero app-specific behavior, so it's reused as-is here rather than
 * duplicated. No defaults endpoint either: apps' /apps/defaults exists to
 * pre-fill Redis/Manager env vars for status reporting, which cron jobs
 * don't do at all (fire-and-forget, no ongoing reporting) - there's
 * nothing equivalent to pre-fill.
 */
import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";
import type { CronJobConfig } from "@/lib/types/platform";

export const listCronJobs = () =>
  apiClient.get<ApiResponse>("/cron-jobs").then((r) => r.data);

export const getCronJob = (name: string) =>
  apiClient.get<ApiResponse>(`/cron-jobs/${name}`).then((r) => r.data);

export const createCronJob = (name: string, config: CronJobConfig, device_groups: string[] = [], owner_group?: string) =>
  apiClient.post<ApiResponse>("/cron-jobs", { name, config, device_groups, owner_group }).then((r) => r.data);

export const updateCronJob = (name: string, config: CronJobConfig) =>
  apiClient.put<ApiResponse>(`/cron-jobs/${name}`, { config }).then((r) => r.data);

export const deleteCronJob = (name: string) =>
  apiClient.delete<ApiResponse>(`/cron-jobs/${name}`).then((r) => r.data);

export const parseYaml = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return apiClient.post<ApiResponse>("/apps/yaml/parse", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

export const exportCronJobYaml = (name: string) =>
  apiClient.get(`/cron-jobs/${name}/yaml`, { responseType: "text" }).then((r) => r.data as string);
