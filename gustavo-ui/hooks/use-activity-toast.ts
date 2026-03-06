"use client";
import { useToast } from "@/hooks/use-toast";
import { addActivity } from "@/lib/activityLog";
import type { ActivityLevel } from "@/lib/activityLog";

interface ActivityToastOptions {
  title: string;
  description?: string;
  variant?: "default" | "destructive";
}

export function useActivityToast() {
  const { toast } = useToast();

  const activityToast = (options: ActivityToastOptions) => {
    const level: ActivityLevel =
      options.variant === "destructive" ? "error" : "success";
    addActivity(level, options.title, options.description);
    toast(options);
  };

  return { toast: activityToast };
}
