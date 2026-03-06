import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";

export const listDeviceGroups = () =>
  apiClient.get<ApiResponse>("/device-groups").then((r) => r.data);

export const getDeviceGroup = (name: string) =>
  apiClient.get<ApiResponse>(`/device-groups/${name}`).then((r) => r.data);

export const createDeviceGroup = (name: string, apps: string[] = []) =>
  apiClient.post<ApiResponse>("/device-groups", { name, apps }).then((r) => r.data);

export const updateDeviceGroup = (name: string, apps: string[]) =>
  apiClient.put<ApiResponse>(`/device-groups/${name}`, { apps }).then((r) => r.data);

export const deleteDeviceGroup = (name: string) =>
  apiClient.delete<ApiResponse>(`/device-groups/${name}`).then((r) => r.data);

export const addAppsToDeviceGroup = (name: string, apps: string[]) =>
  apiClient.post<ApiResponse>(`/device-groups/${name}/apps/add`, { apps }).then((r) => r.data);

export const removeAppsFromDeviceGroup = (name: string, apps: string[]) =>
  apiClient.post<ApiResponse>(`/device-groups/${name}/apps/remove`, { apps }).then((r) => r.data);
