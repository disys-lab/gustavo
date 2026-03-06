"use client";
import { StatusPill } from "@/components/ui/StatusPill";
import type { ServiceName } from "@/lib/types/platform";

interface ServiceStatusRowProps {
  services: Record<string, { error: boolean; response: string }>;
}

// "syncer" is intentionally excluded — preserved for future re-enablement
const SERVICE_NAMES: ServiceName[] = ["redis", "mongo", "registry", "manager"];

export function ServiceStatusRow({ services }: ServiceStatusRowProps) {
  return (
    <div className="flex flex-wrap gap-4 mb-6">
      {SERVICE_NAMES.map((svc) => {
        const entry = services[svc];
        const status = entry ? (entry.error ? "Down" : "Up") : "Unknown";
        return (
          <div key={svc} className="flex items-center gap-2 bg-white rounded-lg border px-3 py-2">
            <span className="text-sm font-medium capitalize">{svc}</span>
            <StatusPill status={status} />
          </div>
        );
      })}
    </div>
  );
}
