"use client";
import { useQuery } from "@tanstack/react-query";
import { getHosts } from "@/lib/api/monitoring";
import { Label } from "@/components/ui/label";

interface HostSelectorProps {
  selectedHost: string;
  selectedDeviceGroup: string;
  onHostChange: (host: string) => void;
  onDeviceGroupChange: (dg: string) => void;
}

export function HostSelector({ selectedHost, selectedDeviceGroup, onHostChange, onDeviceGroupChange }: HostSelectorProps) {
  const { data } = useQuery({
    queryKey: ["monitoring-hosts"],
    queryFn: () => getHosts("all", "all"),
  });

  const hosts: string[] = ["all"];
  const deviceGroups: string[] = ["all"];

  if (data?.response && typeof data.response === "object" && !Array.isArray(data.response)) {
    const resp = data.response as Record<string, string[]>;
    hosts.push(...Object.keys(resp));
    const allDgs = new Set<string>();
    Object.values(resp).flat().forEach((dg) => allDgs.add(dg));
    deviceGroups.push(...Array.from(allDgs));
  }

  return (
    <div className="flex flex-wrap gap-4 mb-4">
      <div>
        <Label className="text-xs">Device Group</Label>
        <select
          className="mt-1 block rounded border border-gray-300 bg-white px-2 py-1.5 text-sm"
          value={selectedDeviceGroup}
          onChange={(e) => onDeviceGroupChange(e.target.value)}
        >
          {deviceGroups.map((dg) => <option key={dg} value={dg}>{dg}</option>)}
        </select>
      </div>
      <div>
        <Label className="text-xs">Host</Label>
        <select
          className="mt-1 block rounded border border-gray-300 bg-white px-2 py-1.5 text-sm"
          value={selectedHost}
          onChange={(e) => onHostChange(e.target.value)}
        >
          {hosts.map((h) => <option key={h} value={h}>{h}</option>)}
        </select>
      </div>
    </div>
  );
}
