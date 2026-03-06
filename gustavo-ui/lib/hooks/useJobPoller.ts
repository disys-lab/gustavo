"use client";
import { useState, useEffect, useRef } from "react";
import { getJob } from "@/lib/api/services";
import type { Job } from "@/lib/types/api";

const POLL_INTERVAL_MS = 1500;

interface UseJobPollerResult {
  job: Job | null;
  isRunning: boolean;
  isDone: boolean;
  isError: boolean;
}

/**
 * Polls GET /api/services/jobs/{jobId} every 1.5 s until status is 'done' or 'error'.
 * Pass null to stop polling.
 */
export function useJobPoller(jobId: string | null): UseJobPollerResult {
  const [job, setJob] = useState<Job | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }

    const poll = async () => {
      try {
        const res = await getJob(jobId);
        if (!res.error && res.response) {
          const j = res.response as Job;
          setJob(j);
          if (j.status === "done" || j.status === "error") {
            if (intervalRef.current) clearInterval(intervalRef.current);
          }
        }
      } catch {
        // Network error — keep polling
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId]);

  return {
    job,
    isRunning: job?.status === "running",
    isDone: job?.status === "done",
    isError: job?.status === "error",
  };
}
