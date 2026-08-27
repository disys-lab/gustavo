"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getApp, updateApp } from "@/lib/api/apps";
import { listDeviceGroups } from "@/lib/api/deviceGroups";
import { listGroups } from "@/lib/api/users";
import { AppForm, AppFormValues } from "@/components/apps/AppForm";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { useAuth } from "@/lib/context/AuthContext";

export default function EditAppPage() {
  const { name } = useParams<{ name: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();
  const { isAdmin } = useAuth();

  const { data: groupsData } = useQuery({
    queryKey: ["user-groups"],
    queryFn: listGroups,
    enabled: isAdmin,
    staleTime: 30_000,
  });
  const grantingGroups = !groupsData?.error
    ? (groupsData?.response.groups ?? [])
        .filter((g) => name in g.apps)
        .map((g) => ({ name: g.name, perm: g.apps[name] }))
    : [];

  const { data, isLoading } = useQuery({
    queryKey: ["app", name],
    queryFn: () => getApp(name),
  });

  const { data: dgData } = useQuery({
    queryKey: ["device-groups"],
    queryFn: listDeviceGroups,
    staleTime: 30_000,
  });

  const memberDeviceGroups: string[] = [];
  if (dgData && !dgData.error && dgData.response) {
    const resp = dgData.response as Record<string, unknown>;
    if (Array.isArray(resp.device_groups)) {
      for (const item of resp.device_groups) {
        if (typeof item === "object" && item !== null && "name" in item && "apps" in item) {
          const entry = item as { name: string; apps: string[] };
          if (entry.apps.includes(name)) memberDeviceGroups.push(entry.name);
        }
      }
    }
  }

  const appConfig = data?.response as Record<string, unknown> | undefined;

  const defaultValues: Partial<AppFormValues> = appConfig
    ? {
        name,
        docker_image: (appConfig.docker_image as string) ?? "",
        env_vars: Object.entries((appConfig.env_vars as Record<string, string>) ?? {}).map(([k, v]) => ({ key: k, value: v })),
        ports: ((appConfig.starting_ports as Record<string, number>[]) ?? []).map((p) => {
          const [host, container] = Object.entries(p)[0] ?? [0, 0];
          return { host: Number(host), container: Number(container) };
        }),
        volumes: ((appConfig.volumes as string[]) ?? []).map((v) => {
          const [host, container] = v.split(":") as [string, string?];
          return { host, container: container ?? "" };
        }),
        network_mode: (appConfig.network_mode as string) ?? "bridge",
        running: (appConfig.running as boolean) ?? true,
        privileged: (appConfig.privileged as boolean) ?? false,
        command: ((appConfig.command as string[]) ?? []).map((value) => ({ value })),
        shm_size: (appConfig.shm_size as string) ?? "",
      }
    : {};

  const handleUpdate = async (values: AppFormValues) => {
    try {
      const config = {
        docker_image: values.docker_image,
        env_vars: Object.fromEntries(values.env_vars.map((e) => [e.key, e.value])),
        starting_ports: values.ports.map((p) => ({ [p.host]: p.container })),
        volumes: values.volumes.map((v) => `${v.host}:${v.container}`),
        network_mode: values.network_mode,
        running: values.running,
        privileged: values.privileged,
        command: values.command.map((c) => c.value).filter((v) => v !== ""),
        shm_size: values.shm_size || "",
      };
      const res = await updateApp(name, config as Parameters<typeof updateApp>[1]);
      if (!res.error) {
        toast({ title: `App '${name}' updated` });
        queryClient.invalidateQueries({ queryKey: ["apps"] });
        queryClient.invalidateQueries({ queryKey: ["app", name] });
        router.push("/apps");
      } else {
        toast({ variant: "destructive", title: "Update failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Update failed", description: String(exc) });
    }
  };

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (data?.error) return <p className="text-red-600">App not found: {name}</p>;

  return (
    <div>
      <nav className="text-sm text-muted-foreground mb-4">
        <Link href="/apps" className="hover:text-foreground transition-colors">Apps</Link>
        <span className="mx-2">/</span>
        <span className="text-foreground font-medium">{name}</span>
      </nav>
      <h1 className="text-2xl font-bold mb-6">Edit App: {name}</h1>

      {isAdmin && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Access</CardTitle>
          </CardHeader>
          <CardContent>
            {grantingGroups.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No group currently has access to this app — only admins can manage it. Edit a group&apos;s
                grants from the <Link href="/users/groups" className="underline">Groups</Link> page.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {grantingGroups.map((g) => (
                  <Badge key={g.name} variant="secondary">{g.name} ({g.perm})</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <AppForm defaultValues={defaultValues} onSubmit={handleUpdate} submitLabel="Update App" isEdit memberDeviceGroups={memberDeviceGroups} />
    </div>
  );
}
