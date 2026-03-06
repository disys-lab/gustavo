"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listDeviceGroups, createDeviceGroup, deleteDeviceGroup,
  addAppsToDeviceGroup, removeAppsFromDeviceGroup,
} from "@/lib/api/deviceGroups";
import { DeviceGroupForm } from "@/components/device-groups/DeviceGroupForm";
import { AppSelector } from "@/components/device-groups/AppSelector";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivityToast } from "@/hooks/use-activity-toast";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type DeviceGroupEntry = { name: string; apps: string[] };

export default function DeviceGroupsPage() {
  const [showForm, setShowForm] = useState(false);
  const [selectedApps, setSelectedApps] = useState<Record<string, string[]>>({});
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["device-groups"],
    queryFn: listDeviceGroups,
  });

  const groups: DeviceGroupEntry[] = [];
  if (data && !data.error) {
    const resp = data.response as Record<string, unknown>;
    if (Array.isArray(resp.device_groups)) {
      for (const item of resp.device_groups) {
        if (typeof item === "object" && item !== null && "name" in item) {
          groups.push(item as DeviceGroupEntry);
        } else if (typeof item === "string") {
          groups.push({ name: item, apps: [] });
        }
      }
    }
  }

  const handleCreate = async ({ name }: { name: string }) => {
    try {
      const res = await createDeviceGroup(name);
      if (!res.error) {
        toast({ title: "Device group created", description: name });
        queryClient.invalidateQueries({ queryKey: ["device-groups"] });
        setShowForm(false);
      } else {
        toast({ variant: "destructive", title: "Failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Failed", description: String(exc) });
    }
  };

  const handleDelete = async (name: string) => {
    try {
      const res = await deleteDeviceGroup(name);
      if (!res.error) {
        toast({ title: "Deleted", description: name });
        queryClient.invalidateQueries({ queryKey: ["device-groups"] });
      } else {
        toast({ variant: "destructive", title: "Delete failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Delete failed", description: String(exc) });
    } finally {
      setPendingDelete(null);
    }
  };

  const handleAddApps = async (dg: string) => {
    const apps = selectedApps[dg] ?? [];
    if (apps.length === 0) return;
    try {
      const res = await addAppsToDeviceGroup(dg, apps);
      if (!res.error) {
        toast({ title: "Apps added", description: `${apps.join(", ")} → ${dg}` });
        queryClient.invalidateQueries({ queryKey: ["device-groups"] });
        setSelectedApps((prev) => ({ ...prev, [dg]: [] }));
      } else {
        toast({ variant: "destructive", title: "Failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Failed", description: String(exc) });
    }
  };

  const handleRemoveApp = async (dg: string, app: string) => {
    try {
      const res = await removeAppsFromDeviceGroup(dg, [app]);
      if (!res.error) {
        toast({ title: "App removed", description: `${app} removed from ${dg}` });
        queryClient.invalidateQueries({ queryKey: ["device-groups"] });
      } else {
        toast({ variant: "destructive", title: "Remove failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Remove failed", description: String(exc) });
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Device Groups</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Group"}
        </Button>
      </div>

      {showForm && (
        <div className="mb-8">
          <DeviceGroupForm onSubmit={handleCreate} />
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
      ) : isError ? (
        <p className="text-red-600 text-sm py-8 text-center">Could not load device groups — is the API server running?</p>
      ) : groups.length === 0 ? (
        <p className="text-gray-500 text-center py-12">No device groups found.</p>
      ) : (
        <div className="space-y-4">
          {groups.map(({ name: dg, apps: currentApps }) => (
            <Card key={dg}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{dg}</CardTitle>
                  <Button size="sm" variant="destructive" onClick={() => setPendingDelete(dg)}>Delete Group</Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Current apps — each with a remove button */}
                <div>
                  <p className="text-sm font-medium mb-2">
                    Current Apps {currentApps.length > 0 ? `(${currentApps.length})` : ""}
                  </p>
                  {currentApps.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No apps assigned</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {currentApps.map((app) => (
                        <Badge key={app} variant="secondary" className="flex items-center gap-1 pr-1">
                          {app}
                          <button
                            className="ml-1 rounded-full hover:bg-destructive/20 text-destructive px-1 text-xs leading-none"
                            onClick={() => handleRemoveApp(dg, app)}
                            title={`Remove ${app} from ${dg}`}
                          >
                            ✕
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                {/* Add apps — only show apps not already in this group */}
                <div className="border-t pt-3">
                  <AppSelector
                    selected={selectedApps[dg] ?? []}
                    exclude={currentApps}
                    onChange={(apps) => setSelectedApps((prev) => ({ ...prev, [dg]: apps }))}
                  />
                  <Button
                    size="sm"
                    className="mt-2"
                    onClick={() => handleAddApps(dg)}
                    disabled={(selectedApps[dg]?.length ?? 0) === 0}
                  >
                    Add Selected Apps
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <AlertDialog open={!!pendingDelete} onOpenChange={(open) => { if (!open) setPendingDelete(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete device group?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{pendingDelete}&quot;? This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => pendingDelete && handleDelete(pendingDelete)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
