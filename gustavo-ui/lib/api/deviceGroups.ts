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
//
// reporter switches worker status reporting to gustavo-reporter's REST API
// instead of direct Redis writes - mutually exclusive with the default
// Redis reporting fields, see nebula_auth.build_worker_env.
//
// check_in_time is NEBULA_MANAGER_CHECK_IN_TIME (seconds) - how often the
// worker polls the Nebula manager and reports status; the same loop tick
// drives both, there's no separate report-only timer.
//
// include_registry, when false, omits registry host/auth entirely - for a
// remote/external worker that can't reach this platform's own registry.
// Without this, a worker whose config still includes registry auth it can't
// reach used to crash outright at startup; gustavo-worker's registry_login
// is now non-fatal on failure too, but omitting the fields is still the
// clean way to tell a remote worker not to attempt it at all.
// public_endpoints, when true, bakes in this platform's PUBLIC_MANAGER_HOST/
// PORT (and PUBLIC_REPORTER_HOST/PORT if reporter is also true) instead of
// the internal LAN addresses - for a worker reaching this platform from
// outside (e.g. through a Cloudflare Tunnel). Only meaningful if
// PUBLIC_ENDPOINTS_ENABLED is also on in Settings.
export const downloadWorkerEnv = (
  name: string, gpu = false, reporter = false, check_in_time = 60, include_registry = true,
  public_endpoints = false
) =>
  apiClient
    .get(`/device-groups/${name}/worker-env`, {
      responseType: "text", params: { gpu, reporter, check_in_time, include_registry, public_endpoints },
    })
    .then((r) => r.data as string);

export const downloadWorkerCompose = (
  name: string, gpu = false, reporter = false, check_in_time = 60, include_registry = true,
  public_endpoints = false
) =>
  apiClient
    .get(`/device-groups/${name}/worker-compose`, {
      responseType: "text", params: { gpu, reporter, check_in_time, include_registry, public_endpoints },
    })
    .then((r) => r.data as string);

export const downloadWorkerScript = (
  name: string, gpu = false, reporter = false, check_in_time = 60, include_registry = true,
  public_endpoints = false
) =>
  apiClient
    .get(`/device-groups/${name}/worker-script`, {
      responseType: "text", params: { gpu, reporter, check_in_time, include_registry, public_endpoints },
    })
    .then((r) => r.data as string);

export const downloadWorkerScriptWindows = (
  name: string, gpu = false, reporter = false, check_in_time = 60, include_registry = true,
  public_endpoints = false
) =>
  apiClient
    .get(`/device-groups/${name}/worker-script-windows`, {
      responseType: "text", params: { gpu, reporter, check_in_time, include_registry, public_endpoints },
    })
    .then((r) => r.data as string);
