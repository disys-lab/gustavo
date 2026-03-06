"use client";
import { formatDistanceToNow, parseISO, isValid } from "date-fns";
import { Button } from "@/components/ui/button";
import type { BackupEntry } from "@/lib/types/api";

interface BackupTableProps {
  backups: BackupEntry[];
  selected: string | null;
  onSelect: (filename: string | null) => void;
  onDelete: (filename: string) => void;
}

function relativeTime(timestamp: string): string {
  try {
    const d = parseISO(timestamp);
    if (isValid(d)) return formatDistanceToNow(d, { addSuffix: true });
  } catch {
    // fall through
  }
  return timestamp;
}

export function BackupTable({ backups, selected, onSelect, onDelete }: BackupTableProps) {
  if (backups.length === 0) {
    return <p className="text-gray-400 text-sm text-center py-8">No backups found.</p>;
  }

  return (
    <div className="overflow-auto rounded border">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-600 w-8"></th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Filename</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Timestamp</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600 w-20">Action</th>
          </tr>
        </thead>
        <tbody>
          {backups.map((b) => (
            <tr
              key={b.filename}
              className={`border-b cursor-pointer hover:bg-gray-50 ${selected === b.filename ? "bg-blue-50" : ""}`}
              onClick={() => onSelect(selected === b.filename ? null : b.filename)}
            >
              <td className="px-4 py-2">
                <input
                  type="radio"
                  readOnly
                  checked={selected === b.filename}
                />
              </td>
              <td className="px-4 py-2 font-mono">{b.filename}</td>
              <td className="px-4 py-2 text-gray-500" title={b.timestamp}>
                {relativeTime(b.timestamp)}
              </td>
              <td className="px-4 py-2">
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-600 hover:text-red-700"
                  onClick={(e) => { e.stopPropagation(); onDelete(b.filename); }}
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
