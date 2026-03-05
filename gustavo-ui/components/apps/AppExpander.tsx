"use client";
import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { deleteApp, exportAppYaml, getApp } from "@/lib/api/apps";
import { listDeviceGroups } from "@/lib/api/deviceGroups";
import { useActivityToast } from "@/hooks/use-activity-toast";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface AppExpanderProps {
  name: string;
  onDeleted: () => void;
  onEdit: () => void;
}

function ConfigRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-muted-foreground w-32 shrink-0">{label}</span>
      <span className="font-mono break-all">{value}</span>
    </div>
  );
}

export function AppExpander({ name, onDeleted, onEdit }: AppExpanderProps) {
  const [expanded, setExpanded] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const { toast } = useActivityToast();
  const queryClient = useQueryClient();

  const handleDelete = async () => {
    try {
      const res = await deleteApp(name);
      if (!res.error) {
        toast({ title: `App '${name}' deleted` });
        queryClient.invalidateQueries({ queryKey: ["apps"] });
        onDeleted();
      } else {
        toast({ variant: "destructive", title: "Delete failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Delete failed", description: String(exc) });
    } finally {
      setConfirmDelete(false);
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: ["app", name],
    queryFn: () => getApp(name),
    enabled: expanded,
    staleTime: 30_000,
  });

  const { data: dgData } = useQuery({
    queryKey: ["device-groups"],
    queryFn: listDeviceGroups,
    enabled: expanded,
    staleTime: 30_000,
  });

  const memberGroups: string[] = [];
  if (dgData && !dgData.error && dgData.response) {
    const resp = dgData.response as Record<string, unknown>;
    if (Array.isArray(resp.device_groups)) {
      for (const item of resp.device_groups) {
        if (typeof item === "object" && item !== null && "name" in item && "apps" in item) {
          const entry = item as { name: string; apps: string[] };
          if (entry.apps.includes(name)) memberGroups.push(entry.name);
        }
      }
    }
  }

  // list_app_info returns reply directly — no double nesting
  const cfg = (data?.response as Record<string, unknown>) ?? {};

  const dockerImage = cfg.docker_image as string | undefined;
  const networks = cfg.networks as string[] | undefined;
  const running = cfg.running as boolean | undefined;
  const privileged = cfg.privileged as boolean | undefined;
  const envVars = cfg.env_vars as Record<string, string> | undefined;
  const ports = cfg.starting_ports as Record<string, number>[] | undefined;
  const volumes = cfg.volumes as string[] | undefined;

  const handleExport = async () => {
    try {
      const yaml = await exportAppYaml(name);
      const blob = new Blob([yaml], { type: "text/yaml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${name}.yaml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (exc) {
      toast({ variant: "destructive", title: "Export failed", description: String(exc) });
    }
  };

  return (
    <>
    <AlertDialog open={confirmDelete} onOpenChange={(open) => { if (!open) setConfirmDelete(false); }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete app?</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete &quot;{name}&quot;? It will be removed from all device groups. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            onClick={handleDelete}
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    <Card>
      <CardHeader className="cursor-pointer py-3" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm font-medium">{name}</CardTitle>
            {running !== undefined && (
              <Badge variant={running ? "default" : "secondary"} className="text-xs">
                {running ? "running" : "stopped"}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <Button size="sm" variant="ghost" onClick={onEdit}>Edit</Button>
            <Button size="sm" variant="ghost" onClick={handleExport}>Export YAML</Button>
            <Button size="sm" variant="destructive" onClick={() => setConfirmDelete(true)}>Delete</Button>
            {expanded ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
          </div>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 space-y-2 border-t">
          {isLoading ? (
            <div className="space-y-2 pt-3">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-5" />)}
            </div>
          ) : data?.error ? (
            <p className="text-sm text-red-500 pt-3">Failed to load config: {String(data.response)}</p>
          ) : (
            <div className="pt-3 space-y-2">
              {dockerImage && <ConfigRow label="Image" value={dockerImage} />}
              {networks && networks.length > 0 && <ConfigRow label="Networks" value={networks.join(", ")} />}
              {privileged !== undefined && (
                <ConfigRow label="Privileged" value={privileged ? "yes" : "no"} />
              )}
              {envVars && Object.keys(envVars).length > 0 && (
                <div className="text-sm">
                  <span className="text-muted-foreground">Env vars</span>
                  <div className="mt-1 space-y-0.5 pl-2">
                    {Object.entries(envVars).map(([k, v]) => (
                      <div key={k} className="font-mono text-xs">
                        <span className="text-blue-600">{k}</span>=<span>{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {ports && ports.length > 0 && (
                <ConfigRow
                  label="Ports"
                  value={ports.map((p) => Object.entries(p).map(([h, c]) => `${h}→${c}`).join(", ")).join(", ")}
                />
              )}
              {volumes && volumes.length > 0 && (
                <div className="text-sm">
                  <span className="text-muted-foreground">Volumes</span>
                  <div className="mt-1 space-y-0.5 pl-2">
                    {volumes.map((v) => <div key={v} className="font-mono text-xs">{v}</div>)}
                  </div>
                </div>
              )}
              <div className="flex gap-2 text-sm">
                <span className="text-muted-foreground w-32 shrink-0">Device groups</span>
                <div className="flex flex-wrap gap-1">
                  {memberGroups.length === 0 ? (
                    <span className="text-muted-foreground font-mono text-xs">none</span>
                  ) : (
                    memberGroups.map((dg) => (
                      <Badge key={dg} variant="outline" className="text-xs opacity-60">{dg}</Badge>
                    ))
                  )}
                </div>
              </div>
              {/* Fallback: show raw if no known fields parsed */}
              {!dockerImage && !envVars && !networks && !ports && (
                <pre className="text-xs bg-gray-50 rounded p-3 overflow-auto max-h-48">
                  {JSON.stringify(cfg, null, 2)}
                </pre>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
    </>
  );
}
