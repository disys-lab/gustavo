import apiClient from "./client";
import type { ApiResponse, HostsResponse } from "@/lib/types/api";

export const getHosts = (device_group = "all", host = "all") =>
  apiClient
    .get<HostsResponse>("/monitoring/hosts", { params: { device_group, host } })
    .then((r) => r.data);

export const getVitals = (device_group = "all", host = "all") =>
  apiClient
    .get<ApiResponse>("/monitoring/vitals", { params: { device_group, host } })
    .then((r) => r.data);

export const getContainers = (device_group = "all", host = "all") =>
  apiClient
    .get<ApiResponse>("/monitoring/containers", { params: { device_group, host } })
    .then((r) => r.data);
