import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";

export const listDeviceGroups = () =>
  apiClient.get<ApiResponse>("/device-groups").then((r) => r.data);

export const getDeviceGroup = (name: string) =>
  apiClient.get<ApiResponse>(`/device-groups/${name}`).then((r) => r.data);

export const createDeviceGroup = (name: string, apps: string[] = [], owner_group?: string) =>
  apiClient.post<ApiResponse>("/device-groups", { name, apps, owner_group }).then((r) => r.data);

export const updateDeviceGroup = (name: string, apps: string[]) =>
  apiClient.put<ApiResponse>(`/device-groups/${name}`, { apps }).then((r) => r.data);

export const deleteDeviceGroup = (name: string) =>
  apiClient.delete<ApiResponse>(`/device-groups/${name}`).then((r) => r.data);

export const addAppsToDeviceGroup = (name: string, apps: string[]) =>
  apiClient.post<ApiResponse>(`/device-groups/${name}/apps/add`, { apps }).then((r) => r.data);

export const removeAppsFromDeviceGroup = (name: string, apps: string[]) =>
  apiClient.post<ApiResponse>(`/device-groups/${name}/apps/remove`, { apps }).then((r) => r.data);

// Three independent worker-launch modalities — the user picks one. Each
// returns a self-contained artifact; downloading one has no effect on the
// others (see nebula_auth.build_worker_env's docstring for why).
//
// gpu grants every container this worker launches GPU access (GPU_ENABLED) -
// only pass true for a device group whose hardware actually has a GPU
// nvidia-container-toolkit can expose.
export const downloadWorkerEnv = (name: string, gpu = false) =>
  apiClient
    .get(`/device-groups/${name}/worker-env`, { responseType: "text", params: { gpu } })
    .then((r) => r.data as string);

export const downloadWorkerCompose = (name: string, gpu = false) =>
  apiClient
    .get(`/device-groups/${name}/worker-compose`, { responseType: "text", params: { gpu } })
    .then((r) => r.data as string);

export const downloadWorkerScript = (name: string, gpu = false) =>
  apiClient
    .get(`/device-groups/${name}/worker-script`, { responseType: "text", params: { gpu } })
    .then((r) => r.data as string);

export const downloadWorkerScriptWindows = (name: string, gpu = false) =>
  apiClient
    .get(`/device-groups/${name}/worker-script-windows`, { responseType: "text", params: { gpu } })
    .then((r) => r.data as string);
