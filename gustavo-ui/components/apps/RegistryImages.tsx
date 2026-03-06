"use client";
import { useQuery } from "@tanstack/react-query";
import { getRegistryImages } from "@/lib/api/apps";
import { useConfig } from "@/lib/context/ConfigContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

interface RegistryImage {
  name: string;
  tags: string[];
}

export function RegistryImages() {
  const { config } = useConfig();
  const host = config.REGISTRY_HOST || "registry";
  const port = config.REGISTRY_PORT || "5000";

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["registry-images"],
    queryFn: getRegistryImages,
  });

  const images: RegistryImage[] = [];
  if (data && !data.error && data.response) {
    const resp = data.response as { images?: RegistryImage[] };
    if (resp.images) images.push(...resp.images);
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Registry Images</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">{host}:{port}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            {isFetching ? "Refreshing…" : "Refresh"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10" />)}
          </div>
        ) : data?.error ? (
          <p className="text-sm text-red-500">
            Could not reach registry at {host}:{port}
          </p>
        ) : images.length === 0 ? (
          <p className="text-sm text-muted-foreground">No images in registry.</p>
        ) : (
          <div className="divide-y">
            {images.map((img) => (
              <div key={img.name} className="py-2.5 flex items-start gap-3">
                <span className="font-mono text-sm min-w-0 flex-1 truncate">{img.name}</span>
                <div className="flex flex-wrap gap-1 justify-end">
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
      </CardContent>
    </Card>
  );
}
