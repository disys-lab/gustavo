"use client";
import { useQuery } from "@tanstack/react-query";
import { getServices } from "@/lib/api/services";
import type { ServicesMap } from "@/lib/types/api";

/**
 * Polls /api/services every 30s.
 * Returns `allUp: true` if every service is running, `false` if any is down,
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
  const statuses = Object.values(map);
  if (statuses.length === 0) return { allUp: null };

  const allUp = statuses.every((s) => s === "Up" || s === "running");
  return { allUp };
}
