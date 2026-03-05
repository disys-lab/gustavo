// Core API response contract matching gustavo.py backend
export interface ApiResponse<T = string | Record<string, unknown>> {
  error: boolean;
  response: T;
}

export interface ServiceStatus {
  error: boolean;
  response: string;
}

export interface ServicesMap {
  redis: ServiceStatus;
  mongo: ServiceStatus;
  registry: ServiceStatus;
  syncer: ServiceStatus;
  manager: ServiceStatus;
}

export interface Job {
  id: string;
  status: "running" | "done" | "error";
  result: ApiResponse | null;
  error: string | null;
  service?: string;
  action?: string;
  type?: string;
  filename?: string;
}

export interface BackupEntry {
  filename: string;
  timestamp: string;
}

export interface VitalsData {
  host?: string;
  timestamp?: number;
  cpu_percent?: number;
  cpu_cores?: number;
  memory_mb?: { total: number; used: number; free: number; available: number };
  disk_mb?: { total: number; used: number; free: number };
}

export interface ContainerMetrics {
  name: string;
  cpu_percent: number;
  memory_mb: number;
  memory_limit_mb: number;
  memory_percent: number;
}

export interface MonitoringEvent {
  vitals: VitalsData;
  containers: ContainerMetrics[];
}

export interface HostsResponse {
  host_queried: string;
  device_group_queried: string;
  response: Record<string, string[]> | boolean | string[];
}
