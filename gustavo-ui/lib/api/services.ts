import apiClient from "./client";
import type { ApiResponse, ServicesMap, Job } from "@/lib/types/api";

export const getServices = () =>
  apiClient.get<ApiResponse<ServicesMap>>("/services").then((r) => r.data);

export const getServiceStatus = (svc: string) =>
  apiClient.get<ApiResponse>(`/services/${svc}/status`).then((r) => r.data);

export const runService = (svc: string) =>
  apiClient.post<ApiResponse<{ job_id: string; status: string }>>(`/services/${svc}/run`).then((r) => r.data);

export const serviceAction = (svc: string, action: string) =>
  apiClient.post<ApiResponse>(`/services/${svc}/action`, { action }).then((r) => r.data);

export const getJob = (jobId: string) =>
  apiClient.get<ApiResponse<Job>>(`/services/jobs/${jobId}`).then((r) => r.data);
