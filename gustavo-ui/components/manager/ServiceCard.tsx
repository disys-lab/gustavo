"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusPill } from "@/components/ui/StatusPill";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { useJobPoller } from "@/lib/hooks/useJobPoller";
import { runService, serviceAction, getServiceStatus } from "@/lib/api/services";
import type { ServiceName } from "@/lib/types/platform";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface ServiceCardProps {
  name: ServiceName;
  initialStatus?: string;
}

export function ServiceCard({ name, initialStatus = "Unknown" }: ServiceCardProps) {
  const [status, setStatus] = useState(initialStatus);
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState<"stop" | "remove" | null>(null);
  const { toast } = useActivityToast();

  const { isRunning: jobRunning, isDone, isError, job } = useJobPoller(jobId);

  useEffect(() => {
    if (isDone && job) {
      const result = job.result;
      if (result && !result.error) {
        toast({ title: `${name} launched`, description: String(result.response) });
        setStatus("Up");
      } else if (result) {
        toast({ variant: "destructive", title: `${name} launch failed`, description: String(result.response) });
      }
      setJobId(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDone]);

  useEffect(() => {
    if (isError && job) {
      toast({ variant: "destructive", title: `${name} failed`, description: job.error ?? "Unknown error" });
      setJobId(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isError]);

  const handleLaunch = async () => {
    try {
      const res = await runService(name);
      if (!res.error) {
        const { job_id } = res.response as { job_id: string };
        setJobId(job_id);
        toast({ title: `Launching ${name}…`, description: "Polling for completion" });
      } else {
        toast({ variant: "destructive", title: "Launch failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Error", description: String(exc) });
    }
  };

  const handleAction = async (action: string) => {
    try {
      const res = await serviceAction(name, action);
      if (!res.error) {
        toast({ title: "Success", description: String(res.response) });
        if (action === "stop" || action === "remove" || action === "kill") setStatus("Down");
        if (action === "start" || action === "restart") setStatus("Up");
      } else {
        toast({ variant: "destructive", title: "Action failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Error", description: String(exc) });
    }
  };

  const handleStatus = async () => {
    setStatusLoading(true);
    try {
      const res = await getServiceStatus(name);
      if (!res.error) {
        setStatus("Up");
      } else {
        setStatus("Down");
      }
    } catch {
      setStatus("Unknown");
    } finally {
      setStatusLoading(false);
    }
  };

  const displayName = name.charAt(0).toUpperCase() + name.slice(1);

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{displayName}</CardTitle>
          <StatusPill status={status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* Primary actions */}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" disabled={statusLoading} onClick={handleStatus}>
            {statusLoading ? "Checking…" : "Status"}
          </Button>
          <Button size="sm" disabled={jobRunning} onClick={handleLaunch}>
            {jobRunning ? "Launching…" : "Launch"}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => handleAction("restart")}>
            Restart
          </Button>
        </div>
        {/* Destructive actions */}
        <div className="flex flex-wrap gap-2 pt-1 border-t">
          <Button size="sm" variant="outline" onClick={() => setPendingAction("stop")}>
            Stop
          </Button>
          <Button size="sm" variant="destructive" onClick={() => setPendingAction("remove")}>
            Remove
          </Button>
        </div>
      </CardContent>

      <AlertDialog open={!!pendingAction} onOpenChange={(open) => { if (!open) setPendingAction(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {pendingAction === "remove" ? `Remove ${displayName}?` : `Stop ${displayName}?`}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {pendingAction === "remove"
                ? `Are you sure you want to remove the ${displayName} container? The container will be deleted and will need to be relaunched.`
                : `Are you sure you want to stop ${displayName}?`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => { if (pendingAction) { handleAction(pendingAction); setPendingAction(null); } }}
            >
              {pendingAction === "remove" ? "Remove" : "Stop"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
