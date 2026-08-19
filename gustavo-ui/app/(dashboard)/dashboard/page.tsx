"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getServices } from "@/lib/api/services";
import { listApps } from "@/lib/api/apps";
import { getHosts } from "@/lib/api/monitoring";
import { useMonitoringStream } from "@/lib/hooks/useMonitoringStream";
import { listDeviceGroups } from "@/lib/api/deviceGroups";
import { StatusPill } from "@/components/ui/StatusPill";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ServiceRow } from "@/components/manager/ServiceRow";
import { subscribeActivity } from "@/lib/activityLog";
import type { ActivityEntry } from "@/lib/activityLog";
import type { VitalsData } from "@/lib/types/api";
import { formatDistanceToNow } from "date-fns";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useAuth } from "@/lib/context/AuthContext";
import { cn } from "@/lib/utils";

// "syncer" is intentionally excluded — preserved for future re-enablement
const VISIBLE_SERVICES = ["redis", "mongo", "registry", "manager"] as const;

const LEVEL_COLORS: Record<string, string> = {
  success: "text-green-600",
  error: "text-red-600",
  info: "text-blue-600",
};

function thresholdColor(pct: number) {
  if (pct >= 80) return "text-red-600 font-semibold";
  if (pct >= 50) return "text-yellow-600";
  return "text-gray-900";
}

function VitalBar({ label, pct }: { label: string; pct: number }) {
  const barColor = pct >= 80 ? "bg-red-500" : pct >= 50 ? "bg-yellow-400" : "bg-blue-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-500">{label}</span>
        <span className={thresholdColor(pct)}>{pct.toFixed(1)}%</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [manageExpanded, setManageExpanded] = useState(false);
  const [selectedHost, setSelectedHost] = useState("all");
  const [selectedDg, setSelectedDg] = useState("all");

  const { isAdmin } = useAuth();

  useEffect(() => subscribeActivity(setActivity), []);

  const { data: hostsData } = useQuery({
    queryKey: ["monitoring-hosts"],
    queryFn: () => getHosts("all", "all"),
    staleTime: 60_000,
    enabled: isAdmin,
  });

  const availableHosts: string[] = ["all"];
  const availableDgs: string[] = ["all"];
  if (hostsData?.response && typeof hostsData.response === "object" && !Array.isArray(hostsData.response)) {
    const resp = hostsData.response as Record<string, string[]>;
    availableHosts.push(...Object.keys(resp));
    const dgSet = new Set<string>();
    Object.values(resp).flat().forEach((dg) => dgSet.add(dg));
    availableDgs.push(...Array.from(dgSet));
  }

  const { data: servicesData, isLoading: servicesLoading } = useQuery({
    queryKey: ["services"],
    queryFn: getServices,
    refetchInterval: 30_000,
    staleTime: 25_000,
    enabled: isAdmin,
  });

  const { lastEvent: monitoringEvent } = useMonitoringStream(selectedDg, selectedHost, isAdmin);

  const { data: appsData } = useQuery({
    queryKey: ["apps"],
    queryFn: listApps,
    staleTime: 30_000,
  });

  const { data: dgData } = useQuery({
    queryKey: ["device-groups"],
    queryFn: listDeviceGroups,
    staleTime: 30_000,
  });

  const services = (servicesData?.response ?? {}) as Record<string, { error: boolean; response: string }>;

  const appList: string[] = [];
  if (appsData && !appsData.error && appsData.response) {
    const resp = appsData.response as Record<string, unknown>;
    if (Array.isArray(resp.apps)) appList.push(...(resp.apps as string[]));
  }

  let dgCount = 0;
  if (dgData && !dgData.error && dgData.response) {
    const resp = dgData.response as Record<string, unknown>;
    if (Array.isArray(resp.device_groups)) dgCount = resp.device_groups.length;
  }

  const vitals: VitalsData | undefined = monitoringEvent?.vitals;
  const cpuPct = vitals?.cpu_percent ?? 0;
  const memPct = vitals?.memory_mb
    ? (vitals.memory_mb.used / vitals.memory_mb.total) * 100
    : 0;
  const diskPct = vitals?.disk_mb
    ? (vitals.disk_mb.used / vitals.disk_mb.total) * 100
    : 0;

  const recentActivity = activity.slice(0, 8);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Platform Services card — admin-only, backend is admin-gated */}
      {isAdmin && (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Platform Services</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">

          {/* Status strip — always visible */}
          {servicesLoading ? (
            <div className="flex gap-3">
              {VISIBLE_SERVICES.map((s) => <Skeleton key={s} className="h-12 w-32" />)}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {VISIBLE_SERVICES.map((svc) => {
                const entry = services[svc];
                const status = entry ? (entry.error ? "Down" : "Up") : "Unknown";
                return (
                  <div key={svc} className="flex flex-col items-start gap-1 rounded-lg border px-3 py-2.5">
                    <span className="text-xs text-gray-500 capitalize">{svc}</span>
                    <StatusPill status={status} />
                  </div>
                );
              })}
            </div>
          )}

          {/* Expandable manage section */}
          <div className="border-t pt-3">
            <button
              onClick={() => setManageExpanded((v) => !v)}
              className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors select-none"
            >
              {manageExpanded
                ? <ChevronDown className="h-4 w-4" />
                : <ChevronRight className="h-4 w-4" />
              }
              Manage Platform Services
            </button>

            {manageExpanded && (
              <div className="mt-3 rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-2.5 text-left font-medium text-gray-600 w-28">Service</th>
                      <th className="px-4 py-2.5 text-left font-medium text-gray-600">Actions</th>
                      <th className="px-4 py-2.5 text-left font-medium text-gray-600 w-40">Danger</th>
                    </tr>
                  </thead>
                  <tbody>
                    {VISIBLE_SERVICES.map((svc) => (
                      <ServiceRow
                        key={svc}
                        name={svc}
                        initialStatus={services[svc]?.error === false ? "Up" : "Unknown"}
                        showStatus={false}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </CardContent>
      </Card>
      )}

      {/* Stat cards row */}
      <div className={cn("grid grid-cols-1 gap-6", isAdmin ? "sm:grid-cols-3" : "sm:grid-cols-2")}>

        {/* System vitals — admin-only, backend is admin-gated */}
        {isAdmin && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">System Vitals</CardTitle>
              <div className="flex items-center gap-2">
                {availableDgs.length > 1 && (
                  <select
                    className="rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600"
                    value={selectedDg}
                    onChange={(e) => { setSelectedDg(e.target.value); setSelectedHost("all"); }}
                  >
                    {availableDgs.map((dg) => (
                      <option key={dg} value={dg}>{dg}</option>
                    ))}
                  </select>
                )}
                {availableHosts.length > 1 && (
                  <select
                    className="rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600"
                    value={selectedHost}
                    onChange={(e) => setSelectedHost(e.target.value)}
                  >
                    {availableHosts.map((h) => (
                      <option key={h} value={h}>{h}</option>
                    ))}
                  </select>
                )}
                <Link href="/monitoring" className="text-xs text-blue-600 hover:underline">Details →</Link>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {vitals ? (
              <>
                <VitalBar label="CPU" pct={cpuPct} />
                <VitalBar label="Memory" pct={memPct} />
                <VitalBar label="Disk" pct={diskPct} />
                {vitals.host && (
                  <p className="text-xs text-gray-400 pt-1">{vitals.host}</p>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-400">No vitals available</p>
            )}
          </CardContent>
        </Card>
        )}

        {/* Apps */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Apps</CardTitle>
              <Link href="/apps" className="text-xs text-blue-600 hover:underline">Manage →</Link>
            </div>
          </CardHeader>
          <CardContent className="flex items-center justify-center h-24">
            {appsData ? (
              <div className="text-center">
                <p className="text-4xl font-bold text-gray-900">{appList.length}</p>
                <p className="text-sm text-gray-500 mt-1">
                  {appList.length === 1 ? "app deployed" : "apps deployed"}
                </p>
              </div>
            ) : (
              <Skeleton className="h-12 w-20" />
            )}
          </CardContent>
        </Card>

        {/* Device Groups */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Device Groups</CardTitle>
              <Link href="/device-groups" className="text-xs text-blue-600 hover:underline">Manage →</Link>
            </div>
          </CardHeader>
          <CardContent className="flex items-center justify-center h-24">
            {dgData ? (
              <div className="text-center">
                <p className="text-4xl font-bold text-gray-900">{dgCount}</p>
                <p className="text-sm text-gray-500 mt-1">
                  {dgCount === 1 ? "group configured" : "groups configured"}
                </p>
              </div>
            ) : (
              <Skeleton className="h-12 w-20" />
            )}
          </CardContent>
        </Card>

      </div>

      {/* Recent activity — full width */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {recentActivity.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">No activity yet — actions you take will appear here.</p>
          ) : (
            <div className="divide-y">
              {recentActivity.map((e) => (
                <div key={e.id} className="flex items-center justify-between gap-4 py-2.5 text-sm">
                  <span className={`font-medium ${LEVEL_COLORS[e.level] ?? "text-gray-700"}`}>
                    {e.title}
                  </span>
                  {e.description && (
                    <span className="text-gray-400 text-xs flex-1 truncate">{e.description}</span>
                  )}
                  <span className="text-gray-400 text-xs shrink-0">
                    {formatDistanceToNow(e.timestamp, { addSuffix: true })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
