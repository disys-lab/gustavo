"use client";
import { useQuery } from "@tanstack/react-query";
import { getRegistryImages } from "@/lib/api/apps";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

interface RegistryImage {
  name: string;
  tags: string[];
}

interface RegistryResponse {
  images?: RegistryImage[];
  registry_url?: string;
  catalog_url?: string;
  message?: string;
  raw_catalog?: unknown;
  raw_response?: string;
}

export default function RegistryPage() {
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["registry-images"],
    queryFn: getRegistryImages,
  });

  const resp = data?.response as RegistryResponse | undefined;
  const registryUrl = resp?.registry_url ?? "";
  const catalogUrl = resp?.catalog_url ?? "";
  const images: RegistryImage[] = (!data?.error && resp?.images) ? resp.images : [];
  const apiError = data?.error ? (resp?.message ?? "Unknown error") : null;
  const rawCatalog = resp?.raw_catalog;
  const rawResponse = resp?.raw_response;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Registry</h1>
          {registryUrl && (
            <p className="text-sm text-muted-foreground mt-0.5 font-mono">{registryUrl}</p>
          )}
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          {isFetching ? "Refreshing…" : "Refresh"}
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-14" />)}
        </div>
      ) : apiError ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700 space-y-2">
          <p className="font-medium">
            Could not reach registry{registryUrl ? ` at ${registryUrl}` : ""}
          </p>
          {catalogUrl && <p className="font-mono text-xs">GET {catalogUrl}</p>}
          <p className="font-mono text-xs break-all">{apiError}</p>
          {rawResponse && (
            <pre className="font-mono text-xs break-all whitespace-pre-wrap bg-red-100 rounded p-2">
              {rawResponse}
            </pre>
          )}
          <p className="text-xs text-red-500">
            The API is using REGISTRY_HOST / REGISTRY_PORT from{" "}
            <Link href="/settings" className="underline font-medium">Settings</Link>.
            If these differ from your Streamlit config, download the <code>.env</code>{" "}
            from the old app and upload it on the Settings page.
          </p>
        </div>
      ) : images.length === 0 ? (
        <div className="space-y-4 py-8">
          <p className="text-muted-foreground text-center">
            No images found{registryUrl ? ` in registry at ${registryUrl}` : ""}.
          </p>
          <div className="rounded-md border bg-muted/40 p-3 space-y-2 text-xs font-mono">
            {catalogUrl && <p><span className="text-muted-foreground">GET </span>{catalogUrl}</p>}
            <p className="text-muted-foreground font-sans font-medium">Raw response:</p>
            <pre className="break-all whitespace-pre-wrap">
              {rawCatalog !== undefined
                ? JSON.stringify(rawCatalog, null, 2)
                : rawResponse ?? "(no response body)"}
            </pre>
          </div>
          <p className="text-xs text-muted-foreground text-center">
            Verify REGISTRY_HOST / REGISTRY_PORT in{" "}
            <Link href="/settings" className="underline">Settings</Link>{" "}
            or upload your existing <code className="bg-muted px-1 rounded">.env</code> file there.
          </p>
        </div>
      ) : (
        <div className="rounded-md border divide-y">
          {images.map((img) => (
            <div key={img.name} className="flex items-center gap-4 px-4 py-3">
              <span className="font-mono text-sm font-medium flex-1 truncate">
                {registryUrl
                  ? `${registryUrl.replace(/^https?:\/\//, "")}/${img.name}`
                  : img.name}
              </span>
              <div className="flex flex-wrap gap-1.5 justify-end">
                {img.tags.length === 0 ? (
                  <span className="text-xs text-muted-foreground">no tags</span>
                ) : (
                  img.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="font-mono text-xs">
                      {tag}
                    </Badge>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
