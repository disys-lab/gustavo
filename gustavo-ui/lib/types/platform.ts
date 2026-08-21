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

export type ServiceName = "redis" | "mongo" | "registry" | "syncer" | "manager";

export interface AppConfig {
  docker_image: string;
  starting_ports?: Array<{ [key: string]: number }>;
  env_vars?: Record<string, string>;
  volumes?: string[];
  network_mode?: string;
  devices?: string[];
  privileged?: boolean;
  running?: boolean;
  [key: string]: unknown;
}
