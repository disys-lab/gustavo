"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getCronJob, updateCronJob } from "@/lib/api/cronJobs";
import { listDeviceGroups } from "@/lib/api/deviceGroups";
import { listGroups } from "@/lib/api/users";
import { CronJobForm, CronJobFormValues } from "@/components/cron-jobs/CronJobForm";
import { parseCronJobConfig } from "@/lib/cronJobConfig";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { useAuth } from "@/lib/context/AuthContext";

export default function EditCronJobPage() {
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
        .filter((g) => name in g.cron_jobs)
        .map((g) => ({ name: g.name, perm: g.cron_jobs[name] }))
    : [];

  const { data, isLoading } = useQuery({
    queryKey: ["cron-job", name],
    queryFn: () => getCronJob(name),
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
        if (typeof item === "object" && item !== null && "name" in item && "cron_jobs" in item) {
          const entry = item as { name: string; cron_jobs: string[] };
          if (entry.cron_jobs.includes(name)) memberDeviceGroups.push(entry.name);
        }
      }
    }
  }

  const cronJobConfig = data?.response as Record<string, unknown> | undefined;

  const defaultValues: Partial<CronJobFormValues> = cronJobConfig
    ? { name, ...parseCronJobConfig(cronJobConfig) }
    : {};

  const handleUpdate = async (values: CronJobFormValues) => {
    try {
      const networks = (values.networks || "nebula").split(",").map((n) => n.trim()).filter((n) => n !== "");
      const config = {
        docker_image: values.docker_image,
        schedule: values.schedule,
        env_vars: Object.fromEntries(values.env_vars.map((e) => [e.key, e.value])),
        volumes: values.volumes.map((v) => `${v.host}:${v.container}`),
        networks,
        running: values.running,
        privileged: values.privileged,
        command: values.command.map((c) => c.value).filter((v) => v !== ""),
        shm_size: values.shm_size || "",
      };
      const res = await updateCronJob(name, config as Parameters<typeof updateCronJob>[1]);
      if (!res.error) {
        toast({ title: `Cron job '${name}' updated` });
        queryClient.invalidateQueries({ queryKey: ["cron-jobs"] });
        queryClient.invalidateQueries({ queryKey: ["cron-job", name] });
        router.push("/cron-jobs");
      } else {
        toast({ variant: "destructive", title: "Update failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Update failed", description: String(exc) });
    }
  };

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (data?.error) return <p className="text-red-600">Cron job not found: {name}</p>;

  return (
    <div>
      <nav className="text-sm text-muted-foreground mb-4">
        <Link href="/cron-jobs" className="hover:text-foreground transition-colors">Cron Jobs</Link>
        <span className="mx-2">/</span>
        <span className="text-foreground font-medium">{name}</span>
      </nav>
      <h1 className="text-2xl font-bold mb-6">Edit Cron Job: {name}</h1>

      {isAdmin && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Access</CardTitle>
          </CardHeader>
          <CardContent>
            {grantingGroups.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No group currently has access to this cron job — only admins can manage it. Edit a group&apos;s
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

      <CronJobForm defaultValues={defaultValues} onSubmit={handleUpdate} submitLabel="Update Cron Job" isEdit memberDeviceGroups={memberDeviceGroups} />
    </div>
  );
}
