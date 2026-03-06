"use client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { VitalsPoint } from "@/lib/hooks/useMonitoringStream";

interface MetricsChartProps {
  buffer: VitalsPoint[];
  title?: string;
}

export function MetricsChart({ buffer, title = "CPU Usage (%)" }: MetricsChartProps) {
  const data = buffer.map((p) => ({
    time: new Date(p.timestamp).toLocaleTimeString(),
    cpu: p.cpu_percent ?? null,
  }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        Waiting for monitoring data…
      </div>
    );
  }

  return (
    <div>
      {title && <h3 className="text-sm font-medium mb-2 text-gray-700">{title}</h3>}
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            connectNulls
            name="CPU %"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
