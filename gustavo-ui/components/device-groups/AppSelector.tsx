"use client";
import { useQuery } from "@tanstack/react-query";
import { listApps } from "@/lib/api/apps";
import { Badge } from "@/components/ui/badge";

interface AppSelectorProps {
  selected: string[];
  onChange: (apps: string[]) => void;
  exclude?: string[];
}

export function AppSelector({ selected, onChange, exclude = [] }: AppSelectorProps) {
  const { data } = useQuery({ queryKey: ["apps"], queryFn: listApps });

  const allApps: string[] = [];
  if (data && !data.error && data.response) {
    const resp = data.response as Record<string, unknown>;
    if (Array.isArray(resp.apps)) allApps.push(...resp.apps);
  }

  const availableApps = allApps.filter((app) => !exclude.includes(app));

  const toggle = (app: string) => {
    if (selected.includes(app)) {
      onChange(selected.filter((a) => a !== app));
    } else {
      onChange([...selected, app]);
    }
  };

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Add Apps</p>
      <div className="flex flex-wrap gap-2">
        {availableApps.length === 0 && (
          <p className="text-sm text-muted-foreground">
            {allApps.length === 0 ? "No apps available" : "All apps already assigned"}
          </p>
        )}
        {availableApps.map((app) => (
          <Badge
            key={app}
            variant={selected.includes(app) ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => toggle(app)}
          >
            {app}
          </Badge>
        ))}
      </div>
    </div>
  );
}
