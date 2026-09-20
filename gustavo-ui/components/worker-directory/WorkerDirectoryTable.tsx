"use client";
import { formatDistanceToNow } from "date-fns";
import { Button } from "@/components/ui/button";
import type { WorkerDirectoryEntry } from "@/lib/types/api";

interface WorkerDirectoryTableProps {
  entries: WorkerDirectoryEntry[];
  onDelete: (deviceGroup: string, nodeId: string) => void;
}

function relativeTime(updatedAt: number): string {
  try {
    return formatDistanceToNow(new Date(updatedAt * 1000), { addSuffix: true });
  } catch {
    return String(updatedAt);
  }
}

export function WorkerDirectoryTable({ entries, onDelete }: WorkerDirectoryTableProps) {
  if (entries.length === 0) {
    return <p className="text-gray-400 text-sm text-center py-8">No workers checked in yet.</p>;
  }

  return (
    <div className="overflow-auto rounded border">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Device Group</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Worker ID</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Host IP</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Remote IP</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Last Updated</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600 w-20">Action</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={`${e.device_group}@${e.node_id}`} className="border-b hover:bg-gray-50">
              <td className="px-4 py-2">{e.device_group}</td>
              <td className="px-4 py-2 font-mono">{e.node_id}</td>
              <td className="px-4 py-2 font-mono">{e.host_ip}</td>
              <td className="px-4 py-2 font-mono">{e.remote_ip}</td>
              <td className="px-4 py-2 text-gray-500" title={new Date(e.updated_at * 1000).toISOString()}>
                {relativeTime(e.updated_at)}
              </td>
              <td className="px-4 py-2">
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-600 hover:text-red-700"
                  onClick={() => onDelete(e.device_group, e.node_id)}
                >
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
