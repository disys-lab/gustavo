"use client";
import { useQuery } from "@tanstack/react-query";
import { getServices } from "@/lib/api/services";
import { ServiceRow } from "@/components/manager/ServiceRow";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

// "syncer" is intentionally excluded from the UI for now — preserved for future re-enablement
const SERVICES = ["redis", "mongo", "registry", "manager"] as const;

export default function ManagerPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["services"],
    queryFn: getServices,
    refetchInterval: 30_000,
  });

  const services = (data?.response ?? {}) as Record<string, { error: boolean; response: string }>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Services</h1>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {SERVICES.map((s) => <Skeleton key={s} className="h-14 w-full" />)}
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Could not reach the API — make sure the FastAPI server is running.{" "}
          <button onClick={() => refetch()} className="underline font-medium">Retry</button>
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600 w-28">Service</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 w-28">Status</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Actions</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 w-40">Danger</th>
              </tr>
            </thead>
            <tbody>
              {SERVICES.map((svc) => (
                <ServiceRow
                  key={svc}
                  name={svc}
                  initialStatus={services[svc]?.error === false ? "Up" : "Unknown"}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
