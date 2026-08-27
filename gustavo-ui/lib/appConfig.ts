import type { AppFormValues } from "@/components/apps/AppForm";

/**
 * Converts a raw app config dict (as returned by the Manager, or parsed
 * from an uploaded YAML file) into the AppForm's field shape. Shared
 * between the edit page (loading an existing app) and the create page's
 * YAML upload (prefilling a new app) so both stay in sync.
 */
export function parseAppConfig(config: Record<string, unknown>): Partial<AppFormValues> {
  return {
    docker_image: (config.docker_image as string) ?? "",
    env_vars: Object.entries((config.env_vars as Record<string, string>) ?? {}).map(([key, value]) => ({ key, value })),
    ports: ((config.starting_ports as Record<string, number>[]) ?? []).map((p) => {
      const [host, container] = Object.entries(p)[0] ?? [0, 0];
      return { host: Number(host), container: Number(container) };
    }),
    volumes: ((config.volumes as string[]) ?? []).map((v) => {
      const [host, container] = v.split(":") as [string, string?];
      return { host, container: container ?? "" };
    }),
    network_mode: (config.network_mode as string) ?? "bridge",
    running: (config.running as boolean) ?? true,
    privileged: (config.privileged as boolean) ?? false,
    command: ((config.command as string[]) ?? []).map((value) => ({ value })),
    shm_size: (config.shm_size as string) ?? "",
  };
}
