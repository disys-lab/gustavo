"use client";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { useConfig } from "@/lib/context/ConfigContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { uploadConfig, downloadConfig } from "@/lib/api/config";
import type { PlatformConfig } from "@/lib/types/platform";

type ConfigField = { key: keyof PlatformConfig; label: string; type?: "text" | "password" };

const PASSWORD_KEYS: Array<keyof PlatformConfig> = [
  "NEBULA_PASSWORD", "NEBULA_AUTH_TOKEN", "REDIS_AUTH_TOKEN", "MONGO_PASSWORD",
];

const MANAGER_FIELDS: ConfigField[] = [
  { key: "MANAGER_HOST", label: "Manager Host" },
  { key: "MANAGER_PORT", label: "Manager Port" },
  { key: "MANAGER_NMODE", label: "Network Mode" },
  { key: "MANAGER_IMAGE", label: "Manager Image" },
  { key: "CACHE_EXPIRE_TIME", label: "Cache Expire Time (s)" },
  { key: "NEBULA_USERNAME", label: "Nebula Username" },
  { key: "NEBULA_PASSWORD", label: "Nebula Password", type: "password" },
  { key: "NEBULA_AUTH_TOKEN", label: "Nebula Auth Token", type: "password" },
  { key: "NEBULA_PROTOCOL", label: "Protocol (http/https)" },
];

const REDIS_FIELDS: ConfigField[] = [
  { key: "REDIS_HOST", label: "Redis Host" },
  { key: "REDIS_PORT", label: "Redis Port" },
  { key: "REDIS_AUTH_TOKEN", label: "Redis Auth Token", type: "password" },
  { key: "REDIS_IMAGE", label: "Redis Image" },
  { key: "REDIS_BKP_DIR", label: "Backup Directory" },
];

const MONGO_FIELDS: ConfigField[] = [
  { key: "MONGO_HOST", label: "Mongo Host" },
  { key: "MONGO_PORT", label: "Mongo Port" },
  { key: "MONGO_USERNAME", label: "Mongo Username" },
  { key: "MONGO_PASSWORD", label: "Mongo Password", type: "password" },
  { key: "MONGO_IMAGE", label: "Mongo Image" },
  { key: "MONGO_CERTIFICATE_FOLDER_PATH", label: "Certificate Folder" },
];

const REGISTRY_FIELDS: ConfigField[] = [
  { key: "REGISTRY_HOST", label: "Registry Host" },
  { key: "REGISTRY_PORT", label: "Registry Port" },
  { key: "REGISTRY_IMAGE", label: "Registry Image" },
  { key: "REGISTRY_BKP_DIR", label: "Backup Directory" },
  { key: "REGISTRY_DATA_PATH", label: "Registry Data Path (host path to live data dir)" },
  { key: "SYNCER_IMAGE", label: "Syncer Image" },
  { key: "SYNCER_NMODE", label: "Syncer Network Mode" },
  { key: "DREGSY_CONFIG_FILE_PATH", label: "DREGSY Config File" },
  { key: "DREGSY_MAPPING_FILE_PATH", label: "DREGSY Mapping File" },
];

function FieldGrid({ fields, register }: {
  fields: ConfigField[];
  register: ReturnType<typeof useForm<PlatformConfig>>["register"];
}) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {fields.map(({ key, label, type = "text" }) => (
        <div key={key}>
          <Label htmlFor={key} className="text-xs">{label}</Label>
          <Input
            id={key}
            type={type}
            {...register(key)}
            className="mt-1"
            autoComplete="off"
            placeholder={type === "password" ? "Leave blank to keep current" : undefined}
          />
        </div>
      ))}
    </div>
  );
}

export default function SettingsPage() {
  const { config, save, refresh } = useConfig();
  const { toast } = useActivityToast();
  const fileRef = useRef<HTMLInputElement>(null);

  const { register, handleSubmit, reset, watch, setValue } = useForm<PlatformConfig>();

  const applyManagerHostToAll = () => {
    const host = watch("MANAGER_HOST");
    if (!host) return;
    setValue("REDIS_HOST", host);
    setValue("MONGO_HOST", host);
    setValue("REGISTRY_HOST", host);
  };

  useEffect(() => {
    if (Object.keys(config).length > 0) {
      const sanitized = { ...config } as Record<string, string>;
      for (const key of PASSWORD_KEYS) {
        if (sanitized[key] === "***") sanitized[key] = "";
      }
      reset(sanitized as unknown as PlatformConfig);
    }
  }, [config, reset]);

  const onSubmit = async (values: PlatformConfig) => {
    const payload = { ...values } as unknown as Record<string, string>;
    for (const key of PASSWORD_KEYS) {
      if (payload[key] === "" || payload[key] == null) delete payload[key];
    }
    const result = await save(payload as Partial<PlatformConfig>);
    if (!result.error) {
      toast({ title: "Settings saved" });
    } else {
      toast({ variant: "destructive", title: "Save failed", description: result.message });
    }
  };

  const handleUpload = async (file: File) => {
    try {
      const res = await uploadConfig(file);
      if (!res.error) {
        toast({ title: "Config loaded", description: String(res.response) });
        await refresh();
      } else {
        toast({ variant: "destructive", title: "Upload failed", description: String(res.response) });
      }
    } catch (exc) {
      toast({ variant: "destructive", title: "Upload failed", description: String(exc) });
    }
  };

  const handleDownload = async () => {
    try {
      const text = await downloadConfig();
      const blob = new Blob([text], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "manager.env";
      a.click();
      URL.revokeObjectURL(url);
    } catch (exc) {
      toast({ variant: "destructive", title: "Download failed", description: String(exc) });
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <div className="flex gap-2">
          <input
            ref={fileRef}
            type="file"
            accept=".env"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
          />
          <Button type="button" variant="outline" onClick={() => fileRef.current?.click()}>
            Upload .env
          </Button>
          <Button type="button" variant="outline" onClick={handleDownload}>
            Download .env
          </Button>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Accordion type="multiple" defaultValue={["manager"]} className="w-full border rounded-lg px-4">
          <AccordionItem value="manager">
            <AccordionTrigger className="text-sm font-semibold">Manager &amp; Nebula</AccordionTrigger>
            <AccordionContent>
              <div className="mb-4 flex items-center justify-between rounded-md border border-blue-100 bg-blue-50 px-3 py-2">
                <p className="text-xs text-blue-700">Apply Manager Host to Redis, Mongo &amp; Registry</p>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-xs h-7"
                  onClick={applyManagerHostToAll}
                >
                  Apply to all
                </Button>
              </div>
              <FieldGrid fields={MANAGER_FIELDS} register={register} />
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="redis">
            <AccordionTrigger className="text-sm font-semibold">Redis</AccordionTrigger>
            <AccordionContent>
              <FieldGrid fields={REDIS_FIELDS} register={register} />
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="mongo">
            <AccordionTrigger className="text-sm font-semibold">MongoDB</AccordionTrigger>
            <AccordionContent>
              <FieldGrid fields={MONGO_FIELDS} register={register} />
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="registry" className="border-b-0">
            <AccordionTrigger className="text-sm font-semibold">Registry &amp; Syncer</AccordionTrigger>
            <AccordionContent>
              <FieldGrid fields={REGISTRY_FIELDS} register={register} />
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        <Button type="submit" className="w-full">Save Configuration</Button>
      </form>
    </div>
  );
}
