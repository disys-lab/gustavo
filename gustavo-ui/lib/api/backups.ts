import apiClient from "./client";
import type { ApiResponse, BackupEntry } from "@/lib/types/api";

// Redis
export const listRedisBackups = () =>
  apiClient.get<ApiResponse<BackupEntry[]>>("/backups/redis").then((r) => r.data);

export const createRedisBackup = () =>
  apiClient.post<ApiResponse<{ job_id: string }>>("/backups/redis/create").then((r) => r.data);

export const restoreRedisBackup = (filename: string) =>
  apiClient.post<ApiResponse<{ job_id: string }>>(`/backups/redis/restore/${filename}`).then((r) => r.data);

export const deleteRedisBackup = (filename: string) =>
  apiClient.delete<ApiResponse>(`/backups/redis/${filename}`).then((r) => r.data);

// Registry
export const listRegistryBackups = () =>
  apiClient.get<ApiResponse<BackupEntry[]>>("/backups/registry").then((r) => r.data);

export const createRegistryBackup = () =>
  apiClient.post<ApiResponse<{ job_id: string }>>("/backups/registry/create").then((r) => r.data);

export const restoreRegistryBackup = (dirname: string) =>
  apiClient.post<ApiResponse<{ job_id: string }>>(`/backups/registry/restore/${dirname}`).then((r) => r.data);

export const deleteRegistryBackup = (dirname: string) =>
  apiClient.delete<ApiResponse>(`/backups/registry/${dirname}`).then((r) => r.data);
