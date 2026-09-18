"use client";
import { useQuery } from "@tanstack/react-query";
import { listCronJobs } from "@/lib/api/cronJobs";
import { Badge } from "@/components/ui/badge";

interface CronJobSelectorProps {
  selected: string[];
  onChange: (cronJobs: string[]) => void;
  exclude?: string[];
}

export function CronJobSelector({ selected, onChange, exclude = [] }: CronJobSelectorProps) {
  const { data } = useQuery({ queryKey: ["cron-jobs"], queryFn: listCronJobs });

  const allCronJobs: string[] = [];
  if (data && !data.error && data.response) {
    const resp = data.response as Record<string, unknown>;
    if (Array.isArray(resp.cron_jobs)) allCronJobs.push(...resp.cron_jobs);
  }

  const availableCronJobs = allCronJobs.filter((c) => !exclude.includes(c));

  const toggle = (cronJob: string) => {
    if (selected.includes(cronJob)) {
      onChange(selected.filter((c) => c !== cronJob));
    } else {
      onChange([...selected, cronJob]);
    }
  };

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Add Cron Jobs</p>
      <div className="flex flex-wrap gap-2">
        {availableCronJobs.length === 0 && (
          <p className="text-sm text-muted-foreground">
            {allCronJobs.length === 0 ? "No cron jobs available" : "All cron jobs already assigned"}
          </p>
        )}
        {availableCronJobs.map((cronJob) => (
          <Badge
            key={cronJob}
            variant={selected.includes(cronJob) ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => toggle(cronJob)}
          >
            {cronJob}
          </Badge>
        ))}
      </div>
    </div>
  );
}
