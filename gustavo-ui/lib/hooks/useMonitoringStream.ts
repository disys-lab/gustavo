"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import type { MonitoringEvent } from "@/lib/types/api";

const BUFFER_MINUTES = 5;
const BUFFER_MAX = BUFFER_MINUTES * 60; // 300 entries max at 10s interval = 3000 s = 50 min

export interface VitalsPoint {
  timestamp: number;
  cpu_percent?: number;
}

interface UseMonitoringStreamResult {
  buffer: VitalsPoint[];
  lastEvent: MonitoringEvent | null;
  connected: boolean;
  error: string | null;
}

/**
 * Opens an EventSource to /api/monitoring/stream and maintains a 5-min rolling buffer.
 * The stream is admin-only on the backend — pass enabled=false (e.g. for a
 * non-admin session) to skip connecting at all.
 */
export function useMonitoringStream(
  device_group = "all",
  host = "all",
  enabled = true
): UseMonitoringStreamResult {
  const [buffer, setBuffer] = useState<VitalsPoint[]>([]);
  const [lastEvent, setLastEvent] = useState<MonitoringEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    const params = new URLSearchParams({ device_group, host });
    const url = `/api/monitoring/stream?${params.toString()}`;

    const es = new EventSource(url);
    esRef.current = es;

    es.addEventListener("monitoring", (ev: MessageEvent) => {
      try {
        const data: MonitoringEvent = JSON.parse(ev.data);
        setLastEvent(data);
        setConnected(true);
        setError(null);

        const point: VitalsPoint = {
          timestamp: Date.now(),
          cpu_percent: data.vitals?.cpu_percent,
        };

        setBuffer((prev) => {
          const next = [...prev, point];
          return next.length > BUFFER_MAX ? next.slice(next.length - BUFFER_MAX) : next;
        });
      } catch {
        // ignore parse errors
      }
    });

    es.addEventListener("error", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        setError(data.error || "Stream error");
      } catch {
        setError("Stream error");
      }
    });

    es.onerror = () => {
      setConnected(false);
      setError("Connection lost");
    };
  }, [device_group, host]);

  useEffect(() => {
    if (!enabled) return;
    connect();
    return () => {
      esRef.current?.close();
    };
  }, [connect, enabled]);

  return { buffer, lastEvent, connected, error };
}
