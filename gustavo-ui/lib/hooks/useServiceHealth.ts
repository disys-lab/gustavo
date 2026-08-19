"use client";
import { useQuery } from "@tanstack/react-query";
import { getServices } from "@/lib/api/services";
import type { ServicesMap } from "@/lib/types/api";

// "syncer" is intentionally excluded — preserved for future re-enablement
const HEALTH_SERVICES: (keyof ServicesMap)[] = ["redis", "mongo", "registry", "manager"];

/**
 * Polls /api/services every 30s. Status is read-only and open to any
 * authenticated user (launch/stop/restart/remove stay admin-only).
 * Returns `allUp: true` if all 4 platform services are running, `false` if any is down,
 * `null` while loading or on error.
 */
export function useServiceHealth() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["services"],
    queryFn: getServices,
    refetchInterval: 30_000,
    staleTime: 25_000,
  });

  if (isLoading || isError || !data || data.error) return { allUp: null };

  const map = data.response as ServicesMap;
  if (!map || typeof map !== "object") return { allUp: null };

  const allUp = HEALTH_SERVICES.every((svc) => {
    const entry = map[svc];
    return entry && !entry.error;
  });
  return { allUp };
}
