"use client";
import { useState, useEffect } from "react";
import { ClipboardList, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { subscribeActivity, clearActivity } from "@/lib/activityLog";
import type { ActivityEntry } from "@/lib/activityLog";
import { formatDistanceToNow } from "date-fns";

const LEVEL_COLORS: Record<string, string> = {
  success: "text-green-600",
  error: "text-red-600",
  info: "text-blue-600",
};

export function ActivitySheet() {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);

  useEffect(() => {
    return subscribeActivity(setEntries);
  }, []);

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="relative w-full justify-start gap-2 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900"
        >
          <ClipboardList className="h-4 w-4 shrink-0" />
          <span className="text-sm font-medium">Activity</span>
          {entries.length > 0 && (
            <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-gray-200 text-xs font-semibold text-gray-700 px-1">
              {entries.length > 99 ? "99+" : entries.length}
            </span>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-80 sm:w-96 flex flex-col">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle>Activity Log</SheetTitle>
            {entries.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearActivity}
                className="text-gray-400 hover:text-gray-600"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </SheetHeader>
        <div className="flex-1 overflow-y-auto mt-4 space-y-2">
          {entries.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No activity yet</p>
          ) : (
            entries.map((e) => (
              <div key={e.id} className="rounded-md border p-3 text-sm space-y-0.5">
                <div className="flex items-start justify-between gap-2">
                  <span className={`font-medium ${LEVEL_COLORS[e.level] ?? "text-gray-900"}`}>
                    {e.title}
                  </span>
                  <span className="text-xs text-gray-400 shrink-0">
                    {formatDistanceToNow(e.timestamp, { addSuffix: true })}
                  </span>
                </div>
                {e.description && (
                  <p className="text-gray-500 text-xs">{e.description}</p>
                )}
              </div>
            ))
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
