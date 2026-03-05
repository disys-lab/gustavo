"use client";
import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listRedisBackups, createRedisBackup, restoreRedisBackup, deleteRedisBackup,
  listRegistryBackups, createRegistryBackup, restoreRegistryBackup, deleteRegistryBackup,
} from "@/lib/api/backups";
import { BackupTable } from "@/components/backups/BackupTable";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { useJobPoller } from "@/lib/hooks/useJobPoller";
import type { BackupEntry } from "@/lib/types/api";

function useBackupPanel(
  queryKey: string[],
  listFn: () => Promise<unknown>,
  createFn: () => Promise<unknown>,
  restoreFn: (name: string) => Promise<unknown>,
  deleteFn: (name: string) => Promise<unknown>,
) {
  const [selected, setSelected] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();

  const { data, isLoading } = useQuery({ queryKey, queryFn: listFn as () => Promise<{ error: boolean; response: BackupEntry[] }> });
  const backups: BackupEntry[] = (!data?.error && Array.isArray(data?.response)) ? data.response : [];

  const { isRunning, isDone, isError, job } = useJobPoller(jobId);

  // Show completion toast and refresh list when job finishes
  useEffect(() => {
    if (isDone) {
      const result = job?.result as { error: boolean; response: string } | null;
      if (result?.error) {
        toast({ variant: "destructive", title: "Backup failed", description: result.response });
      } else {
        toast({ title: "Backup complete", description: result?.response ?? "Done" });
      }
      queryClient.invalidateQueries({ queryKey });
      setJobId(null);
    } else if (isError) {
      toast({ variant: "destructive", title: "Backup job error", description: job?.error ?? "Unknown error" });
      setJobId(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDone, isError]);

  const handleCreate = async () => {
    try {
      const res = await createFn() as { error: boolean; response: { job_id: string } };
      if (!res.error) {
        setJobId(res.response.job_id);
        toast({ title: "Backup started", description: "Polling for completion…" });
      } else {
        toast({ variant: "destructive", title: "Create failed" });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Create failed", description: String(exc) });
    }
  };

  const handleRestore = async () => {
    if (!selected) return;
    try {
      const res = await restoreFn(selected) as { error: boolean; response: { job_id: string } };
      if (!res.error) {
        setJobId(res.response.job_id);
        toast({ title: "Restore started" });
      } else {
        toast({ variant: "destructive", title: "Restore failed" });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Restore failed", description: String(exc) });
    }
  };

  const handleDelete = async (name: string) => {
    try {
      const res = await deleteFn(name) as { error: boolean; response: string };
      if (!res.error) {
        toast({ title: "Deleted", description: name });
        queryClient.invalidateQueries({ queryKey });
        if (selected === name) setSelected(null);
      } else {
        toast({ variant: "destructive", title: "Delete failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Delete failed", description: String(exc) });
    }
  };

  return { backups, isLoading, selected, setSelected, handleCreate, handleRestore, handleDelete, isRunning };
}

export default function BackupsPage() {
  const redisPanel = useBackupPanel(
    ["backups-redis"],
    listRedisBackups,
    createRedisBackup,
    restoreRedisBackup,
    deleteRedisBackup,
  );

  const registryPanel = useBackupPanel(
    ["backups-registry"],
    listRegistryBackups,
    createRegistryBackup,
    restoreRegistryBackup,
    deleteRegistryBackup,
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Backups</h1>
      <Tabs defaultValue="redis">
        <TabsList>
          <TabsTrigger value="redis">Redis</TabsTrigger>
          <TabsTrigger value="registry">Registry</TabsTrigger>
        </TabsList>

        <TabsContent value="redis" className="pt-4 space-y-4">
          <div className="flex gap-2">
            <Button onClick={redisPanel.handleCreate} disabled={redisPanel.isRunning}>
              {redisPanel.isRunning ? "Running…" : "Create Backup"}
            </Button>
            <Button
              variant="outline"
              onClick={redisPanel.handleRestore}
              disabled={!redisPanel.selected || redisPanel.isRunning}
            >
              Restore Selected
            </Button>
          </div>
          {redisPanel.isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <BackupTable
              backups={redisPanel.backups}
              selected={redisPanel.selected}
              onSelect={redisPanel.setSelected}
              onDelete={redisPanel.handleDelete}
            />
          )}
        </TabsContent>

        <TabsContent value="registry" className="pt-4 space-y-4">
          <div className="flex gap-2">
            <Button onClick={registryPanel.handleCreate} disabled={registryPanel.isRunning}>
              {registryPanel.isRunning ? "Running…" : "Create Backup"}
            </Button>
            <Button
              variant="outline"
              onClick={registryPanel.handleRestore}
              disabled={!registryPanel.selected || registryPanel.isRunning}
            >
              Restore Selected
            </Button>
          </div>
          {registryPanel.isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <BackupTable
              backups={registryPanel.backups}
              selected={registryPanel.selected}
              onSelect={registryPanel.setSelected}
              onDelete={registryPanel.handleDelete}
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
