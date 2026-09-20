"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listWorkerDirectory, deleteWorkerDirectoryEntry } from "@/lib/api/workerDirectory";
import { WorkerDirectoryTable } from "@/components/worker-directory/WorkerDirectoryTable";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivityToast } from "@/hooks/use-activity-toast";
import type { WorkerDirectoryEntry } from "@/lib/types/api";

export default function WorkerDirectoryPage() {
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();

  const { data, isLoading } = useQuery({
    queryKey: ["worker-directory"],
    queryFn: listWorkerDirectory,
    staleTime: 30_000,
  });
  const entries: WorkerDirectoryEntry[] = !data?.error && Array.isArray(data?.response) ? data.response : [];

  const handleDelete = async (deviceGroup: string, nodeId: string) => {
    const res = await deleteWorkerDirectoryEntry(deviceGroup, nodeId);
    if (!res.error) {
      toast({ title: `Removed '${nodeId}' from the directory` });
      queryClient.invalidateQueries({ queryKey: ["worker-directory"] });
    } else {
      toast({ variant: "destructive", title: "Delete failed", description: String(res.response) });
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Worker Directory</h1>
        <p className="text-sm text-gray-500">
          Workers currently checked in, scoped to the device groups you have access to.
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <WorkerDirectoryTable entries={entries} onDelete={handleDelete} />
      )}
    </div>
  );
}
