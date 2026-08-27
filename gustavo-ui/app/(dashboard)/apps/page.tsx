"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listApps, createApp } from "@/lib/api/apps";
import { AppForm, AppFormValues } from "@/components/apps/AppForm";
import { AppExpander } from "@/components/apps/AppExpander";
import { YamlUpload } from "@/components/apps/YamlUpload";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { useRouter } from "next/navigation";

export default function AppsPage() {
  const [showForm, setShowForm] = useState(false);
  const [yamlDefaults, setYamlDefaults] = useState<Partial<AppFormValues> | undefined>();
  const queryClient = useQueryClient();
  const { toast } = useActivityToast();
  const router = useRouter();

  const { data, isLoading, isError } = useQuery({ queryKey: ["apps"], queryFn: listApps });

  const apps: string[] = [];
  if (data && !data.error && data.response) {
    const resp = data.response as Record<string, unknown>;
    if (resp.apps && Array.isArray(resp.apps)) {
      apps.push(...(resp.apps as string[]));
    }
  }

  const handleCreate = async (values: AppFormValues) => {
    try {
      const envVars = Object.fromEntries(values.env_vars.map((e) => [e.key, e.value]));
      envVars["APP_ID"] = values.name;
      const command = values.command.map((c) => c.value).filter((v) => v !== "");
      const config = {
        docker_image: values.docker_image,
        env_vars: envVars,
        starting_ports: values.ports.map((p) => ({ [p.host]: p.container })),
        volumes: values.volumes.map((v) => `${v.host}:${v.container}`),
        network_mode: values.network_mode || "bridge",
        running: values.running,
        privileged: values.privileged,
        command,
        shm_size: values.shm_size || "",
      };
      const res = await createApp(
        values.name,
        config as Parameters<typeof createApp>[1],
        values.device_groups ?? [],
        values.owner_group || undefined,
      );
      if (!res.error) {
        toast({ title: `App '${values.name}' created` });
        queryClient.invalidateQueries({ queryKey: ["apps"] });
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
        <h1 className="text-2xl font-bold">Apps</h1>
        <div className="flex gap-2">
          <YamlUpload onParsed={(cfg) => {
            setYamlDefaults({ docker_image: cfg.docker_image as string });
            setShowForm(true);
          }} />
          <Button onClick={() => { setYamlDefaults(undefined); setShowForm(!showForm); }}>
            {showForm ? "Cancel" : "+ New App"}
          </Button>
        </div>
      </div>

      {showForm && (
        <div className="mb-8">
          <AppForm defaultValues={yamlDefaults} onSubmit={handleCreate} />
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">{[1,2,3].map((i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : isError ? (
        <p className="text-red-600 text-sm py-8 text-center">Could not load apps — is the API server running?</p>
      ) : apps.length === 0 ? (
        <p className="text-gray-500 text-center py-12">No apps found. Create one above.</p>
      ) : (
        <div className="space-y-3">
          {apps.map((name) => (
            <AppExpander
              key={name}
              name={name}
              onDeleted={() => queryClient.invalidateQueries({ queryKey: ["apps"] })}
              onEdit={() => router.push(`/apps/${name}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
