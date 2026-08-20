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
import { listGroups, createGroup, updateGroup, deleteGroup } from "@/lib/api/users";
import { useActivityToast } from "@/hooks/use-activity-toast";
import type { UserGroup } from "@/lib/types/users";

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
            Roles, backed directly by Nebula user_groups. App/device-group grants are shown
            here read-only — they&apos;re usually set automatically when a member creates an app.
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
