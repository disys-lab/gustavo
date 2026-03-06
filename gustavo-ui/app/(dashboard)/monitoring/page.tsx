"use client";
import { useState } from "react";
import { useMonitoringStream } from "@/lib/hooks/useMonitoringStream";
import { HostSelector } from "@/components/monitoring/HostSelector";
import { MetricsChart } from "@/components/monitoring/MetricsChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ContainerMetrics } from "@/lib/types/api";

function thresholdColor(pct: number): string {
  if (pct >= 80) return "text-red-600 font-semibold";
  if (pct >= 50) return "text-yellow-600";
  return "text-gray-900";
}

function barColor(pct: number): string {
  if (pct >= 80) return "bg-red-500";
  if (pct >= 50) return "bg-yellow-400";
  return "bg-blue-500";
}

function MemBar({ label, used, total }: { label: string; used: number; total: number }) {
  const pct = total > 0 ? Math.min((used / total) * 100, 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-500">
        <span>{label}</span>
        <span className={thresholdColor(pct)}>
          {used.toLocaleString()} / {total.toLocaleString()} MB ({pct.toFixed(1)}%)
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${barColor(pct)}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function ContainerTable({ containers }: { containers: ContainerMetrics[] }) {
  if (containers.length === 0) return <p className="text-gray-400 text-sm">No containers</p>;
  return (
    <div className="overflow-auto rounded border">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Container</th>
            <th className="px-3 py-2 text-left font-medium text-gray-600">CPU %</th>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Memory</th>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Mem %</th>
          </tr>
        </thead>
        <tbody>
          {containers.map((c) => (
            <tr key={c.name} className="border-b hover:bg-gray-50">
              <td className="px-3 py-2 font-mono">{c.name}</td>
              <td className={`px-3 py-2 ${thresholdColor(c.cpu_percent)}`}>{c.cpu_percent.toFixed(2)}%</td>
              <td className="px-3 py-2 text-gray-500">{c.memory_mb.toFixed(0)} / {c.memory_limit_mb.toFixed(0)} MB</td>
              <td className={`px-3 py-2 ${thresholdColor(c.memory_percent)}`}>{c.memory_percent.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function MonitoringPage() {
  const [selectedHost, setSelectedHost] = useState("all");
  const [selectedDg, setSelectedDg] = useState("all");

  const { buffer, lastEvent, connected, error } = useMonitoringStream(selectedDg, selectedHost);

  const vitals = lastEvent?.vitals;
  const containers = lastEvent?.containers ?? [];
  const cpuPct = vitals?.cpu_percent ?? 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Monitoring</h1>
        <Badge variant={connected ? "default" : "secondary"}>
          {connected ? "Live" : error ?? "Connecting…"}
        </Badge>
      </div>

      {!connected && (
        <div className="mb-4 flex items-center gap-2 rounded-md border border-yellow-200 bg-yellow-50 px-4 py-2 text-sm text-yellow-800">
          <span className="font-semibold">Not connected.</span>
          <span>{error ?? "Attempting to connect to the monitoring stream…"}</span>
        </div>
      )}

      <HostSelector
        selectedHost={selectedHost}
        selectedDeviceGroup={selectedDg}
        onHostChange={setSelectedHost}
        onDeviceGroupChange={setSelectedDg}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* CPU chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">CPU Usage (5-min rolling)</CardTitle>
          </CardHeader>
          <CardContent>
            <MetricsChart buffer={buffer} title="" />
          </CardContent>
        </Card>

        {/* Vitals summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              System Vitals
              {vitals?.host && <span className="ml-2 text-xs font-normal text-gray-500">{vitals.host}</span>}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {vitals ? (
              <>
                <div className="flex gap-6 text-sm">
                  <div>
                    <span className="text-gray-500">CPU</span>
                    <p className={`text-2xl font-semibold ${thresholdColor(cpuPct)}`}>
                      {cpuPct.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-400">{vitals.cpu_cores} cores</p>
                  </div>
                </div>
                {vitals.memory_mb && (
                  <MemBar
                    label="Memory"
                    used={vitals.memory_mb.used}
                    total={vitals.memory_mb.total}
                  />
                )}
                {vitals.disk_mb && (
                  <MemBar
                    label="Disk"
                    used={vitals.disk_mb.used}
                    total={vitals.disk_mb.total}
                  />
                )}
              </>
            ) : (
              <p className="text-gray-400 text-sm">No vitals yet</p>
            )}
          </CardContent>
        </Card>

        {/* Container table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Containers ({containers.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <ContainerTable containers={containers} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
