import apiClient from "./client";
import type { ApiResponse, WorkerDirectoryEntry } from "@/lib/types/api";

export const listWorkerDirectory = () =>
  apiClient.get<ApiResponse<WorkerDirectoryEntry[]>>("/worker-directory").then((r) => r.data);

export const deleteWorkerDirectoryEntry = (deviceGroup: string, nodeId: string) =>
  apiClient.delete<ApiResponse>(`/worker-directory/${deviceGroup}/${nodeId}`).then((r) => r.data);
