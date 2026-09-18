// Platform configuration keys — mirrors config_store.py DEFAULTS
export interface PlatformConfig {
  // Manager
  MANAGER_HOST: string;
  MANAGER_PORT: string;
  MANAGER_NMODE: string;
  MANAGER_IMAGE: string;
  CACHE_EXPIRE_TIME: string;
  // Nebula credentials
  NEBULA_USERNAME: string;
  NEBULA_PASSWORD: string;
  NEBULA_AUTH_TOKEN: string;
  NEBULA_PROTOCOL: string;
  // Registry
  REGISTRY_HOST: string;
  REGISTRY_PORT: string;
  REGISTRY_IP_DISABLED: boolean;
  REGISTRY_IMAGE: string;
  REGISTRY_BKP_DIR: string;
  REGISTRY_DATA_PATH: string;
  REGISTRY_BIND_LOCALHOST: boolean;
  REGISTRY_CONTAINER_PORT: string;
  // Syncer
  SYNCER_IMAGE: string;
  SYNCER_NMODE: string;
  DREGSY_CONFIG_FILE_PATH: string;
  DREGSY_MAPPING_FILE_PATH: string;
  // Reporter
  REPORTER_IMAGE: string;
  REPORTER_HOST: string;
  REPORTER_PORT: string;
  GUSTAVO_API_HOST: string;
  GUSTAVO_API_PORT: string;
  // Public Facing Endpoints
  PUBLIC_ENDPOINTS_ENABLED: boolean;
  PUBLIC_MANAGER_HOST: string;
  PUBLIC_MANAGER_PORT: string;
  PUBLIC_REPORTER_HOST: string;
  PUBLIC_REPORTER_PORT: string;
  PUBLIC_GUSTAVO_HOST: string;
  PUBLIC_GUSTAVO_PORT: string;
  PUBLIC_REGISTRY_ENABLED: boolean;
  PUBLIC_REGISTRY_HOST: string;
  PUBLIC_REGISTRY_PORT: string;
  EXTERNAL_USER_GROUPS: string[];
  // Redis
  REDIS_HOST: string;
  REDIS_PORT: string;
  REDIS_IP_DISABLED: boolean;
  REDIS_AUTH_TOKEN: string;
  REDIS_IMAGE: string;
  REDIS_BKP_DIR: string;
  // MongoDB
  MONGO_HOST: string;
  MONGO_PORT: string;
  MONGO_IP_DISABLED: boolean;
  MONGO_USERNAME: string;
  MONGO_PASSWORD: string;
  MONGO_CERTIFICATE_FOLDER_PATH: string;
  MONGO_IMAGE: string;
  // Worker
  WORKER_NMODE: string;
}

export type ServiceName = "redis" | "mongo" | "registry" | "syncer" | "manager" | "reporter";

export interface AppConfig {
  docker_image: string;
  starting_ports?: Array<{ [key: string]: number }>;
  env_vars?: Record<string, string>;
  volumes?: string[];
  network_mode?: string;
  devices?: string[];
  privileged?: boolean;
  running?: boolean;
  command?: string[];
  shm_size?: string;
  [key: string]: unknown;
}

// Near-identical to AppConfig, minus starting_ports/network_mode (cron
// jobs are one-shot batch containers, not traffic-serving services) plus
// `schedule` (a cron expression, e.g. "*/15 * * * *" - fed straight into
// croniter on the worker side). `command`/`shm_size` were silently
// dropped by Nebula's own cron_job schema (create_cron_job/
// mongo_add_cron_job never read them, unlike the equivalent app fields) -
// fixed in gustavo_manager (disys-lab/gustavo_manager#13, mirroring the
// same fix already shipped for apps). Nothing here or elsewhere in this
// repo needed to change - gustavo's own create/update calls already sent
// both fields all along; only the Manager's own persistence layer was
// dropping them.
export interface CronJobConfig {
  docker_image: string;
  schedule: string;
  env_vars?: Record<string, string>;
  volumes?: string[];
  devices?: string[];
  privileged?: boolean;
  running?: boolean;
  networks?: string[];
  command?: string[];
  shm_size?: string;
  [key: string]: unknown;
}
