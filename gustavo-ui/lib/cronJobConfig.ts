import type { CronJobFormValues } from "@/components/cron-jobs/CronJobForm";

/**
 * Converts a raw cron job config dict (as returned by the Manager, or
 * parsed from an uploaded YAML file) into the CronJobForm's field shape.
 * Mirrors lib/appConfig.ts's parseAppConfig - shared between the edit
 * page (loading an existing cron job) and the create page's YAML upload
 * (prefilling a new cron job) so both stay in sync.
 */
export function parseCronJobConfig(config: Record<string, unknown>): Partial<CronJobFormValues> {
  return {
    docker_image: (config.docker_image as string) ?? "",
    schedule: (config.schedule as string) ?? "",
    env_vars: Object.entries((config.env_vars as Record<string, string>) ?? {}).map(([key, value]) => ({ key, value })),
    volumes: ((config.volumes as string[]) ?? []).map((v) => {
      const [host, container] = v.split(":") as [string, string?];
      return { host, container: container ?? "" };
    }),
    networks: ((config.networks as string[]) ?? ["nebula"]).join(","),
    running: (config.running as boolean) ?? true,
    privileged: (config.privileged as boolean) ?? false,
    command: ((config.command as string[]) ?? []).map((value) => ({ value })),
    shm_size: (config.shm_size as string) ?? "",
  };
}
