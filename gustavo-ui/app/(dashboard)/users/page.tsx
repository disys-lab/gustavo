"use client";
import { useState } from "react";
import Link from "next/link";
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
import { Copy, Check, KeyRound, Trash2 } from "lucide-react";
import { listUsers, createUser, deleteUser, regenerateUserToken, listGroups } from "@/lib/api/users";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { copyToClipboard } from "@/lib/utils";
import type { NebulaUser } from "@/lib/types/users";

function CredentialReveal({ credential }: { credential: string }) {
  const [copied, setCopied] = useState(false);
  const { toast } = useActivityToast();
  return (
    <>
      <Alert>
        <AlertDescription>Copy this now — it won&apos;t be shown again.</AlertDescription>
      </Alert>
      <div className="flex items-center gap-2 rounded-md border bg-gray-50 px-3 py-2">
        <code className="flex-1 break-all text-sm">{credential}</code>
        <Button
          size="sm"
          variant="ghost"
          onClick={async () => {
            const ok = await copyToClipboard(credential);
            if (ok) {
              setCopied(true);
            } else {
              toast({ variant: "destructive", title: "Copy failed", description: "Select the text above and copy it manually." });
            }
          }}
        >
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
    </>
  );
}

function CreateUserDialog({ groups, onCreated }: { groups: string[]; onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState("");
  const [group, setGroup] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [credential, setCredential] = useState<string | null>(null);
  const { toast } = useActivityToast();

  const reset = () => {
    setUsername("");
    setGroup("");
    setError(null);
    setCredential(null);
  };

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      if (credential) onCreated();
      reset();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await createUser(username, group || undefined);
      if (res.error) {
        setError(String(res.response));
      } else {
        setCredential(res.response.credential);
        toast({ title: "User created", description: res.response.username });
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
        <Button>Create user</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create user</DialogTitle>
          <DialogDescription>
            Generates a new access credential — shown once, so copy it before closing.
          </DialogDescription>
        </DialogHeader>

        {!credential ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="alice"
                required
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="group">Group (optional)</Label>
              <select
                id="group"
                value={group}
                onChange={(e) => setGroup(e.target.value)}
                className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
              >
                <option value="">No group</option>
                {groups.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-400">
                A user needs to belong to a group before they can create their own apps.
              </p>
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button type="submit" disabled={loading}>
                {loading ? "Creating…" : "Create"}
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <CredentialReveal credential={credential} />
        )}
      </DialogContent>
    </Dialog>
  );
}

function RegenerateTokenAction({ username }: { username: string }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [credential, setCredential] = useState<string | null>(null);

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setError(null);
      setCredential(null);
    }
  };

  const handleRegenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await regenerateUserToken(username);
      if (res.error) setError(String(res.response));
      else setCredential(res.response.credential);
    } catch (exc) {
      setError(String(exc));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm" variant="ghost" title="Regenerate credential">
          <KeyRound className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Regenerate credential for {username}</DialogTitle>
          <DialogDescription>Their current credential stops working immediately.</DialogDescription>
        </DialogHeader>
        {!credential ? (
          <>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button onClick={handleRegenerate} disabled={loading}>
                {loading ? "Generating…" : "Generate new credential"}
              </Button>
            </DialogFooter>
          </>
        ) : (
          <CredentialReveal credential={credential} />
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function UsersPage() {
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();

  const { data: usersData, isLoading } = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const { data: groupsData } = useQuery({ queryKey: ["user-groups"], queryFn: listGroups });

  const users: NebulaUser[] = !usersData?.error ? usersData?.response.users ?? [] : [];
  const groupNames: string[] = !groupsData?.error ? (groupsData?.response.groups ?? []).map((g) => g.name) : [];

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["users"] });

  const handleDelete = async (username: string) => {
    const res = await deleteUser(username);
    if (res.error) {
      toast({ variant: "destructive", title: "Delete failed", description: String(res.response) });
    } else {
      toast({ title: "User deleted", description: username });
      refresh();
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Users</h1>
          <p className="text-sm text-gray-500">
            Backed by Nebula&apos;s own user/user_group accounts — no separate password store.{" "}
            <Link href="/users/groups" className="underline">Manage groups (roles)</Link>
          </p>
        </div>
        <CreateUserDialog groups={groupNames} onCreated={refresh} />
      </div>

      {isLoading ? (
        <Skeleton className="h-32" />
      ) : users.length === 0 ? (
        <p className="text-gray-400 text-sm text-center py-8">No users yet.</p>
      ) : (
        <div className="overflow-auto rounded border">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Username</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Groups</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Role</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600 w-24">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.username} className="border-b">
                  <td className="px-4 py-2 font-mono">{u.username}</td>
                  <td className="px-4 py-2">
                    <div className="flex flex-wrap gap-1">
                      {u.groups.length === 0 ? (
                        <span className="text-gray-400">—</span>
                      ) : (
                        u.groups.map((g) => (
                          <Badge key={g} variant="secondary">{g}</Badge>
                        ))
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    {u.is_admin ? <Badge>Admin</Badge> : <span className="text-gray-400">User</span>}
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-1">
                      <RegenerateTokenAction username={u.username} />
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button size="sm" variant="ghost" className="text-red-600 hover:text-red-700" title="Delete user">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete user &apos;{u.username}&apos;?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This removes the account from Nebula and from any groups it belongs to. Their credential stops working immediately.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleDelete(u.username)}>Delete</AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
