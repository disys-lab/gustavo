/**
 * API functions for the /api/services endpoints.
 *
 * Services managed: redis, mongo, registry, syncer, manager.
 * Long-running operations (run) return a job_id; poll with getJob().
 */
import apiClient from "./client";
import type { ApiResponse, ServicesMap, Job } from "@/lib/types/api";

/** Return the status of all 5 platform services. */
export const getServices = () =>
  apiClient.get<ApiResponse<ServicesMap>>("/services").then((r) => r.data);

/** Return the status of a single service. */
export const getServiceStatus = (svc: string) =>
  apiClient.get<ApiResponse>(`/services/${svc}/status`).then((r) => r.data);

/** Launch a service in the background. Returns a job_id to poll. */
export const runService = (svc: string) =>
  apiClient.post<ApiResponse<{ job_id: string; status: string }>>(`/services/${svc}/run`).then((r) => r.data);

/** Perform a lifecycle action (stop | start | kill | remove | restart) on a service. */
export const serviceAction = (svc: string, action: string) =>
  apiClient.post<ApiResponse>(`/services/${svc}/action`, { action }).then((r) => r.data);

/** Poll the result of a background job by its ID. */
export const getJob = (jobId: string) =>
  apiClient.get<ApiResponse<Job>>(`/services/jobs/${jobId}`).then((r) => r.data);
