export interface NebulaUser {
  username: string;
  groups: string[];
  is_admin: boolean;
}

export interface UserGroup {
  name: string;
  group_members: string[];
  apps: Record<string, "ro" | "rw">;
  device_groups: Record<string, "ro" | "rw">;
  admin: boolean;
  pruning_allowed: boolean;
  cron_jobs: Record<string, "ro" | "rw">;
}

export interface CredentialResponse {
  username: string;
  credential: string;
  warning?: string;
}
