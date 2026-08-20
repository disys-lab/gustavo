"use client";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getRegistryImages, getAppDefaults } from "@/lib/api/apps";
import { listDeviceGroups } from "@/lib/api/deviceGroups";
import { getMyGroups } from "@/lib/api/users";
import { useAuth } from "@/lib/context/AuthContext";

const envVarSchema = z.object({ key: z.string(), value: z.string() });
const portSchema = z.object({ host: z.number().int().min(0), container: z.number().int().min(0) });
const volumeSchema = z.object({ host: z.string(), container: z.string() });

const appFormSchema = z.object({
  name: z.string().min(1, "Name is required").regex(/^[a-z0-9_-]+$/, "Lowercase, numbers, dashes, underscores only"),
  docker_image: z.string().min(1, "Docker image is required"),
  env_vars: z.array(envVarSchema),
  ports: z.array(portSchema),
  volumes: z.array(volumeSchema),
  network_mode: z.string().optional(),
  running: z.boolean(),
  privileged: z.boolean(),
  device_groups: z.array(z.string()),
  owner_group: z.string().optional(),
});

export type AppFormValues = z.infer<typeof appFormSchema>;

interface AppFormProps {
  defaultValues?: Partial<AppFormValues>;
  onSubmit: (values: AppFormValues) => Promise<void>;
  submitLabel?: string;
  isEdit?: boolean;
  memberDeviceGroups?: string[];
}

export function AppForm({ defaultValues, onSubmit, submitLabel = "Create App", isEdit = false, memberDeviceGroups = [] }: AppFormProps) {
  const { isAdmin } = useAuth();

  const { data: myGroupsData } = useQuery({
    queryKey: ["my-groups"],
    queryFn: getMyGroups,
    enabled: !isEdit && !isAdmin,
    staleTime: 30_000,
  });
  const myGroups: string[] = !myGroupsData?.error ? myGroupsData?.response.groups ?? [] : [];

  const { data: registryData } = useQuery({
    queryKey: ["registry-images"],
    queryFn: getRegistryImages,
    staleTime: 60_000,
  });

  const { data: dgData } = useQuery({
    queryKey: ["device-groups"],
    queryFn: listDeviceGroups,
    staleTime: 30_000,
    enabled: !isEdit,
  });

  const registryOptions: string[] = [];
  if (registryData && !registryData.error && registryData.response) {
    const resp = registryData.response as { images?: { name: string; tags: string[] }[]; registry_url?: string };
    const base = (resp.registry_url ?? "").replace(/^https?:\/\//, "");
    (resp.images ?? []).forEach(({ name, tags }) => {
      if (tags.length === 0) {
        registryOptions.push(base ? `${base}/${name}` : name);
      } else {
        tags.forEach((tag) => registryOptions.push(base ? `${base}/${name}:${tag}` : `${name}:${tag}`));
      }
    });
  }

  const allDeviceGroups: string[] = [];
  if (dgData && !dgData.error && dgData.response) {
    const resp = dgData.response as Record<string, unknown>;
    if (Array.isArray(resp.device_groups)) {
      for (const item of resp.device_groups) {
        if (typeof item === "object" && item !== null && "name" in item) {
          allDeviceGroups.push((item as { name: string }).name);
        } else if (typeof item === "string") {
          allDeviceGroups.push(item);
        }
      }
    }
  }

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AppFormValues>({
    resolver: zodResolver(appFormSchema),
    defaultValues: {
      name: "",
      docker_image: "",
      env_vars: [],
      ports: [],
      volumes: [] as { host: string; container: string }[],
      network_mode: "bridge",
      running: true,
      privileged: false,
      device_groups: [],
      owner_group: "",
      ...defaultValues,
    },
  });

  const envFields = useFieldArray({ control, name: "env_vars" });
  const portFields = useFieldArray({ control, name: "ports" });
  const volumeFields = useFieldArray({ control, name: "volumes" });

  // Fetch server-side defaults (with real unmasked secrets) for create mode only
  const { data: defaultsData } = useQuery({
    queryKey: ["app-defaults"],
    queryFn: getAppDefaults,
    enabled: !isEdit,
    staleTime: Infinity, // config rarely changes mid-session
  });

  useEffect(() => {
    if (isEdit || !defaultsData || defaultsData.error) return;
    const resp = defaultsData.response as { env_vars: Record<string, string> };
    const serverEnvVars = Object.entries(resp.env_vars ?? {}).map(([key, value]) => ({ key, value }));
    reset((prev) => ({ ...prev, env_vars: serverEnvVars }));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultsData]);

  const selectedDGs = watch("device_groups");
  const toggleDG = (dg: string) => {
    if (selectedDGs.includes(dg)) {
      setValue("device_groups", selectedDGs.filter((d) => d !== dg));
    } else {
      setValue("device_groups", [...selectedDGs, dg]);
    }
  };

  const handleFormSubmit = handleSubmit(async (values) => {
    await onSubmit(values);
  });

  return (
    <form onSubmit={handleFormSubmit} className="space-y-6">
      {/* Basic info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Basic Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="name">App Name</Label>
            <Input id="name" {...register("name")} disabled={isEdit} className="mt-1" />
            {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>}
          </div>
          <div>
            <Label htmlFor="docker_image">
              Docker Image
              {registryOptions.length > 0 && (
                <span className="ml-2 text-xs text-muted-foreground font-normal">
                  ({registryOptions.length} from registry)
                </span>
              )}
            </Label>
            <Input
              id="docker_image"
              {...register("docker_image")}
              className="mt-1"
              placeholder="registry:host/image:tag"
              list="registry-images-list"
              autoComplete="off"
            />
            {registryOptions.length > 0 && (
              <datalist id="registry-images-list">
                {registryOptions.map((opt) => (
                  <option key={opt} value={opt} />
                ))}
              </datalist>
            )}
            {errors.docker_image && <p className="text-sm text-red-600 mt-1">{errors.docker_image.message}</p>}
          </div>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" {...register("running")} /> Running on deploy
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" {...register("privileged")} /> Privileged
            </label>
          </div>
          <div>
            <Label htmlFor="network_mode">Network Mode</Label>
            <Input id="network_mode" {...register("network_mode")} className="mt-1" placeholder="bridge" />
          </div>
        </CardContent>
      </Card>

      {/* Owner group — only relevant for non-admins creating a new app */}
      {!isEdit && !isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Owner Group</CardTitle>
          </CardHeader>
          <CardContent>
            {myGroups.length === 0 ? (
              <p className="text-sm text-red-600">
                You&apos;re not a member of any group yet — ask an admin to add you to one before creating apps.
              </p>
            ) : myGroups.length === 1 ? (
              <p className="text-sm text-muted-foreground">
                This app will be owned by your group <strong>{myGroups[0]}</strong>.
              </p>
            ) : (
              <div>
                <Label htmlFor="owner_group">Which group should own this app?</Label>
                <select
                  id="owner_group"
                  {...register("owner_group")}
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                >
                  <option value="">Select a group…</option>
                  {myGroups.map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Device Groups */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Device Groups</CardTitle>
        </CardHeader>
        <CardContent>
          {isEdit ? (
            memberDeviceGroups.length === 0 ? (
              <p className="text-sm text-muted-foreground">Not assigned to any device group</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {memberDeviceGroups.map((dg) => (
                  <Badge key={dg} variant="outline" className="opacity-50 cursor-default">
                    {dg}
                  </Badge>
                ))}
              </div>
            )
          ) : (
            <>
              {allDeviceGroups.length === 0 ? (
                <p className="text-sm text-muted-foreground">No device groups available</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {allDeviceGroups.map((dg) => (
                    <Badge
                      key={dg}
                      variant={selectedDGs.includes(dg) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleDG(dg)}
                    >
                      {dg}
                    </Badge>
                  ))}
                </div>
              )}
              {selectedDGs.length > 0 && (
                <p className="text-xs text-muted-foreground mt-2">
                  Selected: {selectedDGs.join(", ")}
                </p>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Environment variables */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Environment Variables</CardTitle>
            <Button type="button" size="sm" variant="outline" onClick={() => envFields.append({ key: "", value: "" })}>
              + Add
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {envFields.fields.map((field, idx) => (
            <div key={field.id} className="flex gap-2 items-center">
              <Input placeholder="KEY" {...register(`env_vars.${idx}.key`)} className="flex-1" />
              <Input placeholder="value" {...register(`env_vars.${idx}.value`)} className="flex-1" />
              <Button type="button" size="sm" variant="ghost" onClick={() => envFields.remove(idx)}>✕</Button>
            </div>
          ))}
          {envFields.fields.length === 0 && <p className="text-sm text-gray-400">No env vars</p>}
        </CardContent>
      </Card>

      {/* Ports */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Port Mappings</CardTitle>
            <Button type="button" size="sm" variant="outline" onClick={() => portFields.append({ host: 0, container: 0 })}>
              + Add
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {portFields.fields.map((field, idx) => (
            <div key={field.id} className="flex gap-2 items-center">
              <Input placeholder="Host port" type="number" {...register(`ports.${idx}.host`, { valueAsNumber: true })} className="flex-1" />
              <span className="text-gray-400">→</span>
              <Input placeholder="Container port" type="number" {...register(`ports.${idx}.container`, { valueAsNumber: true })} className="flex-1" />
              <Button type="button" size="sm" variant="ghost" onClick={() => portFields.remove(idx)}>✕</Button>
            </div>
          ))}
          {portFields.fields.length === 0 && <p className="text-sm text-gray-400">No port mappings</p>}
        </CardContent>
      </Card>

      {/* Volumes */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Volumes</CardTitle>
            <Button type="button" size="sm" variant="outline" onClick={() => volumeFields.append({ host: "", container: "" })}>
              + Add
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {volumeFields.fields.map((field, idx) => (
            <div key={field.id} className="flex gap-2 items-center">
              <Input placeholder="Host path" {...register(`volumes.${idx}.host`)} className="flex-1" />
              <span className="text-gray-400">→</span>
              <Input placeholder="Container path" {...register(`volumes.${idx}.container`)} className="flex-1" />
              <Button type="button" size="sm" variant="ghost" onClick={() => volumeFields.remove(idx)}>✕</Button>
            </div>
          ))}
          {volumeFields.fields.length === 0 && <p className="text-sm text-gray-400">No volumes</p>}
        </CardContent>
      </Card>

      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}
