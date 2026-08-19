"use client";
import { useQuery } from "@tanstack/react-query";
import { getServices } from "@/lib/api/services";
import { useAuth } from "@/lib/context/AuthContext";
import type { ServicesMap } from "@/lib/types/api";

// "syncer" is intentionally excluded — preserved for future re-enablement
const HEALTH_SERVICES: (keyof ServicesMap)[] = ["redis", "mongo", "registry", "manager"];

/**
 * Polls /api/services every 30s. Admin-only backend route, so this is a
 * no-op (and never fires the request) for non-admin sessions.
 * Returns `allUp: true` if all 4 platform services are running, `false` if any is down,
 * `null` while loading, on error, or when the caller isn't an admin.
 */
export function useServiceHealth() {
  const { isAdmin } = useAuth();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["services"],
    queryFn: getServices,
    refetchInterval: 30_000,
    staleTime: 25_000,
    enabled: isAdmin,
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
