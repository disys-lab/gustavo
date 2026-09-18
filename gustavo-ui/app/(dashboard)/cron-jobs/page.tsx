"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listCronJobs, createCronJob } from "@/lib/api/cronJobs";
import { CronJobForm, CronJobFormValues } from "@/components/cron-jobs/CronJobForm";
import { parseCronJobConfig } from "@/lib/cronJobConfig";
import { CronJobExpander } from "@/components/cron-jobs/CronJobExpander";
import { YamlUpload } from "@/components/apps/YamlUpload";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { useRouter } from "next/navigation";

export default function CronJobsPage() {
  const [showForm, setShowForm] = useState(false);
  const [yamlDefaults, setYamlDefaults] = useState<Partial<CronJobFormValues> | undefined>();
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();
  const router = useRouter();

  const { data, isLoading, isError } = useQuery({ queryKey: ["cron-jobs"], queryFn: listCronJobs });

  const cronJobs: string[] = [];
  if (data && !data.error && data.response) {
    const resp = data.response as Record<string, unknown>;
    if (resp.cron_jobs && Array.isArray(resp.cron_jobs)) {
      cronJobs.push(...(resp.cron_jobs as string[]));
    }
  }

  const handleCreate = async (values: CronJobFormValues) => {
    try {
      const envVars = Object.fromEntries(values.env_vars.map((e) => [e.key, e.value]));
      const command = values.command.map((c) => c.value).filter((v) => v !== "");
      const networks = (values.networks || "nebula").split(",").map((n) => n.trim()).filter((n) => n !== "");
      const config = {
        docker_image: values.docker_image,
        schedule: values.schedule,
        env_vars: envVars,
        volumes: values.volumes.map((v) => `${v.host}:${v.container}`),
        networks,
        running: values.running,
        privileged: values.privileged,
        command,
        shm_size: values.shm_size || "",
      };
      const res = await createCronJob(
        values.name,
        config as Parameters<typeof createCronJob>[1],
        values.device_groups ?? [],
        values.owner_group || undefined,
      );
      if (!res.error) {
        toast({ title: `Cron job '${values.name}' created` });
        queryClient.invalidateQueries({ queryKey: ["cron-jobs"] });
        setShowForm(false);
      } else {
        toast({ variant: "destructive", title: "Create failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Create failed", description: String(exc) });
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Cron Jobs</h1>
        <div className="flex gap-2">
          <YamlUpload onParsed={(cfg) => {
            setYamlDefaults(parseCronJobConfig(cfg));
            setShowForm(true);
          }} />
          <Button onClick={() => { setYamlDefaults(undefined); setShowForm(!showForm); }}>
            {showForm ? "Cancel" : "+ New Cron Job"}
          </Button>
        </div>
      </div>

      {showForm && (
        <div className="mb-8">
          <CronJobForm defaultValues={yamlDefaults} onSubmit={handleCreate} />
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">{[1,2,3].map((i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : isError ? (
        <p className="text-red-600 text-sm py-8 text-center">Could not load cron jobs — is the API server running?</p>
      ) : cronJobs.length === 0 ? (
        <p className="text-gray-500 text-center py-12">No cron jobs found. Create one above.</p>
      ) : (
        <div className="space-y-3">
          {cronJobs.map((name) => (
            <CronJobExpander
              key={name}
              name={name}
              onDeleted={() => queryClient.invalidateQueries({ queryKey: ["cron-jobs"] })}
              onEdit={() => router.push(`/cron-jobs/${name}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
