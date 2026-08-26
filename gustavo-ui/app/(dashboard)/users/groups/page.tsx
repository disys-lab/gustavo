"use client";
import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Trash2 } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle,
  AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { listGroups, createGroup, updateGroup, deleteGroup, addGroupGrant, removeGroupGrant } from "@/lib/api/users";
import { listApps } from "@/lib/api/apps";
import { listDeviceGroups } from "@/lib/api/deviceGroups";
import { useActivityToast } from "@/hooks/use-activity-toast";
import type { UserGroup } from "@/lib/types/users";

const selectClass =
  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm";

interface GroupFormState {
  name: string;
  members: string;
  admin: boolean;
  pruning_allowed: boolean;
}

function GroupFormDialog({
  trigger, initial, onSubmit, title,
}: {
  trigger: React.ReactNode;
  initial: GroupFormState;
  title: string;
  onSubmit: (state: GroupFormState) => Promise<{ error: boolean; response: unknown }>;
}) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<GroupFormState>(initial);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setState(initial);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await onSubmit(state);
      if (res.error) setError(String(res.response));
      else setOpen(false);
    } catch (exc) {
      setError(String(exc));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            A group is a role: its members share whatever apps/device-groups it&apos;s been granted.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="group-name">Name</Label>
            <Input
              id="group-name"
              value={state.name}
              onChange={(e) => setState({ ...state, name: e.target.value })}
              disabled={!!initial.name}
              required
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="group-members">Members (comma-separated usernames)</Label>
            <Input
              id="group-members"
              value={state.members}
              onChange={(e) => setState({ ...state, members: e.target.value })}
              placeholder="alice, bob"
              className="mt-1"
            />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={state.admin}
                onChange={(e) => setState({ ...state, admin: e.target.checked })}
              />
              Admin (bypasses all app/device-group grants)
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={state.pruning_allowed}
                onChange={(e) => setState({ ...state, pruning_allowed: e.target.checked })}
              />
              Pruning allowed
            </label>
          </div>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <DialogFooter>
            <Button type="submit" disabled={loading}>{loading ? "Saving…" : "Save"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function toMembers(text: string): string[] {
  return text.split(",").map((m) => m.trim()).filter(Boolean);
}

function GrantDialog({ group, onChanged }: { group: UserGroup; onChanged: () => void }) {
  const [open, setOpen] = useState(false);
  const [resourceType, setResourceType] = useState<"app" | "device_group">("app");
  const [resourceName, setResourceName] = useState("");
  const [perm, setPerm] = useState<"ro" | "rw">("rw");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useActivityToast();

  const { data: appsData } = useQuery({ queryKey: ["apps"], queryFn: listApps, enabled: open });
  const { data: dgData } = useQuery({ queryKey: ["device-groups"], queryFn: listDeviceGroups, enabled: open });

  const appNames: string[] = [];
  if (appsData && !appsData.error && appsData.response) {
    const resp = appsData.response as Record<string, unknown>;
    if (Array.isArray(resp.apps)) appNames.push(...(resp.apps as string[]));
  }
  const dgNames: string[] = [];
  if (dgData && !dgData.error && dgData.response) {
    const resp = dgData.response as Record<string, unknown>;
    if (Array.isArray(resp.device_groups)) {
      dgNames.push(...(resp.device_groups as { name: string }[]).map((d) => d.name));
    }
  }
  const options = resourceType === "app" ? appNames : dgNames;

  // Already-granted state drives the whole adaptive part of this dialog: whichever
  // resource is currently selected, look it up in this group's own apps/device_groups
  // map (already loaded with the group, no extra fetch) to see if it's already granted.
  const grantMap = resourceType === "app" ? group.apps : group.device_groups;
  const currentPerm = resourceName ? grantMap[resourceName] : undefined;
  const isGranted = currentPerm !== undefined;

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setResourceType("app");
      setResourceName("");
      setPerm("rw");
      setError(null);
    }
  };

  const handleResourceNameChange = (name: string) => {
    setResourceName(name);
    const existing = resourceType === "app" ? group.apps[name] : group.device_groups[name];
    setPerm(existing ?? "rw");
  };

  const handleGrant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resourceName) return;
    setLoading(true);
    setError(null);
    try {
      const res = await addGroupGrant(group.name, resourceType, resourceName, perm);
      if (res.error) {
        setError(String(res.response));
      } else {
        toast({ title: isGranted ? "Grant updated" : "Grant added", description: `${resourceName} (${perm}) → ${group.name}` });
        setOpen(false);
        onChanged();
      }
    } catch (exc) {
      setError(String(exc));
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async () => {
    if (!resourceName) return;
    setLoading(true);
    setError(null);
    try {
      const res = await removeGroupGrant(group.name, resourceType, resourceName);
      if (res.error) {
        setError(String(res.response));
      } else {
        toast({ title: "Grant revoked", description: `${resourceName} ← ${group.name}` });
        setOpen(false);
        onChanged();
      }
    } catch (exc) {
      setError(String(exc));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">Grants</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Grants for &apos;{group.name}&apos;</DialogTitle>
          <DialogDescription>
            Pick an app or device group. Already granted to this group? Change its permission or revoke it.
            Not granted yet? Add it.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleGrant} className="space-y-4">
          <div>
            <Label htmlFor="grant-type">Resource type</Label>
            <select
              id="grant-type"
              className={`${selectClass} mt-1`}
              value={resourceType}
              onChange={(e) => {
                setResourceType(e.target.value as "app" | "device_group");
                setResourceName("");
                setPerm("rw");
              }}
            >
              <option value="app">App</option>
              <option value="device_group">Device group</option>
            </select>
          </div>
          <div>
            <Label htmlFor="grant-name">{resourceType === "app" ? "App" : "Device group"}</Label>
            <select
              id="grant-name"
              className={`${selectClass} mt-1`}
              value={resourceName}
              onChange={(e) => handleResourceNameChange(e.target.value)}
              required
            >
              <option value="" disabled>Select…</option>
              {options.map((name) => (
                <option key={name} value={name}>
                  {name}{name in grantMap ? ` (currently ${grantMap[name]})` : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="grant-perm">Permission</Label>
            <select
              id="grant-perm"
              className={`${selectClass} mt-1`}
              value={perm}
              onChange={(e) => setPerm(e.target.value as "ro" | "rw")}
            >
              <option value="rw">Read/write</option>
              <option value="ro">Read-only</option>
            </select>
          </div>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <DialogFooter>
            {isGranted && (
              <Button
                type="button"
                variant="outline"
                className="text-red-600 hover:text-red-700"
                disabled={loading}
                onClick={handleRevoke}
              >
                {loading ? "Revoking…" : "Revoke"}
              </Button>
            )}
            <Button type="submit" disabled={loading || !resourceName}>
              {loading ? "Saving…" : isGranted ? "Update" : "Grant"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function GroupsPage() {
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();
  const { data, isLoading } = useQuery({ queryKey: ["user-groups"], queryFn: listGroups });
  const groups: UserGroup[] = !data?.error ? data?.response.groups ?? [] : [];

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["user-groups"] });
    queryClient.invalidateQueries({ queryKey: ["users"] });
  };

  const handleDelete = async (name: string) => {
    const res = await deleteGroup(name);
    if (res.error) {
      toast({ variant: "destructive", title: "Delete failed", description: String(res.response) });
    } else {
      toast({ title: "Group deleted", description: name });
      refresh();
    }
  };

  return (
    <div>
      <Link href="/users" className="mb-4 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Users
      </Link>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Groups</h1>
          <p className="text-sm text-gray-500">
            Roles, backed directly by Nebula user_groups. Grants are set automatically when a
            member creates an app, or added directly here via each group&apos;s &quot;Add grant&quot;.
          </p>
        </div>
        <GroupFormDialog
          title="Create group"
          trigger={<Button>Create group</Button>}
          initial={{ name: "", members: "", admin: false, pruning_allowed: false }}
          onSubmit={(state) =>
            createGroup({
              name: state.name,
              group_members: toMembers(state.members),
              apps: {},
              device_groups: {},
              admin: state.admin,
              pruning_allowed: state.pruning_allowed,
              cron_jobs: {},
            }).then((res) => {
              if (!res.error) { toast({ title: "Group created", description: state.name }); refresh(); }
              return res;
            })
          }
        />
      </div>

      {isLoading ? (
        <Skeleton className="h-32" />
      ) : groups.length === 0 ? (
        <p className="text-gray-400 text-sm text-center py-8">No groups yet.</p>
      ) : (
        <div className="space-y-3">
          {groups.map((g) => (
            <div key={g.name} className="rounded border p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold">{g.name}</span>
                    {g.admin && <Badge>Admin</Badge>}
                    {g.pruning_allowed && <Badge variant="secondary">Pruning</Badge>}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {g.group_members.length === 0 ? (
                      <span className="text-sm text-gray-400">No members</span>
                    ) : (
                      g.group_members.map((m) => <Badge key={m} variant="outline">{m}</Badge>)
                    )}
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    Apps: {Object.keys(g.apps).length === 0 ? "none" : Object.entries(g.apps).map(([a, perm]) => `${a} (${perm})`).join(", ")}
                    {" · "}
                    Device groups: {Object.keys(g.device_groups).length === 0 ? "none" : Object.entries(g.device_groups).map(([d, perm]) => `${d} (${perm})`).join(", ")}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <GrantDialog group={g} onChanged={refresh} />
                  <GroupFormDialog
                    title={`Edit ${g.name}`}
                    trigger={<Button size="sm" variant="outline">Edit</Button>}
                    initial={{
                      name: g.name,
                      members: g.group_members.join(", "),
                      admin: g.admin,
                      pruning_allowed: g.pruning_allowed,
                    }}
                    onSubmit={(state) =>
                      updateGroup(g.name, {
                        group_members: toMembers(state.members),
                        admin: state.admin,
                        pruning_allowed: state.pruning_allowed,
                      }).then((res) => {
                        if (!res.error) { toast({ title: "Group updated", description: g.name }); refresh(); }
                        return res;
                      })
                    }
                  />
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button size="sm" variant="ghost" className="text-red-600 hover:text-red-700">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete group &apos;{g.name}&apos;?</AlertDialogTitle>
                        <AlertDialogDescription>
                          Members lose whatever this group granted them. This doesn&apos;t delete the member accounts themselves.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={() => handleDelete(g.name)}>Delete</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
